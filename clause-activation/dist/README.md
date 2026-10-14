# Activation

Authored native Blue proposal package. See the top-level evidence and catalogue for tested scope. No JavaScript business interpreter.


Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.


## Owner-mediated party admission

An approved admission can emit `Party Addition Requested` with its exact
`admissionRef`, `expectedRevision`, new `parties`, `itemPath` and `clauseKey`.
Activation compares the proposed roster's reader groups with its current access
witnesses. It emits a separate `Party Access Update Requested` for each existing
party with missing access and retains those requests under
`/activation/accessRequests/<admissionRef>`.

These events request owner action. They are neither access evidence nor approval
to impersonate the owner. An account adapter may perform the requested grant
under that owner's settings; manual approval remains possible. The request's
`expectedAccessEntry` identifies the observed history state, so a delayed grant
must not overwrite a later revocation. Readiness is recomputed only from native
Timeline Access documents after their embedded update events.

Admission approval, owner grants, newcomer consent and final roster installation
remain separate. `Documents` waits for the required checks before calling the
native admission operation and proceeding to linking/embedding. Losing existing
required access still blocks direct requests; genuine embedded access updates
can recover it. A successful account-side grant response does not activate the
document by itself.
