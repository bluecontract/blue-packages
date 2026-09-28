"""Verified source participation, exact target routing and immutable decisions."""
import json
from collections import OrderedDict
from algorithms import blue as L
from blue_contracts import RuntimeBinding
from blue_contracts.reference.model import ContractError
from blue_contracts.reference.runtime import data_copy
from blue_contracts.reference.channels import operation_request, leaves
from blue_coordination_spec.model import require, CoordinationError
from .sources import PrefixVerifier


def decision_key(member, document, channel, generation):
    return json.dumps([member, document, channel, generation], separators=(',', ':'))


class TimelineRuntime:
    def __init__(self, catalogue, trusted, history):
        self.catalogue = catalogue
        self.trusted = trusted if callable(trusted) else frozenset(trusted)
        self.history = history
        self._prefixes = OrderedDict()

    def verify_admission(self, context):
        try:
            return self._verify(context)
        except CoordinationError as error:
            raise ContractError(error.code, **error.details) from error

    def _verify(self, context):
        c = self.catalogue
        evidence = data_copy(context.evidence)
        require(type(evidence) is dict and set(evidence) == {'ranges'}, 'MISSING_ADMISSION_EVIDENCE')
        require(type(evidence['ranges']) is list, 'INVALID_ADMISSION_EVIDENCE')
        trusted = self.trusted() if callable(self.trusted) else self.trusted
        verifier = PrefixVerifier(c, trusted)
        prefixes = {}
        for proof in evidence['ranges']:
            retained = self.history.retained_prefix(proof, trusted) if hasattr(self.history, 'retained_prefix') else None
            if retained is not None:
                require(retained.timeline not in prefixes, 'DUPLICATE_SOURCE_EVIDENCE')
                prefixes[retained.timeline] = retained
                continue
            cache_key = (proof, tuple(sorted(trusted)))
            prefix = self._prefixes.get(cache_key)
            if prefix is None:
                prefix = verifier.verify(proof)
                self._prefixes[cache_key] = prefix
                while len(self._prefixes) > 128:
                    self._prefixes.popitem(last=False)
            else:
                self._prefixes.move_to_end(cache_key)
            require(prefix.timeline not in prefixes, 'DUPLICATE_SOURCE_EVIDENCE')
            prefixes[prefix.timeline] = prefix
        entry = c.entry(context.event)
        require(entry.timestamp == context.timestamp, 'EVENT_TIMESTAMP_MISMATCH')
        require(entry.timeline in prefixes and entry in prefixes[entry.timeline].entries, 'UNVERIFIED_ENTRY')
        request = operation_request(c.processor.registry, L.Ref(entry.message))
        if request is not None and 'document' in request:
            require(self.history.known(request['document']['blueId']), 'WAITING_TARGET_HISTORY',
                    document=request['document']['blueId'])
        decisions, assessments, audience, declarations_by_document = {}, [], {}, {}
        for row in context.members:
            timeline = c.link(row['declaration'], 'timeline')
            holder = c.link(row['declaration'], 'actor')
            require(timeline in prefixes, 'MISSING_SOURCE_COMPLETENESS', timeline=timeline)
            require(entry.timestamp < prefixes[timeline].before, 'WAITING_COMPLETENESS', timeline=timeline)
            lineage = self.history.lineage(row['member'], row['document'])
            require(lineage is not None, 'UNESTABLISHED_DOCUMENT_HISTORY', document=row['document'])
            disposition, reason = 'INAPPLICABLE', 'Different source participation'
            addressed = request is None or 'document' not in request or self.history.belongs(lineage, request['document']['blueId'])
            audience[row['member']] = addressed
            if row['document'] not in declarations_by_document:
                declarations_by_document[row['document']] = c.processor.registry.contracts(L.Ref(row['document']))
            declarations = declarations_by_document[row['document']]
            candidate = request is not None and addressed and (('document' in request) or
                request['channel'] in declarations and row['channel'] in leaves(declarations,request['channel']))
            observer = any(d['_role'] in ('workflow','extension_handler') and
                d['channel'] in declarations and declarations[d['channel']]['_role'] in
                    ('external','extension_external','composite','all') and
                row['channel'] in leaves(declarations,d['channel']) for d in declarations.values())
            direct = entry.timeline == timeline and entry.actor == holder
            if direct and (request is None or candidate or observer):
                disposition, reason = 'ELIGIBLE', 'Authenticated direct source participation'
            elif addressed and request is not None and entry.authority is not None:
                selected = request['channel']
                if selected in declarations and row['channel'] in leaves(declarations, selected):
                    verdict = self.history.authorize(entry, lineage, row['document'], selected, holder, request)
                    disposition, reason = verdict['disposition'], verdict['reason']
            if disposition == 'ELIGIBLE' and candidate and request['channel'] in declarations and row['channel'] in leaves(declarations,request['channel']):
                if not self.history.actor_policy(row['document'], request['operation'], entry, delegated=not direct):
                    disposition, reason = 'DENIED', 'Actor or authenticated Source policy rejected this action'
            previous = row['checkpoint']
            if disposition == 'ELIGIBLE' and previous is not None:
                previous_entry = c.entry(previous['event']['blueId'])
                require(previous_entry.timestamp == previous['timestamp'], 'CHECKPOINT_TIMESTAMP_MISMATCH')
                if entry.order <= previous_entry.order:
                    disposition, reason = 'INAPPLICABLE', 'This channel lifetime has already passed the full order key'
            key = decision_key(row['member'], row['document'], row['channel'], row['generation'])
            lifetime_scope = getattr(self.history, 'delivery_lifetimes', None)
            if lifetime_scope is not None and (row['member'], row['channel'], row['generation']) not in lifetime_scope:
                disposition, reason = 'INAPPLICABLE', 'Historical input belongs to another channel lifetime'
            if self.history.terminal(lineage, row['member'], row['channel'], row['generation'], entry.blue_id):
                disposition, reason = 'INAPPLICABLE', 'Terminal decision in this channel lifetime'
            decisions[key] = disposition == 'ELIGIBLE'
            assessments.append(dict(member=row['member'], document=row['document'], channel=row['channel'],
                generation=row['generation'], disposition=disposition, reason=reason))
        lifetime_scope = getattr(self.history, 'delivery_lifetimes', None)
        if request is not None and lifetime_scope is not None:
            # Catch-up can expose an old call to a NEW ordinary observer without
            # reopening the operation's already-consumed channel lifetime.
            for member in audience:
                rows = [r for r in context.members if r['member']==member]
                eligible = False
                for row in rows:
                    declarations = declarations_by_document[row['document']]
                    if request['channel'] in declarations and row['channel'] in leaves(declarations,request['channel']):
                        eligible |= (member,row['channel'],row['generation']) in lifetime_scope
                audience[member] &= eligible
        return dict(snapshot=context.snapshot, entry=context.event, timestamp=context.timestamp,
                    runtime=data_copy(context.runtime), decisions=decisions, assessments=assessments,
                    operationAudience=audience)

    def accept(self, context):
        context.gas.charge('accept')
        evidence = context.evidence
        if evidence is None:
            raise ContractError('MISSING_VERIFIED_ADMISSION')
        if context.timestamp != evidence['timestamp']:
            raise ContractError('ADMISSION_TIMESTAMP_MISMATCH')
        key = decision_key(context.member, context.document, context.channel, context.generation)
        if key not in evidence['decisions']:
            raise ContractError('UNASSESSED_CHANNEL')
        return evidence['decisions'][key]


def install(processor, catalogue, trusted, history):
    binding = RuntimeBinding(catalogue.types['Coordination/Timeline Channel'], catalogue.specification,
        'external-channel', ('timeline', 'actor'), (), 'coordinationTimeline', (('accept', 1),))
    processor.install_runtime(binding, TimelineRuntime(catalogue, trusted, history))
    marker = RuntimeBinding(catalogue.types['Coordination/Actor Policy'], catalogue.specification,
        'marker', ('operations',), (), 'coordinationPolicy', ())
    processor.install_runtime(marker, object())
    return binding.type_id


def channels(processor, catalogue, snapshot):
    result = []
    from blue_contracts.reference.graph import Graph
    for member in sorted(Graph(snapshot, processor.registry, processor.archive).reachable(active=True)):
        doc = snapshot.documents[member]
        for key, declaration in processor.registry.contracts(doc.body).items():
            if declaration['_role'] != 'extension_external':
                continue
            if declaration['_extension'].binding.type_id != catalogue.types['Coordination/Timeline Channel']:
                continue
            node = processor.blue.exact(declaration['_recipe'])
            identity = processor.blue.identity(node)
            processor.blue.remember(node)
            result.append(dict(member=member, channel=key, generation=doc.channel_lives[key].generation,
                timeline=catalogue.link(identity, 'timeline'), actor=catalogue.link(identity, 'actor')))
    return result
