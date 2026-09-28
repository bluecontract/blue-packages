"""Timeline-specific evidence acquisition over Contracts-owned source discovery."""
from algorithms import blue as L
from blue_contracts.reference.graph import Graph
from blue_contracts.reference.channels import select_seeds, recognize_call
from blue_contracts.reference.processor import Run
from .timeline_channel import required_sources
from blue_contracts.reference.registry import EXTERNAL, INTERNAL
from blue_contracts.reference.model import SAFE
from .model import MAX_SOURCES, CoordinationError, require, reference, uint
from .evidence import CoordinationEvidence


def surface(processor, snapshot):
    processor.validate(snapshot)
    graph = Graph(snapshot, processor.registry, processor.archive)
    sources = required_sources(processor, snapshot)
    require(len(sources) <= MAX_SOURCES, "SOURCE_LIMIT")
    return graph, tuple(sorted(sources))


def acquire(processor, snapshot, providers, before):
    """Full verified prefixes; extra checkpoint material is lookup-only."""
    uint(before, SAFE + 1)
    graph, sources = surface(processor, snapshot)
    prefixes = [providers.prefix(source, before) for source in sources]
    lookup = {}
    for key in sorted(graph.reachable(active=True)):
        marker = processor.registry.marker(snapshot.documents[key].body, 'checkpoint')
        if marker is None:
            continue
        rows = processor.blue.literal(marker).get('entries', {})
        for _, row in sorted(rows.items()):
            event_id = reference(row['event'])
            known = next((e for p in prefixes for e in p.entries if e.blue_id == event_id), None)
            if known is None:
                # Exact content locates evidence; it does not authenticate itself.
                claimed = providers.catalogue.entry(event_id)
                proof = providers.prefix(claimed.timeline, claimed.timestamp + 1)
                known = next((e for e in proof.entries if e.blue_id == event_id), None)
            require(known is not None, 'CHECKPOINT_NOT_IN_VERIFIED_HISTORY')
            require(known.timestamp == row['timestamp'], 'INVALID_CHECKPOINT_TIMESTAMP')
            lookup[event_id] = known
    return graph, tuple(prefixes), tuple(lookup.values())



def selected_recipients(processor,snapshot,entry):
    """Diagnostic preview; Contracts independently selects again at execution."""
    from .model import Recipient
    run=Run(processor,snapshot,L.Ref(entry.blue_id),entry.timestamp,100000)
    run.call,run.call_record=recognize_call(processor.registry,run.event)
    return tuple(Recipient(s.document,s.channel,s.operation) for s in select_seeds(run))


def first_relevant(processor,snapshot,graph,entries,evidence):
    for entry in sorted(entries,key=lambda e:e.order):
        recipients=selected_recipients(processor,snapshot,entry)
        if recipients:yield entry,recipients
