# Clauses

Portable, event-driven composition of independently authored clauses. `/clauses` remains authoritative. Add, update and remove through the common listener; compose shared channels, workflows and multiple embedded collections.

See SPECIFICATION.md for the current protocol and COMPOSITION.md in the source bundle.


Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.


Identity-sensitive channel and contract reconciliation compares exact Blue
identities (`$nodeBlueId`), including authored declarations and captured effective
views. Existing identical declarations are accepted and unchanged contracts are
not rewritten. Absent contracts are installed; different exact declarations keep
the existing conflict behavior. Pending activation channels may be refreshed and
replaced by their admitted transport. This does not change BEX structural equality.
