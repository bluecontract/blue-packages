"""Granular exact content, execution bundles and on-demand dependency reads.

Only trusted engine heads can use the local restore path. Uploaded/foreign
marked documents must establish initialization and replay separately.
"""
from collections import OrderedDict
from collections.abc import MutableMapping
from dataclasses import fields
from copy import deepcopy, copy
from algorithms import blue as L
from blue_language import MemoryProvider
from blue_language.prepared import PreparedLanguage
from blue_contracts.reference.model import Snapshot, Document, Edge, ChannelLife, require, pointer
from blue_contracts.reference.graph import Graph

_REFERENCE_OPEN = L.open_exact


class _RememberWrites(MutableMapping):
    def __init__(self, target): self.target, self.writes = target, {}
    def __getitem__(self, key): return self.target[key]
    def __setitem__(self, key, value):
        self.target[key] = value; self.writes[key] = value
    def __delitem__(self, key): del self.target[key]
    def __iter__(self): return iter(self.target)
    def __len__(self): return len(self.target)


class ExactBodyCache:
    """Physical parsing evidence, not a validation or authorization result.

    Successful exact opens bind the complete original response and all limits.
    Reuse repeats fetch/step effects and remembered bodies. Near a rejection
    boundary, Source envelopes and cyclic proofs always use the reference.
    Retention is bounded by 8,192 records and 8 MiB of serialized evidence.
    Independent entry and byte budgets avoid the old small-record working-set
    cliff. Reuse still fetches and compares provider evidence on every new scope.
    """
    def __init__(self, *, capacity=8192, byte_limit=8*1024*1024):
        if type(capacity) is not int or type(byte_limit) is not int or min(capacity,byte_limit)<0:
            raise ValueError('nonnegative cache bounds required')
        self.capacity,self.byte_limit=capacity,byte_limit
        self.rows=OrderedDict();self.bytes=0;self.hits=0;self.misses=0;self.evictions=0

    def open(self, node, context, response):
        limits=tuple(getattr(context.limits, field.name) for field in fields(context.limits))
        key=(node.id, response['text'], response.get('format','json'), limits)
        old=self.rows.get(key)
        if old is not None and L.within(context.work+old['steps'],context.limits.steps) and L.within(len(context.demands)+1,context.limits.fetches):
            context.step();L.final_id(node.id);context.demands.append(node.id)
            context.work+=old['steps']-1
            context.bodies.update(old['remember'])
            self.rows.move_to_end(key);self.hits+=1
            return old['body']
        self.misses+=1
        before=context.work;original=context.bodies
        recorder=_RememberWrites(original);context.bodies=recorder
        try:body=_REFERENCE_OPEN(node,context)
        finally:context.bodies=original
        size=len(response['text'].encode('utf-8'))
        if size<=self.byte_limit and self.capacity:
            if old is not None:self.bytes-=old['size']
            self.rows[key]=dict(body=body,remember=recorder.writes,steps=context.work-before,size=size)
            self.bytes+=size
            while len(self.rows)>self.capacity or self.bytes>self.byte_limit:
                _,row=self.rows.popitem(last=False);self.bytes-=row['size'];self.evictions+=1
        return body


def _exact_open(node, context):
    cache=getattr(context,'_engine_exact_bodies',None)
    if cache is not None and type(node) is L.Ref and node.body is None and '#' not in node.id and node.id not in context.bodies:
        response=context.provider.get(node.id)
        if (type(response) is dict and set(response)<={'text','mode','format'} and
                type(response.get('text')) is str and type(response.get('format','json')) is str and
                response.get('mode','exact')=='exact'):
            return cache.open(node,context,response)
    return _REFERENCE_OPEN(node,context)


L.open_exact=_exact_open


def mount_business_repository(language, repository):
    """Keep business content available without replacing this engine's roles.

    The prepared repository retains all original records and BlueIds. Only its
    legacy protocol nicknames are excluded from this host's authoring aliases;
    executable types must come from the selected runtime catalogue.
    """
    from blue_language.prepared import PreparedRepository
    aliases = {name: identity for name, identity in repository.aliases.items()
               if not name.startswith(('Coordination/', 'Mandate/', 'Contracts/'))}
    if isinstance(repository, PreparedRepository):
        language.enable_repository(repository, aliases=False)
        for name, identity in aliases.items():
            prior = language.aliases.get(name, L.CORE.get(name))
            require(prior is None or prior == identity, 'REPOSITORY_ALIAS_CONFLICT', alias=name)
        language.aliases.update(aliases)
    else:
        from blue_repository import Repository
        language.enable_repository(Repository.from_payload(repository.name + '-business', aliases,
            repository.records, metadata=repository.metadata))


class TrackedProvider(MemoryProvider):
    def __init__(self):
        super().__init__()
        self.dirty = {}
        self.retention_generation = 0

    def set_response(self, identity, response):
        previous=self._records.get(identity)
        if previous == response or (previous is not None and
                {'format':'json','mode':'exact',**previous} == {'format':'json','mode':'exact',**response}):return
        if previous is not None:self.retention_generation += 1
        super().set_response(identity, response)
        self.dirty[identity] = deepcopy(response)

    def merge_responses(self, records):
        # The public provider API retains immutable evidence. A merge does not
        # copy the full provider or publish a process head.
        for identity, response in records.items():
            self.set_response(identity, response)

    def acknowledge(self):
        self.dirty.clear()
        if hasattr(self,'admissions'):self.admissions.dirty.clear()

    def snapshot(self):
        # Context construction is trusted read-only code. Responses are replaced,
        # never mutated by this provider; the captured outer map is detached.
        if getattr(self,'_context_capture',False):return dict(self._records)
        return super().snapshot()


class DemandMap(dict):
    def __init__(self, initial, language):
        super().__init__(initial)
        self.language = language
        self.view = language.view  # Never switch a captured value to a later read scope.

    def _fetch(self, key):
        view = self.view
        if view is None:
            return
        response = view.get('content', key)
        self.language.metrics['dynamicReads'] += 1
        if response is not None:
            # This is evidence, not trusted admission. Language verifies IDs.
            super().__setitem__(key, response)

    def __contains__(self, key):
        if not super().__contains__(key):
            self._fetch(key)
        return super().__contains__(key)

    def __getitem__(self, key):
        if not super().__contains__(key):
            self._fetch(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        if key not in self:
            return default
        return super().__getitem__(key)


class StoreLanguage(PreparedLanguage):
    def __init__(self, *, reuse_admission=True):
        self.reuse_admission=reuse_admission
        self.view = None
        self.exact_bodies = ExactBodyCache()
        self.metrics = dict(dynamicReads=0, bundleReads=0, bodyRecords=0)
        self._retained = OrderedDict()
        self._retention_generation = 0
        self._retention_store = None
        super().__init__(TrackedProvider())
        from .admission_evidence import AdmissionEvidence
        self.admissions=AdmissionEvidence(self)
        self.provider.admissions=self.admissions

    def certify_context(self, node, context, goal='value'):
        if not self.reuse_admission:
            L.strict_certify(node,context,goal)
            if goal=='value':self.admissions.issue(node)
            return
        return self.admissions.certify(node,context,goal)

    def retained_records(self, node, context):
        """Delta retention over closures already retained by this host.

        This runs AFTER admission. It does not supply validation evidence or
        skip a required open. The immutable dependency records remain owned by
        this provider; replacing evidence invalidates the retention inventory.
        """
        if self._retention_generation != self.provider.retention_generation:
            self._retained.clear()
        records={};seen=set();pending=[node]
        while pending:
            value=pending.pop();identity=L.identity(value);context.step()
            if identity in seen or identity in self._retained:continue
            # A cold worker need not copy a closure already atomically retained
            # in this store. The protected value-admission record establishes
            # that closure; arbitrary uploaded content cannot assert it.
            if (self.reuse_admission and self.view is not None and '#' not in identity and
                    self.view.get('language_admissions',identity) is not None):
                self.admissions.lookup(identity)  # Validate the protected row.
                require(self.view.get('content',identity) is not None,'CORRUPT_RETAINED_CONTENT',blueId=identity)
                seen.add(identity)
                continue
            seen.add(identity);body=L.open_exact(value,context)
            if identity not in L.CORE_NAME:
                records[identity]=({'proof':L.wire_text(context.proofs[identity]),'body':L.export_exact(body,context)}
                    if '#' in identity else {'text':L.export_exact(body,context),'mode':'exact'})
            for key,child in body.fields:
                if key=='items':
                    payload=L.list_node(child);pid=L.identity(payload)
                    records[pid]={'text':L.export_exact(payload,context),'mode':'exact'}
                    pending.extend(child)
                elif key not in L.LITERALS|{'mergePolicy'}:pending.append(child)
        def prefixes(wire):
            if isinstance(wire,list):
                for item in wire:prefixes(item)
            elif isinstance(wire,dict):
                if set(wire)=={'$previous'}:
                    identity=wire['$previous']['blueId']
                    records[identity]={'text':L.export_exact(L.payload_body(identity,context),context),'mode':'exact'}
                else:
                    for item in wire.values():prefixes(item)
        prefixes(L.canonical_wire(node,context))
        self.provider.merge_responses(records)
        self._retention_generation=self.provider.retention_generation
        for identity in seen:self._retained[identity]=True
        while len(self._retained)>65536:self._retained.popitem(last=False)
        return records

    def processing_context(self):
        provider=self.provider
        captured=copy(provider);captured._context_capture=True
        self.provider=captured
        try:context = super().processing_context()
        finally:self.provider=provider
        context.provider = DemandMap(context.provider, self)
        context._engine_exact_bodies = self.exact_bodies
        return context

    def bind(self, view):
        if view is not None and view.store is not self._retention_store:
            self._retained.clear()
            self._retention_store=view.store
        self.view = view
        self.admissions.bind(view)

    def publish_document(self, document):
        identity = super().publish_document(document)
        # SDK publication swaps its provider state atomically; track the issued
        # handle's public dependency evidence without reading private storage.
        self.provider.dirty.update(document.dependency_responses())
        if document.goal=='value':self.admissions.issue(L.Ref(document.blue_id))
        return identity

    def prefetch(self, identities):
        require(self.view is not None, 'MISSING_CONTENT_READ_VIEW')
        records = self.view.get_many('content', identities)
        self.metrics['bundleReads'] += 1
        present = {k: v for k, v in records.items() if v is not None}
        self.metrics['bodyRecords'] += len(present)
        self.provider.merge_responses(present)


def rooted(processor, state, member):
    result = state.copy()
    result.root = member
    members = Graph(result, processor.registry, processor.archive).reachable()
    result.documents = {k: v for k, v in result.documents.items() if k in members}
    result.edges = {k: e for k, e in result.edges.items() if e.source in members}
    return result


def restore_local(processor, wire):
    """Restore an internally published head, not a user-supplied snapshot."""
    require(wire['release'] == processor.registry.specification, 'INCOMPATIBLE_RELEASE')
    require(tuple(wire['runtimes']) == processor.registry.runtime_bindings, 'INCOMPATIBLE_RUNTIME_BINDINGS')
    documents = {}
    for row in wire['documents']:
        documents[row['key']] = Document(row['key'], L.Ref(row['blueId']), row['blueId'],
            {k: ChannelLife(**v) for k, v in row['channels'].items()},
            dict(row['channelSerials']), dict(row['edgeSerials']), row['birth'])
    edges = {(r['source'], r['path']): Edge(**r) for r in wire['edges']}
    state = Snapshot(wire['root'], documents, edges, wire['generation'], wire['revision'], wire['release'], tuple(wire['runtimes']))
    processor.validate(state)
    processor.archive.add(state)
    return state


def prepare_content(processor, state, view):
    """Split changed exact bodies; return actual read bundles per managed root.

    All declaration headers and ordinary handlers are retained. Operation bodies
    are indexed by their exact declaration, not trusted by their friendly name.
    Cyclic members retain their owning-set evidence and use the lower oracle.
    """
    blue = processor.blue
    indexes = {}
    existing = view.get_many('execution_index', [d.blue_id for d in state.documents.values()])
    writes = {}
    for key, document in sorted(state.documents.items()):
        if existing[document.blue_id] is not None:
            indexes[key] = existing[document.blue_id]
            continue
        body = blue.open(document.body)
        paths = {e.path for e in state.edges.values() if e.source == key}
        contracts = body.get('contracts')
        if isinstance(contracts, L.Node):
            for name, declaration in contracts.fields:
                if isinstance(declaration, L.Node):
                    paths.add(pointer(('contracts', name)))
                    if declaration.has('steps'):
                        paths.add(pointer(('contracts', name, 'steps')))
        if '#' not in document.blue_id and paths:
            selected = []
            for path in sorted(paths):
                try:
                    value = L.exact_at(body, L.path_parts(path), blue.context)
                except L.Failure:
                    continue
                if isinstance(value, L.Node):
                    selected.append(path)
            if selected:
                projected, records = L.split_fragments(body, selected, blue.context)
                require(blue.identity(projected) == document.blue_id, 'COLLAPSE_IDENTITY_MISMATCH')
                for node in records.values():
                    blue.remember(node)
                blue.remember(projected)
                document.body = projected
        declarations = processor.registry.contracts(document.body)
        common = {document.blue_id}
        operations = {}
        for name, declaration in declarations.items():
            exact = blue.exact(declaration['_recipe'])
            identity = blue.identity(exact)
            blue.remember(exact)
            common.add(identity)
            steps = blue.child(declaration['_recipe'], 'steps')
            if steps is not None:
                program = blue.exact(steps)
                program_id = blue.identity(program)
                blue.remember(program)
                if declaration['_role'] == 'operation':
                    operations[name] = dict(declaration=identity, bodies=[program_id])
                else:
                    common.add(program_id)
        from blue_contracts.reference.registry import EXTERNAL
        observers=any(d['_role'] in ('workflow','extension_handler') and
            d['channel'] in declarations and declarations[d['channel']]['_role'] in EXTERNAL
            for d in declarations.values())
        indexes[key] = dict(common=sorted(common), operations=operations,ordinaryObservers=observers)
        writes['execution_index', document.blue_id] = indexes[key]
    return indexes, writes


def content_writes(provider, view):
    """Insert only new immutable evidence; never overwrite published content."""
    records = dict(provider.dirty)
    existing = view.get_many('content', records)
    writes = {('content', key): row for key, row in records.items() if existing[key] is None}
    admissions=getattr(provider,'admissions',None)
    if admissions is not None:
        old=view.get_many('language_admissions',admissions.dirty)
        for identity,row in admissions.dirty.items():
            require(old[identity] is None or old[identity]==row,'CONFLICTING_LANGUAGE_ADMISSION')
            if old[identity] is None and (('content',identity) in writes or
                    existing.get(identity) is not None or view.get('content',identity) is not None):
                writes['language_admissions',identity]=row
    return writes


def cache_declarations(processor, capacity=512):
    """Reuse exact unchanged declaration recipes; business state stays separate."""
    from blue_contracts.reference.registry import MARKERS
    from blue_contracts.reference.model import token, LIMITS
    original = processor.registry.contracts
    cache = OrderedDict()
    indexed = OrderedDict()
    declaration = processor.registry.declaration
    prepared = OrderedDict()
    metrics = dict(mapHits=0, mapMisses=0, declarationHits=0, declarationMisses=0)
    processor.declaration_cache_metrics = metrics

    def cached_declaration(recipe, *, demand=True):
        key = (L.recipe(recipe).key(), demand, tuple(processor.registry.extensions))
        if key not in prepared:
            metrics['declarationMisses'] += 1
            prepared[key] = declaration(recipe, demand=demand)
            while len(prepared) > capacity:prepared.popitem(last=False)
        else:
            metrics['declarationHits'] += 1
            prepared.move_to_end(key)
        return dict(prepared[key])

    processor.registry.declaration = cached_declaration

    def contracts(body):
        head = processor.blue.head(body)
        if head.contracts is None:
            return {}
        # First index an exact full map (including markers and contextual
        # requirements). Repeated calls for that same immutable map need not
        # walk every unused declaration just to form the reusable code key.
        full_key = (head.contracts.key(), tuple(processor.registry.extensions))
        key = indexed.get(full_key)
        if key is None:
            ch = processor.blue.head(head.contracts)
            require(ch.kind in ('object','none'), 'INVALID_CONTRACT_MAP')
            recipes = []
            for name in sorted(ch.fields):
                token(name)
                recipe = L.child_recipe(ch, name)
                if name in MARKERS:
                    require(processor.registry.role(recipe) == MARKERS[name], 'INVALID_PROCESSOR_STATE', key=name)
                else:
                    recipes.append((name, recipe.key()))
            # New marker values are checked, while unchanged declarations
            # retain their preparation across different full map identities.
            key = (tuple(recipes), tuple(processor.registry.extensions))
            indexed[full_key] = key
            while len(indexed) > capacity:indexed.popitem(last=False)
        else:
            indexed.move_to_end(full_key)
        if key not in cache:
            metrics['mapMisses'] += 1
            cache[key] = original(body)
            while len(cache) > capacity:
                cache.popitem(last=False)
        else:
            metrics['mapHits'] += 1
            cache.move_to_end(key)
        # Callers must not mutate shared headers or template containers.
        return {name: dict(value) for name, value in cache[key].items()}

    processor.registry.contracts = contracts
    return cache
