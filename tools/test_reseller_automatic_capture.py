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
    before = copy.deepcopy(cases[0])
    before['name'] = 'Confirmation before authorization automatically captures, then refunds once'
    before['steps'] = [step for step in before['steps'] if step.get('operation') != 'capture']
    for step in before['steps']:
        if step.get('operation') == 'completePayment':
            step['request']['requestId'] = 'confirmed-order'
        if step.get('operation') == 'authorize':
            step['absent'] = [CAPTURE]
        if step.get('operation') == 'secureFunds':
            capture_expected(step)

    after = copy.deepcopy(before)
    after['name'] = 'Authorization waits for seller confirmation; restore and repeated confirmation do not recapture'
    confirmation = after['steps'].pop(2)
    authorized = next(i for i, step in enumerate(after['steps']) if step.get('operation') == 'secureFunds')
    secure = after['steps'][authorized]
    secure.pop('expectEntryCounts')
    secure['expect'] = {PAYMENT + '/secured': 10000, PAYMENT + '/reserved/capture': 0}
    secure['absent'] = [CAPTURE]
    attempted = copy.deepcopy(next(s for s in cases[0]['steps'] if s.get('operation') == 'capture'))
    attempted.update(status='FAILED', unchangedPaths=[PAYMENT], absent=[CAPTURE])
    attempted['request']['requestId'] = 'premature-capture'
    capture_expected(confirmation)
    repeated = copy.deepcopy(confirmation)
    repeated['restore'] = True
    after['steps'][authorized + 1:authorized + 1] = [attempted, confirmation, repeated]

    groups = copy.deepcopy(after)
    groups['name'] = 'Each independently scheduled group must be confirmed before full capture'
    complete = next(i for i, s in enumerate(groups['steps']) if s.get('operation') == 'completePayment')
    groups['steps'] = groups['steps'][:complete + 1]
    order = next(s for s in groups['steps'] if s.get('operation') == 'placeOrder')
    first = order['request']['groups'][0]
    first['lineIndices'] = [0]
    order['request']['groups'].append({**first, 'id': 'rental', 'lineIndices': [1]})
    order['expect']['/orders/o1/reservations/trip/proposal/amountMinor'] = 6000
    confirmations = [s for s in groups['steps'] if s.get('operation') == 'confirmReservation']
    confirmations[0].pop('expectEntryCounts')
    confirmations[0]['expect'] = {PAYMENT + '/reserved/capture': 0}
    confirmations[0]['absent'] = [CAPTURE]
    confirmations[1]['request'].update(key='confirm-2', groupId='rental')
    confirmations[1]['requestFromState']['expectedProposalBlueId'] = '/orders/o1/reservations/rental/proposalBlueId'

    cancelled = copy.deepcopy(after)
    cancelled['name'] = 'Cancellation before confirmation voids authorization without full capture'
    cancelled['steps'] = cancelled['steps'][:authorized + 1]
    cancel = copy.deepcopy(next(s for s in before['steps'] if s.get('operation') == 'cancelReservation'))
    cancel['expect'] = {
        '/orders/o1/reservations/trip/status': 'cancelled',
        PAYMENT + '/reserved/capture': 0,
        PAYMENT + '/reserved/void': 10000,
        '/orders/o1/paymentSettlement/status': 'requested',
    }
    cancel['absent'] = [CAPTURE]
    cancelled['steps'].append(cancel)
    cancelled['steps'].append({
        'operation': 'cancelBeforeCompletion', 'channel': 'guarantor', 'source': 'guarantor',
        'target': '/orders/o1/payment', 'request': {'type': 'PaymentInstruction/Payment Outcome Input'},
        'requestFromState': {'requestId': '/orders/o1/payment/cancellationSettlement/lastRequestId'},
        'timestampMicros': 1794574800000002,
        'expect': {PAYMENT + '/secured': 0, PAYMENT + '/completed': 0, '/orders/o1/paymentSettlement/status': 'settled'},
        'absent': [CAPTURE],
    })

    fee = copy.deepcopy(cases[3])
    fee['name'] = 'Failed full capture does not block later cancellation fee capture and authorization release'
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

    scenarios = [before, after, groups, cancelled, fee, recipient]
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
        clause_path = '/clauses/orders/parameters/template/clauses/payment'
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
    scenario_path.write_text(json.dumps({'scenarios': scenarios}, indent=2) + '\n')
    subprocess.run([
        sys.executable, str(ROOT / 'tools/run_reseller.py'),
        '--source', str(ROOT / 'examples/reseller/cancellation-settlement-native.blue'),
        '--scenarios', str(scenario_path), '--output', str(output),
    ], check=True)


if __name__ == '__main__':
    main()
