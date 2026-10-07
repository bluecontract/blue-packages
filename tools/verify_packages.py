#!/usr/bin/env python3
"""Verify the shared inventory with the installed Blue Python reader (read-only)."""
import hashlib
import json
import re
from pathlib import Path
from blue_packages import PackageStore
from release import selections
from blue_language.physical import PhysicalCache
from blue_runtime.core_reuse import core_reuse_scope

ROOT = Path(__file__).resolve().parents[1]

def verify_authoring_overrides(directory, package):
    """Only the exact sources embedded in the new specification may live here."""
    folder=directory/'reference'
    if not folder.exists():return
    expected={
        'blue-bex': {'reference/gas.py','reference/runtime.py'},
        'blue-contracts': {'reference/model.py','reference/processor.py','reference/GAS_MANIFEST.json'},
    }
    name=package.manifest['name']
    assert name in expected, 'Unexpected embedded reference tree: '+str(directory)
    actual={p.relative_to(directory).as_posix() for p in folder.rglob('*') if p.is_file()}
    assert actual==expected[name], 'Unexpected authoring override files'
    source=json.loads(package.files['docs/sources.json'])
    declared={**source.get('overrides',{}), **source.get('resourceOverrides',{})}
    assert set(declared.values())==actual, 'Unbound authoring override'
    spec=package.files['spec/'+('bex' if name=='blue-bex' else 'contracts')+'.md'].decode()
    for original,relative in declared.items():
        data=(directory/relative).read_bytes()
        if relative.endswith('.py'):
            assert hashlib.sha256(data).hexdigest()==source['modules'][original].removeprefix('sha256:')
            assert '```python\n'+data.decode().rstrip()+'\n```' in spec, 'Code differs from identified specification'
        else:
            value=json.loads(data)
            blocks=[]
            for block in re.findall(r'```json\n(.*?)```',spec,re.S):
                try:blocks.append(json.loads(block))
                except ValueError:pass
            assert value in blocks, 'Gas manifest differs from identified specification'
            assert value['sharedMaximum']==10_000_000

def main():
    inventory=json.loads((ROOT/'SHARED-PACKAGES.json').read_text())
    from blue_packages.reader import read_package
    selected=PackageStore(ROOT)
    assert {r['name']:r for r in inventory['packages']} == selected._entries, 'Consumer/shared selection differs'
    from blue_coordination.engine.mandate_package import supported_definition
    assert json.loads((ROOT/'editions/gas-10m/blue-mandates/docs/native-support.json').read_text()) == supported_definition(True), 'Native approval differs'
    checked=[]
    for row in selections(ROOT):
        package=read_package(ROOT/row['path'])
        assert package.blue_id==row['packageBlueId'], row['name']
        assert package.archive_sha==row['archiveSha256'], row['name']
        directory=(ROOT/row['path']).parent.parent
        assert not (directory/'runtime').exists(), directory
        verify_authoring_overrides(directory, package)
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
