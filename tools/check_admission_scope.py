#!/usr/bin/env python3
"""Compile the selected Documents archive with the published BEX reference."""
import io
import json
from pathlib import Path
import sys
import zipfile

from release import check_archive, digest, require, selections

ROOT = Path(__file__).resolve().parents[1]
STEPS = {'nextAdmission', 'installAdmission', 'finishAdmission'}


def open_reference(root, bex_row):
    _, data = check_archive(root, bex_row)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        sources = json.loads(archive.read('docs/sources.json'))
    reference = root / 'verification/reference/blue-bex'
    compiler = 'src/blue_bex/compiler.py'
    require(
        digest((reference / 'python' / compiler).read_bytes()) == sources['modules'][compiler],
        'The reference compiler differs from the selected BEX publication',
    )
    lock = json.loads((reference / 'SOURCE-LOCK.json').read_text())
    for name, pin in lock['files'].items():
        if name.startswith('src/'):
            require(digest((reference / 'python' / name).read_bytes()) == 'sha256:' + pin,
                    'Reference source differs: ' + name)
    sys.path.insert(0, str(reference / 'python/src'))


def effective_map(bridge, node, field):
    container = bridge.child(node, field)
    if container is None:
        return {}, {}
    children = {key: bridge.child(container, key) for key in bridge.head(container).fields}
    return ({key: bridge.bex_data(value) for key, value in children.items()},
            {key: bridge.identity(bridge.exact(value)) for key, value in children.items()})


def step_programs(plan):
    body = plan['functions']['planAdmission']['do']
    bindings = {statement['$let']['name']: statement['$let']['expr']
                for statement in body if '$let' in statement}
    require(bindings['sharedConstants'] == {'clauseKey': {'$const': 'clauseKey'}, 'bindings': {}},
            'Admission step constants changed')
    programs = {}
    for merge in bindings['steps']:
        require(isinstance(merge, dict) and merge.keys() == {'$merge'}
                and isinstance(merge['$merge'], list), 'Expected a merged admission step')
        step = {}
        for part in merge['$merge']:
            require(isinstance(part, dict) and all(not key.startswith('$') for key in part),
                    'Admission step merge requires literal object operands')
            # BEX merge is shallow and later operands replace earlier members.
            step.update(part)
        name = step.get('name')
        require(isinstance(name, str), 'Expected a literal admission step name')
        if name not in STEPS:
            continue
        require(name not in programs, 'Duplicate admission step: ' + name)
        require(step.get('definition') == {'$var': 'admissionDefinition'},
                'Wrong scoped definition binding: ' + name)
        require(step.get('constants') == {'$var': 'sharedConstants'},
                'Wrong admission constants binding: ' + name)
        quoted = step.get('do')
        require(isinstance(quoted, dict) and quoted.keys() == {'$literal'},
                'Expected a quoted admission program: ' + name)
        programs[name] = {'constants': {'clauseKey': 'conformance', 'bindings': {}},
                          'do': quoted['$literal']}
    require(programs.keys() == STEPS, 'Missing admission step')
    return programs


def stock_guard(plan, stock_id, scope_id):
    scope = {'type': {'blueId': scope_id}}
    require(plan['constants']['admissionStepDefinition'] == scope,
            'Plan scope differs from the selected Documents export')
    expected = {'$and': [
        {'$eq': [{'$var': 'definition'}, {'$pointerGet': {
            'object': {'type': {'blueId': stock_id}}, 'path': '/type'}}]},
        {'$eq': [{'$const': 'admissionStepDefinition'}, scope]},
    ]}
    body = plan['functions']['matchesAdmissionStepFunctions']['do']
    guards = [step['$if']['cond'] for step in body
              if step.get('$if', {}).get('then') == [{'$return': True}]]
    require(guards == [expected], 'Stock guard must bind both same-edition exports')


def check_selection(bridge, plan, stock_id, scope_id, function_ids):
    from blue_bex import Context, Engine, UNDEFINED

    body = plan['functions']['planAdmission']['do']
    decision = next(i for i, step in enumerate(body)
                    if step.get('$let', {}).get('name') == 'admissionDefinition')
    scope_carrier = plan['constants']['admissionStepDefinition']
    scope_carrier_id = bridge.identity(bridge.node(scope_carrier, certify=False))
    program = {
        'constants': {'clauseKey': 'conformance', 'admissionStepDefinition': scope_carrier},
        'functions': {name: plan['functions'][name] for name in
                      ('isAdmissionDefinitionReference', 'matchesAdmissionStepFunctions')},
        'do': [{'$let': {'name': 'definition', 'expr': {'$binding': 'input'}}},
               *body[decision:decision + 2],
               {'$return': {'$var': 'admissionDefinition'}}],
    }
    root = '/clauseRuntime/work/candidate/conformance/type'
    actual_path = root + '/actionDefinition/type'
    scope_path = root + '/hookDefinition/constants/admissionStepDefinition/type'

    author = {'type': {'blueId': stock_id}, 'name': 'Conformance author'}
    changed_name = next(iter(function_ids))
    original = bridge.bex_data(bridge.node({'blueId': function_ids[changed_name]}, certify=False))
    # Refine the existing body by preserving the inherited list prefix.
    override = {'do': [*original['do'], {'$return': 'Changed admission function'}]}
    variants = (
        ('stock', {'blueId': stock_id}, True),
        ('equivalent author', author, True),
        ('author with constants', {**author, 'constants': {'conformance': 1}}, False),
        ('author with changed function', {**author, 'functions': {changed_name: override}}, False),
    )
    for label, actual, selects_scope in variants:
        # Model only the reads consumed by the selector. Native provider and
        # gas behavior are checked separately with the Java runtime.
        custom = 'type' in actual
        constants = actual.get('constants', {})
        actual_node = bridge.node(actual, certify=False)
        actual_id = bridge.identity(actual_node)
        actual_function_ids = function_ids
        if 'functions' in actual:
            selected = bridge.child(bridge.child(actual_node, 'functions'), changed_name)
            identity = bridge.identity(bridge.exact(selected))
            require(identity != function_ids[changed_name], 'Expected a distinct effective function')
            actual_function_ids = {**function_ids, changed_name: identity}
        canonical_reads = {
            actual_path: actual,
            actual_path + '/constants': constants,
            scope_path + '/constants': {},
            scope_path + '/functions': {name: {} for name in function_ids},
        }

        def read(path, view, _):
            if view == 'definition':
                require(custom and not constants, label + ' made a definition-role read')
                parent, name = path.rsplit('/', 1)
                if parent == actual_path + '/functions':
                    return {'blueId': actual_function_ids[name]}
                require(parent == scope_path + '/functions',
                        'Selector requested a definition outside the two function maps')
                return {'blueId': function_ids[name]}
            require(view == 'canonical', 'Selector requested an unexpected read view')
            return canonical_reads.get(path, UNDEFINED)

        def identify(value, _):
            if value == actual:
                return actual_id
            require(value == scope_carrier, 'Selector requested an unexpected identity')
            return scope_carrier_id

        context = Context(bindings={'input': {'blueId': actual_id}}, read_document=read,
                          matcher=lambda _, pattern: pattern == {}, node_blue_id=identify)
        expected = scope_carrier_id if selects_scope else actual_id
        require(Engine().execute(program, context).value == {'blueId': expected},
                'Unexpected admission definition selection: ' + label)


def compile_closure(compiler_type, programs, stock, scope):
    reached = set()
    for program in programs.values():
        compiler_type().compile(program, definition=stock)
        compiler = compiler_type()
        compiler.compile(program, definition=scope)
        pending = list(compiler.calls['<root>'])
        while pending:
            name = pending.pop()
            if name not in reached:
                reached.add(name)
                pending.extend(compiler.calls[name])
    require(reached == scope['functions'].keys(),
            'Admission scope must contain exactly the compiled transitive call closure')


def check(root):
    rows = {row['directory']: row for row in selections(root)}
    open_reference(root, rows['blue-bex'])
    from blue_bex.compiler import Compiler
    from blue_contracts.reference.language import Bridge
    from blue_language.api import Language, MemoryProvider

    row = rows['clause-documents']
    published, data = check_archive(root, row)
    require(published['imports']['BEX'] == rows['blue-bex']['packageBlueId'],
            'Documents does not import the selected BEX publication')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        records = json.loads(archive.read('package-records.json'))
    ids = {entry['name']: entry['blueId'] for entry in published['exports']}
    bridge = Bridge(Language(MemoryProvider(records)))

    def definition(name):
        node = bridge.node({'blueId': ids[name]}, goal='definition', certify=False)
        functions, whole_ids = effective_map(bridge, node, 'functions')
        constants, _ = effective_map(bridge, node, 'constants')
        return {'functions': functions, 'constants': constants}, whole_ids

    stock_name, scope_name = 'Document Preparation Functions', 'Admission Step Functions'
    plan, _ = definition('Preparation Plan')
    stock, stock_functions = definition(stock_name)
    scope, scope_functions = definition(scope_name)
    require(not stock['constants'] and not scope['constants'],
            'Stock and scoped definitions must have empty effective constants')
    scope_record = json.loads(records[ids[scope_name]]['text'])
    require(scope_record['functions'] == {name: {'blueId': identity}
                                          for name, identity in scope_functions.items()},
            'Scope must consist of whole-function references')
    for name, identity in scope_functions.items():
        require(stock_functions.get(name) == identity
                and stock['functions'][name] == scope['functions'][name],
                'Scope differs from the effective stock function: ' + name)

    for name in ('Documents Clause', 'Document Clause'):
        clause = bridge.node({'blueId': ids[name]}, goal='definition', certify=False)
        for field, export in (('actionDefinition', stock_name), ('hookDefinition', 'Preparation Plan')):
            selected = bridge.child(bridge.child(clause, field), 'type')
            require(bridge.identity(bridge.exact(selected)) == ids[export],
                    f'{name} does not select the same-edition {export}')

    stock_guard(plan, ids[stock_name], ids[scope_name])
    Compiler().compile({'constants': {'clauseKey': 'conformance', 'mode': 'configuration',
                                     'typeId': 'conformance'}, 'do': [{'$return': {}}]},
                       definition=plan)
    compile_closure(Compiler, step_programs(plan), stock, scope)
    check_selection(bridge, plan, ids[stock_name], ids[scope_name], scope_functions)
    print(f"{row['packageBlueId']}: compiled the Plan and all three admission steps "
          f"against stock and scope. Exact call closure: {len(scope_functions)} functions. "
          "Stock read trap and custom selection checks passed.")


if __name__ == '__main__':
    check(ROOT)
