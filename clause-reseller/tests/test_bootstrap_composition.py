"""Verify native reuse and the boundary around the imported historical package."""
import hashlib
import json
from pathlib import Path
import unittest
import zipfile
import yaml

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'clause-reseller'


def records(path):
    with zipfile.ZipFile(path) as archive:
        return json.loads(archive.read('package-records.json'))


class BootstrapCompositionTest(unittest.TestCase):
    def test_selected_catalogue_contains_the_exact_reseller_dependency_closure(self):
        sources = json.loads((ROOT / 'PACKAGE-SOURCES.json').read_text())
        self.assertIn('clause-reseller', sources['packages'])
        catalogue = json.loads((ROOT / 'PACKAGES.json').read_text())
        selected = {row['packageBlueId']: row for row in catalogue['packages']}
        metadata = json.loads((PACKAGE / 'dist/package.json').read_text())
        self.assertIn(metadata['packageBlueId'], selected)
        lock = json.loads((PACKAGE / 'blue-package.lock.json').read_text())
        for dependency in lock['imports'].values():
            row = selected[dependency['packageBlueId']]
            self.assertEqual(row['archiveSha256'], dependency['archiveSha256'])
        for name in ('SHARED-PACKAGES.json', 'PAYMENT-FAMILY-PACKAGES.json'):
            consumer = json.loads((ROOT / name).read_text())
            self.assertIn(metadata['packageBlueId'],
                          {row['packageBlueId'] for row in consumer['packages']})

    def test_import_provenance_and_explicitly_evolved_sources(self):
        source = json.loads((PACKAGE / 'source-import.json').read_text())
        self.assertEqual(len(source['sourceFiles']), 14)
        # Historical provenance remains immutable. These three authored sources
        # evolved deliberately: main's optional quotes/catalog bootstrap and the
        # qualified guarded commission attachment. All other imports stay exact.
        evolved = {
            'types/catalog-functions.blue': '0f24eab9c459cd2f58baec2d383ddf3337517554be84417d308c64514126f1eb',
            'types/customer-orders-clause.blue': 'c77ddfc0332a33026c1b21dab7563136b6c0899d6051e0dd9d5a9c1449e7a091',
            'types/commission-clause.blue': '326f5b14bd84fbe4d1284a85e3f56450a97acea3a25018856427941cb40861f9',
        }
        seen = set()
        for item in source['sourceFiles']:
            relative = Path(item['path']).relative_to('sources/clause-reseller')
            path = PACKAGE / relative
            key = relative.as_posix()
            if key in evolved:
                self.assertNotEqual(evolved[key], item['sha256'])
                seen.add(key)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                             evolved.get(key, item['sha256']), str(path))
        self.assertEqual(seen, set(evolved))

    def test_generic_lifecycle_uses_exact_existing_native_function_nodes(self):
        composition = json.loads((PACKAGE / 'bootstrap-composition.json').read_text())
        definitions = records(ROOT / 'clause-documents/dist/package.bluepkg')
        clause = yaml.safe_load((PACKAGE / 'types/customer-orders-bootstrap-clause.blue').read_text())
        functions = clause['actionDefinition']['type']['functions']
        for name, reference in composition['functions'].items():
            self.assertEqual(functions[name], reference, name)
            self.assertIn(reference['blueId'], definitions, name)
        for name in ['checkProvision', 'sharedProvide', 'validateProviderSlots',
                     'validateBootstrapAccess', 'requireSameBootstrapParty',
                     'normalizeProvisionSource', 'sharedPrepare', 'prepareMappedChild',
                     'mappedBootstrapPartyCovered']:
            self.assertIn(name, composition['functions'])
        self.assertEqual(len(composition['functions']), 106)

    def test_domain_helpers_retain_exact_native_identities(self):
        composition = json.loads((PACKAGE / 'bootstrap-composition.json').read_text())
        definitions = records(PACKAGE / 'dist/package.bluepkg')
        clause = yaml.safe_load((PACKAGE / 'types/customer-orders-bootstrap-clause.blue').read_text())
        for name, reference in composition['domainFunctionReferences'].items():
            function = clause['actionDefinition']['type']['functions'][name]
            if name == 'prepareBooking':
                # Native identity equality for this private quote-based body is
                # enforced by ResellerBootstrapFunctionPinsConformance.
                self.assertEqual({'args', 'do'}, set(function))
                self.assertIn('quoteKey', json.dumps(function))
                self.assertNotIn('catalogRevision', json.dumps(function))
            else:
                self.assertEqual(function, reference)
            self.assertIn(reference['blueId'], definitions)
        self.assertEqual(set(composition['customFunctions']), {
            'constructDocument', 'prepareCustomerOrder', 'domainPrepare',
            'domainValidateCandidate', 'domainNextActions', 'suppliedCustomerOrderRoles',
            'maySelectInactiveCandidate'})

    def test_ordinary_provision_and_planning_are_not_replaced(self):
        clause = yaml.safe_load((PACKAGE / 'types/customer-orders-bootstrap-clause.blue').read_text())
        base = yaml.safe_load((ROOT / 'clause-documents/types/base.blue').read_text())
        for action in ['provide', 'resume', 'cancel']:
            self.assertEqual(clause['actions'][action], base['actions'][action])
        self.assertEqual(clause['hookDefinition'], base['hookDefinition'])
        self.assertEqual(clause['actions']['prepare'], clause['actions']['startOrder'])

    def test_only_the_three_corrected_examples_remove_customer_activation_approval(self):
        paths = sorted((PACKAGE / 'examples').glob('*/order-template.blue'))
        self.assertEqual(len(paths), 3)
        for path in paths:
            template = yaml.safe_load(path.read_text())
            self.assertEqual(template['clauses']['activation']['parameters']['required'], [])
        clause = yaml.safe_load((PACKAGE / 'types/customer-orders-bootstrap-clause.blue').read_text())
        constructor = clause['actionDefinition']['type']['functions']['constructDocument']
        text = json.dumps(constructor)
        self.assertNotIn('/parameters/required', text)
        self.assertNotIn('"required":', text)


if __name__ == '__main__':
    unittest.main()
