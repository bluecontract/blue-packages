"""The generated refresh selection follows executable code, including literal Compute bodies."""
import json
from pathlib import Path
import unittest
import zipfile
import yaml
from tools.refresh_reseller_composition import refresh_program_roots
from tools.test_admission_definition_closure import calls

ROOT = Path(__file__).resolve().parents[1]


class DocumentRefreshClosureTest(unittest.TestCase):
    def test_final_archive_and_source_have_the_complete_exact_closure(self):
        plan = yaml.safe_load((ROOT/'clause-documents/types/preparation-plan.blue').read_text())
        roots, overrides = refresh_program_roots(plan)
        self.assertEqual({'sharedRefresh', 'rootSourceAccessLost'}, roots)
        records = {}
        for path in sorted(ROOT.glob('*/dist/package.bluepkg')):
            with zipfile.ZipFile(path) as archive:
                records.update(json.loads(archive.read('package-records.json')))
        def node(identifier):
            return json.loads(records[identifier]['text'])
        def effective(identifier):
            value = node(identifier)
            parent = value.get('type', {}).get('blueId')
            inherited = effective(parent) if parent in records else {}
            return {**inherited, **value.get('functions', {})}
        def plain(value):
            if isinstance(value, dict):
                if set(value) == {'blueId'}:
                    return plain(node(value['blueId']))
                if 'value' in value and set(value) <= {'type', 'value'}:
                    return value['value']
                if 'items' in value and set(value) <= {'type', 'items'}:
                    return [plain(child) for child in value['items']]
                return {key: plain(child) for key, child in value.items() if key != 'type'}
            return [plain(child) for child in value] if isinstance(value, list) else value
        metadata = json.loads((ROOT/'clause-documents/dist/package.json').read_text())
        exports = {row['name']: row['blueId'] for row in metadata['exports']}
        functions = effective(exports['Document Preparation Functions'])
        reached, pending = set(), list(roots)
        while pending:
            name = pending.pop()
            if name in reached:
                continue
            reached.add(name)
            pending.extend(calls(plain(overrides.get(name, functions.get(name)))))
        selected = plan['constants']['refreshCanonicalFunctions']
        self.assertEqual(reached - overrides.keys(), selected.keys())
        for name, identity in selected.items():
            self.assertEqual(plain(functions[name]), plain(node(identity)), name)
        packaged = plain(node(exports['Preparation Plan']))['constants']['refreshCanonicalFunctions']
        self.assertEqual(selected, packaged)

    def test_generated_compute_roots_include_code_but_not_literal_data(self):
        plan = {'do': [{'$let': {'name': 'refreshFunctions', 'expr': {
            'custom': {'args': {}, 'do': [{'$call': {'function': 'dependency'}}]}}}},
            {'functions': {'$var': 'refreshFunctions'}, 'constants': {'preflight': {'$call': {'function': 'before'}}},
             'do': {'$literal': [{'$call': {'function': 'custom'}}, {'$literal': {'$call': {'function': 'data'}}}]}}]}
        roots, _ = refresh_program_roots(plan)
        self.assertEqual({'custom', 'dependency', 'before'}, roots)


if __name__ == '__main__':
    unittest.main()
