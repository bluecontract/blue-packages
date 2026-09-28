import copy
import unittest
from blue_contracts import Processor
from blue_contracts.reference.model import digest, Outcome
from blue_runtime.sealed import sealed_scope, SealedOutcome
from blue_runtime.indexed_topology import topology_scope
from .test_contracts_event_api import counter, call
from .test_completion_cycles import cycle_documents
from .test_completion_graph import start


class SealedResults(unittest.TestCase):
    def reference(self,p,before,event,timestamp):
        with topology_scope(enabled=False),sealed_scope(enabled=False):
            return p.process(before,event,timestamp)

    def test_canonical_receipt_and_detached_nested_mutations(self):
        p=Processor(local_driver=True); before=p.create(counter()); expected=self.reference(p,before,call(),10)
        metrics={}
        with sealed_scope(metrics), topology_scope(): actual=p.process(before,call(),10)
        self.assertIsInstance(actual,Outcome);self.assertIsInstance(actual,SealedOutcome)
        self.assertEqual(actual.observations(),expected.observations())
        self.assertEqual(actual.receipt,expected.receipt)
        self.assertEqual(actual.receipt,digest('contracts.result/completion-1',actual.observations()))
        self.assertEqual(metrics['receiptDigests'],1)
        copy_out=copy.deepcopy(actual);self.assertIs(copy_out,actual)
        observation=actual.observations();observation['gasTrace'][0]['owner']='same-length edit'
        snapshot=actual.snapshot;snapshot.documents[snapshot.root].channel_serials.clear()
        actual.gas_trace[0]['amount']=99
        self.assertEqual(actual.observations(),expected.observations())
        self.assertEqual(actual.receipt,expected.receipt)
        with self.assertRaises(TypeError):actual.gas=99
        capability=p.capture_source_outcome(actual)
        self.assertEqual(capability.descriptor['receipt'],expected.receipt)

    def test_cyclic_observations_and_working_snapshot_independence(self):
        p=Processor(local_driver=True);before=p.admit(cycle_documents(),root='A').snapshot
        expected=self.reference(p,before,start(),10)
        with sealed_scope(),topology_scope():actual=p.process(before,start(),10)
        self.assertEqual(actual.observations(),expected.observations())
        self.assertEqual(actual.snapshot.wire(),expected.snapshot.wire())
        first=actual.snapshot;second=actual.snapshot
        first.edges.clear();self.assertTrue(second.edges)

    def test_all_counter_gas_boundaries_and_original_checkpoint(self):
        p=Processor(local_driver=True);before=p.create(counter());full=p.process(before,call(),10)
        total=0;budgets={0}
        for charge in full.gas_trace:
            total+=charge['amount'];budgets.update((max(total-1,0),total))
        for budget in sorted(budgets):
            p.gas_limit=budget
            expected=self.reference(p,before,call(),10)
            with sealed_scope(),topology_scope():actual=p.process(before,call(),10)
            self.assertEqual(actual.observations(),expected.observations(),budget)
            self.assertEqual(actual.receipt,expected.receipt,budget)


if __name__=='__main__':unittest.main()
