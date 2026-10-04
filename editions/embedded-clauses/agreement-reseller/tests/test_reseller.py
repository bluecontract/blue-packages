"""Acceptance against actual signed Timelines and automatic Coordination owners."""
from pathlib import Path
import json,sys,unittest,tempfile
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
from session import Session,ROOT
from run_scenario import run
from blue_coordination.engine import SQLiteStore
from blue_packages import Runtime,read_package,mount,PackageError
from blue_language.physical import PhysicalCache


class ResellerAcceptance(unittest.TestCase):
    def session(self,**kw):
        s=Session(**kw);self.addCleanup(s.close);return s
    def negotiating(self,allowed='EITHER',**kw):
        s=self.session(**kw);h=s.add(s.source(allowed));a=s.managed('MutualActivation/Mutual Activation Clause')
        s.wait_phase(h,'NEGOTIATING');return s,h,a
    def active(self,allowed='EITHER',**kw):
        s,h,a=self.negotiating(allowed,**kw)
        s.action(a,'A','approve','approve-a');s.action(a,'B','approve','approve-b');s.wait_phase(h,'ACTIVE')
        t=None if allowed is None else s.managed('ImmediateTermination/Immediate Termination Clause')
        return s,h,a,t
    def request(self,s,t,request_id='terminate',**extra):
        return {'requestId':request_id,'termsId':s.read(t,'/termsId'),**extra}
    def no_effect(self,s,t,h,invoke):
        before=s.read(t,'/state');parent=s.read(h,'/phase');events=len(s.events_of('ImmediateTermination/Agreement Terminated'))
        invoke()
        self.assertEqual(s.read(t,'/state'),before)
        self.assertEqual(s.read(h,'/phase'),parent)
        self.assertEqual(len(s.events_of('ImmediateTermination/Agreement Terminated')),events)

    def test_01_requested_negotiation_activation_unilateral_story(self):
        result=run();self.assertEqual(result['finalPhase'],'TERMINATED')
        self.assertEqual(result['termination']['party'],'A')

    def test_02_authorization_matrix_and_either_is_unilateral(self):
        for option,side,denied in [('A','A','B'),('B','B','A'),('EITHER','A',None),('EITHER','B',None)]:
            with self.subTest(option=option,terminating_party=side):
                s,h,a,t=self.active(option)
                if denied:
                    self.no_effect(s,t,h,lambda:s.invoke(t,denied,'terminate'+denied,self.request(s,t,'denied')))
                s.invoke(t,side,'terminate'+side,self.request(s,t,'valid'))
                s.wait_phase(h,'TERMINATED')
                self.assertEqual(s.read(h,'/termination/party'),side)
                self.assertEqual(len(s.events_of('ImmediateTermination/Agreement Terminated')),1)
                s.close()

    def test_03_absent_clause_stays_absent_after_activation(self):
        s,h,a,t=self.active(None)
        self.assertIsNone(t)
        self.assertNotIn('immediateTermination',s.read(h,'/terms/clauses'))
        self.assertEqual(s.read(h,'/clauses'),{})
        self.assertEqual(len(s.events_of('ImmediateTermination/Agreement Terminated')),0)

    def test_04_no_executable_termination_before_activation_or_from_ready(self):
        s,h,a=self.negotiating('A')
        self.assertEqual(s.read(h,'/clauses'),{})
        s.action(a,'A','ready','ra');s.action(a,'B','ready','rb')
        self.assertEqual(s.read(h,'/phase'),'NEGOTIATING')
        self.assertEqual(s.read(h,'/clauses'),{})
        s.action(a,'A','approve','aa')
        self.assertEqual(s.read(h,'/phase'),'NEGOTIATING')
        self.assertEqual(s.read(h,'/clauses'),{})

    def test_05_wrong_actor_cannot_select_the_permitted_operation(self):
        s,h,a,t=self.active('A')
        self.no_effect(s,t,h,lambda:s.invoke(t,'A','terminateA',self.request(s,t),sender='B'))
        # A legitimate request after the rejected request must still progress.
        s.invoke(t,'A','terminateA',self.request(s,t,'real-a'));s.wait_phase(h,'TERMINATED')

    def test_06_wrong_revision_and_caller_supplied_party_are_rejected(self):
        s,h,a,t=self.active('A')
        wrong=self.request(s,t,'stale');wrong['termsId']=s.repo.aliases['Reseller/Reseller Agreement']
        self.no_effect(s,t,h,lambda:s.invoke(t,'A','terminateA',wrong))
        forged=self.request(s,t,'forged',party='A')
        self.no_effect(s,t,h,lambda:s.invoke(t,'B','terminateB',forged))
        s.invoke(t,'A','terminateA',self.request(s,t,'good'));s.wait_phase(h,'TERMINATED')

    def test_07_exact_retry_no_duplicate_and_changed_reuse_rejected(self):
        s,h,a,t=self.active('EITHER');req=self.request(s,t,'once',reason='First notice')
        s.invoke(t,'A','terminateA',req);s.wait_phase(h,'TERMINATED')
        record=s.read(h,'/termination');accepted=s.read(h,'/acceptedRevision');terms=s.read(h,'/terms')
        s.invoke(t,'A','terminateA',req)
        self.no_effect(s,t,h,lambda:s.invoke(t,'A','terminateA',{**req,'reason':'Changed notice'}))
        self.no_effect(s,t,h,lambda:s.invoke(t,'B','terminateB',self.request(s,t,'second-party')))
        self.assertEqual(s.read(h,'/termination'),record)
        self.assertEqual(s.read(h,'/acceptedRevision'),accepted)
        self.assertEqual(s.read(h,'/terms'),terms)
        self.assertEqual(len(s.events_of('ImmediateTermination/Termination Exercised')),1)
        self.assertEqual(len(s.events_of('ImmediateTermination/Agreement Terminated')),1)

    def test_08_negotiation_cannot_reopen_or_reactivate_after_termination(self):
        s,h,a,t=self.active('A')
        s.invoke(t,'A','terminateA',self.request(s,t));s.wait_phase(h,'TERMINATED')
        state=s.read(a,'/state');record=s.read(h,'/termination')
        s.action(a,'A','approve','late-approval')
        s.action(a,'B','proposeChange','late-edit',message='Too late',changes=[{'op':'set','path':'/commercial/paymentTermDays','val':60}])
        self.assertEqual(s.read(a,'/state'),state)
        self.assertEqual(s.read(h,'/phase'),'TERMINATED')
        self.assertEqual(s.read(h,'/termination'),record)
        self.assertEqual(len(s.events_of('Agreements/Agreement Activated')),1)

    def test_09_negotiating_policy_change_invalidates_earlier_approval(self):
        s,h,a=self.negotiating('EITHER')
        old=s.action(a,'A','approve','old-approval')
        s.action(a,'B','proposeChange','narrow-policy',message='Only the reseller may terminate',changes=[
            {'op':'set','path':'/clauses/immediateTermination/allowedParty','val':'B'}])
        self.assertEqual(s.read(a,'/state/signals'),{'A':'NONE','B':'NONE'})
        state=s.read(a,'/state')
        stale={**old,'requestId':'stale-round-new-id'}
        s.invoke(a,'A','actA',stale)
        self.assertEqual(s.read(a,'/state'),state)
        s.action(a,'A','acceptChange','accept-narrow',proposalId=s.value_id(a,'/state/proposal'))
        s.action(a,'A','approve','new-a');s.action(a,'B','approve','new-b');s.wait_phase(h,'ACTIVE')
        t=s.managed('ImmediateTermination/Immediate Termination Clause')
        self.assertEqual(s.read(t,'/allowedParty'),'B')
        self.no_effect(s,t,h,lambda:s.invoke(t,'A','terminateA',self.request(s,t,'wrong-a')))
        s.invoke(t,'B','terminateB',self.request(s,t,'right-b'));s.wait_phase(h,'TERMINATED')

    def test_10_negotiated_removal_does_not_reappear_as_a_default(self):
        s,h,a=self.negotiating('EITHER')
        s.action(a,'A','proposeChange','remove-clause',message='Remove automated immediate termination',changes=[
            {'op':'remove','path':'/clauses/immediateTermination'}])
        s.action(a,'B','acceptChange','accept-removal',proposalId=s.value_id(a,'/state/proposal'))
        s.action(a,'A','approve','a');s.action(a,'B','approve','b');s.wait_phase(h,'ACTIVE')
        self.assertNotIn('immediateTermination',s.read(h,'/terms/clauses'))
        self.assertEqual(s.read(h,'/clauses'),{})

    def test_11_sqlite_restart_preserves_terminal_evidence_and_retry_semantics(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        store=SQLiteStore(Path(directory.name)/'reseller.sqlite');self.addCleanup(store.close)
        s,h,a,t=self.active('A',store=store);req=self.request(s,t,'durable')
        s.invoke(t,'A','terminateA',req);s.wait_phase(h,'TERMINATED')
        record=s.read(h,'/termination');s.restart()
        self.assertEqual(s.read(h,'/termination'),record)
        s.invoke(t,'A','terminateA',req)
        self.assertEqual(s.read(h,'/phase'),'TERMINATED')
        self.assertEqual(s.read(h,'/termination'),record)
        self.assertEqual(len(s.events_of('ImmediateTermination/Agreement Terminated')),1)

    def test_12_package_content_does_not_grant_native_runtime_support(self):
        with PhysicalCache(65536).scope():
            p=read_package(ROOT/'agreement-reseller/dist/package.bluepkg')
            Runtime.agreements().require(p)
            with self.assertRaises(PackageError):Runtime.current().require(p)
            language=Runtime.agreements().language();mount(language,p,'Shop',list(p.exports))
            self.assertIn('Shop/Reseller Agreement',language.aliases)
            self.assertNotIn('ImmediateTermination/Immediate Termination Clause',language.aliases)
            self.assertNotIn('MutualActivation/Mutual Activation Clause',language.aliases)
            self.assertFalse(any(n.endswith('.py') for n in p.files))

if __name__=='__main__':unittest.main(verbosity=2)
