"""Host accounting form is distinct from value reads and semantic output."""
import unittest
from collections.abc import Mapping
from blue_bex import Context, Engine, Gas, GasExhausted
from blue_bex.values import HostValue, size_parts, equal


class BoundObject(HostValue,Mapping):
    """A test host's asserted identity capability, not authored BEX syntax."""
    def __init__(self,value,identity):self.value=value;self.identity=identity;self.reads=[]
    def value_kind(self):return 'object'
    def __iter__(self):return iter(self.value)
    def __len__(self):return len(self.value)
    def __getitem__(self,key):self.reads.append(key);return self.value[key]
    def blue_output(self):return dict(self.value)
    def accounting_view(self):return {'blueId':self.identity}


class TransferAccounting(unittest.TestCase):
    def test_independent_token_vector_and_first_rejection(self):
        value=BoundObject({'deep':{'body':'x'*10000}},'x'*44)
        gas=Gas();parts=list(size_parts(value,gas.charge))
        # One object member, the six UTF-16 units in blueId, 44 in the ID.
        self.assertEqual(parts,[1,6,44]);self.assertEqual(value.reads,[])
        self.assertEqual([(r['counter'],r['units']) for r in gas.trace],
            [('valueMember',1),('valueMember',0),('textWork',1),('textWork',1),('textWork',1)])
        self.assertEqual(gas.used,4)
        # Effect base 5 + fragments 51 + key/scalar prepayment 4 = 60.
        from blue_bex.runtime import Invocation
        program=Engine().compile({'expr':0})
        gas=Gas();Invocation(program,Context(),gas,{}).sized('appendEventBase',value)
        self.assertEqual(gas.used,60)
        for limit in range(61):
            meter=Gas(limit);run=Invocation(program,Context(),meter,{})
            if limit<60:
                with self.assertRaises(GasExhausted):run.sized('appendEventBase',value)
                expected=next(row for row in gas.trace if row['before']+row['amount']>limit)
                self.assertEqual(meter.rejected,{**expected,'remaining':limit-expected['before'],'cap':'SHARED'})
            else:run.sized('appendEventBase',value)
        self.assertEqual(value.reads,[])

    def test_all_sized_consumers_share_boundary_and_keep_value_semantics(self):
        value=BoundObject({'a':1,'b':[2,3]},'x'*44)
        programs=[{'do':[{'$appendEvent':{'$document':'/'}}]},
                  {'do':[{'$appendEvents':[{'$document':'/'},{'$document':'/'}]}]},
                  {'do':[{'$appendChange':{'op':'add','path':'/x','val':{'$document':'/'}}}]},
                  {'do':[{'$appendChanges':[{'op':'add','path':'/x','val':{'$document':'/'}}]}]},
                  {'expr':{'$objectSet':{'object':{},'key':'x','val':{'$document':'/'}}}},
                  {'expr':{'$pointerSet':{'object':{},'path':'/x','val':{'$document':'/'}}}}]
        for program in programs:
            value.reads.clear();result=Engine().execute(program,Context(document=value))
            self.assertEqual(value.reads,[])
            self.assertTrue(any(row['counter']=='textWork' for row in result.gas_trace))
        self.assertTrue(equal(value,{'a':1,'b':[2,3]},Gas().charge))
        self.assertEqual(value.reads,['a','b'])
        self.assertEqual(Engine().execute({'expr':{'$keys':{'$document':'/'}}},Context(document=value)).value,['a','b'])
        self.assertEqual(value.blue_output(),{'a':1,'b':[2,3]})

if __name__=='__main__':unittest.main()
