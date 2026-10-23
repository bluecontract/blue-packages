import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import semantic_infrastructure as infra


class InfrastructureCliTests(unittest.TestCase):
    def setUp(self):
        self.config = infra.configuration('dev')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'run'

    def test_targets_have_separate_accounts_and_fixed_resources(self):
        prod = infra.configuration('prod')
        self.assertNotEqual(prod['account_id'], self.config['account_id'])
        for config in (prod, self.config):
            self.assertIn(config['account_id'], config['cloudformation_role_arn'])
            self.assertIn(config['environment'], config['stack_name'])
        with self.assertRaises(ValueError):
            infra.configuration('../../prod')

    @patch.object(infra, 'aws_json')
    @patch.object(infra.subprocess, 'run')
    def test_wrong_account_fails_before_any_cloudformation_mutation(self, run, aws_json):
        aws_json.return_value = {'Account': '334557859583', 'Arn': 'unexpected'}
        with self.assertRaisesRegex(ValueError, 'caller account'):
            infra.deploy(self.config, self.output)
        run.assert_not_called()
        self.assertEqual('FAIL', json.loads((self.output / 'receipt.json').read_text())['result'])

    def stack_response(self, role=None, status='UPDATE_COMPLETE'):
        return {'Stacks': [{
            'StackId': 'arn:aws:cloudformation:eu-west-1:604151511147:stack/blue-semantic-cards-dev/fixture',
            'StackStatus': status,
            'RoleARN': role or self.config['cloudformation_role_arn'],
            'Outputs': [
                {'OutputKey': 'BucketName', 'OutputValue': 'blue-semantic-cards-dev'},
                {'OutputKey': 'GitHubVariables', 'OutputValue': 'SEMANTICS_BUCKET=blue-semantic-cards-dev\n'},
            ],
        }]}

    @patch.object(infra, 'aws_json')
    @patch.object(infra.subprocess, 'run')
    def test_success_uses_exact_execution_role_and_both_boundaries(self, run, aws_json):
        aws_json.side_effect = [
            {'Account': '604151511147', 'Arn': 'fixture-caller'}, self.stack_response(),
        ]
        receipt = infra.deploy(self.config, self.output)
        self.assertEqual('PASS', receipt['result'])
        command = run.call_args.args[0]
        self.assertEqual(self.config['cloudformation_role_arn'], command[command.index('--role-arn') + 1])
        self.assertIn('CreateGitHubOIDCProvider=false', command)
        self.assertIn('ReadRolePermissionsBoundaryArn=' + self.config['read_boundary_arn'], command)
        self.assertIn('PublishRolePermissionsBoundaryArn=' + self.config['publish_boundary_arn'], command)
        self.assertIn('--no-fail-on-empty-changeset', command)
        self.assertNotIn('--resource-types', command)
        self.assertTrue((self.output / 'github-variables.txt').exists())

    @patch.object(infra, 'aws_json')
    @patch.object(infra.subprocess, 'run')
    def test_cli_failure_is_not_reported_as_success(self, run, aws_json):
        aws_json.return_value = {'Account': '604151511147', 'Arn': 'fixture-caller'}
        run.side_effect = subprocess.CalledProcessError(1, ['aws', 'cloudformation', 'deploy'])
        with self.assertRaises(subprocess.CalledProcessError):
            infra.deploy(self.config, self.output)
        self.assertEqual('FAIL', json.loads((self.output / 'receipt.json').read_text())['result'])
        self.assertFalse((self.output / 'github-variables.txt').exists())

    @patch.object(infra, 'aws_json')
    @patch.object(infra.subprocess, 'run')
    def test_successful_cli_exit_is_insufficient_with_wrong_service_role(self, run, aws_json):
        aws_json.side_effect = [
            {'Account': '604151511147', 'Arn': 'fixture-caller'},
            self.stack_response(role='arn:aws:iam::604151511147:role/unrelated'),
        ]
        with self.assertRaisesRegex(ValueError, 'expected scoped'):
            infra.deploy(self.config, self.output)
        self.assertEqual('FAIL', json.loads((self.output / 'receipt.json').read_text())['result'])

    @patch.object(infra, 'aws_json')
    def test_reusing_a_receipt_directory_cannot_preserve_stale_success(self, aws_json):
        self.output.mkdir()
        (self.output / 'receipt.json').write_text('{"result":"PASS"}')
        with self.assertRaisesRegex(ValueError, 'fresh output'):
            infra.deploy(self.config, self.output)
        aws_json.assert_not_called()


if __name__ == '__main__':
    unittest.main()
