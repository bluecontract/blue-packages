"""Independent bounded source-expansion decisions; not native qualification."""
import json
import unittest
from source_expansion_reference import empty, expand, next_turn, settle, discover_initial_source


K50 = [50, 'agent', 'entry50']
K100 = [100, 'seller', 'entry100']
K200 = [200, 'agent', 'entry200']
LIFETIME = ['root', 'seller', 1]


def anchor(identity='a1', previous=None, source='agent'):
    return {'id': identity, 'previous': previous, 'receipt': 'established-receipt100',
            'position': 1, 'A': K100, 'effectiveOrder': K100, 'V': K100,
            'sources': [source], 'lifetimes': [LIFETIME]}


def decision(turn, status):
    return [{'lifetime': lifetime, 'authorityK': turn['K'], 'status': status}
            for lifetime in turn['lifetimes']]


class SourceExpansionTests(unittest.TestCase):
    def test_denial_progress_and_restart_reach_later_ordinary_boundary(self):
        state = expand(empty(), anchor())
        entries = [{'source': 'agent', 'K': K50}, {'source': 'agent', 'K': K200}]
        turn = next_turn(state, entries, {'agent': 201})
        self.assertEqual(turn['K'], K50)
        self.assertEqual(turn['lifetimes'], [LIFETIME])
        uninterrupted = settle(state, turn, decision(turn, 'DENIED'), 'denial50')
        reopened = json.loads(json.dumps(state))
        resumed_turn = next_turn(reopened, entries, {'agent': 201})
        resumed = settle(reopened, resumed_turn, decision(resumed_turn, 'DENIED'), 'denial50')
        self.assertEqual(uninterrupted, resumed)
        self.assertEqual(resumed['slices'][0]['examined'], K50)
        self.assertEqual(next_turn(resumed, entries, {'agent': 201}), {'status': 'CAUGHT_UP'})
        # K200 was not consumed by the strictly-before-A expansion; ordinary
        # processing still owns it. No Contracts completion was fabricated.
        self.assertNotIn([LIFETIME, K200[2]], resumed['terminal'])

    def test_missing_prefix_or_required_premise_does_not_advance(self):
        state = expand(empty(), anchor())
        entries = [{'source': 'agent', 'K': K50}]
        self.assertEqual(next_turn(state, entries, {}), {'status': 'WAIT', 'source': 'agent'})
        self.assertEqual(next_turn(state, entries, {'agent': 100}), {'status': 'WAIT', 'source': 'agent'})
        turn = next_turn(state, entries, {'agent': 201})
        self.assertEqual(settle(state, turn, decision(turn, 'WAIT'), None), state)
        wrong_time = decision(turn, 'APPLIED')
        wrong_time[0]['authorityK'] = K100
        with self.assertRaisesRegex(ValueError, 'ORIGINAL_K'):
            settle(state, turn, wrong_time, 'bad')

    def test_repeated_expansion_preserves_cursor_and_deduplicates_lifetime_entry(self):
        state = expand(empty(), anchor())
        entries = [{'source': 'agent', 'K': K50}]
        turn = next_turn(state, entries, {'agent': 201})
        state = settle(state, turn, decision(turn, 'APPLIED'), 'completion50')
        later = expand(state, anchor('a2', 'a1'))
        self.assertEqual(later['slices'][0]['examined'], K50)
        self.assertIsNone(later['slices'][1]['examined'])
        repeated = next_turn(later, entries, {'agent': 201})
        self.assertEqual(repeated['lifetimes'], [])
        settled = settle(later, repeated, [], 'examined-existing50')
        self.assertEqual(settled['terminal'], [[LIFETIME, K50[2]]])
        self.assertEqual([s['examined'] for s in settled['slices']], [K50, K50])
        self.assertEqual([a['id'] for a in settled['anchors']], ['a1', 'a2'])
        with self.assertRaisesRegex(ValueError, 'DISCONTIGUOUS'):
            expand(settled, anchor('a3', 'a1'))

    def test_new_source_keeps_independent_cursor_and_orders_with_activation(self):
        state = expand(empty(), anchor())
        turn = next_turn(state, [{'source': 'agent', 'K': K50}], {'agent': 201})
        state = settle(state, turn, decision(turn, 'NO_MATCH'), 'nomatch50')
        state = expand(state, anchor('a2', 'a1', 'second-agent'))
        earlier = [10, 'second-agent', 'entry10']
        entries = [{'source': 'second-agent', 'K': earlier}]
        activation = [{'K': [5, 'third', 'entry5'], 'lifetime': ['root', 'other', 1]}]
        selected = next_turn(state, entries, {'agent': 201, 'second-agent': 201}, activation)
        self.assertEqual(selected['K'][0], 5)
        self.assertEqual(selected['slices'], [])
        selected = next_turn(state, entries, {'agent': 201, 'second-agent': 201})
        self.assertEqual(selected['K'], earlier)
        result = settle(state, selected, decision(selected, 'APPLIED'), 'completion10')
        self.assertEqual([s['examined'] for s in result['slices']], [K50, earlier])

    def test_initial_cursor_is_not_expansion_progress_after_restart(self):
        for status in ('APPLIED', 'DENIED', 'NO_MATCH'):
            with self.subTest(status=status):
                state = empty()
                state['initial'] = {'examined': K100, 'sourceCursors': {'seller': K100},
                                    'visibility': K200, 'links': []}
                a = anchor()
                a['V'] = K200
                state = expand(state, a)
                turn = next_turn(state, [{'source': 'agent', 'K': K50}], {'agent': 201})
                result = settle(state, turn, decision(turn, status), 'expansion50')
                restored = json.loads(json.dumps(result))
                self.assertEqual(restored['initial']['examined'], K100)
                self.assertEqual(restored['initial']['sourceCursors'], {'seller': K100})
                self.assertEqual(restored['initial']['links'],
                                 [{'phase': 'SOURCE_EXPANSION', 'transition': 'expansion50'}])
                self.assertIn('expansion50', restored['transitions'])
                self.assertEqual(restored['slices'][0]['examined'], K50)
                self.assertEqual(settle(state, turn, decision(turn, 'WAIT'), None), state)

    def test_absent_frontier_adds_source_to_existing_initial_birth_bound(self):
        state = empty()
        state['initial'] = {'examined': None, 'birthOrder': K100,
                            'sourceCursors': {'seller': None},
                            'visibility': K100, 'links': []}
        result = discover_initial_source(state, 'agent')
        self.assertEqual(result['initial']['birthOrder'], K100)
        self.assertIsNone(result['initial']['examined'])
        self.assertEqual(result['initial']['sourceCursors'], {'seller': None, 'agent': None})
        self.assertEqual(result['anchors'], [])
        self.assertEqual(result['slices'], [])
        self.assertEqual(result['terminal'], [])
        self.assertEqual(discover_initial_source(json.loads(json.dumps(result)), 'agent'), result)
        result['initial']['examined'] = K50
        with self.assertRaisesRegex(ValueError, 'REQUIRES_EXPANSION'):
            discover_initial_source(result, 'another-agent')

    def test_original_frontier_can_exist_without_causal_visibility(self):
        # Native 7755: shared NO_MATCH advances A, but initialization has no
        # native effectiveOrder. A and V are independent authenticated facts.
        first = anchor()
        first.update(A=[20, 'seller', 'nomatch20'], effectiveOrder=None, V=None)
        state = expand(empty(), first)
        self.assertIsNone(state['anchors'][0]['V'])
        older = [10, 'agent', 'entry10']
        turn = next_turn(state, [{'source': 'agent', 'K': older}], {'agent': 21})
        self.assertEqual(turn['K'], older)
        resumed = json.loads(json.dumps(state))
        self.assertEqual(settle(resumed, turn, decision(turn, 'NO_MATCH'), 'nomatch10'),
                         settle(state, turn, decision(turn, 'NO_MATCH'), 'nomatch10'))
        later = anchor('a2', 'a1', 'second-agent')
        later.update(A=[20, 'seller', 'nomatch20'], effectiveOrder=[5, 'seller', 'effect5'],
                     V=[5, 'seller', 'effect5'])
        state = expand(state, later)
        self.assertEqual(state['slices'][1]['V'], later['V'])
        inherited = anchor('a3', 'a2', 'third-agent')
        inherited.update(effectiveOrder=None, V=later['V'])
        self.assertEqual(expand(state, inherited)['slices'][-1]['V'], later['V'])
