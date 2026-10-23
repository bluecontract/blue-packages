"""Bind external qualification to the selected immutable publication inputs."""
import hashlib
import json
from pathlib import Path
import unittest


class QualificationBindingTests(unittest.TestCase):
    def test_exact_publication_and_historical_coverage_are_preserved(self):
        root = Path(__file__).resolve().parents[3]
        profile = json.loads(Path(__file__).with_name('qualification.json').read_text())
        for name, expected in profile['publications'].items():
            package = root / name
            manifest = json.loads((package / 'dist/package.json').read_text())
            self.assertEqual(manifest['packageBlueId'], expected['packageBlueId'])
            self.assertEqual(manifest['protocol'], expected['protocolBlueId'])
            self.assertEqual(manifest['semanticSpecifications'][manifest['protocol']]['rules']['blueId'],
                             expected['rulesBlueId'])
            self.assertEqual(hashlib.sha256((package / 'dist/package.bluepkg').read_bytes()).hexdigest(),
                             expected['archiveSha256'])
        contracts = root / 'blue-contracts'
        self.assertEqual((contracts / 'conformance/reference/coverage.json').read_bytes(),
                         (contracts / 'dist/conformance/reference/coverage.json').read_bytes())
