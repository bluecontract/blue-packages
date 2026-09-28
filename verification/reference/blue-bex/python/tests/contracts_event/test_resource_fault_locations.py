"""Host interruptions at the public and extension boundaries preserve retry."""
import unittest
from unittest.mock import patch
from concurrent.futures import CancelledError
from asyncio import CancelledError as AsyncCancelledError
from blue_host import HostIncomplete
from blue_contracts import Processor, RuntimeBinding
from blue_contracts.reference.graph import Graph
from blue_contracts.reference.work import LogicalWork
from blue_language.physical import PhysicalCache
from tests.contracts_event.test_contracts_event_api import counter,call


class ResourceFaultLocations(unittest.TestCase):
    def setUp(self):
        self.scope=PhysicalCache(65536).scope();self.scope.__enter__()
        self.addCleanup(self.scope.__exit__,None,None,None)

    def faults(self):
        return [MemoryError(),RecursionError(),CancelledError(),AsyncCancelledError(),HostIncomplete('host cutoff')]

    def test_initialization_runtime_read_and_finalization_retry_exactly(self):
        p=Processor();state=p.create(counter())
        initialization=p.initialize(state);oracle=p.process(state,call(),1)
        for target,name,fn,expected in [
                (Graph,'finalize',lambda:p.initialize(state),initialization),
                (LogicalWork,'read',lambda:p.process(state,call(),1),oracle),
                (Graph,'finalize_local',lambda:p.process(state,call(),1),oracle)]:
            for error in self.faults():
                with self.subTest(site=name,fault=type(error).__name__):
                    with patch.object(target,name,side_effect=error) as injected,self.assertRaises(HostIncomplete):fn()
                    self.assertTrue(injected.called)
                    self.assertEqual(fn().observations(),expected.observations())
                    self.assertEqual(p.read(state,'/count'),0)

    def test_external_acceptance_and_admission_wrappers_preserve_faults(self):
        class Channel:
            def verify_admission(self,context):return {}
            def accept(self,context):return True
        p=Processor();implementation=Channel()
        tid=p.blue.identity(p.blue.source({'name':'Fault Channel','type':{'blueId':p.registry.types['Channel']}},goal='definition'))
        sid=p.blue.identity(p.blue.source('Test-only admission and acceptance callbacks'))
        p.install_runtime(RuntimeBinding(tid,sid,'external-channel',(),(),'fault-tests',(('accept',1),)),implementation)
        doc=counter();doc['contracts']['input']={'type':{'blueId':tid}}
        state=p.create(doc);oracle=p.process(state,call(),1)
        self.assertTrue(oracle.commits,oracle.diagnostic)
        for method in ('accept','verify_admission'):
            for error in self.faults():
                with self.subTest(site=method,fault=type(error).__name__):
                    with patch.object(implementation,method,side_effect=error) as injected,self.assertRaises(HostIncomplete):
                        p.process(state,call(),1)
                    self.assertTrue(injected.called)
                    self.assertEqual(p.process(state,call(),1).observations(),oracle.observations())
                    self.assertEqual(p.read(state,'/count'),0)
