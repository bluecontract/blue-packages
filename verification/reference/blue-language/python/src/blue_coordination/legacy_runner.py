"""Timeline adapter over the Contracts one-event boundary.

LocalTimelineStore is an authoritative, local demo provider, not a verifier for
remote claims. Remote providers must verify their evidence before adaptation.
Contracts alone owns graph state, lifecycle, checkpoints and consequence closure.
"""
from copy import deepcopy
from dataclasses import asdict
from algorithms import blue as L
from blue_contracts import (Processor, Evidence, Envelope, next_plan, ContractError,
                            export_snapshot, import_snapshot, export_invocation,
                            import_invocation, compare_replay)
from blue_contracts.channels import leaves
from blue_contracts.registry import EXTERNAL
from blue_contracts.graph import Graph
from blue_contracts.model import integer, require, SAFE


def required_sources(engine, snapshot):
    result = {}
    graph = Graph(snapshot, engine.registry, engine.archive)
    for doc in sorted(graph.reachable(active=True)):
        cs = engine.registry.contracts(snapshot.documents[doc].body)
        for key, contract in cs.items():
            if contract['_role'] in EXTERNAL:
                for _, source, actor in leaves(cs, key):
                    result.setdefault(source, set()).add(actor)
    return result


def verified_timeline_evidence(windows, *, grants=()):
    """Adapt already-verified provider windows, preserving original Entry IDs.

Call a provider's verify(acquire(...)) first. A caller-supplied window is not
proof of authority. This function neither invents nor approves mandate grants.
"""
    envelopes = []; frontiers = {}
    for window in windows:
        frontiers[window.timeline_blue_id] = window.complete_before
        for entry in window.entries:
            envelopes.append(Envelope(entry.blue_id, entry.timeline.blue_id,
                                      entry.timestamp, entry.message.blue_id, entry.actor.blue_id))
    return Evidence(envelopes, frontiers, grants)


class LocalTimelineStore:
    def __init__(self, engine):
        self.engine = engine; self.sources = {}; self.events = []; self.unavailable = set()

    def register(self, source, actors=()):
        L.final_id(source)
        row = self.sources.setdefault(source, {'actors': [], 'before': 0})
        for actor in actors:
            if actor is not None: L.final_id(actor)
            if actor not in row['actors']: row['actors'].append(actor)

    def append(self, source, actor, timestamp, payload):
        integer(timestamp)
        require(source in self.sources, 'UNKNOWN_TIMELINE')
        row = self.sources[source]
        require(actor in row['actors'], 'INVALID_TIMELINE_ACTOR')
        history = [e for e in self.events if e.source == source]
        require(timestamp >= row['before'], 'ENTRY_BEHIND_FRONTIER')
        require(not history or timestamp > history[-1].timestamp, 'INVALID_SOURCE_ORDER')
        blue = self.engine.blue
        payload_id = blue.identity(blue.source(payload))
        body = {'timeline': {'blueId': source}, 'timestamp': timestamp,
                'message': {'blueId': payload_id}}
        if actor is not None: body['actor'] = {'blueId': actor}
        if history: body['prevEntry'] = {'blueId': history[-1].event}
        exact_id = blue.identity(blue.source(body))
        event = Envelope(exact_id, source, timestamp, payload_id, actor)
        self.events.append(event)
        return event

    def close_before(self, source, before):
        integer(before, 0, SAFE + 1)
        require(source in self.sources, 'UNKNOWN_TIMELINE')
        require(before >= self.sources[source]['before'], 'FRONTIER_REGRESSION')
        self.sources[source]['before'] = before

    def evidence(self, needed=None):
        needed = set(self.sources) if needed is None else set(needed)
        require(not needed & self.unavailable, 'PROVIDER_UNAVAILABLE', sources=sorted(needed & self.unavailable))
        # Retain evidence for checkpoints on channels that were rebound/removed.
        return Evidence(self.events, {s:r['before'] for s,r in self.sources.items() if s not in self.unavailable})

    def wire(self):
        return {'sources':deepcopy(self.sources), 'events':[e.wire() for e in self.events],
                'unavailable':sorted(self.unavailable)}

    def restore(self, value):
        self.sources = deepcopy(value['sources']); self.events = [Envelope.load(e) for e in value['events']]
        self.unavailable = set(value['unavailable'])
        self.evidence([])  # Validate timestamp uniqueness and source identity domains.
        previous = {}
        for e in self.events:
            require(e.source in self.sources and e.actor in self.sources[e.source]['actors'], 'INVALID_TIMELINE_ACTOR')
            body = self.engine.blue.literal(L.Ref(e.event))
            expected = {'timeline':{'blueId':e.source}, 'timestamp':e.timestamp, 'message':{'blueId':e.payload}}
            if e.actor is not None: expected['actor'] = {'blueId':e.actor}
            if e.source in previous:
                prior=previous[e.source]; require(prior.timestamp < e.timestamp, 'INVALID_SOURCE_ORDER')
                expected['prevEntry']={'blueId':prior.event}
            require(body == expected, 'INVALID_ORIGINAL_ENTRY')
            previous[e.source]=e


class Runner:
    """Independent rooted Contracts snapshots sharing one local Timeline store."""
    def __init__(self, language=None):
        self.processor=Processor(language); self.timelines=LocalTimelineStore(self.processor)
        self.roots={}; self.history={}; self.receipts=[]; self.events=[]; self.capsules={}

    def sync_sources(self):
        for snapshot in self.roots.values():
            for source, actors in required_sources(self.processor,snapshot).items():
                self.timelines.register(source, actors)

    def admit(self, name, members, *, bindings=None, gas_limit=100000):
        require(name not in self.roots, 'DUPLICATE_ROOT')
        outcome=self.processor.admit(members, name, bindings=bindings, gas_limit=gas_limit)
        require(outcome.commits, outcome.status, diagnostic=outcome.diagnostic)
        self.roots[name]=outcome.snapshot
        self.history[name]=[{'epoch':0,'blueId':outcome.snapshot.documents[name].blue_id,
                            'previousBlueId':None,'entry':None,'events':len(outcome.public_events),'receipt':outcome.receipt}]
        self.events.extend({'source':name,**event} for event in outcome.public_events)
        self.sync_sources()
        return outcome

    def plan(self, root):
        self.sync_sources(); snapshot=self.roots[root]
        evidence=self.timelines.evidence(required_sources(self.processor,snapshot))
        return next_plan(self.processor,snapshot,evidence), evidence

    def advance(self, root, *, gas_limit=100000):
        plan,evidence=self.plan(root)
        if plan is None:return None
        before=self.roots[root]; capsule=export_invocation(self.processor,before,plan,evidence,gas_limit=gas_limit)
        outcome=self.processor.process(before,plan,evidence,gas_limit=gas_limit)
        saved={'observations':outcome.observations(),'receipt':outcome.receipt}
        self.capsules[outcome.invocation]={'capsule':capsule,'gasLimit':gas_limit,'result':saved}
        self.receipts.append({'root':root,'entry':plan.envelope.event,'result':saved})
        if outcome.commits:
            self.roots[root]=outcome.snapshot
            self.history[root].append({'epoch':outcome.snapshot.revision,
                'blueId':outcome.snapshot.documents[root].blue_id,
                'previousBlueId':before.documents[root].blue_id,'entry':plan.envelope.event,
                'events':len(outcome.public_events),'receipt':outcome.receipt})
            self.events.extend({'source':root,**event} for event in outcome.public_events)
            self.sync_sources()  # Rediscover after each event; no global watermark.
        return outcome

    def replay(self, invocation):
        saved=self.capsules[invocation]; p=Processor()
        snapshot,plan,evidence,policy=import_invocation(p,saved['capsule'],saved['capsule']['identity'],with_policy=True)
        return compare_replay(saved['result'],p.process(snapshot,plan,evidence,**policy))

    def export(self):
        p=self.processor
        return {'release':p.registry.specification,'content':p.blue.language.provider.snapshot(),
                'roots':{k:export_snapshot(p,v) for k,v in self.roots.items()},
                'archive':[export_snapshot(p,v) for v in p.archive.versions.values()],
                'archiveChoices':dict(p.archive.choices),
                'timelines':self.timelines.wire(),'history':self.history,
                'receipts':self.receipts,'events':self.events,'capsules':self.capsules}

    def restore(self, value):
        p=self.processor; require(value['release']==p.registry.specification,'INCOMPATIBLE_RELEASE')
        p.blue.language.provider._records.update(value['content']); p.blue.refresh()
        for package in value['archive']:import_snapshot(p,package,package['identity'])
        for blue_id,identity in value.get('archiveChoices',{}).items():p.archive.bind(blue_id,identity)
        self.roots={k:import_snapshot(p,v,v['identity']) for k,v in value['roots'].items()}
        self.timelines.restore(value['timelines']); self.history=value['history']
        self.receipts=value['receipts']; self.events=value['events']; self.capsules=value['capsules']
        for snapshot in self.roots.values():p.validate(snapshot,evidence=self.timelines.evidence([]))
