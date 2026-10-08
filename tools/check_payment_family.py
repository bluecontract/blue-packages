#!/usr/bin/env python3
"""Check the current business subset and its exact dependency graph; no publication."""
import json
from pathlib import Path
from release import check_archive

ROOT = Path(__file__).resolve().parents[1]

def check(root=ROOT):
    selection = json.loads((root / 'PAYMENT-FAMILY-PACKAGES.json').read_text())
    source = json.loads((root / 'PACKAGE-SOURCES.json').read_text())
    assert selection['status'] == source['status'] == 'unpublished-candidate'
    assert [row['directory'] for row in selection['packages']] == [p for p in source['packages'] if p != 'blue-mandates']
    assert len({r['namespace'] for r in selection['packages']}) == len(selection['packages'])
    for row in selection['packages']:
        checked, _ = check_archive(root, dict(row, selection='payment-family-candidate'))
        for alias, blue_id in checked['imports'].items():
            assert blue_id == selection['mounts'][alias]['blueId'], f'Mixed candidate editions: {row["namespace"]}/{alias}'
    print(f"Verified {len(selection['packages'])} candidate archives, distributions and dependency locks; nothing published")

if __name__ == '__main__':
    check()
