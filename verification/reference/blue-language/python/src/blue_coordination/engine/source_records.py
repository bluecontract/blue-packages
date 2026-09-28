"""Immutable accepted entries with a small verified-prefix head."""
from collections.abc import Sequence
from blue_coordination_spec.model import Entry


def order_key(timestamp, identity=''):
    return str(timestamp).zfill(20) + '/' + identity


def entries(view, timeline, source=None, *, after=None, before=None, limit=256):
    """Read only the requested suffix. Bounds use the full cross-source K."""
    if source is not None and 'entries' in source:  # retained predecessor store
        rows = [r for r in source['entries'] if
            (after is None or (r['timestamp'], timeline, r['blue_id']) > tuple(after)) and
            (before is None or (r['timestamp'], timeline, r['blue_id']) < tuple(before))]
        return rows[:limit]
    prefix=timeline+'/'
    start=prefix
    cursor=None
    if after is not None:
        timestamp, other, identity=after
        if timeline < other:start=prefix+order_key(timestamp+1)
        elif timeline > other:start=prefix+order_key(timestamp)
        else:cursor=prefix+order_key(timestamp,identity)
    rows=view.page('source_order',prefix,start=start,after=cursor,limit=limit)
    return [r for _,r in rows if before is None or (r['timestamp'],timeline,r['blue_id']) < tuple(before)]


class StoredEntries(Sequence):
    """A verified immutable prefix; its private read view must remain open."""
    def __init__(self,view,timeline,count):
        self.view,self.timeline,self.count=view,timeline,count
    def __len__(self):return self.count
    def __getitem__(self,index):
        if isinstance(index,slice):return tuple(self[i] for i in range(*index.indices(self.count)))
        if index<0:index+=self.count
        if not 0<=index<self.count:raise IndexError(index)
        row=self.view.get('source_entries',self.timeline+'/'+str(index).zfill(16))
        if row is None:raise KeyError('Missing verified source predecessor')
        return Entry(**row)
    def index(self,identity):
        row=self.view.get('source_entry_ids',self.timeline+'/'+identity)
        if row is None or row['number']>=self.count:raise ValueError(identity)
        return row['number']
    def __contains__(self,entry):
        row=self.view.get('source_entry_ids',self.timeline+'/'+entry.blue_id)
        return row is not None and row['number']<self.count and self[row['number']]==entry


class AcquiredEntries(Sequence):
    """Private verified page facts; availability is not yet source completeness."""
    def __init__(self,store,key,count):self.store,self.key,self.count=store,key,count
    def __len__(self):return self.count
    def __getitem__(self,index):
        if isinstance(index,slice):return tuple(self[i] for i in range(*index.indices(self.count)))
        if index<0:index+=self.count
        if not 0<=index<self.count:raise IndexError(index)
        with self.store.read() as view:
            row=view.get('source_acquisition_entries',self.key+'/'+str(index).zfill(20))
        if row is None:raise KeyError('Missing verified acquisition entry')
        return Entry(**row)
    def __eq__(self,other):return len(self)==len(other) and all(a==b for a,b in zip(self,other))
