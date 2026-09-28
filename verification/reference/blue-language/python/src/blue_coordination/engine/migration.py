"""Explicit offline upgrade of an idle strict-wave context.

Stop every old worker using the store before calling this function and keep
administrative ownership until new-profile workers start. This is not a live
rolling migration and never discards a retained receiving obligation.
"""
from .work import publish, wake
from blue_coordination_spec.model import require

POLICY = 'independent-owner-prefix/1'


def migrate_quiescent_context(store, hub, *, context='default'):
    """Upgrade only a stable context with no active/reserved/failed work.

    Existing exact content, history, receipts, source progress and occurrence
    generations stay unchanged. Stale old claims are fenced. Backlog is woken
    under the new scheduler. An ambiguous/nonquiescent workspace is refused.
    """
    expected = {'coordination': hub.catalogue.specification,
                'contracts': hub.processor.registry.specification,
                'storage': 'coordination.records/20260922.6'}
    target = {**expected, 'scheduling': POLICY}
    with store.read() as view:
        prior = view.get('engine_contexts', context)
        if prior == target:
            return {'changed': False, 'context': context, 'scheduling': POLICY}
        require(prior == expected, 'INCOMPATIBLE_MIGRATION_SOURCE', context=context)
        instances = [row['instance'] for _, row in view.scan('managed', context + '/')]
        # Registering another document is also a context mutation. Capture the
        # membership/registration ranges so concurrent writers cannot be missed.
        pending = [row for _, row in view.scan('registration') if row['context'] == context]
        require(not pending, 'MIGRATION_REQUIRES_QUIESCENCE', reason='pending registration')
        writes = {('engine_contexts', context): target}
        for instance in sorted(instances):
            head = view.get('heads', instance)
            work = view.get('work', instance)
            lease = view.get('leases', instance)
            reservation = view.get('reservation', instance)
            require(head is not None and head['context'] == context and head.get('stable', True)
                    and not head.get('attachmentGoals') and not head.get('rebaseGoals')
                    and work is not None and not work['owner'] and reservation is None
                    and work['status'] == 'READY' and work.get('issue') is None,
                    'MIGRATION_REQUIRES_QUIESCENCE', instance=instance)
            position = view.get('positions', instance)
            require(position is not None, 'INVALID_MIGRATION_HISTORY', instance=instance)
            row = view.get('history', instance + '/' + str(position['number']).zfill(16))
            require(row is not None and row['stable'] and row['number'] == head['number'],
                    'INVALID_MIGRATION_HISTORY', instance=instance)
            writes['positions', instance] = {**position, 'stableNumber': row['number']}
            writes['work', instance] = {**work, 'owner': None, 'leaseUntil': 0,
                                        'fence': work['fence'] + 1}
            if lease is not None:
                writes['leases', instance] = None
            wake(view, writes, instance)
        packet = view.packet('independent-owner-prefix-upgrade:' + context, writes=writes,
            result={'changed': True, 'context': context, 'scheduling': POLICY,
                    'instances': len(instances)})
    result = publish(store, packet)
    require(result.status == 'COMMITTED', 'MIGRATION_CONFLICT', context=context)
    return result.result
