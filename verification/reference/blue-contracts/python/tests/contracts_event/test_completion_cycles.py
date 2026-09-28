"""Real Language cyclic proofs and completion-1 previous-round observations."""
import unittest
from blue_contracts import Processor,Link
from .test_contracts_event_api import T,change,update,flow,operation,compute
from .test_completion_graph import child,parent,start,emit,append


def cycle_documents():
    a={'done':False,'calls':0,'peer':Link('B'),'contracts':{
        'embedded':T('Process Embedded',paths=['/peer']),'input':T('External Channel'),
        'go':operation(update(change('/calls',{'$add':[{'$document':'/calls'},1]})),emit('ping')),
        'peerEvents':T('Embedded Node Channel',event={'kind':'pong'}),
        'finish':flow(update(change('/done',True)),channel='peerEvents')}}
    b={'replied':False,'peer':Link('A'),'contracts':{
        'embedded':T('Process Embedded',paths=['/peer']),
        'peerEvents':T('Embedded Node Channel',event={'kind':'ping'}),
        'reply':flow(update(change('/replied',True)),emit('pong'),channel='peerEvents')}}
    return {'A':a,'B':b}


class CompletionCycles(unittest.TestCase):
    def setUp(self):self.p=Processor()
    def admit(self,docs,root='A'):
        out=self.p.admit(docs,root=root);self.assertTrue(out.commits,out.diagnostic);return out.snapshot
    def run_cycle(self,docs=None,root='A',event=None):
        state=self.admit(docs or cycle_documents(),root)
        out=self.p.process(state,event or start(),10);self.assertTrue(out.commits,out.diagnostic)
        self.p.validate(out.snapshot)
        return out
    def test_dc37_finite_cycle_has_three_sealed_rounds(self):
        out=self.run_cycle()
        self.assertEqual(self.p.read(out.snapshot,'/done'),True)
        self.assertEqual(self.p.read(out.snapshot,'/calls'),1)
        self.assertEqual(self.p.read(out.snapshot,'/peer/replied'),True)
        self.assertEqual([r['turnInput']['member'] for r in out.completions],['A','B','A'])
        self.assertEqual(len(out.rounds),3)
        self.assertEqual([r['document'] for r in out.checkpoints],['A'])
        self.assertTrue(all('#' in d.blue_id for d in out.snapshot.documents.values()))

    def test_dc38_both_external_recipients_read_previous_peer(self):
        docs={}
        for name,peer in [('A','B'),('B','A')]:
            docs[name]=child(update(change('/count',1)),update(change('/seen',{'$document':'/peer/count'})),name=name,count=0,seen=-1,peer=Link(peer))
            docs[name]['contracts']['embedded']=T('Process Embedded',paths=['/peer'])
        out=self.run_cycle(docs)
        self.assertEqual(self.p.read(out.snapshot,'/seen'),0)
        self.assertEqual(self.p.read(out.snapshot,'/peer/seen'),0)
        self.assertEqual(len(out.rounds),1)

    def test_dc39_self_edge_is_a_pin_not_the_writable_body(self):
        a=child(update(change('/count',1)),update(change('/seen',{'$document':'/peer/count'})),count=0,seen=-1,peer=Link('A'))
        a['contracts']['embedded']=T('Process Embedded',paths=['/peer'])
        out=self.run_cycle({'A':a})
        self.assertEqual(self.p.read(out.snapshot,'/seen'),0)
        self.assertEqual(self.p.read(out.snapshot,'/peer/count'),1)
        self.assertEqual(len(out.rounds),1)

    def test_dc40_infinite_feedback_rolls_back(self):
        docs=cycle_documents();docs['A']['contracts']['finish']['steps'].append(emit('ping'))
        state=self.admit(docs);self.p.gas_limit=2000
        out=self.p.process(state,start(),10)
        self.assertEqual(out.status,'GAS_LIMIT_EXCEEDED',out.diagnostic)
        self.assertEqual(out.snapshot.identity,state.identity);self.assertEqual(out.public_events,[])
        self.assertEqual(sum(r['amount'] for r in out.gas_trace),out.gas)
        self.assertIsNotNone(out.rejected)

    def test_dc42_outside_parent_sees_final_cycle_not_round_zero(self):
        docs=cycle_documents();docs['P']=parent(Link('A'),append({'$document':'/child/done'}))
        out=self.run_cycle(docs,root='P')
        self.assertEqual(self.p.read(out.snapshot,'/seen'),[True])
        self.assertEqual(self.p.emitted(out),[])
        self.assertEqual([t['turnInput']['member'] for t in out.completions],['A','B','A','P'])

    def test_dc42_outside_batches_follow_source_order_not_round_interleaving(self):
        docs=cycle_documents();docs['A']['contracts']['finish']['steps'].append(emit('ack'))
        docs['P']={'a':Link('A'),'b':Link('B'),'seen':[],'contracts':{
            'embedded':T('Process Embedded',paths=['/a','/b']),
            'events':T('Embedded Node Channel'),
            'hear':flow(append({'$event':'/event/kind'}),channel='events')}}
        out=self.run_cycle(docs,root='P')
        self.assertEqual([self.p.blue.read(self.p.blue.node({'blueId':e['event']}),'/kind')
                          for e in out.event_trace],['ping','pong','ack'])
        self.assertEqual(self.p.read(out.snapshot,'/seen'),['ping','ack','pong'])

    def test_dc44_split_keeps_sticky_execution_unit_and_real_identities(self):
        docs=cycle_documents()
        # Emit before retiring the incoming route: retirement correctly stops
        # the rest of that embedded handler, so a later emit would not run.
        docs['B']['contracts']['reply']['steps'].append(update(change('/peer',None,'remove')))
        out=self.run_cycle(docs)
        self.assertTrue(self.p.read(out.snapshot,'/done'))
        self.assertTrue(all('#' not in d.blue_id for d in out.snapshot.documents.values()))
        self.assertEqual(len(out.rounds),3)

    def test_dc43_dynamic_join_preserves_consumed_operation(self):
        b=child(update(change('/peer',{'$binding':'call/request/root'},'add')),emit('ready'),count=0)
        b['contracts']['embedded']=T('Process Embedded',paths=['/peer'])
        a=parent(Link('B'),update(change('/observed',{'$document':'/child/count'},'add')))
        state=self.admit({'A':a,'B':b})
        event=T('Operation Request',channel='input',operation='go',request={'root':{'blueId':state.documents['A'].blue_id}})
        out=self.p.process(state,event,10);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(self.p.read(out.snapshot,'/observed'),0)
        self.assertEqual(len([t for t in out.completions if t['consumedSeeds']]),1)
        self.assertTrue(all('#' in d.blue_id for d in out.snapshot.documents.values()))
        self.p.validate(out.snapshot)

    def test_dc28_created_child_return_edge_reads_sealed_creator(self):
        b={'seen':-1,'peer':{},'contracts':{'embedded':T('Process Embedded',paths=['/peer']),
            'life':T('Lifecycle Event Channel'),'init':flow(update(change('/seen',{'$document':'/peer/count'})),emit('ready'),channel='life')}}
        raw=self.p.blue.literal(self.p.blue.source(b))
        new_child={'$merge':[{'$literal':raw},{'peer':{'$binding':'call/request/root'}}]}
        a=child(update(change('/count',1)),update(change('/child',new_child,'add')),update(change('/childSaw',{'$document':'/child/seen'})),
                count=0,childSaw=-1,seen=[])
        a['contracts'].update(embedded=T('Process Embedded',paths=['/child']),events=T('Embedded Node Channel'),hear=flow(append('ready'),channel='events'))
        state=self.p.create(a)
        event=T('Operation Request',channel='input',operation='go',request={'root':{'blueId':state.documents['root'].blue_id}})
        out=self.p.process(state,event,10);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(self.p.read(out.snapshot,'/childSaw'),0)
        self.assertEqual(self.p.read(out.snapshot,'/seen'),['ready'])
        self.assertEqual(len(out.checkpoints),1)
        self.assertTrue(all('#' in d.blue_id for d in out.snapshot.documents.values()))
        self.p.validate(out.snapshot)


if __name__=='__main__':unittest.main()
