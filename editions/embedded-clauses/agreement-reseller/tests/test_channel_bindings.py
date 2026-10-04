"""Every managed instance supplies its own concrete channel bindings."""
from pathlib import Path
import sys
import unittest
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'examples'))
from session import Session


class ChannelBindings(unittest.TestCase):
    def binding(self, s, handle, channel):
        row = s.row(handle)
        with s.store.read() as view:
            member = view.get('heads', row['instance'])['member']
        return next(c for c in row['channels'] if c['member'] == member and c['channel'] == channel)

    def session(self):
        s = Session()
        self.addCleanup(s.close)
        return s

    def rejected_start(self, s, source):
        handle = s.engine.add(source)
        row = s.wait(handle, lambda r: r['processing']['state'] == 'ERROR', allow_error=True)
        self.assertIsNone(row['lastStable'])
        self.assertIsNotNone(row['processing']['issue'])
        return row['processing']['issue']

    def test_missing_bindings_are_not_inherited_between_documents(self):
        for document in ('root', 'activation'):
            for channel in ('partyA', 'partyB'):
                with self.subTest(document=document, channel=channel):
                    s = self.session()
                    source = s.source('A')
                    target = source if document == 'root' else source['activation']
                    del target['contracts'][channel]
                    issue = self.rejected_start(s, source)
                    self.assertEqual(issue['code'], 'BEX_EXECUTION_REJECTED')
                    s.close()

    def test_root_channel_actor_must_match_the_party(self):
        s = self.session()
        source = s.source('A')
        source['contracts']['partyA']['actor'] = {'blueId': s.actors['B']}
        issue = self.rejected_start(s, source)
        self.assertEqual(issue['code'], 'BEX_EXECUTION_REJECTED')

    def test_inline_signed_timelines_and_repeated_channel_bindings(self):
        s = self.session()
        source = s.source('A')
        for document in (source, source['activation']):
            for side in ('A', 'B'):
                channel = document['contracts']['party' + side]
                # Supply the actual Signed Timeline with timelineId/publicKey
                # inline, rather than resolving it through a BlueId reference.
                channel['timeline'] = s.read_id(s.providers[side].timeline)
                self.assertIn('timelineId', channel['timeline'])
                self.assertIn('publicKey', channel['timeline'])
        root = s.add(source)
        activation = s.managed('MutualActivation/Mutual Activation Clause')
        s.action(activation, 'A', 'approve', 'approve-a')
        s.action(activation, 'B', 'approve', 'approve-b')
        s.wait_phase(root, 'ACTIVE')
        termination = s.managed('ImmediateTermination/Immediate Termination Clause')
        for side in ('A', 'B'):
            path = '/contracts/party' + side
            self.assertEqual(s.value_id(root, path), s.value_id(termination, path))
        s.invoke(termination, 'A', 'terminateA', dict(requestId='terminate', termsId=s.read(termination, '/termsId')))
        s.wait_phase(root, 'TERMINATED')

    def test_unregistered_channel_subtype_does_not_gain_native_support(self):
        s = self.session()
        source = s.source('A')
        channel = source['contracts']['partyA']
        channel['type'] = {'name': 'Unregistered Channel', 'type': deepcopy(channel['type'])}
        issue = self.rejected_start(s, source)
        self.assertEqual(issue['code'], 'INVALID_CONTRACT_ROLE')

    def test_distinct_activation_timelines_do_not_supply_the_root_bindings(self):
        s = self.session()
        source = s.source('A')
        root_bindings = deepcopy(source['contracts'])
        for side in ('A', 'B'):
            s.providers['root' + side] = s.providers[side]
            s.actors['root' + side] = s.actors[side]
            s.providers[side] = s.hub.create('activation-' + side, [s.actors[side]])
            source['activation']['contracts']['party' + side] = s.channel(side)
        root = s.add(source)
        activation = s.managed('MutualActivation/Mutual Activation Clause')
        s.action(activation, 'A', 'approve', 'approve-a')
        s.action(activation, 'B', 'approve', 'approve-b')
        s.wait_phase(root, 'ACTIVE')
        termination = s.managed('ImmediateTermination/Immediate Termination Clause')
        for side in ('A', 'B'):
            path = '/contracts/party' + side + '/timeline'
            self.assertEqual(self.binding(s, root, 'party'+side)['timeline'], root_bindings['party'+side]['timeline']['blueId'])
            self.assertEqual(s.value_id(termination, path), s.value_id(root, path))
            self.assertNotEqual(s.value_id(termination, path), s.value_id(activation, path))
        request = dict(requestId='terminate', termsId=s.read(termination, '/termsId'))
        # The activation Timeline cannot call the termination clause merely
        # because its actor is the same; both Timeline and actor must match.
        # The termination owner does not subscribe to this Timeline, so its
        # completeness frontier need not advance for this unrelated input.
        s.time += 1000
        s.hub.append(s.providers['A'].timeline, s.actors['A'], s.time, {
            'type': 'Contracts/Operation Request',
            'document': {'blueId': s.row(termination)['lastStable']['blueId']},
            'channel': 'partyA', 'operation': 'terminateA', 'request': request})
        s.wait(activation, lambda row: row['processing']['checkedBoundary'] > s.time)
        self.assertEqual(s.read(termination, '/state/phase'), 'OPEN')
        self.assertEqual(s.read(root, '/phase'), 'ACTIVE')
        s.invoke(termination, 'A', 'terminateA', request, sender='rootA')
        s.wait_phase(root, 'TERMINATED')
        self.assertEqual(len(s.events_of('ImmediateTermination/Agreement Terminated')), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
