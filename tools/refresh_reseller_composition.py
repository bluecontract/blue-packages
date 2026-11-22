#!/usr/bin/env python3
"""Refresh exact canonical function references in the Documents preparation plan.

Build clause-documents after updating the pinned functions. Identities are read
from the native package records.
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


if __name__ == '__main__':
    refresh()
