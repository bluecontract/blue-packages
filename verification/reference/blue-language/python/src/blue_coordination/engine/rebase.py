"""Q18: independent examined prefixes for newly activated channel lifetimes.

The activation entry is a boundary, never a retroactive external seed. Entries
strictly before it are offered only to the new lifetimes. Existing checkpoints
and the document's LIVE high-water mark remain untouched.
"""
from copy import deepcopy
from blue_coordination_spec.model import Entry, require
from .source_records import entries as source_entries


def key(row):
    return (row['member'], row['channel'], row['generation'])


def pending(view, goals):
    """Return remaining goals and the least original cause, with coverage."""
    remaining, candidates = [], {}
    for goal in goals:
        cursor = tuple(goal.get('cursor') or (-1, '', ''))
        cutoff = tuple(goal['cutoff'])
        sources = {t: view.get('sources', t) for t in goal['timelines']}
        if any(s is None or s['before'] <= cutoff[0] for s in sources.values()):
            remaining.append(goal)
            continue
        entries = [Entry(**raw) for timeline,source in sources.items() for raw in
                   source_entries(view,timeline,source,after=cursor,before=cutoff,limit=1)]
        if entries:
            remaining.append(goal)
            for entry in entries: candidates[entry.blue_id] = entry
    # Missing coverage on one new source must not permit a later known cause.
    for goal in remaining:
        for timeline in goal['timelines']:
            source = view.get('sources', timeline)
            require(source is not None, 'WAITING_SOURCE_PROVIDER', timeline=timeline)
            require(source['before'] > goal['cutoff'][0], 'WAITING_HISTORY_COMPLETENESS',
                    timeline=timeline, before=source['before'], activation=goal['cutoff'])
            require(view.get('source_issues', timeline) is None, 'SOURCE_INTEGRITY_FAILURE', timeline=timeline)
    selected = min(candidates.values(), key=lambda e:e.order) if candidates else None
    return remaining, selected


def activate(view, context, old, rows, member, activation, *, progressed=None):
    live = {key(r) for r in rows if r['member'] == member}
    goals = [deepcopy(g) for g in (progressed if progressed is not None else (old or {}).get('rebaseGoals', []))
             if key(g) in live]
    if old is None or activation is None:
        return goals
    previous = {key(r) for r in old['channels'] if r['member'] == member}
    existing = {key(g) for g in goals}
    for row in rows:
        if row['member'] != member or key(row) in previous | existing:
            continue
        timelines = {row['timeline']}
        timelines.update(r['timeline'] for _, r in view.scan('authority_sources', context+'/'+row['actor']+'/'))
        goal = dict(member=member, channel=row['channel'], generation=row['generation'],
                    timelines=sorted(timelines), cutoff=list(activation), cursor=None)
        # Avoid an unnecessary unstable position when the complete empty prefix
        # is already known. Missing evidence remains a durable obligation.
        sources = [view.get('sources', t) for t in timelines]
        if any(s is None or s['before'] <= activation[0] for s in sources) or any(
            source_entries(view,t,view.get('sources',t),before=activation,limit=1) for t in timelines):
            goals.append(goal)
    return goals
