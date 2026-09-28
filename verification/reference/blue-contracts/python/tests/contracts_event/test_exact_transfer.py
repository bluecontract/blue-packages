"""N1: whole exact values have canonical transfer gas, not physical wire gas."""
import copy
import unittest
from unittest.mock import patch
from algorithms import blue as L
from blue_bex import Engine, Context, Gas, GasExhausted
from blue_bex.values import HostValue, size_parts, UNDEFINED
from blue_contracts import Processor, Link, ContractError, export_snapshot, import_snapshot, export_invocation, import_invocation
from blue_contracts.reference.language import Bridge
from blue_contracts.reference.model import Meter, NeedResources
from blue_contracts.reference.work import LogicalWork
from blue_language.physical import PhysicalCache, reference_scope
from .test_contracts_event_api import T, operation, compute

PAYLOAD={'left':[1,2],'right':'z'*80}
EVENT=T('Operation Request',channel='input',operation='go')
READ={'$document':'/payload'}


def fixture(*statements,payload=PAYLOAD,steps=None):
    return {'payload':copy.deepcopy(payload),'contracts':{'input':T('External Channel'),
        'go':operation(*(steps if steps is not None else [compute(*statements)]))}}


def cut(p,state,paths=('/payload',)):
    """Only requested data paths; executable declarations stay inline."""
    out=state.copy();doc=out.documents[out.root]
    doc.body,records=L.split_fragments(doc.body,paths,p.blue.context)
    for value in records.values():p.blue.remember(value)
    p.blue.refresh();p.validate(out)
    assert state.identity==out.identity
    assert p.blue.identity(doc.body)==state.documents[state.root].blue_id
    return out


class ExactTransfer(unittest.TestCase):
    def setUp(self):
        self.cache=PhysicalCache(65536);scope=self.cache.scope();scope.__enter__()
        self.addCleanup(scope.__exit__,None,None,None)

    def compare(self,p,states,event=EVENT,budgets=(100000,),timestamp=10):
        for limit in budgets:
            p.gas_limit=limit
            outcomes=[p.process(state,event,timestamp) for state in states]
            first=outcomes[0]
            for state,result in zip(states,outcomes):
                self.assertEqual(result.input_identity,first.input_identity)
                self.assertEqual(result.invocation,first.invocation)
                self.assertEqual(result.observations(),first.observations(),limit)
                self.assertEqual(result.receipt,first.receipt,limit)
                self.assertEqual(result.rejected,first.rejected,limit)
                if not result.commits:
                    self.assertEqual(result.snapshot.identity,state.identity)
                    self.assertEqual(result.public_events,[])
                    self.assertEqual(result.checkpoints,[])
        return first

    def test_original_emit_and_copy_all_charge_boundaries(self):
        for effect,cutoff in [('emit',472),('copy',649)]:
            with self.subTest(effect=effect):
                row={'$appendEvent':READ} if effect=='emit' else {'$appendChange':{'op':'add','path':'/copy','val':READ}}
                p=Processor();state=p.create(fixture(row));collapsed=cut(p,state)
                full=self.compare(p,[state,collapsed]);self.assertTrue(full.commits,full.diagnostic)
                self.assertEqual(full.checkpoints[0]['after']['event'],{'blueId':p.blue.identity(p.blue.source(EVENT))})
                budgets={0,472,649,full.gas-1,full.gas};total=0
                for charge in full.gas_trace:
                    total+=charge['amount'];budgets.update((max(0,total-1),total))
                for budget in sorted(budgets):
                    result=self.compare(p,[state,collapsed],budgets=[budget])
                    self.assertEqual(result.commits,budget>=full.gas)
                if effect=='emit':self.assertEqual(p.emitted(full),[PAYLOAD])
                else:self.assertEqual(p.read(full.snapshot,'/copy'),PAYLOAD)
                # Restore output in a fresh resolver, including transferred data.
                p.gas_limit=100000;package=export_snapshot(p,full.snapshot)
                fresh=Processor();restored=import_snapshot(fresh,package,package['identity'])
                self.assertEqual(restored.identity,full.snapshot.identity)
                if effect=='copy':self.assertEqual(fresh.read(restored,'/copy'),PAYLOAD)
                else:
                    for occurrence in full.public_events:
                        self.assertEqual(fresh.blue.project(L.Ref(occurrence['event'])),PAYLOAD)
                capsule=export_invocation(p,collapsed,p.blue.source(EVENT),10)
                replay=Processor();s,e,t=import_invocation(replay,capsule,capsule['identity'])
                actual=replay.process(s,e,t)
                self.assertEqual(actual.observations(),full.observations());self.assertEqual(actual.receipt,full.receipt)

    def test_plural_mixed_effects_nested_values_and_occurrence_order(self):
        native={'$literal':{'new':['created',7]}}
        wrapped={'envelope':[{'payload':READ},[READ,native]],'marker':'wrapped'}
        rows=[{'$appendEvent':READ},{'$appendEvents':[READ,wrapped,READ]},
            {'$appendChange':{'op':'add','path':'/copy','val':wrapped}},
            {'$appendChanges':[{'op':'add','path':'/copies','val':[READ,native,READ]}]}]
        p=Processor();state=p.create(fixture(*rows))
        states=[state,cut(p,state),cut(p,state,('/payload/left',)),cut(p,state,('/payload/right',))]
        result=self.compare(p,states);self.assertTrue(result.commits,result.diagnostic)
        expected={'envelope':[{'payload':PAYLOAD},[PAYLOAD,{'new':['created',7]}]],'marker':'wrapped'}
        self.assertEqual(p.emitted(result),[PAYLOAD,PAYLOAD,expected,PAYLOAD])
        self.assertEqual(len({r['identity'] for r in result.public_events}),4)
        self.assertEqual(p.read(result.snapshot,'/copy'),expected)
        self.assertEqual(p.read(result.snapshot,'/copies'),[PAYLOAD,{'new':['created',7]},PAYLOAD])
        self.compare(p,states,budgets=(result.gas-1,result.gas))

    def test_event_and_call_values_with_independent_reference_cuts(self):
        for expr in ({'$event':'/request/payload'},{'$binding':'call/request/payload'}):
            p=Processor();state=p.create(fixture({'$appendEvent':expr}))
            event=p.blue.source({**EVENT,'request':{'payload':PAYLOAD}})
            projected,records=L.split_fragments(event,('/request/payload',),p.blue.context)
            for n in records.values():p.blue.remember(n)
            a=p.process(state,event,10);b=p.process(state,projected,10)
            self.assertTrue(a.commits,a.diagnostic);self.assertEqual(p.emitted(a),[PAYLOAD])
            self.assertEqual(a.observations(),b.observations());self.assertEqual(a.receipt,b.receipt)
            for cap in (a.gas-1,a.gas):
                p.gas_limit=cap
                self.assertEqual(p.process(state,event,10).observations(),p.process(state,projected,10).observations())

    def test_result_overlays_step_results_and_local_bindings(self):
        steps=[{**T('Compute',expr=READ),'name':'read'},compute(
            {'$let':{'name':'saved','expr':{'$steps':'read'}}},
            {'$appendChange':{'op':'add','path':'/copy','val':{'$var':'saved'}}},
            {'$appendEvent':{'$resultValue':'/copy'}},
            {'$appendEvents':[{'$var':'saved'},{'$document':'/payload'}]})]
        p=Processor();state=p.create(fixture(steps=steps));result=self.compare(p,[state,cut(p,state)])
        self.assertTrue(result.commits,result.diagnostic)
        self.assertEqual(p.read(result.snapshot,'/copy'),PAYLOAD);self.assertEqual(p.emitted(result),[PAYLOAD]*3)

    def test_scalar_empty_list_object_and_typed_exact_values(self):
        values=[{},[],False,0,'', 'hello',[1,{'n':2}], {'type':'List','items':[1,2]},
            {'name':'Typed','type':'Dictionary','valueType':{'type':'Integer'},'a':3}]
        for value in values:
            with self.subTest(value=value):
                p=Processor();state=p.create(fixture({'$appendEvent':READ},payload=value))
                result=self.compare(p,[state,cut(p,state)])
                self.assertTrue(result.commits,result.diagnostic)
                expected=p.read(state,'/payload');self.assertEqual(p.emitted(result),[expected])
        p=Processor();state=p.create(fixture({'$appendEvent':{'$document':'/absent'}}))
        result=self.compare(p,[state,cut(p,state)])
        self.assertFalse(result.commits);self.assertEqual(result.diagnostic['code'],'BEX_BEX_RUNTIME_ERROR')

    def test_inherited_context_preserves_exact_origin(self):
        p=Processor();base=p.blue.source({'payload':{'base':{'type':'Integer'}}},goal='definition')
        source=fixture({'$appendChange':{'op':'add','path':'/copy','val':READ}},payload={'base':3,'extra':True})
        source['type']={'blueId':p.blue.identity(base)}
        state=p.create(source);result=self.compare(p,[state,cut(p,state)])
        self.assertTrue(result.commits,result.diagnostic)
        self.assertEqual(p.read(result.snapshot,'/copy'),{'base':3,'extra':True})
        # A Dictionary requirement is effective context, not exact authored type.
        blue=Bridge();node=blue.source({'type':'Dictionary','valueType':{'type':'List'},'x':[1,2]})
        work=LogicalWork(blue,Meter());value=work.read(node,'/x')
        self.assertEqual(value.accounting_view(),{'blueId':blue.identity(blue.exact(blue.select(node,'/x')))})
        # Recipe construction and its reuse also agree across physical caches.
        traces=[]
        for capacity in (None,0,1,65536):
            with reference_scope() if capacity is None else PhysicalCache(capacity).scope():
                for referenced in (False,True):
                    blue=Bridge();a=blue.source({'a':1});b=blue.source({'b':2})
                    parts=[L.Ref(blue.identity(x)) if referenced else x for x in (a,b)]
                    work=LogicalWork(blue,Meter());value=blue.view(L.recipe(*parts),logical=work)
                    form=value.accounting_view();again=blue.view(L.recipe(*parts),logical=work).accounting_view()
                    self.assertEqual(form,again);traces.append(work.meter.trace)
        self.assertTrue(all(t==traces[0] for t in traces))

    def test_captured_step_result_does_not_follow_new_document_state(self):
        steps=[{**T('Compute',expr=READ),'name':'saved'},compute(
            {'$appendChange':{'op':'replace','path':'/payload','val':{'changed':True}}}),
            compute({'$appendEvent':{'$steps':'saved'}})]
        p=Processor();state=p.create(fixture(steps=steps));out=self.compare(p,[state,cut(p,state)])
        self.assertTrue(out.commits,out.diagnostic)
        self.assertEqual(p.read(out.snapshot,'/payload'),{'changed':True})
        self.assertEqual(p.emitted(out),[PAYLOAD])

    def test_stricter_target_validation_is_not_skipped(self):
        source=fixture({'$appendChange':{'op':'replace','path':'/target','val':READ}},payload={'n':1})
        source['type']={'target':{'n':{'type':'Integer','schema':{'minimum':5}}}}
        source['target']={'n':6}
        p=Processor();state=p.create(source);out=self.compare(p,[state,cut(p,state)])
        self.assertFalse(out.commits);self.assertEqual(out.snapshot.identity,state.identity)
        self.assertIn(out.diagnostic['code'],('LANGUAGE_SchemaViolation','LANGUAGE_FixedValueConflict','INVALID_PATCH'))

    def test_composed_transfer_direct_chunked_and_member_local_boundaries(self):
        p=Processor();base=p.blue.source({'payload':{'a':{'type':'Integer'}}},goal='definition')
        source=fixture({'$appendEvents':[READ,READ]},payload={'a':1,'b':True})
        source['type']={'blueId':p.blue.identity(base)}
        state=p.create(source);states=[state,cut(p,state)]
        full=self.compare(p,states);self.assertTrue(full.commits,full.diagnostic)
        local_cost=sum(row['amount'] for row in full.gas_trace if row['owner']=='root')
        for local in (0,local_cost-1,local_cost):
            p.local_limits={'root':local};p.local_driver=False
            expected=self.compare(p,states)
            p.local_driver=True;actual=self.compare(p,states)
            self.assertEqual(actual.observations(),expected.observations())
            self.assertEqual(actual.receipt,expected.receipt)
            self.assertEqual(actual.commits,local==local_cost)

    def test_composed_identity_evidence_survives_continuation_copy_without_cache(self):
        observations=[]
        for capacity in (None,0,1,65536):
            with reference_scope() if capacity is None else PhysicalCache(capacity).scope():
                p=Processor();base=p.blue.source({'payload':{'a':{'type':'Integer'}}},goal='definition')
                source=fixture({'$appendEvents':[READ,READ]},payload={'a':1,'b':True})
                source['type']={'blueId':p.blue.identity(base)}
                root={'x':{**source,'name':'X'},'y':{**source,'name':'Y'},
                      'contracts':{'embedded':T('Process Embedded',paths=['/x','/y'])}}
                state=p.create(root)
                for local in (False,True):
                    p.local_driver=local;p.gas_limit=100000
                    out=p.process(state,EVENT,10)
                    self.assertTrue(out.commits,out.diagnostic);observations.append(out.observations())
                    # The same composed exact child crosses two distinct units.
                    self.assertEqual(len(out.event_trace),4)
                    for cap in (out.gas-1,out.gas):
                        p.gas_limit=cap;bounded=p.process(state,EVENT,10)
                        self.assertEqual(bounded.commits,cap==out.gas)
        self.assertTrue(all(o==observations[0] for o in observations))

    def test_controls_keep_their_existing_tariffs(self):
        cases=[(T('Trigger Event',event=READ),404),
               (T('Update Document',changeset=[{'op':'add','path':'/copy','val':READ}]),591)]
        for step,expected in cases:
            p=Processor();state=p.create(fixture(steps=[step]));out=self.compare(p,[state,cut(p,state)])
            self.assertTrue(out.commits,out.diagnostic);self.assertEqual(out.gas,expected)

    def test_cache_prior_read_eviction_and_fresh_import(self):
        rows=[]
        for capacity in (None,0,1,65536):
            with reference_scope() if capacity is None else PhysicalCache(capacity).scope():
                p=Processor();state=p.create(fixture({'$appendEvent':READ}));collapsed=cut(p,state)
                for warm in (False,True):
                    if warm:p.read(state,'/payload/left/0');p.read(collapsed,'/payload/right')
                    out=self.compare(p,[state,collapsed]);rows.append(out.observations())
                package=export_snapshot(p,collapsed);fresh=Processor()
                restored=import_snapshot(fresh,package,package['identity'])
                rows.append(fresh.process(restored,EVENT,10).observations())
        self.assertTrue(all(row==rows[0] for row in rows))

    def test_cyclic_value_retains_captured_member_and_owning_proof(self):
        p=Processor();docs={'A':{'name':'A','peer':Link('B')},'B':{'name':'B','peer':Link('A')}}
        for doc in docs.values():doc['contracts']={'embedded':T('Process Embedded',paths=['/peer'])}
        admitted=p.admit(docs,root='A');self.assertTrue(admitted.commits,admitted.diagnostic)
        rid=admitted.snapshot.documents['A'].blue_id;self.assertIn('#',rid)
        source=fixture({'$appendEvent':READ},payload={'blueId':rid})
        state=p.create(source);materialized=state.copy()
        doc=materialized.documents[materialized.root]
        doc.body=L.changed(doc.body,payload=L.Ref(rid,p.blue.open(L.Ref(rid))))
        full=self.compare(p,[state,materialized])
        self.assertTrue(full.commits,full.diagnostic);self.assertEqual(full.public_events[0]['event'],rid)
        self.assertLess(full.gas,1000)
        capsule=export_invocation(p,state,p.blue.source(EVENT),10);fresh=Processor()
        restored,event,t=import_invocation(fresh,capsule,capsule['identity'])
        other=fresh.process(restored,event,t)
        self.assertEqual(other.observations(),full.observations());self.assertEqual(other.receipt,full.receipt)
        self.assertEqual(fresh.blue.read(L.Ref(rid),'/peer/name'),'B')
        # Owning-set evidence cannot be invented by a transfer token.
        blue=Bridge();blue.language.provider.set_unavailable(rid.split('#')[0]);blue.refresh()
        with self.assertRaises(NeedResources):blue.view(L.Ref(rid),logical=LogicalWork(blue,Meter()))
        blue.language.provider.set_exact(rid.split('#')[0],'{"wrong":true}');blue.refresh()
        with self.assertRaises(ContractError):blue.view(L.Ref(rid),logical=LogicalWork(blue,Meter()))

    def test_missing_invalid_ordinary_evidence_and_untrusted_reference_object(self):
        for corrupt in (False,True):
            blue=Bridge();node=blue.source(PAYLOAD);rid=blue.identity(node)
            if corrupt:blue.language.provider.set_exact(rid,'{"wrong":true}')
            else:blue.language.provider.set_unavailable(rid)
            blue.refresh()
            with self.assertRaises(ContractError if corrupt else NeedResources):
                blue.view(L.Ref(rid),logical=LogicalWork(blue,Meter()))
        # Authored reference syntax still goes through Language verification.
        p=Processor();unknown=L.H({'not':'installed'})
        state=p.create(fixture({'$appendEvent':{'$objectSet':{'object':{},'key':'blueId','val':unknown}}}))
        out=p.process(state,EVENT,10)
        self.assertFalse(out.commits);self.assertEqual(out.snapshot.identity,state.identity)

    def test_composed_exact_recipe_is_established_before_first_new_hash(self):
        blue=Bridge();a=blue.source({'a':1});b=blue.source({'b':2})
        recipe=L.recipe(a,b);seen=[];real=L.H
        meter=Meter();work=LogicalWork(blue,meter);value=blue.view(recipe,logical=work)
        def track(raw):
            if type(raw) is dict and set(raw)=={'a','b'}:seen.append((meter.used,copy.deepcopy(meter.trace[-1])))
            return real(raw)
        with reference_scope(),patch.object(L,'H',side_effect=track):form=value.accounting_view()
        self.assertTrue(seen);first,charge=seen[0];self.assertEqual(charge['counter'],'directIdentityHashBlock')
        self.assertEqual(form,{'blueId':blue.identity(blue.exact(recipe))})
        for local in (False,True):
            fresh=Bridge();a=fresh.source({'a':1});b=fresh.source({'b':2});seen.clear()
            meter=Meter(first-1) if not local else Meter(local_limits={'root':first-1})
            meter.owner='root'
            work=LogicalWork(fresh,meter);value=fresh.view(L.recipe(a,b),logical=work)
            with reference_scope(),patch.object(L,'H',side_effect=track):
                with self.assertRaises(GasExhausted):value.accounting_view()
            self.assertEqual(seen,[]);self.assertEqual(work.exact_values,{})

    def test_native_container_pays_while_nested_exact_child_transfers(self):
        blue=Bridge();node=blue.source(PAYLOAD)
        views=[blue.view(node),blue.view(L.Ref(blue.identity(node)))]
        expected={'wrapper':[{'blueId':blue.identity(node)}]}
        for value in views:
            gas=Gas();actual=list(size_parts({'wrapper':[value]},gas.charge))
            native=Gas();wanted=list(size_parts(expected,native.charge))
            self.assertEqual(actual,wanted);self.assertEqual(gas.trace,native.trace)
            # Reads/equality retain effective values, not the metering wrapper.
            self.assertEqual(list(value),['left','right']);self.assertEqual(value['left'][1],2)
        # No HostValue-wide admission shortcut: default host metering stays deep.
        class Ordinary(HostValue,dict):
            def value_kind(self):return 'object'
            def blue_output(self):return dict(self)
        host=Gas();native=Gas()
        self.assertEqual(list(size_parts(Ordinary(PAYLOAD),host.charge)),list(size_parts(PAYLOAD,native.charge)))
        self.assertEqual(host.trace,native.trace)

if __name__=='__main__':unittest.main()
