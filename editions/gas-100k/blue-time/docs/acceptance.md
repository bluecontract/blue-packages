# Qualification

The executable tests are in the MyOS checkout. `./blue-package test` runs them.
The package's preserved 0.1 Python fixture is historical evidence only. No current
Python-native implementation or cross-language parity is claimed.

`CoordinationTimeTest` exercises strict deadlines, exact logical timestamps,
keyed replacement/cancellation, equal-time common ordering, trusted inclusive
completeness, late earlier cancellation, rollback, pause/resume, removed channel
generations, multiple simultaneous timers, forged Timeline payloads, failed and
unmatched terminal inputs, child propagation, dependent operations, and cycles
that later split.

`TimeIntegrationTest` exercises real-clock idle timelines and SQLite process death
before/after registration and before/after firing commits. The subprocess is halted,
not cleanly shut down. On reopening, both transitions must occur exactly once and
retain their original requested timestamp differences.

MyOS uses the same conditional publication interface for SQLite and DynamoDB.
Live AWS verification exercises its DynamoDB journal. Local kill-window testing
is SQLite-specific; it is not proof of every possible infrastructure outage.
Host overload can delay observation. Safety requires trustworthy clock and source
completeness, as it does for the selected Coordination profile. Arbitrary dynamic
topologies and cross-language parity are not exhaustively proven by this suite.
