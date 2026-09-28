"""Q16 and Appendix B: exact-subject newness and atomic settlement projections."""
from __future__ import annotations
from typing import Callable
from .model import Entry, Channel
from .language import BlueAccess
from .registry import RuntimeRegistry
from .errors import Code, Newness, require, CoordinationError


def classify_newness(channel: Channel, candidate: Entry, blue: BlueAccess,
                     registry: RuntimeRegistry) -> Newness:
    binding = registry.lookup(channel.type_blue_id)
    require(binding.role == channel.kind, Code.INVALID_EVIDENCE, 'channel projection/runtime mismatch')
    if channel.checkpoint_subject is None:
        return Newness.NEW
    if channel.checkpoint_lineage != channel.source_lineage:
        return Newness.NEW_WITH_CHECKPOINT_RESET
    try:
        previous = Entry.read(blue.get(channel.checkpoint_subject), blue, registry)
    except CoordinationError as error:
        if error.code == Code.NEEDS_RESOURCES:
            raise
        raise CoordinationError(Code.INVALID_CHECKPOINT_EVIDENCE, error.detail) from error
    if not channel.accepts(previous):
        return Newness.NEW_WITH_CHECKPOINT_RESET
    if channel.kind == 'timeline_channel':
        require(len(channel.sources) == 1, Code.INVALID_EVIDENCE, 'direct Timeline Channel must have one source')
        if previous.timeline.blue_id != channel.sources[0].timeline_blue_id:
            return Newness.NEW_WITH_CHECKPOINT_RESET
        return Newness.STALE if (candidate.blue_id == previous.blue_id or
                                  candidate.timestamp <= previous.timestamp) else Newness.NEW
    if channel.kind in ('composite_channel', 'all_timelines_channel'):
        return Newness.STALE if candidate.order <= previous.order else Newness.NEW
    require(binding.implementation is not None, Code.UNSUPPORTED_COORDINATION_TYPE, 'no newness adapter')
    return binding.implementation.newness(previous, candidate, channel)


def checkpoint_writes(channels: tuple[Channel, ...], entry: Entry) -> dict:
    """A staged projection; publication still requires the complete committed result."""
    result = {}
    for channel in channels:
        address = channel.address
        require(address not in result, Code.INVALID_EVIDENCE, 'duplicate checkpoint owner')
        result[address] = {'subject': {'blueId': entry.blue_id}}
    return result


def checkpoint_resets(before: tuple[Channel, ...], after: tuple[Channel, ...]) -> frozenset:
    current = {(c.address.document_id, c.address.scope_path, c.address.channel_key): c for c in after}
    reset = set()
    for old in before:
        key = old.address.document_id, old.address.scope_path, old.address.channel_key
        new = current.get(key)
        if new is None or new.address != old.address or new.source_lineage != old.source_lineage:
            reset.add(old.address)
    return frozenset(reset)


def migrate_projected_subject(projected: dict, blue: BlueAccess, registry: RuntimeRegistry) -> dict:
    """Migration is verified against retained original content, never a reconstruction."""
    required = {'semantics', 'timestamp', 'timelineBlueId', 'entryBlueId'}
    require(type(projected) is dict and set(projected) == required,
            Code.INVALID_CHECKPOINT_EVIDENCE, 'unsupported projected checkpoint shape')
    entry = Entry.read(blue.get(projected['entryBlueId']), blue, registry)
    require(type(projected['timestamp']) is int and projected['timestamp'] == entry.timestamp
            and projected['timelineBlueId'] == entry.timeline.blue_id,
            Code.INVALID_CHECKPOINT_EVIDENCE, 'copied checkpoint tuple disagrees with exact entry')
    return {'subject': {'blueId': entry.blue_id}}
