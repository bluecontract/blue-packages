"""Receiver-specific prefix evidence; a producer's global READY state is irrelevant.

All reads occur in the attempt's coherent view. Positive retained history can
justify a prefix even while a newer producer turn is running. Negative facts
remain in the view's conflict set. No current-head alias replaces an exact
occurrence cursor.
"""
from .source_records import entries as source_entries
from blue_coordination_spec.model import require
from copy import deepcopy


def _facts(view):
    view._check()
    if not hasattr(view, '_projections'):
        view._projections = {}
    return view._projections


def sealed_position(view, instance):
    """Newest completely published history prefix, not an idle/READY test."""
    facts = _facts(view)
    key = ('sealed-prefix', instance)
    if key in facts:
        return deepcopy(facts[key])
    result = _sealed_position(view, instance)
    if len(facts) < 4096:
        facts[key] = deepcopy(result)
    return result


def _sealed_position(view, instance):
    point = ('positions', instance)
    already_read = point in view.points
    position = view.get(*point)
    if position is None:
        return None
    number = position.get('stableNumber')
    if number is None:
        # Read-compatible fallback for established histories from an explicitly
        # migrated store. Do not assume a provisional head is a sealed prefix.
        number = position['number']
        while number >= 0:
            row = view.get('history', instance + '/' + str(number).zfill(16))
            if row is not None and row['stable']:
                break
            number -= 1
    if number < 0:
        return None
    row = view.get('history', instance + '/' + str(number).zfill(16))
    require(row is not None and row['number'] == number and row['stable'],
            'WAITING_SOURCE_HISTORY', instance=instance)
    # This immutable row, not the moving discovery pointer, is the proof.
    # Later source commits cannot change it. Never erase someone else's read.
    if not already_read:
        view.points.pop(point, None)
    return row


def complete_through(engine, view, instance, key, *, inclusive=True, visiting=None):
    """Prove no unresolved source work through K (or strictly before K).

    A completed later position certifies its earlier prefix. Otherwise check
    original source coverage, examined input, attachment/rebase obligations and
    the exact next child predecessors. Leases and global worker status are not
    a positive readiness condition.
    """
    visiting = set() if visiting is None else visiting
    if not engine.optimized or 'prefix-reuse' in engine.disabled_optimizations:
        return _complete_through(engine, view, instance, key, inclusive=inclusive, visiting=visiting)
    facts = _facts(view)
    # A coherent view binds exact sources, positions, occurrence generations,
    # channel lifetimes and policy reads. No fact crosses a view/reservation
    # refresh. Include the traversal context: SCC shortcuts are path dependent.
    cache_key = ('complete-prefix', engine.context, instance, tuple(key), inclusive, frozenset(visiting))
    if cache_key in facts:
        result, visited = facts[cache_key]
        visiting.update(visited)
        engine.metrics['prefixFactHits'] = engine.metrics.get('prefixFactHits', 0) + 1
        return result
    result = _complete_through(engine, view, instance, key, inclusive=inclusive, visiting=visiting)
    if len(facts) < 4096:
        facts[cache_key] = result, frozenset(visiting)
    return result


def _complete_through(engine, view, instance, key, *, inclusive, visiting):
    if instance in visiting:
        return True  # Member of this captured dependency SCC, handled atomically.
    visiting.add(instance)
    sealed = sealed_position(view, instance)
    if sealed is None:
        return False
    effective = sealed.get('effectiveOrder')
    if effective is not None and tuple(effective) >= key:
        return True
    head = view.project('heads', instance, ('context', 'attachmentGoals', 'rebaseGoals',
                        'lastOrder', 'terminated', 'channels', 'sourceTimelines'))
    if head is None or head['context'] != engine.context:
        return False
    relevant = lambda order: order is None or (tuple(order) <= key if inclusive else tuple(order) < key)
    if any(relevant(g.get('activationOrder')) for g in head.get('attachmentGoals', {}).values()):
        return False
    if any(relevant(g['cutoff']) for g in head.get('rebaseGoals', [])):
        return False
    examined = tuple(head.get('lastOrder') or (-1, '', ''))
    covered = examined >= key
    if not covered and not head.get('terminated'):
        timelines = set(head.get('sourceTimelines', [r['timeline'] for r in head['channels']]))
        for actor in {r['actor'] for r in head['channels']}:
            timelines.update(r['timeline'] for _, r in view.scan(
                'authority_sources', engine.context + '/' + actor + '/'))
        # A strict full K may still have predecessors at the same timestamp.
        # Only the synthetic (timestamp, '', '') cut excludes all equal-time
        # occurrences and can use COMPLETE_BEFORE(timestamp) directly.
        required_before = key[0] + int(inclusive or bool(key[1]) or bool(key[2]))
        for timeline in sorted(timelines):
            source = view.get('sources', timeline)
            if source is None or source['before'] < required_before or view.get('source_issues', timeline):
                return False
            # Fetching one earliest row is sufficient. Check the complete K,
            # including the same-timestamp source/event tie-breaks.
            rows = source_entries(view, timeline, source, after=examined,
                                  before=(key[0] + 1, '', ''), limit=1)
            if rows and relevant((rows[0]['timestamp'], timeline, rows[0]['blue_id'])):
                return False
            view.pin_prefix(timeline, source)
    for _, edge in view.scan('forward', instance + '/'):
        source = edge['source']
        if source in visiting:
            continue
        selected = view.project('versions', engine.context + '/' + edge['selected'], ('number',))
        if selected is None:
            return False
        successor = view.get('history', source + '/' + str(selected['number'] + 1).zfill(16))
        if successor is not None and relevant(successor.get('effectiveOrder')):
            return False  # Source may be ready, but THIS consumer has not used it.
        if not complete_through(engine, view, source, key, inclusive=inclusive, visiting=visiting):
            return False
    return True
