"""Focused conformance cases, run only against extracted specification modules."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
from pathlib import Path
import unittest

from blue_bex import BexError, Context, Engine, Gas, GasExhausted, UNDEFINED
from blue_bex.values import HostValue, pointer_get


def patch(op, path, **value):
    return {'$appendChange': dict(op=op, path=path, **value)}


def read(path='/q', view='canonical'):
    return {'$resultValue': {'path': path, 'view': view}}


def let(name, expression):
    return {'$let': {'name': name, 'expr': expression}}


def run(document, *steps, gas=None):
    return Engine().execute({'do': list(steps)}, Context(document=document), gas=gas)


class CountingGas(Gas):
    def __init__(self, limit=100_000):
        super().__init__(limit)
        self.copies = []

    def charge(self, counter, units=1, **kwargs):
        super().charge(counter, units, **kwargs)
        if counter == 'valueMember' and units >= 90:
            self.copies.append(units)


class PreviewTests(unittest.TestCase):
    def test_structural_operations(self):
        cases = [
            ('remove', '0', ['B', 'C']), ('remove', '1', ['A', 'C']),
            ('remove', '2', ['A', 'B']), ('add', '0', ['X', 'A', 'B', 'C']),
            ('add', '1', ['A', 'X', 'B', 'C']), ('add', '3', ['A', 'B', 'C', 'X']),
            ('add', '-', ['A', 'B', 'C', 'X']), ('replace', '1', ['A', 'X', 'C']),
        ]
        for op, index, expected in cases:
            with self.subTest(op=op, index=index):
                self.assertEqual(expected, run({'q': ['A', 'B', 'C']},
                    patch(op, '/q/' + index, val='X'), {'$return': read()}).value)
        for index in ('0', '-'):
            self.assertEqual(['X'], run({'q': []}, patch('add', '/q/' + index, val='X'),
                                       {'$return': read()}).value)
        self.assertEqual([], run({'q': ['A']}, patch('remove', '/q/0'),
                                 {'$return': read()}).value)

    def test_invalid_indices_and_intermediate_segments(self):
        for op in ('add', 'replace', 'remove'):
            bad = ['-1', '01', '4', '999999999999999999999999']
            if op != 'add': bad += ['-', '3']
            for index in bad:
                with self.subTest(op=op, index=index), self.assertRaises(BexError):
                    run({'q': ['A', 'B', 'C']}, patch(op, '/q/' + index, val='X'),
                        {'$return': read()})
        for path in ('/q/-/x', '/q/1/x'):
            with self.subTest(path=path), self.assertRaises(BexError):
                run({'q': [{}]}, patch('add', path, val='X'), {'$return': read()})

    def test_successive_removals(self):
        result = run({'q': ['A', 'B', 'C']}, patch('remove', '/q/0'),
                     patch('remove', '/q/0'), {'$return': read()})
        self.assertEqual(['C'], result.value)

    def test_each_patch_projected_once(self):
        gas = CountingGas()
        steps = []
        for _ in range(5):
            steps += [patch('remove', '/q/0'), let('v', read())]
        steps.append({'$return': read()})
        result = run({'q': ['A'] * 100}, *steps, gas=gas)
        self.assertEqual([100, 99, 98, 97, 96], gas.copies)
        self.assertEqual(95, len(result.value))

    def test_mixed_nested_patches_size_and_iteration(self):
        result = run({'q': [{'name': 'A'}, {'name': 'B'}, {'name': 'C'}]},
                     patch('remove', '/q/0'), patch('add', '/q/1', val={'name': 'X'}),
                     patch('replace', '/q/2/name', val='Y'), patch('remove', '/q/0'),
                     {'$forEach': {'item': 'item', 'in': read(),
                                   'do': [{'$appendEvent': {'$var': 'item'}}]}},
                     {'$return': {'list': read(), 'size': {'$size': read()}}})
        self.assertEqual({'list': [{'name': 'X'}, {'name': 'Y'}], 'size': 2}, result.value)
        self.assertEqual([{'name': 'X'}, {'name': 'Y'}], result.events)
        self.assertEqual([['B']], run({'q': [['A', 'B']]}, patch('remove', '/q/0/0'),
                                      {'$return': read()}).value)

    def test_missing_read_cannot_be_patch_value(self):
        prefix = [patch('remove', '/q/0'), patch('remove', '/q/0')]
        self.assertIs(UNDEFINED, run({'q': ['A', 'B', 'C']}, *prefix,
                                      {'$return': read('/q/1')}).value)
        for op in ('add', 'replace'):
            with self.subTest(op=op), self.assertRaisesRegex(BexError, 'patch val is required'):
                run({'q': ['A', 'B', 'C']}, *prefix, patch(op, '/bad', val=read('/q/1')))

    def test_functions_capture_effects_and_patch_values(self):
        program = {'functions': {'capture': {'do': [
            {'$appendChanges': {'$literal': [{'op': 'remove', 'path': '/q/0'}]}},
            {'$return': read()}]}}, 'do': [
            let('original', read('/')), let('saved', {'$call': {'function': 'capture'}}),
            {'$appendEvent': {'$var': 'saved'}}, patch('add', '/saved', val={'$var': 'saved'}),
            let('changes', {'$changeset': True}), let('events', {'$events': True}),
            patch('remove', '/q/0'),
            {'$return': {'old': {'$var': 'original'}, 'saved': {'$var': 'saved'},
                         'latest': read(), 'patchValue': read('/saved'),
                         'changes': {'$var': 'changes'}, 'events': {'$var': 'events'}}}]}
        result = Engine().execute(program, Context(document={'q': ['A', 'B', 'C']}))
        self.assertEqual({'old': {'q': ['A', 'B', 'C']}, 'saved': ['B', 'C'],
                          'latest': ['C'], 'patchValue': ['B', 'C'],
                          'changes': [{'op': 'remove', 'path': '/q/0'},
                                      {'op': 'add', 'path': '/saved', 'val': ['B', 'C']}],
                          'events': [['B', 'C']]}, result.value)
        self.assertEqual([['B', 'C']], result.events)
        self.assertEqual(['B', 'C'], result.changeset[1]['val'])

    def test_document_pointer_set_object_rules_and_root_replacement(self):
        document = {'q': ['A', 'B']}
        self.assertEqual(document, run(document, patch('remove', '/q/0'),
                                       {'$return': {'$document': '/'}}).value)
        sparse = run(document, {'$return': {'$pointerSet': {
            'object': {'$document': '/'}, 'path': '/q/0', 'op': 'remove'}}}).value
        self.assertEqual([UNDEFINED, 'B'], sparse['q'])
        self.assertEqual({'new': {'field': 'X'}}, run({}, patch('remove', '/missing'),
            patch('replace', '/new/field', val='X'), {'$return': read('/')}).value)
        self.assertEqual({'q': ['B']}, run(document, patch('replace', '/', val={'q': ['B']}),
                                           {'$return': read('/')}).value)
        self.assertIs(UNDEFINED, run(document, patch('remove', '/'),
                                     {'$return': read('/')}).value)

    def test_views_and_every_host_callback(self):
        calls = []
        def reader(path, view, root):
            calls.append(view)
            return pointer_get(root, path)
        context = Context(document={'q': ['A', 'B', 'C']},
                          resolved_document={'q': ['X', 'Y', 'Z']}, read_document=reader)
        program = {'do': [patch('remove', '/q/0'), let('c', read('/q/0')),
            let('r', read('/q/0', 'resolved')), patch('remove', '/q/0'),
            {'$return': [read('/q/0'), read('/q/0'), read('/q/0', 'resolved'),
                         {'$var': 'c'}, {'$var': 'r'}]}]}
        self.assertEqual(['C', 'C', 'Z', 'B', 'Y'], Engine().execute(program, context).value)
        self.assertEqual(['canonical', 'resolved', 'canonical', 'canonical', 'resolved'], calls)
        with self.assertRaisesRegex(BexError, 'resolved document capability unavailable'):
            run({}, {'$return': read('/', 'resolved')})
        def unavailable(path, view, root):
            if len(calls) == 6: raise BexError('resource unavailable')
            calls.append(view)
            return pointer_get(root, path)
        context.read_document = unavailable
        with self.assertRaisesRegex(BexError, 'resource unavailable'):
            Engine().execute({'do': [let('a', read()), {'$return': read()}]}, context)
        self.assertEqual(6, len(calls))

    def test_no_read_and_unselected_read_do_not_project(self):
        gas = CountingGas()
        run({'q': ['A'] * 100}, patch('remove', '/q/999'),
            {'$if': {'cond': False, 'then': [{'$return': read()}]}}, gas=gas)
        self.assertEqual([], gas.copies)

    def test_batch_and_repeated_reads_only_project_suffix_once_per_view(self):
        for repetitions in (1, 4):
            with self.subTest(repetitions=repetitions):
                gas = CountingGas()
                steps = [patch('remove', '/q/0'), patch('remove', '/q/0')]
                steps += [let('x', read()) for _ in range(repetitions)]
                steps += [let('x', read('/q', 'resolved')), {'$return': read()}]
                context = Context(document={'q': ['A'] * 100},
                                  resolved_document={'q': ['X'] * 100})
                self.assertEqual(['A'] * 98, Engine().execute({'do': steps}, context, gas=gas).value)
                self.assertEqual([100, 99, 100, 99], gas.copies)

    def test_repeat_concurrent_invocations_and_exact_budgets(self):
        engine = Engine()
        program = engine.compile({'do': [patch('remove', '/q/0'), let('a', read()),
            patch('add', '/q/0', val='X'), {'$return': read()}]})
        context = Context(document={'q': ['A', 'B', 'C']})
        expected = engine.execute(program, context)
        self.assertEqual(['X', 'B', 'C'], expected.value)
        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual([expected] * 4, list(executor.map(
                lambda _: engine.execute(program, context), range(4))))
        exact = expected.gas_used
        for limit in (exact - 1, exact, exact + 1):
            with self.subTest(limit=limit):
                parent = Gas(1000)
                gas = Gas(limit, parent=parent)
                if limit < exact:
                    with self.assertRaises(GasExhausted): engine.execute(program, context, gas=gas)
                    first = dict(gas.rejected)
                    with self.assertRaises(GasExhausted): gas.charge('expressionBase')
                    self.assertEqual(first, gas.rejected)
                else:
                    self.assertEqual(expected, engine.execute(program, context, gas=gas))
                self.assertEqual(gas.used, parent.used)
                self.assertLessEqual(gas.used, limit)
                self.assertFalse(hasattr(gas, 'trace'))
        parent = Gas(exact - 1)
        child = Gas(1000, parent=parent)
        with self.assertRaises(GasExhausted): engine.execute(program, context, gas=child)
        self.assertEqual('SHARED', parent.rejected['cap'])
        self.assertEqual(parent.used, child.used)

    def test_charge_before_host_list_copy_and_untouched_subtrees(self):
        class HostList(HostValue):
            def __init__(self): self.reads = 0
            def value_kind(self): return 'list'
            def __len__(self): return 100
            def __getitem__(self, index):
                self.reads += 1
                return 'A'
            def blue_output(self): raise AssertionError('recursive materialization')
        class RejectCopy(Gas):
            def charge(self, counter, units=1, **kwargs):
                if counter == 'valueMember' and units == 100: raise BexError('copy denied')
                super().charge(counter, units, **kwargs)
        touched, untouched = HostList(), HostList()
        document = {'q': touched, 'untouched': untouched}
        steps = [patch('remove', '/q/0'), {'$return': read('/q/0')}]
        with self.assertRaisesRegex(BexError, 'copy denied'):
            run(document, *steps, gas=RejectCopy())
        self.assertEqual((0, 0), (touched.reads, untouched.reads))
        self.assertEqual('A', run(document, *steps).value)
        self.assertEqual((100, 0), (touched.reads, untouched.reads))

    def test_explicit_return_does_not_replace_preview_accumulator(self):
        result = run({'q': ['A', 'B']}, patch('remove', '/q/0'),
            {'$return': {'changeset': [{'op': 'add', 'path': '/observed', 'val': read('/q/0')}]}})
        self.assertEqual({'changeset': [{'op': 'add', 'path': '/observed', 'val': 'B'}]}, result.value)
        self.assertEqual([{'op': 'remove', 'path': '/q/0'}], result.changeset)

    def test_unchanged_arithmetic_control_and_collection_vectors(self):
        # Fixed original vectors: arithmetic, short circuit, undefined, collections
        # and type-sensitive equality. No candidate-derived expected values.
        vectors = json.loads((Path(__file__).resolve().parents[1] /
                              'conformance/bex.json').read_text(), parse_float=Decimal)['vectors']
        def decode(value):
            if isinstance(value, dict):
                if set(value) == {'$undefined'}: return UNDEFINED
                if set(value) == {'$decimal'}: return Decimal(value['$decimal'])
                return {key: decode(item) for key, item in value.items()}
            if isinstance(value, list): return [decode(item) for item in value]
            return value
        selected = {'bex-python-' + f'{n:04}' for n in range(20)}
        rows = [vector for vector in vectors if vector['id'] in selected]
        self.assertEqual(selected, {vector['id'] for vector in rows})
        for vector in rows:
            with self.subTest(vector=vector['id']):
                request, expected = decode(vector['request']), decode(vector['expected'])
                result = Engine().execute(request['program'], gas_limit=request['gasLimit'])
                self.assertEqual(expected, dict(outcome='Established', value=result.value,
                    changeset=result.changeset, events=result.events, gasUsed=result.gas_used))


if __name__ == '__main__':
    unittest.main()
