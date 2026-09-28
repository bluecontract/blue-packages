"""All published Contracts lessons against the untouched semantic reference."""
import unittest
from blue_runtime.indexed_topology import topology_scope
from blue_runtime.sealed import sealed_scope
from blue_runtime.syntax_cache import syntax_scope
from . import scenarios


class GrowthEquivalence(unittest.TestCase):
    def test_every_guide_result_matches_complete_reference_observations(self):
        for name in scenarios.ids():
            with self.subTest(lesson=name):
                with topology_scope(enabled=False),sealed_scope(enabled=False),syntax_scope(enabled=False):
                    _,initial,results,_=scenarios.execute(name)
                    expected=[(r.observations(),r.receipt,r.snapshot.wire()) for r in [initial,*results]]
                with topology_scope(),sealed_scope(),syntax_scope():
                    _,initial,results,_=scenarios.execute(name)
                    actual=[(r.observations(),r.receipt,r.snapshot.wire()) for r in [initial,*results]]
                self.assertEqual(actual,expected)


if __name__=='__main__':unittest.main()
