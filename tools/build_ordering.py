#!/usr/bin/env python3
"""Build/check the isolated ordering correction with the existing native builder.

Requires BLUE_JAVA_CLASSPATH and --inputs pointing to the exact retained 10M
package set. Does not alter the root catalogue or any historical publication.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EDITION = ROOT / 'editions/ordering-1'
BASE_SHA = '045402347b399e13cce2c97ad1f72913b0846f008ac8bb86cc931c95557292e1'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def build(inputs, check):
    base = (ROOT / 'blue-contracts/spec/contracts.md').read_bytes()
    assert sha(base) == BASE_SHA, 'Historical base changed'
    work = (EDITION / 'work.py').read_text()
    text = base.decode()
    old = re.search(r'### `src/blue_contracts/reference/work.py`\n\n```python\n(.*?)\n```', text, re.S)
    assert old, 'Missing normative work module'
    old_sha = sha(old[1].encode())
    # Source inventory hashes include the final newline.
    old_sha = sha((old[1] + '\n').encode())
    text = text[:old.start(1)] + work.rstrip('\n') + text[old.end(1):]
    text = text.replace(old_sha, sha(work.encode()))
    gas_match = re.search(r'(### Exact counter schedule\n\n```json\n)(.*?)(\n```)', text, re.S)
    assert gas_match, 'Missing gas schedule'
    gas = json.loads(gas_match[2])
    gas['profile'] = 'contracts-deterministic-gas-6-ordering'
    gas['status'] = 'Explicit ordering correction; unchanged 10M weights and limits.'
    text = text[:gas_match.start(2)] + json.dumps(gas, indent=2) + text[gas_match.end(2):]
    text = text.replace('## Appendix C. Complete executable algorithms',
        (EDITION / 'rules.md').read_text() + '\n## Appendix C. Complete executable algorithms', 1)
    classpath = os.environ['BLUE_JAVA_CLASSPATH']
    java_home = Path(os.environ['JAVA_HOME'])
    with tempfile.TemporaryDirectory(prefix='blue-ordering-') as temporary:
        stage = Path(temporary)
        p = stage / 'blue-contracts'
        shutil.copytree(ROOT / 'blue-contracts', p,
            ignore=shutil.ignore_patterns('dist', 'reference', '__pycache__'))
        for name, expected in [('blue-language','a030dd4c88e41a414918ef4895017862e154b438848bd5c0e4f5bc880e7b8a90'),
                               ('blue-bex','905e3fad22199f158df8745336d57ba369ae96093f452dec77c16b970f38bedb')]:
            data = (inputs / name / 'dist/package.bluepkg').read_bytes()
            assert sha(data) == expected, 'Wrong retained input: ' + name
            target = stage / name / 'dist/package.bluepkg'
            target.parent.mkdir(parents=True)
            target.write_bytes(data)
        config = json.loads((p / 'blue-package.yaml').read_text())
        config['version'] = '1.0.0-ordering.1'
        config['protocol']['rules'] = 'spec/contracts-ordering.md'
        (p / 'blue-package.yaml').write_text(json.dumps(config, indent=2)+'\n')
        (p / 'spec/contracts-ordering.md').write_text(text)
        (p / 'spec/frozen.json').write_text(json.dumps({'spec/contracts-ordering.md':'sha256:'+sha(text.encode())}))
        modules = {name: sha((body.rstrip('\n')+'\n').encode()) for name,body in
                   re.findall(r'### `([^`]+)`\n\n```python\n(.*?)\n```', text, re.S)}
        assert modules['src/blue_contracts/reference/work.py'] == sha(work.encode())
        sources = {'format':'blue-source-binding/1', 'edition':'ordering-1', 'modules':modules,
                   'baseSpecificationSha256':BASE_SHA,
                   'languagePackageBlueId':'8XGYNufx24r7Dc5bGoeobcGNCn9roLzSfZCQyHBTaTx4',
                   'bexPackageBlueId':'6m7CxeDA9F74LyfU1H5zYGmo6ozXr4zJFbh7j6F6QJ7a',
                   'bexSpecificationBlueId':'7m8k8P8b8Kn2jHF96EQogWTpsouytXmDFQ3qdmWdY5A3',
                   'executableAppendix':'spec/contracts-ordering.md',
                   'authoredWorkSha256':sha(work.encode())}
        (p / 'docs/sources.json').write_text(json.dumps(sources, indent=2)+'\n')
        (p / 'README.md').write_text((EDITION / 'rules.md').read_text())
        classes=stage/'classes';classes.mkdir()
        subprocess.run([str(java_home/'bin/javac'),'-cp',classpath,'-d',str(classes),
            str(ROOT/'tools/BuildPaymentFamily.java'),str(ROOT/'tools/BuildFinalGas.java')],check=True)
        subprocess.run([str(java_home/'bin/java'),'-Xmx1500m','-cp',str(classes)+os.pathsep+classpath,
            'BuildFinalGas',str(stage),'blue-contracts'],check=True,stdout=subprocess.DEVNULL)
        archive=(p/'dist/package.bluepkg').read_bytes()
        manifest=json.loads((p/'dist/package.json').read_text())
        pins={'format':'blue-ordering-edition/1','baseSpecificationSha256':BASE_SHA,
              'packageBlueId':manifest['packageBlueId'],'archiveSha256':'sha256:'+sha(archive),
              'specificationSha256':sha(text.encode()),'protocol':manifest['protocol'],
              'specificationBlueId':manifest['semanticPackages'][manifest['packageBlueId']]['documentation']['spec/contracts-ordering.md']['content']['blueId'],
              'sourceSha256':sha(work.encode()),'gas':gas}
        outputs={'package.bluepkg':archive,'selection.json':(json.dumps(pins,indent=2)+'\n').encode()}
        for name,data in outputs.items():
            target=EDITION/name
            if check:
                assert target.read_bytes()==data, 'Nonreproducible '+name
            else:target.write_bytes(data)
    print('PASS: ordering-1; historical publications and root catalogue unchanged')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();build(args.inputs.resolve(),args.check)
