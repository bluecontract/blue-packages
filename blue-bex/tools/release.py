#!/usr/bin/env python3
"""Build or verify the sole current package; installed runtime checks are explicit."""
import argparse
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'verify', 'test', 'demo', 'reference-tests'])
    args = parser.parse_args()
    if args.command == 'build': command = [str(ROOT.parent/'tools/build_final_gas.py'), ROOT.name]
    elif args.command == 'verify': command = [str(ROOT.parent/'tools/release.py'), 'check']
    elif args.command == 'test': command = ['-m', 'pytest', '-q', str(ROOT/'tests')]
    elif args.command == 'demo': command = [str(ROOT/'examples/run.py')]
    else: command = [str(ROOT/'tools/run_reference_tests.py')]
    return subprocess.run([sys.executable, *command], cwd=ROOT).returncode
if __name__ == '__main__': raise SystemExit(main())
