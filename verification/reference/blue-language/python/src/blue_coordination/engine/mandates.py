"""Result-based protected Mandate program and lifecycle admission.

Writer evidence comes from complete Contracts local turns, never a submitted
claim. This validation runs before the atomic Coordination publication.
"""
from algorithms import blue as L
from blue_coordination_spec.model import require
from blue_contracts.reference.channels import operation_request

BASE_WRITERS = {'initializeMandate': {'status'}, 'approveMandate': {'status', 'approvedAt'},
                'applyMandateTermination': {'status', 'terminatedAt'}}


def validate_program(c, body):
    p = c.processor
    if not c.is_type(body, 'Mandate/Mandate'):
        return None
    contracts = p.registry.contracts(body)
    base = p.registry.contracts(L.Ref(c.types['Mandate/Mandate']))
    for name, declaration in base.items():
        if name in ('authorityHolderChannel', 'authorizedActorChannel'):
            require(name in contracts, 'INVALID_MANDATE_PARTICIPANTS')
            node = p.blue.exact(contracts[name]['_recipe'])
            identity = p.blue.identity(node)
            p.blue.remember(node)
            require(c.is_type(node, 'Timeline Channel'), 'INVALID_MANDATE_PARTICIPANTS')
            c.timeline(c.link(identity, 'timeline')); c.actor(c.link(identity, 'actor'))
        else:
            require(name in contracts and contracts[name]['_recipe'].key() == declaration['_recipe'].key(),
                    'PROTECTED_MANDATE_PROGRAM', handler=name)
    if c.is_type(body, 'Mandate/Operation Mandate'):
        scope = c.operand(p.blue.identity(body), 'scope')
        if scope is not None and L.present_recipe(scope, p.blue.context):
            head = p.blue.head(scope)
            require(head.value is L.ABSENT and head.items is None, 'INVALID_MANDATE_SCOPE')
            for name in head.fields:
                grant = c.operand(p.blue.identity(scope), name); p.blue.remember(grant)
                grant_id = p.blue.identity(grant)
                c.read(grant_id, 'Mandate/Operation Grant')
                target = c.link(grant_id, 'target')
                shape = c.read(target)
                require(set(shape) <= {'initialDocument', 'channel', 'operation', 'documentValidation'} and
                    all(type(shape.get(k)) is str and bool(shape[k]) for k in ('channel', 'operation')), 'INVALID_MANDATE_TARGET')
                for owner, field, typ in ((grant_id, 'validation', 'Mandate/Request Validation'),
                                          (target, 'documentValidation', 'Mandate/Document Validation')):
                    selected = c.link(owner, field, optional=True)
                    if selected: c.read(selected, typ)
    # All executable declarations and participant roles are owner-reviewed.
    return {name: p.blue.identity(p.blue.exact(row['_recipe'])) for name, row in contracts.items()
            if row['_role'] not in ('initialized', 'checkpoint', 'terminated')}


def validate_result(c, result, member, old_head, cause):
    body = result.snapshot.documents[member].body
    program = validate_program(c, body)
    if program is None:
        return None
    p = c.processor
    old_approval = old_head.get('approvedProgram') if old_head else None
    old_program = old_head.get('mandateProgram') if old_head else None
    if old_program is not None:
        require(program == old_program, 'PROTECTED_MANDATE_PROGRAM')
    approved = old_approval
    turns = [t for t in result.completions if t['turnInput']['member'] == member]
    for turn in turns:
        for write in turn.get('writes', []):
            before, after = L.Ref(write['before']), L.Ref(write['after'])
            require(c.is_type(before, 'Mandate/Mandate') and c.is_type(after, 'Mandate/Mandate'), 'PROTECTED_MANDATE_TYPE')
            validate_program(c, after)
            writer = write['writer']
            path = L.path_parts(write['path'])
            if path[0] == 'contracts':
                require(validate_program(c, before) == validate_program(c, after), 'PROTECTED_MANDATE_PROGRAM')
            if path[0] in ('status', 'approvedAt', 'terminatedAt'):
                require(path[0] in BASE_WRITERS.get(writer['handler'], set()), 'PROTECTED_MANDATE_WRITER', path=write['path'])
                declaration = p.registry.contracts(before)[writer['handler']]
                require(writer['declaration'] == p.blue.identity(p.blue.exact(declaration['_recipe'])), 'PROTECTED_MANDATE_WRITER')
                if writer['handler'] == 'approveMandate':
                    require(cause is not None and writer['kind'] == 'EXTERNAL', 'INVALID_MANDATE_APPROVAL')
                    holder = p.registry.contracts(before)['authorityHolderChannel']
                    channel = p.blue.exact(holder['_recipe']); p.blue.remember(channel)
                    cid = p.blue.identity(channel)
                    request = operation_request(p.registry, L.Ref(cause.message))
                    require(cause.actor == c.link(cid, 'actor') and cause.timeline == c.link(cid, 'timeline') and
                        request and request['operation'] == 'approveMandate' and request.get('requireExactDocumentVersion') is True and
                        old_head is not None and request.get('document', {}).get('blueId') == old_head['document'],
                        'INVALID_MANDATE_APPROVAL')
                    approved = program
    if p.blue.read(body, '/status') == 'Active':
        require(approved is not None, 'UNESTABLISHED_MANDATE_APPROVAL')
    return dict(mandateProgram=program, approvedProgram=approved)
