"""Versioned logical records and conditional, idempotent atomic publication.

No account-wide runtime snapshot or revision is replaced. Point reads include
tombstones, range reads include absence, and every writer uses this protocol.
Computation happens outside the short publication lock/SQLite writer transaction.
"""
from __future__ import annotations
from bisect import bisect_right, bisect_left, insort
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from threading import RLock
from uuid import uuid4
from weakref import WeakValueDictionary
from .observability import Metrics
from blue_runtime.immutable_bytes import BytePool


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def prefix_end(prefix):
    """Exclusive UTF-8 binary upper bound; SQL metacharacters stay literal."""
    for index in range(len(prefix)-1, -1, -1):
        value=ord(prefix[index])
        if value < 0x10ffff:
            return prefix[:index]+chr(0xe000 if value==0xd7ff else value+1)
    return None


def range_rows(connection, columns, family, prefix):
    upper=prefix_end(prefix)
    sql='SELECT '+columns+' FROM records WHERE family=? AND key>=?'
    parameters=[family,prefix]
    if upper is not None:
        sql+=' AND key<?';parameters.append(upper)
    return connection.execute(sql+' ORDER BY key',parameters)

def fingerprint(value):
    # Physical publication identity, deliberately not a Blue content identity.
    return 'sha256:' + hashlib.sha256(encode(value).encode()).hexdigest()


class StoreError(RuntimeError):
    pass


class PublicationUnknown(StoreError):
    def __init__(self, publication):
        self.publication = publication
        super().__init__('Publication acknowledgment lost: ' + publication)


@dataclass
class Packet:
    publication: str
    application: str
    points: dict
    ranges: dict
    writes: dict = field(default_factory=dict)
    result: object = None
    leases: dict = field(default_factory=dict)
    acknowledgements: dict = field(default_factory=dict)
    prefixes: dict = field(default_factory=dict)

    def wire(self):
        wire = dict(publication=self.publication, application=self.application,
            points=[[f, k, v] for (f, k), v in sorted(self.points.items())],
            ranges=[[f, p, list(v)] for (f, p), v in sorted(self.ranges.items())],
            writes=[[f, k, v] for (f, k), v in sorted(self.writes.items())], result=self.result,
            leases=self.leases)
        if self.acknowledgements:wire['acknowledgements']=self.acknowledgements
        if self.prefixes:wire['prefixes']=self.prefixes
        return wire


def publication_writes(packet, current):
    """Merge only monotonic input progress and pending wake hints atomically.

    All business/control reads still use ordinary point/range conflicts.
    A renewed lease uses its owner/fence/expiry guard, never an old expiry row.
    """
    writes=dict(packet.writes);compatible=set()
    for instance,ack in packet.acknowledgements.items():
        old=ack['observed'];now=current.get('work',instance)
        if now is None or now['requested']<old['requested']:return None,set()
        stable=lambda row:{k:v for k,v in row.items() if k not in ('requested','requestedAt')}
        if stable(now)!=stable(old):return None,set()
        desired=deepcopy(writes['work',instance])
        desired['requested']=now['requested']
        if 'requestedAt' in now:desired['requestedAt']=now['requestedAt']
        writes['work',instance]=desired;compatible.add(('work',instance))
        if (desired['status']!='ERROR' and (desired.get('issue') or {}).get('code')!='HOST_INCOMPLETE'
                and (desired['requested']>desired['checked'] or desired['remaining'])):
            due=current.get('due',instance)
            writes['due',instance]={'at':0,'eligibleAt':(due or {}).get('eligibleAt',ack['time'])}
    for timeline,prior in packet.prefixes.items():
        now=current.get('sources',timeline)
        if now is None or now['before']<prior['before'] or now['count']<prior['count']:
            return None,set()
        if prior['count']:
            entry=current.get('source_entries',timeline+'/'+str(prior['count']-1).zfill(16))
            if entry is None or entry['blue_id']!=prior['head']:return None,set()
        compatible.add(('sources',timeline))
    return writes,compatible


@dataclass(frozen=True)
class Commit:
    status: str
    result: object = None
    publication: str | None = None


@dataclass(frozen=True, slots=True)
class StoredJSON:
    """Owned immutable JSON segments; opening produces a detached caller tree.

    Outcome observation fields share the exact same bytes held by sealed local
    results. The pool is only deduplication, never identity/admission evidence.
    Both canonical public JSON and untrusted-input validation remain unchanged.
    """
    parts: tuple
    size: int
    fields: tuple | None = None

    @classmethod
    def capture(cls, value, pool=None, *, split_records=True):
        share=pool.intern if pool is not None else lambda b:b
        def encoded(item):return share(encode(item).encode('utf-8'))
        if split_records and type(value) is dict and type(value.get('snapshot')) is dict:
            # Heads and retained versions share immutable snapshot/bundle bytes.
            # Metadata reads can open a few fields without decoding that graph.
            columns = tuple((key, encoded(value[key])) for key in sorted(value))
            parts = [b'{']
            for index, (key, body) in enumerate(columns):
                if index: parts.append(b',')
                parts.extend((encoded(key), b':', body))
            parts.append(b'}')
            return cls(tuple(parts), sum(map(len, parts)), columns)
        if type(value) is dict and type(value.get('observations')) is dict:
            parts=[b'{']
            for i,key in enumerate(sorted(value)):
                if i:parts.append(b',')
                parts.extend((encoded(key),b':'))
                if key!='observations':parts.append(encoded(value[key]));continue
                parts.append(b'{')
                for j,field in enumerate(sorted(value[key])):
                    if j:parts.append(b',')
                    parts.extend((encoded(field),b':',encoded(value[key][field])))
                parts.append(b'}')
            parts.append(b'}');parts=tuple(parts)
        else:parts=(encoded(value),)
        return cls(parts,sum(map(len,parts)))

    def open(self): return json.loads(b''.join(self.parts))

    def open_fields(self, names):
        if self.fields is not None:
            return {key: json.loads(body) for key, body in self.fields if key in names}
        value = self.open()
        if type(value) is not dict:
            raise StoreError('Metadata projection requires an object record')
        return {key: value[key] for key in names if key in value}


class ReadView:
    def __init__(self, store):
        self.store = store
        self.points, self.ranges = {}, {}
        self.leases = {}
        self.acknowledgements,self.prefixes={},{}
        self.closed = False

    def _check(self):
        if self.closed:
            raise StoreError('Read view is closed')

    def _size(self, family, key, version, value):
        return len(encode(value).encode()) if value is not None else 0

    def _detach(self, value): return deepcopy(value)

    def get(self, family, key, default=None):
        self._check()
        version, value = self._point(family, key)
        self.points[family, key] = version
        self.store.metrics.add('recordsRead', 1)
        self.store.metrics.add('bytesRead', self._size(family,key,version,value))
        return self._detach(value) if value is not None else deepcopy(default)

    def project(self, family, key, names):
        """Read selected top-level fields with the SAME whole-record predicate.

        This is physical projection, not weaker validation or a partial record
        publication. Missing fields remain absent; explicit null remains present.
        Callers that need a snapshot still use get().
        """
        self._check()
        names = tuple(dict.fromkeys(names))
        if not all(type(name) is str and name.isidentifier() for name in names):
            raise StoreError('Projection fields must be identifiers')
        if not self.store.project_records:
            value = self.get(family, key)
            return None if value is None else {k: value[k] for k in names if k in value}
        revision, value = self._project(family, key, names)
        self.points[family, key] = revision
        self.store.metrics.add('recordsRead', 1)
        self.store.metrics.add('projectionReads', 1)
        self.store.metrics.add('bytesRead', len(encode(value).encode()) if value is not None else 0)
        return value

    def scan(self, family, prefix='', *, limit=None):
        self._check()
        rows = self._range(family, prefix)
        # Protect the complete predicate, including insertion before a selected
        # first candidate. Tombstones prevent delete/recreate ABA.
        self.ranges[family, prefix] = tuple((k, revision) for k, revision, _ in rows)
        live = [(k, self._detach(value)) for k, _, value in rows if value is not None]
        selected = live if limit is None else live[:limit]
        selected_keys = {key for key,_ in selected}
        self.store.metrics.add('recordsRead', len(selected))
        self.store.metrics.add('bytesRead', sum(self._size(family,k,rev,v) for k,rev,v in rows if v is not None and (limit is None or k in selected_keys)))
        return selected

    def get_many(self, family, keys):
        return {key: self.get(family, key) for key in dict.fromkeys(keys)}

    def revisions(self, family, keys):
        """Read revision evidence without decoding immutable descriptor bodies."""
        self._check()
        result = {key: self._point(family, key)[0] for key in dict.fromkeys(keys)}
        self.points.update({(family, key): revision for key, revision in result.items()})
        self.store.metrics.add('revisionReads', len(result))
        return result

    def matches(self, facts):
        """Revalidate a bounded wait certificate in this coherent read scope."""
        by_family = {}
        for family, key, revision in facts['points']:
            by_family.setdefault(family, {})[key] = revision
        for family, expected in by_family.items():
            if self.revisions(family, expected) != expected:
                return False
        for family, prefix, expected in facts['ranges']:
            self.scan(family, prefix)
            if list(map(list, self.ranges[family, prefix])) != expected:
                return False
        return True

    def continue_after(self, packet):
        """Continue this *same* private attempt after its reservation commits.

        Validate every captured positive/negative/range dependency in a fresh
        snapshot. Only the reservation's own known writes may differ. Keeping
        this view object lets already captured resolvers follow the revalidated
        snapshot; their old exact immutable values remain valid. A miss leaves
        the original view untouched and requires normal replanning.
        """
        self._check()
        allowed={'reservation','waves','due','work'}
        if any(f not in allowed for f,_ in packet.writes):
            raise StoreError('Only operational reservation writes can advance a prepared view')
        with self.store.read() as fresh:
            expected=dict(self.points)
            for (family,key),value in packet.writes.items():
                if fresh.get(family,key) != value: return False
                expected[family,key]=fresh.points[family,key]
            by_family={}
            for (family,key),revision in expected.items(): by_family.setdefault(family,{})[key]=revision
            for family,rows in by_family.items():
                if fresh.revisions(family,rows) != rows: return False
            for (family,prefix),rows in self.ranges.items():
                expected_range=dict(rows)
                for (f,key),_ in packet.writes.items():
                    if f==family and key.startswith(prefix): expected_range[key]=fresh.points[f,key]
                fresh.scan(family,prefix)
                if fresh.ranges[family,prefix] != tuple(sorted(expected_range.items())): return False
            self._adopt(fresh)
            self.points,self.ranges=fresh.points,fresh.ranges
            self._projections={}
            return True

    def page(self, family, prefix='', *, after=None, start=None, limit=50, reverse=False):
        """Bounded ordered reads. Points are protected; this is not range absence.

        Append-only history is pinned by the caller's head/position. Scheduling
        uses a hint followed by conditional point reads, never this as proof of
        semantic completeness.
        """
        self._check()
        rows = self._page(family, prefix, after, start, limit, reverse)
        result = []
        for key, version, value in rows:
            self.points[family,key] = version
            result.append((key,self._detach(value)))
        self.store.metrics.add('recordsRead', len(result))
        self.store.metrics.add('bytesRead', sum(self._size(family,k,rev,v) for k,rev,v in rows))
        return result

    def due(self, now, *, after=None, limit=64):
        self._check()
        return self._due(now, after, limit)

    def fence_lease(self, instance, owner, fence):
        self.leases[instance] = {'owner': owner, 'fence': fence}
        self.points.pop(('leases',instance),None)

    def pin_prefix(self, timeline, source):
        """Bind a verified immutable prefix instead of its extendable head row."""
        if source.get('count') is None:return False
        proof=self.get('source_proofs',source['proof'])
        if proof is None or any(proof.get(k)!=source.get(k) for k in ('before','count','head')):
            return False
        if proof.get('timeline')!=timeline or self.get('source_issues',timeline) is not None:return False
        if source['count']:
            anchor=self.get('source_entries',timeline+'/'+str(source['count']-1).zfill(16))
            if anchor is None or anchor['blue_id']!=source['head']:return False
        self.prefixes[timeline]={k:source[k] for k in ('before','count','head')}
        return True

    def history_before(self, instance, order, *, inclusive=False):
        self._check()
        selected=self._history_before(instance,tuple(order),inclusive)
        if selected is None:return None
        key,revision,row=selected
        self.points['history',key]=revision
        self.store.metrics.add('recordsRead', 1)
        self.store.metrics.add('bytesRead', self._size('history',key,revision,row))
        return self._detach(row)

    def packet(self, application, *, publication=None, writes=None, result=None):
        self._check()
        return Packet(publication or str(uuid4()), application, deepcopy(self.points),
                      deepcopy(self.ranges), deepcopy(writes or {}), deepcopy(result), deepcopy(self.leases),
                      deepcopy(self.acknowledgements),deepcopy(self.prefixes))

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class MemoryStore:
    """MVCC memory adapter; snapshots retain a sequence, not an account copy."""
    def __init__(self, *, failpoint=None, compact=True, share_bytes=True, project_records=True):
        self.project_records = project_records
        self._lock = RLock()
        self._sequence = 0
        self._records = {}
        self.byte_pool=BytePool(capacity=8192 if share_bytes else 0)
        self._readers = WeakValueDictionary()
        self._compact_enabled = compact
        self._changed_versions = set()
        self._keys = {}
        self._live_keys = {}
        self._due_index, self._due_at = [], {}
        self._history_index, self._history_order = {}, {}
        self._publications, self._applications = {}, {}
        self.failpoint = failpoint
        self.metrics = Metrics(recordsRead=0, bytesRead=0, recordsWritten=0, bytesWritten=0, queries=0, conflicts=0, readTransactions=0, writeTransactions=0)

    def read(self):
        self.metrics.add('readTransactions')
        store = self

        class View(ReadView):
            def __init__(self):
                super().__init__(store)
                with store._lock:
                    self.sequence = store._sequence
                    store._readers[id(self)] = self

            def _visible(self, family, key):
                versions=store._records.get((family,key),())
                if not versions: return 0,None
                if versions[-1][0] <= self.sequence: return versions[-1]
                low,high=0,len(versions)
                while low<high:
                    middle=(low+high)//2
                    if versions[middle][0] <= self.sequence: low=middle+1
                    else: high=middle
                return (0,None) if low==0 else versions[low-1]

            def _adopt(self, fresh):
                with store._lock: self.sequence=fresh.sequence

            def _detach(self, value): return value  # _point/_range already decode a fresh owned tree.

            def _size(self, family, key, version, value):
                if value is None: return 0
                with store._lock:
                    revision,record=self._visible(family,key)
                    assert revision==version
                    return record.size

            def revisions(self, family, keys):
                self._check()
                with store._lock: result={key:self._visible(family,key)[0] for key in dict.fromkeys(keys)}
                self.points.update({(family,key):revision for key,revision in result.items()})
                store.metrics.add('revisionReads',len(result))
                return result

            def close(self):
                with store._lock: store._readers.pop(id(self),None)
                super().close()

            def _point(self, family, key):
                with store._lock:
                    revision,record=self._visible(family,key)
                    return revision,record.open() if record is not None else None

            def _project(self, family, key, names):
                with store._lock:
                    revision, record = self._visible(family, key)
                    return revision, record.open_fields(names) if record is not None else None

            def _range(self, family, prefix):
                with store._lock:
                    result = []
                    keys=store._keys.get(family,[]);upper=prefix_end(prefix)
                    start=bisect_left(keys,prefix);end=bisect_left(keys,upper) if upper is not None else len(keys)
                    for i in range(start,end):
                        key=keys[i];revision,value=self._point(family,key)
                        if revision:result.append((key,revision,value))
                    return result

            def _page(self, family, prefix, after, start, limit, reverse):
                with store._lock:
                    # The live index describes only the current snapshot. Older
                    # readers still need all keys, including later deletions.
                    index = store._live_keys if self.sequence == store._sequence else store._keys
                    keys = index.get(family, [])
                    low = bisect_left(keys, max(prefix, start or prefix))
                    upper = prefix_end(prefix)
                    high = bisect_left(keys, upper) if upper is not None else len(keys)
                    if after is not None:
                        if reverse: high = min(high,bisect_left(keys,after))
                        else: low = max(low,bisect_right(keys,after))
                    indices = range(high-1,low-1,-1) if reverse else range(low,high)
                    result=[]
                    for i in indices:
                        rev,value=self._point(family,keys[i])
                        if value is not None:result.append((keys[i],rev,value))
                        if len(result)>=limit:break
                    return result

            def _due(self, now, after, limit):
                # Current index is a hint. A subsequent MVCC point/claim is the
                # authority; reading it creates no global false-conflict fence.
                with store._lock:
                    low=bisect_right(store._due_index,tuple(after)) if after else 0
                    high=bisect_right(store._due_index,(now,chr(0x10ffff)))
                    return list(store._due_index[low:min(high,low+limit)])

            def _history_before(self, instance, order, inclusive):
                with store._lock:
                    rows=store._history_index.get(instance,[])
                    bound=(*order,chr(0x10ffff) if inclusive else '')
                    end=bisect_right(rows,bound) if inclusive else bisect_left(rows,bound)
                    for index in range(end-1,-1,-1):
                        item=rows[index]
                        rev,value=self._point('history',item[-1])
                        if value is not None:return item[-1],rev,value
                    return None

        return View()

    def resolve(self, publication):
        with self._lock:
            row = self._publications.get(publication)
            return deepcopy(row[1]) if row else None

    def commit(self, packet):
        self.metrics.add('writeTransactions')
        wire = packet.wire()
        identity = fingerprint(wire)
        with self._lock:
            existing = self._publications.get(packet.publication)
            if existing:
                if existing[0] != identity:
                    raise StoreError('Publication identity reused for different content')
                return deepcopy(existing[1])
            prior = self._applications.get(packet.application)
            if prior:
                return deepcopy(self._publications[prior][1])
            current = self.read()
            writes,compatible=publication_writes(packet,current)
            conflict = writes is None or any(current._visible(f, k)[0] != v
                for (f, k), v in packet.points.items() if (f,k) not in compatible)
            conflict |= any(tuple((k, rev) for k, rev, _ in current._range(f, prefix)) != expected
                            for (f, prefix), expected in packet.ranges.items())
            for instance, guard in packet.leases.items():
                lease=current.get('leases',instance)
                conflict |= not lease or lease['owner'] != guard['owner'] or lease['fence'] != guard['fence'] or lease['until'] <= time.time()
            current.close()
            if conflict:
                self.metrics.add('conflicts', 1)
                return Commit('CONFLICT')
            if self.failpoint:
                self.failpoint('before_commit', packet)
            self._sequence += 1
            for key, value in writes.items():
                family, record_key = key
                if key not in self._records:insort(self._keys.setdefault(family,[]),record_key)
                was_live = key in self._records and self._records[key][-1][1] is not None
                if was_live != (value is not None):
                    live = self._live_keys.setdefault(family, [])
                    if value is None:live.pop(bisect_left(live, record_key))
                    else:insort(live, record_key)
                if family == 'due':
                    old=self._due_at.pop(record_key,None)
                    if old is not None:self._due_index.pop(bisect_left(self._due_index,(old,record_key)))
                    if value is not None:
                        self._due_at[record_key]=value['at'];insort(self._due_index,(value['at'],record_key))
                if family == 'history':
                    instance=record_key.split('/',1)[0]
                    index=self._history_index.setdefault(instance,[])
                    old=self._history_order.pop(record_key,None)
                    if old is not None:index.pop(bisect_left(index,old))
                    if value is not None:
                        order=(*(value.get('effectiveOrder') or (-1,'','')),record_key)
                        self._history_order[record_key]=order;insort(index,order)
                record=StoredJSON.capture(value,self.byte_pool,split_records=self.project_records) if value is not None else None
                self._records.setdefault(key, []).append((self._sequence, record))
                self._changed_versions.add(key)
                self.metrics.add('recordsWritten', 1)
                self.metrics.add('bytesWritten', record.size if record is not None else 0)
            result = Commit('COMMITTED', deepcopy(packet.result), packet.publication)
            self._publications[packet.publication] = identity, result
            self._applications[packet.application] = packet.publication
            if self._compact_enabled and self._sequence % 64 == 0: self.compact()
        if self.failpoint:
            try:
                self.failpoint('after_commit', packet)
            except Exception as exc:
                raise PublicationUnknown(packet.publication) from exc
        return result

    def compact(self):
        """Collect obsolete physical versions, retaining all semantic records.

        Latest tombstones and their revisions never disappear. Closed-view
        packets contain detached writes and revision/range predicates: their
        validation compares latest revisions, and requires no obsolete bodies.
        Open views pin their oldest visible predecessor and all newer versions.
        Idempotence/publication and immutable business-history rows are untouched.
        """
        with self._lock:
            oldest=min((v.sequence for v in self._readers.values() if not v.closed),default=self._sequence)
            retained=set();removed=0
            for key in self._changed_versions:
                versions=self._records[key]
                keep=bisect_right(versions,oldest,key=lambda row:row[0])-1
                if keep>0:
                    removed+=keep;del versions[:keep]
                if len(versions)>1: retained.add(key)
            self._changed_versions=retained
            self.metrics.add('versionsCollected',removed)
            return removed

    def statistics(self):
        with self._lock:
            return {'recordKeys':len(self._records),
                    'liveRecords':sum(rows[-1][1] is not None for rows in self._records.values()),
                    'retainedVersions':sum(map(len,self._records.values())),
                    'obsoleteVersions':sum(len(rows)-1 for rows in self._records.values()),
                    'retainedPayloadBytes':sum(record.size for rows in self._records.values() for _,record in rows if record is not None),
                    'pinnedReaders':len(self._readers),
                    'deduplicationPoolBytes':self.byte_pool.bytes,'deduplicationHits':self.byte_pool.hits}

    def close(self):
        pass


class SQLiteStore:
    """Durable reference adapter supporting independent worker processes."""
    def __init__(self, path, *, failpoint=None, timeout=10, project_records=True):
        self.project_records = project_records
        self.path, self.failpoint, self.timeout = str(path), failpoint, timeout
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.metrics = Metrics(recordsRead=0, bytesRead=0, recordsWritten=0, bytesWritten=0, queries=0, conflicts=0, readTransactions=0, writeTransactions=0)
        with closing(self._connect()) as connection:
            connection.execute('PRAGMA journal_mode=WAL')
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value INTEGER NOT NULL);
                INSERT OR IGNORE INTO metadata VALUES ('sequence', 0);
                CREATE TABLE IF NOT EXISTS records (
                    family TEXT NOT NULL, key TEXT NOT NULL, revision INTEGER NOT NULL,
                    body TEXT, PRIMARY KEY(family,key));
                CREATE TABLE IF NOT EXISTS publications (
                    id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                    application TEXT NOT NULL UNIQUE, result TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS records_live_by_family_key ON records
                    (family,key) WHERE body IS NOT NULL;
                CREATE INDEX IF NOT EXISTS due_by_time ON records
                    (CAST(json_extract(body,'$.at') AS REAL),key)
                    WHERE family='due' AND body IS NOT NULL;
                CREATE INDEX IF NOT EXISTS history_by_order ON records
                    (substr(key,1,instr(key,'/')-1),
                     coalesce(json_extract(body,'$.effectiveOrder[0]'),-1),
                     coalesce(json_extract(body,'$.effectiveOrder[1]'),''),
                     coalesce(json_extract(body,'$.effectiveOrder[2]'),''),key)
                    WHERE family='history' AND body IS NOT NULL;
            ''')

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=self.timeout)
        def observed(_statement):
            self.metrics.add('queries', 1)
        connection.set_trace_callback(observed)
        connection.execute('PRAGMA synchronous=FULL')
        return connection

    def read(self):
        self.metrics.add('readTransactions')
        store = self

        class View(ReadView):
            def __init__(self):
                super().__init__(store)
                self.connection = store._connect()
                self.connection.execute('BEGIN')
                # Establish the coherent WAL snapshot before the first get.
                self.connection.execute("SELECT value FROM metadata WHERE key='sequence'").fetchone()

            def _adopt(self, fresh):
                self.connection.rollback();self.connection.close()
                self.connection=fresh.connection
                fresh.closed=True  # Transfer this WAL read transaction, not its ownership twice.

            def _point(self, family, key):
                row = self.connection.execute('SELECT revision,body FROM records WHERE family=? AND key=?', (family, key)).fetchone()
                return (0, None) if row is None else (row[0], json.loads(row[1]) if row[1] is not None else None)

            def _project(self, family, key, names):
                if sqlite3.sqlite_version_info < (3, 38):
                    revision, value = self._point(family, key)
                    return revision, None if value is None else {k: value[k] for k in names if k in value}
                columns = ['revision', 'json_type(body)']
                parameters = []
                for name in names:
                    # Keep the exact JSON token: json_extract converts large
                    # JSON Integers to SQLite floating point before Python reads.
                    columns.append('body -> ?')
                    parameters.append('$.' + name)
                row = self.connection.execute('SELECT ' + ','.join(columns) +
                    ' FROM records WHERE family=? AND key=?', [*parameters, family, key]).fetchone()
                if row is None: return 0, None
                if row[1] is None: return row[0], None
                if row[1] != 'object': raise StoreError('Metadata projection requires an object record')
                result = {}
                for name, raw in zip(names, row[2:]):
                    if raw is not None:
                        result[name] = json.loads(raw)
                return row[0], result

            def _range(self, family, prefix):
                # Both index bounds are literal; unrelated later accounts are not scanned.
                rows = range_rows(self.connection, 'key,revision,body', family, prefix)
                return [(k, rev, json.loads(body) if body is not None else None) for k, rev, body in rows]

            def _page(self, family, prefix, after, start, limit, reverse):
                sql='SELECT key,revision,body FROM records WHERE family=? AND key>=? AND body IS NOT NULL'
                params=[family,max(prefix,start or prefix)];upper=prefix_end(prefix)
                if upper is not None:sql+=' AND key<?';params.append(upper)
                if after is not None:sql+=' AND key'+('<' if reverse else '>')+'?';params.append(after)
                sql+=' ORDER BY key '+('DESC' if reverse else 'ASC')+' LIMIT ?';params.append(limit)
                return [(k,rev,json.loads(body)) for k,rev,body in self.connection.execute(sql,params)]

            def _due(self, now, after, limit):
                at="CAST(json_extract(body,'$.at') AS REAL)"
                sql="SELECT "+at+",key FROM records INDEXED BY due_by_time WHERE family='due' AND body IS NOT NULL AND "+at+'<=?'
                params=[now]
                if after is not None:sql+=' AND ('+at+',key)>(?,?)';params.extend(after)
                return self.connection.execute(sql+' ORDER BY '+at+',key LIMIT ?',[*params,limit]).fetchall()

            def _history_before(self, instance, order, inclusive):
                expressions=["coalesce(json_extract(body,'$.effectiveOrder[0]'),-1)",
                    "coalesce(json_extract(body,'$.effectiveOrder[1]'),'')",
                    "coalesce(json_extract(body,'$.effectiveOrder[2]'),'')"]
                sql="SELECT key,revision,body FROM records INDEXED BY history_by_order WHERE family='history' AND body IS NOT NULL AND substr(key,1,instr(key,'/')-1)=? AND ("+','.join(expressions)+')'+('<=' if inclusive else '<')+'(?,?,?)'
                row=self.connection.execute(sql+' ORDER BY '+','.join(x+' DESC' for x in [*expressions,'key'])+' LIMIT 1',[instance,*order]).fetchone()
                return (row[0],row[1],json.loads(row[2])) if row else None

            def get_many(self, family, keys):
                self._check()
                keys = list(dict.fromkeys(keys))
                result = dict.fromkeys(keys)
                for offset in range(0, len(keys), 500):
                    batch = keys[offset:offset + 500]
                    rows = self.connection.execute('SELECT key,revision,body FROM records WHERE family=? AND key IN (' + ','.join('?' for _ in batch) + ')', [family, *batch])
                    found = set()
                    for key, revision, body in rows:
                        found.add(key)
                        self.points[family, key] = revision
                        result[key] = json.loads(body) if body is not None else None
                        store.metrics.add('bytesRead', len(body.encode()) if body else 0)
                    for key in set(batch) - found:
                        self.points[family, key] = 0
                store.metrics.add('recordsRead', len(keys))
                return result

            def revisions(self, family, keys):
                self._check()
                keys = list(dict.fromkeys(keys))
                result = dict.fromkeys(keys, 0)
                for offset in range(0, len(keys), 500):
                    batch = keys[offset:offset + 500]
                    result.update(self.connection.execute(
                        'SELECT key,revision FROM records WHERE family=? AND key IN (' +
                        ','.join('?' for _ in batch) + ')', [family, *batch]))
                self.points.update({(family, key): revision for key, revision in result.items()})
                store.metrics.add('revisionReads', len(keys))
                return result

            def close(self):
                if not self.closed:
                    self.connection.rollback()
                    self.connection.close()
                super().close()

        return View()

    def resolve(self, publication):
        with closing(self._connect()) as connection:
            row = connection.execute('SELECT result FROM publications WHERE id=?', (publication,)).fetchone()
            return Commit('COMMITTED', json.loads(row[0]), publication) if row else None

    def commit(self, packet):
        self.metrics.add('writeTransactions')
        identity = fingerprint(packet.wire())
        connection = self._connect()
        try:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('SELECT fingerprint,result FROM publications WHERE id=?', (packet.publication,)).fetchone()
            if row:
                if row[0] != identity:
                    raise StoreError('Publication identity reused for different content')
                return Commit('COMMITTED', json.loads(row[1]), packet.publication)
            row = connection.execute('SELECT id,result FROM publications WHERE application=?', (packet.application,)).fetchone()
            if row:
                return Commit('COMMITTED', json.loads(row[1]), row[0])
            class Current:
                def get(self, family, key):
                    row=connection.execute('SELECT body FROM records WHERE family=? AND key=?',(family,key)).fetchone()
                    return json.loads(row[0]) if row and row[0] is not None else None
            writes,compatible=publication_writes(packet,Current())
            if writes is None:
                self.metrics.add('conflicts',1)
                return Commit('CONFLICT')
            families={family for family,_ in packet.points}
            for family in families:
                expected={key:value for (f,key),value in packet.points.items() if f==family and (f,key) not in compatible}
                keys=list(expected)
                for offset in range(0,len(keys),500):
                    batch=keys[offset:offset+500]
                    actual=dict(connection.execute('SELECT key,revision FROM records WHERE family=? AND key IN ('+
                        ','.join('?' for _ in batch)+')',[family,*batch]))
                    if any(actual.get(key,0)!=expected[key] for key in batch):
                        self.metrics.add('conflicts', 1)
                        return Commit('CONFLICT')
            for (family, prefix), expected in packet.ranges.items():
                rows = range_rows(connection, 'key,revision', family, prefix).fetchall()
                if tuple(rows) != expected:
                    self.metrics.add('conflicts', 1)
                    return Commit('CONFLICT')
            for instance, guard in packet.leases.items():
                row=connection.execute("SELECT body FROM records WHERE family='leases' AND key=?",(instance,)).fetchone()
                lease=json.loads(row[0]) if row and row[0] else None
                if not lease or lease['owner'] != guard['owner'] or lease['fence'] != guard['fence'] or lease['until'] <= time.time():
                    self.metrics.add('conflicts', 1)
                    return Commit('CONFLICT')
            if self.failpoint:
                self.failpoint('before_commit', packet)
            sequence = connection.execute("UPDATE metadata SET value=value+1 WHERE key='sequence' RETURNING value").fetchone()[0]
            for (family, key), value in writes.items():
                body = encode(value) if value is not None else None
                connection.execute('INSERT INTO records VALUES (?,?,?,?) ON CONFLICT(family,key) DO UPDATE SET revision=excluded.revision,body=excluded.body', (family, key, sequence, body))
                self.metrics.add('recordsWritten', 1)
                self.metrics.add('bytesWritten', len(body.encode()) if body else 0)
            connection.execute('INSERT INTO publications VALUES (?,?,?,?)', (packet.publication, identity, packet.application, encode(packet.result)))
            connection.commit()
        finally:
            connection.rollback()
            connection.close()
        if self.failpoint:
            try:
                self.failpoint('after_commit', packet)
            except Exception as exc:
                raise PublicationUnknown(packet.publication) from exc
        return Commit('COMMITTED', deepcopy(packet.result), packet.publication)

    def close(self):
        pass
