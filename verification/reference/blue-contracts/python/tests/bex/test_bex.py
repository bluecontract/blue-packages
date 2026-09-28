"""Public BEX spec vectors plus independent negative/gas/property checks."""
import unittest
from decimal import Decimal
from copy import deepcopy
from blue_bex import *
from blue_bex.values import estimated_size,equal,truthy,pointer_overlay

BAD={'$divide':[1,0]}
MISSING={'$get':{'object':{},'key':'absent'}}
VECTORS=[
 ('literal',{'$literal':{'$doesNotExist':1}},{'$doesNotExist':1}),
 ('null',{'$null':True},None),('empty_object',{'$emptyObject':True},{}),('empty_list',{'$emptyList':True},[]),
 ('unwrap',{'$unwrap':{'value':{'value':3}}},3),('kind',{'$kind':False},'boolean'),
 ('text_bool',{'$text':False},'false'),('integer',{'$integer':'100000000000000000000000000000000000000'},10**38),
 ('number',{'$number':'1.25'},Decimal('1.25')),('boolean_false',{'$boolean':'false'},False),
 ('object_from_null',{'$object':{'$null':True}},{}),('list_from_null',{'$list':{'$null':True}},[]),
 ('concat',{'$concat':['a',2,True,None]},'a2true'),('pointer_join',{'$pointerJoin':['a/b','x~y']},'/a~1b/x~0y'),
 ('pointer_empty',{'$pointerJoin':[]},'/'),('join',{'$join':{'list':['a',2],'separator':','}},'a,2'),
 ('split_trailing',{'$split':{'text':'a,','separator':','}},['a','']),
 ('split_limit',{'$split':{'text':'a,b,c','separator':',','limit':2}},['a','b,c']),
 ('split_one',{'$split':{'text':'a,b','separator':',','limit':1}},['a,b']),
 ('starts',{'$startsWith':['abcdef','abc']},True),('slice_after',{'$sliceAfter':['abcdef','abc']},'def'),
 ('eq_numeric',{'$eq':[1,Decimal('1.0')]},True),('eq_bool_number',{'$eq':[True,1]},False),
 ('ne',{'$ne':[1,2]},True),('gt',{'$gt':['3','2.5']},True),('gte',{'$gte':[2,2]},True),
 ('lt',{'$lt':[1,2]},True),('lte',{'$lte':[2,2]},True),
 ('and_lazy',{'$and':[False,BAD]},False),('or_lazy',{'$or':[True,BAD]},True),
 ('and_empty',{'$and':[]},True),('or_empty',{'$or':[]},False),
 ('not',{'$not':0},False),('truthy_zero',{'$truthy':0},True),('empty',{'$empty':{}},True),
 ('is_empty',{'$isEmpty':False},True),('exists_null',{'$exists':None},True),('exists_missing',{'$exists':MISSING},False),
 ('coalesce_zero',{'$coalesce':[False,0,BAD]},0),('default_empty',{'$default':[]},UNDEFINED),
 ('add',{'$add':[2,'3',5]},10),('subtract',{'$subtract':[10,3,2]},5),('multiply',{'$multiply':[2,3,4]},24),
 ('divide',{'$divide':[24,3,2]},4),('arithmetic_identity',{'$subtract':['7']},7),
 ('keys_unicode',{'$keys':{'😀':1,'\ue000':2,'a':3}},['a','\ue000','😀']),
 ('entries',{'$entries':{'b':2,'a':1}},[{'key':'a','val':1},{'key':'b','val':2}]),
 ('size_scalar',{'$size':'abcdef'},1),('size_null',{'$size':None},0),
 ('size_list',{'$size':[1,2]},2),('list_get',{'$listGet':{'list':[4],'index':0,'default':BAD}},4),
 ('list_get_default',{'$listGet':{'list':[],'index':2,'default':9}},9),
 ('list_concat',{'$listConcat':[[1],[2,3]]},[1,2,3]),('merge',{'$merge':[{'a':1},{'a':2,'b':3}]},{'a':2,'b':3}),
 ('object_set',{'$objectSet':{'object':{'a':1},'key':'b','val':2}},{'a':1,'b':2}),
 ('object_remove',{'$objectSet':{'object':{'a':1},'key':'a','val':MISSING}},{}),
 ('pointer_get',{'$pointerGet':{'object':{'a/b':3},'path':'/a~1b','default':BAD}},3),
 ('pointer_default',{'$pointerGet':{'object':{},'path':'/missing','default':8}},8),
 ('pointer_set',{'$pointerSet':{'object':{},'path':'/a/b','val':4}},{'a':{'b':4}}),
 ('pointer_remove_lazy',{'$pointerSet':{'object':{'a':1},'path':'/a','op':'remove','val':BAD}},{}),
 ('map',{'$map':{'in':[1,2],'item':'n','expr':{'$add':[{'$var':'n'},1]}}},[2,3]),
 ('filter',{'$filter':{'in':{'c':3,'a':1,'b':2},'item':'n','where':{'$gt':[{'$var':'n'},1]}}},{'b':2,'c':3}),
 ('flat_map',{'$flatMap':{'in':[1,2],'item':'n','expr':[{'$var':'n'},{'$var':'n'}]}},[1,1,2,2]),
 ('reduce',{'$reduce':{'in':[1,2,3],'item':'n','acc':'sum','init':0,'expr':{'$add':[{'$var':'sum'},{'$var':'n'}]}}},6),
 ('some',{'$some':{'in':[0,1],'item':'n','where':{'$eq':[{'$var':'n'},0]}}},True),
 ('find',{'$find':{'in':[1,2,3],'item':'n','where':{'$gt':[{'$var':'n'},1]}}},2),
 ('find_entry',{'$findEntry':{'in':{'b':2,'a':1},'item':'n','where':{'$eq':[{'$var':'n'},2]}}},{'key':'b','val':2,'index':1}),
 ('includes',{'$includes':{'list':[1,2,3],'val':2}},True),('has_key',{'$hasKey':{'object':{'a':None},'key':'a'}},True),
 ('has_key_scalar',{'$hasKey':{'object':3,'key':'a'}},False),
 ('object_from_entries',{'$objectFromEntries':[{'key':'x','val':1},{'key':'x','val':2}]},{'x':2}),
 ('choose',{'$choose':{'cond':True,'then':7,'else':BAD}},7),
 ('choose_missing',{'$choose':{'cond':False,'then':BAD}},UNDEFINED),
 ('is_kind',{'$isKind':{'val':1,'kind':['integer','text']}},True),
 ('dollar_object_data',{'$unknown':1,'other':2},{'$unknown':1,'other':2}),
 ('omit_missing_member',{'present':1,'absent':MISSING},{'present':1}),
 ('changes_empty',{'$changeset':True},[]),('events_empty',{'$events':True},[]),
]

class BexVectors(unittest.TestCase):pass
for name,expression,expected in VECTORS:
    def test(self,expression=expression,expected=expected):
        actual=Engine().execute({'expr':expression}).value
        self.assertTrue(equal(actual,expected),(expression,actual,expected))
    setattr(BexVectors,'test_'+name,test)

class BexSemantics(unittest.TestCase):
    def run_expr(self,expr,**kw):return Engine().execute({'expr':expr},**kw)
    def test_root_three_gas(self):self.assertEqual(self.run_expr(1).gas_used,3)
    def test_add_six_gas(self):self.assertEqual(self.run_expr({'$add':[2,3]}).gas_used,6)
    def test_document_read_five_gas(self):self.assertEqual(self.run_expr({'$document':'/n'},context=Context(document={'n':3})).gas_used,5)
    def test_exact_gas_cliff(self):
        for limit in (4,5,6):
            if limit<6:
                with self.assertRaises(GasExhausted):self.run_expr({'$add':[2,3]},gas_limit=limit)
            else:self.assertEqual(self.run_expr({'$add':[2,3]},gas_limit=limit).gas_used,6)
    def test_lazy_gas(self):self.assertEqual(self.run_expr({'$and':[False,BAD]}).gas_used,4)
    def test_binding_read(self):self.assertEqual(self.run_expr({'$binding':'event/message/request/n'},context=Context(bindings={'event':{'message':{'request':{'n':4}}}})).value,4)
    def test_event_current_contract_steps(self):
        ctx=Context(event={'a':1},current_contract={'b':2},steps={'x':{'a':3}})
        self.assertEqual(self.run_expr([{'$event':'/a'},{'$currentContract':'/b'},{'$steps':'x.a'}],context=ctx).value,[1,2,3])
    def test_document_scoping(self):
        ctx=Context(document={'x':3,'nested':{'x':4}},scope='/nested')
        self.assertEqual(self.run_expr([{'$document':'x'},{'$document':'/x'},{'$document':''}],context=ctx).value,[4,3,{'x':4}])
    def test_unavailable_resolved_view(self):
        with self.assertRaises(BexError):self.run_expr({'$document':{'path':'/x','view':'resolved'}})
    def test_utf16_size(self):
        self.assertEqual([estimated_size(x) for x in ['hello','',True,12345,'😀']],[5,1,4,5,2])
    def test_large_integers_exact(self):
        for n in range(1,40):
            val=10**n+7
            self.assertEqual(self.run_expr({'$divide':[{'$multiply':[val,7]},7]}).value,val)
    def test_null_boundary_not_empty_object(self):
        with self.assertRaises(BoundaryError):self.run_expr({'$null':True}).blue_output()
        self.assertEqual(self.run_expr({'$emptyObject':True}).blue_output(),{})
    def test_root_undefined_rejected(self):
        with self.assertRaises(BoundaryError):self.run_expr(MISSING).blue_output()
    def test_undefined_list_rejected_at_boundary(self):
        with self.assertRaises(BoundaryError):self.run_expr([MISSING]).blue_output()
    def test_decimal_overflow_boundary(self):
        with self.assertRaises(BoundaryError):self.run_expr({'$number':'1e999'}).blue_output()
    def test_no_input_mutation(self):
        doc={'x':[1,2,3]};before=deepcopy(doc)
        p={'do':[{'$appendChange':{'op':'remove','path':'/x/1','val':BAD}},{'$return':{'at2':{'$resultValue':'/x/2'},'size':{'$size':{'$resultValue':'/x'}},'gone':{'$exists':{'$resultValue':'/x/1'}}}}]}
        r=Engine().execute(p,Context(document=doc));self.assertEqual(r.value,{'at2':3,'size':3,'gone':False});self.assertEqual(doc,before)
    def test_sparse_overlay_not_output(self):
        p={'do':[{'$appendChange':{'op':'remove','path':'/x/1'}},{'$return':{'$resultValue':'/x'}}]}
        with self.assertRaises(BoundaryError):Engine().execute(p,Context(document={'x':[1,2,3]})).blue_output()
    def test_duplicate_patches_keep_order(self):
        p={'do':[{'$appendChange':{'op':'replace','path':'/x','val':i}} for i in (1,2)]+[{'$return':{'$resultValue':'/x'}}]}
        r=Engine().execute(p,Context(document={'x':0}));self.assertEqual([x['val'] for x in r.changeset],[1,2]);self.assertEqual(r.value,2)
    def test_append_plural_and_events(self):
        p={'do':[{'$appendChanges':[{'op':'add','path':'/x','val':1}]},{'$appendEvents':[{'kind':'A'},{'kind':'A'}]},{'$return':None}]}
        r=Engine().execute(p);self.assertEqual(len(r.changeset),1);self.assertEqual(len(r.events),2);self.assertEqual(r.value,{'changeset':r.changeset,'events':r.events})
    def test_statement_if_lazy_fail(self):
        p={'do':[{'$if':{'cond':False,'then':[{'$fail':'bad'}],'else':[{'$return':7}]}},{'$fail':'after'}]}
        self.assertEqual(Engine().execute(p).value,7)
    def test_return_if_and_fail_if_lazy(self):
        p={'do':[{'$failIf':{'cond':False,'message':BAD}},{'$returnIf':{'cond':False,'expr':BAD}},{'$returnIf':{'cond':True,'expr':3}},{'$fail':'after'}]}
        self.assertEqual(Engine().execute(p).value,3)
    def test_let_set_and_parallel(self):
        p={'do':[{'$let':{'name':'x','expr':1}},{'$let':{'vars':{'x':2,'y':{'$var':'x'}}}},{'$set':{'name':'x','expr':3}},{'$return':[{'$var':'x'},{'$var':'y'}]}]}
        self.assertEqual(Engine().execute(p).value,[3,1])
    def test_let_ordered(self):
        p={'do':[{'$let':{'vars':{'x':2,'y':{'$add':[{'$var':'x'},1]}},'order':['x','y']}},{'$return':{'$var':'y'}}]}
        self.assertEqual(Engine().execute(p).value,3)
    def test_query_bindings_restore(self):
        p={'do':[{'$let':{'name':'x','expr':99}},{'$let':{'name':'res','expr':{'$map':{'in':[1,2],'item':'x','expr':{'$var':'x'}}}}},{'$return':[{'$var':'x'},{'$var':'res'}]}]}
        self.assertEqual(Engine().execute(p).value,[99,[1,2]])
    def test_object_for_each_pairs_and_index(self):
        p={'do':[{'$forEach':{'in':{'b':2,'a':1},'item':'row','index':'ix','do':[{'$appendEvent':{'row':{'$var':'row'},'hasIndex':{'$exists':{'$var':'ix'}}}}]}},{'$return':{'$events':True}}]}
        self.assertEqual(Engine().execute(p).value,[{'row':{'key':'a','val':1},'hasIndex':False},{'row':{'key':'b','val':2},'hasIndex':False}])
    def test_return_exits_loop(self):
        p={'do':[{'$forEach':{'in':[1,2,3],'item':'x','do':[{'$return':{'$var':'x'}}]}},{'$return':7}]}
        self.assertEqual(Engine().execute(p).value,1)
    def test_variables_with_slash_not_path(self):
        p={'constants':{'some/name':7},'do':[{'$let':{'name':'other/name','expr':4}},{'$return':[{'$var':'other/name'},{'$const':'some/name'}]}]}
        self.assertEqual(Engine().execute(p).value,[4,7])
    def test_function_frames_and_statement_call(self):
        p={'functions':{'f':{'args':{'x':{}},'do':[{'$let':{'name':'local','expr':9}},{'$appendEvent':{'$var':'x'}},{'$return':3}]}},'do':[{'$let':{'name':'local','expr':1}},{'$call':{'function':'f','args':{'x':2}}},{'$return':{'$var':'local'}}]}
        r=Engine().execute(p,Context(matcher=lambda x,p:True));self.assertEqual(r.value,1);self.assertEqual(r.events,[2])
    def test_entry_precedence(self):
        p={'entry':'f','functions':{'f':{'expr':2},'g':{'expr':3}},'expr':1}
        self.assertEqual(Engine().execute(p).value,2);self.assertEqual(Engine().execute(p,entry='g').value,3)
    def test_definition_merge(self):
        p={'constants':{'x':3},'expr':{'$const':'x'}}
        self.assertEqual(Engine().execute(p,definition={'constants':{'x':2,'y':9}}).value,3)
    def test_intrinsic_exact_dispatch_and_gas(self):
        calls=[]
        def intrinsic(payload,gas):calls.append(payload);gas.charge('host',amount=7);return payload['x']+1
        r=Engine(intrinsics={'exact-type':intrinsic}).execute({'expr':{'$intrinsic':{'type':{'blueId':'exact-type'},'x':2}}})
        self.assertEqual((r.value,r.gas_used),(3,11));self.assertEqual(calls,[{'x':2}])
    def test_forged_program_revalidated(self):
        with self.assertRaises(CompileError):Engine().execute(Program({'expr':{'$evil':1}},None,()))

INVALID_COMPILE=[
 {'expr':{'$unknown':1}}, {'do':[{}]}, {'do':[None]}, {'do':[{'$return':1,'x':2}]},
 {'constants':{'value':1},'expr':1}, {'expr':{'type':{'$get':{'object':{},'key':'a'}}}},
 {'expr':{'$literal':{'type':{'$call':{'function':'f'}}}}},
 {'expr':{'$var':'x'}}, {'do':[{'$set':{'name':'x','expr':1}}]},
 {'expr':{'$add':[]}}, {'expr':{'$eq':[1]}},
 {'functions':{'f':{'expr':{'$call':{'function':'f','args':{}}}}}},
 {'functions':{'f':{'args':{'x':{}},'expr':1}},'expr':{'$call':{'function':'f','args':{}}}},
 {'expr':{'$intrinsic':{'type':{'blueId':'missing'},'x':1}}},
 {'do':[{'$forEach':{'in':[],'item':'x','index':'x','do':[]}}]},
 {'do':[{'$let':{'vars':{'x':1},'order':['x','x']}}]},
 {'expr':{'$isKind':{'val':1,'kind':'number'}}},
 {'expr':{'$map':{'in':[],'item':'n','expr':1,'unused':2}}},
]
INVALID_RUNTIME=[
 {'$divide':[1,0]}, {'$divide':[1,2]}, {'$integer':'01'}, {'$integer':'-0'}, {'$integer':'1.5'},
 {'$integer':True}, {'$number':'NaN'}, {'$text':{}}, {'$list':1}, {'$object':[]},
 {'$split':{'text':'a','separator':''}}, {'$split':{'text':'a','separator':',','limit':0}},
 {'$pointerGet':{'object':{},'path':None}}, {'$pointerGet':{'object':{},'path':'/a~9'}},
 {'$pointerSet':{'object':{'a':1},'path':'/a/b','val':2}},
 {'$objectSet':{'object':{},'key':None,'val':1}}, {'$get':{'object':{},'key':MISSING}},
 {'$binding':{'name':None}}, {'$steps':{'step':None}},
 {'$objectFromEntries':[{'key':None,'val':2}]},
 {'$flatMap':{'in':[1],'item':'n','expr':3}}, {'$listGet':{'list':[1],'index':-1}},
]
class BexRejections(unittest.TestCase):pass
for i,p in enumerate(INVALID_COMPILE):
    def test(self,p=p):
        with self.assertRaises(CompileError):Engine().compile(p)
    setattr(BexRejections,f'test_compile_rejection_{i:02}',test)
for i,e in enumerate(INVALID_RUNTIME):
    def test(self,e=e):
        with self.assertRaises(BexError):Engine().execute({'expr':e})
    setattr(BexRejections,f'test_runtime_rejection_{i:02}',test)
