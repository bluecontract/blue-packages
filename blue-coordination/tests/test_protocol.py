from pathlib import Path
import copy
import json
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from reference import (Exact, ModelProvider, Verifier, Coverage, ref, commitment,
                       verify_opening, MAX_TIME, MAX_BOUND, api_urls)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from blue_language.physical import PhysicalCache

SEED = b'\x22' * 32
KEY = Ed25519PrivateKey.from_private_bytes(SEED).public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
OTHER = Ed25519PrivateKey.from_private_bytes(b'\x33' * 32).public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()

class ProtocolFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = PhysicalCache(65536).scope()
        cls.scope.__enter__()
        cls.e = Exact()

    @classmethod
    def tearDownClass(cls):
        cls.scope.__exit__(None, None, None)

    def setUp(self):
        self.p = ModelProvider(self.e)
        self.t = self.p.create('alice', self._testMethodName, public=True)
        self.v = self.p.verifier

    def entry(self, timestamp=99, request='a', owner='alice'):
        return self.p.append(owner, self.t, {'text': request}, request, timestamp)

    def request(self, request='read', **kw):
        return self.p.request('Read Timeline Request', timeline=ref(self.e.identity(self.t)), limit=kw.pop('limit', 100), **kw)

    def chain(self):
        a = self.entry()
        initial = self.p.seal(self.t, 100)
        b = self.entry(101, 'b')
        return a, b, self.v.range(initial, [a])

    def private(self):
        self.t = self.p.create('alice', self._testMethodName + '-private')
        control = self.p.create('__provider__', self._testMethodName + '-control', public=True)
        readers = [KEY]
        access, change = self.p.create_access('alice', [self.t], readers, 'grant', control, 10)
        return control, readers, access, change

class ProtocolTests(ProtocolFixture):





    def test_optional_signature_on_public_access_discovery_is_validated(self):
        control, readers, access, _ = self.private()
        q = self.p.request('Get Timeline Access Request', access=access)
        request, key = self.p.authenticate_reader(self.p.sign_reader(q, SEED))
        self.assertEqual(key, KEY)
        self.assertEqual(self.e.identity(request), self.e.identity(q))

    def test_checkpoint_only_nonempty_is_not_an_empty_range(self):
        entry = self.entry()
        q = self.request(limit=0)
        response = self.v.read_response(q, self.p.read(q, 102))
        self.assertNotIn('page', response)
        _, guarantee = self.v.checkpoint(response['checkpoint'])
        self.assertEqual(self.e.identity(guarantee['lastEntry']), self.e.identity(entry))
        with self.assertRaisesRegex(ValueError, 'HEAD_MISMATCH'):
            self.v.range(response['checkpoint'], [])

    def test_checkpoint_only_empty_timeline(self):
        q = self.request(limit=0)
        response = self.v.read_response(q, self.p.read(q, 102))
        self.assertEqual(self.v.range(response['checkpoint'], []).complete_before, 102)

    def test_read_minimum_boundary_honored(self):
        self.entry()
        q = self.request(minimumCompleteBefore=102)
        response = self.v.read_response(q, self.p.read(q, 103))
        self.assertGreaterEqual(self.v.checkpoint(response['checkpoint'])[1]['completeBefore'], 102)

    def test_read_impossible_minimum_is_failure(self):
        q = self.request(limit=0, minimumCompleteBefore=1000)
        with self.assertRaisesRegex(ValueError, 'BOUND_UNAVAILABLE'):
            self.p.read(q, 102)

    def test_checkpoint_only_forbids_position_selectors(self):
        for selector in ({'afterTimestamp': -1}, {'afterEntry': ref(self.e.identity(self.entry()))}):
            q = self.request(limit=0, **selector)
            with self.assertRaisesRegex(ValueError, 'CHECKPOINT_ONLY_SELECTOR'):
                self.p.read(q, 102)

    def test_cursor_cannot_request_new_boundary(self):
        self.chain()
        first, _ = self.v.page(self.request(limit=1), self.p.read(self.request(limit=1), 102))
        q = self.request(cursor=first['nextCursor'], minimumCompleteBefore=105)
        with self.assertRaisesRegex(ValueError, 'CURSOR_MINIMUM_BOUND'):
            self.p.read(q, 106)

    def test_positive_read_cannot_omit_page(self):
        q = self.request()
        response = self.v.attestation(self.p.read(q, 102))
        del response['page']
        with self.assertRaisesRegex(ValueError, 'UNEXPECTED_PAGE_PRESENCE'):
            self.v.read_response(q, self.p.attest(response))

    def test_zero_read_cannot_include_page(self):
        q = self.request(limit=0)
        response = self.v.attestation(self.p.read(q, 102))
        response['page'] = self.v.attestation(self.p.read(self.request(), 102))['page']
        with self.assertRaisesRegex(ValueError, 'UNEXPECTED_PAGE_PRESENCE'):
            self.v.read_response(q, self.p.attest(response))

    def test_response_checkpoint_cannot_differ_from_page(self):
        q = self.request()
        response = self.v.attestation(self.p.read(q, 102))
        response['checkpoint'] = self.p.seal(self.t, 103)
        with self.assertRaisesRegex(ValueError, 'CHECKPOINT_CHANGED'):
            self.v.page(q, self.p.attest(response))

    def test_signed_response_below_requested_minimum_rejected(self):
        q = self.request(limit=0, minimumCompleteBefore=105)
        response = self.v.attestation(self.p.read(q, 106))
        other = ModelProvider(self.e)
        other.create('alice', self._testMethodName, public=True)
        response['checkpoint'] = other.seal(self.t, 102)
        with self.assertRaisesRegex(ValueError, 'BOUND_UNAVAILABLE'):
            self.v.read_response(q, self.p.attest(response))

    def test_empty_guarantee(self):
        coverage = self.v.range(self.p.seal(self.t, 100), [])
        self.assertEqual((coverage.head, coverage.complete_before), (None, 100))

    def test_successor_proves_gap(self):
        a, b, known = self.chain()
        coverage = self.v.successor(self.p.attest(b), [b], self.e.identity(a), known.entries)
        self.assertEqual((coverage.head, coverage.complete_before), (self.e.identity(a), 101))
        self.assertNotIn(self.e.identity(b), coverage.entries)

    def test_successor_from_genesis_proves_empty_prefix(self):
        entry = self.entry(101)
        coverage = self.v.successor(self.p.attest(entry), [entry])
        self.assertEqual((coverage.entries, coverage.complete_before), ([], 101))

    def test_unknown_anchor_rejected(self):
        a, b, known = self.chain()
        with self.assertRaisesRegex(ValueError, 'UNKNOWN_ANCHOR'):
            self.v.successor(self.p.attest(b), [b], self.e.identity(a), [])

    def test_omitted_middle_entry_rejected(self):
        a = self.entry(99)
        middle = self.entry(100, 'middle')
        b = self.entry(101, 'b')
        with self.assertRaisesRegex(ValueError, 'CHAIN_GAP'):
            self.v.successor(self.p.attest(b), [a, b])

    def test_fake_unsigned_successor_rejected(self):
        a, b, known = self.chain()
        bad = self.p.attest(b)
        bad['signature'] = '00' * 64
        with self.assertRaisesRegex(ValueError, 'INVALID_SIGNATURE'):
            self.v.successor(bad, [b], self.e.identity(a), known.entries)

    def test_signature_domain_separation(self):
        a = self.entry()
        g = self.p.seal(self.t, 100)
        bad = self.p.attest(a)
        bad['signature'] = g['signature']
        with self.assertRaisesRegex(ValueError, 'INVALID_SIGNATURE'):
            self.v.attestation(bad)

    def test_wrong_provider_rejected(self):
        other = ModelProvider(self.e, seed=b'\x44' * 32, endpoint='https://other.example')
        with self.assertRaisesRegex(ValueError, 'WRONG_PROVIDER'):
            self.v.attestation(other.attest(self.entry()))

    def test_wrong_timeline_rejected(self):
        a = self.entry()
        other = self.p.create('alice', 'other-' + self._testMethodName, public=True)
        checkpoint = self.p.seal(other, 100)
        with self.assertRaisesRegex(ValueError, 'WRONG_TIMELINE'):
            self.v.range(checkpoint, [a])

    def test_bound_does_not_include_equal_timestamp(self):
        a = self.entry(100)
        g = self.e.typed('Timeline Completeness Guarantee', timeline=ref(self.e.identity(self.t)), completeBefore=100, lastEntry=ref(self.e.identity(a)))
        sig = self.p.secret.sign(('blue.coordination.guarantee\n' + self.e.identity(g)).encode()).hex()
        checkpoint = self.e.typed('Timeline Attestation', timeline=ref(self.e.identity(self.t)), guarantee=g, signature=sig)
        with self.assertRaisesRegex(ValueError, 'ENTRY_OUTSIDE_PREFIX'):
            self.v.range(checkpoint, [a])

    def test_explicit_bound_allows_successor_itself(self):
        a, b, known = self.chain()
        coverage = self.v.range(self.p.seal(self.t, 102), [a, b])
        self.assertEqual(coverage.head, self.e.identity(b))

    def test_conflicting_retained_prefix_rejected(self):
        a, b, known = self.chain()
        full = self.v.range(self.p.seal(self.t, 102), [a, b])
        fork = copy.deepcopy(b)
        fork['message'] = {'text': 'fork'}
        with self.assertRaisesRegex(ValueError, 'HISTORY_CONFLICT'):
            self.v.successor(self.p.attest(fork), [fork], self.e.identity(a), full.entries)

    def test_append_after_seal_cannot_backdate(self):
        self.p.seal(self.t, 200)
        a = self.entry(99)
        self.assertEqual(a['timestamp'], 200)
        b = self.entry(1, 'b')
        self.assertEqual(b['timestamp'], 201)

    def test_bound_never_decreases(self):
        self.p.seal(self.t, 200)
        g = self.v.checkpoint(self.p.seal(self.t, 100))[1]
        self.assertEqual(g['completeBefore'], 200)

    def test_future_minimum_not_fabricated(self):
        with self.assertRaisesRegex(ValueError, 'BOUND_UNAVAILABLE'):
            self.p.seal(self.t, 100, minimum=100000000)

    def test_time_exhaustion(self):
        self.entry(MAX_TIME)
        self.p.seal(self.t, MAX_BOUND)
        with self.assertRaisesRegex(ValueError, 'TIME_EXHAUSTED'):
            self.entry(MAX_BOUND, 'overflow')

    def test_append_owner_only(self):
        with self.assertRaisesRegex(ValueError, 'ACCESS_DENIED'):
            self.entry(owner='bob')

    def test_append_idempotency_after_restart(self):
        a = self.entry()
        state = json.loads(json.dumps(self.p.snapshot()))
        resumed = ModelProvider(self.e, snapshot=state)
        retry = resumed.append('alice', self.t, {'text': 'a'}, 'a', 500)
        self.assertEqual(self.e.identity(a), self.e.identity(retry))
        self.assertEqual(len(resumed.state['timelines'][self.e.identity(self.t)]['entries']), 1)

    def test_conflicting_retry_rejected(self):
        self.entry()
        with self.assertRaisesRegex(ValueError, 'IDEMPOTENCY_CONFLICT'):
            self.p.append('alice', self.t, {'text': 'changed'}, 'a', 100)

    def test_expected_head_conflict(self):
        self.entry()
        with self.assertRaisesRegex(ValueError, 'HEAD_CONFLICT'):
            self.p.append('alice', self.t, {'text': 'b'}, 'b', 100, expected='not-the-head')

    def test_pagination_snapshot_survives_new_append(self):
        a, b, known = self.chain()
        q = self.request(limit=1)
        first, ids = self.v.page(q, self.p.read(q, 102))
        c = self.entry(200, 'c')
        q2 = self.request('read-2', limit=1, cursor=first['nextCursor'])
        second, ids2 = self.v.page(q2, self.p.read(q2, 201))
        self.assertTrue(first['hasMore'])
        self.assertFalse(second['hasMore'])
        self.assertEqual(ids + ids2, [self.e.identity(a), self.e.identity(b)])
        self.assertEqual(self.e.identity(first['checkpoint']), self.e.identity(second['checkpoint']))
        coverage = self.v.range(second['checkpoint'], [ref(x) for x in ids + ids2])
        self.assertEqual(coverage.complete_before, 102)
        self.assertNotIn(self.e.identity(c), coverage.entries)

    def test_timestamp_seek_is_exclusive(self):
        a, b, known = self.chain()
        q = self.request(afterTimestamp=99)
        page, ids = self.v.page(q, self.p.read(q, 102))
        self.assertEqual(ids, [self.e.identity(b)])
        self.assertEqual(self.e.identity(page['predecessor']), self.e.identity(a))

    def test_timestamp_beyond_checkpoint_not_future_proof(self):
        self.entry()
        q = self.request(afterTimestamp=999)
        page, ids = self.v.page(q, self.p.read(q, 100))
        self.assertEqual(ids, [])
        self.assertEqual(self.v.checkpoint(page['checkpoint'])[1]['completeBefore'], 100)

    def test_page_is_not_whole_range(self):
        self.chain()
        q = self.request(limit=1)
        page, ids = self.v.page(q, self.p.read(q, 102))
        with self.assertRaisesRegex(ValueError, 'HEAD_MISMATCH'):
            self.v.range(page['checkpoint'], page['entries'])

    def test_truncated_signed_page_rejected(self):
        self.chain()
        q = self.request()
        response = self.v.attestation(self.p.read(q, 102))
        page = self.e.get(response['page'])
        page['entries'] = page['entries'][:-1]
        response['page'] = page
        with self.assertRaisesRegex(ValueError, 'TRUNCATED_PAGE'):
            self.v.page(q, self.p.attest(response))

    def test_false_has_more_without_progress_rejected(self):
        self.chain()
        q = self.request(limit=1)
        response = self.v.attestation(self.p.read(q, 102))
        page = self.e.get(response['page'])
        page['entries'] = []
        response['page'] = page
        with self.assertRaisesRegex(ValueError, 'NO_CURSOR_PROGRESS'):
            self.v.page(q, self.p.attest(response))

    def test_page_wrong_request_rejected(self):
        self.entry()
        q = self.request()
        reply = self.p.read(q, 100)
        q2 = self.request(limit=1)
        with self.assertRaisesRegex(ValueError, 'WRONG_REQUEST'):
            self.v.page(q2, reply)

    def test_conflicting_selectors_rejected(self):
        a = self.entry()
        q = self.request(afterTimestamp=10, afterEntry=ref(self.e.identity(a)))
        with self.assertRaisesRegex(ValueError, 'INVALID_SELECTORS'):
            self.p.read(q, 100)

    def test_mixed_checkpoint_rejected(self):
        self.chain()
        q = self.request(limit=1)
        first, _ = self.v.page(q, self.p.read(q, 102))
        q2 = self.request('next', cursor=first['nextCursor'])
        response = self.v.attestation(self.p.read(q2, 105))
        page = self.e.get(response['page'])
        page['checkpoint'] = self.p.seal(self.t, 105)
        response['page'] = page
        with self.assertRaisesRegex(ValueError, 'CHECKPOINT_CHANGED'):
            self.v.page(q2, self.p.attest(response))

    def test_revoked_reader_cannot_continue_cursor(self):
        control, readers, access, _ = self.private()
        self.chain()
        q = self.request(limit=1)
        page, _ = self.v.page(q, self.p.read(q, 102, key=KEY))
        self.p.update_access('alice', access, [self.t], [], 'revoke', 103)
        q2 = self.request('next', cursor=page['nextCursor'])
        with self.assertRaisesRegex(ValueError, 'ACCESS_DENIED'):
            self.p.read(q2, 105, key=KEY)
        self.p.update_access('alice', access, [self.t], readers, 'restore', 106)
        page2, _ = self.v.page(q2, self.p.read(q2, 107, key=KEY))
        self.assertFalse(page2['hasMore'])

    def test_repeatable_reader_signature_rechecks_access_after_restart(self):
        control, readers, access, first = self.private()
        q = self.request()
        envelope = self.p.sign_reader(q, SEED)
        self.p.authenticate_reader(envelope)
        resumed = ModelProvider(self.e, snapshot=json.loads(json.dumps(self.p.snapshot())))
        resumed.authenticate_reader(envelope)
        resumed.update_access('alice', access, [self.t], [], 'revoke', 20)
        with self.assertRaisesRegex(ValueError, 'ACCESS_DENIED'):
            resumed.authenticate_reader(envelope)

    def test_obsolete_request_metadata_rejected(self):
        for name, value in [('requestId', 'unused'), ('provider', ref(self.p.pid)), ('nonce', '00' * 32), ('createdAt', 1), ('expiresAt', 2)]:
            with self.subTest(name=name):
                q = self.request(**{name: value})
                with self.assertRaisesRegex(ValueError, 'UNEXPECTED_REQUEST_METADATA'):
                    self.p.public_read(q, 100)

    def test_reader_signature_does_not_authorize_append(self):
        self.private()
        q = self.p.request('Append Entry Request', idempotencyKey='append', timeline=ref(self.e.identity(self.t)), message={'text': 'no'})
        with self.assertRaisesRegex(ValueError, 'OWNER_OPERATION'):
            self.p.authenticate_reader(self.p.sign_reader(q, SEED))

    def test_ungranted_signed_key_rejected(self):
        self.private()
        with self.assertRaisesRegex(ValueError, 'ACCESS_DENIED'):
            self.p.authenticate_reader(self.p.sign_reader(self.request(), b'\x33' * 32))

    def test_access_history_and_restoration(self):
        control, readers, access, first = self.private()
        self.p.update_access('alice', access, [self.t], [], 'revoke', 20)
        self.assertEqual(self.p.access_execution(access,21).permissions()['allowedKeys'], [])
        self.p.update_access('alice', access, [self.t], readers, 'restore', 30)
        self.assertEqual(self.p.access_execution(access,31).permissions()['allowedKeys'], readers)
        self.assertTrue(self.p.can_read(control))

    def test_access_owner_only(self):
        control, readers, access, first = self.private()
        with self.assertRaisesRegex(ValueError, 'ACCESS_DENIED'):
            self.p.update_access('bob', access, [self.t], [], 'no', 20)

    def test_access_updates_target_initial_document_and_follow_timeline_order(self):
        control, readers, access, first = self.private()
        a = self.p.update_access('alice', access, [self.t], [], 'revoke', 20)
        b = self.p.update_access('alice', access, [self.t], readers, 'restore', 20)
        for entry in (a, b):
            call = self.e.get(entry['message'])
            self.assertEqual(self.e.identity(call['document']), self.e.identity(access))
            self.assertNotIn('requireExactDocumentVersion', call)
        self.assertLess(a['timestamp'], b['timestamp'])
        self.assertEqual(self.p.access_execution(access, 30).permissions()['allowedKeys'], readers)

    def test_access_retry_returns_original_change(self):
        control, readers, access, first = self.private()
        again, event = self.p.create_access('alice', [self.t], readers, 'grant', control, 20)
        self.assertEqual(self.e.identity(first), self.e.identity(event))

    def test_duplicate_access_key_rejected(self):
        control, readers, access, first = self.private()
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_ACCESS_VALUE'):
            self.p.update_access('alice', access, [self.t], readers + readers, 'no', 20)

    def test_access_union_and_removed_timeline(self):
        control, keys, first, _ = self.private()
        second_timeline = self.p.create('alice', 'second-granted')
        second, _ = self.p.create_access('alice', [self.t, second_timeline], keys, 'second-access', control, 12)
        self.p.update_access('alice', first, [self.t], [], 'revoke-first', 20)
        self.assertTrue(self.p.can_read(self.t,key=KEY))
        self.p.update_access('alice', second, [second_timeline], keys, 'remove-timeline', 30)
        self.assertFalse(self.p.can_read(self.t,key=KEY))
        self.assertTrue(self.p.can_read(second_timeline,key=KEY))

    def test_owner_public_timeline_cannot_issue_provider_grants(self):
        control = self.p.create('alice', 'not-provider-control', True)
        with self.assertRaisesRegex(ValueError, 'INVALID_CONTROL_TIMELINE'):
            self.p.create_access('alice', [self.t], [KEY], 'invalid-control', control, 10)

    def test_access_update_retry_is_idempotent_after_restart(self):
        control, keys, access, _ = self.private()
        entry = self.p.update_access('alice', access, [self.t], [], 'revoke', 20)
        resumed = ModelProvider(self.e, snapshot=json.loads(json.dumps(self.p.snapshot())))
        repeated = resumed.update_access('alice', access, [self.t], [], 'revoke', 50)
        self.assertEqual(self.e.identity(entry), self.e.identity(repeated))
        self.assertFalse(resumed.can_read(self.t,key=KEY))

    def test_cross_timeline_tie_requires_strictly_later_bound(self):
        from reference import next_input
        a = self.entry(100)
        c = self.v.range(self.p.seal(self.t, 101), [a])
        other = self.p.create('bob', 'tie-other', public=True)
        lower = self.v.range(self.p.seal(other, 100), [])
        with self.assertRaisesRegex(ValueError, 'WAITING_FOR_COVERAGE'):
            next_input(self.e, [a], [c, lower])
        upper = self.v.range(self.p.seal(other, 101), [])
        self.assertEqual(next_input(self.e, [a], [c, upper]), a)


class StreamTests(ProtocolFixture):
    pass


def stream_fixture(self):
    a = self.entry(110)
    feed = self.p.create('__provider__', self._testMethodName + '-feed', public=True)
    stream = self.e.typed('Timeline Update Stream', provider=ref(self.p.pid), generation=1, timeline=ref(self.e.identity(feed)))
    binding = self.e.typed('Timeline Stream Binding', timeline=ref(self.e.identity(self.t)), stream=ref(self.e.identity(stream)), timelineTag='aa' * 32, fromInclusive=100, untilExclusive=200)
    salt = 'bb' * 32
    row = {'type': 'Coordination/Timeline Announcement', 'timelineTag': 'aa' * 32, 'timestamp': 110, 'entryCommitment': commitment(self.e.identity(stream), 'aa' * 32, 110, self.e.identity(a), salt)}
    batch = self.e.typed('Timeline Stream Batch', stream=ref(self.e.identity(stream)), sequence=0, fromInclusive=100, completeBefore=120, announcements=[row])
    entry = self.p.append('__provider__', feed, batch, 'batch-0', 130)
    return a, feed, stream, binding, salt, row, entry


def test_stream_window_and_opening(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    facts = self.v.stream(binding, self.p.attest(binding), [self.p.attest(entry)])
    self.assertEqual((facts['fromInclusive'], facts['completeBefore']), (100, 120))
    self.assertEqual(len(facts['announcements']), 1)
    verify_opening(self.e, binding, row, a, salt)


def test_stream_empty_batch_advances(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    batch = self.e.typed('Timeline Stream Batch', stream=stream, sequence=1, fromInclusive=120, completeBefore=150, announcements=[])
    entry2 = self.p.append('__provider__', feed, batch, 'batch-1', 160)
    facts = self.v.stream(binding, self.p.attest(binding), [self.p.attest(entry), self.p.attest(entry2)])
    self.assertEqual(facts['completeBefore'], 150)


def test_stream_window_gap_rejected(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    batch = self.e.typed('Timeline Stream Batch', stream=stream, sequence=1, fromInclusive=121, completeBefore=150, announcements=[])
    entry2 = self.p.append('__provider__', feed, batch, 'batch-1', 160)
    with self.assertRaisesRegex(ValueError, 'STREAM_WINDOW_GAP'):
        self.v.stream(binding, self.p.attest(binding), [self.p.attest(entry), self.p.attest(entry2)])


def test_stream_last_block_without_prefix_rejected(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    batch = self.e.typed('Timeline Stream Batch', stream=stream, sequence=1, fromInclusive=120, completeBefore=150, announcements=[])
    entry2 = self.p.append('__provider__', feed, batch, 'batch-1', 160)
    with self.assertRaisesRegex(ValueError, 'CHAIN_GAP'):
        self.v.stream(binding, self.p.attest(binding), [self.p.attest(entry2)])


def test_stream_bad_salt_rejected(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    with self.assertRaisesRegex(ValueError, 'COMMITMENT_MISMATCH'):
        verify_opening(self.e, binding, row, a, 'cc' * 32)


def test_stream_wrong_source_opening_rejected(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    with self.assertRaisesRegex(ValueError, 'WRONG_TIMELINE'):
        verify_opening(self.e, binding, row, entry, salt)


def test_stream_binding_limits_coverage(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    binding['untilExclusive'] = 115
    facts = self.v.stream(binding, self.p.attest(binding), [self.p.attest(entry)])
    self.assertEqual(facts['completeBefore'], 115)


def test_stream_batch_timestamp_not_data_coverage(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    self.assertEqual(entry['timestamp'], 130)
    facts = self.v.stream(binding, self.p.attest(binding), [self.p.attest(entry)])
    self.assertEqual(facts['completeBefore'], 120)

for name, value in list(globals().items()):
    if name.startswith('test_stream_'):
        setattr(StreamTests, name, value)


# Additional adversarial stream fixtures use accepted, signed but invalid
# messages, proving that signatures do not replace semantic verification.
def test_stream_duplicate_announcement_rejected(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    batch = self.e.get(entry['message'])
    batch['announcements'] = [row, row]
    bad = copy.deepcopy(entry)
    bad['message'] = batch
    with self.assertRaisesRegex(ValueError, 'DUPLICATE_ANNOUNCEMENT'):
        self.v.stream(binding, self.p.attest(binding), [self.p.attest(bad)])


def test_stream_row_outside_window_rejected(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    batch = self.e.get(entry['message'])
    batch['completeBefore'] = 110
    bad = copy.deepcopy(entry)
    bad['message'] = batch
    with self.assertRaisesRegex(ValueError, 'ANNOUNCEMENT_OUTSIDE_WINDOW'):
        self.v.stream(binding, self.p.attest(binding), [self.p.attest(bad)])


def test_stream_wrong_generation_rejected(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    new_stream = copy.deepcopy(stream)
    new_stream['generation'] = 2
    changed = copy.deepcopy(binding)
    changed['stream'] = new_stream
    with self.assertRaisesRegex(ValueError, 'WRONG_STREAM'):
        self.v.stream(changed, self.p.attest(changed), [self.p.attest(entry)])


def test_stream_binding_is_not_self_authenticating(self):
    a, feed, stream, binding, salt, row, entry = stream_fixture(self)
    attestation = self.p.attest(binding)
    changed = copy.deepcopy(binding)
    changed['untilExclusive'] = 300
    with self.assertRaisesRegex(ValueError, 'WRONG_BINDING'):
        self.v.stream(changed, attestation, [self.p.attest(entry)])

for name, value in list(globals().items()):
    if name.startswith('test_stream_'):
        setattr(StreamTests, name, value)

if __name__ == '__main__':
    unittest.main()
