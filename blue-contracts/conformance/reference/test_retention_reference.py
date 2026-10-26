import hashlib
import json
from pathlib import Path
import unittest
from retention_reference import derive_records
from restore_reference import derive_restore_obligations
from algorithms import blue as L
from test_restore_reference import fixture_context


class DerivedRetentionTests(unittest.TestCase):
    def test_authored_graph_derives_exact_required_records(self):
        vector = json.loads(Path(__file__).with_name('retention-vectors.json').read_text())
        root = Path(__file__).resolve().parents[2]
        for path, digest in vector['referenceSources'].items():
            self.assertEqual(hashlib.sha256((root / path).read_bytes()).hexdigest(), digest)
        for row in vector['vectors']:
            context, types = fixture_context()
            actual = derive_records(row['input'], context, types)
            self.assertEqual(actual, row['expected'], row['id'])
            self.assertNotIn('FLuyvQ2oZFQENdGNuNCY2MmUzfyrDbLCRwVmeeG8LqD9', actual['records'])
            cold, cold_types = fixture_context()
            cold.provider.update(actual['records'])
            restored = derive_restore_obligations({key: L.Ref(identity) for key, identity in actual['members'].items()},
                row['input']['edges'], cold, cold_types)
            self.assertEqual(restored['paths'], actual['paths'])
