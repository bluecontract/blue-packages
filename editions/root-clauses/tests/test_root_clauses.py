"""Integration tests of authored/compiled data against the unmodified runtime."""
from copy import deepcopy
from pathlib import Path
import json,os,sys,time,unittest,traceback
from support import *
from blue_language.physical import PhysicalCache
from blue_runtime.core_reuse import core_reuse_scope

class RootClauses(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=processor(sources=os.environ.get('CLAUSE_TEST_SOURCES')=='1')
  cls.gas={}
  cls.cache={}
 def init(self,**params):
  k=json.dumps(params,sort_keys=True)
  if k not in self.cache:
   o=self.p.initialize(source(**params));self.gas['init'+k]=o.gas;self.cache[k]=good(o)
  return self.cache[k].copy()
 def accepted(self,**params):
  s=self.init(**params)
  for i,side in enumerate('AB'):
   o=op(self.p,s,'act'+side,request(self.p,s,request_id='approval-'+side),100+i)
   self.gas['approve'+side]=o.gas;s=good(o)
  return s
 def denied(self,s,o,code=None):
  self.assertEqual(o.status,'FAILED',o.diagnostic)
  self.assertEqual(o.snapshot.identity,s.identity,'failed attempt must roll back')
  if code:self.assertEqual(o.diagnostic['code'],code)
 def amend(self,s,**kwargs):
  o=op(self.p,s,'amendA',kwargs,250);self.gas['amend']=o.gas;return o
 def termreq(self,s,**kw):
  return dict(requestId='end-1',termsId=self.p.read(s,'/acceptedRevision/termsId'),**kw)
 def test_01_minimal_source_contains_no_generated_state_or_contracts(self):
  raw=source();self.assertNotIn('contracts',raw);self.assertNotIn('clauses',raw)
  self.assertNotIn('terminated',raw);self.assertNotIn('activated',raw)
  doc=self.p.blue.source(raw)
  self.assertIsNone(self.p.blue.select(doc,'/activated'))
  self.assertIsNone(self.p.blue.select(doc,'/contracts/actA'))
 def test_02_initialization_generates_one_managed_agreement(self):
  s=self.init();self.assertEqual(len(s.documents),1)
  for key in ['actA','actB','terminateA','terminateB','completeActivation']:
   self.assertIsNotNone(self.p.blue.select(s.documents[s.root].body,'/contracts/'+key))
  self.assertEqual(self.p.read(s,'/terminated'),False)
  self.assertEqual(self.p.read(s,'/activated'),False)
  self.assertEqual(self.p.read(s,'/clauseRuntime/revision'),1)
 def test_03_root_parameters_reach_clause_and_generated_state(self):
  for party,discount in [('A',700),('B',1500),('EITHER',2200)]:
   s=self.init(terminationAllowedParty=party,resellerDiscountBps=discount)
   self.assertEqual(self.p.read(s,'/terminationPolicy/initialAllowedParty'),party)
   self.assertEqual(self.p.read(s,'/activationState/settled/resellerDiscountBps'),discount)
   self.assertEqual(self.p.read(s,'/contracts/terminateA/steps/0/constants/parameters/allowedParty'),party)
 def test_04_parameter_amendment_triggers_reconciliation(self):
  s=self.init();s=good(self.amend(s,parameters={'resellerDiscountBps':2000,'terminationAllowedParty':'A'}))
  self.assertEqual(self.p.read(s,'/clauseRuntime/revision'),2)
  self.assertEqual(self.p.read(s,'/terminationPolicy/initialAllowedParty'),'A')
  self.assertEqual(self.p.read(s,'/activationState/settled/resellerDiscountBps'),2000)
 def test_05_changed_configuration_invalidates_old_approval(self):
  s=self.init();s=good(op(self.p,s,'actA',request(self.p,s,request_id='old-A'),100))
  old=request(self.p,s,request_id='old-B')
  s=good(self.amend(s,parameters={'resellerDiscountBps':1900,'terminationAllowedParty':'B'}))
  self.assertEqual(self.p.read(s,'/activationState/signals'),{'A':'NONE','B':'NONE'})
  self.assertEqual(len(self.p.read(s,'/activationHistory')),1)
  self.denied(s,op(self.p,s,'actB',old,300),'BEX_EXECUTION_REJECTED')
 def test_06_bindings_rename_workflow_without_editing_contracts(self):
  s=self.init();clauses=clause_config(self.p,s)
  clauses['termination']['bindings']['terminateB']='/contracts/endB'
  s=good(self.amend(s,clauses=clauses))
  body=s.documents[s.root].body
  self.assertIsNone(self.p.blue.select(body,'/contracts/terminateB'))
  self.assertIsNotNone(self.p.blue.select(body,'/contracts/endB'))
  self.assertEqual(self.p.read(s,'/terminated'),False)
 def test_07_binding_collision_rolls_back(self):
  s=self.init();clauses=clause_config(self.p,s)
  clauses['termination']['bindings']['terminateB']='/contracts/actA'
  self.denied(s,self.amend(s,clauses=clauses),'BEX_EXECUTION_REJECTED')
 def test_08_state_rebinding_requires_explicit_migration(self):
  s=self.init();clauses=clause_config(self.p,s)
  for c in clauses.values():c['bindings']['terminated']='/ended'
  self.denied(s,self.amend(s,clauses=clauses),'BEX_EXECUTION_REJECTED')
 def test_09_users_cannot_send_arbitrary_contract_patches(self):
  s=self.init()
  for r in [{'contracts':{}},{'path':'/contracts','val':{}},{'parameters':{},'clauses':{}}]:
   self.denied(s,op(self.p,s,'amendA',r,100),'BEX_EXECUTION_REJECTED')
 def test_10_removing_state_owner_or_prerequisite_is_rejected(self):
  s=self.init();clauses=clause_config(self.p,s);del clauses['termination']
  self.denied(s,self.amend(s,clauses=clauses),'BEX_EXECUTION_REJECTED')
 def test_11_activation_requires_both_same_revision_approvals(self):
  s=self.init();s=good(op(self.p,s,'actA',request(self.p,s),100))
  self.assertFalse(self.p.read(s,'/activated'))
  s=good(op(self.p,s,'actB',request(self.p,s,request_id='b'),200))
  self.assertTrue(self.p.read(s,'/activated'))
  self.assertEqual(set(self.p.read(s,'/acceptedRevision/approvals')),{'A','B'})
 def test_12_ready_is_not_binding_approval(self):
  s=self.init()
  for i,side in enumerate('AB'):s=good(op(self.p,s,'act'+side,request(self.p,s,action='ready',request_id='ready-'+side),100+i))
  self.assertFalse(self.p.read(s,'/activated'))
  self.assertEqual(self.p.read(s,'/activationState/signals'),{'A':'READY','B':'READY'})
 def test_13_termination_before_activation_rejected(self):
  s=self.init();self.denied(s,op(self.p,s,'terminateB',{'requestId':'x','termsId':'not-accepted'},100),'BEX_EXECUTION_REJECTED')
 def test_14_only_negotiated_party_can_terminate(self):
  s=self.accepted();self.denied(s,op(self.p,s,'terminateA',self.termreq(s),300),'BEX_EXECUTION_REJECTED')
  o=op(self.p,s,'terminateB',self.termreq(s),301);self.gas['terminate']=o.gas;s=good(o)
  self.assertTrue(self.p.read(s,'/terminated'));self.assertTrue(self.p.read(s,'/activated'))
  self.assertEqual(len(s.documents),1)
  self.assertIsNone(self.p.blue.select(s.documents[s.root].body,'/contracts/terminated'))
 def test_15_termination_retry_idempotent_and_conflict_rejected(self):
  s=self.accepted();r=self.termreq(s,reason='Close new business');s=good(op(self.p,s,'terminateB',r,300))
  before=self.p.read(s,'/terminationRecord');o=op(self.p,s,'terminateB',r,301);s=good(o)
  self.assertEqual(self.p.read(s,'/terminationRecord'),before)
  self.assertEqual(self.p.emitted(o),[])
  self.denied(s,op(self.p,s,'terminateB',{**r,'reason':'changed'},302),'BEX_EXECUTION_REJECTED')
 def test_16_active_configuration_cannot_be_rewritten(self):
  s=self.accepted();before=self.p.read(s,'/acceptedRevision')
  self.denied(s,self.amend(s,parameters={'resellerDiscountBps':9000,'terminationAllowedParty':'A'}),'BEX_EXECUTION_REJECTED')
  self.assertEqual(self.p.read(s,'/acceptedRevision'),before)
 def test_17_decline_closes_negotiation(self):
  s=self.init();s=good(op(self.p,s,'actB',request(self.p,s,action='decline',request_id='decline',message='No agreement'),100))
  self.assertFalse(self.p.read(s,'/activated'));self.assertTrue(self.p.read(s,'/negotiationClosed'))
  self.denied(s,self.amend(s,parameters={'resellerDiscountBps':1600,'terminationAllowedParty':'B'}),'BEX_EXECUTION_REJECTED')
 def test_18_wrong_channel_cannot_approve_as_other_party(self):
  s=self.init();o=self.p.process(s,{'type':'Contracts/Operation Request','channel':'partyB','operation':'actA','request':request(self.p,s)},100)
  self.denied(s,o,'INVALID_TARGET_OPERATION')
 def test_19_invalid_initial_parameters_rejected(self):
  for bad in [{'terminationAllowedParty':'C'},{'resellerDiscountBps':-1},{'resellerDiscountBps':10001},{'resellerDiscountBps':'cheap'}]:
   o=self.p.initialize(source(**bad));self.assertEqual(o.status,'FAILED',o.diagnostic)
 def test_20_gas_exhaustion_does_not_commit_partial_initialization(self):
  previous=self.p.gas_limit
  try:
   self.p.gas_limit=2000;o=self.p.initialize(source());self.assertEqual(o.status,'GAS_LIMIT_EXCEEDED')
   self.assertIsNone(self.p.blue.select(o.snapshot.documents[o.snapshot.root].body,'/activated'))
  finally:self.p.gas_limit=previous
 def test_21_negotiation_proposal_acceptance_and_final_policy(self):
  s=self.init()
  r=request(self.p,s,action='proposeChange',request_id='proposal',message='Change discount and termination',changes=[{'op':'set','path':'/resellerDiscountBps','val':2000},{'op':'set','path':'/terminationAllowedParty','val':'A'}])
  s=good(op(self.p,s,'actA',r,100))
  node=self.p.blue.select(s.documents[s.root].body,'/activationState/proposal');proposal=self.p.blue.identity(self.p.blue.exact(node))
  s=good(op(self.p,s,'actB',request(self.p,s,action='acceptChange',request_id='accept',proposalId=proposal),101))
  self.assertFalse(self.p.read(s,'/activated'))
  for i,side in enumerate('AB'):s=good(op(self.p,s,'act'+side,request(self.p,s,request_id='approve-'+side),102+i))
  self.assertEqual(self.p.read(s,'/acceptedTerms'),{'resellerDiscountBps':2000,'terminationAllowedParty':'A'})
  self.denied(s,op(self.p,s,'terminateB',self.termreq(s),300),'BEX_EXECUTION_REJECTED')
  s=good(op(self.p,s,'terminateA',self.termreq(s),301));self.assertTrue(self.p.read(s,'/terminated'))
 def test_22_forbidden_source_path_cannot_read_execution_state_as_parameters(self):
  s=self.init();clauses=clause_config(self.p,s)
  clauses['termination']['parameters']['allowedParty']={'from':'/terminated'}
  self.denied(s,self.amend(s,clauses=clauses),'BEX_EXECUTION_REJECTED')
 def test_23_unchanged_inputs_do_not_reset_state(self):
  s=self.accepted();r=self.termreq(s);s=good(op(self.p,s,'terminateB',r,300))
  before=self.p.read(s,'/terminationRecord');s=good(op(self.p,s,'amendA',{'parameters':self.p.read(s,'/parameters')},301))
  self.assertTrue(self.p.read(s,'/terminated'));self.assertEqual(self.p.read(s,'/terminationRecord'),before)
 def test_24_unknown_clause_type_rejected(self):
  s=self.init();clauses=clause_config(self.p,s);clauses['termination']['type']={'blueId':self.p.blue.language.aliases['Contracts/Compute']}
  self.denied(s,self.amend(s,clauses=clauses))

class RecordResult(unittest.TextTestResult):
 def addFailure(self,test,err):
  super().addFailure(test,err);self.stream.writeln(self.failures[-1][1])
 def addError(self,test,err):
  super().addError(test,err);self.stream.writeln(self.errors[-1][1])
 def __init__(self,*a,**k):super().__init__(*a,**k);self.successes=[]
 def addSuccess(self,test):self.successes.append(str(test));super().addSuccess(test)

if __name__=='__main__':
 with PhysicalCache(65536).scope(),core_reuse_scope():
  start=time.time();result=unittest.TextTestRunner(verbosity=2,resultclass=RecordResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(RootClauses))
  report=dict(mode='authored-sources' if os.environ.get('CLAUSE_TEST_SOURCES')=='1' else 'compiled-packages',testsRun=result.testsRun,passed=result.wasSuccessful(),successfulTests=result.successes,failures=[(str(t),msg) for t,msg in result.failures],errors=[(str(t),msg) for t,msg in result.errors],gas=RootClauses.gas,seconds=round(time.time()-start,3))
  (ROOT/'verification'/('source-tests.json' if os.environ.get('CLAUSE_TEST_SOURCES')=='1' else 'tests.json')).write_text(json.dumps(report,indent=2)+'\n')
  sys.exit(0 if result.wasSuccessful() else 1)
