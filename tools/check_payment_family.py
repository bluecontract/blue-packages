#!/usr/bin/env python3
"""Check the current business subset and its exact dependency graph; no publication."""
import json
from pathlib import Path
from release import check_archive, check_dependency_closure, retained_archives

ROOT = Path(__file__).resolve().parents[1]

def check(root=ROOT):
    selection = json.loads((root / 'PAYMENT-FAMILY-PACKAGES.json').read_text())
    source = json.loads((root / 'PACKAGE-SOURCES.json').read_text())
    assert selection['status'] == source['status'] == 'unpublished-candidate'
    assert [row['directory'] for row in selection['packages']] == [p for p in source['packages'] if p != 'blue-mandates']
    assert len({r['namespace'] for r in selection['packages']}) == len(selection['packages'])
    current_imports = {alias: mount['blueId'] for alias, mount in selection['mounts'].items()}
    retained = retained_archives(root, current_ids=current_imports.values())
    for row in selection['packages']:
        checked, _ = check_archive(root, dict(row, selection='payment-family-candidate'))
        check_dependency_closure(root, checked, current_imports, retained)
    from check_payment_protocol import check as check_protocol
    check_protocol(root)
    print(f"Verified {len(selection['packages'])} candidate archives, distributions and dependency locks; nothing published")

if __name__ == '__main__':
    check()
