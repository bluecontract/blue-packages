"""Verify native reuse and the boundary around the imported historical package."""
import hashlib
import json
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'clause-reseller'


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
        # Preserve the import receipt while explicitly identifying later authored changes.
        evolved = {
            'types/catalog-functions.blue': '8696fa79e07ee66a9dc423e8f06429de3f7eeaa4d57f3e99640a1091ca7ac5fd',
            'types/commercial-terms-validation-clause.blue': '6dbb1867f61143db14faee751046d964abd252abaacb77f262ddf1f217b8f14f',
            'types/commission-clause.blue': 'ae0b5bc12b8608903226edbf54f2701fda45909a611189f6ecaa0a8dc51f5f13',
            'types/customer-orders-clause.blue': '4399be172449010ab84cf7429029d1522cb86ddd4d3b25357bd48dd0df3d61f8',
            'types/fulfilment-terms-clause.blue': 'da0c1080d77202947491c49b3bad2bcc35338f1a789e5da1eb49b4d0c6200ba6',
            'types/order-functions.blue': '21c57248e318bba2c99bfed12ae88da515466cfd78bf571032def0d2dfb5296b',
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

    def test_only_the_three_corrected_examples_remove_customer_activation_approval(self):
        paths = sorted((PACKAGE / 'examples').glob('*/order-template.blue'))
        self.assertEqual(len(paths), 3)
        for path in paths:
            template = yaml.safe_load(path.read_text())
            self.assertEqual(template['clauses']['activation']['parameters']['required'], [])


if __name__ == '__main__':
    unittest.main()
