from __future__ import annotations
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from blue_language import Language,MemoryProvider,Failure,CORE

EXAMPLE='2EgiMQBQBKBUVtsgEbzwwgtjbZnA34u86jWNCKd3Nc1D'
FOO='ECc6R5e3P3NXPfji7AroyyArv3MKFacsff8AEBoATHji'
CURRENCY='A6bEQcVduDsMYqrecotcG1NPMXeYf8PncRbqe3CFTUXN'

def text(x):return json.dumps(x,ensure_ascii=False)

class DiagnosticTests(unittest.TestCase):
    def setUp(self):self.l=Language()
    def failure(self,source,category,**options):
        result=self.l.check(source,**options)
        self.assertEqual(result['outcome'],'Incomplete' if category in ('ProviderUnavailable','OperationLimitExceeded') else 'Invalid',result)
        self.assertEqual(result['category'],category,result)
        self.assertNotIn('blueId',result)
        return result
    def example(self):
        self.assertEqual(self.l.publish('name: Example\namount: 42\ncurrency: PLN\n',format='yaml',goal='definition'),EXAMPLE)
    def foo(self):
        self.assertEqual(self.l.publish('name: Foo\nbar:\n  type: Integer\n',format='yaml',goal='definition'),FOO)
    def test_screenshot_fixed_currency(self):
        self.example();before=self.l.provider.snapshot()
        d=self.failure(f'type:\n  blueId: {EXAMPLE}\ncurrency: USD\nx: 1\n','FixedValueConflict',format='yaml')
        self.assertEqual(d['path'],'/currency');self.assertEqual(d['expected']['value'],'PLN');self.assertEqual(d['actual']['value'],'USD')
        self.assertEqual(d['expected']['type']['name'],'Text');self.assertEqual(d['documentType']['name'],'Example')
        self.assertEqual(d['message'],'The value at /currency is fixed to "PLN" (Text); received "USD" (Text). An inherited fixed value cannot be changed.')
        self.assertEqual(before,self.l.provider.snapshot())
    def test_fixed_conflict_is_not_fixed_by_definition_mode(self):
        self.example()
        d=self.failure(text({'type':{'blueId':EXAMPLE},'currency':'USD'}),'FixedValueConflict',goal='definition')
        self.assertNotIn('hint',d);self.assertEqual(d['goal'],'definition')
    def test_fixed_error_explicit_and_reference_equivalent(self):
        self.example();usd=self.l.publish('"USD"')
        inputs=['USD',{'type':{'blueId':CORE['Text']},'value':'USD'},{'blueId':usd}]
        ds=[self.failure(text({'type':{'blueId':EXAMPLE},'currency':x}),'FixedValueConflict') for x in inputs]
        for d in ds[1:]:
            for k in ('path','category','message','expected','actual','documentType'):self.assertEqual(d[k],ds[0][k])
    def test_screenshot_foo_text_is_integer_error(self):
        self.foo();s=f'blue:\n  imports:\n    Foo:\n      blueId: {FOO}\ntype: Foo\nname: test\nbar: tekst a Foo ma bar jako integer\n'
        d=self.failure(s,'TypeCompatibilityViolation',format='yaml')
        self.assertEqual(d['path'],'/bar');self.assertEqual(d['expected']['type']['name'],'Integer');self.assertEqual(d['actual']['type']['name'],'Text')
        self.assertEqual(d['documentType']['name'],'Foo');self.assertIn('Expected Integer',d['message']);self.assertNotIn(CORE['Integer'],d['message'])
        self.assertEqual(d['expected']['type']['blueId'],CORE['Integer']);self.assertIn(CORE['Integer'],d['detail'])
    def test_foo_type_inline_and_referenced_same_diagnostic(self):
        self.foo();a=self.failure(text({'type':{'name':'Foo','bar':{'type':'Integer'}},'bar':'bad'}),'TypeCompatibilityViolation')
        b=self.failure(text({'type':{'blueId':FOO},'bar':'bad'}),'TypeCompatibilityViolation')
        for k in ('path','category','message','expected','actual','documentType'):self.assertEqual(a[k],b[k])
    def test_foo_integer_success_unchanged(self):
        self.foo();r=self.l.check(text({'type':{'blueId':FOO},'bar':7}));self.assertEqual(r['outcome'],'Established');self.assertTrue(r['validated'])
    def test_nested_field_pointer(self):
        self.foo();t=self.l.publish(text({'child':{'type':{'blueId':FOO}}}),goal='definition')
        d=self.failure(text({'type':{'blueId':t},'child':{'bar':'bad'}}),'TypeCompatibilityViolation')
        self.assertEqual(d['path'],'/child/bar')
    def test_typed_list_item_pointer(self):
        self.foo();d=self.failure(text({'type':'List','itemType':{'blueId':FOO},'items':[{'bar':1},{'bar':'bad'}]}),'TypeCompatibilityViolation')
        self.assertEqual(d['path'],'/items/1/bar')
    def test_dictionary_value_type_pointer(self):
        d=self.failure(text({'type':'Dictionary','valueType':'Integer','a':1,'b':'bad'}),'TypeCompatibilityViolation')
        self.assertEqual(d['path'],'/b')
    def test_empty_property_name_is_not_root(self):
        tid=self.l.publish(text({'':{'type':'Integer'}}),goal='definition')
        d=self.failure(text({'type':{'blueId':tid},'':'bad'}),'TypeCompatibilityViolation')
        self.assertEqual(d['path'],'/');self.assertIn('at /;',d['message'])
    def test_json_pointer_escaping(self):
        tid=self.l.publish(text({'a/b~c':{'type':'Integer'}}),goal='definition')
        d=self.failure(text({'type':{'blueId':tid},'a/b~c':'bad'}),'TypeCompatibilityViolation')
        self.assertEqual(d['path'],'/a~1b~0c')
    def test_optional_field_count_does_not_lose_child_error_path(self):
        tid=self.l.publish(text({'schema':{'minFields':1},'a':1}),goal='definition')
        d=self.failure(text({'type':{'blueId':tid},'a':2}),'FixedValueConflict')
        self.assertEqual(d['path'],'/a')
    def test_missing_type_pointer(self):
        unknown=self.l.raw_identify('{"name":"Not installed"}')
        d=self.failure(text({'bar':{'type':{'blueId':unknown}}}),'ProviderUnavailable')
        self.assertEqual(d['path'],'/bar/type');self.assertIn(unknown,d['message']);self.assertNotIn('documentType',d)
    def test_bad_provider_not_rendered_as_missing(self):
        self.foo();self.l.provider.set_exact(FOO,'{"name":"wrong"}')
        d=self.failure(text({'type':{'blueId':FOO},'bar':1}),'ProviderBlueIdMismatch')
        self.assertEqual(d['outcome'],'Invalid');self.assertEqual(d['path'],'/type')
    def test_core_display_cannot_be_spoofed_by_a_custom_name(self):
        tid=self.l.publish('{"name":"Integer","type":"Text"}',goal='definition')
        parent=self.l.publish('{"bar":{"type":"Integer"}}',goal='definition')
        d=self.failure(text({'type':{'blueId':parent},'bar':{'type':{'blueId':tid},'value':'bad'}}),'TypeCompatibilityViolation')
        self.assertFalse(d['actual']['type']['core']);self.assertIn('custom type '+tid,d['message']);self.assertTrue(d['expected']['type']['core'])
    def test_long_error_value_has_bounded_preview(self):
        self.foo();d=self.failure(text({'type':{'blueId':FOO},'bar':'Z'*10000}),'TypeCompatibilityViolation')
        self.assertTrue(d['actual']['value']['truncated']);self.assertEqual(d['actual']['value']['length'],10000);self.assertLess(len(d['message']),500)
    def test_exception_string_is_human_readable(self):
        self.foo()
        with self.assertRaises(Failure) as caught:self.l.identify(text({'type':{'blueId':FOO},'bar':'bad'}))
        self.assertIn('Expected Integer at /bar',str(caught.exception));json.dumps(caught.exception.as_dict())
    def test_diagnostics_do_not_add_provider_fetches(self):
        self.foo();d=self.failure(text({'type':{'blueId':FOO},'bar':'bad'}),'TypeCompatibilityViolation')
        self.assertEqual(d['requestedBlueIds'],[FOO])
    def test_error_path_does_not_leak_between_operations(self):
        self.foo();self.failure(text({'type':{'blueId':FOO},'bar':'bad'}),'TypeCompatibilityViolation')
        d=self.failure('name: Currency\ntype: Text\n','SchemaViolation',format='yaml');self.assertEqual(d['path'],'')
    def test_source_refinement_fixed_conflict_has_slot_pointer(self):
        tid=self.l.publish('{"entries":{"type":"List","items":["A","B"]}}',goal='definition')
        d=self.failure(text({'type':{'blueId':tid},'entries':{'items':[{'$pos':1,'value':'C'}]}}),'FixedValueConflict')
        self.assertEqual(d['path'],'/entries/items/1')
    def test_screenshot_currency_definition_succeeds(self):
        d=self.l.admit_definition('name: Currency\ntype: Text\n',format='yaml')
        self.assertEqual(d.blue_id,CURRENCY);self.assertEqual(d.goal,'definition');self.assertNotIn('value',json.loads(d.exact_text))
    def test_currency_value_mode_has_explicit_definition_hint(self):
        d=self.failure('name: Currency\ntype: Text\n','SchemaViolation',format='yaml')
        self.assertEqual(d['path'],'');self.assertEqual(d['expected']['type']['name'],'Text');self.assertTrue(d['expected']['present'])
        self.assertFalse(d['actual']['present']);self.assertIn('Definition',d['hint']);self.assertEqual(self.l.provider.snapshot(),{})
    def test_no_silent_value_to_definition_fallback(self):
        with self.assertRaises(Failure):self.l.publish('name: Currency\ntype: Text\n',format='yaml')
        self.assertEqual(self.l.provider.snapshot(),{})
    def test_scalar_and_collection_definitions_all_succeed(self):
        for core in CORE:
            with self.subTest(core=core):
                d=self.l.admit_definition(text({'name':'Custom '+core,'type':core}))
                self.assertEqual(d.goal,'definition');self.assertNotIn('value',json.loads(d.exact_text));self.assertNotIn('items',json.loads(d.exact_text))
    def test_text_schema_definition_and_values(self):
        t=self.l.publish('{"name":"ThreeLetters","type":"Text","schema":{"minLength":3,"maxLength":3}}',goal='definition')
        self.l.identify(text({'type':{'blueId':t},'value':'PLN'}))
        d=self.failure(text({'type':{'blueId':t},'value':'EURO'}),'SchemaViolation');self.assertEqual(d['keyword'],'maxLength');self.assertEqual(d['expected']['value'],3)
    def test_list_schema_definition_without_items(self):
        t=self.l.publish('{"name":"TwoToFour","type":"List","itemType":"Integer","schema":{"minItems":2,"maxItems":4}}',goal='definition')
        self.l.identify(text({'type':{'blueId':t},'items':[1,2]}))
        d=self.failure(text({'type':{'blueId':t}}),'SchemaViolation');self.assertIn('Definition',d['hint'])
    def test_explicit_empty_list_is_fixed_payload_even_in_definition(self):
        self.failure('{"type":"List","items":[],"schema":{"minItems":2}}','SchemaViolation',goal='definition')
    def test_schema_narrowing_named_types_and_error_values(self):
        t=self.l.publish('{"name":"Range","type":"Integer","schema":{"minimum":5,"maximum":10}}',goal='definition')
        n=self.l.publish(text({'name':'NarrowRange','type':{'blueId':t},'schema':{'minimum':6,'maximum':9}}),goal='definition')
        self.l.identify(text({'type':{'blueId':n},'value':7}))
        d=self.failure(text({'type':{'blueId':t},'schema':{'minimum':4,'maximum':11}}),'SchemaWeakening',goal='definition')
        self.assertEqual(d['keyword'],'minimum');self.assertEqual(d['expected']['value']['numerator'],'5');self.assertEqual(d['actual']['value']['numerator'],'4')
    def test_list_schema_cannot_weaken(self):
        t=self.l.publish('{"name":"Bounded","type":"List","schema":{"minItems":2,"maxItems":4}}',goal='definition')
        self.l.admit_definition(text({'type':{'blueId':t},'schema':{'minItems':3,'maxItems':3}}))
        d=self.failure(text({'type':{'blueId':t},'schema':{'minItems':1}}),'SchemaWeakening',goal='definition');self.assertEqual(d['keyword'],'minItems')
    def test_definition_does_not_hide_invalid_kind_schema(self):
        self.failure('{"type":"Text","schema":{"minimum":5}}','SchemaViolation',goal='definition')
    def test_definition_publication_and_fresh_reload(self):
        d=self.l.admit_definition('name: Currency\ntype: Text\n',format='yaml');self.l.publish_document(d)
        fresh=Language(MemoryProvider(self.l.provider.snapshot()));loaded=fresh.load(CURRENCY,goal='definition')
        self.assertEqual(loaded.blue_id,CURRENCY)
        with self.assertRaises(Failure):fresh.load(CURRENCY,goal='value')
    def test_definition_certificate_does_not_certify_completed_value(self):
        d=self.l.admit_definition('name: Currency\ntype: Text\n',format='yaml')
        with self.assertRaises(Failure) as e:self.l.identify(d)
        self.assertEqual(e.exception.category,'InvalidValidationEvidence')
    def test_required_nested_value_has_node_path(self):
        t=self.l.publish('{"age":{"type":"Integer","schema":{"required":true}}}',goal='definition')
        d=self.failure(text({'type':{'blueId':t}}),'SchemaViolation');self.assertEqual(d['path'],'/age');self.assertEqual(d['keyword'],'required')
    def test_literal_field_shape_error_has_path(self):
        d=self.failure('{"x":{"type":"Integer","value":[]}}','InvalidScalar')
        # Preprocessing detects a malformed scalar before value normalization.
        self.assertEqual(d['phase'],'preprocessing');self.assertEqual(d['path'],'/x')
    def test_numeric_bound_diagnostic_retains_exact_rational(self):
        d=self.failure('{"type":"Integer","schema":{"minimum":5},"value":4}','SchemaViolation')
        self.assertEqual(d['keyword'],'minimum');self.assertEqual(d['expected']['value'],{'numerator':'5','denominator':'1'});self.assertEqual(d['actual']['value'],4)

if __name__=='__main__':unittest.main()
