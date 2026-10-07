"""Executable acceptance checks against the actual signed Coordination engine."""
import sys,json,time,unittest,tempfile,hashlib
from pathlib import Path
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
from session import Session,operation,change,workflow
from blue_coordination.engine import CoordinationEngine,MemoryStore,SQLiteStore
from blue_coordination.engine.mandate_package import supported_definition
from blue_coordination_spec.model import CoordinationError
from algorithms import blue as L


def scope_keys(s,h):return set(s.read(h,'/scope'))-{'type'}
def event_rows(s,name):
    tid=s.repo.aliases['Mandates/'+name]
    return [x for x in s.events() if x['content'].get('type',{}).get('blueId')==tid]

def bounded(s,target):
    g=s.grant(target,validation={'request':{'amount':2},
        'function':{'expr':{'$eq':[{'$keys':{'$binding':'request'}},['amount']]}}})
    g['target']['documentValidation']={'document':s.typ('Pattern',valueType={'count':{'type':'Integer','schema':{'required':True}}}),
        'function':{'expr':{'$and':[{'$gte':[{'$binding':'targetDocument/count'},0]},
                                   {'$lte':[{'$binding':'targetDocument/count'},98]}]}}}
    return g

class Base(unittest.TestCase):
    def session(self,**kw):
        s=Session(**kw);self.addCleanup(s.close);return s
    def fixture(self,*,scope=True,target_source=None,approve=True,**session_kw):
        s=self.session(**session_kw)
        target=s.add(target_source(s) if target_source else s.counter_source())
        m=s.add(s.mandate_source({'byTwo':bounded(s,target)} if scope else {}))
        if approve:s.approve(m)
        return s,target,m,s.authority(m)
    def call(self,s,t,a,amount=2,**kw):return s.invoke('agent',t,'increment',{'amount':amount},channel='ownerChannel',authority=a,**kw)
    def fail_initialization(self,s,source,code):
        h=s.engine.add(source)
        row=s.wait(h,lambda r:r['processing']['state']=='ERROR',allow_error=True)
        self.assertIsNone(row['lastStable'])
        self.assertEqual(row['processing']['issue']['code'],code)

class PackageSupport(Base):
    def test_01_loading_data_does_not_enable_native_support(self):
        s=self.session(enabled=False)
        self.fail_initialization(s,s.mandate_source(),'INVALID_CONTRACT_ROLE')
    def test_02_unknown_package_is_rejected_synchronously(self):
        with self.assertRaises(CoordinationError) as caught:
            CoordinationEngine(supported_packages=['not-a-supported-exact-package'])
        self.assertEqual(caught.exception.code,'UNSUPPORTED_AUTHORITY_PACKAGE')
    def test_03_support_set_is_bound_to_durable_context(self):
        s=self.session();s.close()
        with self.assertRaises(CoordinationError) as caught:
            CoordinationEngine(store=s.store,hub=s.hub,repository=s.repo,supported_packages=s.runtime.supported_packages[:-1])
        self.assertEqual(caught.exception.code,'INCOMPATIBLE_ENGINE_RELEASE')
    def test_04_message_schemas_reject_missing_and_unknown_results(self):
        s=self.session();t=s.add(s.counter_source())
        req=s.typ('Evidence Requested',requestId='source-entry',recipientChannel='evidenceProviderChannel',responseOperation='provideEvidence',operationId='check',operationRevision=1,document={'blueId':s.row(t)['documentId']})
        rid=s.engine.publish_content(req)
        valid=s.typ('Evidence Responded',inResponseTo={'blueId':rid},executionId='exec',executionStatus='Succeeded',result={'qualified':True})
        s.engine.publish_content(valid)
        for field in ('inResponseTo','executionId','executionStatus','result'):
            value=deepcopy(valid);value.pop(field)
            with self.subTest(field=field),self.assertRaises(Exception):s.engine.publish_content(value)
        bad=deepcopy(valid);bad['executionStatus']='invented'
        with self.assertRaises(Exception):s.engine.publish_content(bad)
        for field in ('requestId','recipientChannel','responseOperation','operationId','operationRevision','document'):
            value=deepcopy(req);value.pop(field)
            with self.subTest(request_field=field),self.assertRaises(Exception):s.engine.publish_content(value)
    def test_05_participants_must_be_distinct(self):
        s=self.session();src=s.mandate_source();src['contracts']['authorizedActorChannel']=s.channel('holder')
        self.fail_initialization(s,src,'INVALID_MANDATE_PARTICIPANTS')
    def test_06_future_predicates_are_prepared_before_authority(self):
        s=self.session();t=s.add(s.counter_source());g=s.grant(t,validation={'function':{'expr':3}})
        src=s.mandate_source(grantTemplates={'future':g})
        self.fail_initialization(s,src,'INVALID_AUTHORITY_PREDICATE')
    def test_07_effectful_predicate_is_not_a_permission(self):
        s=self.session();t=s.add(s.counter_source())
        g=s.grant(t,validation={'function':{'expr':True,'functions':{'hidden':{'do':[{'$appendEvent':{'kind':'bad'}}]}}}})
        self.fail_initialization(s,s.mandate_source({'bad':g}),'EFFECTFUL_AUTHORITY_PREDICATE')
    def test_08_plain_untyped_scope_values_receive_contextual_types(self):
        s=self.session();t=s.add(s.counter_source());g=s.grant(t);g.pop('type')
        m=s.add(s.mandate_source({'plain':g}));s.approve(m)
        self.call(s,t,s.authority(m));self.assertEqual(s.read(t,'/count'),2)

class Authority(Base):
    def test_10_owner_approval_then_real_agent_call(self):
        s,t,m,a=self.fixture();entry=self.call(s,t,a)
        self.assertEqual(s.read(t,'/count'),2);self.assertEqual(entry.actor,s.actors['agent'])
        self.assertEqual(s.engine.history(t)['items'][-1]['effectiveOrder'][2],entry.blue_id)
        self.assertEqual(len(event_rows(s,'Mandate Initialized')),1)
        self.assertEqual(len(event_rows(s,'Mandate Approved')),1)
    def test_11_pending_scope_and_agent_presence_give_no_authority(self):
        s,t,m,a=self.fixture(approve=False)
        self.call(s,t,a);self.assertEqual(s.read(t,'/count'),0)
        s.invoke('agent',t,'increment',{'amount':2},channel='ownerChannel');self.assertEqual(s.read(t,'/count'),0)
        s.approve(m);self.call(s,t,a);self.assertEqual(s.read(t,'/count'),2)
    def test_12_empty_scope_and_owner_direct_call(self):
        s,t,m,a=self.fixture(scope=False)
        self.call(s,t,a);self.assertEqual(s.read(t,'/count'),0)
        s.invoke('holder',t,'increment',{'amount':3},channel='ownerChannel');self.assertEqual(s.read(t,'/count'),3)
    def test_13_wrong_amount_extra_keys_and_document_predicate(self):
        s,t,m,a=self.fixture(target_source=lambda s:s.counter_source(count=98))
        self.call(s,t,a,3);self.assertEqual(s.read(t,'/count'),98)
        s.invoke('agent',t,'increment',{'amount':2,'extra':True},channel='ownerChannel',authority=a)
        self.assertEqual(s.read(t,'/count'),98)
        self.call(s,t,a);self.assertEqual(s.read(t,'/count'),100)
        self.call(s,t,a);self.assertEqual(s.read(t,'/count'),100)
    def test_14_one_complete_grant_no_field_mixing(self):
        s=self.session();t=s.add(s.counter_source());g=s.grant(t,validation={'request':{'amount':3}})
        other=s.grant(t,'anotherOperation',validation={'request':{'amount':2}})
        m=s.add(s.mandate_source({'a':g,'b':other}));s.approve(m)
        self.call(s,t,s.authority(m));self.assertEqual(s.read(t,'/count'),0)
    def test_15_wrong_logical_target(self):
        s,t,m,a=self.fixture();other=s.add(s.counter_source(name='Other'))
        self.call(s,other,a);self.assertEqual(s.read(other,'/count'),0)
    def test_16_holder_identity_and_real_actor_are_checked(self):
        s,t,m,a=self.fixture()
        bad=s.authority(m,holder='other');self.call(s,t,bad);self.assertEqual(s.read(t,'/count'),0)
        src=s.counter_source();src['contracts']['otherChannel']=s.channel('other');other=s.add(src)
        s.invoke('other',other,'increment',{'amount':2},channel='ownerChannel',authority=a)
        self.assertEqual(s.read(other,'/count'),0)
    def test_17_target_must_contain_agent_timeline(self):
        s,t,m,a=self.fixture(target_source=lambda s:s.counter_source(include_agent=False))
        self.call(s,t,a);self.assertEqual(s.read(t,'/count'),0)
    def test_18_separate_document_timeline_for_same_actor_is_supported(self):
        s=self.session()
        provider=s.hub.create('agent-on-target',[s.actors['agent']],key=s.keys['agent'])
        t=s.add(s.counter_source(agent_provider=provider));m=s.add(s.mandate_source({'grant':s.grant(t)}));s.approve(m)
        self.call(s,t,s.authority(m),provider=provider);self.assertEqual(s.read(t,'/count'),2)
    def test_19_non_delegable_target_policy_wins(self):
        def source(s):
            result=s.counter_source();result['contracts']['policy']=s.hub.catalogue.typed('Actor Policy',operations={'increment':{'allowsDelegation':False}});return result
        s,t,m,a=self.fixture(target_source=source)
        self.call(s,t,a);self.assertEqual(s.read(t,'/count'),0)
        s.invoke('holder',t,'increment',{'amount':2},channel='ownerChannel');self.assertEqual(s.read(t,'/count'),2)
    def test_20_owner_approval_must_pin_exact_current_state(self):
        s,t,m,a=self.fixture(approve=False)
        s.invoke('holder',m,'approveMandate');self.assertEqual(s.read(m,'/status'),'Pending')
        s.invoke('holder',m,'approveMandate',exact=True,document=s.row(m)['documentId']);self.assertEqual(s.read(m,'/status'),'Pending')
        before=s.row(m)['lastStable']['blueId'];s.approve(m)
        self.assertEqual(event_rows(s,'Mandate Approved')[0]['content']['reviewedDocumentId'],before)
    def test_21_agent_cannot_approve_owner_program(self):
        s,t,m,a=self.fixture(approve=False)
        s.invoke('agent',m,'approveMandate',channel='authorityHolderChannel',exact=True)
        self.assertEqual(s.read(m,'/status'),'Pending')
    def test_22_fabricated_active_start_is_reset(self):
        s=self.session();src=s.mandate_source(status='Active',approvedAt=10,terminatedAt=20)
        m=s.add(src);self.assertEqual(s.read(m,'/status'),'Pending')
        self.assertEqual(len(event_rows(s,'Mandate Approved')),0)
    def test_23_extra_writer_cannot_forge_activation(self):
        s=self.session();src=s.mandate_source()
        src['contracts']['fake']=operation('authorizedActorChannel',[change('/status','Active')])
        m=s.add(src);before=s.row(m)['lastStable']
        s.invoke('agent',m,'fake',expect_error=True)
        self.assertEqual(s.row(m)['processing']['issue']['code'],'PROTECTED_MANDATE_WRITER')
        self.assertEqual(s.row(m)['lastStable'],before)
    def test_24_revocation_preserves_prior_effects_and_owner_authority(self):
        s,t,m,a=self.fixture();self.call(s,t,a)
        s.invoke('holder',m,'terminateMandate',{'reason':'Agent reassigned'})
        self.assertEqual(s.read(m,'/status'),'Terminated');self.assertEqual(scope_keys(s,m),set())
        self.call(s,t,a);self.assertEqual(s.read(t,'/count'),2)
        s.invoke('holder',t,'increment',{'amount':2},channel='ownerChannel');self.assertEqual(s.read(t,'/count'),4)
        self.assertEqual(event_rows(s,'Mandate Terminated')[0]['content']['reason'],'Agent reassigned')
    def test_25_multiple_targets_one_mandate(self):
        s=self.session();a=s.add(s.counter_source(name='A'));b=s.add(s.counter_source(name='B'))
        m=s.add(s.mandate_source({'a':bounded(s,a),'b':s.grant(b,validation={'request':{'amount':5}})}));s.approve(m);authority=s.authority(m)
        self.call(s,a,authority,2);self.call(s,b,authority,5)
        self.assertEqual([s.read(x,'/count') for x in [a,b]],[2,5])
    def test_26_invalid_scope_installation_cannot_publish(self):
        s=self.session();src=s.mandate_source()
        src['contracts']['bad']=operation('authorizedActorChannel',[change('/scope',{'bad':{'target':{'channel':'ownerChannel'}}})])
        m=s.add(src);s.approve(m);before=s.row(m)['lastStable']
        s.invoke('agent',m,'bad',expect_error=True)
        self.assertEqual(scope_keys(s,m),set())
        self.assertEqual(s.row(m)['lastStable'],before)
    def test_27_restart_retains_approval_and_exact_authority_reference(self):
        s,t,m,a=self.fixture();s.restart();self.call(s,t,a);self.assertEqual(s.read(t,'/count'),2)

if __name__=='__main__':unittest.main(verbosity=2)

class Evidence(Base):
    def gate(self,*,approve=True):
        s=self.session();t=s.add(s.counter_source())
        src=s.mandate_source(type_name='Qualification Mandate',
            evidenceRequirement={'operationId':'customer.qualify','operationRevision':1,'document':{'blueId':s.row(t)['documentId']}},
            scopeOnSuccess={'byTwo':bounded(s,t)})
        src['contracts']['evidenceProviderChannel']=s.channel('provider')
        m=s.add(src)
        if approve:s.approve(m)
        return s,t,m,s.authority(m)
    def request(self,s,m):
        entry=s.invoke('agent',m,'requestEvidence')
        self.assertEqual(s.read(m,'/stage'),'EvidencePending')
        return s.value_id(m,'/pendingEvidence'),entry
    def response(self,s,m,rid,status='Succeeded',result=None,execution='execution-1',side='provider'):
        value=s.typ('Evidence Responded',inResponseTo={'blueId':rid},executionId=execution,executionStatus=status,
            result=({'qualified':True} if status=='Succeeded' else {}) if result is None else result)
        bid=s.engine.publish_content(value)
        s.invoke(side,m,'provideEvidence',{'blueId':bid},channel='evidenceProviderChannel')
        return bid
    def test_30_real_typed_request_response_exact_correlation_and_actor(self):
        s,t,m,a=self.gate();rid,entry=self.request(s,m)
        requests=event_rows(s,'Evidence Requested');self.assertEqual(len(requests),1)
        self.assertEqual(requests[0]['event']['event'],rid)
        self.assertEqual(requests[0]['content']['requestId'],entry.blue_id)
        self.assertEqual(entry.actor,s.actors['agent'])
        response=self.response(s,m,rid)
        self.assertEqual(s.read(m,'/stage'),'EvidencePassed');self.assertEqual(scope_keys(s,m),{'byTwo'})
        replies=event_rows(s,'Evidence Responded');self.assertEqual(len(replies),1)
        self.assertEqual(replies[0]['event']['event'],response)
        self.assertEqual(replies[0]['content']['inResponseTo'],{'blueId':rid})
        self.assertEqual(s.value_id(m,'/evidenceResponse'),response)
        with s.hub.lock,s.hub.cache.scope(),s.store.read() as v:
            c=s.hub.catalogue;c.blue.language.bind(v);c.blue.refresh()
            try:
                self.assertEqual(c.link(rid,'document'),s.row(t)['documentId'])
                self.assertTrue(c.is_type(L.Ref(rid),'Request'))
                self.assertTrue(c.is_type(L.Ref(response),'Response'))
                self.assertEqual(c.link(response,'inResponseTo'),rid)
            finally:c.blue.language.bind(None);c.blue.refresh()
        self.call(s,t,a);self.assertEqual(s.read(t,'/count'),2)
    def test_31_unknown_reconciles_only_same_execution(self):
        s,t,m,a=self.gate();rid,_=self.request(s,m)
        self.response(s,m,rid,'Unknown');self.assertEqual(s.read(m,'/stage'),'EvidencePending')
        self.assertEqual(scope_keys(s,m),set());self.call(s,t,a);self.assertEqual(s.read(t,'/count'),0)
        self.response(s,m,rid,execution='another-execution');self.assertEqual(s.read(m,'/stage'),'EvidencePending')
        self.response(s,m,rid);self.assertEqual(s.read(m,'/stage'),'EvidencePassed')
        self.assertEqual(len(event_rows(s,'Evidence Responded')),2)
    def test_32_false_failure_and_refusal_do_not_enable_grants(self):
        for status,result in [('Succeeded',{'qualified':False}),('Failed',{}),('Refused',{})]:
            with self.subTest(status=status):
                s,t,m,a=self.gate();rid,_=self.request(s,m)
                self.response(s,m,rid,status,result);self.assertEqual(s.read(m,'/stage'),'NeedsReview')
                self.assertEqual(scope_keys(s,m),set())
                self.call(s,t,a);self.assertEqual(s.read(t,'/count'),0)
                s.close()
    def test_33_modified_request_same_request_id_cannot_be_answered(self):
        s,t,m,a=self.gate();rid,_=self.request(s,m)
        copied=deepcopy(event_rows(s,'Evidence Requested')[0]['content']);copied['operationId']='weaker-check'
        fake=s.engine.publish_content(copied);self.assertNotEqual(fake,rid)
        self.response(s,m,fake);self.assertEqual(s.read(m,'/stage'),'EvidencePending')
        self.assertEqual(len(event_rows(s,'Evidence Responded')),0)
        self.response(s,m,rid);self.assertEqual(s.read(m,'/stage'),'EvidencePassed')
    def test_34_agent_cannot_supply_provider_response(self):
        s,t,m,a=self.gate();rid,_=self.request(s,m)
        self.response(s,m,rid,side='agent');self.assertEqual(s.read(m,'/stage'),'EvidencePending')
        self.assertEqual(len(event_rows(s,'Evidence Responded')),0)
    def test_35_exact_retry_is_not_a_second_response(self):
        s,t,m,a=self.gate();rid,_=self.request(s,m)
        response=self.response(s,m,rid);self.assertEqual(s.read(m,'/stage'),'EvidencePassed')
        s.invoke('provider',m,'provideEvidence',{'blueId':response})
        self.assertEqual(len(event_rows(s,'Evidence Responded')),1)
        self.assertEqual(scope_keys(s,m),{'byTwo'})
    def test_36_no_repeat_check_or_agent_selected_recipe(self):
        s,t,m,a=self.gate()
        s.invoke('agent',m,'requestEvidence',{'operationId':'weaker'})
        self.assertEqual(len(event_rows(s,'Evidence Requested')),0)
        self.request(s,m);s.invoke('agent',m,'requestEvidence')
        self.assertEqual(len(event_rows(s,'Evidence Requested')),1)
    def test_37_closed_result_shape_and_boolean_are_enforced(self):
        s,t,m,a=self.gate();rid,_=self.request(s,m)
        for result in [{'qualified':'yes'},{'qualified':True,'extra':'private'},{}]:
            self.response(s,m,rid,result=result);self.assertEqual(s.read(m,'/stage'),'EvidencePending')
        self.assertEqual(len(event_rows(s,'Evidence Responded')),0)
        self.response(s,m,rid);self.assertEqual(s.read(m,'/stage'),'EvidencePassed')
    def test_38_bare_response_is_not_an_operation(self):
        s,t,m,a=self.gate();rid,_=self.request(s,m)
        value=s.typ('Evidence Responded',inResponseTo={'blueId':rid},executionId='execution-1',executionStatus='Succeeded',result={'qualified':True})
        s.time+=100;timestamp=s.time
        s.hub.append(s.providers['provider'].timeline,s.actors['provider'],timestamp,value)
        s.wait(m,lambda r:r['processing']['checkedBoundary']>timestamp)
        self.assertEqual(s.read(m,'/stage'),'EvidencePending');self.assertEqual(len(event_rows(s,'Evidence Responded')),0)
    def test_39_known_final_result_cannot_be_replaced(self):
        s,t,m,a=self.gate();rid,_=self.request(s,m)
        response=self.response(s,m,rid,'Succeeded',{'qualified':False})
        self.response(s,m,rid,'Succeeded',{'qualified':True})
        self.assertEqual(s.read(m,'/stage'),'NeedsReview');self.assertEqual(scope_keys(s,m),set())
        self.assertEqual(s.value_id(m,'/evidenceResponse'),response)
    def test_40_gate_requires_owner_approval(self):
        s,t,m,a=self.gate(approve=False);s.invoke('agent',m,'requestEvidence')
        self.assertEqual(s.read(m,'/status'),'Pending');self.assertEqual(len(event_rows(s,'Evidence Requested')),0)

from order_flow import order,mandate as order_mandate

class Connected(Base):
    def setup_order(self,**kw):
        s=self.session(workers=2);t,events=order(s);m=order_mandate(s,t,events,**kw);s.approve(m)
        return s,t,m,s.authority(m),events
    def await_scope(self,s,m,key):
        s.wait(m,lambda r: scope_keys(s,m)==({key} if key else set()))
    def test_50_real_child_events_replace_scope_then_terminate(self):
        s,t,m,a,ev=self.setup_order()
        first=s.invoke('agent',t,'approveOrder',channel='sellerChannel',authority=a)
        self.assertEqual(s.read(t,'/phase'),'Approved');self.await_scope(s,m,'release')
        self.assertEqual(s.read(m,'/stage'),'ReleaseEnabled')
        self.assertEqual(len(event_rows(s,'Scope Changed')),1)
        second=s.invoke('agent',t,'releaseForFulfilment',{'method':'standard'},channel='sellerChannel',authority=a)
        self.assertEqual(s.read(t,'/phase'),'Released')
        s.wait(m,lambda r:s.read(m,'/status')=='Terminated')
        self.assertEqual(scope_keys(s,m),set());self.assertEqual(s.read(m,'/stage'),'Finished')
        self.assertEqual(len(event_rows(s,'Mandate Terminated')),1)
        self.assertEqual([h['effectiveOrder'][2] for h in s.engine.history(t)['items'][1:]],[first.blue_id,second.blue_id])
        self.assertNotEqual(s.row(t)['processing']['state'],'ERROR')
    def test_51_release_cannot_overtake_actual_approval(self):
        s,t,m,a,ev=self.setup_order()
        s.invoke('agent',t,'releaseForFulfilment',{'method':'standard'},channel='sellerChannel',authority=a)
        self.assertEqual(s.read(t,'/phase'),'Proposed');self.assertEqual(scope_keys(s,m),{'approve'})
        s.invoke('agent',t,'approveOrder',channel='sellerChannel',authority=a);self.await_scope(s,m,'release')
        s.invoke('agent',t,'releaseForFulfilment',{'method':'express'},channel='sellerChannel',authority=a)
        self.assertEqual(s.read(t,'/phase'),'Approved')
    def test_52_forged_root_event_does_not_impersonate_child(self):
        s,t,m,a,ev=self.setup_order()
        s.time+=100;ts=s.time
        s.hub.append(s.providers['agent'].timeline,s.actors['agent'],ts,{'type':{'blueId':ev['Approved']}})
        s.wait(m,lambda r:r['processing']['checkedBoundary']>ts)
        self.assertEqual(scope_keys(s,m),{'approve'});self.assertEqual(s.read(m,'/stage'),'ApprovalEnabled')
    def test_53_provider_gate_and_actual_order_progress(self):
        s,t,m,a,ev=self.setup_order(qualified=True)
        s.invoke('agent',t,'approveOrder',channel='sellerChannel',authority=a)
        self.assertEqual(s.read(t,'/phase'),'Proposed')
        s.invoke('agent',m,'requestEvidence');rid=s.value_id(m,'/pendingEvidence')
        bid=s.engine.publish_content(s.typ('Evidence Responded',inResponseTo={'blueId':rid},executionId='order-check',executionStatus='Succeeded',result={'qualified':True}))
        s.invoke('provider',m,'provideEvidence',{'blueId':bid});self.assertEqual(scope_keys(s,m),{'approve'})
        s.invoke('agent',t,'approveOrder',channel='sellerChannel',authority=a);self.await_scope(s,m,'release')
        s.invoke('agent',t,'releaseForFulfilment',{'method':'standard'},channel='sellerChannel',authority=a)
        s.wait(m,lambda r:s.read(m,'/status')=='Terminated');self.assertEqual(s.read(t,'/phase'),'Released')
    def test_54_owner_progress_outside_stage_ends_mandate_not_order(self):
        s,t,m,a,ev=self.setup_order(qualified=True)
        s.invoke('holder',t,'approveOrder',channel='sellerChannel')
        self.assertEqual(s.read(t,'/phase'),'Approved')
        s.wait(m,lambda r:s.read(m,'/status')=='Terminated')
        s.invoke('holder',t,'releaseForFulfilment',{'method':'standard'},channel='sellerChannel')
        self.assertEqual(s.read(t,'/phase'),'Released')
    def test_55_manual_stage_owner_not_agent(self):
        s,t,m,a,ev=self.setup_order(connected=False)
        s.invoke('agent',m,'acknowledgeOrderApproval',channel='authorityHolderChannel')
        self.assertEqual(scope_keys(s,m),{'approve'})
        s.invoke('agent',t,'approveOrder',channel='sellerChannel',authority=a)
        self.assertEqual(scope_keys(s,m),{'approve'})
        s.invoke('holder',m,'acknowledgeOrderApproval');self.assertEqual(scope_keys(s,m),{'release'})
        s.invoke('agent',t,'releaseForFulfilment',{'method':'standard'},channel='sellerChannel',authority=a)
        self.assertEqual(s.read(t,'/phase'),'Released')
    def test_56_early_manual_acknowledgment_does_not_override_target_guard(self):
        s,t,m,a,ev=self.setup_order(connected=False)
        s.invoke('holder',m,'acknowledgeOrderApproval')
        self.assertEqual(scope_keys(s,m),{'release'})
        s.invoke('agent',t,'releaseForFulfilment',{'method':'standard'},channel='sellerChannel',authority=a)
        self.assertEqual(s.read(t,'/phase'),'Proposed')

class Historical(Base):
    def scenario(self,*,owner_first=True,termination=None):
        s=self.session(auto_complete=False,workers=2)
        if (s.providers['holder'].timeline < s.providers['agent'].timeline) != owner_first:
            for table in (s.providers,s.actors,s.keys):table['holder'],table['agent']=table['agent'],table['holder']
        t=s.add(s.counter_source());m=s.add(s.mandate_source({'byTwo':bounded(s,t)}));a=s.authority(m)
        def append(side,h,name,ts,request,channel,authority=None,exact=False):
            message={'type':'Contracts/Operation Request','channel':channel,'operation':name,
                'document':{'blueId':s.row(h)['lastStable']['blueId']},'request':request}
            if exact:message['requireExactDocumentVersion']=True
            return s.hub.append(s.providers[side].timeline,s.actors[side],ts,message,**({'authority':authority} if authority else {}))
        approval=append('holder',m,'approveMandate',100,{},'authorityHolderChannel',exact=True)
        if termination is not None:
            for provider in s.providers.values():provider.close_before(101)
            s.wait(m,lambda r:s.read(m,'/status')=='Active')
            s.engine.close()
            append('holder',m,'terminateMandate',termination,{'reason':'Historical revocation'},'authorityHolderChannel')
        ts=100 if termination is None else 200
        action=append('agent',t,'increment',ts,{'amount':2},'ownerChannel',authority=a)
        boundary=max(ts,termination or 100)+1
        for provider in s.providers.values():provider.close_before(boundary)
        s.engine.start()
        s.wait(t,lambda r:r['processing']['checkedBoundary']>=boundary)
        expected=2*int(owner_first) if termination is None else 2*int(termination>ts)
        self.assertEqual(s.read(t,'/count'),expected)
        if expected:self.assertEqual(s.engine.history(t)['items'][-1]['effectiveOrder'],[ts,action.timeline,action.blue_id])
        if termination is not None:s.wait(m,lambda r:s.read(m,'/status')=='Terminated')
    def test_60_same_timestamp_uses_both_canonical_timeline_orders(self):
        for order_first in (True,False):
            with self.subTest(owner_first=order_first):self.scenario(owner_first=order_first)
    def test_61_delayed_work_uses_before_action_not_latest_revocation(self):
        for termination in (180,300):
            with self.subTest(termination=termination):self.scenario(termination=termination)
    def test_62_incomplete_authority_prefix_waits_then_resumes(self):
        s=self.session(auto_complete=False,workers=2);t=s.add(s.counter_source());m=s.add(s.mandate_source({'byTwo':bounded(s,t)}));a=s.authority(m)
        s.hub.append(s.providers['holder'].timeline,s.actors['holder'],100,{'type':'Contracts/Operation Request',
            'channel':'authorityHolderChannel','operation':'approveMandate','document':{'blueId':s.row(m)['lastStable']['blueId']},'requireExactDocumentVersion':True,'request':{}})
        action=s.hub.append(s.providers['agent'].timeline,s.actors['agent'],200,{'type':'Contracts/Operation Request',
            'channel':'ownerChannel','operation':'increment','document':{'blueId':s.row(t)['lastStable']['blueId']},'request':{'amount':2}},authority=a)
        s.wait(t,lambda r:r['processing']['state']=='WAITING')
        self.assertEqual(s.read(t,'/count'),0)
        for provider in s.providers.values():provider.close_before(201)
        s.wait(t,lambda r:s.read(t,'/count')==2)
        self.assertEqual(s.engine.history(t)['items'][-1]['effectiveOrder'][2],action.blue_id)
    def test_63_sqlite_restart_preserves_new_package_authority(self):
        with tempfile.TemporaryDirectory() as d:
            store=SQLiteStore(Path(d)/'mandates.sqlite')
            with Session(store=store) as s:
                t=s.add(s.counter_source());m=s.add(s.mandate_source({'byTwo':bounded(s,t)}));s.approve(m);a=s.authority(m)
                self.call(s,t,a);s.restart();self.call(s,t,a)
                self.assertEqual(s.read(t,'/count'),4)
                self.assertEqual(len(event_rows(s,'Mandate Approved')),1)

class PatternValidation(Base):
    def test_70_request_required_pattern_witness_matches_actual_payload(self):
        s=self.session();t=s.add(s.counter_source());g=s.grant(t,validation={'request':s.typ('Pattern',valueType={
            'amount':{'type':'Integer','schema':{'required':True,'minimum':2,'maximum':2}}})})
        m=s.add(s.mandate_source({'p':g}));s.approve(m);a=s.authority(m)
        self.call(s,t,a,3);self.assertEqual(s.read(t,'/count'),0)
        self.call(s,t,a,2);self.assertEqual(s.read(t,'/count'),2)
    def test_71_pattern_witness_without_value_type_rejected(self):
        s=self.session();t=s.add(s.counter_source());g=s.grant(t,validation={'request':s.typ('Pattern')})
        self.fail_initialization(s,s.mandate_source({'p':g}),'INVALID_AUTHORITY_PATTERN')
    def test_72_runtime_nonboolean_predicate_cannot_authorize(self):
        s=self.session();t=s.add(s.counter_source());g=s.grant(t,validation={'function':{'expr':{'$size':{'$keys':{'$binding':'request'}}}}})
        m=s.add(s.mandate_source({'p':g}));s.approve(m);a=s.authority(m)
        self.call(s,t,a);self.assertEqual(s.read(t,'/count'),0)
        s.invoke('holder',t,'increment',{'amount':2},channel='ownerChannel');self.assertEqual(s.read(t,'/count'),2)
    def test_73_mutating_approved_future_grants_rejected(self):
        s=self.session();t=s.add(s.counter_source());g=bounded(s,t)
        src=s.mandate_source({'p':g},grantTemplates={'future':g})
        src['contracts']['replaceFuture']=operation('authorizedActorChannel',[change('/grantTemplates',{'$emptyObject':True})])
        m=s.add(src);s.approve(m);before=s.row(m)['lastStable']
        s.invoke('agent',m,'replaceFuture',expect_error=True)
        self.assertEqual(s.row(m)['lastStable'],before)
        self.assertEqual(s.row(m)['processing']['issue']['code'],'PROTECTED_MANDATE_PROGRAM')

if __name__ == '__main__':
    unittest.main()
