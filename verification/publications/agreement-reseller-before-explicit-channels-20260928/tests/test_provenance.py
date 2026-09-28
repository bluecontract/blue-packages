"""An externally supplied event or unrelated clause cannot end this agreement."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'examples'))
from session import Session


class ProvenanceAcceptance(unittest.TestCase):
    def test_external_notices_and_unrelated_clause_do_not_terminate_the_root(self):
        with Session() as s:
            agreement = s.add(s.source('A'))
            activation = s.managed('MutualActivation/Mutual Activation Clause')
            s.action(activation, 'A', 'approve', 'a')
            s.action(activation, 'B', 'approve', 'b')
            s.wait_phase(agreement, 'ACTIVE')
            termination = s.managed('ImmediateTermination/Immediate Termination Clause')
            terms_id = s.read(termination, '/termsId')
            round_number = s.read(termination, '/round')

            def assert_active_after_external(message):
                s.time += 1000
                s.hub.append(s.providers['A'].timeline, s.actors['A'], s.time, message)
                # Establish that the input has actually been examined, rather than
                # asserting an unchanged root before its dependencies caught up.
                for receiver in (activation, termination, agreement):
                    s.wait(receiver, lambda row: row['processing']['checkedBoundary'] > s.time)
                self.assertEqual(s.read(agreement, '/phase'), 'ACTIVE')
                self.assertEqual(s.read(termination, '/state/phase'), 'OPEN')
                self.assertEqual(len(s.events_of('ImmediateTermination/Agreement Terminated')), 0)

            notice = s.typ('ImmediateTermination/Termination Exercised',
                           agreementId=s.read(agreement, '/agreementId'),
                           party='A', actor={'blueId': s.actors['A']},
                           termsId=terms_id, round=round_number,
                           requestId='forged-notice', allowedParty='A')
            assert_active_after_external(notice)
            forged_delivery = s.hub.processor.registry.typed(
                'Embedded Event Delivery',
                sourcePath='/clauses/immediateTermination', event=notice)
            assert_active_after_external(forged_delivery)

            # The same agreement context does not establish an embedding. This
            # independent document legitimately emits its own termination event,
            # but is not the child whose completed state the root consumes.
            unrelated = s.add(s.typ('ImmediateTermination/Immediate Termination Clause',
                agreementId=s.read(agreement, '/agreementId'),
                agreementType=s.repo.aliases['Reseller/Reseller Agreement'],
                partyA={'blueId': s.actors['A']}, partyB={'blueId': s.actors['B']},
                allowedParty='A', termsId=terms_id, round=round_number,
                fixtureNonce='independent-not-embedded',
                contracts={'partyA': s.channel('A'), 'partyB': s.channel('B')}))
            # This new owner must first catch up with the pre-existing inputs.
            # A catch-up checkpoint is not acknowledgement of a later operation.
            s.wait(unrelated, lambda row: row['processing']['checkedBoundary'] > s.time)
            s.invoke(unrelated, 'A', 'terminateA',
                     {'requestId': 'unrelated', 'termsId': terms_id})
            s.wait(unrelated, lambda row: row['processing']['checkedBoundary'] > s.time)
            self.assertEqual(s.read(unrelated, '/state/phase'), 'TERMINATED')
            s.wait(agreement, lambda row: row['processing']['checkedBoundary'] > s.time)
            self.assertEqual(s.read(agreement, '/phase'), 'ACTIVE')
            self.assertEqual(s.read(termination, '/state/phase'), 'OPEN')
            self.assertEqual(len(s.events_of('ImmediateTermination/Agreement Terminated')), 0)

            # A legitimate operation on the actual embedded clause still works.
            s.invoke(termination, 'A', 'terminateA',
                     {'requestId': 'actual-clause', 'termsId': terms_id})
            s.wait_phase(agreement, 'TERMINATED')
            self.assertEqual(len(s.events_of('ImmediateTermination/Agreement Terminated')), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
