"""Rooted managed closure with staged local admission and history import.

DurableStack supplies the optional validated SQLite commit/recovery boundary.
Dynamic cyclic ownership changes and remote retained import fail explicitly.
"""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from collections import deque, defaultdict
from threading import RLock
import hashlib
import hmac
import json
from pathlib import Path
from blue_contracts.catalogue import Catalogue
from blue_contracts.patch import CapabilityError
from blue_contracts.patch import ContractError
from blue_contracts.legacy_processor import Processor
from blue_contracts.patch import apply
from blue_contracts.catalogue import compact
from blue_bex import Gas, GasExhausted, BexError
from blue_bex.values import clone, pointer_get, segments, escape, UNDEFINED
from .compiler import compile_channels
from .model import Snapshot, DocumentView, Occurrence, Entry
from .graph import forward_domain, entry_owners, derive_context, semantic_snapshot_identity, vertex_simple_routes
from .identity import H, canonical_bytes, history_basis, delivery_basis, rooted_invocation, terminal_key
from .feeder import HostStep, Feeder
from .errors import CoordinationError, Code, require
from .managed import ManagedAdmissions

def reference_hash(domain,value):
    """Inspection/receipt identity only; never BlueId or a Java wire envelope."""
    data=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    return 'sha256:'+hashlib.sha256(domain.encode('ascii')+b'\0'+data).hexdigest()

PROFILE = reference_hash('blue-python-stack-profile/1',{'name':'rooted-managed-closure','revision':'2'})

@dataclass
class GraphState:
    documents: dict
    ids: dict
    edges: dict
    epochs: dict
    initials: dict
    bases: dict
    channels: dict = field(default_factory=dict)
    revision: int = 0
    generations: dict = field(default_factory=dict)
    catchups: dict = field(default_factory=dict)
    births: dict = field(default_factory=dict)

@dataclass(frozen=True)
class Receipt:
    identity: str
    invocation: str
    entry_blue_id: str
    status: str
    before_identity: str
    after_identity: str
    owners: tuple
    work_order: tuple
    events: tuple
    gas_used: int
    trace: tuple
    rejected: dict | None
    detail: str = ''


def reach(edges,root):
    seen=set();todo=[root]
    while todo:
        node=todo.pop()
        if node in seen:continue
        seen.add(node);todo.extend(edges.get(node,{}).values())
    return seen


def components(nodes,edges):
    """Deterministic SCC partition; restricted to an already rooted domain."""
    nodes=set(nodes);forward={n:set(edges.get(n,{}).values())&nodes for n in nodes}
    reverse={n:set() for n in nodes}
    for n,targets in forward.items():
        for t in targets:reverse[t].add(n)
    remaining=set(nodes);out=[]
    def walk(start,adj):
        seen=set();todo=[start]
        while todo:
            x=todo.pop()
            if x in seen:continue
            seen.add(x);todo.extend(adj[x]-seen)
        return seen
    while remaining:
        first=min(remaining);component=walk(first,forward)&walk(first,reverse)
        out.append(tuple(sorted(component)));remaining-=component
    return tuple(sorted(out))


def put(document,path,value):
    return apply(document,{'op':'add','path':path,'val':value})

class ClosureHost(ManagedAdmissions):
    def __init__(self,catalogue:Catalogue,*,processor=None,seal_key=None,attachment_mode='FULL_HISTORY'):
        self.cat=catalogue;self.blue=catalogue.blue;self.registry=catalogue.registry
        self.processor=processor if processor is not None else Processor(catalogue)
        if attachment_mode not in ('FULL_HISTORY','FUTURE_ONLY'):raise ValueError('unsupported managed attachment mode')
        self.attachment_mode=attachment_mode
        self.roots={};self.receipts={};self.saved_originals={};self.published=[]
        self.terminals={};self._issued={};self._base_admissions={};self._cohorts={};self._authored_ids=set();self._lock=RLock()
        self.profile=reference_hash('blue-python-stack-profile/1',{'profile':PROFILE,
            'specifications':{k:v.blue_id for k,v in catalogue.specs.items()},
            'languagePolicy':catalogue.language._policy(),
            'executionProfile':getattr(catalogue.registry,'profile_identity',None),
            'repository':getattr(getattr(catalogue,'repository',None),'identity',None),
            'attachmentMode':attachment_mode,
            'implementation':self._implementation_binding()})
        if getattr(self.processor.bex,'intrinsics',{}):
            raise CapabilityError('managed custom intrinsics require a production runtime-semantics binding adapter')
        # Public fixture key is not a production trust configuration.
        self._key=seal_key if seal_key is not None else b'blue-stack-fixture-seal-not-secret'
        self.required_retained={}
        self.histories={}
        self.on_commit=lambda roots:None
        self.validate_routes=lambda state:None

    @staticmethod
    def _implementation_binding():
        base=Path(__file__).resolve().parents[1]
        files=sorted(p for folder in ('blue_bex','blue_contracts','blue_coordination','blue_runtime','blue_repository') for p in (base/folder).rglob('*.py'))
        return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

    def _seal(self,payload):return hmac.new(self._key,canonical_bytes(payload),hashlib.sha256).hexdigest()

    def finalize(self,documents,edges):
        docs=clone(documents);ids={};parts=components(docs,edges);which={n:i for i,c in enumerate(parts) for n in c};done=set()
        def finish(i):
            if i in done:return
            members=parts[i]
            for n in members:
                for target in edges.get(n,{}).values():
                    if target not in docs:raise CapabilityError('managed dependency unavailable')
                    if which[target]!=i:finish(which[target])
            cyclic=len(members)>1 or any(t==members[0] for t in edges.get(members[0],{}).values())
            raws=[]
            for n in members:
                raw=clone(docs[n])
                for path,target in sorted(edges.get(n,{}).items()):
                    tid='this#'+str(members.index(target)) if cyclic and which[target]==i else ids[target]
                    raw=put(raw,path,{'blueId':tid})
                raws.append(self.cat.normalize_types(raw))
            if cyclic:
                result=self.cat.language.finalize([json.dumps(x,ensure_ascii=False) for x in raws],publish=True,goal='definition')
                for n,tid in zip(members,result['blueIds']):ids[n]=tid
                for n in members:docs[n]=compact(self.blue.tree(self.blue.get(ids[n],goal='definition')))
            else:
                exact,body=self.cat.admit(raws[0]);ids[members[0]]=exact.blue_id;docs[members[0]]=body
            done.add(i)
        for i in range(len(parts)):finish(i)
        return docs,ids

    def _declared(self,document):
        contracts=self.cat.effective_contracts(document);paths=[]
        for c in contracts.values():
            if self.cat.role(c)!='process_embedded':continue
            paths.extend(c.get('paths',[]))
            for p in c.get('collectionPaths',[]):
                collection=pointer_get(document,p)
                if collection is UNDEFINED:continue
                if type(collection) is not dict:raise ContractError('embedded collection must be object')
                paths.extend(p.rstrip('/')+'/'+escape(k) for k in sorted(collection))
        if len(set(paths))!=len(paths):raise ContractError('duplicate managed path')
        for p in paths:
            if not segments(p):raise ContractError('managed root occurrence is forbidden')
        return tuple(sorted(paths))

    def admit_graph(self,documents,edges,*,public_roots):
        """Explicit graph authoring/admission, not a proof-free historical attach.

        Inputs may use aliases. Managed edges MUST be declared in Process
        Embedded, and are finalized by Language rather than independently hashed.
        Each one-way public root receives its own private dependency projection.
        """
        with self._lock:
            raw={k:self.cat.normalize_types(v) for k,v in documents.items()}
            def reject_authored_progress(value):
                if type(value) is dict:
                    contracts=value.get('contracts')
                    if type(contracts) is dict and {'initialized','terminated','checkpoint','process','managed','runtime'}&contracts.keys():
                        raise CapabilityError('authoring cannot assert processor progress; import needs authenticated history evidence')
                    for child in value.values():reject_authored_progress(child)
                elif type(value) is list:
                    for child in value:reject_authored_progress(child)
            for value in raw.values():reject_authored_progress(value)
            edges={k:dict(v) for k,v in edges.items()}
            for root in public_roots:
                if root not in raw:raise ContractError('unknown public root')
            needed=set().union(*(reach(edges,r) for r in public_roots))
            if needed & self._authored_ids:raise CapabilityError('logical document already admitted; history reset/re-admission requires an evidence adapter')
            if not needed<=raw.keys():raise CapabilityError('missing forward dependency')
            raw={n:raw[n] for n in sorted(needed)};edges={n:edges.get(n,{}) for n in raw}
            # Populate managed placeholder fields before checking collection paths.
            for n in raw:
                for path,target in edges[n].items():
                    if target not in raw:raise CapabilityError('missing managed target')
                    raw[n]=put(raw[n],path,{'blueId':'this#0'})
            # Symbolic bodies cannot enter ordinary admission. Finalize first.
            docs,ids=self.finalize(raw,edges)
            for n in docs:
                if not set(edges[n])<=set(self._declared(docs[n])):raise ContractError('managed binding is not declared by Process Embedded')
            # Initialization is a separate admitted operation here. Its SCC
            # lifecycle-causality semantics are NOT claimed as Java parity.
            initialized={};initial_events={}
            for n in sorted(docs):
                result=self.processor.process(docs[n],{},initialize_only=True,
                    managed_paths=tuple(edges[n]),gas=Gas(1000000,owner=n))
                initialized[n]=result.document
                initial_events[n]=[{'source':n,'blueId':self._event_exact(e).blue_id,'payload':e,
                    'occurrence':reference_hash('blue-python-initialization-event/1',{'target':n,'initial':ids[n],'ordinal':i})}
                    for i,e in enumerate(result.events)]
            docs,ids=self.finalize(initialized,edges)
            initials=dict(ids)
            bases={n:history_basis({'documentId':n,'initialDocumentBlueId':ids[n],
                'runtimeSemanticsIdentity':self.profile,'admission':{'mode':'FULL_HISTORY'}}) for n in docs}
            # Validate every initial channel plan before publishing any root.
            # Language content admission may populate immutable caches, but an
            # invalid channel cannot leave a partially published graph behind.
            initial_channels={}
            for n in sorted(docs):
                initial_channels[n]=compile_channels(self.blue,self.registry,self.blue.get(ids[n],goal='definition'),n,bases[n],trusted_checkpoint=True)[0]
            self.validate_routes(GraphState(docs,ids,edges,{n:0 for n in docs},initials,bases,initial_channels))
            groups={}
            for root in public_roots:
                domain=reach(edges,root);scc=next(c for c in components(domain,edges) if root in c)
                key=min(scc)
                if key not in groups:
                    groups[key]=GraphState({n:clone(docs[n]) for n in domain},{n:ids[n] for n in domain},
                        {n:clone(edges[n]) for n in domain},{n:0 for n in domain},
                        {n:initials[n] for n in domain},{n:bases[n] for n in domain})
                old=self.roots.get(root)
                if old is not None:self._cohorts.get(id(old),set()).discard(root)
                self.roots[root]=groups[key]
                self._cohorts.setdefault(id(groups[key]),set()).add(root)
            for root in public_roots:self.load_root(root)
            for root in public_roots:
                state=self.roots[root]
                state.generations={n:{p:0 for p in state.edges[n]} for n in state.documents}
                self.histories[root]=[self._history_row(root,state,events=initial_events[root],
                    authored=self.cat.validate(documents[root]).blue_id)]
            self._authored_ids.update(needed)
        return {r:self.roots[r].ids[r] for r in public_roots}

    def load_root(self,root):
        with self._lock:
            state=self.roots[root];domain=reach(state.edges,root);views=[];edges=[]
            for n in sorted(domain):
                exact=self.blue.get(state.ids[n],goal='definition')
                channels,operations=compile_channels(self.blue,self.registry,exact,n,state.bases[n],
                    old=state.channels.get(n,()),trusted_checkpoint=True)
                state.channels[n]=channels
                position=reference_hash('blue-python-stack-position/1',{'documentId':n,'basis':state.bases[n],
                                                          'state':state.ids[n],'epoch':str(state.epochs[n])})
                views.append(DocumentView(n,n,exact,state.initials[n],state.bases[n],state.epochs[n],
                    channels,operations,True,position))
                for path,t in sorted(state.edges[n].items()):
                    generation=str(state.generations.get(n,{}).get(path,0))
                    eid=reference_hash('blue-python-stack-occurrence/1',{'parent':n,'basis':state.bases[n],'path':path,'child':t,'generation':generation})
                    edges.append(Occurrence(eid,n,t,path,generation))
            snapshot=Snapshot(root,tuple(views),tuple(edges),state.revision)
            semantic=semantic_snapshot_identity(snapshot)
            token=self._seal({'semantic':semantic,'revision':str(state.revision),'requestedRoot':root})
            snapshot=replace(snapshot,verification_identity=token)
            self._issued[token]=snapshot
            return snapshot

    def verify_snapshot(self,snapshot):
        require(self._issued.get(snapshot.verification_identity)==snapshot,Code.INVALID_EVIDENCE,'snapshot was not inspected by this host')
        current=self.load_root(snapshot.root_view)
        require(current==snapshot,Code.CONFLICT,'stale inspected snapshot')

    def terminal_subject(self,snapshot,view,channel):
        key=(derive_context(snapshot)[1],view.key,channel.source_lineage)
        return self.terminals.get(key)

    def retained_heads(self,snapshot):
        if snapshot.root_view in self.required_retained:
            raise CoordinationError(Code.NEEDS_RESOURCES,'required retained predecessor/import adapter unavailable; live work is blocked')
        return ()
    def live_tie_break(self,snapshot,entry):return canonical_bytes({'entry':entry.blue_id})
    def cause_identity(self,entry):return reference_hash('blue-python-stack-cause/1',{'entry':entry.blue_id})
    def base_invocation_identity(self,snapshot,entry,deliveries,gas_limit):
        base=reference_hash('blue-python-stack-base-invocation/1',{'snapshot':semantic_snapshot_identity(snapshot),
                'entry':entry.blue_id,'gasLimit':str(gas_limit),
                'deliveries':sorted([{'view':d.view_key,'channels':sorted(c.address.channel_key for c in d.source_channels),
                    'operation':{'kind':'NONE'} if d.operation is None else {'kind':'OPERATION','key':d.operation.key}} for d in deliveries],key=canonical_bytes)})
        # This is an internal Feeder admission port, not a network endpoint.
        self._base_admissions[base]=(snapshot,entry,deliveries,gas_limit)
        return base

    def _verify_frozen(self,frozen,gas_limit):
        record=self._base_admissions.get(frozen.base_invocation_identity)
        require(record==(frozen.snapshot,frozen.entry,frozen.deliveries,gas_limit),Code.INVALID_EVIDENCE,'unknown or altered Feeder admission')
        require(frozen.kind=='LIVE',Code.INVALID_EVIDENCE,'wrong input kind')
        _,owner,context,_=derive_context(frozen.snapshot)
        basis=delivery_basis({'operationOwnerIdentity':owner,'causeIdentity':self.cause_identity(frozen.entry),
            'kind':'LIVE','receivingBindings':[c.address.record() for d in frozen.deliveries for c in d.source_channels],
            'sourcePositionIdentity':{'kind':'NONE'}})
        require((frozen.owner_identity,frozen.context_identity,frozen.delivery_identity,
                 frozen.invocation_identity,frozen.terminal_identity)==
                (owner,context,basis,rooted_invocation(frozen.base_invocation_identity,context,basis),terminal_key(owner,basis)),
                Code.INVALID_EVIDENCE,'altered rooted admission envelope')
        self.blue.verify(frozen.entry.exact)
    def process_retained(self,*args):raise CoordinationError(Code.NEEDS_RESOURCES,'retained import requires production Contracts evidence adapter')
    def verify_ready(self,snapshot,windows):self.verify_snapshot(snapshot);self.retained_heads(snapshot)

    def commit_terminal(self,plan,candidate,decisions):
        with self._lock:
            self.verify_snapshot(plan.snapshot);owner=derive_context(plan.snapshot)[1]
            for d in decisions:
                for c in d.observed_channels:self.terminals[(owner,d.view_key,c.source_lineage)]=candidate.entry.blue_id
            statuses={str(d.status) for d in decisions}
            return HostStep(next(iter(statuses)) if len(statuses)==1 else 'MIXED',candidate.entry.blue_id,progress_committed=True)

    def _reader(self,stage,n,overrides=None):
        def read(path,view,local):
            parts=segments(path);document=n;at=local;prefix=[]
            # A finite pointer traverses a finite number of managed edges, even
            # in a cyclic graph. It never recursively flattens an entire SCC.
            for part in parts:
                prefix.append(part);p='/'+'/'.join(escape(x) for x in prefix)
                target=stage.edges.get(document,{}).get(p)
                if target is not None:
                    document=target;at=(overrides or {}).get(target,stage.documents[target]);prefix=[]
                elif type(at) is dict:at=at.get(part,UNDEFINED)
                elif type(at) is list:
                    from blue_bex.values import index
                    try:at=at[index(part,len(at))]
                    except BexError:return UNDEFINED
                else:return UNDEFINED
            if at is UNDEFINED:return UNDEFINED
            # Do not turn whole managed cyclic objects into infinite trees.
            if type(at) in (int,float,str,bool):return at
            return self.cat.read_plain(at)
        return read

    def _route(self,stage,origin,event):
        reverse=defaultdict(list)
        for parent,bindings in stage.edges.items():
            for path,child in bindings.items():reverse[child].append((parent,path))
        out=[];todo=[(origin,'',frozenset({origin}))]
        while todo:
            child,suffix,visited=todo.pop()
            for parent,path in sorted(reverse[child],reverse=True):
                if parent in visited:continue
                source_path=path+suffix;matches=[]
                cs=self.cat.effective_contracts(stage.documents[parent])
                for key,c in sorted(cs.items(),key=lambda p:(p[1].get('order',0),p[0])):
                    if self.cat.role(c)!='embedded_channel' or c.get('sourcePath')!=source_path:continue
                    if 'event'in c and not self.cat.matches(event,c['event']):continue
                    # A delivery is still work when the channel accepts and
                    # no current workflow matches; the processor decides effects.
                    matches.append(key)
                if matches:out.append((parent,tuple(matches),source_path))
                todo.append((parent,source_path,visited|{parent}))
        return sorted(out,key=lambda row:(row[0],row[2],row[1]))

    def _execute(self,frozen,stage,gas_limit,captured=None):
        meter=Gas(gas_limit);work=[];public=[];all_events=[];owned=entry_owners(frozen.snapshot)
        queue=deque()
        captured=clone(self._capture_admissions() if captured is None else captured)
        stage.births={}
        def schedule(parent,path,event,overrides):
            matches=[]
            for key,c in self.cat.effective_contracts(stage.documents[parent]).items():
                if self.cat.role(c)=='embedded_channel' and c.get('sourcePath')==path and ('event' not in c or self.cat.matches(event,c['event'])):
                    matches.append(key)
            if matches:queue.append((parent,tuple(sorted(matches)),event,None,path,clone(overrides)))
        # The entry snapshot freezes external deliveries; deterministic selection
        # is independent of materialization/input-map insertion order.
        # Preserve authored executable subtrees in requests. A resolved business
        # view would manufacture absent declaration fields inside nested
        # workflows (including an event matcher), changing their semantics.
        event=compact(self.blue.tree(frozen.entry.exact))
        event['message']=compact(self.blue.tree(frozen.entry.message))
        for d in sorted(frozen.deliveries,key=lambda d:(d.view_key,d.scope_path)):
            if d.scope_path!='/':raise CapabilityError('nested external channel address adapter is not implemented')
            channels=(d.operation.channel_key,) if d.operation is not None else tuple(c.address.channel_key for c in d.source_channels)
            queue.append((d.view_key,channels,event,None if d.operation is None else d.operation.key,None,None))
        try:
            while queue:
                n,channels,payload,operation,source_path,overrides=queue.popleft();meter.owner=n
                meter.charge('closure.work',amount=10);ordinal=len(work);work.append(n)
                if source_path is not None:meter.charge('contracts.bridge',amount=10)
                before=clone(stage.documents[n]);declared_before=self._declared(before)
                result=self.processor.process(before,payload,channels=channels,operation=operation,gas=meter,
                            managed_paths=tuple(stage.edges[n]),read_document=self._reader(stage,n,overrides),managed_children=True)
                after=result.document
                stage.documents[n]=after
                self._reconcile(stage,n,before,frozen.entry,frozen.invocation_identity,meter,captured,schedule)
                for i,emitted in enumerate(result.events):
                    exact=self.cat.validate(emitted,goal='value')
                    occurrence=reference_hash('blue-python-stack-event-occurrence/1',{'invocation':frozen.invocation_identity,
                        'work':str(ordinal),'emission':str(i),'source':n})
                    row={'source':n,'blueId':exact.blue_id,'occurrence':occurrence,'payload':clone(emitted)}
                    all_events.append(row)
                    # The selected root's event stream is public. SCC ownership
                    # authorizes atomic member publication; it does NOT make
                    # every dependency emission a public root event.
                    if n==frozen.snapshot.root_view:public.append(row)
                    for parent,ch,path in self._route(stage,n,emitted):queue.append((parent,ch,emitted,None,path,None))
            # Original Timeline Entry owns checkpoint subjects, not rewritten payloads.
            for d in frozen.deliveries:
                cs=stage.documents[d.view_key].setdefault('contracts',{})
                checkpoint=cs.setdefault('checkpoint',self.cat.typed('Channel Event Checkpoint',entries={}))
                entries=checkpoint.setdefault('entries',{})
                for channel in d.source_channels:
                    meter.owner=d.view_key;meter.charge('contracts.checkpoint',amount=20)
                    entries[channel.address.channel_key]=self.cat.checkpoint_value(frozen.entry.blue_id)
            domain=set().union(*(reach(stage.edges,n) for n in owned))
            for field in ('documents','ids','edges','epochs','initials','bases','channels','generations'):
                setattr(stage,field,{n:v for n,v in getattr(stage,field).items() if n in domain})
            stage.births={n:v for n,v in stage.births.items() if n in domain}
            docs,ids=self.finalize(stage.documents,stage.edges)
            for n in docs:
                if ids[n]!=stage.ids[n] or n in set(work):stage.epochs[n]+=1
            stage.documents=docs;stage.ids=ids;stage.revision+=1
            for n in docs:stage.channels[n]=self._compile_new(stage,n,frozen.entry)
            self.validate_routes(stage)
            return stage,meter,work,public,all_events,None
        except (BexError,CoordinationError) as e:return None,meter,work,[],all_events,e

    def process_and_publish(self,frozen,gas_limit):
        with self._lock:
            self._verify_frozen(frozen,gas_limit)
            previous=self.receipts.get(frozen.invocation_identity)
            if previous is not None and previous.status=='APPLIED':
                # A response retry may carry the saved *old* inspected snapshot.
                require(self._issued.get(frozen.snapshot.verification_identity)==frozen.snapshot,Code.INVALID_EVIDENCE,'unknown saved original')
                return HostStep('APPLIED',frozen.entry.blue_id,frozen.invocation_identity,previous.gas_used,
                                receipt_identity=previous.identity,progress_committed=True)
            self.verify_snapshot(frozen.snapshot)
            for proof in frozen.evidence:self.blue.verify(proof)
            before=self.roots[frozen.snapshot.root_view];original=clone(before)
            saved={'state':original,'frozen':frozen,'gas_limit':gas_limit,'admissions':self._capture_admissions()}
            self.saved_originals[frozen.invocation_identity]=saved
            stage,meter,work,public,all_events,error=self._execute(frozen,clone(before),gas_limit,saved['admissions'])
            before_id=semantic_snapshot_identity(frozen.snapshot)
            after_id=before_id if stage is None else reference_hash('blue-python-stack-output/1',{'ids':stage.ids,'epochs':{k:str(v) for k,v in stage.epochs.items()}})
            status='APPLIED' if error is None else getattr(error,'code','CONTRACT_FATAL')
            detail='' if error is None else str(error)
            rid=reference_hash('blue-python-stack-receipt/1',{'invocation':frozen.invocation_identity,'status':str(status),
                'before':before_id,'after':after_id,'gas':str(meter.used),'trace':meter.trace,'rejected':meter.rejected,
                'work':work,'events':[e['occurrence'] for e in public]})
            receipt=Receipt(rid,frozen.invocation_identity,frozen.entry.blue_id,str(status),before_id,after_id,
                tuple(sorted(entry_owners(frozen.snapshot))),tuple(work),tuple(public),meter.used,tuple(clone(meter.trace)),
                clone(meter.rejected),detail)
            self.receipts[frozen.invocation_identity]=receipt
            if stage is not None:
                # One atomic lock-protected commit; independent one-way source
                # roots are different GraphState objects and are never replaced.
                cohort=self._cohorts.pop(id(before),{frozen.snapshot.root_view})
                for root in cohort:
                    require(self.roots[root] is before,Code.CONFLICT,'owned cohort changed')
                for root in cohort:self.roots[root]=stage
                self._cohorts[id(stage)]=cohort
                self.published.extend(clone(public))
                for target,row in stage.births.items():
                    domain=reach(stage.edges,target)
                    child=GraphState(**{field:{n:clone(getattr(stage,field)[n]) for n in domain}
                        for field in ('documents','ids','edges','epochs','initials','bases','channels','generations')})
                    self.roots[target]=child;self._cohorts[id(child)]={target};self._authored_ids.add(target)
                    self.histories[target]=[clone(row)]
                for root in sorted(cohort|set(stage.births)):
                    rows=self.histories[root]
                    if stage.epochs[root]>rows[-1]['epoch']:
                        rows.append(self._history_row(root,stage,previous=rows[-1],entry=frozen.entry,receipt=rid,
                            events=[e for e in all_events if e['source']==root]))
                admitted_roots=cohort|set(stage.births)
                stage.births={}
                self.on_commit(admitted_roots)
            return HostStep(str(status),frozen.entry.blue_id,frozen.invocation_identity,meter.used,detail,rid,stage is not None)

    def replay_saved(self,invocation):
        saved=self.saved_originals[invocation]
        stage,meter,work,public,all_events,error=self._execute(saved['frozen'],clone(saved['state']),saved['gas_limit'],saved.get('admissions'))
        receipt=self.receipts[invocation]
        after=saved['frozen'].snapshot
        after_id=semantic_snapshot_identity(after) if stage is None else reference_hash('blue-python-stack-output/1',{'ids':stage.ids,'epochs':{k:str(v) for k,v in stage.epochs.items()}})
        ok=(after_id==receipt.after_identity and meter.used==receipt.gas_used and tuple(work)==receipt.work_order
            and tuple(meter.trace)==receipt.trace and meter.rejected==receipt.rejected and tuple(public)==receipt.events)
        return {'verified':ok,'gas':meter.used,'work':work,'status':'APPLIED' if error is None else str(getattr(error,'code','CONTRACT_FATAL'))}

    def selected(self,root,document=None):
        with self._lock:return clone(self.roots[root].documents[document or root])
