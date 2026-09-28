"""Context, evidence, topology capacity, historical views and cold storage."""
import unittest
from copy import deepcopy
from algorithms import blue as L
from blue_contracts import Processor,Link,ContractError,export_snapshot,import_snapshot
from blue_contracts.reference.graph import Graph
from .test_contracts_event_api import T,change,update,flow,operation
from .test_completion_graph import child,parent,start,emit,append


class CompletionBoundaries(unittest.TestCase):
    def setUp(self):self.p=Processor()

    def test_dc45_new_edge_does_not_replay_already_sealed_output(self):
        root=parent(Link('B'),append({'$event':'/sourcePath'}))
        root['contracts']['embedded']['paths'].append('/copy')
        root['contracts'].update(input=T('External Channel'),go=operation(update(change('/copy',{'$document':'/child'},'add'))))
        # Accept either path, but capture only the original occurrence for B.
        del root['contracts']['events']['sourcePath']
        initial=self.p.admit({'A':root,'B':child(emit('E'))},root='A')
        self.assertTrue(initial.commits,initial.diagnostic)
        out=self.p.process(initial.snapshot,start(),10);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(self.p.read(out.snapshot,'/seen'),['/child'])
        self.assertEqual(out.snapshot.edges[('A','/child')].target,
                         out.snapshot.edges[('A','/copy')].target)

    def test_dc15_old_exact_attachment_uses_selected_archived_state(self):
        b=child(update(change('/count',1)),count=0)
        b['contracts']['input']['event']={'channel':'input'}
        a={'child':Link('B'),'contracts':{'embedded':T('Process Embedded',paths=['/child','/copy']),
            'parent':T('External Channel',event={'channel':'parent'}),'attach':operation(update(change('/copy',{'$binding':'call/request/node'},'add')),channel='parent')}}
        initial=self.p.admit({'A':a,'B':b},root='A');self.assertTrue(initial.commits,initial.diagnostic)
        old=initial.snapshot.copy();old.root='B';self.p.archive.add(old)
        original_id=old.documents['B'].blue_id
        advanced=self.p.process(initial.snapshot,start(),10);self.assertTrue(advanced.commits,advanced.diagnostic)
        event=T('Operation Request',channel='parent',operation='attach',request={'node':{'blueId':original_id}})
        out=self.p.process(advanced.snapshot,event,11);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(self.p.read(out.snapshot,'/child/count'),1)
        self.assertEqual(self.p.read(out.snapshot,'/copy/count'),0)
        self.assertNotEqual(out.snapshot.edges[('A','/child')].target,out.snapshot.edges[('A','/copy')].target)

    def test_dc26_attach_initialized_child_does_not_reinitialize_or_replay(self):
        b={'count':0,'contracts':{'life':T('Lifecycle Event Channel'),
            'init':flow(update(change('/count',1)),emit('initialized'),channel='life')}}
        ready=self.p.create(b);tid=ready.documents[ready.root].blue_id
        a=child(update(change('/child',{'$binding':'call/request/node'},'add')),heard=0)
        a['contracts'].update(embedded=T('Process Embedded',paths=['/child']),events=T('Embedded Node Channel'),
            hear=flow(update(change('/heard',1)),channel='events'))
        state=self.p.create(a)
        out=self.p.process(state,T('Operation Request',channel='input',operation='go',request={'node':{'blueId':tid}}),10)
        self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(self.p.read(out.snapshot,'/child/count'),1);self.assertEqual(self.p.read(out.snapshot,'/heard'),0)
        self.assertFalse(any(t['turnInput']['lifecycle']['kind']=='INITIALIZE' for t in out.completions))

    def test_dc26_missing_managed_evidence_fails_closed(self):
        other=Processor();ready=other.create({'count':1});tid=ready.documents['root'].blue_id
        records=L.admitted_records(ready.documents['root'].body,other.blue.context)
        self.p.blue.language.provider.merge_responses(records);self.p.blue.refresh()
        a=child(update(change('/child',{'blueId':tid},'add')))
        a['contracts']['embedded']=T('Process Embedded',paths=['/child'])
        initial=self.p.create(a);out=self.p.process(initial,start(),10)
        self.assertEqual(out.status,'NEEDS_RESOURCES',out.diagnostic)
        self.assertEqual(out.snapshot.identity,initial.identity);self.assertEqual(out.public_events,[])

    def test_dc35_inherited_child_requirement_is_not_erased(self):
        base={'name':'FixedChild','count':0}
        tid=self.p.blue.identity(self.p.blue.source(base,goal='definition'))
        b=child(update(change('/count',1)),type={'blueId':tid})
        a=parent(b,append('must not run'))
        initial=self.p.create(a);out=self.p.process(initial,start(),10)
        self.assertEqual(out.status,'FAILED',out.diagnostic)
        self.assertEqual(out.snapshot.identity,initial.identity);self.assertEqual(out.public_events,[])

    def test_dc47_active_capacity_does_not_count_retired_history(self):
        children={f'C{i:03}':{'name':f'Child {i}','count':0} for i in range(127)}
        a=child(update(change('/children',{})),update(change('/children/new',{'count':1},'add')),
                children={k:Link(k) for k in children})
        a['contracts']['embedded']=T('Process Embedded',collectionPaths=['/children'])
        initial=self.p.admit({'A':a,**children},root='A');self.assertTrue(initial.commits,initial.diagnostic)
        self.assertEqual(len(Graph(initial.snapshot,self.p.registry,self.p.archive).reachable()),128)
        out=self.p.process(initial.snapshot,start(),10);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(len(Graph(out.snapshot,self.p.registry,self.p.archive).reachable()),2)
        self.assertEqual(len(out.snapshot.documents),129)
        self.assertEqual(self.p.read(out.snapshot,'/children/new/count'),1)

    def test_dc46_map_collection_replacement_and_removal_have_separate_lifetimes(self):
        a=child(update(change('/children/one',None,'remove')),
                update(change('/children/two',{'count':8})),
                update(change('/children/three',{'count':3},'add')),
                children={'one':{'count':0},'two':{'count':2}})
        a['contracts']['embedded']=T('Process Embedded',collectionPaths=['/children'])
        initial=self.p.create(a)
        old=initial.edges[(initial.root,'/children/two')]
        removed=initial.edges[(initial.root,'/children/one')].target
        out=self.p.process(initial,start(),10);self.assertTrue(out.commits,out.diagnostic)
        current=out.snapshot.edges[(initial.root,'/children/two')]
        self.assertEqual(current.generation,old.generation+1)
        self.assertNotEqual(current.target,old.target)
        self.assertNotIn((initial.root,'/children/one'),out.snapshot.edges)
        self.assertEqual(self.p.read(out.snapshot,'/children/two/count'),8)
        self.assertEqual(self.p.read(out.snapshot,'/children/three/count'),3)
        for key,value in [(removed,0),(old.target,2)]:
            self.assertEqual(self.p.read(out.snapshot,'/count',document=key),value)
        for path in ('two','three'):
            key=out.snapshot.edges[(initial.root,'/children/'+path)].target
            self.assertIsNotNone(self.p.registry.marker(out.snapshot.documents[key].body,'initialized'))
            self.assertIsNone(self.p.registry.marker(out.snapshot.documents[key].body,'checkpoint'))

    def test_dc36_completed_child_must_satisfy_remaining_parent_requirement(self):
        open_id=self.p.blue.identity(self.p.blue.source({'name':'Open','count':{'type':'Integer'}},goal='definition'))
        fixed=self.p.blue.identity(self.p.blue.source({'name':'Fixed','type':{'blueId':open_id},'count':0},goal='definition'))
        holder=self.p.blue.identity(self.p.blue.source({'name':'Holder','child':{'type':{'blueId':fixed}}},goal='definition'))
        b=child(update(change('/count',1)),emit('E'),type={'blueId':fixed})
        b['contracts']['generalization']=T('Type Generalization Policy',rules=[
            {'path':'/count','mode':'reject'},
            {'path':'','mode':'nearest-valid-ancestor','mustRemainSubtypeOf':{'blueId':open_id}}])
        a=parent(b,append('must not run'));a['type']={'blueId':holder}
        initial=self.p.create(a);out=self.p.process(initial,start(),10)
        self.assertEqual(out.status,'FAILED')
        self.assertEqual(out.diagnostic['code'],'LANGUAGE_TypeCompatibilityViolation')
        self.assertEqual(len(out.event_trace),1,'Child finished its own effects before parent validation')
        self.assertFalse(any(w['document']==initial.root for w in out.work_trace))
        self.assertEqual(out.snapshot.identity,initial.identity);self.assertEqual(out.public_events,[])

    def test_dc49_unknown_runtime_constructed_blueid_suspends_then_retries(self):
        from blue_language import Language
        node=Language().create('name: Later\nscore: 7',format='yaml')
        a=child(update(change('/child',{'$objectFromEntries':[{'key':'blueId','val':{'$binding':'call/request/id'}}]},'add')))
        a['contracts']['embedded']=T('Process Embedded',paths=['/child'])
        initial=self.p.create(a);event=T('Operation Request',channel='input',operation='go',request={'id':node.blue_id})
        missing=self.p.process(initial,event,10)
        self.assertEqual(missing.status,'NEEDS_RESOURCES',missing.diagnostic)
        self.assertEqual(missing.snapshot.identity,initial.identity);self.assertEqual(missing.gas_trace,[])
        self.p.blue.language.provider.merge_responses(node.dependency_responses());self.p.blue.refresh()
        retry=self.p.process(initial,event,10);self.assertTrue(retry.commits,retry.diagnostic)
        self.assertEqual(self.p.read(retry.snapshot,'/child/score'),7)

    def test_dc60_old_snapshot_domain_is_rejected(self):
        state=self.p.create({'count':0});wire=export_snapshot(self.p,state)
        from blue_contracts.reference.model import digest
        old=digest('contracts.snapshot/1',wire['snapshot']);wire['identity']=old
        with self.assertRaises(ContractError) as error:import_snapshot(Processor(),wire,old)
        self.assertEqual(error.exception.code,'INVALID_SNAPSHOT_COMMITMENT')


if __name__=='__main__':unittest.main()
