import unittest
from receiver_reference import Before, classify_operation, replay_frontier, next_activation


class ReceiverTests(unittest.TestCase):
    def test_operation_decisions_do_not_use_global_cached_targets(self):
        import json
        from pathlib import Path
        data = json.loads(Path(__file__).with_name('vectors.json').read_text())
        row = data['pre']
        pre = Before(row['current'], frozenset(row['ownPast']), frozenset(row['foreign']), row['complete'])
        for vector in data['vectors']:
            with self.subTest(vector=vector):
                self.assertEqual(classify_operation(vector['target'], vector['exact'], pre), vector['expected'])
        incomplete = Before('now', pre.own_past, pre.foreign, False)
        self.assertEqual(classify_operation('foreign', True, incomplete), 'WAIT_PRE_HISTORY')

    def test_full_order_ties_birth_once_and_activation_strict_bound(self):
        earlier, birth, later = (10, 'a'), (10, 'b'), (10, 'c')
        entries = (later, birth, earlier)
        self.assertEqual(replay_frontier('INITIAL', birth, entries), (earlier, birth))
        self.assertEqual(replay_frontier('INITIAL', birth, entries, (earlier, birth)), ())
        self.assertEqual(replay_frontier('ACTIVATION', birth, entries), (earlier,))
        self.assertEqual(replay_frontier('ACTIVATION', earlier, entries), ())

    def test_equal_order_activation_uses_member_channel_generation(self):
        a, b = ((10, 'b'), 'member', 'channel', 1), ((10, 'b'), 'member', 'channel', 2)
        self.assertEqual(next_activation((b, a)), a)

    def test_attachment_rejects_future_initialized_position(self):
        from receiver_reference import attachment_goal
        source = ((1, 'a'), (2, 'b'), (3, 'c'))
        self.assertEqual(attachment_goal(source, (3, 'c'), (1, 'a')),
                         ((2, 'b'), ((2, 'b'),)))
        with self.assertRaisesRegex(ValueError, 'BEYOND_ATTACHMENT_GOAL'):
            attachment_goal(source, (3, 'c'), (3, 'c'))
        with self.assertRaisesRegex(ValueError, 'MISSING_SOURCE_PREDECESSOR'):
            attachment_goal(source, (3, 'c'), (1, 'unknown'))

    def test_reattachment_does_not_inherit_retired_receiving_position(self):
        from receiver_reference import occurrence_receiving
        source = ((1, 'a'), (2, 'b'))
        received = {('member', 'channel', 1, position) for position in source}
        self.assertEqual(occurrence_receiving(source, received, 'member', 'channel', 1), ())
        self.assertEqual(occurrence_receiving(source, received, 'member', 'channel', 2), source)

class DependencyTests(unittest.TestCase):
    def test_decreasing_history_is_not_collapsed_to_document_visited_flag(self):
        from receiver_reference import HistoryKey as K, HistoryPremise as P, settle_dependencies
        a30, b20, a10 = K('A', (30,), 'BEFORE'), K('B', (20,), 'BEFORE'), K('A', (10,), 'BEFORE')
        facts = {a30: P('a30', ((b20, 'b20'),)), b20: P('b20', ((a10, 'a10'),)), a10: P('a10')}
        self.assertEqual(settle_dependencies(a30, facts)['status'], 'ESTABLISHED')
        del facts[a10]
        self.assertEqual(settle_dependencies(a30, facts), {'status': 'WAIT', 'obligations': (a10,)})

    def test_unresolved_cycle_does_not_prove_success_or_contradiction(self):
        from receiver_reference import HistoryKey as K, HistoryPremise as P, settle_dependencies
        a, b = K('A', (30,), 'BEFORE'), K('B', (30,), 'BEFORE')
        facts = {a: P('a', ((b, 'b'),), pre_view_established=False),
                 b: P('b', ((a, 'a'),), pre_view_established=False)}
        self.assertEqual(settle_dependencies(a, facts)['status'], 'WAIT')
        proved = {a: P('a', ((b, 'b'),), pre_view_established=False, closed_impossible_creation=True),
                  b: P('b', ((a, 'a'),), pre_view_established=False, closed_impossible_creation=True)}
        self.assertEqual(settle_dependencies(a, proved)['status'], 'INVALID_CAUSAL_HISTORY')
        live = {a: P('a', ((b, 'b'),)), b: P('b', ((a, 'a'),))}
        self.assertEqual(settle_dependencies(a, live)['status'], 'COMPONENT_READY')
        conflicting = {a: P('a', ((b, 'b'),)), b: P('b', ((a, 'wrong-version'),))}
        with self.assertRaisesRegex(ValueError, 'INCOMPATIBLE_EXPECTED'):
            settle_dependencies(a, conflicting)
