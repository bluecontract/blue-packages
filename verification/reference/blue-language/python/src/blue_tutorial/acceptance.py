"""Portable command/observation format shared with a future Java oracle.

Definitions come from hash-checked original fixtures. Commands and assertions
are data: a second host can execute this manifest without importing Python tests.
"""
import json
from dataclasses import asdict
from pathlib import Path
from blue_bex.values import pointer_get
from blue_repository.runtime import RepositoryCatalogue
from blue_runtime import Stack

PATH=Path(__file__).with_name('acceptance.json')

def run_scenario(scenario):
    from .runner import source,require,MANIFEST
    from vendor import yaml
    s=Stack(catalogue=RepositoryCatalogue());inputs=[];observations=[]
    def value(v):
        if type(v) is dict and set(v)=={'$managedHead'}:
            root=v['$managedHead'];return {'blueId':s.host.roots[root].ids[root]}
        if type(v) is dict and set(v)=={'$fixture'}:
            chapter,file=v['$fixture'];text=source(chapter,file);inputs.append([chapter,file]);return yaml.safe_load(text)
        if type(v) is dict:return {k:value(x) for k,x in v.items()}
        if type(v) is list:return [value(x) for x in v]
        return v
    for command in scenario['commands']:
        if command['action']=='start':s.admit_graph({command['document']:value({'$fixture':command['fixture']})})
        elif command['action']=='call':
            published_before=len(s.host.published)
            root=command['document'];entry=s.call(root,command['operation'],value(command['request']),channel=command['channel'],timestamp=command['timestamp'])
            s.close_before(entry.timestamp+1);run=s.drain(root)
            applied=[x for x in run.steps if x.entry_blue_id==entry.blue_id and x.status=='APPLIED']
            require(len(applied)==1,'command was not applied exactly once')
            state=s.host.roots[root];receipt=s.host.receipts[applied[0].invocation_identity]
            snapshot=s.host.load_root(root)
            observations.append({'document':root,'entryBlueId':entry.blue_id,'gas':applied[0].gas_used,
                'stateBlueId':state.ids[root],'epochs':dict(state.epochs),'checkpointedState':s.state(root),
                'history':[{k:r[k] for k in ('epoch','blueId','predecessorBlueId','entry')} for r in s.host.histories[root]],
                'events':s.host.published[published_before:],'occurrences':[asdict(o) for o in snapshot.occurrences],
                'receipt':{'status':receipt.status,'work':list(receipt.work_order),'trace':list(receipt.trace)},
                'replayVerified':s.host.replay_saved(applied[0].invocation_identity)['verified'],
                'duplicateDrainSteps':len(s.drain(root).steps)})
            require(observations[-1]['replayVerified'] and observations[-1]['duplicateDrainSteps']==0,
                    'receipt replay or consumed-entry idempotency failed')
        else:raise ValueError('unknown acceptance command')
    for assertion in scenario['assertions']:
        actual=pointer_get(s.state(assertion['root'],assertion.get('document')),assertion['pointer'])
        require(type(actual)==type(assertion['equals']) and actual==assertion['equals'],str(assertion)+' got '+repr(actual))
    fixture_paths={str(p.relative_to(Path(__file__).with_name('fixtures'))) for chapter,file in inputs
                   for p in (Path(__file__).with_name('fixtures')/'examples').glob(chapter+'*/'+file)}
    return {'id':scenario['id'],'profile':s.catalogue.registry.profile_identity,
            'repository':s.catalogue.repository.identity,'observations':observations,
            'fixtureHashes':{r['file']:r['sha256'] for r in MANIFEST['examples'] if r['file'] in fixture_paths}}

def scenarios():return json.loads(PATH.read_text())['scenarios']
