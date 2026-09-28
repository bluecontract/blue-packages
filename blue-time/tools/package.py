#!/usr/bin/env python3
"""Locked build/verification using the sibling publisher and live Python.
No dependency code is copied into this project.
"""
from __future__ import annotations
import argparse, atexit, importlib.resources, json, os
from pathlib import Path
import subprocess, sys, tempfile, types
ROOT=Path(__file__).resolve().parents[1]
SHARED=ROOT.parent
PYTHON=SHARED.parent/'blue-python'
if (PYTHON/'src').is_dir():sys.path.insert(0,str(PYTHON/'src'))

def setup_publisher():
    """Same isolated standard-data adapter used by build_mandates.py."""
    temp=tempfile.TemporaryDirectory(prefix='blue-time-standard-');atexit.register(temp.cleanup)
    standard=Path(temp.name)/'python/src/registry/standard';standard.mkdir(parents=True)
    for name in ('Package.json','ProtocolSpecification.json'):
        (standard/name).write_bytes(importlib.resources.files('registry').joinpath('standard',name).read_bytes())
    bootstrap=types.ModuleType('bootstrap')
    bootstrap.WORKSPACE=Path(temp.name);bootstrap.ROOT=SHARED/'blue-contracts'
    provenance=json.loads((ROOT/'provenance/source.json').read_text())
    bootstrap.LOCK={'blue':{'archiveSha256':provenance['sourceArchiveSha256']}}
    sys.modules['bootstrap']=bootstrap
    sys.path.insert(0,str(SHARED/'blue-contracts/tools'))

def compile_package(refresh_lock=False):
    setup_publisher()
    from package_core import build,wire,Language,Repository,sha,source,read_package,require
    from blue_language.physical import PhysicalCache
    config=source((ROOT/'blue-package.yaml').read_bytes())
    packages={}
    for prefix,entry in config['imports'].items():
        print('Verifying dependency '+prefix, file=sys.stderr, flush=True)
        packages[prefix]=read_package(ROOT/entry['path'])
    pins={'format':2,'imports':{prefix:{
        'path':config['imports'][prefix]['path'],'packageBlueId':p.manifest['packageBlueId'],
        'archiveSha256':p.archive_sha,'repositoryIdentity':p.repository.identity,
        'name':p.manifest['name'],'version':p.manifest['version']} for prefix,p in packages.items()}}
    if not refresh_lock:
        require(pins==json.loads((ROOT/'blue-package.lock.json').read_text()),
                'Dependency lock mismatch; refresh is an explicit authoring action')
    with tempfile.TemporaryDirectory(prefix='blue-time-build-') as tmp,PhysicalCache(65536).scope():
        stage=Path(tmp)
        names={config['readme'],config['protocol']['rules'],'spec/frozen.json',*config.get('files',[])}
        names.update(row['path'] for row in config['exports'])
        for name in names:
            destination=stage/name;require(destination.resolve().is_relative_to(stage),'Unsafe authored path')
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes((ROOT/name).read_bytes())
        (stage/'inputs').mkdir();stage_pins=json.loads(json.dumps(pins))
        for prefix,entry in config['imports'].items():
            name='inputs/'+prefix+'.bluepkg';(stage/name).write_bytes(packages[prefix].archive)
            entry['path']=name;stage_pins['imports'][prefix]['path']=name
        language=Language(core_contracts=False)
        for prefix,p in packages.items():
            language.enable_repository(Repository.from_payload('import:'+prefix,
                {prefix+'/'+e['name']:e['blueId'] for e in p.manifest['exports']},p.repository.records))
        rules=language.create(wire((stage/config['protocol']['rules']).read_text()).decode(),format='json')
        language.publish_document(rules);aliases={}
        for row in config['exports']:
            alias=config['namespace']+'/'+row['name'];raw=source((stage/row['path']).read_bytes())
            raw['specification']={'blueId':rules.blue_id}
            doc=language.admit_definition(wire(raw).decode(),format='json');language.publish_document(doc)
            language.aliases[alias]=doc.blue_id;aliases[alias]=doc.blue_id
        repository=Repository.from_payload(config['name'],aliases,language.provider.snapshot())
        data=(repository._json+'\n').encode();relative='inputs/authored.repository.json';(stage/relative).write_bytes(data)
        config['inputs']=[{'path':relative,'sha256':sha(data),'identity':repository.identity}]
        config['exports']=[{'name':e['name'],'fromInput':relative,'inputAlias':config['namespace']+'/'+e['name']} for e in config['exports']]
        (stage/'blue-package.yaml').write_bytes(wire(config));(stage/'blue-package.lock.json').write_bytes(wire(stage_pins))
        print('Building and verifying immutable publication',file=sys.stderr,flush=True)
        package=build(stage,revision='blue-time-20260928-preview-1',source_url='')
    return package,pins,rules.blue_id

def write_publication(package,pins,rules):
    expected={**package.files,'package.bluepkg':package.archive};dist=ROOT/'dist'
    if dist.exists():
        actual={p.relative_to(dist).as_posix():p.read_bytes() for p in dist.rglob('*') if p.is_file()}
        if actual!=expected:raise ValueError('Existing publication differs; publish a new revision explicitly')
    else:
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.publish-') as tmp:
            stage=Path(tmp)/'dist'
            for name,data in expected.items():
                path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            os.rename(stage,dist)
    (ROOT/'blue-package.lock.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n')
    selected=[{'name':r['name'],'packageBlueId':r['packageBlueId'],'archiveSha256':r['archiveSha256'],'path':r['path']} for r in pins['imports'].values()]
    selected.append({'name':'blue-time','packageBlueId':package.manifest['packageBlueId'],'archiveSha256':package.archive_sha,'path':'dist/package.bluepkg'})
    manifest={'approvedNativeSupport':False,'packageBlueId':package.manifest['packageBlueId'],
              'protocolBlueId':package.manifest['protocol'],'rulesBlueId':rules,'requiredPackages':selected,
              'exports':{'Time/'+e['name']:e['blueId'] for e in package.manifest['exports']}}
    (ROOT/'docs/integration-selection.json').write_text(json.dumps(manifest,indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('build','check-source','verify','inspect','test','example'))
    parser.add_argument('--refresh-lock',action='store_true');args=parser.parse_args()
    if args.refresh_lock and args.command!='build':parser.error('--refresh-lock is allowed only with build')
    if args.command in ('verify','inspect'):
        from blue_packages.reader import read_package
        p=read_package(ROOT/'dist/package.bluepkg')
        print(json.dumps(p.manifest if args.command=='inspect' else {'verified':True,'packageBlueId':p.blue_id,
              'archiveSha256':p.archive_sha,'exports':list(p.exports),'nativeSupportApproved':False},indent=2))
    elif args.command in ('test','example'):
        env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join(filter(None,[str(PYTHON/'src'),str(ROOT/'tests'),env.get('PYTHONPATH','')]))
        command=([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'] if args.command=='test'
                 else [sys.executable,str(ROOT/'examples/run.py')])
        raise SystemExit(subprocess.call(command,cwd=ROOT,env=env))
    else:
        p,pins,rules=compile_package(args.refresh_lock)
        if args.command=='check-source':
            expected={**p.files,'package.bluepkg':p.archive}
            actual={f.relative_to(ROOT/'dist').as_posix():f.read_bytes() for f in (ROOT/'dist').rglob('*') if f.is_file()}
            if expected!=actual:raise ValueError('Locked sources do not reproduce distribution')
        else:write_publication(p,pins,rules)
        print(json.dumps({'command':args.command,'verified':True,'packageBlueId':p.manifest['packageBlueId'],
              'archiveSha256':p.archive_sha,'rulesBlueId':rules,'nativeSupportApproved':False},indent=2))
if __name__=='__main__':
    from blue_language.physical import PhysicalCache
    with PhysicalCache(131072).scope():
        main()
