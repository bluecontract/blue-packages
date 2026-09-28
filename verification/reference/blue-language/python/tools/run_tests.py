#!/usr/bin/env python3
"""Run public API and runner tests with machine-readable case results."""
import argparse,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
class Result(unittest.TextTestResult):
    def __init__(self,*args,**kw):super().__init__(*args,**kw);self.rows=[]
    def addSuccess(self,test):super().addSuccess(test);self.rows.append({'id':test.id(),'status':'PASS'})
    def addFailure(self,test,err):super().addFailure(test,err);self.rows.append({'id':test.id(),'status':'FAIL','detail':self._exc_info_to_string(err,test)})
    def addError(self,test,err):super().addError(test,err);self.rows.append({'id':test.id(),'status':'ERROR','detail':self._exc_info_to_string(err,test)})
    def addSkip(self,test,reason):super().addSkip(test,reason);self.rows.append({'id':test.id(),'status':'SKIP','detail':reason})
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.defaultTestLoader.discover(str(ROOT/'tests/language')))
summary={'tests':r.testsRun,'passed':sum(x['status']=='PASS'for x in r.rows),'failed':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'cases':r.rows}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items()if k!='cases'},sort_keys=True))
sys.exit(0 if r.wasSuccessful()and not r.skipped else 1)
