#!/usr/bin/env python3
"""Explicitly prepare the 10M BEX/Contracts publication; ordinary builds remain frozen.

Input specifications and source overrides are authored files. This command
recomputes dependent native types, locks, release metadata and the audit map.
It never modifies the preserved gas-100k publication or frozen reference source.
"""
from pathlib import Path
import hashlib
import json
import sys
import subprocess, tempfile, os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blue-contracts/tools'))
import bootstrap
from package_core import Language, Repository, build, read_package, sha, wire
from package_v2 import lock_v2
from blue_contracts.reference.catalogue import publish_catalogue
from algorithms import blue as L
from blue_language.physical import PhysicalCache


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def prepare(name):
    root = ROOT / name
    old = ROOT / 'editions/gas-100k' / name
    prior = json.loads((old / 'release.json').read_text())
    cfg = json.loads((root / 'blue-package.yaml').read_text())
    cfg['version'] = '1.0.0-rc.2'
    spec_path = 'spec/' + ('bex.md' if name == 'blue-bex' else 'contracts.md')
    text = (root / 'SPECIFICATION.md').read_text()
    if name == 'blue-contracts':
        selected = json.loads((ROOT / 'blue-bex/release.json').read_text())
        for key in ('packageBlueId', 'protocolBlueId', 'specificationBlueId'):
            before = json.loads((ROOT / 'editions/gas-100k/blue-bex/release.json').read_text())[key]
            text = text.replace(before, selected[key])
        (root / 'inputs/bex.bluepkg').write_bytes((ROOT / 'blue-bex/dist/package.bluepkg').read_bytes())
        sources = json.loads((root / 'docs/sources.json').read_text())
        sources['bexPackageBlueId'] = selected['packageBlueId']
        sources['bexSpecificationBlueId'] = selected['specificationBlueId']
        write(root / 'docs/sources.json', sources)
    (root / 'SPECIFICATION.md').write_text(text)
    (root / spec_path).write_text(text)
    write(root / 'spec/frozen.json', {spec_path: sha(text.encode())})
    language = Language(core_contracts=False)
    spec = language.create(json.dumps(text))
    language.publish_document(spec)
    types = {}
    if name == 'blue-contracts':
        def admit(raw):
            d = language.admit_definition(json.dumps(raw))
            language.publish_document(d)
            return d.blue_id
        types = publish_catalogue(admit, spec.blue_id, L.CORE)
        repo = Repository.from_payload(name, {'Contracts/' + n: i for n, i in types.items()}, language.provider.snapshot())
        data = (repo._json + '\n').encode()
        (root / 'inputs/catalogue.repository.json').write_bytes(data)
        cfg['inputs'] = [{'path': 'inputs/catalogue.repository.json', 'identity': repo.identity, 'sha256': sha(data)}]
        for n, i in types.items():
            slug = n.lower().replace(' ', '-') + '.blue'
            raw = json.loads(language.verify(i))
            for folder in ('types', 'docs/types'):
                write(root / folder / slug, raw)
    write(root / 'blue-package.yaml', cfg)
    lock_v2(root)
    revision = name + '-2026-10-07-gas-10m-1'
    result = build(root, revision=revision, source_url='')
    for relative, data in {**result.files, 'package.bluepkg': result.archive}.items():
        path = root / 'dist' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    if name == 'blue-contracts':
        # Conformance inputs use the new exact types and the new default policy.
        # Preserve the old fixture in editions/gas-100k, never overwrite its receipt.
        from release import runtime_tree
        with tempfile.TemporaryDirectory(prefix='gas10m-oracle-') as directory:
            src = runtime_tree(Path(directory) / 'src')
            consumer = (root / 'examples/consumer.py').read_text().split('expected=json.loads')[0]
            consumer += "\nprint(json.dumps(dict(authoredBlueId=authored.blue_id, resultBlueId=result.snapshot.documents[result.snapshot.root].blue_id, outcome=result.status, count=1, emitted=p.emitted(result), gas=result.gas, receipt=result.receipt)))\n"
            script = Path(directory) / 'counter.py'
            script.write_text("__file__=" + repr(str(root / 'examples/consumer.py')) + "\n" + consumer)
            env = dict(os.environ, PYTHONPATH=str(src), PYTHONDONTWRITEBYTECODE='1')
            expected = json.loads(subprocess.check_output([sys.executable, str(script)], env=env, cwd=directory))
        fixture = json.loads((root / 'conformance/counter.json').read_text())
        fixture.update(gasLimit=10_000_000, expected=expected)
        write(root / 'conformance/counter.json', fixture)
        result = build(root, revision=revision, source_url='')
        for relative, data in {**result.files, 'package.bluepkg': result.archive}.items():
            path = root / 'dist' / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    release = dict(prior, version=cfg['version'], revision=revision,
                   packageBlueId=result.manifest['packageBlueId'], archiveSha256=result.archive_sha,
                   protocolBlueId=result.manifest['protocol'], specificationBlueId=spec.blue_id,
                   specificationSha256=sha(text.encode()))
    if name == 'blue-contracts':
        release.update(bexPackageBlueId=selected['packageBlueId'], bexProtocolBlueId=selected['protocolBlueId'])
    write(root / 'release.json', release)
    old_types = {e['name']: e['blueId'] for e in json.loads((old / 'dist/package.json').read_text())['exports']}
    write(root / 'migration.json', {'from': prior, 'to': release,
          'types': {n: {'from': old_types[n], 'to': i} for n, i in types.items()}})
    print(name, release['packageBlueId'], flush=True)


if __name__ == '__main__':
    with PhysicalCache(65536).scope():
        prepare('blue-bex')
        prepare('blue-contracts')
