"""Automatic managed documents: append accepted inputs, then read stable results."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import fields
from threading import Event, Thread, RLock, local
from collections import OrderedDict, deque
import sqlite3
import time
from uuid import uuid4, uuid5, NAMESPACE_URL
from algorithms import blue as L
from blue_host import HostIncomplete, HOST_FAILURES, incomplete
from blue_contracts import Processor, ContractError, NeedResources
from blue_contracts.reference.model import Outcome
from blue_contracts.reference.graph import Graph, Archive, components
from blue_contracts.reference.channels import operation_request, leaves
from blue_runtime.record_bridge import install_record_bridge
from blue_runtime.indexed_topology import topology_scope
from blue_runtime.sealed import sealed_scope
from blue_runtime.syntax_cache import syntax_scope
from blue_language.physical import PhysicalCache
from blue_coordination_spec.model import require, CoordinationError, Entry
from .store import MemoryStore, PublicationUnknown, fingerprint
from .work import WorkQueue, WavePlanner, wake, publish
from .catalogue import Catalogue
from .content import StoreLanguage, rooted, restore_local, prepare_content, content_writes, cache_declarations, mount_business_repository
from .history import HistoryResolver
from .admission import install, channels
from .hub import SourceHub
from .mandates import validate_result as validate_mandate_result
from .attachments import attachments, next_history
from . import rebase
from .source_records import entries as source_entries


class LocalCompletionReader:
    """Only protected local publications use this path; no web upload calls it."""
    def __init__(self, language, context):
        self.language, self.context = language, context

    def read_completed(self, processor, reference):
        row = self.language.view.get('outcomes', self.context + '/' + reference)
        require(row is not None and row['before'] is not None, 'WAITING_SOURCE_COMPLETION', receipt=reference)
        established = self.language.view.get('established', self.context + '/' + row['receipt'])
        require(established == {'receipt': reference}, 'UNESTABLISHED_LOCAL_COMPLETION')
        observations = row['observations']
        before = restore_local(processor, row['before'])
        after = restore_local(processor, row['after'])
        result = Outcome(observations['status'], after, observations['input'], observations['invocation'],
            public_events=observations['publicEvents'], event_trace=observations['events'], work_trace=observations['work'],
            changes=observations['changes'], checkpoints=observations['checkpoints'], gas=observations['gas'],
            gas_trace=observations['gasTrace'], rejected=observations['rejected'], diagnostic=observations['diagnostic'],
            completions=observations['completions'], rounds=observations['rounds'], units=observations['units'])
        require(result.receipt == row['receipt'], 'CORRUPT_LOCAL_COMPLETION')
        return before, result, row['event'], row['timestamp']


def execute(processor, attempt):
    if processor.local_driver:
        result = processor.complete_local(attempt)
    else:
        while (token := processor.next_chunk(attempt)) is not None:
            processor.accept_chunk(attempt, token, processor.execute_chunk(token))
        result = processor.finish(attempt)
    processor.observe_execution('outcome', gas=result.gas, status=result.status, invocation=result.invocation)
    return result


def require_complete(result):
    if result.commits:return
    if result.status == 'NEEDS_RESOURCES':
        raise NeedResources(*result.diagnostic.get('required', []))
    raise CoordinationError(result.diagnostic.get('code', result.status), status=result.status,
                            diagnostic=result.diagnostic, gas=result.gas)


class CoordinationEngine:
    def __init__(self, *, store=None, hub=None, context='default', workers=2,
                 poll_interval=0.25, repository=None, optimized=True, disabled_optimizations=()):
        if not context or '/' in context:
            raise ValueError('A nonempty execution context token is required')
        self.store = store or MemoryStore()
        self.hub = hub or SourceHub(self.store)
        self.context, self.worker_count, self.poll_interval = context, workers, poll_interval
        self.repository, self.optimized = repository, optimized
        self.disabled_optimizations = frozenset(disabled_optimizations)
        self.queue, self.waves = WorkQueue(self.store), WavePlanner(self.store)
        self._signal, self._stop = Event(), Event()
        self._threads = []
        self._lifecycle_lock = RLock()
        self.hub.on_change = self._signal.set
        self.metrics = dict(invocations=0, receivingApplications=0, sourceReexecutions=0, retries=0,
            planningSeconds=0.0, processorSeconds=0.0, publicationPreparationSeconds=0.0,
            commitSeconds=0.0, restorationSeconds=0.0, dynamicReads=0, bundleReads=0, bodyRecords=0,
            sourceLocalTurns=0, receiverLocalTurns=0, initializationLocalTurns=0, verificationLocalTurns=0,
            adoptionHits=0, adoptionRejections=0, verificationReplays=0, logicalGasAttempted=0,
            logicalGasCommitted=0, contractBodiesOpened=0, selectionSeconds=0.0, queueWaitSeconds=0.0)
        self.metrics['repeatedTurnAttempts'] = 0
        self.metrics['completionLoads'] = 0
        self._metrics_lock = RLock()
        self.execution_observations = deque(maxlen=512)
        self._executions = OrderedDict()
        self._local = local()
        release = {'coordination': self.hub.catalogue.specification,
                   'contracts': self.hub.processor.registry.specification,
                   'storage': 'coordination.records/20260922.6',
                   'scheduling': 'independent-owner-prefix/1'}
        while True:
            with self.store.read() as view:
                established = view.get('engine_contexts', context)
                require(established is None or established == release, 'INCOMPATIBLE_ENGINE_RELEASE', context=context)
                if established is not None:
                    break
                require(not view.scan('managed', context + '/'), 'UNVERSIONED_ENGINE_CONTEXT', context=context)
                packet = view.packet('engine-context:' + context, writes={('engine_contexts', context): release})
            if publish(self.store, packet).status == 'COMMITTED':
                break

    def _measure(self, phase, action):
        started = time.perf_counter()
        try:
            return action()
        finally:
            with self._metrics_lock:
                elapsed=time.perf_counter()-started
                self.metrics[phase] += elapsed
                phases=getattr(self._local,'phases',None)
                if phases is not None:phases[phase]=phases.get(phase,0)+elapsed

    def _observe_execution(self, kind, record, language=None):
        if kind == 'localTurn' and not record['verifying'] and language and language.view:
            identity=self._execution_key(record['member'],record['event'],record['before'],record['phase'])
            record={**record,'previouslyCommitted': language.view.get('executed_turns',identity) is not None}
        with self._metrics_lock:
            self.execution_observations.append({'kind':kind, **record})
            if kind == 'localTurn':
                metric=('verificationLocalTurns' if record['verifying'] else 'initializationLocalTurns'
                    if record['initialization'] else 'receiverLocalTurns' if record['receiving'] else 'sourceLocalTurns')
                self.metrics[metric]+=1
                key=(record['member'],record['event'],record['before'],record['phase'])
                if not record['initialization'] and not record['verifying']:
                    if key in self._executions:self.metrics['repeatedTurnAttempts']+=1
                    if record.get('previouslyCommitted') and not record['receiving']:self.metrics['sourceReexecutions']+=1
                    self._executions[key]=True;self._executions.move_to_end(key)
                    while len(self._executions)>4096:self._executions.popitem(last=False)
            elif kind == 'verificationReplay':self.metrics['verificationReplays']+=1
            elif kind == 'outcome':self.metrics['logicalGasAttempted']+=record['gas']
            elif kind == 'bodyOpened':self.metrics['contractBodiesOpened']+=1
            elif kind == 'adoption':self.metrics['adoptionHits']+=record['count']
            elif kind == 'adoptionRejected':self.metrics['adoptionRejections']+=1

    def _execution_key(self, member, event, before, phase):
        return '/'.join((self.context, member, event or 'initialize', before, phase))

    def start(self):
        with self._lifecycle_lock:
            if self._threads:
                return self
            self._stop.clear()
            self.hub.start()
            for number in range(self.worker_count):
                thread = Thread(target=self._worker, args=(str(uuid4()),), name='blue-coordination-' + str(number), daemon=True)
                thread.start()
                self._threads.append(thread)
            self._signal.set()
        return self

    def close(self):
        self._stop.set()
        self._signal.set()
        for thread in self._threads:
            thread.join(30)
        if any(thread.is_alive() for thread in self._threads):
            raise RuntimeError('A Coordination worker is still completing its atomic invocation')
        self._threads.clear()
        self.hub.close()

    def __enter__(self):
        return self.start()

    def __exit__(self, *_):
        self.close()

    def add(self, document):
        handle = str(uuid4())
        source = {'blueId': document} if isinstance(document, str) else deepcopy(document)
        with self.store.read() as view:
            view.get('registration', handle)
            writes = {('registration', handle): dict(source=source, context=self.context),
                      ('handles', handle): {'instance': handle}}
            wake(view, writes, handle)
            packet = view.packet('register:' + handle, writes=writes, result=handle)
        publish(self.store, packet)
        self._signal.set()
        return handle

    def _instance(self, view, handle):
        row = view.get('handles', handle)
        return row['instance'] if row else handle

    def get(self, handle):
        with self.store.read() as view:
            instance = self._instance(view, handle)
            head = view.get('heads', instance)
            registration = view.get('registration', instance)
            work = view.get('work', instance)
            if head is None and registration is None:
                raise KeyError(handle)
            if head is not None and head['context'] != self.context:
                raise KeyError(handle)
            if registration is not None and registration['context'] != self.context:
                raise KeyError(handle)
            stable = head.get('lastStable') if head else None
            decision=(view.get('assessments',instance+'/'+head['lastOrder'][2])
                      if head and head.get('lastOrder') else None)
            return dict(handle=handle, instance=instance, documentId=head['documentId'] if head else None,
                lastStable=deepcopy(stable), processing=dict(state=work['status'] if work else 'READY',
                    checkedBoundary=head.get('checkedBoundary', 0) if head else 0,
                    issue=work.get('issue') if work else None),
                lastInputDisposition=({k:decision[k] for k in ('entry','order','outcome','reason','decision')}
                    if decision and 'decision' in decision else None),
                channels=deepcopy(head.get('channels', [])) if head else [],
                operations=deepcopy(head.get('operations', [])) if head else [],
                timings=deepcopy(head.get('timings', {})) if head else {})

    def list(self):
        with self.store.read() as view:
            rows = view.scan('managed', self.context + '/')
            pending = [(key, value) for key, value in view.scan('registration') if value['context'] == self.context]
        instances = {row['instance'] for _, row in rows} | {key for key, _ in pending}
        return [self.get(instance) for instance in sorted(instances)]

    def history(self, handle, *, cursor=0, limit=50):
        if type(cursor) is not int or cursor < 0 or type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError('Invalid history page')
        with self.store.read() as view:
            instance = self._instance(view, handle)
            head = view.get('heads', instance)
            if head is None or head['context'] != self.context:
                raise KeyError(handle)
            rows = [row for _, row in view.page('history', instance + '/',
                start=instance+'/'+str(cursor).zfill(16), limit=limit+1)]
            page = rows[:limit]
            return dict(items=page, nextCursor=page[-1]['number'] + 1 if len(rows) > limit else None)

    def publish_content(self, document):
        with self.hub.lock, self.hub.cache.scope():
            c = self.hub.catalogue
            with self.store.read() as content_view:
                c.blue.language.bind(content_view)
                c.blue.refresh()
                try:
                    identity = c.admit(document)
                finally:
                    c.blue.language.bind(None)
            while True:
                with self.store.read() as view:
                    writes = content_writes(c.blue.language.provider, view)
                    packet = view.packet(str(uuid4()), writes=writes)
                if publish(self.store, packet).status == 'COMMITTED':
                    break
            for key in c.blue.language.provider.dirty:
                self.queue.available('content:' + key)
            c.blue.language.provider.acknowledge()
        self._signal.set()
        return identity

    def _worker(self, owner):
        with PhysicalCache(capacity=65536).scope(), self.store.metrics.scope('engine'), topology_scope(
                self.metrics, enabled=self.optimized and 'topology' not in self.disabled_optimizations), sealed_scope(
                self.metrics, enabled=self.optimized and 'receipts' not in self.disabled_optimizations, pool=getattr(self.store,'byte_pool',None)), syntax_scope(
                enabled=self.optimized and 'syntax' not in self.disabled_optimizations):
            language = StoreLanguage(reuse_admission=self.hub.reuse_admission)
            if 'bodies' in self.disabled_optimizations: language.exact_bodies.capacity=512
            if self.repository is not None:
                mount_business_repository(language, self.repository)
            processor = install_record_bridge(Processor(language, local_driver=self.optimized))
            processor.execution_observer = lambda kind,record:self._observe_execution(kind,record,language)
            def observe_attachment(predecessors):
                for member,identity in predecessors.items():
                    self._local.owner_predecessors.setdefault(member,set()).add(identity)
            processor.registry.observe_attachment=observe_attachment
            declaration = processor.registry.declaration
            def observe_declaration(recipe, *, demand=True):
                result=declaration(recipe,demand=demand)
                if demand and result['_role'] in {'workflow','operation','compute','patch_step','emit_step','terminate_step','extension_handler','extension_step'}:
                    processor.observe_execution('bodyOpened', role=result['_role'])
                return result
            processor.registry.declaration=observe_declaration
            catalogue = Catalogue(processor)
            history = HistoryResolver(catalogue, self.context)
            channel_type = install(processor, catalogue, lambda: self.hub.trusted, history)
            processor.install_completion_reader(LocalCompletionReader(language, self.context))
            if self.optimized:
                cache_declarations(processor)
            while not self._stop.is_set():
                try:
                    self._deliver_completion_notices()
                except (PublicationUnknown, OSError, sqlite3.OperationalError, HostIncomplete):
                    with self._metrics_lock:self.metrics['retries'] += 1
                    self._signal.wait(self.poll_interval)
                claim = self.queue.claim(owner, context=self.context)
                if claim is None:
                    self._signal.wait(self.poll_interval)
                    self._signal.clear()
                    continue
                started = time.perf_counter()
                self._local.phases = {}
                with self._metrics_lock:
                    self.metrics['queueWaitSeconds'] += claim.get('queueWaitSeconds',0)
                read_metrics = dict(language.metrics)
                heartbeat_stop = Event()
                def renew():
                    while not heartbeat_stop.wait(self.queue.lease_seconds / 3):
                        if not self.queue.renew(claim):break
                heartbeat = Thread(target=renew, name='blue-worker-lease', daemon=True)
                heartbeat.start()
                try:
                    self._step(processor, catalogue, history, channel_type, claim, started)
                except HOST_FAILURES as error:
                    self._issue(claim,incomplete(error))
                except (NeedResources, CoordinationError, ContractError, L.Failure) as error:
                    self._issue(claim, error)
                except Exception as error:
                    self._issue(claim, error)
                finally:
                    elapsed=time.perf_counter()-started
                    with self._metrics_lock:
                        self.metrics['selectionSeconds'] += max(0,elapsed-sum(self._local.phases.values()))
                    heartbeat_stop.set()
                    heartbeat.join()
                    language.bind(None)
                    try:
                        if self.queue.release_unpublished(claim):
                            self.metrics['retries'] += 1
                    except (OSError, sqlite3.OperationalError):
                        pass  # Durable lease expiry handles an unavailable store.
                    with self._metrics_lock:
                        for key, value in language.metrics.items():
                            self.metrics[key] += value - read_metrics[key]

    def _issue(self, claim, error):
        code = getattr(error, 'code', getattr(error, 'category', type(error).__name__))
        detail = getattr(error, 'context', getattr(error, 'details', {}))
        host = isinstance(error,HOST_FAILURES) or code in ('OperationLimitExceeded','LANGUAGE_OperationLimitExceeded')
        if host:
            code='HOST_INCOMPLETE'
            detail={**detail,'reason':getattr(error,'reason',type(error).__name__)}
        physical = isinstance(error, (OSError, sqlite3.OperationalError))
        waiting = host or physical or isinstance(error, NeedResources) or code.startswith('WAITING_') or code in ('NEEDS_RESOURCES', 'ProviderUnavailable', 'UNESTABLISHED_DOCUMENT_HISTORY')
        if physical:code = 'WAITING_STORAGE_RECOVERY'
        issue = dict(code=code, message=str(error), **detail)
        if getattr(self._local,'cause_order',None) is not None:issue['order']=self._local.cause_order
        try:
            with self.store.read() as view:
                writes = {}
                receiving = getattr(self._local,'receiving',None)
                if receiving is not None:
                    wave=view.get('waves',receiving['wave'])
                    require(wave is not None and (receiving['instance'] in wave['pending'] or
                        wave['phase']=='SOURCE' and receiving['instance']==wave['source']),
                        'LOST_RECEIVING_OBLIGATION')
                    issue.update(order=wave['order'],phase='RECEIVE',receiver=receiving['instance'],wave=wave['identity'])
                    failure={**receiving,'issue':issue,'result':getattr(self._local,'failure_result',None)}
                    writes['receiving_failures',wave['identity']+'/'+receiving['instance']]=failure
                    writes['waves',wave['identity']]={**wave,'status':'WAITING' if waiting else 'ERROR','failure':failure}
                    dependency=dict(code='DEPENDENCY_FAILED',receiver=receiving['instance'],wave=wave['identity'],
                                    order=wave['order'],diagnostic=issue)
                    for member in wave['members']:
                        if member == claim['instance']:continue
                        work=view.get('work',member)
                        if work is not None:
                            status=('WAITING' if waiting else 'ERROR') if member==receiving['instance'] else 'WAITING'
                            writes['work',member]={**work,'status':status,
                                'issue':issue if member==receiving['instance'] else dependency}
                            writes['due',member]=None
                    is_receiver = claim['instance'] == receiving['instance']
                    self.queue.finish(view,writes,claim,status='WAITING' if waiting or not is_receiver else 'ERROR',
                                      issue=issue if is_receiver else dependency,
                                      poll_after=self.poll_interval if waiting and not host else None)
                    publish(self.store,view.packet(str(uuid4()),writes=writes))
                    return
                self.queue.finish(view, writes, claim, status='WAITING' if waiting else 'ERROR', issue=issue,
                                  poll_after=self.poll_interval if waiting and not host else None)
                changed=False
                if code=='WAITING_COMPLETENESS':
                    for resource,observed in getattr(self._local,'wait_resources',{}).items():
                        generation=view.get('availability',resource,{'generation':0})['generation']
                        if generation!=observed: changed=True
                        else: writes['waiters',resource+'/'+claim['instance']]=dict(instance=claim['instance'],generation=generation)
                required=detail.get('required', [])
                missing=False
                for identity in required:
                    resource = 'content:' + identity
                    if view.get('content',identity) is not None:
                        continue
                    missing=True
                    generation = view.get('availability', resource, {'generation': 0})['generation']
                    writes['waiters', resource + '/' + claim['instance']] = dict(instance=claim['instance'], generation=generation)
                # Required can include already opened evidence, not just absent
                # bodies. Existing evidence must not cause a busy retry loop
                # while another required body is still missing. These negative
                # point reads also fence arrivals before waiter publication.
                if required and not missing:changed=True
                if changed:
                    # A dependency arrived before registration; do not sleep past it.
                    for key in list(writes):
                        if key[0]=='waiters': del writes[key]
                    self.queue.finish(view,writes,claim,remaining=True)
                packet = view.packet(str(uuid4()), writes=writes)
            publish(self.store, packet)
        except RuntimeError:
            # A newer fenced worker owns recovery. Never publish a stale error.
            self.metrics['retries'] += 1

    def _reschedule(self, claim):
        with self.store.read() as fresh:
            writes = {}
            self.queue.finish(fresh, writes, claim, remaining=True)
            publish(self.store, fresh.packet(str(uuid4()), writes=writes))
        self._signal.set()

    def retry(self, handle):
        """Retry an operationally incomplete invocation at its original gas."""
        with self.store.read() as view:
            instance=self._instance(view,handle)
            issue=(view.get('work',instance) or {}).get('issue') or {}
            timeline=issue.get('timeline')
        if timeline:self.hub.retry(timeline)
        with self.store.read() as view:
            instance=self._instance(view,handle)
            row=view.get('work',instance)
            require(row is not None and not row['owner'],'WAITING_OWNER_LEASE')
            reservation=view.get('reservation',instance)
            if reservation is not None:
                wave=view.get('waves',reservation['wave'])
                if wave is not None and wave.get('failure'):
                    return self.retry_receiving(handle)
            require((row.get('issue') or {}).get('code')=='HOST_INCOMPLETE','NO_HOST_INTERRUPTION')
            writes={('work',instance):{**row,'issue':None,'status':'WAITING'}}
            wake(view,writes,instance)
            require(publish(self.store,view.packet(str(uuid4()),writes=writes)).status=='COMMITTED','RETRY_CONFLICT')
        self._signal.set()

    def retry_receiving(self, handle):
        """Explicitly revalidate the retained obligation; never rerun its source."""
        with self.store.read() as view:
            instance=self._instance(view,handle)
            reservation=view.get('reservation',instance)
            require(reservation is not None,'NO_RECEIVING_OBLIGATION')
            wave=view.get('waves',reservation['wave'])
            require(wave is not None and wave.get('failure'),'NO_RECEIVING_FAILURE')
            writes={('waves',wave['identity']):{**wave,'status':'PROCESSING','failure':None}}
            for member in wave['members']:
                work=view.get('work',member)
                if work:
                    require(not work['owner'],'WAITING_OWNER_LEASE',instance=member)
                    writes['work',member]={**work,'status':'WAITING','issue':None}
            wake(view,writes,wave['source'])
            require(publish(self.store,view.packet(str(uuid4()),writes=writes)).status=='COMMITTED','RETRY_CONFLICT')
        self._signal.set()

    def _with_history(self, processor, view, action):
        """Resolve only exact views actually requested by the lower processor."""
        loaded = set()
        while True:
            raised = None
            self._local.owner_predecessors={}
            try:
                result = action()
                needed = result.diagnostic.get('required', []) if result.status == 'NEEDS_RESOURCES' else []
            except NeedResources as error:
                raised, needed = error, error.context['required']
                result = None
            candidates = []
            for identity in needed:
                if identity not in loaded:
                    selected = view.get('versions', self.context + '/' + identity)
                    if selected is not None:
                        candidates.append((identity, selected))
            if not candidates:
                if raised:
                    raise raised
                return result
            for identity, selected in candidates:
                processor.blue.language.prefetch(selected['bundle'])
                processor.blue.refresh()
                state = restore_local(processor, selected['snapshot'])
                processor.archive.bind(identity, state.identity)
                loaded.add(identity)
            self.metrics['retries'] += 1

    def _step(self, p, c, history, channel_type, claim, started):
        with self.store.read() as view:
            p.blue.language.bind(view)
            history.bind(view)
            history.delivery_lifetimes = None
            p.archive = Archive()
            p.blue.refresh()
            instance = claim['instance']
            history.receiving_instance = instance
            self._local.receiving = None
            self._local.failure_result = None
            self._local.cause_order = None
            self._local.wait_resources = {}
            head = view.get('heads', instance)
            control = view.get('control', instance, {'paused': False})
            if control['paused']:
                raise CoordinationError('WAITING_PAUSED', instance=instance)
            if head is None:
                registration = view.get('registration', instance)
                require(registration is not None, 'MISSING_REGISTRATION')
                require(registration['context'] == self.context, 'WRONG_EXECUTION_CONTEXT')
                raw = registration['source']
                node = p.blue.source(raw)
                initial = p.blue.identity(node)
                existing = view.get('binding', self.context + '/' + initial)
                if existing is None:
                    version = view.get('versions', self.context + '/' + initial)
                    if version is not None:
                        existing = view.get('binding', self.context + '/' + version['documentId'])
                        position = view.get('history', version['instance'] + '/' + str(version['number']).zfill(16))
                        require(existing == {'instance': version['instance'], 'member': version['member']}
                            and position is not None and position['position'] == version['position']
                            and position['document'] == initial, 'INVALID_ESTABLISHED_VERSION', document=initial)
                if existing is not None:
                    writes = {('handles', instance): {'instance': existing['instance']}, ('registration', instance): None}
                    self.queue.finish(view, writes, claim)
                    packet = view.packet('bind-existing:' + instance, writes=writes)
                    publish(self.store, packet)
                    return
                require(p.registry.marker(node, 'initialized') is None, 'WAITING_ESTABLISHED_HISTORY', document=initial)
                before = None
                self.metrics['invocations'] += 1
                result = self._measure('processorSeconds', lambda: self._with_history(p, view, lambda: p.admit({initial: {'blueId': initial}}, root=initial)))
                p.observe_execution('outcome', gas=result.gas, status=result.status, invocation=result.invocation)
                kind, cause, proof = 'INITIALIZE', None, None
            else:
                reservation = view.get('reservation', instance)
                if reservation is not None:
                    # A reserved wave continues through its source worker.
                    wave = view.get('waves', reservation['wave'])
                    if wave['source'] != instance:
                        writes = {}
                        self.queue.finish(view, writes, claim, status='WAITING', issue={'code': 'WAITING_WAVE', 'wave': wave['identity']}, poll_after=self.poll_interval)
                        publish(self.store, view.packet(str(uuid4()), writes=writes))
                        return
                else:
                    wave = None
                if wave is not None and wave['phase'] == 'RECEIVE':
                    self._continue_wave(p, c, history, view, claim, wave, started)
                    return
                if head.get('rebaseGoals'):
                    self._rebase_step(p, c, history, channel_type, view, claim, head, wave, started)
                    return
                waiting_on = view.get('preparation_waits', instance)
                if waiting_on is not None:
                    from .waits import validate as validate_wait
                    validate_wait(waiting_on,instance)
                if wave is None and waiting_on is not None and view.matches(waiting_on['facts']):
                    writes = {}
                    self.queue.finish(view, writes, claim, status='WAITING',
                        issue={'code':'WAITING_SOURCE_COMPLETION','instance':waiting_on['source']},
                        poll_after=self.poll_interval)
                    publish(self.store, view.packet(str(uuid4()), writes=writes))
                    return
                participants = head['channels']
                needed = {row['timeline'] for row in participants}
                for actor in {row['actor'] for row in participants}:
                    needed.update(row['timeline'] for _, row in view.scan('authority_sources', self.context + '/' + actor + '/'))
                subscribed = set(head.get('sourceTimelines', {r['timeline'] for r in participants}))
                if subscribed != needed:
                    goals=deepcopy(head.get('rebaseGoals',[]))
                    added=needed-subscribed
                    if added and head.get('lastOrder') is not None:
                        goals.extend(dict(member=r['member'],channel=r['channel'],generation=r['generation'],
                            timelines=sorted(added),cutoff=head['lastOrder'],cursor=None)
                            for r in participants if r['member']==head['member'])
                    writes = {('heads', instance): {**head, 'sourceTimelines': sorted(needed), 'rebaseGoals':goals}}
                    for timeline in subscribed | needed:
                        view.get('subscriptions', timeline + '/' + instance)
                        writes['subscriptions', timeline + '/' + instance] = {'instance': instance} if timeline in needed else None
                    self.queue.finish(view, writes, claim, remaining=True)
                    publish(self.store, view.packet(str(uuid4()), writes=writes))
                    return
                self._local.wait_resources = {'timeline:'+tid:view.get('availability','timeline:'+tid,{'generation':0})['generation'] for tid in needed}
                sources = {tid: view.get('sources', tid) for tid in needed}
                for timeline in needed:
                    integrity = view.get('source_issues', timeline)
                    require(integrity is None or integrity.get('code')=='HOST_INCOMPLETE', 'SOURCE_INTEGRITY_FAILURE', timeline=timeline, issue=integrity)
                missing = [tid for tid, row in sources.items() if row is None]
                require(not missing, 'WAITING_SOURCE_PROVIDER', timelines=missing)
                boundary = min((row['before'] for row in sources.values()), default=0)
                entries = {e['blue_id']: Entry(**e) for tid, row in sources.items() for e in
                    source_entries(view, tid, row, after=head.get('lastOrder'), before=(boundary, '', ''), limit=1)}
                candidates = [e for e in entries.values() if head.get('lastOrder') is None or
                              (e.timestamp, e.timeline, e.blue_id) > tuple(head['lastOrder'])]
                candidates.sort(key=lambda e: e.order)
                pending_history = next_history(self, c, view, head, instance,
                    before_order=([candidates[0].timestamp, candidates[0].timeline, candidates[0].blue_id] if candidates else None))
                next_order = (pending_history[0]['order'] if pending_history else
                    (candidates[0].timestamp, candidates[0].timeline, candidates[0].blue_id) if candidates else None)
                if next_order is not None:
                    if needed and next_order[0] >= boundary:
                        self.hub.request_completeness(next_order[0] + 1)
                        raise CoordinationError('WAITING_COMPLETENESS', before=boundary,
                                                candidateTimestamp=next_order[0])
                    self._require_dependencies(history, view, instance, next_order)
                if pending_history:
                    if wave is None:
                        wave = self._reserve_wave(view, instance, pending_history[0]['order'])
                        require(wave is not None, 'WAITING_WAVE', instance=instance)
                        self._reschedule(claim)
                        return
                    self._apply_history(p, c, view, claim, head, instance, pending_history, wave, started)
                    return
                if not candidates:
                    for timeline in needed:
                        issue=view.get('source_issues',timeline)
                        if issue and issue.get('code')=='HOST_INCOMPLETE':
                            raise HostIncomplete('source acquisition interrupted',timeline=timeline)
                    observed = max((row.get('observedHeadTime') or 0 for row in sources.values()), default=0)
                    if observed >= boundary and observed:
                        self.hub.request_completeness(observed + 1)
                        raise CoordinationError('WAITING_COMPLETENESS', before=boundary, candidateTimestamp=observed)
                    if boundary:
                        self._require_dependencies(history, view, instance, (boundary, '', ''), inclusive=False)
                    writes = {('heads', instance): {**head, 'checkedBoundary': boundary}}
                    if boundary != head.get('checkedBoundary', 0):
                        self._completion_notice(view, writes, instance, 'boundary:' + str(boundary) + ':' + str(head['number']))
                    self.queue.finish(view, writes, claim)
                    publish(self.store, view.packet(str(uuid4()), writes=writes))
                    return
                cause = candidates[0]
                self._local.cause_order = [cause.timestamp,cause.timeline,cause.blue_id]
                request = operation_request(p.registry, L.Ref(cause.message))
                address=request.get('document',{}).get('blueId') if request else None
                if address is not None and head.get('ordinaryObservers') is False:
                    addressed=view.project('versions',self.context+'/'+address, ('member',)) or view.get('binding',self.context+'/'+address)
                    members={doc['key'] for doc in head['snapshot']['documents']}
                    if addressed is not None and addressed['member'] not in members:
                        self._dispose(view,claim,head,None,cause,None,None,wave,
                            evidence={'exactHead':head['document'],'address':address,
                                      'proofs':[row['proof'] for _,row in sorted(sources.items())]})
                        return
                bundle = set(head['bundle'])
                p.blue.language.prefetch(bundle)
                p.blue.refresh()
                before = self._measure('restorationSeconds', lambda: restore_local(p, head['snapshot']))
                selected = request['operation'] if request else None
                if selected:
                    p.blue.language.prefetch(head.get('operationBodies', {}).get(selected, []))
                    p.blue.refresh()
                proof = {'ranges': [row['proof'] for _, row in sorted(sources.items())]}
                attempt = self._measure('planningSeconds', lambda: p.prepare_invocation(before, L.Ref(cause.blue_id), cause.timestamp, evidence={channel_type: proof}))
                if attempt.outcome is not None:
                    result = execute(p, attempt)
                elif not attempt.run.seeds:
                    # Inapplicable/denied examined progress is separate from a
                    # Contracts checkpoint and does not invent a stable epoch.
                    self._dispose(view, claim, head, before, cause, attempt, None, wave)
                    return
                else:
                    if wave is None:
                        # An embedded managed source owns its independent turn.
                        # The containing root receives its retained completion;
                        # notification order cannot pick a larger replay root.
                        seeds = {seed.document for seed in attempt.run.seeds}
                        groups = components(before.documents, before.edges.values())
                        owners = set().union(*(set(group) for group in groups if set(group) & seeds))
                        if before.root not in owners:
                            source = min(owners)
                            source_doc = before.documents[source].blue_id
                            selected_source = view.project('versions', self.context + '/' + source_doc, ('instance',))
                            require(selected_source is not None, 'WAITING_SOURCE_HISTORY', document=source_doc)
                            writes = {}
                            target=selected_source['instance']
                            view.revisions('heads', [target])  # Exact completion availability pins the wait.
                            target_work=view.get('work',target);target_due=view.get('due',target)
                            # Polling a waiting parent must not repeatedly
                            # invalidate its already running child's CAS.
                            if target_work is not None and not target_work['owner'] and target_work['status']!='ERROR' and (
                                    target_due is None or target_due['at']>time.time()):
                                wake(view,writes,target)
                            # Reuse only the fact that these exact inputs are
                            # waiting, never a mutable Run or a successful result.
                            # Every semantic read is pinned; own claim metadata
                            # is checked afresh by the queue/publication protocol.
                            facts = dict(points=[[f,k,v] for (f,k),v in view.points.items()
                                if (f,k) != ('preparation_waits',instance) and
                                not (k==instance and f in ('work','due','leases'))],
                                ranges=[[f,k,list(map(list,v))] for (f,k),v in view.ranges.items()])
                            if len(facts['points']) + sum(len(r[2]) for r in facts['ranges']) <= 2048:
                                from .waits import FORMAT as WAIT_FORMAT,validate as validate_wait
                                writes['preparation_waits',instance]=validate_wait(
                                    {'format':WAIT_FORMAT,'source':target,'facts':facts},instance)
                            self.queue.finish(view, writes, claim, status='WAITING',
                                issue={'code': 'WAITING_SOURCE_COMPLETION', 'instance': selected_source['instance']},
                                poll_after=self.poll_interval)
                            publish(self.store, view.packet(str(uuid4()), writes=writes))
                            self._signal.set()
                            return
                        # Continue this untouched local attempt after revalidating
                        # all captured reads against the committed reservation.
                        # No mutable Run/meter is passed to a later worker attempt.
                        reuse=self.optimized and 'preparation' not in self.disabled_optimizations
                        wave = self._reserve_wave(view, instance, (cause.timestamp, cause.timeline, cause.blue_id), continue_view=reuse)
                        if wave is None:
                            raise CoordinationError('WAITING_WAVE', instance=instance)
                        if not reuse or not getattr(view,'_reservation_continued',False):
                            self.metrics['preparationFallbacks']=self.metrics.get('preparationFallbacks',0)+1
                            self._reschedule(claim)
                            return
                        current_work=view.get('work',instance);lease=view.get('leases',instance)
                        require(current_work is not None and lease is not None and
                            current_work['owner']==claim['owner'] and current_work['fence']==claim['fence'] and
                            lease['owner']==claim['owner'] and lease['fence']==claim['fence'] and lease['until']>time.time(),
                            'WAITING_STALE_RESERVATION',instance=instance)
                        view.fence_lease(instance,claim['owner'],claim['fence'])
                        require(view.get('reservation',instance)=={'wave':wave['identity']},'WAITING_WAVE',instance=instance)
                        self.metrics['preparationContinuations']=self.metrics.get('preparationContinuations',0)+1
                    for timeline,source in sources.items():
                        if view.pin_prefix(timeline,source):
                            # This generation was read only for wait registration.
                            # A running turn uses its verified immutable prefix;
                            # new input remains pending in the work generation.
                            view.points.pop(('availability','timeline:'+timeline),None)
                    self.metrics['invocations'] += 1
                    prepared = [attempt]
                    result = self._measure('processorSeconds', lambda: self._with_history(p, view, lambda: execute(p, prepared.pop() if prepared else
                        p.prepare_invocation(before, L.Ref(cause.blue_id), cause.timestamp, evidence={channel_type: proof}))))
                kind = 'PROCESS'
                from .dispositions import REJECTIONS
                if not result.commits and result.diagnostic.get('code') in REJECTIONS and (wave is None or not wave.get('completed')):
                    self._dispose(view, claim, head, before, cause, attempt, result, wave)
                    return
            require_complete(result)
            timings = {'processingSeconds': time.perf_counter() - started}
            self._publish_outcome(p, c, view, claim, before, result, kind, cause, proof, timings,
                                  wave=wave if head is not None else None)

    def _dispose(self, view, claim, head, before, cause, attempt, result, wave, *, evidence=None):
        from .dispositions import FORMAT, key, validate
        from .store import fingerprint
        assessments = deepcopy(attempt.run.external_admissions) if attempt is not None else {'selection':evidence}
        denied = any(row['disposition'] == 'DENIED' for evidence in assessments.values()
                     for row in evidence.get('assessments', []))
        wire=before.wire() if before is not None else head['snapshot']
        from blue_contracts.reference.model import digest
        scope = [dict(member=doc['key'],channel=channel,generation=life['generation'])
                 for doc in wire['documents'] for channel,life in sorted(doc['channels'].items())]
        reason = result.diagnostic['code'] if result else 'AUTHORITY_DENIED' if denied else 'NO_MATCH'
        outcome = ('EXECUTION_REJECTED' if reason in ('BEX_EXECUTION_REJECTED','GAS_LIMIT_EXCEEDED')
                   else 'REJECTED') if result or denied else 'NO_MATCH'
        row = validate(dict(format=FORMAT, instance=claim['instance'], lineage=head['documentId'],
            entry=cause.blue_id, order=[cause.timestamp,cause.timeline,cause.blue_id],
            before=digest('contracts.snapshot/completion-1',wire), scope=scope, evidence=assessments,
            outcome=outcome, reason=reason, result=result.observations() if result else None))
        identity = fingerprint(row)
        writes = {('heads',claim['instance']): {**head,'lastOrder':row['order']},
                  ('input_dispositions',identity): row,
                  ('assessments',claim['instance']+'/'+cause.blue_id): {'decision':identity,**row}}
        order_key=claim['instance']+'/'+str(cause.timestamp).zfill(20)+'/'+cause.timeline+'/'+cause.blue_id
        writes['input_disposition_order',order_key]={k:row[k] for k in ('entry','order','outcome','reason')}
        writes['input_disposition_order',order_key].update(decision=identity,gas=result.gas if result else None)
        for item in scope:
            lookup=key(claim['instance'],item['member'],item['channel'],item['generation'],cause.blue_id)
            previous=view.get('terminal_inputs',lookup)
            require(previous is None or previous == {'decision':identity}, 'CONFLICTING_INPUT_DISPOSITION')
            writes['terminal_inputs',lookup]={'decision':identity}
        if wave is not None:
            require(not wave.get('completed'), 'OUTSTANDING_SOURCE_OBLIGATION')
            self.waves.finish(view,writes,wave)
            writes['waves',wave['identity']].update(phase='REJECTED',disposition=identity)
        boundary = None
        if self.optimized and 'no-match' not in self.disabled_optimizations and wave is None:
            boundary=self._examined_boundary(view,head,row['order'])
        if boundary is not None:
            writes['heads',claim['instance']]['checkedBoundary']=boundary
            self.metrics['combinedNoMatch']=self.metrics.get('combinedNoMatch',0)+1
        self._completion_notice(view, writes, claim['instance'], identity)
        self.queue.finish(view,writes,claim,remaining=boundary is None)
        publish(self.store,view.packet('disposition:'+identity,writes=writes))
        self._signal.set()

    def _examined_boundary(self, view, head, order):
        # Conservative: parents with retained/history goals take normal selection.
        if head['snapshot']['edges'] or head.get('attachmentGoals') or head.get('rebaseGoals'):
            return None
        timelines=set(head.get('sourceTimelines',[r['timeline'] for r in head['channels']]))
        sources={t:view.get('sources',t) for t in timelines}
        if any(s is None or view.get('source_issues',t) is not None for t,s in sources.items()):
            return None
        boundary=min((s['before'] for s in sources.values()),default=0)
        if any((s.get('observedHeadTime') or 0)>=boundary and s.get('observedHeadTime') for s in sources.values()):
            return None
        if any(source_entries(view,t,s,after=order,before=(boundary,'',''),limit=1) for t,s in sources.items()):
            return None
        return boundary

    def _reserve_wave(self, view, instance, order, *, continue_view=False):
        """Claim this owner/SCC. Acyclic consumers never backpressure it."""
        return self.waves.reserve(instance, order, observed=view, continue_view=continue_view)

    def _completion_notice(self, view, writes, instance, identity):
        # A durable hint in the same publication as history/progress. Its own
        # key avoids reading a concurrently running consumer (or notifier).
        key = self.context + '/' + identity + '/' + instance
        writes['completion_notices', key] = {'source': instance}

    def _deliver_completion_notices(self):
        """Wake direct consumers separately: contention cannot rerun a producer.

        Notices are hints, not input events. History/occurrence cursors decide
        exactly which results to consume. Publication is idempotent and durable.
        """
        batch = self.optimized and 'notice-batching' not in self.disabled_optimizations
        for _ in range(1 if batch else 4):
            with self.store.read() as view:
                rows = view.page('completion_notices', self.context + '/', limit=4 if batch else 1)
                if not rows:
                    return
                # Page reads pin every acknowledged notice. Complete reverse
                # range reads fence removal/recreation and generation changes.
                # Only wake hints coalesce; all source results remain distinct.
                writes = {('completion_notices', key): None for key, _ in rows}
                parents = set()
                for source in sorted({notice['source'] for _, notice in rows}):
                    parents.update(edge['parent'] for _, edge in view.scan('reverse', source + '/')
                                   if edge['parent'] != source)
                for parent in sorted(parents):
                    scope = view.get('managed', self.context + '/' + parent)
                    if scope is not None:
                        wake(view, writes, parent)
                packet = view.packet('completion-notices:' + fingerprint([key for key, _ in rows]), writes=writes)
            if publish(self.store, packet).status != 'COMMITTED':
                return  # Another worker/new topology will be observed next pass.
            with self._metrics_lock:
                self.metrics['noticesDelivered'] = self.metrics.get('noticesDelivered', 0) + len(rows)
                self.metrics['noticeBatches'] = self.metrics.get('noticeBatches', 0) + 1
                self.metrics['noticeWakeHints'] = self.metrics.get('noticeWakeHints', 0) + sum(f == 'work' for f, _ in writes)
            self._signal.set()

    def _require_dependencies(self, history, view, instance, order, *, inclusive=True):
        from .readiness import complete_through
        owners = set(self.waves.closure(view, [instance]))
        blocked = []
        dependencies = [edge for owner in sorted(owners)
                        for _, edge in view.scan('forward', owner + '/')]
        for edge in dependencies:
            source = edge['source']
            if source in owners:
                continue  # The Contracts cyclic component owns these local turns.
            if not complete_through(self, view, source, tuple(order),
                                    inclusive=inclusive, visiting=set(owners)):
                blocked.append(source)
        if blocked:
            # Do not poke an already working/due prerequisite on every poll.
            # In particular, do not introduce a reverse producer->consumer wait.
            for source in sorted(set(blocked)):
                with self.store.read() as fresh:
                    row = fresh.get('work', source)
                    due = fresh.get('due', source)
                if row and not row['owner'] and row['status'] != 'ERROR' and (
                        due is None or due['at'] > time.time()):
                    if (row.get('issue') or {}).get('code') != 'HOST_INCOMPLETE':
                        self.queue.request(source)
            raise CoordinationError('WAITING_SOURCE_PREFIX', instances=sorted(set(blocked)),
                                    requiredOrder=list(order))

    def _publish_outcome(self, p, c, view, claim, before, result, kind, cause, proof, timings, *, wave=None,
                         receiving=None, receiver_instance=None):
        publication_started = time.perf_counter()
        snapshot=result.snapshot
        indexes, index_writes = prepare_content(p, snapshot, view)
        reachable = Graph(snapshot, p.registry, p.archive).reachable()
        # A cyclic unit remains an atomic owner set for this invocation even
        # when the operation splits it. Already-managed former members still
        # receive their complete result; detached provisional births do not.
        for unit in result.units:
            if not unit['turnResults']:
                continue
            for member in unit['members']:
                if member in reachable:
                    continue
                marker = p.registry.marker(snapshot.documents[member].body, 'initialized')
                if marker is not None:
                    initial = p.blue.literal(marker)['document']['blueId']
                    if view.get('binding', self.context + '/' + initial) is not None:
                        reachable.add(member)
        member_instances, lineages, newborn = {}, {}, set()
        class Heads(dict):
            def __missing__(self, member):
                value = view.get('heads', member_instances[member])
                self[member] = value
                return value
        # Unchanged descendants are pinned by exact versions. Their unrelated
        # examined-input progress must not invalidate this owner's publication.
        old_heads = Heads()
        writes = dict(index_writes)
        for member in sorted(reachable):
            document = snapshot.documents[member]
            marker = p.registry.marker(document.body, 'initialized')
            initial = p.blue.literal(marker)['document']['blueId']
            lineages[member] = initial
            binding = view.get('binding', self.context + '/' + initial)
            if binding is None:
                newborn.add(member)
                instance = (receiver_instance or claim['instance']) if member == snapshot.root else str(uuid5(NAMESPACE_URL, self.context + '/' + initial))
                writes['binding', self.context + '/' + initial] = {'instance': instance, 'member': member}
                writes['managed', self.context + '/' + instance] = {'instance': instance}
                writes['handles', instance] = {'instance': instance}
            else:
                require(binding['member'] == member, 'AMBIGUOUS_LINEAGE_ORIGIN',
                        document=initial, selectedMember=member, managedMember=binding['member'],
                        limitation=('UNSUPPORTED_HISTORICAL_OWNER_JOIN' if before is not None
                                    and member not in before.documents else 'CONFLICTING_BIRTH_ORIGIN'))
                instance = binding['instance']
            member_instances[member] = instance
        owned = set(newborn)
        for unit in result.units:
            if unit['turnResults']:
                owned.update(set(unit['members']) & reachable)
        owned.add(snapshot.root)
        discovered={member_instances[m] for m in owned-newborn}
        if wave is not None and discovered-set(wave['members']):
            # Reserve only actual newly acquired owners. Parent polling cannot
            # starve a cycle join; already-running peers are fenced at commit.
            self.waves.extend(view,wave,discovered)
            raise CoordinationError('WAITING_OWNER_ACQUISITION', instances=sorted(discovered))
        self._fence_owners(view, claim, wave, owned, member_instances, lineages, newborn)
        if before is not None:
            for member in owned & before.documents.keys():
                if old_heads[member] is not None:
                    require(old_heads[member]['document'] == before.documents[member].blue_id,
                            'WAITING_SOURCE_PREDECESSOR', document=lineages[member])
            for member in owned - before.documents.keys() - newborn:
                # A join may already have changed cyclic addresses before the
                # first local turn. Fence the actual exact archive view opened
                # by the kernel, not that later derived cyclic address.
                captures=self._local.owner_predecessors.get(member,set())
                require(captures=={old_heads[member]['document']},
                        'WAITING_OWNER_PREDECESSOR', document=lineages[member])
        public_members = []
        for member in sorted(owned, key=lambda k: lineages[k]):
            old = old_heads[member]
            public_members.append(c.typed('Member Result', documentId={'blueId': lineages[member]},
                before={'blueId': old['document'] if old else lineages[member]},
                after={'blueId': snapshot.documents[member].blue_id},
                emitted=[c.typed('Emitted Occurrence', ordinal=i, event={'blueId': event['event']})
                         for i, event in enumerate(e for e in result.event_trace if e['document'] == member)]))
        receipt_raw = c.typed('Processing Receipt', kind=kind, documentId={'blueId': lineages[snapshot.root]},
            before={'blueId': before.documents[before.root].blue_id if before else lineages[snapshot.root]},
            after={'blueId': snapshot.documents[snapshot.root].blue_id}, gas=result.gas,
            emitted=[c.typed('Emitted Occurrence', ordinal=i, event={'blueId': event['event']}) for i, event in enumerate(result.public_events)],
            members=public_members)
        if cause is not None:
            receipt_raw.update(event={'blueId': cause.blue_id}, eventTimestamp=cause.timestamp)
        if receiving is not None and 'receipts' in receiving:
            receipt_raw['sourceReceipts'] = [{'blueId': identity} for identity in receiving['receipts']]
            receipt_raw['attachment'] = {'blueId': receiving['attachment']}
        receipt = c.admit(receipt_raw)
        c.validate(receipt, 'Processing Receipt')
        effective = (receiving.get('effectiveOrder') if receiving and 'effectiveOrder' in receiving else
            [cause.timestamp, cause.timeline, cause.blue_id] if cause else None)
        completed_members = set()
        for member in sorted(owned):
            instance, initial = member_instances[member], lineages[member]
            old = old_heads[member]
            state = rooted(p, snapshot, member)
            document = state.documents[member].blue_id
            number = old['number'] + 1 if old else 0
            goals = attachments(self, c, view, state, member, instance, old, member_instances,
                old_heads, owned, cause, prior_goals=receiving.get('goals') if receiving and member == snapshot.root else None)
            participant_rows = channels(p, c, state)
            rebasing = rebase.activate(view, self.context, old, participant_rows, member, effective,
                progressed=receiving.get('rebase') if receiving and member == snapshot.root else None)
            stable = not goals and not rebasing
            epoch = old['epoch'] + int(stable) if old else 0
            if stable:completed_members.add(member)
            position_raw = c.typed('History Position', documentId={'blueId': initial}, position=number,
                document={'blueId': document}, processing={'blueId': receipt}, stable=stable, epoch=epoch)
            if old:
                position_raw['previous'] = {'blueId': old['position']}
            if effective:
                position_raw['effectiveEntry'] = {'blueId': effective[2]}
            position = c.admit(position_raw)
            bundle, bodies = set(), {}
            for key in state.documents:
                bundle.update(indexes[key]['common'])
                for name, row in indexes[key]['operations'].items():
                    bodies.setdefault(name, set()).update(row['bodies'])
            declared = p.registry.contracts(state.documents[member].body)
            terminated = p.registry.marker(state.documents[member].body, 'terminated') is not None
            operations = [dict(name=name, channel=row['channel'], request=row.get('request'),
                sourceChannels=list(leaves(declared, row['channel']))) for name, row in declared.items() if row['_role'] == 'operation' and not terminated]
            display = p.blue.literal(state.documents[member].body)
            next_head = dict(context=self.context, documentId=initial, member=member, document=document,
                snapshot=state.wire(), bundle=sorted(bundle), operationBodies={k: sorted(v) for k, v in bodies.items()},
                number=number, epoch=epoch, position=position, checkedBoundary=old.get('checkedBoundary', 0) if old else 0,
                lastOrder=(old.get('lastOrder') if old else None) if receiving and 'rebase' in receiving else
                    effective if cause and (kind == 'PROCESS' or receiving and receiving.get('live')) else old.get('lastOrder') if old else None,
                lastStable=(dict(document=display, blueId=document, epoch=epoch, position=position) if stable else
                            old.get('lastStable') if old else None), attachmentGoals=goals, rebaseGoals=rebasing,
                channels=participant_rows, operations=operations, timings=timings, terminated=terminated)
            next_head['ordinaryObservers']=any(indexes[k].get('ordinaryObservers',True) for k in state.documents)
            mandate = validate_mandate_result(c, result, member, old, cause)
            if mandate is not None:
                next_head.update(mandate)
                def participant(name):
                    node = p.blue.exact(declared[name]['_recipe']); p.blue.remember(node)
                    identity = p.blue.identity(node)
                    return {'actor': c.link(identity, 'actor'), 'timeline': c.link(identity, 'timeline')}
                # Termination retires live channels, but must not erase the
                # authenticated participants from the retained authority history.
                holder = participant('authorityHolderChannel')
                delegate = participant('authorizedActorChannel')
                authority_key = self.context + '/' + holder['actor'] + '/' + instance
                previous_authority = view.get('authority_sources', authority_key)
                authority_source = {'timeline': delegate['timeline'], 'instance': instance}
                # Existing holders must discover the additional source even
                # when no new entry arrives after registration. An unchanged
                # source index must not read/rewrite every subscriber's work:
                # a subscriber waiting on this very approval/termination can
                # otherwise invalidate its publication on every polling turn.
                # Existing authority waits already have durable due work.
                if previous_authority != authority_source:
                    writes['authority_sources', authority_key] = authority_source
                    for _, subscriber in view.scan('subscriptions', holder['timeline'] + '/'):
                        wake(view, writes, subscriber['instance'])
            writes['heads', instance] = next_head
            view.get('positions', instance)
            writes['positions', instance] = {'number': number, 'position': position, 'documentId': initial,
                'stableNumber': number if stable else (view.get('positions', instance) or {}).get('stableNumber', old['number'] if old and old.get('lastStable') else -1)}
            writes['versions', self.context + '/' + document] = dict(documentId=initial, member=member, instance=instance,
                position=position, number=number, snapshot=state.wire(), bundle=sorted(bundle))
            writes['history', instance + '/' + str(number).zfill(16)] = dict(number=number, position=position,
                document=document, receipt=receipt, epoch=epoch, stable=stable, effectiveOrder=effective, kind=kind,
                gas=result.gas, timings=timings)
            if mandate is not None:
                writes['history', instance + '/' + str(number).zfill(16)].update(mandate)
            old_subscriptions = set(old.get('sourceTimelines', {r['timeline'] for r in old.get('channels', [])})) if old else set()
            new_subscriptions = {r['timeline'] for r in participant_rows}
            for actor in {r['actor'] for r in participant_rows}:
                new_subscriptions.update(r['timeline'] for _, r in view.scan('authority_sources', self.context + '/' + actor + '/'))
            next_head['sourceTimelines'] = sorted(new_subscriptions)
            for timeline in old_subscriptions | new_subscriptions:
                previous_subscription=view.get('subscriptions',timeline+'/'+instance)
                subscription={'instance':instance} if timeline in new_subscriptions else None
                if previous_subscription!=subscription:
                    writes['subscriptions',timeline+'/'+instance]=subscription
            previous_relations=dict(view.scan('forward',instance+'/'))
            current_relations={}
            for edge in state.edges.values():
                if edge.source != member: continue
                source_instance=member_instances[edge.target];key=instance+'/'+edge.path
                current_relations[key]=dict(parent=instance,source=source_instance,path=edge.path,
                    generation=edge.generation,selected=state.documents[edge.target].blue_id)
            for key in previous_relations.keys() | current_relations.keys():
                prior=previous_relations.get(key);relation=current_relations.get(key)
                if prior==relation and 'relations' not in self.disabled_optimizations: continue
                if prior is not None: writes['reverse',prior['source']+'/'+key]=None
                writes['forward',key]=relation
                if relation is not None: writes['reverse',relation['source']+'/'+key]=relation
            if stable:
                self._completion_notice(view, writes, instance, receipt)
            if instance != claim['instance']:
                wake(view, writes, instance)
        # Local receipt provenance is protected by the same atomic publication.
        writes['outcomes', self.context + '/' + receipt] = dict(before=before.wire() if before else None,
            after=snapshot.wire(), observations=result.observations(), receipt=result.receipt,
            event=cause.blue_id if cause else None, timestamp=cause.timestamp if cause else None,
            evidence=proof, owners=sorted(owned))
        writes['established', self.context + '/' + result.receipt] = {'receipt': receipt}
        for turn in result.completions:
            input=turn['turnInput'];member=input['member']
            if member in owned:
                key=self._execution_key(member,cause.blue_id if cause else None,
                    input['beforeView'][member]['document']['blueId'],input['phase'])
                view.get('executed_turns',key)
                writes['executed_turns',key]={'receipt':receipt,'turn':turn['identity']}
        for event in (e for e in result.event_trace if e['document'] in owned):
            writes['outbox', self.context + '/' + event['identity']] = dict(receipt=receipt, event=event, acknowledged=False)
        writes['registration', claim['instance']] = None
        if wave is not None:
            prior = wave.get('completed', {})
            completed = {**prior, **{member_instances[m]: receipt for m in owned & completed_members}}
            parents = [m for m in wave['members'] if m not in completed]
            if snapshot.root not in completed_members:
                writes['waves', wave['identity']] = {**wave, 'phase': 'RECEIVE' if receiver_instance and receiver_instance != wave['source'] else 'SOURCE',
                    'completed': completed}
            elif parents:
                writes['waves', wave['identity']] = {**wave, 'phase': 'RECEIVE', 'pending': parents,
                                                    'completed': completed, 'sourceReceipt': receipt}
            else:
                self.waves.finish(view, writes, wave)
        self.queue.finish(view, writes, claim, remaining=True)
        writes.update(content_writes(p.blue.language.provider, view))
        packet = view.packet(self.context + '/' + result.receipt, writes=writes, result={'receipt': receipt})
        with self._metrics_lock:
            elapsed=time.perf_counter()-publication_started
            self.metrics['publicationPreparationSeconds'] += elapsed
            phases=getattr(self._local,'phases',None)
            if phases is not None:phases['publicationPreparationSeconds']=phases.get('publicationPreparationSeconds',0)+elapsed
        committed = self._measure('commitSeconds', lambda: publish(self.store, packet))
        if committed.status == 'CONFLICT':
            self.metrics['retries'] += 1
            self._reschedule(claim)
        else:
            p.blue.language.provider.acknowledge()
            with self._metrics_lock:self.metrics['logicalGasCommitted'] += result.gas
        self._signal.set()

    def _rebase_step(self, p, c, history, channel_type, view, claim, head, wave, started):
        goals, cause = rebase.pending(view, head['rebaseGoals'])
        activation = max(g['cutoff'] for g in head['rebaseGoals'])
        if wave is None:
            wave = self._reserve_wave(view, claim['instance'], activation)
            require(wave is not None, 'WAITING_WAVE', instance=claim['instance'])
            self._reschedule(claim)
            return
        history.delivery_lifetimes = set()
        if cause is not None:
            order = [cause.timestamp, cause.timeline, cause.blue_id]
            for goal in goals:
                if (tuple(goal.get('cursor') or (-1, '', '')) < tuple(order) < tuple(goal['cutoff'])
                        and cause.timeline in goal['timelines']):
                    history.delivery_lifetimes.add(rebase.key(goal))
                    goal['cursor'] = order
            goals, _ = rebase.pending(view, goals)
        else:
            self._seal_rebase(p,c,view,claim,head,wave,activation,{})
            return
        p.blue.language.prefetch(head['bundle']); p.blue.refresh()
        before = self._measure('restorationSeconds', lambda: restore_local(p, head['snapshot']))
        timelines = set(head['sourceTimelines'])
        for goal in head['rebaseGoals']: timelines.update(goal['timelines'])
        sources = {tid: view.get('sources', tid) for tid in timelines}
        require(all(sources.values()), 'WAITING_SOURCE_PROVIDER')
        proof = {'ranges': [row['proof'] for _, row in sorted(sources.items())]}
        attempt=p.prepare_invocation(before,L.Ref(cause.blue_id),cause.timestamp,evidence={channel_type:proof})
        if attempt.outcome is None and not attempt.run.seeds:
            writes={}
            for member,channel,generation in history.delivery_lifetimes:
                writes['assessments',claim['instance']+'/'+channel+'/'+str(generation)+'/'+cause.blue_id]=deepcopy(attempt.run.external_admissions)
            if goals:
                writes['heads',claim['instance']]={**head,'rebaseGoals':goals}
                self.queue.finish(view,writes,claim,remaining=True)
                publish(self.store,view.packet(str(uuid4()),writes=writes))
            else:self._seal_rebase(p,c,view,claim,head,wave,activation,writes)
            return
        self.metrics['invocations'] += 1
        prepared=[attempt]
        result = self._measure('processorSeconds', lambda: self._with_history(p, view, lambda: execute(p,
            prepared.pop() if prepared else p.prepare_invocation(before, L.Ref(cause.blue_id), cause.timestamp, evidence={channel_type: proof}))))
        require_complete(result)
        self._publish_outcome(p, c, view, claim, before, result, 'PROCESS', cause, proof,
            {'processingSeconds': time.perf_counter() - started}, wave=wave,
            receiving={'rebase': goals, 'effectiveOrder': activation})

    def _seal_rebase(self,p,c,view,claim,head,wave,activation,writes):
        """Seal an examined interval; no inapplicable entry gets a success.

        The new History Position references the existing genuine processing
        receipt. This is a stability boundary, with no processor invocation,
        new checkpoint, emitted occurrence or invented source execution.
        """
        instance=claim['instance'];member=head['member']
        self._fence_owners(view,claim,wave,{member},{member:instance},{member:head['documentId']},set())
        next_head={**head,'rebaseGoals':[]}
        changed=head['lastStable'] is None or head['lastStable']['blueId']!=head['document']
        current=view.get('history',instance+'/'+str(head['number']).zfill(16))
        if changed:
            p.blue.language.prefetch(head['bundle']);p.blue.refresh()
            number,epoch=head['number']+1,head['epoch']+1
            position=c.admit(c.typed('History Position',documentId={'blueId':head['documentId']},position=number,
                document={'blueId':head['document']},processing={'blueId':current['receipt']},stable=True,epoch=epoch,
                previous={'blueId':head['position']},effectiveEntry={'blueId':activation[2]}))
            next_head.update(number=number,epoch=epoch,position=position,lastStable=dict(
                document=p.blue.literal(L.Ref(head['document'])),blueId=head['document'],epoch=epoch,position=position))
            writes['history',instance+'/'+str(number).zfill(16)]={**current,'number':number,'position':position,
                'epoch':epoch,'stable':True,'effectiveOrder':activation,'kind':'COMPLETE','gas':0}
            view.get('positions',instance)
            writes['positions',instance]={'number':number,'position':position,'documentId':head['documentId'], 'stableNumber':number}
            version=view.get('versions',self.context+'/'+head['document'])
            writes['versions',self.context+'/'+head['document']]={**version,'number':number,'position':position}
        writes['heads',instance]=next_head
        self._completion_notice(view, writes, instance, 'seal:' + next_head['position'])
        completed={**wave.get('completed',{}),instance:current['receipt']}
        parents=[m for m in wave['members'] if m not in completed]
        if changed and parents:
            writes['waves',wave['identity']]={**wave,'phase':'RECEIVE','pending':parents,
                'completed':completed,'sourceReceipt':current['receipt']}
        else:self.waves.finish(view,writes,wave)
        self.queue.finish(view,writes,claim,remaining=True)
        writes.update(content_writes(p.blue.language.provider,view))
        publish(self.store,view.packet(str(uuid4()),writes=writes))

    def _fence_owners(self, view, claim, wave, owned, instances, lineages, newborn):
        """Every writer is conditional on this attempt's starting snapshot.

        ReadView is MVCC: even owners discovered during execution read the
        original facts. The final packet validates these points atomically.
        Immutable witnesses and scheduling-only ancestors are not writers.
        """
        driver = view.get('work', claim['instance'])
        require(driver is not None and driver['owner'] == claim['owner'] and
                driver['fence'] == claim['fence'], 'WAITING_STALE_WORKER')
        view.fence_lease(claim['instance'], claim['owner'], claim['fence'])
        for member in sorted(owned):
            instance = instances[member]
            binding = view.get('binding', self.context + '/' + lineages[member])
            head = view.get('heads', instance)
            control = view.get('control', instance, {'paused': False})
            require(not control['paused'], 'WAITING_PAUSED', instance=instance)
            reservation = view.get('reservation', instance)
            require(reservation is None or wave is not None and reservation['wave'] == wave['identity'],
                    'WAITING_SOURCE_WAVE', instance=instance)
            if wave is not None and instance in wave['members']:
                require(reservation == {'wave': wave['identity']}, 'WAITING_LOST_RESERVATION', instance=instance)
            if member in newborn:
                require(binding is None and head is None, 'WAITING_INSTANCE_CREATION', instance=instance)
            else:
                require(binding == {'instance': instance, 'member': member} and head is not None,
                        'WAITING_INSTANCE_BINDING', instance=instance)
            if instance != claim['instance']:
                work = view.get('work', instance)
                if work and work['owner']:
                    lease = view.get('leases', instance)
                    until = lease['until'] if lease and lease['fence'] == work['fence'] else work['leaseUntil']
                    require(until <= time.time(), 'WAITING_OWNER_LEASE', instance=instance)

    def _continue_wave(self, p, c, history, view, claim, wave, started):
        completed = wave['completed']
        ready = []
        for instance in wave['pending']:
            edges = [row for _, row in view.scan('forward', instance + '/')]
            predecessors = {e['source'] for e in edges if e['source'] in wave['members']}
            if predecessors <= set(completed):
                ready.append((instance, edges))
        require(bool(ready), 'WAITING_CYCLIC_OWNER_CONTEXT', wave=wave['identity'])
        instance, edges = min(ready, key=lambda x: x[0])
        history.receiving_instance=instance
        head = view.get('heads', instance)
        self._local.receiving=dict(instance=instance,wave=wave['identity'],before=head['snapshot'],
                                   occurrences=edges,sourceReceipts=wave['completed'])
        pending_history = next_history(self, c, view, head, instance, before_order=wave['order'])
        if pending_history and (tuple(pending_history[0]['order']) < tuple(wave['order']) or
                head.get('attachmentGoals') or any(row['successor']['receipt'] !=
                    completed.get(row['edge']['source']) for row in pending_history)):
            self._apply_history(p, c, view, claim, head, instance, pending_history, wave, started)
            return
        control = view.get('control', instance, {'paused': False})
        require(not control['paused'], 'WAITING_PAUSED', instance=instance)
        p.blue.language.prefetch(head['bundle'])
        p.blue.refresh()
        before = self._measure('restorationSeconds', lambda: restore_local(p, head['snapshot']))
        by_receipt = {}
        attachment_rows = []
        for edge in edges:
            source = edge['source']
            if source not in completed:
                continue
            source_head = view.get('heads', source)
            receipt = completed[source]
            by_receipt.setdefault(receipt, set()).add(source_head['member'])
            selected = view.get('versions', self.context + '/' + edge['selected'])
            require(selected is not None, 'WAITING_SOURCE_HISTORY', document=edge['selected'])
            attachment_rows.append(c.typed('Attachment', source={'blueId': source_head['documentId']},
                path=edge['path'], generation=edge['generation'], sourcePosition={'blueId': selected['position']}))
        require(bool(by_receipt), 'WAITING_SOURCE_COMPLETION', instance=instance)
        capabilities = self._source_capabilities(p, view, by_receipt)
        source = view.get('outcomes', self.context + '/' + next(iter(by_receipt)))
        cause = c.entry(source['event']) if source['event'] else None
        attachment = c.admit(attachment_rows[0] if len(attachment_rows) == 1 else {'occurrences': attachment_rows})
        self.metrics['receivingApplications'] += 1
        timelines = set(head['sourceTimelines'])
        sources = {tid: view.get('sources', tid) for tid in timelines}
        require(all(sources.values()), 'WAITING_SOURCE_PROVIDER')
        proof = {'ranges': [row['proof'] for _, row in sorted(sources.items())]}
        channel_type = c.types['Coordination/Timeline Channel']
        result = self._measure('processorSeconds', lambda: execute(p, p.begin_live_application(
            before, capabilities, evidence={channel_type: proof})))
        self._local.failure_result=result.observations() if not result.commits else None
        require_complete(result)
        self._publish_outcome(p, c, view, claim, before, result, 'APPLY', cause, proof,
            {'processingSeconds': time.perf_counter() - started}, wave=wave,
            receiving={'receipts': sorted(by_receipt), 'attachment': attachment, 'live': True}, receiver_instance=instance)

    def _apply_history(self, p, c, view, claim, head, instance, selected, wave, started):
        self._local.receiving=dict(instance=instance,wave=wave['identity'],before=head['snapshot'],
            occurrences=[row['edge'] for row in selected],sourceReceipts=[row['successor']['receipt'] for row in selected])
        p.blue.language.prefetch(head['bundle'])
        p.blue.refresh()
        before = self._measure('restorationSeconds', lambda: restore_local(p, head['snapshot']))
        by_receipt, attachment_rows, goals, boundaries = {}, [], {}, []
        for row in selected:
            edge, source_position = row['edge'], row['selected']
            source_head = source_position
            receipt = row['successor']['receipt']
            by_receipt.setdefault(receipt, set()).add(source_head['member'])
            goals[edge['path']] = row['goal']
            activation = row['goal']['activationOrder']
            if activation:boundaries.append(activation)
            if row['successor'].get('effectiveOrder'):boundaries.append(row['successor']['effectiveOrder'])
            attachment_rows.append(c.typed('Attachment', source={'blueId': source_head['documentId']},
                path=edge['path'], generation=edge['generation'], sourcePosition={'blueId': source_position['position']},
                **({'activationEntry': {'blueId': activation[2]}} if activation else {})))
        capabilities = self._source_capabilities(p, view, by_receipt)
        cause = selected[0]['cause']
        attachment = c.admit(attachment_rows[0] if len(attachment_rows) == 1 else {'occurrences': attachment_rows})
        self.metrics['receivingApplications'] += 1
        live = (cause is not None and tuple(selected[0]['order']) ==
                (cause.timestamp, cause.timeline, cause.blue_id) and not head.get('attachmentGoals') and not head.get('rebaseGoals')
                and (head.get('lastOrder') is None or
                     (cause.timestamp, cause.timeline, cause.blue_id) > tuple(head['lastOrder'])))
        proof = None
        if live:
            sources = {tid: view.get('sources', tid) for tid in head['sourceTimelines']}
            require(all(sources.values()), 'WAITING_SOURCE_PROVIDER')
            proof = {'ranges': [row['proof'] for _, row in sorted(sources.items())]}
            for tid, source in sources.items():
                view.pin_prefix(tid, source)
            channel_type = c.types['Coordination/Timeline Channel']
            attempt = p.begin_live_application(before, capabilities, evidence={channel_type: proof})
        else:
            attempt = p.begin_receiving_application(before, capabilities)
        result = self._measure('processorSeconds', lambda: execute(p, attempt))
        self._local.failure_result=result.observations() if not result.commits else None
        require_complete(result)
        self._publish_outcome(p, c, view, claim, before, result, 'APPLY', cause, proof,
            {'processingSeconds': time.perf_counter() - started}, wave=wave,
            receiving={'receipts': sorted(by_receipt), 'attachment': attachment, 'goals': goals,
                       'live': live, 'effectiveOrder': max(boundaries) if boundaries else None}, receiver_instance=instance)

    def _source_capabilities(self, processor, view, by_receipt):
        capabilities = []
        for receipt, selected in sorted(by_receipt.items()):
            members = set(selected)
            record = view.get('outcomes', self.context + '/' + receipt)
            require(record is not None, 'WAITING_SOURCE_COMPLETION')
            for unit in record['observations']['units']:
                if members.intersection(unit['members']):
                    members.update(unit['members'])
            try:
                capability=processor.load_source_completion(receipt, sorted(members))
            except Exception:
                with self._metrics_lock:self.metrics['adoptionRejections']+=1
                raise
            capabilities.append(capability)
            with self._metrics_lock:self.metrics['completionLoads']+=1
        return capabilities
