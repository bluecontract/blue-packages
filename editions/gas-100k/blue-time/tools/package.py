#!/usr/bin/env python3
"""Compatibility entry point for the locked native publisher."""
import os, sys
from pathlib import Path
os.execv(str(Path(__file__).resolve().parents[1]/'blue-package'), ['blue-package', *sys.argv[1:]])
