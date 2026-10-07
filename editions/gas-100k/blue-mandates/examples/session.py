"""Local signed-Timeline example harness. No authority or lifecycle is evaluated here."""
from pathlib import Path
import sys,time,json,os
from copy import deepcopy
from blue_packages import Runtime
from blue_repository import Repository
from functools import lru_cache

@lru_cache(maxsize=1)
def repository():
    p=Runtime.mandates().packages.package('blue-mandates')
    return Repository.from_payload('mandates', {'Mandates/'+name:bid for name,bid in p.exports.items()},p.repository.records)

from algorithms import blue as L
from blue_coordination.engine import CoordinationEngine, SourceHub, MemoryStore
from blue_coordination.engine.content import mount_business_repository
from blue_coordination.engine.mandate_package import supported_definition
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def operation(channel,body,request=None):
    return {'type':'Contracts/Sequential Workflow Operation','channel':channel,
        'request':{} if request is None else request,'steps':[{'type':'Contracts/Compute','do':body}]}
def change(path,value):return {'$appendChange':{'op':'replace','path':path,'val':value}}
def workflow(channel,event,body):
    return {'type':'Contracts/Sequential Workflow','channel':channel,'event':event,
        'steps':[{'type':'Contracts/Compute','do':body}]}

class Session:
    def __init__(self,*,store=None,enabled=True,workers=1,name='demo',auto_complete=True):
        self.runtime=Runtime.mandates();self.repo=repository();self.store=store or MemoryStore();self.hub=SourceHub(self.store,auto_complete=auto_complete,runtime=self.runtime)
        mount_business_repository(self.hub.processor.blue.language,self.repo)
        self.hub.processor.blue.refresh()
        self.keys={k:Ed25519PrivateKey.generate() for k in ('holder','agent','provider','other')}
        self.providers={k:self.hub.create(name+'-'+k,[name+'-'+k],key=self.keys[k]) for k in self.keys}
        self.actors={k:next(iter(p.actors)) for k,p in self.providers.items()}
        self.engine=CoordinationEngine(store=self.store,hub=self.hub,repository=self.repo,
            workers=workers,poll_interval=.02,supported_packages=self.runtime.supported_packages if enabled else Runtime.agreements().supported_packages).start()
        self.time=0;self.trace=[]
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def close(self):self.engine.close()
    def typ(self,name,**fields):return {'type':{'blueId':self.repo.aliases['Mandates/'+name]},**fields}
    def channel(self,side,provider=None):
        return self.hub.catalogue.typed('Timeline Channel',timeline={'blueId':(provider or self.providers[side]).timeline},actor={'blueId':self.actors[side]})
    def wait(self,handle,predicate=None,seconds=40,allow_error=False):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            row=self.engine.get(handle)
            if not allow_error and row['processing']['state']=='ERROR':raise RuntimeError(json.dumps(row['processing'],default=str))
            if predicate(row) if predicate is not None else row['lastStable'] is not None:return row
            time.sleep(.015)
        raise TimeoutError(json.dumps(self.engine.get(handle),default=str)[:4000])
    def add(self,source):
        h=self.engine.add(source);self.wait(h);return h
    def row(self,h):return self.engine.get(h)
    def read(self,h,path=''):
        bid=self.row(h)['lastStable']['blueId']
        with self.hub.lock,self.hub.cache.scope(),self.store.read() as view:
            p=self.hub.processor;p.blue.language.bind(view);p.blue.refresh()
            try:return p.blue.read(L.Ref(bid),path)
            finally:p.blue.language.bind(None);p.blue.refresh()
    def value_id(self,h,path):
        bid=self.row(h)['lastStable']['blueId']
        with self.hub.lock,self.hub.cache.scope(),self.store.read() as view:
            p=self.hub.processor;p.blue.language.bind(view);p.blue.refresh()
            try:return p.blue.identity(p.blue.exact(p.blue.select(L.Ref(bid),path)))
            finally:p.blue.language.bind(None);p.blue.refresh()
    def counter_source(self,*,include_agent=True,count=0,agent_provider=None,name='Counter'):
        source={'name':name,'count':count,'contracts':{'ownerChannel':self.channel('holder'),
            'increment':operation('ownerChannel',[change('/count',{'$add':[{'$document':'/count'},{'$binding':'call/request/amount'}]})],{'amount':{'type':'Integer','schema':{'required':True}}})}}
        if include_agent:source['contracts']['agentChannel']=self.channel('agent',agent_provider)
        return source
    def grant(self,target,operation_name='increment',channel='ownerChannel',**extra):
        return self.typ('Operation Grant',target={'initialDocument':{'blueId':self.row(target)['documentId']},'channel':channel,'operation':operation_name},**extra)
    def mandate_source(self,scope=None,type_name='Operation Mandate',**extra):
        return self.typ(type_name,scope=scope or {},contracts={'authorityHolderChannel':self.channel('holder'),'authorizedActorChannel':self.channel('agent')},**extra)
    def invoke(self,side,h,operation_name,request=None,*,channel=None,authority=None,exact=False,document=None,provider=None,expect_error=False):
        before=self.row(h)['lastStable'];self.time+=100
        default={'holder':'authorityHolderChannel','agent':'authorizedActorChannel','provider':'evidenceProviderChannel'}
        message={'type':'Contracts/Operation Request','document':{'blueId':document or before['blueId']},
            'channel':channel or default[side],'operation':operation_name,'request':{} if request is None else request}
        if exact:message['requireExactDocumentVersion']=True
        if os.environ.get('TRACE_SESSION'):print('APPEND',operation_name,self.time,flush=True)
        entry=self.hub.append((provider or self.providers[side]).timeline,self.actors[side],self.time,message,**({'authority':authority} if authority else {}))
        if os.environ.get('TRACE_SESSION'):print('APPENDED',operation_name,flush=True)
        timestamp=self.time
        row=self.wait(h,lambda r:(r['lastStable'] is not None and r['lastStable']['epoch']>before['epoch']) or
            r['processing']['checkedBoundary']>timestamp or (expect_error and r['processing']['state']=='ERROR'),allow_error=expect_error)
        if os.environ.get('TRACE_SESSION'):print('OBSERVED',operation_name,row['processing']['state'],flush=True)
        self.trace.append({'operation':operation_name,'actor':side,'entry':entry.blue_id,'timestamp':timestamp,'document':h,
            'epoch':row['lastStable']['epoch'] if row['lastStable'] else None,'state':row['processing']['state'],'disposition':row.get('lastInputDisposition')})
        return entry
    def approve(self,h):return self.invoke('holder',h,'approveMandate',exact=True)
    def authority(self,h,holder='holder'):
        return self.engine.publish_content(self.typ('Mandate Authority',actor={'blueId':self.actors[holder]},mandate={'blueId':self.row(h)['documentId']}))
    def events(self):
        with self.hub.lock,self.hub.cache.scope(),self.store.read() as view:
            p=self.hub.processor;p.blue.language.bind(view);p.blue.refresh()
            try:return [{'occurrence':key,**row,'content':p.blue.literal(L.Ref(row['event']['event']))} for key,row in view.scan('outbox','default/')]
            finally:p.blue.language.bind(None);p.blue.refresh()
    def restart(self):
        self.engine.close()
        for provider in self.providers.values():self.hub.adopt(provider)
        self.engine=CoordinationEngine(store=self.store,hub=self.hub,repository=self.repo,workers=1,poll_interval=.02,supported_packages=self.runtime.supported_packages).start()
