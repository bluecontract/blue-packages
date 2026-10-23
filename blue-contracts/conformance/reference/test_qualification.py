"""Bind current and historical external qualification to exact publication bytes."""
import hashlib
import json
from pathlib import Path
import unittest
import zipfile


class QualificationBindingTests(unittest.TestCase):
    def test_exact_publication_and_historical_coverage_are_preserved(self):
        root = Path(__file__).resolve().parents[3]
        profiles = (
            ('qualification.json', {
                'blue-contracts': 'blue-contracts/dist/package.bluepkg',
                'blue-coordination': 'blue-coordination/conformance/reference/retained/coordination-receiver-relative.8.bluepkg',
            }),
            ('qualification-source-transport.json', None),
        )
        for profile_name, retained in profiles:
            with self.subTest(profile=profile_name):
                profile = json.loads(Path(__file__).with_name(profile_name).read_text())
                self.assertEqual(set(profile['publications']), {'blue-contracts', 'blue-coordination'})
                for name, expected in profile['publications'].items():
                    archive = root / (retained[name] if retained is not None else name + '/dist/package.bluepkg')
                    with zipfile.ZipFile(archive) as package:
                        manifest = json.loads(package.read('package.json'))
                    self.assertEqual(manifest['packageBlueId'], expected['packageBlueId'])
                    self.assertEqual(manifest['protocol'], expected['protocolBlueId'])
                    self.assertEqual(manifest['semanticSpecifications'][manifest['protocol']]['rules']['blueId'],
                                     expected['rulesBlueId'])
                    self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), expected['archiveSha256'])
                    if retained is None:
                        self.assertEqual(manifest, json.loads((root / name / 'dist/package.json').read_text()))
        retained_archive = root / profiles[0][1]['blue-coordination']
        provenance = json.loads(retained_archive.with_suffix('.provenance.json').read_text())
        self.assertEqual(provenance['archive'], retained_archive.name)
        self.assertEqual(provenance['size'], retained_archive.stat().st_size)
        self.assertEqual(provenance['archiveSha256'], hashlib.sha256(retained_archive.read_bytes()).hexdigest())
        contracts = root / 'blue-contracts'
        self.assertEqual((contracts / 'conformance/reference/coverage.json').read_bytes(),
                         (contracts / 'dist/conformance/reference/coverage.json').read_bytes())
