import unittest
from decreasing_history_reference import prerequisite_order


class DecreasingHistoryReferenceTests(unittest.TestCase):
    def test_prior_version_terminates_return_to_same_lineage(self):
        rows = [dict(document='A30', lineage='A', order=30, dependencies=['B20']),
                dict(document='B20', lineage='B', order=20, dependencies=['A10']),
                dict(document='A10', lineage='A', order=10, dependencies=[])]
        self.assertEqual(prerequisite_order('A30', rows), ['A10', 'B20', 'A30'])
        with self.assertRaisesRegex(ValueError, 'WAIT_MISSING_ESTABLISHED_VERSION'):
            prerequisite_order('A30', rows[:2])

    def test_actual_established_versions_match_independent_walk(self):
        import hashlib
        import json
        from pathlib import Path
        vector = json.loads(Path(__file__).with_name('decreasing-vector.json').read_text())
        source = Path(__file__).resolve().parents[2] / 'tools/decreasing_history_reference.py'
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), vector['referenceSourceSha256'])
        self.assertEqual(prerequisite_order(**vector['input']), vector['expected'])
