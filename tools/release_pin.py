#!/usr/bin/env python3
"""Bind release preparation to exact reviewed asset bytes, before tag publication.

Recording is an explicit authoring step, not semantic or consumer qualification.
Checks never refresh the pin. The pin is outside the ZIP to avoid circular hashes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FORMAT = 'blue-packages-release-pin/1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def recorded(directory, tag):
    require(re.fullmatch(r'blue-packages-[A-Za-z0-9][A-Za-z0-9._-]*', tag) is not None,
            'Invalid immutable release tag')
    require(directory.is_dir() and not directory.is_symlink(), 'Invalid asset directory')
    files = {}
    for path in sorted(directory.iterdir()):
        require(path.is_file() and not path.is_symlink()
                and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', path.name) is not None,
                'Invalid release asset: ' + path.name)
        files[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    require({'blue-packages.zip', 'CATALOG.json', 'SHA256SUMS'} <= files.keys(),
            'Incomplete release assets')
    return dict(format=FORMAT, tag=tag, files=files)


def verify(directory, pin, tag=None):
    require(isinstance(pin, dict) and set(pin) == {'format', 'tag', 'files'}
            and pin['format'] == FORMAT, 'Invalid release pin')
    require(tag is None or tag == pin['tag'], 'Release tag differs from pinned candidate')
    require(recorded(directory, pin['tag']) == pin,
            'Release assets differ from pinned candidate; checks never refresh the pin')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('record', 'check'))
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--pin', type=Path, default=ROOT / 'RELEASE-PIN.json')
    parser.add_argument('--tag')
    args = parser.parse_args()
    if args.command == 'record':
        if args.tag is None:
            parser.error('record requires --tag')
        value = recorded(args.assets, args.tag)
        payload = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
        if args.pin.exists():
            require(args.pin.read_bytes() == payload, 'Refuse replacing an existing release pin')
        else:
            args.pin.write_bytes(payload)
    else:
        value = json.loads(args.pin.read_text())
        verify(args.assets, value, args.tag)
    print(json.dumps(dict(status='PINNED' if args.command == 'record' else 'PASS',
                          tag=value['tag'], assets=len(value['files']), pin=str(args.pin))))


if __name__ == '__main__':
    main()
