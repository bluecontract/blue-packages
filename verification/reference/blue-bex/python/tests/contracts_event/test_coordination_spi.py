"""Independent routing and retained-receiving oracles for the engine bridge."""
import inspect
import unittest
from copy import deepcopy
from unittest.mock import patch
from pathlib import Path
from vendor import yaml
from blue_contracts import Processor, RuntimeBinding, ContractError
from blue_contracts.reference.graph import Graph
from blue_contracts.reference.processor import Run
from .test_contracts_event_api import T, operation, update, change


def finish(processor, attempt):
    while (token := processor.next_chunk(attempt)) is not None:
        processor.accept_chunk(attempt, token, processor.execute_chunk(token))
    return processor.finish(attempt)


def reroot(processor, snapshot, member):
    state = snapshot.copy()
    state.root = member
    members = Graph(state, processor.registry, processor.archive).reachable()
    state.documents = {k: v for k, v in state.documents.items() if k in members}
    state.edges = {k: e for k, e in state.edges.items() if e.source in members}
    return state


class CoordinationSPI(unittest.TestCase):
    def test_exact_channel_context_and_no_cross_document_call(self):
        p = Processor()
        typ = p.blue.identity(p.blue.source({'name': 'Verified channel', 'type': 'Contracts/Channel'}, goal='definition'))
        semantics = p.blue.identity(p.blue.source('test exact admission'))
        observations = []

        class Runtime:
            def verify_admission(self, context):
                evidence = context.evidence
                if evidence is None or evidence['snapshot'] != context.snapshot or evidence['event'] != context.event:
                    raise ContractError('BAD_PROOF')
                return {'members': [dict(row) for row in context.members], 'selected': evidence['member']}

            def accept(self, context):
                context.gas.charge('accept')
                self_row = next(r for r in context.evidence['members'] if r['member'] == context.member)
                assert self_row['document'] == context.document
                assert self_row['channel'] == context.channel
                assert self_row['generation'] == context.generation
                with self_test.assertRaises(TypeError):
                    context.evidence['selected'] = 'forged'
                observations.append(context.member)
                return context.member == context.evidence['selected']

        self_test = self
        p.install_runtime(RuntimeBinding(typ, semantics, 'external-channel', (), (), 'testAdmission', (('accept', 1),)), Runtime())
        gate = {'type': {'blueId': typ}}
        a = {'count': 0, 'contracts': {'in': gate, 'go': operation(update(change('/count', 1)), channel='in')}}
        b = {'name': 'wrong receiver', 'contracts': {'in': gate}}
        initial = p.create({'a': a, 'b': b, 'contracts': {'embedded': T('Process Embedded', paths=['/a', '/b'])}})
        selected = next(e.target for e in initial.edges.values() if e.path == '/a')
        event = p.blue.source(T('Operation Request', channel='in', operation='go'))
        evidence = {typ: dict(snapshot=initial.identity, event=p.blue.identity(event), member=selected)}
        attempt = p.prepare_invocation(initial, event, 1, evidence=evidence)
        evidence[typ]['member'] = 'mutated after preparation'
        result = finish(p, attempt)
        self.assertEqual(result.status, 'APPLIED', result.diagnostic)
        self.assertEqual(p.read(result.snapshot, '/a/count'), 1)
        self.assertEqual(len(observations), 2)
        self.assertEqual(list(inspect.signature(p.process).parameters), ['document', 'event', 'eventTimestamp'])
        denied = finish(p, p.prepare_invocation(initial, event, 1, evidence={typ: {'snapshot': 'wrong', 'event': p.blue.identity(event)}}))
        self.assertEqual(denied.diagnostic['code'], 'BAD_PROOF')

    def test_retained_batch_uses_complete_state_without_source_reexecution(self):
        p = Processor()
        path = Path(__file__).resolve().parents[2] / 'inputs/contracts-completion-1-design/examples/01-parent.yaml'
        initial = p.create(yaml.safe_load(path.read_text()))
        child = next(e.target for e in initial.edges.values() if e.path == '/b')
        source = reroot(p, initial, child)
        event = T('Operation Request', channel='input', operation='start')
        result = p.process(source, event, 123)
        self.assertEqual(result.status, 'APPLIED', result.diagnostic)
        capability = p.capture_source_outcome(result)
        original = Run.run_local

        def check(run, sealed, key, *args):
            self.assertNotEqual(key, child, 'receiving must not execute the source')
            return original(run, sealed, key, *args)

        with patch.object(Run, 'run_local', check):
            received = finish(p, p.begin_receiving_application(initial, [capability]))
        self.assertEqual(received.status, 'APPLIED', received.diagnostic)
        self.assertEqual(p.read(received.snapshot, '/payloadAtE1'), 1)
        self.assertEqual(p.read(received.snapshot, '/childAtE1'), 2)
        self.assertEqual(p.read(received.snapshot, '/stageAtP1'), 2)
        self.assertEqual(p.emitted(received), [{'kind': 'P1'}])
        self.assertEqual(received.snapshot.documents[child].metadata(), result.snapshot.documents[child].metadata())
        self.assertFalse(any(r['document'] == child for r in received.work_trace))
        self.assertEqual(received.checkpoints, [])
        duplicate = finish(p, p.begin_receiving_application(received.snapshot, [capability]))
        self.assertEqual(duplicate.diagnostic['code'], 'SOURCE_PREDECESSOR_MISMATCH')
        p.gas_limit = 1
        failed = finish(p, p.begin_receiving_application(initial, [capability]))
        self.assertEqual(failed.status, 'GAS_LIMIT_EXCEEDED')
        self.assertEqual(failed.snapshot.identity, initial.identity)
        self.assertEqual(failed.public_events, [])

    def test_foreign_and_mutated_results_have_no_local_provenance(self):
        p = Processor()
        state = p.create({'count': 0, 'contracts': {'in': T('External Channel'), 'go': operation(update(change('/count', 1)), channel='in')}})
        result = p.process(state, T('Operation Request', channel='in', operation='go'), 1)
        altered = deepcopy(result)
        altered.gas += 1
        with self.assertRaises(ContractError):
            p.capture_source_outcome(altered)
        with self.assertRaises(ContractError):
            Processor().capture_source_outcome(result)


if __name__ == '__main__':
    unittest.main()
