"""Four real-engine examples. The provider supplies local test outcomes, not external execution."""
import json,sys,platform
from pathlib import Path
from session import Session
from order_flow import order,mandate as order_mandate
from algorithms import blue as L
ROOT=Path(__file__).resolve().parents[1]
import hashlib
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def scope_names(s,m):return sorted(set(s.read(m,'/scope'))-{'type'})
def record(s,name,handles):
    sources={}
    with s.hub.lock,s.hub.cache.scope(),s.store.read() as view:
        p=s.hub.processor;p.blue.language.bind(view);p.blue.refresh()
        try:
            for label,h in handles.items():sources[label]=p.blue.literal(L.Ref(s.row(h)['documentId']))
        finally:p.blue.language.bind(None);p.blue.refresh()
    for label,value in sources.items():
        path=ROOT/'examples/generated'/f'{name}-{label}.blue';path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(value,indent=2)+'\n')
    histories={k:s.engine.history(h)['items'] for k,h in handles.items()}
    return {'name':name,'verified':True,'entries':s.trace,'events':s.events(),
        'documents':{k:{'initial':s.row(h)['documentId'],'head':s.row(h)['lastStable']['blueId'],
            'epoch':s.row(h)['lastStable']['epoch']} for k,h in handles.items()},
        'histories':histories,'maxObservedContractsGas':max(x['gas'] for hs in histories.values() for x in hs)}

def grant_by_two(s,t):
    return s.grant(t,validation={'request':{'amount':2},
        'function':{'expr':{'$eq':[{'$keys':{'$binding':'request'}},['amount']]}}})

def static_counter():
    with Session(name='static') as s:
        t=s.add(s.counter_source());m=s.add(s.mandate_source({'byTwo':grant_by_two(s,t)}));s.approve(m);a=s.authority(m)
        for amount,expected in [(3,0),(2,2)]:
            s.invoke('agent',t,'increment',{'amount':amount},channel='ownerChannel',authority=a)
            assert s.read(t,'/count')==expected
        s.invoke('holder',m,'terminateMandate',{'reason':'Agent reassigned'})
        s.invoke('agent',t,'increment',{'amount':2},channel='ownerChannel',authority=a);assert s.read(t,'/count')==2
        s.invoke('holder',t,'increment',{'amount':2},channel='ownerChannel');assert s.read(t,'/count')==4
        result=record(s,'static',{'counter':t,'mandate':m});result['final']={'count':4,'mandate':'Terminated'};return result

def manual_order():
    with Session(name='manual') as s:
        t,events=order(s);m=order_mandate(s,t,events,connected=False);s.approve(m);a=s.authority(m)
        s.invoke('agent',t,'approveOrder',channel='sellerChannel',authority=a);assert s.read(t,'/phase')=='Approved'
        assert scope_names(s,m)==['approve']
        s.invoke('holder',m,'acknowledgeOrderApproval');assert scope_names(s,m)==['release']
        s.invoke('agent',t,'releaseForFulfilment',{'method':'standard'},channel='sellerChannel',authority=a)
        assert s.read(t,'/phase')=='Released'
        result=record(s,'manual',{'order':t,'mandate':m});result['final']={'order':'Released','mandate':'Active'};return result

def evidence(s,m,*,unknown=False):
    request=s.invoke('agent',m,'requestEvidence');rid=s.value_id(m,'/pendingEvidence')
    for status in (['Unknown','Succeeded'] if unknown else ['Succeeded']):
        reply=s.typ('Evidence Responded',inResponseTo={'blueId':rid},executionId='local-example-execution',
            executionStatus=status,result={'qualified':True} if status=='Succeeded' else {})
        reply_id=s.engine.publish_content(reply)
        s.invoke('provider',m,'provideEvidence',{'blueId':reply_id})
        assert s.read(m,'/stage')==('EvidencePassed' if status=='Succeeded' else 'EvidencePending')
        if status=='Unknown':assert scope_names(s,m)==[]
    assert s.value_id(m,'/evidenceResponse')==reply_id
    with s.hub.lock,s.hub.cache.scope(),s.store.read() as v:
        c=s.hub.catalogue;c.blue.language.bind(v);c.blue.refresh()
        try:assert c.link(reply_id,'inResponseTo')==rid
        finally:c.blue.language.bind(None);c.blue.refresh()
    return {'request':rid,'response':reply_id,'requestCausalEntry':request.blue_id,'provider':'signed local test participant'}

def provider_counter():
    with Session(name='provider-gate') as s:
        t=s.add(s.counter_source());src=s.mandate_source(type_name='Qualification Mandate',
            evidenceRequirement={'operationId':'customer-qualification','operationRevision':1,'document':{'blueId':s.row(t)['documentId']}},
            scopeOnSuccess={'byTwo':grant_by_two(s,t)})
        src['contracts']['evidenceProviderChannel']=s.channel('provider');m=s.add(src);s.approve(m);a=s.authority(m)
        assert scope_names(s,m)==[]
        rr=evidence(s,m,unknown=True)
        s.invoke('agent',t,'increment',{'amount':2},channel='ownerChannel',authority=a);assert s.read(t,'/count')==2
        result=record(s,'provider',{'counter':t,'mandate':m});result['correlation']=rr
        result['final']={'count':2,'mandate':'Active','stage':'EvidencePassed'};return result

def connected_order():
    with Session(name='connected',workers=2) as s:
        t,events=order(s);m=order_mandate(s,t,events,qualified=True);s.approve(m);a=s.authority(m)
        rr=evidence(s,m);assert scope_names(s,m)==['approve']
        s.invoke('agent',t,'approveOrder',channel='sellerChannel',authority=a)
        s.wait(m,lambda r:scope_names(s,m)==['release']);assert s.read(t,'/phase')=='Approved'
        s.invoke('agent',t,'releaseForFulfilment',{'method':'standard'},channel='sellerChannel',authority=a)
        s.wait(m,lambda r:s.read(m,'/status')=='Terminated')
        assert s.read(t,'/phase')=='Released' and scope_names(s,m)==[]
        result=record(s,'connected',{'order':t,'mandate':m});result['correlation']=rr
        result['final']={'order':'Released','mandate':'Terminated','stage':'Finished'};return result

if __name__=='__main__':
    cases=[]
    for fn in [static_counter,manual_order,provider_counter,connected_order]:
        case=fn();cases.append(case);print(case['name'],json.dumps(case['final']),flush=True)
    report={'passed':True,'python':platform.python_version(),'runtimeProfile':__import__('blue_packages').Runtime.mandates().profile,
        'packageArchiveSha256':sha(ROOT/'dist/package.bluepkg'),'examples':cases}
    (ROOT/'verification').mkdir(exist_ok=True)
    (ROOT/'verification/examples.json').write_text(json.dumps(report,indent=2)+'\n')
