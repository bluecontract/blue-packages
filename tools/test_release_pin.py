import copy
from pathlib import Path
import tempfile
import unittest

from release_pin import recorded, verify


class ReleasePinTests(unittest.TestCase):
    def fixture(self, root):
        for name in ('blue-packages.zip', 'CATALOG.json', 'SHA256SUMS'):
            (root / name).write_bytes(name.encode())
        return recorded(root, 'blue-packages-2026.10.02.1')

    def test_exact_assets_and_tag_are_required_without_refreshing_expectations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pin = self.fixture(root)
            original = copy.deepcopy(pin)
            verify(root, pin, pin['tag'])
            with self.assertRaisesRegex(ValueError, 'tag differs'):
                verify(root, pin, 'blue-packages-2026.10.02.2')
            (root / 'blue-packages.zip').write_bytes(b'different compressed transport')
            with self.assertRaisesRegex(ValueError, 'assets differ'):
                verify(root, pin)
            self.assertEqual(pin, original)

    def test_missing_and_additional_assets_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pin = self.fixture(root)
            (root / 'unexpected.bluepkg').write_bytes(b'new')
            with self.assertRaisesRegex(ValueError, 'assets differ'):
                verify(root, pin)
            (root / 'unexpected.bluepkg').unlink()
            (root / 'CATALOG.json').unlink()
            with self.assertRaisesRegex(ValueError, 'Incomplete'):
                verify(root, pin)

    def test_symbolic_assets_cannot_become_release_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pin = self.fixture(root)
            (root / 'extra.bluepkg').symlink_to(root / 'blue-packages.zip')
            with self.assertRaisesRegex(ValueError, 'Invalid release asset'):
                verify(root, pin)
