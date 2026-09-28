#!/usr/bin/env python3
"""Locked, staged Mandates construction. Never refresh or publish implicitly."""
from pathlib import Path
import argparse
import atexit
import importlib.resources
import json
import os
import shutil
import sys
import tempfile
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blue-contracts/tools'))
# The generic distribution adapter needs two standard *data* definitions. Use
# the installed library, never a historical implementation from this workspace.
_standard = tempfile.TemporaryDirectory(prefix='blue-package-standard-')
atexit.register(_standard.cleanup)
standard = Path(_standard.name) / 'python/src/registry/standard'
standard.mkdir(parents=True)
for name in ('Package.json', 'ProtocolSpecification.json'):
    (standard / name).write_bytes((importlib.resources.files('registry') / 'standard' / name).read_bytes())
bootstrap = types.ModuleType('bootstrap')
bootstrap.WORKSPACE = Path(_standard.name)
bootstrap.ROOT = ROOT / 'blue-contracts'
bootstrap.LOCK = {'blue': {'archiveSha256': json.loads((ROOT / 'blue-mandates/provenance/import.json').read_text())['sha256']}}
sys.modules['bootstrap'] = bootstrap
from package_core import build, wire, Language, Repository, sha, source, verify_bytes, read_package, require
from blue_language.physical import PhysicalCache


def locked_dependencies(project, config, *, refresh=False):
    packages = {prefix: read_package(project / entry['path']) for prefix, entry in config['imports'].items()}
    pins = {'format': 2, 'imports': {prefix: {
        'path': config['imports'][prefix]['path'], 'packageBlueId': p.manifest['packageBlueId'],
        'archiveSha256': p.archive_sha, 'repositoryIdentity': p.repository.identity,
        'name': p.manifest['name'], 'version': p.manifest['version'],
        **({'source': config['imports'][prefix]['source']} if config['imports'][prefix].get('source') else {})
    } for prefix, p in packages.items()}}
    if not refresh:
        require(pins == json.loads((project / 'blue-package.lock.json').read_text()),
                'Dependency lock mismatch; ordinary build/check never refresh selections')
    return packages, pins


def compile_locked(project, *, revision='shared-mandates-20260927-2', version=None, refresh=False):
    config = json.loads((project / 'blue-package.yaml').read_text())
    dependencies, pins = locked_dependencies(project, config, refresh=refresh)
    with tempfile.TemporaryDirectory(prefix='blue-mandates-build-') as tmp, PhysicalCache(65536).scope():
        stage = Path(tmp).resolve()
        # Copy only declared source inputs; no dist, environments or old runtime.
        names = {config['readme'], config['protocol']['rules'], 'spec/frozen.json', *config.get('files', [])}
        names.update(entry['path'] for entry in config['exports'])
        for name in names:
            target=stage/name
            require(target.resolve().is_relative_to(stage), 'unsafe authored path')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((project/name).read_bytes())
        (stage/'inputs').mkdir()
        stage_pins = json.loads(json.dumps(pins))
        for prefix, entry in config['imports'].items():
            path='inputs/'+prefix+'.bluepkg'
            (stage/path).write_bytes(dependencies[prefix].archive)
            entry['path']=path
            stage_pins['imports'][prefix]['path']=path
        language=Language(core_contracts=False)
        for prefix, dependency in dependencies.items():
            language.enable_repository(Repository.from_payload('import:'+prefix,
                {prefix+'/'+e['name']:e['blueId'] for e in dependency.manifest['exports']}, dependency.repository.records))
        rules=language.create(wire((stage/config['protocol']['rules']).read_text()).decode(),format='json')
        language.publish_document(rules)
        aliases={}
        for entry in config['exports']:
            alias=config['namespace']+'/'+entry['name']
            raw=source((stage/entry['path']).read_bytes());raw['specification']={'blueId':rules.blue_id}
            doc=language.admit_definition(wire(raw).decode(),format='json')
            language.publish_document(doc);language.aliases[alias]=doc.blue_id;aliases[alias]=doc.blue_id
        repository=Repository.from_payload(config['name'],aliases,language.provider.snapshot())
        data=(repository._json+'\n').encode();rel='inputs/authored.repository.json';(stage/rel).write_bytes(data)
        config['inputs']=[{'path':rel,'sha256':sha(data),'identity':repository.identity}]
        config['exports']=[{'name':e['name'],'fromInput':rel,'inputAlias':config['namespace']+'/'+e['name']} for e in config['exports']]
        if version:
            config['version']=version
            (stage/'spec/frozen.json').write_bytes(wire({config['protocol']['rules']:sha((stage/config['protocol']['rules']).read_bytes())}))
        (stage/'blue-package.yaml').write_bytes(wire(config))
        (stage/'blue-package.lock.json').write_bytes(wire(stage_pins))
        package=build(stage,revision=revision,source_url='')
        verify_bytes(package.archive)
        return package,pins,rules.blue_id


def selection(package, path):
    return dict(name='blue-mandates', path=path, packageBlueId=package.manifest['packageBlueId'], archiveSha256=package.archive_sha)


def approved(project, package, rules):
    support=json.loads((project/'docs/native-support.json').read_text())
    from blue_coordination.engine.mandate_package import supported_definition
    require(support == supported_definition(), 'Package support manifest differs from the installed native approval')
    exports={'Mandates/'+e['name']:e['blueId'] for e in package.manifest['exports']}
    require(support['types']==exports, 'Unapproved type identities; prepare an explicit candidate revision')
    require(support['packageId']==package.manifest['packageBlueId'] and support['rulesId']==rules and
            support['coordinationPackage']==package.manifest['imports']['coordination']['packageBlueId'],
            'Unapproved package/rules/dependency identity; prepare an explicit candidate revision')
    # The inventory and native runtime are independent approvals, not outputs
    # inferred from whatever happens to have compiled today.
    inventory=json.loads((ROOT/'SHARED-PACKAGES.json').read_text())
    row=next(r for r in inventory['packages'] if r['name']=='blue-mandates')
    require(row==selection(package,row['path']), 'Selected inventory pin differs from staged build')
    require(package.manifest['protocol']==support['protocolId'], 'Native protocol pin differs')


def check_dist(project, package):
    dist=project/'dist'
    expected={**package.files, 'package.bluepkg':package.archive}
    actual={p.relative_to(dist).as_posix():p.read_bytes() for p in dist.rglob('*') if p.is_file()}
    require(actual==expected, 'Published archive/unpacked files differ from current locked source')


def write_set(directory, package):
    for name,data in {**package.files,'package.bluepkg':package.archive}.items():
        target=directory/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',nargs='?',default='build',choices=('build','check','candidate'))
    parser.add_argument('--root',type=Path,default=ROOT/'blue-mandates')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--revision')
    parser.add_argument('--version')
    parser.add_argument('--refresh-lock',action='store_true')
    args=parser.parse_args(argv);project=args.root.resolve()
    candidate=args.command=='candidate'
    if candidate:
        if not all((args.output,args.revision,args.version)):
            parser.error('candidate requires a new --output directory, --revision and --version')
        require(not args.output.exists(), 'Candidate destination already exists; immutable releases are not overwritten')
    elif args.output or args.revision or args.version or args.refresh_lock:
        parser.error('revision/lock changes require the explicit candidate command')
    package,pins,rules=compile_locked(project,revision=args.revision or 'shared-mandates-20260927-2',version=args.version,refresh=args.refresh_lock)
    if candidate:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=args.output.parent,prefix='.candidate-') as tmp:
            stage=Path(tmp)/'release';stage.mkdir()
            write_set(stage/'dist',package)
            (stage/'blue-package.lock.json').write_bytes(wire(pins))
            proposal={'approvedNativeSupport':False,'rulesId':rules,
                      'selection':selection(package,str(args.output/'dist/package.bluepkg')),
                      'exports':package.manifest['exports'], 'protocol':package.manifest['protocol']}
            (stage/'REVIEW.json').write_bytes(wire(proposal))
            # One directory rename advertises the complete candidate. Existing
            # releases, locks and native/consumer approvals remain untouched.
            os.rename(stage,args.output)
        result=proposal
    else:
        approved(project,package,rules)
        if (project/'dist').exists():
            check_dist(project,package)  # An identical immutable release needs no write.
        elif args.command=='check':
            raise ValueError('Missing published distribution')
        else:
            with tempfile.TemporaryDirectory(dir=project,prefix='.build-') as tmp:
                stage=Path(tmp)/'dist';write_set(stage,package)
                os.rename(stage,project/'dist')
        result={**selection(package,'blue-mandates/dist/package.bluepkg'),'sourceVerified':True,'command':args.command}
    import blue_language
    result['toolchain']={'python':sys.executable,'language':str(Path(blue_language.__file__).resolve())}
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
