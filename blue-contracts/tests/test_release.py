from pathlib import Path
import io,json,re,hashlib,zipfile
import pytest
from package_core import read_package,verify_bytes,build,mount,Language,PackageError
from release import ROOT,REVISION,checked_package

@pytest.fixture(scope='module')
def package():return checked_package()

def test_specification_in_package_is_exact(package):
    from package_core import config
    path=config(ROOT)['protocol']['rules']
    assert package.files[path]==(ROOT/'SPECIFICATION.md').read_bytes()
    sid=package.manifest['semanticSpecifications'][package.manifest['protocol']]['rules']['blueId']
    assert sid==json.loads((ROOT/'release.json').read_text())['specificationBlueId']

def test_clean_protocol_has_one_rules_document(package):
    p=package.manifest['semanticSpecifications'][package.manifest['protocol']]
    assert 'effectiveRules' not in p and 'schedulingPolicy' not in p
    assert p['language']=={'blueId':'8XGYNufx24r7Dc5bGoeobcGNCn9roLzSfZCQyHBTaTx4'}
    assert not any('source-binding' in x or 'upstream' in x for x in package.files)

def test_included_algorithms_are_exact():
    source=json.loads((ROOT/'docs/sources.json').read_text())
    text=(ROOT/'SPECIFICATION.md').read_text()
    assert len(source['modules']) in (6,18)
    for name,digest in source['modules'].items():
        data=((ROOT/source['overrides'][name]) if name in source.get('overrides',{}) else (ROOT.parent/'verification/reference/blue-contracts/python'/name)).read_bytes()
        assert digest==hashlib.sha256(data).hexdigest() or digest=='sha256:'+hashlib.sha256(data).hexdigest()
        assert '```python\n'+data.decode().rstrip()+'\n```' in text

def test_specification_has_no_hidden_editorial_inputs():
    text=(ROOT/'SPECIFICATION.md').read_text();prose=re.sub(r'```.*?```','',text,flags=re.S)
    assert not re.search(r'(?i)\b(?:codex|handoff|upstream|current-source-binding|HELPER-REFERENCE)\b',prose)
    assert not re.search(r'`(?:ALGORITHMS|DEPENDENCIES|GAS_PROFILE|SPECIFICATION)\.md`',prose)
    assert text.count('```')%2==0
    anchors=re.findall(r'<a id="([^"]+)"',prose)
    assert len(anchors)==len(set(anchors))
    assert set(re.findall(r'\]\(#([^)]*)\)',prose))<=set(anchors)

def test_exact_dependency_selection(package):
    root=package.manifest['semanticPackages'][package.manifest['packageBlueId']]
    assert root['imports']['language']['blueId']=='8XGYNufx24r7Dc5bGoeobcGNCn9roLzSfZCQyHBTaTx4'
    spec=package.manifest['semanticSpecifications'][package.manifest['protocol']]
    if package.manifest['name']=='blue-contracts':
        selected=read_package(ROOT/'inputs/bex.bluepkg')
        assert root['imports']['bex']['blueId']==selected.manifest['packageBlueId']
        assert spec['requires']['bex']['blueId']==selected.manifest['protocol']
    else:
        assert spec['requires']=={} and package.manifest['exports']==[]

@pytest.mark.parametrize('prefix',['x','@repo.blue','company/contracts'])
def test_only_explicit_names_are_mounted(package,prefix):
    lang=Language(core_contracts=False)
    names=[e['name'] for e in package.manifest['exports']]
    if not names:
        # A protocol-only package is valid without inventing executable types.
        assert package.repository.aliases=={}
        return
    mount(lang,package,prefix,[names[0]])
    assert prefix+'/'+names[0] in lang.aliases
    assert 'Language/Package' not in lang.aliases and 'language/Package' not in lang.aliases
    assert not any(n.startswith('bex/') for n in lang.aliases)
    for n in names[1:]:assert prefix+'/'+n not in lang.aliases

def test_native_specification_bindings(package):
    if not package.manifest['exports']:return
    spec=json.loads((ROOT/'release.json').read_text())['specificationBlueId']
    lang=Language(provider=__import__('blue_language').MemoryProvider(package.repository.records),core_contracts=False)
    for e in package.manifest['exports']:
        raw=json.loads(lang.verify(e['blueId']))
        assert raw['specification']=={'blueId':spec}
        assert 'spec' not in raw

def test_no_missing_or_unused_supporting_records(package):
    # read_package has executed root-role checks and strict definition admission.
    assert package.audit['failed']==0
    assert package.audit['passed']==len(package.manifest['exports'])

def test_corruption_rejected_before_use(package):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for name,data in package.files.items():z.writestr(name,data+b'bad' if name=='README.md' else data)
    with pytest.raises(PackageError):verify_bytes(out.getvalue())

def test_rebuild_is_byte_identical(package):
    import subprocess,sys
    subprocess.run([sys.executable,str(ROOT.parent/'tools/build_final_gas.py'),'blue-contracts','--check'],check=True)


def test_explicit_empty_source_url_does_not_inherit_git_remote(monkeypatch):
    import package_v2
    monkeypatch.setattr(package_v2, 'git', lambda *args: 'git@github.com:example/local-checkout.git')
    explicit = package_v2._source_info(ROOT, 'fixed-revision', '')
    inferred = package_v2._source_info(ROOT, 'fixed-revision', None)
    assert explicit == {'revision': 'fixed-revision', 'repository': ''}
    assert inferred == {'revision': 'fixed-revision', 'repository': 'https://github.com/example/local-checkout'}


def prior_publication():
    fixtures=ROOT.parent/'verification/fixtures'
    pin=json.loads((fixtures/(ROOT.name+'-100k.json')).read_text())
    data=(fixtures/(ROOT.name+'-100k.bluepkg')).read_bytes()
    assert 'sha256:'+hashlib.sha256(data).hexdigest()==pin['archiveSha256']
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        manifest=json.loads(archive.read('package.json'))
        assert manifest['packageBlueId']==pin['packageBlueId']
        return archive.read('spec/'+('bex' if ROOT.name=='blue-bex' else 'contracts')+'.md').decode(),pin


def test_preserved_hundred_thousand_publication():
    text,pin=prior_publication()
    assert '100000' in text
    assert pin['packageBlueId']!=json.loads((ROOT/'release.json').read_text())['packageBlueId']


def test_new_default_and_maximum():
    text=(ROOT/'SPECIFICATION.md').read_text()
    assert '10,000,000' in text
    if ROOT.name=='blue-contracts':
        manifest=json.loads((ROOT/'reference/GAS_MANIFEST.json').read_text())
        assert manifest['sharedMaximum']==10_000_000
        prior,_=prior_publication()
        blocks=re.findall(r'```json\n(.*?)\n```',prior,re.S)
        old=next(json.loads(b) for b in blocks if '"sharedMaximum"' in b)
        assert manifest['weights']==old['weights']
        assert 'integer(gas_limit, 0, 10000000)' in text
