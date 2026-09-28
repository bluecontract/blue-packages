"""Run tutorial slices; PASS is never a claim that the complete Java chapter passed."""
from __future__ import annotations
import argparse,copy,hashlib,json,time,traceback
from pathlib import Path
from vendor import yaml
from blue_language import Language
from blue_repository.runtime import RepositoryCatalogue
from blue_contracts.legacy_processor import Processor
from blue_runtime import Stack
from blue_bex import Gas

FIXTURES=Path(__file__).resolve().parent/'fixtures'
MANIFEST=json.loads((FIXTURES/'MANIFEST.json').read_text())

def source(chapter,filename):
    candidates=list((FIXTURES/'examples').glob(chapter+'*/'+filename))
    if len(candidates)!=1:raise ValueError('ambiguous tutorial fixture')
    p=candidates[0];rel=p.relative_to(FIXTURES).as_posix()
    row=next(x for x in MANIFEST['examples'] if x['file']==rel)
    if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('tutorial source hash mismatch: '+rel)
    return p.read_text()

def doc(chapter,filename):return yaml.safe_load(source(chapter,filename))
def require(value,message):
    if not value:raise AssertionError(message)

def _language_identity():
    l=Language();a=l.identify(source('01','03_scalar_compact.yaml'),format='yaml');b=l.identify(source('01','04_scalar_explicit.yaml'),format='yaml')
    require(a==b,'compact/explicit scalar identity mismatch');return {'blueId':a}

def _references():
    l=Language();child=l.create(source('01','01_xyz.yaml'),format='yaml');l.publish_document(child)
    a=l.identify(source('02','01_parent_inline.yaml'),format='yaml')
    b=l.identify(source('02','02_parent_reference.template.yaml').replace('<XYZ_CONTENT_BLUE_ID>',child.blue_id),format='yaml')
    require(a==b,'inline/reference identity mismatch');return {'parent':a,'child':child.blue_id}

def _types():
    l=Language();point=l.admit_definition(source('03','01_point_type.yaml'),format='yaml');l.publish_document(point)
    colored=l.admit_definition(source('03','02_colored_point_type.template.yaml').replace('<POINT_TYPE_BLUE_ID>',point.blue_id),format='yaml');l.publish_document(colored)
    p=l.create(source('03','03_valid_point.template.yaml').replace('<POINT_TYPE_BLUE_ID>',point.blue_id),format='yaml')
    c=l.create(source('03','04_valid_colored_point.template.yaml').replace('<COLORED_POINT_TYPE_BLUE_ID>',colored.blue_id),format='yaml')
    require(p.blue_id!=c.blue_id,'distinct instances must differ');return {'point':p.blue_id,'coloredPoint':c.blue_id,'types':[point.blue_id,colored.blue_id]}

def _lists():
    l=Language();a=l.identify(source('04','01_list_compact.yaml'),format='yaml');b=l.identify(source('04','02_list_explicit.yaml'),format='yaml')
    require(a==b,'list spelling mismatch');empty=l.create(source('04','04_empty_list.yaml'),format='yaml')
    require(empty.blue_id!=l.identify('{}'),'empty list is not absence');return {'list':a,'empty':empty.blue_id}

def _counter():
    s=Stack(catalogue=RepositoryCatalogue());s.admit_graph({'counter':doc('06','counter.yaml')})
    a=s.call('counter','increment',{'amount':3},channel='aliceChannel',timestamp=10)
    b=s.call('counter','decrement',{'amount':1},channel='bobChannel',timestamp=11)
    s.close_before(20);r=s.drain('counter');state=s.state('counter')
    require(len(r.steps)==2 and all(x.status=='APPLIED' for x in r.steps),'counter operations failed')
    require(state['counter']==2,'counter should be 2')
    entries=state['contracts']['checkpoint']['entries']
    require(entries['aliceChannel']['subject']['blueId']==a.blue_id,'original Alice entry checkpoint')
    require(entries['bobChannel']['subject']['blueId']==b.blue_id,'original Bob entry checkpoint')
    return {'counter':state['counter'],'checkpointSubjects':[a.blue_id,b.blue_id],'steps':[x.status for x in r.steps],
            'epochs':s.host.roots['counter'].epochs,'runtimeProfile':s.catalogue.registry.profile_identity}

def _bare():
    s=Stack(catalogue=RepositoryCatalogue());s.admit_graph({'bare':doc('05','01_bare_document.yaml')})
    state=s.state('bare');require(s.catalogue.role(state['contracts']['initialized'])=='initialized','initialization marker missing')
    return {'initialized':True,'blueId':s.host.roots['bare'].ids['bare']}

def _order():
    s=Stack(catalogue=RepositoryCatalogue());s.admit_graph({'order':doc('13','01_order.yaml')})
    s.call('order','markReady',{},channel='ownerChannel');s.close_before(20);r=s.drain('order')
    require(r.steps[0].status=='APPLIED' and s.state('order')['status']=='ready','markReady failed')
    return {'status':'ready','publishedEvents':len(s.host.published)}

def _temperature():
    s=Stack(catalogue=RepositoryCatalogue());s.admit_graph({'logger':doc('16','01_temperature_logger.yaml')})
    s.call('logger','reportTemperature',{'temperatureC':12.0},channel='ownerChannel');s.close_before(20);r=s.drain('logger')
    require(r.steps[0].status=='APPLIED','temperature operation failed');state=s.state('logger')
    require(state['state']=='excursion' and state['temperatureC']==12.0,'temperature state mismatch')
    return {'temperatureC':state['temperatureC'],'state':state['state']}

def _rooted():
    s=Stack(catalogue=RepositoryCatalogue());s.admit_graph({'parent':doc('10','02_host.yaml'),'child':doc('10','01_child_counter.yaml')},
         {'parent':{'/child':'child'}},public_roots=['parent','child'])
    s.call('child','increment',{'amount':3},channel='ownerChannel');s.close_before(20);r=s.drain('parent')
    require(r.steps[0].status=='APPLIED','rooted operation failed')
    require(s.state('parent')['observedCounter']==3,'parent did not observe child')
    require(s.state('child')['counter']==0,'parent advanced independent public source')
    require(s.state('parent','child')['counter']==3,'private child projection missing')
    r2=s.drain('child');require(r2.steps[0].status=='APPLIED' and s.state('child')['counter']==3,'independent source failed')
    return {'parentObserved':3,'sourceBeforeIndependentDrain':0,'sourceAfterIndependentDrain':3}

def _cold_chain():
    s=Stack(catalogue=RepositoryCatalogue());s.admit_graph({'shipment':doc('16','02_vaccine_shipment.yaml'),'logger':doc('16','01_temperature_logger.yaml')},
         {'shipment':{'/logger':'logger'}},public_roots=['shipment','logger'])
    s.call('logger','reportTemperature',{'temperatureC':12.0},channel='ownerChannel');s.close_before(20);r=s.drain('shipment')
    require(r.steps[0].status=='APPLIED','cold-chain closure failed');state=s.state('shipment')
    require(state['status']=='quarantined' and state['releaseBlocked'] is True and state['excursionCount']==1,'quarantine mismatch')
    return {k:state[k] for k in ('status','releaseBlocked','excursionCount')}

def _factory_inline():
    cat=RepositoryCatalogue();processor=Processor(cat)
    _,host=cat.admit(doc('18','factory-host.yaml'))
    started=processor.process(host,{},initialize_only=True)
    # This explicitly tests local Contracts execution, not MyOS independent-child admission.
    event={'message':cat.typed('Coordination/Operation Request',operation='createOrder01',channel='merchantChannel',request=doc('18','factory-input.yaml'))}
    result=processor.process(started.document,event,channels=('merchantChannel',),operation='createOrder01',gas=Gas(200000))
    order=result.document['orders']['order-01']
    require(order['initializedState']=='initialized','new inline scope was not initialized in the same process')
    require(result.document['initializedOrderCount']==1,'host did not observe inline initialization')
    require(result.document['lastInitializedOrder']=='tutorial-order','wrong child document pointer')
    return {'initializedOrderCount':1,'initializedState':order['initializedState'],'gas':result.gas_used,
            'independentManagedChildAdmission':False}

CASES=[
 ('01.scalar-identity','Language spelling equivalence',_language_identity),
 ('02.reference-identity','Language materialization equivalence',_references),
 ('03.typed-values','Type definitions and valid typed instances',_types),
 ('04.list-identity','Ordinary list spelling and empty-list identity',_lists),
 ('05.bare-initialization','Managed initial admission only',_bare),
 ('06.counter','Original counter operations, timeline order and checkpoints',_counter),
 ('10.rooted-prebound','Static prebinding adaptation; NOT historical attachChild',_rooted),
 ('13.order-operation','Original Order.markReady operation; NOT collection lifecycle',_order),
 ('16.temperature-operation','Original logger operation',_temperature),
 ('16.cold-chain-prebound','Static prebinding adaptation; NOT historical attachLogger',_cold_chain),
 ('18.factory-inline','Original factory request in local Contracts scope; NOT independent child admission',_factory_inline),
]
from .managed_cases import CASES as MANAGED_CASES
CASES += MANAGED_CASES
DEFERRED=[
 {'chapter':'dynamic cycles','capability':'Admission into a newly formed cyclic ownership cohort; existing explicitly admitted cycles remain supported'},
 {'chapter':'history','capability':'Remote production transition evidence and incremental pending-head import; local committed histories are supported'},
 {'chapter':'contracts','capability':'Nearest-valid type generalization and the complete upstream local-fatal envelope'},
 {'chapter':'all','capability':'Exact pinned Java differential execution and gas parity'},
]


def run(selected=None):
    rows=[]
    for ident,scope,fn in CASES:
        if selected and ident not in selected:continue
        started=time.monotonic()
        try:observations=fn();row={'id':ident,'status':'PASS','scope':scope,'observations':observations}
        except Exception as error:row={'id':ident,'status':'FAIL','scope':scope,'error':str(error),'traceback':traceback.format_exc()}
        row['elapsedSeconds']=time.monotonic()-started;rows.append(row)
    return {'format':'blue-python-tutorial-slices/1','inputMyOSCommit':MANIFEST['myosCommit'],
            'passed':sum(x['status']=='PASS' for x in rows),'failed':sum(x['status']!='PASS' for x in rows),
            'cases':rows,'deferredNotCountedAsPassed':DEFERRED}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--case',action='append')
    args=parser.parse_args();result=run(args.case);text=json.dumps(result,indent=2)+'\n'
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
    print(text);return int(result['failed']>0)
if __name__=='__main__':raise SystemExit(main())
