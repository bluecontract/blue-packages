#!/usr/bin/env python3
"""Explicitly build/check the new Contracts publication from canonical sources."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'blue-contracts'


def outputs():
    host = (PACKAGE / 'reference-host.py').read_text()
    modules = {'src/blue_contracts/reference/' + p.name: p.read_text()
               for p in sorted((PACKAGE / 'reference').glob('*.py'))}
    modules['src/blue_host/__init__.py'] = host
    prose = (PACKAGE / 'spec/deterministic-prose.md').read_text()
    gas = (PACKAGE / 'reference/GAS_MANIFEST.json').read_text()
    prose = re.sub(r'(### Exact counter schedule\n\n```json\n).*?(```)',
                   lambda m: m[1] + gas + m[2], prose, flags=re.S)
    amendment = (PACKAGE / 'spec/deterministic-rules.md').read_text()
    publication = prose + amendment + '\n## Appendix C. Complete executable algorithms\n\n'
    for name, body in modules.items():
        publication += f'### `{name}`\n\n```python\n{body}```\n\n'
    manifest = {'format': 'blue-source-binding/1', 'edition': '2026-10-17-deterministic-3',
                'modules': {name: hashlib.sha256(body.encode()).hexdigest() for name, body in modules.items()}}
    publication += '### Source inventory\n\n```json\n' + json.dumps(manifest, indent=2) + '\n```\n'
    return {'spec/contracts-deterministic-3.md': publication, 'SPECIFICATION.md': publication,
            'docs/sources.json': json.dumps(manifest, indent=2) + '\n'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for name, body in outputs().items():
        path = PACKAGE / name
        if args.check:
            if not path.exists() or path.read_text() != body:
                raise SystemExit('Publication differs: ' + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
    print('PASS: canonical deterministic Contracts publication')


if __name__ == '__main__':
    main()
