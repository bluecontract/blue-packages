"""Keep generated admission definitions complete without importing unrelated code."""
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def calls(value):
    if isinstance(value, dict):
        call = value.get('$call')
        if isinstance(call, dict):
            if not isinstance(call.get('function'), str):
                raise AssertionError('Dynamic function call requires explicit closure review')
            yield call['function']
        for key, child in value.items():
            if key != '$literal':
                yield from calls(child)
    elif isinstance(value, list):
        for child in value:
            yield from calls(child)

class AdmissionDefinitionClosureTest(unittest.TestCase):
    def test_every_admission_step_has_complete_exact_function_selection(self):
        plan = yaml.safe_load((ROOT/'clause-documents/types/admission-plan-function.blue').read_text())
        definitions = {}
        for folder in ['blue-parties/types', 'clause-documents/types']:
            for path in (ROOT/folder).glob('*.blue'):
                node = yaml.safe_load(path.read_text())
                if isinstance(node, dict):
                    definitions.update({name: body for name, body in node.get('functions', {}).items()
                                        if isinstance(body, dict) and set(body) != {'blueId'}})
        found = {}
        def visit(node):
            if isinstance(node, dict):
                if node.get('name') in ['nextAdmission', 'installAdmission', 'finishAdmission']:
                    found[node['name']] = node['definition']
                for child in node.values(): visit(child)
            elif isinstance(node, list):
                for child in node: visit(child)
        visit(plan)
        for step, entry in [('nextAdmission','nextAdmissionRequest'), ('installAdmission','admissionInstallRequest'), ('finishAdmission','finishAdmission')]:
            with self.subTest(step=step):
                selected = found[step].get('$call', {}).get('args', {}).get('names', [])
                self.assertTrue(selected, 'Whole definition must not be loaded for admission step')
                pending, reached = [entry], set()
                while pending:
                    name = pending.pop()
                    if name in reached: continue
                    reached.add(name)
                    pending.extend(calls(definitions[name]))
                self.assertEqual(set(selected), reached)
                self.assertEqual(len(selected), len(set(selected)))

if __name__ == '__main__': unittest.main()
