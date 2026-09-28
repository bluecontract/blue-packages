"""Atomic state, Coordination audit, input receipt and public outbox publication.

The database is a trusted local adapter, not an authority proof for remote peers.
"""
from __future__ import annotations
import json
import sqlite3
from blue_contracts import export_snapshot, import_snapshot
from blue_contracts.reference.model import digest, canonical, Meter
from .model import require

class Store:
    def __init__(self, path, processor):
        self.processor = processor
        self.db = sqlite3.connect(str(path), isolation_level=None)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS heads(slot TEXT PRIMARY KEY, identity TEXT NOT NULL, package TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS commits(request TEXT PRIMARY KEY, slot TEXT NOT NULL, binding TEXT NOT NULL, receipt TEXT NOT NULL, audit TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS outbox(ordinal INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, slot TEXT NOT NULL, event TEXT NOT NULL, acknowledged INTEGER NOT NULL DEFAULT 0);
        ''')

    def close(self):
        self.db.close()

    def initialize(self, slot, snapshot):
        package = export_snapshot(self.processor, snapshot)
        self.db.execute('INSERT INTO heads VALUES(?,?,?)',
                        (slot, snapshot.identity, json.dumps(package, ensure_ascii=False)))

    def load(self, slot):
        row = self.db.execute('SELECT identity, package FROM heads WHERE slot=?', (slot,)).fetchone()
        require(row is not None, 'UNKNOWN_SLOT')
        return import_snapshot(self.processor, json.loads(row[1]), row[0])

    def recorded(self, request):
        row = self.db.execute('SELECT slot,binding,receipt,audit FROM commits WHERE request=?', (request,)).fetchone()
        return None if row is None else {'slot': row[0], 'binding': row[1], 'receipt': row[2], 'audit': json.loads(row[3])}

    def commit(self, slot, request, decision, outcome, *, gas_limit=100000, local_limits=None, fail_before_commit=False):
        require(outcome.commits and decision.status == 'READY'
                and decision.snapshot == outcome.input_identity, 'INVALID_COMMIT')
        # The local caller obtained outcome from Coordinator.execute. Compare
        # every bound cause and the public result, rather than accepting counts.
        require(outcome.input_identity == decision.plan.snapshot
                and decision.entry == decision.plan.envelope.event, 'COMMIT_CAUSE_MISMATCH')
        gas_policy=Meter(gas_limit,local_limits).policy()
        expected_invocation = digest('contracts.invocation/event-1', {
            'input': outcome.input_identity, 'event': decision.entry,
            'timestamp': decision.plan.envelope.timestamp,
            'gas': gas_policy, 'release': self.processor.registry.specification})
        require(outcome.invocation == expected_invocation, 'COMMIT_INVOCATION_MISMATCH')
        package = export_snapshot(self.processor, outcome.snapshot)
        record = {'decision': decision.wire(), 'decisionIdentity': decision.identity,
                  'observations': outcome.observations(), 'receipt': outcome.receipt, 'gasPolicy':gas_policy}
        binding = digest('coordination.commit-request/1', {'slot': slot, 'decision': decision.identity,
                                                          'receipt': outcome.receipt})
        self.db.execute('BEGIN IMMEDIATE')
        try:
            prior = self.recorded(request)
            if prior is not None:
                require(prior['slot'] == slot and prior['binding'] == binding,
                        'IDEMPOTENCY_CONFLICT')
                self.db.execute('ROLLBACK')
                return 'ALREADY_COMMITTED'
            row = self.db.execute('SELECT identity FROM heads WHERE slot=?', (slot,)).fetchone()
            require(row is not None and row[0] == outcome.input_identity, 'COMPARE_AND_SWAP_CONFLICT')
            self.db.execute('UPDATE heads SET identity=?,package=? WHERE slot=?',
                            (outcome.snapshot.identity, json.dumps(package, ensure_ascii=False), slot))
            self.db.execute('INSERT INTO commits VALUES(?,?,?,?,?)',
                            (request, slot, binding, outcome.receipt, json.dumps(record, ensure_ascii=False)))
            for event in outcome.public_events:
                self.db.execute('INSERT INTO outbox(id,slot,event) VALUES(?,?,?)',
                                (event['identity'], slot, json.dumps(event, ensure_ascii=False)))
            require(not fail_before_commit, 'INJECTED_STORAGE_FAILURE')
            self.db.execute('COMMIT')
            return 'COMMITTED'
        except BaseException:
            if self.db.in_transaction:
                self.db.execute('ROLLBACK')
            raise

    def pending(self):
        return [json.loads(row[0]) for row in self.db.execute(
            'SELECT event FROM outbox WHERE acknowledged=0 ORDER BY ordinal')]

    def acknowledge(self, occurrence):
        self.db.execute('UPDATE outbox SET acknowledged=1 WHERE id=?', (occurrence,))
