"""Ed25519 closed-prefix acquisition, paged transport and overlap verification."""
from dataclasses import dataclass
from threading import RLock
from copy import deepcopy
from bisect import bisect_left
from collections.abc import Sequence
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.exceptions import InvalidSignature
from algorithms import blue as L
from blue_contracts.reference.channels import operation_request
from blue_contracts.reference.model import SAFE, digest
from blue_coordination_spec.model import require, uint, closed, CoordinationError


def transcript(guarantee):
    return ('blue.coordination.guarantee/1\n' + guarantee).encode('utf-8')


@dataclass(frozen=True)
class VerifiedPrefix:
    timeline: str
    before: int
    entries: tuple
    guarantee: str
    attestation: str


class ExtendedEntries(Sequence):
    """Share an immutable prefix rather than copying it on every extension."""
    def __init__(self, prefix, suffix):
        self.prefix, self.suffix = prefix, tuple(suffix)
        self.count = len(prefix) + len(suffix)
    def __len__(self):return self.count
    def __getitem__(self, index):
        if isinstance(index,slice):return tuple(self[i] for i in range(*index.indices(self.count)))
        if index<0:index+=self.count
        if not 0<=index<self.count:raise IndexError(index)
        node=self
        while isinstance(node,ExtendedEntries):
            if index>=len(node.prefix):return node.suffix[index-len(node.prefix)]
            node=node.prefix
        return node[index]


class SignedProvider:
    """Trusted ingress owns authentication and provenance, not submitted YAML.

    Supply configured keys for durable deployments. generate() is an explicit
    local/demo convenience; private keys never appear in portable evidence.
    """
    def __init__(self, catalogue, name, key, actors, *, notify=None):
        self.catalogue, self.key = catalogue, key
        self.actors = frozenset(actors)
        for actor in self.actors:
            catalogue.actor(actor)
        self.timeline = catalogue.admit(catalogue.typed('Signed Timeline', timelineId=name,
            publicKey=key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()))
        self.entries = []
        self._entry_index = {}
        self.frontier = 0
        self.requests = {}
        self._listeners = [notify] if notify else []
        self._lock = RLock()

    @classmethod
    def generate(cls, catalogue, name, actors, **options):
        return cls(catalogue, name, Ed25519PrivateKey.generate(), actors, **options)

    def subscribe(self, notify):
        with self._lock:
            self._listeners.append(notify)
        def unsubscribe():
            with self._lock:
                if notify in self._listeners:
                    self._listeners.remove(notify)
        return unsubscribe

    def _notify(self):
        # Notifications are hints. Failure never reverses an accepted append;
        # durable source reconciliation is the consumer's recovery mechanism.
        with self._lock:
            callbacks = tuple(self._listeners)
        for callback in callbacks:
            try:
                callback(self.timeline)
            except Exception:
                continue

    def append(self, actor, timestamp, message, *, source=None, authority=None, request_id=None):
        uint(timestamp)
        require(actor in self.actors, 'APPEND_NOT_AUTHORIZED')
        fingerprint = digest('coordination.provider-request/1', dict(actor=actor, timestamp=timestamp,
            message=message, source=source, authority=authority))
        with self._lock:
            if request_id is not None:
                require(type(request_id) is str and bool(request_id), 'INVALID_REQUEST_ID')
                if request_id in self.requests:
                    old, entry = self.requests[request_id]
                    require(old == fingerprint, 'IDEMPOTENCY_CONFLICT')
                    return entry
            require(timestamp >= self.frontier and (not self.entries or timestamp > self.entries[-1].timestamp), 'BACKDATED_APPEND')
            c = self.catalogue
            c.blue.certify(L.Ref(message))
            if source is not None:
                require(c.is_type(L.Ref(source), 'Source'), 'INVALID_SOURCE_TYPE')
            raw = c.typed('Timeline Entry', timeline={'blueId': self.timeline}, timestamp=timestamp,
                          actor={'blueId': actor}, message={'blueId': message})
            if operation_request(c.processor.registry, L.Ref(message)) is not None:
                raw['operation'] = {'blueId': message}
            if self.entries:
                raw['prevEntry'] = {'blueId': self.entries[-1].blue_id}
            if source:
                raw['source'] = {'blueId': source}
            if authority:
                raw['onBehalfOf'] = {'blueId': authority}
            entry = c.entry(c.admit(raw))
            self.entries.append(entry)
            self._entry_index[entry.blue_id] = len(self.entries)-1
            if request_id is not None:
                self.requests[request_id] = (fingerprint, entry)
        self._notify()
        return entry

    def close_before(self, before):
        uint(before, SAFE + 1)
        with self._lock:
            require(before >= self.frontier, 'FRONTIER_REGRESSION')
            self.frontier = before
        self._notify()

    def page(self, before=None, *, after=None, limit=256):
        require(type(limit) is int and limit > 0, 'INVALID_PAGE_LIMIT')
        with self._lock:
            before = self.frontier if before is None else uint(before, SAFE + 1)
            require(before <= self.frontier, 'UNESTABLISHED_COMPLETENESS')
            end = bisect_left(self.entries, before, key=lambda e:e.timestamp)
            if after is not None:
                index = self._entry_index.get(after)
                require(index is not None and index < end, 'UNKNOWN_RANGE_ANCHOR')
                offset = index + 1
            else:
                offset = 0
            c = self.catalogue
            guarantee = c.admit(c.typed('Timeline Completeness Guarantee', timeline={'blueId': self.timeline},
                completeBefore=before, **({'lastEntry': {'blueId': self.entries[end-1].blue_id}} if end else {})))
            attestation = c.admit(c.typed('Timeline Attestation', timeline={'blueId': self.timeline},
                guarantee={'blueId': guarantee}, signature=self.key.sign(transcript(guarantee)).hex()))
            selected = [e.blue_id for e in self.entries[offset:min(offset+limit,end)]]
            return dict(guarantee=guarantee, attestation=attestation, after=after,
                        entries=selected, more=offset + len(selected) < end)

    def pages(self, before=None, *, after=None, limit=256):
        first = self.page(before, after=after, limit=limit)
        bound = self.catalogue.read(first['guarantee'], 'Timeline Completeness Guarantee')['completeBefore']
        yield first
        while first['more']:
            first = self.page(bound, after=first['entries'][-1], limit=limit)
            yield first

    def evidence(self, before=None, *, after=None):
        pages = list(self.pages(before, after=after))
        c = self.catalogue
        return c.admit(c.typed('Timeline Range Evidence',
            guarantee={'blueId': pages[0]['guarantee']}, attestation={'blueId': pages[0]['attestation']},
            entries=[{'blueId': i} for page in pages for i in page['entries']],
            **({'after': {'blueId': after}} if after else {})))


class PrefixVerifier:
    """Adopted provider authority plus exact authenticated contiguous prefixes."""
    def __init__(self, catalogue, trusted=()):
        self.catalogue = catalogue
        self.trusted = frozenset(trusted)
        self.prefixes = {}

    def _authentication(self, guarantee, attestation):
        c = self.catalogue
        g = c.read(guarantee, 'Timeline Completeness Guarantee')
        a = c.read(attestation, 'Timeline Attestation')
        timeline = c.link(guarantee, 'timeline')
        require(timeline in self.trusted, 'UNTRUSTED_PROVIDER')
        t = c.timeline(timeline)
        require(c.link(attestation, 'timeline') == timeline and c.link(attestation, 'guarantee') == guarantee, 'ATTESTATION_BINDING_MISMATCH')
        signature = a['signature']
        require(type(signature) is str and len(signature) == 128 and all(x in '0123456789abcdef' for x in signature), 'INVALID_SIGNATURE_ENCODING')
        try:
            Ed25519PublicKey.from_public_bytes(bytes.fromhex(t['publicKey'])).verify(bytes.fromhex(signature), transcript(guarantee))
        except InvalidSignature as exc:
            raise CoordinationError('INVALID_PROVIDER_SIGNATURE') from exc
        return timeline, uint(g['completeBefore'], SAFE + 1), c.link(guarantee, 'lastEntry', optional=True)

    def verify(self, evidence):
        c = self.catalogue
        c.read(evidence, 'Timeline Range Evidence')
        return self.verify_pages([dict(guarantee=c.link(evidence, 'guarantee'),
            attestation=c.link(evidence, 'attestation'), after=c.link(evidence, 'after', optional=True),
            entries=list(c.links(evidence, 'entries')), more=False)])

    def verify_pages(self, pages, *, store=None, generation=0, anchor=...):
        """Stream one signed candidate; incomplete pages never expand completeness.

        With a private store, verified page facts and their exact binding survive
        restart. A resumed transport may begin at the retained cursor when the
        original anchor is supplied. Replayed pages must match retained facts.
        """
        from itertools import chain
        from uuid import uuid4
        from .work import publish
        from .source_records import AcquiredEntries
        pages=iter(pages)
        first=next(pages,None)
        require(first is not None,'MISSING_RANGE_EVIDENCE')
        closed(first, {'guarantee','attestation','after','entries','more'})
        timeline,before,head=self._authentication(first['guarantee'],first['attestation'])
        old=self.prefixes.get(timeline)
        origin=first['after'] if anchor is ... else anchor
        retained=();anchored=False
        if origin is not None:
            if old is not None and old.entries and origin==old.entries[-1].blue_id:
                retained=old.entries;anchored=before>=old.before
            else:
                require(old is not None,'UNESTABLISHED_RANGE_ANCHOR')
                at=next((i for i,e in enumerate(old.entries) if e.blue_id==origin),None)
                require(at is not None,'UNESTABLISHED_RANGE_ANCHOR')
                retained=old.entries[:at+1]
            require(retained[-1].timestamp<before,'ANCHOR_OUTSIDE_PREFIX')
        binding=dict(timeline=timeline,guarantee=first['guarantee'],attestation=first['attestation'],
                     generation=generation,anchor=origin,before=before,head=head,
                     priorBefore=old.before if old else None)
        key=digest('coordination.prefix-acquisition/1',binding)
        self.acquisition=key
        progress=None
        if store is not None:
            with store.read() as view:progress=view.get('source_acquisitions',key)
            if progress is not None:require(progress['binding']==binding,'RANGE_PAGE_BINDING_MISMATCH')
        count=0;previous=origin;last_time=retained[-1].timestamp if retained else -1
        if first['after']!=origin:
            require(progress is not None and first['after']==progress['last'],'NONCONTIGUOUS_RANGE_PAGE')
            count=progress['count'];previous=progress['last'];last_time=progress['timestamp']
        suffix=[];final=False
        for page in chain((first,),pages):
            require(not final,'INCOMPLETE_RANGE')
            closed(page, {'guarantee','attestation','after','entries','more'})
            require(type(page['more']) is bool and type(page['entries']) is list,'INVALID_RANGE_PAGE')
            require(page['guarantee']==binding['guarantee'] and page['attestation']==binding['attestation'],'RANGE_PAGE_BINDING_MISMATCH')
            require(page['after']==previous,'NONCONTIGUOUS_RANGE_PAGE')
            require(not page['more'] or bool(page['entries']),'EMPTY_CONTINUATION_PAGE')
            batch=[]
            for identity in page['entries']:
                if progress and count<progress['count']:
                    with store.read() as view:raw=view.get('source_acquisition_entries',key+'/'+str(count).zfill(20))
                    require(raw is not None and raw['blue_id']==identity,'CONFLICTING_RANGE_PAGE')
                    from blue_coordination_spec.model import Entry
                    entry=Entry(**raw)
                else:
                    with self.catalogue.admission_unit():entry=self.catalogue.entry(identity)
                require(entry.timeline==timeline and entry.previous==previous,'BROKEN_TIMELINE_CHAIN')
                require(last_time<entry.timestamp<before,'INVALID_TIMELINE_ORDER')
                if anchored:require(entry.timestamp>=old.before,'CONTRADICTORY_PROVIDER_PREFIX')
                batch.append((count,entry));count+=1
                previous,last_time=identity,entry.timestamp
            final=not page['more']
            if final:require(previous==head,'INCOMPLETE_RANGE')
            if store is None:suffix.extend(entry for _,entry in batch)
            else:
                with store.read() as view:
                    prior=view.get('source_acquisitions',key)
                    writes={}
                    for number,entry in batch:
                        record_key=key+'/'+str(number).zfill(20)
                        existing=view.get('source_acquisition_entries',record_key)
                        require(existing is None or existing==entry.wire(),'CONFLICTING_RANGE_PAGE')
                        if existing is None:writes['source_acquisition_entries',record_key]=entry.wire()
                    # Never move a durable cursor backwards on replay.
                    if prior is None or prior['count']<=count:
                        writes['source_acquisitions',key]=dict(binding=binding,count=count,last=previous,timestamp=last_time)
                    packet=view.packet(str(uuid4()),writes=writes)
                require(publish(store,packet).status=='COMMITTED','ACQUISITION_CONFLICT')
        require(final,'INCOMPLETE_RANGE')
        if store is not None:suffix=AcquiredEntries(store,key,count)
        else:suffix=tuple(suffix)
        combined=retained if not count else JoinedEntries(retained,suffix) if retained else suffix
        result=VerifiedPrefix(timeline,before,combined,binding['guarantee'],binding['attestation'])
        if old and not anchored:
            # Compare the closed overlap incrementally, never allocate a whole ID list.
            overlap=min(old.before,before)
            a=iter(e.blue_id for e in old.entries if e.timestamp<overlap)
            b=iter(e.blue_id for e in result.entries if e.timestamp<overlap)
            from itertools import zip_longest
            require(all(x==y for x,y in zip_longest(a,b,fillvalue=object())),'CONTRADICTORY_PROVIDER_PREFIX')
        if old is None or before>=old.before:self.prefixes[timeline]=result
        return result


class JoinedEntries(Sequence):
    """A closed prefix plus a verified streamed suffix, without copying either."""
    def __init__(self,prefix,suffix):self.prefix,self.suffix=prefix,suffix
    def __len__(self):return len(self.prefix)+len(self.suffix)
    def __getitem__(self,index):
        if isinstance(index,slice):return tuple(self[i] for i in range(*index.indices(len(self))))
        if index<0:index+=len(self)
        if not 0<=index<len(self):raise IndexError(index)
        return self.prefix[index] if index<len(self.prefix) else self.suffix[index-len(self.prefix)]
    def __eq__(self,other):return len(self)==len(other) and all(a==b for a,b in zip(self,other))
