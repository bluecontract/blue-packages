"""Immutable semantic projections supplied by exact installed adapters."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .language import BlueAccess, ExactValue, MISSING
from .registry import RuntimeRegistry
from .errors import Code, require, Eligibility
from .identity import MAX_SAFE_INTEGER, blue_id, document_id, unsigned, sha, H

@dataclass(frozen=True, order=True)
class ExternalOrderKey:
    timestamp: int
    timeline_blue_id: str
    entry_blue_id: str

    def __post_init__(self):
        require(type(self.timestamp) is int and 0 <= self.timestamp <= MAX_SAFE_INTEGER,
                Code.INVALID_EVIDENCE, 'timestamp must be an unsigned safe integer in microseconds')
        blue_id(self.timeline_blue_id); blue_id(self.entry_blue_id)
        require(self.timeline_blue_id.isascii() and self.entry_blue_id.isascii(),
                Code.INVALID_EVIDENCE, 'order requires ASCII BlueIds')

    def record(self) -> dict:
        return {'timestampUs': str(self.timestamp), 'timelineBlueId': self.timeline_blue_id,
                'entryBlueId': self.entry_blue_id}

    @classmethod
    def from_record(cls, value: dict) -> 'ExternalOrderKey':
        from .identity import order_record
        order_record(value)
        return cls(int(value['timestampUs']), value['timelineBlueId'], value['entryBlueId'])

@dataclass(frozen=True)
class Entry:
    exact: ExactValue
    timeline: ExactValue
    actor: ExactValue
    timestamp: int
    previous_blue_id: str | None
    message: ExactValue
    source: Any = MISSING
    authority: Any = MISSING

    @property
    def blue_id(self) -> str:
        return self.exact.blue_id

    @property
    def order(self) -> ExternalOrderKey:
        return ExternalOrderKey(self.timestamp, self.timeline.blue_id, self.blue_id)

    @classmethod
    def read(cls, exact: ExactValue, blue: BlueAccess, registry: RuntimeRegistry) -> 'Entry':
        blue.verify(exact)
        view = blue.view(exact)
        registry.expect(view, 'timeline_entry')
        timeline = view.need('timeline'); actor = view.need('actor')
        registry.expect(timeline, 'timeline'); registry.expect(actor, 'actor')
        previous = view.optional('prevEntry')
        source = view.optional('source'); authority = view.optional('onBehalfOf')
        result = cls(exact, timeline.literal_exact('value',identity_operand=True), actor.literal_exact('value',identity_operand=True),
            view.need('timestamp').integer(), None if previous is MISSING else previous.literal_exact('definition',identity_operand=True).blue_id,
            view.need('message').literal_exact('value',identity_operand=True),
            MISSING if source is MISSING else source.literal_exact('value',identity_operand=True),
            MISSING if authority is MISSING else authority.literal_exact('value',identity_operand=True))
        result.order  # Validate the exact order domain, including zero.
        return result

@dataclass(frozen=True, order=True)
class Address:
    document_id: str
    scope_path: str
    activation_generation: str
    channel_key: str
    occurrence_identity: str

    def __post_init__(self):
        document_id(self.document_id); unsigned(self.activation_generation); sha(self.occurrence_identity)
        require(type(self.scope_path) is str and type(self.channel_key) is str,
                Code.INVALID_EVIDENCE, 'invalid channel address')

    def record(self) -> dict:
        return {'documentId': self.document_id, 'scopePath': self.scope_path,
                'activationGeneration': self.activation_generation, 'channelKey': self.channel_key,
                'occurrenceIdentity': self.occurrence_identity}

@dataclass(frozen=True)
class Source:
    timeline_blue_id: str
    actor_blue_id: str
    leaf_key: str
    active_after: ExternalOrderKey | None = None

    def admits(self, entry: Entry) -> bool:
        return (entry.timeline.blue_id == self.timeline_blue_id
                and entry.actor.blue_id == self.actor_blue_id
                and (self.active_after is None or entry.order > self.active_after))

@dataclass(frozen=True)
class Channel:
    address: Address
    type_blue_id: str
    kind: str  # timeline_channel | composite_channel | all_timelines_channel
    sources: tuple[Source, ...]
    checkpoint_subject: str | None = None
    source_lineage: str = ''
    checkpoint_lineage: str | None = None

    def accepts(self, entry: Entry) -> bool:
        return any(source.admits(entry) for source in self.sources)

    def in_interval(self, entry: Entry) -> bool:
        return any(s.timeline_blue_id == entry.timeline.blue_id and
                   (s.active_after is None or entry.order > s.active_after) for s in self.sources)

@dataclass(frozen=True)
class Operation:
    scope_path: str
    key: str
    channel_key: str
    type_blue_id: str
    exact: ExactValue
    request_pattern: Any = MISSING
    actor_policy: Any = MISSING

@dataclass(frozen=True)
class Occurrence:
    identity: str
    parent_view: str
    child_view: str
    source_path: str
    activation_generation: str = '0'
    live: bool = True

@dataclass(frozen=True)
class DocumentView:
    key: str
    document_id: str
    state: ExactValue
    initial_blue_id: str
    history_basis_identity: str
    epoch: int
    channels: tuple[Channel, ...] = ()
    operations: tuple[Operation, ...] = ()
    initialized: bool = True
    position_identity: str = ''

@dataclass(frozen=True)
class Snapshot:
    root_view: str
    views: tuple[DocumentView, ...]
    occurrences: tuple[Occurrence, ...] = ()
    revision: int = 0
    # A processor-owned inspection token/receipt is verified at the host boundary.
    verification_identity: str = ''

    def index(self) -> dict[str, DocumentView]:
        result = {v.key: v for v in self.views}
        require(len(result) == len(self.views), Code.INVALID_EVIDENCE, 'duplicate selected view')
        require(self.root_view in result, Code.INVALID_EVIDENCE, 'missing selected root')
        return result

@dataclass(frozen=True)
class Decision:
    status: Eligibility
    view_key: str
    scope_path: str
    source_channels: tuple[Channel, ...]
    operation: Operation | None = None
    authority_evidence: ExactValue | None = None
    detail: str = ''
    observed_channels: tuple[Channel, ...] = ()

@dataclass(frozen=True)
class Delivery:
    view_key: str
    scope_path: str
    source_channels: tuple[Channel, ...]
    operation: Operation | None
    authority_evidence: ExactValue | None = None

@dataclass(frozen=True)
class FrozenInput:
    snapshot: Snapshot
    entry: Entry
    deliveries: tuple[Delivery, ...]
    decisions: tuple[Decision, ...]
    owner_identity: str
    context_identity: str
    delivery_identity: str
    invocation_identity: str
    terminal_identity: str
    evidence: tuple[ExactValue, ...]
    base_invocation_identity: str
    kind: str = 'LIVE'
