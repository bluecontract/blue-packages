"""Independent negative and graph/lifetime tests beyond tutorial happy paths."""
import sys,unittest,tempfile
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
from .test_contracts_event_api import T,change,update,compute,flow,operation,call,counter
from blue_contracts import Processor,ContractError,Journal,Link
from blue_contracts.reference.policy import GeneralizationRule,GeneralizationPolicy,choose_type,GeneralizationError
from blue_contracts.reference.model import Meter
from blue_contracts.reference.runtime import RuntimeBinding,RuntimeMeter,frozen
from blue_bex import GasExhausted
from .scenarios import load

class GraphAndPolicy(unittest.TestCase):
 def setUp(self):self.p=Processor()
 def process(self,d,event=None):
  self.s=self.p.create(d);return self.p.process(self.s,event or T('Operation Request',channel='input',operation='go'),1)
 def test_new_child_does_not_receive_old_external_event(self):
  child={'count':0,'contracts':{'input':T('External Channel'),'go':operation(update(change('/count',99)))}}
  d={'children':{},'contracts':{'embedded':T('Process Embedded',collectionPaths=['/children']),'input':T('External Channel'),'go':operation(update(change('/children/new',child,'add')))}}
  # Runtime-created authored children have exact type references, not aliases.
  d['contracts']['go']['steps'][0]['changeset'][0]['val']=self.p.blue.literal(self.p.blue.source(child))
  o=self.process(d);self.assertEqual(o.status,'APPLIED',o.diagnostic);self.assertEqual(self.p.read(o.document,'/children/new/count'),0);self.assertEqual(len(o.checkpoints),1)
 def test_local_only_updates_cannot_remove_source(self):
  child={'count':0,'contracts':{'input':T('External Channel'),'go':operation(T('Trigger Event',event={'kind':'old'}),update(change('/count',1)))}}
  d={'child':child,'heard':0,'contracts':{'embedded':T('Process Embedded',paths=['/child']), 'updates':T('Document Update Channel',path='/child/count'),'remove':flow(update(change('/child',None,'remove')),channel='updates'), 'events':T('Embedded Node Channel'),'hear':flow(update(change('/heard',1)),channel='events')}}
  o=self.process(d);self.assertEqual(o.status,'APPLIED',o.diagnostic);self.assertEqual(self.p.read(o.document,'/heard'),1);self.assertEqual(self.p.read(o.document,'/child/count'),1);self.assertEqual(o.public_events,[])
 def test_local_only_updates_cannot_replace_source(self):
  child={'count':0,'contracts':{'input':T('External Channel'),'go':operation(T('Trigger Event',event={'kind':'old'}),update(change('/count',1)),update(change('/count',2)))}}
  d={'child':child,'heard':0,'contracts':{'embedded':T('Process Embedded',paths=['/child']), 'updates':T('Document Update Channel',path='/child/count'),'replace':flow(update(change('/child',{'count':100})),channel='updates'),'events':T('Embedded Node Channel'),'hear':flow(update(change('/heard',1)),channel='events')}}
  o=self.process(d);self.assertEqual(o.status,'APPLIED',o.diagnostic);self.assertEqual(self.p.read(o.document,'/child/count'),2);self.assertEqual(self.p.read(o.document,'/heard'),1)
 def test_surviving_shared_occurrence_receives_event(self):
  child={'count':0,'contracts':{'input':T('External Channel'),'go':operation(update(change('/count',1)),T('Trigger Event',event={'kind':'signal'}))}}
  root={'a':Link('child'),'b':Link('child'),'heard':0,'contracts':{'embedded':T('Process Embedded',paths=['/a','/b']),'updates':T('Document Update Channel',path='/a/count'),'remove':flow(update(change('/a',None,'remove')),channel='updates'),'events':T('Embedded Node Channel',sourcePath='/b'),'hear':flow(update(change('/heard',1)),channel='events')}}
  initial=self.p.admit({'root':root,'child':child});self.assertTrue(initial.commits,initial.diagnostic);o=self.p.process(initial.document,T('Operation Request',channel='input',operation='go'),1);self.assertTrue(o.commits,o.diagnostic);self.assertEqual(self.p.read(o.document,'/b/count'),1);self.assertEqual(self.p.read(o.document,'/heard'),1)
 def test_cycle_gas_failure_atomic(self):
  docs=load('09-cycle')['document'];docs[0]['contracts']['finish']['steps'].append(T('Trigger Event',event={'kind':'ping'}))
  def symbols(v):
   if isinstance(v,dict):
    if set(v)=={'blueId'} and v['blueId'].startswith('this#'):return Link('m'+v['blueId'][5:])
    return {k:symbols(x) for k,x in v.items()}
   if isinstance(v,list):return [symbols(x) for x in v]
   return v
  init=self.p.admit({'m0':symbols(docs[0]),'m1':symbols(docs[1])},root='m0');self.assertTrue(init.commits,init.diagnostic)
  self.p.gas_limit=3000;o=self.p.process(init.document,T('Operation Request',channel='input',operation='start'),1);self.assertEqual(o.status,'GAS_LIMIT_EXCEEDED',o.diagnostic);self.assertEqual(o.document.identity,init.document.identity);self.assertEqual(o.public_events,[])
 def test_generalization_forbidden_without_policy(self):
  scenario=load('10-generalization');d=deepcopy(scenario['document'])
  for alias,definition in scenario['definitions'].items():self.p.blue.language.aliases[alias]=self.p.blue.identity(self.p.blue.source(definition,goal='definition'));self.p.blue.refresh()
  del d['contracts']['generalization'];o=self.process(d,scenario['inputs'][0]['event']);self.assertEqual(o.status,'FAILED');self.assertEqual(self.p.read(o.document,'/amount'),80)
 def test_explicit_retype_must_validate(self):
  tid=self.p.blue.identity(self.p.blue.source({'name':'Nonnegative','type':'Integer','schema':{'minimum':0}},goal='definition'))
  d={'count':-1,'contracts':{'input':T('External Channel'),'go':operation(update(change('/count/type',{'blueId':tid},'add')))}}
  o=self.process(d);self.assertEqual(o.status,'FAILED');self.assertEqual(self.p.read(o.document,'/count'),-1)
 def test_generalization_policy_cannot_be_removed(self):
  d=counter();d['contracts']['generalization']=T('Type Generalization Policy',defaultMode='reject');d['contracts']['add']['steps']=[update(change('/contracts/generalization',None,'remove'))]
  o=self.process(d,call());self.assertEqual(o.status,'FAILED');self.assertEqual(o.diagnostic['code'],'PROTECTED_STATE_MUTATION')
 def test_union_members_must_be_external(self):
  d={'contracts':{'local':T('Triggered Event Channel'),'bad':T('Composite External Channels',channels=['local'])}}
  with self.assertRaises(ContractError):self.p.create(d)
 def test_union_cycles_rejected(self):
  d={'contracts':{'a':T('Composite External Channels',channels=['b']),'b':T('Composite External Channels',channels=['a'])}}
  with self.assertRaises(ContractError):self.p.create(d)
 def test_collection_requires_map(self):
  d={'children':[],'contracts':{'embedded':T('Process Embedded',collectionPaths=['/children'])}}
  with self.assertRaises(ContractError):self.p.create(d)
 def test_overlapping_embeddings_rejected(self):
  d={'child':{'inner':{}},'contracts':{'embedded':T('Process Embedded',paths=['/child','/child/inner'])}}
  with self.assertRaises(ContractError):self.p.create(d)
 def test_owning_member_can_mutate_own_state(self):
  o=self.process({'count':0,'contracts':{'input':T('External Channel'),'go':operation(update(change('/count',1)))}});self.assertTrue(o.commits,o.diagnostic)
 def test_journal_transaction_failure_does_not_publish(self):
  s=self.p.create(counter());o=self.p.process(s,call(),1)
  with tempfile.TemporaryDirectory() as tmp:
   j=Journal(Path(tmp)/'state.db',self.p);j.initialize('counter',s)
   with self.assertRaises(ContractError):j.commit('counter',o,fail_before_commit=True)
   self.assertEqual(j.load('counter').identity,s.identity);self.assertEqual(j.pending(),[]);self.assertEqual(j.commit('counter',o),'COMMITTED');self.assertEqual(j.commit('counter',o),'ALREADY_COMMITTED');j.close()

class PolicyAlgorithm(unittest.TestCase):
 def choose(self,valid,policy=None):return choose_type('C',None,'/amount',policy or GeneralizationPolicy((GeneralizationRule('/amount','nearest-valid-ancestor','A'),)),immediate_ancestor=lambda t:{'C':'B','B':'A','A':None}[t],valid_with_type=lambda _,t:t in valid,is_subtype=lambda a,b:a in {'A','B','C'})
 def test_nearest_ancestor(self):self.assertEqual(self.choose({'B','A'}),'B')
 def test_current_type_retained(self):self.assertEqual(self.choose({'A','B','C'}),'C')
 def test_no_valid_candidate(self):
  with self.assertRaises(GeneralizationError):self.choose(set())
 def test_longest_policy_prefix(self):
  p=GeneralizationPolicy((GeneralizationRule('','nearest-valid-ancestor'),GeneralizationRule('/amount','reject')));self.assertEqual(p.select('/amount/value').mode,'reject');self.assertEqual(p.select('/amountExtra').mode,'nearest-valid-ancestor')
 def test_equal_specificity_first_rule(self):
  p=GeneralizationPolicy((GeneralizationRule('/amount','reject'),GeneralizationRule('/amount','nearest-valid-ancestor')));self.assertEqual(p.select('/amount').mode,'reject')
 def test_invalid_policy_mode(self):
  with self.assertRaises(GeneralizationError):GeneralizationRule('/amount','widen-everything')
 def test_floor_prevents_escape(self):
  p=GeneralizationPolicy((GeneralizationRule('/amount','nearest-valid-ancestor','C'),))
  with self.assertRaises(GeneralizationError):choose_type('C',None,'/amount',p,immediate_ancestor=lambda _: 'B',valid_with_type=lambda _,t:t=='B',is_subtype=lambda a,b:a==b)

class MeterAlgorithm(unittest.TestCase):
 def test_charge_before_work(self):
  m=Meter(3);m.contracts('objectMemberRead',3)
  with self.assertRaises(GasExhausted):m.contracts('objectMemberRead',1)
  self.assertEqual(m.used,3);self.assertEqual(len(m.trace),1);self.assertEqual(m.rejected['amount'],1)
 def test_zero_limit_rejects_first_charge(self):
  m=Meter(0)
  with self.assertRaises(GasExhausted):m.contracts('processInvocation')
  self.assertEqual(m.used,0)
 def test_local_cap_does_not_create_shared_allowance(self):
  m=Meter(10,{'a':8,'b':8},{'a','b'});m.owner='a';m.contracts('objectMemberRead',7);m.owner='b'
  with self.assertRaises(GasExhausted):m.contracts('objectMemberRead',4)
  self.assertEqual(m.used,7);self.assertEqual(m.rejected['cap'],'SHARED')
 def test_frozen_runtime_data_is_recursive(self):
  x=frozen({'a':{'b':[1]}})
  with self.assertRaises(TypeError):x['a']['b'][0]=2

if __name__=='__main__':unittest.main()
