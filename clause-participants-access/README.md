# Participants with Access

An initial portable clause for confirmed provider access. Supply `parameters.participants`, `parameters.accessPaths` and `bindings.state`. Access documents must first be imported with verified publication history. Each participant contains a current Coordination `channel` and an optional `readerKey`.

Put `AccessParticipants / Require Participant Access` first in every protected operation, with `constants.clauseKey` naming this clause. The clause updates the bound status on provider changes; it does not silently rewrite other clauses or every operation in the document. Loss of the processor’s own key also blocks native processing until access recovers.


Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.
