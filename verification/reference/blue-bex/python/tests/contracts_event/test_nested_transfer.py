"""N2: exact descendant provenance survives storage, selection and transport."""
import copy
import json
import unittest
from unittest.mock import patch
from algorithms import blue as L
from blue_bex import GasExhausted
from blue_contracts import Processor, Link, ContractError, export_snapshot, import_snapshot
from blue_contracts.reference.language import Bridge
from blue_contracts.reference.model import Meter, NeedResources
from blue_contracts.reference.work import LogicalWork
from blue_language.physical import PhysicalCache, reference_scope
from .test_contracts_event_api import T, compute
from . import test_exact_transfer as exact_transfer
from .test_exact_transfer import fixture, cut, EVENT
from .test_completion_chunks import chunks

SMALL={'left':[1,2]}
READ={'$document':'/payload'}
EXPRS={
    'direct_path':{'$document':'/payload/left'},
    'get':{'$get':{'object':READ,'key':'left'}},
    'object_set':{'$objectSet':{'object':READ,'key':'extra','val':9}},
    'entries':{'$entries':READ},
}


class NestedTransfer(unittest.TestCase):
    setUp=exact_transfer.ExactTransfer.setUp
    compare=exact_transfer.ExactTransfer.compare

    def test_review_four_cases_and_every_charge_boundary(self):
        for name,expr in EXPRS.items():
            with self.subTest(case=name):
                p=Processor();state=p.create(fixture({'$appendEvent':expr},payload=SMALL))
                states=[state,cut(p,state),cut(p,state,('/payload/left',)),cut(p,state,('/payload/left/items/0',))]
                full=self.compare(p,states);self.assertTrue(full.commits,full.diagnostic)
                expected={'direct_path':[1,2],'get':[1,2],'object_set':{'left':[1,2],'extra':9},'entries':[{'key':'left','val':[1,2]}]}[name]
                self.assertEqual(p.emitted(full),[expected])
                total=0;budgets={0,445,446,544,554,full.gas-1,full.gas}
                for charge in full.gas_trace:
                    total+=charge['amount'];budgets.update((max(0,total-1),total))
                for cap in sorted(budgets):
                    bounded=self.compare(p,states,budgets=(cap,))
                    self.assertEqual(bounded.commits,cap>=full.gas)

    def test_nested_reads_transforms_and_reference_cut_matrix(self):
        payload={'left':[1,{'values':[2,3]}],'right':'z'*80,'object':{'nested':[4]}}
        expressions={**EXPRS,
            'list_get':{'$listGet':{'list':{'$document':'/payload/left'},'index':1}},
            'nested':{'$document':'/payload/left/1/values'},
            'map':{'$map':{'in':{'$document':'/payload/left'},'item':'v','expr':{'wrapped':{'$var':'v'}}}},
            'pointer':{'$pointerSet':{'object':READ,'path':'/left/0','val':99}},
            'whole':READ,'keys':{'$keys':READ},'equal':{'$eq':[READ,{'$literal':payload}]}}
        for name,expr in expressions.items():
            with self.subTest(case=name):
                p=Processor();state=p.create(fixture({'$appendEvent':expr},payload=payload))
                states=[state]+[cut(p,state,paths) for paths in [('/payload',),('/payload/left',),
                    ('/payload/left/items/1',),('/payload/left/items/1/values/items/0','/payload/right','/payload/object')]]
                full=self.compare(p,states);self.assertTrue(full.commits,full.diagnostic)
                self.compare(p,states,budgets=(full.gas-1,full.gas))

    def test_plural_effects_mixed_containers_and_occurrences(self):
        read={'$document':'/payload/left'};mixed={'new':[{'selected':read},read]}
        p=Processor();state=p.create(fixture({'$appendEvent':read},{'$appendEvents':[read,mixed,read]},
            {'$appendChange':{'op':'add','path':'/copy','val':read}},
            {'$appendChanges':[{'op':'add','path':'/mixed','val':mixed}]},payload=SMALL))
        states=[state,cut(p,state),cut(p,state,('/payload/left/items/1',))]
        out=self.compare(p,states);self.assertTrue(out.commits,out.diagnostic)
        expected={'new':[{'selected':[1,2]},[1,2]]}
        self.assertEqual(p.emitted(out),[[1,2],[1,2],expected,[1,2]])
        self.assertEqual(len({row['identity'] for row in out.public_events}),4)
        self.assertEqual(p.read(out.snapshot,'/copy'),[1,2]);self.assertEqual(p.read(out.snapshot,'/mixed'),expected)
        self.compare(p,states,budgets=(out.gas-1,out.gas))
        package=export_snapshot(p,out.snapshot);fresh=Processor();restored=import_snapshot(fresh,package,package['identity'])
        self.assertEqual(fresh.read(restored,'/mixed'),expected)
        for row,value in zip(out.public_events,p.emitted(out)):
            self.assertEqual(fresh.blue.project(L.Ref(row['event'])),value)

    def test_event_and_call_descendants(self):
        for expr in ({'$event':'/request/payload/left'},{'$binding':'call/request/payload/left'}):
            p=Processor();state=p.create(fixture({'$appendEvent':expr}))
            event=p.blue.source({**EVENT,'request':{'payload':SMALL}});events=[event]
            for paths in [('/request',),('/request/payload',),('/request/payload/left',),('/request/payload/left/items/0',)]:
                value,records=L.split_fragments(event,paths,p.blue.context)
                for node in records.values():p.blue.remember(node)
                events.append(value)
            full=p.process(state,event,10);self.assertTrue(full.commits,full.diagnostic)
            self.assertEqual(p.emitted(full),[[1,2]])
            for cap in (100000,full.gas-1,full.gas):
                p.gas_limit=cap;outcomes=[p.process(state,e,10) for e in events]
                for out in outcomes:
                    self.assertEqual(out.observations(),outcomes[0].observations())
                    self.assertEqual(out.receipt,outcomes[0].receipt)

    def test_saved_selection_and_overlay_keep_captured_history(self):
        selected={'$document':'/payload/left'}
        steps=[{**T('Compute',expr=selected),'name':'saved'},compute(
            {'$let':{'name':'old','expr':{'$steps':'saved'}}},
            {'$appendChange':{'op':'replace','path':'/payload','val':{'left':[9]}}},
            {'$appendChange':{'op':'add','path':'/copy','val':{'$var':'old'}}},
            {'$appendEvent':{'$resultValue':'/copy'}},
            {'$appendEvent':{'$var':'old'}})]
        p=Processor();state=p.create(fixture(steps=steps,payload=SMALL));states=[state,cut(p,state)]
        out=self.compare(p,states);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(p.emitted(out),[[1,2],[1,2]])
        self.assertEqual(p.read(out.snapshot,'/payload/left'),[9]);self.assertEqual(p.read(out.snapshot,'/copy'),[1,2])
        self.compare(p,states,budgets=(out.gas-1,out.gas))

    def test_cache_read_history_order_and_restoration(self):
        observations=[]
        for capacity in (None,0,1,65536):
            with reference_scope() if capacity is None else PhysicalCache(capacity).scope():
                p=Processor();state=p.create(fixture({'$appendEvent':EXPRS['object_set']},payload=SMALL))
                states=[state,cut(p,state),cut(p,state,('/payload/left/items/1',))]
                for warm in (False,True):
                    if warm:
                        for s in states:p.read(s,'/payload/left/0')
                    for order in (states,list(reversed(states))):
                        full=self.compare(p,order);self.assertTrue(full.commits,full.diagnostic);observations.append(full.observations())
                        self.compare(p,order,budgets=(full.gas-1,full.gas))
                for s in states:
                    package=export_snapshot(p,s);fresh=Processor();restored=import_snapshot(fresh,package,package['identity'])
                    observations.append(fresh.process(restored,EVENT,10).observations())
        self.assertTrue(all(row==observations[0] for row in observations))

    def test_distinct_members_local_chunk_portable_and_local_caps(self):
        source=fixture({'$appendEvents':[EXPRS['direct_path'],EXPRS['direct_path']]},payload=SMALL)
        p=Processor();state=p.create({'a':{**source,'name':'A'},'b':{**source,'name':'B'},
            'contracts':{'embedded':T('Process Embedded',paths=['/a','/b'])}})
        full=p.process(state,EVENT,10);self.assertTrue(full.commits,full.diagnostic)
        self.assertEqual(len(full.event_trace),4)
        portable=chunks(p,state,EVENT,10,transport=True)
        self.assertEqual(portable.observations(),full.observations());self.assertEqual(portable.receipt,full.receipt)
        owner=next(row['owner'] for row in full.gas_trace if row['namespace']=='bex')
        local_cost=sum(row['amount'] for row in full.gas_trace if row['owner']==owner)
        for cap in (local_cost-1,local_cost):
            p.local_limits={owner:cap};outcomes=[]
            for driver in (False,True):
                p.local_driver=driver;outcomes.append(p.process(state,EVENT,10))
            self.assertEqual(outcomes[0].observations(),outcomes[1].observations());self.assertEqual(outcomes[0].receipt,outcomes[1].receipt)
            if cap<local_cost:self.assertEqual(outcomes[0].rejected['cap'],'LOCAL')
            else:self.assertTrue(outcomes[0].commits,outcomes[0].diagnostic)

    def test_contextual_contributions_remain_exact_and_target_checked(self):
        p=Processor();base=p.blue.source({'payload':{'left':{'field':{'type':'Integer'}}}},goal='definition')
        source=fixture({'$appendEvent':EXPRS['direct_path']},payload={'left':{'field':2,'extra':True}})
        source['type']={'blueId':p.blue.identity(base)}
        state=p.create(source);states=[state,cut(p,state),cut(p,state,('/payload/left',))]
        out=self.compare(p,states);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(p.emitted(out),[{'field':2,'extra':True}]);self.compare(p,states,budgets=(out.gas-1,out.gas))
        source=fixture({'$appendChange':{'op':'replace','path':'/target','val':EXPRS['direct_path']}},payload={'left':{'n':1}})
        source['type']={'target':{'n':{'type':'Integer','schema':{'minimum':5}}}};source['target']={'n':6}
        p=Processor();state=p.create(source);out=self.compare(p,[state,cut(p,state)])
        self.assertFalse(out.commits);self.assertEqual(out.snapshot.identity,state.identity)

    def test_selected_cyclic_descendant_keeps_owning_proof(self):
        p=Processor();docs={'A':{'name':'A','peer':Link('B')},'B':{'name':'B','peer':Link('A')}}
        for doc in docs.values():doc['contracts']={'embedded':T('Process Embedded',paths=['/peer'])}
        admitted=p.admit(docs,root='A');self.assertTrue(admitted.commits,admitted.diagnostic)
        a=admitted.snapshot.documents['A'].blue_id;b=admitted.snapshot.documents['B'].blue_id
        state=p.create(fixture({'$appendEvent':{'$document':'/payload/member/peer'}},payload={'member':{'blueId':a}}))
        out=self.compare(p,[state,cut(p,state)]);self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(out.public_events[0]['event'],b)
        self.compare(p,[state,cut(p,state)],budgets=(out.gas-1,out.gas))
        for corrupt in (False,True):
            blue=Bridge()
            if corrupt:blue.language.provider.set_exact(a.split('#')[0],'{"wrong":true}')
            else:blue.language.provider.set_unavailable(a.split('#')[0])
            blue.refresh()
            with self.assertRaises(ContractError if corrupt else NeedResources):
                LogicalWork(blue,Meter()).read(L.Ref(a),'/peer')

    def test_witness_derivation_is_lazy_and_does_not_admit_unknown_nodes(self):
        blue=Bridge();node=blue.source({'payload':{'left':[1,2]},'unread':{'huge':'x'*10000}})
        selected=blue.child(L.recipe(node),'payload')
        self.assertTrue(all(blue.has_identity_evidence(n) for n in selected.parts))
        # Selecting a child does not recursively enumerate witness descendants.
        selected_node=selected.parts[0]
        self.assertFalse(blue.has_identity_evidence(selected_node.get('left')))
        unknown=L.node({'payload':L.node({'new':L.scalar('Text','runtime')})})
        selected=blue.child(L.recipe(unknown),'payload')
        self.assertFalse(blue.has_identity_evidence(selected.parts[0]))
        for local in (False,True):
            meter=Meter(0) if not local else Meter(local_limits={'root':0});meter.owner='root'
            work=LogicalWork(blue,meter)
            hashes=[];original=L.H
            def hashed(raw):hashes.append(raw);return original(raw)
            with reference_scope(),patch.object(L,'H',side_effect=hashed):
                with self.assertRaises(GasExhausted):work.establish(selected.parts[0])
            self.assertEqual(hashes,[]);self.assertFalse(blue.has_identity_evidence(selected.parts[0]))

    def test_successful_establishment_issues_only_ordinary_completed_evidence(self):
        blue=Bridge();meter=Meter();work=LogicalWork(blue,meter)
        node=L.node({'fresh':L.scalar('Text','never admitted')})
        identity=work.establish(node)
        self.assertEqual(blue.known_identity(node),identity)
        before=meter.used;work.establish(node)
        self.assertLess(meter.used-before,before)
        other=L.node({'fresh':L.scalar('Text','interrupted new value')})
        original=L.H
        def interrupt(raw):
            if type(raw) is dict and raw.get('value')=='interrupted new value':raise MemoryError('test interruption')
            return original(raw)
        with reference_scope(),patch.object(L,'H',side_effect=interrupt):
            with self.assertRaises(MemoryError):work.establish(other)
        self.assertFalse(blue.has_identity_evidence(other))
        self.assertFalse(blue.has_identity_evidence(other.get('fresh')))
        local=L.node({'peer':L.Local(0)})
        work.establish(local,token=lambda i:'this#'+str(i),scope=('test',1))
        self.assertFalse(blue.has_identity_evidence(local))

if __name__=='__main__':unittest.main()
