"""Finite SCC partition from authenticated graph edges, not lifecycle authority.

This checker takes actual native graph vertices/edges as premises. It neither
creates completions nor treats a cycle as a proof of impossible initialization.
Mutual reachability is computed independently of the runtime Tarjan traversal.
"""


def components(vertices, edges):
    vertices = set(vertices)
    outgoing = {vertex: set() for vertex in vertices}
    for source, target in edges:
        if source not in vertices or target not in vertices:
            raise ValueError('EDGE_OUTSIDE_GRAPH')
        outgoing[source].add(target)
    reachable = {}
    for vertex in vertices:
        seen, pending = set(), [vertex]
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            pending.extend(outgoing[current] - seen)
        reachable[vertex] = seen
    remaining, result = set(vertices), []
    while remaining:
        first = min(remaining)
        component = {other for other in remaining
                     if other in reachable[first] and first in reachable[other]}
        result.append(sorted(component))
        remaining -= component
    return sorted(result)
