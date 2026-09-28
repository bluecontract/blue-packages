"""Executable regression contract: every test starts from supplied source."""
import inspect,sys,unittest
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
from blue_contracts import Processor,ContractError,RuntimeBinding,export_snapshot,import_snapshot,export_invocation,import_invocation,compare_replay
from blue_contracts.reference.model import Meter,segments,pointer
from blue_bex import UNDEFINED,GasExhausted
from algorithms import blue as L
from .scenarios import execute,ids,install_extensions

def T(name,**v):return {'type':'Contracts/'+name,**v}
def change(path,val,op='replace'):return {'op':op,'path':path,**({'val':val} if op!='remove' else {})}
def update(*rows):return T('Update Document',changeset=list(rows))
def compute(*rows):return T('Compute',do=list(rows))
def flow(*steps,channel='input',order=0,**v):return T('Sequential Workflow',channel=channel,order=order,steps=list(steps),**v)
def operation(*steps,channel='input',order=0,**v):return T('Sequential Workflow Operation',channel=channel,order=order,steps=list(steps),**v)
def call(amount=3,**v):return T('Operation Request',channel='input',operation='add',request={'amount':amount},**v)
def counter(extra=None):
    d={'count':0,'before':-1,'after':-1,'contracts':{
        'input':T('External Channel'),
        'add':operation(compute({'$appendChange':change('/count',{'$add':[{'$document':'/count'},{'$binding':'call/request/amount'}]})}),order=10,request={'amount':{'type':'Integer','schema':{'required':True}}}),
        'before':flow(update(change('/before',{'$document':'/count'})),order=0),
        'after':flow(update(change('/after',{'$document':'/count'})),order=20)}}
    if extra:d['contracts'].update(extra)
    return d

class EventAPI(unittest.TestCase):
    def setUp(self):self.p=Processor()
    def run_case(self,event,doc=None,t=1000000):
        self.s=self.p.create(doc or counter());return self.p.process(self.s,event,t)
    def assertGood(self,out):self.assertEqual(out.status,'APPLIED',out.diagnostic)
    def assertFailure(self,out,code=None):
        self.assertEqual(out.status,'FAILED',out.diagnostic);self.assertEqual(out.document.identity,self.s.identity);self.assertEqual(out.public_events,[])
        if code:self.assertEqual(out.diagnostic['code'],code)
    def test_signature_exact(self):self.assertEqual(list(inspect.signature(self.p.process).parameters),['document','event','eventTimestamp'])
    def test_direct_call_and_workflow_order(self):
        o=self.run_case(call());self.assertGood(o);self.assertEqual([self.p.read(o.document,x) for x in ['/before','/count','/after']],[0,3,3])
    def test_nested_call(self):
        o=self.run_case({'tag':'outer','operation':call()});self.assertGood(o);self.assertEqual(self.p.read(o.document,'/count'),3)
    def test_deeper_request_not_a_call(self):
        o=self.run_case({'nested':{'operation':call()}});self.assertGood(o);self.assertEqual(self.p.read(o.document,'/count'),0)
    def test_old_message_shape_not_a_call(self):
        o=self.run_case({'message':call()});self.assertGood(o);self.assertEqual(self.p.read(o.document,'/count'),0)
    def test_untyped_shape_not_a_call(self):
        event=call();del event['type'];o=self.run_case(event);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/count'),0)
    def test_unknown_operation_fails_before_observers(self):
        e=call();e['operation']='missing';self.assertFailure(self.run_case(e),'INVALID_TARGET_OPERATION')
    def test_unaddressed_missing_channel_is_no_operation_match(self):
        # Lazy/routing revision: ordinary observers retain independent rights.
        e=call();e['channel']='missing';out=self.run_case(e);self.assertGood(out)
        self.assertEqual(self.p.read(out.snapshot,'/count'),0)
        self.assertEqual(self.p.read(out.snapshot,'/before'),0)
        self.assertEqual(self.p.read(out.snapshot,'/after'),0)
    def test_addressed_wrong_channel_is_rejected(self):
        self.s=self.p.create(counter());e=call(document={'blueId':self.s.documents[self.s.root].blue_id})
        e['channel']='missing';self.assertFailure(self.p.process(self.s,e,1),'INVALID_TARGET_CHANNEL')
    def test_invalid_arguments(self):self.assertFailure(self.run_case(call('bad')),'INVALID_REQUEST')
    def test_required_missing(self):
        e=call();e['request']={};self.assertFailure(self.run_case(e),'INVALID_REQUEST')
    def test_optional_request_not_invented(self):
        e=call();del e['request'];self.assertFailure(self.run_case(e),'INVALID_REQUEST')
    def test_optional_request_allowed_when_not_required(self):
        d={'count':0,'contracts':{'input':T('External Channel'),'go':operation(update(change('/count',1)))}}
        o=self.run_case(T('Operation Request',channel='input',operation='go'),d);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/count'),1)
    def test_invalid_call_fields(self):
        e=call();e['payloadPath']='/x';self.assertFailure(self.run_case(e),'INVALID_OPERATION_REQUEST')
    def test_exact_precondition_success(self):
        self.s=self.p.create(counter());e=call(document={'blueId':self.s.documents[self.s.root].blue_id},requireExactDocumentVersion=True);self.assertGood(self.p.process(self.s,e,1))
    def test_exact_precondition_failure(self):
        self.s=self.p.create(counter());e=call(document={'blueId':self.p.blue.identity(self.p.blue.source({'count':999}))},requireExactDocumentVersion=True);self.assertFailure(self.p.process(self.s,e,1),'STALE_DOCUMENT_PRECONDITION')
    def test_exact_precondition_requires_document(self):self.assertFailure(self.run_case(call(requireExactDocumentVersion=True)),'INVALID_OPERATION_REQUEST')
    def test_checkpoint_original_event(self):
        e={'outer':'preserved','operation':call()};o=self.run_case(e,t=1234567);self.assertGood(o);row=o.checkpoints[0]['after'];self.assertEqual(row,{'timestamp':1234567,'event':{'blueId':self.p.blue.identity(self.p.blue.source(e))}})
    def test_duplicate_last_event(self):
        o=self.run_case(call());again=self.p.process(o.document,call(),1000000);self.assertGood(again);self.assertEqual(self.p.read(again.document,'/count'),3);self.assertEqual(again.checkpoints,[])
    def test_duplicate_timestamp_conflict(self):
        o=self.run_case(call());self.s=o.document;self.assertFailure(self.p.process(self.s,call(),1000001),'EVENT_TIMESTAMP_CONFLICT')
    def test_distinct_events_same_timestamp(self):
        o=self.run_case(call());o=self.p.process(o.document,call(4),1000000);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/count'),7)
    def test_no_invented_timestamp_ordering(self):
        o=self.run_case(call());o=self.p.process(o.document,call(4),1);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/count'),7)
    def test_timestamp_must_be_integer_not_bool(self):
        for t in [True,1.5,'1',-1]:
            with self.subTest(timestamp=t),self.assertRaises(ContractError):self.p.process(counter(),call(),t)
    def test_original_event_in_external_handler(self):
        d=counter({'capture':flow(update(change('/captured',{'$event':'/outer'},'add')),order=30)})
        o=self.run_case({'outer':'kept','operation':call()},d);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/captured'),'kept')
    def test_internal_event_and_external_context_restoration(self):
        d=counter();d.update(internal='none',outer='none');d['contracts']['updates']=T('Document Update Channel',path='/count')
        d['contracts']['capture']=flow(update(change('/internal',{'$event':'/op'})),channel='updates')
        d['contracts']['after']['steps'].append(update(change('/outer',{'$event':'/outer'})))
        o=self.run_case({'outer':'complete','operation':call()},d);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/internal'),'replace');self.assertEqual(self.p.read(o.document,'/outer'),'complete')
    def test_missing_filter_field_not_synthesized(self):
        d={'seen':0,'contracts':{'input':T('External Channel',event={'status':'settled'}),'seen':flow(update(change('/seen',1)))}}
        o=self.run_case({'amount':10},d);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/seen'),0);self.assertEqual(o.checkpoints,[])
    def test_empty_filter_accepts_empty_event(self):
        d={'seen':0,'contracts':{'input':T('External Channel',event={}), 'seen':flow(update(change('/seen',1)))}}
        o=self.run_case({},d);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/seen'),1)
    def test_typed_filter_nominal_ancestry(self):
        p=self.p;a=p.blue.source(p.typed('Document Processing Initiated',document={'blueId':p.blue.identity(p.blue.source({}))}));self.assertFalse(p.blue.matches(a,{'type':{'blueId':p.registry.types['Document Processing Terminated']}}))
    def test_event_extra_fields_allowed(self):self.assertTrue(self.p.blue.matches({'kind':'paid','amount':10},{'kind':'paid'}))
    def test_absent_filter_field_false(self):self.assertFalse(self.p.blue.matches({'amount':10},{'kind':'paid'}))
    def test_schema_filter_threshold(self):
        for value,want in [(100,True),(99,False)]:self.assertEqual(self.p.blue.matches({'amount':value},{'amount':{'type':{'blueId':L.CORE['Integer']},'schema':{'minimum':100}}}),want)
    def test_missing_filter_schema_field_false(self):self.assertFalse(self.p.blue.matches({}, {'amount':{'type':{'blueId':L.CORE['Integer']},'schema':{'minimum':100}}}))
    def test_when_rejected(self):
        d=counter();d['contracts']['before']['when']=True
        with self.assertRaises(ContractError):self.p.create(d)
    def test_step_forbidden_top_level(self):
        d=counter();d['contracts']['invalid']=update(change('/count',1))
        with self.assertRaises(ContractError):self.p.create(d)
    def test_operation_is_handler(self):self.assertIn(self.p.registry.types['Handler'],L.ancestry(self.p.registry.types['Operation'],self.p.blue.context))
    def test_initialize_marker_exact_preimage(self):
        d=counter();tid=self.p.blue.identity(self.p.blue.source(d));s=self.p.create(d);marker=self.p.registry.marker(s.documents[s.root].body,'initialized');self.assertEqual(self.p.blue.literal(marker)['document']['blueId'],tid)
    def test_initialize_no_checkpoint(self):self.assertIsNone(self.p.registry.marker(self.p.create(counter()).documents['root'].body,'checkpoint'))
    def test_initialize_existing_does_not_repeat(self):
        o=self.p.initialize(counter());again=self.p.initialize(o.document);self.assertGood(again);self.assertEqual(again.public_events,[])
    def test_raw_document_one_atomic_process(self):
        o=self.p.process(counter(),call(),1);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/count'),3)
    def test_replay_identical(self):
        o=self.run_case(call());again=self.p.process(self.s,call(),1000000);self.assertEqual(o.observations(),again.observations())
    def test_snapshot_roundtrip_new_processor(self):
        self.s=self.p.create(counter());payload=export_snapshot(self.p,self.s);other=Processor();restored=import_snapshot(other,payload,payload['identity']);self.assertEqual(restored.identity,self.s.identity)
    def test_replay_capsule_fresh_processor(self):
        self.s=self.p.create(counter());e={'operation':call(),'tag':'outer'};a=self.p.process(self.s,e,123)
        capsule=export_invocation(self.p,self.s,self.p.blue.source(e),123);other=Processor();s,event,t=import_invocation(other,capsule,capsule['identity']);b=other.process(s,event,t);self.assertEqual(a.observations(),b.observations())
    def test_snapshot_tamper_rejected(self):
        s=self.p.create(counter());payload=export_snapshot(self.p,s);payload['snapshot']['revision']+=1
        with self.assertRaises(ContractError):import_snapshot(Processor(),payload,payload['identity'])
    def test_unused_executable_not_compiled(self):
        d=counter({'unused':operation(T('Compute',do=[{'$notAnOperator':True}]))});o=self.run_case(call(),d);self.assertGood(o)
        e=call();e['operation']='unused';self.s=o.document;self.assertFailure(self.p.process(self.s,e,2))
    def test_event_emitting_request_does_not_reinvoke(self):
        d=counter();d['contracts']['add']['steps'].append(T('Trigger Event',event={'$binding':'call'}));o=self.run_case(call(),d);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/count'),3);self.assertEqual(len(o.public_events),1)
    def test_shared_gas_exhaustion_rolls_back(self):
        self.s=self.p.create(counter());self.p.gas_limit=1;o=self.p.process(self.s,call(),1);self.assertEqual(o.status,'GAS_LIMIT_EXCEEDED');self.assertEqual(o.document.identity,self.s.identity);self.assertIsNotNone(o.rejected)
    def test_local_gas_exhaustion_rolls_back(self):
        self.s=self.p.create(counter());self.p.local_limits={'root':1};o=self.p.process(self.s,call(),1);self.assertEqual(o.status,'GAS_LIMIT_EXCEEDED');self.assertEqual(o.rejected['cap'],'LOCAL');self.assertEqual(o.document.identity,self.s.identity)
    def test_business_failure_rolls_back_init(self):
        d={'count':0,'contracts':{'input':T('External Channel'),'fail':operation(update(change('/count',1)),compute({'$fail':'expected'}))}}
        o=self.p.process(d,T('Operation Request',channel='input',operation='fail'),1);self.assertEqual(o.status,'FAILED');self.assertIsNone(self.p.registry.marker(o.document.documents['root'].body,'initialized'));self.assertEqual(self.p.read(o.document,'/count'),0)
    def test_parent_cannot_patch_child(self):
        d={'child':{'count':0},'contracts':{'embedded':T('Process Embedded',paths=['/child']),'input':T('External Channel'),'go':operation(update(change('/child/count',1)))}}
        self.assertFailure(self.run_case(T('Operation Request',channel='input',operation='go'),d))
    def test_parent_may_replace_whole_child(self):
        d={'child':{'count':0},'contracts':{'embedded':T('Process Embedded',paths=['/child']),'input':T('External Channel'),'go':operation(update(change('/child',{'count':10})))}}
        o=self.run_case(T('Operation Request',channel='input',operation='go'),d);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/child/count'),10)
    def test_protected_marker_cannot_be_removed(self):
        d=counter();d['contracts']['add']['steps']=[update(change('/contracts/initialized',None,'remove'))];self.assertFailure(self.run_case(call(),d),'PROTECTED_STATE_MUTATION')
    def test_noop_patch_no_update(self):
        d={'count':0,'seen':0,'contracts':{'input':T('External Channel'),'go':operation(update(change('/count',0))), 'updates':T('Document Update Channel',path='/count'),'seen':flow(update(change('/seen',1)),channel='updates')}}
        o=self.run_case(T('Operation Request',channel='input',operation='go'),d);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/seen'),0)
    def test_list_remove_reports_absent_after(self):
        d={'itemsList':['a','b'],'removed':False,'contracts':{'input':T('External Channel'),'go':operation(update(change('/itemsList/0',None,'remove'))),'updates':T('Document Update Channel',path='/itemsList'),'seen':flow(update(change('/removed',{'$event':'/afterPresent'})),channel='updates')}}
        o=self.run_case(T('Operation Request',channel='input',operation='go'),d);self.assertGood(o);self.assertEqual(self.p.read(o.document,'/itemsList'),['b']);self.assertIs(self.p.read(o.document,'/removed'),False)
    def test_pointers_escape_roundtrip(self):self.assertEqual(segments(pointer(['children','a/b~c'])),('children','a/b~c'))
    def test_extension_exact_category(self):
        tid=self.p.blue.identity(self.p.blue.source({'name':'NotAChannel'},goal='definition'));sid=self.p.blue.identity(self.p.blue.source('test'));binding=RuntimeBinding(tid,sid,'external-channel',(),(),'test',( ('one',1),))
        with self.assertRaises(ContractError):self.p.install_runtime(binding,object())

class TutorialScenarios(unittest.TestCase):
    """One test per YAML scenario; includes exact check points and failures."""
for name in ids():
    def test(self,name=name):execute(name)
    setattr(TutorialScenarios,'test_'+name.replace('-','_'),test)

if __name__=='__main__':unittest.main()
