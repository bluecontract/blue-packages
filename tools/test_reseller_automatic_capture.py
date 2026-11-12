#!/usr/bin/env python3
"""Exercise the example's real capture configuration on native Order/PI events."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAYMENT = '/orders/o1/payment/payment'
CAPTURE = PAYMENT + '/requests/confirmed-order'
TEMPLATE = '/clauses/orders/parameters/template/clauses/payment/parameters/template/clauses/payment'


def capture_expected(step):
    step.setdefault('expect', {}).update({
        CAPTURE + '/intent/action': 'capture',
        CAPTURE + '/intent/amountMinor': 10000,
        CAPTURE + '/status': 'pending',
        PAYMENT + '/completed': 0,
        PAYMENT + '/reserved/capture': 10000,
    })
    step['expectEntryCounts'] = {PAYMENT + '/requests': 2}


def main():
    output = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'reports/automatic-order-capture')
    output.mkdir(parents=True, exist_ok=True)
    example = yaml.safe_load((ROOT / 'examples/reseller/cancellation-enabled-agreement.blue').read_text())
    payment_clause = example['orderTemplate']['clauses']['payment']
    payment_template = payment_clause['parameters']['template']
    process = payment_template['clauses']['payment']
    terms = payment_template['paymentTerms']
    fixture = yaml.safe_load((ROOT / 'examples/reseller/cancellation-settlement-native.blue').read_text())
    fixture_payment = fixture['clauses']['orders']['parameters']['template']['clauses']['payment']
    fixture_bindings = fixture_payment['parameters']['template']['clauses']['payment']['bindings']
    cases = json.loads((ROOT / 'examples/reseller/tests/cancellation-settlement.case.json').read_text())['scenarios']
    approval = {
        'operation': 'approve_seller', 'channel': 'seller', 'target': '/orders/o1',
        'request': {}, 'requestFromState': {'revision': '/orders/o1/activation/revision'},
        'requireExactDocumentVersion': True, 'timestampMicros': 1794574799999999,
    }
    before = copy.deepcopy(cases[0])
    before['name'] = 'Seller approval before authorization captures once and cancellation refunds once'
    before['steps'] = [step for step in before['steps'] if step.get('operation') != 'capture']
    before['steps'].insert(3, copy.deepcopy(approval))
    for step in before['steps']:
        if step.get('operation') == 'completePayment':
            step['request']['requestId'] = 'confirmed-order'
        if step.get('operation') in ('authorize', 'approve_seller'):
            step['absent'] = [CAPTURE]
        if step.get('operation') == 'secureFunds':
            capture_expected(step)

    after = copy.deepcopy(before)
    after['name'] = 'Authorization and reservation confirmation wait for seller approval; replay does not recapture'
    approved = after['steps'].pop(3)
    authorized = next(i for i, step in enumerate(after['steps']) if step.get('operation') == 'secureFunds')
    secure = after['steps'][authorized]
    secure.pop('expectEntryCounts')
    secure['expect'] = {PAYMENT + '/secured': 10000, PAYMENT + '/reserved/capture': 0}
    secure['absent'] = [CAPTURE]
    attempted = copy.deepcopy(next(s for s in cases[0]['steps'] if s.get('operation') == 'capture'))
    attempted.update(status='FAILED', unchangedPaths=[PAYMENT], absent=[CAPTURE])
    attempted['request']['requestId'] = 'premature-capture'
    customer = copy.deepcopy(approval)
    customer.update(operation='approve_customer', channel='customer', absent=[CAPTURE],
                    expect={'/orders/o1/activation/active': False, PAYMENT + '/reserved/capture': 0})
    stale = copy.deepcopy(approval)
    stale.pop('requestFromState')
    stale.update(request={'revision': 0}, status='FAILED', unchangedPaths=[PAYMENT], absent=[CAPTURE])
    approved.pop('absent')
    capture_expected(approved)
    repeated = copy.deepcopy(approved)
    repeated['restore'] = True
    after['steps'][authorized + 1:authorized + 1] = [attempted, customer, stale, approved, repeated]

    groups = copy.deepcopy(before)
    groups['name'] = 'One seller approval confirms every proposed date and captures the multi-product order'
    complete = next(i for i, s in enumerate(groups['steps']) if s.get('operation') == 'completePayment')
    groups['steps'] = [s for s in groups['steps'][:complete + 1] if s.get('operation') != 'confirmReservation']
    order = groups['steps'][1]
    first = order['request']['groups'][0]
    first['lineIndices'] = [0]
    order['request']['groups'].append({**first, 'id': 'rental', 'lineIndices': [1],
                                      'proposedStartMicros': first['proposedStartMicros'] + 3600000000})
    order['expect']['/orders/o1/reservations/trip/proposal/amountMinor'] = 6000
    for step in groups['steps']:
        if step.get('operation') in ('approve_seller', 'secureFunds'):
            step.setdefault('expect', {}).update({
                '/orders/o1/reservations/trip/status': 'confirmed',
                '/orders/o1/reservations/trip/confirmedStartMicros': first['proposedStartMicros'],
                '/orders/o1/reservations/rental/status': 'confirmed',
                '/orders/o1/reservations/rental/confirmedStartMicros': first['proposedStartMicros'] + 3600000000,
            })

    combined_after = copy.deepcopy(after)
    combined_after['name'] = 'Authorized payment waits for exact seller acceptance and date confirmation together'
    combined_after['steps'] = [s for s in combined_after['steps'] if s.get('operation') != 'confirmReservation']
    for step in combined_after['steps']:
        if step.get('operation') == 'approve_seller':
            if step.get('status') == 'FAILED':
                step['unchangedPaths'] = ['/orders/o1/activation', '/orders/o1/reservations', PAYMENT]
                step['expectNoEffects'] = True
                step['diagnosticContains'] = 'BEX_EXECUTION_REJECTED'
            else:
                step['expect'].update({'/orders/o1/activation/active': True,
                                      '/orders/o1/reservations/trip/status': 'confirmed'})
                if step.get('restore'):
                    step['unchangedPaths'] = ['/orders/o1/reservations', '/orders/o1/reservationRequests']
    successful = next(s for s in combined_after['steps']
                      if s.get('operation') == 'approve_seller' and s.get('status') != 'FAILED')
    rejected = copy.deepcopy(approval)
    rejected.update(status='FAILED', expectNoPublicEffects=True, absent=[CAPTURE],
                    diagnosticContains='BEX_EXECUTION_REJECTED',
                    unchangedPaths=['/orders/o1/activation', '/orders/o1/reservations',
                                    '/orders/o1/reservationRequests', PAYMENT])
    unchecked = copy.deepcopy(rejected)
    unchecked['requireExactDocumentVersion'] = False
    impostor = copy.deepcopy(rejected)
    impostor['channel'] = 'customer'
    impostor.pop('diagnosticContains')
    at_approval = combined_after['steps'].index(successful)
    combined_after['steps'][at_approval:at_approval] = [unchecked, impostor]

    # Start the boundary cases with an authorized PI and no seller/date approval.
    secured_index = next(i for i, s in enumerate(combined_after['steps']) if s.get('operation') == 'secureFunds')
    pending = copy.deepcopy(combined_after)
    pending['steps'] = pending['steps'][:secured_index + 1]
    past_date = copy.deepcopy(pending)
    past_date['name'] = 'One expired date rolls back seller approval, all group confirmations and capture'
    past_order = past_date['steps'][1]
    past_order['request']['groups'] = copy.deepcopy(groups['steps'][1]['request']['groups'])
    past_order['request']['groups'][1]['proposedStartMicros'] += 172800000000
    past_order['expect']['/orders/o1/reservations/trip/proposal/amountMinor'] = 6000
    expired_approval = copy.deepcopy(rejected)
    expired_approval['timestampMicros'] = first['proposedStartMicros'] + 1
    past_date['steps'].append(expired_approval)

    alternative = copy.deepcopy(pending)
    alternative['name'] = 'Seller approval cannot bypass customer acceptance of an alternative date'
    alternative_date = first['proposedStartMicros'] + 86400000000
    proposed = {
        'operation': 'proposeAlternative', 'channel': 'seller', 'target': '/orders/o1',
        'request': {'key': 'alternative', 'groupId': 'trip', 'catalog': fixture['catalog'],
                    'lines': copy.deepcopy(pending['steps'][0]['request']['lines']),
                    'proposedStartMicros': alternative_date},
        'requestFromState': {'expectedProposalBlueId': '/orders/o1/reservations/trip/proposalBlueId'},
        'timestampMicros': approval['timestampMicros'], 'absent': [CAPTURE],
        'expect': {'/orders/o1/reservations/trip/status': 'pending_customer'},
    }
    consent = {
        'operation': 'acceptProposal', 'channel': 'customer', 'target': '/orders/o1',
        'request': {'key': 'consent', 'groupId': 'trip'},
        'requestFromState': {'expectedProposalBlueId': '/orders/o1/reservations/trip/proposalBlueId'},
        'timestampMicros': approval['timestampMicros'], 'absent': [CAPTURE],
        'expect': {'/orders/o1/activation/active': False, '/orders/o1/reservations/trip/status': 'confirmed',
                   '/orders/o1/reservations/trip/confirmedStartMicros': alternative_date},
    }
    alternative['steps'].extend([proposed, copy.deepcopy(rejected), consent, copy.deepcopy(successful)])

    immediate = copy.deepcopy(pending)
    immediate['name'] = 'Seller approval cannot impose an immediate cancellation fee without customer consent'
    immediate_rejected = copy.deepcopy(rejected)
    immediate_rejected['timestampMicros'] = approval['timestampMicros'] + 2
    confirmation = copy.deepcopy(next(s for s in before['steps'] if s.get('operation') == 'confirmReservation'))
    confirmation.update(timestampMicros=immediate_rejected['timestampMicros'], absent=[CAPTURE],
                        expect={'/orders/o1/activation/active': False,
                                '/orders/o1/reservations/trip/status': 'pending_customer'})
    immediate_consent = copy.deepcopy(consent)
    immediate_consent['timestampMicros'] = immediate_rejected['timestampMicros']
    immediate_consent['request']['acceptImmediateCharge'] = True
    immediate_consent['expect']['/orders/o1/reservations/trip/confirmedStartMicros'] = first['proposedStartMicros']
    immediate_approved = copy.deepcopy(successful)
    immediate_approved['timestampMicros'] = immediate_rejected['timestampMicros']
    immediate['steps'].extend([immediate_rejected, confirmation, copy.deepcopy(immediate_rejected),
                               immediate_consent, immediate_approved])

    undated = copy.deepcopy(pending)
    undated['name'] = 'Order without a confirmation clause needs no date for seller acceptance'
    undated['steps'] = undated['steps'][:2]
    undated['sourceRemove'] = ['/clauses/orders/parameters/template/clauses/confirmation',
                               '/clauses/orders/parameters/template/clauses/cancellation']
    undated['steps'][1]['request']['groups'][0].pop('proposedStartMicros')
    undated['steps'][1]['expect'] = {'/orders/o1/reservations': {}}
    undated_approved = copy.deepcopy(approval)
    undated_approved['expect'] = {'/orders/o1/activation/active': True, '/orders/o1/reservations': {}}
    undated['steps'].append(undated_approved)

    cancelled = copy.deepcopy(after)
    cancelled['name'] = 'Cancellation before seller approval voids authorization; late approval cannot capture'
    cancelled['steps'] = [s for s in cancelled['steps'][:authorized + 1] if s.get('operation') != 'confirmReservation']
    cancel = copy.deepcopy(next(s for s in before['steps'] if s.get('operation') == 'cancelReservation'))
    cancel['expect'] = {
        '/orders/o1/reservations/trip/status': 'cancelled',
        PAYMENT + '/reserved/capture': 0, PAYMENT + '/reserved/void': 10000,
        '/orders/o1/paymentSettlement/status': 'requested',
    }
    cancel['absent'] = [CAPTURE]
    late_approval = copy.deepcopy(approval)
    late_approval.update(timestampMicros=1794574800000001, absent=[CAPTURE], expect={
        '/orders/o1/activation/active': True, PAYMENT + '/reserved/void': 10000,
        PAYMENT + '/reserved/capture': 0,
    })
    cancelled['steps'].extend([cancel, late_approval, {
        'operation': 'cancelBeforeCompletion', 'channel': 'guarantor', 'source': 'guarantor',
        'target': '/orders/o1/payment', 'request': {'type': 'PaymentInstruction/Payment Outcome Input'},
        'requestFromState': {'requestId': '/orders/o1/payment/cancellationSettlement/lastRequestId'},
        'timestampMicros': 1794574800000002,
        'expect': {PAYMENT + '/secured': 0, PAYMENT + '/completed': 0, '/orders/o1/paymentSettlement/status': 'settled'},
        'absent': [CAPTURE],
    }])

    fee = copy.deepcopy(cases[3])
    fee['name'] = 'Failed full capture still permits cancellation fee capture and release of the balance'
    fee['steps'].insert(3, copy.deepcopy(approval))
    authorized = next(i for i, s in enumerate(fee['steps']) if s.get('operation') == 'secureFunds')
    capture_expected(fee['steps'][authorized])
    fee['steps'].insert(authorized + 1, {
        'operation': 'failCompletePayment', 'channel': 'guarantor', 'source': 'guarantor',
        'target': '/orders/o1/payment',
        'request': {'type': 'PaymentInstruction/Payment Outcome Input', 'requestId': 'confirmed-order', 'reason': 'Native test decline'},
        'timestampMicros': 1794574799999999,
        'expect': {CAPTURE + '/status': 'failed', PAYMENT + '/reserved/capture': 0},
    })

    recipient = copy.deepcopy(before)
    recipient['name'] = 'Recipient approval after authorization wakes automatic capture'
    authorized = next(i for i, s in enumerate(recipient['steps']) if s.get('operation') == 'secureFunds')
    secured = recipient['steps'][authorized]
    secured['expect'] = {PAYMENT + '/secured': 10000, PAYMENT + '/reserved/capture': 0}
    secured.pop('expectEntryCounts')
    secured['absent'] = [CAPTURE]
    approved = {
        'operation': 'approveRecipient', 'channel': 'payee', 'source': 'seller',
        'target': '/orders/o1/payment', 'request': {}, 'timestampMicros': 1794574799999999,
    }
    capture_expected(approved)
    recipient['steps'].insert(authorized + 1, approved)
    recipient['sourcePatch'] = {
        TEMPLATE.rsplit('/clauses/payment', 1)[0] + '/paymentTerms/recipientApprovalRequired': True,
    }

    scenarios = [cancelled, before, after, groups, combined_after, past_date, alternative, immediate, undated, fee, recipient]
    for scenario in scenarios:
        # Use the authored example, including an absent binding in the red run.
        scenario.setdefault('sourcePatch', {}).update({
            TEMPLATE.rsplit('/clauses/payment', 1)[0] + '/businessContext': payment_template['businessContext'],
            TEMPLATE.rsplit('/clauses/payment', 1)[0] + '/sources': payment_template['sources'],
            TEMPLATE.rsplit('/clauses/payment', 1)[0] + '/paymentTerms/captureGate': terms['captureGate'],
            TEMPLATE + '/parameters': process['parameters'],
            TEMPLATE + '/bindings': {
                **fixture_bindings,
                'requestCapture': {
                    **fixture_bindings['requestCapture'],
                    **{key: value for key, value in process['bindings']['requestCapture'].items() if key != 'pay'},
                },
                'approveRecipient': {
                    'approveRecipient': {'on': 'workflow', 'party': 'payee'},
                },
            },
        })
        activation_parameters = copy.deepcopy(example['orderTemplate']['clauses']['activation']['parameters'])
        activation_parameters['parties'] = fixture['clauses']['orders']['parameters']['template']['clauses']['activation']['parameters']['parties']
        activation_parameters['preActivationChannels'].append('cx.confirmation.initialize._automatic_source')
        # This component fixture explicitly requests the same preparation instead of a host timer.
        activation_parameters['preActivationOperations'].append('startPayment')
        scenario['sourcePatch']['/clauses/orders/parameters/template/clauses/activation/parameters'] = activation_parameters
        confirmation = example['clauses']['fulfilment']['parameters']['template']['clauses']['confirmation']
        scenario['sourcePatch']['/clauses/orders/parameters/template/clauses/confirmation/bindings'] = {
            **fixture['clauses']['orders']['parameters']['template']['clauses']['confirmation']['bindings'],
            **confirmation['bindings'],
        }
        clause_path = '/clauses/orders/parameters/template/clauses/payment'
        scenario['sourcePatch'] = {
            clause_path + '/parameters': {
                **fixture_payment['parameters'],
                'sourcePaths': payment_clause['parameters']['sourcePaths'],
            },
            **scenario['sourcePatch'],
            clause_path + '/bindings/sources': {},
        }
        for step in scenario['steps']:
            step.pop('bindPreparedSources', None)
            if 'bootstrapPrepared' in step:
                step['receivePreparedSource'] = '/orders/o1'
        scenario['sourcePatch'][clause_path + '/parameters/fieldPaths'] = payment_clause['parameters']['fieldPaths']
        scenario['sourcePatch'][clause_path + '/bindings/prepare/startPayment/params/values'] = {
            **fixture_payment['bindings']['prepare']['startPayment']['params']['values'],
            **{field: payment_clause['bindings']['prepare']['onOrderCreated']['params']['values'][field]
               for field in ('orderOrigin', 'orderRevision', 'orderTermsRef')},
        }
    conflicting = copy.deepcopy(before)
    conflicting['name'] = 'Conflicting PI Order source declarations reject Order initialization'
    conflicting['steps'] = conflicting['steps'][:2]
    conflicting['steps'][-1]['status'] = 'FAILED'
    conflicting['steps'][-1]['expect'] = {}
    conflicting['steps'][-1]['unchangedPaths'] = ['/orders']
    conflicting['sourcePatch'][TEMPLATE.rsplit('/clauses/payment', 1)[0] + '/sources'] = {'order': {}}
    scenarios.append(conflicting)
    scenario_path = output / 'scenarios.json'
    for scenario in scenarios:
        # Exercise the Order as its own native root before preparing the observing PI.
        # The legacy fixture's embedded factory is only used to calculate its basket.
        if scenario is not conflicting:
            scenario['steps'][1]['expect'].update({'/orders/o1/activation/required': ['seller'], '/orders/o1/activation/active': False})
            scenario['steps'][1]['focus'] = '/orders/o1'
        scenario['steps'][2:] = json.loads(json.dumps(scenario['steps'][2:]).replace('/orders/o1', ''))
    scenario_path.write_text(json.dumps({'scenarios': scenarios}, indent=2) + '\n')
    subprocess.run([
        sys.executable, str(ROOT / 'tools/run_reseller.py'),
        '--source', str(ROOT / 'examples/reseller/cancellation-settlement-native.blue'),
        '--scenarios', str(scenario_path), '--output', str(output),
    ], check=True)


if __name__ == '__main__':
    main()
