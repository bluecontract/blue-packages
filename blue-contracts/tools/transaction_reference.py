"""Finite publication/rollback reference, not a second Contracts or BEX engine.

Native Language owns exact identities/contextual schema; native Contracts owns
completion provenance, unit membership, receipts and capability authentication.
This model checks the transaction consequences of the corresponding shared raw
fixture operations, including an explicit owner boundary for receiving.
"""
import bootstrap  # Establish the same pinned reference environment as other models.


def evaluate(case):
    kind = case['kind']
    if kind == 'interleaved-failure':
        candidate = case['initial']
        missing = False
        for step in case['candidateSteps']:
            if step['op'] == 'add':
                candidate += step['value']
            elif step['op'] == 'read':
                if step['resource'] not in case['available']:
                    missing = True
                    break
                candidate = case['available'][step['resource']]
            else:
                raise ValueError('Unsupported interleaved operation')
        if not missing:
            raise ValueError('This finite vector requires a failed candidate')
        # The rollback baseline is the latest shared commit, not begin's snapshot.
        shared_value = case['foreignInitial'] + case['foreignAdd']
        return {'candidateStatus': 'NEEDS_RESOURCES', 'candidateValue': case['initial'],
                'foreignValue': shared_value, 'foreignRetained': True,
                'sharedEvidenceUnchanged': True, 'archiveUnchanged': True,
                'completionsUnchanged': True, 'candidateCaptureAllowed': False}
    if kind == 'mutation':
        accepted = case['x'] >= case['minimumAfter']
        return {'status': 'APPLIED' if accepted else 'FAILED',
                'x': case['x'], 'y': 1 if accepted else 0,
                'stateChanged': accepted}
    if kind == 'portable':
        accepted = case['profile'] == 'contracts-deterministic-gas-4'
        return {'imported': accepted, 'contextPublished': accepted,
                'archivePublished': accepted, 'completionPublished': False}
    if kind != 'invocation':
        raise ValueError('Unsupported reference fixture kind')
    value = case['initial']
    for step in case['steps']:
        if step['op'] == 'add':
            value += step['value']
        elif step['op'] == 'read':
            if step['resource'] not in case['available']:
                return {'status': 'NEEDS_RESOURCES', 'value': case['initial'],
                        'stateChanged': False, 'archivePublished': False,
                        'completionPublished': False, 'captureAllowed': False,
                        'receiveStatus': 'NOT_ATTEMPTED', 'receiverValue': case['initial'],
                        'receiverUnchanged': True}
            value = case['available'][step['resource']]
        else:
            raise ValueError('Unsupported reference fixture operation')
    owned = case['sourceOwner'] == case['receiverOwner']
    return {'status': 'APPLIED', 'value': value,
            'stateChanged': True, 'archivePublished': True,
            'completionPublished': True, 'captureAllowed': True,
            'receiveStatus': 'APPLIED' if owned else 'REJECTED',
            'receiverValue': value if owned else case['initial'],
            'receiverUnchanged': not owned}
