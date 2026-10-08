#!/usr/bin/env python3
"""Check complete clause coverage and exact tutorial excerpts; does not execute Blue."""
from pathlib import Path
import hashlib
import json
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]

class SourceLoader(yaml.SafeLoader):
    """Keep YAML authoring keys such as 'on' as text."""

SourceLoader.yaml_implicit_resolvers = {
    key: [(tag, expr) for tag, expr in values if tag != 'tag:yaml.org,2002:bool']
    for key, values in SourceLoader.yaml_implicit_resolvers.items()
}
SourceLoader.add_implicit_resolver('tag:yaml.org,2002:bool', re.compile(r'^(?:true|false)$', re.I), list('tTfF'))

def load(path):
    return yaml.load(path.read_text(), Loader=SourceLoader)

def select(file, pointer):
    path = (ROOT / file).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f'Path outside repository: {file}')
    value = load(path)
    for part in pointer.split('/')[1:] if pointer else []:
        key = part.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value

def main():
    exports = {}
    for package in load(ROOT / 'PACKAGE-SOURCES.json')['packages']:
        manifest = load(ROOT / package / 'blue-package.yaml')
        for item in manifest['exports']:
            exports[manifest['namespace'] + '/' + item['name']] = load(ROOT / package / item['path'])
    families = load(ROOT / 'PUBLIC-CLAUSES.json')['families']
    public = [t for family in families for t in family['types']]
    assert len(public) == len(set(public))
    assert set(public) <= exports.keys(), 'Missing public clause definition'
    assert len(families) == 13, 'Review additions to the selected public families'
    guide = (ROOT / 'docs/clauses-tutorial.md').read_text()
    assert (ROOT / 'clause-connections/types/hello-clause.blue').read_text().rstrip() in guide
    def visit(value):
        if isinstance(value, dict):
            assert 'contracts' not in value, 'Public examples must use clauses'
            for child in value.values(): visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    files = list((ROOT / 'examples/apps').glob('*.blue'))
    assert len(files) >= 20, 'Keep the ten application scenarios and at least ten additional examples'
    for file in files:
        document = load(file); visit(document)
        assert any(c.get('type') == 'Activation/Activation Clause' for c in document['clauses'].values()), file.name
        assert file.read_text().rstrip() in guide, 'Stale or missing full document: '+file.name
    for path in (ROOT / 'examples/apps').glob('*.case.yaml'):
        case=load(path)
        assert path.with_name(case['document']).is_file(), path.name
        assert case.get('steps'), path.name
    print(f'PASS: {len(families)} selected families, {len(files)} full clause-based documents; static checks only')

if __name__ == '__main__':
    try:
        main()
    except (AssertionError, KeyError, ValueError, FileNotFoundError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        raise SystemExit(1)
