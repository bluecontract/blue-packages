"""Durable wake generations, fenced worker claims and dependency registration."""
from copy import deepcopy
import time
from uuid import uuid4
from .store import PublicationUnknown


def publish(store, packet):
    try:
        return store.commit(packet)
    except PublicationUnknown:
        # Reconcile the ORIGINAL identity. Never retry work under a fresh ID.
        result = store.resolve(packet.publication)
        if result is None:
            raise
        return result


def wake(view, writes, instance, *, now=0):
    prior = writes.get(('work', instance), view.get('work', instance)) or dict(
        requested=0, checked=0, fence=0, owner=None, leaseUntil=0,
        status='READY', issue=None, remaining=False)
    row = deepcopy(prior)
    if prior['requested'] == prior['checked']:row['requestedAt'] = time.time()
    row['requested'] += 1
    host_wait=(row.get('issue') or {}).get('code')=='HOST_INCOMPLETE'
    if row['status'] != 'ERROR' and not host_wait and row['owner'] is None:
        row['status'] = 'PROCESSING'
    writes['work', instance] = row
    writes['due', instance] = None if row['status'] == 'ERROR' or host_wait else {'at': now, 'eligibleAt': time.time() if now == 0 else now}


class WorkQueue:
    def __init__(self, store, *, clock=time.time, lease_seconds=30):
        self.store, self.clock, self.lease_seconds = store, clock, lease_seconds
        self._cursor = None

    def request(self, instance):
        while True:
            with self.store.read() as view:
                writes = {}
                wake(view, writes, instance)
                packet = view.packet(str(uuid4()), writes=writes)
            if publish(self.store, packet).status == 'COMMITTED':
                return

    def claim(self, owner, *, limit=64, context=None):
        if limit < 1: raise ValueError('positive page size required')
        now=self.clock();cursor=self._cursor;wrap=cursor is not None
        while True:
            with self.store.read() as view:
                candidates=view.due(now,after=cursor,limit=limit)
            self.store.metrics.add('claimPages')
            for _due_time, instance in candidates:
                with self.store.read() as view:
                    row = view.get('work', instance)
                    current_due = view.get('due', instance)
                    lease = view.get('leases', instance)
                    reservation = view.get('reservation', instance)
                    if reservation is not None:
                        wave = view.get('waves', reservation['wave'])
                        if wave is not None and wave['source'] != instance:
                            continue  # The wave owner drives this receiving work.
                    if context is not None:
                        scope = view.project('heads', instance, ('context',)) or view.get('registration', instance)
                        if scope is None or scope['context'] != context:
                            continue
                    if row is None or current_due is None or current_due['at'] > now:
                        continue
                    if row['status'] == 'ERROR':
                        continue
                    until = lease['until'] if lease and lease['owner'] == row['owner'] and lease['fence'] == row['fence'] else row['leaseUntil']
                    if row['owner'] and until > now:
                        continue
                    row.update(owner=owner, leaseUntil=now + self.lease_seconds,
                               fence=row['fence'] + 1, status='PROCESSING', issue=None)
                    row['queueWaitSeconds'] = max(0,now-current_due.get('eligibleAt',current_due['at'] or now))
                    packet = view.packet(str(uuid4()), writes={('work', instance): row,
                        ('due', instance): {'at': now + self.lease_seconds},
                        ('leases', instance): dict(owner=owner, fence=row['fence'], until=now + self.lease_seconds)}, result=dict(instance=instance, **row))
                result = publish(self.store, packet)
                if result.status == 'COMMITTED':
                    self._cursor=(_due_time,instance)
                    return result.result
            if len(candidates)==limit:
                cursor=candidates[-1]
                continue  # Exhausted candidates are not evidence that the queue is empty.
            if wrap:
                cursor=None;wrap=False
                continue
            self._cursor=None
            return None

    def renew(self, claim):
        """Lease liveness is separate from the attempt's semantic read set."""
        with self.store.read() as view:
            row = view.get('work', claim['instance'])
            lease = view.get('leases', claim['instance'])
            if row is None or row['owner'] != claim['owner'] or row['fence'] != claim['fence']:
                return False
            packet = view.packet(str(uuid4()), writes={('leases', claim['instance']): dict(
                owner=claim['owner'], fence=claim['fence'], until=self.clock() + self.lease_seconds)})
        return publish(self.store, packet).status == 'COMMITTED'

    def release_unpublished(self, claim):
        """A rejected CAS must remain due, not wait for its own lease expiry."""
        while True:
            with self.store.read() as view:
                row = view.get('work', claim['instance'])
                if row is None or row['owner'] != claim['owner'] or row['fence'] != claim['fence']:
                    return False
                writes = {}
                self.finish(view, writes, claim, remaining=True)
                packet = view.packet(str(uuid4()), writes=writes)
            if publish(self.store, packet).status == 'COMMITTED':
                return True

    def finish(self, view, writes, claim, *, status='READY', issue=None, remaining=False, poll_after=None):
        instance = claim['instance']
        current = view.get('work', instance)
        if current is None or current['owner'] != claim['owner'] or current['fence'] != claim['fence']:
            raise RuntimeError('Stale worker claim')
        view.acknowledgements[instance]={'observed':deepcopy(current),'time':self.clock()}
        current.update(checked=max(current['checked'], claim['requested']), status=status,
                       issue=deepcopy(issue), owner=None, leaseUntil=0, remaining=remaining)
        writes['work', instance] = current
        host_wait=(issue or {}).get('code')=='HOST_INCOMPLETE'
        more = not host_wait and status != 'ERROR' and (current['requested'] > current['checked'] or remaining)
        writes['due', instance] = ({'at': 0,'eligibleAt':self.clock()} if more else
            {'at': self.clock() + poll_after,'eligibleAt':self.clock()+poll_after} if poll_after is not None else None)

    def wait(self, claim, resources, issue, *, poll_after=1):
        """Registration and availability are protected by one read/commit set."""
        with self.store.read() as view:
            writes = {}
            for resource, observed_generation in resources.items():
                current = view.get('availability', resource, {'generation': 0})
                if current['generation'] != observed_generation:
                    self.finish(view, writes, claim, remaining=True)
                    break
                writes['waiters', resource + '/' + claim['instance']] = dict(instance=claim['instance'], generation=observed_generation)
            else:
                self.finish(view, writes, claim, status='WAITING', issue=issue, poll_after=poll_after)
            packet = view.packet(str(uuid4()), writes=writes)
        return publish(self.store, packet)

    def available(self, resource, *, companion_writes=None):
        while True:
            with self.store.read() as view:
                row = view.get('availability', resource, {'generation': 0})
                writes = deepcopy(companion_writes or {})
                writes['availability', resource] = {'generation': row['generation'] + 1}
                for key, waiter in view.scan('waiters', resource + '/'):
                    wake(view, writes, waiter['instance'])
                    writes['waiters', key] = None
                packet = view.packet(str(uuid4()), writes=writes)
            result = publish(self.store, packet)
            if result.status == 'COMMITTED':
                return result


class WavePlanner:
    """Legacy record name; reservations now cover one turn's actual SCC owners."""
    def __init__(self, store):
        self.store = store

    def closure(self, view, sources):
        """Reserve actual cyclic owners, never acyclic containing consumers.

        Follow authored forward edges only. Reverse reachability within that
        captured graph identifies the SCC containing each requested owner.
        A producer with no outgoing edges never reads any consumer's state.
        """
        origins = set(sources)
        graph, pending = {}, list(origins)
        while pending:
            member = pending.pop()
            if member in graph:
                continue
            children = {row['source'] for _, row in view.scan('forward', member + '/')}
            graph[member] = children
            pending.extend(children - graph.keys())
        reverse = {member: set() for member in graph}
        for member, children in graph.items():
            for child in children:
                reverse[child].add(member)
        owners = set(origins)
        for origin in origins:
            reaches_origin, pending = set(), [origin]
            while pending:
                member = pending.pop()
                if member not in reaches_origin:
                    reaches_origin.add(member)
                    pending.extend(reverse[member])
            # All nodes were discovered forward from the selected origins;
            # reserve only those also reachable from this particular origin.
            reachable, pending = set(), [origin]
            while pending:
                member = pending.pop()
                if member not in reachable:
                    reachable.add(member)
                    pending.extend(graph[member])
            owners.update(reachable & reaches_origin)
        return sorted(owners)

    def reserve(self, source, order, *, prerequisites=(), observed=None, continue_view=False):
        while True:
            from contextlib import nullcontext
            with (nullcontext(observed) if observed is not None else self.store.read()) as view:
                members = self.closure(view, [source, *prerequisites])
                reservations = [view.get('reservation', member) for member in members]
                if any(row is not None for row in reservations):
                    return None
                for member in members:
                    control = view.get('control', member, {'paused': False})
                    if control['paused']:
                        return None
                identity = str(uuid4())
                wave = dict(identity=identity, source=source, order=list(order), members=members,
                            phase='SOURCE', pending=[], status='PROCESSING')
                writes = {('reservation', member): {'wave': identity} for member in members}
                # Reservation alone excludes new peer claims. Do not read/write
                # their churning work rows here: concurrent SCC contenders would
                # otherwise invalidate each other's acquisition indefinitely.
                # Existing peer attempts are fenced by their reservation reads;
                # owner publication additionally requires their lease release.
                writes['waves', identity] = wave
                packet = view.packet('reserve:' + identity, writes=writes, result=wave)
            result = publish(self.store, packet)
            if result.status == 'COMMITTED':
                if continue_view and observed is not None:
                    observed._reservation_continued=observed.continue_after(packet)
                return result.result
            if observed is not None:
                return None

    def extend(self, view, wave, instances):
        """Acquire newly discovered actual writers before repeating a join.

        A concurrent peer's tentative packet is fenced by its reservation read.
        Let its active attempt finish/release normally; the next source turn
        observes that release. Never reserve unrelated containing consumers.
        """
        members=sorted(set(wave['members']) | set(instances))
        writes={}
        for member in members:
            row=view.get('reservation',member)
            if row is not None and row != {'wave':wave['identity']}:
                return False
            if view.get('control',member,{'paused':False})['paused']:
                return False
            if member not in wave['members']:
                writes['reservation',member]={'wave':wave['identity']}
        current=view.get('waves',wave['identity'])
        if current != wave:
            return False
        writes['waves',wave['identity']]={**wave,'members':members}
        return publish(self.store,view.packet(str(uuid4()),writes=writes)).status=='COMMITTED'

    def finish(self, view, writes, wave):
        for member in wave['members']:
            reservation = view.get('reservation', member)
            if reservation is None or reservation['wave'] != wave['identity']:
                raise RuntimeError('Lost wave reservation')
            writes['reservation', member] = None
            wake(view, writes, member)
        writes['waves', wave['identity']] = {**wave, 'status': 'READY', 'phase': 'COMPLETE'}
