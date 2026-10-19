## 16. Conformance claims

A provider qualifies the signature, append/seal/access, range and optional stream
interfaces it actually implements. An evidence verifier qualifies exact identities,
signatures, continuity, full-key ordering and strict completeness. A feeder qualifies
historical source selection, access/authority context, original-entry identity and
per-input dispositions. An executing host additionally qualifies sections 14–15
under its declared storage and ownership model. Passing one role does not establish
another. In-memory, SQLite, journal and remote durability claims are separate.

Qualification compares typed full results: state/graph, ordered events, native work,
checkpoints, completions, dispositions, selected runtime commitments, final gas,
first rejected charge, diagnostics and validated receipts. It includes Unicode
ordering, simultaneous source ties, frozen attach/detach/rebase, independent source
progress on receiver failure, real cyclic atomicity, terminal finite closure,
crash/restart, stale-fence publication, durable output retry and account isolation.
Warm/cold caches and alternate physical schedules must preserve those observations.
Timer-dependent cases are explicitly outside a non-timer claim. Missing resources,
unsupported histories and unexecuted cases are reported, never treated as passes.
