"""Physical topology indexes must match the independently retained reference."""
import random
import unittest
from types import SimpleNamespace
from copy import deepcopy
from blue_contracts.reference.model import Snapshot, Document, Edge
from blue_contracts.reference.graph import Graph
from blue_contracts.reference.completion import Phase
from blue_runtime.indexed_topology import (
    topology_scope, topology, RevisionMap, components, promote, next_unit,
    _REFERENCE_COMPONENTS, _REFERENCE_PROMOTE, _REFERENCE_NEXT, _REFERENCE_REACHABLE,
)


class IndexedTopology(unittest.TestCase):
    def fake(self, n=10):
        state = Snapshot('0', {str(i): Document(str(i), {}, str(i)) for i in range(n)})
        state.edges = {('0', '/' + str(i)): Edge('0', '/' + str(i), str(i), 1) for i in range(1, n)}
        g = Graph.__new__(Graph); g.state = state; g.terminated = lambda k: False
        phase = Phase('PROCESS', set(state.documents), [set(g) for g in _REFERENCE_COMPONENTS(state.documents,state.edges.values())], {}, {}, {})
        machine=SimpleNamespace(state=state, graph=g)
        machine.promote=lambda phase,members:_REFERENCE_PROMOTE(machine,phase,members)
        return machine, phase

    def test_random_scc_order_including_self_loops_and_disconnected_vertices(self):
        rng = random.Random(441)
        for n in range(1, 26):
            vertices = list(map(str,range(n)))
            for density in (.05, .2, .8):
                edges = [Edge(a,'/'+b,b,1) for a in vertices for b in vertices if rng.random() < density]
                expected = _REFERENCE_COMPONENTS(vertices,edges)
                with topology_scope(): self.assertEqual(components(vertices,edges),expected)

    def test_dispatch_cost_tracks_topology_not_empty_units(self):
        machine, phase = self.fake(128); metrics = {}
        with topology_scope(metrics):
            while (unit := next_unit(machine,phase)) is not None: phase.done.add(tuple(sorted(unit)))
        self.assertEqual(metrics['topologyIndexBuilds'],1)
        self.assertEqual(metrics['sccBuilds'],1)
        self.assertEqual(metrics['scheduleBuilds'],1)
        self.assertEqual(metrics['scheduleEdgeVisits'],127)
        self.assertEqual(metrics['dependencyUpdates'],127)
        self.assertEqual(len(phase.done),128)

    def test_dynamic_merge_split_retirement_recreation_and_done_reactivation(self):
        machine, phase = self.fake(8)
        reference, ref_phase = self.fake(8)
        def compare():
            expected = _REFERENCE_NEXT(reference,ref_phase)
            with topology_scope(): actual = next_unit(machine,phase)
            self.assertEqual(actual,expected)
            return actual
        compare()
        for edges in [
            [Edge('1','/a','2',1),Edge('2','/b','1',1)],
            [Edge('2','/b','3',2),Edge('3','/c','2',1)],
            [Edge('3','/c','3',2)],
        ]:
            for edge in edges:
                machine.state.edges[edge.key]=edge; reference.state.edges[edge.key]=edge
            compare()
        for key in [('0','/4'),('2','/b')]:
            machine.state.edges.pop(key); reference.state.edges.pop(key)
        compare()
        while (unit := compare()) is not None:
            identity=tuple(sorted(unit));phase.done.add(identity);ref_phase.done.add(identity)
        identity=next(g for g in phase.done if '1' in g)
        phase.done.discard(identity);ref_phase.done.discard(identity);compare()
        edge=Edge('0','/4','4',2)
        machine.state.edges[edge.key]=edge;reference.state.edges[edge.key]=edge;compare()

    def test_copy_and_ordinary_content_do_not_reuse_stale_structure_or_lifecycle(self):
        machine, phase = self.fake()
        with topology_scope():
            index=topology(machine.graph)
            machine.state.documents['1'].body={'value':'changed'}
            self.assertIs(topology(machine.graph),index)
            machine.graph.terminated=lambda k:k=='1'
            self.assertNotIn('1',machine.graph.reachable(active=True))
            copied=deepcopy(machine.state)
            machine.graph.state=copied
            self.assertIsNot(topology(machine.graph),index)
            copied.edges.pop(('0','/2'))
            self.assertNotIn('2',machine.graph.reachable())
            self.assertIn('2',_REFERENCE_REACHABLE(SimpleNamespace(state=machine.state)))

    def test_mutation_methods_invalidate_edge_occurrences(self):
        edges=RevisionMap({('a','/b'):Edge('a','/b','b',1)})
        version=edges.version;edges.update({('a','/b'):Edge('a','/b','b',2)})
        self.assertGreater(edges.version,version)
        version=edges.version;edges[('a','/b')]=Edge('a','/b','b',2)
        self.assertEqual(edges.version,version)
        version=edges.version;edges.clear();self.assertGreater(edges.version,version)


if __name__=='__main__':unittest.main()
