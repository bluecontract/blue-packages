"""Commission channels must reject irrelevant events before Compute dispatch."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class CommissionEventFiltersTest(unittest.TestCase):
    def test_channel_filters_preserve_each_existing_inner_guard(self):
        clause = yaml.safe_load((ROOT / 'clause-reseller/types/commission-clause.blue').read_text())
        expected = {
            'confirmed': {'type': 'Payment/Payment Event Received', 'event': {'type': 'PaymentInstruction/Payment Completed'}},
            'reversed': {'type': 'Payment/Payment Event Received', 'event': {'type': 'PaymentInstruction/Payment Reversed After Completion'}},
            # Each /payouts item is the provided payout Payment Instruction itself: both its payment events and
            # its operator split report (Account Settlement Confirmed) reconcile, so any event of an item counts.
            'observed': {'type': 'Events/Event'},
        }
        for action, pattern in expected.items():
            with self.subTest(action=action):
                source = clause['actions'][action]
                guard = source['do'][0]['$if']
                self.assertEqual({'$event': '/event'}, guard['cond']['$not']['$is']['node'])
                self.assertEqual(pattern, guard['cond']['$not']['$is']['pattern'])
                self.assertEqual([{'$return': {}}], guard['then'])
                self.assertEqual(pattern, source['automatic'].get('event'))
                self.assertEqual('collection', source['automatic']['on'])
                self.assertEqual('payouts' if action == 'observed' else 'orders', source['automatic']['pathBinding'])


if __name__ == '__main__':
    unittest.main()
