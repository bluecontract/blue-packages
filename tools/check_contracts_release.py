#!/usr/bin/env python3
"""Check Contracts 1.1.0 pins and the three real default corpus outputs.

SDK receipts must match completely. MyOS has a native dispatch binding; report
its different commitments explicitly, and compare complete document metadata,
events, gas and failure behavior. Never label the native receipts byte-equal.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile
from check_determinism import difference

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'releases/contracts-1.1.0'

def read(path):
    return json.loads(path.read_text())

def sha(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()

def no_charge_trace(value):
    if isinstance(value, dict):
        assert not ({'gasTrace', 'workSegment'} & value.keys()), 'Accepted charge history in compact result'
        for child in value.values(): no_charge_trace(child)
    elif isinstance(value, list):
        for child in value: no_charge_trace(child)

def check(args):
    pins = read(RELEASE/'selection.json')
    data = (RELEASE/'package.bluepkg').read_bytes()
    assert sha(data) == pins['archiveSha256']
    for path in (args.python/'src/blue_packages/resources/releases/contracts-1.1.0.bluepkg',
                 args.java/'blue-contracts-core/src/main/resources/contracts/1.1.0/package.bluepkg',
                 args.myos/'runtime/blue-contracts-core/src/main/resources/contracts/1.1.0/package.bluepkg'):
        assert path.read_bytes() == data, 'Different release copy: '+str(path)
    assert read(args.python/'src/blue_packages/contracts-release.json') == pins
    with zipfile.ZipFile(RELEASE/'package.bluepkg') as archive:
        rules = archive.read(pins['rulesPath'])
        assert rules == (RELEASE/'SPECIFICATION.md').read_bytes()
        assert sha(rules) == 'sha256:'+pins['specificationSha256']
        modules = {name:(body.rstrip('\n')+'\n').encode() for name,body in re.findall(
            r'### `([^`]+)`\n\n```python\n(.*?)\n```',rules.decode(),re.S)}
        sources = json.loads(archive.read('docs/sources.json'))
        assert {name:sha(body)[7:] for name,body in modules.items()} == sources['modules']
        assert modules['src/blue_contracts/reference/work.py'] == (args.python/'src/blue_contracts/reference/work.py').read_bytes()
    sdk, java, native = [read(path) for path in (args.python_run,args.java_run,args.myos_run)]
    error = difference(sdk,java)
    assert error is None, 'Python/Java: '+str(error)
    for run in (sdk,java,native):
        assert run['selection']['profile'] == pins['gasProfile']
        assert run['selection']['contractsPackage'] == pins['packageBlueId']
        assert run['selection']['contractsRules'] == pins['specificationBlueId']
        assert run['selection']['contractsProtocol'] == pins['protocol']
        assert run['selection']['gasProfile'] == pins['gasProfile']
        no_charge_trace(run)
    corpus = read(ROOT/'conformance/determinism/cases.json')
    differing,observations,snapshots=set(),set(),set()
    count=0
    for case in corpus['cases']:
        rows=sdk[case['id']]; others=native[case['id']]
        assert len(rows)==len(others)
        full=next(row for row in rows if row['budget']==100000)
        gas=full['observations']['gas']
        for run_rows in (rows,others):
            exact=next(row for row in run_rows if row['budget']==gas)
            below=next(row for row in run_rows if row['budget']==gas-1)
            assert exact['observations']['status']==full['observations']['status']
            assert below['observations']['status']=='GAS_LIMIT_EXCEEDED'
            assert below['before']==below['after'] and below['emitted']==[]
        for row,other in zip(rows,others):
            count+=1
            differing.update(k for k in row if row[k]!=other[k])
            observations.update(k for k in row['observations'] if row['observations'][k]!=other['observations'][k])
            snapshots.update(k for k in row['snapshot'] if row['snapshot'][k]!=other['snapshot'][k])
            for key in ('budget','documentBlueId','emitted','value'):
                assert difference(row[key],other[key]) is None, case['id']+': '+key
            # The whole semantic state is compared; only the explicit native
            # implementation declaration differs, and is retained in the report.
            for key in row['snapshot']:
                if key!='runtimes': assert difference(row['snapshot'][key],other['snapshot'][key]) is None, case['id']+': snapshot/'+key
            for key in ('status','gas','rejected','diagnostic','publicEvents','events','changes','checkpoints','completions','rounds','units'):
                assert difference(row['observations'][key],other['observations'][key]) is None, case['id']+': '+key
    for key in ('selection','merge','graph','privateDigest','firstError'):
        assert difference(sdk[key],native[key]) is None, key
    example=corpus['cases'][0]['id']
    return dict(status='PASS_SCOPED',fixtures=len(corpus['cases']),outcomes=count,
        release=pins,pythonJava='Complete recursive JSON equality, including receipts and snapshots',
        nativeComparison='Complete document metadata/state, events, gas, status, rejection, checkpoints and completion observations match; native commitments differ',
        differentNativeFields=sorted(differing),differentNativeObservationFields=sorted(observations),
        differentNativeSnapshotFields=sorted(snapshots),
        sdkRuntimeBindings=sdk[example][0]['snapshot']['runtimes'],
        myosRuntimeBindings=native[example][0]['snapshot']['runtimes'],
        runs={name:dict(file=path.name,sha256=sha(path.read_bytes())) for name,path in
              [('python',args.python_run),('java',args.java_run),('myos',args.myos_run)]},
        limitation='Different installed runtime bindings commit different snapshot/invocation/work/receipt identities. This is not three-way byte-identical receipt qualification or production qualification.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('python','java','myos','python-run','java-run','myos-run','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();result=check(args)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS:',result['fixtures'],'fixtures;',result['outcomes'],'outcomes; exact SDK receipts, scoped native parity')
