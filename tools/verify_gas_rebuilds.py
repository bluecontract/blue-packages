#!/usr/bin/env python3
"""Reproduce 10M data packages from frozen inputs, without editing publications.

The generic builder intentionally forbids parent paths. This repository adapter
stages only declared files and exact locked dependency archives into a temporary
package root, just like the BEX/Contracts release adapters.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blue-contracts/tools'))
import bootstrap
from package_core import build, read_package, wire
from package_v2 import lock_v2
from blue_language.physical import PhysicalCache
from blue_runtime.core_reuse import core_reuse_scope


def verify(relative):
    root = (ROOT / relative).resolve()
    if not root.is_relative_to(ROOT):
        raise ValueError('Package outside this repository')
    cfg = json.loads((root / 'blue-package.yaml').read_text())
    pins = json.loads((root / 'blue-package.lock.json').read_text())['imports']
    files = {cfg['readme'], *cfg.get('files', [])}
    files.update(row['path'] for row in cfg.get('inputs', []))
    files.update(row['path'] for row in cfg['exports'] if 'path' in row)
    if cfg.get('protocol'):
        files.update((cfg['protocol']['rules'], 'spec/frozen.json'))
    with tempfile.TemporaryDirectory(prefix='blue-gas-rebuild-') as name:
        stage = Path(name)
        for path in files:
            source = (root / path).resolve()
            if not source.is_relative_to(root):
                raise ValueError('Declared file outside its package')
            target = stage / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for prefix, entry in cfg['imports'].items():
            source = (root / entry['path']).resolve()
            if not source.is_relative_to(ROOT):
                raise ValueError('Dependency outside this repository')
            package = read_package(source)
            pin = pins[prefix]
            if (package.manifest['packageBlueId'] != pin['packageBlueId'] or
                    'sha256:' + hashlib.sha256(source.read_bytes()).hexdigest() != pin['archiveSha256']):
                raise ValueError('Dependency differs from lock: ' + prefix)
            entry['path'] = 'inputs/' + prefix + '.bluepkg'
            target = stage / entry['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        (stage / 'blue-package.yaml').write_bytes(wire(cfg))
        lock_v2(stage)
        result = build(stage, revision='gas10m-dependencies-20261007', source_url='')
        if result.archive != (root / 'dist/package.bluepkg').read_bytes():
            raise ValueError('Rebuilt archive differs: ' + relative)
        print('PASS exact rebuild', relative, result.manifest['packageBlueId'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packages', nargs='+')
    args = parser.parse_args()
    with PhysicalCache(131072).scope(), core_reuse_scope():
        for relative in args.packages:
            verify(relative)
