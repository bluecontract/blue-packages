#!/usr/bin/env python3
"""Check the current business subset and its exact dependency graph; no publication."""
import json
from pathlib import Path
from release import check_archive, retained_archives, retained_import
import yaml

ROOT = Path(__file__).resolve().parents[1]

def check_import_mount(root, folder, prefix, identity, config, lock, mounts, retained):
    pin = retained_import(root, folder, prefix, lock['imports'][prefix], config, retained)
    if pin is not None:
        source_pin = retained_import(root, folder, prefix, config['imports'][prefix], config, retained)
        assert source_pin == pin and pin['packageBlueId'] == identity, 'Retained source import differs: ' + prefix
        return
    assert identity == mounts[prefix]['blueId'], 'Mixed candidate editions: ' + config['namespace'] + '/' + prefix


def check(root=ROOT):
    selection = json.loads((root / 'PAYMENT-FAMILY-PACKAGES.json').read_text())
    source = json.loads((root / 'PACKAGE-SOURCES.json').read_text())
    assert selection['status'] == source['status'] == 'unpublished-candidate'
    assert [row['directory'] for row in selection['packages']] == [p for p in source['packages'] if p != 'blue-mandates']
    assert len({r['namespace'] for r in selection['packages']}) == len(selection['packages'])
    retained = retained_archives(root)
    for row in selection['packages']:
        checked, _ = check_archive(root, dict(row, selection='payment-family-candidate'))
        folder = root / row['directory']
        config = yaml.safe_load((folder / 'blue-package.yaml').read_text())
        lock = json.loads((folder / 'blue-package.lock.json').read_text())
        for alias, blue_id in checked['imports'].items():
            check_import_mount(root, folder, alias, blue_id, config, lock, selection['mounts'], retained)
    from check_payment_protocol import check as check_protocol
    check_protocol(root)
    print(f"Verified {len(selection['packages'])} candidate archives, distributions and dependency locks; nothing published")

if __name__ == '__main__':
    check()
