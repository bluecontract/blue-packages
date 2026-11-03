"""A complete source inventory builds in dependency order, never using stale downstream archives."""
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from build_final_gas import dependency_order, export_sources


class DependencyOrderTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def package(self, name, dependencies=()):
        folder = self.root / name
        folder.mkdir()
        (folder / 'blue-package.yaml').write_text(json.dumps({
            'imports': {dep: {'path': '../' + dep + '/dist/package.bluepkg'} for dep in dependencies}
        }))

    def test_reordered_inventory_keeps_the_complete_dependency_closure(self):
        self.package('language')
        self.package('documents', ['language'])
        self.package('payment', ['documents', 'language'])
        self.package('inspection', ['documents'])
        self.assertEqual(['language', 'documents', 'payment', 'inspection'],
                         dependency_order(self.root, ['payment', 'inspection', 'documents', 'language']))

    def test_missing_dependency_is_not_satisfied_by_an_old_archive(self):
        self.package('payment', ['documents'])
        self.package('documents')
        with self.assertRaisesRegex(ValueError, 'absent from the source inventory'):
            dependency_order(self.root, ['payment'])

    def test_shell_builder_rejects_removed_edition_option_before_building(self):
        script = Path(__file__).resolve().parent / 'build-payment-family.sh'
        result = subprocess.run(['bash', str(script), '--edition', 'demand-scoped'],
                                text=True, capture_output=True)
        self.assertEqual(2, result.returncode)
        self.assertIn('Unsupported option: --edition', result.stderr)

    def test_cycle_fails_before_building(self):
        self.package('a', ['b'])
        self.package('b', ['a'])
        with self.assertRaisesRegex(ValueError, 'cycle'):
            dependency_order(self.root, ['a', 'b'])

    def test_external_import_cannot_escape_the_inventory(self):
        self.package('payment')
        (self.root / 'payment/blue-package.yaml').write_text(json.dumps({
            'imports': {'external': {'path': '../../outside/dist/package.bluepkg'}}
        }))
        with self.assertRaisesRegex(ValueError, 'Unsupported package import path'):
            dependency_order(self.root, ['payment'])


    def test_undeclared_retained_execution_archive_is_not_an_active_dependency(self):
        self.package('representation')
        manifest = self.root / 'representation/blue-package.yaml'
        manifest.write_text(json.dumps({'imports': {'Mandates': {
            'path': '../verification/publications/mandates-v1/dist/package.bluepkg',
            'packageBlueId': 'retained-test-identity', 'archiveSha256': 'sha256:' + '0' * 64,
        }}, 'executionRequires': ['Mandates']}))
        with self.assertRaisesRegex(ValueError, 'Unsupported package import path'):
            dependency_order(self.root, ['representation'])

class SharedExportSourcesTest(unittest.TestCase):
    def test_only_declared_shared_file_is_selected_with_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'direct'
            source.mkdir()
            shared = root / 'myos/types/helper.blue'
            shared.parent.mkdir(parents=True)
            shared.write_bytes(b'name: shared\n')
            (shared.parent / 'unrelated.blue').write_text('excluded')
            selected = export_sources(root, source, {'exports': [{'path': '../myos/types/helper.blue'}]})
            self.assertEqual([(shared, Path('myos/types/helper.blue'))], selected)
            self.assertEqual(b'name: shared\n', selected[0][0].read_bytes())

    def test_outside_traversal_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / 'repo'
            source = root / 'direct'
            source.mkdir(parents=True)
            outside = parent / 'outside.blue'
            outside.write_text('outside')
            (source / 'link.blue').symlink_to(outside)
            for path in ('../../outside.blue', 'link.blue'):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    export_sources(root, source, {'exports': [{'path': path}]})

    def test_internal_symlink_is_explicitly_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'helper.blue').write_text('shared')
            (root / 'link.blue').symlink_to(root / 'helper.blue')
            with self.assertRaisesRegex(ValueError, 'Symlink export'):
                export_sources(root, root, {'exports': [{'path': 'link.blue'}]})


if __name__ == '__main__':
    unittest.main()
