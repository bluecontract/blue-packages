"""Local transport elision must preserve the complete reference observation."""
import unittest
from blue_contracts import Processor, ContractError
from .test_contracts_event_api import counter, call, compute
from .test_completion_graph import child, parent, start, emit, append, update, change
from .test_completion_cycles import cycle_documents
from .test_coordination_spi import reroot, finish


class LocalDriver(unittest.TestCase):
    def compare(self, processor, state, event):
        processor.local_driver = False
        expected = processor.process(state, event, 10)
        processor.local_driver = True
        actual = processor.process(state, event, 10)
        self.assertEqual(actual.observations(), expected.observations())
        self.assertEqual(actual.receipt, expected.receipt)
        return actual

    def test_initialization_and_dag_and_failure(self):
        for source in [counter(), parent(child(emit('E1'), emit('E2')), append({'$event':'/event/kind'})),
                       parent(child(update(change('/count', 1)), emit('E'), count=0), compute({'$fail':'late'}))]:
            with self.subTest(source=source):
                p = Processor()
                reference = p.initialize(source)
                p.local_driver = True
                local = p.initialize(source)
                self.assertEqual(local.observations(), reference.observations())
                self.compare(p, reference.snapshot, call() if source == counter() else start())

    def test_cyclic_unit_and_local_gas_rollback(self):
        p = Processor(); initial = p.admit(cycle_documents(), root='A')
        self.assertTrue(self.compare(p, initial.snapshot, start()).commits)
        p.local_limits = {'A':50}
        self.assertEqual(self.compare(p, initial.snapshot, start()).status, 'GAS_LIMIT_EXCEEDED')

    def test_each_logical_charge_boundary(self):
        p = Processor(); state = p.create(counter()); full = p.process(state, call(), 10)
        budgets = {0}; total = 0
        for charge in full.gas_trace:
            total += charge['amount']; budgets.update((max(0,total-1),total))
        for budget in sorted(budgets):
            with self.subTest(budget=budget):
                p.gas_limit = budget; result = self.compare(p,state,call())
                self.assertEqual(result.status,'APPLIED' if budget == full.gas else 'GAS_LIMIT_EXCEEDED')

    def test_receiving_batch_and_stale_chunk(self):
        p=Processor(); state=p.create(parent(child(emit('E1'),emit('E2')),append({'$event':'/event/kind'})))
        source=next(e.target for e in state.edges.values() if e.path=='/child')
        result=p.process(reroot(p,state,source),start(),10)
        capability=p.capture_source_outcome(result)
        expected=finish(p,p.begin_receiving_application(state,[capability]))
        actual=p.complete_local(p.begin_receiving_application(state,[capability]))
        self.assertEqual(actual.observations(),expected.observations())
        attempt=p.begin(state,start(),10); token=attempt.next_chunk()
        with self.assertRaises(ContractError):p.complete_local(attempt)
        with self.assertRaises(ContractError):Processor().complete_local(p.begin(state,start(),10))
        self.assertIs(attempt.next_chunk(),token)


if __name__=='__main__':unittest.main()
