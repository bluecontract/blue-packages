#!/usr/bin/env python3
"""Build the explicit C1 Contracts candidate; never replace/select a release."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import tempfile

from build_mandates import (ROOT, Language, Repository, PhysicalCache, build,
                           locked_dependencies, require, sha, verify_bytes, wire,
                           write_set)

EDITION = ROOT / 'editions/contracts-exact-target'


def checked(path, expected):
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected, 'source pin mismatch: ' + str(path))
    return data


def specification(python_root, recipe):
    for name, expected in recipe['inputs'].items():
        checked(ROOT/name, expected)
    for name, expected in recipe['pythonInputs'].items():
        checked(python_root/name, expected)
    amendment = checked(EDITION/'target-slot.md', recipe['amendmentSha256']).decode()
    text = (ROOT/'blue-contracts/SPECIFICATION.md').read_text()
    old_edition = 'blue-contracts/2026-09-26-standalone-1'
    require(text.count(old_edition) == 1, 'unexpected base edition')
    text = text.replace(old_edition, recipe['edition'])
    marker = '<a id="section-7"></a>'
    require(text.count(marker) == 1, 'missing owning request clause')
    text = text.replace(marker, amendment + '\n' + marker)
    module = 'src/blue_contracts/reference/channels.py'
    pattern = r'(### `' + re.escape(module) + r'`\n\n```python\n)(.*?)(\n```)'
    matches = list(re.finditer(pattern, text, re.S))
    require(len(matches) == 1, 'unexpected channels annex')
    match = matches[0]
    old = match.group(2) + '\n'
    old_hash = hashlib.sha256(old.encode()).hexdigest()
    inventory = json.loads((ROOT/'blue-contracts/docs/sources.json').read_text())
    require(old_hash == inventory['modules'][module], 'annex/source inventory mismatch')
    new = (python_root/module).read_text()
    text = text[:match.start(2)] + new.rstrip('\n') + text[match.end(2):]
    inventory['modules'][module] = hashlib.sha256(new.encode()).hexdigest()
    text = text.replace('| `' + module + '` | `' + old_hash + '` |',
                        '| `' + module + '` | `' + inventory['modules'][module] + '` |')
    inventory['allAlgorithmFilesUnchanged'] = False
    inventory['amendment'] = 'C1 exact document slot; only channels.py changed'
    return text, inventory


def compile_candidate(python_root, destination):
    recipe = json.loads((EDITION/'candidate.json').read_text())
    require(recipe['nativeSupportApproved'] is False, 'candidate cannot approve itself')
    require(not destination.exists(), 'refuse existing candidate destination')
    text, inventory = specification(python_root, recipe)
    cfg = json.loads((ROOT/'blue-contracts/blue-package.yaml').read_text())
    dependencies, pins = locked_dependencies(ROOT/'blue-contracts', cfg)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix='.contracts-candidate-') as tmp, PhysicalCache(65536).scope():
        root = Path(tmp)/'candidate'; root.mkdir()
        source = root/'source'; (source/'spec').mkdir(parents=True)
        (source/'inputs').mkdir(); (source/'docs').mkdir()
        (source/'spec/contracts.md').write_text(text)
        (source/'spec/frozen.json').write_bytes(wire({'spec/contracts.md': sha(text.encode())}))
        (source/'README.md').write_bytes((EDITION/'README.md').read_bytes())
        (source/'docs/sources.json').write_bytes(wire(inventory))
        for prefix, entry in cfg['imports'].items():
            (source/entry['path']).write_bytes(dependencies[prefix].archive)
        language = Language(core_contracts=False)
        for prefix, dependency in dependencies.items():
            language.enable_repository(Repository.from_payload('import:' + prefix,
                {prefix + '/' + e['name']: e['blueId'] for e in dependency.manifest['exports']},
                dependency.repository.records))
        rules = language.create(wire({'type': 'Text', 'value': text}).decode(), format='json')
        language.publish_document(rules)
        spec = importlib.util.spec_from_file_location('candidate_catalogue', python_root/'src/blue_contracts/reference/catalogue.py')
        catalogue = importlib.util.module_from_spec(spec); spec.loader.exec_module(catalogue)
        from algorithms.blue import CORE
        def admit(raw):
            doc = language.admit_definition(wire(raw).decode(), format='json')
            language.publish_document(doc)
            return doc.blue_id
        types = catalogue.publish_catalogue(admit, rules.blue_id, CORE)
        aliases = {'Contracts/' + name: bid for name, bid in types.items()}
        repository = Repository.from_payload(cfg['name'], aliases, language.provider.snapshot())
        data = (repository._json + '\n').encode()
        rel = 'inputs/catalogue.repository.json'; (source/rel).write_bytes(data)
        cfg['version'] = recipe['version']
        cfg['files'] = ['docs/sources.json']
        cfg['inputs'] = [{'path': rel, 'sha256': sha(data), 'identity': repository.identity}]
        (source/'blue-package.yaml').write_bytes(wire(cfg))
        (source/'blue-package.lock.json').write_bytes(wire(pins))
        package = build(source, revision=recipe['edition'], source_url='')
        verify_bytes(package.archive)
        require(all(package.manifest['imports'][p]['packageBlueId'] == d.manifest['packageBlueId']
                    for p, d in dependencies.items()), 'dependency drift')
        write_set(root/'dist', package)
        review = {'nativeSupportApproved': False, 'selectedByAnyRuntime': False,
                  'recipe': recipe, 'rulesId': rules.blue_id,
                  'packageId': package.manifest['packageBlueId'], 'archiveSha256': package.archive_sha,
                  'protocolId': package.manifest['protocol'], 'types': aliases,
                  'imports': pins['imports'], 'audit': package.audit,
                  'pythonSource': str(python_root), 'retainedGasProfile': recipe['retainedGasProfile']}
        (root/'REVIEW.json').write_bytes(wire(review))
        os.rename(root, destination)
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(compile_candidate(args.python_source.resolve(), args.output.resolve()), indent=2))


if __name__ == '__main__':
    main()
