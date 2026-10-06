from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import package as publisher
from reference import Exact, ModelProvider, hexbytes
from blue_language.physical import PhysicalCache

class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = PhysicalCache(65536).scope()
        cls.scope.__enter__()
        cls.e = Exact()

    @classmethod
    def tearDownClass(cls):
        cls.scope.__exit__(None, None, None)

    def test_all_exports_have_explicit_current_rules(self):
        for export in publisher.config()['exports']:
            raw = json.loads((publisher.ROOT / export['path']).read_text())
            self.assertEqual(raw['specification'], {'blueId': self.e.rules}, export['name'])
            self.assertIn('Coordination/' + export['name'], self.e.aliases)

    def test_distribution_has_one_example_document_and_fixture(self):
        self.assertEqual(publisher.config()['files'], ['docs/examples.md', 'examples/protocol.json'])
        names = {e['name'] for e in publisher.config()['exports']}
        self.assertIn('Agent Actor', names)
        self.assertNotIn('Provider Actor', names)

    def test_optional_predecessor_is_absent_at_genesis(self):
        p = ModelProvider(self.e)
        t = p.create('alice', 'package-genesis', public=True)
        entry = p.append('alice', t, 'hello', 'hello', 100)
        exact = json.loads(self.e.language.load(self.e.identity(entry)).exact_text)
        self.assertNotIn('prevEntry', exact)
        self.assertNotIn('operation', exact)

    def test_short_key_fails_semantic_schema(self):
        with self.assertRaises(Exception):
            self.e.put({'type': 'Coordination/Ed25519 Public Key', 'value': 'abcd'})

    def test_uppercase_key_fails_protocol_encoding(self):
        with self.assertRaisesRegex(ValueError, 'INVALID_HEX'):
            hexbytes('AB' * 32, 32)

    def test_frozen_rules_cannot_change_silently(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(publisher.ROOT / 'spec', root / 'spec')
            with (root / 'spec/coordination.md').open('a') as f:
                f.write('\nUnreviewed semantic change.\n')
            with self.assertRaisesRegex(ValueError, 'frozen specification mismatch'):
                publisher.current_ledger(root)

    def test_missing_source_specification_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ('blue-package.yaml', 'blue-package.lock.json'):
                shutil.copyfile(publisher.ROOT / name, root / name)
            shutil.copytree(publisher.ROOT / 'spec', root / 'spec')
            shutil.copytree(publisher.ROOT / 'types', root / 'types')
            target = root / publisher.config()['exports'][0]['path']
            raw = json.loads(target.read_text())
            del raw['specification']
            target.write_text(json.dumps(raw))
            with patch.object(publisher, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Incorrect source specification'):
                    publisher.context()

if __name__ == '__main__':
    unittest.main()
