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
    require(plan['functions']['planAdmission']['do'] == [{'$return': {'$call': {
        'function': 'assembleAdmissionPlan', 'args': {
            'base': {'$var': 'base'}, 'definition': {'$var': 'definition'},
            'clauses': {'$document': '/clauseRuntime/work/candidate'},
            'clauseKey': {'$const': 'clauseKey'}}}}}],
        'Admission entry must delegate to the selected extracted planner')
    body = plan['functions']['assembleAdmissionPlan']['do']
    bindings = {statement['$let']['name']: statement['$let']['expr']
                for statement in body if '$let' in statement}
    require(bindings['sharedConstants'] == {'clauseKey': {'$var': 'clauseKey'}, 'bindings': {}},
            'Admission step constants changed')
    programs, selections = {}, {}
    for merge in bindings['steps']:
        require(isinstance(merge, dict) and merge.keys() == {'$merge'}
                and isinstance(merge['$merge'], list), 'Expected a merged admission step')
        step = {}
        for part in merge['$merge']:
            require(isinstance(part, dict) and all(not key.startswith('$') for key in part),
                    'Admission step merge requires literal object operands')
            step.update(part)
        name = step.get('name')
        require(isinstance(name, str), 'Expected a literal admission step name')
        if name not in STEPS:
            continue
        require(name not in programs, 'Duplicate admission step: ' + name)
        selection = step.get('definition', {}).get('$call', {})
        require(selection.get('function') == 'assembleAdmissionDefinition',
                'Wrong scoped definition binding: ' + name)
        args = selection.get('args', {})
        require(args.get('definition') == {'$var': 'definition'}, 'Wrong source definition: ' + name)
        for field, suffix in (('definitionPath', '/type/actionDefinition/type'),
                              ('canonicalPath', '/type/hookDefinition/type/constants/admissionCanonicalDefinition/type')):
            require(args.get(field) == {'$concat': ['/clauseRuntime/work/candidate/',
                                                  {'$var': 'clauseKey'}, suffix]},
                    'Wrong same-clause definition path: ' + name)
        selected = args.get('names', [])
        require(selected and len(selected) == len(set(selected)), 'Missing or duplicate closure: ' + name)
        require(step.get('constants') == {'$var': 'sharedConstants'}, 'Wrong admission constants binding: ' + name)
        quoted = step.get('do')
        require(isinstance(quoted, dict) and quoted.keys() == {'$literal'},
                'Expected a quoted admission program: ' + name)
        programs[name] = {'constants': {'clauseKey': 'conformance', 'bindings': {}}, 'do': quoted['$literal']}
        selections[name] = selected
    require(programs.keys() == STEPS, 'Missing admission step')
    return programs, selections


def check_selection(bridge, plan, stock_id, anchor_id, function_ids, selections):
    from blue_bex import Context, Engine, UNDEFINED

    require(plan['constants']['admissionCanonicalDefinition'] == {'type': {'blueId': anchor_id}},
            'Plan anchor differs from same-edition Admission Functions')
    root = '/clauseRuntime/work/candidate/conformance/type'
    actual_path = root + '/actionDefinition/type'
    anchor_path = root + '/hookDefinition/type/constants/admissionCanonicalDefinition/type'
    anchor = {'blueId': anchor_id}
    author = {'type': {'blueId': stock_id}, 'name': 'Conformance author'}
    for step, names in selections.items():
        program = {
            'functions': {name: plan['functions'][name] for name in
                          ('assembleAdmissionDefinition', 'admissionDefinition', 'projectCanonicalDefinition')},
            'do': [{'$return': {'$call': {'function': 'assembleAdmissionDefinition', 'args': {
                'definition': {'$binding': 'input'}, 'names': names,
                'definitionPath': actual_path, 'canonicalPath': anchor_path,
                'clauseKey': 'conformance', 'clauses': {}}}}}],
        }
        variants = [('stock', {'blueId': stock_id}, {}, None, anchor, True),
                    ('equivalent author', author, {}, None, anchor, True),
                    ('author with constants', author, {'conformance': 1}, None, anchor, True),
                    ('missing anchor', author, {}, None, UNDEFINED, False),
                    ('changed anchor', author, {}, None, {'blueId': stock_id}, False)]
        for selected_name in (names[0], names[-1]):
            original = bridge.bex_data(bridge.node({'blueId': function_ids[selected_name]}, certify=False))
            override = {**original, 'do': [*original['do'], {'$return': 'Changed admission function'}]}
            variants.append(('changed ' + selected_name, author, {}, (selected_name, override), anchor, False))
        for label, actual, constants, changed, canonical, selects_scope in variants:
            actual = {**actual, **({'constants': constants} if constants else {}),
                      **({'functions': {changed[0]: changed[1]}} if changed else {})}
            actual_id = bridge.identity(bridge.node(actual, certify=False))
            actual_ids = dict(function_ids)
            if changed:
                actual_node = bridge.node(actual, certify=False)
                selected = bridge.child(bridge.child(actual_node, 'functions'), changed[0])
                actual_ids[changed[0]] = bridge.identity(bridge.exact(selected))
                require(actual_ids[changed[0]] != function_ids[changed[0]], 'Override must change identity')
            reads = []

            def read(path, view, _):
                require(view == 'canonical', 'Unexpected admission read view')
                reads.append(path)
                if path == anchor_path:
                    return canonical
                if path == actual_path + '/constants':
                    return constants
                for parent, identities in ((actual_path, actual_ids), (anchor_path, function_ids)):
                    prefix = parent + '/functions/'
                    if path.startswith(prefix):
                        name = path[len(prefix):]
                        require(name in names, 'Selector read outside this step closure: ' + name)
                        return {'blueId': identities[name]}
                raise AssertionError('Selector attempted whole-library or unrelated read: ' + path)

            def identify(value, _):
                return bridge.identity(bridge.node(value, certify=False))

            # BEX checks missing/invalid values before invoking the host matcher.
            # Keep main's unconstrained {} argument behavior; use Language for
            # the extracted planner's additional typed path/key arguments.
            def matches(value, pattern):
                return pattern == {} or bridge.matches(value, pattern)

            print('Checking selector: ' + step + '/' + label, flush=True)
            context = Context(bindings={'input': {'blueId': actual_id}}, read_document=read,
                              matcher=matches, node_blue_id=identify)
            result = Engine().execute(program, context).value
            if selects_scope:
                require(result.get('functions') == {name: {'blueId': function_ids[name]} for name in names},
                        'Wrong exact closure: ' + step + '/' + label)
                require(result.get('constants') == constants, 'Custom constants were lost')
            else:
                require(result == {'blueId': actual_id}, 'Custom definition was not retained: ' + step + '/' + label)
            require(len(reads) <= 4 + 2 * len(names), 'Unbounded admission definition reads')


def compile_closure(compiler_type, programs, stock, scope, selections):
    reached = set()
    for name, program in programs.items():
        compiler_type().compile(program, definition=stock)
        compiler = compiler_type()
        compiler.compile(program, definition=scope)
        # Each actual emitted definition must compile without unrelated helpers.
        selected_scope = {'constants': scope['constants'],
                          'functions': {function: scope['functions'][function] for function in selections[name]}}
        selected_compiler = compiler_type()
        selected_compiler.compile(program, definition=selected_scope)
        pending = list(compiler.calls['<root>'])
        step_reached = set()
        while pending:
            name = pending.pop()
            if name not in step_reached:
                step_reached.add(name)
                pending.extend(compiler.calls[name])
        require(step_reached == selected_scope['functions'].keys(), 'Step scope is not its exact call closure')
        reached.update(step_reached)
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

    Compiler().compile({'constants': {'clauseKey': 'conformance', 'mode': 'configuration',
                                     'typeId': 'conformance'}, 'do': [{'$return': {}}]},
                       definition=plan)
    print('Compiled selected Preparation Plan; checking step closures', flush=True)
    programs, selected = step_programs(plan)
    compile_closure(Compiler, programs, stock, scope, selected)
    check_selection(bridge, plan, ids[stock_name], ids['Admission Functions'], scope_functions, selected)
    print(f"{row['packageBlueId']}: compiled the Plan and all three admission steps "
          f"against stock and scope. Exact call closure: {len(scope_functions)} functions. "
          "Stock read trap and custom selection checks passed.")


if __name__ == '__main__':
    check(ROOT)
