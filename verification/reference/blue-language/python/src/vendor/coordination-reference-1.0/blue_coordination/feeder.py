"""Executable Q Appendix A: completeness/eligibility outside one-input PROCESS.

The Host port is the Contracts/storage boundary, not a hidden implementation of
BEX, cyclic finalization or durable publication. Its complete obligations are
specified in SDK.md. The bundled reference host is an executable finite profile.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any
from .model import Snapshot, Entry, Channel, DocumentView, Decision, Delivery, FrozenInput
from .language import BlueAccess, ExactValue
from .registry import RuntimeRegistry
from .provider import TimelineProvider, VerifiedWindow, obtain_complete_windows
from .graph import forward_domain, derive_context, semantic_snapshot_identity
from .checkpoints import classify_newness
from .authority import LanguageEligibility, MandateResolver, classify_eligibility
from .history import PendingHead, minimum_ready_head
from .identity import H, delivery_basis, rooted_invocation, terminal_key, canonical_bytes
from .errors import Code, Newness, Eligibility, ADMITTED, TERMINAL, CoordinationError, require

@dataclass(frozen=True)
class HostStep:
    status: str
    entry_blue_id: str | None = None
    invocation_identity: str | None = None
    gas_used: int = 0
    detail: str = ''
    receipt_identity: str | None = None
    progress_committed: bool = False

@dataclass(frozen=True)
class DriverResult:
    status: str
    safe_before: int | None
    steps: tuple[HostStep, ...]
    detail: str = ''

@dataclass(frozen=True)
class Candidate:
    entry: Entry
    bindings: tuple[tuple[str, Channel], ...]

@dataclass(frozen=True)
class Plan:
    snapshot: Snapshot
    safe_before: int | None
    windows: tuple[VerifiedWindow, ...]
    selected: PendingHead | None

class Host(Protocol):
    def load_root(self, root: str) -> Snapshot: ...
    def verify_snapshot(self, snapshot: Snapshot) -> None: ...
    def terminal_subject(self, snapshot: Snapshot, view: DocumentView, channel: Channel) -> str | None: ...
    def retained_heads(self, snapshot: Snapshot) -> tuple[PendingHead, ...]: ...
    def live_tie_break(self, snapshot: Snapshot, entry: Entry) -> bytes: ...
    def cause_identity(self, entry: Entry) -> str: ...
    def base_invocation_identity(self, snapshot: Snapshot, entry: Entry,
                                 deliveries: tuple[Delivery, ...], gas_limit: int) -> str: ...
    def process_and_publish(self, admitted: FrozenInput, gas_limit: int) -> HostStep: ...
    def process_retained(self, snapshot: Snapshot, selected: PendingHead, gas_limit: int) -> HostStep: ...
    def commit_terminal(self, plan: Plan, candidate: Candidate, decisions: tuple[Decision, ...]) -> HostStep: ...
    def verify_ready(self, snapshot: Snapshot, windows: tuple[VerifiedWindow, ...]) -> None: ...


def plan_next(host: Host, root: str, blue: BlueAccess, registry: RuntimeRegistry,
              providers: dict[str, TimelineProvider]) -> Plan:
    snapshot = host.load_root(root)
    host.verify_snapshot(snapshot)
    views = forward_domain(snapshot)
    timelines = []
    for view in views:
        require(view.initialized, Code.NEEDS_RESOURCES, 'required view initialization incomplete')
        for channel in view.channels:
            registry.lookup(channel.type_blue_id)
            timelines.extend(s.timeline_blue_id for s in channel.sources)
    safe, windows = obtain_complete_windows(tuple(timelines), providers)
    by_timeline = {w.timeline_blue_id: w for w in windows}
    heads: dict[str, list[tuple[str, Channel]]] = {}
    entries: dict[str, Entry] = {}
    for view in views:
        for channel in view.channels:
            terminal_subject = host.terminal_subject(snapshot, view, channel)
            terminal = None if terminal_subject is None else Entry.read(blue.get(terminal_subject), blue, registry)
            relevant: dict[str, Entry] = {}
            for source in channel.sources:
                for entry in by_timeline[source.timeline_blue_id].entries:
                    if safe is not None and entry.timestamp < safe and channel.in_interval(entry):
                        relevant[entry.blue_id] = entry
            for entry in sorted(relevant.values(), key=lambda e: e.order):
                if terminal is not None and entry.order <= terminal.order:
                    continue
                # Checkpoints only classify entries accepted by this source law;
                # a nonmatching actor remains a terminal NO_MATCH obligation.
                if channel.accepts(entry) and classify_newness(channel, entry, blue, registry) == Newness.STALE:
                    continue
                entries[entry.blue_id] = entry
                heads.setdefault(entry.blue_id, []).append((view.key, channel))
                break
    pending = []
    for eid, bindings in heads.items():
        entry = entries[eid]
        pending.append(PendingHead(eid, 'LIVE', entry.order, Candidate(entry, tuple(bindings)),
                                   True, host.live_tie_break(snapshot, entry)))
    # The installed Contracts/history adapter exposes one authenticated head
    # per pending receiving context, including unavailable prerequisite heads.
    pending.extend(host.retained_heads(snapshot))
    selected = minimum_ready_head(tuple(pending))
    return Plan(snapshot, safe, windows, selected)


def freeze_eligibility(plan: Plan, host: Host, blue: BlueAccess, registry: RuntimeRegistry,
                       policy: LanguageEligibility, resolver: MandateResolver | None,
                       gas_limit: int) -> tuple[Candidate, tuple[Decision, ...], FrozenInput | None]:
    require(plan.selected is not None and plan.selected.kind == 'LIVE', Code.INVALID_EVIDENCE, 'not a selected LIVE head')
    candidate: Candidate = plan.selected.payload
    groups: dict[tuple[str, str], list[Channel]] = {}
    for view_key, channel in candidate.bindings:
        groups.setdefault((view_key, channel.address.scope_path), []).append(channel)
    index = plan.snapshot.index()
    decisions = tuple(classify_eligibility(candidate.entry, index[v], scope, tuple(channels),
                          blue, registry, policy, resolver)
                      for (v, scope), channels in sorted(groups.items()))
    for decision in decisions:
        if decision.status == Eligibility.DEFERRED_UNAVAILABLE:
            raise CoordinationError(Code.NEEDS_RESOURCES, decision.detail)
        if decision.status == Eligibility.INVALID_EVIDENCE:
            raise CoordinationError(Code.INVALID_EVIDENCE, decision.detail)
        if decision.status == Eligibility.UNSUPPORTED:
            raise CoordinationError(Code.UNSUPPORTED_COORDINATION_TYPE, decision.detail)
    deliveries = tuple(Delivery(d.view_key, d.scope_path, d.source_channels, d.operation, d.authority_evidence)
                       for d in decisions if d.status in ADMITTED)
    if not deliveries:
        require(all(d.status in TERMINAL for d in decisions), Code.INVALID_EVIDENCE, 'unclassified nonterminal decision')
        return candidate, decisions, None
    _, owner, context, _ = derive_context(plan.snapshot)
    receiving = [c.address.record() for d in deliveries for c in d.source_channels]
    basis = delivery_basis({'operationOwnerIdentity': owner,
        'causeIdentity': host.cause_identity(candidate.entry), 'kind': 'LIVE',
        'receivingBindings': receiving, 'sourcePositionIdentity': {'kind': 'NONE'}})
    base = host.base_invocation_identity(plan.snapshot, candidate.entry, deliveries, gas_limit)
    invocation = rooted_invocation(base, context, basis)
    evidence = tuple(w.evidence for w in plan.windows) + tuple(
        d.authority_evidence for d in deliveries if d.authority_evidence is not None)
    frozen = FrozenInput(plan.snapshot, candidate.entry, deliveries, decisions, owner, context,
                         basis, invocation, terminal_key(owner, basis), evidence, base)
    return candidate, decisions, frozen


class Feeder:
    def __init__(self, host: Host, blue: BlueAccess, registry: RuntimeRegistry,
                 providers: dict[str, TimelineProvider], *, policy: LanguageEligibility | None = None,
                 mandate_resolver: MandateResolver | None = None):
        self.host, self.blue, self.registry, self.providers = host, blue, registry, providers
        self.policy = policy or LanguageEligibility(blue, registry)
        self.mandate_resolver = mandate_resolver

    def drain(self, root: str, *, gas_limit: int = 100000, max_steps: int = 1000) -> DriverResult:
        require(type(gas_limit) is int and gas_limit >= 0, Code.REJECTED, 'invalid gas allowance')
        require(type(max_steps) is int and max_steps >= 1, Code.REJECTED, 'invalid operational drain budget')
        results = []
        safe = None
        for _ in range(max_steps):
            try:
                plan = plan_next(self.host, root, self.blue, self.registry, self.providers)
                safe = plan.safe_before
                if plan.selected is None:
                    self.host.verify_ready(plan.snapshot, plan.windows)
                    return DriverResult('IDLE_AT_BOUNDARY', safe, tuple(results))
                if plan.selected.kind != 'LIVE':
                    step = self.host.process_retained(plan.snapshot, plan.selected, gas_limit)
                else:
                    candidate, decisions, frozen = freeze_eligibility(
                        plan, self.host, self.blue, self.registry, self.policy, self.mandate_resolver, gas_limit)
                    step = (self.host.commit_terminal(plan, candidate, decisions) if frozen is None
                            else self.host.process_and_publish(frozen, gas_limit))
                results.append(step)
                if not step.progress_committed or step.status not in ('APPLIED', 'NO_MATCH', 'STALE', 'REJECTED', 'WITHHELD', 'MIXED'):
                    return DriverResult(step.status, safe, tuple(results), step.detail)
                # No remainder of the old plan survives this iteration.
            except CoordinationError as error:
                return DriverResult(str(error.code), safe, tuple(results), error.detail)
        # This is an operational cancellation point, NOT semantic gas failure.
        return DriverResult('DRAIN_BUDGET_EXHAUSTED', safe, tuple(results))
