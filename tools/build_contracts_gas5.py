#!/usr/bin/env python3
"""Build an immutable C1/gas5 edition and its explicitly selected import closure.

Uses the existing locked publisher and ordinary Language definition admission.
Historical source projects, distributions and native approvals are never edited.
An existing output is only compared by --check, never replaced.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile

from build_mandates import (
    ROOT, Language, Repository, PhysicalCache, build, read_package,
    require, sha, source, verify_bytes, wire, write_set,
)
from blue_runtime.core_reuse import core_reuse_scope

EDITION = 'contracts-c1-gas5-20261002-1'
PROFILE = 'blue-runtime/2026-10-02-contracts-c1-gas5-1'
RECIPE = ROOT / 'editions/contracts-c1-gas5/recipe.json'


def put(root, name, data):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def checked_inputs(python_root, recipe):
    for root, key in ((ROOT, 'packageInputs'), (python_root, 'pythonInputs')):
        for name, expected in recipe[key].items():
            require(sha((root / name).read_bytes()) == expected, 'Input drift: ' + name)


def contracts_specification(python_root):
    text = (ROOT / 'blue-contracts/SPECIFICATION.md').read_text()
    require(text.count('blue-contracts/2026-09-26-standalone-1') == 1, 'Base edition drift')
    text = text.replace('blue-contracts/2026-09-26-standalone-1', 'blue-contracts/' + EDITION)
    amendment = (ROOT / 'editions/contracts-exact-target/target-slot.md').read_text()
    require(text.count('<a id="section-7"></a>') == 1, 'Request clause drift')
    text = text.replace('<a id="section-7"></a>', amendment + '\n<a id="section-7"></a>')
    gas = (python_root / 'specification-src/contracts/GAS_PROFILE.md').read_text()
    enum = gas.split('## Enum validation order\n\n', 1)[1].split('\n## Counter placement', 1)[0]
    # The prior reading publication described its intentionally stale catalogue.
    # This successor contains the actual gas5 listing and schedule itself.
    enum = enum.split('\nThe gas profile selects', 1)[0].rstrip()
    text = text.replace('### Counter placement\n', '### Enum validation order\n\n' + enum + '\n\n### Counter placement\n', 1)
    inventory = json.loads((ROOT / 'blue-contracts/docs/sources.json').read_text())
    changed = []
    for name, expected in inventory['modules'].items():
        pattern = r'(### `' + re.escape(name) + r'`\n\n```python\n)(.*?)(\n```)'
        matches = list(re.finditer(pattern, text, re.S))
        require(len(matches) == 1, 'Missing unique executable annex: ' + name)
        match = matches[0]
        require(hashlib.sha256((match.group(2) + '\n').encode()).hexdigest() == expected,
                'Frozen annex inventory drift: ' + name)
        data = (python_root / name).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual == expected:
            continue
        require(name in ('src/blue_contracts/reference/channels.py', 'src/blue_contracts/reference/work.py'),
                'Unapproved executable change: ' + name)
        text = text[:match.start(2)] + data.decode().rstrip('\n') + text[match.end(2):]
        text = text.replace('| `' + name + '` | `' + expected + '` |',
                            '| `' + name + '` | `' + actual + '` |')
        inventory['modules'][name] = actual
        changed.append(name)
    require(len(changed) == 2, 'Expected exactly C1 and gas5 executable changes')
    manifest = json.loads((python_root / 'src/blue_contracts/GAS_MANIFEST.json').read_text())
    schedules = []
    for match in re.finditer(r'```json\n(.*?)\n```', text, re.S):
        try:
            value = json.loads(match.group(1))
        except ValueError:
            continue
        if isinstance(value, dict) and value.get('profile') == 'contracts-deterministic-gas-4':
            schedules.append((match, value))
    require(len(schedules) == 1, 'Missing unique gas4 schedule')
    match, old = schedules[0]
    require(old['weights'] == manifest['weights'] and old['sharedMaximum'] == manifest['sharedMaximum'],
            'Tariff or maximum changed')
    text = text[:match.start(1)] + json.dumps(manifest, indent=2) + text[match.end(1):]
    inventory.update(allAlgorithmFilesUnchanged=False, edition=EDITION,
                     changedModules=changed, gasProfile=manifest['profile'])
    return text, inventory


def replace_ids(value, replacements):
    """Rebind explicit exact operands, including Blue programs' string type IDs."""
    if isinstance(value, str):
        return replacements.get(value, value)
    if isinstance(value, list):
        return [replace_ids(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: replace_ids(item, replacements) for key, item in value.items()}
    return value


def coordination_specification(python_root):
    text = (ROOT / 'blue-coordination/spec/coordination.md').read_text()
    marker = '# Exact imported specification bindings\n\n```json\n'
    require(text.count(marker) == 1, 'Coordination imported binding drift')
    prefix, tail = text.split(marker)
    payload, suffix = tail.split('\n```', 1)
    binding = json.loads(payload)
    require(binding['edition'] == '2026-09-24-core-compute-1', 'Coordination binding edition drift')
    require(binding['files'].pop('contracts/COMPLETE_SPECIFICATION.md') ==
            'c7cf9c28ca437701e1be27c925e4152cadce0eb6a3b4dc59e3cebbba4a63746a',
            'Coordination predecessor Contracts binding drift')
    contracts, _ = contracts_specification(python_root)
    binding['edition'] = EDITION
    binding['files']['contracts/PACKAGE_SPECIFICATION.md'] = hashlib.sha256(contracts.encode()).hexdigest()
    return prefix + marker + json.dumps(binding, indent=2, sort_keys=True) + '\n```' + suffix


def contracts_counter(project, python_root, rules, aliases):
    """Publish a successor example, retaining the independent predecessor oracle.

    The selected catalogue is bound just as in the library's package adapter.
    No runtime algorithm or historical expected output is rewritten. Business
    effects and the entire gas observation must still match the frozen Counter.
    Fresh identities/receipts are then independently checked by native Java.
    """
    from blue_contracts.reference.processor import Processor
    from blue_contracts.reference.registry import Registry, ROLES
    from blue_contracts.reference.language import Bridge
    from blue_contracts.reference.catalogue import publish_catalogue
    from algorithms.blue import CORE
    processor = Processor()
    processor.blue = Bridge(Language(core_contracts=False))
    bridge = processor.blue
    specification = bridge.identity(bridge.source((project / 'spec/contracts.md').read_text()))
    require(specification == rules, 'Counter specification differs')
    types = publish_catalogue(lambda raw: bridge.identity(bridge.source(raw, goal='definition')), specification, CORE)
    require(types == {name.split('/')[-1]: identity for name, identity in aliases.items()},
            'Counter native catalogue differs')
    registry = object.__new__(Registry)
    registry.blue, registry.specification, registry.types, registry.extensions = bridge, specification, types, {}
    registry.by_id = {identity: ROLES[name] for name, identity in types.items()}
    bridge.language.aliases.update({prefix + name: identity for name, identity in types.items()
                                   for prefix in ('', 'Contracts/', 'contracts/')})
    bridge.refresh()
    processor.registry = registry
    document = source((project / 'examples/counter.blue').read_bytes())
    event = source((project / 'examples/request.blue').read_bytes())
    prior = json.loads((ROOT / 'blue-contracts/conformance/counter.json').read_text())
    frozen = json.loads((python_root / 'provenance/enum-metering-20260930/counter-gas4.json').read_text())
    before = processor.initialize(document)
    result = processor.process(before.snapshot, event, prior['eventTimestamp'])
    observations = result.observations()
    require(result.status == prior['expected']['outcome'] == 'APPLIED', 'Counter outcome changed')
    require(processor.read(result.snapshot, '/count') == prior['expected']['count'] == 1, 'Counter value changed')
    require(processor.emitted(result) == prior['expected']['emitted'], 'Counter events changed')
    require(result.gas == prior['expected']['gas'], 'Counter gas changed')
    for key in ('gas', 'gasTrace', 'changes', 'rounds', 'diagnostic', 'rejected', 'status'):
        require(observations[key] == frozen['observations'][key],
                'Counter independent predecessor observation changed: ' + key)
    expected = dict(prior['expected'], authoredBlueId=bridge.identity(bridge.source(document)),
                    resultBlueId=result.snapshot.documents['root'].blue_id, receipt=result.receipt)
    vector = dict(prior, expected=expected, gasProfile='contracts-deterministic-gas-5-enum',
                  observations=observations, predecessor=dict(
                      packageBlueId=frozen['packageBlueId'], archiveSha256=frozen['archiveSha256'],
                      conformanceSha256=sha((ROOT / 'blue-contracts/conformance/counter.json').read_bytes()),
                      fullGasObservationUnchanged=True))
    put(project, 'conformance/counter.json', wire(vector))


def dependency_pins(config, packages):
    return {'format': 2, 'imports': {prefix: dict(
        path=config['imports'][prefix]['path'], packageBlueId=package.manifest['packageBlueId'],
        archiveSha256=package.archive_sha, repositoryIdentity=package.repository.identity,
        name=package.manifest['name'], version=package.manifest['version'])
        for prefix, package in packages.items()}}


def predecessor(relative, python_root):
    path = ROOT / relative / 'dist/package.bluepkg'
    if relative == 'blue-mandates':
        path = python_root / 'inputs/mandates-predicate-scalar-20261001/package.bluepkg'
    return read_package(path)


def compile_project(relative, output, python_root, replacements, successors, *, contracts=False):
    original = ROOT / relative
    project = output / relative
    config = json.loads((original / 'blue-package.yaml').read_text())
    dependencies = {}
    for prefix, entry in config['imports'].items():
        old_path = (original / entry['path']).resolve()
        old = read_package(old_path)
        selected = successors.get(old.manifest['packageBlueId'])
        dependencies[prefix] = selected if selected is not None else old
        # Source dependencies are pinned copied archives, never a moving sibling.
        entry['path'] = 'inputs/' + prefix + '.bluepkg'
        put(project, entry['path'], dependencies[prefix].archive)
    language = Language(core_contracts=False)
    for prefix, package in dependencies.items():
        language.enable_repository(Repository.from_payload('import:' + prefix,
            {prefix + '/' + row['name']: row['blueId'] for row in package.manifest['exports']},
            package.repository.records))
    readme = (original / config['readme']).read_bytes()
    put(project, config['readme'], readme)
    rules = None
    if 'protocol' in config:
        path = config['protocol']['rules']
        if contracts:
            text, inventory = contracts_specification(python_root)
            put(project, 'docs/sources.json', wire(inventory))
            put(project, 'SPECIFICATION.md', text.encode())
        elif relative == 'blue-coordination':
            text = coordination_specification(python_root)
        else:
            text = (original / path).read_text()
        put(project, path, text.encode())
        put(project, 'spec/frozen.json', wire({path: sha(text.encode())}))
        rules = language.create(wire({'type': 'Text', 'value': text}).decode(), format='json')
        language.publish_document(rules)
    aliases = {}

    def admit(name, raw):
        doc = language.admit_definition(wire(raw).decode(), format='json')
        language.publish_document(doc)
        language.aliases[name] = doc.blue_id
        aliases[name] = doc.blue_id
        return doc.blue_id

    if contracts:
        spec = importlib.util.spec_from_file_location('edition_catalogue', python_root / 'src/blue_contracts/reference/catalogue.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        from algorithms.blue import CORE
        types = module.publish_catalogue(lambda raw: admit('Contracts/' + raw['name'], raw), rules.blue_id, CORE)
        aliases = {'Contracts/' + name: identity for name, identity in types.items()}
    elif relative == 'blue-coordination':
        catalogue = json.loads((original / 'docs/catalogue.json').read_text())
        sources = catalogue['sources']
        pending = set(sources)
        while pending:
            ready = sorted(name for name in pending if not (named_dependencies(sources[name]) & pending))
            require(ready, 'Unresolved Coordination type dependencies')
            for name in ready:
                raw = deepcopy(sources[name])
                raw['specification'] = {'blueId': rules.blue_id}
                # The authored catalogue includes signed-64-bit bounds. Use the
                # same public adapter as its owning catalogue generator so
                # these become exact Integer nodes, never unsafe JSON numbers.
                from blue_contracts.reference.language import Bridge
                admit(name, Bridge(language).normalize_input(raw))
                pending.remove(name)
    else:
        for entry in config['exports']:
            raw = replace_ids(source((original / entry['path']).read_bytes()), replacements)
            put(project, entry['path'], wire(raw))
            admit(config['namespace'] + '/' + entry['name'], raw)

    old = predecessor(relative, python_root)
    for entry in old.manifest['exports']:
        matches = [value for name, value in aliases.items() if name.split('/')[-1] == entry['name']]
        require(len(matches) == 1, 'Missing successor export: ' + entry['name'])
        replacements[entry['blueId']] = matches[0]
    if rules:
        old_text = old.files[config['protocol']['rules']].decode()
        old_rules = Language(core_contracts=False).create(wire(old_text).decode(), format='json').blue_id
        replacements[old_rules] = rules.blue_id
    repository = Repository.from_payload(config['name'], aliases, language.provider.snapshot())
    payload = (repository._json + '\n').encode()
    rel = 'inputs/catalogue.repository.json'
    put(project, rel, payload)
    config['inputs'] = [dict(path=rel, sha256=sha(payload), identity=repository.identity)]
    exports = config['exports']
    config['exports'] = [dict(name=entry['name'], fromInput=rel,
                              inputAlias=entry.get('inputAlias', config['namespace'] + '/' + entry['name']))
                         for entry in exports]
    config['version'] += '.c1-gas5.1'
    # Copy declared auxiliary sources; the catalogue is generated above/below.
    for name in config.get('files', []):
        if (project / name).exists() or name in ('docs/catalogue.json', 'docs/coordination.prepared.json'):
            continue
        data = (original / name).read_bytes()
        # Blue examples/docs with embedded exact IDs belong to the same closure.
        if name.endswith(('.json', '.blue', '.yaml')):
            try:
                data = wire(replace_ids(source(data), replacements))
            except (ValueError, TypeError):
                pass
        put(project, name, data)
    if relative == 'blue-coordination':
        from blue_repository.prepare import prepare
        data = dict(specification=rules.blue_id, contracts=replacements[catalogue['contracts']],
                    types=aliases, sources=sources)
        put(project, 'docs/catalogue.json', wire(data))
        prepared, digest = prepare(repository)
        put(project, 'docs/coordination.prepared.json', prepared)
    if contracts:
        contracts_counter(project, python_root, rules.blue_id, aliases)
    put(project, 'blue-package.yaml', wire(config))
    put(project, 'blue-package.lock.json', wire(dependency_pins(config, dependencies)))
    package = build(project, revision=EDITION, source_url='')
    verify_bytes(package.archive)
    write_set(project / 'dist', package)
    return package, rules.blue_id if rules else None, aliases


def named_dependencies(value):
    if isinstance(value, dict):
        return {v for k, v in value.items() if k in ('type', 'itemType', 'keyType', 'valueType') and isinstance(v, str)} | set().union(*(named_dependencies(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(named_dependencies(v) for v in value))
    return set()


def generate(python_root, destination):
    recipe = json.loads(RECIPE.read_text())
    checked_inputs(python_root, recipe)
    replacements, successors, rows, built = {}, {}, [], []
    for relative in recipe['projects']:
        print('Building', relative, flush=True)
        package, rules, aliases = compile_project(relative, destination, python_root, replacements,
                                                   successors, contracts=relative == 'blue-contracts')
        old = predecessor(relative, python_root)
        old_exports = {entry['name']: entry['blueId'] for entry in old.manifest['exports']}
        for entry in package.manifest['exports']:
            replacements[old_exports[entry['name']]] = entry['blueId']
        if rules:
            # Rules identity is evaluated with Language, never guessed from transport hashes.
            text = old.files[json.loads((ROOT / relative / 'blue-package.yaml').read_text())['protocol']['rules']].decode()
            language = Language(core_contracts=False)
            old_rules = language.create(wire({'type': 'Text', 'value': text}).decode(), format='json').blue_id
            replacements[old_rules] = rules
        replacements[old.manifest['packageBlueId']] = package.manifest['packageBlueId']
        if old.manifest['protocol']:
            replacements[old.manifest['protocol']] = package.manifest['protocol']
        successors[old.manifest['packageBlueId']] = package
        built.append((relative, old, package))
        # The authored Mandates project currently locks the same old foundation;
        # predecessor inventories keep their own old Mandates archive unchanged.
        row = dict(name=Path(relative).name, path=relative + '/dist/package.bluepkg',
                   packageBlueId=package.manifest['packageBlueId'], archiveSha256=package.archive_sha,
                   protocolId=package.manifest['protocol'], rulesId=rules,
                   predecessor=old.manifest['packageBlueId'])
        rows.append(row)
        print('Built', relative, row['packageBlueId'], flush=True)
    # An identity rotation is not permission to revise unrelated definitions.
    # Compare every canonical export body with its actual predecessor after
    # substituting only the generated exact identity map.
    compared = 0
    for relative, old, package in built:
        old_exports = {entry['name']: entry['blueId'] for entry in old.manifest['exports']}
        for entry in package.manifest['exports']:
            before = json.loads(old.repository.records[old_exports[entry['name']]]['text'])
            after = json.loads(package.repository.records[entry['blueId']]['text'])
            require(replace_ids(before, replacements) == after,
                    'Definition changed beyond identity rebinding: ' + relative + '/' + entry['name'])
            compared += 1
    support = json.loads((python_root / 'inputs/mandates-predicate-scalar-20261001/native-support.json').read_text())
    support = replace_ids(support, replacements)
    put(destination / 'blue-mandates', 'docs/native-support.json', wire(support))
    review = dict(format='contracts-c1-gas5-composition/1', edition=EDITION, profile=PROFILE,
                  nativeSupportApproved=False, gasProfile='contracts-deterministic-gas-5-enum',
                  recipe=recipe, packages=rows, identityMap=replacements,
                  definitionBodiesCompared=compared)
    put(destination, 'composition.json', wire(review))
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    destination = args.output.resolve()
    require(args.check or not destination.exists(), 'Refuse existing immutable destination')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix='.c1-gas5-') as tmp, PhysicalCache(65536).scope(), core_reuse_scope():
        staged = Path(tmp) / 'edition'
        staged.mkdir()
        review = generate(args.python_source.resolve(), staged)
        if args.check:
            files = lambda root: {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            require(files(staged) == files(destination), 'Rebuild differs from immutable edition')
        else:
            os.rename(staged, destination)
    print(json.dumps(dict(status='PASS', packages=len(review['packages']), edition=EDITION)))


if __name__ == '__main__':
    main()
