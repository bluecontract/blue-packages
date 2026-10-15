#!/usr/bin/env python3
"""Check public payment message/operation coverage; execution belongs to the Java scenarios."""
import json
from pathlib import Path
from check_clause_tutorial import load

ROOT = Path(__file__).resolve().parents[1]

def check(root=ROOT):
    manifest = load(root / 'payment-instruction/blue-package.yaml')
    exports = {e['name']: e for e in manifest['exports']}
    messages = {name for name, e in exports.items() if '/messages/' in e['path']}
    concrete = messages - {'Payment Request', 'Payment Response'}
    covered, invoked = set(), set()
    for number in ('27', '28', '29'):
        case = next((root / 'examples/apps').glob(number + '-*.case.yaml'))
        data = load(case)
        for row in [data.get('initial', {}), *data['steps']]:
            covered.update(t.split('/', 1)[1] for t in row.get('eventTypes', []))
            if row.get('status', 'APPLIED') == 'APPLIED' and row.get('eventCount') != 0:
                invoked.add(row.get('operation'))
    assert concrete == covered, f'Missing or unknown message assertions: {concrete ^ covered}'
    metadata = json.loads((root / 'docs/payment-protocol-operations.json').read_text())
    assert set(metadata['guarantorOperations']) <= invoked, 'Untested guarantor operation'
    operations = load(root / 'payment-instruction/types/payment-instruction.blue')['contracts']
    assert set(metadata['guarantorOperations']) <= operations.keys(), 'Undeclared domain operation'
    assert 'confirm' not in operations, 'Generic confirmation must not be the public operation'
    request_clause = load(root / 'payment-instruction/types/payment-request-actions.blue')
    assert request_clause['type'] == 'PaymentInstruction/Payment Action Definitions'
    requests = load(root / 'payment-instruction/types/payment-action-definitions.blue')['actions']
    payment = load(root / 'clause-payment/types/conditional-base.blue')
    assert not set(metadata['guarantorOperations']) & (set(requests) | set(payment['actions']) | set(payment['childActions'])), 'Guarantor operation leaked into a clause'
    assert load(root / 'payment-instruction/types/host-with-clauses.blue')['type'] == 'PaymentInstruction/Payment Instruction'
    for domain, folder, prefix in [('Payment', 'payment-instruction', 'messages/'), ('Shipping', 'shipping-instruction', '')]:
        manifest = load(root / folder / 'blue-package.yaml')
        types = {e['name']: load(root / folder / e['path']) for e in manifest['exports']}
        for kind in ['Request', 'Response']:
            assert types[domain+' '+kind]['type'] == 'Events/'+kind
    assert load(root / 'blue-events/types/request.blue')['type'] == 'Events/Event'
    assert load(root / 'blue-events/types/response.blue')['type'] == 'Events/Event'
    print(f'PASS: {len(concrete)} concrete messages and {len(metadata["guarantorOperations"])} guarantor operations have executable scenario assertions (static coverage check; run Java separately)')

if __name__ == '__main__':
    check()
