"""Verified Coordination facts; deliberately not a Contracts argument."""
from types import MappingProxyType
from .model import require, Envelope, digest

class CoordinationEvidence:
    def __init__(self,prefixes,*,eligible=None,bindings=None,lookup=()):
        self.prefixes=tuple(prefixes)
        entries={e.blue_id:e for p in prefixes for e in p.entries}
        if eligible is not None:
            require(set(eligible)<=entries.keys(),'UNKNOWN_SELECTED_EVENT')
            entries={k:v for k,v in entries.items() if k in eligible}
        for entry in lookup:
            require(entry.blue_id not in entries or entries[entry.blue_id]==entry,'CONFLICTING_ENTRY')
            entries[entry.blue_id]=entry
        self.entries=MappingProxyType(entries)
        self.events=MappingProxyType({k:Envelope(k,e.timeline,e.timestamp,e.message,e.actor) for k,e in entries.items()})
        self.frontiers=MappingProxyType({p.timeline:p.before for p in prefixes})
        self.bindings=MappingProxyType(dict(bindings or {}))
        self.proofs=tuple(sorted(p.proof for p in prefixes))
        self.identity=digest('coordination.evidence/event-1',{'prefixes':[p.wire() for p in prefixes],
            'lookup':[e.wire() for e in lookup],'bindings':dict(self.bindings)})
    def resolve(self,identity):
        require(identity in self.events,'NEEDS_SOURCE_EVIDENCE',event=identity)
        return self.events[identity]
