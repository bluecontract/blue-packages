"""Completion-1 graph, lifecycle and FIFO observations, independently asserted."""
import unittest
from copy import deepcopy
from blue_contracts import Processor, Link
from .test_contracts_event_api import T, change, update, flow, operation, compute


def start(): return T('Operation Request', channel='input', operation='go')
def emit(kind, **fields): return T('Trigger Event', event={'kind':kind, **fields})
def child(*steps, **values):
    return {**values, 'contracts':{'input':T('External Channel'),'go':operation(*steps)}}
def parent(document, *steps):
    return {'child':document,'seen':[],'contracts':{
        'embedded':T('Process Embedded',paths=['/child']),
        'events':T('Embedded Node Channel',sourcePath='/child'),
        'hear':flow(*steps,channel='events')}}
def append(value,path='/seen'):return update(change(path+'/-',value,'add'))


class CompletionGraph(unittest.TestCase):
    def setUp(self):self.p=Processor()
    def run_document(self,document,event=None):
        self.initial=self.p.create(document)
        out=self.p.process(self.initial,start() if event is None else event,10)
        self.assertEqual(out.status,'APPLIED',out.diagnostic)
        return out
    def read(self,out,path,**kwargs):return self.p.read(out.snapshot,path,**kwargs)

    def test_dc02_ordinary_nested_updates_remain_immediate(self):
        d=child(update(change('/customer/address/city','B')),update(change('/after',{'$document':'/seen'})),
                customer={'address':{'city':'A'}},seen=False,after=False)
        d['contracts'].update(updates=T('Document Update Channel',path='/customer/address'),
            observe=flow(update(change('/seen',True)),channel='updates'))
        out=self.run_document(d);self.assertTrue(self.read(out,'/after'))

    def test_dc03_attachment_update_is_local_and_not_deep(self):
        d=child(update(change('/child',None,'remove')),child={'count':0},local=False,deep=False)
        d['contracts'].update(embedded=T('Process Embedded',paths=['/child']),
            attachment=T('Document Update Channel',path='/child'),
            nested=T('Document Update Channel',path='/child/count'),
            one=flow(update(change('/local',True)),channel='attachment'),
            two=flow(update(change('/deep',True)),channel='nested'))
        out=self.run_document(d);self.assertTrue(self.read(out,'/local'));self.assertFalse(self.read(out,'/deep'))

    def test_dc07_fifo_preserves_chained_parent_events(self):
        d=parent(child(emit('E1'),emit('E2')),append({'$event':'/event/kind'}),emit('P1'))
        d['contracts'].update(local=T('Triggered Event Channel'),
            onP1=flow(append('P1'),emit('P2'),channel='local',event={'kind':'P1'}),
            onP2=flow(append('P2'),channel='local',event={'kind':'P2'}))
        out=self.run_document(d)
        self.assertEqual(self.read(out,'/seen'),['E1','E2','P1','P1','P2','P2'])

    def test_dc08_all_siblings_installed_and_prequeued(self):
        b=child(update(change('/count',2)),emit('B1'),emit('B2'),count=0)
        c=child(update(change('/count',3)),emit('C1'),count=0)
        root={'b':Link('B'),'c':Link('C'),'seen':[],'reads':[], 'contracts':{
            'embedded':T('Process Embedded',paths=['/b','/c']), 'events':T('Embedded Node Channel'),
            'hear':flow(append({'$event':'/event/kind'}),append([{'$document':'/b/count'},{'$document':'/c/count'}],'/reads'),emit('P'),channel='events'),
            'local':T('Triggered Event Channel'),'own':flow(append('P'),channel='local')}}
        initial=self.p.admit({'A':root,'B':b,'C':c},root='A');self.assertTrue(initial.commits,initial.diagnostic)
        out=self.p.process(initial.snapshot,start(),10);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(self.read(out,'/seen'),['B1','B2','C1','P','P','P'])
        self.assertEqual(self.read(out,'/reads'),[[2,3]]*3)

    def test_dc09_equal_values_keep_distinct_occurrences(self):
        out=self.run_document(parent(child(emit('same'),emit('same')),append({'$event':'/event/kind'})))
        self.assertEqual(self.read(out,'/seen'),['same','same'])
        events=[e for e in out.event_trace if e['document']!=out.snapshot.root]
        self.assertEqual(len({e['identity'] for e in events}),2)
        self.assertEqual([e['sourceOrdinal'] for e in events],[0,1])

    def test_dc10_grandparent_sees_only_explicit_parent_output(self):
        a=parent(child(emit('child')),emit('parent'))
        root=parent(a,append({'$event':'/event/kind'}))
        out=self.run_document(root);self.assertEqual(self.read(out,'/seen'),['parent'])

    def test_dc12_equal_replacement_retires_old_remaining_batch(self):
        d=parent(child(emit('E1'),emit('E2')),append({'$event':'/event/kind'}),update(change('/child',{'$document':'/child'})))
        out=self.run_document(d);self.assertEqual(self.read(out,'/seen'),['E1'])
        self.assertEqual(out.snapshot.documents[out.snapshot.root].edge_serials['/child'],2)

    def test_dc13_shared_routes_are_event_major_and_retire_independently(self):
        root={'a':Link('B'),'b':Link('B'),'seen':[],'contracts':{
            'embedded':T('Process Embedded',paths=['/a','/b']),'events':T('Embedded Node Channel'),
            'hear':flow(append({'$event':'/sourcePath'}),channel='events',order=0),
            'retire':flow(update(change('/a',None,'remove')),channel='events',order=1,
                          event={'sourcePath':'/a','event':{'kind':'E1'}})}}
        initial=self.p.admit({'A':root,'B':child(emit('E1'),emit('E2'))},root='A')
        self.assertTrue(initial.commits,initial.diagnostic)
        out=self.p.process(initial.snapshot,start(),10);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(self.read(out,'/seen'),['/a','/b','/b'])
        self.assertEqual(len([t for t in out.completions if t['turnInput']['member']=='B']),1)

    def test_dc14_two_parents_share_one_source_turn(self):
        a=parent(Link('B'),append({'$event':'/event/kind'}));c=deepcopy(a)
        root={'a':Link('A'),'c':Link('C'),'contracts':{'embedded':T('Process Embedded',paths=['/a','/c'])}}
        initial=self.p.admit({'R':root,'A':a,'B':child(emit('E')),'C':c},root='R')
        out=self.p.process(initial.snapshot,start(),10);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(self.read(out,'/a/seen'),['E']);self.assertEqual(self.read(out,'/c/seen'),['E'])
        self.assertEqual(len([t for t in out.completions if t['turnInput']['member']=='B']),1)

    def test_dc15_distinct_explicit_equal_members_keep_distinct_turns(self):
        c=child(emit('E'))
        root={'b':Link('B'),'c':Link('C'),'contracts':{'embedded':T('Process Embedded',paths=['/b','/c'])}}
        initial=self.p.admit({'A':root,'B':c,'C':deepcopy(c)},root='A')
        self.assertTrue(initial.commits,initial.diagnostic)
        out=self.p.process(initial.snapshot,start(),10);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual({e['document'] for e in out.event_trace},{'B','C'})
        self.assertEqual(len({e['identity'] for e in out.event_trace}),2)

    def test_dc16_child_batch_precedes_frozen_parent_seed(self):
        d=parent(child(emit('E')),append('child'))
        d['contracts'].update(input=T('External Channel'),go=operation(append('own')))
        out=self.run_document(d);self.assertEqual(self.read(out,'/seen'),['child','own'])

    def test_dc19_new_handler_waits_for_next_dispatch(self):
        late=flow(update(change('/late',True)))
        late=self.p.blue.literal(self.p.blue.source(late))
        d=child(update(change('/contracts/late',{'$literal':late},'add')),late=False)
        out=self.run_document(d);self.assertFalse(self.read(out,'/late'))
        again=self.p.process(out.snapshot,{'operation':start(),'nonce':2},11)
        self.assertTrue(again.commits,again.diagnostic);self.assertTrue(self.read(again,'/late'))

    def test_dc23_dc24_parent_initializer_reads_completed_child_and_original_id(self):
        b={'count':0,'contracts':{'life':T('Lifecycle Event Channel'),'init':flow(update(change('/count',7)),emit('childReady'),channel='life')}}
        d=parent(b,append({'$event':'/event/kind'}));d['read']=0
        d['contracts'].update(life=T('Lifecycle Event Channel'),init=flow(update(change('/read',{'$document':'/child/count'})),emit('parentReady'),channel='life'),
                             local=T('Triggered Event Channel'),own=flow(append({'$event':'/kind'}),channel='local'))
        from blue_contracts.reference.graph import prepare_bundle
        from blue_contracts.reference.channels import refresh_lifetimes
        from blue_contracts.reference.graph import Graph
        raw=prepare_bundle(self.p.registry,{'root':d},'root',archive=self.p.archive);refresh_lifetimes(Graph(raw,self.p.registry,self.p.archive))
        before=raw.documents['root'].blue_id
        out=self.p.initialize(raw);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(self.read(out,'/read'),7)
        self.assertEqual(self.read(out,'/seen'),['childReady','parentReady'])
        marker=self.p.registry.marker(out.snapshot.documents['root'].body,'initialized')
        self.assertEqual(self.p.blue.literal(marker)['document']['blueId'],before)
        self.assertEqual(out.checkpoints,[])

    def test_dc25_new_child_barrier_finishes_before_next_creator_step(self):
        b={'count':0,'contracts':{'life':T('Lifecycle Event Channel'),'init':flow(update(change('/count',7)),emit('ready'),channel='life')}}
        b=self.p.blue.literal(self.p.blue.source(b))
        d=child(update(change('/child',{'$literal':b},'add')),update(change('/after',{'$document':'/child/count'})),after=0,seen=[])
        d['contracts'].update(embedded=T('Process Embedded',paths=['/child']),events=T('Embedded Node Channel'),hear=flow(append('ready'),channel='events'))
        out=self.run_document(d);self.assertEqual(self.read(out,'/after'),7);self.assertEqual(self.read(out,'/seen'),['ready'])
        self.assertEqual(len(out.checkpoints),1)

    def test_dc27_failed_child_initialization_rolls_back_creator(self):
        b={'contracts':{'life':T('Lifecycle Event Channel'),'init':flow(compute({'$fail':'child failed'}),channel='life')}}
        b=self.p.blue.literal(self.p.blue.source(b))
        d=child(update(change('/child',{'$literal':b},'add')))
        d['contracts']['embedded']=T('Process Embedded',paths=['/child'])
        initial=self.p.create(d);out=self.p.process(initial,start(),10)
        self.assertEqual(out.status,'FAILED');self.assertEqual(out.snapshot.identity,initial.identity);self.assertEqual(out.public_events,[])

    def test_dc30_parent_termination_stops_remaining_receiving_work(self):
        d=parent(child(emit('E1'),emit('E2')),append({'$event':'/event/kind'}),T('Terminate Processing',cause='finished'))
        out=self.run_document(d);self.assertEqual(self.read(out,'/seen'),['E1'])
        self.assertEqual(self.read(out,'/contracts/terminated/cause'),'finished')

    def test_dc31_child_checkpoint_visible_at_parent_callback(self):
        d=parent(child(emit('E')),update(change('/timestamp',{'$document':'/child/contracts/checkpoint/entries/input/timestamp'},'add')))
        out=self.run_document(d);self.assertEqual(self.read(out,'/timestamp'),10)
        self.assertFalse(any(r['document']==out.snapshot.root for r in out.checkpoints))

    def test_dc32_new_channel_signature_loses_frozen_seed(self):
        new=self.p.blue.literal(self.p.blue.source(T('External Channel',event={'other':True})))
        d=parent(child(emit('E')),update(change('/contracts/input',{'$literal':new})))
        d['own']=False;d['contracts'].update(input=T('External Channel'),go=operation(update(change('/own',True))))
        out=self.run_document(d);self.assertFalse(self.read(out,'/own'))
        self.assertFalse(any(r['document']==out.snapshot.root for r in out.checkpoints))

    def test_dc59_late_parent_failure_rolls_back_finished_child(self):
        d=parent(child(update(change('/count',1)),emit('E'),count=0),compute({'$fail':'late failure'}))
        initial=self.p.create(d);out=self.p.process(initial,start(),10)
        self.assertEqual(out.status,'FAILED');self.assertEqual(out.snapshot.identity,initial.identity)
        self.assertEqual(self.read(out,'/child/count'),0);self.assertEqual(out.public_events,[])


if __name__=='__main__':unittest.main()
