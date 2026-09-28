"""Additional integration boundaries, exercised through authenticated Timeline input."""
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
from session import Session

class Boundaries(unittest.TestCase):
    def session(self):
        s=Session();self.addCleanup(s.close);return s
    def negotiating(self):
        s=self.session();h=s.add(s.source('A'));a=s.managed('MutualActivation/Mutual Activation Clause')
        s.wait_phase(h,'NEGOTIATING');return s,h,a

    def test_stale_proposal_terms_and_round_then_valid_acceptance(self):
        s,h,a=self.negotiating()
        s.action(a,'A','proposeChange','proposal',message='Change payment days',changes=[{'op':'set','path':'/commercial/paymentTermDays','val':45}])
        state=s.read(a,'/state');proposal=s.value_id(a,'/state/proposal')
        req=dict(requestId='accept',action='acceptChange',round=state['round'],termsId=state['targetId'],proposalId=proposal)
        for index,change in enumerate(({'round':state['round']-1},{'termsId':s.repo.aliases['Reseller/Reseller Agreement']},{'proposalId':s.repo.aliases['Reseller/Reseller Agreement']})):
            with self.subTest(change=change):
                s.invoke(a,'B','actB',{**req,**change,'requestId':'stale-'+str(index)})
                self.assertEqual(s.read(a,'/state'),state)
        s.invoke(a,'B','actB',req)
        s.wait_value(h,'/terms/commercial/paymentTermDays',45)
        self.assertEqual(s.read(h,'/phase'),'NEGOTIATING')

    def test_wrong_channel_and_operation_then_authorized_termination(self):
        s,h,a=self.negotiating();s.action(a,'A','approve','a');s.action(a,'B','approve','b');s.wait_phase(h,'ACTIVE')
        t=s.managed('ImmediateTermination/Immediate Termination Clause')
        req=dict(requestId='terminate',termsId=s.read(t,'/termsId'))
        original=s.read(t,'/state')
        for operation,channel in (('terminateA','partyB'),('actA','partyA'),('terminateB','partyA')):
            with self.subTest(operation=operation,channel=channel):
                s.invoke(t,'A',operation,req,channel=channel)
                self.assertEqual(s.read(t,'/state'),original)
                self.assertEqual(s.read(h,'/phase'),'ACTIVE')
        s.invoke(t,'A','terminateA',req);s.wait_phase(h,'TERMINATED')

    def test_executable_looking_terms_and_wrong_configuration_type_do_not_install(self):
        for invalid in ('program','type'):
            with self.subTest(invalid=invalid):
                s=self.session();source=s.source('A')
                config=source['activation']['initialTerms']['clauses']['immediateTermination']
                if invalid=='program':config['contracts']={'injected':{'name':'Must never execute'}}
                else:config['type']={'blueId':s.repo.aliases['MutualActivation/Action']}
                h=s.add(source);a=s.managed('MutualActivation/Mutual Activation Clause')
                s.action(a,'A','approve','a');s.action(a,'B','approve','b')
                row=s.wait(h,lambda r:r['processing']['state']=='ERROR',seconds=45,allow_error=True)
                self.assertIsNotNone(row['processing']['issue'])
                self.assertEqual(s.read(h,'/phase'),'NEGOTIATING')
                self.assertEqual(s.read(h,'/clauses'),{})
                self.assertEqual(s.events_of('ImmediateTermination/Agreement Terminated'),[])
                s.close()

if __name__=='__main__':unittest.main()
