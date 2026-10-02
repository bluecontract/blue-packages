#!/usr/bin/env python3
"""Generate the release selection for the C1/gas5 composition, retaining old bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EDITION = ROOT / 'editions/contracts-c1-gas5'
PREFIX = 'editions/contracts-c1-gas5/generated/'


def wire(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


def sha(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def generated(python_root, java_inputs):
    before = json.loads((EDITION / 'previous-shared.json').read_text())
    old_root = json.loads((EDITION / 'previous-root-clauses.json').read_text())
    composition = json.loads((ROOT / PREFIX / 'composition.json').read_text())
    new = {row['path']: {key: row[key] for key in ('name', 'path', 'packageBlueId', 'archiveSha256')}
           for row in composition['packages']}
    for row in new.values():
        row['path'] = PREFIX + row['path']
        data = (ROOT / row['path']).read_bytes()
        if sha(data) != row['archiveSha256']:
            raise ValueError('Generated archive drift: ' + row['path'])
    selected = [new.get(row['path'], row) for row in before['packages']]
    shared = dict(format=before['format'], packages=selected, profile=composition['profile'],
                  profiles=[composition['profile']])
    roots = dict(edition='root-clause-contracts-c1-gas5-20261002-1', nativeRuntimeModified=False,
                 packages=[new[row['path']] for row in old_root['packages']])
    active_paths = {row['path'] for row in selected}
    retained = [dict(row, selection='retained-shared-20260930') for row in before['packages'] if row['path'] not in active_paths]
    retained += [dict(row, selection=old_root['edition']) for row in old_root['packages']]
    # This approved predecessor was a pinned consumer input, not part of the
    # September release. Include its exact bytes so the new bundle is self-contained.
    original = python_root / 'inputs/mandates-predicate-scalar-20261001/package.bluepkg'
    data = original.read_bytes()
    if sha(data) != 'sha256:5e6a2d2abceed158a7716113b59683c71c7b6f6fdb21dc27e4c0e9153b145a57':
        raise ValueError('Approved Mandates predecessor drift')
    destination = 'blue-mandates-predicate-scalar'
    outputs = {destination + '/dist/package.bluepkg': data}
    with zipfile.ZipFile(original) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(files['package.json'])
    outputs.update({destination + '/dist/' + name: value for name, value in files.items()})
    by_id = {row['packageBlueId']: row for row in before['packages']}
    pins = {}
    for prefix, pin in manifest['imports'].items():
        row = by_id[pin['packageBlueId']]
        payload = (ROOT / row['path']).read_bytes()
        if sha(payload) != pin['archiveSha256']:
            raise ValueError('Retained dependency drift: ' + prefix)
        relative = 'inputs/' + prefix + '.bluepkg'
        outputs[destination + '/' + relative] = payload
        pins[prefix] = dict(pin, path=relative)
    outputs[destination + '/blue-package.lock.json'] = wire(dict(format=2, imports=pins))
    retained.append(dict(name='blue-mandates', path=destination + '/dist/package.bluepkg',
                         packageBlueId=manifest['packageBlueId'], archiveSha256=sha(data),
                         selection='retained-mandates-predicate-scalar-20261001'))
    # Exact historic Java authority selectors remain available. The source PR
    # already retains the /1 archive; the /2 scalar archive is the approved,
    # immutable input carried by the pinned MyOS base, never a performance tree.
    retained.append(dict(name='blue-mandates',
        path='editions/contracts-c1-gas5/retained/java-mandates/dist/package.bluepkg',
        packageBlueId='HCpgCrquNyV5iVfFZnq2XqMfjoqiqftz5AzQCN9zqsP9',
        archiveSha256='sha256:ebb150b7e7a474924fb7c462b3cad9cb660f6416692c3158026e007a132f7538',
        selection='retained-java-mandates-20260927'))
    retained.append(dict(name='blue-mutual-activation',
        path='editions/contracts-c1-gas5/retained/java-mutual-activation/dist/package.bluepkg',
        packageBlueId='46pv9pZoyGpHuVA2tY6JZuhQ8JdJ6TGcMv8bp4ExmpbH',
        archiveSha256='sha256:e8fee57aa81eaf1f85258dae1436e72be79e9780a0a4f08afa7d9a563b693616',
        selection='retained-java-mutual-activation-20260927'))
    for original, row in zip((
            'verification/publications/mandates-before-predicate-context-20260929/dist/package.bluepkg',
            'verification/publications/blue-mutual-activation/dist/package.bluepkg'), retained[-2:], strict=True):
        # Historical source snapshots have archive-only distributions and locks
        # relative to their old workspace. Preserve them, and generate a separate
        # self-contained transport layout with the very same archive bytes.
        payload = (ROOT / original).read_bytes()
        if sha(payload) != row['archiveSha256']:
            raise ValueError('Historical Java archive drift: ' + original)
        outputs[row['path']] = payload
        with zipfile.ZipFile(ROOT / original) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        destination = str(Path(row['path']).parent.parent)
        outputs.update({destination + '/dist/' + name: value for name, value in files.items()})
        manifest = json.loads(files['package.json'])
        pins = {}
        for prefix, pin in manifest['imports'].items():
            dependency = by_id[pin['packageBlueId']]
            data = (ROOT / dependency['path']).read_bytes()
            if sha(data) != pin['archiveSha256']:
                raise ValueError('Retained Java dependency drift: ' + prefix)
            relative = 'inputs/' + prefix + '.bluepkg'
            outputs[destination + '/' + relative] = data
            pins[prefix] = dict(pin, path=relative)
        outputs[destination + '/blue-package.lock.json'] = wire(dict(format=2, imports=pins))
    scalar = java_inputs / 'blue-mandates-scalar/dist/package.bluepkg'
    scalar_bytes = scalar.read_bytes()
    if sha(scalar_bytes) != 'sha256:80baaf9264eb5f0322c4e96aa89711da20d6c6261868fa2a566da1aeb4ca17d7':
        raise ValueError('Retained Java scalar archive drift')
    destination = 'verification/publications/mandates-scalar-20261001'
    outputs[destination + '/dist/package.bluepkg'] = scalar_bytes
    with zipfile.ZipFile(scalar) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    outputs.update({destination + '/dist/' + name: value for name, value in files.items()})
    manifest = json.loads(files['package.json'])
    pins = {}
    for prefix, pin in manifest['imports'].items():
        row = by_id[pin['packageBlueId']]
        payload = (ROOT / row['path']).read_bytes()
        if sha(payload) != pin['archiveSha256']:
            raise ValueError('Retained scalar dependency drift: ' + prefix)
        relative = 'inputs/' + prefix + '.bluepkg'
        outputs[destination + '/' + relative] = payload
        pins[prefix] = dict(pin, path=relative)
    outputs[destination + '/blue-package.lock.json'] = wire(dict(format=2, imports=pins))
    retained.append(dict(name='blue-mandates', path=destination + '/dist/package.bluepkg',
                         packageBlueId=manifest['packageBlueId'], archiveSha256=sha(scalar_bytes),
                         releaseAsset='blue-mandates-' + manifest['version'] + '-' + manifest['packageBlueId'] + '.bluepkg',
                         selection='retained-java-mandates-scalar-20261001'))
    outputs.update({'SHARED-PACKAGES.json': wire(shared), 'ROOT-CLAUSE-PACKAGES.json': wire(roots),
                    'RETAINED-PACKAGES.json': wire(dict(format='retained-package-selection/1', packages=retained))})
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-source', type=Path, required=True)
    parser.add_argument('--java-inputs', type=Path, required=True, help='Pinned MyOS base vendor/blue-java/packages')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    for name, data in generated(args.python_source.resolve(), args.java_inputs.resolve()).items():
        target = ROOT / name
        if args.write:
            # Existing immutable predecessor files must be byte-identical.
            if name not in ('SHARED-PACKAGES.json', 'ROOT-CLAUSE-PACKAGES.json', 'RETAINED-PACKAGES.json') and target.exists() and target.read_bytes() != data:
                raise ValueError('Refuse retained identity overwrite: ' + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        elif not target.exists() or target.read_bytes() != data:
            raise ValueError('Selection generation drift: ' + name)
    print(json.dumps(dict(status='PASS', wrote=args.write)))


if __name__ == '__main__':
    main()
