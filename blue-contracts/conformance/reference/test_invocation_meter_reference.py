import unittest
from invocation_meter_reference import check_meter
from blue_contracts.reference.model import ContractError


class InvocationMeterTests(unittest.TestCase):
    def test_tariff_is_derived_not_trusted_from_reported_amount(self):
        row = dict(ordinal=0, namespace='contracts', counter='processInvocation', units=2, amount=40, owner='root')
        observation = {'gasTrace': [row], 'gas': 40, 'rejected': None}
        self.assertEqual(check_meter(observation, {'profile': 'contracts-deterministic-gas-4', 'shared': 40, 'local': {'root': 40}})['gas'], 40)
        with self.assertRaises(ContractError):
            check_meter({**observation, 'gas': 2, 'gasTrace': [{**row, 'amount': 2}]}, {'profile': 'contracts-deterministic-gas-4', 'shared': 40, 'local': {}})

    def test_rejected_charge_uses_first_exhausted_cap_without_debit(self):
        rejected = dict(ordinal=0, namespace='contracts', counter='processInvocation', units=1,
                        amount=20, owner='root', remaining=19, cap='LOCAL', sharedRemaining=100, localRemaining=19)
        observation = {'gasTrace': [], 'gas': 0, 'rejected': rejected}
        self.assertEqual(check_meter(observation, {'profile': 'contracts-deterministic-gas-4', 'shared': 100, 'local': {'root': 19}})['gas'], 0)
        with self.assertRaises(ContractError):
            check_meter(observation, {'profile': 'contracts-deterministic-gas-4', 'shared': 100, 'local': {'root': 20}})

    def test_native_shared_charge_inputs_match_independent_tariff_result(self):
        import hashlib
        import json
        from pathlib import Path
        source = Path(__file__).resolve().parents[2] / 'tools/invocation_meter_reference.py'
        vector = json.loads(Path(__file__).with_name('invocation-meter-vector.json').read_text())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), vector['referenceSourceSha256'])
        for case in vector['cases']:
            self.assertEqual(check_meter(case['observations'], case['policy']), case['expected'], case['label'])
