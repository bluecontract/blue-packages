#!/usr/bin/env python3
"""Assemble the single canonical Coordination rules publication."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'blue-coordination/spec'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = '\n\n'.join((ROOT / name).read_text().rstrip() for name in (
        'provider-source.md', 'execution.md', 'host-contract.md', 'qualification.md')) + '\n'
    output = ROOT / 'coordination.md'
    if args.check:
        if output.read_text() != text: raise SystemExit('Coordination publication differs')
    else: output.write_text(text)
    print('PASS: one Coordination publication with provider and execution obligations')


if __name__ == '__main__': main()
