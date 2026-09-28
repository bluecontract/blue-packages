"""Host provider acquisition; public signed facts persist independently of work."""
from blue_host import HOST_FAILURES, incomplete
from threading import RLock, Event, Thread
from uuid import uuid4
import time
from algorithms import blue as L
from blue_contracts import Processor
from blue_runtime.record_bridge import install_record_bridge
from blue_language.physical import PhysicalCache
from .catalogue import Catalogue
from .content import StoreLanguage, content_writes
from .sources import SignedProvider, PrefixVerifier
from .work import publish, wake, WorkQueue
from .durable_source import DurableProvider
from .store import SQLiteStore
from blue_coordination_spec.model import CoordinationError


class SourceHub:
    def __init__(self, store, *, auto_complete=True, clock=lambda: time.time_ns() // 1000, reuse_admission=True):
        self.store, self.auto_complete, self.clock = store, auto_complete, clock
        self.reuse_admission=reuse_admission
        self.lock = RLock()
        self.cache = PhysicalCache(capacity=65536)
        with self.cache.scope():
            self.processor = install_record_bridge(Processor(StoreLanguage(reuse_admission=reuse_admission)))
            self.catalogue = Catalogue(self.processor)
        self.providers = {}
        self.unsubscribers = {}
        self.on_change = lambda: None
        self._poll_stop, self._poll_thread = Event(), None
        self._requested_boundary = 0
        self.metrics = dict(providerEntriesVerified=0)

    def start(self):
        with self.lock:
            if self._poll_thread is None:
                self._poll_stop.clear()
                self._poll_thread = Thread(target=self._poll, name='blue-source-reconciliation', daemon=True)
                self._poll_thread.start()
        return self

    def _poll(self):
        while not self._poll_stop.wait(0.25):
            try:
                self.request_completeness(self._requested_boundary)
                self.poll()
            except Exception:
                # Verified state remains unchanged. Workers expose missing or
                # incomplete evidence; a failed notification is retried here.
                continue

    @property
    def trusted(self):
        return frozenset(self.providers)

    def create(self, name, actors, *, key=None):
        with self.lock, self.cache.scope(), self.store.metrics.scope('provider'):
            c = self.catalogue
            actor_ids = [c.admit(c.typed('Principal Actor', accountId=a)) if isinstance(a, str) and a not in self.processor.blue.context.provider else a for a in actors]
            if isinstance(self.store, SQLiteStore):
                if key is None:
                    raise ValueError('A configured Ed25519 private key is required for a persistent provider')
                provider = DurableProvider(c, name, key, actor_ids, self.store)
            else:
                provider = (SignedProvider.generate(c, name, actor_ids) if key is None else
                            SignedProvider(c, name, key, actor_ids))
            self.adopt(provider)
            return provider

    def adopt(self, provider):
        with self.lock, self.cache.scope():
            if provider.catalogue is not self.catalogue:
                # Explicit host adoption imports public content, never keys or
                # provider trust inferred from a business document.
                self.processor.blue.language.provider.merge_responses(provider.catalogue.blue.language.provider.snapshot())
                self.processor.blue.refresh()
            self.providers[provider.timeline] = provider
            if provider.timeline in self.unsubscribers:
                self.unsubscribers[provider.timeline]()
            self.unsubscribers[provider.timeline] = provider.subscribe(self.ingest)
            self.ingest(provider.timeline)

    def retry(self, timeline):
        """Explicit host recovery; signed candidate bindings are rechecked."""
        with self.store.read() as view:
            issue=view.get('source_issues',timeline)
            if issue and issue.get('code')=='HOST_INCOMPLETE':
                publish(self.store,view.packet(str(uuid4()),writes={('source_issues',timeline):None}))
        return self.ingest(timeline)

    def ingest(self, timeline):
        with self.store.read() as view:
            issue=view.get('source_issues',timeline)
            if issue and issue.get('code')=='HOST_INCOMPLETE':return
        try:
            return self._ingest(timeline)
        except HOST_FAILURES as error:
            with self.store.read() as view:
                writes={('source_issues',timeline):{'code':'HOST_INCOMPLETE','details':incomplete(error).context}}
                for _,row in view.scan('subscriptions',timeline+'/'):wake(view,writes,row['instance'])
                publish(self.store,view.packet(str(uuid4()),writes=writes))
            self.on_change()
            raise incomplete(error) from error
        except CoordinationError as error:
            if error.code in {'INVALID_PROVIDER_SIGNATURE', 'CONTRADICTORY_PROVIDER_PREFIX',
                    'ATTESTATION_BINDING_MISMATCH', 'BROKEN_TIMELINE_CHAIN', 'INVALID_SIGNATURE_ENCODING'}:
                while True:
                    with self.store.read() as view:
                        old = view.get('source_issues', timeline)
                        issue = {'code': error.code, 'details': error.details}
                        if old == issue: break
                        writes = {('source_issues', timeline): issue}
                        for _, row in view.scan('subscriptions', timeline + '/'):
                            wake(view, writes, row['instance'])
                        packet = view.packet(str(uuid4()), writes=writes)
                    if publish(self.store, packet).status == 'COMMITTED': break
                self.on_change()
            raise

    def _ingest(self, timeline):
        from .source_records import StoredEntries, order_key
        from .sources import VerifiedPrefix
        with self.lock, self.cache.scope(), self.store.metrics.scope('provider'):
            provider = self.providers[timeline]
            language = self.processor.blue.language
            while True:
                if isinstance(provider, DurableProvider):provider.refresh()
                observed = provider.entries[-1].timestamp if provider.entries else None
                observed_head = provider.entries[-1].blue_id if provider.entries else None
                with self.store.read() as view:
                    old = view.get('sources', timeline)
                    if old is not None and old['before'] == provider.frontier and old.get('observedHead') == observed_head:
                        return
                    prior_view = language.view
                    language.bind(view);self.processor.blue.refresh()
                    try:
                        verifier = PrefixVerifier(self.catalogue, [timeline])
                        count = old.get('count', 0) if old else 0
                        if old and 'count' in old:
                            # These facts were verified on insertion by this
                            # protected source store. They are not upload data.
                            verifier.prefixes[timeline] = VerifiedPrefix(timeline, old['before'],
                                StoredEntries(view,timeline,count),old['guarantee'],old['attestation'])
                        elif old:
                            verifier.verify(old['proof']);count=len(verifier.prefixes[timeline].entries)
                        anchor = verifier.prefixes[timeline].entries[-1].blue_id if count else None
                        last_page={}
                        def pages():
                            for page in provider.pages(after=anchor):
                                if not last_page and provider.catalogue is not self.catalogue:
                                    language.provider.merge_responses(provider.catalogue.blue.language.provider.snapshot())
                                    self.processor.blue.refresh()
                                last_page.clear();last_page.update(page)
                                yield page
                        try:
                            verified=verifier.verify_pages(pages(),store=self.store,
                                generation=old.get('generation',0) if old else 0,anchor=anchor)
                        except CoordinationError as error:
                            if error.code=='UNKNOWN_RANGE_ANCHOR':
                                raise CoordinationError('CONTRADICTORY_PROVIDER_PREFIX',timeline=timeline) from error
                            raise
                        # This bounded final-page carrier is bound to the complete
                        # locally established interval by source_proofs below.
                        proof=self.catalogue.admit(self.catalogue.typed('Timeline Range Evidence',
                            guarantee={'blueId':verified.guarantee},attestation={'blueId':verified.attestation},
                            entries=[{'blueId':i} for i in last_page['entries']],
                            **({'after':{'blueId':last_page['after']}} if last_page['after'] else {})))
                        self.metrics['providerEntriesVerified'] += len(verified.entries)-count
                        writes = content_writes(language.provider,view)
                        for number in range(count,len(verified.entries)):
                            entry=verified.entries[number];raw=entry.wire()
                            writes['source_entries',timeline+'/'+str(number).zfill(16)]=raw
                            writes['source_entry_ids',timeline+'/'+entry.blue_id]={'number':number}
                            writes['source_order',timeline+'/'+order_key(entry.timestamp,entry.blue_id)]=raw
                        generation=(old.get('generation',0) if old else 0)+1
                        verified_head=verified.entries[-1].blue_id if verified.entries else None
                        row=dict(proof=proof,before=verified.before,count=len(verified.entries),generation=generation,
                            guarantee=verified.guarantee,attestation=verified.attestation,head=verified_head,
                            observedHeadTime=observed,observedHead=observed_head)
                        writes['sources',timeline]=row
                        # An immutable proof-to-established-prefix mapping binds
                        # suffix evidence for cold admission and exact replay.
                        prior_proof=view.get('source_proofs',proof)
                        bound=dict(timeline=timeline,before=verified.before,count=len(verified.entries),
                            guarantee=verified.guarantee,attestation=verified.attestation,head=verified_head,
                            predecessor=old['proof'] if old and old['proof']!=proof else None)
                        if prior_proof is None:writes['source_proofs',proof]=bound
                        notified=set()
                        for _, subscriber in view.scan('subscriptions',timeline+'/'):
                            wake(view,writes,subscriber['instance']);notified.add(subscriber['instance'])
                        availability=view.get('availability','timeline:'+timeline,{'generation':0})
                        writes['availability','timeline:'+timeline]={'generation':availability['generation']+1}
                        for key,waiter in view.scan('waiters','timeline:'+timeline+'/'):
                            if waiter['instance'] not in notified: wake(view,writes,waiter['instance']);notified.add(waiter['instance'])
                            writes['waiters',key]=None
                        packet=view.packet(str(uuid4()),writes=writes)
                    finally:
                        language.bind(prior_view)
                        self.processor.blue.refresh()
                if publish(self.store,packet).status=='COMMITTED':
                    language.provider.acknowledge();break
        self.on_change()

    def append(self, timeline, actor, timestamp, message, **options):
        with self.lock, self.cache.scope(), self.store.metrics.scope('provider'):
            provider = self.providers[timeline]
            with self.store.read() as view:
                self.processor.blue.language.bind(view)
                self.processor.blue.refresh()
                try:
                    if not isinstance(message, str):
                        message = self.catalogue.admit(message)
                    entry = provider.append(actor, timestamp, message, **options)
                finally:
                    self.processor.blue.language.bind(None)
                    self.processor.blue.refresh()
            if self.auto_complete:
                self.request_completeness(timestamp + 1)
            return entry

    def request_completeness(self, before):
        self._requested_boundary = max(self._requested_boundary, before)
        if not self.auto_complete or before > self.clock():
            return
        with self.lock, self.cache.scope():
            for provider in self.providers.values():
                if provider.frontier < before:
                    provider.close_before(before)

    def poll(self):
        for timeline in tuple(self.providers):
            self.ingest(timeline)

    def close(self):
        self._poll_stop.set()
        if self._poll_thread is not None:
            self._poll_thread.join(10)
            self._poll_thread = None
        for unsubscribe in self.unsubscribers.values():
            unsubscribe()
        self.unsubscribers.clear()
