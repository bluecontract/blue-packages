#!/usr/bin/env python3
"""Compare an independently implemented JSONL adapter with original fixtures."""
import argparse,json,shlex,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run import match,check_fixture
p=argparse.ArgumentParser()
p.add_argument('fixtures',nargs='+',type=Path)
p.add_argument('--command',help='Adapter command; parsed without a shell')
p.add_argument('--results',type=Path,help='Existing JSONL results instead of executing an adapter')
p.add_argument('--output',type=Path)
a=p.parse_args()
if bool(a.command)==bool(a.results):p.error('choose exactly one of --command or --results')
cases=[json.loads(l) for f in a.fixtures for l in f.read_text().splitlines() if l.strip()]
for c in cases:check_fixture(c)
ids=[c['id'] for c in cases]
if len(ids)!=len(set(ids)):raise ValueError('duplicate case ID')
if a.command:
    payload=''.join(json.dumps({k:c[k] for k in ('id','environment','request') if k in c},ensure_ascii=False)+'\n' for c in cases)
    proc=subprocess.run(shlex.split(a.command),input=payload,text=True,capture_output=True)
    if proc.returncode:
        print(proc.stderr,file=sys.stderr);raise SystemExit('adapter execution failed; not a Language rejection')
    text=proc.stdout
else:text=a.results.read_text()
results=[json.loads(l) for l in text.splitlines() if l.strip()]
seen={};errors=[]
for r in results:
    i=r.get('caseId')
    if i not in ids or i in seen:errors.append({'caseId':i,'message':'unexpected/duplicate result'})
    seen[i]=r
for c in cases:
    if c['id'] not in seen:errors.append({'caseId':c['id'],'message':'missing result'});continue
    errors.extend({'caseId':c['id'],'message':e} for e in match(seen[c['id']],c['expected']))
if a.output:a.output.write_text(text)
print(json.dumps({'cases':len(cases),'results':len(results),'passed':len(cases)-len({e['caseId'] for e in errors if e['caseId'] in ids}),'failures':errors},ensure_ascii=False,indent=2))
raise SystemExit(1 if errors else 0)
