"""L1: representation operations never reserve Python parameter names."""
import itertools
import json
import unittest

from blue_language import Language, MemoryProvider
from algorithms.blue import Failure


def wire(value):
    return json.dumps(value, ensure_ascii=False)


def pointer(key):
    return '/' + key.replace('~', '~0').replace('/', '~1')


class RepresentationFieldNames(unittest.TestCase):
    methods = ('split', 'collapse', 'expand')

    def check_result(self, language, source, cuts, scalar_path, method):
        original = language.identify(source, mode='exact')
        result = getattr(language, method)(source, cuts)
        if method == 'split':
            self.assertEqual(result['blueId'], original)
            provider = MemoryProvider()
            for rid, body in result['fragments'].items():
                if rid in result['proofTexts']:
                    provider.set_response(rid, {'proof': result['proofTexts'][rid], 'body': body})
                else:
                    provider.set_exact(rid, body)
            verifier = Language(provider)
            for rid, body in result['fragments'].items():
                if rid not in result['proofTexts']:
                    self.assertEqual(verifier.identify(body, mode='exact'), rid)
            text = result['rootText']
        else:
            provider = MemoryProvider(language.provider.snapshot())
            text = result
        fresh = Language(provider)
        self.assertEqual(fresh.identify(text, mode='exact'), original)
        self.assertEqual(fresh.query(text, scalar_path, mode='exact'),
                         {'outcome': 'Established', 'value': {'kind': 'Integer', 'decimal': '1'}})
        return result

    def test_field_n_is_supported_by_all_representation_operations(self):
        source = wire({'n': {'child': [1, 2]}})
        for method in self.methods:
            with self.subTest(method=method):
                language = Language()
                # Independently recorded on unchanged gas-4 before the repair.
                self.assertEqual(language.publish(source), 'Enz3sgAK3Lm2zfXWn1QLUmNCSMewiBtbyQv1uWc9crUN')
                self.check_result(language, source, ['/n/child'], '/n/child/items/0', method)

    def test_root_nested_and_list_positions_direct_and_descendant_selection(self):
        for source, base in [({'n': {'child': [1, 2]}}, '/n'),
                             ({'outer': {'n': {'child': [1, 2]}}}, '/outer/n'),
                             ({'rows': [{'n': {'child': [1, 2]}}]}, '/rows/items/0/n')]:
            for suffix, method in itertools.product(('', '/child'), self.methods):
                with self.subTest(base=base, suffix=suffix, method=method):
                    language = Language(); text = wire(source); language.publish(text)
                    self.check_result(language, text, [base + suffix], base + '/child/items/0', method)

    def test_helper_names_and_escaped_keys_are_ordinary_fields(self):
        for key, method in itertools.product(
                ('n', 'node', 'data', 'updates', 'm', 'k', 'v', 'b', 'fn', 'parts',
                 'c', 'self', 'text', 'paths', '', 'a/b', 'a~b', '~1', '😀'), self.methods):
            with self.subTest(key=key, method=method):
                language = Language(); text = wire({key: {'child': [1, 2]}}); language.publish(text)
                base = pointer(key)
                self.check_result(language, text, [base + '/child'], base + '/child/items/0', method)

    def test_verified_ancestors_and_multiple_cut_order(self):
        for referenced, method in itertools.product((False, True), self.methods):
            language = Language(); body = {'n': {'child': [1, 2]}, 'right': {'leaf': 3}}
            rid = language.publish(wire(body)); source = wire({'blueId': rid}) if referenced else wire(body)
            results = []
            for cuts in itertools.permutations(('/n', '/n/child', '/right')):
                with self.subTest(referenced=referenced, method=method, cuts=cuts):
                    results.append(self.check_result(language, source, [*cuts, cuts[0]], '/n/child/items/0', method))
            self.assertTrue(all(result == results[0] for result in results))

    def test_verified_nested_and_list_ancestors(self):
        for method in self.methods:
            language = Language(); rid = language.publish(wire({'n': {'child': [1, 2]}}))
            source = wire({'rows': [{'blueId': rid}]}); language.publish(source)
            self.check_result(language, source, ['/rows/items/0/n/child'], '/rows/items/0/n/child/items/0', method)

    def test_missing_and_corrupt_required_ancestors_remain_errors(self):
        good = Language(); rid = good.publish(wire({'n': {'child': [1, 2]}}))
        for corrupt, method in itertools.product((False, True), self.methods):
            language = Language()
            if corrupt: language.provider.set_exact(rid, wire({'n': {'child': [9]}}))
            else: language.provider.set_unavailable(rid)
            with self.subTest(corrupt=corrupt, method=method):
                with self.assertRaises(Failure) as caught:
                    getattr(language, method)(wire({'blueId': rid}), ['/n/child'])
                self.assertEqual(caught.exception.category, 'ProviderBlueIdMismatch' if corrupt else 'ProviderUnavailable')

    def test_invalid_and_absent_pointers_keep_their_categories(self):
        source = wire({'n': {'child': [1, 2]}})
        for method in self.methods:
            for path in ('n', '/n~2', '/n/child/items/01', '/n/child/items'):
                with self.subTest(method=method, path=path):
                    with self.assertRaises(Failure) as caught:
                        getattr(Language(), method)(source, [path])
                    self.assertEqual(caught.exception.category, 'InvalidPath')
            with self.assertRaises(Failure) as caught:
                getattr(Language(), method)(source, ['/missing'])
            self.assertEqual(caught.exception.category, 'InvalidPath' if method == 'split' else 'PathAbsent')

    def test_supported_cyclic_cuts_preserve_member_and_owning_proof(self):
        for method in self.methods:
            language = Language()
            finalized = language.finalize([wire({'name': 'Loop', 'n': {'child': [1, 2]},
                                                  'next': {'blueId': 'this#0'}})], publish=True)
            rid = finalized['blueIds'][0]
            source = wire({'n': {'blueId': rid}}); language.publish(source)
            result = self.check_result(language, source, ['/n/n/child', '/n/next'], '/n/n/child/items/0', method)
            if method == 'split':
                self.assertIn(rid, result['proofTexts'])
                provider = MemoryProvider()
                provider.set_response(rid, {'proof': result['proofTexts'][rid], 'body': result['fragments'][rid]})
                fresh = Language(provider)
                self.assertIn('n', json.loads(fresh.verify(rid)))
                self.assertEqual(fresh.identify(wire({'blueId': rid}), mode='exact'), rid)
                provider.set_response(rid, {'body': result['fragments'][rid]})
                with self.assertRaises(Failure) as caught: Language(provider).verify(rid)
                self.assertEqual(caught.exception.category, 'InvalidCyclicProof')


if __name__ == '__main__':
    unittest.main()
