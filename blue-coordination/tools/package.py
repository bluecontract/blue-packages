#!/usr/bin/env python3
"""Current Coordination authoring checks and the shared native package builder."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
from blue_language import Language
from blue_repository import Repository
from blue_packages.reader import read_package

ROOT = Path(__file__).resolve().parents[1]
HOME = Path(os.environ.get('BLUE_PACKAGES_DIR', ROOT.parent)).resolve()

def config():
    return json.loads((ROOT / 'blue-package.yaml').read_text())

def current_ledger(root=ROOT):
    root = Path(root)
    expected = json.loads((ROOT / 'spec/frozen.json').read_text())
    rel = config()['protocol']['rules']
    if expected[rel] != 'sha256:' + hashlib.sha256((root / rel).read_bytes()).hexdigest():
        raise ValueError('frozen specification mismatch')
    return expected

def dependencies():
    cfg = config(); packages = {}; pins = {'format': 2, 'imports': {}}
    for prefix, item in cfg['imports'].items():
        path = (ROOT / item['path']).resolve()
        if not path.is_relative_to(HOME):
            raise ValueError('Import escapes shared package home')
        package = packages[prefix] = read_package(path)
        pins['imports'][prefix] = dict(path=item['path'], packageBlueId=package.blue_id,
            archiveSha256=package.archive_sha, name=package.manifest['name'], version=package.manifest['version'])
    if pins != json.loads((ROOT / 'blue-package.lock.json').read_text()):
        raise ValueError('Dependency pins changed')
    return packages

def context():
    language = Language(core_contracts=False)
    for entry in config()['exports']:
        raw=json.loads((ROOT/entry['path']).read_text())
        if 'specification' in raw:
            expected=json.loads((HOME/'blue-coordination/docs/runtime-catalogue.json').read_text())['specification']
            if raw['specification'] != {'blueId': expected}:
                raise ValueError('Incorrect source specification: ' + entry['path'])
    packages = dependencies()
    for prefix, package in packages.items():
        language.enable_repository(Repository.from_payload('import:' + prefix,
            {prefix + '/' + name: bid for name, bid in package.exports.items()}, package.repository.records))
    rules = language.create(json.dumps({'type': 'Text', 'value': (ROOT / config()['protocol']['rules']).read_text()}), format='json')
    language.publish_document(rules); aliases = {}
    package = read_package(ROOT / 'dist/package.bluepkg')
    declared_rules = package.manifest['semanticSpecifications'][package.manifest['protocol']]['rules']['blueId']
    if rules.blue_id != declared_rules: raise ValueError('Compiled rules differ from source')
    for entry in config()['exports']:
        raw = json.loads((ROOT / entry['path']).read_text())
        if 'specification' in raw and raw['specification'] != {'blueId': rules.blue_id}:
            raise ValueError('Incorrect source specification: ' + entry['path'])
    aliases = {'Coordination/' + name: bid for name, bid in package.exports.items()}
    language.enable_repository(Repository.from_payload('current-coordination', aliases, package.repository.records))
    return language, aliases, rules.blue_id

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'check', 'verify', 'inspect'])
    args = parser.parse_args()
    if args.command in ('build', 'check'):
        command = [sys.executable, str(HOME / 'tools/build_final_gas.py'), ROOT.name]
        if args.command == 'check': command.append('--check')
        subprocess.run(command, check=True)
    current_ledger()
    package = read_package(ROOT / 'dist/package.bluepkg')
    print(json.dumps(dict(verified=True, name=package.manifest['name'],
        packageBlueId=package.blue_id, archiveSha256=package.archive_sha, exports=len(package.exports)), indent=2))

if __name__ == '__main__': main()
