"""Profile publication/fixture checks; native behavior is qualified by Core."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'blue-execution-profile'


class ExecutionProfilePublicationTest(unittest.TestCase):
    def test_native_publication_adds_no_execution_requirement(self):
        manifest = json.loads((PACKAGE / 'dist/package.json').read_text())
        semantic = manifest['semanticPackages'][manifest['packageBlueId']]
        self.assertIsNone(manifest['protocol'])
        self.assertEqual({'Language'}, set(manifest['imports']))
        self.assertEqual([], semantic['declaredRequirements'])
        self.assertEqual({}, semantic['specBindings'])
        rules = 'spec/execution-profile-v1.md'
        expected = 'sha256:' + hashlib.sha256((PACKAGE / rules).read_bytes()).hexdigest()
        frozen = json.loads((PACKAGE / 'spec/frozen.json').read_text())
        self.assertEqual(expected, frozen[rules])
        self.assertEqual(expected, semantic['documentation'][rules]['sha256'])

    def test_descriptor_remains_data_with_only_a_language_dependency(self):
        source = json.loads((PACKAGE / 'blue-package.yaml').read_text())
        profile = json.loads((PACKAGE / 'types/profile.blue').read_text())
        self.assertEqual({'Language'}, set(source['imports']))
        self.assertEqual([], source['executionRequires'])
        self.assertNotIn('protocol', source)
        # Plural contracts is Language execution metadata, not a descriptor field.
        self.assertNotIn('contracts', profile)
        self.assertIn('contract', profile)
        for field in ('coordination', 'coordinationSpecification', 'provider'):
            self.assertEqual({'schema': {'required': False}}, profile[field])
        required = {name for name, value in profile.items()
                    if isinstance(value, dict) and value.get('schema', {}).get('required')}
        self.assertEqual({'executionSpecification', 'language', 'bex', 'bexSpecification',
                          'contract', 'contractsSpecification', 'capabilities',
                          'supportedPackages'}, required)

    def test_fixture_parameters_are_explicit_and_no_fake_references_are_published(self):
        fixture = json.loads((PACKAGE / 'conformance/cases.json').read_text())
        self.assertEqual('blue-execution-profile-cases/1', fixture['format'])
        parameters = fixture['parameters']
        used = set()

        def inspect(value):
            if isinstance(value, dict):
                if '$fixture' in value:
                    self.assertEqual({'$fixture'}, set(value))
                    self.assertIn(value['$fixture'], parameters)
                    used.add(value['$fixture'])
                self.assertNotIn('blueId', value)
                for child in value.values():
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)

        inspect(fixture['cases'])
        inspect(fixture['descriptorCases'])
        self.assertEqual(set(parameters), used)
        cases = fixture['cases'] + fixture['descriptorCases']
        self.assertEqual(len(cases), len({case['id'] for case in cases}))
        for case in cases:
            self.assertIn('expect', case)


if __name__ == '__main__':
    unittest.main()
