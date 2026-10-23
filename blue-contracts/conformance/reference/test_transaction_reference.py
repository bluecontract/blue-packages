import hashlib
import json
from pathlib import Path
import unittest
from transaction_reference import evaluate


class TransactionReferenceTests(unittest.TestCase):
    def test_checked_vectors_recompute_from_actual_operands(self):
        root = Path(__file__).resolve().parents[2]
        data = json.loads(Path(__file__).with_name('transaction-vectors.json').read_text())
        self.assertEqual(data['referenceSourceSha256'], hashlib.sha256(
            (root / 'tools/transaction_reference.py').read_bytes()).hexdigest())
        for vector in data['vectors']:
            with self.subTest(vector=vector['id']):
                self.assertEqual(vector['expected'], evaluate(vector['input']))

    def test_failure_after_write_discards_candidate_value(self):
        case = {'kind': 'invocation', 'initial': 8, 'steps': [
            {'op': 'add', 'value': 13}, {'op': 'read', 'resource': 'payload'}],
            'available': {}, 'sourceOwner': 'local', 'receiverOwner': 'local'}
        self.assertEqual(8, evaluate(case)['value'])
        case['available']['payload'] = 34
        self.assertEqual(34, evaluate(case)['value'])
        case['receiverOwner'] = 'foreign'
        self.assertEqual(8, evaluate(case)['receiverValue'])
