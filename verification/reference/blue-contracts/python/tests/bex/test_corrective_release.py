import unittest
from decimal import Decimal
from blue_bex import Compiler, CompileError

class CorrectiveBex(unittest.TestCase):
    def test_all_user_binding_declarations_reject_reserved_names(self):
        for name in ('$previousItems', '$previous', 'blueId', 'type', 'value'):
            programs = [
                {'do':[{'$let':{'name':name,'expr':1}}]},
                {'do':[{'$let':{'vars':{name:1}}}]},
                {'do':[{'$forEach':{'in':[1],'item':name,'do':[]}}]},
                {'expr':{'$map':{'in':[1],'item':name,'expr':1}}},
                {'expr':{'$reduce':{'in':[1],'item':'row','acc':name,'init':0,'expr':1}}}]
            for program in programs:
                with self.subTest(name=name,program=program), self.assertRaises(CompileError):
                    Compiler().compile(program)

    def test_includes_uses_numeric_equality_but_not_boolean_equality(self):
        from blue_bex.values import equal
        self.assertTrue(equal(1,Decimal('1.0')))
        self.assertFalse(equal(True,1))
        # Ordinary object keys are data, not binding declarations.
        Compiler().compile({'expr':{'$literal':{'$previousItems':True,'value':0}}})
