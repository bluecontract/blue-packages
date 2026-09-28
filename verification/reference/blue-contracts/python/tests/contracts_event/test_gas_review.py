"""R3 guards cover real runtime normalization, not just final rollback."""
import copy
import unittest
from unittest.mock import patch
from algorithms import blue as L
from blue_bex import GasExhausted
from blue_contracts import Processor
from blue_contracts.reference.language import Bridge
from blue_contracts.reference.model import Meter
from blue_contracts.reference.work import LogicalWork
from blue_host import HostIncomplete
from blue_language.physical import PhysicalCache,reference_scope
from blue_runtime.record_bridge import install_record_bridge
from blue_runtime.compact import collapse_snapshot
from .test_contracts_event_api import T,operation,compute,change


def scenario(value):
    return {'data':'old','contracts':{'input':T('External Channel'),
        'go':operation(compute({'$appendChange':change('/data',value)}))}}


class IdentityPrepayment(unittest.TestCase):
    def setUp(self):
        self.scope=PhysicalCache(65536).scope();self.scope.__enter__()
        self.addCleanup(self.scope.__exit__,None,None,None)

    def test_unknown_descendant_has_no_hash_or_encoding_at_two_gas(self):
        for length in (65,200000):
            text='x'*length;blue=Bridge();meter=Meter(2);work=LogicalWork(blue,meter)
            before=L.node({'data':L.scalar('Text','old')});candidate=L.node({'data':L.scalar('Text',text)})
            calls=[];original=L.H;encode=L.canonical_text
            def tracked(value):
                if type(value) is dict and value.get('value')==text:calls.append(('hash',meter.used))
                return original(value)
            def encoding(value):
                if type(value) is str and value==text:calls.append(('encoding',meter.used))
                return encode(value)
            with reference_scope(),patch.object(L,'H',side_effect=tracked),patch.object(L,'canonical_text',side_effect=encoding):
                with self.assertRaises(GasExhausted):work.establish(candidate,before)
            self.assertEqual(calls,[]);self.assertEqual(meter.used,2)
            self.assertEqual((meter.rejected['counter'],meter.rejected['units']),('identityInputMember',2))
            self.assertEqual(work.established,set())

    def test_unknown_objects_lists_sharing_and_local_tokens(self):
        for local in (False,True):
            traces=[]
            for shared in (False,True):
                blue=Bridge();leaf=L.node({'text':L.scalar('Text','new'*30), 'count':L.scalar('Integer',L.integer_text(2**100))})
                other=leaf if shared else copy.deepcopy(leaf)
                candidate=L.node({'items':(leaf,other,L.Local(0) if local else L.scalar('Boolean',False))})
                meter=Meter();work=LogicalWork(blue,meter);token=lambda i:'this#'+str(i)
                with reference_scope():identity=work.establish(candidate,token=token,scope=('component',1))
                self.assertEqual(identity,L.identity(candidate,token));traces.append(meter.trace)
                self.assertTrue(any(key[0]==('cyclic' if local else 'ordinary') for key in work.established))
                for limit in (meter.used-1,meter.used):
                    bounded=Meter(limit);again=LogicalWork(Bridge(),bounded)
                    if limit<meter.used:
                        with self.assertRaises(GasExhausted):again.establish(candidate,token=token,scope=('component',1))
                    else:self.assertEqual(again.establish(candidate,token=token,scope=('component',1)),identity)
            self.assertEqual(*traces)

    def test_normalization_unicode_prepaid_and_host_interruption_no_proof(self):
        text='😀'*65;blue=Bridge();meter=Meter(1);work=LogicalWork(blue,meter);checks=[];original=L.checked_unicode
        def track(value):
            if value==text:checks.append(meter.used)
            return original(value)
        with reference_scope(),patch.object(L,'checked_unicode',side_effect=track):
            with self.assertRaises(GasExhausted):work.node(text)
        self.assertEqual(checks,[]);self.assertEqual(work.established,set())
        meter=Meter();work=LogicalWork(blue,meter);original=L.H
        def stop(value):
            if type(value) is dict and value.get('value')==text:raise MemoryError('interrupted before hash')
            return original(value)
        with patch.object(L,'H',side_effect=stop):
            with self.assertRaises(MemoryError):work.node(text)
        self.assertEqual(work.established,set())

    def test_real_processor_first_new_hash_is_prepaid_in_all_cache_modes(self):
        text='x'*2048+'tail';source=scenario({'$concat':['x'*2048,'tail']})
        event=T('Operation Request',channel='input',operation='go')
        p=install_record_bridge(Processor());state=p.create(source);collapsed,_=collapse_snapshot(p,state)
        original_init=LogicalWork.__init__;original_hash=L.H
        def run(snapshot,limit,local=False):
            box={};hashes=[]
            def init(work,blue,meter):box['meter']=meter;original_init(work,blue,meter)
            def hashed(raw):
                if type(raw) is dict and raw.get('value')==text:
                    meter=box['meter'];hashes.append((meter.used,copy.deepcopy(meter.trace[-1])))
                return original_hash(raw)
            p.gas_limit=limit;p.local_limits={'root':local} if local else {}
            with patch.object(LogicalWork,'__init__',init),patch.object(L,'H',side_effect=hashed):
                result=p.process(snapshot,event,1)
            return result,hashes
        with reference_scope():
            full,hashes=run(state,100000)
            self.assertTrue(full.commits,full.diagnostic);self.assertEqual(p.read(full.snapshot,'/data'),text)
            self.assertTrue(hashes);first,charge=hashes[0]
            identity_rows=[row for row in full.gas_trace if row['counter'] in {'identityInputMember','identityInputTextBlock','directIdentityHashBlock'}]
            self.assertTrue(identity_rows);self.assertTrue(all(row['owner']=='root' for row in identity_rows))
            self.assertEqual(charge['counter'],'directIdentityHashBlock')
            for snapshot in (state,collapsed):
                denied,calls=run(snapshot,first-1)
                self.assertEqual(denied.status,'GAS_LIMIT_EXCEEDED');self.assertEqual(calls,[])
                self.assertEqual(denied.snapshot.identity,state.identity)
                self.assertEqual(denied.rejected['counter'],'directIdentityHashBlock')
                local_allowance=sum(row['amount'] for row in full.gas_trace[:charge['ordinal']+1] if row['owner']=='root')-1
                local_denied,calls=run(snapshot,first,local_allowance)
                self.assertEqual(calls,[]);self.assertEqual(local_denied.rejected['cap'],'LOCAL')
                at_boundary,calls=run(snapshot,first)
                self.assertTrue(calls);self.assertEqual(calls[0][0],first)
                for allowance in (full.gas-1,full.gas):
                    result,_=run(snapshot,allowance)
                    self.assertEqual(result.commits,allowance==full.gas)
        for capacity in (0,1,65536):
            cache=PhysicalCache(capacity)
            with cache.scope():
                for snapshot in (state,collapsed,state):
                    result,_=run(snapshot,100000)
                    self.assertEqual(result.observations(),full.observations());self.assertEqual(result.receipt,full.receipt)
                    cache.clear()

    def test_admitted_descendant_witnesses_do_not_depend_on_prior_reads(self):
        traces=[]
        for warm,collapsed in ((False,False),(True,False),(False,True),(True,True)):
            with reference_scope():
                blue=Bridge();child=blue.source({'a':{'x':{'v':1},'label':'one'},'b':{'x':{'v':1},'label':'two'}})
                if warm:
                    for name in ('a','b'):blue.open(blue.open(child.get(name)).get('x'))
                exact=L.Ref(blue.identity(child)) if collapsed else child
                meter=Meter();work=LogicalWork(blue,meter);work.establish(L.node({'child':exact}))
                traces.append(meter.trace)
        self.assertTrue(all(trace==traces[0] for trace in traces))

    def test_runtime_normalization_key_order_sharing_and_large_integer(self):
        outcomes=[]
        for shared,reverse in ((False,False),(True,False),(False,True),(True,True)):
            child={'long'*40:'new'*70,'😀':[3,{'type':{'blueId':L.CORE['Integer']},'value':2**150}]}
            other=child if shared else copy.deepcopy(child)
            value={'z':child,'a':other,'\ue000':False}
            if reverse:value=dict(reversed(list(value.items())))
            blue=Bridge();meter=Meter();node=LogicalWork(blue,meter).node(value)
            outcomes.append((blue.identity(node),meter.trace))
        self.assertTrue(all(row==outcomes[0] for row in outcomes))

    def test_contracts_control_for_shared_equality_and_effect_order(self):
        results=[]
        for shared,reverse in ((False,False),(True,False),(False,True),(True,True)):
            value={'a':1,'b':'x'*200};other=value if shared else copy.deepcopy(value)
            if reverse:value=dict(reversed(list(value.items())));other=dict(reversed(list(other.items())))
            expr={'$eq':[{'$literal':[value,other]},{'$literal':[other,value]}]}
            p=Processor();state=p.create(scenario(expr));result=p.process(state,T('Operation Request',channel='input',operation='go'),1)
            self.assertTrue(result.commits,result.diagnostic);self.assertIs(p.read(result.snapshot,'/data'),True)
            results.append(result.observations())
        self.assertTrue(all(r==results[0] for r in results))

    def test_completed_dependency_inventory_has_no_partial_identity(self):
        outcomes=[]
        for collapsed in (False,True):
            p=Processor();child=p.blue.source({'name':'shared'})
            value={'blueId':p.blue.identity(child)} if collapsed else {'name':'shared'}
            refs={f'c{i}':copy.deepcopy(value) for i in range(8)}
            doc={**refs,'contracts':{'embedded':T('Process Embedded',paths=['/'+key for key in refs])}}
            original=L.H;inventories=[]
            def hashed(raw):
                if type(raw) is dict and all(key in raw for key in refs):
                    inventories.append({raw[key]['blueId'] for key in refs})
                return original(raw)
            with reference_scope(),patch.object(L,'H',side_effect=hashed):result=p.initialize(doc)
            self.assertTrue(result.commits,result.diagnostic)
            self.assertEqual(len(result.snapshot.edges),8)
            self.assertTrue(inventories)
            self.assertTrue(all(len(ids)==1 for ids in inventories))
            self.assertEqual(sum(row['units'] for row in result.gas_trace if row['counter']=='containingReferenceUpdated'),8)
            outcomes.append(result.observations())
        self.assertEqual(*outcomes)

if __name__=='__main__':unittest.main()
