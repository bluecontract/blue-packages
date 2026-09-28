"""Test/example transport harness, not a per-package SDK or business implementation.
All negotiation, authorization decisions and lifecycle changes execute in Blue.
"""
from pathlib import Path
from functools import lru_cache
from copy import deepcopy
import json,time
from blue_packages import Runtime,read_package
from blue_repository import Repository
from blue_language.physical import PhysicalCache
from blue_coordination.engine import CoordinationEngine,MemoryStore,SourceHub
from blue_coordination.engine.content import mount_business_repository
from algorithms import blue as L
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=Path(__file__).resolve().parents[2]

@lru_cache(maxsize=1)
def repository():
    runtime=Runtime.agreements();aliases={};records={}
    with PhysicalCache(65536).scope():
        for name,prefix in [('blue-agreements','Agreements'),('clause-mutual-activation','MutualActivation'),
                            ('clause-immediate-termination','ImmediateTermination'),('agreement-reseller','Reseller')]:
            package=read_package(ROOT/name/'dist/package.bluepkg');runtime.require(package)
            aliases.update({prefix+'/'+label:bid for label,bid in package.exports.items()})
            records.update(package.repository.records)
        return Repository.from_payload('reseller-example-explicit-imports',aliases,records)

class Session:
    def __init__(self,*,store=None,workers=1):
        self.runtime=Runtime.agreements();self.repo=repository()
        self.store=store or MemoryStore();self.hub=SourceHub(self.store,runtime=self.runtime)
        mount_business_repository(self.hub.processor.blue.language,self.repo);self.hub.processor.blue.refresh()
        self.providers={side:self.hub.create('reseller-'+side,['principal-'+side],key=Ed25519PrivateKey.generate()) for side in ('A','B','outsider')}
        self.actors={side:next(iter(provider.actors)) for side,provider in self.providers.items()}
        self.engine=CoordinationEngine(store=self.store,hub=self.hub,repository=self.repo,
            workers=workers,poll_interval=.01,supported_packages=self.runtime.supported_packages).start()
        # Engine selection replaces the hub's isolated processor. Mount authoring
        # content on that selected processor as well; workers mount repository separately.
        mount_business_repository(self.hub.processor.blue.language,self.repo);self.hub.processor.blue.refresh()
        self.time=0;self.trace=[]
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def close(self):self.engine.close()
    def typ(self,alias,**fields):return {'type':{'blueId':self.repo.aliases[alias]},**fields}
    def channel(self,side):
        return self.hub.catalogue.typed('Timeline Channel',timeline={'blueId':self.providers[side].timeline},actor={'blueId':self.actors[side]})
    def row(self,h):return self.engine.get(h)
    def wait(self,h,predicate=None,seconds=45,allow_error=False):
        end=time.monotonic()+seconds;row=None
        while time.monotonic()<end:
            row=self.row(h)
            if not allow_error and row['processing']['state']=='ERROR':raise RuntimeError(json.dumps(row['processing'],default=str))
            if predicate(row) if predicate else row['lastStable'] is not None:return row
            time.sleep(.01)
        raise TimeoutError(json.dumps(row,default=str)[:4000])
    def add(self,source):
        h=self.engine.add(source);self.wait(h);return h
    def read_id(self,bid,path='',identity=False):
        with self.hub.lock,self.hub.cache.scope(),self.store.read() as view:
            p=self.hub.processor;p.blue.language.bind(view);p.blue.refresh()
            try:
                if identity:return p.blue.identity(p.blue.exact(p.blue.select(L.Ref(bid),path)))
                return p.blue.read(L.Ref(bid),path)
            finally:p.blue.language.bind(None);p.blue.refresh()
    def read(self,h,path=''):return self.read_id(self.row(h)['lastStable']['blueId'],path)
    def value_id(self,h,path):return self.read_id(self.row(h)['lastStable']['blueId'],path,True)
    def managed(self,alias,seconds=45):
        end=time.monotonic()+seconds;target=self.repo.aliases[alias]
        while time.monotonic()<end:
            for row in self.engine.list():
                if row['lastStable'] and self.read_id(row['lastStable']['blueId'],'/type',True)==target:return row['instance']
            time.sleep(.01)
        raise TimeoutError('Managed type not found: '+alias)
    def source(self,allowed='EITHER',agreement_id='reseller-demo'):
        tid=self.repo.aliases['Reseller/Reseller Agreement']
        terms=deepcopy(self.read_id(tid,'/defaultTerms'))
        if allowed is None:terms['clauses'].pop('immediateTermination',None)
        else:terms['clauses']['immediateTermination']=self.typ('ImmediateTermination/Immediate Termination Terms',allowedParty=allowed)
        parties={'partyA':{'blueId':self.actors['A']},'partyB':{'blueId':self.actors['B']}}
        return self.typ('Reseller/Reseller Agreement',agreementId=agreement_id,**parties,
            contracts={'partyA':self.channel('A'),'partyB':self.channel('B')},
            activation=self.typ('MutualActivation/Mutual Activation Clause',agreementId=agreement_id,
                agreementType=tid,**parties,initialTerms=terms,
                contracts={'partyA':self.channel('A'),'partyB':self.channel('B')}))
    def invoke(self,h,side,operation,request,*,channel=None,sender=None,exact=False,allow_error=False):
        before=self.row(h)['lastStable'];self.time+=1000;sender=sender or side
        message={'type':'Contracts/Operation Request','document':{'blueId':before['blueId']},
            'channel':channel or 'party'+side,'operation':operation,'request':deepcopy(request)}
        if exact:message['requireExactDocumentVersion']=True
        entry=self.hub.append(self.providers[sender].timeline,self.actors[sender],self.time,message)
        row=self.wait(h,lambda r:(r['lastStable'] is not None and r['lastStable']['epoch']>before['epoch']) or
            r['processing']['checkedBoundary']>self.time or (allow_error and r['processing']['state']=='ERROR'),allow_error=allow_error)
        self.trace.append({'operation':operation,'side':side,'sender':sender,'request':deepcopy(request),
            'entry':entry.blue_id,'timestampUs':self.time,'receiver':h,
            'epoch':row['lastStable']['epoch'] if row['lastStable'] else None,
            'processing':row['processing'],'disposition':row.get('lastInputDisposition')})
        return entry
    def action(self,h,side,action,request_id,**fields):
        state=self.read(h,'/state')
        req={'requestId':request_id,'action':action,'round':state['round'],'termsId':state['targetId'],**fields}
        self.invoke(h,side,'act'+side,req);return req
    def wait_phase(self,h,phase,seconds=45):
        return self.wait(h,lambda r:r['lastStable'] is not None and self.read(h,'/phase')==phase,seconds=seconds)
    def wait_value(self,h,path,value,seconds=45):
        return self.wait(h,lambda r:r['lastStable'] is not None and self.read(h,path)==value,seconds=seconds)
    def events(self):
        with self.hub.lock,self.hub.cache.scope(),self.store.read() as view:
            p=self.hub.processor;p.blue.language.bind(view);p.blue.refresh()
            try:return [{'occurrence':key,**row,'content':p.blue.literal(L.Ref(row['event']['event']))}
                        for key,row in view.scan('outbox','default/')]
            finally:p.blue.language.bind(None);p.blue.refresh()
    def events_of(self,alias):
        tid=self.repo.aliases[alias]
        return [row for row in self.events() if row['content'].get('type',{}).get('blueId')==tid]
    def restart(self):
        self.engine.close()
        for provider in self.providers.values():self.hub.adopt(provider)
        self.engine=CoordinationEngine(store=self.store,hub=self.hub,repository=self.repo,workers=1,
            poll_interval=.01,supported_packages=self.runtime.supported_packages).start()
