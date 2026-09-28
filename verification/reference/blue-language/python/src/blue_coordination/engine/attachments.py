"""Exact occurrence cutoffs and contiguous retained-history selection."""
from blue_coordination_spec.model import require


def attachments(engine, catalogue, view, state, member, instance, old, member_instances,
                old_heads, owned, cause, prior_goals=None):
    """Freeze new runtime attachments strictly before their activation entry."""
    goals = {}
    effective = [cause.timestamp, cause.timeline, cause.blue_id] if cause else None
    for edge in state.edges.values():
        if edge.source != member:
            continue
        source = member_instances[edge.target]
        prior = view.get('forward', instance + '/' + edge.path)
        selected_id = state.documents[edge.target].blue_id
        selected = view.project('versions', engine.context + '/' + selected_id, ('number', 'documentId'))
        if selected is None:
            require(edge.target in owned, 'WAITING_SOURCE_HISTORY', document=selected_id)
            continue  # A genuine birth / same complete atomic owner result.
        inherited = (old or {}).get('attachmentGoals', {}).get(edge.path)
        if prior_goals and edge.path in prior_goals:
            inherited = prior_goals[edge.path]
        continuing = prior is not None and prior['generation'] == edge.generation and prior['source'] == source
        if continuing and inherited is not None:
            goal = dict(inherited)
        elif not continuing and cause is not None and edge.target not in owned:
            from .readiness import complete_through
            order = tuple(effective)
            require(complete_through(engine, view, source, order, inclusive=False),
                    'WAITING_ATTACHMENT_COMPLETENESS', instance=source)
            target = view.history_before(source, order)
            require(target is not None and target['stable'], 'WAITING_SOURCE_HISTORY', instance=source)
            require(selected['number'] <= target['number'], 'FUTURE_ATTACHMENT_POSITION',
                    source=selected['documentId'], selected=selected['number'], goal=target['number'])
            goal = dict(source=source, generation=edge.generation, number=target['number'],
                        activationOrder=effective)
        else:
            continue
        if selected['number'] < goal['number']:
            goals[edge.path] = goal
    return goals


def next_history(engine, catalogue, view, head, instance, *, before_order=None):
    """Select each exact next predecessor, then group one original cause.

    An existing frozen goal has priority. Otherwise an independently completed
    source may advance the occurrence only through already established history.
    """
    choices = []
    for _, edge in view.scan('forward', instance + '/'):
        if edge['source'] == instance:
            continue
        selected = view.project('versions', engine.context + '/' + edge['selected'],
                                ('number', 'member', 'documentId', 'position'))
        require(selected is not None, 'WAITING_SOURCE_HISTORY', document=edge['selected'])
        from .readiness import sealed_position
        source_head = sealed_position(view, edge['source'])
        require(source_head is not None, 'WAITING_SOURCE_HISTORY', instance=edge['source'])
        if selected['number'] >= source_head['number']:
            continue
        frozen = head.get('attachmentGoals', {}).get(edge['path'])
        if frozen is not None:
            require(frozen['generation'] == edge['generation'] and frozen['source'] == edge['source'], 'RETIRED_ATTACHMENT_GOAL')
            goal = frozen
        else:
            available = (view.history_before(edge['source'],before_order,inclusive=True) if before_order is not None else
                view.get('history',edge['source']+'/'+str(source_head['number']).zfill(16)))
            if available and available['number'] > source_head['number']:
                available = source_head
            if not available or available['number'] <= selected['number']:
                continue
            goal = dict(source=edge['source'], generation=edge['generation'], number=available['number'],
                        activationOrder=None)
        successor = view.get('history',edge['source']+'/'+str(selected['number']+1).zfill(16))
        require(successor is not None, 'WAITING_SOURCE_PREDECESSOR', instance=edge['source'])
        if successor['number'] > goal['number']:
            continue
        record = view.get('outcomes', engine.context + '/' + successor['receipt'])
        require(record is not None and record['before'] is not None, 'WAITING_SOURCE_COMPLETION')
        cause = catalogue.entry(record['event']) if record['event'] else None
        original_order = (cause.timestamp, cause.timeline, cause.blue_id) if cause else (-1, '', '')
        order = tuple(successor.get('effectiveOrder') or original_order)
        choices.append(dict(edge=edge, selected=selected, successor=successor, goal=goal, cause=cause, order=order, originalOrder=original_order))
    if not choices:
        return []
    first = min((row['order'], row['originalOrder']) for row in choices)
    return [row for row in choices if (row['order'], row['originalOrder']) == first]
