"""Independent F2/F3 vectors; expectations follow the declared charge schedule."""
import itertools
import unittest
from collections.abc import Mapping
from unittest.mock import patch
from blue_bex import Engine, Context, Gas, GasExhausted
from blue_bex.values import HostValue, UNDEFINED, equal
from blue_host import HostIncomplete


class LazyObject(HostValue, Mapping):
    def __init__(self, values, reads):self.values=values;self.reads=reads
    def value_kind(self):return 'object'
    def __len__(self):return len(self.values)
    def __iter__(self):return iter(self.values)
    def __getitem__(self,key):
        self.reads.append(key)
        value=self.values[key]
        return LazyObject(value,self.reads) if type(value) is dict else value


def observed(program,context=None,limit=100000):
    gas=Gas(limit)
    try:
        result=Engine().execute(program,context,gas=gas)
        return ('OK',result.value,gas.used,gas.trace,gas.rejected)
    except GasExhausted:
        return ('GAS_LIMIT_EXCEEDED',None,gas.used,gas.trace,gas.rejected)


class DeterministicGas(unittest.TestCase):
    def test_native_literal_permutations_at_every_boundary(self):
        rows=[('a',1),('b','x'*200),('😀',{'é':[1,1.0]}),('\ue000',False)]
        right={**dict(rows),'a':2}
        programs=[{'expr':{'$eq':[{'$literal':dict(order)},{'$literal':right}]}}
                  for order in itertools.permutations(rows)]
        expected=observed(programs[0]);self.assertIs(expected[1],False)
        # Same program identity despite native literal insertion order.
        from blue_language import Language
        from algorithms import blue as L
        language=Language()
        self.assertEqual(len({language.identify(L.wire_text(p)) for p in programs}),1)
        boundaries={0,13,expected[2]}
        for row in expected[3]:boundaries.update((max(0,row['before']+row['amount']-1),row['before']+row['amount']))
        for budget in sorted(boundaries):
            want=observed(programs[0],limit=budget)
            for program in programs[1:]:self.assertEqual(observed(program,limit=budget),want)

    def test_nested_nonascii_key_order_and_lazy_early_exit(self):
        # Code-point order puts U+E000 before U+1F600 (UTF-16 order differs).
        for lazy in (False,True):
            for order in itertools.permutations(('😀','\ue000','é')):
                reads=[]
                a={key: {'z':1,'a':'x'*200} if key=='é' else 1 for key in order}
                b={**a,'\ue000':2}
                x=LazyObject(a,reads) if lazy else a;y=LazyObject(b,reads) if lazy else b
                gas=Gas();self.assertFalse(equal(x,y,gas.charge))
                if lazy:self.assertEqual(reads,['é','é','a','a','z','z','\ue000','\ue000'])
                if order==('😀','\ue000','é'):expected=gas.trace
                else:self.assertEqual(gas.trace,expected)

    def test_equal_different_keys_and_shared_comparison_operators(self):
        cases=[({'a':1,'b':[]},{'b':[],'a':1.0},True),
               ({'a':1},{'b':1},False),({'a':{'v':'x'*200}},{'a':{'v':'x'*200}},True)]
        for left,right,want in cases:
            for op in ('$eq','$ne','$includes'):
                args=[{'$literal':left},{'$literal':right}]
                if op=='$includes':args={'list':{'$literal':[left]},'val':{'$literal':right}}
                result=Engine().execute({'expr':{op:args}})
                self.assertEqual(result.value,not want if op=='$ne' else want)

    def test_ordering_is_prepaid_and_values_are_not_read_after_rejection(self):
        reads=[];obj=LazyObject({'b':'x'*200,'a':1},reads)
        gas=Gas(1)
        with self.assertRaises(GasExhausted):equal(obj,obj,gas.charge)
        self.assertEqual(reads,[])
        self.assertEqual(gas.rejected['counter'],'valueMember')
        # All key work is paid before a first child lookup.
        full=Gas();equal(obj,LazyObject({'a':2,'b':'x'*200},[]),full.charge)
        stop=next(row['before'] for row in full.trace[1:] if row['counter']=='valueMember' and row['units']==1)
        reads.clear()
        with self.assertRaises(GasExhausted):equal(obj,LazyObject({'a':2,'b':'x'*200},[]),Gas(stop).charge)
        # Fetching a pair precedes its pair-inspection debit, but traversal
        # never reaches the undecisive long-text sibling.
        self.assertNotIn('b',reads)

    def test_unwrap_depth_counts_terminal_inspection(self):
        program={'expr':{'$unwrap':{'$event':'/'}}}
        for depth in (0,1,10,1000,20000):
            value=1
            for _ in range(depth):value={'value':value}
            result=Engine().execute(program,Context(event=value))
            self.assertEqual((result.value,result.gas_used),(1,5+depth+1))
            rows=[row for row in result.gas_trace if row['counter']=='valueMember']
            self.assertEqual(len(rows),depth+1)
            with self.assertRaises(GasExhausted):Engine().execute(program,Context(event=value),gas_limit=result.gas_used-1)
        for value in ({},{'value':UNDEFINED},False,0,'',[],None):
            result=Engine().execute(program,Context(event=value))
            self.assertEqual(result.value,value);self.assertEqual(result.gas_used,6)

    def test_unwrap_debits_before_kind_and_single_host_read(self):
        program={'expr':{'$unwrap':{'$event':'/'}}};reads=[]
        value=LazyObject({'value':{'value':1}},reads)
        for limit,want in ((5,[]),(6,['value']),(7,['value','value'])):
            reads.clear()
            with self.assertRaises(GasExhausted):Engine().execute(program,Context(event=value),gas_limit=limit)
            self.assertEqual(reads,want)
        result=Engine().execute(program,Context(event=value),gas_limit=8)
        self.assertEqual((result.value,result.gas_used),(1,8))
        class Interrupted(LazyObject):
            def value_kind(self):raise MemoryError('host stopped')
        with self.assertRaises(GasExhausted):Engine().execute(program,Context(event=Interrupted({},[])),gas_limit=5)
        with self.assertRaises(HostIncomplete):Engine().execute(program,Context(event=Interrupted({},[])),gas_limit=6)


if __name__=='__main__':unittest.main()
