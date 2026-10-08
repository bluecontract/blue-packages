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
    for number in ('23', '24', '25'):
        case = next((root / 'examples/payment-family').glob(number + '-*.case.yaml'))
        data = load(case)
        for row in [data.get('initial', {}), *data['steps']]:
            covered.update(t.split('/', 1)[1] for t in row.get('eventTypes', []))
            if row.get('status', 'APPLIED') == 'APPLIED' and row.get('eventCount') != 0:
                invoked.add(row.get('operation'))
    assert concrete == covered, f'Missing or unknown message assertions: {concrete ^ covered}'
    metadata = json.loads((root / 'docs/payment-protocol-operations.json').read_text())
    assert set(metadata['guarantorOperations']) <= invoked, 'Untested guarantor operation'
    actions = load(root / 'payment-instruction/types/payment-lifecycle-clause.blue')['actions']
    assert set(metadata['guarantorOperations']) <= actions.keys(), 'Undeclared operation'
    assert 'confirm' not in actions, 'Generic confirmation must not be the public operation'
    print(f'PASS: {len(concrete)} concrete messages and {len(metadata["guarantorOperations"])} guarantor operations have executable scenario assertions')

if __name__ == '__main__':
    check()
