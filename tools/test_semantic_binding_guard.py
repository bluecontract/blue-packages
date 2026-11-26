from unittest import TestCase

from semantic_sources import evidence


SUBJECT = 'A' * 44
PLANNER = 'B' * 44
PARENT = 'C' * 44
CLAUSE_KEY = {'$const': 'clauseKey'}


def let(name, expr):
    return {'$let': {'name': name, 'expr': expr}}


def lookup(source, key, default):
    return {'$pointerGet': {'object': {'$var': source}, 'path': '/bindings/' + key,
                            'default': default}}


class KnownConfigurablePathsTests(TestCase):
    def test_own_clause_selectors_remain_evidence_but_are_not_fixed_state(self):
        variable = {'$concat': ['/stored_', CLAUSE_KEY]}
        stable = {'$concat': ['/fixed_', CLAUSE_KEY]}
        body = [
            let('candidate', {'$document': {'$concat': ['/clauseRuntime/work/candidate/', CLAUSE_KEY]}}),
            let('published', {'$document': '/anotherClause'}),
            let('first', lookup('candidate', 'target', variable)),
            let('second', lookup('candidate', 'amount', '/amount')),
            let('foreign', lookup('published', 'target', stable)),
            {'$return': {'first': {'$var': 'first'}, 'read': {'$document': '/amount'}}},
        ]
        values = {
            SUBJECT: {'hookDefinition': {'type': {'blueId': PLANNER}}},
            PLANNER: {'functions': {'plan': {'do': body}}},
        }
        result = evidence(SUBJECT, values)
        self.assertEqual([
            {'bindingPointer': '/bindings/amount', 'defaultPath': '/amount',
             'definitionBlueId': PLANNER, 'function': 'plan'},
            {'bindingPointer': '/bindings/target', 'defaultPath': '/stored_{clauseKey}',
             'definitionBlueId': PLANNER, 'function': 'plan'},
        ], result['configurablePathDefaults'])
        self.assertNotIn('/stored_{clauseKey}', result['clausePaths'])
        self.assertNotIn('/amount', result['documentPaths'])
        self.assertIn('/fixed_{clauseKey}', result['clausePaths'])
        self.assertEqual([], result['bindings'])

    def test_overridden_function_does_not_establish_a_configurable_default(self):
        body = [
            let('candidate', {'$document': {'$concat': ['/clauseRuntime/work/candidate/', CLAUSE_KEY]}}),
            let('slot', lookup('candidate', 'target', {'$concat': ['/other_', CLAUSE_KEY]})),
        ]
        values = {
            SUBJECT: {'hookDefinition': {'type': {'blueId': PLANNER}}},
            PLANNER: {'type': {'blueId': PARENT}, 'functions': {'plan': {'do': []}}},
            PARENT: {'functions': {'plan': {'do': body}}},
        }
        self.assertNotIn('configurablePathDefaults', evidence(SUBJECT, values))

    def test_let_alias_shadow_does_not_claim_a_foreign_lookup_as_own(self):
        for replacement in ({'$document': '/anotherClause'}, 'literal', [], None):
            body = [
                let('candidate', {'$document': {'$concat': ['/clauseRuntime/work/candidate/', CLAUSE_KEY]}}),
                let('candidate', replacement),
                let('slot', lookup('candidate', 'target', {'$concat': ['/other_', CLAUSE_KEY]})),
            ]
            values = {
                SUBJECT: {'hookDefinition': {'type': {'blueId': PLANNER}}},
                PLANNER: {'functions': {'plan': {'do': body}}},
            }
            with self.subTest(replacement=replacement):
                self.assertNotIn('configurablePathDefaults', evidence(SUBJECT, values))

    def test_uncalled_helper_does_not_remove_a_host_path(self):
        helper = [
            let('candidate', {'$document': {'$concat': ['/clauseRuntime/work/candidate/', CLAUSE_KEY]}}),
            let('slot', lookup('candidate', 'target', '/status')),
        ]
        native_read = {'$document': '/status'}
        values = {
            SUBJECT: {'hookDefinition': {'type': {'blueId': PLANNER}}},
            PLANNER: {'functions': {
                'plan': {'do': [{'$return': native_read}]},
                'other': {'do': helper},
            }},
        }
        result = evidence(SUBJECT, values)
        self.assertNotIn('configurablePathDefaults', result)
        self.assertIn('/status', result['documentPaths'])

    def test_direct_plan_call_uses_the_inherited_helper(self):
        helper = [
            let('candidate', {'$document': {'$concat': ['/clauseRuntime/work/candidate/', CLAUSE_KEY]}}),
            let('slot', lookup('candidate', 'target', '/status')),
        ]
        values = {
            SUBJECT: {'hookDefinition': {'type': {'blueId': PLANNER}}},
            PLANNER: {'type': {'blueId': PARENT}, 'functions': {'plan': {'do': [
                {'$return': {'$call': {'function': 'selectPath', 'args': {}}}},
            ]}}},
            PARENT: {'functions': {'selectPath': {'do': helper}}},
        }
        self.assertEqual([
            {'bindingPointer': '/bindings/target', 'defaultPath': '/status',
             'definitionBlueId': PARENT, 'function': 'selectPath'},
        ], evidence(SUBJECT, values)['configurablePathDefaults'])
