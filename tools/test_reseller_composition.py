"""Guard the native Documents lifecycle seam used by the reseller constructor."""
import copy
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class ResellerCompositionTest(unittest.TestCase):
    def test_preparation_retains_native_lifecycle(self):
        native = yaml.safe_load((ROOT / 'clause-documents/types/preparation-functions.blue').read_text())
        reseller = yaml.safe_load((ROOT / 'clause-reseller/types/customer-orders-clause.blue').read_text())
        expected = copy.deepcopy(native['functions']['sharedPrepare'])
        replacements = 0

        def adapt(value):
            nonlocal replacements
            if isinstance(value, dict):
                if value.get('function') == 'constructDocument':
                    value['function'] = 'constructOrder'
                    replacements += 1
                for child in value.values():
                    adapt(child)
            elif isinstance(value, list):
                for child in value:
                    adapt(child)

        adapt(expected)
        self.assertEqual(1, replacements)
        self.assertEqual(expected, reseller['actionDefinition']['type']['functions']['sharedPrepareOrder'])

    def test_examples_request_independent_bootstrap_without_customer_approval(self):
        examples = list((ROOT / 'examples/reseller').glob('*-preview.blue'))
        self.assertEqual(3, len(examples))
        for path in examples:
            with self.subTest(example=path.name):
                source = yaml.safe_load(path.read_text())
                self.assertNotIn('quotes', source)
                self.assertNotIn('quote', source['clauses']['catalog']['bindings'])
                self.assertEqual('/products', source['clauses']['orders']['bindings']['catalog'])
                self.assertNotIn('startOrder', source['clauses']['orders']['bindings'])
                order = source['orderTemplate']['clauses']
                self.assertEqual([], order['activation']['parameters']['required'])
                self.assertEqual('bootstrap', order['payment']['parameters']['prepareFor'])
                self.assertEqual(['guarantor'], order['payment']['parameters']['suppliedParties'])
                self.assertNotIn('guarantor', order['payment']['bindings']['parties'])
                guarantor = order['payment']['parameters']['template']['clauses']['activation']['parameters']['parties']['guarantor']
                self.assertEqual('payments@example.test', guarantor['email'])
                self.assertEqual('timer', order['payment']['bindings']['prepare']['onOrderCreated']['on'])
