"""Configured-key provider with atomic accepted-entry/content persistence."""
from copy import deepcopy
from uuid import uuid4
from blue_coordination_spec.model import Entry, require
from .sources import SignedProvider
from .content import content_writes
from .work import publish


class DurableProvider(SignedProvider):
    def __init__(self, catalogue, name, key, actors, store):
        self.store = store
        self._suppress_notifications = False
        self._loaded_revision = None
        super().__init__(catalogue, name, key, actors)
        with store.read() as view:
            self._restore(view)

    def _restore(self, view):
        row = view.get('provider_heads', self.timeline)
        if row is None:
            self.entries, self.frontier, self.requests = [], 0, {}
            self._entry_index = {}
            self._loaded_revision = None
            return
        require(set(row['actors']) == set(self.actors), 'PROVIDER_ACTOR_CONFIGURATION_MISMATCH')
        if row['revision'] != self._loaded_revision:
            require(len(self.entries) <= row['count'], 'PROVIDER_PREFIX_REGRESSION')
            if self.entries:
                anchor=view.get('provider_entries',self.timeline+'/'+str(len(self.entries)-1).zfill(16))
                require(anchor and anchor['entry']==self.entries[-1].wire(), 'CONTRADICTORY_PROVIDER_PREFIX')
            start=self.timeline+'/'+str(len(self.entries)).zfill(16)
            while len(self.entries)<row['count']:
                page=view.page('provider_entries',self.timeline+'/',start=start,limit=min(256,row['count']-len(self.entries)))
                require(bool(page), 'MISSING_PROVIDER_PREDECESSOR')
                for _, item in page:
                    entry=Entry(**item['entry'])
                    require(entry.previous==(self.entries[-1].blue_id if self.entries else None), 'BROKEN_TIMELINE_CHAIN')
                    self._entry_index[entry.blue_id]=len(self.entries);self.entries.append(entry)
                start=self.timeline+'/'+str(len(self.entries)).zfill(16)
            self.frontier = row['frontier']
            self._loaded_revision = row['revision']

    def refresh(self):
        with self._lock, self.store.read() as view:
            self._restore(view)

    def _notify(self):
        if not self._suppress_notifications:
            super()._notify()

    def _transaction(self, action, *, request_id=None):
        language = self.catalogue.blue.language
        with self._lock:
            while True:
                with self.store.read() as view:
                    prior_view = language.view
                    language.bind(view)
                    self.catalogue.blue.refresh()
                    prior_count, prior_requests = len(self.entries), set(self.requests)
                    try:
                        self._restore(view)
                        prior_count = len(self.entries)
                        prior_requests = set(self.requests)
                        if request_id is not None and request_id not in self.requests:
                            request=view.get('provider_requests',self.timeline+'/'+request_id)
                            if request is not None:
                                self.requests[request_id]=(request['fingerprint'],Entry(**request['entry']))
                                prior_requests.add(request_id)
                        self._suppress_notifications = True
                        result = action()
                        self._suppress_notifications = False
                        revision = str(uuid4())
                        writes = content_writes(language.provider, view)
                        writes['provider_heads', self.timeline] = dict(actors=sorted(self.actors),
                            frontier=self.frontier, revision=revision, count=len(self.entries))
                        for number in range(prior_count, len(self.entries)):
                            writes['provider_entries', self.timeline + '/' + str(number).zfill(16)] = {'entry': self.entries[number].wire()}
                        for key in set(self.requests) - prior_requests:
                            fingerprint, entry = self.requests[key]
                            writes['provider_requests', self.timeline + '/' + key] = dict(request=key, fingerprint=fingerprint, entry=entry.wire())
                        packet = view.packet(revision, writes=writes)
                    except BaseException:
                        self.entries=self.entries[:prior_count]
                        self._entry_index={e.blue_id:i for i,e in enumerate(self.entries)}
                        self.requests={k:v for k,v in self.requests.items() if k in prior_requests}
                        self._loaded_revision = None
                        raise
                    finally:
                        self._suppress_notifications = False
                        language.bind(prior_view)
                        self.catalogue.blue.refresh()
                committed = publish(self.store, packet)
                if committed.status == 'COMMITTED':
                    language.provider.acknowledge()
                    self._loaded_revision = revision
                    break
                self.entries=self.entries[:prior_count]
                self._entry_index={e.blue_id:i for i,e in enumerate(self.entries)}
                self.requests={k:v for k,v in self.requests.items() if k in prior_requests}
                self._loaded_revision = None
        self._notify()
        return result

    def append(self, *args, **kwargs):
        return self._transaction(lambda: super(DurableProvider, self).append(*args, **kwargs), request_id=kwargs.get('request_id'))

    def close_before(self, before):
        return self._transaction(lambda: super(DurableProvider, self).close_before(before))
