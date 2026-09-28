"""Combined LIVE completion exposes only a finished receiver, with stable IDs.

Gas belongs to the actual invocation. Direct/local chunk transport must agree
at every rejection point; independent source invocation gas is never added to
this receiver's meter.
"""
import unittest
from unittest.mock import patch
from blue_contracts import Processor
from blue_contracts.reference.processor import Run
from blue_language.physical import PhysicalCache
from .test_coordination_spi import reroot, finish
from .test_contracts_event_api import T, operation, update, change


def fixture():
    return {'seen':[], 'a':{'count':0,'b':{'contracts':{'in':T('External Channel'),
        'go':operation(T('Trigger Event',event={'kind':'B'}),channel='in')}},'contracts':{
        'in':T('External Channel'),'go':operation(update(change('/count',5)),T('Trigger Event',event={'kind':'Second'}),channel='in'),
        'embedded':T('Process Embedded',paths=['/b']),'child':T('Embedded Node Channel',sourcePath='/b'),
        'observe':T('Sequential Workflow',channel='child',steps=[T('Trigger Event',event={'kind':'First'})])}},
        'contracts':{'in':T('External Channel'),'go':operation(channel='in'),
            'embedded':T('Process Embedded',paths=['/a']),'child':T('Embedded Node Channel',sourcePath='/a'),
            'observe':T('Sequential Workflow',channel='child',steps=[T('Update Document',changeset=[
                {'op':'add','path':'/seen/-','val':{'$document':'/a/count'}}])])}}


class LiveCompletion(unittest.TestCase):
    def test_retained_child_and_direct_seeds_match_rooted_content_and_occurrences(self):
        with PhysicalCache(capacity=65536).scope():
            p=Processor(local_driver=True);state=p.create(fixture())
            a=next(e.target for e in state.edges.values() if e.path=='/a')
            b=next(e.target for e in state.edges.values() if e.path=='/b')
            event=T('Operation Request',channel='in',operation='go')
            oracle=p.process(state,event,123);self.assertTrue(oracle.commits)
            source=p.process(reroot(p,state,b),event,123);capability=p.capture_source_outcome(source)
            original=Run.run_local;executed=[]
            def count(run,sealed,key,*args):
                executed.append(key);return original(run,sealed,key,*args)
            with patch.object(Run,'run_local',count):
                result=finish(p,p.begin_live_application(state,[capability],evidence={}))
            self.assertEqual(executed,[a,state.root])
            self.assertTrue(result.commits,result.diagnostic)
            self.assertEqual(p.read(result.snapshot,'/seen'),[5,5])
            self.assertEqual({k:d.blue_id for k,d in result.snapshot.documents.items()},
                             {k:d.blue_id for k,d in oracle.snapshot.documents.items()})
            self.assertEqual([e['identity'] for e in result.event_trace],
                             [e['identity'] for e in oracle.event_trace if e['document']!=b])
            local=p.complete_local(p.begin_live_application(state,[capability],evidence={}))
            self.assertEqual(local.observations(),result.observations())
            total=0;budgets={0,result.gas}
            for row in result.gas_trace:
                total+=row['amount'];budgets.update((max(0,total-1),total))
            # All charge boundaries of this corrected SPI, separately from the
            # unchanged full-reference direct/chunk sweep.
            for budget in sorted(budgets):
                with self.subTest(budget=budget):
                    p.gas_limit=budget
                    p.blue.refresh()
                    native=p.complete_local(p.begin_live_application(state,[capability],evidence={}))
                    p.blue.refresh()
                    chunked=finish(p,p.begin_live_application(state,[capability],evidence={}))
                    self.assertEqual(native.observations(),chunked.observations())
                    self.assertEqual(native.status,'APPLIED' if budget==result.gas else 'GAS_LIMIT_EXCEEDED')
                    if not native.commits:
                        self.assertEqual(native.snapshot.identity,state.identity)
                        self.assertEqual(native.public_events,[])
