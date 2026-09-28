"""Local host for the immutable Coordination specification.

Private signing keys and append ACLs belong to this trusted local workspace.
Channel discovery never creates a provider or grants append authority.
"""
from copy import deepcopy
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from algorithms import blue as L
from blue_contracts import (Processor, import_invocation, compare_replay, export_snapshot, import_snapshot)
from blue_runtime.portable import export_invocation
from blue_coordination_spec.model import Envelope
from blue_contracts.model import SAFE
from blue_coordination_spec import Catalogue, Coordinator, LocalProvider, ProviderSet
from blue_coordination_spec.model import CoordinationError, require, uint
from blue_coordination_spec.evidence import CoordinationEvidence
from blue_coordination_spec.timeline_channel import required_sources, install as install_timeline_channel
from blue_runtime.record_bridge import install_record_bridge


def envelope(entry):
    return Envelope(entry.blue_id, entry.timeline, entry.timestamp, entry.message, entry.actor)


class HostCatalogue(Catalogue):
    """Read standard Entry links by exact Blue identity at the host boundary.

    Language retention can store an admitted DAG child inline instead of as a
    reference (notably when retaining an SCC and historical checkpoints). Those
    representations have the same Blue identity. The immutable Coordination
    verifier consumes reference-shaped link fields, so project only those links
    back to exact references. Keep all other fields for its closed-record checks;
    target types, signatures, chain ordering and entry identities are still
    verified by the supplied implementation.
    """
    def read(self, blue_id, name=None):
        value = super().read(blue_id, name)
        if name == 'Timeline Entry':
            value = deepcopy(value); projected = False
            for key in ('timeline', 'actor', 'message', 'operation', 'prevEntry', 'onBehalfOf', 'source'):
                field = value.get(key)
                if type(field) is dict and set(field) != {'blueId'}:
                    exact = self.blue.exact(self.blue.select(L.Ref(blue_id), '/' + key))
                    value[key] = {'blueId': self.blue.identity(exact)}; projected = True
            # Representation projection must never alter the signed commitment.
            if projected:
                node = self.blue.node(value)
                require(self.blue.identity(node) == blue_id, 'ENTRY_IDENTITY_MISMATCH')
        return value


class SignedTimelines:
    def __init__(self, catalogue):
        self.catalogue = catalogue
        self.providers = ProviderSet(catalogue)
        self.needed = {}

    @property
    def unavailable(self):
        return self.providers.unavailable

    @property
    def events(self):
        return sorted((envelope(e) for p in self.providers.providers.values() for e in p.entries),
                      key=lambda e: (e.timestamp, e.source, e.event))

    @property
    def sources(self):
        rows = {s: {'actors': sorted(a, key=lambda x: x or ''), 'before': 0, 'owned': False}
                for s, a in self.needed.items()}
        for s, p in self.providers.providers.items():
            rows[s] = {'actors': sorted(p.actors), 'before': p.frontier, 'owned': True}
        return rows

    def track(self, sources):
        self.needed = sources

    def create(self, name, actor_names):
        require(type(name) is str and bool(name.strip()), 'INVALID_TIMELINE')
        c = self.catalogue
        actors = tuple(c.blue.identity(c.blue.source(c.typed('Actor', actorId=a))) for a in actor_names)
        for provider in self.providers.providers.values():
            if c.timeline(provider.timeline)['timelineId'] == name:
                require(set(actors) <= provider.actors, 'APPEND_ACL_CONFLICT')
                return provider
        provider = LocalProvider(c, name, Ed25519PrivateKey.generate(), actors)
        self.providers.providers[provider.timeline] = provider
        self.providers.verifier.trusted = frozenset(self.providers.providers)
        return provider

    def append(self, source, actor, timestamp, payload, *, authority=None, attribution=None, request_id=None):
        require(source in self.providers.providers, 'NOT_FOUND', timeline=source)
        require(source not in self.unavailable, 'DEFERRED_UNAVAILABLE', timeline=source)
        message = self.catalogue.blue.identity(self.catalogue.blue.source(payload))
        entry = self.providers.providers[source].append(actor, timestamp, message,
            authority=authority, source=attribution, request_id=request_id)
        return envelope(entry)

    def close_before(self, source, before):
        uint(before, SAFE + 1)
        require(source in self.providers.providers, 'NOT_FOUND', timeline=source)
        require(source not in self.unavailable, 'DEFERRED_UNAVAILABLE', timeline=source)
        provider = self.providers.providers[source]
        require(before >= provider.frontier, 'FRONTIER_REGRESSION')
        self.providers.prefix(source, before)

    def evidence(self, needed=None):
        selected = set(self.providers.providers) if needed is None or not needed else set(needed)
        # Restore authenticates retained local provider state even if its live
        # acquisition switch is unavailable. Coordinator.next still blocks it.
        return CoordinationEvidence([self.providers.verifier.verify(
            self.providers.providers[s].acquire(self.providers.providers[s].frontier),
            s, self.providers.providers[s].frontier) for s in sorted(selected)])

    def wire(self):
        return {'providers': [{
            'name': self.catalogue.timeline(p.timeline)['timelineId'],
            'privateKey': p.key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()).hex(),
            'actors': sorted(p.actors), 'state': p.checkpoint()}
            for _, p in sorted(self.providers.providers.items())],
            'verifier': self.providers.verifier.export(), 'unavailable': sorted(self.unavailable)}

    def restore(self, wire):
        providers = []
        for row in wire['providers']:
            provider = LocalProvider(self.catalogue, row['name'],
                Ed25519PrivateKey.from_private_bytes(bytes.fromhex(row['privateKey'])), tuple(row['actors']))
            provider.restore(row['state'])
            providers.append(provider)
        self.providers = ProviderSet(self.catalogue, providers)
        self.providers.verifier.restore(wire['verifier'])
        require(set(wire['unavailable']) <= self.providers.providers.keys(), 'UNKNOWN_TIMELINE')
        self.providers.unavailable = set(wire['unavailable'])


class Runner:
    """The new Coordinator selects and authorizes; Contracts executes each event."""
    def __init__(self, language=None):
        self.processor = install_record_bridge(Processor(language))
        self.catalogue = HostCatalogue(self.processor)
        self.timeline_channel_type = install_timeline_channel(self.processor,self.catalogue)
        self.timelines = SignedTimelines(self.catalogue)
        self.coordinator = Coordinator(self.processor, self.catalogue, self.timelines.providers)
        self.roots = {}; self.history = {}; self.receipts = []; self.events = []; self.capsules = {}
        self.instances = {}; self.port_owners = {}; self.last_decisions = {}

    def sync_sources(self):
        needed = {}
        for snapshot in self.roots.values():
            for source, actors in required_sources(self.processor, snapshot).items():
                needed.setdefault(source, set()).update(actors)
        self.timelines.track(needed)

    def prepare_source(self, value):
        """Explicit local authoring helper. Never opens or rewrites exact refs.

        Convert named draft Timeline/Actor placeholders into new signed Timeline
        definitions. The caller displays the changed Source before saving it.
        """
        result = deepcopy(value); declarations = []
        def visit(node):
            if type(node) is list:
                for v in node: visit(v)
            if type(node) is not dict or set(node) == {'blueId'}: return
            for contract in node.get('contracts', {}).values() if type(node.get('contracts')) is dict else ():
                if type(contract) is not dict: continue
                if contract.get('type') not in ('Coordination/Timeline Channel', {'blueId': self.timeline_channel_type}): continue
                source, actor = contract.get('timeline'), contract.get('actor')
                source_type = source.get('type') if type(source) is dict else None
                actor_type = actor.get('type') if type(actor) is dict else None
                source_placeholder = type(source) is dict and (set(source) == {'timelineId'} or
                    set(source) == {'type', 'timelineId'} and source_type in ('Coordination/Timeline', {'blueId': self.catalogue.types['Timeline']}))
                actor_placeholder = type(actor) is dict and (set(actor) in ({'accountId'}, {'actorId'}) or
                    set(actor) == {'type', 'actorId'} and actor_type in ('Coordination/Actor', {'blueId': self.catalogue.types['Actor']}))
                if source_placeholder and actor_placeholder:
                    name = source['timelineId']; person = actor.get('accountId', actor.get('actorId'))
                    require(type(name) is str and bool(name), 'INVALID_TIMELINE')
                    require(type(person) is str and bool(person), 'INVALID_ACTOR')
                    declarations.append((contract, name, person))
            for key, child in node.items():
                if type(key) is str and key not in ('contracts', 'steps') and not key.startswith('$'): visit(child)
        visit(result)
        groups = {}
        for _, name, person in declarations: groups.setdefault(name, set()).add(person)
        providers = {name: self.timelines.create(name, sorted(actors)) for name, actors in groups.items()}
        for contract, name, person in declarations:
            provider = providers[name]
            # Inline exact definitions keep this Source portable through Content.
            contract['timeline'] = self.catalogue.read(provider.timeline, 'Timeline')
            contract['actor'] = self.catalogue.typed('Actor', actorId=person)
        return result

    def prepare_graph(self, graph):
        """Re-address explicitly authored local definitions with prepared channels."""
        if type(graph) is not dict: return graph
        definitions = graph.get('definitions', [])
        if type(definitions) is not list or any(type(d) is not dict for d in definitions):
            return graph  # The application reports its normal graph diagnostic.
        old_ids = [self.processor.blue.identity(self.processor.blue.source(d, goal='definition'))
                   for d in definitions]
        prepared = self.prepare_source(graph)
        mapping = {}
        def rewrite(value):
            if type(value) is list: return [rewrite(v) for v in value]
            if type(value) is not dict: return value
            if set(value) == {'blueId'} and value['blueId'] in mapping:
                return {'blueId': mapping[value['blueId']]}
            return {k: rewrite(v) for k, v in value.items()}
        for index, original in enumerate(old_ids):
            definition = rewrite(prepared['definitions'][index])
            prepared['definitions'][index] = definition
            mapping[original] = self.processor.blue.identity(self.processor.blue.source(definition, goal='definition'))
        prepared['documents'] = rewrite(prepared.get('documents', {}))
        return prepared

    def decision(self, root):
        self.processor.blue.begin_request()
        self.sync_sources(); state = self.roots[root]
        needed = required_sources(self.processor, state)
        before = min((self.timelines.sources[s]['before'] for s in needed), default=0)
        decision = self.coordinator.next(state, before=before,
            instances=self.instances, port_owners=self.port_owners)
        self.last_decisions[root] = decision.wire()
        return decision

    def plan(self, root):
        decision = self.decision(root)
        if decision.status not in ('READY', 'IDLE_THROUGH'):
            raise CoordinationError(decision.status, diagnostic=decision.diagnostic)
        return decision.plan, decision.evidence

    def advance(self, root, *, gas_limit=100000, local_limits=None):
        decision = self.decision(root)
        if decision.status == 'IDLE_THROUGH': return None
        if decision.status != 'READY':
            raise CoordinationError(decision.status, diagnostic=decision.diagnostic)
        before = self.roots[root]
        self.processor.gas_limit=gas_limit; self.processor.local_limits=dict(local_limits or {})
        capsule = export_invocation(self.processor, before, L.Ref(decision.entry), decision.plan.envelope.timestamp)
        outcome = self.coordinator.execute(before, decision, gas_limit=gas_limit, local_limits=local_limits)
        saved = {'observations': outcome.observations(), 'receipt': outcome.receipt,
                 'coordination': decision.wire(), 'decisionIdentity': decision.identity}
        self.capsules[outcome.invocation] = {'capsule': capsule, 'gasLimit': gas_limit,
            'result': {'observations': saved['observations'], 'receipt': saved['receipt']}}
        self.receipts.append({'root': root, 'entry': decision.entry, 'result': saved})
        if outcome.commits:
            self.roots[root] = outcome.snapshot
            self.history[root].append({'epoch': outcome.snapshot.revision,
                'blueId': outcome.snapshot.documents[root].blue_id,
                'previousBlueId': before.documents[root].blue_id, 'entry': decision.entry,
                'events': len(outcome.public_events), 'receipt': outcome.receipt})
            self.events.extend({'source': root, **event} for event in outcome.public_events)
            self.sync_sources()
        return outcome


    def admit(self,name,members,*,bindings=None,gas_limit=100000):
        require(name not in self.roots,'DUPLICATE_ROOT')
        outcome=self.processor.admit(members,name,bindings=bindings,gas_limit=gas_limit)
        require(outcome.commits,outcome.status,diagnostic=outcome.diagnostic)
        self.roots[name]=outcome.snapshot
        self.history[name]=[{'epoch':0,'blueId':outcome.snapshot.documents[name].blue_id,
            'previousBlueId':None,'entry':None,'events':len(outcome.public_events),'receipt':outcome.receipt}]
        self.events.extend({'source':name,**event} for event in outcome.public_events)
        self.sync_sources();return outcome

    def replay(self,invocation):
        saved=self.capsules[invocation];other=Runner();p=other.processor
        snapshot,event,timestamp=import_invocation(p,saved['capsule'],saved['capsule']['identity'])
        return compare_replay(saved['result'],p.process(snapshot,event,timestamp))

    def export(self):
        p=self.processor
        return {'release':p.registry.specification,'coordinationRelease':self.catalogue.specification,
            'providerRelease':self.catalogue.provider_specification,
            'content':p.blue.language.provider.snapshot(),
            'roots':{k:export_snapshot(p,v) for k,v in self.roots.items()},
            'archive':[export_snapshot(p,v) for v in p.archive.versions.values()],
            'archiveChoices':dict(p.archive.choices),'timelines':self.timelines.wire(),
            'history':self.history,'receipts':self.receipts,'events':self.events,
            'capsules':self.capsules,'instances':self.instances,
            'portOwners':[[list(k),list(v)] for k,v in self.port_owners.items()]}

    def restore(self,value):
        p=self.processor
        require(value.get('coordinationRelease')==self.catalogue.specification,'INCOMPATIBLE_COORDINATION_RELEASE')
        require(value.get('providerRelease')==self.catalogue.provider_specification,'INCOMPATIBLE_PROVIDER_RELEASE')
        require(value['release']==p.registry.specification,'INCOMPATIBLE_RELEASE')
        p.blue.language.provider.merge_responses(value['content']);p.blue.refresh()
        for package in value['archive']:import_snapshot(p,package,package['identity'])
        for blue_id,identity in value.get('archiveChoices',{}).items():p.archive.bind(blue_id,identity)
        self.roots={k:import_snapshot(p,v,v['identity']) for k,v in value['roots'].items()}
        self.timelines.restore(value['timelines'])
        self.history=value['history'];self.receipts=value['receipts'];self.events=value['events'];self.capsules=value['capsules']
        self.instances=value.get('instances',{});self.port_owners={tuple(k):tuple(v) for k,v in value.get('portOwners',[])}
        self.coordinator=Coordinator(p,self.catalogue,self.timelines.providers)
        for snapshot in self.roots.values():p.validate(snapshot)
        self.sync_sources()
