#!/usr/bin/env python3
"""Verify locked clause/agreement publications using the installed Python toolchain.

Ordinary builds are read-only when dist exists. A changed source or dependency
requires an explicit candidate, then review and selection outside this tool.
No foundation package is rebuilt and no native support is registered here.
"""
from pathlib import Path
import argparse
import json
import os
import tempfile
# Reuse the installed-toolchain adapter and locked dependency reader, not a
# historical runtime from a package's verification material.
from build_mandates import ROOT, locked_dependencies, check_dist, write_set
from package_core import build, wire, Language, Repository, sha, source, verify_bytes, require
from blue_language.physical import PhysicalCache
from blue_runtime.core_reuse import core_reuse_scope

NAMES = ('clause-mutual-activation', 'clause-immediate-termination', 'agreement-reseller')
REVISION = 'reseller-clauses-20260928-1'
REVISIONS = {'agreement-reseller': 'reseller-explicit-channels-20260928-2'}


def compile_locked(project, *, refresh=False, revision=REVISION, version=None):
    config = json.loads((project/'blue-package.yaml').read_text())
    require(config['name'] in NAMES, 'Select one of the clause/agreement packages')
    with PhysicalCache(65536).scope(), core_reuse_scope():
        dependencies, pins = locked_dependencies(project, config, refresh=refresh)
    with tempfile.TemporaryDirectory(prefix='blue-clauses-build-') as tmp, PhysicalCache(65536).scope(), core_reuse_scope():
        stage=Path(tmp).resolve()
        for name in {config['readme'], *config.get('files', []), *(e['path'] for e in config['exports'])}:
            target=stage/name
            require(target.resolve().is_relative_to(stage), 'unsafe authored path')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((project/name).read_bytes())
        (stage/'inputs').mkdir()
        stage_pins=json.loads(json.dumps(pins))
        for prefix, entry in config['imports'].items():
            path='inputs/'+prefix+'.bluepkg'
            (stage/path).write_bytes(dependencies[prefix].archive)
            entry['path']=path;stage_pins['imports'][prefix]['path']=path
        language=Language(core_contracts=False)
        for prefix, dependency in dependencies.items():
            language.enable_repository(Repository.from_payload('import:'+prefix,
                {prefix+'/'+e['name']:e['blueId'] for e in dependency.manifest['exports']},dependency.repository.records))
        aliases={}
        for entry in config['exports']:
            alias=config['namespace']+'/'+entry['name']
            doc=language.admit_definition(wire(source((stage/entry['path']).read_bytes())).decode(),format='json')
            language.publish_document(doc);language.aliases[alias]=doc.blue_id;aliases[alias]=doc.blue_id
        repository=Repository.from_payload(config['name'],aliases,language.provider.snapshot())
        data=(repository._json+'\n').encode();relative='inputs/authored.repository.json'
        (stage/relative).write_bytes(data)
        config['inputs']=[{'path':relative,'sha256':sha(data),'identity':repository.identity}]
        config['exports']=[{'name':e['name'],'fromInput':relative,'inputAlias':config['namespace']+'/'+e['name']} for e in config['exports']]
        if version:config['version']=version
        (stage/'blue-package.yaml').write_bytes(wire(config))
        (stage/'blue-package.lock.json').write_bytes(wire(stage_pins))
        package=build(stage,revision=revision,source_url='');verify_bytes(package.archive)
        return package,pins


def selection(name,package):
    return dict(name=name,path=name+'/dist/package.bluepkg',packageBlueId=package.manifest['packageBlueId'],archiveSha256=package.archive_sha)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('build','check','candidate'),default='check',nargs='?')
    parser.add_argument('--package',choices=NAMES)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--revision');parser.add_argument('--version')
    parser.add_argument('--refresh-lock',action='store_true')
    args=parser.parse_args();candidate=args.command=='candidate'
    if candidate:
        if not all((args.package,args.output,args.revision,args.version)):
            parser.error('candidate requires --package, new --output, --revision and --version')
        require(not args.output.exists(),'Candidate destination already exists')
    elif args.output or args.revision or args.version or args.refresh_lock:
        parser.error('revision and lock changes require candidate')
    rows=[]
    for name in (args.package,) if args.package else NAMES:
        project=ROOT/name
        package,pins=compile_locked(project,refresh=args.refresh_lock,
            revision=args.revision or REVISIONS.get(name, REVISION),version=args.version)
        row=selection(name,package)
        if candidate:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(dir=args.output.parent,prefix='.candidate-') as tmp:
                staged=Path(tmp)/'release';staged.mkdir()
                write_set(staged/'dist',package)
                (staged/'blue-package.lock.json').write_bytes(wire(pins))
                (staged/'REVIEW.json').write_bytes(wire(dict(selection=row,exports=package.manifest['exports'],nativeSupportChanged=False)))
                os.rename(staged,args.output)
        else:
            inventory=json.loads((ROOT/'SHARED-PACKAGES.json').read_text())
            require(row==next(r for r in inventory['packages'] if r['name']==name),'Unselected build; review a candidate explicitly')
            if (project/'dist').exists():check_dist(project,package)
            elif args.command=='check':raise ValueError('Missing dist: '+name)
            else:
                with tempfile.TemporaryDirectory(dir=project,prefix='.build-') as tmp:
                    staged=Path(tmp)/'dist';write_set(staged,package);os.rename(staged,project/'dist')
        rows.append(row)
    print(json.dumps({'command':args.command,'packages':rows},indent=2))

if __name__=='__main__':main()
