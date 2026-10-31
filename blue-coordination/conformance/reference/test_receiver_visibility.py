import hashlib
import json
from pathlib import Path
import unittest
from receiver_visibility_reference import derive_visibility


class ReceiverVisibilityTests(unittest.TestCase):
    def test_independent_causal_coordinates_and_terminal_scope(self):
        fixture = json.loads(Path(__file__).with_name("visibility-vector.json").read_text())
        source = Path(__file__).resolve().parents[2] / "tools/receiver_visibility_reference.py"
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), fixture["referenceSourceSha256"])
        for row in fixture["vectors"]:
            self.assertEqual(row["expected"], derive_visibility(row["input"]), row["id"])
