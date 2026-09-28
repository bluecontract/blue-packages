"""End-to-end commands over unmodified, hash-checked Java tutorial documents."""
from blue_runtime import Stack
from blue_repository.runtime import RepositoryCatalogue


def perform(s,root,operation,request,*,channel='ownerChannel',timestamp=10,gas=100000):
    from .runner import require
    entry=s.call(root,operation,request,channel=channel,timestamp=timestamp)
    s.close_before(entry.timestamp+1);result=s.drain(root,gas_limit=gas)
    applied=[step for step in result.steps if step.entry_blue_id==entry.blue_id and step.status=='APPLIED']
    require(len(applied)==1,'expected exactly one applied original input: '+repr(result))
    return entry,applied[0]


def factory():
    from .runner import doc,require
    s=Stack(catalogue=RepositoryCatalogue());s.admit_graph({'factory':doc('18','factory-host.yaml')})
    entry,step=perform(s,'factory','createOrder01',doc('18','factory-input.yaml'),channel='merchantChannel')
    require(s.state('factory')['initializedOrderCount']==1,'parent did not observe initialization')
    require('tutorial-order' in s.host.roots,'child has no independent public admission')
    require(s.state('tutorial-order')['initializedState']=='initialized','child not initialized')
    perform(s,'tutorial-order','markReady',{},timestamp=30)
    require(s.state('tutorial-order')['status']=='ready','independent child route failed')
    require(s.state('factory','tutorial-order')['status']=='draft','source publication leaked into parent projection')
    require(s.host.replay_saved(step.invocation_identity)['verified'],'factory replay changed after source advancement')
    return {'independentManagedChildAdmission':True,'parentObservedInitializations':1,
            'childStatus':'ready','parentPrivateChildStatus':'draft','gas':step.gas_used,'originalEntry':entry.blue_id}


def historical_attach():
    from .runner import doc,require
    s=Stack(catalogue=RepositoryCatalogue());s.admit_graph({'child':doc('10','01_child_counter.yaml'),'parent':doc('10','02_host.yaml')})
    perform(s,'child','increment',{'amount':3})
    head=s.host.roots['child'].ids['child']
    entry,step=perform(s,'parent','attachChild',{'child':{'blueId':head}},timestamp=20)
    require(s.state('parent')['observedCounter']==3,'retained event did not reach parent')
    catchup=s.host.roots['parent'].catchups['parent/child']
    require(catchup['appliedEpochs']==1,'historical interval not imported')
    require(s.drain('parent').steps==(),'catch-up repeated')
    require(s.host.replay_saved(step.invocation_identity)['verified'],'retained original replay mismatch')
    return {'parentObserved':3,'sourceCounter':s.state('child')['counter'],'retainedEpochs':1,
            'mode':catchup['mode'],'originalEntry':entry.blue_id,'gas':step.gas_used}


def shared_occurrences():
    from .runner import doc,require
    s=Stack(catalogue=RepositoryCatalogue());s.admit_graph({'child':doc('10','01_child_counter.yaml'),'host':doc('11','01_two_slot_host.yaml')})
    perform(s,'child','increment',{'amount':3})
    head=s.host.roots['child'].ids['child']
    perform(s,'host','attachFirst',{'child':{'blueId':head}},timestamp=20)
    perform(s,'host','attachSecond',{'child':{'blueId':head}},timestamp=30)
    snap=s.host.load_root('host');occ=snap.occurrences
    require(len(occ)==2 and len({o.identity for o in occ})==2,'equal child values collapsed occurrences')
    require(len({o.child_view for o in occ})==1,'one source became two logical documents')
    perform(s,'child','increment',{'amount':2},timestamp=40)
    run=s.drain('host');require(s.state('host','child')['counter']==5,'private source applied twice or was skipped')
    return {'occurrences':len(occ),'uniqueOccurrenceIds':len({o.identity for o in occ}),'sharedChildCounter':5,
            'generations':[o.activation_generation for o in occ]}


def collection_lifecycle():
    from .runner import doc,require
    s=Stack(catalogue=RepositoryCatalogue());s.admit_graph({'host':doc('13','02_order_host.yaml')})
    perform(s,'host','addOrder',{'orderKey':'order/01','order':doc('13','01_order.yaml')})
    state=s.host.roots['host'];path='/orders/order~101';child=state.edges['host'][path];head=state.ids[child]
    perform(s,'host','removeOrder',{'orderKey':'order/01'},timestamp=20)
    require(not s.host.roots['host'].edges['host'],'removed collection occurrence remains live')
    require(child in s.host.roots,'removing occurrence deleted independent source')
    perform(s,'host','addOrder',{'orderKey':'order/01','order':{'blueId':head}},timestamp=30)
    generation=s.host.roots['host'].generations['host'][path]
    require(generation==1,'remove/readd reset occurrence generation')
    return {'escapedPath':path,'generationAfterReadd':generation,'independentSourcePreserved':True}


def historical_cold_chain():
    from .runner import doc,require
    s=Stack(catalogue=RepositoryCatalogue());s.admit_graph({'logger':doc('16','01_temperature_logger.yaml'),'shipment':doc('16','02_vaccine_shipment.yaml')})
    perform(s,'logger','reportTemperature',{'temperatureC':12.0})
    head=s.host.roots['logger'].ids['logger']
    perform(s,'shipment','attachLogger',{'logger':{'blueId':head}},timestamp=20)
    state=s.state('shipment')
    require(state['status']=='quarantined' and state['releaseBlocked'] is True and state['excursionCount']==1,'retained excursion did not quarantine shipment')
    return {k:state[k] for k in ('status','releaseBlocked','excursionCount')}

CASES=[('10.historical-attach','Original attachChild after one committed source revision; authenticated local history',historical_attach),
       ('11.two-occurrences','Original two-slot host: distinct occurrences, one shared managed source',shared_occurrences),
       ('13.collection-lifecycle','Original addOrder/removeOrder with escaped stable key and generation tombstone',collection_lifecycle),
       ('16.historical-cold-chain','Original attachLogger after a retained temperature excursion',historical_cold_chain),
       ('18.managed-factory','Original factory: independent admission, initialization, routing, isolation and replay',factory)]
