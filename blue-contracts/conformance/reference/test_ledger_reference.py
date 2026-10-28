import hashlib
import json
from pathlib import Path
import unittest
from ledger_reference import execute_sequence


class LedgerReferenceTests(unittest.TestCase):
    def test_checked_sequences_are_independently_recomputed(self):
        root = Path(__file__).resolve().parents[2]
        vector = json.loads(Path(__file__).with_name('ledger-sequences.json').read_text())
        self.assertEqual(hashlib.sha256((root/'tools/ledger_reference.py').read_bytes()).hexdigest(), vector['referenceSourceSha256'])
        for row in vector['vectors']:
            with self.subTest(sequence=row['id']):
                self.assertEqual(row['expected'], execute_sequence(row['input']))
