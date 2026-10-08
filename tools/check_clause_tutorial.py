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
    def is_clause(name, seen=()):
        if name == 'Clauses/Clause':
            return True
        if not isinstance(name, str) or name not in exports or name in seen:
            return False
        return is_clause(exports[name].get('type'), (*seen, name))
    expected = {name for name in exports if is_clause(name)}
    index = load(ROOT / 'examples/clause-tutorial/coverage.json')
    actual = [row['type'] for row in index['clauses']]
    assert len(actual) == len(set(actual)), 'Duplicate clause coverage'
    assert set(actual) == expected, f'Coverage mismatch: {set(actual) ^ expected}'
    for row in index['clauses']:
        assert 2 <= len(row['examples']) <= 3, row['type']
        assert (ROOT / row['definition']).is_file(), row['definition']
        for example in row['examples']:
            select(example['file'], example['pointer'])
    guide = (ROOT / 'docs/clauses-tutorial.md').read_text()
    for snippet in index['snippets']:
        file, pointer = snippet['file'], snippet['pointer']
        rendered = yaml.safe_dump(select(file, pointer), sort_keys=False, allow_unicode=True, width=105).rstrip()
        assert hashlib.sha256(rendered.encode()).hexdigest() == snippet['sha256'], f'Stale index: {file}#{pointer}'
        marker = f'<!-- source:{file}#{pointer} -->'
        sections = guide.split(marker)
        assert len(sections) > 1, f'Missing excerpt: {marker}'
        for section in sections[1:]:
            code = section.split('```yaml\n', 1)[1].split('\n```', 1)[0]
            assert code == rendered, f'Stale tutorial excerpt: {file}#{pointer}'
    for path in (ROOT / 'examples/clause-tutorial').glob('*.case.yaml'):
        case = load(path)
        assert path.with_name(case['document']).is_file(), str(path)
        assert case.get('steps'), f'Empty walkthrough: {path}'
    print(f'PASS: {len(expected)} clause types, {sum(len(r["examples"]) for r in index["clauses"])} use-case references, {len(index["snippets"])} exact excerpts')

if __name__ == '__main__':
    try:
        main()
    except (AssertionError, KeyError, ValueError, FileNotFoundError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        raise SystemExit(1)
