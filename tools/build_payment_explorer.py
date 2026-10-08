#!/usr/bin/env python3
"""Render existing native reports for inspection; never calculates business outcomes."""
import argparse
import json
import shutil
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'build/payment-explorer')
    args=parser.parse_args();rows=[]
    for case in sorted((ROOT/'examples/payment-family').glob('*.case.yaml')):
        report=args.reports/(case.name+'.json')
        if not report.exists(): continue
        cfg=yaml.safe_load(case.read_text());source=case.parent/cfg['document']
        name=yaml.safe_load(source.read_text())['name']
        rows.append(dict(id=case.name[:2],title=name,casePath=str(case.relative_to(ROOT)),sourcePath=str(source.relative_to(ROOT)),
                         source=source.read_text(),documentName=name,trace=json.loads(report.read_text())))
    args.output.mkdir(parents=True,exist_ok=True)
    for name in ['index.html','app.js','style.css']:
        shutil.copyfile(ROOT/'tools/payment-explorer'/name,args.output/name)
    (args.output/'docs').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'docs/payment-family.md',args.output/'docs/payment-family.md')
    payload=dict(version='0.6.0-preview.4',cases=rows,catalogue=json.loads((ROOT/'catalogue/payment-family.json').read_text()))
    (args.output/'data.js').write_text('window.BLUE_DEMO = '+json.dumps(payload,ensure_ascii=False).replace('</','<\\/')+';\n')
    print(f'{len(rows)} native traces: {args.output / "index.html"}')

if __name__=='__main__':main()
