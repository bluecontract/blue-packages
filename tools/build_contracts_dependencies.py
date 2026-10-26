#!/usr/bin/env python3
"""Build/check the exact native and SDK dependencies of Contracts 1.1.0.

Use JAVA_HOME and BLUE_JAVA_CLASSPATH with the maintained Java package builder.
The Core and Python checkout inputs are explicit; no network is used.
"""
from pathlib import Path
import json,shutil,subprocess,os,hashlib,zipfile
import argparse, tempfile
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--core', type=Path, required=True)
parser.add_argument('--python', type=Path, required=True)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
p = Path(__file__).resolve().parents[1]
core, python = args.core.resolve(), args.python.resolve()
release = p/'releases/contracts-1.1.0'
workspace = tempfile.TemporaryDirectory(prefix='contracts-dependencies-')
stage = Path(workspace.name)/'build'; stage.mkdir()
out = Path(workspace.name)/'release'; out.mkdir()
for name in ('package.bluepkg', 'selection.json'):
 shutil.copyfile(release/name, out/name)
cp=os.environ['BLUE_JAVA_CLASSPATH'];java=Path(os.environ['JAVA_HOME'])/'bin';classes=stage/'classes';classes.mkdir(exist_ok=True)
sha=lambda data:hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
subprocess.run([str(java/'javac'),'-cp',cp,'-d',str(classes),str(p/'tools/BuildFinalGas.java'),str(p/'tools/BuildPaymentFamily.java')],check=True)
def build(name):
 subprocess.run([str(java/'java'),'-Xmx1500m','-cp',str(classes)+os.pathsep+cp,'BuildFinalGas',str(stage),name],check=True,stdout=subprocess.DEVNULL)
 return read(stage/name/'dist/package.json')
for name in ('blue-language','blue-bex','blue-contracts'):
 target=stage/name/'dist/package.bluepkg';target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(out/'package.bluepkg' if name=='blue-contracts' else p/name/'dist/package.bluepkg',target)
meta={}
# Current MyOS provider, timer and Mandates sources: only dependencies and release versions change.
for name,version in [('blue-coordination','0.2.1'),('blue-time','0.2.1'),('blue-mandates','0.2.1')]:
 source=p/name;target=stage/name
 shutil.copytree(source,target,dirs_exist_ok=True,ignore=shutil.ignore_patterns('dist','__pycache__'))
 cfg=read(target/'blue-package.yaml');cfg['version']=version;write(target/'blue-package.yaml',cfg)
 meta[name]=build(name)
 dest=out/'native'/name;dest.mkdir(parents=True,exist_ok=True);shutil.copyfile(target/'dist/package.bluepkg',dest/'package.bluepkg')
# Execution bridge retains its authority/ordering rules with the exact Contracts release substituted.
target=stage/'execution';shutil.copytree(core/'runtime/final-gas-bridge',target,dirs_exist_ok=True)
cfg=read(target/'blue-package.yaml');cfg['version']='0.1.0';cfg['protocol']['name']='Coordination execution bridge';cfg['protocol']['rules']='spec/coordination-1.1.0.md'
text=(target/'spec/coordination-final-gas.md').read_text().replace('# Coordination execution bridge: final gas edition','# Coordination execution bridge for Contracts 1.1.0').replace('final-gas specification `Dsxv7hUoGTsTod8gPrHo3iC6VJ2sDhXTeZXThx9r6QPG`','1.1.0 specification `'+read(out/'selection.json')['specificationBlueId']+'`')
text=text.replace('A host must select this edition explicitly for a fresh runtime and must\nretain the prior edition when replaying its saved histories.','This release is the default for newly created state. Old histories are not upgraded or reinterpreted.')
(target/cfg['protocol']['rules']).write_text(text);write(target/'spec/frozen.json',{cfg['protocol']['rules']:'sha256:'+sha(text.encode())});write(target/'blue-package.yaml',cfg)
# Authored type metadata pins the previous bridge rules; remove that top-level binding so the maintained builder selects the new exact rules.
for row in cfg['exports']:
 path=target/row['path'];value=read(path);value.pop('specification',None);write(path,value)
meta['execution']=build('execution')
catalog=read(core/'runtime/blue-coordination-core/src/main/resources/final-gas/catalogue.json');m=meta['execution'];catalog['specification']=m['semanticSpecifications'][m['protocol']]['rules']['blueId'];catalog['contracts']=read(out/'selection.json')['specificationBlueId'];exports={r['name']:r['blueId'] for r in m['exports']};catalog['types']={n:exports[n.split('/',1)[1]] for n in catalog['sources']}
write(out/'native/catalogue.json',catalog);dest=out/'native/execution';dest.mkdir(parents=True,exist_ok=True);shutil.copyfile(target/'dist/package.bluepkg',dest/'package.bluepkg')
# SDK Coordination uses the same execution record types and embeds its catalogue.
write(target/'docs/catalogue.json',catalog);cfg['files'].append('docs/catalogue.json');cfg['name']='blue-coordination';write(target/'blue-package.yaml',cfg);meta['sdk-coordination']=build('execution');dest=out/'sdk/blue-coordination';dest.mkdir(parents=True,exist_ok=True);shutil.copyfile(target/'dist/package.bluepkg',dest/'package.bluepkg')
# SDK Mandates remains the existing owner-approved native authority extension, with no business-rule edits.
prior=read(python/'src/blue_coordination/engine/resources/mandates-support-gas10m.json')
old=python/'vendor/blue-packages/editions/gas-10m/blue-mandates/dist/package.bluepkg'
with zipfile.ZipFile(old) as z:
 manifest=json.loads(z.read('package.json'));rule=manifest['semanticSpecifications'][manifest['protocol']]['rules']['blueId'];files=[n for n in z.namelist() if n.startswith('spec/')]
 # The sole normative rules asset is selected by its Text identity in package metadata.
 docs=manifest['semanticPackages'][manifest['packageBlueId']]['documentation'];rulepath=next(n for n,v in docs.items() if v['content']['blueId']==rule);rules=z.read(rulepath).decode()
 target=stage/'sdk-mandates';(target/'spec').mkdir(parents=True,exist_ok=True);(target/rulepath).write_text(rules)
 (target/'README.md').write_text(z.read('README.md').decode())
imports={'language':{'path':'../blue-language/dist/package.bluepkg'},'bex':{'path':'../blue-bex/dist/package.bluepkg'},'contracts':{'path':'../blue-contracts/dist/package.bluepkg'},'coordination':{'path':'../execution/dist/package.bluepkg'}}
cfg=dict(name='blue-mandates',namespace='Mandates',version='0.2.1',language='language',imports=imports,previewOnly=True,protocol=dict(name='Mandates',status='release-candidate',rules=rulepath,requires={'coordination':'coordination','contracts':'contracts','bex':'bex'}),exports=[])
for i,(name,value) in enumerate(prior['sources'].items()):
 rel=f'types/{i:02}.json';cfg['exports'].append(dict(name=name.split('/',1)[1],path=rel));write(target/rel,json.loads(json.dumps(value).replace('Contracts/', 'contracts/').replace('Coordination/', 'coordination/').replace('BEX/', 'bex/')))
write(target/'blue-package.yaml',cfg);write(target/'spec/frozen.json',{rulepath:'sha256:'+sha(rules.encode())});meta['sdk-mandates']=build('sdk-mandates');dest=out/'sdk/blue-mandates';dest.mkdir(parents=True,exist_ok=True);shutil.copyfile(target/'dist/package.bluepkg',dest/'package.bluepkg')
m=meta['sdk-mandates'];prior.update(contractsSpecification=catalog['contracts'],coordinationPackage=meta['sdk-coordination']['packageBlueId'],coordinationSpecification=catalog['specification'],packageId=m['packageBlueId'],protocolId=m['protocol'],rulesId=m['semanticSpecifications'][m['protocol']]['rules']['blueId'],types={'Mandates/'+r['name']:r['blueId'] for r in m['exports']});write(out/'sdk/mandates-support.json',prior)
summary={n:{'name':m['name'],'version':m['version'],'packageBlueId':m['packageBlueId'],'protocol':m['protocol'],'rules':m['semanticSpecifications'][m['protocol']]['rules']['blueId']} for n,m in meta.items()};write(out/'dependencies.json',summary)
for source in sorted(out.rglob('*')):
 if not source.is_file(): continue
 destination = release/source.relative_to(out)
 if args.check:
  assert destination.read_bytes() == source.read_bytes(), 'Nonreproducible dependency: '+str(destination)
 else:
  destination.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(source,destination)
workspace.cleanup()
print('PASS: native and SDK release dependency graphs rebuilt without authored business-rule changes')
