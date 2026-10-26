"""§12.5 invocation ledger transitions independent of the Java implementation.

Pinned Language owns Recipe composition, native checks and exact identity.
Counter traversal reuses the independently implemented demand reference, not a
Java trace. This model is a finite ledger adapter, not a Contracts executor.
"""
import bootstrap
from collections import Counter
from fractions import Fraction
from algorithms import blue as L
from blue_language import Language
from demand_reference import Obligations


class Ledger(Obligations):
    def __init__(self, context):
        super().__init__(context)
        self.checks = 0

    def compare(self, left, right):
        # Integral native rational bounds use integer comparison/limb accounting.
        if isinstance(right, Fraction) and right.denominator == 1:
            right = right.numerator
        if type(left) is int and type(right) is int:
            self.charges['integerLimbOperation'] += max(1, (abs(left).bit_length()+31)//32) + max(1, (abs(right).bit_length()+31)//32)
        return super().compare(left, right)

    def require(self, selected, kind, coverage=None):
        coverage = coverage if kind == 'container' else 'complete-selected-subtree'
        key = (selected.key(), kind, coverage)
        if key in self.success:
            self.charges['validationProofReused'] += 1
            return
        pending = {}
        if kind == 'container':
            for part in selected.parts:
                if self.open(part).has('type'):
                    self.charges['typeEdgeFollowed'] += 1
            head = L.head(selected, self.context)
            self.charges['schemaPredicateEvaluated'] += len(L.describe_constraints(head.constraints))
            self.checks += 1
            # Coverage is a caller-declared occurrence obligation, never a global fact.
            present = L.present_recipe(selected, self.context) if coverage == 'optional-occurrence' else True
            L.validate_schema(head, present, 'value', coverage != 'optional-occurrence', self.context)
        elif kind == 'definition':
            seen = set()
            for part in (*selected.parts, *(L.Ref(tid) for tid in selected.requirements)):
                self.definition(part, seen)
            self.checks += 1
            L.strict_certify(L.recipe_exact_value(selected, self.context), self.context, 'definition')
        elif kind == 'value':
            self.visit(selected, set(), pending, coverage)
            self.checks += 1
            L.strict_certify(L.recipe_exact_value(selected, self.context), self.context, 'value')
            L.validate(selected, self.context, 'value')
        else:
            raise ValueError('UNSUPPORTED_LEDGER_KIND')
        self.success.update(pending)
        self.success[key] = True


def execute_sequence(data):
    def fresh():
        context = Language(core_contracts=False).processing_context()
        nodes = {name: L.normalize(L.preprocess(raw, context), context) for name, raw in data['nodes'].items()}
        return context, nodes, Ledger(context)

    context, nodes, ledger = fresh()
    rows = []
    for action in data['actions']:
        operation = action['op']
        if operation == 'cold':
            context, nodes, ledger = fresh()
        elif operation == 'newInvocation':
            ledger = Ledger(context)
        before = Counter(ledger.charges)
        checks = ledger.checks
        result = {'status': 'OK'}
        try:
            if operation in {'cold', 'newInvocation'}:
                pass
            elif operation == 'supply':
                context.remember(L.normalize(L.preprocess(action['value'], context), context))
            else:
                node = nodes[action['node']]
                selected = L.recipe(node, requirements=tuple(L.identity(nodes[name]) for name in action.get('requirements', [])))
                if operation == 'warm':
                    L.head(selected, context)
                elif operation == 'identity':
                    if not isinstance(node, L.Ref):
                        raise ValueError('EXPLICIT_REFERENCE_REQUIRED')
                    result.update({'identity': L.identity(node), 'local': False,
                                   'establishedFacts': 0, 'validationFacts': 0})
                elif operation == 'require':
                    ledger.require(selected, action['kind'], action.get('coverage'))
                else:
                    raise ValueError('UNSUPPORTED_LEDGER_ACTION')
        except L.Failure as failure:
            result = {'status': 'REJECTED', 'code': 'NEEDS_RESOURCES' if failure.category == 'ProviderUnavailable' else 'LANGUAGE_' + failure.category}
        result['counters'] = dict(sorted((ledger.charges-before).items()))
        result['nativeChecks'] = ledger.checks-checks
        rows.append(result)
    return {'rows': rows}
