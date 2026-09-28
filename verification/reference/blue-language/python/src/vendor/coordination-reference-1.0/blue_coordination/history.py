"""Retained position validation and one-head merging, separate from PROCESS.

Contracts authenticates transition bodies, finalizer classification, cyclic
proofs and publication membership. The verifier is an explicit required port;
a recomputed hash or equal endpoint is never accepted as that evidence.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Protocol, Any
from .model import ExternalOrderKey
from .language import ExactValue
from .errors import Code, require, CoordinationError
from .identity import H, sha, document_id, canonical_bytes

@dataclass(frozen=True)
class Emission:
    ordinal: int
    exact: ExactValue
    occurrence_identity: str

@dataclass(frozen=True)
class Position:
    source_document_id: str
    epoch: int
    representation_ordinal: int
    blue_id: str
    identity: str
    predecessor_identity: str | None
    predecessor_blue_id: str | None
    receipt_identity: str
    cause_identity: str
    source_order: ExternalOrderKey | None
    kind: str  # INITIALIZATION | REVISION | REPRESENTATION
    source_cause_kind: str  # Kept unchanged, including TIMELINE_ENTRY and EVENT_ONLY.
    emissions: tuple[Emission, ...] = ()

@dataclass(frozen=True)
class VerifiedTransition:
    position_identity: str
    receipt_identity: str
    committed: bool
    finalizer_only: bool = False

class TransitionVerifier(Protocol):
    def verify(self, previous: Position, successor: Position) -> VerifiedTransition: ...


def verify_successor(previous: Position, successor: Position, verifier: TransitionVerifier) -> None:
    proof = verifier.verify(previous, successor)
    require(proof.position_identity == successor.identity and proof.receipt_identity == successor.receipt_identity
            and proof.committed, Code.INVALID_EVIDENCE, 'transition lacks authenticated committed membership')
    require(successor.source_document_id == previous.source_document_id,
            Code.INVALID_EVIDENCE, 'retained lineage mismatch')
    require(successor.predecessor_identity == previous.identity
            and successor.predecessor_blue_id == previous.blue_id,
            Code.INVALID_EVIDENCE, 'retained predecessor position/content mismatch')
    require(type(successor.epoch) is int and type(successor.representation_ordinal) is int,
            Code.INVALID_EVIDENCE, 'non-integer source position')
    if successor.kind == 'REVISION':
        require(successor.epoch == previous.epoch + 1 and successor.representation_ordinal == 0,
                Code.INVALID_EVIDENCE, 'ManagedRevision must advance exactly one epoch')
    elif successor.kind == 'REPRESENTATION':
        require(successor.epoch == previous.epoch
                and successor.representation_ordinal == previous.representation_ordinal + 1
                and proof.finalizer_only, Code.INVALID_EVIDENCE,
                'same-epoch position needs contiguous authenticated finalizer-only transition')
    else:
        require(False, Code.INVALID_EVIDENCE, 'initialization is not a retained successor')
    require(successor.source_order is not None, Code.INVALID_EVIDENCE, 'retained successor lacks original cause order')
    ordinals = [e.ordinal for e in successor.emissions]
    require(ordinals == list(range(len(ordinals))), Code.INVALID_EVIDENCE, 'emission ordinals must be contiguous')
    require(len({e.occurrence_identity for e in successor.emissions}) == len(successor.emissions),
            Code.INVALID_EVIDENCE, 'duplicate emission occurrence identity')

@dataclass(frozen=True)
class HistoryCursor:
    occurrence_identity: str
    activation_generation: str
    position: Position
    captured_goal_identity: str
    attachment_order: ExternalOrderKey
    active: bool = False

    @property
    def next_numbered_epoch(self) -> int:
        return self.position.epoch + 1


def advance_cursor(cursor: HistoryCursor, successor: Position, verifier: TransitionVerifier) -> HistoryCursor:
    require(not cursor.active and cursor.position.identity != cursor.captured_goal_identity,
            Code.INVALID_EVIDENCE, 'no pending retained step at/after captured goal')
    verify_successor(cursor.position, successor, verifier)
    require(successor.source_order <= cursor.attachment_order,
            Code.INVALID_EVIDENCE, 'retained step overtakes frozen attachment cutoff')
    return replace(cursor, position=successor)


def activate_at_goal(cursor: HistoryCursor, *, terminal_reconciliation_identity: str,
                     verified_terminal: bool) -> HistoryCursor:
    # verified_terminal is the result of the installed Contracts verifier, not
    # an authored/request field. Require its exact terminal receipt as well.
    sha(terminal_reconciliation_identity)
    require(verified_terminal and cursor.position.identity == cursor.captured_goal_identity,
            Code.INVALID_EVIDENCE, 'live join before authenticated captured goal')
    return replace(cursor, active=True)

@dataclass(frozen=True)
class PendingHead:
    binding_identity: str
    kind: str
    order: ExternalOrderKey | None
    payload: Any = None
    available: bool = True
    # The registered base runtime supplies its exact occurrence/position tie
    # projection. It is NOT an epoch number compared across different lineages.
    tie_break: bytes = b''
    detail: str = ''


def minimum_ready_head(heads: tuple[PendingHead, ...]) -> PendingHead | None:
    """An earlier unavailable obligation cannot be bypassed by a ready worker."""
    require(len({h.binding_identity for h in heads}) == len(heads), Code.INVALID_EVIDENCE,
            'more than one pending head for one receiving obligation')
    if not heads:
        return None
    if any(h.order is None for h in heads):
        raise CoordinationError(Code.NEEDS_RESOURCES, 'an unresolved required head has no proven lower order')
    require(len({(h.order, h.tie_break) for h in heads}) == len(heads), Code.INVALID_EVIDENCE,
            'distinct pending work lacks an unambiguous registered tie projection')
    selected = min(heads, key=lambda h: (h.order, h.tie_break))
    if not selected.available:
        raise CoordinationError(Code.NEEDS_RESOURCES, selected.detail or 'earliest required input unavailable')
    # Same-order unknown dependency work may precede the selected runnable one.
    for head in heads:
        if not head.available and (head.order, head.tie_break) <= (selected.order, selected.tie_break):
            raise CoordinationError(Code.NEEDS_RESOURCES, head.detail or 'unavailable prerequisite')
    return selected


def classify_cause(*, already_live: bool, pending_retained: Position | None) -> str:
    """Selection is independent of cache state or another root's source commit."""
    if already_live:
        require(pending_retained is None, Code.INVALID_EVIDENCE, 'live occurrence has a historical interval')
        return 'LIVE'
    require(pending_retained is not None, Code.NEEDS_RESOURCES, 'historical occurrence needs exact successor')
    if pending_retained.kind == 'REVISION':
        return 'MANAGED_REVISION'
    require(pending_retained.kind == 'REPRESENTATION', Code.INVALID_EVIDENCE, 'unsupported retained position')
    return 'MANAGED_REPRESENTATION'


def reference_work_identity(cursor: HistoryCursor, successor: Position,
                            consumer_head: str, barrier_identity: str) -> str:
    """Local-test work wrapper; not the missing Contracts/Java base constructor."""
    return H('blue-python-reference-retained-work/1', {
        'occurrenceIdentity': sha(cursor.occurrence_identity),
        'activationGeneration': cursor.activation_generation,
        'sourceDocumentId': document_id(successor.source_document_id),
        'beforePosition': sha(cursor.position.identity), 'afterPosition': sha(successor.identity),
        'capturedGoal': sha(cursor.captured_goal_identity), 'sourceEpoch': str(successor.epoch),
        'kind': classify_cause(already_live=False, pending_retained=successor),
        'receiptIdentity': sha(successor.receipt_identity), 'causeIdentity': sha(successor.cause_identity),
        'consumerHead': consumer_head, 'barrierIdentity': sha(barrier_identity)})
