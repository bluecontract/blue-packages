"""R1/R2 independent invariants from the second deterministic gas review."""
import copy
import itertools
import unittest
from collections.abc import Mapping
from unittest.mock import patch
from blue_bex import Context, Engine, Gas, GasExhausted
from blue_bex.values import HostValue, equal, size_parts
from tests.bex.test_deterministic_gas import observed, LazyObject

TEXT='x'*200


def pair(shared, unequal=False, sequence=False):
    child={'n':1,'text':TEXT}
    values=[child,child] if shared else [copy.deepcopy(child),copy.deepcopy(child)]
    if unequal:values[1]={**child,'text':TEXT+'!'}
    return values if sequence else dict(zip(('first','second'),values))


def boundaries(trace,total):
    return sorted({0,total,*[n for r in trace for n in (max(0,r['before']+r['amount']-1),r['before']+r['amount'])]})


class KeyObject(HostValue,Mapping):
    def __init__(self,values,key):self.values=values;self.key=key
    def value_kind(self):return 'object'
    def comparison_key(self):return self.key
    def __len__(self):return len(self.values)
    def __iter__(self):return iter(self.values)
    def __getitem__(self,key):return self.values[key]


class ReviewGas(unittest.TestCase):
    def test_shared_copied_mixed_operators_and_boundaries(self):
        for sequence,unequal,op in itertools.product((False,True),(False,True),('$eq','$ne','$includes')):
            programs=[]
            for left,right in itertools.product((False,True),repeat=2):
                a,b=pair(left,sequence=sequence),pair(right,unequal,sequence)
                args=[{'$literal':a},{'$literal':b}]
                if op=='$includes':args={'list':{'$literal':[a]},'val':{'$literal':b}}
                programs.append({'expr':{op:args}})
            result=observed(programs[0]);self.assertEqual(result[1],unequal if op=='$ne' else not unequal)
            for limit in boundaries(result[3],result[2]):
                expected=observed(programs[0],limit=limit)
                for program in programs[1:]:self.assertEqual(observed(program,limit=limit),expected)
        self.assertEqual(observed({'expr':{'$eq':[{'$literal':pair(True)},{'$literal':pair(True)}]}})[2],80)

    def test_host_comparison_keys_are_active_cycle_keys_not_completed_cache(self):
        leaf=KeyObject({'n':1,'text':TEXT},'leaf')
        left=KeyObject({'a':leaf,'b':leaf},'left')
        right=KeyObject({'b':leaf,'a':leaf},'right')
        native={'a':{'n':1,'text':TEXT},'b':{'n':1,'text':TEXT}}
        a,b=Gas(),Gas();self.assertTrue(equal(left,right,a.charge));self.assertTrue(equal(native,copy.deepcopy(native),b.charge))
        self.assertEqual(a.trace,b.trace)
        # New wrapper per cyclic read, stable host identity. Only active paths
        # terminate coinductively; repeated acyclic branches above are charged.
        class Cycle(KeyObject):
            def __getitem__(self,key):return Cycle({'self':None},self.key)
        gas=Gas();self.assertTrue(equal(Cycle({'self':None},'a'),Cycle({'self':None},'b'),gas.charge))
        self.assertLess(gas.used,30)
        x=[];x.append(x);y=[];y.append(y)
        self.assertTrue(equal(x,y,Gas().charge))  # Helper safety, not native input admission.

    def test_effect_permutations_trace_and_rejection(self):
        rows=[('a',1),('b',TEXT)]
        variants=[dict(items) for items in itertools.permutations(rows)]
        variants += [dict(items) for items in itertools.permutations([('😀',{'z':2**130,'é':TEXT}),('\ue000',[{'b':TEXT,'a':1}]),('k'*130,False)])]
        for op in ('$appendEvent','$appendChange'):
            for group in (variants[:2],variants[2:]):
                def program(value):
                    arg={'$literal':value}
                    if op=='$appendChange':arg={'op':'add','path':'/x','val':arg}
                    return {'do':[{op:arg}]}
                expected=observed(program(group[0]))
                for budget in boundaries(expected[3],expected[2]):
                    want=observed(program(group[0]),limit=budget)
                    for value in group[1:]:self.assertEqual(observed(program(value),limit=budget),want)
                for value in group:
                    native=Gas();host=Gas();reads=[]
                    self.assertEqual(list(size_parts(value,native.charge)),list(size_parts(LazyObject(value,reads),host.charge)))
                    self.assertEqual(native.trace,host.trace)
        first=observed({'do':[{'$appendEvent':{'$literal':variants[0]}}]},limit=15)
        self.assertEqual(first[0],'GAS_LIMIT_EXCEEDED')

    def test_sizing_orders_keys_before_lazy_children_and_encoding(self):
        reads=[];obj=LazyObject({'b':TEXT,'a':1},reads)
        with self.assertRaises(GasExhausted):list(size_parts(obj,Gas(0).charge))
        self.assertEqual(reads,[])
        import blue_bex.values as values
        original=values.utf16_length;encoded=[]
        def track(text):encoded.append(text);return original(text)
        with patch.object(values,'utf16_length',side_effect=track):
            with self.assertRaises(GasExhausted):list(size_parts(obj,Gas(1).charge))
        self.assertEqual(encoded,[]);self.assertEqual(reads,[])
        gas=Gas();list(size_parts(obj,gas.charge));self.assertEqual(reads,['a','b'])
        # Code-point order, but a supplementary character contributes two UTF-16 units.
        self.assertEqual(list(size_parts({'😀':'😀','\ue000':''})),[2,1,2,1,2])

if __name__=='__main__':unittest.main()
