#!/usr/bin/env python3
"""Verify archives, dependency locks, retained legacy IDs and unchanged foundations."""
from pathlib import Path
import hashlib,json,os,sys,time
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=Path(os.environ.get('BLUE_SOURCE_WORKSPACE',str(ROOT.parents[2])))
sys.path.insert(0,str(WORKSPACE/'blue-language-python/src'))
from blue_packages import Runtime
from blue_packages.reader import read_package
from blue_language.physical import PhysicalCache
from blue_runtime.core_reuse import core_reuse_scope
NAMES=['blue-agreements','clause-mutual-activation','clause-immediate-termination','agreement-reseller']
RENAMED={('blue-agreements','Clause'),('blue-agreements','Agreement'),
 ('clause-mutual-activation','Mutual Activation Clause'),
 ('clause-immediate-termination','Immediate Termination Clause'),
 ('agreement-reseller','Reseller Agreement')}
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 start=time.time();prior=json.loads((ROOT.parent/'root-clauses/verification/legacy-export-ids.json').read_text());rows=[];retained=[]
 runtime=Runtime.agreements(packages=WORKSPACE/'blue-packages')
 with PhysicalCache(65536).scope(),core_reuse_scope():
  for name in NAMES:
   project=ROOT/'blue-packages'/name;p=runtime.require(read_package(project/'dist/package.bluepkg'))
   for old,identity in prior[name].items():
    alias='Embedded '+old if (name,old) in RENAMED else old
    assert p.exports[alias]==identity,(name,old,alias)
    retained.append(dict(package=name,oldExport=old,newExport=alias,blueId=identity))
   lock=json.loads((project/'blue-package.lock.json').read_text())
   for prefix,item in lock['imports'].items():
    dependency=project/item['path']
    assert 'sha256:'+sha(dependency.read_bytes())==item['archiveSha256'],(name,prefix)
   rows.append(dict(name=name,packageBlueId=p.blue_id,archiveSha256=p.archive_sha,exports=len(p.exports),audit=p.audit))
   print('VERIFIED',name,p.blue_id,flush=True)
 foundations=[]
 for name in ['blue-language','blue-bex','blue-contracts','blue-coordination']:
  raw=(ROOT.parent/'root-clauses/blue-packages'/name/'dist/package.bluepkg').read_bytes()
  original=(WORKSPACE/'blue-packages'/name/'dist/package.bluepkg').read_bytes()
  assert raw==original,name+': changed foundation archive'
  foundations.append(dict(name=name,sha256=sha(raw)))
 baseline=[]
 for row in json.loads((ROOT.parent/'root-clauses/verification/candidate-packages.json').read_text())['packages']:
  raw=(ROOT.parent/'root-clauses/blue-packages'/row['path']).read_bytes()
  assert 'sha256:'+sha(raw)==row['archiveSha256'],row['name']+': changed original edition'
  baseline.append(dict(name=row['name'],packageBlueId=row['packageBlueId'],archiveSha256=row['archiveSha256']))
 report=dict(passed=True,unchangedBaselineArchives=baseline,packages=rows,legacyExports=retained,legacyCount=len(retained),
  unchangedFoundationArchives=foundations,seconds=round(time.time()-start,3))
 (ROOT/'verification/package-integrity.json').write_text(json.dumps(report,indent=2)+'\n')
 print('All archives, locks, legacy identities and foundations passed.',flush=True)
if __name__=='__main__':main()
