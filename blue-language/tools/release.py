#!/usr/bin/env python3
"""Local Language release build/verification. No network and no expected-ID rewrite."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, zipfile, shutil
from pathlib import Path
import bootstrap
from package_core import build, read_package
ROOT=bootstrap.ROOT

def check_reference():
    failures=[]
    for name,digest in bootstrap.SOURCE_LOCK['files'].items():
        p=ROOT.parent/'verification/reference/blue-language/python'/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest: failures.append(name)
    if failures: raise RuntimeError('reference differs from source lock: '+', '.join(failures))
    return len(bootstrap.SOURCE_LOCK['files'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['build','verify','inspect','test'])
    p.add_argument('archive',nargs='?',type=Path,default=ROOT/'dist/package.bluepkg')
    a=p.parse_args(); n=check_reference()
    if a.command=='build':
        # Copies are transport layout, not independent sources of truth.
        shutil.copyfile(ROOT/'SPECIFICATION.md',ROOT/'spec/language.md')
        for path in (ROOT/'types').glob('*.json'):
            shutil.copyfile(path,ROOT/'docs/types'/path.name)
        result=build(ROOT,output=a.archive,revision='blue-language-1.0-2026-09-26',source_url='')
        a.archive.parent.mkdir(parents=True,exist_ok=True)
        for name,data in result.files.items():
            target=a.archive.parent/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        print(json.dumps({'packageBlueId':result.manifest['packageBlueId'],'archiveSha256':result.archive_sha,'audit':result.audit,'referenceFilesVerified':n},indent=2))
        return 0
    if a.command in ('verify','inspect'):
        result=read_package(a.archive)
        data={'verified':True,'referenceFilesVerified':n,'packageBlueId':result.manifest['packageBlueId'],'archiveSha256':result.archive_sha,'exports':result.manifest['exports'],'audit':result.audit}
        expected=ROOT/'release.json'
        if expected.is_file():
            selected=json.loads(expected.read_text())
            if result.manifest['packageBlueId']!=selected['packageBlueId']:raise RuntimeError('verified content differs from release selection')
            if result.archive_sha!=selected['archiveSha256']:raise RuntimeError('archive differs from release selection')
        if a.command=='inspect':data['package']=result.manifest['semanticPackages'][result.manifest['packageBlueId']]
        print(json.dumps(data,indent=2,ensure_ascii=False));return 0
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT.parent/'verification/reference/blue-language/python/src')+os.pathsep+str(ROOT.parent/'verification/reference/blue-language/python'))
    commands=[
        [sys.executable,str(ROOT.parent/'verification/reference/blue-language/python/tools/run.py'),str(ROOT/'conformance/language-cases.jsonl')],
        [sys.executable,str(ROOT.parent/'verification/reference/blue-language/python/tools/run.py'),str(ROOT/'conformance/language-edge-cases.jsonl')],
        [sys.executable,'-m','pytest','-q',str(ROOT.parent/'verification/reference/blue-language/python/tests/metadata/test_specification_metadata.py')],
        [sys.executable,'-m','pytest','-q',str(ROOT.parent/'verification/reference/blue-language/python/tests/language')],
        [sys.executable,'-m','pytest','-q',str(ROOT/'tests')],
    ]
    for cmd in commands:
        status=subprocess.run(cmd,cwd=ROOT,env=env).returncode
        if status:return status
    return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'status':'FAIL','error':str(exc)}),file=sys.stderr);raise SystemExit(1)
