# Executable reference algorithm models

These blocks are executed by the source runners and checked byte-for-byte by
`blue-contracts/tools/reference_sources.py --check`. They model only the stated
algorithm boundaries; they are not another whole Contracts executor or an
issuer of trusted completion capabilities. The runners report individual vector
execution separately from whole-edition qualification, which remains
`NOT_VERIFIED` until all required composition and Java equivalence gates pass.
The historical final-gas Python processor is a separate legacy profile and is
not the reference authority for demand-scoped execution or receiver-relative replay.

Native identity, contextual Recipe validation and owning proofs use the immutable,
SOURCE-LOCK-verified Language implementation. These models do not replace its
strict certification or reproduce its cryptography. Production source/journal
premises of receiver algorithms require actual authentication outside the model.

## tools/receiver_reference.py

SHA-256: `c6f2c778cd1d6223037dc977e0b98929f6e985d59477d9d0bf4c1b739085947c`

```python
"""Receiver-relative decision models over already authenticated history premises.

These functions do not authenticate records or execute Contracts. Their callers
must establish the premises through native source/journal verification; models
cannot grant authority from caller-provided booleans in a production runtime.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Before:
    current: str
    own_past: frozenset
    foreign: frozenset
    complete: bool


def classify_operation(target, exact, pre):
    if not pre.complete:
        return 'WAIT_PRE_HISTORY'
    if target is None:
        return 'SELECT_USING_CURRENT_DECLARATIONS'
    if exact:
        if target == pre.current:
            return 'ELIGIBLE'
        if target in pre.own_past:
            return 'REJECT_STALE_EXACT'
        return 'OUTSIDE_EXACT_PRE_VIEW'
    if target == pre.current or target in pre.own_past:
        return 'ELIGIBLE'
    if target in pre.foreign:
        return 'OUTSIDE_LINEAGE'
    return 'WAIT_TARGET_HISTORY'


def replay_frontier(phase, bound, ordered_entries, completed=()):
    """Full-K scan selection only; actual authority/receiving remain prerequisites."""
    if phase not in ('INITIAL', 'ACTIVATION'):
        raise ValueError('UNSUPPORTED_REPLAY_PHASE')
    if len(set(ordered_entries)) != len(ordered_entries):
        raise ValueError('DUPLICATE_SOURCE_ORDER')
    return tuple(key for key in sorted(ordered_entries)
                 if (key <= bound if phase == 'INITIAL' else key < bound)
                 and key not in completed)


def next_activation(obligations):
    """Deterministic ready order: original K, member, channel, generation."""
    return min(obligations, key=lambda row: (row[0], row[1].encode('utf-16-be'),
                                           row[2].encode('utf-16-be'), row[3])) if obligations else None


def attachment_goal(positions, attachment_order, supplied_position=None):
    """Established-history attachment uses strictly-before positions, never latest."""
    if len(set(positions)) != len(positions):
        raise ValueError('DUPLICATE_SOURCE_ORDER')
    before = tuple(sorted(position for position in positions if position < attachment_order))
    goal = before[-1] if before else None
    if supplied_position is not None and (goal is None or supplied_position > goal):
        raise ValueError('INITIALIZED_POSITION_BEYOND_ATTACHMENT_GOAL')
    if supplied_position is not None and supplied_position not in before:
        raise ValueError('MISSING_SOURCE_PREDECESSOR')
    return goal, tuple(position for position in before
                       if supplied_position is None or position > supplied_position)


def occurrence_receiving(source_positions, received, member, channel, generation):
    """Source execution survives detach; receiving positions are generation-local."""
    return tuple(position for position in source_positions
                 if (member, channel, generation, position) not in received)


@dataclass(frozen=True, order=True)
class HistoryKey:
    lineage: str
    bound: tuple
    phase: str
    generation: int = 0


@dataclass(frozen=True)
class HistoryPremise:
    version: str
    dependencies: tuple = ()  # (HistoryKey, exact expected source version)
    prefix_complete: bool = True
    pre_view_established: bool = True


def settle_dependencies(root, facts):
    """§4 worklist over authenticated immutable local-journal premises.

    Premises summarize verified histories; they do not authenticate evidence.
    Missing witnesses and unestablished pre-views remain WAIT. Malformed native
    receipts are rejected by their validator before becoming premises here.
    COMPONENT_READY permits the existing component algorithm, never its result.
    """
    from types import SimpleNamespace
    from blue_contracts.reference.graph import components
    pending, checked, edges, missing = [(root, None)], {}, [], set()
    while pending:
        key, expected = pending.pop(0)
        premise = facts.get(key)
        if premise is None:
            missing.add(key)
            continue
        # Incoming expectations must also be checked on a repeated obligation.
        if expected is not None and premise.version != expected:
            raise ValueError('INCOMPATIBLE_EXPECTED_SOURCE_POSITION')
        if not premise.prefix_complete:
            missing.add(key)
        if key in checked:
            continue
        checked[key] = premise
        for index, (dependency, version) in enumerate(premise.dependencies):
            edges.append(SimpleNamespace(source=key, target=dependency, path=str(index)))
            pending.append((dependency, version))
    if missing:
        return {'status': 'WAIT', 'obligations': tuple(sorted(missing))}
    for group in components(checked, edges):
        cyclic = len(group) > 1 or any(edge.source == group[0] == edge.target for edge in edges)
        if cyclic:
            if not all(checked[key].pre_view_established for key in group):
                return {'status': 'WAIT', 'obligations': group}
            return {'status': 'COMPONENT_READY', 'obligations': group}
        if not checked[group[0]].pre_view_established:
            return {'status': 'WAIT', 'obligations': group}
    return {'status': 'ESTABLISHED', 'obligations': tuple(sorted(checked))}
```
