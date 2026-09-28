from __future__ import annotations
import json, tempfile, unittest, copy, importlib.util, sys
from pathlib import Path
from blue_language import Language, MemoryProvider, Failure, Limits, CORE
from algorithms import blue as B

class LanguageTests(unittest.TestCase):
    def setUp(self):self.lang=Language()

    def assert_failure(self,category,fn):
        with self.assertRaises(Failure)as cm:fn()
        self.assertEqual(cm.exception.category,category)

    def test_documented_scalar_vector(self):
        self.assertEqual(self.lang.identify('1'),'GhNUbi6oXA1HArr2uTqwpcgegPv8kxUuj11riBtoMJXz')
        self.assertEqual(self.lang.identify('{"x":1}'),'GK4yR8GtLdg9y97uEPUAbepLF3M8qXsbgXRt7Kb3yQAr')

    def test_numeric_kinds(self):
        self.assertEqual(self.lang.identify('1.0'),self.lang.identify('1e0'))
        self.assertNotEqual(self.lang.identify('1'),self.lang.identify('1.0'))
        self.assertNotEqual(self.lang.identify('"1"'),self.lang.identify('1'))

    def test_yaml_json_parity(self):
        a='x: 1\ny: [PLN, 2]\n'
        self.assertEqual(self.lang.identify(a,format='yaml'),self.lang.identify('{"x":1,"y":["PLN",2]}'))

    def test_duplicate_decoded_keys(self):
        self.assert_failure('DuplicateKey',lambda:self.lang.identify('{"x":1,"\\u0078":2}'))
        self.assert_failure('DuplicateKey',lambda:self.lang.identify('x: 1\nx: 2',format='yaml'))

    def test_yaml_alias_rejected(self):
        self.assert_failure('InvalidSyntax',lambda:self.lang.identify('x: &a 1\ny: *a',format='yaml'))

    def test_empty_values_distinct(self):
        ids=[self.lang.identify(x)for x in ['{}','[]','{"x":{}}','{"x":[]}','{"$empty":true}']]
        self.assertEqual(len(set(ids)),len(ids))
        self.assertEqual(self.lang.identify('{"x":null}'),self.lang.identify('{}'))
        self.assertEqual(self.lang.identify('{"x":{"y":null}}'),self.lang.identify('{"x":{}}'))

    def test_list_source_null_and_exact_empty(self):
        self.assertEqual(self.lang.identify('[null]'),self.lang.identify('[{"$empty":true}]'))
        self.assertNotEqual(self.lang.identify('[{}]'),self.lang.identify('[null]'))
        self.assert_failure('InvalidExactNode',lambda:self.lang.identify('[null]',mode='exact'))

    def test_reference_siblings_rejected_before_cleaning(self):
        self.assert_failure('InvalidReferenceShape',lambda:self.lang.identify(json.dumps({'blueId':CORE['Text'],'x':None})))

    def test_direct_alias_boundary(self):
        self.assert_failure('InvalidBlueIdInput',lambda:self.lang.identify('{"type":"Integer","value":1}',mode='direct'))
        self.assertEqual(self.lang.identify('{"type":"Integer","value":1}'),self.lang.identify('1'))

    def test_reference_no_fetch_to_name(self):
        rid=self.lang.identify('7')
        self.assertEqual(self.lang.raw_identify(json.dumps({'blueId':rid})),rid)
        self.assertEqual(self.lang.last_demands,())

    def test_provider_verification(self):
        rid=self.lang.identify('7');self.lang.provider.set_exact(rid,'8')
        self.assert_failure('ProviderBlueIdMismatch',lambda:self.lang.verify(rid))

    def test_invalid_provider_shape_is_invalid_evidence(self):
        rid=self.lang.identify('7');self.lang.provider.set_exact(rid,'{"value":1,"x":2}')
        self.assert_failure('ProviderBlueIdMismatch',lambda:self.lang.verify(rid))

    def test_partial_manifest_never_proves_absence(self):
        rid=self.lang.identify('{"a":1,"b":2}')
        self.lang.provider.set_response(rid,{'partialObject':{'a':1},'completeDirectManifest':False})
        result=self.lang.query(json.dumps({'blueId':rid}),'/b','present',mode='exact')
        self.assertEqual(result['outcome'],'Incomplete')

    def test_provider_defensive_snapshot(self):
        rid=self.lang.identify('7');self.lang.provider.set_exact(rid,'7')
        snap=self.lang.provider.snapshot();snap[rid]['text']='8'
        self.assertEqual(self.lang.identify(self.lang.verify(rid),mode='exact'),rid)

    def test_current_invocation_does_not_reuse_stale_evidence(self):
        rid=self.lang.publish('7');self.lang.verify(rid)
        self.lang.provider.set_exact(rid,'8')
        self.assert_failure('ProviderBlueIdMismatch',lambda:self.lang.verify(rid))

    def test_source_and_exact_export_roundtrip(self):
        original='{"type":{"name":"Custom","type":"Double"},"value":1e20}'
        doc=self.lang.create(original);rid=self.lang.publish_document(doc);wire=doc.exact_text
        self.assertEqual(self.lang.identify(wire,mode='exact'),rid)
        self.assertIn('100000000000000000000.0',wire)

    def test_currency_holder_classes(self):
        currency=self.lang.publish('name: Currency\ntype: Text',format='yaml',goal='definition')
        holder=self.lang.publish(json.dumps({'name':'Holder','currency':{'type':{'blueId':currency}}}),goal='definition')
        text=self.lang.publish('"PLN"');custom=self.lang.publish(json.dumps({'type':{'blueId':currency},'value':'PLN'}))
        values=['PLN',{'type':{'blueId':CORE['Text']},'value':'PLN'},{'blueId':text},{'blueId':custom},{'type':{'blueId':currency},'value':'PLN'}]
        ids=[self.lang.identify(json.dumps({'type':{'blueId':holder},'currency':v}))for v in values]
        self.assertEqual(ids[:3],['844qf3Ye22h84i9vMm5Jpg8t5M6UFBBo5AaBhbsCawMq']*3)
        self.assertEqual(ids[3:],['3vZvAB5unPV5z3vp1wTXCz461tNjBJGErasewFhARM7F']*2)

    def test_labels_belong_to_instance(self):
        text='{"type":{"name":"Address","description":"type only","city":{"type":"Text"}},"city":"Warsaw","name":"Delivery"}'
        view=self.lang.resolve(text)['view']
        self.assertEqual(view['labels'],{'name':'Delivery'})
        self.assertNotIn('description',view['labels'])

    def test_schema_bounds_narrow(self):
        for lo,hi in [(5,10),(6,9),(5,9),(6,10)]:
            text=json.dumps({'type':{'type':'Integer','schema':{'minimum':5,'maximum':10}},'schema':{'minimum':lo,'maximum':hi}})
            self.lang.validate(text,goal='definition')

    def test_explicit_schema_widening_rejected(self):
        for lo,hi in [(4,11),(4,10),(5,11)]:
            text=json.dumps({'type':{'type':'Integer','schema':{'minimum':5,'maximum':10}},'schema':{'minimum':lo,'maximum':hi}})
            self.assert_failure('SchemaWeakening',lambda:self.lang.validate(text,goal='definition'))

    def test_schema_omission_inherits(self):
        text='{"type":{"type":"Integer","schema":{"minimum":5,"maximum":10}},"value":7}'
        self.lang.validate(text)
        self.assert_failure('SchemaViolation',lambda:self.lang.validate(text.replace('"value":7','"value":4')))

    def test_fixed_scalar_cannot_change(self):
        self.assert_failure('FixedValueConflict',lambda:self.lang.validate('{"type":{"x":1},"x":2}'))

    def test_list_hole_fill_append_reload(self):
        base=self.lang.publish('{"name":"Base List","type":"List","items":["X",null,"Y"]}')
        source=json.dumps({'type':{'blueId':base},'items':['X',42,'Y','Z']})
        rid=self.lang.publish(source)
        self.assertEqual(self.lang.validate(source),rid)
        values=self.lang.resolve(json.dumps({'blueId':rid}))['view']['items']
        self.assertEqual([v['value'].get('value',v['value'].get('decimal'))for v in values],['X','42','Y','Z'])
        self.assertEqual(self.lang.identify(self.lang.verify(rid),mode='exact'),rid)

    def test_list_fixed_replacement_rejected(self):
        base=self.lang.publish('{"type":"List","items":["A","B"]}')
        source=json.dumps({'type':{'blueId':base},'items':[{'$pos':1,'value':'C'}]})
        self.assert_failure('FixedValueConflict',lambda:self.lang.identify(source))

    def test_list_object_extension_preserves_fixed_fields(self):
        base=self.lang.publish('{"type":"List","items":[{"carrier":"BA"}]}')
        source=json.dumps({'type':{'blueId':base},'items':[{'$pos':0,'from':'LHR'}]})
        self.lang.validate(source)
        result=self.lang.resolve(source)['view']['items'][0]['fields']
        self.assertEqual(result['carrier']['value']['value'],'BA')
        self.assertEqual(result['from']['value']['value'],'LHR')

    def test_append_only_rejects_edits(self):
        base=self.lang.publish('{"type":"List","mergePolicy":"append-only","items":[{"$previousItems":false},"A"]}')
        self.assert_failure('ListControlViolation',lambda:self.lang.identify(json.dumps({'type':{'blueId':base},'items':[{'$pos':0,'value':'A'}]})))

    def test_type_only_definition_does_not_supply_value(self):
        self.lang.validate('{"type":"Integer","schema":{"minimum":5}}',goal='definition')
        self.assert_failure('SchemaViolation',lambda:self.lang.validate('{"type":"Integer","schema":{"minimum":5}}'))

    def test_minimization_roundtrip(self):
        src='{"type":{"x":1},"x":1,"y":2}'
        result=self.lang.minimize(src)
        c=self.lang._context();a=self.lang._input(src,c,'source','json');b=self.lang._input(result,c,'source','json')
        self.assertTrue(B.same_view(a,b,c))

    def test_fragments_order_and_reconstruction(self):
        src='{"left":{"deep":{"x":1}},"right":{"y":2}}'
        a=self.lang.split(src,['/left/deep','/right']);b=self.lang.split(src,['/right','/left/deep'])
        self.assertEqual(a,b);self.assertEqual(len(a['fragments']),4)
        for rid,body in a['fragments'].items():self.lang.provider.set_exact(rid,body)
        self.assertEqual(self.lang.identify(a['rootText'],mode='exact'),self.lang.identify(src))
        self.assertEqual(self.lang.query(a['rootText'],'/left/deep/x','value',mode='exact')['value']['decimal'],'1')

    def test_cyclic_finalize_publish_verify(self):
        z=self.lang.finalize(['{"name":"A","next":{"blueId":"this#1"}}','{"name":"B","next":{"blueId":"this#0"}}'],publish=True)
        self.assertEqual(z['master'],'C18ETfS2A7MNmBGo67MYaQrRL9TrUSGwvvEu6KoMqC2R')
        for rid in z['blueIds']:self.lang.verify(rid)

    def test_cyclic_member_body_not_member_identity(self):
        z=self.lang.finalize(['{"name":"Loop","self":{"blueId":"this#0"}}'],publish=True)
        self.assertNotEqual(self.lang.identify(self.lang.verify(z['blueIds'][0]),mode='exact'),z['blueIds'][0])

    def test_provider_restart(self):
        rid=self.lang.publish('name: Saved\na: [1, 2]',format='yaml')
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'provider.json';self.lang.provider.dump(path)
            restarted=Language(MemoryProvider.load(path))
            self.assertEqual(restarted.identify(restarted.verify(rid),mode='exact'),rid)

    def test_path_escapes_and_empty_root(self):
        src='{"":"empty","a/b":{"c~d":7}}'
        self.assertEqual(self.lang.query(src,'/','value')['value']['value'],'empty')
        self.assertEqual(self.lang.query(src,'/a~1b/c~0d','value')['value']['decimal'],'7')

    def test_unrelated_reference_not_fetched_for_identity(self):
        rid=self.lang.identify('"unavailable"')
        src=json.dumps({'type':{'name':'Custom'},'other':{'blueId':rid}})
        self.lang.raw_identify(src);self.assertEqual(self.lang.last_demands,())

if __name__=='__main__':unittest.main()
