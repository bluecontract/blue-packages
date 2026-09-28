"""Operation headers, direct-first eligibility and exact-time Mandate checks."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol
from .language import BlueAccess, ExactValue, MISSING
from .model import Entry, Channel, DocumentView, Operation, Decision, ExternalOrderKey
from .registry import RuntimeRegistry
from .checkpoints import classify_newness
from .errors import Code, Eligibility, Newness, MandateOutcome, CoordinationError, require

@dataclass(frozen=True)
class OperationRequest:
    channel: str
    operation: str
    document: Any = MISSING
    require_exact_document_version: bool = False
    request: Any = MISSING

@dataclass(frozen=True)
class MandateResolution:
    outcome: MandateOutcome
    initial_blue_id: str
    before: ExternalOrderKey
    state: ExactValue | None = None
    evidence: ExactValue | None = None
    detail: str = ''

class MandateResolver(Protocol):
    def resolve_before(self, initial_blue_id: str, order: ExternalOrderKey) -> MandateResolution: ...
    def verify(self, result: MandateResolution) -> None: ...


def operation_request(entry: Entry, blue: BlueAccess, registry: RuntimeRegistry) -> OperationRequest | None:
    view = blue.view(entry.message)
    role = registry.role(view, required=False)
    if role != 'operation_request':
        # A genuinely unrelated general event need not be an Operation Request.
        if role is None:
            registry.unknown_contract_is_inert(view)
        return None
    exact = view.optional('requireExactDocumentVersion')
    exact_flag = False if exact is MISSING else exact.scalar()
    require(type(exact_flag) is bool, Code.REJECTED, 'requireExactDocumentVersion must be Boolean')
    document = view.optional('document'); request = view.optional('request')
    return OperationRequest(view.need('channel').text(), view.need('operation').text(),
        MISSING if document is MISSING else document.exact('value'), exact_flag,
        MISSING if request is MISSING else request.literal_exact('value'))

class LanguageEligibility:
    """Conservative installed boundary policy used by the reference adapter.

    A declared request pattern requires a present value satisfying Language
    specialization; no declaration accepts either absence or a valid value.
    Non-exact-version targeting still requires the current exact state. Hosts
    can install a different, proven same-lineage policy, not an arbitrary latest
    redirect. Actor Policy's small reference profile uses exact type allow/deny
    lists, never descriptive strings or a provider's preapproval flag.
    """
    def __init__(self, blue: BlueAccess, registry: RuntimeRegistry):
        self.blue, self.registry = blue, registry

    def request_allowed(self, operation: Operation, request: Any) -> bool:
        return operation.request_pattern is MISSING or self.blue.matches(operation.request_pattern, request)

    def document_allowed(self, request: OperationRequest, target: DocumentView) -> bool:
        if request.document is MISSING:
            return not request.require_exact_document_version
        return request.document.blue_id == target.state.blue_id

    def actor_allowed(self, policy: Any, entry: Entry) -> bool:
        if policy is MISSING:
            return True
        self.registry.expect(policy, 'actor_policy')
        view = self.blue.view(policy)
        allowed = {'allowedActorTypes', 'deniedActorTypes', 'allowedSourceTypes', 'deniedSourceTypes', 'specification'}
        require(set(view.fields()) <= allowed, Code.UNSUPPORTED_COORDINATION_TYPE, 'unknown Actor Policy predicate')
        actor_type = self.blue.view(entry.actor).type_id
        source_type = None if entry.source is MISSING else self.blue.view(entry.source).type_id
        for allow_name, deny_name, actual in (
            ('allowedActorTypes', 'deniedActorTypes', actor_type),
            ('allowedSourceTypes', 'deniedSourceTypes', source_type)):
            allow = view.optional(allow_name); deny = view.optional(deny_name)
            if allow is not MISSING and actual not in {v.blue_id for v in allow.items()}:
                return False
            if deny is not MISSING and actual in {v.blue_id for v in deny.items()}:
                return False
        return True


def direct_authority(target: Channel, accepted: tuple[Channel, ...], entry: Entry) -> bool:
    for source in accepted:
        if source.address == target.address:
            return True
        if target.kind == 'timeline_channel':
            # Aggregate source matching carries its exact leaf authority binding.
            if any(a.admits(entry) and b.admits(entry) and a.timeline_blue_id == b.timeline_blue_id
                   and a.actor_blue_id == b.actor_blue_id
                   for a in source.sources for b in target.sources):
                return True
    return False


def verify_operation_mandate(entry: Entry, request: OperationRequest, target: DocumentView,
                             target_channel: Channel, blue: BlueAccess, registry: RuntimeRegistry,
                             resolver: MandateResolver | None) -> tuple[Eligibility, ExactValue | None, str]:
    if entry.authority is MISSING:
        return Eligibility.WITHHELD, None, 'no delegated authority'
    authority = blue.view(entry.authority)
    registry.expect(authority, 'mandate_authority')
    holder = authority.need('actor').exact('value')
    initial = authority.need('initialMandateDocument').blue_id
    if resolver is None:
        return Eligibility.DEFERRED_UNAVAILABLE, None, 'no exact-time Mandate resolver'
    resolved = resolver.resolve_before(initial, entry.order)
    require(resolved.initial_blue_id == initial and resolved.before == entry.order,
            Code.INVALID_EVIDENCE, 'Mandate resolution targets a different history or action order')
    if resolved.outcome == MandateOutcome.DEFERRED_UNAVAILABLE:
        return Eligibility.DEFERRED_UNAVAILABLE, None, resolved.detail
    if resolved.outcome in (MandateOutcome.INVALID_EVIDENCE, MandateOutcome.AMBIGUOUS):
        return Eligibility.INVALID_EVIDENCE, None, resolved.outcome
    resolver.verify(resolved)
    if resolved.outcome == MandateOutcome.INELIGIBLE:
        return Eligibility.WITHHELD, resolved.evidence, resolved.detail
    require(resolved.state is not None and resolved.evidence is not None,
            Code.INVALID_EVIDENCE, 'resolved authority needs exact processed state and evidence')
    binding = registry.expect(resolved.state, 'operation_mandate')
    runtime = binding.implementation
    require(runtime is not None and callable(getattr(runtime, 'validate_delegation', None)),
            Code.UNSUPPORTED_COORDINATION_TYPE, 'Operation Mandate type needs an exact restriction runtime')
    return runtime.validate_delegation(entry, request, target, target_channel,
                                       holder, resolved.state, resolved.evidence, blue, registry)


def classify_eligibility(entry: Entry, target: DocumentView, scope_path: str,
                         candidates: tuple[Channel, ...], blue: BlueAccess,
                         registry: RuntimeRegistry, policy: LanguageEligibility,
                         resolver: MandateResolver | None = None) -> Decision:
    """Q17 order: evidence is already verified by planning; source/newness first."""
    def decision(status, sources=(), operation=None, evidence=None, detail=''):
        return Decision(status, target.key, scope_path, tuple(sources), operation, evidence, detail, candidates)
    try:
        matching = tuple(c for c in candidates if c.accepts(entry))
        if not matching:
            return decision(Eligibility.NO_MATCH)
        new = tuple(c for c in matching if classify_newness(c, entry, blue, registry) != Newness.STALE)
        if not new:
            return decision(Eligibility.STALE)
        request = operation_request(entry, blue, registry)
        if request is None:
            return decision(Eligibility.ELIGIBLE_DIRECT, new)
        channels = {c.address.channel_key: c for c in target.channels if c.address.scope_path == scope_path}
        target_channel = channels.get(request.channel)
        operation = next((o for o in target.operations if o.scope_path == scope_path and o.key == request.operation), None)
        if target_channel is None or operation is None or operation.channel_key != request.channel:
            return decision(Eligibility.REJECTED, new, detail='missing/mismatched target Channel or Operation')
        registry.lookup(operation.type_blue_id)
        if not policy.document_allowed(request, target):
            return decision(Eligibility.REJECTED, new, operation, detail='target document precondition')
        if not policy.request_allowed(operation, request.request):
            return decision(Eligibility.REJECTED, new, operation, detail='Operation request pattern')
        if not policy.actor_allowed(operation.actor_policy, entry):
            return decision(Eligibility.WITHHELD, new, operation, detail='Actor Policy')
        if direct_authority(target_channel, new, entry):
            return decision(Eligibility.ELIGIBLE_DIRECT, new, operation)
        status, evidence, detail = verify_operation_mandate(
            entry, request, target, target_channel, blue, registry, resolver)
        return decision(status, new, operation, evidence, detail)
    except CoordinationError as error:
        status = {Code.NEEDS_RESOURCES: Eligibility.DEFERRED_UNAVAILABLE,
                  Code.REJECTED: Eligibility.REJECTED,
                  Code.UNSUPPORTED_COORDINATION_TYPE: Eligibility.UNSUPPORTED,
                  Code.INCOMPATIBLE_COORDINATION_TYPES: Eligibility.UNSUPPORTED}.get(error.code, Eligibility.INVALID_EVIDENCE)
        return decision(status, detail=str(error))
