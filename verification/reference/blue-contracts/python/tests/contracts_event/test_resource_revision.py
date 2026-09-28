"""Independent boundary vectors for the fixed-100k resource edition."""
import unittest
import json
from unittest.mock import patch
from concurrent.futures import CancelledError
from blue_host import HostIncomplete
from blue_language import Language, Limits
from blue_language.physical import PhysicalCache
from blue_contracts import Processor, ContractError
from blue_contracts.reference.model import Meter
from blue_bex import Engine, GasExhausted, Context
from .test_contracts_event_api import T, counter, call, operation, compute


class ResourceRevision(unittest.TestCase):
    def setUp(self):
        self.scope=PhysicalCache(65536).scope();self.scope.__enter__()
        self.addCleanup(self.scope.__exit__,None,None,None)

    def test_fixed_shared_maximum_and_exact_charge_boundary(self):
        self.assertEqual(Meter().limit,100000)
        for value in (100001,-1,None,True):
            with self.subTest(value=value),self.assertRaises(ContractError):Meter(value)
        for value in (100001,-1,None):
            with self.assertRaises(ContractError):Processor(gas_limit=value)
        meter=Meter(3);meter.contracts('objectMemberRead',3)
        self.assertEqual(meter.used,3)
        with self.assertRaises(GasExhausted):meter.contracts('objectMemberRead')
        self.assertEqual(meter.rejected['remaining'],0)

    def test_identity_prerequisite_precedes_lookup_and_canonical_size(self):
        from algorithms import blue as L
        from blue_contracts.reference.work import LogicalWork, canonical_size
        node=L.node({'value':'a'*65});meter=Meter(3)
        with patch.object(L,'identity',side_effect=AssertionError('identity ran before debit')):
            with self.assertRaises(GasExhausted):LogicalWork(None,meter).establish(node)
        self.assertEqual(meter.rejected['counter'],'identityInputTextBlock')
        self.assertEqual(meter.used,2)
        self.assertEqual(canonical_size({'value':'a'*65}),77)
        for value in ({'x':'"\\\n\u0000😀é'},[],{'a':[1,True,None,0.1]}):
            self.assertEqual(canonical_size(value),len(L.canonical_text(value).encode('utf8')))

    def test_integer_cost_is_debited_before_multiplication(self):
        # Two 33-bit operands occupy two 32-bit limbs. 2+3+2*2 = 9.
        expr={'expr':{'$multiply':[2**32,2**32]}}
        result=Engine().execute(expr,gas_limit=9)
        self.assertEqual((result.value,result.gas_used),(2**64,9))
        with self.assertRaises(GasExhausted):Engine().execute(expr,gas_limit=8)
        # 1025 limbs each: reject their million-unit multiplication work first.
        with self.assertRaises(GasExhausted):Engine().execute({'expr':{'$multiply':[2**32768,2**32768]}})

    def test_failure_text_and_pending_overlay_cannot_bypass_work_charges(self):
        for statement in ({'$fail':10**20000},
                          {'$failIf':{'cond':True,'message':10**20000}}):
            with self.subTest(statement=next(iter(statement))),self.assertRaises(GasExhausted):
                Engine().execute({'do':[statement]})
        # Pending changes copy the same object spine as $pointerSet. An
        # unaffordable copy must stop before constructing that collection.
        doc={str(i):i for i in range(100001)}
        program={'do':[{'$appendChange':{'op':'replace','path':'/0','val':1}},
                       {'$return':{'$resultValue':'/'}}]}
        with self.assertRaises(GasExhausted):Engine().execute(program,Context(document=doc))

    def test_large_integers_are_values_not_portable_limit_errors(self):
        language=Language()
        for size in (4097,10001,20001):
            with self.subTest(digits=size):
                source={'type':'Integer','value':'1'+'0'*(size-1)}
                identity=language.identify(json.dumps(source))
                self.assertTrue(identity)
                with self.assertRaises(GasExhausted):Engine().execute({'expr':{'$integer':source['value']}})
        # A large already available literal requires no decimal conversion.
        value=10**20000
        self.assertEqual(Engine().execute({'expr':value}).value,value)

    def test_language_defaults_unbounded_explicit_cutoff_incomplete(self):
        self.assertTrue(all(getattr(Limits(),n) is None for n in Limits.__dataclass_fields__))
        p=Processor();p.blue.language.limits=Limits(steps=1)
        with self.assertRaises(HostIncomplete):p.blue.source({'x':1})

    def test_129_members_and_513_occurrences(self):
        p=Processor()
        children={f'c{i}':{'name':f'child{i}'} for i in range(128)}
        doc={**children,'contracts':{'embedded':T('Process Embedded',paths=['/'+key for key in children])}}
        out=p.initialize(doc)
        self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(len(out.snapshot.documents),129)
        self.assertLess(out.gas,100000)
        child=p.blue.source({'name':'shared'})
        refs={f'c{i}':{'blueId':p.blue.identity(child)} for i in range(513)}
        out=p.initialize({**refs,'contracts':{'embedded':T('Process Embedded',paths=['/'+key for key in refs])}})
        self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(len(out.snapshot.edges),513)

    def test_257_headers_1025_steps_and_long_token(self):
        p=Processor()
        doc=counter({f'unused{i}':operation() for i in range(257)})
        del doc['contracts']['before'];del doc['contracts']['after']
        initial=p.initialize(doc)
        self.assertTrue(initial.commits,initial.diagnostic)
        out=p.process(initial.snapshot,call(),1)
        self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(p.read(out.snapshot,'/count'),3)
        name='a'*1025
        doc={'contracts':{'input':T('External Channel'),name:operation(*[compute() for _ in range(1025)])}}
        out=p.process(doc,T('Operation Request',channel='input',operation=name),1)
        self.assertTrue(out.commits,out.diagnostic)
        self.assertLess(out.gas,100000)

    def test_large_selected_program_and_deep_source(self):
        p=Processor()
        doc={'contracts':{'input':T('External Channel'),'go':operation(T('Compute',constants={'unused':'x'*(1024*1024+1)},expr=1))}}
        out=p.process(doc,T('Operation Request',channel='input',operation='go'),1)
        self.assertTrue(out.commits,out.diagnostic)
        value=True
        for _ in range(170):value={'$not':value}
        self.assertTrue(Engine().execute({'expr':value}).value)
        doc={'leaf':1}
        for _ in range(140):doc={'child':doc}
        self.assertTrue(Language().identify(json.dumps(doc)))

    def test_direct_local_cold_chunks_at_exact_budget_boundaries(self):
        from .test_completion_chunks import chunks
        p=Processor();state=p.create(counter());event=call();oracle=p.process(state,event,10)
        self.assertTrue(oracle.commits)
        for budget in (0,oracle.gas-1,oracle.gas):
            with self.subTest(budget=budget):
                p.gas_limit=budget;p.blue.refresh()
                direct=p.process(state,event,10)
                p.blue.refresh();local=p.complete_local(p.begin(state,event,10))
                p.blue.refresh();cold=chunks(p,state,event,transport=True)
                self.assertEqual(direct.observations(),local.observations())
                self.assertEqual(direct.observations(),cold.observations())
                self.assertEqual(direct.status,'APPLIED' if budget==oracle.gas else 'GAS_LIMIT_EXCEEDED')
        p.gas_limit=100000;p.local_limits={'root':1}
        direct=p.process(state,event,10);chunked=chunks(p,state,event)
        self.assertEqual(direct.observations(),chunked.observations())
        self.assertEqual(direct.rejected['cap'],'LOCAL')

    def test_host_faults_do_not_become_outcomes_and_same_input_retries(self):
        p=Processor();state=p.create(counter());oracle=p.process(state,call(),1)
        from blue_contracts.reference.work import LogicalWork
        for fault in (MemoryError,RecursionError,CancelledError,lambda:HostIncomplete('test cutoff')):
            with self.subTest(fault=fault):
                with patch.object(LogicalWork,'validate',side_effect=fault()),self.assertRaises(HostIncomplete):
                    p.process(state,call(),1)
                result=p.process(state,call(),1)
                self.assertEqual(result.observations(),oracle.observations())
                self.assertEqual(p.read(state,'/count'),0)
        for fault in (MemoryError,RecursionError,CancelledError):
            with self.subTest(intrinsic=fault):
                def fail(payload,gas):raise fault()
                with self.assertRaises(HostIncomplete):Engine(intrinsics={'test':fail}).execute({'expr':{'$intrinsic':{'type':{'blueId':'test'}}}})

    def test_long_type_plan_candidate_search_and_function_stack(self):
        from algorithms import blue as L
        from blue_contracts.reference.policy import GeneralizationPolicy, choose_type
        language=Language();previous=L.CORE['Integer']
        for number in range(1030):
            node=L.node({'name':'Type'+str(number),'type':L.Ref(previous)})
            previous=L.identity(node);language.provider.set_exact(previous,L.export_exact(node))
        checked=language.check(json.dumps({'type':{'blueId':previous},'value':1}))
        self.assertEqual(checked['outcome'],'Established',checked)
        meter=Meter();visited=[]
        def charge(tid):visited.append(tid);meter.contracts('subtypeCandidateTested')
        result=choose_type('0',{},'',GeneralizationPolicy(default_mode='nearest-valid-ancestor'),
            immediate_ancestor=lambda tid:str(int(tid)+1),valid_with_type=lambda node,tid:tid=='1025',
            is_subtype=lambda a,b:True,charge_candidate=charge)
        self.assertEqual((result,len(visited),meter.used),('1025',1026,5130))
        functions={f'f{i}':{'expr':{'$call':{'function':f'f{i+1}'}}} for i in range(120)}
        functions['f120']={'expr':7}
        result=Engine().execute({'functions':functions,'expr':{'$call':{'function':'f0'}}})
        self.assertEqual((result.value,result.gas_used),(7,366))

    def test_authored_constraints_remain_enforced(self):
        p=Processor()
        with self.assertRaises(ContractError):p.blue.source({'type':'List','schema':{'maxItems':1},'items':[1,2]})
        with self.assertRaises(ContractError):p.blue.source({'type':'Integer','value':'01'})
