"""Explicit Timeline acceptance runtime layered above the event-only processor.

Provider verification is Coordination's responsibility. This installed runtime
matches immutable Timeline/Actor definitions and suppresses older source entries.
It receives only the public Contracts ExternalChannelContext.
"""
from algorithms import blue as L
from blue_contracts import RuntimeBinding
from blue_contracts.reference.channels import leaves, checkpoint
from blue_contracts.reference.registry import EXTERNAL
from blue_contracts.reference.graph import Graph
from blue_contracts.reference.model import require

SEMANTICS = '''Blue Coordination Timeline Channel — event integration 2026-09-21.
The header contains exact timeline and actor definitions. Accept only whole
Timeline Entries whose projected timeline and actor equal those definitions.
An entry timestamp must equal the supplied processing timestamp. Accept an entry
only when its timestamp is greater than this channel's last checkpoint timestamp.
The signed provider guarantees strictly increasing timestamps per Timeline.
Proof acquisition, authorization and completeness occur in Coordination before
processing. No proof or delivery list is an argument to Contracts. Charge one
coordinationTimeline/accept counter before testing each channel. A mismatch is
false; invalid evidence is an error. This binding does not confer append rights.
'''

class TimelineAcceptance:
    def __init__(self, blue, entry_type): self.blue, self.entry_type = blue, entry_type
    def accept(self, context):
        context.gas.charge('accept')
        event = context.event
        if not hasattr(event, 'get') or event.get('type') != {'blueId': self.entry_type}: return False
        if event.get('timestamp') != context.timestamp: return False
        for key in ('timeline','actor'):
            if event.get(key) != context.header[key]: return False
        return context.checkpoint is None or context.timestamp > context.checkpoint['timestamp']


def publish_type(processor, catalogue):
    """Make the exact authoring type available without installing executable roles."""
    blue = processor.blue
    typ = blue.identity(blue.source({'name':'Timeline Channel',
        'type':{'blueId':processor.registry.types['Channel']},
        'coordinationSpecification':{'blueId':catalogue.specification}}, goal='definition'))
    blue.language.aliases['Coordination/Timeline Channel'] = typ
    blue.refresh()
    return typ


def install(processor, catalogue):
    blue = processor.blue
    semantics = blue.identity(blue.source(SEMANTICS))
    typ = publish_type(processor, catalogue)
    binding = RuntimeBinding(typ,semantics,'external-channel',('timeline','actor','coordinationSpecification'),(),
                             'coordinationTimeline',(('accept',1),))
    processor.install_runtime(binding, TimelineAcceptance(blue,catalogue.types['Timeline Entry']))
    return typ


def sources_for(processor, cs, key):
    result=[]
    for name in leaves(cs,key):
        c=cs[name]
        runtime=c.get('_extension')
        require(runtime is not None and runtime.binding.namespace=='coordinationTimeline',
                'UNBOUND_COORDINATION_CHANNEL',channel=name)
        source=processor.blue.identity(processor.blue.exact(processor.blue.select(c['_recipe'],'/timeline')))
        actor=processor.blue.identity(processor.blue.exact(processor.blue.select(c['_recipe'],'/actor')))
        result.append((name,source,actor))
    return result


def required_sources(processor,snapshot):
    result={}
    for key in Graph(snapshot,processor.registry,processor.archive).reachable(active=True):
        cs=processor.registry.contracts(snapshot.documents[key].body)
        for name,c in cs.items():
            if c['_role'] in EXTERNAL:
                for _,source,actor in sources_for(processor,cs,name):
                    result.setdefault(source,set()).add(actor)
    return result
