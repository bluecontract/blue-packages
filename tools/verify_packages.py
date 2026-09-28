#!/usr/bin/env python3
"""Verify the shared inventory with the installed Blue Python reader (read-only)."""
import hashlib
import json
from pathlib import Path
from blue_packages import PackageStore
from release import selections
from blue_language.physical import PhysicalCache
from blue_runtime.core_reuse import core_reuse_scope

ROOT = Path(__file__).resolve().parents[1]

def main():
    inventory=json.loads((ROOT/'SHARED-PACKAGES.json').read_text())
    from blue_packages.reader import read_package
    selected=PackageStore(ROOT)
    assert {r['name']:r for r in inventory['packages']} == selected._entries, 'Consumer/shared selection differs'
    from blue_coordination.engine.mandate_package import supported_definition
    assert json.loads((ROOT/'blue-mandates/docs/native-support.json').read_text()) == supported_definition(), 'Native approval differs'
    checked=[]
    for row in selections(ROOT):
        package=read_package(ROOT/row['path'])
        assert package.blue_id==row['packageBlueId'], row['name']
        assert package.archive_sha==row['archiveSha256'], row['name']
        directory=(ROOT/row['path']).parent.parent
        assert not (directory/'runtime').exists(), directory
        assert not (directory/'reference').exists(), directory
        # Every current package keeps an exact unpacked distribution.
        dist=directory/'dist'
        expected={**package.files,'package.bluepkg':(ROOT/row['path']).read_bytes()}
        actual={p.relative_to(dist).as_posix():p.read_bytes() for p in dist.rglob('*') if p.is_file()}
        assert actual==expected, row['name']+' unpacked distribution differs'
        checked.append({'name':row['name'],'packageBlueId':package.blue_id,'archiveSha256':package.archive_sha})
    reference_count=0
    for root in (ROOT/'verification/reference').iterdir():
        lock=json.loads((root/'SOURCE-LOCK.json').read_text())
        for name,digest in lock['files'].items():
            assert hashlib.sha256((root/'python'/name).read_bytes()).hexdigest()==digest, name
            reference_count+=1
    print(json.dumps({'verified':True,'packages':checked,'historicalReferenceFiles':reference_count},indent=2))

if __name__=='__main__':
    with PhysicalCache(131072).scope(), core_reuse_scope():
        main()
