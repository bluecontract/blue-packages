"""Executable demand-edition algorithms; not the legacy whole Contracts engine.

The pinned Language owns exact identity, contextual Recipes and validation.
Coverage is reported separately from execution success by the reference runner.
"""
from collections import Counter
from algorithms import blue as L


class Obligations:
    def __init__(self, context):
        self.context = context
        self.success = {}
        self.charges = Counter()
        self.manifests = set()

    def require(self, recipe, kind, coverage='selected', ancestors=()):
        for ancestor in ancestors:
            self.require(ancestor, 'container')
        key = (recipe.key(), kind, coverage)
        if key in self.success:
            self.charges['validationProofReused'] += 1
            return self.success[key]
        if kind not in {'container', 'event', 'definition', 'value'}:
            raise ValueError('UNSUPPORTED_OBLIGATION:' + kind)
        if kind in {'container', 'event'}:
            for part in recipe.parts:
                body = self.open(part)
                if body.has('type'):
                    self.charges['typeEdgeFollowed'] += 1
            result = L.head(recipe, self.context)
            if kind == 'container':
                L.require(result.kind == 'object' or result.kind == 'list' and result.items is not None,
                          'InvalidNodeShape', 'required container')
            for part in recipe.parts:
                body = L.open_exact(part, self.context)
                for field in ('type', 'specification', 'itemType', 'keyType', 'valueType'):
                    definition = body.get(field)
                    if definition is not L.ABSENT:
                        self.require(L.recipe(definition), 'definition')
            for definition in (result.type_id, result.item_type, result.key_type, result.value_type):
                if definition:
                    self.require(L.recipe(L.Ref(definition)), 'definition')
            if result.specification:
                self.require(L.recipe(result.specification), 'definition')
            predicates = L.describe_constraints(result.constraints)
            self.charges['schemaPredicateEvaluated'] += len(predicates)
            if result.key_type:
                self.require(recipe, 'value')
            elif predicates:
                # The container role is an already-required root occurrence. Native
                # presence for optional occurrences is outside this model boundary.
                presence_only = (kind == 'container' and result.kind == 'object'
                    and set(predicates) == {'required'}
                    and type(predicates['required']) is bool)
                if not presence_only:
                    L.validate_schema(result, True, 'value', True, self.context)
        else:
            pending = {}
            if kind == 'definition':
                seen = set()
                for part in (*recipe.parts, *(L.Ref(t) for t in recipe.requirements)):
                    self.definition(part, seen)
            else:
                self.visit(recipe, set(), pending, coverage)
            exact = L.recipe_exact_value(recipe, self.context)
            L.strict_certify(exact, self.context, kind)
            result = L.validate(recipe, self.context, kind)
            self.success.update(pending)
        self.success[key] = result
        return result

    def open(self, node):
        identity = L.identity(node)
        if identity not in self.manifests:
            self.charges['nodeManifestOpened'] += 1
            self.manifests.add(identity)
        return L.open_exact(node, self.context)

    def definition(self, node, seen):
        identity = L.identity(node)
        if identity in seen:
            return
        seen.add(identity)
        body = self.open(node)
        for name, value in body.fields:
            if isinstance(value, (L.Node, L.Ref)):
                self.charges['typeEdgeFollowed' if name in L.TYPES else 'objectMemberRead'] += 1
                self.definition(value, seen)
            elif name == 'items':
                for child in value:
                    self.charges['listItemRead'] += 1
                    self.definition(child, seen)

    def compare(self, left, right):
        self.charges['scalarComparison'] += 1
        if isinstance(left, str) and isinstance(right, str):
            for offset in range(0, min(len(left), len(right)), 64):
                self.charges['textBlockExamined'] += 2
                a, b = left[offset:offset+64], right[offset:offset+64]
                if a != b:
                    return (a > b) - (a < b)
        return (left > right) - (left < right)

    def visit(self, recipe, seen, pending, coverage):
        if recipe.key() in seen:
            return
        head = L.head(recipe, self.context)
        key = (recipe.key(), 'value', coverage)
        if key in self.success or key in pending:
            self.charges['validationProofReused'] += 1
            return
        seen = seen | {recipe.key()}
        for part in recipe.parts:
            self.open(part)
        constraints = head.constraints
        self.charges['schemaPredicateEvaluated'] += len(L.describe_constraints(constraints))
        value = head.value
        if value is not L.ABSENT:
            if type(value) in (int, float):
                for bound in (constraints.lower, constraints.upper):
                    if bound:
                        self.compare(value, bound.value)
                if constraints.multiple is not None:
                    self.charges['scalarComparison'] += 1
                    if type(value) is int:
                        self.charges['integerLimbOperation'] += max(1, (abs(value).bit_length()+31)//32) * max(1, (abs(constraints.multiple.numerator).bit_length()+31)//32)
            elif isinstance(value, str) and constraints.counts:
                self.charges['textBlockExamined'] += (len(value)+63)//64
                for count in constraints.counts.values():
                    self.compare(len(value), count)
            if constraints.enum:
                for group in constraints.enum:
                    for alternative in group:
                        self.charges['validationMemberExamined'] += 1
                        _, _, other = constraints.enum_values[alternative]
                        if type(value) is type(other) and self.compare(value, other) == 0:
                            break
        for name in L.ordered(head.fields):
            self.charges['objectMemberRead'] += 1
            if head.value_type or head.key_type:
                self.charges['validationMemberExamined'] += 1
            self.visit(L.child_recipe(head, name), seen, pending, coverage)
        if head.items is not None:
            for count in constraints.counts.values():
                self.compare(len(head.items), count)
            for index in range(len(head.items)):
                self.charges['listItemRead'] += 1
                if head.item_type or constraints.unique:
                    self.charges['validationMemberExamined'] += 1
                self.visit(L.child_recipe(head, index), seen, pending, coverage)
        if head.contracts is not None:
            self.visit(head.contracts, seen, pending, coverage)
        pending[key] = head


def externalized_proof(identity, proof, context):
    """Re-encode verified owning members through unchanged native finalization."""
    def child(value):
        if isinstance(value, (L.Ref, L.Local)):
            return value
        return shallow(value) if L.locals_in(value) else L.Ref(L.identity(value))

    def shallow(body):
        fields = {}
        for name, value in body.fields:
            if name in L.LITERALS | {'mergePolicy'}:
                fields[name] = value
            elif name == 'items':
                fields[name] = tuple(child(item) for item in value)
            else:
                fields[name] = child(value)
        return L.node(fields)

    members = [L.export_tree(shallow(L.normalize(row, context, symbolic=True)))
               for row in proof['members']]
    rebuilt = L.finalize_set(members, context)
    master = identity.split('#')[0]
    L.require(rebuilt['ids'] == [master+'#'+str(i) for i in range(len(members))],
              'InvalidCyclicProof', 'externalization changed owning identities')
    return {'members': [L.export_tree(row) for row in rebuilt['canonical']]}


def prepare_records(obligations, context, public_records=()):
    """Prepare exact records for explicit successful role edges, then cold verify.

    Each row is (node, role, purpose, required_children). Deriving these rows from
    the complete Contracts graph is a separate, currently unqualified boundary.
    """
    pending = list(obligations)
    seen, records = set(), {}
    while pending:
        node, role, purpose, children = pending.pop(0)
        identity = L.identity(node)
        key = (identity, role, purpose)
        if key in seen:
            continue
        seen.add(key)
        body = L.open_exact(node, context)
        fields = {}
        for name, value in body.fields:
            if name == 'items':
                fields[name] = tuple(L.Ref(L.identity(item)) for item in value)
            elif name in L.LITERALS | {'mergePolicy'}:
                fields[name] = value
            else:
                fields[name] = L.Ref(L.identity(value))
        shallow = L.node(fields)
        if '#' in identity:
            L.require(identity in context.proofs, 'InvalidCyclicProof', 'owning proof missing')
            record = {'proof': L.wire_text(externalized_proof(identity, context.proofs[identity], context)),
                      'body': L.wire_text(L.export_tree(shallow))}
        else:
            L.require(L.identity(shallow) == identity, 'IdentityMismatch', 'shallow body')
            record = {'mode': 'exact', 'text': L.wire_text(L.export_tree(shallow))}
        if identity not in L.CORE_NAME:
            records[identity] = record
        pending.extend(children)
    checking = L.Context(provider={**dict(public_records), **records})
    for identity in sorted(records):
        L.open_exact(L.Ref(identity), checking)
    return records


class Publication:
    """Reference atomic publication state, not a real completion capability issuer."""
    def __init__(self, public_records=()):
        self.records = dict(public_records)
        self.archive = {}
        self.completions = {}

    def commit(self, identity, prepared_records, sealed_result):
        # Validate against the latest shared state; never restore the begin snapshot.
        records = {**self.records, **prepared_records}
        # Equal exact identities can have distinct inline/reference encodings.
        # Verify the proposed bytes natively instead of comparing transport maps.
        checking = L.Context(provider=records)
        for key in prepared_records:
            L.open_exact(L.Ref(key), checking)
        archive = {**self.archive, identity: sealed_result}
        completions = {**self.completions, identity: sealed_result}
        self.records, self.archive, self.completions = records, archive, completions


def execute_vector(vector):
    """Independent JSON input shared with the Java primitive conformance test."""
    from blue_language import Language
    context = Language(core_contracts=False).processing_context()
    if vector['supplyPrivate']:
        private = L.scalar('Integer', 42)
        context.provider[L.identity(private)] = {'mode': 'exact', 'text': L.wire_text(L.export_tree(private))}
    root = L.normalize(vector['root'], context)
    obligations = Obligations(context)
    result = {'id': vector['id'], 'rootBlueId': L.identity(root)}
    try:
        parent = L.recipe(root)
        head = obligations.require(parent, 'container')
        selected = L.child_recipe(head, vector['path'])
        # A selected read requires its ancestor even after a previous header read.
        obligations.charges['objectMemberRead'] += 1
        obligations.require(selected, 'value', ancestors=(parent,))
        result['outcome'] = 'ESTABLISHED'
        result['valueBlueId'] = L.recipe_exact_id(selected, context)
        records = prepare_records([(root, 'structural', 'restore', ((L.recipe_exact_value(selected, context), 'value', 'consumed', ()),))], context)
        result['records'] = records
    except L.Failure as failure:
        # The public Contracts boundary maps native content demand to NEEDS_RESOURCES.
        # Keep exact required identities; invalid native failures retain their category.
        result['outcome'] = 'NEEDS_RESOURCES' if failure.category == 'ProviderUnavailable' else 'LANGUAGE_' + failure.category
        if failure.category == 'ProviderUnavailable':
            result['required'] = [L.final_id(failure.detail)]
    result['charges'] = dict(sorted((k, v) for k, v in obligations.charges.items() if v))
    return result


BODY_FIELDS = {
    'workflow': frozenset({'steps'}),
    'operation': frozenset({'steps'}),
    'compute': frozenset({'expr', 'do', 'constants', 'functions', 'entry', 'definition'}),
    'compute-definition': frozenset({'constants', 'functions'}),
    'patch-step': frozenset({'changeset'}),
    'emit-step': frozenset({'event'}),
    'terminate-step': frozenset({'cause', 'reason'}),
}


def declaration_edges(kind, fields, body_reads=(), extension_policy=None, extension_selected=False):
    """§12.4 selection; field legality/requiredness remain native header checks.

    An extension policy must come from the exact installed catalogue, never the
    authored document. `body_reads` are actual consumer reads, not availability.
    """
    if kind in BODY_FIELDS:
        body = BODY_FIELDS[kind]
    elif extension_policy is not None:
        header, body = map(frozenset, extension_policy)
        if header & body or not set(fields) <= header | body:
            raise ValueError('INVALID_EXTENSION_POLICY')
        if extension_selected:
            body_reads = body & set(fields)
    else:
        raise ValueError('UNSUPPORTED_HANDLER_ROLE')
    if not set(body_reads) <= body & set(fields):
        raise ValueError('UNDECLARED_BODY_READ')
    edges = []
    for name in L.ordered(fields):
        if name not in body:
            edges.append((name, 'definition' if name in L.TYPES or name == 'specification' else 'header'))
        elif name in body_reads:
            edges.append((name, 'value'))
        elif name == 'steps' and kind in {'workflow', 'operation'}:
            edges.append((name, 'list-shape'))
    return tuple(edges)


def check_snapshot_envelope(package, expected, release, bindings, public_records=()):
    """Independent cold-envelope precondition; not a managed graph admission.

    Reuses the unchanged snapshot digest/closed-record codec. Native managed
    declarations, initialized markers and channel signatures remain Java
    composition checks; this function does not issue a restored Snapshot.
    """
    from blue_contracts.reference.model import closed, digest, require, integer, token, segments
    closed(package, {'snapshot', 'identity', 'content'})
    require(package['identity'] == expected, 'UNTRUSTED_SNAPSHOT_COMMITMENT')
    wire = closed(package['snapshot'], {'root', 'documents', 'edges', 'generation', 'revision', 'release', 'runtimes'})
    require(digest('contracts.snapshot/completion-1', wire) == expected, 'INVALID_SNAPSHOT_COMMITMENT')
    require(wire['release'] == release and wire['runtimes'] == bindings, 'INCOMPATIBLE_RUNTIME_BINDINGS')
    integer(wire['generation']); integer(wire['revision'])
    checking = L.Context(provider={**dict(public_records), **package['content']})
    obligations = Obligations(checking)
    members = {}
    for row in wire['documents']:
        closed(row, {'key', 'blueId', 'channels', 'channelSerials', 'edgeSerials', 'birth'})
        key = token(row['key'])
        require(key not in members, 'DUPLICATE_DOCUMENT_KEY')
        root = L.Ref(L.final_id(row['blueId']))
        L.open_exact(root, checking)
        obligations.require(L.recipe(root), 'container')
        for name, life in row['channels'].items():
            token(name); closed(life, {'generation', 'signature'})
            integer(life['generation'], 1); require(isinstance(life['signature'], str), 'INVALID_CHANNEL_SIGNATURE')
        for counters in (row['channelSerials'], row['edgeSerials']):
            for name, generation in counters.items():
                token(name); integer(generation, 1)
        if row['birth'] is not None:
            token(row['birth'])
        members[key] = root
    require(wire['root'] in members, 'MISSING_ROOT')
    seen = set()
    for edge in wire['edges']:
        closed(edge, {'source', 'path', 'target', 'generation'})
        integer(edge['generation'], 1)
        key = (edge['source'], edge['path'])
        require(key not in seen, 'DUPLICATE_EDGE'); seen.add(key)
        require(edge['source'] in members and edge['target'] in members, 'MISSING_EDGE_MEMBER')
        found = L.exact_at(members[edge['source']], segments(edge['path']), checking)
        require(isinstance(found, (L.Node, L.Ref)) and L.identity(found) == members[edge['target']].id,
                'INVALID_EDGE_IDENTITY')
    return {'identity': expected, 'members': tuple(sorted(members)),
            'qualification': 'ENVELOPE_ONLY'}


def check_result_observations(observations, receipt, before, after, event, timestamp, gas_policy, release):
    """Independent result postcondition, never local-completion authentication."""
    from blue_contracts.reference.model import digest, require, integer
    require(digest('contracts.result/completion-1', observations) == receipt, 'INVALID_RECEIPT')
    require(observations['input'] == before, 'INPUT_MISMATCH')
    require(observations['output'] == after, 'OUTPUT_MISMATCH')
    integer(observations['gas'])
    require(observations['invocation'] == digest('contracts.invocation/completion-1',
            {'input': before, 'event': event, 'timestamp': timestamp, 'gas': gas_policy, 'release': release}), 'CAUSE_MISMATCH')
    if observations['status'] != 'APPLIED':
        require(after == before, 'FAILED_ATTEMPT_PUBLISHED_STATE')
    return {'receipt': receipt, 'qualification': 'OBSERVATIONS_ONLY'}
