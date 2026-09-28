"""Ordinary-path evidence reuse, complete exports, and independent references."""
import copy
import unittest
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields
from unittest.mock import patch

from algorithms import blue as L
from blue_contracts import Processor,export_snapshot,export_invocation,import_invocation,Journal
from blue_contracts.reference.language import Bridge
from blue_language import Language
from blue_language.physical import PhysicalCache
from blue_runtime.core_reuse import CoreReuse,core_reuse_scope,export_collection
from tools.benchmark_release_baseline import fixture


def scenario(options=None,capacity=8192,budget=100000):
    with PhysicalCache().scope(),core_reuse_scope(capacity=capacity) as cache:
        p=Processor(local_driver=True);members,target,path=fixture(options or {'records':3})
        initialized=p.admit(members);assert initialized.commits
        before=initialized.snapshot
        event={'sequence':1,'operation':p.typed('Operation Request',channel='input',operation='op0',
              document={'blueId':before.documents[target].blue_id})}
        p.gas_limit=budget
        out=p.process(before,event,1)
        observations=out.observations()
        with export_collection():capsule=export_invocation(p,before,event,1)
        return observations,out.snapshot.wire(),out.receipt,capsule,dict(cache.metrics)


class CoreReuseTests(unittest.TestCase):
    def test_complete_observations_and_export_cold_warm_evicted_disabled(self):
        expected=scenario(capacity=0)
        for capacity in (8192,1):
            actual=scenario(capacity=capacity)
            self.assertEqual(expected[:4],actual[:4])
        self.assertGreater(scenario()[-1]['closedSubtreesReused'],0)

    def test_cycles_sharing_and_history(self):
        for options in ({'cycle':2},{'children':3,'shared':True},{'operations':5}):
            self.assertEqual(scenario(options,0)[:4],scenario(options)[:4])

    def test_first_rejected_charge_and_exact_boundary(self):
        expected=scenario(capacity=0);gas=expected[0]['gas']
        for budget in (0,gas-1,gas):
            self.assertEqual(scenario(capacity=0,budget=budget)[:4],scenario(budget=budget)[:4])

    def test_provider_isolation_missing_and_corrupt(self):
        with PhysicalCache().scope(),core_reuse_scope() as reuse:
            p=Processor();node=p.blue.source({'name':'retained','n':3});identity=L.identity(node)
            p.blue.source({'child':{'blueId':identity}})
            p.blue.language.provider.set_unavailable(identity)
            with self.assertRaises(Exception):p.blue.source({'child':{'blueId':identity}})
            p.blue.language.provider.set_exact(identity,'{"n":99}')
            with self.assertRaises(Exception):p.blue.source({'child':{'blueId':identity}})
            fresh=Processor()
            with self.assertRaises(Exception):fresh.blue.source({'child':{'blueId':identity}})
            self.assertGreater(reuse.metrics['resolverInvalidations'],0)

    def test_new_effective_constraint_is_not_value_evidence(self):
        for enabled in (False,True):
            with PhysicalCache().scope(),core_reuse_scope(enabled=enabled):
                p=Processor();child=p.blue.source({'value':3});identity=L.identity(child)
                with self.assertRaises(Exception):p.blue.source({'type':'Dictionary',
                    'valueType':{'type':'Integer','schema':{'maximum':2}},'entry':{'blueId':identity}})

    def test_definition_goal_does_not_certify_a_value(self):
        with PhysicalCache().scope(),core_reuse_scope():
            p=Processor();node=p.blue.source({'type':'Text'},goal='definition')
            with self.assertRaises(Exception):p.blue.certify(node,'value')

    def test_all_finite_limits_take_reference_path(self):
        for field in fields(L.Limits):
            for changed_after_creation in (False,True):
                with self.subTest(limit=field.name,changed_after_creation=changed_after_creation),core_reuse_scope() as reuse:
                    language=Language()
                    p=Processor(language) if changed_after_creation else None
                    setattr(language.limits,field.name,100000)
                    p=p or Processor(language)
                    if changed_after_creation:reuse.clear()  # Discard evidence from construction.
                    p.blue.source({'name':'limits'})
                    self.assertFalse(reuse.sessions)
        from blue_host import HostIncomplete
        with core_reuse_scope() as reuse:
            p=Processor();p.blue.language.limits=L.Limits(steps=1)
            reuse.clear()
            with self.assertRaises(HostIncomplete):p.blue.source({'x':1})
            self.assertFalse(reuse.sessions)

    def test_public_inventory_remains_complete_and_delta_work_is_bounded(self):
        with PhysicalCache().scope(),core_reuse_scope() as reuse:
            p=Processor();node=p.blue.source({'x':[{'n':i} for i in range(20)]})
            before=reuse.metrics['retentionBodiesVisited'];p.blue.retain([node])
            self.assertEqual(before,reuse.metrics['retentionBodiesVisited'])
            complete=L.admitted_records(node,p.blue.context)
            self.assertGreater(len(complete),20)
            fresh=Language();fresh.provider.merge_responses(complete)
            self.assertEqual(fresh.load(L.identity(node)).blue_id,L.identity(node))

    def test_cold_restore_replay_and_capsule_are_complete(self):
        observations,wire,receipt,capsule,_=scenario()
        with PhysicalCache().scope(),core_reuse_scope():
            fresh=Processor(local_driver=True)
            state,event,time=import_invocation(fresh,capsule,capsule['identity'])
            result=fresh.process(state,event,time)
            self.assertEqual(observations,result.observations());self.assertEqual(receipt,result.receipt)

    def test_concurrent_scopes_are_isolated(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda size:scenario({'records':size}),[2,2]))
        self.assertEqual(results[0][:4],results[1][:4])

    def test_new_construction_still_calls_original_hash(self):
        with PhysicalCache().scope(),core_reuse_scope():
            p=Processor();p.blue.source({'x':1})
            with patch.object(L,'identity',wraps=L.identity) as identity:
                p.blue.source({'x':2})
                self.assertGreater(identity.call_count,0)

    def test_retained_list_prefixes(self):
        def run(capacity):
            with PhysicalCache().scope(),core_reuse_scope(capacity=capacity):
                p=Processor();typ=p.blue.source({'type':'List','mergePolicy':'append-only','items':[{'$previousItems':False},1,2]},goal='definition')
                node=p.blue.source({'type':{'blueId':L.identity(typ)},'items':[{'$previousItems':True},3]})
                return L.canonical_export(node,p.blue.context),L.admitted_records(node,p.blue.context)
        self.assertEqual(run(0),run(8192))

if __name__=='__main__':unittest.main()

class RetentionInvalidation(unittest.TestCase):
    def test_changed_provider_is_repaired_by_complete_captured_retention(self):
        for broken in ('missing','corrupt'):
            with PhysicalCache().scope(),core_reuse_scope() as cache:
                p=Processor();root=p.blue.source({'child':{'n':7}})
                child=root.get('child');identity=L.identity(child)
                if broken=='missing':p.blue.language.provider.set_unavailable(identity)
                else:p.blue.language.provider.set_exact(identity,'{"n":99}')
                # The resolver still owns its already verified immutable body.
                # Reference retention restores it, so delta retention must too.
                p.blue.retain([root])
                fresh=p.blue.language.processing_context()
                self.assertEqual(L.identity(L.open_exact(L.Ref(identity),fresh)),identity)
                self.assertGreater(cache.metrics['retentionInvalidations'],0)

    def test_scope_clear_cannot_keep_old_coverage(self):
        with PhysicalCache().scope(),core_reuse_scope() as cache:
            p=Processor();node=p.blue.source({'x':1});cache.clear()
            p.blue.retain([node]);self.assertEqual(len(cache.sessions),1)

    def test_every_export_limit_has_distinct_evidence(self):
        from dataclasses import replace
        from blue_language.physical import _REFERENCE_EXPORT
        cache=PhysicalCache()
        with cache.scope():
            for field in fields(L.Limits):
                limits=replace(L.Limits(),**{field.name:100000})
                node=L.normalize({'x':[1,2,3]},L.Context())
                self.assertEqual(L.export_exact(node,L.Context(limits=limits)),_REFERENCE_EXPORT(node,L.Context(limits=limits)))
            self.assertEqual(len(cache.roundtrips),len(fields(L.Limits)))

class ExactResolverCoverage(unittest.TestCase):
    def test_same_identity_alternate_body_does_not_replace_provider_materialization(self):
        def run(capacity):
            with PhysicalCache().scope(),core_reuse_scope(capacity=capacity):
                p=Processor();node=p.blue.source({'payload':{'n':1}})
                identity=L.identity(node);child=node.get('payload')
                alternate=L.node({'payload':L.Ref(L.identity(child))})
                self.assertEqual(L.identity(alternate),identity)
                p.blue.context.bodies[identity]=alternate
                received=p.blue.source({'copy':{'blueId':identity}})
                return L.admitted_records(received,p.blue.context)
        self.assertEqual(run(0),run(8192))

    def test_missing_cyclic_proof_keeps_the_reference_diagnostic(self):
        from blue_runtime.core_reuse import ExportCollection
        base=L.identity(L.node({'name':'opaque'}))
        pinned=L.Ref(base+'#0',L.node({'name':'body'}))
        outcomes=[]
        for collect in (L.admitted_records,ExportCollection().records):
            try:collect(pinned,L.Context())
            except L.Failure as error:outcomes.append((error.category,error.detail))
        self.assertEqual(outcomes,[('InvalidCyclicProof','publication proof unavailable')]*2)

class IrrelevantProviderRecords(unittest.TestCase):
    def test_nondemanded_opaque_or_malformed_records_do_not_become_errors(self):
        from blue_language import MemoryProvider
        identity=L.identity(L.node({'name':'unrelated'}))
        for response in ([],{'partialObject':{},'completeDirectManifest':False},
                         {'text':'\ud800'},{'text':123},{'nested':{'x':[1,2]}}):
            results=[]
            for capacity in (0,8192):
                with PhysicalCache().scope(),core_reuse_scope(capacity=capacity):
                    p=Processor(Language(MemoryProvider({identity:response})))
                    node=p.blue.source({'x':1});node=p.blue.source({'x':2})
                    results.append(L.export_exact(node))
            self.assertEqual(*results)
