"""Core authoring, exact identity and shared executable definitions."""
import copy
import json
import unittest
from algorithms import blue as L
from blue_language import Language
from blue_contracts import Processor, ContractError, Link, export_snapshot, import_snapshot
from blue_bex import Engine, Context, BoundaryError, CompileError
from .test_exact_transfer import cut


def step(**fields):return {'type':'Compute',**fields}
def fixture(*steps,**fields):
    return {**fields,'contracts':{'input':{'type':'External Channel'},
        'go':{'type':'Sequential Workflow','channel':'input','steps':list(steps)}}}
def emit(expr):return step(do=[{'$appendEvent':expr}])
def identity(expr):return {'$nodeBlueId':expr}
def library(value=42):return {'constants':{'n':value},'functions':{'main':{'expr':{'$const':'n'}}}}


class CoreCompute(unittest.TestCase):
    def setUp(self):
        from blue_language.physical import PhysicalCache
        scope=PhysicalCache(65536).scope();scope.__enter__();self.addCleanup(scope.__exit__,None,None,None)
        self.p=Processor()
    def run_doc(self,doc,event=None):
        state=self.p.create(doc);result=self.p.process(state,event if event is not None else {},10)
        self.assertEqual(result.status,'APPLIED',result.diagnostic)
        return state,result
    def test_default_language_has_all_core_names(self):
        language=Language()
        for name,tid in self.p.registry.types.items():
            self.assertEqual(language.aliases[name],tid)
            self.assertEqual(language.create(json.dumps({'type':name}),goal='definition').blue_id,
                language.create(json.dumps({'type':'Contracts/'+name}),goal='definition').blue_id)
    def test_conflicting_core_name_is_rejected(self):
        with self.assertRaises(L.Failure):Language(aliases={'Compute':L.CORE['Text']})
    def test_namespaced_spelling_is_same_exact_content(self):
        doc=fixture(emit(1));old=copy.deepcopy(doc)
        def qualify(value):
            if isinstance(value,dict):
                for k,v in value.items():
                    if k=='type' and isinstance(v,str) and v in self.p.registry.types:value[k]='Contracts/'+v
                    else:qualify(v)
            elif isinstance(value,list):
                for v in value:qualify(v)
        qualify(old)
        self.assertEqual(self.p.blue.identity(self.p.blue.source(doc)),self.p.blue.identity(self.p.blue.source(old)))
    def test_scalar_and_constructed_identity_uses_language(self):
        values=[1,1.0,True,'hello',{},[],{'a':[1,2]}]
        _,out=self.run_doc(fixture(*(emit(identity(v)) for v in values)))
        self.assertEqual(self.p.emitted(out),[self.p.blue.identity(self.p.blue.node(v)) for v in values])
    def test_exact_identity_across_inline_reference_variable_and_function(self):
        payload={'a':[1,2]}
        doc=fixture(step(functions={'id':{'args':{'x':{}},'expr':identity({'$var':'x'})}},do=[
            {'$let':{'name':'v','expr':{'$document':'/payload'}}},
            {'$appendEvent':identity({'$var':'v'})},
            {'$appendEvent':{'$call':{'function':'id','args':{'x':{'$document':'/payload'}}}}}],),payload=payload)
        state=self.p.create(doc);other=cut(self.p,state,('/payload',))
        results=[self.p.process(s,{},10) for s in (state,other)]
        self.assertEqual(results[0].observations(),results[1].observations())
        expected=self.p.blue.identity(self.p.blue.source(payload))
        for out in results:
            self.assertEqual(out.status,'APPLIED',out.diagnostic);self.assertEqual(self.p.emitted(out),[expected,expected])
    def test_constructed_identity_retains_nested_exact_values(self):
        read={'$document':'/payload'}
        for expression in ({'wrapped':read},[read],{'nested':{'items':[read]}}):
            state=self.p.create(fixture(emit(identity(expression)),payload={'a':[1,2]}))
            other=cut(self.p,state,('/payload',))
            full=self.p.process(state,{},10)
            self.assertEqual(full.status,'APPLIED',full.diagnostic)
            self.assertEqual(full.observations(),self.p.process(other,{},10).observations())
            for cap in (0,full.gas-1,full.gas):
                self.p.gas_limit=cap
                left,right=[self.p.process(x,{},10) for x in (state,other)]
                self.assertEqual(left.observations(),right.observations())
            self.p.gas_limit=100000
    def test_exact_type_identity_not_specialization(self):
        parent=self.p.blue.source({'name':'Parent'},goal='definition');pid=self.p.blue.identity(parent)
        child=self.p.blue.source({'name':'Child','type':{'blueId':pid}},goal='definition');cid=self.p.blue.identity(child)
        _,out=self.run_doc(fixture(emit(identity({'$document':'/item/type'})),item={'type':{'blueId':cid}}))
        self.assertEqual(self.p.emitted(out),[cid]);self.assertNotEqual(pid,cid)
    def test_invalid_identity_input_rolls_back(self):
        for expr in ({'$null':True},{'$var':'missing'},{'a':{'$null':True}},[{'$null':True}],[{'$event':'/missing'}]):
            doc=fixture(step(do=[{'$appendChange':{'op':'replace','path':'/n','val':1}}, {'$appendEvent':identity(expr)}]),n=0)
            state=self.p.create(doc);out=self.p.process(state,{},10)
            self.assertEqual(out.status,'FAILED',out.diagnostic);self.assertEqual(out.snapshot.identity,state.identity);self.assertFalse(out.public_events)
    def test_undefined_identity_rejected(self):
        state=self.p.create(fixture(emit(identity({'$event':'/missing'}))))
        self.assertEqual(self.p.process(state,{},10).status,'FAILED')
    def test_identity_gas_and_rollback(self):
        state,out=self.run_doc(fixture(emit(identity({'nested':[1,2]}))))
        self.assertTrue(any(r['counter']=='nodeIdentityRequested' for r in out.gas_trace))
        self.p.gas_limit=out.gas-1;failed=self.p.process(state,{},10)
        self.assertEqual(failed.status,'GAS_LIMIT_EXCEEDED');self.assertEqual(failed.snapshot.identity,state.identity);self.assertFalse(failed.public_events)
        self.p.gas_limit=out.gas;bounded=self.p.process(state,{},10)
        self.assertEqual(bounded.status,'APPLIED');self.assertEqual(bounded.gas_trace,out.gas_trace)
        self.assertEqual(self.p.emitted(bounded),self.p.emitted(out))
    def test_cyclic_member_identity_is_preserved(self):
        doc=fixture(emit(identity({'$document':'/peer'})),peer=Link('A'))
        doc['contracts']['embedded']={'type':'Process Embedded','paths':['/peer']}
        admitted=self.p.admit({'A':doc},root='A')
        self.assertTrue(admitted.commits,admitted.diagnostic)
        state=admitted.snapshot
        expected=self.p.blue.identity(self.p.blue.exact(self.p.blue.select(state.documents['A'].body,'/peer')))
        out=self.p.process(state,{},10)
        self.assertEqual(out.status,'APPLIED',out.diagnostic)
        self.assertEqual(self.p.emitted(out),[expected]);self.assertIn('#',expected)
    def test_exact_identity_all_charge_boundaries(self):
        state=self.p.create(fixture(emit(identity({'$document':'/payload'})),payload={'a':[1,2]}))
        other=cut(self.p,state)
        full=self.p.process(state,{},10);total=0;budgets={0,full.gas}
        for row in full.gas_trace:
            total+=row['amount'];budgets.add(max(0,total-1))
        for limit in sorted(budgets):
            self.p.gas_limit=limit
            a,b=[self.p.process(x,{},10) for x in (state,other)]
            self.assertEqual(a.observations(),b.observations(),limit)
            self.assertEqual(a.commits,limit>=full.gas)
    def test_bex_definition_maps_are_validated(self):
        with self.assertRaises(CompileError):Engine().compile({'expr':1},definition={'functions':[]})
        with self.assertRaises(CompileError):Engine().compile({'expr':1,'constants':[]},definition={})
    def test_standalone_bex_requires_explicit_identity_boundary(self):
        with self.assertRaises(BoundaryError):Engine().execute({'expr':identity(1)})
    def definition_doc(self,definition):
        return fixture(step(name='result',definition=definition,entry='main'),emit({'$steps':'result'}))
    def test_inline_definition(self):
        _,out=self.run_doc(self.definition_doc(library()));self.assertEqual(self.p.emitted(out),[42])
    def test_exact_definition_reference(self):
        did=self.p.blue.identity(self.p.blue.source(library()))
        _,out=self.run_doc(self.definition_doc({'blueId':did}));self.assertEqual(self.p.emitted(out),[42])
    def test_sibling_definition_marker(self):
        doc=self.definition_doc('shared');doc['contracts']['shared']={'type':'Compute Definition',**library()}
        _,out=self.run_doc(doc);self.assertEqual(self.p.emitted(out),[42])
    def test_pointer_definition(self):
        doc=self.definition_doc('/libraries/main');doc['libraries']={'main':library()}
        _,out=self.run_doc(doc);self.assertEqual(self.p.emitted(out),[42])
    def test_definition_is_resolved_after_previous_step(self):
        doc=self.definition_doc('/library');doc['library']=library()
        doc['contracts']['go']['steps'].insert(0,{'type':'Update Document','changeset':[{'op':'replace','path':'/library/constants/n','val':99}]})
        _,out=self.run_doc(doc);self.assertEqual(self.p.emitted(out),[99])
    def test_step_local_overrides(self):
        doc=self.definition_doc(library());doc['contracts']['go']['steps'][0]['constants']={'n':7}
        _,out=self.run_doc(doc);self.assertEqual(self.p.emitted(out),[7])
        doc['contracts']['go']['steps'][0]['functions']={'main':{'expr':9}}
        _,out=self.run_doc(doc);self.assertEqual(self.p.emitted(out),[9])
    def test_current_contract_does_not_invent_imported_or_empty_fields(self):
        read={'$exists':{'$currentContract':'/functions'}}
        _,out=self.run_doc(fixture(emit(read)))
        self.assertEqual(self.p.emitted(out),[False])
        lib={'functions':{'main':{'do':[{'$appendEvent':read}]}}}
        _,out=self.run_doc(fixture(step(definition=lib,entry='main')))
        self.assertEqual(self.p.emitted(out),[False])
    def test_imported_functions_see_result_overlay(self):
        lib={'functions':{'main':{'do':[{'$appendChange':{'op':'replace','path':'/n','val':9}}, {'$appendEvent':{'$resultValue':'/n'}}]}}}
        _,out=self.run_doc(fixture(step(definition=lib,entry='main'),n=0));self.assertEqual(self.p.emitted(out),[9])
    def test_missing_malformed_and_recursive_definition_fail_atomically(self):
        bad=['absent','/absent',17,{'functions':[]},{'functions':{'main':{'expr':{'$call':{'function':'main'}}}}}]
        for value in bad:
            with self.subTest(value=value):
                doc=self.definition_doc(value);state=self.p.create(doc);out=self.p.process(state,{},10)
                self.assertEqual(out.status,'FAILED',out.diagnostic);self.assertEqual(out.snapshot.identity,state.identity);self.assertFalse(out.public_events)
    def test_unused_invalid_definition_is_not_executed(self):
        doc=self.definition_doc('absent');doc['contracts']['go']['event']={'run':True}
        _,out=self.run_doc(doc);self.assertFalse(out.public_events)
    def test_escaped_definition_name_and_pointer(self):
        doc=self.definition_doc('/libraries/a~1b~0c');doc['libraries']={'a/b~c':library()}
        _,out=self.run_doc(doc);self.assertEqual(self.p.emitted(out),[42])
    def test_processing_event_binding_stays_unchanged(self):
        _,out=self.run_doc(fixture(emit({'$binding':'processingEvent/amount'})),{'amount':17});self.assertEqual(self.p.emitted(out),[17])
        with self.assertRaises(CompileError):Engine().compile({'expr':{'$processingEvent':'/value'}})
    def test_definition_snapshot_roundtrip(self):
        state,out=self.run_doc(self.definition_doc(library()))
        package=export_snapshot(self.p,state);other=Processor();restored=import_snapshot(other,package,package['identity'])
        replay=other.process(restored,{},10);self.assertEqual(replay.observations(),out.observations())

if __name__=='__main__':unittest.main()
