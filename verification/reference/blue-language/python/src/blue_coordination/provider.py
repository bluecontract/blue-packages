"""Provider contracts and a single-writer, explicit-time in-memory provider.

The example provider authenticates reads with a configured HMAC key and verifies
actor registration. It does not claim network identity, public verifiability,
legal attestation or crash durability. Its append/close/read lock enforces the
binding no-future-backdating promise, rather than inferring it from a scan.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any
from threading import RLock
import hashlib, hmac, json
from .language import BlueAccess, ExactValue, MISSING
from .model import Entry
from .registry import RuntimeRegistry
from .errors import Code, Acquisition, require, CoordinationError
from .identity import MAX_SAFE_INTEGER

@dataclass(frozen=True)
class Acquired:
    status: Acquisition
    timeline_blue_id: str
    complete_before: int | None = None
    entries: tuple[Entry, ...] = ()
    evidence: ExactValue | None = None
    detail: str = ''

@dataclass(frozen=True)
class VerifiedWindow:
    timeline_blue_id: str
    complete_before: int
    entries: tuple[Entry, ...]
    evidence: ExactValue

class TimelineProvider(Protocol):
    def acquire(self, timeline_blue_id: str) -> Acquired: ...
    def verify(self, acquired: Acquired) -> VerifiedWindow: ...

class MemoryTimelineProvider:
    def __init__(self, blue: BlueAccess, registry: RuntimeRegistry, *,
                 entry_type: str, evidence_type: str, signing_key: bytes):
        require(len(signing_key) >= 16, Code.INVALID_EVIDENCE, 'provider HMAC key too short')
        self.blue, self.registry = blue, registry
        self.entry_type, self.evidence_type = entry_type, evidence_type
        self._key = bytes(signing_key)
        self._timelines: dict[str, ExactValue] = {}
        self._actors: dict[str, frozenset[str]] = {}
        self._entries: dict[str, tuple[Entry, ...]] = {}
        self._frontiers: dict[str, int] = {}
        self._unavailable: set[str] = set()
        self._lock = RLock()

    def register(self, timeline: ExactValue, actors: tuple[ExactValue, ...]) -> None:
        with self._lock:
            self.registry.expect(timeline, 'timeline')
            for actor in actors:
                self.registry.expect(actor, 'actor')
            tid = timeline.blue_id
            allowed = frozenset(a.blue_id for a in actors)
            if tid in self._timelines:
                require(self._actors[tid] == allowed, Code.INVALID_EVIDENCE, 'cannot silently reassign Timeline owner')
                return
            self._timelines[tid] = timeline
            self._actors[tid] = allowed
            self._entries[tid] = ()
            self._frontiers[tid] = 0

    def set_available(self, timeline_blue_id: str, available: bool) -> None:
        with self._lock:
            if available:
                self._unavailable.discard(timeline_blue_id)
            else:
                self._unavailable.add(timeline_blue_id)

    def append(self, exact: ExactValue) -> Entry:
        entry = Entry.read(exact, self.blue, self.registry)
        tid = entry.timeline.blue_id
        with self._lock:
            require(tid in self._timelines, Code.NEEDS_RESOURCES, 'Timeline not registered')
            require(tid not in self._unavailable, Code.NEEDS_RESOURCES, 'provider unavailable')
            history = self._entries[tid]
            for previous in history:
                if previous.blue_id == entry.blue_id:
                    return previous  # An exact retry is not a new append behind a frontier.
            require(entry.actor.blue_id in self._actors[tid], Code.INVALID_EVIDENCE, 'actor not attributed by provider')
            require(entry.timestamp >= self._frontiers[tid], Code.INVALID_EVIDENCE, 'append behind closed frontier')
            predecessor = history[-1] if history else None
            require(entry.previous_blue_id == (predecessor.blue_id if predecessor else None),
                    Code.INVALID_EVIDENCE, 'entry does not link to immediate predecessor')
            require(predecessor is None or entry.timestamp > predecessor.timestamp,
                    Code.INVALID_EVIDENCE, 'Timeline timestamps must strictly increase')
            self._entries[tid] = history + (entry,)
            return entry

    def emit(self, timeline: ExactValue, actor: ExactValue, message: ExactValue, *,
             observed_timestamp: int, source: Any = MISSING, authority: Any = MISSING) -> Entry:
        with self._lock:
            tid = timeline.blue_id
            require(tid in self._entries, Code.NEEDS_RESOURCES, 'unregistered Timeline')
            require(type(observed_timestamp) is int and observed_timestamp >= 0,
                    Code.INVALID_EVIDENCE, 'explicit observed microseconds required')
            history = self._entries[tid]
            timestamp = max(observed_timestamp, self._frontiers[tid], history[-1].timestamp + 1 if history else 0)
            require(timestamp <= MAX_SAFE_INTEGER, Code.INVALID_EVIDENCE, 'timestamp overflow')
            node = {'type': {'blueId': self.entry_type}, 'timeline': {'blueId': tid},
                    'actor': {'blueId': actor.blue_id}, 'timestamp': timestamp,
                    'message': {'blueId': message.blue_id}}
            if history:
                node['prevEntry'] = {'blueId': history[-1].blue_id}
            if source is not MISSING:
                node['source'] = {'blueId': source.blue_id}
            if authority is not MISSING:
                node['onBehalfOf'] = {'blueId': authority.blue_id}
            return self.append(self.blue.admit(node))

    def close_before(self, timeline_blue_id: str, before: int) -> None:
        with self._lock:
            require(timeline_blue_id in self._entries, Code.NEEDS_RESOURCES, 'unregistered Timeline')
            require(type(before) is int and 0 <= before <= MAX_SAFE_INTEGER + 1,
                    Code.INVALID_EVIDENCE, 'invalid exclusive frontier')
            require(before >= self._frontiers[timeline_blue_id], Code.INCOMPATIBLE_FRONTIER, 'frontier regression')
            self._frontiers[timeline_blue_id] = before

    def _sign(self, payload: dict) -> str:
        data = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
        return hmac.new(self._key, data, hashlib.sha256).hexdigest()

    def _evidence(self, tid: str, frontier: int, entries: tuple[Entry, ...], *, beginning: bool = False) -> ExactValue:
        payload = {'domain': 'blue-python-reference-provider/1', 'timelineBlueId': tid,
                   'completeBefore': str(frontier), 'entryBlueIds': [e.blue_id for e in entries],
                   'beginning': 'YES' if beginning else 'NO'}
        return self.blue.admit({'type': {'blueId': self.evidence_type}, 'claim': payload,
                                'signature': self._sign(payload)})

    def acquire(self, timeline_blue_id: str) -> Acquired:
        with self._lock:
            if timeline_blue_id not in self._entries:
                return Acquired(Acquisition.NOT_FOUND, timeline_blue_id)
            if timeline_blue_id in self._unavailable:
                return Acquired(Acquisition.DEFERRED_UNAVAILABLE, timeline_blue_id)
            frontier = self._frontiers[timeline_blue_id]
            entries = tuple(e for e in self._entries[timeline_blue_id] if e.timestamp < frontier)
            proof = self._evidence(timeline_blue_id, frontier, entries)
            return Acquired(Acquisition.COMPLETE if entries else Acquisition.COMPLETE_EMPTY,
                            timeline_blue_id, frontier, entries, proof)

    def verify(self, acquired: Acquired) -> VerifiedWindow:
        require(acquired.status in (Acquisition.COMPLETE, Acquisition.COMPLETE_EMPTY),
                Code.INVALID_EVIDENCE, 'a negative acquisition is not a complete window')
        require(acquired.evidence is not None, Code.INVALID_EVIDENCE, 'missing completeness evidence')
        self.registry.expect(acquired.evidence, 'completeness_evidence')
        view = self.blue.view(acquired.evidence)
        claim = view.need('claim').plain(); signature = view.need('signature').text()
        expected = {'domain': 'blue-python-reference-provider/1',
                    'timelineBlueId': acquired.timeline_blue_id,
                    'completeBefore': str(acquired.complete_before),
                    'entryBlueIds': [e.blue_id for e in acquired.entries], 'beginning': 'NO'}
        require(claim == expected and hmac.compare_digest(signature, self._sign(expected)),
                Code.INVALID_EVIDENCE, 'completeness signature or operand mismatch')
        require(type(acquired.complete_before) is int and 0 <= acquired.complete_before <= MAX_SAFE_INTEGER + 1,
                Code.INVALID_EVIDENCE, 'invalid signed frontier')
        require((acquired.status == Acquisition.COMPLETE_EMPTY) == (not acquired.entries),
                Code.INVALID_EVIDENCE, 'complete-empty outcome contradicts interval')
        previous = None
        seen = set()
        verified = []
        for claimed in acquired.entries:
            entry = Entry.read(claimed.exact, self.blue, self.registry)
            require(entry == claimed, Code.INVALID_EVIDENCE, 'parsed entry facts disagree with exact entry')
            require(entry.timeline.blue_id == acquired.timeline_blue_id, Code.INVALID_EVIDENCE, 'wrong Timeline')
            require(entry.blue_id not in seen, Code.INVALID_EVIDENCE, 'duplicate entry in complete prefix')
            require(entry.timestamp < acquired.complete_before, Code.INVALID_EVIDENCE, 'entry at/after exclusive bound')
            require(entry.previous_blue_id == (previous.blue_id if previous else None),
                    Code.INVALID_EVIDENCE, 'gapped complete prefix')
            require(previous is None or entry.timestamp > previous.timestamp,
                    Code.INVALID_EVIDENCE, 'non-increasing complete prefix')
            with self._lock:
                require(entry.actor.blue_id in self._actors.get(acquired.timeline_blue_id, ()),
                        Code.INVALID_EVIDENCE, 'actor not verified by this provider')
            seen.add(entry.blue_id); verified.append(entry); previous = entry
        return VerifiedWindow(acquired.timeline_blue_id, acquired.complete_before, tuple(verified), acquired.evidence)

    def establish_beginning(self, timelines: tuple[str, ...]) -> tuple[ExactValue, ...]:
        """Caller must retain the enclosing lock through successful atomic admission."""
        require(self._lock._is_owned(), Code.INVALID_EVIDENCE, 'beginning admission requires held provider lock')
        proofs = []
        for tid in sorted(set(timelines)):
            require(tid in self._entries and tid not in self._unavailable,
                    Code.NEEDS_RESOURCES, 'beginning requires registered available authoritative provider')
            require(not self._entries[tid], Code.INVALID_EVIDENCE, 'history is not at beginning')
            proofs.append(self._evidence(tid, self._frontiers[tid], (), beginning=True))
        return tuple(proofs)

    def admission_lock(self):
        return self._lock

    def history(self, timeline_blue_id: str) -> tuple[Entry, ...]:
        with self._lock:
            return self._entries[timeline_blue_id]


def obtain_complete_windows(timelines: tuple[str, ...], providers: dict[str, TimelineProvider]) -> tuple[int | None, tuple[VerifiedWindow, ...]]:
    windows = []
    for timeline in sorted(set(timelines)):
        provider = providers.get(timeline)
        require(provider is not None, Code.NEEDS_RESOURCES, 'no provider for required Timeline')
        acquired = provider.acquire(timeline)
        require(acquired.timeline_blue_id == timeline, Code.INVALID_EVIDENCE, 'provider returned a different Timeline')
        if acquired.status in (Acquisition.DEFERRED_UNAVAILABLE, Acquisition.NOT_FOUND):
            raise CoordinationError(Code.NEEDS_RESOURCES, acquired.status)
        if acquired.status == Acquisition.INVALID_EVIDENCE:
            raise CoordinationError(Code.INVALID_EVIDENCE, acquired.detail)
        if acquired.status == Acquisition.INCOMPATIBLE_FRONTIER:
            raise CoordinationError(Code.INCOMPATIBLE_FRONTIER, acquired.detail)
        windows.append(provider.verify(acquired))
    safe = min((w.complete_before for w in windows), default=None)
    return safe, tuple(windows)
