"""Root-directed discovery, ownership and frozen semantic projections.

Graph rows enter after Contracts verifies declarations, positions and cyclic
proofs. These algorithms never turn a supplied row into admission authority.
"""
from __future__ import annotations
from .model import Snapshot, DocumentView, Occurrence
from .errors import Code, require
from .identity import H, operation_owner, root_context, canonical_bytes, sha


def forward_domain(snapshot: Snapshot) -> tuple[DocumentView, ...]:
    index = snapshot.index()
    edges: dict[str, list[Occurrence]] = {}
    for edge in snapshot.occurrences:
        edges.setdefault(edge.parent_view, []).append(edge)
    identities = set()
    todo = [snapshot.root_view]
    seen = set()
    while todo:
        key = todo.pop()
        if key in seen:
            continue
        require(key in index, Code.NEEDS_RESOURCES, 'missing required exact forward view')
        seen.add(key)
        for edge in edges.get(key, ()):
            require(edge.identity not in identities, Code.INVALID_EVIDENCE, 'duplicate required managed occurrence identity')
            identities.add(edge.identity)
            todo.append(edge.child_view)
    return tuple(sorted((index[k] for k in seen),
                        key=lambda v: (v.document_id.encode('utf-8'), v.position_identity, v.key)))


def live_component(snapshot: Snapshot, selected: str, *, _domain: set[str] | None = None) -> frozenset[str]:
    """SCC containing one selected view, not its weak/reverse-connected cohort."""
    domain = {v.key for v in forward_domain(snapshot)} if _domain is None else _domain
    require(selected in domain, Code.INVALID_EVIDENCE, 'component anchor outside rooted graph')
    forward = {key: set() for key in domain}
    reverse = {key: set() for key in domain}
    for edge in snapshot.occurrences:
        if edge.live and edge.parent_view in domain:
            require(edge.child_view in domain, Code.NEEDS_RESOURCES, 'incomplete live graph')
            forward[edge.parent_view].add(edge.child_view)
            reverse[edge.child_view].add(edge.parent_view)
    def reach(edges):
        seen, todo = set(), [selected]
        while todo:
            key = todo.pop()
            if key not in seen:
                seen.add(key); todo.extend(edges[key])
        return seen
    return frozenset(reach(forward) & reach(reverse))


def entry_owners(snapshot: Snapshot) -> frozenset[str]:
    return live_component(snapshot, snapshot.root_view)


def expand_owners(snapshot: Snapshot, entry_owner_keys: frozenset[str],
                  authenticated_newborns: frozenset[str] = frozenset()) -> frozenset[str]:
    """Monotone OWN-03 fixed point; newborn set comes from verified birth work."""
    index = snapshot.index()
    owned = set(entry_owner_keys | authenticated_newborns)
    require(owned <= set(index), Code.NEEDS_RESOURCES, 'owned member missing from candidate evidence')
    # Splitting cannot drop an entry owner merely because the requested view
    # no longer reaches it. Discover from every retained owner, never incoming
    # unrelated observers.
    domain, todo = set(), list(owned | {snapshot.root_view})
    while todo:
        key = todo.pop()
        if key in domain:
            continue
        require(key in index, Code.NEEDS_RESOURCES, 'missing expanded dependency')
        domain.add(key)
        todo.extend(e.child_view for e in snapshot.occurrences if e.parent_view == key)
    while True:
        expanded = set(owned)
        for member in owned:
            expanded.update(live_component(snapshot, member, _domain=domain))
        if expanded == owned:
            return frozenset(owned)
        owned = expanded


def derive_context(snapshot: Snapshot) -> tuple[str, str, str, dict]:
    index = snapshot.index(); owned = entry_owners(snapshot)
    members = [{'documentId': index[k].document_id,
                'historyBasisIdentity': index[k].history_basis_identity} for k in owned]
    edges = [{'occurrenceIdentity': e.identity, 'parentDocumentId': index[e.parent_view].document_id,
              'sourcePath': e.source_path, 'childDocumentId': index[e.child_view].document_id,
              'activationGeneration': e.activation_generation}
             for e in snapshot.occurrences
             if e.live and e.parent_view in owned and e.child_view in owned]
    anchor, owner, descriptor = operation_owner(members, edges)
    return anchor, owner, root_context(anchor, owner), descriptor


def semantic_snapshot_record(snapshot: Snapshot) -> dict:
    """An internal reference projection, not the absent base Contracts constructor.

    Positional identities distinguish equal-body epochs and historical views.
    Revision counters, worker IDs, requested cycle entrypoint and unrelated
    observers are deliberately absent. Installed processors supply their own
    complete base invocation constructor at the integration boundary.
    """
    domain = forward_domain(snapshot)
    index = {v.key: v for v in domain}
    anchor, owner, context, _ = derive_context(snapshot)
    rows = []
    for v in domain:
        sha(v.position_identity)
        channels = []
        for c in v.channels:
            channels.append({'address': c.address.record(), 'runtime': c.type_blue_id,
                'sourceLineage': c.source_lineage,
                'checkpointLineage': {'kind': 'NONE'} if c.checkpoint_lineage is None else
                    {'kind': 'VALUE', 'value': c.checkpoint_lineage},
                'subject': {'kind': 'NONE'} if c.checkpoint_subject is None else
                    {'kind': 'ENTRY', 'blueId': c.checkpoint_subject}})
        rows.append({'documentId': v.document_id, 'historyBasisIdentity': v.history_basis_identity,
                     'positionIdentity': v.position_identity, 'stateBlueId': v.state.blue_id,
                     'epoch': str(v.epoch), 'initialized': 'YES' if v.initialized else 'NO',
                     'channels': sorted(channels, key=canonical_bytes)})
    edges = []
    for e in snapshot.occurrences:
        if e.parent_view not in index:
            continue
        p, c = index[e.parent_view], index[e.child_view]
        edges.append({'occurrenceIdentity': e.identity, 'parentPosition': p.position_identity,
                      'childPosition': c.position_identity, 'sourcePath': e.source_path,
                      'activationGeneration': e.activation_generation, 'live': 'YES' if e.live else 'NO'})
    return {'canonicalRootDocumentId': anchor, 'operationOwnerIdentity': owner,
            'rootProcessingContextIdentity': context, 'views': sorted(rows, key=canonical_bytes),
            'occurrences': sorted(edges, key=canonical_bytes)}


def semantic_snapshot_identity(snapshot: Snapshot) -> str:
    return H('blue-python-reference-snapshot/1', semantic_snapshot_record(snapshot))


def vertex_simple_routes(snapshot: Snapshot, origin: str) -> tuple[tuple[str, ...], ...]:
    """One routing occurrence per authored reverse path inside the rooted graph.

    The discovery visited set is NOT reused here. Distinct diamond paths and
    repeated emissions retain multiplicity. A route visits each vertex at most
    once; actual FIFO work and handler order remain Contracts responsibilities.
    """
    domain = {v.key for v in forward_domain(snapshot)}
    require(origin in domain, Code.INVALID_EVIDENCE, 'event origin outside domain')
    parents: dict[str, list[Occurrence]] = {}
    for edge in snapshot.occurrences:
        if edge.parent_view in domain:
            parents.setdefault(edge.child_view, []).append(edge)
    routes = []
    todo = [(origin, frozenset({origin}), ())]
    while todo:
        child, visited, route = todo.pop()
        for edge in sorted(parents.get(child, ()), key=lambda e: e.identity, reverse=True):
            if edge.parent_view in visited:
                continue
            next_route = route + (edge.identity,)
            routes.append(next_route)
            todo.append((edge.parent_view, visited | {edge.parent_view}, next_route))
    return tuple(routes)
