"""Execute the tutorial's YAML using the actual three-input processor."""
from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[2]/'apps/workbench/guide_data'
from vendor import yaml
from blue_contracts import Processor,Link,RuntimeBinding
from blue_bex import UNDEFINED
from algorithms import blue as L


REPORTS = {}

def install_extensions(p):
    class TickChannel:
        def accept(self,context):
            context.gas.charge('accept')
            return context.event.get('kind')=='tick'
    class DoubleStep:
        def execute(self,context):
            context.gas.charge('execute')
            value=context.read('/count')*2
            return {'patches':[{'op':'replace','path':'/count','val':value}],
                    'events':[{'kind':'doubled','count':value}]}
    for alias,parent,role,tariff,impl in [
        ('Tick Channel','Channel','external-channel',(('accept',1),),TickChannel()),
        ('Double Step','Contract','step',(('execute',2),),DoubleStep())]:
        tid=p.blue.identity(p.blue.source({'name':alias,'type':{'blueId':p.registry.types[parent]}},goal='definition'))
        sid=p.blue.identity(p.blue.source('Tutorial '+alias+' runtime v1: see tools/scenarios.py.'))
        p.install_runtime(RuntimeBinding(tid,sid,role,(),(),'tutorial-'+role,tariff),impl)
        p.blue.language.aliases['Tutorial/'+alias]=tid
    p.blue.refresh()


def load(name):return yaml.safe_load((ROOT/'contracts'/name/'scenario.yaml').read_text())
def ids():return yaml.safe_load((ROOT/'contracts/MANIFEST.yaml').read_text())['scenarios']

def execute(name):
    scenario=load(name);p=Processor()
    if scenario.get('extensions'):install_extensions(p)
    for alias,definition in scenario.get('definitions',{}).items():
        node=p.blue.source(definition,goal='definition')
        p.blue.language.aliases[alias]=p.blue.identity(node);p.blue.refresh()
    doc=scenario['document']
    if scenario.get('cyclicSet'):
        def symbols(v):
            if isinstance(v,dict):
                if set(v)=={'blueId'} and v['blueId'].startswith('this#'):return Link('member'+v['blueId'][5:])
                return {k:symbols(x) for k,x in v.items()}
            if isinstance(v,list):return [symbols(x) for x in v]
            return v
        initial=p.admit({'member'+str(i):symbols(v) for i,v in enumerate(doc)},root='member0')
    else:initial=p.initialize(doc)
    assert initial.commits,(name,'initialization',initial.status,initial.diagnostic)
    state=initial.document
    def checks(out,row):
        for path,wanted in row.get('expect',{}).items():
            value=p.read(out.document,path)
            assert value==wanted,(name,path,value,wanted,out.diagnostic)
        for path in row.get('expectAbsent',[]):assert p.read(out.document,path) is UNDEFINED,(name,path)
        if row.get('expectRetired'):
            from blue_contracts.reference.graph import Graph
            retired=set(out.snapshot.documents)-Graph(out.snapshot,p.registry,p.archive).reachable()
            assert len(retired)==1,(name,'retired source missing')
            for path,wanted in row['expectRetired'].items():
                assert p.read(out.snapshot,path,document=next(iter(retired)))==wanted,(name,'retired',path)
        for path,alias in row.get('expectTypes',{}).items():
            node=p.blue.select(out.document.documents[out.document.root].body,path)
            assert p.blue.head(node).type_id==p.blue.language.aliases[alias],(name,path,'type mismatch')
        if 'expectEvents' in row:assert p.emitted(out)==row['expectEvents'],(name,'events',p.emitted(out),row['expectEvents'])
        if 'expectCheckpointCount' in row:assert len(out.checkpoints)==row['expectCheckpointCount'],(name,out.checkpoints)
        if 'expectCheckpointChannels' in row:assert {x['channel'] for x in out.checkpoints}==set(row['expectCheckpointChannels'])
        if row.get('expectRootCheckpoint') is False:assert not any(x['document']==out.document.root for x in out.checkpoints)
        if row.get('expectCycle'):
            assert all('#' in d.blue_id for d in out.document.documents.values())
            p.validate(out.document)
    checks(initial,{'expect':scenario.get('expectInitialization',{}),'expectEvents':scenario.get('expectInitializationEvents',[])})
    if 'expectTerminated' in scenario:
        assert (p.registry.marker(state.documents[state.root].body,'terminated') is not None)==scenario['expectTerminated']
    report={'id':name,'initialization':{'status':initial.status,'gas':initial.gas,'rootBlueId':state.documents[state.root].blue_id,'events':p.emitted(initial)},'steps':[]}
    results=[]
    for row in scenario['inputs']:
        before=state
        out=p.process(state,row['event'],row['eventTimestamp'])
        assert out.status==row.get('expectStatus','APPLIED'),(name,out.status,out.diagnostic)
        checks(out,row)
        if not out.commits:assert out.document.identity==before.identity and not out.public_events
        expected_event_id=p.blue.identity(p.blue.source(row['event']))
        for change in out.checkpoints:
            if change['after'] is not None:
                assert change['after']['event']['blueId']==expected_event_id
                assert change['after']['timestamp']==row['eventTimestamp']
        report['steps'].append({'status':out.status,'gas':out.gas,'rootBlueId':out.document.documents[out.document.root].blue_id,
                               'events':p.emitted(out),'reads':{path:p.read(out.document,path) for path in row.get('expect',{})},
                               'receipt':out.receipt,'checkpointChanges':out.checkpoints,'diagnostic':out.diagnostic})
        results.append(out);state=out.document
    REPORTS[name] = report
    return p,initial,results,report

if __name__=='__main__':
    reports=[]
    for name in ids():
        _,_,_,report=execute(name);reports.append(report)
        print(name,'PASS', 'gas='+','.join(str(s['gas']) for s in report['steps']))
    output=ROOT.parents[2]/'runs/codex/contracts-completion-1/tutorial-results.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(reports,indent=2,ensure_ascii=False)+'\n')
