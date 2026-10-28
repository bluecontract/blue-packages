# Generated Activation operation inputs

The current `0.8.0-preview.3` candidate publishes standard native `request`
matchers for generated Activation operations. A shared authoring helper resolves
explicit library/function/argument links; dynamic generation copies those same
input definitions. Dispatch keys and authorized channels retain their native
identities.

Approval requires Integer `revision`. Negotiable approval additionally requires
Text `termsRef`. Descriptions identify the relevant authorized document state;
neither Core nor Business fills these fields during prepare or Confirm.
Party replacement does not gain a revision field. Negotiation operations publish
their actual proposal, terms-selection and change inputs, including inherited
optional fields and explicit native list representation.

Public adapters remove only their declared typed envelopes during native execution
before calling existing internal functions. They do not change the reviewed request
bytes sent by Business. Raw internal callers retain their existing interfaces.

The prior document-level `operationPreparation` entries, automatic bindings,
metadata ownership ledger and synchronization workflows have been removed from
newly generated documents. Existing immutable historical publications remain
unchanged; this change performs no automatic migration or history rewrite.

See [operation-input-coverage.md](operation-input-coverage.md) for the complete
34-package baseline and the additional explicit definition-read support protocol,
and [operation-input-qualification.md](operation-input-qualification.md) for native
qualification and byte-for-byte reproducibility. Package builds remain local
unpublished candidates until a separately authorized release.
