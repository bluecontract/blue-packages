#!/usr/bin/env python3
"""Build or verify this package using the canonical package-home tooling."""
import argparse
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('command', choices=['build', 'verify'])
a = p.parse_args()
if a.command == 'build':
    command = [sys.executable, str(ROOT.parent / 'tools/build_final_gas.py'), ROOT.name]
else:
    command = [sys.executable, str(ROOT.parent / 'tools/release.py'), 'check']
raise SystemExit(subprocess.run(command, cwd=ROOT.parent).returncode)
