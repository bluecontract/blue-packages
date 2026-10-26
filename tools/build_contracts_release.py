#!/usr/bin/env python3
"""Build/check Contracts 1.1.0 with the maintained native package builder.

Creates a new unpublished archive without rewriting prior publications. Exact
Language/BEX dependencies remain the ones specified in the complete rules.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'releases/contracts-1.1.0'
RULES = 'spec/contracts-1.1.0.md'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def build(check=False):
    specification = (RELEASE / 'SPECIFICATION.md').read_bytes()
    classpath = os.environ['BLUE_JAVA_CLASSPATH']
    java = Path(os.environ['JAVA_HOME']) / 'bin'
    with tempfile.TemporaryDirectory(prefix='contracts-release-') as temporary:
        root = Path(temporary)
        package = root / 'blue-contracts'
        shutil.copytree(ROOT / 'blue-contracts', package,
                        ignore=shutil.ignore_patterns('dist', 'reference', '__pycache__'))
        config = json.loads((package / 'blue-package.yaml').read_text())
        config['version'] = '1.1.0'
        config['protocol']['name'] = 'Blue Contracts 1.1.0'
        config['protocol']['rules'] = RULES
        (package / 'blue-package.yaml').write_text(json.dumps(config, indent=2)+'\n')
        (package / RULES).write_bytes(specification)
        (package / 'spec/frozen.json').write_text(json.dumps({RULES: 'sha256:'+sha(specification)}))
        shutil.copyfile(RELEASE / 'README.md', package / 'README.md')
        shutil.copyfile(RELEASE / 'sources.json', package / 'docs/sources.json')
        for name in ('blue-language', 'blue-bex'):
            target = root / name / 'dist/package.bluepkg'
            target.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / name / 'dist/package.bluepkg', target)
        classes = root / 'classes'; classes.mkdir()
        subprocess.run([str(java/'javac'), '-cp', classpath, '-d', str(classes),
                        str(ROOT/'tools/BuildPaymentFamily.java'), str(ROOT/'tools/BuildFinalGas.java')], check=True)
        subprocess.run([str(java/'java'), '-Xmx1500m', '-cp', str(classes)+os.pathsep+classpath,
                        'BuildFinalGas', str(root), 'blue-contracts'], check=True, stdout=subprocess.DEVNULL)
        manifest = json.loads((package/'dist/package.json').read_text())
        archive = (package/'dist/package.bluepkg').read_bytes()
        pins = dict(version='1.1.0', packageBlueId=manifest['packageBlueId'],
                    archiveSha256='sha256:'+sha(archive), protocol=manifest['protocol'],
                    specificationBlueId=manifest['semanticSpecifications'][manifest['protocol']]['rules']['blueId'],
                    specificationSha256=sha(specification), rulesPath=RULES,
                    gasProfile='blue-contracts/1.1.0', imports=manifest['imports'])
        for name, data in {'package.bluepkg':archive,
                           'selection.json':(json.dumps(pins,indent=2)+'\n').encode()}.items():
            target = RELEASE/name
            if check:
                assert target.read_bytes() == data, 'Nonreproducible release: '+name
            else:
                target.write_bytes(data)
    print('PASS: Contracts 1.1.0 archive and exact dependency identities')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
