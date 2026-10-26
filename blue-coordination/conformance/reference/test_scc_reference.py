import unittest
from scc_reference import components


class SccReferenceTests(unittest.TestCase):
    def test_mutual_reachability_does_not_merge_one_way_dependencies(self):
        self.assertEqual(components(['a', 'b', 'c'], [('a', 'b'), ('b', 'a'), ('b', 'c')]),
                         [['a', 'b'], ['c']])
        self.assertEqual(components(['a', 'b'], []), [['a'], ['b']])

    def test_missing_vertex_is_not_a_completion(self):
        with self.assertRaisesRegex(ValueError, 'EDGE_OUTSIDE_GRAPH'):
            components(['a'], [('a', 'missing')])

    def test_actual_receiving_graph_matches_independent_partition(self):
        import hashlib
        import json
        from pathlib import Path
        source = Path(__file__).resolve().parents[2] / 'tools/scc_reference.py'
        for name in ('scc-vector.json', 'source-transport-scc-vector.json'):
            with self.subTest(vector=name):
                vector = json.loads(Path(__file__).with_name(name).read_text())
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), vector['referenceSourceSha256'])
                for row in vector['vectors']:
                    self.assertEqual(components(**row['input']), row['expected'])
