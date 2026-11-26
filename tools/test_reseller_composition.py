"""Guard the native Documents lifecycle seam used by the reseller constructor."""
import json
from pathlib import Path
import unittest
from zipfile import ZipFile
import yaml

ROOT = Path(__file__).resolve().parents[1]


class ResellerCompositionTest(unittest.TestCase):
    def test_provision_retains_native_validation_and_effects(self):
        native = yaml.safe_load((ROOT / 'clause-documents/types/base.blue').read_text())
        reseller = yaml.safe_load((ROOT / 'clause-reseller/types/customer-orders-clause.blue').read_text())
        expected = native['actions']['provide']
        actual = reseller['actions']['provideOrder']
        self.assertEqual(expected['preflight'], actual['preflight'][:1])
        self.assertEqual(expected['defaults'], actual['defaults'])
        self.assertEqual(expected['do'], actual['do'])

    def test_preparation_retains_native_lifecycle(self):
        package = ROOT / 'clause-reseller'
        lock = json.loads((package / 'blue-package.lock.json').read_text())
        documents = package / lock['imports']['Documents']['path']
        preparation, documents_records = self.exact_export(documents, 'Documents/Preparation Functions')
        reseller, reseller_records = self.exact_export(
            package / 'dist/package.bluepkg', 'Reseller/Customer Orders Clause')
        action_definition = self.exact_record(reseller_records, reseller['actionDefinition']['type'])
        expected = self.exact_record(documents_records, preparation['functions']['sharedPrepare'])
        actual = self.exact_record(reseller_records, action_definition['functions']['sharedPrepareOrder'])
        replacements = 0

        def adapt(value):
            nonlocal replacements
            if isinstance(value, dict):
                function = value.get('function')
                if isinstance(function, dict) and function.get('value') == 'constructDocument':
                    function['value'] = 'constructOrder'
                    replacements += 1
                for child in value.values():
                    adapt(child)
            elif isinstance(value, list):
                for child in value:
                    adapt(child)

        adapt(expected)
        self.assertEqual(1, replacements)
        self.assertEqual(expected, actual)

    @staticmethod
    def exact_record(records, node):
        if set(node) != {'blueId'}:
            return node
        record = records[node['blueId']]
        if record['mode'] != 'exact':
            raise AssertionError('Expected exact published record')
        return json.loads(record['text'])

    def exact_export(self, path, alias):
        with ZipFile(path) as archive:
            manifest = json.loads(archive.read('package.json'))
            records = json.loads(archive.read('package-records.json'))
        export, = [row for row in manifest['exports'] if row['alias'] == alias]
        return self.exact_record(records, {'blueId': export['blueId']}), records

    def test_current_clause_exports_retire_stored_quote_checkout(self):
        package = ROOT / 'clause-reseller'
        manifest = yaml.safe_load((package / 'blue-package.yaml').read_text())
        exports = {definition['name']: definition['path'] for definition in manifest['exports']}
        self.assertNotIn('Customer Orders Bootstrap Clause', exports)
        fulfilment = yaml.safe_load((package / exports['Fulfilment Terms Clause']).read_text())
        self.assertNotIn('place', fulfilment['actions'])
        self.assertIn('approveAvailability', fulfilment['actions'])
        order_functions = yaml.safe_load((package / exports['Order Functions']).read_text())
        self.assertNotIn('placeOrder', order_functions['functions'])
        catalogue = yaml.safe_load((package / exports['Catalog Clause']).read_text())
        self.assertIn('quote', catalogue['actions'])

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
                self.assertEqual('initialized', order['payment']['bindings']['prepare']['onOrderCreated']['on'])
