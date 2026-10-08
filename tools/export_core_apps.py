#!/usr/bin/env python3
"""Export the selected unpublished packages and clause examples to an explicit Core checkout."""
import argparse, hashlib, json, sys
from pathlib import Path
from check_clause_tutorial import SourceLoader
import yaml
ROOT=Path(__file__).resolve().parents[1]
def read(p): return yaml.load(p.read_text(),Loader=SourceLoader)
def write_changed(path, data):
    raw=data.encode() if isinstance(data,str) else data
    if not path.exists() or path.read_bytes()!=raw:path.write_bytes(raw)
def export(core):
    catalog=json.loads((ROOT/'PACKAGES.json').read_text())
    by_ns={r['namespace']:r for r in catalog['packages']}
    manifests={ns:read(ROOT/r['directory']/'blue-package.yaml') for ns,r in by_ns.items()}
    out=core/'runtime/blue-core-service/src/main/resources/package-catalog'
    existing=json.loads((out/'catalog.json').read_text())
    for ns,row in by_ns.items():
        manifest=manifests[ns]
        if row['directory'] in json.loads((ROOT/'PACKAGE-SOURCES.json').read_text())['foundations'] or manifest.get('protocol'):continue
        archive=ROOT/row['path'];actual='sha256:'+hashlib.sha256(archive.read_bytes()).hexdigest()
        if actual!=row['archiveSha256']:raise ValueError('Stale package catalogue: '+ns)
        ident=row['name']+'@'+row['version']
        dist=json.loads((archive.parent/'package.json').read_text())
        lock=json.loads((archive.parent.parent/'blue-package.lock.json').read_text())
        record=dict(id=ident,name=ns,version=row['version'],blueId=row['packageBlueId'],description='Clause application candidate. Explicit package selection; payment adapters are test integrations.',imports={n:d['packageBlueId'] for n,d in lock['imports'].items()},exports={e['name']:e['blueId'] for e in dist['exports']},archiveSha256=actual,hasPackageSpecification=False)
        previous=next((r for r in existing if r['id']==ident),None)
        if previous is not None and previous['blueId']!=record['blueId'] and 'preview' not in row['version']:raise ValueError('Cannot replace published package '+ident)
        existing=[r for r in existing if r['id']!=ident]+[record]
        write_changed(out/(ident+'.bluepkg'),archive.read_bytes())
    write_changed(out/'catalog.json',json.dumps(existing,indent=2)+'\n')
    def namespaces(value,result):
        if isinstance(value,str) and '/' in value and value.split('/')[0] in by_ns:result.add(value.split('/')[0])
        elif isinstance(value,dict):
            for v in value.values():namespaces(v,result)
        elif isinstance(value,list):
            for v in value:namespaces(v,result)
    descriptions={
      '00':'One reusable action, explicit validation, and an audit step.',
      '01':'A customer confirms satisfaction inside the Payment Instruction. The order observes the resulting event.',
      '02':'Orders generate commission only from confirmed net collection.',
      '03':'Independent design and delivery acceptance controls separate payments.',
      '04':'One agreement starts independent service orders from an agreed template.',
      '05':'A matching smart-home check-in requests capture. Incorrect reservations are rejected.',
      '06':'Each membership period is a separate obligation; termination has its own lifecycle.',
      '07':'Both parties approve one exact booking amendment.',
      '08':'A predeclared representative can use assigned actions without gaining the lead party’s permissions.',
      '09':'Create and approve a native fixed-scope mandate; the acceptance action also verifies delivered evidence. Hosted delegated invocation is not included.',
      '10':'Corrections change the net obligation. A distinct confirmed payment settles it.',
      '11':'A local event triggers Hello once. Other events do not consume the connection.',
      '12':'A property update triggers a reusable action without a separate user workflow.',
      '13':'Listen to one embedded document and observe its event in the parent.',
      '14':'Observe matching events from any child in an embedded collection.',
      '15':'Reprice a product through a validated action, rejecting invalid quantities and amounts.',
      '16':'Accrue an obligation, reserve a settlement amount and confirm the resulting ledger entry.',
      '17':'Stop accepting new work while winding down, then terminate after obligations are complete.',
      '18':'Propose a terms change and require both parties to approve the same amendment.',
      '19':'Add ordinary clauses to a standard Payment Instruction while keeping its party roster frozen.',
      '20':'Model alternative state transitions and reject transitions outside the agreed graph.',
      '21':'Initialize a customer payment for a MyOS recipient and exercise the explicit test guarantor protocol.',
      '22':'Transfer between two distinct MyOS accounts using the common payment request protocol.',
      '23':'Request a manual bank payment and let the designated recipient confirm receipt.',
      '24':'Use an abstract bank-specific initialization flow with the same capture and refund request model.',
      '25':'A carrier confirms shipment requests and delivery; an address request is not a confirmed address change.',
      '26':'Compare absolute deadlines, first/latest event anchors, cancellation and signed-time completion.',
      '27':'Exercise correlated payment requests, confirmations, failures, retries and unknown outcomes.',
      '28':'Exercise cancellation and policy controls without confusing requests with authoritative results.',
      '29':'Reject an instruction and verify that rejected payments cannot continue through the normal flow.'}
    fixtures=core/'examples/clause-apps'
    fixtures.mkdir(parents=True,exist_ok=True)
    current={p.name for p in (ROOT/'examples/apps').iterdir() if p.suffix in {'.blue','.yaml'}}
    # This directory is owned by this exporter. Remove retired scenario kinds too,
    # e.g. a mock-transport case replaced by a real-provider native scenario.
    for path in fixtures.iterdir():
        if path.is_file() and path.suffix in {'.blue','.yaml'} and path.name not in current:
            path.unlink()
    for path in (ROOT/'examples/apps').iterdir():
        if path.suffix in {'.blue','.yaml'}:write_changed(fixtures/path.name,path.read_bytes())
    mounts={}
    for ns,row in by_ns.items():
        manifest=manifests[ns]
        if manifest.get('protocol') or row['directory'] in json.loads((ROOT/'PACKAGE-SOURCES.json').read_text())['foundations']:
            destination=core/'runtime/pinned-packages'/row['directory']/'dist/package.bluepkg'
            if ns=='Coordination':destination=core/'runtime/blue-coordination-core/src/main/resources/provider-v1/coordination.bluepkg'
            if ns=='Time':destination=core/'runtime/blue-coordination-core/src/main/resources/canonical/time.bluepkg'
            if ns=='Mandates':destination=core/'runtime/blue-coordination-core/src/main/resources/canonical/mandates.bluepkg'
        else:
            destination=out/(row['name']+'@'+row['version']+'.bluepkg')
        if not destination.exists():raise ValueError('Missing Core dependency: '+str(destination))
        digest='sha256:'+hashlib.sha256(destination.read_bytes()).hexdigest()
        if digest!=row['archiveSha256']:raise ValueError('Core native dependency differs: '+ns)
        mounts[ns]=dict(path=str(destination.relative_to(core)),blueId=row['packageBlueId'],archiveSha256=digest)
    write_changed(fixtures/'packages.json',json.dumps(dict(mounts=mounts),indent=2)+'\n')
    examples=[]
    for path in sorted(list((ROOT/'examples/apps').glob('*.case.yaml'))+list((ROOT/'examples/apps').glob('*.time.yaml'))+list((ROOT/'examples/apps').glob('*.native.yaml'))):
        case=read(path);source=(path.parent/case['document']).read_text();doc=read(path.parent/case['document'])
        activation=next(c for c in doc['clauses'].values() if c['type']=='Activation/Activation Clause')
        wanted=set();namespaces(doc,wanted)
        # All directly named packages are explicit. Closure installation pins transitive dependencies.
        selected=[by_ns[n]['packageBlueId'] for n in sorted(wanted) if not manifests[n].get('protocol') and by_ns[n]['directory'] not in json.loads((ROOT/'PACKAGE-SOURCES.json').read_text())['foundations']]
        roles=[]
        for role,party in activation['parameters']['parties'].items():
            roles.append(dict(name=role,label=party.get('displayName',role),kind='lead'))
            for rep in party.get('representatives',{}):roles.append(dict(name=role+'__'+rep,label=role+' · '+rep,kind='representative'))
        examples.append(dict(id=path.name.removesuffix('.case.yaml').removesuffix('.time.yaml').removesuffix('.native.yaml'),title=doc['name'],description=descriptions.get(path.name[:2],doc['name']),source=source,roles=roles,packages=selected,steps=case.get('steps',[]),distinctRoles={'09':[['buyer','buyer__agent']],'22':[['customer','seller']]}.get(path.name[:2],[])))
    target=core/'core-ui/src/data/clause-examples.json';target.parent.mkdir(exist_ok=True);write_changed(target,json.dumps(examples,indent=2)+'\n')
    print('Exported',len(examples),'documents and verified candidate packages to',core)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('core',type=Path);export(p.parse_args().core.resolve())
