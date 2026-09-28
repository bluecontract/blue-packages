"""Coordination data roles, separate from the existing Contracts registry."""
from pathlib import Path
import json
from algorithms import blue as L
from .model import Entry, CoordinationError, require, closed, uint, reference

PARENTS = {"Timeline": None, "Actor": None, "Source": None,
           "Timeline Entry": None, "Authority": None,
           "Mandate Authority": "Authority", "Operation Mandate": None,
           "Mandate Approval": None}

class Catalogue:
    def __init__(self, processor):
        self.processor = processor
        self.blue = processor.blue
        directory = Path(__file__).parent
        expected = json.loads((directory / "TYPE_CATALOGUE.json").read_text("utf-8"))
        text = (directory / "COMPLETE_SPECIFICATION.md").read_text("utf-8")
        self.specification = self.blue.identity(self.blue.source(text))
        require(self.specification == expected['specification'], 'SPECIFICATION_IDENTITY_MISMATCH')
        self.base_types = {}
        remaining = set(PARENTS)
        while remaining:
            for name in sorted(remaining):
                parent = PARENTS[name]
                if parent is not None and parent not in self.base_types:
                    continue
                raw = {"name": name, "specification": {"blueId": self.specification}}
                if parent is not None:
                    raw["type"] = {"blueId": self.base_types[parent]}
                self.base_types[name] = self.blue.identity(self.blue.source(raw, goal="definition"))
                remaining.remove(name)
        require(self.base_types == expected['baseRoles'], 'CATALOGUE_IDENTITY_MISMATCH')
        binding = (directory / "COMPLETE_ED25519_FULL_PREFIX.md").read_text("utf-8")
        self.provider_specification = self.blue.identity(self.blue.source(binding))
        require(self.provider_specification == expected['providerSpecification'], 'PROVIDER_BINDING_MISMATCH')
        concrete = self.blue.source({'name': 'Ed25519 Timeline',
            'type': {'blueId': self.base_types['Timeline']},
            'providerSpecification': {'blueId': self.provider_specification}}, goal='definition')
        self.types = {**self.base_types, 'Timeline': self.blue.identity(concrete)}
        require(self.types == expected['referenceTypes'], 'CATALOGUE_IDENTITY_MISMATCH')
        for name, blue_id in self.types.items():
            self.blue.language.aliases[f"Coordination/{name}"] = blue_id
        self.blue.language.aliases['Coordination/Generic Timeline'] = self.base_types['Timeline']
        self.blue.language.aliases['Coordination/Ed25519 Timeline'] = self.types['Timeline']
        self.blue.refresh()

    def typed(self, name: str, **fields) -> dict:
        return {"type": {"blueId": self.types[name]}, **fields}

    def read(self, blue_id: str, name: str | None = None) -> dict:
        node = L.Ref(blue_id)
        self.blue.certify(node)
        if name is not None:
            # The standard profile uses exact catalogue types. Extensions need an
            # installed, independently specified verifier, not shape inference.
            require(self.blue.head(node).type_id == self.types[name], "UNSUPPORTED_TYPE", role=name)
        value = self.blue.literal(node)
        require(type(value) is dict, "INVALID_TYPED_VALUE")
        return value

    def timeline(self, blue_id: str) -> dict:
        value = self.read(blue_id, "Timeline")
        closed(value, {"type", "timelineId", "publicKey"})
        require(type(value["timelineId"]) is str and bool(value["timelineId"]), "INVALID_TIMELINE")
        public = value["publicKey"]
        require(type(public) is str and len(public) == 64 and public == public.lower(), "INVALID_PUBLIC_KEY")
        try:
            require(len(bytes.fromhex(public)) == 32, "INVALID_PUBLIC_KEY")
        except ValueError as exc:
            raise CoordinationError("INVALID_PUBLIC_KEY") from exc
        return value

    def actor(self, blue_id: str) -> dict:
        value = self.read(blue_id, "Actor")
        closed(value, {"type", "actorId"})
        require(type(value["actorId"]) is str and bool(value["actorId"]), "INVALID_ACTOR")
        return value

    def entry(self, blue_id: str) -> Entry:
        value = self.read(blue_id, "Timeline Entry")
        closed(value, {"type", "timeline", "timestamp", "actor", "message"},
               {"prevEntry", "onBehalfOf", "source", "operation"})
        timeline = reference(value["timeline"])
        actor = reference(value["actor"])
        self.timeline(timeline)
        self.actor(actor)
        message = reference(value["message"])
        self.blue.certify(L.Ref(message))
        from blue_contracts.reference.channels import operation_request
        call = operation_request(self.processor.registry, L.Ref(message))
        require(('operation' in value) == (call is not None), 'ENTRY_OPERATION_MISMATCH')
        if call is not None:
            require(reference(value['operation']) == message, 'ENTRY_OPERATION_MISMATCH')
        previous = reference(value["prevEntry"]) if "prevEntry" in value else None
        authority = reference(value["onBehalfOf"]) if "onBehalfOf" in value else None
        source = reference(value["source"]) if "source" in value else None
        # Attribution is needed for every entry. Authority is resolved only if
        # direct authority fails, so unnecessary authority may remain opaque.
        if source is not None:
            self.blue.certify(L.Ref(source))
        return Entry(blue_id, timeline, uint(value["timestamp"]), actor,
                     message, previous, authority, source)
