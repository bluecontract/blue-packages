"""Exercise the real Time builder against disposable source copies."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = """
import importlib.util
from pathlib import Path
import sys
spec = importlib.util.spec_from_file_location('time_builder', sys.argv[1])
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
builder.ROOT = Path(sys.argv[2])
sys.argv = [sys.argv[1], 'check-source']
from blue_language.physical import PhysicalCache
with PhysicalCache(131072).scope():
    builder.main()
"""


class LockedTimeBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='blue-time-build-tests-')
        cls.root = Path(cls.tmp.name).resolve()
        cls.project = cls.root / 'blue-time'
        shutil.copytree(ROOT / 'blue-time', cls.project)
        for name in ('blue-language', 'blue-bex', 'blue-contracts', 'blue-coordination'):
            target = cls.root / name / 'dist'
            target.mkdir(parents=True)
            shutil.copyfile(ROOT / name / 'dist/package.bluepkg', target / 'package.bluepkg')
        cls.source_files = {p.relative_to(cls.project): p.read_bytes()
                            for p in cls.project.rglob('*') if p.is_file()}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        for name, data in self.source_files.items():
            (self.project / name).write_bytes(data)

    def state(self):
        return {p.relative_to(self.project).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.project.rglob('*') if p.is_file()}

    def check(self, error=None):
        before = self.state()
        result = subprocess.run(
            [sys.executable, '-c', RUNNER, str(ROOT / 'blue-time/tools/package.py'), str(self.project)],
            capture_output=True, text=True,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=300)
        if error is None:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)['verified'])
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(error, result.stderr)
        self.assertEqual(self.state(), before)

    def test_unchanged_sources_reproduce_publication_without_writes(self):
        self.check()

    def test_missing_specification_is_rejected_without_writes(self):
        path = self.project / 'types/timer-channel.blue'
        raw = json.loads(path.read_text())
        del raw['specification']
        path.write_text(json.dumps(raw))
        self.check('timer-channel.blue: specification must explicitly reference')

    def test_protocol_descriptor_cannot_replace_rules_reference(self):
        path = self.project / 'types/timer-channel.blue'
        raw = json.loads(path.read_text())
        manifest = json.loads((self.project / 'dist/package.json').read_text())
        raw['specification'] = {'blueId': manifest['protocol']}
        path.write_text(json.dumps(raw))
        self.check('timer-channel.blue: specification must explicitly reference')

    def test_edited_rules_fail_frozen_check_without_writes(self):
        path = self.project / 'spec/time.md'
        path.write_text(path.read_text() + '\nNew normative rule.\n')
        self.check('frozen specification mismatch')


if __name__ == '__main__':
    unittest.main(verbosity=2)
