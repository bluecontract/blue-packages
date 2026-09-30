"""Independent package/editorial invariants; algorithms and existing goldens are not rewritten."""
from pathlib import Path
import ast,hashlib,io,json,re,shutil,zipfile
import pytest
from algorithms import blue as B
from blue_language import Language,MemoryProvider
from blue_repository import Repository,RepositoryError
from package_core import build,read_package,verify_bytes,PackageError,mount,wire,sha
from package_v2 import lock_v2
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def package():return read_package(ROOT/'dist/package.bluepkg')

@pytest.mark.parametrize('name',list(B.CORE)+['Package','ProtocolSpecification'])
def test_definitions_unchanged(name):
    target=ROOT.parent/'verification/reference/blue-language/python/src/registry'/('standard' if name in ('Package','ProtocolSpecification') else '')/(name+'.json')
    assert (ROOT/'types'/f'{name}.json').read_bytes()==target.read_bytes()
    doc=Language(core_contracts=False).admit_definition(target.read_text())
    known=json.loads((ROOT/'types/IDENTITIES.json').read_text())
    expected=B.CORE[name] if name in B.CORE else known['standard'][name]['blueId']
    assert doc.blue_id==expected

@pytest.mark.parametrize('filename',['blue.py','operations.py'])
def test_normative_algorithms_exact(filename):
    source=(ROOT.parent/'verification/reference/blue-language/python/src/algorithms'/filename).read_text().rstrip()
    assert '```python\n'+source+'\n```' in (ROOT/'SPECIFICATION.md').read_text()

def test_normative_document_is_standalone():
    s=(ROOT/'SPECIFICATION.md').read_text()
    prose=re.sub(r'```.*?```','',s,flags=re.S)
    assert not re.search(r'\]\((?!#)',prose)
    assert not re.search(r'(?i)\b(?:codex|handoff|upstream|local candidate|previous discussion|SDK\.md|REGISTRY\.md|ALGORITHMS\.md|CHANGES\.md)\b',prose)
    assert not re.search(r'\{\{[A-Z_]+\}\}',s)
    assert s.count('```')%2==0
    anchors=re.findall(r'<a id="([^"]+)"',s)
    assert len(anchors)==len(set(anchors))
    assert set(re.findall(r'\]\(#([^)]*)\)',s))<=set(anchors)

def test_specification_copy_matches(package):
    assert package.files['spec/language.md']==(ROOT/'SPECIFICATION.md').read_bytes()
    root=package.manifest['semanticPackages'][package.manifest['packageBlueId']]
    asset=root['documentation']['spec/language.md']
    assert asset['sha256']==sha((ROOT/'SPECIFICATION.md').read_bytes())
    assert asset['size']==len((ROOT/'SPECIFICATION.md').read_bytes())

def test_clean_rebuild_is_byte_identical(package,tmp_path):
    path=tmp_path/'package.bluepkg'
    rebuilt=build(ROOT,output=path,revision='blue-language-1.0-2026-09-26',source_url='')
    assert rebuilt.archive==package.archive

def test_corrupt_archive_rejected(package):
    original=zipfile.ZipFile(io.BytesIO(package.archive));stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:
        for i in original.infolist():
            data=original.read(i)
            if i.filename=='README.md':data+=b'\nTampered\n'
            z.writestr(i,data)
    with pytest.raises(PackageError):verify_bytes(stream.getvalue())

@pytest.mark.parametrize('prefix',['language','@repo.blue','company/language'])
def test_mount_is_only_explicit_vocabulary(package,prefix):
    l=Language(core_contracts=False)
    mount(l,package,prefix,['Package'])
    assert prefix+'/Package' in l.aliases
    assert prefix+'/Protocol Specification' not in l.aliases
    assert 'Language/Protocol Specification' not in l.aliases
    d=l.admit_definition(json.dumps({'type':prefix+'/Package'}))
    assert json.loads(d.exact_text)['type']['blueId']==package.repository.aliases['Language/Package']

def test_missing_specification_is_incomplete_not_absent():
    a=Language(core_contracts=False);s=a.create('"Rules"');a.publish_document(s)
    doc=a.create(json.dumps({'type':'Text','value':'x','specification':{'blueId':s.blue_id}}))
    b=Language(core_contracts=False)
    assert b.raw_identify(doc.exact_text,mode='exact')==doc.blue_id
    with pytest.raises(B.Failure) as e:b.create(doc.exact_text,mode='exact')
    assert e.value.category=='ProviderUnavailable'

def test_cycle_proof_and_order():
    c=Language(core_contracts=False).processing_context()
    raw=[{'name':'A','next':{'blueId':'this#1'}},{'name':'B','next':{'blueId':'this#0'}}]
    final=B.finalize_set(raw,c)
    reordered=B.finalize_set([{'name':'B','next':{'blueId':'this#1'}},{'name':'A','next':{'blueId':'this#0'}}],Language(core_contracts=False).processing_context())
    assert final['master']==reordered['master']
    assert final['ids'][0]==reordered['ids'][1]
    proof=B.wire_text({'members':[B.export_tree(n) for n in final['canonical']]})
    for i in final['ids']:
        verified=B.verify_member(i,proof,None,Language(core_contracts=False).processing_context())
        assert verified.id==i

def test_member_body_is_not_owning_proof():
    c=Language(core_contracts=False).processing_context();f=B.finalize_set([{'name':'Loop','self':{'blueId':'this#0'}}],c)
    assert f['master']=='7Ydx3cm8uySLmzNyTcbpM5fufGaLSKnEs9cUcMMxRkeC'
    tid=f['ids'][0];body=B.export_exact(f['bodies'][0],c)
    fresh=Language(MemoryProvider({tid:{'mode':'exact','text':body}}),core_contracts=False)
    with pytest.raises(B.Failure):fresh.verify(tid)

# Build a real dependency chain. X may use Y's types, while X's consumer mounts only X.
def make_project(root,name,imports,definition, *, bootstrap=False):
    root.mkdir(parents=True);(root/'types').mkdir();(root/'inputs').mkdir();(root/'README.md').write_text(name+'\n')
    cfg={'format':2,'name':name,'namespace':name,'version':'1.0.0','readme':'README.md','imports':{},'exports':[{'name':'Value','path':'types/value.blue'}]}
    if bootstrap:cfg['bootstrapLanguage']=True
    else:cfg['language']='language'
    for prefix,p in imports.items():
        target=root/'inputs'/f'{prefix.replace("/","_")}.bluepkg';target.write_bytes(p.archive)
        cfg['imports'][prefix]={'path':str(target.relative_to(root))}
    (root/'types/value.blue').write_text(json.dumps(definition))
    (root/'blue-package.yaml').write_text(json.dumps(cfg));lock_v2(root)
    return root

def test_transitive_content_does_not_import_names(package,tmp_path):
    yroot=make_project(tmp_path/'Y','Y',{'language':package},{'name':'Y Value','type':'Integer'})
    y=build(yroot)
    xroot=make_project(tmp_path/'X','X',{'language':package,'internalY':y},{'name':'X Value','member':{'type':'internalY/Value'}})
    x=build(xroot)
    l=Language(core_contracts=False);mount(l,x,'x',['Value'])
    assert 'internalY/Value' not in l.aliases
    assert 'Y/Value' not in l.aliases
    result=l.create(json.dumps({'type':'x/Value','member':7}))
    assert l.query(result.exact_text,'/member',mode='exact')['value']['decimal']=='7'
    mount(l,y,'xyz',['Value']);assert 'xyz/Value' in l.aliases
    assert y.repository.aliases['Y/Value'] in x.repository.records

def test_other_language_selection_rejects_without_automatic_compatibility(package,tmp_path):
    otherroot=make_project(tmp_path/'OtherLanguage','OtherLanguage',{}, {'name':'Value','type':'Text'},bootstrap=True)
    other=build(otherroot)
    assert other.manifest['packageBlueId']!=package.manifest['packageBlueId']
    p=make_project(tmp_path/'Wrong','Wrong',{'language':package,'foreign':other},{'name':'Value','type':'Text'})
    with pytest.raises(PackageError,match='cross-Language'):build(p)

def test_unused_import_is_not_execution_requirement(package,tmp_path):
    # An ordinary import, even if it supplies definitions, is not executionRequires.
    p=make_project(tmp_path/'Ordinary','Ordinary',{'language':package},{'name':'Value','type':'Text'})
    result=build(p);r=result.manifest['semanticPackages'][result.manifest['packageBlueId']]
    assert r['declaredRequirements']==[]
    assert r['protocol'] is None
