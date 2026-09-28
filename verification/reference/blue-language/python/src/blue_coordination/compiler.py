"""Reference channel/operation compiler reused from the audited Coordination package.

Supported: root scopes, literal acyclic Process Embedded paths/collections,
Timeline/Composite/All Channels, Operation headers, static workflow metadata,
and exact checkpoints emitted by this reference host. Unsupported Contracts
features fail closed; schemas and identity are still supplied by Language.
"""
from __future__ import annotations
from dataclasses import replace
from typing import Any
from algorithms import blue as L
from blue_coordination.language import BlueAccess, ExactValue, View, MISSING
from blue_coordination.registry import RuntimeRegistry
from blue_coordination.model import (Address, Source, Channel, Operation, DocumentView,
                                     Occurrence, Snapshot, Entry, ExternalOrderKey)
from blue_coordination.identity import H, canonical_bytes, history_basis
from blue_coordination.errors import Code, require, CoordinationError

PROFILE_ID = H('blue-python-fixture-contracts-profile/1', {
    'name': 'literal-workflow-subset', 'version': '1', 'gas': 'see-blue-stack-reference-profile'})


def reference_position(document: str, basis: str, state: ExactValue, epoch: int) -> str:
    return H('blue-python-reference-position/1', {'documentId': document,
        'historyBasisIdentity': basis, 'stateBlueId': state.blue_id, 'epoch': str(epoch)})


def source_fingerprint(type_id: str, kind: str, sources: tuple[Source, ...], membership: list[str]) -> str:
    return H('blue-python-reference-source-lineage/1', {'type': type_id, 'kind': kind,
        'members': sorted(membership), 'sources': sorted([
            {'timeline': s.timeline_blue_id, 'actor': s.actor_blue_id, 'leaf': s.leaf_key,
             'activeAfter': {'kind': 'BEGINNING'} if s.active_after is None else s.active_after.record()}
            for s in sources], key=canonical_bytes)})


def optional_at(blue: BlueAccess, state: ExactValue, pointer: str):
    current = blue.view(state)
    for part in L.path_parts(pointer):
        h = current.head
        if h.kind not in ('object', 'none', 'list'):
            raise CoordinationError(Code.REJECTED, 'embedded pointer traverses incompatible content')
        if h.items is not None:
            require(part.isdigit() and str(int(part)) == part, Code.REJECTED, 'invalid embedded list index')
            items = current.items()
            if int(part) >= len(items):
                return MISSING
            current = items[int(part)]
        else:
            current = current.field(part)
            if current is MISSING:
                return MISSING
    if not L.present_recipe(current.recipe, current.context):
        return MISSING
    return current


def embedded_values(blue: BlueAccess, registry: RuntimeRegistry, state: ExactValue) -> tuple[tuple[str, ExactValue], ...]:
    contracts = blue.view(state).field('contracts')
    if contracts is MISSING:
        return ()
    paths = []
    for contract in contracts.fields().values():
        if registry.role(contract, required=False) != 'process_embedded':
            continue
        direct = contract.optional('paths')
        collections = contract.optional('collectionPaths')
        if direct is not MISSING:
            paths.extend(x.text() for x in direct.items())
        if collections is not MISSING:
            for item in collections.items():
                path = item.text()
                container = optional_at(blue, state, path)
                if container is MISSING:
                    continue
                require(container.head.kind == 'object', Code.REJECTED,
                        'Process Embedded collection must be an object; empty and missing are distinct values')
                for key, member in sorted(container.fields().items()):
                    if L.present_recipe(member.recipe, member.context):
                        paths.append(path + '/' + key.replace('~', '~0').replace('/', '~1'))
    require(len(paths) == len(set(paths)), Code.REJECTED, 'overlapping duplicate managed occurrence path')
    values = []
    for path in sorted(paths):
        require(path != '', Code.REJECTED, 'root cannot directly contain itself without owning-set evidence')
        value = optional_at(blue, state, path)
        if value is not MISSING:
            values.append((path, value.exact('definition')))
    return tuple(values)


def compile_channels(blue: BlueAccess, registry: RuntimeRegistry, state: ExactValue,
                     document: str, basis: str, *, old: tuple[Channel, ...] = (),
                     admission_after: ExternalOrderKey | None = None,
                     creating_entry: Entry | None = None, trusted_checkpoint: bool = False
                     ) -> tuple[tuple[Channel, ...], tuple[Operation, ...]]:
    root = blue.view(state)
    cs = root.field('contracts')
    if cs is MISSING:
        return (), ()
    require(cs.head.kind == 'object', Code.REJECTED, 'contracts must be a map')
    items = cs.fields(); roles = {}
    checkpoints = {}
    checkpoint_count = 0
    for key, value in items.items():
        role = registry.role(value, required=False)
        if role is None:
            registry.unknown_contract_is_inert(value)
        roles[key] = role
        if role == 'checkpoint':
            require(trusted_checkpoint, Code.INVALID_CHECKPOINT_EVIDENCE, 'raw authored checkpoint has no processor provenance')
            checkpoint_count += 1
            require(checkpoint_count == 1, Code.INVALID_CHECKPOINT_EVIDENCE, 'multiple checkpoint markers')
            entries = value.field('entries')
            if entries is not MISSING:
                for ck, item in entries.fields().items():
                    checkpoints[ck] = item.need('subject').blue_id
    old_by_key = {c.address.channel_key: c for c in old}
    channels: dict[str, Channel] = {}
    def build(key: str, kind: str, sources: tuple[Source, ...], membership: list[str]) -> Channel:
        value = items[key]; previous = old_by_key.get(key)
        # Determine semantic changes without letting a new creation bound make
        # every old channel appear new. The bound is retained for same lineage.
        prototype = [(s.timeline_blue_id, s.actor_blue_id, s.leaf_key) for s in sources]
        previous_prototype = [] if previous is None else [(s.timeline_blue_id, s.actor_blue_id, s.leaf_key) for s in previous.sources]
        unchanged = (previous is not None and previous.type_blue_id == value.type_id
                     and previous.kind == kind and prototype == previous_prototype)
        if unchanged:
            sources = tuple(Source(s.timeline_blue_id, s.actor_blue_id, s.leaf_key,
                                   p.active_after) for s, p in zip(sources, previous.sources))
            generation = previous.address.activation_generation
        else:
            lower = creating_entry.order if creating_entry else admission_after
            sources = tuple(Source(s.timeline_blue_id, s.actor_blue_id, s.leaf_key,
                                   s.active_after if s.active_after is not None else lower) for s in sources)
            generation = str(int(previous.address.activation_generation) + 1) if previous else '0'
        lineage = source_fingerprint(value.type_id, kind, sources, membership)
        # A membership-only mutation also starts a fresh generation.
        if unchanged and lineage != previous.source_lineage:
            generation = str(int(previous.address.activation_generation) + 1)
            lower = creating_entry.order if creating_entry else admission_after
            sources = tuple(Source(s.timeline_blue_id, s.actor_blue_id, s.leaf_key, lower) for s in sources)
            lineage = source_fingerprint(value.type_id, kind, sources, membership)
            unchanged = False
        occurrence = H('blue-python-reference-channel-occurrence/1', {
            'documentId': document, 'historyBasisIdentity': basis, 'scopePath': '/',
            'channelKey': key, 'activationGeneration': generation})
        subject = checkpoints.get(key)
        checkpoint_lineage = (previous.source_lineage if previous is not None else lineage) if subject else None
        return Channel(Address(document, '/', generation, key, occurrence), value.type_id,
                       kind, sources, subject, lineage, checkpoint_lineage)
    for key in sorted(items):
        if roles[key] == 'timeline_channel':
            value = items[key]
            timeline = value.need('timeline'); actor = value.need('actor')
            registry.expect(timeline, 'timeline'); registry.expect(actor, 'actor')
            timeline_value=timeline.literal_exact('value',identity_operand=True)
            actor_value=actor.literal_exact('value',identity_operand=True)
            channels[key] = build(key, roles[key], (Source(timeline_value.blue_id, actor_value.blue_id, key),), [key])
    for key in sorted(items):
        if roles[key] == 'composite_channel':
            member_keys = [v.text() for v in items[key].need('channels').items()]
            require(len(member_keys) == len(set(member_keys)), Code.REJECTED, 'duplicate composite member')
            require(all(k in channels and channels[k].kind == 'timeline_channel' for k in member_keys),
                    Code.REJECTED, 'composite requires installed same-scope direct Timeline Channels')
            sources = tuple(channels[k].sources[0] for k in sorted(member_keys))
            channels[key] = build(key, roles[key], sources, sorted(member_keys))
    for key in sorted(items):
        if roles[key] == 'all_timelines_channel':
            direct = tuple(channels[k].sources[0] for k in sorted(channels) if channels[k].kind == 'timeline_channel')
            channels[key] = build(key, roles[key], direct,
                                  [k for k in sorted(channels) if channels[k].kind != 'all_timelines_channel'])
    operations = []
    for key in sorted(items):
        if roles[key] == 'operation':
            value = items[key]; request = value.field('request'); policy = value.optional('actorPolicy')
            operations.append(Operation('/', key, value.need('channel').text(), value.type_id,
                value.exact('definition'), MISSING if request is MISSING else request.literal_exact('definition'),
                MISSING if policy is MISSING else policy.exact('definition')))
    return tuple(channels[k] for k in sorted(channels)), tuple(operations)
