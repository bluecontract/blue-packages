"""Pure per-delivery policy hook; policy decisions are authored in BEX."""
from .model import closed, require
from .runtime import RuntimeMeter


def admit(run, member, channel, payload, kind, operation, call, declarations, delivery):
    if not any(d['_role'] == 'extension_dispatch_policy' for d in declarations.values()):
        return True
    allowed = True
    # Sorting all declarations is charged even though only policies are evaluated.
    for key, header in run.ordered(declarations):
        if header['_role'] != 'extension_dispatch_policy':
            continue
        policy = run.reg.declaration(header['_recipe'])
        meter = RuntimeMeter(run.meter, policy['_extension'].binding, member)
        meter.charge('dispatchPolicyCheck')
        meter.merge()
        definition = run.compute_definition(member, policy)
        program = run.program(policy)
        overlay = {**program, 'functions': {**(definition or {}).get('functions', {}),
                                           **policy.get('functions', {})}}
        context = run.context(member, payload, policy, {}, call, overlay_program=overlay)
        context.bindings['dispatch'] = {'kind': kind, 'channel': channel, 'operation': operation}
        result = run.engine.bex.execute(program, context, gas=run.meter,
                                        entry=policy.get('entry'), definition=definition)
        require(not result.changeset and not result.events, 'EFFECTFUL_DISPATCH_POLICY')
        decision = closed(result.value, {'allowed'}, {'reason'})
        require(type(decision['allowed']) is bool, 'INVALID_DISPATCH_DECISION')
        require('reason' not in decision or type(decision['reason']) is str, 'INVALID_DISPATCH_REASON')
        accept = decision['allowed']
        allowed = allowed and accept
        run.frame.dispatch_decisions.append(dict(
            delivery=delivery, policy=key, declaration=run.blue.identity(run.blue.exact(policy['_recipe'])),
            channel=channel, kind=kind, operation=operation, allowed=accept,
            reason=decision.get('reason', '' if accept else 'DISPATCH_REJECTED')))
    return allowed
