"""Derive required records from authored managed structure, never a provider bag.

Contextual selection is performed by restore_reference. This worklist expands
only its successful value/definition observations; containers remain shallow.
Native Language owns identities and cyclic proof verification/externalization.
"""
import bootstrap
from algorithms import blue as L
from demand_reference import prepare_records
from restore_reference import derive_restore_obligations


def derive_records(data, context, installed_types):
    if 'component' in data:
        component = L.finalize_set(data['component'], context)
        proof = {'members': [L.export_tree(node) for node in component['canonical']]}
        members = {key: L.verify_member(component['ids'][index], proof, None, context)
                   for key, index in data['memberIndices'].items()}
    else:
        members = {key: L.normalize(L.preprocess(value, context), context)
                   for key, value in sorted(data['members'].items())}
    derived = derive_restore_obligations(members, data['edges'], context, installed_types)
    pending = []
    for row in derived['observations']:
        pending.extend((L.Ref(identity), row['purpose'], tuple(row['requirements'])) for identity in row['parts'])
        pending.extend((L.Ref(identity), 'definition', ()) for identity in row['requirements'])
    seen, roots = set(), []
    while pending:
        node, purpose, requirements = pending.pop(0)
        key = (L.identity(node), purpose, requirements)
        if key in seen:
            continue
        seen.add(key)
        roots.append((node, purpose, 'derived-restore', ()))
        if purpose in {'container', 'predicate-read'}:
            continue
        if purpose not in {'value', 'definition'}:
            raise ValueError('UNSUPPORTED_RETENTION_ROLE:' + purpose)
        body = L.open_exact(node, context)
        for field, child in body.fields:
            if isinstance(child, (L.Node, L.Ref)):
                pending.append((child, purpose, ()))
            elif field == 'items':
                pending.extend((item, purpose, ()) for item in child)
    records = prepare_records(roots, context)
    return {'records': records, 'paths': derived['paths'],
            'members': {key: L.identity(node) for key, node in members.items()}}
