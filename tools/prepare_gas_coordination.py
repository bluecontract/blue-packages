#!/usr/bin/env python3
"""Publish native Coordination against the explicitly authored 10M edition."""
from pathlib import Path
import json,hashlib,sys,shutil,tempfile,os,zipfile
H=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(H/'blue-contracts/tools'))
import bootstrap
from package_core import Language,Repository,build,read_package,wire,sha
from package_v2 import lock_v2
from blue_repository.prepare import prepare
from blue_language.physical import PhysicalCache
OLD=H/'editions/pre-timeline-provider/blue-coordination'; R=H/'editions/gas-10m/blue-coordination'
if not R.exists():shutil.copytree(OLD,R)
with zipfile.ZipFile(OLD/'dist/package.bluepkg') as z:
 oldcat=json.loads(z.read('docs/catalogue.json'));text=z.read('spec/coordination.md').decode()
 for name in z.namelist():
  if name.startswith('docs/'):
   p=R/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(z.read(name))
# Explicitly rebind exact dependencies in a new edition; never rewrite preserved objects.
for layer in ('blue-bex','blue-contracts'):
 migration=json.loads((H/layer/'migration.json').read_text())
 for key in ('packageBlueId','protocolBlueId','specificationBlueId'):
  text=text.replace(migration['from'][key],migration['to'][key])
text=text.replace('100,000','10,000,000').replace('100000','10000000')
text+='\n## Gas edition\n\nThis edition selects the 10,000,000-gas default and maximum of its exact Contracts prerequisite. Gas tariffs, scheduling, authority and history semantics are unchanged. Previously published histories retain their original dependency selection.\n'
(R/'spec').mkdir(exist_ok=True);(R/'spec/coordination.md').write_text(text);(R/'spec/frozen.json').write_bytes(wire({'spec/coordination.md':sha(text.encode())}))
cfg=json.loads((R/'blue-package.yaml').read_text());cfg['version']='0.1.0-gas10m.1'
language=Language(core_contracts=False)
deps={}
for prefix,entry in cfg['imports'].items():
 target=H/('blue-language' if prefix=='Language' else 'blue-contracts')/'dist/package.bluepkg'
 entry['path']=os.path.relpath(target,R);p=read_package(target);deps[prefix]=p
 language.enable_repository(Repository.from_payload('import:'+prefix,{prefix+'/'+e['name']:e['blueId'] for e in p.manifest['exports']},p.repository.records))
spec=language.create(json.dumps(text));language.publish_document(spec)
sources=oldcat['sources'];remaining=set(sources);aliases={}
def needs(v):
 if isinstance(v,dict):return {x for k,x in v.items() if k in ('type','itemType','keyType','valueType') and isinstance(x,str)}|set().union(*(needs(x) for x in v.values()))
 if isinstance(v,list):return set().union(*(needs(x) for x in v))
 return set()
def portable(v):
 if type(v) is int and abs(v)>(1<<53)-1:return {'type':'Integer','value':str(v)}
 if isinstance(v,dict):return {k:portable(x) for k,x in v.items()}
 if isinstance(v,list):return [portable(x) for x in v]
 return v
with PhysicalCache(65536).scope():
 while remaining:
  ready=sorted(n for n in remaining if not needs(sources[n])&remaining)
  assert ready,remaining
  for name in ready:
   raw=dict(sources[name]);raw['specification']={'blueId':spec.blue_id}
   d=language.admit_definition(json.dumps(portable(raw)));language.publish_document(d)
   language.aliases[name]=d.blue_id;aliases[name]=d.blue_id;remaining.remove(name)
 repo=Repository.from_payload('coordination-gas10m',aliases,language.provider.snapshot(),metadata={'specification':spec.blue_id,'contracts':json.loads((H/'blue-contracts/release.json').read_text())['specificationBlueId']})
 data=(repo._json+'\n').encode();(R/'inputs').mkdir(exist_ok=True);(R/'inputs/catalogue.repository.json').write_bytes(data)
 cfg['inputs']=[{'path':'inputs/catalogue.repository.json','identity':repo.identity,'sha256':sha(data)}]
 artifact,digest=prepare(repo)
 (R/'docs/coordination.prepared.json').write_bytes(artifact)
 (R/'docs/catalogue.json').write_bytes(wire({'contracts':repo.metadata['contracts'],'sources':sources,'specification':spec.blue_id,'types':aliases}))
 (R/'blue-package.yaml').write_bytes(wire(cfg))
 with tempfile.TemporaryDirectory() as t:
  st=Path(t);shutil.copytree(R,st,dirs_exist_ok=True)
  for prefix,p in deps.items():
   cfg['imports'][prefix]['path']='inputs/'+prefix+'.bluepkg';(st/cfg['imports'][prefix]['path']).write_bytes(p.archive)
  (st/'blue-package.yaml').write_bytes(wire(cfg));pins=lock_v2(st)
  p=build(st,revision='coordination-gas10m-20261007',source_url='')
  for name,data in {**p.files,'package.bluepkg':p.archive}.items():
   f=R/'dist'/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
  for prefix,pin in pins['imports'].items():pin['path']=os.path.relpath(H/('blue-language' if prefix=='Language' else 'blue-contracts')/'dist/package.bluepkg',R)
  (R/'blue-package.lock.json').write_bytes(wire(pins))
 old=json.loads((OLD/'dist/package.json').read_text())
 (R/'migration.json').write_bytes(wire({'from':{'packageBlueId':old['packageBlueId'],'protocolBlueId':old['protocol'],'specificationBlueId':oldcat['specification']},'to':{'packageBlueId':p.manifest['packageBlueId'],'protocolBlueId':p.manifest['protocol'],'specificationBlueId':spec.blue_id,'archiveSha256':p.archive_sha},'types':{n:{'from':oldcat['types'][n],'to':i} for n,i in aliases.items()}}))
 print(p.manifest['packageBlueId'],p.manifest['protocol'],spec.blue_id,flush=True)
