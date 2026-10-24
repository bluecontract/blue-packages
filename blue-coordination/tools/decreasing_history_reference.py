"""Finite prerequisite walk over exact established document versions.

Native receipt authentication and extraction of selected document dependencies
are premises. Lineage alone is not a recursion key: a prior version of A may
terminate a chain which started at a later version of A.
"""


def prerequisite_order(root, observations):
    nodes = {row['document']: row for row in observations}
    if len(nodes) != len(observations):
        raise ValueError('DUPLICATE_VERSION')
    completed, visiting, result = set(), set(), []

    def visit(identity):
        if identity in completed:
            return
        if identity in visiting:
            raise ValueError('LIVE_COMPONENT_REQUIRES_SEPARATE_ESTABLISHMENT')
        if identity not in nodes:
            raise ValueError('WAIT_MISSING_ESTABLISHED_VERSION')
        visiting.add(identity)
        row = nodes[identity]
        for dependency in row['dependencies']:
            if dependency not in nodes:
                raise ValueError('WAIT_MISSING_ESTABLISHED_VERSION')
            if nodes[dependency]['order'] > row['order']:
                raise ValueError('FUTURE_PREREQUISITE')
            visit(dependency)
        visiting.remove(identity)
        completed.add(identity)
        result.append(identity)
    visit(root)
    return result
