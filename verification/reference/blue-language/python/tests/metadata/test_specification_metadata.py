import json
import pytest
from algorithms import blue as B
from blue_language import Language, MemoryProvider
from blue_language.specifications import declared_requirements


def setup():
    l=Language(core_contracts=False)
    a=l.create(json.dumps('Specification A'));l.publish_document(a)
    b=l.create(json.dumps('Specification B'));l.publish_document(b)
    return l,a,b

def admit(l,raw,goal='value',mode='source'):
    d=l.create(json.dumps(raw),goal=goal,mode=mode);l.publish_document(d);return d

def ref(d):return {'blueId':d.blue_id}

@pytest.mark.parametrize('shape',[{}, {'type':'Text'}, {'type':'Integer'}, {'type':'Double'}, {'type':'Boolean'}, {'type':'List'}, {'type':'Dictionary'}])
def test_all_node_kinds(shape):
    l,a,b=setup();d=admit(l,dict(shape,name='Type',description='Doc',specification=ref(a)),goal='definition')
    view=l.resolve(d.exact_text,goal='definition',mode='exact')['view']
    assert view['specification']==ref(a)
    assert 'specification' not in view.get('fields',{})
    assert l.query(d.exact_text,'/specification',mode='exact')['value']==ref(a)

@pytest.mark.parametrize('value',[{'type':'Text','value':'x'},{'type':'Integer','value':5},{'type':'Double','value':1.25},{'type':'Boolean','value':True},{'items':[1,2]},{'x':1}])
def test_metadata_on_completed_values(value):
    l,a,_=setup();d=admit(l,dict(value,specification=ref(a)))
    assert json.loads(d.exact_text)['specification']==ref(a)
    assert l.query(d.exact_text,'','specification',mode='exact')['value']==ref(a)

def test_not_inherited_but_requirements_preserved():
    l,a,b=setup()
    parent=admit(l,{'name':'Parent','specification':ref(a),'x':{'type':'Integer'}},goal='definition')
    child=admit(l,{'name':'Child','type':ref(parent),'specification':ref(b)},goal='definition')
    inst=admit(l,{'type':ref(child),'x':4})
    view=l.resolve(inst.exact_text,mode='exact')['view']
    assert 'specification' not in view and 'specification' not in view['fields']
    assert l.query(inst.exact_text,'/specification',mode='exact')['outcome']=='Absent'
    context=l.processing_context();req=declared_requirements(B.Ref(inst.blue_id),context)
    assert [r['specification'] for r in req]==[b.blue_id,a.blue_id]

def test_not_field_count():
    l,a,_=setup();d=admit(l,{'specification':ref(a),'x':1,'schema':{'maxFields':1}})
    assert l.query(d.exact_text,'','keys',mode='exact')['value']==['x']

def test_different_metadata_changes_id():
    l,a,b=setup()
    x=admit(l,{'type':'Text','value':'x','specification':ref(a)})
    y=admit(l,{'type':'Text','value':'x','specification':ref(b)})
    assert x.blue_id!=y.blue_id

def test_exact_reference_does_not_need_body_for_structural_hash():
    l,a,_=setup();raw={'type':'Text','value':'x','specification':ref(a)}
    d=admit(l,raw)
    fresh=Language(core_contracts=False)
    assert fresh.raw_identify(d.exact_text,mode='exact')==d.blue_id
    with pytest.raises(B.Failure) as err:fresh.create(d.exact_text,mode='exact')
    assert err.value.category=='ProviderUnavailable'

def test_bad_provider_body_rejected():
    l,a,_=setup();l.provider.set_exact(a.blue_id,json.dumps('not Specification A'))
    with pytest.raises(B.Failure) as err:l.create(json.dumps({'type':'Text','value':'x','specification':ref(a)}))
    assert err.value.category=='ProviderBlueIdMismatch'

def test_inline_and_ref_identical():
    l,a,_=setup()
    x=admit(l,{'name':'X','specification':ref(a)},goal='definition')
    y=admit(l,{'name':'X','specification':{'type':'Text','value':'Specification A'}},goal='definition')
    assert x.blue_id==y.blue_id
    assert json.loads(y.exact_text)['specification']==ref(a)

def test_expand_collapse_identity():
    l,a,_=setup();d=admit(l,{'x':1,'specification':ref(a)})
    expanded=l.expand(d.exact_text,['/specification'],mode='exact')
    assert l.create(expanded,mode='exact').blue_id==d.blue_id

def test_short_spec_is_not_metadata():
    l,a,_=setup()
    with pytest.raises(B.Failure):admit(l,{'type':'Text','value':'x','spec':ref(a)})
    d=admit(l,{'spec':ref(a),'x':1})
    assert 'spec' in l.resolve(d.exact_text,mode='exact')['view']['fields']

def test_metadata_cannot_inject_an_alias():
    l,a,_=setup()
    with pytest.raises(B.Failure):admit(l,{'specification':'Contracts/Whatever'},goal='definition')

def test_concrete_field_refinement_cannot_replace_spec():
    l,a,b=setup();t=admit(l,{'x':{'type':'Text','value':'fixed','specification':ref(a)}},goal='definition')
    with pytest.raises(B.Failure) as err:admit(l,{'type':ref(t),'x':{'type':'Text','value':'fixed','specification':ref(b)}})
    assert err.value.category=='FixedValueConflict'

def test_metadata_reference_does_not_invent_protocol_completeness():
    l,a,_=setup();t=admit(l,{'type':'Text','schema':{'required':True}},goal='definition')
    # Language verifies an exact semantic document, not a processor's protocol-role claim.
    d=admit(l,{'specification':ref(t),'x':1})
    assert l.query(d.exact_text,'/specification',mode='exact')['value']==ref(t)


def test_canonical_roundtrip_and_minimize():
    l,a,_=setup();d=admit(l,{'type':'Text','value':'x','specification':ref(a)})
    assert l.create(d.canonical_text,mode='canonical').blue_id==d.blue_id
    m=l.minimize(d.exact_text,mode='exact')
    md=l.create(m)
    assert l.resolve(md.exact_text,mode='exact')['view']['specification']==ref(a)

def test_metadata_not_removed_as_duplicate_business_child():
    l,a,_=setup();t=admit(l,{'name':'T','specification':ref(a),'x':1},goal='definition')
    d=admit(l,{'type':ref(t),'specification':ref(a),'x':1})
    assert '/x' in d.removed_fields
    assert json.loads(d.exact_text)['specification']==ref(a)
