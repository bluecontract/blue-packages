"""Exact signed full-prefix protocol and its authoritative local provider.

Signatures authenticate a provider assertion, not the truth of its actor claims.
Transport I/O and credential authentication occur outside deterministic execution.
"""
from __future__ import annotations
from copy import deepcopy
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.exceptions import InvalidSignature
from blue_contracts.reference.model import SAFE, digest
from .model import (MAX_ENTRIES, CoordinationError, VerifiedPrefix, closed,
                    decimal, require, transcript, uint)

class LocalProvider:
    """A provider controls its append ACL; reading a channel never expands it."""
    def __init__(self, catalogue, timeline_id: str, private_key: Ed25519PrivateKey,
                 actors: tuple[str, ...]):
        self.catalogue = catalogue
        self.key = private_key
        public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
        self.timeline = catalogue.blue.identity(catalogue.blue.source(
            catalogue.typed("Timeline", timelineId=timeline_id, publicKey=public_key)))
        self.actors = frozenset(actors)
        for actor in self.actors:
            catalogue.actor(actor)
        self.entries = []
        self.frontier = 0
        self.requests = {}

    def append(self, actor: str, requested_time: int, message: str, *,
               authority: str | None = None, source: str | None = None,
               request_id: str | None = None):
        """actor is an authenticated principal supplied by the provider ingress."""
        uint(requested_time)
        require(actor in self.actors, "APPEND_NOT_AUTHORIZED")
        request = {"actor": actor, "time": requested_time, "message": message,
                   "authority": authority, "source": source}
        request_hash = digest("coordination.append/1", request)
        if request_id is not None:
            require(type(request_id) is str and bool(request_id), "INVALID_REQUEST_ID")
            if request_id in self.requests:
                prior_hash, entry = self.requests[request_id]
                require(prior_hash == request_hash, "IDEMPOTENCY_CONFLICT")
                return entry
        timestamp = max(requested_time, self.frontier,
                        self.entries[-1].timestamp + 1 if self.entries else 0)
        uint(timestamp)
        require(len(self.entries) < MAX_ENTRIES, "PREFIX_LIMIT")
        raw = self.catalogue.typed("Timeline Entry", timeline={"blueId": self.timeline},
                                  actor={"blueId": actor}, timestamp=timestamp,
                                  message={"blueId": message})
        # Publish the recognition site in the original signed entry. Never
        # unwrap/rewrite an already signed event when delivering to Contracts.
        from algorithms import blue as L
        from blue_contracts.reference.channels import operation_request
        if operation_request(self.catalogue.processor.registry, L.Ref(message)) is not None:
            raw['operation'] = {'blueId': message}
        if self.entries:
            raw["prevEntry"] = {"blueId": self.entries[-1].blue_id}
        if authority is not None:
            raw["onBehalfOf"] = {"blueId": authority}
        if source is not None:
            raw["source"] = {"blueId": source}
        blue_id = self.catalogue.blue.identity(self.catalogue.blue.source(raw))
        entry = self.catalogue.entry(blue_id)
        self.entries.append(entry)
        if request_id is not None:
            self.requests[request_id] = (request_hash, entry)
        return entry

    def acquire(self, before: int) -> dict:
        uint(before, SAFE + 1)
        # A request can ask for an older prefix after a later promise. The new
        # assertion is still true; it does not withdraw the later promise.
        self.frontier = max(self.frontier, before)
        statement = {"timeline": self.timeline, "completeBefore": str(before),
                     "entries": [e.blue_id for e in self.entries if e.timestamp < before]}
        signature = self.key.sign(transcript("prefix", statement)).hex()
        return {"statement": statement, "signature": signature}

    def checkpoint(self) -> dict:
        return {"timeline": self.timeline, "frontier": str(self.frontier),
                "entries": [e.blue_id for e in self.entries],
                "requests": {k: [v[0], v[1].blue_id] for k, v in sorted(self.requests.items())}}

    def restore(self, value: dict) -> None:
        closed(value, {"timeline", "frontier", "entries", "requests"})
        require(value["timeline"] == self.timeline, "PROVIDER_IDENTITY_MISMATCH")
        entries = verify_chain(self.catalogue, self.timeline, value["entries"], SAFE + 1)
        require(all(e.actor in self.actors for e in entries), "APPEND_NOT_AUTHORIZED")
        known = {e.blue_id: e for e in entries}
        requests = {}
        require(type(value["requests"]) is dict, "INVALID_PROVIDER_STATE")
        for key, row in value["requests"].items():
            require(type(key) is str and bool(key) and type(row) is list and len(row) == 2
                    and type(row[0]) is str and type(row[1]) is str and row[1] in known, "INVALID_PROVIDER_STATE")
            requests[key] = (row[0], known[row[1]])
        self.entries, self.frontier, self.requests = list(entries), decimal(value["frontier"]), requests


def verify_chain(catalogue, timeline: str, ids: list[str], before: int):
    require(type(ids) is list and len(ids) <= MAX_ENTRIES
            and all(type(x) is str for x in ids) and len(ids) == len(set(ids)), "INVALID_PREFIX")
    result = []
    previous = None
    last = -1
    for blue_id in ids:
        entry = catalogue.entry(blue_id)
        require(entry.timeline == timeline, "ENTRY_TIMELINE_MISMATCH")
        require(entry.previous == previous, "BROKEN_PREDECESSOR")
        require(last < entry.timestamp < before, "INVALID_SOURCE_ORDER")
        result.append(entry)
        previous, last = blue_id, entry.timestamp
    return tuple(result)

class PrefixVerifier:
    """Trust is explicit exact Timeline adoption; no inferred provider registry."""
    def __init__(self, catalogue, trusted_timelines=()):
        self.catalogue = catalogue
        self.trusted = frozenset(trusted_timelines)
        self.verified = {}
        self.packages = {}

    def export(self) -> dict:
        return {"packages": [deepcopy(self.packages[k]) for k in sorted(self.packages)]}

    def restore(self, wire: dict) -> None:
        closed(wire, {"packages"})
        require(type(wire["packages"]) is list, "INVALID_VERIFIER_STATE")
        staged = PrefixVerifier(self.catalogue, self.trusted)
        for package in wire["packages"]:
            closed(package, {"statement", "signature"})
            statement = closed(package.get("statement"), {"timeline", "completeBefore", "entries"})
            staged.verify(package, statement["timeline"], decimal(statement["completeBefore"]))
        self.verified, self.packages = staged.verified, staged.packages

    def verify(self, package: dict, timeline: str, required_before: int) -> VerifiedPrefix:
        uint(required_before, SAFE + 1)
        require(timeline in self.trusted, "UNTRUSTED_TIMELINE")
        closed(package, {"statement", "signature"})
        statement = closed(package["statement"], {"timeline", "completeBefore", "entries"})
        require(statement["timeline"] == timeline, "PREFIX_TIMELINE_MISMATCH")
        before = decimal(statement["completeBefore"])
        require(before >= required_before, "INSUFFICIENT_FRONTIER")
        require(type(statement["entries"]) is list and len(statement["entries"]) <= MAX_ENTRIES,
                "PREFIX_LIMIT")
        key = self.catalogue.timeline(timeline)["publicKey"]
        signature = package["signature"]
        require(type(signature) is str and len(signature) == 128
                and signature == signature.lower(), "INVALID_SIGNATURE")
        try:
            Ed25519PublicKey.from_public_bytes(bytes.fromhex(key)).verify(
                bytes.fromhex(signature), transcript("prefix", statement))
        except (ValueError, InvalidSignature) as exc:
            raise CoordinationError("INVALID_SIGNATURE") from exc
        entries = verify_chain(self.catalogue, timeline, statement["entries"], before)
        prior = self.verified.get(timeline)
        if prior is not None:
            common = min(prior.before, before)
            old = tuple(e.blue_id for e in prior.entries if e.timestamp < common)
            new = tuple(e.blue_id for e in entries if e.timestamp < common)
            require(old == new, "COMPLETENESS_CONTRADICTION")
        proof = digest("coordination.prefix/1", package)
        verified = VerifiedPrefix(timeline, before, entries, proof)
        self.packages[proof] = deepcopy(package)
        if prior is None or before >= prior.before:
            self.verified[timeline] = verified
        return verified

class ProviderSet:
    """Reference acquisition port. A network implementation returns the same facts.

    Unavailable/not-found/invalid are not empty-prefix results. Verifier state is
    updated only by validated statements, never by transport notifications.
    """
    def __init__(self, catalogue, providers=()):
        self.catalogue = catalogue
        providers = tuple(providers)
        self.providers = {p.timeline: p for p in providers}
        require(len(self.providers) == len(tuple(providers)), "DUPLICATE_PROVIDER")
        self.verifier = PrefixVerifier(catalogue, self.providers)
        self.unavailable = set()

    def prefix(self, timeline: str, before: int) -> VerifiedPrefix:
        require(timeline not in self.unavailable, "DEFERRED_UNAVAILABLE", timeline=timeline)
        require(timeline in self.providers, "NOT_FOUND", timeline=timeline)
        package = self.providers[timeline].acquire(before)
        return self.verifier.verify(package, timeline, before)
