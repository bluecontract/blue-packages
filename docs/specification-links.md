# Specification references

Native type sources explicitly identify their normative rules Text with
`specification: {blueId: ...}`. The package's protocol descriptor is a separate
Blue document describing those rules and exact native dependencies. Its ID
is not a substitute for the rules Text ID.

The current builder rejects native sources without an explicit rules reference,
rejects a reference that differs from the selected protocol rules, and checks
`spec/frozen.json` before construction. Ordinary business packages compose
existing types and do not invent native protocols.

Archive integrity, package dependency closure, reproducible source builds and
explicit Java native approval are separate checks. See [publication guidance](publishing.md)
and [consolidation notes](consolidation.md). Frozen historical publications
retain their original specification identities for replay.
