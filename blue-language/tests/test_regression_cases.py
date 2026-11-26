"""Diagnostic facts for conformance/language-regression-cases.jsonl.

The portable fixture format records only the outcome and category of a failure.
These checks add the detail, path and expected/actual facts the normative
algorithms establish for the same cases (LANG-CYCLE-INPUT, LANG-DIAGNOSTIC-FACTS).
"""
import importlib.util
import json
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    'portable_fixture_run', ROOT.parent/'verification/reference/blue-language/python/tools/run.py')
run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run)
_LINES = [json.loads(line) for line in (ROOT/'conformance/language-regression-cases.jsonl').read_text().splitlines() if line.strip()]
CASES = {c['id']: c for c in _LINES}

FACTS = {
    'regression-cycle-local-index-beyond-int32': {'detail': 'local target'},
    'regression-cycle-local-index-beyond-int64': {'detail': 'local target'},
    'regression-untyped-schema-only-value': {
        'detail': 'payload required', 'path': '',
        'expected': {'present': True, 'kind': 'none'}, 'actual': {'present': False}},
    'regression-bare-item-type-value': {
        'detail': 'list payload required', 'path': '',
        'expected': {'present': True, 'kind': 'List'}, 'actual': {'present': False}},
}


def test_case_ids_unique_and_facts_bound():
    assert len(CASES) == len(_LINES)
    assert set(FACTS) <= set(CASES)


@pytest.mark.parametrize('case_id', list(CASES))
def test_regression_case(case_id):
    case = CASES[case_id]
    result = run.execute(case)
    assert run.match(result, case['expected']) == []
    for key, value in FACTS.get(case_id, {}).items():
        assert result[key] == value, key
