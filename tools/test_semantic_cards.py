"""Semantic discovery and incremental delivery; no model calls or AWS access."""
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

import boto3
import yaml
from botocore.exceptions import ClientError
from botocore.response import StreamingBody
from botocore.stub import Stubber
from jsonschema import ValidationError

from release import ROOT, digest, wire
import semantic_cards as cards
import semantic_ci as ci
import semantic_sources as sources
from semantic_s3 import Store, card_key

A, B, C, D, E, F = (letter * 44 for letter in 'ABCDEF')
PACKAGE = dict(name='fixture', version='1.0', blueId='P' * 44, archiveSha256=digest(b'archive'))
DEFINITIONS = {
    A: {'name': 'Clause', 'bindingTypes': {'state': {}}, 'defaultBindings': {'state': '/state'}},
    B: {'name': 'New type', 'type': {'blueId': A}, 'parameters': {'amount': 1}, 'counter': 0,
        'actions': {'change': {'$appendChange': {'op': 'add', 'path': '/result',
                                               'val': {'$object': {'items': []}}}}}},
    C: {'type': {'blueId': B}, 'bindingTypes': {'state': {}}},
    D: {'name': 'Misleading Clause name'},
    E: {'clauses': {}, 'childTemplate': {'type': {'blueId': F}}},
    F: {'name': 'Child document'},
}


def subject(blue_id):
    return dict(blueId=blue_id, alias='Fixture/' + blue_id[:1], package=deepcopy(PACKAGE), roles=['clause'])


def response(blue_id):
    return dict(blueId=blue_id, semanticText='# Fixture\n\nAn exact reusable type description.')


def request(blue_id):
    context = sources.evidence(blue_id, DEFINITIONS)
    generator = json.loads((cards.ASSETS / 'generator.json').read_text())
    generator['promptSha256'] = digest((cards.ASSETS / 'prompt.md').read_bytes())
    return dict(context=context, definitionDigest=sources.definition_digest(blue_id, DEFINITIONS),
                sourceDigest=digest(wire(context)), package=deepcopy(PACKAGE), generator=generator)


class InfrastructureTests(unittest.TestCase):
    def test_stack_returns_every_aws_variable_consumed_by_workflows(self):
        template = yaml.safe_load((ROOT / 'semantics/template.yaml').read_text())
        output = template['Outputs']['GitHubVariables']['Value']['Fn::Sub']
        variables = dict(line.split('=', 1) for line in output.splitlines())
        workflows = '\n'.join(path.read_text() for path in (ROOT / '.github/workflows').glob('semantic-cards-*.yml'))
        required = set(re.findall(r'vars\.(SEMANTICS_[A-Z_]+)', workflows))
        required -= {'SEMANTICS_GENERATION_ENABLED', 'SEMANTICS_PUBLICATION_ENABLED'}
        self.assertEqual(required, set(variables))
        self.assertEqual('${SemanticCardsReadRole.Arn}', variables['SEMANTICS_READ_ROLE_ARN'])
        self.assertEqual('${SemanticCardsPublishRole.Arn}', variables['SEMANTICS_PUBLISH_ROLE_ARN'])

    def test_roles_restrict_callers_and_s3_permissions(self):
        resources = yaml.safe_load((ROOT / 'semantics/template.yaml').read_text())['Resources']
        prefix = 'repo:bluecontract@93829250/blue-packages@1391542341'
        for name, context, actions in (
            ('SemanticCardsReadRole', ':ref:refs/heads/main', {'s3:ListBucket', 's3:GetObject'}),
            ('SemanticCardsPublishRole', ':environment:semantics-publish', {'s3:ListBucket', 's3:GetObject', 's3:PutObject'}),
        ):
            role = resources[name]['Properties']
            trust, = role['AssumeRolePolicyDocument']['Statement']
            self.assertEqual('Allow', trust['Effect'])
            self.assertEqual('sts:AssumeRoleWithWebIdentity', trust['Action'])
            self.assertEqual({'StringEquals': {
                'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com',
                'token.actions.githubusercontent.com:sub': prefix + context,
            }}, trust['Condition'])
            granted = set()
            for policy in role['Policies']:
                for statement in policy['PolicyDocument']['Statement']:
                    self.assertEqual('Allow', statement['Effect'])
                    listed = statement['Action']
                    for action in listed if isinstance(listed, list) else [listed]:
                        granted.add(action)
                        expected = ({'Fn::GetAtt': ['SemanticCardsBucket', 'Arn']} if action == 's3:ListBucket'
                                    else {'Fn::Sub': '${SemanticCardsBucket.Arn}/*.json'})
                        self.assertEqual(expected, statement['Resource'])
            self.assertEqual(actions, granted)


class SourceTests(unittest.TestCase):
    def test_discovers_new_inherited_clause_host_and_template_without_name_catalogue(self):
        exports = {key: subject(key) for key in DEFINITIONS}
        found = sources.discover(exports, DEFINITIONS, A)
        self.assertEqual({A, B, C, E, F}, set(found))
        self.assertEqual(['clause'], found[C]['roles'])
        self.assertEqual(['host'], found[E]['roles'])
        self.assertEqual(['helper'], found[F]['roles'])
        with self.assertRaisesRegex(ValueError, 'cycle'):
            sources.discover(exports, {A: {'type': {'blueId': B}}, B: {'type': {'blueId': A}}}, A)

    def test_evidence_includes_inheritance_bindings_and_literal_written_fields(self):
        context = sources.evidence(C, DEFINITIONS)
        self.assertEqual([dict(name='state', defaultPath='/state')], context['bindings'])
        self.assertEqual(['bindings.state', 'parameters.amount'], context['parameterRefs'])
        self.assertTrue({'/counter', '/result', '/result/items'} <= set(context['documentPaths']))
        self.assertEqual({A, B}, set(context['referencedBlueIds']))
        missing = 'G' * 44
        context = sources.evidence(B, {**DEFINITIONS, B: {'type': {'blueId': missing}}})
        self.assertEqual([missing], context['omittedDependencies'])
        context = sources.evidence(B, {**DEFINITIONS, B: {'defaultBindings': {'inline': {}}}})
        self.assertEqual([dict(name='inline', defaultPath=None)], context['bindings'])


    def test_added_export_without_rebuild_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist = root / 'fixture/dist'
            dist.mkdir(parents=True)
            exports = [dict(name='Clause', alias='Clauses/Clause', blueId=A)]
            payloads = {'package-records.json': wire({A: {'mode': 'exact', 'text': json.dumps(DEFINITIONS[A])}})}
            manifest = dict(packageBlueId=PACKAGE['blueId'], version='1.0', exports=exports,
                            imports={}, semanticPackages={}, protocol=None,
                            files={name: dict(sha256=digest(data), size=len(data)) for name, data in payloads.items()})
            payloads['package.json'] = wire(manifest)
            with zipfile.ZipFile(dist / 'package.bluepkg', 'w') as archive:
                for name, data in payloads.items():
                    archive.writestr(name, data)
                    (dist / name).write_bytes(data)
            (root / 'fixture/blue-package.lock.json').write_text('{"imports": {}}')
            config = root / 'fixture/blue-package.yaml'
            config.write_bytes(wire({'exports': [{'name': 'Clause'}]}))
            row = dict(name='fixture', directory='fixture', path='fixture/dist/package.bluepkg',
                       packageBlueId=PACKAGE['blueId'], archiveSha256=digest((dist / 'package.bluepkg').read_bytes()))
            with patch.object(sources, 'selections', return_value=[row]):
                self.assertEqual({A}, set(sources.inventory(root)[0]))
                config.write_bytes(wire({'exports': [{'name': 'Clause'}, {'name': 'NewClause'}]}))
                with self.assertRaisesRegex(ValueError, 'Unbuilt exports'):
                    sources.inventory(root)

    def test_current_collection_covers_public_clause_catalogue(self):
        subjects, definitions = sources.inventory(ROOT)
        catalogue = json.loads((ROOT / 'PUBLIC-CLAUSES.json').read_text())
        public_aliases = {alias for family in catalogue['families'] for alias in family['types']}
        self.assertTrue(public_aliases)
        self.assertTrue(public_aliases <= {item['alias'] for item in subjects.values()})
        self.assertTrue(any('host' in item['roles'] for item in subjects.values()))
        for blue_id in subjects:
            context = sources.evidence(blue_id, definitions)
            self.assertEqual(blue_id, context['blueId'])


class CardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.destination = self.root / 'semantics/cards'
        self.output = self.root / 'build/semantics'
        self.subjects = {B: subject(B), C: subject(C)}
        self.inventory = patch.object(cards, 'inventory', return_value=(self.subjects, DEFINITIONS)).start()
        self.addCleanup(patch.stopall)

    def card(self, blue_id=B):
        return cards.accept(request(blue_id), response(blue_id), self.destination)

    def test_local_card_not_uploaded_is_reused_even_after_package_version_changes(self):
        card = self.card()
        self.subjects[B]['package']['version'] = '2.0'
        store = Mock()
        store.keys.return_value = set()
        store.restore.return_value = None
        plan = cards.prepare(self.root, self.output, store)
        self.assertEqual([B], plan['ready'])
        self.assertEqual([B], plan['unpublished'])
        self.assertEqual([C], plan['generate'])
        store.restore.assert_called_once_with(C, set())
        self.assertEqual(card, cards.read_json(self.destination / (B + '.json')))

    def test_s3_restore_avoids_model_and_ignores_stale_staging_files(self):
        remote = self.card()
        (self.destination / (B + '.json')).unlink()
        self.subjects.pop(C)
        store = Mock()
        store.keys.return_value = {card_key(B)}
        store.restore.return_value = remote
        cards.save_card(self.output / 'cards', cards.accept(request(C), response(C), self.root / 'old'))
        with patch.object(cards.subprocess, 'check_output') as model:
            plan = cards.generate(self.root, self.output, 2, store)
        model.assert_not_called()
        self.assertEqual([], plan['generate'])
        self.assertEqual([B], plan['restored'])
        self.assertEqual({B}, set(cards.cards_in(self.root)))

    def test_replanning_refreshes_s3_staging_after_an_approved_remote_correction(self):
        remote = self.card()
        (self.destination / (B + '.json')).unlink()
        self.subjects.pop(C)
        store = Mock()
        store.keys.return_value = {card_key(B)}
        store.restore.return_value = remote
        cards.prepare(self.root, self.output, store)
        corrected = deepcopy(remote)
        corrected['semanticText'] += '\n\nCorrected meaning.'
        store.restore.return_value = corrected
        plan = cards.prepare(self.root, self.output, store)
        self.assertEqual([B], plan['restored'])
        self.assertEqual(corrected, cards.read_json(self.output / 'cards' / (B + '.json')))

    def test_local_partial_generation_keeps_success_and_next_run_requests_only_failure(self):
        version = request(B)['generator']['codexVersion']

        def run(command, **kwargs):
            blue_id = json.loads(kwargs['input'].split('Evidence (JSON):\n')[1])['blueId']
            if blue_id == B:
                Path(command[-2]).write_bytes(wire(response(B)))
                return subprocess.CompletedProcess(command, 0)
            return subprocess.CompletedProcess(command, 1)

        with patch.object(cards.subprocess, 'check_output', return_value='codex-cli ' + version), \
             patch.object(cards.subprocess, 'run', side_effect=run):
            with self.assertRaisesRegex(ValueError, 'successful cards were retained'):
                cards.generate(self.root, self.output, 2)
        self.assertEqual({B}, set(cards.cards_in(self.root)))
        self.assertEqual([C], cards.prepare(self.root, self.output)['generate'])

    def test_accept_stores_only_identity_and_text_without_padding_or_fixed_sections(self):
        card = self.card()
        self.assertEqual(response(B), card)
        self.assertEqual(wire(response(B)), (self.destination / (B + '.json')).read_bytes())
        self.assertEqual(card, cards.validate_card(card, B))

    def test_validation_rejects_wrong_identity_and_symlinks(self):
        card = self.card()
        with self.assertRaisesRegex(ValueError, 'BlueId'):
            cards.validate_card(card, C)
        with self.assertRaisesRegex(ValueError, 'BlueId'):
            cards.accept(request(C), response(B), self.root / 'wrong-identity')
        (self.destination / (C + '.json')).symlink_to(self.destination / (B + '.json'))
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            cards.cards_in(self.root)

    def test_validation_rejects_extra_fields_invalid_text_and_size(self):
        for field in ('metadata', 'dependencies', 'omittedDependencies', 'sourceDigest',
                      'definitionDigest', 'semanticHash', 'package', 'generator', 'review',
                      'validation', 'language', 'format'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                cards.validate_card({**response(B), field: {}}, B)
        for changes in ({'blueId': '../invalid'}, {'semanticText': []}, {'semanticText': ''},
                        {'semanticText': '# Fixture\n\n' + 'x' * 20_000}):
            with self.subTest(changes=changes.keys()), self.assertRaises(ValidationError):
                cards.validate_card({**response(B), **changes}, B)
        for text, error in (('No heading\n\nMeaning.', 'heading'), ('# \n\nMeaning.', 'heading'),
                            ('# Fixture\n\n', 'explanation'), ('# Fixture\n\n' + '界' * 16_000, 'byte limit')):
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                cards.validate_card(dict(response(B), semanticText=text), B)

    def test_accept_checks_request_checksum_and_refuses_overwrite(self):
        invalid = request(B)
        invalid['context']['definition']['name'] = 'Changed source'
        with self.assertRaisesRegex(ValueError, 'checksum'):
            cards.accept(invalid, response(B), self.destination)
        self.assertFalse(self.destination.exists())
        self.card()
        corrected = dict(response(B), semanticText='# Fixture\n\nCorrected meaning.')
        with self.assertRaisesRegex(ValueError, 'Refusing to replace'):
            cards.accept(request(B), corrected, self.destination)
        self.assertEqual(response(B), cards.read_json(self.destination / (B + '.json')))

    def test_restore_rejects_legacy_envelope_before_generation(self):
        store = Mock()
        store.keys.return_value = {card_key(B)}
        store.restore.return_value = dict(response(B), metadata={})
        with patch.object(cards.subprocess, 'check_output') as model:
            with self.assertRaises(ValidationError):
                cards.generate(self.root, self.output, 2, store)
        model.assert_not_called()
        self.assertFalse(self.destination.exists())

    def test_collect_preserves_success_when_another_output_fails_schema(self):
        cards.prepare(self.root, self.output)
        responses = self.root / 'responses'
        responses.mkdir()
        (responses / (B + '.json')).write_bytes(wire(response(B)))
        (responses / (C + '.json')).write_text('{}')
        with patch.object(ci, 'inventory', return_value=(self.subjects, DEFINITIONS)):
            result = ci.collect(self.root, self.output, responses)
        self.assertEqual({'accepted': [B], 'failed': [C]}, result)
        self.assertEqual({B}, set(cards.cards_in(self.root)))

    def test_collect_rejects_changed_definition_or_dependency_evidence(self):
        self.subjects.pop(C)
        cards.prepare(self.root, self.output)
        responses = self.root / 'responses'
        responses.mkdir()
        (responses / (B + '.json')).write_bytes(wire(response(B)))
        for blue_id in (B, A):
            changed = deepcopy(DEFINITIONS)
            changed[blue_id]['name'] = 'Changed source'
            with self.subTest(blue_id=blue_id), \
                 patch.object(ci, 'inventory', return_value=(self.subjects, changed)):
                self.assertEqual({'accepted': [], 'failed': [B]}, ci.collect(self.root, self.output, responses))
                self.assertFalse(self.destination.exists())


class S3Tests(unittest.TestCase):
    def setUp(self):
        client = boto3.client('s3', region_name='eu-west-1', aws_access_key_id='test', aws_secret_access_key='test')
        self.stub = Stubber(client)
        self.stub.activate()
        self.addCleanup(self.stub.deactivate)
        self.store = Store('fixture-bucket', client)
        with tempfile.TemporaryDirectory() as tmp:
            self.card = cards.accept(request(B), response(B), Path(tmp))
        self.key = B + '.json'

    def get(self, key, value, etag='"etag"'):
        data = wire(value)
        self.stub.add_response('get_object', {'Body': StreamingBody(io.BytesIO(data), len(data)), 'ETag': etag},
                               {'Bucket': self.store.bucket, 'Key': key})

    def missing(self, key):
        self.stub.add_client_error('get_object', service_error_code='NoSuchKey', http_status_code=404,
                                  expected_params={'Bucket': self.store.bucket, 'Key': key})

    def put(self, key, value, condition, error=None):
        params = dict(Bucket=self.store.bucket, Key=key, Body=wire(value), ContentType='application/json',
                      CacheControl='no-cache', **condition)
        if error:
            self.stub.add_client_error('put_object', service_error_code=error, http_status_code=412, expected_params=params)
        else:
            self.stub.add_response('put_object', {}, params)

    def test_paginated_listing_and_access_denied_is_not_a_cache_miss(self):
        self.stub.add_response('list_objects_v2', {'IsTruncated': True, 'NextContinuationToken': 'next',
            'Contents': [{'Key': self.key}]}, {'Bucket': self.store.bucket})
        self.stub.add_response('list_objects_v2', {'IsTruncated': False, 'Contents': [{'Key': C + '.json'}]},
            {'Bucket': self.store.bucket, 'ContinuationToken': 'next'})
        self.assertEqual({self.key, C + '.json'}, self.store.keys())
        self.stub.add_client_error('get_object', service_error_code='AccessDenied', http_status_code=403,
            expected_params={'Bucket': self.store.bucket, 'Key': self.key})
        with self.assertRaises(ClientError):
            self.store.restore(B, {self.key})
        self.stub.assert_no_pending_responses()

    def test_restore_fetches_only_the_exact_card_and_rejects_invalid_data(self):
        self.assertIsNone(self.store.restore(B, {C + '.json'}))
        self.get(self.key, self.card)
        self.assertEqual(self.card, self.store.restore(B, {self.key}))
        self.missing(self.key)
        self.assertIsNone(self.store.restore(B, {self.key}))
        self.get(self.key, None)
        with self.assertRaisesRegex(ValueError, 'Invalid semantic object'):
            self.store.restore(B, {self.key})
        self.stub.assert_no_pending_responses()

    def test_publish_uploads_missing_card_and_skips_identical_existing_card(self):
        self.put(self.key, self.card, {'IfNoneMatch': '*'})
        self.assertEqual(dict(uploaded=True, correctionPending=False), self.store.publish(B, self.card, set()))
        self.get(self.key, self.card)
        self.assertEqual(dict(uploaded=False, correctionPending=False), self.store.publish(B, self.card, {self.key}))
        self.missing(self.key)
        self.put(self.key, self.card, {'IfNoneMatch': '*'})
        self.assertTrue(self.store.publish(B, self.card, {self.key})['uploaded'])
        self.stub.assert_no_pending_responses()

    def test_upload_race_accepts_identical_card_and_rejects_conflicting_card(self):
        self.put(self.key, self.card, {'IfNoneMatch': '*'}, error='PreconditionFailed')
        self.get(self.key, self.card)
        self.assertFalse(self.store.publish(B, self.card, set())['uploaded'])
        self.put(self.key, self.card, {'IfNoneMatch': '*'}, error='PreconditionFailed')
        self.get(self.key, dict(self.card, semanticText='# Concurrent card'))
        with self.assertRaisesRegex(ValueError, 'Conflicting semantic card'):
            self.store.publish(B, self.card, set())
        self.stub.assert_no_pending_responses()

    def test_text_correction_requires_promotion_and_uses_conditional_write(self):
        corrected = deepcopy(self.card)
        corrected['semanticText'] += '\n\nCorrected meaning.'
        self.get(self.key, self.card)
        self.assertTrue(self.store.publish(B, corrected, {self.key})['correctionPending'])
        self.get(self.key, self.card)
        self.put(self.key, corrected, {'IfMatch': '"etag"'})
        self.assertTrue(self.store.publish(B, corrected, {self.key}, promote=True)['uploaded'])
        self.get(self.key, corrected)
        self.assertTrue(self.store.publish(B, self.card, {self.key})['correctionPending'])
        self.get(self.key, self.card)
        self.put(self.key, corrected, {'IfMatch': '"etag"'}, error='PreconditionFailed')
        self.get(self.key, dict(self.card, semanticText='# Concurrent correction'))
        with self.assertRaisesRegex(ValueError, 'Conflicting semantic card'):
            self.store.publish(B, corrected, {self.key}, promote=True)
        self.stub.assert_no_pending_responses()


class CITests(unittest.TestCase):
    def event(self, repository='owner/repo', branch='feature'):
        return {'workflow_run': dict(conclusion='success', head_repository={'full_name': repository},
                                     head_sha='a' * 40, head_branch=branch)}

    def test_stale_fork_closed_and_duplicate_main_requests_do_not_generate(self):
        with patch.object(ci, 'api') as api:
            self.assertIsNone(ci.target(self.event('fork/repo'), 'owner/repo', 'main'))
            api.assert_not_called()
        with patch.object(ci, 'api', return_value={'object': {'sha': 'b' * 40}}):
            self.assertIsNone(ci.target(self.event(), 'owner/repo', 'main'))
        with patch.object(ci, 'api', side_effect=[{'object': {'sha': 'a' * 40}}, []]):
            self.assertIsNone(ci.target(self.event(), 'owner/repo', 'main'))
        with patch.object(ci, 'api', side_effect=[{'object': {'sha': 'a' * 40}}, [{'number': 1}]]):
            self.assertIsNone(ci.target(self.event(branch='main'), 'owner/repo', 'main'))
        pr = dict(number=42, head={'sha': 'a' * 40, 'repo': {'full_name': 'owner/repo'}})
        with patch.object(ci, 'api', side_effect=[{'object': {'sha': 'a' * 40}}, [pr]]):
            self.assertEqual(42, ci.target(self.event(), 'owner/repo', 'main')['pullRequest'])

    def test_commit_rechecks_source_before_any_git_write(self):
        selected = dict(repository='owner/repo', branch='feature', sha='a' * 40, pullRequest=42)
        with patch.object(ci, 'api', return_value={'object': {'sha': 'b' * 40}}), \
             patch.object(ci.subprocess, 'check_output') as git:
            ci.commit(Path('/unused'), selected)
        git.assert_not_called()

    def test_one_bot_commit_contains_only_cards_and_dispatches_new_head_checks(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'GIT_CONFIG_GLOBAL': os.devnull}):
            root = Path(tmp) / 'candidate'
            root.mkdir()
            remote = Path(tmp) / 'remote.git'

            def git(*args):
                return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', *args],
                                               cwd=root, text=True, stderr=subprocess.DEVNULL).strip()

            git('init', '--initial-branch=feature')
            git('init', '--bare', str(remote))
            git('config', 'user.name', 'Fixture')
            git('config', 'user.email', 'fixture@example.invalid')
            (root / 'README.md').write_text('Original\n')
            git('add', 'README.md')
            git('commit', '-m', 'Initial source')
            git('remote', 'add', 'origin', str(remote))
            git('push', 'origin', 'feature')
            expected = git('rev-parse', 'HEAD')
            selected = dict(repository='owner/repo', branch='feature', sha=expected, pullRequest=42, defaultBranch='main')
            cards.accept(request(B), response(B), root / 'semantics/cards')
            (root / 'README.md').write_text('Unrelated local change\n')
            pr = dict(state='open', head={'sha': expected, 'repo': {'full_name': 'owner/repo'}})
            with patch.object(ci, 'api', side_effect=[{'object': {'sha': expected}}, pr]), patch.object(ci, 'gh') as gh:
                ci.commit(root, selected)
            current = git('rev-parse', 'HEAD')
            self.assertNotEqual(expected, current)
            self.assertEqual('semantics/cards/' + B + '.json', git('diff', '--name-only', expected, current))
            self.assertEqual('Original', git('show', 'HEAD:README.md'))
            self.assertEqual(current, git('rev-parse', 'origin/feature'))
            self.assertEqual(['semantic-cards-check.yml', 'packages-release.yml'], [call.args[2] for call in gh.call_args_list])
            selected['sha'] = current
            pr['head']['sha'] = current
            with patch.object(ci, 'api', side_effect=[{'object': {'sha': current}}, pr]), patch.object(ci, 'gh') as gh:
                ci.commit(root, selected)
            gh.assert_not_called()
            self.assertEqual(current, git('rev-parse', 'HEAD'))


if __name__ == '__main__':
    unittest.main()
