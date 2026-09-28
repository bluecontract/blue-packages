"""Build shared data packages in disposable workspaces; no vendored runtimes or input copies."""
from pathlib import Path
import json, shutil, sys, tempfile

ROOT=Path(__file__).resolve().parents[1]
# One existing generic package publisher owns these algorithms. The new packages
# contain only their own Blue definitions, documentation and exact data artifacts.
sys.path.insert(0,str(ROOT/'blue-contracts/tools'))
from package_core import build, read_package, wire, Language, Repository, sha, source as parse_source
from package_v2 import lock_v2
from blue_language.physical import PhysicalCache

def main():
    rows=[]
    for name in ['blue-coordination','blue-agreements','clause-mutual-activation','blue-agreement-examples']:
        source=ROOT/name
        original=json.loads((source/'blue-package.yaml').read_text())
        with tempfile.TemporaryDirectory(prefix='blue-package-build-') as tmp:
            stage=Path(tmp)/name
            shutil.copytree(source,stage,ignore=shutil.ignore_patterns('dist','build','__pycache__'))
            cfg=json.loads(json.dumps(original));(stage/'inputs').mkdir(exist_ok=True)
            for prefix,entry in cfg['imports'].items():
                selected=(source/entry['path']).resolve()
                if not selected.is_relative_to(ROOT):raise ValueError('Dependency must be in shared package home')
                target='inputs/'+prefix+'.bluepkg';shutil.copyfile(selected,stage/target);entry['path']=target
            # The older generic publisher's from_definitions() preloads its
            # default Contracts aliases. Author explicitly with Language only,
            # then pass the admitted exact definitions to its normal verifier.
            if any('path' in entry for entry in cfg['exports']):
                language=Language(core_contracts=False)
                for prefix,entry in cfg['imports'].items():
                    dependency=read_package(stage/entry['path'])
                    aliases={prefix+'/'+e['name']:e['blueId'] for e in dependency.manifest['exports']}
                    language.enable_repository(Repository.from_payload('import:'+prefix,aliases,dependency.repository.records))
                aliases={}
                for entry in cfg['exports']:
                    alias=cfg['namespace']+'/'+entry['name']
                    document=language.admit_definition(wire(parse_source((stage/entry['path']).read_bytes())).decode(),format='json')
                    language.publish_document(document);language.aliases[alias]=document.blue_id;aliases[alias]=document.blue_id
                repository=Repository.from_payload(cfg['name'],aliases,language.provider.snapshot())
                data=(repository._json+'\n').encode();relative='inputs/authored.repository.json'
                (stage/relative).write_bytes(data)
                cfg['inputs']=[{'path':relative,'sha256':sha(data),'identity':repository.identity}]
                cfg['exports']=[{'name':e['name'],'fromInput':relative,'inputAlias':cfg['namespace']+'/'+e['name']} for e in cfg['exports']]
            (stage/'blue-package.yaml').write_bytes(wire(cfg))
            pins=lock_v2(stage)
            with PhysicalCache(65536).scope():
                package=build(stage,revision='shared-agreements-20260927-2',source_url='')
                checked=read_package_bytes(package)
            dist=source/'dist';dist.mkdir(exist_ok=True)
            for relative,data in package.files.items():
                dest=dist/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            (dist/'package.bluepkg').write_bytes(package.archive)
            for prefix in pins['imports']:pins['imports'][prefix]['path']=original['imports'][prefix]['path']
            (source/'blue-package.lock.json').write_bytes(wire(pins))
            row={'name':name,'path':name+'/dist/package.bluepkg','packageBlueId':package.manifest['packageBlueId'],
                 'archiveSha256':package.archive_sha,'exports':package.manifest['exports'],
                 'protocolBlueId':package.manifest['protocol'],'audit':package.audit}
            rows.append(row);print(name,row['packageBlueId'],flush=True)
    (ROOT/'AGREEMENTS-PACKAGES.json').write_bytes(wire({'format':'blue-shared-agreements/1','packages':rows}))

def read_package_bytes(package):
    from package_core import verify_bytes
    return verify_bytes(package.archive)

if __name__=='__main__':
    with PhysicalCache(65536).scope():main()
