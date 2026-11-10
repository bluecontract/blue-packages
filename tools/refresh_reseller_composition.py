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
    updated = yaml.safe_load(source)['actionDefinition']['type']['functions']
    selected = sorted(closure(['sharedRefresh'], updated))
    selection = '    refreshFunctionNames:\n'+''.join('    - '+name+'\n' for name in selected)
    source, count = re.subn(r'(?m)^    refreshFunctionNames:\n(?:    - .*\n)+', selection, source)
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
            marker = '  functions:\n'
            assert source.count(marker) == 1
            source = source.replace(marker, marker+replacement+'\n')
    manifest['sourceDefinition'] = exports['Document Preparation Functions']
    manifest['sourcePackageId'] = metadata['packageBlueId']
    source_path.write_text(source)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')

if __name__ == '__main__':
    refresh()
