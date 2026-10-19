from pathlib import Path
import copy
import json
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import package as publisher
from reference import Exact, ModelProvider, Verifier, ref, verify_sig, validate_endpoint, api_urls
from access_runtime import AccessExecution, control_timeline
from examples import import_inline
from blue_language.physical import PhysicalCache

class ExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope=PhysicalCache(65536).scope();cls.scope.__enter__()
        cls.addClassCleanup(cls.scope.__exit__,None,None,None)
        cls.f=json.loads((publisher.ROOT/'examples/protocol.json').read_text())
        cls.e=Exact()
        for definition in cls.f['definitions']:
            assert cls.e.define(definition['alias'],definition['body'])==definition['blueId']
        for value in (cls.f['provider'],cls.f['timelines'],cls.f['timelineAccess'],cls.f['beforeUpdate'],cls.f['entries'],cls.f['discovery']['response']):
            import_inline(cls.e,value)
        for case in cls.f['cases'].values():
            import_inline(cls.e,case['request']);import_inline(cls.e,case['response'])
        import_inline(cls.e,cls.f['afterUpdate'])
        cls.v=Verifier(cls.e,cls.f['provider'])

    def test_domain_provider_and_actor_types(self):
        self.assertTrue(self.e.kind(self.f['provider'],'Timeline Provider'))
        self.assertTrue(self.e.kind(self.f['actors']['human'],'Principal Actor'))
        self.assertTrue(self.e.kind(self.f['actors']['agent'],'Agent Actor'))
        self.assertFalse(self.e.kind(self.f['actors']['human'],'Agent Actor'))
        definition=self.f['definitions'][0]['body']
        self.assertEqual(definition['companyName'],'ACME Timeline Services Sp. z o.o.')
        for actor in self.f['actors'].values():self.assertNotIn('provider',actor)

    def test_no_artificial_ids_or_protocol_version_in_wire_examples(self):
        forbidden={'protocolVersion','providerId','timelineId','accessId','grantId','streamId','partyId','requestId'}
        def visit(value):
            if isinstance(value,dict):
                self.assertFalse(forbidden.intersection(value))
                for child in value.values():visit(child)
            elif isinstance(value,list):
                for child in value:visit(child)
        visit(self.f)

    def test_access_is_a_contracts_document_with_one_provider_declaration(self):
        access=self.f['timelineAccess']
        self.assertEqual(set(access),{'type','allowedTimelines','allowedKeys','contracts'})
        self.assertEqual(set(access['contracts']),{'provider','update'})
        self.assertTrue(self.e.kind(access['contracts']['provider'],'Public Timeline Channel'))
        self.assertTrue(self.e.kind(access['contracts']['update'],'Update Timeline Access'))
        self.assertEqual(self.e.identity(control_timeline(self.e,access)),self.f['expected']['controlTimeline'])
        self.assertTrue(all(set(t)=={'blueId'} for t in access['allowedTimelines']))

    def test_two_plain_text_entries_have_linked_unique_times(self):
        a,b=self.f['entries']
        self.assertEqual((a['message'],b['message']),('Hello','Hello 2'))
        self.assertNotIn('prevEntry',a);self.assertEqual(b['prevEntry'],ref(self.e.identity(a)))
        self.assertLess(a['timestamp'],b['timestamp'])

    def test_public_request_is_keyless_and_uses_resolved_read_url(self):
        c=self.f['cases']['publicControl']
        self.assertEqual(set(c['request']),{'type','timeline','limit'})
        self.assertEqual(c['url'],api_urls(self.e,self.f['timelineAccess']['contracts']['provider'])['read'])
        page,ids=self.v.page(c['request'],c['response'])
        self.assertEqual(len(ids),2)
        self.assertFalse(page['hasMore'])
        self.assertEqual(self.v.range(c['response']['object']['checkpoint'],page['entries']).complete_before,self.f['expected']['completeBefore'])

    def test_private_signatures_and_blue_request_references(self):
        for name in ('privateBoth','privateAfterFirst','firstPage','nextPage'):
            c=self.f['cases'][name];signed=c['request'];q=signed['request']
            verify_sig(signed['publicKey'],signed['signature'],('blue.coordination.reader-request\n'+self.e.identity(q)).encode())
            page,ids=self.v.page(q,c['response'])
            self.assertEqual(ids,c['entries'])
            self.assertEqual(self.e.identity(c['response']['object']['request']),self.e.identity(q))
            self.assertNotIn('requestBlueId',c['response']['object'])

    def test_after_first_returns_only_second_and_cursor_keeps_checkpoint(self):
        c=self.f['cases']['privateAfterFirst'];page,ids=self.v.page(c['request']['request'],c['response'])
        self.assertEqual(ids,[self.f['expected']['secondEntry']])
        self.assertEqual(self.e.identity(page['predecessor']),self.f['expected']['firstEntry'])
        a,b=(self.f['cases'][n]['response']['object']['checkpoint'] for n in ('firstPage','nextPage'))
        self.assertEqual(self.e.identity(a),self.e.identity(b))

    def test_access_discovery_contains_real_executed_state(self):
        c=self.f['cases']['accessDiscovery'];body=self.v.attestation(c['response'])
        self.assertEqual(self.e.identity(body['access']),self.f['expected']['access'])
        self.assertEqual(self.e.identity(body['current']),self.f['expected']['afterUpdate'])
        self.assertEqual(self.e.identity(self.v.attestation(body['publication'])['message']),self.f['expected']['access'])

    def test_same_microsecond_gets_distinct_positions(self):
        p=ModelProvider(self.e);t=p.create('alice','same-microsecond',True)
        a=p.append('alice',t,'Hello','a',100);b=p.append('alice',t,'Hello 2','b',100)
        self.assertEqual((a['timestamp'],b['timestamp']),(100,101))

    def test_false_has_more_permanently_closes_even_empty_range(self):
        for populated in (False,True):
            p=ModelProvider(self.e);t=p.create('alice','closed-'+str(populated),True)
            if populated:p.append('alice',t,'old','old',100)
            q=p.request('Read Timeline Request',timeline=t,limit=100)
            response=p.public_read(q,150);page,_=p.verifier.page(q,response)
            self.assertFalse(page['hasMore'])
            self.assertEqual(p.append('alice',t,'late','late',101)['timestamp'],150)

    def test_domain_fields_still_enforced(self):
        human=copy.deepcopy(self.f['actors']['human']);del human['citizenNumber']
        with self.assertRaises(Exception):self.e.put(human)

    def test_provider_defaults_are_inherited_and_public_private_share_one_url(self):
        self.assertNotIn('endpoint', self.f['provider'])
        self.assertEqual(self.e.text_field(self.f['provider'], 'endpoint'), 'https://timeline.acme.example')
        shared = self.f['cases']['privateBoth']['url']
        self.assertEqual(shared, 'https://timeline.acme.example/timelines/read')
        self.assertEqual(self.f['cases']['publicControl']['url'], shared)



    def test_url_constraints(self):
        self.assertEqual(validate_endpoint('https://acme.example/api'),'https://acme.example/api')
        for url in ('http://acme.example','https://user:pass@acme.example','https://acme.example/../api','https://acme.example/#x'):
            with self.assertRaises(ValueError):validate_endpoint(url)

class NativeAccessTests(ExampleTests):
    # Native execution cases reuse one independently imported public fixture.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.f['cases']['publicControl']['response']['object']
        cls.execution=AccessExecution(cls.e,cls.f['timelineAccess'],cls.f['discovery']['response'],c['checkpoint'],c['page']['entries'])
        cls.final=cls.execution.replay()
        cls.initial=cls.execution.p.create(cls.f['timelineAccess'])
        cls.initial_id=cls.initial.documents[cls.initial.root].blue_id
        cls.signer=ModelProvider(cls.e,endpoint=None,provider_type='Example/ACME Timeline Provider')

    def test_native_update_replaces_both_lists(self):
        self.assertEqual(self.e.identity(self.final),self.f['expected']['afterUpdate'])
        self.assertEqual(self.execution.outcomes[-1].status,'APPLIED')
        self.assertEqual(len(self.execution.p.read(self.execution.state,'/allowedTimelines')),2)
        self.assertEqual(self.execution.p.read(self.execution.state,'/allowedKeys'),self.f['expected']['keys'])

    def rejected(self, arguments, target=None):
        run=copy.copy(self.execution);run.state=self.initial;run.outcomes=[]
        publication=self.e.get(self.f['cases']['publicControl']['response']['object']['page']['entries'][0])
        call={'type':'Contracts/Operation Request','document':ref(target or self.initial_id),
            'channel':'provider','operation':'update','request':arguments}
        entry=self.e.typed('Timeline Entry',timeline=ref(self.f['expected']['controlTimeline']),timestamp=1791288002500000,
            actor=self.f['actors']['agent'],message=call,operation=call,prevEntry=ref(self.e.identity(publication)))
        guarantee=self.e.typed('Timeline Completeness Guarantee',timeline=ref(self.f['expected']['controlTimeline']),
            completeBefore=1791288003000000,lastEntry=ref(self.e.identity(entry)))
        run.checkpoint=self.e.typed('Timeline Attestation',timeline=ref(self.f['expected']['controlTimeline']),guarantee=guarantee,
            signature=self.signer.secret.sign(('blue.coordination.guarantee\n'+self.e.identity(guarantee)).encode()).hex())
        run.entries=[publication,entry]
        with self.assertRaisesRegex(ValueError,'ACCESS_EXECUTION_FAILED'):run.apply(entry)
        self.assertEqual(run.current_id(),self.initial_id)
        self.assertEqual(run.p.read(run.state,'/allowedKeys'),self.f['timelineAccess']['allowedKeys'])
        return run.outcomes[-1]

    def test_native_duplicate_values_roll_back(self):
        args=copy.deepcopy(self.f['updateOperation']['request']);args['allowedKeys']*=2
        result=self.rejected(args)
        self.assertEqual(result.diagnostic['code'],'BEX_EXECUTION_REJECTED')

    def test_native_foreign_provider_timeline_rolls_back(self):
        other=ModelProvider(self.e,seed=b'\x44'*32,endpoint='https://other.example')
        args=copy.deepcopy(self.f['updateOperation']['request']);args['allowedTimelines']=[other.create('alice','foreign')]
        result=self.rejected(args)
        self.assertEqual(result.diagnostic['code'],'BEX_EXECUTION_REJECTED')

    def test_native_update_targets_original_document_without_version_precondition(self):
        self.assertEqual(self.e.identity(self.f['updateOperation']['document']), self.f['expected']['access'])
        self.assertNotIn('requireExactDocumentVersion', self.f['updateOperation'])
        self.assertEqual(self.execution.outcomes[-1].status, 'APPLIED')

    def test_native_missing_evidence_does_not_execute(self):
        event=self.e.get(self.f['cases']['publicControl']['response']['object']['page']['entries'][1])
        result=self.execution.p.process(self.initial,event,event['timestamp'])
        self.assertNotEqual(result.status,'APPLIED')
        self.assertEqual(result.snapshot.identity,self.initial.identity)

# Avoid running the fast inherited examples twice.
for name in list(ExampleTests.__dict__):
    if name.startswith('test_') and name not in NativeAccessTests.__dict__:
        setattr(NativeAccessTests,name,None)

if __name__=='__main__':unittest.main()
