#!/usr/bin/env python3
"""Execute bounded receiver algorithms, never claim whole Coordination parity."""
from pathlib import Path
import json
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent/'blue-contracts/tools'))
import bootstrap  # Immutable native algorithms/source lock; no legacy processor execution.
if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover(str(ROOT/'conformance/reference'), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'profile': 'receiver-algorithms', 'tests': result.testsRun,
        'vectorExecution': 'PASS' if result.wasSuccessful() else 'FAIL',
        'editionQualification': 'NOT_VERIFIED',
        'coverage': {'q06_classification': 'MODEL_ONLY', 'q13_scan_bounds': 'MODEL_ONLY', 'q13_attachment_generations': 'MODEL_ONLY',
                     'source_expansion_scheduling': 'MODEL_ONLY', 'source_authentication': 'NOT_VERIFIED', 'receiving_and_restart': 'NOT_VERIFIED',
                     'dependency_worklist_dispositions': 'MODEL_ONLY', 'causal_history_and_cycles': 'NOT_VERIFIED', 'java_paired_vectors': 'NOT_VERIFIED'}}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
