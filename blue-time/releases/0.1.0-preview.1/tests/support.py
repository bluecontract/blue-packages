"""Explicit in-memory conformance fixture, NOT a production Time runtime.

Uses the attached Contracts/BEX interpreters. Owner inputs and time/completeness
are trusted test facts, not provider evidence. No storage, worker, graph or auth
qualification is claimed. Nothing here is installed by reading a .bluepkg.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from collections.abc import Mapping
import sys
ROOT=Path(__file__).resolve().parents[1]
SHARED=ROOT.parent
PYTHON=SHARED.parent/'blue-python'
if (PYTHON/'src').is_dir():sys.path.insert(0,str(PYTHON/'src'))
from blue_packages import Runtime, read_package, mount
from blue_contracts import RuntimeBinding, ContractError
from blue_bex import Engine, Context, DEFAULT, UNDEFINED
from blue_bex.values import blue_value
from blue_language.physical import PhysicalCache
from vendor import yaml
SAFE=(1<<53)-1
ACTIVATION=1790931600000000
REMINDER=1790856000000000
OPERATION_TIME=1790848800000000

def load(name='two-timers.blue'):
    return yaml.safe_load((ROOT/'examples'/name).read_text())

def thaw(value):
    if isinstance(value,Mapping):return {k:thaw(v) for k,v in value.items()}
    if type(value) in (list,tuple):return [thaw(x) for x in value]
    return value

def check_request(value,cancel=False,typed=False):
    if type(value) is not dict:raise ContractError('TIME_REQUEST_NOT_OBJECT')
    required={'channel','key'} if cancel else {'channel','timestamp'}
    allowed=required if cancel else required|{'key','context'}
    if typed:required=required|{'type'};allowed=allowed|{'type'}
    if not required<=value.keys() or not value.keys()<=allowed:
        raise ContractError('TIME_INVALID_REQUEST_FIELDS',fields=list(value),required=sorted(required))
    for field in ('channel','key'):
        if field in value and (type(value[field]) is not str or not value[field]):
            raise ContractError('TIME_INVALID_NAME')
    if not cancel and (type(value['timestamp']) is not int or not 0<=value['timestamp']<=SAFE):
        raise ContractError('TIME_INVALID_TIMESTAMP')

class MeterProxy:
    """Debits the same Contracts allowance, before each BEX charge."""
    def __init__(self,meter):self.meter=meter;self.used=0;self.trace=[]
    def charge(self,counter,units=1,*,amount=None):
        expected=DEFAULT[counter]*units
        if amount is not None and amount!=expected:raise ContractError('FIXTURE_TARIFF_MISMATCH')
        self.meter.charge(counter,units)
        self.trace.append({'counter':counter,'units':units,'amount':expected});self.used+=expected

class StepFixture:
    def __init__(self,host,cancel=False):self.host=host;self.cancel=cancel
    def execute(self,c):
        if 'request' not in c.body:raise ContractError('TIME_MISSING_REQUEST')
        expression=thaw(c.body['request'])
        bindings={'call':c.call if c.call is not None else UNDEFINED,
                  'timestamp':c.timestamp if c.timestamp is not None else UNDEFINED,
                  'processingEvent':c.event if c.processing_event is not None else UNDEFINED}
        context=Context(event=c.event,current_contract={'request':expression},steps=thaw(c.steps),
                        bindings=bindings,read_document=lambda path,view,doc:thaw(c.read(path)))
        result=Engine().execute({'expr':expression},context,gas=MeterProxy(c.gas))
        if result.events or result.changeset:raise ContractError('TIME_EFFECTFUL_ARGUMENTS')
        request=blue_value(result.value)
        c.gas.charge('validate',len(request) if type(request) is dict else 1)
        check_request(request,self.cancel)
        name='Cancel Timer Request' if self.cancel else 'Timer Request'
        return {'events':[{'type':{'blueId':self.host.package.exports[name]},**request}]}

class TimerChannelFixture:
    def __init__(self,host):self.host=host
    def verify_admission(self,c):
        if c.evidence is None:return {'allowed':False}
        ticket=self.host.ticket
        if ticket is None:raise ContractError('TIME_NO_FIXTURE_TICKET')
        if (dict(c.evidence)!=ticket['evidence'] or c.snapshot!=ticket['snapshot']
            or c.event!=ticket['event'] or c.timestamp!=ticket['timestamp']):
            raise ContractError('TIME_FIXTURE_EVIDENCE_MISMATCH')
        rid=ticket['registrationId']
        if rid not in self.host.pending:raise ContractError('TIME_NOT_PENDING')
        row=self.host.pending[rid]
        if c.timestamp!=row['request']['timestamp']:raise ContractError('TIME_TIMESTAMP_MISMATCH')
        if self.host.time_reached<c.timestamp or self.host.closed_through<c.timestamp:
            raise ContractError('TIME_INCOMPLETE')
        members=[dict(row) for row in c.members]
        selected=next((r for r in members if r['member']==ticket['member'] and r['channel']==ticket['channel']),None)
        if selected is None or selected['generation']!=ticket['generation']:
            raise ContractError('TIME_CHANNEL_GENERATION_MISMATCH')
        return {'allowed':True,'member':ticket['member'],'channel':ticket['channel'],'generation':ticket['generation']}
    def accept(self,c):
        c.gas.charge('accept')
        return bool(c.evidence and c.evidence['allowed'] and c.member==c.evidence['member']
                    and c.channel==c.evidence['channel'] and c.generation==c.evidence['generation'])

class OwnerChannelFixture:
    """Synthetic owner delivery; deliberately NOT Timeline authentication."""
    def accept(self,c):
        c.gas.charge('accept')
        return c.event.get('channel')==c.channel and type(c.event.get('operation')) is str

class Host:
    def __init__(self,document=None,*,install=True):
        self.cache=PhysicalCache(65536).scope();self.cache.__enter__()
        self.runtime=Runtime.agreements(packages=SHARED)
        language=self.runtime.language()
        coordination=self.runtime.mount(language,'blue-coordination','Coordination')
        self.package=read_package(ROOT/'dist/package.bluepkg')
        mount(language,self.package,'Time',list(self.package.exports))
        self.p=self.runtime.contracts(language)
        self.p.blue.refresh()
        self.rules=self.package.manifest['exports'][0]['specificationMetadata']
        self.time_type=self.package.exports['Timer Channel']
        self.pending={};self.terminal={};self.seen_effects=set();self.ticket=None;self.state=None
        self.time_reached=0;self.closed_through=0;self.floor=None;self.firings=[]
        self.source=deepcopy(document if document is not None else load())
        # Test-only owner admission still uses the exact attached channel type.
        coord_type=coordination.exports['Timeline Channel']
        coord_rules=coordination.manifest['exports'][0]['specificationMetadata']
        self.p.install_runtime(RuntimeBinding(coord_type,coord_rules,'external-channel',
            ('timeline','actor'),(),'testOwnerDelivery',(('accept',1),)),OwnerChannelFixture())
        if install:self.install_time()
    def close(self):self.cache.__exit__(None,None,None)
    def install_time(self):
        self.p.install_runtime(RuntimeBinding(self.time_type,self.rules,'external-channel',(),(),
            'testTimeAdmission',(('accept',1),)),TimerChannelFixture(self))
        for name,cancel in [('Schedule Timer',False),('Cancel Timer',True)]:
            self.p.install_runtime(RuntimeBinding(self.package.exports[name],self.rules,'step',(),('request',),
                'testTimeCancel' if cancel else 'testTimeSchedule',tuple(sorted({**DEFAULT,'validate':1}.items()))),StepFixture(self,cancel))
    def identity(self,value):return self.p.blue.identity(self.p.blue.source(value))
    def initialize(self):
        result=self.p.initialize(self.source if self.state is None else self.state)
        self.commit(result)
        return result
    def commit(self,result,position=None):
        if not result.commits:return
        pending=deepcopy(self.pending);terminal=dict(self.terminal);seen=set(self.seen_effects)
        floor=position if position is not None else self.floor
        for i,event in enumerate(self.p.emitted(result)):
            type_id=event.get('type',{}).get('blueId')
            cancel=type_id==self.package.exports['Cancel Timer Request']
            if not cancel and type_id!=self.package.exports['Timer Request']:continue
            occurrence=self.identity({'sourceReceipt':result.receipt,'ordinal':i})
            if occurrence in seen:continue
            check_request(event,cancel,True)
            seen.add(occurrence)
            channel=event['channel'];doc=result.snapshot.documents[result.snapshot.root]
            declarations=self.p.registry.contracts(doc.body)
            if channel not in declarations or declarations[channel]['type']['blueId']!=self.time_type:
                raise ContractError('TIME_INVALID_CHANNEL')
            generation=doc.channel_lives[channel].generation
            key=event.get('key')
            matching=[rid for rid,row in pending.items() if row['channel']==channel and row['generation']==generation
                      and key is not None and row['request'].get('key')==key]
            for rid in matching:terminal[rid]='CANCELLED' if cancel else 'REPLACED';del pending[rid]
            if cancel:continue
            t=event['timestamp']
            if floor is not None and (t<floor[0] or t==floor[0] and floor[1]=='timer'):
                raise ContractError('TIME_DEADLINE_BEFORE_POSITION')
            descriptor={'domain':'Time/registration/1','contextId':'test-context','documentId':'test-document',
                        'channel':channel,'channelGeneration':generation,
                        'occurrenceId':occurrence}
            rid=self.identity(descriptor)
            if rid in terminal:continue
            pending[rid]={'request':deepcopy(event),'requestId':result.public_events[i]['event'],
                          'channel':channel,'generation':generation}
        self.pending=pending;self.terminal=terminal;self.seen_effects=seen;self.state=result.snapshot
        if position is not None:self.floor=position
    def invoke(self,event=None,timestamp=OPERATION_TIME):
        if self.floor is not None and timestamp<self.floor[0]:raise ContractError('FIXTURE_INPUT_BEFORE_POSITION')
        if any(row['request']['timestamp']<timestamp for row in self.pending.values()):
            raise ContractError('FIXTURE_PENDING_TIMER_PRECEDES_INPUT')
        result=self.p.process(self.state,event if event is not None else load('schedule-reminder.blue'),timestamp)
        self.commit(result,(timestamp,'external'))
        return result
    def progress(self,timestamp,closed_through=None):
        self.time_reached=max(self.time_reached,timestamp)
        if closed_through is not None:self.closed_through=max(self.closed_through,closed_through)
    def ordered(self):
        return sorted(self.pending,key=lambda rid:(self.pending[rid]['request']['timestamp'],
                      self.pending[rid]['channel'].encode(),rid.encode()))
    def prepare_firing(self,rid):
        row=self.pending[rid]
        event={'type':{'blueId':self.package.exports['Timer Fired']},'registrationId':rid,'request':{'blueId':row['requestId']}}
        event_node=self.p.blue.source(event);event_id=self.p.blue.identity(event_node)
        evidence={'fixtureTicket':self.identity({'snapshot':self.state.identity,'event':event_id})}
        self.ticket={'evidence':deepcopy(evidence),'snapshot':self.state.identity,'event':event_id,
                     'timestamp':row['request']['timestamp'],'registrationId':rid,'member':self.state.root,
                     'channel':row['channel'],'generation':row['generation']}
        return event,event_node,{self.time_type:evidence}
    def deliver(self,event_node,timestamp,evidence):
        attempt=self.p.prepare_invocation(self.state,event_node,timestamp,evidence=evidence)
        while (token:=self.p.next_chunk(attempt)) is not None:
            self.p.accept_chunk(attempt,token,self.p.execute_chunk(token))
        return self.p.finish(attempt)
    def fire_next(self):
        candidates=self.ordered()
        if not candidates:return None
        rid=candidates[0];t=self.pending[rid]['request']['timestamp']
        if self.time_reached<t or self.closed_through<t:return None
        event,node,evidence=self.prepare_firing(rid)
        try:
            result=self.deliver(node,t,evidence)
            if not result.commits:raise ContractError('FIXTURE_TIMER_EXECUTION_FAILED',diagnostic=result.diagnostic)
            self.commit(result,(t,'timer'))
            self.pending.pop(rid,None);self.terminal[rid]='FIRED'
            self.firings.append({'event':self.p.blue.project(node),'requestBlueId':event['request']['blueId'],
                                 'logicalTimestamp':t,'gas':result.gas})
            return result
        finally:self.ticket=None
    def drain(self):
        rows=[]
        while (result:=self.fire_next()) is not None:rows.append(result)
        return rows
    def business(self):
        return {k:self.p.read(self.state,'/'+k) for k in ('status','reminderCount','lastReminder')}
