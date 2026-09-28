"""Collapse is a storage projection, never a change in logical work."""
import unittest
from unittest.mock import patch
from algorithms import blue as L
from blue_contracts import Processor, export_snapshot, import_snapshot, ContractError
from blue_contracts.reference.language import Bridge
from blue_contracts.reference.model import Meter, NeedResources
from blue_contracts.reference.work import LogicalWork
from blue_language.physical import PhysicalCache, reference_scope
from blue_runtime.record_bridge import install_record_bridge
from blue_runtime.compact import collapse_snapshot
from .test_contracts_event_api import counter,call,T,operation,compute,change
from .test_completion_cycles import cycle_documents
from .test_completion_graph import start


class DeterministicGas(unittest.TestCase):
    def setUp(self):
        self.cache=PhysicalCache(65536);self.scope=self.cache.scope();self.scope.__enter__()
        self.addCleanup(self.scope.__exit__,None,None,None)

    def compare(self,p,state,collapsed,event,budgets):
        for budget in budgets:
            p.gas_limit=budget
            a=p.process(state,event,10);b=p.process(collapsed,event,10)
            self.assertEqual(a.observations(),b.observations(),budget)
            self.assertEqual(a.receipt,b.receipt,budget)
            self.assertEqual(a.rejected,b.rejected,budget)
            if not a.commits:self.assertEqual(a.snapshot.identity,state.identity)
        return a

    def test_original_counter_and_first_rejected_charges(self):
        p=install_record_bridge(Processor());state=p.create(counter());collapsed,_=collapse_snapshot(p,state)
        full=self.compare(p,state,collapsed,call(),[100000,1396,100000])
        self.assertTrue(full.commits,full.diagnostic);self.assertEqual(p.read(full.snapshot,'/count'),3)
        budgets={0,full.gas};after=0
        for row in full.gas_trace:
            after+=row['amount'];budgets.update((max(0,after-1),after))
        self.compare(p,state,collapsed,call(),sorted(budgets))

    def test_mixed_nested_shared_declarations_and_workflow_bodies(self):
        source=counter();source.update(data={'left':{'n':0},'right':{'n':0}},unrelated={'text':'x'*8192})
        source['contracts']['add']['steps'].append(compute({'$appendChange':change('/data/left/n',5)}))
        p=install_record_bridge(Processor());state=p.create(source)
        collapsed,_=collapse_snapshot(p,state,data_paths=('/data/left','/data/right','/unrelated','/contracts/add/steps'))
        full=self.compare(p,state,collapsed,call(),[100000]);self.assertTrue(full.commits,full.diagnostic)
        self.assertEqual(p.read(full.snapshot,'/data/left/n'),5)
        self.compare(p,state,collapsed,call(),[full.gas-1,full.gas])
        package=export_snapshot(p,collapsed);fresh=install_record_bridge(Processor())
        restored=import_snapshot(fresh,package,package['identity']);fresh.gas_limit=p.gas_limit=100000
        self.assertEqual(p.process(state,call(),10).observations(),fresh.process(restored,call(),10).observations())
        self.cache.clear();self.compare(p,state,collapsed,call(),[100000])
        with reference_scope():self.compare(p,state,collapsed,call(),[100000])

    def test_cyclic_identity_and_fresh_restore(self):
        p=install_record_bridge(Processor());out=p.admit(cycle_documents(),root='A');self.assertTrue(out.commits,out.diagnostic)
        state=out.snapshot;collapsed,_=collapse_snapshot(p,state)
        result=self.compare(p,state,collapsed,start(),[100000]);self.assertTrue(result.commits,result.diagnostic)
        self.assertTrue(all('#' in d.blue_id for d in result.snapshot.documents.values()))
        package=export_snapshot(p,collapsed);fresh=install_record_bridge(Processor())
        restored=import_snapshot(fresh,package,package['identity'])
        self.assertEqual(result.observations(),fresh.process(restored,start(),10).observations())

    def test_logical_delta_does_not_open_unchanged_large_or_unselected_content(self):
        blue=Bridge();unused=blue.source({'nested':{'text':'x'*100000}})
        old=L.node({'count':L.scalar('Integer',0),'unused':unused})
        new=L.changed(old,count=L.scalar('Integer',1));rid=blue.identity(unused)
        collapsed_old=L.changed(old,unused=L.Ref(rid));collapsed_new=L.changed(new,unused=L.Ref(rid))
        traces=[]
        for before,after in ((old,new),(collapsed_old,collapsed_new)):
            meter=Meter();work=LogicalWork(blue,meter);original=blue.open
            def guarded(node):
                if isinstance(node,L.Ref) and node.id==rid:raise AssertionError('opened unchanged payload for gas')
                return original(node)
            with patch.object(blue,'open',side_effect=guarded):work.establish(after,before)
            traces.append(meter.trace)
        self.assertEqual(*traces)
        self.assertLess(sum(r['amount'] for r in traces[0]),100)

    def test_new_nested_content_inline_and_referenced_has_same_work(self):
        blue=Bridge();child=blue.source({'a':[1,2,{'n':5}],'z':'x'*200})
        before=blue.source({'child':{'a':[],'z':''}})
        traces=[]
        for value in (child,L.Ref(blue.identity(child))):
            meter=Meter();work=LogicalWork(blue,meter)
            work.establish(L.node({'child':value}),before);traces.append(meter.trace)
        self.assertEqual(*traces)
        self.assertIn('identityInputTextBlock',[r['counter'] for r in traces[0]])

    def test_missing_and_invalid_evidence_is_not_replaced_by_reuse(self):
        blue=Bridge();child=blue.source({'a':1});rid=blue.identity(child)
        blue.language.provider.set_unavailable(rid);blue.refresh()
        with self.assertRaises(NeedResources):LogicalWork(blue,Meter()).establish(L.node({'x':L.Ref(rid)}))
        blue.language.provider.set_exact(rid,'{"a":2}');blue.refresh()
        with self.assertRaises(ContractError):LogicalWork(blue,Meter()).establish(L.node({'x':L.Ref(rid)}))

    def test_contracts_object_order_control(self):
        observations=[]
        for order in ('ab','ba'):
            left={k:1 if k=='a' else 'x'*200 for k in order};right={'a':2,'b':'x'*200}
            source={'result':True,'contracts':{'input':T('External Channel'),
                'go':operation(compute({'$appendChange':change('/result',{'$eq':[{'$literal':left},{'$literal':right}]})}))}}
            p=Processor();state=p.create(source);result=p.process(state,T('Operation Request',channel='input',operation='go'),10)
            self.assertTrue(result.commits,result.diagnostic);self.assertIs(p.read(result.snapshot,'/result'),False)
            observations.append(result.observations())
        self.assertEqual(*observations)


if __name__=='__main__':unittest.main()
