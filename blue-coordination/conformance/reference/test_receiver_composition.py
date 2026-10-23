import hashlib
import json
from pathlib import Path
import unittest
from receiver_composition_reference import derive_decisions


class NativeReceiverCompositionTests(unittest.TestCase):
    def test_native_authenticated_inputs_have_independent_decisions(self):
        vector = json.loads(Path(__file__).with_name('replay-composition-vector.json').read_text())
        source = Path(__file__).resolve().parents[2] / 'tools/receiver_composition_reference.py'
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), vector['referenceSourceSha256'])
        for row in vector['vectors']:
            self.assertEqual(derive_decisions(row['input']), row['expected'], row['id'])
