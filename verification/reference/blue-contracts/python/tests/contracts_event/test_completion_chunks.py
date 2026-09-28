"""A11: the data boundary is execution-verified, input-bound and one-use."""
import json
import unittest
from copy import deepcopy
from blue_contracts import Processor,ContractError,export_invocation,import_invocation
from blue_contracts.reference.chunks import committed
from .test_contracts_event_api import counter,call,compute
from .test_completion_graph import child,parent,start,emit,append,update,change
from .test_completion_cycles import cycle_documents


def chunks(p,state,event,time=10,transport=False):
    attempt=p.begin(state,event,time)
    while (token:=p.next_chunk(attempt)) is not None:
        if transport:
            data=json.loads(json.dumps(token.to_data()))
            result=Processor().execute_chunk(data).to_data()
            result=json.loads(json.dumps(result))
        else:result=p.execute_chunk(token)
        p.accept_chunk(attempt,token,result)
    return p.finish(attempt)


class CompletionChunks(unittest.TestCase):
    def setUp(self):self.p=Processor()
    def compare(self,state,event,**kwargs):
        expected=self.p.process(state,event,10)
        actual=chunks(self.p,state,event,**kwargs)
        self.assertEqual(actual.observations(),expected.observations())
        self.assertEqual(actual.receipt,expected.receipt)
        return actual
    def test_dc55_static_dag_direct_chunk_exact_equivalence(self):
        state=self.p.create(parent(child(emit('E1'),emit('E2')),append({'$event':'/event/kind'})))
        self.assertTrue(self.compare(state,start()).commits)
    def test_dc56_cyclic_complete_unit_equivalence(self):
        initial=self.p.admit(cycle_documents(),root='A');self.assertTrue(initial.commits,initial.diagnostic)
        self.assertTrue(self.compare(initial.snapshot,start()).commits)
    def test_dc57_data_only_transport_to_fresh_processor(self):
        state=self.p.create(counter())
        self.assertTrue(self.compare(state,call(),transport=True).commits)
    def test_dc57_raw_initialization_transport(self):
        expected=self.p.process(counter(),call(),10)
        actual=chunks(self.p,counter(),call(),transport=True)
        self.assertEqual(expected.observations(),actual.observations())
    def test_dc57_cyclic_proofs_cross_the_data_boundary(self):
        initial=self.p.admit(cycle_documents(),root='A');self.assertTrue(initial.commits,initial.diagnostic)
        self.assertTrue(self.compare(initial.snapshot,start(),transport=True).commits)
    def test_dc57_portable_worker_requires_exact_installed_runtime(self):
        from blue_workbench.guide_extensions import install_extensions
        install_extensions(self.p)
        state=self.p.create({'count':2,'contracts':{
            'input':{'type':'Tutorial/Tick Channel'},
            'double':{'type':'Contracts/Sequential Workflow','channel':'input',
                      'steps':[{'type':'Tutorial/Double Step'}]}}})
        event={'kind':'tick'};expected=self.p.process(state,event,10)
        attempt=self.p.begin(state,event,10);token=attempt.next_chunk()
        with self.assertRaises(ContractError) as error:Processor().execute_chunk(token.to_data())
        self.assertEqual(error.exception.code,'INCOMPATIBLE_RUNTIME_BINDINGS')
        while token is not None:
            worker=Processor();install_extensions(worker)
            result=worker.execute_chunk(json.loads(json.dumps(token.to_data())))
            attempt.accept_chunk(token,json.loads(json.dumps(result.to_data())))
            token=attempt.next_chunk()
        actual=attempt.finish()
        self.assertEqual(actual.observations(),expected.observations())
        self.assertEqual(self.p.read(actual.snapshot,'/count'),4)
    def test_dc54_duplicate_acceptance_cannot_double_work(self):
        state=self.p.create(counter());attempt=self.p.begin(state,call(),10)
        token=attempt.next_chunk();result=attempt.execute_chunk(token)
        attempt.accept_chunk(token,result);before=attempt.run.meter.used
        with self.assertRaises(ContractError):attempt.accept_chunk(token,result)
        self.assertEqual(attempt.run.meter.used,before)
        while (token:=attempt.next_chunk()) is not None:attempt.accept_chunk(token,attempt.execute_chunk(token))
        self.assertTrue(attempt.finish().commits)
    def test_dc53_changed_result_with_valid_hash_is_not_execution_proof(self):
        state=self.p.create(counter());attempt=self.p.begin(state,call(),10)
        token=attempt.next_chunk();wire=attempt.execute_chunk(token).to_data()
        wire['gas']+=1;wire=committed('chunk-result',{k:v for k,v in wire.items() if k!='identity'})
        with self.assertRaises(ContractError) as error:attempt.accept_chunk(token,wire)
        self.assertEqual(error.exception.code,'INVALID_CHUNK_EXECUTION')
        self.assertEqual(attempt.run.state.identity,state.identity)
    def test_dc53_wrong_input_profile_seed_and_occurrence_rejected(self):
        state=self.p.create(counter());attempt=self.p.begin(state,call(),10)
        token=attempt.next_chunk();data=token.to_data()
        for field in ['beforeViews','profile','seeds','pending','logicalPrefix']:
            with self.subTest(field=field):
                bad=deepcopy(data);bad['token'][field]='forged'
                with self.assertRaises(ContractError):self.p.execute_chunk(bad)
    def test_finish_rejects_unfinished_attempt(self):
        state=self.p.create(counter());attempt=self.p.begin(state,call(),10)
        with self.assertRaises(ContractError) as error:attempt.finish()
        self.assertEqual(error.exception.code,'UNFINISHED_ATTEMPT')
    def test_dc58_shared_gas_boundaries_have_same_first_rejection(self):
        state=self.p.create(counter());full=self.p.process(state,call(),10)
        for budget in [0,19,20,full.gas-1,full.gas]:
            with self.subTest(budget=budget):
                self.p.gas_limit=budget
                out=self.compare(state,call())
                self.assertEqual(out.status,'APPLIED' if budget==full.gas else 'GAS_LIMIT_EXCEEDED')
                self.assertEqual(sum(r['amount'] for r in out.gas_trace),out.gas)
    def test_dc58_local_cap_and_cyclic_rejection_prefix(self):
        initial=self.p.admit(cycle_documents(),root='A');self.assertTrue(initial.commits,initial.diagnostic)
        self.p.local_limits={'A':50}
        out=self.compare(initial.snapshot,start())
        self.assertEqual(out.status,'GAS_LIMIT_EXCEEDED');self.assertEqual(out.rejected['cap'],'LOCAL')
    def test_dc59_parent_failure_rolls_back_already_accepted_child_chunk(self):
        state=self.p.create(parent(child(update(change('/count',1)),emit('E'),count=0),compute({'$fail':'late'})))
        out=self.compare(state,start());self.assertEqual(out.status,'FAILED')
        self.assertEqual(out.snapshot.identity,state.identity);self.assertEqual(out.public_events,[])
    def test_cold_capsule_replay_keeps_completion_and_round_identities(self):
        state=self.p.create(parent(child(emit('E')),append('E')))
        expected=self.p.process(state,start(),10)
        capsule=export_invocation(self.p,state,start(),10);other=Processor()
        document,event,time=import_invocation(other,capsule,capsule['identity'])
        actual=other.process(document,event,time)
        self.assertEqual(expected.observations(),actual.observations())


if __name__=='__main__':unittest.main()
