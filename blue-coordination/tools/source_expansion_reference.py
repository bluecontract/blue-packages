"""Bounded source-expansion scheduling over native-authenticated premises.

Anchor and transition identities are supplied verified identities, not hashes
invented by this model. This does not verify signatures, authorize an actor,
construct a Contracts receipt, or qualify the complete receiver implementation.
"""
from copy import deepcopy


def _order(k):
    return (k[0], k[1].encode('utf-16-be'), k[2].encode('utf-16-be'))


def _lifetime(value):
    return (value[0].encode('utf-16-be'), value[1].encode('utf-16-be'), value[2])


def empty():
    return {'anchors': [], 'slices': [], 'terminal': [], 'transitions': []}



def discover_initial_source(state, source):
    """A absent: existing raw INITIAL rule, not a source-expansion anchor.

Receiver rules §3 require null initial progress and inclusive Kbirth. The
source-discovery branch in §4 reuses that bound; it creates no new lifetime,
anchor or terminal fact. Authentication remains an input premise.
"""
    out = deepcopy(state)
    initial = out['initial']
    if initial['examined'] is not None:
        raise ValueError('EXAMINED_FRONTIER_REQUIRES_EXPANSION')
    if initial.get('birthOrder') is None:
        raise ValueError('MISSING_INITIAL_BOUND')
    initial['sourceCursors'].setdefault(source, None)
    return out


def expand(state, anchor):
    """Append a verified anchor; source subscriptions publish with this state."""
    out = deepcopy(state)
    previous = out['anchors'][-1]['id'] if out['anchors'] else None
    if anchor['previous'] != previous:
        raise ValueError('DISCONTIGUOUS_CONTINUATION')
    if any(row['id'] == anchor['id'] for row in out['anchors']):
        raise ValueError('REUSED_ANCHOR')
    if anchor['A'] is None:
        raise ValueError('INITIAL_SOURCE_DISCOVERY_NOT_EXPANSION')
    visibility = [anchor['effectiveOrder']] + [s['V'] for s in out['slices']]
    if out.get('initial') is not None:
        visibility.append(out['initial']['visibility'])
    causal_orders = [order for order in visibility if order is not None]
    if anchor['V'] != max(causal_orders, key=_order, default=None):
        raise ValueError('INCORRECT_CAUSAL_VISIBILITY')
    if not anchor['receipt'] or anchor['position'] is None:
        raise ValueError('MISSING_ESTABLISHED_ANCHOR')
    sources = anchor['sources']
    lifetimes = anchor['lifetimes']
    if len(sources) != len(set(sources)) or len(lifetimes) != len({tuple(v) for v in lifetimes}):
        raise ValueError('DUPLICATE_EXPANSION_SCOPE')
    out['anchors'].append(deepcopy(anchor))
    for lifetime in sorted(lifetimes, key=_lifetime):
        for source in sorted(sources, key=lambda s: s.encode('utf-16-be')):
            out['slices'].append({'id': [anchor['id'], list(lifetime), source],
                                  'lifetime': list(lifetime), 'source': source,
                                  'anchor': anchor['id'], 'A': anchor['A'],
                                  'V': anchor['V'], 'examined': None})
    return out


def next_turn(state, entries, complete_sources, activation=()):
    """Choose full K only after applicable prefix completeness is established.

`activation` contains already eligible native activation candidates with K and
lifetime. They share ordering; their phase-specific cursor is not edited here.
"""
    if any(row['K'][1] != row['source'] for row in entries):
        raise ValueError('SOURCE_ORDER_MISMATCH')
    if len({tuple(row['K']) for row in entries}) != len(entries):
        raise ValueError('DUPLICATE_SOURCE_ENTRY')
    candidates = []
    for s in state['slices']:
        covered = complete_sources.get(s['source'])
        if covered is None or covered <= s['A'][0]:
            return {'status': 'WAIT', 'source': s['source']}
        available = [row for row in entries if row['source'] == s['source']
                     and _order(row['K']) < _order(s['A'])
                     and (s['examined'] is None or _order(row['K']) > _order(s['examined']))]
        if available:
            row = min(available, key=lambda v: _order(v['K']))
            candidates.append({'K': row['K'], 'lifetime': s['lifetime'], 'slice': s['id']})
    candidates.extend({'K': row['K'], 'lifetime': row['lifetime'], 'slice': None} for row in activation)
    if not candidates:
        return {'status': 'CAUGHT_UP'}
    first = min(candidates, key=lambda row: (_order(row['K']), _lifetime(row['lifetime'])))
    selected = [row for row in candidates if row['K'] == first['K']]
    lifetimes = sorted({tuple(row['lifetime']) for row in selected}, key=_lifetime)
    deliveries = [list(lifetime) for lifetime in lifetimes
                  if [list(lifetime), first['K'][2]] not in state['terminal']]
    return {'status': 'TURN', 'K': first['K'], 'slices': [row['slice'] for row in selected if row['slice'] is not None],
            'lifetimes': deliveries}


def settle(state, turn, decisions, transition):
    """Consume native terminal decisions at original K, never at A or V."""
    if turn['status'] != 'TURN':
        raise ValueError('NO_SELECTED_TURN')
    by_lifetime = {tuple(row['lifetime']): row for row in decisions}
    if len(by_lifetime) != len(decisions) or set(by_lifetime) != {tuple(v) for v in turn['lifetimes']}:
        raise ValueError('INCOMPLETE_OR_DUPLICATE_DECISIONS')
    for row in decisions:
        if row['authorityK'] != turn['K']:
            raise ValueError('AUTHORITY_NOT_AT_ORIGINAL_K')
        if row['status'] not in ('APPLIED', 'DENIED', 'NO_MATCH', 'WAIT'):
            raise ValueError('UNSUPPORTED_DECISION')
    if any(row['status'] == 'WAIT' for row in decisions):
        return deepcopy(state)
    if not transition or transition in state['transitions']:
        raise ValueError('MISSING_OR_REUSED_TRANSITION')
    out = deepcopy(state)
    for s in out['slices']:
        if s['id'] in turn['slices']:
            s['examined'] = turn['K']
    for lifetime in turn['lifetimes']:
        out['terminal'].append([lifetime, turn['K'][2]])
    out['transitions'].append(transition)
    if out.get('initial') is not None:
        out['initial']['links'].append({'phase': 'SOURCE_EXPANSION', 'transition': transition})
    return out
