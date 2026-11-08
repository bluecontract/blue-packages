"""Bound the hosted Order refresh library without dropping native helper dependencies."""
import unittest
from pathlib import Path
import yaml
from tools.test_admission_definition_closure import calls
ROOT = Path(__file__).resolve().parents[1]

class ResellerRefreshDefinitionClosureTest(unittest.TestCase):
    def test_refresh_selection_covers_exact_calls_without_bootstrap_library(self):
        clause = yaml.safe_load((ROOT/'clause-reseller/types/customer-orders-bootstrap-clause.blue').read_text())
        hook = clause['hookDefinition']
        selected = hook.get('constants', {}).get('refreshFunctionNames', [])
        self.assertTrue(selected, 'Refresh must not load the complete bootstrap action definition')
        import json, zipfile
        with zipfile.ZipFile(ROOT/'clause-documents/dist/package.bluepkg') as archive:
            records = json.loads(archive.read('package-records.json'))
        def expand(value):
            if isinstance(value, dict):
                if 'value' in value and set(value) <= {'type', 'value'}:
                    return value['value']
                if 'items' in value and set(value) <= {'type', 'items'}:
                    return [expand(child) for child in value['items']]
                if set(value) == {'blueId'}:
                    return expand(json.loads(records[value['blueId']]['text']))
                return {key: expand(child) for key, child in value.items() if key != 'type'}
            if isinstance(value, list): return [expand(child) for child in value]
            return value
        functions = clause['actionDefinition']['type']['functions']
        pending, reached = ['sharedRefresh'], set()
        while pending:
            name = pending.pop()
            if name in reached: continue
            reached.add(name)
            pending.extend(calls(expand(functions[name])))
        self.assertEqual(set(selected), reached)
        self.assertEqual(len(selected), len(reached))
        self.assertNotIn('sharedPrepare', selected)
        self.assertNotIn('sharedProvide', selected)
        metadata = json.loads((ROOT/'clause-documents/dist/package.json').read_text())
        plan_id = next(row['blueId'] for row in metadata['exports'] if row['alias'] == 'Documents/Preparation Plan')
        with zipfile.ZipFile(ROOT/'clause-connections/dist/package.bluepkg') as archive:
            records.update(json.loads(archive.read('package-records.json')))
        def inherited_functions(identifier):
            node = json.loads(records[identifier]['text'])
            parent = node.get('type', {}).get('blueId')
            functions = inherited_functions(parent) if parent in records else {}
            return {**functions, **node.get('functions', {})}
        canonical_functions = inherited_functions(plan_id)
        canonical = canonical_functions['plan']
        pending, reached = ['plan', 'validateConfiguration', 'validateTransition'], set()
        while pending:
            name = pending.pop()
            if name in reached: continue
            reached.add(name)
            pending.extend(calls(expand(canonical_functions[name])))
        self.assertEqual(set(hook['functions']), (reached - {'plan'}) | {'basePreparationPlan', 'plan'})
        for name in reached - {'plan'}:
            self.assertEqual(expand(hook['functions'][name]), expand(canonical_functions[name]), name)
        delegated_id = hook['functions']['basePreparationPlan']['blueId']
        self.assertEqual(json.loads(records[delegated_id]['text']), canonical)

if __name__ == '__main__': unittest.main()
