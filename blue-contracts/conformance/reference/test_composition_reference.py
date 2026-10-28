"""Independent structural transitions, not native authentication substitutes."""
import unittest
from composition_reference import channel_lifetimes, check_channel_lifetimes
from blue_contracts.reference.model import ContractError


class ChannelLifetimeTests(unittest.TestCase):
    def test_changed_acceptance_resets_lifetime_but_unselected_body_does_not(self):
        declarations = {'in': {'_role': 'external', 'type': {'blueId': 'channel-type'}}}
        first = channel_lifetimes(declarations, {}, {})
        self.assertEqual(first['channels']['in']['generation'], 1)
        same = channel_lifetimes({**declarations, 'compute': {'_role': 'compute', 'expr': 'opaque'}},
                                 first['channels'], first['serials'])
        self.assertEqual(same, first)
        changed = {'in': {**declarations['in'], 'event': {'blueId': 'selected-event-type'}}}
        second = channel_lifetimes(changed, first['channels'], first['serials'])
        self.assertEqual(second['channels']['in']['generation'], 2)
        with self.assertRaises(ContractError):
            check_channel_lifetimes(changed, first['channels'], first['serials'])
        check_channel_lifetimes(changed, second['channels'], second['serials'])

    def test_removed_recreated_channel_uses_retained_serial(self):
        declarations = {'in': {'_role': 'external', 'type': {'blueId': 'channel-type'}}}
        first = channel_lifetimes(declarations, {}, {})
        removed = channel_lifetimes({}, first['channels'], first['serials'])
        self.assertEqual(removed, {'channels': {}, 'serials': {'in': 1}})
        recreated = channel_lifetimes(declarations, removed['channels'], removed['serials'])
        self.assertEqual(recreated['channels']['in']['generation'], 2)

    def test_composite_signature_includes_selected_leaf_acceptance(self):
        declarations = {
            'in': {'_role': 'external', 'type': {'blueId': 'channel-type'}},
            'both': {'_role': 'composite', 'type': {'blueId': 'composite-type'}, 'channels': ['in']}}
        first = channel_lifetimes(declarations, {}, {})
        declarations['in']['event'] = {'blueId': 'new-event-type'}
        second = channel_lifetimes(declarations, first['channels'], first['serials'])
        self.assertEqual({key: row['generation'] for key, row in second['channels'].items()},
                         {'in': 2, 'both': 2})

    def test_checked_shared_vector_is_recomputed_from_its_inputs(self):
        import hashlib
        import json
        from pathlib import Path
        source = Path(__file__).resolve().parents[2] / 'tools/composition_reference.py'
        vector = json.loads(Path(__file__).with_name('channel-lifetimes-vector.json').read_text())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), vector['referenceSourceSha256'])
        previous, serials = {}, {}
        for row in vector['transitions']:
            actual = channel_lifetimes(row['declarations'], previous, serials)
            self.assertEqual(actual, row['expected'], row['label'])
            previous, serials = actual['channels'], actual['serials']
