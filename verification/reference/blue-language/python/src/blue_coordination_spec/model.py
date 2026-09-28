"""Closed Coordination records and commitments; no document execution here."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from copy import deepcopy
from typing import Any
from blue_contracts.reference.model import SAFE, canonical, digest

@dataclass(frozen=True, order=True)
class Order:
    timestamp: int
    source: str
    event: str

    def wire(self): return asdict(self)

@dataclass(frozen=True)
class Envelope:
    """Coordination metadata only; never an argument to Contracts."""
    event: str
    source: str
    timestamp: int
    payload: str
    actor: str | None = None

    def wire(self): return asdict(self)

@dataclass(frozen=True)
class Recipient:
    document: str
    handler_channel: str
    operation: str | None = None

    def wire(self): return asdict(self)

@dataclass(frozen=True)
class PlannedEvent:
    snapshot: str
    envelope: Envelope
    deliveries: tuple = ()

    def wire(self):
        return {'snapshot':self.snapshot, 'event':self.envelope.wire(),
                'recipients':[x.wire() for x in self.deliveries]}

MAX_ENTRIES = 4096
MAX_MANDATE_STEPS = 4096
MAX_SOURCES = 256

class CoordinationError(Exception):
    def __init__(self, code: str, **details: Any):
        self.code, self.details = code, deepcopy(details)
        super().__init__(f"{code}: {details}")

def require(condition: bool, code: str, **details: Any) -> None:
    if not condition:
        raise CoordinationError(code, **details)

def closed(value: Any, required: set[str], optional: set[str] = frozenset()) -> dict:
    require(type(value) is dict and required <= value.keys() <= required | optional,
            "INVALID_RECORD")
    return value

def uint(value: Any, maximum: int = SAFE) -> int:
    require(type(value) is int and 0 <= value <= maximum, "INVALID_INTEGER")
    return value

def decimal(value: str, maximum: int = SAFE + 1) -> int:
    require(type(value) is str and value.isascii() and value.isdigit()
            and len(value) <= len(str(maximum))
            and (value == "0" or not value.startswith("0")), "INVALID_DECIMAL")
    return uint(int(value), maximum)

def reference(value: Any) -> str:
    from algorithms import blue as L
    closed(value, {"blueId"})
    try:
        return L.final_id(value["blueId"])
    except L.Failure as exc:
        raise CoordinationError("INVALID_BLUE_ID") from exc

def transcript(kind: str, value: dict) -> bytes:
    return b"Blue Coordination 1\n" + canonical({"kind": kind, "value": value})

@dataclass(frozen=True)
class Entry:
    blue_id: str
    timeline: str
    timestamp: int
    actor: str
    message: str
    previous: str | None
    authority: str | None = None
    source: str | None = None

    @property
    def order(self) -> Order:
        return Order(self.timestamp, self.timeline, self.blue_id)

    def wire(self) -> dict:
        return asdict(self)

@dataclass(frozen=True)
class VerifiedPrefix:
    timeline: str
    before: int
    entries: tuple[Entry, ...]
    proof: str

    def wire(self) -> dict:
        return {"timeline": self.timeline, "before": str(self.before),
                "entries": [e.wire() for e in self.entries], "proof": self.proof}

@dataclass
class Decision:
    status: str
    snapshot: str
    entry: str | None = None
    plan: Any = None
    evidence: Any = None
    audit: dict | None = None
    diagnostic: dict | None = None

    def wire(self) -> dict:
        return {"status": self.status, "snapshot": self.snapshot, "entry": self.entry,
                "plan": self.plan.wire() if self.plan else None,
                "evidence": self.evidence.identity if self.evidence else None,
                "audit": self.audit, "diagnostic": self.diagnostic}

    @property
    def identity(self) -> str:
        return digest("coordination.decision/1", self.wire())
