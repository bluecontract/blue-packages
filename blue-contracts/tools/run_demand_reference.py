#!/usr/bin/env python3
"""Run implemented normative vectors and report remaining gates independently."""
from pathlib import Path
import json
import sys
import unittest
import bootstrap  # Verifies the immutable native source lock before imports.

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = {
    'contextual_role_obligations': 'PARTIAL',
    'cold_envelope_preconditions': 'MODEL_ONLY',
    'restore_structural_invariants': 'NOT_VERIFIED',
    'required_record_and_cyclic_transport': 'MODEL_ONLY',
    'receipt_and_cause_postconditions': 'MODEL_ONLY',
    'declaration_role_edges': 'MODEL_ONLY',
    'finalization_completion_receiving': 'NOT_VERIFIED',
    'logical_obligation_counters': 'MODEL_ONLY',
    'logical_meter_full_tariff': 'NOT_VERIFIED',
    'latest_shared_publication': 'MODEL_ONLY',
    'activation_transactions': 'NOT_VERIFIED',
    'java_paired_vectors': 'NOT_VERIFIED',
}
if __name__ == '__main__':
    if '--vectors' in sys.argv:
        from demand_reference import execute_vector
        vectors = json.loads((ROOT/'conformance/reference/vectors.json').read_text())['vectors']
        print(json.dumps([execute_vector(vector) for vector in vectors], indent=2))
        raise SystemExit(0)
    suite = unittest.defaultTestLoader.discover(str(ROOT/'conformance/reference'), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'profile': 'demand-algorithms', 'tests': result.testsRun,
                      'vectorExecution': 'PASS' if result.wasSuccessful() else 'FAIL',
                      'editionQualification': 'NOT_VERIFIED', 'coverage': COVERAGE}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
