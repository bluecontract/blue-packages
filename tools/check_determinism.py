#!/usr/bin/env python3
"""Verify ordering publication bindings and compare complete semantic runner outputs.

Usage: --python PATH --java PATH --myos PATH --output RESULT.json
       --result python=RUN.json --result java=RUN.json --result myos=RUN.json
Extra named process/cache variants are compared without normalization.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EDITION = ROOT / 'editions/ordering-1'


def sha(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def difference(a, b, path='$'):
    if type(a) is not type(b):
        return path + ': JSON types differ'
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return path + ': fields differ'
        for key in sorted(a):
            found = difference(a[key], b[key], path + '/' + key)
            if found:
                return found
    elif isinstance(a, list):
        if len(a) != len(b):
            return path + ': list lengths differ'
        for index, (left, right) in enumerate(zip(a, b)):
            found = difference(left, right, path + '/' + str(index))
            if found:
                return found
    elif a != b:
        return path + ': values differ: ' + repr(a)[:100] + ' != ' + repr(b)[:100]
    return None


def verify_sources(args, pins):
    archive = (EDITION / 'package.bluepkg').read_bytes()
    assert sha(archive) == pins['archiveSha256']
    copies = [args.python / 'src/blue_packages/resources/ordering-1.bluepkg',
              args.java / 'blue-contracts-core/src/main/resources/ordering-1/package.bluepkg',
              args.myos / 'runtime/blue-contracts-core/src/main/resources/ordering-1/package.bluepkg']
    for copy in copies:
        assert copy.read_bytes() == archive, 'Publication differs: ' + str(copy)
    assert json.loads((args.python / 'src/blue_packages/ordering.json').read_text()) == pins
    for root in [args.java, args.myos / 'runtime']:
        source = (root / 'blue-contracts-core/src/main/java/blue/contracts/OrderingPublication.java').read_text()
        for value in [pins['packageBlueId'], pins['protocol'], pins['specificationBlueId'], pins['archiveSha256'][7:]]:
            assert '"' + value + '"' in source, 'Wrong Java publication binding'
    work = (EDITION / 'work.py').read_bytes()
    assert (args.python / 'src/blue_contracts/reference/work.py').read_bytes() == work
    with zipfile.ZipFile(EDITION / 'package.bluepkg') as package:
        manifest = json.loads(package.read('package.json'))
        assert manifest['packageBlueId'] == pins['packageBlueId']
        rules = package.read('spec/contracts-ordering.md')
        assert sha(rules) == 'sha256:' + pins['specificationSha256']
        sources = json.loads(package.read('docs/sources.json'))
        modules = {name: (body.rstrip('\n') + '\n').encode() for name, body in
                   re.findall(r'### `([^`]+)`\n\n```python\n(.*?)\n```', rules.decode(), re.S)}
        assert modules['src/blue_contracts/reference/work.py'] == work
        assert {name: sha(body)[7:] for name, body in modules.items()} == sources['modules']
        assert sha(work)[7:] == pins['sourceSha256'] == sources['authoredWorkSha256']
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['python', 'java', 'myos', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--result', action='append', required=True)
    args = parser.parse_args()
    pins = json.loads((EDITION / 'selection.json').read_text())
    manifest = verify_sources(args, pins)
    runs = {name: Path(path) for name, path in (item.split('=', 1) for item in args.result)}
    assert {'python', 'java', 'myos'} <= runs.keys()
    values = {name: json.loads(path.read_text()) for name, path in runs.items()}
    expected = values['python']
    for name, value in values.items():
        error = difference(expected, value)
        assert error is None, name + ': ' + str(error)
    corpus = ROOT / 'conformance/determinism/cases.json'
    rows = []
    for fixture in json.loads(corpus.read_text())['cases']:
        case = fixture['id']
        outcomes = expected[case]
        full = next(r for r in outcomes if r['budget'] == 100000)
        gas = full['observations']['gas']
        exact = next(r for r in outcomes if r['budget'] == gas)
        below = next(r for r in outcomes if r['budget'] == gas - 1)
        assert exact['observations']['status'] == full['observations']['status']
        assert below['observations']['status'] == 'GAS_LIMIT_EXCEEDED'
        assert below['before'] == below['after'] and below['emitted'] == []
        if case == 'ordered-events':
            assert full['emitted'] == [{'label': '\U00010000'}, {'label': '\ue000'}]
        for row in outcomes:
            observed = row['observations']
            rows.append({'case': case, 'budget': row['budget'], 'status': observed['status'],
                         'gas': observed['gas'], 'inputSnapshot': row['before'], 'outputSnapshot': row['after'],
                         'receipt': row['receipt'], 'emitted': row['emitted'],
                         'observationsSha256': sha(json.dumps(observed, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())})
    result = {'format': 'blue-determinism-conformance/1', 'status': 'PASS',
              'scope': 'Contracts ordering-1, exact retained Language/BEX; not a cross-runtime Coordination qualification',
              'comparison': 'Recursive JSON value/type equality; list order retained; no output fields discarded',
              'publication': pins, 'languagePackage': manifest['language'],
              'corpusSha256': sha(corpus.read_bytes()), 'cases': len(json.loads(corpus.read_text())['cases']),
              'runs': {name: {'file': path.name, 'sha256': sha(path.read_bytes())} for name, path in runs.items()},
              'physicalChecks': ['reused runtime after unrelated operation', 'cold serialized snapshot replay',
                                 'input immutability', 'reversed graph acquisition', 'Java cleared cache'],
              'firstError': expected['firstError'], 'merge': expected['merge'],
              'privateDigest': expected['privateDigest'], 'outcomes': rows}
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print('PASS:', len(runs), 'runs;', len(rows), 'outcomes; sources, exact budgets and rollback verified')


if __name__ == '__main__':
    main()
