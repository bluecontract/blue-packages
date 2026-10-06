#!/usr/bin/env python3
"""Reproduce the selected timeline-dependent data packages; no native approval implied."""
from pathlib import Path
import argparse,json,os,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
# The launcher pins the same reference implementation used for the selected publications.
if os.environ.get('BLUE_TIMELINE_BUILD_RUNTIME')!='1':
    with tempfile.TemporaryDirectory(prefix='timeline-package-runtime-') as tmp:
        runtime=Path(tmp)/'src'
        subprocess.run([sys.executable,'-B',str(ROOT/'blue-contracts/tools/release.py'),'runtime-copy',str(runtime)],check=True,stdout=subprocess.DEVNULL)
        env=dict(os.environ,PYTHONPATH=str(runtime),BLUE_PACKAGES_DIR=str(ROOT),BLUE_TIMELINE_BUILD_RUNTIME='1')
        raise SystemExit(subprocess.call([sys.executable,'-B',__file__,*sys.argv[1:]],env=env))
sys.path.insert(0,str(ROOT/'blue-coordination/tools'))
import package as pub
from blue_language.physical import PhysicalCache
from blue_runtime.core_reuse import core_reuse_scope
NAMES=['blue-agreements','clause-mutual-activation','clause-immediate-termination','agreement-reseller','blue-mutual-activation','blue-agreement-examples','blue-time']

def compile_package(name):
    project=ROOT/name;cfg=json.loads((project/'blue-package.yaml').read_text())
    deps={prefix:pub.read_package((project/item['path']).resolve()) for prefix,item in cfg['imports'].items()}
    pins={'format':2,'imports':{prefix:{'path':cfg['imports'][prefix]['path'],'packageBlueId':p.manifest['packageBlueId'],'archiveSha256':p.archive_sha,'repositoryIdentity':p.repository.identity,'name':p.manifest['name'],'version':p.manifest['version']} for prefix,p in deps.items()}}
    pub.require(pins==json.loads((project/'blue-package.lock.json').read_text()),'Dependency pins changed')
    with tempfile.TemporaryDirectory(prefix='timeline-consumer-build-') as tmp:
        stage=Path(tmp);names={cfg['readme'],*cfg.get('files',[])}
        if cfg.get('protocol') and cfg['protocol'].get('rules'):names|={cfg['protocol']['rules'],'spec/frozen.json'}
        for f in names:
            dest=stage/f;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((project/f).read_bytes())
        (stage/'inputs').mkdir();language=pub.Language(core_contracts=False)
        for prefix,p in deps.items():language.enable_repository(pub.Repository.from_payload('import:'+prefix,{prefix+'/'+x['name']:x['blueId'] for x in p.manifest['exports']},p.repository.records))
        if cfg.get('protocol') and cfg['protocol'].get('rules'):
            d=language.create(json.dumps((project/cfg['protocol']['rules']).read_text()),format='json');language.publish_document(d)
        aliases={}
        for ex in cfg['exports']:
            raw=pub.source((project/ex['path']).read_bytes());d=language.admit_definition(json.dumps(raw),format='json');language.publish_document(d)
            alias=cfg['namespace']+'/'+ex['name'];language.aliases[alias]=d.blue_id;aliases[alias]=d.blue_id
        repo=pub.Repository.from_payload(cfg['name'],aliases,language.provider.snapshot());data=(repo._json+'\n').encode();rel='inputs/authored.repository.json';(stage/rel).write_bytes(data)
        cfg['inputs']=[{'path':rel,'sha256':pub.sha(data),'identity':repo.identity}]
        cfg['exports']=[{'name':x['name'],'fromInput':rel,'inputAlias':cfg['namespace']+'/'+x['name']} for x in cfg['exports']]
        stagepins=json.loads(json.dumps(pins))
        for prefix,p in deps.items():
            path='inputs/'+prefix+'.bluepkg';(stage/path).write_bytes(p.archive);cfg['imports'][prefix]['path']=path;stagepins['imports'][prefix]['path']=path
        (stage/'blue-package.yaml').write_bytes(pub.wire(cfg));(stage/'blue-package.lock.json').write_bytes(pub.wire(stagepins))
        result=pub.build(stage,revision='coordination-provider-migration-20261006',source_url='');pub.verify_bytes(result.archive)
        return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['check','build']);p.add_argument('--package',choices=NAMES);a=p.parse_args()
    with PhysicalCache(65536).scope(),core_reuse_scope():
        for name in [a.package] if a.package else NAMES:
            result=compile_package(name);expected={**result.files,'package.bluepkg':result.archive};dist=ROOT/name/'dist'
            if a.command=='check':
                actual={x.relative_to(dist).as_posix():x.read_bytes() for x in dist.rglob('*') if x.is_file()}
                pub.require(actual==expected,'Source-to-distribution mismatch: '+name)
            else:
                for relative,data in expected.items():
                    out=dist/relative;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
            print(name,result.manifest['packageBlueId'],flush=True)
if __name__=='__main__':main()
