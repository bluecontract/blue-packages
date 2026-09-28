"""Exact, separately prepared Coordination types and closed protocol records."""
from copy import deepcopy, copy
from contextlib import contextmanager
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import re
from algorithms import blue as L
from blue_language.prepared import PreparedRepository, PreparedLanguage
from blue_repository import Repository
from blue_coordination_spec.model import Entry, require, uint
from blue_contracts.reference.channels import operation_request
from ._release import PREPARED_SHA256, CATALOGUE_SHA256

DIRECTORY = Path(__file__).with_name('resources')


@lru_cache(maxsize=1)
def repository():
    return PreparedRepository.load(DIRECTORY / 'coordination.prepared.json', expected_sha256=PREPARED_SHA256)


class Catalogue:
    def __init__(self, processor):
        self.processor = processor
        self.blue = processor.blue
        raw = (DIRECTORY / 'catalogue.json').read_bytes()
        require(hashlib.sha256(raw).hexdigest() == CATALOGUE_SHA256, 'CATALOGUE_INTEGRITY')
        data = json.loads(raw)
        require(data['contracts'] == processor.registry.specification, 'INCOMPATIBLE_CONTRACTS_RELEASE')
        self.specification, self.types, self.sources = data['specification'], data['types'], data['sources']
        prepared = repository()
        mounted = prepared if isinstance(self.blue.language, PreparedLanguage) else Repository.from_payload(
            prepared.name, prepared.aliases, prepared.records, metadata=prepared.metadata)
        self.blue.language.enable_repository(mounted)
        self.blue.refresh()
        self._reads = OrderedDict()

    @contextmanager
    def admission_unit(self):
        """One record admission outside a Contracts invocation.

        Keep the same captured evidence and successful validation caches. Each
        record is fully admitted with optional host controls. Transport batches
        do not limit the total signed finite history.
        """
        prior = self.blue.context
        context = copy(prior)
        context.work, context.demands = 0, []
        self.blue.context = context
        try:
            yield
        finally:
            self.blue.context = prior

    def typed(self, type_name, **fields):
        type_name = type_name if '/' in type_name else 'Coordination/' + type_name
        return {'type': {'blueId': self.types[type_name]}, **fields}

    def admit(self, value):
        """Admit Source with the Language port, without unused pretty exports.

        This host needs exact identity and retained evidence, not a canonical
        presentation of every referenced business graph. Run the same parsing,
        strict admission and root-duplicate rules as Language.create. The
        invocation's fixed resolver already holds verified immutable content.
        This is outside Contracts processing and its logical gas machine.
        """
        context = self.blue.context
        context.work = 0
        context.demands.clear()
        try:
            with L.error_scope(context, '', 'operation'):
                context.diagnostic_goal = 'value'
                raw = L.parse(L.wire_text(self.blue.normalize_input(value)), limits=context.limits)
                node = L.prepare_source(raw, context)
                context.diagnostic_root = node
                self.blue.certify(node,'value')
                node, removed = L.omit_root_duplicates(node, context)
                if removed:
                    self.blue.certify(node,'value')
                records = (self.blue.language.retained_records(node,context)
                    if hasattr(self.blue.language,'retained_records') else L.admitted_records(node, context))
                self.blue.language.provider.merge_responses(records)
                self.blue.remember(node)
                return self.blue.identity(node)
        except L.Failure as error:
            self.blue.translate(error)
        except RecursionError as error:
            self.blue.translate(L.Failure('OperationLimitExceeded', 'recursion'))

    def is_type(self, node, name):
        name = name if '/' in name else 'Coordination/' + name
        tid = self.blue.head(node).type_id
        return tid is not None and self.types[name] in L.ancestry(tid, self.blue.context)

    def fields(self, name):
        source = self.sources[name]
        parent = source.get('type')
        inherited = self.fields(parent) if isinstance(parent, str) and parent in self.sources else {}
        return {**inherited, **{k: v for k, v in source.items() if k not in L.RESERVED}}

    def read(self, identity, name=None, *, closed=True):
        cache_key = (identity, name, closed, tuple((key, runtime.binding) for key, runtime in sorted(self.processor.registry.extensions.items())))
        if cache_key in self._reads:
            self._reads.move_to_end(cache_key)
            return deepcopy(self._reads[cache_key])
        node = L.Ref(identity)
        self.blue.certify(node)
        if name is not None:
            name = name if '/' in name else 'Coordination/' + name
            require(self.is_type(node, name), 'INVALID_PROTOCOL_TYPE', expected=name)
            fields = self.fields(name)
            # Business Mandates may extend their state and executable program;
            # their lifecycle and writer rules are verified separately.
            if closed:
                require(set(self.blue.head(node).fields) <= set(fields), 'UNKNOWN_PROTOCOL_FIELD', type=name)
            for key, shape in fields.items():
                if isinstance(shape, dict) and shape.get('description', '').startswith('Required exact content operand.'):
                    require(self.operand(identity, key) is not None, 'MISSING_PROTOCOL_FIELD', field=key)
                child = self.blue.child(node, key)
                if child is None or not L.present_recipe(child, self.blue.context):
                    continue
                description = shape.get('description', '') if isinstance(shape, dict) else ''
                optional = re.match(r'Optional ([A-Za-z]+/[A-Za-z ]+);', description)
                if optional:
                    expected = optional.group(1)
                    if expected == 'Contracts/Operation Request':
                        require(operation_request(self.processor.registry, self.blue.exact(child)) is not None, 'INVALID_PROTOCOL_TYPE', field=key)
                    else:
                        require(self.is_type(child, expected), 'INVALID_PROTOCOL_TYPE', field=key)
        value = self._values(node)
        require(type(value) is dict, 'INVALID_PROTOCOL_RECORD')
        self._reads[cache_key] = deepcopy(value)
        while len(self._reads) > 128:
            self._reads.popitem(last=False)
        return value

    def _values(self, node, seen=frozenset()):
        """Read protocol data without reifying contextual declaration holes.

        Exact operands keep their authored identity. In particular an optional
        empty-object declaration must not become part of a referenced program.
        """
        identity = self.blue.identity(node)
        if identity in seen:
            return {'blueId': identity}
        head = self.blue.head(node)
        if head.value is not L.ABSENT:
            return self.blue.project(node)
        seen = seen | {identity}
        if head.items is not None:
            body = self.blue.open(node)
            items = body.get('items')
            if isinstance(items, tuple):
                return [self._values(item, seen) for item in items]
            return self.blue.project(node, preserve_cyclic=True)
        result = {}
        for key in head.fields:
            operand = self.operand(identity, key)
            if operand is not None:
                # Protocol links select exact content; reading a receipt must
                # not expand every business document (and its whole program).
                links = {'documentId', 'document', 'before', 'after', 'event', 'message',
                    'source', 'initialDocument', 'mandate', 'guarantee', 'attestation',
                    'timeline', 'actor', 'onBehalfOf', 'processing', 'previous',
                    'sourcePosition', 'lastEntry', 'prevEntry', 'operation'}
                if key in links and self.blue.head(operand).value is L.ABSENT:
                    result[key] = {'blueId': self.blue.identity(operand)}
                else:
                    result[key] = self._values(operand, seen)
        return result

    def link(self, identity, field, *, optional=False):
        child = self.operand(identity, field)
        if child is None:
            require(optional, 'MISSING_PROTOCOL_FIELD', field=field)
            return None
        return self.blue.identity(child)

    def operand(self, identity, field):
        """The selected exact operand, without contextual field requirements.

        A slot's `schema.required` applies to admission; it must not be folded
        into a signed Timeline's identity. Inherited authored operands remain
        supported, but declaration holes in the protocol catalogue are absent.
        """
        node, seen = L.Ref(identity), set()
        standard = set(self.types.values())
        while node is not None:
            bid = self.blue.identity(node)
            if bid in seen or bid in standard:
                return None
            seen.add(bid)
            body = self.blue.open(node)
            value = body.get(field)
            if value is not L.ABSENT:
                return value
            parent = body.get('type')
            node = parent if isinstance(parent, (L.Node, L.Ref)) else None
        return None

    def links(self, identity, field):
        child = self.operand(identity, field)
        require(child is not None and self.blue.head(child).items is not None, 'INVALID_PROTOCOL_LIST', field=field)
        body = self.blue.open(child)
        items = body.get('items')
        require(isinstance(items, tuple), 'INVALID_PROTOCOL_LIST', field=field)
        return tuple(self.blue.identity(item) for item in items)

    def timeline(self, identity):
        row = self.read(identity, 'Signed Timeline')
        key = row['publicKey']
        require(type(key) is str and len(key) == 64 and all(c in '0123456789abcdef' for c in key), 'INVALID_PUBLIC_KEY')
        return row

    def actor(self, identity):
        node = L.Ref(identity)
        name = 'Principal Actor' if self.is_type(node, 'Principal Actor') else 'Agent Actor'
        return self.read(identity, name)

    def entry(self, identity):
        row = self.read(identity, 'Timeline Entry')
        timeline, actor, message = (self.link(identity, k) for k in ('timeline', 'actor', 'message'))
        self.timeline(timeline)
        self.actor(actor)
        request = operation_request(self.processor.registry, L.Ref(message))
        operation = self.link(identity, 'operation', optional=True)
        require(operation == (message if request is not None else None), 'ENTRY_OPERATION_MISMATCH')
        source = self.link(identity, 'source', optional=True)
        if source:
            require(self.is_type(L.Ref(source), 'Source'), 'INVALID_SOURCE_TYPE')
        authority = self.link(identity, 'onBehalfOf', optional=True)
        if authority:
            require(self.is_type(L.Ref(authority), 'Authority'), 'INVALID_AUTHORITY_TYPE')
        return Entry(identity, timeline, uint(row['timestamp']), actor, message,
                     self.link(identity, 'prevEntry', optional=True), authority, source)

    def validate(self, identity, name):
        """Schema admission plus protocol cross-field rules (not proof trust)."""
        row = self.read(identity, name, closed=name not in ('Mandate/Mandate', 'Mandate/Operation Mandate'))
        suffix = name.split('/')[-1]
        if suffix == 'Timeline Entry':
            self.entry(identity)
        elif suffix == 'Signed Timeline':
            self.timeline(identity)
        elif suffix == 'Processing Receipt':
            kind = row['kind']
            event = self.link(identity, 'event', optional=True)
            has_sources = self.operand(identity, 'sourceReceipts') is not None
            has_attachment = self.operand(identity, 'attachment') is not None
            require((event is not None) == ('eventTimestamp' in row), 'INVALID_RECEIPT_CAUSE')
            if kind == 'INITIALIZE':
                require(event is None and not has_sources and not has_attachment, 'INVALID_RECEIPT_KIND')
            elif kind == 'PROCESS':
                require(event is not None and not has_sources and not has_attachment, 'INVALID_RECEIPT_KIND')
            else:
                require(has_sources and bool(row.get('sourceReceipts')) and has_attachment, 'INVALID_RECEIPT_KIND')
            if event:
                require(self.entry(event).timestamp == row['eventTimestamp'], 'RECEIPT_TIMESTAMP_MISMATCH')
            for field in ('emitted',):
                require([e['ordinal'] for e in row[field]] == list(range(len(row[field]))), 'INVALID_EMISSION_ORDINALS')
        elif suffix == 'History Position':
            previous = self.link(identity, 'previous', optional=True)
            require((row['position'] == 0) == (previous is None), 'INVALID_HISTORY_PREDECESSOR')
            if previous:
                prior = self.read(previous, 'History Position')
                require(prior['position'] + 1 == row['position'], 'NONCONTIGUOUS_HISTORY')
                require(self.link(previous, 'documentId') == self.link(identity, 'documentId'), 'HISTORY_LINEAGE_MISMATCH')
                require(row['epoch'] == prior['epoch'] + int(row['stable']), 'INVALID_EPOCH_INCREMENT')
        elif suffix == 'Order Key':
            entry = self.entry(self.link(identity, 'entry'))
            require(entry.timeline == self.link(identity, 'timeline') and entry.timestamp == row['timestamp'], 'ORDER_KEY_MISMATCH')
        return deepcopy(row)
