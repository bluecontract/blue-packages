"""Recompute complete shared rows from actual authored documents, not expected roots."""
import hashlib
import json
from pathlib import Path
import unittest
import zipfile
from restore_reference import execute_fixture
from blue_language import Language

ROOT = Path(__file__).resolve().parents[2]


def fixture_context():
    with zipfile.ZipFile(ROOT / 'dist/package.bluepkg') as archive:
        package = json.loads(archive.read('package.json'))
        records = json.loads(archive.read('package-records.json'))
    types = {entry['name']: entry['blueId'] for entry in package['exports']}
    context = Language(core_contracts=False).processing_context()
    context.provider.update(records)
    context.aliases.update({'Contracts/' + name: tid for name, tid in types.items()})
    return context, types


class RestoreReferenceTests(unittest.TestCase):
    def test_shared_rows_are_independently_recomputed(self):
        document = json.loads(Path(__file__).with_name('restore-structural.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT / 'tools/restore_reference.py').read_bytes()).hexdigest(),
                         document['referenceSourceSha256'])
        for vector in document['vectors']:
            with self.subTest(vector=vector['id']):
                context, types = fixture_context()
                self.assertEqual(vector['expected'], execute_fixture(vector['input'], context, types))
