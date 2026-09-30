from pathlib import Path
import os,sys,json,copy
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=Path(os.environ.get('BLUE_SOURCE_WORKSPACE',str(ROOT.parents[2])))
sys.path.insert(0,str(WORKSPACE/'blue-language-python/src'))
from blue_packages import Runtime
from blue_packages.reader import mount,read_package
from blue_language import Language
from vendor import yaml
NAMES=[('blue-agreements','Agreements'),('clause-mutual-activation','MutualActivation'),('clause-immediate-termination','ImmediateTermination'),('agreement-reseller','Reseller')]

def processor(*,sources=False):
 runtime=Runtime.agreements(packages=WORKSPACE/'blue-packages')
 lang=Language(core_contracts=False)
 for n,pre in [('blue-language','Language'),('blue-contracts','Contracts'),('blue-coordination','Coordination')]:runtime.mount(lang,n,pre)
 for n,pre in NAMES:
  root=ROOT/'blue-packages'/n
  if sources:
   cfg=json.loads((root/'blue-package.yaml').read_text())
   for e in cfg['exports']:
    raw=json.loads((root/e['path']).read_text())
    if pre=='Reseller' and e['name']=='Reseller Agreement':
     raw['clauseTypes']=[lang.aliases['MutualActivation/Mutual Activation Clause'],lang.aliases['ImmediateTermination/Immediate Termination Clause']]
    doc=lang.admit_definition(json.dumps(raw),format='json');lang.publish_document(doc);lang.aliases[pre+'/'+e['name']]=doc.blue_id
  else:
   p=read_package(root/'dist/package.bluepkg');runtime.require(p);mount(lang,p,pre,list(p.exports))
 return runtime.contracts(lang)

def source(**params):return {'type':'Reseller/Reseller Agreement','agreementId':'reseller-demo','channels':{side:{'type':'Contracts/External Channel','event':{'channel':'party'+side}} for side in ['A','B']},'parameters':{'resellerDiscountBps':1500,'terminationAllowedParty':'B',**params}}

def op(p,s,operation,request,ts=100):
 side='B' if operation.endswith('B') else 'A'
 return p.process(s,{'channel':'party'+side,'deliveryId':str(ts),'operation':{'type':'Contracts/Operation Request','channel':'party'+side,'operation':operation,'request':request}},ts)

def request(p,s,action='approve',request_id='r1',**kw):
 state=p.read(s,'/activationState')
 return dict(requestId=request_id,action=action,termsId=state['targetId'],round=state['round'],**kw)

def good(o):
 assert o.status=='APPLIED',(o.status,o.diagnostic,o.gas)
 return o.snapshot


def clause_config(p,s):
 values=p.read(s,'/clauses')
 return {k:{f:copy.deepcopy(c[f]) for f in ('type','text','parameters','bindings') if f in c} for k,c in values.items()}
