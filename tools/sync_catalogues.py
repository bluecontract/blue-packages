#!/usr/bin/env python3
"""Generate consumer views from the single current package catalogue."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def views(root=ROOT):
    catalogue=json.loads((root/'PACKAGES.json').read_text())
    sources=json.loads((root/'PACKAGE-SOURCES.json').read_text())
    rows=catalogue['packages']
    assert [r['directory'] for r in rows] == sources['foundations'] + sources['packages']
    shared=dict(format='blue-shared-packages/1', generatedFrom='PACKAGES.json', packages=[
        {key:r[key] for key in ('name','path','packageBlueId','archiveSha256')} for r in rows])
    business=[r for r in rows if r['directory'] in sources['packages'] and r['directory']!='blue-mandates']
    family=dict(format='blue-payment-family/1', status='unpublished-candidate', generatedFrom='PACKAGES.json',
                packages=business, mounts={k:v for k,v in catalogue['mounts'].items() if k != 'Mandates'})
    return {'SHARED-PACKAGES.json':shared, 'PAYMENT-FAMILY-PACKAGES.json':family}

def sync(root=ROOT, check=False):
    for name, value in views(root).items():
        path=root/name
        if check:
            assert json.loads(path.read_text())==value, f'Stale generated catalogue: {name}'
        else:
            path.write_text(json.dumps(value, indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    sync(check=parser.parse_args().check)
