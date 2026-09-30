#!/usr/bin/env python3
"""Build four explicitly separate candidates using the target's generic publisher.

No selected publication or runtime registry is changed. Dependencies are exact
bundled archives. Repeat builds must produce identical archive bytes.
"""
from pathlib import Path
from copy import deepcopy
import json, os, sys, tempfile, argparse, hashlib

ROOT=Path(__file__).resolve().parents[1]
NAMES=('blue-agreements','clause-mutual-activation','clause-immediate-termination','agreement-reseller')
REVISION='root-clause-bindings-20260929-1'

def setup(workspace):
 sys.path.insert(0,str(workspace/'blue-language-python/src'))
 sys.path.insert(0,str(workspace/'blue-packages/tools'))
 # Standard data adapter only, using installed runtime; no provenance runtime.
 import build_mandates
 return build_mandates

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,default=Path(os.environ.get('BLUE_SOURCE_WORKSPACE',str(ROOT.parents[2]))))
 p.add_argument('--check',action='store_true');args=p.parse_args(argv);workspace=args.workspace.resolve()
 adapter=setup(workspace)
 from package_core import build,wire,Language,Repository,sha,source,verify_bytes,read_package
 from blue_language.physical import PhysicalCache
 from blue_runtime.core_reuse import core_reuse_scope
 rows=[]
 for name in NAMES:
  project=ROOT/'blue-packages'/name
  cfg=json.loads((project/'blue-package.yaml').read_text())
  with PhysicalCache(65536).scope(),core_reuse_scope():
   deps={prefix:read_package(project/entry['path']) for prefix,entry in cfg['imports'].items()}
   if name=='agreement-reseller':
    path=project/'types/reseller-agreement.blue';raw=source(path.read_bytes())
    raw['clauseTypes']=[next(e['blueId'] for e in deps[prefix].manifest['exports'] if e['name']==alias) for prefix,alias in [('MutualActivation','Mutual Activation Clause'),('ImmediateTermination','Immediate Termination Clause')]]
    if args.check:
     assert source(path.read_bytes()) == raw, 'Reseller clause type pins differ'
    else:
     path.write_text(json.dumps(raw,indent=2)+'\n')
   pins={'format':2,'imports':{prefix:dict(path=cfg['imports'][prefix]['path'],packageBlueId=dep.manifest['packageBlueId'],archiveSha256=dep.archive_sha,repositoryIdentity=dep.repository.identity,name=dep.manifest['name'],version=dep.manifest['version']) for prefix,dep in deps.items()}}
   with tempfile.TemporaryDirectory(prefix='root-clauses-build-') as tmp:
    stage=Path(tmp);(stage/'inputs').mkdir()
    for rel in {cfg['readme'],*cfg.get('files',[]),*(e['path'] for e in cfg['exports'])}:
     dest=stage/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((project/rel).read_bytes())
    stagecfg=deepcopy(cfg);stagepins=deepcopy(pins)
    language=Language(core_contracts=False)
    for prefix,dep in deps.items():
     rel='inputs/'+prefix+'.bluepkg';(stage/rel).write_bytes(dep.archive)
     stagecfg['imports'][prefix]['path']=rel;stagepins['imports'][prefix]['path']=rel
     language.enable_repository(Repository.from_payload('import:'+prefix,{prefix+'/'+e['name']:e['blueId'] for e in dep.manifest['exports']},dep.repository.records))
    aliases={}
    for entry in cfg['exports']:
     alias=cfg['namespace']+'/'+entry['name']
     print('admit',alias,flush=True)
     doc=language.admit_definition(wire(source((stage/entry['path']).read_bytes())).decode(),format='json')
     language.publish_document(doc);language.aliases[alias]=doc.blue_id;aliases[alias]=doc.blue_id
    repo=Repository.from_payload(name,aliases,language.provider.snapshot());raw=(repo._json+'\n').encode();rel='inputs/authored.repository.json';(stage/rel).write_bytes(raw)
    stagecfg['inputs']=[dict(path=rel,sha256=sha(raw),identity=repo.identity)]
    stagecfg['exports']=[dict(name=e['name'],fromInput=rel,inputAlias=cfg['namespace']+'/'+e['name']) for e in cfg['exports']]
    (stage/'blue-package.yaml').write_bytes(wire(stagecfg));(stage/'blue-package.lock.json').write_bytes(wire(stagepins))
    package=build(stage,revision=REVISION,source_url='');verify_bytes(package.archive)
    dist=project/'dist'
    files={**package.files,'package.bluepkg':package.archive}
    if args.check:
     assert all((dist/rel).read_bytes()==raw for rel,raw in files.items()),name+': non-reproducible build'
     assert json.loads((project/'blue-package.lock.json').read_text())==pins
    else:
     for rel,raw in files.items():
      dest=dist/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
     (project/'blue-package.lock.json').write_bytes(wire(pins))
    rows.append(dict(name=name,path=name+'/dist/package.bluepkg',packageBlueId=package.manifest['packageBlueId'],archiveSha256=package.archive_sha,exports=package.manifest['exports'],audit=package.audit))
    print('BUILT',name,package.manifest['packageBlueId'],flush=True)
 if not args.check:
  (ROOT/'verification/candidate-packages.json').write_text(json.dumps(dict(revision=REVISION,packages=rows),indent=2)+'\n')

if __name__=='__main__':main()
