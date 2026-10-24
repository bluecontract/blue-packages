#!/usr/bin/env python3
"""Render/check exact executable model blocks; does not build a package."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    ROOT: ('tools/demand_reference.py',),
    ROOT.parent/'blue-coordination': ('tools/receiver_reference.py',),
}


def render(root, paths):
    prefix = '''# Executable reference algorithm models

These blocks are executed by the source runners and checked byte-for-byte by
`blue-contracts/tools/reference_sources.py --check`. They model only the stated
algorithm boundaries; they are not another whole Contracts executor or an
issuer of trusted completion capabilities. The runners report individual vector
execution separately from whole-edition qualification, which remains
`NOT_VERIFIED` until all required composition and Java equivalence gates pass.
The historical final-gas Python processor is a separate legacy profile and is
not the reference authority for demand-scoped execution or receiver-relative replay.

Native identity, contextual Recipe validation and owning proofs use the immutable,
SOURCE-LOCK-verified Language implementation. These models do not replace its
strict certification or reproduce its cryptography. Production source/journal
premises of receiver algorithms require actual authentication outside the model.

'''
    manifest = {}
    for path in paths:
        data = (root/path).read_bytes()
        manifest[path] = hashlib.sha256(data).hexdigest()
        prefix += f'## {path}\n\nSHA-256: `{manifest[path]}`\n\n```python\n{data.decode().rstrip()}\n```\n\n'
    return prefix.rstrip() + '\n', manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write', action='store_true')
    group.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for root, paths in SOURCES.items():
        document, manifest = render(root, paths)
        output = root/'docs/reference-algorithms.md'
        sources = root/'docs/reference-algorithms.json'
        metadata = json.dumps({'format': 'blue-reference-models/1', 'qualification': 'NOT_VERIFIED',
                               'sourceSha256': manifest}, indent=2)+'\n'
        if args.write:
            output.write_text(document)
            sources.write_text(metadata)
        elif output.read_text() != document or sources.read_text() != metadata:
            raise SystemExit('STALE_REFERENCE_ALGORITHMS: '+str(root))
    print('Exact executable reference source blocks: PASS')


if __name__ == '__main__':
    main()
