#!/usr/bin/env python3
"""Rebuild unchanged Core-authored application sources against Contracts 1.1.0.

The source snapshot is retained separately from all prior publications. Importing
it is an explicit authoring step; ordinary builds/checks require no Git/network.
"""
import argparse, hashlib, json, os, re, shutil, subprocess, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'releases/contracts-1.1.0'
HOME=RELEASE/'catalogue'
SOURCE='8e074c9bd1e1a8a2154aa41988b18a94a4dde218'

def read(p): return json.loads(p.read_text())
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(data):return 'sha256:'+hashlib.sha256(data).hexdigest()
def original(path):return subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT)
def import_sources():
 assert not HOME.exists(), 'Source import is exclusive; never overwrite an existing snapshot'
 inventory=json.loads(original('PACKAGE-SOURCES.json'));inventory['runtimeProfile']='blue-contracts/1.1.0'
 write(HOME/'PACKAGE-SOURCES.json',inventory)
 source_hashes={}
 for name in inventory['foundations']+inventory['packages']:
  import yaml
  cfg=yaml.safe_load(original(name+'/blue-package.yaml'))
  files={'blue-package.yaml','README.md',*(r['path'] for r in cfg.get('exports',[])),*cfg.get('files',[])}
  if 'protocol' in cfg:files.update([cfg['protocol']['rules'],'spec/frozen.json'])
  for rel in files:
   data=original(name+'/'+rel);target=HOME/name/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
   if rel!='blue-package.yaml':source_hashes[name+'/'+rel]=sha(data)
  if name=='blue-contracts':
   cfg.update(version='1.1.0');cfg['protocol']['name']='Blue Contracts 1.1.0';cfg['protocol']['rules']='spec/contracts-1.1.0.md'
   shutil.copyfile(RELEASE/'SPECIFICATION.md',HOME/name/cfg['protocol']['rules'])
   write(HOME/name/'spec/frozen.json',{cfg['protocol']['rules']:sha((RELEASE/'SPECIFICATION.md').read_bytes())})
   shutil.copyfile(RELEASE/'sources.json',HOME/name/'docs/sources.json');shutil.copyfile(RELEASE/'README.md',HOME/name/'README.md')
   source_hashes={k:v for k,v in source_hashes.items() if not k.startswith(name+'/')}
  elif name not in ('blue-language','blue-bex'):
   a,b,c=map(int,re.match(r'(\d+)\.(\d+)\.(\d+)',cfg['version']).groups());cfg['version']=f'{a}.{b}.{c+1}'
  write(HOME/name/'blue-package.yaml',cfg)
 for name in ('BuildFinalGas.java','BuildPaymentFamily.java','OperationInputs.java'):
  data=original('tools/'+name);target=HOME/'tools'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);source_hashes['tools/'+name]=sha(data)
 write(HOME/'SOURCE.json',dict(repository='bluecontract/blue-packages',commit=SOURCE,
       scope='Exact current Core authored sources; only package versions and dependency bindings change',unchangedFiles=source_hashes))

def build(check):
 inventory=read(HOME/'PACKAGE-SOURCES.json');names=inventory['foundations']+inventory['packages']
 for rel,digest in read(HOME/'SOURCE.json')['unchangedFiles'].items():
  assert sha((HOME/rel).read_bytes())==digest, 'Authored source changed: '+rel
 cp=os.environ['BLUE_JAVA_CLASSPATH'];java=Path(os.environ['JAVA_HOME'])/'bin'
 with tempfile.TemporaryDirectory(prefix='contracts-catalogue-') as tmp:
  stage=Path(tmp)/'packages';shutil.copytree(HOME,stage,ignore=shutil.ignore_patterns('dist','blue-package.lock.json'))
  classes=Path(tmp)/'classes';classes.mkdir()
  subprocess.run([str(java/'javac'),'-cp',cp,'-d',str(classes),str(HOME/'tools/BuildFinalGas.java'),str(HOME/'tools/BuildPaymentFamily.java'),str(HOME/'tools/OperationInputs.java')],check=True)
  manifests={};ordered=[];active=set()
  def visit(name):
   if name in ordered:return
   assert name not in active, 'Dependency cycle'
   active.add(name);cfg=read(stage/name/'blue-package.yaml')
   for imp in cfg.get('imports',{}).values():visit((stage/name/imp['path']).resolve().parent.parent.name)
   active.remove(name);ordered.append(name)
  for name in names:visit(name)
  for name in ordered:
   folder=stage/name
   if name in ('blue-language','blue-bex','blue-contracts'):
    source=RELEASE/'package.bluepkg' if name=='blue-contracts' else ROOT/name/'dist/package.bluepkg'
    (folder/'dist').mkdir();shutil.copyfile(source,folder/'dist/package.bluepkg')
    with zipfile.ZipFile(source) as z:m=json.loads(z.read('package.json'))
    write(folder/'dist/package.json',m)
    # Exact pins for the importer, without rebuilding immutable foundations.
    cfg=read(folder/'blue-package.yaml');locks={}
    for alias,imp in cfg.get('imports',{}).items():
     archive=folder/imp['path']
     with zipfile.ZipFile(archive) as z:dep=json.loads(z.read('package.json'))
     locks[alias]=dict(path=imp['path'],packageBlueId=dep['packageBlueId'],archiveSha256=sha(archive.read_bytes()),name=dep['name'],version=dep['version'])
    write(folder/'blue-package.lock.json',dict(format=2,imports=locks))
   else:
    subprocess.run([str(java/'java'),'-Xmx1500m','-cp',str(classes)+os.pathsep+cp,'BuildFinalGas',str(stage),name],check=True,stdout=subprocess.DEVNULL)
   manifests[name]=read(folder/'dist/package.json')
   for rel in ('dist/package.bluepkg','dist/package.json','blue-package.lock.json'):
    destination=HOME/name/rel;data=(folder/rel).read_bytes()
    if check:assert destination.read_bytes()==data,'Nonreproducible '+name+'/'+rel
    else:destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
  # Native releases must be identical to the independently built pinned copies.
  for name in ('blue-coordination','blue-time','blue-mandates'):
   assert (stage/name/'dist/package.bluepkg').read_bytes()==(RELEASE/'native'/name/'package.bluepkg').read_bytes(), 'Native source mismatch: '+name
  rows=[dict(name=m['name'],namespace=read(stage/n/'blue-package.yaml')['namespace'],version=m['version'],blueId=m['packageBlueId'],archiveSha256=sha((stage/n/'dist/package.bluepkg').read_bytes()),path=n+'/dist/package.bluepkg') for n,m in manifests.items()]
  if check:assert read(HOME/'selection.json')==rows
  else:write(HOME/'selection.json',rows)
 print('PASS:',len(manifests),'closed release packages; unchanged authored business sources')

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--import-source',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
 if args.import_source:import_sources()
 build(args.check)
