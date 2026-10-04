"""Validate the public authoring parameter with the real Language facade."""
from pathlib import Path
import json,unittest
from blue_packages import Runtime,read_package,mount
from blue_language import Failure
from blue_language.physical import PhysicalCache
ROOT=Path(__file__).resolve().parents[1]

class TerminationTermsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache=PhysicalCache(65536).scope();cls.cache.__enter__()
        cls.runtime=Runtime.agreements();cls.package=read_package(ROOT/'dist/package.bluepkg')
        cls.runtime.require(cls.package);cls.language=cls.runtime.language()
        mount(cls.language,cls.package,'ImmediateTermination',list(cls.package.exports))
    @classmethod
    def tearDownClass(cls):cls.cache.__exit__(None,None,None)
    def create(self,**fields):
        return self.language.create(json.dumps({'type':'ImmediateTermination/Immediate Termination Terms',**fields}))
    def test_all_three_options_are_valid(self):
        for option in ('A','B','EITHER'):
            with self.subTest(option=option):self.assertTrue(self.create(allowedParty=option).blue_id)
    def test_missing_option_is_rejected(self):
        with self.assertRaises(Failure):self.create()
    def test_unknown_and_wrongly_typed_options_are_rejected(self):
        for option in ('ANY','BOTH','partyA','',0,True,None):
            with self.subTest(option=option),self.assertRaises(Failure):self.create(allowedParty=option)

if __name__=='__main__':unittest.main(verbosity=2)
