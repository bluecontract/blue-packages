"""Bounded integrity/export tests; no runtime benchmark or network access."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location('package_release', Path(__file__).with_name('release.py'))
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def fixture(self, root, *, extra=None):
        folder = root / 'example'
        dist = folder / 'dist'
        dist.mkdir(parents=True)
        files = {'README.md': b'Definitions\n'}
        manifest = dict(packageBlueId='example-id', version='0.1.0', imports={},
                        semanticPackages={}, exports=[], protocol=None,
                        files={name: dict(sha256=release.digest(data), size=len(data)) for name, data in files.items()})
        files['package.json'] = release.wire(manifest)
        if extra:
            files.update(extra)
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        data = output.getvalue()
        (dist / 'package.bluepkg').write_bytes(data)
        for name, content in files.items():
            if '..' not in name:
                (dist / name).write_bytes(content)
        (folder / 'blue-package.lock.json').write_text('{"imports": {}}')
        return dict(name='example', path='example/dist/package.bluepkg',
                    archiveSha256=release.digest(data), packageBlueId='example-id', selection='shared')

    def test_rejects_changed_archive_and_unpacked_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = self.fixture(root)
            release.check_archive(root, row)
            (root / 'example/dist/README.md').write_bytes(b'Changed')
            with self.assertRaisesRegex(ValueError, 'Unpacked distribution'):
                release.check_archive(root, row)
            (root / row['path']).write_bytes(b'Changed')
            with self.assertRaisesRegex(ValueError, 'Archive checksum'):
                release.check_archive(root, row)

    def test_rejects_unsafe_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = self.fixture(root, extra={'../escape': b'bad'})
            with self.assertRaisesRegex(ValueError, 'Unsafe archive member'):
                release.check_archive(root, row)

    def test_bundle_is_deterministic_and_contains_only_selected_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'docs').mkdir()
            (root / 'docs/distribution.md').write_text('Distribution')
            (root / 'blue-language').mkdir()
            (root / 'blue-language/THIRD-PARTY-NOTICES.md').write_text('Notices')
            (root / 'private.txt').write_text('Must not be bundled')
            payloads = {'example/dist/package.bluepkg': b'Exact archive bytes'}
            first, second = root / 'a.zip', root / 'b.zip'
            release.bundle(first, {'packages': []}, payloads, root)
            release.bundle(second, {'packages': []}, payloads, root)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(set(archive.namelist()), {*payloads, 'CATALOG.json', 'README.md', 'THIRD-PARTY-NOTICES.md', 'SHA256SUMS'})
                for line in archive.read('SHA256SUMS').decode().splitlines():
                    expected, name = line.split('  ', 1)
                    self.assertEqual(expected, hashlib.sha256(archive.read(name)).hexdigest())
            with self.assertRaises(FileExistsError):
                release.bundle(first, {}, {}, root)
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == '__main__':
    unittest.main()
