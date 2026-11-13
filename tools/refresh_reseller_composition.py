#!/usr/bin/env python3
"""Refresh exact native Documents references after building its new archive.

Domain functions remain unchanged. Identities are read from native package records,
never computed by this adapter. Build clause-reseller afterwards, then check pins.
"""
import json
import re
import zipfile
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def refresh_program_roots(plan):
    """Read actual emitted Compute programs, including their step-level overrides."""
    roots = set()
    overrides = None
    def calls(value):
        if isinstance(value, dict):
            if '$call' in value:
                name = value['$call']['function']
                if not isinstance(name, str):
                    raise ValueError('Dynamic refresh function requires explicit closure review')
                roots.add(name)
            for key, child in value.items():
                if key != '$literal':
                    calls(child)
        elif isinstance(value, list):
            for child in value:
                calls(child)
    def visit(value):
        nonlocal overrides
        if isinstance(value, dict):
            if value.get('$let', {}).get('name') == 'refreshFunctions':
                overrides = value['$let']['expr']
            if value.get('functions') == {'$var': 'refreshFunctions'}:
                program = value.get('do', {})
                if set(program) != {'$literal'}:
                    raise ValueError('Refresh Compute must expose its complete literal program')
                calls(program['$literal'])
                calls({key: child for key, child in value.items() if key != 'do'})
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(plan)
    if not roots or not isinstance(overrides, dict):
        raise ValueError('No complete Documents refresh Compute was found')
    calls(overrides)
    return roots, overrides

def refresh(root=ROOT):
    records = {}
    # Dependencies first; the candidate Documents archive supplies its exact closure.
    for path in sorted(root.glob('*/dist/package.bluepkg')):
        with zipfile.ZipFile(path) as archive:
            records.update(json.loads(archive.read('package-records.json')))
    def node(identifier):
        return json.loads(records[identifier]['text'])
    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(',', ':'))
    index = {canonical(node(key)): key for key in records}
    def reference(value):
        return value if set(value) == {'blueId'} else {'blueId': index[canonical(value)]}
    def effective(identifier):
        value = node(identifier)
        parent = value.get('type', {}).get('blueId')
        result = effective(parent) if parent in records else {}
        return {**result, **value.get('functions', {})}
    def plain(value):
        if isinstance(value, dict):
            if 'value' in value and set(value) <= {'type', 'value'}:
                return value['value']
            if 'items' in value and set(value) <= {'type', 'items'}:
                return [plain(child) for child in value['items']]
            if set(value) == {'blueId'}:
                return plain(node(value['blueId']))
            return {key: plain(child) for key, child in value.items() if key != 'type'}
        return [plain(child) for child in value] if isinstance(value, list) else value
    def calls(value):
        if isinstance(value, dict):
            if '$call' in value:
                yield value['$call']['function']
            for key, child in value.items():
                if key != '$literal':
                    yield from calls(child)
        elif isinstance(value, list):
            for child in value:
                yield from calls(child)
    metadata = json.loads((root/'clause-documents/dist/package.json').read_text())
    exports = {row['name']: row['blueId'] for row in metadata['exports']}
    functions = effective(exports['Document Preparation Functions'])
    plan_path = root/'clause-documents/types/preparation-plan.blue'
    plan_source = plan_path.read_text()
    plan = yaml.safe_load(plan_source)
    roots, overrides = refresh_program_roots(plan)
    reached, pending = set(), list(roots)
    while pending:
        name = pending.pop()
        if name in reached:
            continue
        reached.add(name)
        # Step-level functions take precedence, as in Contracts Compute.
        body = overrides.get(name, functions.get(name))
        if body is None:
            raise ValueError('Missing Documents refresh dependency: '+name)
        pending.extend(calls(plain(body)))
    selected = {name: reference(functions[name])['blueId'] for name in sorted(reached - overrides.keys())}
    generated = yaml.safe_dump({'refreshCanonicalFunctions': selected}, sort_keys=False)
    generated = ''.join('  '+line+'\n' for line in generated.splitlines())
    if 'refreshCanonicalFunctions' in plan.get('constants', {}):
        plan_source, count = re.subn(r'(?ms)^  refreshCanonicalFunctions:\n.*?(?=^  [A-Za-z]|^functions:)', generated, plan_source)
        assert count == 1
    else:
        plan_source = plan_source.replace('constants:\n', 'constants:\n'+generated, 1)
    plan_path.write_text(plan_source)
    manifest_path = root/'clause-reseller/bootstrap-composition.json'
    manifest = json.loads(manifest_path.read_text())
    source_path = root/'clause-reseller/types/customer-orders-bootstrap-clause.blue'
    source = source_path.read_text()
    authored = yaml.safe_load(source)
    copied = authored['actionDefinition']['type']['functions']
    shared = set(manifest['functions']) | {'rootSourceAccessLost'}
    # Follow the actual inherited library; preserve explicit domain overrides.
    pending = list(shared)
    while pending:
        name = pending.pop()
        for called in calls(plain(functions[name])):
            if called in functions and called not in copied and called not in shared:
                shared.add(called)
                pending.append(called)
    for name in sorted(shared):
        ref = reference(functions[name])
        pattern = r'(?m)^      '+re.escape(name)+r':\n        blueId: \S+$'
        replacement = '      '+name+':\n        blueId: '+ref['blueId']
        if name in manifest['functions']:
            source, count = re.subn(pattern, replacement, source)
            assert count == 1, name
        else:
            source = source.replace('    functions:\n', '    functions:\n'+replacement+'\n', 1)
        manifest['functions'][name] = ref
    def closure(start, library):
        reached, pending = set(), list(start)
        while pending:
            name = pending.pop()
            if name in reached:
                continue
            reached.add(name)
            pending.extend(calls(plain(library[name])))
        return reached
    # The copied planner must carry the same guard metadata. Its plan delegates
    # directly, so it cannot undo the generic selector's custom-library path.
    selection = ''.join('    '+line+'\n' for line in yaml.safe_dump(
        {'refreshCanonicalFunctions': selected}, sort_keys=False).splitlines())
    if 'refreshFunctionNames' in authored['hookDefinition'].get('constants', {}):
        source, count = re.subn(r'(?m)^    refreshFunctionNames:\n(?:    - .*\n)+', selection, source)
    else:
        source, count = re.subn(r'(?ms)^    refreshCanonicalFunctions:\n.*?(?=^    [A-Za-z]|^  functions:)', selection, source)
    assert count == 1
    planning = effective(exports['Preparation Plan'])
    needed = closure(['plan', 'validateConfiguration', 'validateTransition'], planning)
    hook = yaml.safe_load(source)['hookDefinition']['functions']
    for name in sorted(needed):
        target = 'basePreparationPlan' if name == 'plan' else name
        ref = reference(planning[name])
        pattern = r'(?m)^    '+re.escape(target)+r':\n      blueId: \S+$'
        replacement = '    '+target+':\n      blueId: '+ref['blueId']
        if target in hook:
            source, count = re.subn(pattern, replacement, source)
            assert count == 1, target
        else:
            source, count = re.subn(r'(?m)^  functions:\n', lambda match: match.group()+replacement+'\n', source)
            assert count == 1
    manifest['sourceDefinition'] = exports['Document Preparation Functions']
    manifest['sourcePackageId'] = metadata['packageBlueId']
    source_path.write_text(source)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')

if __name__ == '__main__':
    refresh()
