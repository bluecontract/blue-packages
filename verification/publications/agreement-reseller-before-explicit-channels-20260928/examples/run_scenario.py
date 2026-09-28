"""Signed-Timeline negotiation -> activation -> unilateral termination.
Run with the sibling blue-python installed, or PYTHONPATH=../blue-python/src.
"""
import argparse,json
from pathlib import Path
from session import Session


def run(output=None):
    with Session() as s:
        print('Creating reseller agreement without an immediate-termination right',flush=True)
        h=s.add(s.source(None));a=s.managed('MutualActivation/Mutual Activation Clause')
        s.wait_phase(h,'NEGOTIATING')
        assert 'immediateTermination' not in s.read(a,'/state/settled/clauses')
        assert not s.read(h,'/clauses')
        print('Negotiating 15% -> 20% discount and adding Supplier-only termination',flush=True)
        proposal=s.action(a,'A','proposeChange','offer-1',message='Increase the reseller discount to 20% and add immediate termination for Supplier only.',changes=[
            {'op':'set','path':'/commercial/resellerDiscountBps','val':2000},
            {'op':'set','path':'/clauses/immediateTermination','val':s.typ('ImmediateTermination/Immediate Termination Terms',allowedParty='A')}])
        proposed_id=s.value_id(a,'/state/proposal');terms_id=s.read(a,'/state/targetId')
        assert s.read(a,'/state/settled/commercial/resellerDiscountBps')==1500
        assert not s.read(h,'/clauses')
        s.action(a,'B','acceptChange','accept-1',proposalId=proposed_id)
        s.wait_value(h,'/terms/commercial/resellerDiscountBps',2000)
        assert any(row['content'].get('result')=='ACCEPTED' and
                   row['content'].get('inResponseTo',{}).get('blueId')==proposed_id
                   for row in s.events_of('MutualActivation/Change Decision'))
        assert s.read(h,'/phase')=='NEGOTIATING'
        assert s.read(a,'/state/signals')=={'A':'NONE','B':'NONE'}
        s.action(a,'A','ready','ready-a');s.action(a,'B','ready','ready-b')
        assert s.read(h,'/phase')=='NEGOTIATING'
        assert not s.read(h,'/clauses')
        print('Both principals approve the exact settled revision',flush=True)
        s.action(a,'A','approve','approve-a');s.action(a,'B','approve','approve-b')
        s.wait_phase(h,'ACTIVE');t=s.managed('ImmediateTermination/Immediate Termination Clause')
        assert s.read(t,'/allowedParty')=='A'
        assert s.read(t,'/termsId')==terms_id
        assert s.read(h,'/acceptedRevision/termsId')==terms_id
        accepted=s.read(h,'/acceptedRevision');terms=s.read(h,'/terms')
        print('Reseller termination is rejected; Supplier then acts alone',flush=True)
        s.invoke(t,'B','terminateB',{'requestId':'not-permitted','termsId':terms_id})
        assert s.read(t,'/state/phase')=='OPEN'
        assert s.read(h,'/phase')=='ACTIVE'
        request={'requestId':'supplier-termination-1','termsId':terms_id,'reason':'Supplier exercises the agreed immediate-termination right.'}
        s.invoke(t,'A','terminateA',request);s.wait_phase(h,'TERMINATED')
        assert s.read(h,'/termination/party')=='A'
        assert s.read(h,'/acceptedRevision')==accepted
        assert s.read(h,'/terms')==terms
        assert len(s.events_of('ImmediateTermination/Agreement Terminated'))==1
        print('Retrying the same request does not terminate twice',flush=True)
        record=s.read(h,'/termination')
        s.invoke(t,'A','terminateA',request)
        assert s.read(h,'/termination')==record
        assert len(s.events_of('ImmediateTermination/Agreement Terminated'))==1
        result={'status':'PASS','finalPhase':s.read(h,'/phase'),'allowedParty':'A',
            'discountBps':s.read(h,'/terms/commercial/resellerDiscountBps'),
            'termination':record,'acceptedRevision':accepted,'trace':s.trace,
            'agreementEvents':[r['content'] for r in s.events_of('Agreements/Agreement Activated')+s.events_of('ImmediateTermination/Agreement Terminated')],
            'history':s.engine.history(h)['items']}
        if output:Path(output).write_text(json.dumps(result,indent=2,default=str)+'\n')
        print(json.dumps({k:result[k] for k in ('status','finalPhase','allowedParty','discountBps')},indent=2),flush=True)
        return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output');run(p.parse_args().output)
