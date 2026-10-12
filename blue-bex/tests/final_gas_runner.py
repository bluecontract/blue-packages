"""Run against an explicitly selected reference tree, never the frozen base."""
from decimal import Decimal
from dataclasses import fields
import json
import sys
from blue_bex import Engine, Context, Gas, BexError, UNDEFINED
from blue_language import Language
from blue_contracts.reference.language import Bridge


def decode(v):
    if isinstance(v, dict):
        if set(v) == {'$undefined'}: return UNDEFINED
        if set(v) == {'$decimal'}: return Decimal(v['$decimal'])
        return {k: decode(x) for k, x in v.items()}
    if isinstance(v, list): return [decode(x) for x in v]
    return v


def check_vectors():
    vectors = json.load(open(sys.argv[1]), parse_float=Decimal)['vectors']
    for vector in vectors:
        request = decode(vector['request']); expected = decode(vector['expected'])
        context = Context()
        names = {'currentContract':'current_contract', 'resolvedDocument':'resolved_document'}
        for key, value in request.get('context', {}).items(): setattr(context, names.get(key,key), value)
        context.matcher = Bridge(Language(core_contracts=False)).matches
        if 'matcher' in request:
            assert request['matcher'] == 'always-true'
            context.matcher = lambda value, pattern: True
        intrinsics = {}
        if 'intrinsics' in request:
            assert request['intrinsics'] == 'increment-x-cost-7'
            def increment(payload, meter):
                meter.charge('host', amount=7)
                return payload['x'] + 1
            intrinsics['exact-type'] = increment
        gas = Gas(request.get('gasLimit', 10_000_000))
        try:
            result = Engine(intrinsics=intrinsics).execute(request['program'], context, gas=gas, definition=request.get('definition'), entry=request.get('entry'))
            actual = dict(outcome='Established', value=result.value, changeset=result.changeset,
                          events=result.events, gasUsed=result.gas_used)
            assert {f.name for f in fields(result)} == {'value','changeset','events','gas_used'}
        except BexError as error:
            actual = dict(outcome='Invalid', code=error.code, gasUsed=gas.used, rejected=gas.rejected)
        assert actual == expected, (vector['id'], actual, expected)
        assert not hasattr(gas, 'trace')
    print(f'Final-gas vectors: {len(vectors)} passed')


def check_meters():
    gas = Gas(100_000)
    for _ in range(100_000): gas.charge('expressionBase')
    assert gas.used == 100_000 and not hasattr(gas, 'trace')
    try: gas.charge('expressionBase')
    except BexError: pass
    else: raise AssertionError('Missing exhaustion')
    rejected = dict(gas.rejected)
    try: gas.charge('expressionBase', 0)
    except BexError: pass
    else: raise AssertionError('Rejected meter resumed')
    assert gas.rejected == rejected and 'ordinal' not in rejected
    parent=Gas(5); child=Gas(3, parent=parent)
    child.charge('expressionBase', 3)
    try: child.charge('expressionBase')
    except BexError: pass
    else: raise AssertionError('Missing local exhaustion')
    assert parent.used == child.used == 3
    assert parent.rejected['cap'] == child.rejected['cap'] == 'LOCAL'
    first = Engine().execute({'expr': 1}, gas=Gas(100))
    shared=Gas(100); shared.charge('expressionBase', 7)
    second=Engine().execute({'expr': 1}, gas=shared)
    assert first.gas_used == second.gas_used and shared.used == 7+first.gas_used

check_vectors()
check_meters()
