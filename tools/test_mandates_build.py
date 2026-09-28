"""Failure preservation and source-vs-archive verification of the real builder."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import build_mandates as builder
from blue_packages import PackageStore, PackageError
from blue_packages.reader import read_package


class LockedBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='blue-build-tests-');cls.root=Path(cls.tmp.name).resolve()
        cls.project=cls.root/'blue-mandates'
        shutil.copytree(builder.ROOT/'blue-mandates',cls.project)
        for name in ('blue-language','blue-bex','blue-contracts','blue-coordination'):
            target=cls.root/name/'dist';target.mkdir(parents=True)
            shutil.copyfile(builder.ROOT/name/'dist/package.bluepkg',target/'package.bluepkg')
        cls.source_files={p.relative_to(cls.project):p.read_bytes() for p in cls.project.rglob('*') if p.is_file()}
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def setUp(self):
        for name,data in self.source_files.items():(self.project/name).write_bytes(data)
    def state(self):
        return {str(p.relative_to(self.project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.project.rglob('*')
                if p.is_file() and ('dist' in p.parts or p.name in ('blue-package.lock.json','native-support.json'))}
    def run_command(self,*args):
        with contextlib.redirect_stdout(io.StringIO()):builder.main([*args,'--root',str(self.project)])
    def test_01_unchanged_locked_build_and_check_are_identical_and_read_only(self):
        before=self.state();self.run_command('check');self.run_command('build');self.assertEqual(self.state(),before)
    def test_02_unapproved_export_preserves_every_published_file(self):
        p=self.project/'types/operation-grant.blue';p.write_text(p.read_text()+'\nreviewProbe: example\n')
        before=self.state()
        read_package(self.project/'dist/package.bluepkg') # Old archive is still valid.
        with self.assertRaisesRegex(ValueError,'Unapproved type identities'):self.run_command('build')
        self.assertEqual(self.state(),before)
    def test_03_edited_rules_fail_source_check_without_publishing(self):
        p=self.project/'spec/mandates.md';p.write_text(p.read_text()+'\nNew normative rule.\n')
        before=self.state();read_package(self.project/'dist/package.bluepkg')
        with self.assertRaisesRegex(ValueError,'frozen specification mismatch'):self.run_command('check')
        self.assertEqual(self.state(),before)
    def test_04_dependency_drift_and_invalid_source_do_not_publish(self):
        p=self.project/'blue-package.lock.json';pins=json.loads(p.read_text());pins['imports']['bex']['archiveSha256']='sha256:'+'0'*64;p.write_text(json.dumps(pins))
        before=self.state()
        with self.assertRaisesRegex(ValueError,'Dependency lock mismatch'):self.run_command('build')
        self.assertEqual(self.state(),before)
        self.setUp();(self.project/'types/operation-grant.blue').write_text('invalid: [')
        before=self.state()
        with self.assertRaises(Exception):self.run_command('build')
        self.assertEqual(self.state(),before)
    def test_05_invalid_supporting_record_and_loose_file_drift(self):
        package=read_package(self.project/'dist/package.bluepkg')
        loose=self.project/'dist/package-records.json';loose.write_text('{}')
        before=self.state()
        with self.assertRaisesRegex(ValueError,'unpacked files'):self.run_command('check')
        self.assertEqual(self.state(),before)
        # Corrupted dependency closure is detected before compilation/promotion.
        dep=self.root/'blue-bex/dist/package.bluepkg';original=dep.read_bytes();dep.write_bytes(b'invalid archive')
        try:
            with self.assertRaises(Exception):self.run_command('build')
            self.assertEqual(self.state(),before)
        finally:dep.write_bytes(original)
    def test_06_interrupted_candidate_does_not_advertise_partial_release(self):
        before=self.state();destination=self.root/'interrupted'
        with patch.object(builder.os,'rename',side_effect=OSError('interrupted before promotion')):
            with self.assertRaisesRegex(OSError,'interrupted'):
                self.run_command('candidate','--output',str(destination),'--revision','candidate-test','--version','0.1.0-preview.3')
        self.assertFalse(destination.exists());self.assertEqual(self.state(),before)
    def test_07_candidate_has_new_immutable_ids_but_no_native_approval(self):
        p=self.project/'types/operation-grant.blue';p.write_text(p.read_text()+'\nreviewProbe: example\n')
        before=self.state();destination=self.root/'candidate'
        self.run_command('candidate','--output',str(destination),'--revision','test-reviewed-edit','--version','0.1.0-preview.3')
        self.assertEqual(self.state(),before)
        review=json.loads((destination/'REVIEW.json').read_text());self.assertFalse(review['approvedNativeSupport'])
        package=read_package(destination/'dist/package.bluepkg')
        self.assertNotEqual(package.blue_id,read_package(self.project/'dist/package.bluepkg').blue_id)
        vendor=self.root/'consumer';path=vendor/'blue-mandates/dist';path.mkdir(parents=True)
        shutil.copyfile(destination/'dist/package.bluepkg',path/'package.bluepkg')
        with self.assertRaises(PackageError):PackageStore(vendor).package('blue-mandates')
        with self.assertRaisesRegex(ValueError,'already exists'):
            self.run_command('candidate','--output',str(destination),'--revision','another','--version','0.1.0-preview.4')

if __name__=='__main__':unittest.main(verbosity=2)
