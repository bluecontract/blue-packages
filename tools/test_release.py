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

    def test_current_catalogue_and_generated_views_are_consistent(self):
        rows = release.selections(release.ROOT)
        self.assertEqual(34, len(rows))
        self.assertTrue({'blue-dispatch', 'clause-inspection', 'clause-attachments'} <= {row['name'] for row in rows})
        self.assertEqual(1, sum(row['name'] == 'blue-mandates' for row in rows))
        self.assertEqual(1, sum(row['name'] == 'blue-tasks' for row in rows))
        self.assertFalse((release.ROOT / 'editions').exists())
        self.assertEqual({row['directory'] for row in rows},
                         {row['path'].split('/')[0] for row in rows})

    def test_historical_gas_fixtures_keep_exact_publications(self):
        for name in ('blue-bex', 'blue-contracts'):
            folder=release.ROOT / 'verification/fixtures'
            pin=json.loads((folder / (name + '-100k.json')).read_text())
            data=(folder / (name + '-100k.bluepkg')).read_bytes()
            self.assertEqual(pin['archiveSha256'], release.digest(data))
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                manifest=json.loads(archive.read('package.json'))
                self.assertEqual(pin['packageBlueId'], manifest['packageBlueId'])
            current=json.loads((release.ROOT / name / 'dist/package.json').read_text())
            self.assertNotEqual(current['packageBlueId'], pin['packageBlueId'])

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

    def distribution_fixture(self, root):
        (root / 'docs').mkdir()
        (root / 'docs/distribution.md').write_text('Distribution')
        (root / 'blue-language').mkdir()
        (root / 'blue-language/THIRD-PARTY-NOTICES.md').write_text('Notices')
        row, data = release.check_archive(root, self.fixture(root))
        edition_data = b'Exact root-clause edition bytes'
        edition = dict(row, version='0.2.0-preview.1', selection='root-clause-edition',
                       path='fixtures/second/example.bluepkg',
                       packageBlueId='edition-id', archiveSha256=release.digest(edition_data))
        return {'packages': [row, edition]}, {row['path']: data, edition['path']: edition_data}

    def test_assets_preserve_variants_identities_and_checksums(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalogue, payloads = self.distribution_fixture(root)
            (root / 'private.txt').write_text('Must not be published')
            first, second = root / 'first', root / 'second'
            release.assets(first, catalogue, payloads, root)
            release.assets(second, catalogue, payloads, root)
            uploaded = {p.name: p.read_bytes() for p in first.iterdir()}
            self.assertEqual(uploaded, {p.name: p.read_bytes() for p in second.iterdir()})
            published = json.loads(uploaded['CATALOG.json'])
            expected_names = {'blue-packages.zip', 'CATALOG.json', 'README.md',
                              'THIRD-PARTY-NOTICES.md', 'SHA256SUMS'}
            for original, row in zip(catalogue['packages'], published['packages']):
                expected_names.add(row['releaseAsset'])
                self.assertEqual({k: v for k, v in row.items() if k != 'releaseAsset'}, original)
                self.assertEqual(uploaded[row['releaseAsset']], payloads[row['path']])
            self.assertEqual(set(uploaded), expected_names)
            checksums = dict(line.split('  ', 1)[::-1]
                             for line in uploaded['SHA256SUMS'].decode().splitlines())
            self.assertEqual(set(checksums), set(uploaded) - {'SHA256SUMS'})
            for name, expected in checksums.items():
                self.assertEqual(expected, hashlib.sha256(uploaded[name]).hexdigest())
            with zipfile.ZipFile(first / 'blue-packages.zip') as archive:
                self.assertEqual(archive.read('CATALOG.json'), uploaded['CATALOG.json'])
                for path, data in payloads.items():
                    self.assertEqual(archive.read(path), data)

    def test_assets_reject_colliding_or_unsafe_filenames_before_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalogue, payloads = self.distribution_fixture(root)
            output = root / 'release'
            catalogue['packages'][1]['version'] = catalogue['packages'][0]['version']
            with self.assertRaisesRegex(ValueError, 'Duplicate release asset'):
                release.assets(output, catalogue, payloads, root)
            self.assertFalse(output.exists())
            for key, value in [('name', '../escape'), ('version', '1.0/escape'),
                               ('version', '1.0#asset-label'), ('name', '-option')]:
                with self.subTest(key=key, value=value):
                    row = dict(catalogue['packages'][0], **{key: value})
                    with self.assertRaisesRegex(ValueError, 'Unsafe release asset'):
                        release.assets(output, {'packages': [row]},
                                       {row['path']: payloads[row['path']]}, root)
                    self.assertFalse(output.exists())

    def test_assets_reject_changed_or_unselected_payloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalogue, payloads = self.distribution_fixture(root)
            output = root / 'release'
            with self.assertRaisesRegex(ValueError, 'Release payloads differ'):
                release.assets(output, catalogue, dict(payloads, private=b'Unselected'), root)
            changed = dict(payloads)
            changed[catalogue['packages'][0]['path']] = b'Changed archive'
            with self.assertRaisesRegex(ValueError, 'Release payload checksum differs'):
                release.assets(output, catalogue, changed, root)
            self.assertFalse(output.exists())

    def test_assets_do_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalogue, payloads = self.distribution_fixture(root)
            output = root / 'release'
            release.assets(output, catalogue, payloads, root)
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            with self.assertRaises(FileExistsError):
                release.assets(output, catalogue, payloads, root)
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})


if __name__ == '__main__':
    unittest.main()
