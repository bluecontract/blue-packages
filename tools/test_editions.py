"""Standard commands select Access Events; Demand is an explicit, isolated candidate."""
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
import unittest

from editions import edition_root, require_built, mark_built

ROOT = Path(__file__).resolve().parents[1]


class EditionTests(unittest.TestCase):
    def fixture(self, root):
        snapshot = root / 'editions/demand-scoped'
        snapshot.mkdir(parents=True)
        (root / 'docs').mkdir()
        (root / 'retained').mkdir()
        package = root / 'example'
        package.mkdir()
        (package / 'type.blue').write_text('old source')
        (package / 'blue-package.yaml').write_text('{}')
        archive = root / 'original.bluepkg'
        with zipfile.ZipFile(archive, 'w') as output:
            output.writestr('package.json', '{}')
        digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        manifest = dict(files={'example/type.blue': dict(overlay=False, sha256=digest(package / 'type.blue'))},
            sharedConfigs={'example/blue-package.yaml': digest(package / 'blue-package.yaml')},
            archives={'example': dict(path='original.bluepkg', sha256=digest(archive))})
        (snapshot / 'edition.json').write_text(json.dumps(manifest))

    def test_changed_shared_source_requires_build_and_built_output_is_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            (root / 'example/type.blue').write_text('new source')
            selected = edition_root(root, 'demand-scoped')
            self.assertEqual('new source', (selected / 'example/type.blue').read_text())
            with self.assertRaisesRegex(ValueError, 'sources changed'):
                require_built(selected)
            (selected / 'example/dist/package.bluepkg').write_bytes(b'rebuilt candidate')
            mark_built(selected)
            self.assertEqual(selected, edition_root(root, 'demand-scoped'))
            require_built(selected)
            self.assertEqual(b'rebuilt candidate', (selected / 'example/dist/package.bluepkg').read_bytes())

    def test_shared_interface_drift_fails_instead_of_silently_omitting_new_exports(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            (root / 'example/blue-package.yaml').write_text('{"exports": ["new"]}')
            with self.assertRaisesRegex(ValueError, 'interface changed'):
                edition_root(root, 'demand-scoped')

    def test_default_is_access_events_root(self):
        self.assertEqual(ROOT, edition_root(ROOT))
        config = json.loads((ROOT / 'PACKAGE-SOURCES.json').read_text())
        self.assertEqual('core-java-access-events', config['runtimeProfile'])

    def test_unknown_edition_fails(self):
        with self.assertRaisesRegex(ValueError, 'Unknown edition'):
            edition_root(ROOT, 'typo')

    def test_demand_is_explicit_isolated_and_keeps_native_identity(self):
        selected = edition_root(ROOT, 'demand-scoped')
        self.assertNotEqual(ROOT, selected)
        rows = {r['namespace']: r for r in json.loads((selected / 'PACKAGES.json').read_text())['packages']}
        self.assertEqual('Cj2SnbMNz9VkQg9Dc7hzEoy7GdBUYqTfzh1XCKu5ANSr', rows['Contracts']['packageBlueId'])
        self.assertEqual('8LBAZGgzAvrDRHxbHDGhb3DTPZyZUgJeKMEq3xBrLo8C', rows['Coordination']['packageBlueId'])


if __name__ == '__main__':
    unittest.main()
