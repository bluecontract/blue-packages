import unittest
from algorithms import blue as L
from blue_language import Language
from demand_reference import Obligations


class RoleTests(unittest.TestCase):
    def test_required_object_presence_does_not_count_unconsumed_private_fields(self):
        context = Language(core_contracts=False).processing_context()
        import json
        from pathlib import Path
        vector = json.loads(Path(__file__).with_name('presence-vector.json').read_text())
        private_id = vector['privateBlueId']
        root = L.normalize(vector['root'], context)
        obligations = Obligations(context)
        self.assertEqual(obligations.require(L.recipe(root), 'container').kind, 'object')
        self.assertEqual(obligations.charges['schemaPredicateEvaluated'], 1)
        broader = L.normalize({'schema': {'required': True, 'minFields': 1},
                               'payload': {'blueId': private_id}}, context)
        with self.assertRaises(L.Failure) as missing:
            Obligations(context).require(L.recipe(broader), 'container')
        self.assertEqual(missing.exception.category, 'ProviderUnavailable')

    def test_container_does_not_require_unused_value_but_value_does(self):
        private = L.scalar('Integer', 42)
        root = L.node({'unused': L.Ref(L.identity(private))})
        obligations = Obligations(Language(core_contracts=False).processing_context())
        recipe = L.recipe(root)
        self.assertEqual(obligations.require(recipe, 'container').kind, 'object')
        with self.assertRaises(L.Failure) as missing:
            obligations.require(recipe, 'value')
        self.assertEqual(missing.exception.category, 'ProviderUnavailable')
        self.assertFalse(any(key[1] == 'value' for key in obligations.success))

    def test_contextual_constraints_are_not_identity_exemptions(self):
        value = L.scalar('Integer', 2)
        constrained = L.node({'type': L.Ref(L.CORE['Integer']), 'schema': L.node({'minimum': L.scalar('Integer', 3)})})
        context = Language(core_contracts=False).processing_context()
        context.remember(constrained)
        obligations = Obligations(context)
        obligations.require(L.recipe(value), 'value')
        with self.assertRaises(L.Failure) as failure:
            obligations.require(L.recipe(value, requirements=(L.identity(constrained),)), 'value')
        self.assertEqual(failure.exception.category, 'SchemaViolation')
        self.assertEqual(sum(key[1] == 'value' for key in obligations.success), 1)

    def test_unknown_role_fails_without_success_fact(self):
        obligations = Obligations(Language(core_contracts=False).processing_context())
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_OBLIGATION'):
            obligations.require(L.recipe(L.node({})), 'custom')
        self.assertEqual(obligations.success, {})

    def test_invocation_ledger_does_not_reuse_global_native_cache(self):
        recipe = L.recipe(L.scalar('Integer', 2))
        context = Language(core_contracts=False).processing_context()
        first = Obligations(context)
        first.require(recipe, 'value')
        first.require(recipe, 'value')
        self.assertEqual(first.charges['validationProofReused'], 1)
        second = Obligations(context)
        second.require(recipe, 'value')
        self.assertEqual(second.charges['validationProofReused'], 0)

class RecordTests(unittest.TestCase):
    def test_prepare_does_not_export_unused_body_and_cold_opens_root(self):
        from demand_reference import prepare_records
        private = L.scalar('Integer', 42)
        root = L.node({'unused': private})
        records = prepare_records([(root, 'structural', 'restore', ())], L.Context())
        self.assertEqual(set(records), {L.identity(root)})
        cold = L.Context(provider=records)
        self.assertEqual(L.identity(L.open_exact(L.Ref(L.identity(root)), cold)), L.identity(root))
        with self.assertRaises(L.Failure):
            L.open_exact(L.Ref(L.identity(private)), cold)

    def test_latest_shared_publication_survives_failed_candidate(self):
        from demand_reference import Publication, prepare_records
        shared = Publication()
        a = L.node({'a': L.node({})})
        b = L.node({'b': L.node({})})
        a_records = prepare_records([(a, 'structural', 'restore', ())], L.Context())
        b_records = prepare_records([(b, 'structural', 'restore', ())], L.Context())
        shared.commit('B', b_records, ('B-result',))
        corrupted = {L.identity(a): {'mode': 'exact', 'text': '{}'}}
        with self.assertRaises(L.Failure):
            shared.commit('A', corrupted, ('A-result',))
        self.assertEqual(set(shared.archive), {'B'})
        self.assertEqual(shared.records, b_records)
        shared.commit('A', a_records, ('A-result',))
        self.assertEqual(set(shared.archive), {'A', 'B'})
        self.assertEqual(set(shared.records), set(a_records) | set(b_records))

    def test_real_native_cycle_retains_owning_proof_and_rejects_tampering(self):
        from demand_reference import prepare_records
        context = L.Context()
        component = L.finalize_set([{'next': {'blueId': 'this#0'}}], context)
        identity = component['ids'][0]
        proof = {'members': [L.export_tree(node) for node in component['canonical']]}
        original = L.verify_member(identity, proof, None, context)
        records = prepare_records([(original, 'structural', 'restore', ())], context)
        reopened = L.open_exact(L.Ref(identity), L.Context(provider=records))
        self.assertEqual(reopened.get('next').id, identity)
        self.assertEqual(set(records[identity]), {'proof', 'body'})
        bad = {identity: {**records[identity], 'body': '{}'}}
        with self.assertRaises(L.Failure) as failure:
            L.open_exact(L.Ref(identity), L.Context(provider=bad))
        self.assertEqual(failure.exception.category, 'InvalidCyclicProof')

class SharedVectorTests(unittest.TestCase):
    def test_shared_inputs_and_exact_results(self):
        import json
        from pathlib import Path
        from demand_reference import execute_vector
        vectors = json.loads((Path(__file__).with_name('vectors.json')).read_text())['vectors']
        results = [execute_vector(vector) for vector in vectors]
        for vector, result in zip(vectors, results):
            self.assertEqual(result['outcome'], vector['expected'], vector['id'])
        missing, full = results[:2]
        self.assertEqual({k: v for k, v in missing.items() if k != 'id'},
                         {k: v for k, v in full.items() if k != 'id'})

class PublicationEncodingTests(unittest.TestCase):
    def test_same_identity_equivalent_encoding_uses_native_verification(self):
        from demand_reference import Publication, prepare_records
        root = L.node({'a': L.node({})})
        identity = L.identity(root)
        shallow = prepare_records([(root, 'structural', 'restore', ())], L.Context())
        inline = {identity: {'mode': 'exact', 'text': L.wire_text(L.export_tree(root))}}
        shared = Publication()
        shared.commit('first', shallow, ('first',))
        shared.commit('second', inline, ('second',))
        self.assertEqual(set(shared.archive), {'first', 'second'})

class CyclicPrivacyTests(unittest.TestCase):
    def test_inline_private_owning_proof_is_externalized_without_changing_id(self):
        from demand_reference import prepare_records
        context = L.Context()
        import json
        from pathlib import Path
        raw = json.loads(Path(__file__).with_name('cyclic-vector.json').read_text())['members']
        component = L.finalize_set(raw, context)
        identity = component['ids'][0]
        proof = {'members': [L.export_tree(node) for node in component['canonical']]}
        original = L.verify_member(identity, proof, None, context)
        records = prepare_records([(original, 'structural', 'restore', ())], context)
        import json
        exported = json.loads(records[identity]['proof'])
        self.assertEqual(set(exported['members'][0]['private']), {'blueId'})
        cold = L.Context(provider=records)
        reopened = L.open_exact(L.Ref(identity), cold)
        self.assertEqual(reopened.get('next').id, identity)
        with self.assertRaises(L.Failure) as missing:
            L.open_exact(reopened.get('private'), cold)
        self.assertEqual(missing.exception.category, 'ProviderUnavailable')

class DeclarationTests(unittest.TestCase):
    def test_native_compute_shared_body_selection(self):
        import json
        from pathlib import Path
        from demand_reference import declaration_edges
        vector = json.loads(Path(__file__).with_name('body-vector.json').read_text())
        discovered = dict(declaration_edges(vector['kind'], vector['fields']))
        consumed = dict(declaration_edges(vector['kind'], vector['fields'], (vector['selectedBody'],)))
        self.assertNotIn(vector['selectedBody'], discovered)
        self.assertEqual(consumed[vector['selectedBody']], 'value')
        policy = ((), vector['installedBindingBody'])
        fields = (vector['selectedBody'],)
        self.assertEqual(declaration_edges('dispatch-policy', fields, extension_policy=policy), ())
        self.assertEqual(declaration_edges('dispatch-policy', fields, extension_policy=policy,
                                          extension_selected=True), ((vector['selectedBody'], 'value'),))

    def test_discovery_keeps_step_shape_but_defers_body_until_consumer(self):
        from demand_reference import declaration_edges
        fields = ('steps', 'type', 'channel', 'specification')
        self.assertEqual(declaration_edges('workflow', fields),
                         (('channel', 'header'), ('specification', 'definition'),
                          ('steps', 'list-shape'), ('type', 'definition')))
        self.assertEqual(declaration_edges('compute', ('type', 'expr')),
                         (('type', 'definition'),))
        self.assertEqual(declaration_edges('compute', ('type', 'expr'), ('expr',)),
                         (('expr', 'value'), ('type', 'definition')))
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_HANDLER_ROLE'):
            declaration_edges('unknown-extension', ('private',))

class CompositionConditionTests(unittest.TestCase):
    def test_cold_envelope_uses_only_supplied_records_and_exact_commitment(self):
        from demand_reference import prepare_records, check_snapshot_envelope
        from blue_contracts.reference.model import digest, ContractError
        root = L.node({'unused': L.Ref(L.identity(L.scalar('Integer', 42)))})
        wire = {'root': 'root', 'documents': [{'key': 'root', 'blueId': L.identity(root),
                 'channels': {}, 'channelSerials': {}, 'edgeSerials': {}, 'birth': None}],
                'edges': [], 'generation': 0, 'revision': 0, 'release': 'selected', 'runtimes': []}
        identity = digest('contracts.snapshot/completion-1', wire)
        package = {'snapshot': wire, 'identity': identity,
                   'content': prepare_records([(root, 'structural', 'restore', ())], L.Context())}
        self.assertEqual(check_snapshot_envelope(package, identity, 'selected', [])['qualification'], 'ENVELOPE_ONLY')
        with self.assertRaises(ContractError):
            check_snapshot_envelope(package, identity, 'other-edition', [])
        with self.assertRaises(L.Failure):
            check_snapshot_envelope({**package, 'content': {}}, identity, 'selected', [])
        with self.assertRaises(ContractError):
            check_snapshot_envelope(package, 'untrusted', 'selected', [])

    def test_result_cause_and_failed_state_are_checked_without_issuing_capability(self):
        from demand_reference import check_result_observations
        from blue_contracts.reference.model import digest, ContractError
        gas = {'shared': 10000000, 'local': {}, 'profile': 'fixture'}
        observations = {'status': 'NEEDS_RESOURCES', 'input': 'before', 'output': 'before', 'gas': 3,
            'invocation': digest('contracts.invocation/completion-1',
                {'input': 'before', 'event': 'event', 'timestamp': 1, 'gas': gas, 'release': 'selected'})}
        receipt = digest('contracts.result/completion-1', observations)
        self.assertEqual(check_result_observations(observations, receipt, 'before', 'before', 'event', 1, gas, 'selected')['qualification'], 'OBSERVATIONS_ONLY')
        with self.assertRaises(ContractError):
            check_result_observations(observations, receipt, 'before', 'before', 'foreign-event', 1, gas, 'selected')
        changed = {**observations, 'output': 'after'}
        with self.assertRaises(ContractError):
            check_result_observations(changed, digest('contracts.result/completion-1', changed), 'before', 'after', 'event', 1, gas, 'selected')
