#!/usr/bin/env python3
"""Generate/check host catalogue exports from the one canonical publication.

These host inputs are outside the semantic package: packageId is derived from
its compiled archive and must never be embedded back into that archive.
"""
import argparse, json, zipfile
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]

def outputs(root=ROOT):
    manifests = {}
    for name in ('blue-contracts','blue-coordination','blue-mandates'):
        with zipfile.ZipFile(root/name/'dist/package.bluepkg') as archive:
            manifests[name] = json.loads(archive.read('package.json'))
    def rules(name):
        m=manifests[name];return m['semanticSpecifications'][m['protocol']]['rules']['blueId']
    out={}
    for name,ns in [('blue-coordination','Coordination'),('blue-mandates','Mandates')]:
        m=manifests[name];config=yaml.safe_load((root/name/'blue-package.yaml').read_text())
        data=dict(types={ns+'/'+e['name']:e['blueId'] for e in m['exports']},
                  sources={ns+'/'+e['name']:yaml.safe_load((root/name/e['path']).read_text()) for e in config['exports']})
        if ns=='Coordination': data.update(contracts=rules('blue-contracts'),specification=rules(name))
        else:data.update(packageId=m['packageBlueId'],protocolId=m['protocol'],rulesId=rules(name),
             coordinationPackage=manifests['blue-coordination']['packageBlueId'],
             coordinationSpecification=rules('blue-coordination'),contractsSpecification=rules('blue-contracts'))
        out[name+'/docs/runtime-catalogue.json']=(json.dumps(data,indent=2)+'\n').encode()
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    for name,data in outputs().items():
        path=ROOT/name
        if args.check:
            if path.read_bytes()!=data:raise ValueError('Canonical host catalogue differs: '+name)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print('PASS: canonical host catalogue exports')
if __name__=='__main__':main()
