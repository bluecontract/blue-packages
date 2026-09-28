"""Public admission tests. Expectations describe the contract, not observed output."""
from __future__ import annotations
import copy,json,tempfile,unittest
from pathlib import Path
from dataclasses import replace
from blue_language import Language,MemoryProvider,Failure,CORE,AdmittedDocument,Limits
from algorithms import blue as B
ROOT=Path(__file__).resolve().parents[2]
PAIR='9ExKbrHq1ZMpFiEESUPLpfoRegzkReCV9164BuUJoDEh'
PREFIX='49W45qY1LKK66NNRDF8k3W75zd8mj48Fh9wBs31ZNceB'
RESULT='EDEm6BiWq1YTaCHUSbxtSakf3Ebi7Tar1TLuHArkhru6'
def wire(x):return json.dumps(x,ensure_ascii=False)

class AdmissionTests(unittest.TestCase):
    def setUp(self):self.l=Language()
    def fails(self,category,fn):
        with self.assertRaises(Failure)as cm:fn()
        self.assertEqual(cm.exception.category,category)
    def tutorial(self):
        data=json.loads((ROOT/'examples/append_only_pair.json').read_text())
        self.assertEqual(self.l.publish(wire(data['typeSource']),goal='definition'),PAIR)
        return data
    def test_tutorial_expected_expanded_and_prefix_identity(self):
        s=wire(self.tutorial()['source']);d=self.l.create(s)
        self.assertEqual(d.blue_id,RESULT)
        full=json.loads(d.exact_text)['entries']['items']
        self.assertEqual([x['value']for x in full],['A','B','C'])
        compact=json.loads(d.canonical_text)['entries']['items']
        self.assertEqual(compact[0],{'$previous':{'blueId':PREFIX}})
        self.assertEqual(len(compact),2);self.assertEqual(compact[1]['value'],'C')
        self.assertEqual(self.l.raw_identify(d.exact_text,mode='exact'),RESULT)
        self.assertEqual(self.l.identify(d.canonical_text,mode='canonical'),RESULT)
    def test_tutorial_source_replay_of_emitted_anchor_is_not_double_append(self):
        d=self.l.create(wire(self.tutorial()['source']))
        self.assertEqual(self.l.identify(d.canonical_text),RESULT)
        self.assertEqual(self.l.resolve(d.canonical_text)['view']['fields']['entries']['items'][-1]['value']['value'],'C')
    def test_tutorial_literal_prefix_reference_is_not_splicing(self):
        d=self.l.create(wire(self.tutorial()['source']));self.l.publish_document(d)
        raw=json.loads(d.canonical_text)
        raw['entries']['items'][0]={'blueId':PREFIX}
        # A normal reference supplies a list element, not the parent's two entries.
        self.assertNotEqual(self.l.raw_identify(wire(raw),mode='exact'),RESULT)
        self.fails('FixedValueConflict',lambda:self.l.identify(wire(raw),mode='exact'))
    def test_tutorial_fresh_store_roundtrip(self):
        d=self.l.create(wire(self.tutorial()['source']));self.l.publish_document(d)
        fresh=Language(MemoryProvider(self.l.provider.snapshot()))
        for text,mode in [(d.canonical_text,'canonical'),(d.exact_text,'exact'),(wire({'blueId':d.blue_id}),'exact')]:
            self.assertEqual(fresh.identify(text,mode=mode),RESULT)
            xs=fresh.resolve(text,mode=mode)['view']['fields']['entries']['items']
            self.assertEqual([x['value']['value']for x in xs],['A','B','C'])
        self.assertIn(PREFIX,fresh.provider.snapshot())
    def test_tutorial_omitted_local_core_type_still_constructs(self):
        x=self.tutorial()['source'];del x['entries']['type']
        d=self.l.create(wire(x));xs=self.l.resolve(wire(x))['view']['fields']['entries']['items']
        self.assertEqual([y['value']['value']for y in xs],['A','B','C'])
        self.assertEqual(json.loads(d.canonical_text)['entries'][0]['$previous']['blueId'],PREFIX)
    def test_tutorial_inline_parent_is_identical(self):
        data=self.tutorial();s=copy.deepcopy(data['source']);s['type']=data['typeSource']
        self.assertEqual(self.l.identify(wire(s)),RESULT)
    def test_source_suffix_is_not_valid_complete_exact_payload(self):
        s=self.tutorial()['source'];s['entries']['type']={'blueId':CORE['List']};s['entries']['items']=['C']
        self.fails('FixedValueConflict',lambda:self.l.identify(wire(s),mode='exact'))
    def test_wrong_anchor_rejected_before_success(self):
        s=self.tutorial()['source'];s['entries']['items']=[{'$previous':{'blueId':self.l.raw_identify('["X"]')}},'C']
        self.fails('ListControlViolation',lambda:self.l.identify(wire(s)))
    def test_canonical_wrong_prefix_rejected(self):
        d=self.l.create(wire(self.tutorial()['source']));bad=json.loads(d.canonical_text)
        other=self.l.publish('["X","B"]');bad['entries']['items'][0]['$previous']['blueId']=other
        self.fails('InvalidCanonicalList',lambda:self.l.identify(wire(bad),mode='canonical'))
    def test_canonical_input_has_no_source_aliases(self):
        self.fails('UnknownTypeAlias',lambda:self.l.identify('{"type":"List","items":[]}',mode='canonical'))
    def test_metadata_bearing_prefix_id_rejected(self):
        d=self.l.create(wire(self.tutorial()['source']));bad=json.loads(d.canonical_text)
        typed=self.l.publish('{"type":"List","items":["A","B"]}')
        bad['entries']['items'][0]['$previous']['blueId']=typed
        self.fails('InvalidCanonicalList',lambda:self.l.identify(wire(bad),mode='canonical'))
    def test_late_anchor_is_invalid_canonical_wire(self):
        d=self.l.create(wire(self.tutorial()['source']));bad=json.loads(d.canonical_text)
        bad['entries']['items'].reverse()
        self.fails('InvalidCanonicalList',lambda:self.l.identify(wire(bad),mode='canonical'))
    def test_append_only_positional_edit_forbidden(self):
        s=self.tutorial()['source'];s['entries']['items']=[{'$pos':0,'value':'A'},'C']
        self.fails('ListControlViolation',lambda:self.l.identify(wire(s)))
    def test_repeated_empty_suffix_does_not_repeat_base(self):
        s=self.tutorial()['source'];s['entries']['items']=[{'$previousItems':True}]
        d=self.l.create(wire(s));xs=self.l.resolve(wire(s))['view']['fields']['entries']['items']
        self.assertEqual([x['value']['value']for x in xs],['A','B'])
        self.assertEqual(self.l.identify(d.canonical_text,mode='canonical'),d.blue_id)
    def test_transitive_append_base_commits_complete_prefix(self):
        first=self.l.publish('{"name":"First","type":"List","mergePolicy":"append-only","items":[{"$previousItems":false},"A"]}')
        second=self.l.publish(wire({'name':'Second','type':{'blueId':first},'items':[{'$previousItems':True},'B']}))
        d=self.l.create(wire({'type':{'blueId':second},'items':[{'$previousItems':True},'C']}))
        self.assertEqual(json.loads(d.canonical_text)['items'][0]['$previous']['blueId'],PREFIX)
        self.assertEqual([v['value']for v in json.loads(d.exact_text)['items']],['A','B','C'])
    def test_nested_suffix_below_two_objects(self):
        parent={'outer':{'inner':{'type':'List','mergePolicy':'append-only','items':[{'$previousItems':False},'A','B']}}}
        pid=self.l.publish(wire(parent),goal='definition')
        s={'type':{'blueId':pid},'outer':{'inner':{'items':[{'$previousItems':True},'C']}}}
        d=self.l.create(wire(s))
        self.assertEqual(json.loads(d.canonical_text)['outer']['inner'][0]['$previous']['blueId'],PREFIX)
        self.assertEqual([x['value']for x in json.loads(d.exact_text)['outer']['inner']],['A','B','C'])
    def test_reference_child_is_complete_not_source_suffix(self):
        data=self.tutorial();cid=self.l.publish('{"type":"List","items":["A","B","C"]}')
        s=data['source'];s['entries']={'blueId':cid}
        self.assertEqual(self.l.identify(wire(s)),RESULT)
        self.assertEqual(len(self.l.resolve(wire(s))['view']['fields']['entries']['items']),3)
    def test_list_item_constraints_apply_after_append(self):
        pid=self.l.publish('{"entries":{"type":"List","itemType":"Integer","mergePolicy":"append-only","items":[{"$previousItems":false},1,2]}}',goal='definition')
        self.l.identify(wire({'type':{'blueId':pid},'entries':{'items':[{'$previousItems':True},3]}}))
        self.fails('TypeCompatibilityViolation',lambda:self.l.identify(wire({'type':{'blueId':pid},'entries':{'items':[{'$previousItems':True},'bad']}})))
    def test_max_items_applies_to_complete_payload(self):
        p=self.l.publish('{"entries":{"type":"List","items":["A","B"],"schema":{"maxItems":2}}}',goal='definition')
        self.fails('SchemaViolation',lambda:self.l.identify(wire({'type':{'blueId':p},'entries':{'items':['A','B','C']}})))

    def test_illegal_unknown_type_not_admitted(self):
        missing=self.l.raw_identify('{"x":2}')
        s=wire({'type':{'blueId':missing},'x':1})
        for f in (self.l.identify,self.l.canonicalize,self.l.publish,self.l.validate):
            with self.subTest(operation=f.__name__): self.fails('ProviderUnavailable',lambda:f(s))
        self.assertEqual(self.l.provider.snapshot(),{})
    def test_fixed_value_conflict_not_cleaned_away(self):
        tid=self.l.publish('{"x":2}',goal='definition');s=wire({'type':{'blueId':tid},'x':1})
        before=self.l.provider.snapshot()
        for f in (self.l.identify,self.l.canonicalize,self.l.publish,self.l.validate):
            with self.subTest(operation=f.__name__): self.fails('FixedValueConflict',lambda:f(s))
        self.assertEqual(before,self.l.provider.snapshot())
        self.assertIsInstance(self.l.raw_identify(s),str)
    def test_invalid_type_evidence_rejected(self):
        tid=self.l.raw_identify('{"x":2}');self.l.provider.set_exact(tid,'{"x":1}')
        self.fails('ProviderBlueIdMismatch',lambda:self.l.identify(wire({'type':{'blueId':tid}})))
    def test_empty_list_item_type_must_be_known(self):
        tid=self.l.raw_identify('{"name":"Unknown"}')
        self.fails('ProviderUnavailable',lambda:self.l.identify(wire({'type':'List','itemType':{'blueId':tid},'items':[]})))
    def test_empty_dictionary_key_type_must_be_known(self):
        tid=self.l.raw_identify('{"name":"Unknown"}')
        self.fails('ProviderUnavailable',lambda:self.l.identify(wire({'type':'Dictionary','keyType':{'blueId':tid}})))
    def test_empty_dictionary_value_type_must_be_known(self):
        tid=self.l.raw_identify('{"name":"Unknown"}')
        self.fails('ProviderUnavailable',lambda:self.l.identify(wire({'type':'Dictionary','valueType':{'blueId':tid}})))
    def test_empty_dictionary_nonscalar_key_type_rejected(self):
        self.fails('TypeCompatibilityViolation',lambda:self.l.identify('{"type":"Dictionary","keyType":"List"}'))
    def test_empty_dictionary_scalar_key_type_allowed(self):
        self.l.identify('{"type":"Dictionary","keyType":"Boolean"}')
    def test_hidden_unknown_type_behind_unconstrained_reference_rejected(self):
        tid=self.l.raw_identify('{"name":"Unknown"}')
        body=wire({'type':{'blueId':tid},'x':1});cid=self.l.raw_identify(body)
        self.l.provider.set_exact(cid,body)
        self.fails('ProviderUnavailable',lambda:self.l.identify(wire({'hidden':{'blueId':cid}})))
    def test_unused_invalid_item_definition_rejected(self):
        base=self.l.publish('{"x":2}',goal='definition');bad=wire({'type':{'blueId':base},'x':1})
        tid=self.l.raw_identify(bad);self.l.provider.set_exact(tid,bad)
        self.fails('FixedValueConflict',lambda:self.l.identify(wire({'type':'List','itemType':{'blueId':tid},'items':[]})))
    def test_partial_query_never_becomes_full_admission(self):
        tid=self.l.raw_identify('"missing"');src=wire({'x':1,'hidden':{'blueId':tid}})
        self.assertEqual(self.l.query(src,'/x','value')['value']['decimal'],'1')
        self.fails('ProviderUnavailable',lambda:self.l.identify(src))
    def test_definition_role_is_explicit(self):
        s='{"type":"Integer","schema":{"minimum":5}}'
        d=self.l.admit_definition(s)
        self.assertEqual(d.goal,'definition');self.l.publish_document(d)
        self.fails('SchemaViolation',lambda:self.l.create(s))
        self.fails('InvalidValidationEvidence',lambda:self.l.create(d))
    def test_duplicate_inherited_field_removed_only_after_validating(self):
        t={'amount':{'type':{'blueId':CORE['Integer']},'value':42},'currency':{'type':{'blueId':CORE['Text']},'value':'PLN'},'name':'Example'}
        tid=self.l.publish(wire(t),goal='definition');self.assertEqual(tid,'2EgiMQBQBKBUVtsgEbzwwgtjbZnA34u86jWNCKd3Nc1D')
        a={'type':{'blueId':tid},'x':1,'amount':42};b={'type':{'blueId':tid},'x':1}
        da=self.l.create(wire(a));db=self.l.create(wire(b))
        self.assertEqual(da.blue_id,'JUhfQvQwZgS3bqRRYbpyvahHBAdrbhUvL116W2BgZXW')
        self.assertEqual(da.blue_id,db.blue_id);self.assertEqual(da.removed_fields,('/amount',))
        self.assertNotIn('amount',json.loads(da.exact_text))
        self.assertNotEqual(self.l.raw_identify(wire(a)),self.l.raw_identify(wire(b)))
    def test_duplicate_reference_and_inline_field_removed_equally(self):
        t=self.l.publish('{"amount":42}',goal='definition');v=self.l.publish('42')
        roots=[{'type':{'blueId':t},'x':1,'amount':x}for x in (42,{'type':'Integer','value':42},{'blueId':v})]
        ids=[self.l.identify(wire(r))for r in roots]
        self.assertEqual(len(set(ids)),1)
    def test_extra_label_is_not_an_exact_duplicate(self):
        t=self.l.publish('{"amount":42}',goal='definition')
        s={'type':{'blueId':t},'amount':{'name':'Confirmed amount','type':'Integer','value':42}}
        d=self.l.create(wire(s));self.assertIn('amount',json.loads(d.exact_text))
    def test_partial_child_is_not_turned_into_delta(self):
        t=self.l.publish('{"a":{"a1":1}}',goal='definition')
        s={'type':{'blueId':t},'a':{'a1':1,'b2':2}}
        d=self.l.create(wire(s));self.assertIn('a1',json.loads(d.exact_text)['a'])
        ref=self.l.publish('{"a1":1,"b2":2}')
        s['a']={'blueId':ref};self.assertEqual(self.l.identify(wire(s)),d.blue_id)
    def test_existing_noncanonical_reference_not_reidentified(self):
        t=self.l.publish('{"amount":42}',goal='definition');s=wire({'type':{'blueId':t},'amount':42})
        old=self.l.publish_raw(s);normal=self.l.identify(s)
        self.assertNotEqual(old,normal)
        self.assertEqual(self.l.identify(wire({'blueId':old})),old)
        self.assertEqual(self.l.identify(self.l.verify(old),mode='exact'),old)
    def test_schema_weakening_rejected_before_canonicalization(self):
        p=self.l.publish('{"type":"Integer","schema":{"minimum":5,"maximum":10}}',goal='definition')
        bad=wire({'type':{'blueId':p},'schema':{'minimum':4,'maximum':11},'value':7})
        self.fails('SchemaWeakening',lambda:self.l.create(bad))
    def test_trusted_handle_reuses_completed_evidence(self):
        d=self.l.create('{"type":{"x":2},"x":2,"y":1}')
        self.assertEqual(self.l.identify(d),d.blue_id);self.assertEqual(self.l.last_demands,())
        self.assertEqual(self.l.publish_document(d),d.blue_id)
    def test_handle_from_another_instance_is_not_accepted(self):
        d=self.l.create('1');other=Language()
        self.fails('InvalidValidationEvidence',lambda:other.identify(d))
    def test_forged_or_mutated_handle_not_accepted(self):
        d=self.l.create('1');bad=replace(d,exact_text='2')
        self.fails('InvalidValidationEvidence',lambda:self.l.identify(bad))
        object.__setattr__(d,'blue_id',self.l.raw_identify('2'))
        self.fails('InvalidValidationEvidence',lambda:self.l.identify(d))
    def test_signed_evidence_can_survive_restart(self):
        d=self.l.create(wire(self.tutorial()['source']));key=bytes(range(32))
        sealed=self.l.export_validated(d,key);fresh=Language()
        restored=fresh.import_validated(sealed,key,goal='value')
        self.assertEqual(fresh.last_demands,());self.assertEqual(fresh.publish_document(restored),RESULT)
        self.assertEqual(fresh.identify(restored),RESULT)
        self.assertEqual(fresh.resolve(restored.exact_text,mode='exact')['blueId'],RESULT)
    def test_signed_evidence_wrong_key_rejected(self):
        d=self.l.create('1');s=self.l.export_validated(d,b'A'*32)
        self.fails('InvalidValidationEvidence',lambda:Language().import_validated(s,b'B'*32))
    def test_signed_evidence_tamper_rejected(self):
        d=self.l.create('1');s=json.loads(self.l.export_validated(d,b'A'*32));s['payload']['exactText']='2'
        self.fails('InvalidValidationEvidence',lambda:Language().import_validated(wire(s),b'A'*32))
    def test_signed_definition_cannot_satisfy_value_goal(self):
        d=self.l.admit_definition('{"type":"Integer"}');s=self.l.export_validated(d,b'A'*32)
        self.fails('InvalidValidationEvidence',lambda:Language().import_validated(s,b'A'*32,goal='value'))
    def test_importing_boolean_validity_claim_is_rejected(self):
        self.fails('InvalidValidationEvidence',lambda:self.l.import_validated('{"valid":true}',b'A'*32))
    def test_definition_invalidated_by_new_policy(self):
        d=self.l.create('1');payload=self.l._document_payload(d);payload['policy']='old'
        # Even correctly signed evidence for another policy must be rejected.
        import hmac,hashlib
        key=b'A'*32;signature=hmac.new(key,json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode(),hashlib.sha256).hexdigest()
        self.fails('InvalidValidationEvidence',lambda:self.l.import_validated(wire({'payload':payload,'hmacSha256':signature}),key))
    def test_plain_text_after_provider_tamper_does_not_use_old_certificate(self):
        t=self.l.publish('{"x":2}',goal='definition');src=wire({'type':{'blueId':t}})
        self.l.create(src);self.l.provider.set_exact(t,'{"x":1}')
        self.fails('ProviderBlueIdMismatch',lambda:self.l.create(src))
    def test_minimization_fresh_call_has_new_replacement_body(self):
        t=self.l.publish('{"name":"HoleList","type":"List","items":[null]}',goal='definition')
        src=wire({'type':{'blueId':t},'items':[{'$pos':0,'$replace':{'x':1}}]})
        out=self.l.minimize(src);fresh=Language(MemoryProvider(self.l.provider.snapshot()))
        self.assertEqual(fresh.resolve(out)['view'],self.l.resolve(src)['view'])
    def test_minimization_contextual_core_list_roundtrip(self):
        src=wire(self.tutorial()['source']);out=self.l.minimize(src)
        fresh=Language(MemoryProvider(self.l.provider.snapshot()))
        self.assertEqual(fresh.resolve(out)['view'],self.l.resolve(src)['view'])
    def test_literal_control_content_canonical_escape_roundtrip(self):
        raw={'items':[{'$pos':0,'$replace':{'value':'A'}}]}
        d=self.l.create(wire(raw),mode='exact');self.l.publish_document(d)
        self.assertEqual(self.l.identify(d.canonical_text,mode='canonical'),d.blue_id)
        self.assertIn('blueId',json.loads(d.canonical_text)[0])
    def test_finalize_does_not_publish_invalid_type_cycle(self):
        before=self.l.provider.snapshot()
        self.fails('TypeCycle',lambda:self.l.finalize(['{"name":"Bad","type":{"blueId":"this#0"}}'],publish=True))
        self.assertEqual(before,self.l.provider.snapshot())

if __name__=='__main__':unittest.main()
