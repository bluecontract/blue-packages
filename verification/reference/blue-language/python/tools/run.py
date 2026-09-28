#!/usr/bin/env python3
"""Run the portable fixture protocol; the adapter contains no Language merging."""
from __future__ import annotations
import argparse,sys,json,hashlib,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from algorithms import blue as B

def registry():
    r=Path(__file__).resolve().parents[1]/'src/registry'
    return {p.stem:json.loads(p.read_text()) for p in r.glob('*.json') if p.stem in B.CORE}

def make_context(case):
    e=case.get('environment',{})
    lim=B.Limits(**e.get('limits',{}))
    c=B.initialize(registry(),e.get('provider',{}),e.get('aliases',{}))
    c.directive_aliases=dict(e.get('directiveAliases',{}))
    for d in e.get('definitions',[]):
        n=B.input_node(d['input'],c)
        if 'blueId' in d: B.require(B.identity(n)==d['blueId'],'FixtureEnvironmentError','definition identity')
        c.remember(n)
        if 'alias' in d:
            B.require(d['alias'] not in B.CORE,'FixtureEnvironmentError','core alias')
            c.aliases[d['alias']]=B.identity(n)
    c.limits=lim;c.work=0;c.demands=[]
    return c

def request(req,c):
    op=req['operation']
    def input_(key='input'): return B.input_node(req[key],c)
    if op=='preprocess':
        i=req['input'];s=B.preprocess(B.parse(i['text'],i.get('format','json'),c.limits),c)
        # Preprocessing may still contain Source controls; do not identify them as data.
        def show(x):
            if isinstance(x,(B.Node,B.Ref,B.Local)): return B.export_tree(x)
            if isinstance(x,list): return [show(a) for a in x]
            if isinstance(x,dict): return {k:show(v) for k,v in x.items()}
            return x
        return {'outcome':'Established','text':B.wire_text(show(s))}
    if op in ('identify','canonicalize'):
        n=input_();return {'outcome':'Established','blueId':B.identity(n),'text':B.export_exact(n,c)}
    if op=='validate':
        n=input_();B.certify(n,c,req.get('goal','value'))
        return {'outcome':'Established','valid':True,'blueId':B.identity(n)}
    if op in ('resolve','resolveLimited','resolveComplete'):
        n=input_();results=[]
        if op=='resolveComplete': B.certify(n,c,req.get('goal','value'))
        for q in req['queries']:
            results.append(B.outcome(lambda q=q:B.observe(n,q.get('path',''),q['query'],c)))
        return {'outcome':'Established','observations':results}
    if op=='subtype':
        a=input_('candidate');b=input_('parent');c.remember(a);c.remember(b)
        return {'outcome':'Established','subtype':B.check_subtype(B.identity(a),B.identity(b),c)}
    if op=='preserves':
        a=input_('candidate');b=input_('parent')
        B.certify(a,c,'definition');B.certify(b,c,'definition')
        return {'outcome':'Established','preserves':B.preserves_heads(B.head(B.recipe(a),c),B.head(B.recipe(b),c),c,check_type=False)}
    if op=='schemaRefine':
        a=input_('parent');b=input_('candidate')
        v=B.refine_schema(B.read_schema(a,c),B.read_schema(b,c),c)
        n=B.merge_schema_exact(a,b,c)
        return {'outcome':'Established','constraints':B.describe_constraints(v),'blueId':B.identity(n),'text':B.export_exact(n,c)}
    if op=='schemaConjoin':
        a=input_('left');b=input_('right')
        v=B.conjoin_schema(B.read_schema(a,c),B.read_schema(b,c))
        return {'outcome':'Established','constraints':B.describe_constraints(v)}
    if op=='fold':
        p=B.plain_id(req['prefix'])
        for item in req['suffix']:
            p=B.append_id(p,B.identity(B.input_node(item,c)))
        return {'outcome':'Established','blueId':p}
    if op=='verify':
        rid=B.final_id(req['blueId']);b=B.open_exact(B.Ref(rid),c)
        return {'outcome':'Established','blueId':rid,'bodyBlueId':B.identity(b)}
    if op in ('expand','collapse'):
        n=input_();out=(B.expand if op=='expand' else B.collapse)(n,req['paths'],c)
        return {'outcome':'Established','blueId':B.identity(out),'text':B.wire_text(B.export_tree(out))}
    if op=='lookupExact':
        n=input_();a=B.exact_at(n,B.path_parts(req['path']),c)
        if a is B.ABSENT: return {'outcome':'Absent'}
        if isinstance(a,(B.Node,B.Ref)): return {'outcome':'Established','blueId':B.identity(a)}
        if isinstance(a,tuple): return {'outcome':'Established','length':len(a)}
        return {'outcome':'Established','value':B.literal_output(a)}
    if op=='minimize':
        n=input_();text=B.minimize(n,c,req.get('goal','value'))
        again=B.prepare_source(B.parse(text,limits=c.limits),c)
        return {'outcome':'Established','text':text,'sameView':B.same_view(n,again,c),'blueId':B.identity(again),'originalBlueId':B.identity(n)}
    if op=='finalize':
        ns=[B.parse(d['text'],d.get('format','json'),c.limits) for d in req['documents']]
        z=B.finalize_set(ns,c)
        return {'outcome':'Established','master':z['master'],'blueIds':z['ids'],
                'proofText':B.wire_text({'members':[B.export_tree(n) for n in z['canonical']]}),
                'bodyTexts':[B.export_exact(n,c) for n in z['bodies']]}
    if op=='verifyMember':
        h=B.verify_member(req['blueId'],req['proof'],req.get('body'),c)
        return {'outcome':'Established','blueId':h.id,'bodyBlueId':B.identity(h.body)}
    if op=='roundtrip':
        n=input_();text=B.export_exact(n,c)
        m=B.normalize(B.parse(text,limits=c.limits),c)
        return {'outcome':'Established','blueId':B.identity(n),'reloadedBlueId':B.identity(m),'equal':B.identity(n)==B.identity(m)}
    raise B.Failure('UnknownFixtureOperation',op)

REQUEST_FIELDS = {
 'preprocess': ({'input'},set()),
 'identify': ({'input'},set()), 'canonicalize': ({'input'},set()),
 'validate': ({'input'},{'goal'}),
 'resolve': ({'input','queries'},set()),
 'resolveLimited': ({'input','queries'},set()),
 'resolveComplete': ({'input','queries'},{'goal'}),
 'subtype': ({'candidate','parent'},set()), 'preserves': ({'candidate','parent'},set()),
 'schemaRefine': ({'candidate','parent'},set()), 'schemaConjoin': ({'left','right'},set()),
 'fold': ({'prefix','suffix'},set()), 'verify': ({'blueId'},set()),
 'expand': ({'input','paths'},set()), 'collapse': ({'input','paths'},set()),
 'lookupExact': ({'input','path'},set()), 'minimize': ({'input'},{'goal'}),
 'finalize': ({'documents'},set()), 'verifyMember': ({'blueId','proof'},{'body'}),
 'roundtrip': ({'input'},set())
}

class FixtureError(Exception): pass

def strict_record(value, required, optional, label):
    if not isinstance(value,dict) or not required<=set(value) or set(value)-(required|optional):
        raise FixtureError(label+': invalid fields')

def check_input(value):
    strict_record(value,{'text'},{'mode','format'},'input')
    if not isinstance(value['text'],str) or value.get('mode','source') not in ('source','exact','direct') or value.get('format','json') not in ('json','yaml'):
        raise FixtureError('input: invalid role, format or text')

def check_fixture(case):
    strict_record(case,{'id','request','expected'},{'description','environment'},'case')
    if not isinstance(case['id'],str) or not case['id']: raise FixtureError('case id')
    r=case['request'];op=r.get('operation') if isinstance(r,dict) else None
    if op not in REQUEST_FIELDS: raise FixtureError('unknown fixture operation')
    required,optional=REQUEST_FIELDS[op]
    strict_record(r,required|{'operation'},optional,'request')
    for key in ('input','candidate','parent','left','right'):
        if key in r: check_input(r[key])
    for key in ('suffix','documents'):
        if key in r:
            if not isinstance(r[key],list): raise FixtureError(key+' must be a list')
            for a in r[key]: check_input(a)
    if 'goal' in r and r['goal'] not in ('definition','value'): raise FixtureError('goal')
    if 'queries' in r:
        if not isinstance(r['queries'],list): raise FixtureError('queries')
        for q in r['queries']:
            strict_record(q,{'query'},{'path'},'query')
            if q['query'] not in ('exactId','kind','type','value','constraints','keys','length','present','name','description'): raise FixtureError('query name')
            if not isinstance(q.get('path',''),str): raise FixtureError('query path')
    if 'paths' in r and (not isinstance(r['paths'],list) or not all(isinstance(p,str) for p in r['paths'])): raise FixtureError('paths')
    if 'path' in r and not isinstance(r['path'],str): raise FixtureError('path')
    if 'proof' in r and not isinstance(r['proof'],str): raise FixtureError('proof must be original JSON text')
    if 'body' in r and not isinstance(r['body'],str): raise FixtureError('body must be original exact JSON text')
    e=case.get('environment',{})
    strict_record(e,set(),{'limits','provider','aliases','definitions','directiveAliases'},'environment')
    for d in e.get('definitions',[]):
        strict_record(d,{'input'},{'alias','blueId'},'definition');check_input(d['input'])
    for v in e.get('provider',{}).values():
        if not isinstance(v,dict): raise FixtureError('provider response envelope')
        if 'outcome' in v:
            strict_record(v,{'outcome'},set(),'provider outcome')
            if v['outcome'] not in ('NotFound','Unavailable','InvalidEvidence'): raise FixtureError('provider outcome')
        elif 'proof' in v:
            strict_record(v,{'proof'},{'body'},'member response')
            if not isinstance(v['proof'],str) or 'body' in v and not isinstance(v['body'],str): raise FixtureError('proof/body text')
        else:
            strict_record(v,{'text'},{'format','mode','environment'},'provider text response')
    if not isinstance(case['expected'],dict) or case['expected'].get('outcome') not in ('Established','Absent','Incomplete','Invalid'):
        raise FixtureError('expected outcome')
    # These are result fields, not a catch-all implementation-specific expectation.
    allowed={'outcome','category','blueId','bodyBlueId','text','valid','observations','subtype','preserves','constraints','length','value','sameView','originalBlueId','master','blueIds','proofText','bodyTexts','reloadedBlueId','equal'}
    if set(case['expected'])-allowed: raise FixtureError('unknown expected field')

def execute(case):
    check_fixture(case)
    try:
        c=make_context(case)
    except (B.Failure,TypeError,ValueError) as e:
        raise FixtureError('environment setup: '+str(e)) from e
    result=B.outcome(lambda:request(case['request'],c))
    result['caseId']=case['id']
    return result

def match(actual,expected,path=''):
    if isinstance(expected,dict):
        if not isinstance(actual,dict): return [path+': object expected']
        out=[]
        for k,v in expected.items():
            if k not in actual: out.append(path+'/'+k+': absent')
            else: out.extend(match(actual[k],v,path+'/'+k))
        return out
    if isinstance(expected,list):
        if not isinstance(actual,list) or len(actual)!=len(expected): return [path+': list length/type']
        return [msg for i,(a,b) in enumerate(zip(actual,expected)) for msg in match(a,b,path+'/'+str(i))]
    return [] if type(actual)==type(expected) and actual==expected else [path+': '+repr(actual)+' != '+repr(expected)]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('fixtures',type=Path);ap.add_argument('--output',type=Path);args=ap.parse_args()
    cases=[json.loads(line) for line in args.fixtures.read_text().splitlines() if line.strip()]
    results=[];errors=[]
    ids=[x['id'] for x in cases]
    if len(ids)!=len(set(ids)): raise FixtureError('duplicate fixture ID')
    for case in cases:
        result=execute(case);results.append(result)
        for msg in match(result,case['expected']): errors.append({'caseId':case['id'],'message':msg})
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in results))
    print(json.dumps({'cases':len(cases),'passed':len(cases)-len({e['caseId'] for e in errors}),'failures':errors},ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
