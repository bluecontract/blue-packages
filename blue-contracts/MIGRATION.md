# Final gas edition

The 2026-10-12 edition keeps deterministic tariffs, charge-before-work,
the 10,000,000 shared maximum, member-local ceilings and atomic rollback.
It removes accepted-charge rows from canonical evidence. Outcomes keep final
admitted gas and one compact rejection diagnostic; turns/units keep scalar gas.
Chunk verification still verifies execution, not a caller-supplied total.

This changes native specification, type, package and receipt identities. Select
the new edition explicitly for new documents. Do not reinterpret old snapshots,
receipts or pending invocations; retain their original runtime and packages.
Frozen `spec/contracts.md` records the preceding trace-bearing edition.
New normative rules are in `spec/contracts-final-gas.md`; the root specification
is an exact copy. Derived Python source overrides are listed in `docs/sources.json`.
