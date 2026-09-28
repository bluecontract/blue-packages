import unittest
from algorithms import blue as L
from blue_runtime.syntax_cache import syntax_scope, SyntaxCache, _PLAIN, _FINAL


class SyntaxMemo(unittest.TestCase):
    def test_valid_invalid_cyclic_subclasses_and_bounded_retention(self):
        cache=SyntaxCache(2)
        values=[*L.CORE.values(),'',None,True,{},'0invalid','1'*32,'1'*33]
        values += [next(iter(L.CORE.values()))+suffix for suffix in ['#0','#01','#1','##1','#-1','#'+('1'*200)]]
        class Text(str):pass
        values.append(Text(next(iter(L.CORE.values()))))
        for value in values:
            for operation,reference in [(L.plain_id,_PLAIN),(L.final_id,_FINAL)]:
                def run(enabled):
                    with syntax_scope(cache,enabled=enabled):
                        try:return 'value',operation(value)
                        except L.Failure as e:return 'failure',e.as_dict()
                self.assertEqual(run(True),run(False))
                self.assertLessEqual(len(cache.rows),2)
        identity=next(iter(L.CORE.values()))
        with syntax_scope(cache):
            L.final_id(identity);L.final_id(identity)
        self.assertGreater(cache.hits,0)

    def test_syntax_hit_does_not_supply_missing_content(self):
        node=L.normalize({'unknown':'body'},L.Context());identity=L.identity(node)
        with syntax_scope():
            L.final_id(identity);L.final_id(identity)
            with self.assertRaises(L.Failure) as error:L.open_exact(L.Ref(identity),L.Context())
            self.assertEqual(error.exception.category,'ProviderUnavailable')


if __name__=='__main__':unittest.main()
