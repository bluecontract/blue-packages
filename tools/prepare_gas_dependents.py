#!/usr/bin/env python3
"""Explicitly rebind authored packages to the 10M native prerequisites.

Old archives remain immutable. The migration maps describe newly authored
content and never instruct a runtime to reinterpret a stored BlueId.
"""
from pathlib import Path
import json, os, shutil, sys, tempfile, zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'blue-contracts/tools'))
import bootstrap
from package_core import Language, MemoryProvider, Repository, read_package, build, wire, sha, source
from package_v2 import lock_v2
from blue_language.physical import PhysicalCache

MAPPING = {}
for project in ('blue-bex','blue-contracts','editions/gas-10m/blue-coordination'):
    m = json.loads((ROOT/project/'migration.json').read_text())
    for key in ('packageBlueId','protocolBlueId','specificationBlueId'):
        MAPPING[m['from'][key]] = m['to'][key]
    for row in m.get('types',{}).values(): MAPPING[row['from']] = row['to']


def replace(value):
    if isinstance(value, dict): return {k:replace(v) for k,v in value.items()}
    if isinstance(value, list): return [replace(v) for v in value]
    return MAPPING.get(value,value) if isinstance(value,str) else value


def references(value):
    if isinstance(value,dict):
        return ({value['blueId']} if set(value)=={'blueId'} else set().union(*(references(v) for v in value.values())))
    if isinstance(value,list): return set().union(*(references(v) for v in value))
    return set()


def portable(value):
    if type(value) is int and abs(value)>(1<<53)-1:return {'type':'Integer','value':str(value)}
    if isinstance(value,dict):return {k:portable(v) for k,v in value.items()}
    if isinstance(value,list):return [portable(v) for v in value]
    return value


def prepare(relative, origin, dependencies, *, archive_only=False):
    project=ROOT/relative; original=ROOT/origin
    if project.is_symlink():
        raise ValueError("Materialize the new edition before authoring through a historical symlink: "+relative)
    if project == original:
        preserved=ROOT/'editions/gas-100k'/relative
        if not preserved.exists():shutil.copytree(project,preserved,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
        original=preserved
    elif not project.exists():shutil.copytree(original,project)
    old=read_package(original/'dist/package.bluepkg')
    oldtypes={e['name']:e['blueId'] for e in old.manifest['exports']}
    cfg=json.loads((original/'blue-package.yaml').read_text())
    cfg['version']=cfg['version'].split('-')[0]+'-gas10m.1'
    dependencies={prefix:next(path for key,path in dependencies.items() if key.lower()==prefix.lower()) for prefix in cfg['imports']}
    selected={prefix:read_package(ROOT/path/'dist/package.bluepkg') for prefix,path in dependencies.items()}
    assert set(selected)==set(cfg['imports']), (relative,set(selected),set(cfg['imports']))
    for prefix,path in dependencies.items():cfg['imports'][prefix]['path']=os.path.relpath(ROOT/path/'dist/package.bluepkg',project)
    with tempfile.TemporaryDirectory(prefix='gas10m-package-') as t:
        stage=Path(t);(stage/'inputs').mkdir()
        language=Language(core_contracts=False)
        for prefix,p in selected.items():
            language.enable_repository(Repository.from_payload('import:'+prefix,{prefix+'/'+e['name']:e['blueId'] for e in p.manifest['exports']},p.repository.records))
        files={cfg['readme'],*cfg.get('files',[])}
        spec_id=None
        if cfg.get('protocol'):
            rule=cfg['protocol']['rules'];files.add(rule)
            raw=(original/rule).read_bytes() if (original/rule).is_file() else old.files[rule]
            text=raw.decode()
            for before,after in MAPPING.items():text=text.replace(before,after)
            text=text.replace('100,000','10,000,000').replace('100000','10000000')
            text+='\nThis edition selects the exact 10M gas prerequisites. Previously published content retains its original semantics.\n'
            d=language.create(json.dumps(text));language.publish_document(d);spec_id=d.blue_id
            prior_spec=old.manifest['semanticSpecifications'][old.manifest['protocol']]['rules']['blueId']
            MAPPING[prior_spec]=spec_id
            dest=stage/rule;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
            (stage/'spec/frozen.json').write_bytes(wire({rule:sha(text.encode())}))
            for rel in (rule,'spec/frozen.json'):
                p=project/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((stage/rel).read_bytes())
        for rel in files:
            if (stage/rel).exists():continue
            raw=(original/rel).read_bytes() if (original/rel).is_file() else old.files[rel]
            text=raw.decode()
            for before,after in MAPPING.items():text=text.replace(before,after)
            dest=stage/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
            out=project/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text)
        # Authored sources are preferred. Preserved archive-only editions export exact definitions.
        old_language=Language(provider=MemoryProvider(old.repository.records),core_contracts=False)
        raws={}
        for entry in cfg['exports']:
            name=entry['name'];path=entry.get('path')
            if not archive_only and path and (original/path).is_file():raw=source((original/path).read_bytes())
            else:raw=json.loads(old_language.verify(oldtypes[name]))
            raws[name]=raw
        pending=list(raws);aliases={}
        while pending:
            progress=False
            for name in list(pending):
                raw=replace(raws[name])
                unresolved=references(raw)&{oldtypes[n] for n in pending if n!=name}
                if unresolved:continue
                if spec_id is not None:raw['specification']={'blueId':spec_id}
                try:d=language.admit_definition(json.dumps(portable(raw)))
                except Exception as error:
                    if 'UnknownAlias' in str(error) or 'unknown alias' in str(error):continue
                    raise RuntimeError(f'{relative}: {name}: {error}') from error
                language.publish_document(d);alias=cfg['namespace']+'/'+name;language.aliases[alias]=d.blue_id;aliases[alias]=d.blue_id
                MAPPING[oldtypes[name]]=d.blue_id
                path=next(e.get('path') for e in cfg['exports'] if e['name']==name)
                if path:
                    f=project/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(wire(portable(raw)))
                pending.remove(name);progress=True
            if not progress:raise ValueError(f'Unresolved definitions: {relative}: {pending}')
        repo=Repository.from_payload(cfg['name'],aliases,language.provider.snapshot());data=(repo._json+'\n').encode();rel='inputs/authored.repository.json';(stage/rel).write_bytes(data)
        staged=json.loads(json.dumps(cfg));staged['inputs']=[{'path':rel,'sha256':sha(data),'identity':repo.identity}]
        staged['exports']=[{'name':e['name'],'fromInput':rel,'inputAlias':cfg['namespace']+'/'+e['name']} for e in cfg['exports']]
        for prefix,p in selected.items():
            path='inputs/'+prefix+'.bluepkg';(stage/path).write_bytes(p.archive);staged['imports'][prefix]['path']=path
        (stage/'blue-package.yaml').write_bytes(wire(staged));pins=lock_v2(stage)
        result=build(stage,revision='gas10m-dependencies-20261007',source_url='')
        for rel,data in {**result.files,'package.bluepkg':result.archive}.items():
            p=project/'dist'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        for prefix,pin in pins['imports'].items():pin['path']=cfg['imports'][prefix]['path']
        (project/'blue-package.lock.json').write_bytes(wire(pins))
        # Persist the exact staged authoring repository/configuration so the frozen
        # package build is reproducible without this migration helper.
        (project/'inputs').mkdir(exist_ok=True)
        (project/'inputs/authored.repository.json').write_bytes((stage/'inputs/authored.repository.json').read_bytes())
        staged['imports'] = cfg['imports']
        (project/'blue-package.yaml').write_bytes(wire(staged))
        MAPPING[old.manifest['packageBlueId']]=result.manifest['packageBlueId']
        if old.manifest['protocol']:MAPPING[old.manifest['protocol']]=result.manifest['protocol']
        migration={'from':{'packageBlueId':old.manifest['packageBlueId'],'protocolBlueId':old.manifest['protocol']},'to':{'packageBlueId':result.manifest['packageBlueId'],'protocolBlueId':result.manifest['protocol'],'specificationBlueId':spec_id,'archiveSha256':result.archive_sha},'types':{n:{'from':oldtypes[n],'to':aliases[cfg['namespace']+'/'+n]} for n in oldtypes}}
        (project/'migration.json').write_bytes(wire(migration))
        # Native-support is host configuration, outside the identified archive.
        support=original/'docs/native-support.json'
        if support.exists():
            values=replace(json.loads(support.read_text()));values['packageId']=result.manifest['packageBlueId'];values['protocolId']=result.manifest['protocol'];values['rulesId']=spec_id
            (project/'docs').mkdir(exist_ok=True);(project/'docs/native-support.json').write_bytes(wire(values))
        print(relative,result.manifest['packageBlueId'],flush=True)
    return result


if __name__=='__main__':
    foundation={'Language':'blue-language','BEX':'blue-bex','Contracts':'blue-contracts'}
    with PhysicalCache(65536).scope():
        prepare('editions/gas-10m/blue-mandates','verification/publications/mandates-before-predicate-context-20260929', {**foundation,'Coordination':'editions/gas-10m/blue-coordination'})
        prepare('editions/gas-10m/blue-time','editions/pre-timeline-provider/blue-time',{**foundation,'Coordination':'editions/gas-10m/blue-coordination'},archive_only=True)
        prepare('blue-coordination','blue-coordination',{'Language':'blue-language','Contracts':'blue-contracts'})
    (ROOT/'editions/gas-10m/mapping.json').write_bytes(wire(MAPPING))
