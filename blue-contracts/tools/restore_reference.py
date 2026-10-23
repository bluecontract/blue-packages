"""Independent §12.1 structural restoration slice over native contextual Recipes.

Installed catalogue identity/role authentication, envelope commitments and local
completion authority remain native boundaries. Inputs contain documents, never
precomputed obligation lists. Unsupported roles fail explicitly.
"""
import bootstrap
from algorithms import blue as L
from demand_reference import Obligations

ROLES = {'Compute': 'compute', 'Compute Definition': 'compute_definition', 'Process Embedded': 'embedding',
         'Processing Initialized Marker': 'initialized',
         'Channel Event Checkpoint': 'checkpoint'}
BODY = {'compute_definition': {'constants', 'functions'}, 'compute': {'expr', 'do', 'constants', 'functions', 'entry', 'definition'}}


def ensure(condition, code):
    if not condition:
        raise ValueError(code)


def recipe_row(recipe, purpose):
    return {'purpose': purpose, 'parts': [L.identity(n) for n in recipe.parts],
            'requirements': list(recipe.requirements)}


class RestoreObligations(Obligations):
    def __init__(self, context):
        super().__init__(context)
        self.rows = {}

    def require(self, recipe, kind, coverage='selected', ancestors=()):
        if kind == 'optional':
            # Native optional occurrence semantics, not synthetic present/null data.
            result = L.head(recipe, self.context)
            definitions = []
            for part in recipe.parts:
                raw = L.open_exact(part, self.context)
                definitions.extend(raw.get(field) for field in
                    ('type', 'specification', 'itemType', 'keyType', 'valueType')
                    if raw.get(field) is not L.ABSENT)
            definitions.extend(L.Ref(tid) for tid in
                (result.type_id, result.item_type, result.key_type, result.value_type) if tid)
            if result.specification:
                definitions.append(result.specification)
            for definition in definitions:
                self.require(L.recipe(definition), 'definition')
            predicates = L.describe_constraints(result.constraints)
            present = L.present_recipe(recipe, self.context) if predicates or result.key_type else False
            if result.key_type and present:
                self.require(recipe, 'value')
            elif predicates and not (present and result.kind == 'object'
                    and set(predicates) == {'required'} and type(predicates['required']) is bool):
                L.validate_schema(result, present, 'value', False, self.context)
        else:
            result = super().require(recipe, kind, coverage, ancestors)
        row = recipe_row(recipe, 'container' if kind in {'event', 'optional'} else kind)
        self.rows[(tuple(row['parts']), tuple(row['requirements']), row['purpose'])] = row
        return result


def derive_restore_obligations(members, edges, context, installed_types):
    """Return actual selection roots for retention plus validated graph structure.

`members` holds exact native nodes. installed_types is the authenticated installed
catalogue's name→ID map; neither serialized role labels nor claimed successes are
accepted. Paths/ancestors are traversal metadata, never validation certificates.
"""
    roles = {installed_types[name]: role for name, role in ROLES.items()}
    work = RestoreObligations(context)
    selections = []
    paths_by_member = {}

    def observe(member, path, recipe, kind, ancestors=()):
        result = work.require(recipe, kind)
        selections.append({'member': member, 'path': path, **recipe_row(recipe, kind),
                           'ancestors': [recipe_row(r, 'container') for r in ancestors]})
        return result

    def scalar(recipe):
        h = L.head(recipe, context)
        ensure(h.value is not L.ABSENT, 'REQUIRED_SCALAR')
        return h.value

    def role(recipe):
        h = L.head(recipe, context)
        for tid in L.ancestry(h.type_id, context) if h.type_id else ():
            if tid in roles:
                return roles[tid]
        raise ValueError('UNSUPPORTED_CONTRACT_TYPE')

    def select(member, root, path):
        ensure(path.startswith('/') and path != '/', 'INVALID_EMBEDDED_PATH')
        parts = [s.replace('~1', '/').replace('~0', '~') for s in path[1:].split('/')]
        ensure(parts[0] != 'contracts' and all(parts), 'INVALID_EMBEDDED_PATH')
        selected = L.recipe(root)
        ancestors = []
        for index, key in enumerate(parts):
            head = observe(member, '/' + '/'.join(parts[:index]) if index else '', selected, 'optional', ancestors)
            ancestors.append(selected)
            selected = L.child_recipe(head, key)
            if selected is None:
                return None
        observe(member, path, selected, 'optional', ancestors)
        return selected

    for member, node in sorted(members.items()):
        root = L.recipe(node)
        head = observe(member, '', root, 'container')
        ensure(head.items is None and head.value is L.ABSENT, 'PROCESSING_DOCUMENT_NOT_OBJECT')
        paths = []
        if head.contracts is not None:
            table = observe(member, '/contracts', head.contracts, 'container', (root,))
            for name in sorted(table.fields):
                selected = L.child_recipe(table, name)
                declaration = observe(member, '/contracts/' + name, selected, 'container', (root, head.contracts))
                selected_role = role(selected)
                if name in {'initialized', 'checkpoint', 'terminated'}:
                    ensure(name == selected_role, 'INVALID_PROCESSOR_STATE')
                    if name == 'initialized':
                        item = L.child_recipe(declaration, 'document')
                        ensure(item is not None, 'INVALID_PROCESSOR_STATE')
                        observe(member, '/contracts/initialized/document', item, 'event')
                    elif name == 'checkpoint':
                        entries = L.child_recipe(declaration, 'entries')
                        ensure(entries is not None, 'INVALID_PROCESSOR_STATE')
                        rows = observe(member, '/contracts/checkpoint/entries', entries, 'container')
                        for channel in sorted(rows.fields):
                            row = observe(member, '/contracts/checkpoint/entries/' + channel,
                                          L.child_recipe(rows, channel), 'container')
                            ensure(set(row.fields) == {'timestamp', 'event'}, 'INVALID_PROCESSOR_STATE')
                            observe(member, '/contracts/checkpoint/entries/' + channel + '/timestamp', L.child_recipe(row, 'timestamp'), 'value')
                            observe(member, '/contracts/checkpoint/entries/' + channel + '/event', L.child_recipe(row, 'event'), 'event')
                    continue
                ensure(selected_role != 'compute', 'INVALID_CONTRACT_ROLE')
                ensure(selected_role != 'embedding' or name == 'embedded', 'EMBEDDING_KEY')
                allowed = {'compute_definition': BODY['compute_definition'], 'embedding': {'paths', 'collectionPaths'}}[selected_role]
                ensure(set(declaration.fields) <= allowed | {'order', 'specification'}, 'UNKNOWN_RUNTIME_FIELD')
                for field in sorted(declaration.fields):
                    if field == 'specification' or field in BODY.get(selected_role, set()):
                        continue
                    value = L.child_recipe(declaration, field)
                    if L.present_recipe(value, context):
                        observe(member, '/contracts/' + name + '/' + field, value, 'value')
                    else:
                        observe(member, '/contracts/' + name + '/' + field, value, 'optional')
                if name == 'embedded':
                    ensure(selected_role == 'embedding', 'INVALID_EMBEDDING')
                    for field in ('paths', 'collectionPaths'):
                        value = L.child_recipe(declaration, field)
                        if value is None or not L.present_recipe(value, context):
                            continue
                        values = L.head(value, context)
                        ensure(values.items is not None, 'INVALID_EMBEDDED_PATHS')
                        for index in range(len(values.items)):
                            path = scalar(L.child_recipe(values, index))
                            target = select(member, node, path)
                            if target is None:
                                continue
                            if field == 'paths':
                                paths.append(path)
                            else:
                                h = L.head(target, context)
                                ensure(h.items is None and h.value is L.ABSENT and h.kind in {'object', 'none'}, 'EMBEDDED_COLLECTION_NOT_OBJECT')
                                for key in sorted(h.fields):
                                    item_path = path + '/' + key.replace('~', '~0').replace('/', '~1')
                                    observe(member, item_path, L.child_recipe(h, key), 'optional')
                                    paths.append(item_path)
        ensure(len(paths) == len(set(paths)), 'DUPLICATE_EMBEDDED_PATH')
        ensure(not any(a != b and b.startswith(a + '/') for a in paths for b in paths), 'OVERLAPPING_EMBEDDED_PATH')
        paths_by_member[member] = sorted(paths)
        selected_edges = [e for e in edges if e['source'] == member]
        ensure(sorted(e['path'] for e in selected_edges) == sorted(paths), 'INVALID_GRAPH_BINDINGS')
        for edge in selected_edges:
            ensure(edge['target'] in members, 'MISSING_GRAPH_VERTEX')
            target = select(member, node, edge['path'])
            ensure(L.identity(L.recipe_exact_value(target, context)) == L.identity(members[edge['target']]), 'INVALID_GRAPH_BINDING')
            ensure(type(edge['generation']) is int and edge['generation'] > 0, 'INVALID_EDGE_GENERATION')
    rows = sorted(work.rows.values(), key=lambda r: (r['purpose'], r['parts'], r['requirements']))
    return {'observations': rows, 'paths': paths_by_member, 'selections': selections}


def execute_fixture(data, context, installed_types):
    """Normalize actual authored members using the installed alias environment."""
    try:
        members = {key: L.normalize(L.preprocess(value, context), context)
                   for key, value in sorted(data['members'].items())}
        result = derive_restore_obligations(members, data['edges'], context, installed_types)
        return {'status': 'VALID', 'observations': result['observations'], 'paths': result['paths']}
    except L.Failure as failure:
        # Contracts facade preserves the native category under its LANGUAGE_ namespace.
        return {'status': 'REJECTED', 'code': 'LANGUAGE_' + failure.category}
    except ValueError as failure:
        return {'status': 'REJECTED', 'code': str(failure)}
