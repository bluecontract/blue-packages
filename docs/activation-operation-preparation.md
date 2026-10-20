# Generated approval inputs

Activation `0.8.0-preview.2` publishes the input contract for each dynamically
generated approval operation. The exact dispatch key and executor are unchanged.
The request always requires Integer `revision`. If the candidate clause enables
negotiation with a nonempty `negotiation.allowedPaths`, it also requires Text
`termsRef`, matching the executor's existing checks. Non-negotiable approvals do
not gain this extra input.

`approvalPreparation` builds both the request matcher and version 1
`operationPreparation.operations` entry from the same authoring parameters.
Planning passes the candidate configuration; runtime roster regeneration passes
the installed clause configuration. The technical bindings read
`/activation/revision` and, when required, `/activation/terms/ref`. The latter is
the existing canonical reference stored by `initializeTerms` and updated by the
negotiation lifecycle. Preparation does not calculate replacement terms or
invent a business decision.

Synchronization follows clause initialization, accepted amendments and party
changes. The existing initialization refresh remains in place. The document
dispatch policy permits the three generated internal triggered channels while
inactive, alongside its existing initialization channel; this does not authorize
external operation calls or bypass access checks for business actions.

`activation.preparationOperations` records owned metadata. Synchronization
checks the complete generated operation's canonical identity, preserves unrelated
entries, removes only unchanged owned entries and rejects conflicts. An
identical preexisting foreign entry is retained without claiming ownership.
Revision and terms-reference changes do not require rewriting a binding pointer.

Existing immutable `0.8.0-preview.1` publications and documents remain unchanged.
They do not acquire a matcher or metadata retroactively. This edition introduces
no automatic clause replacement, migration or history rewrite. The prior
`0.7.0-preview.1.finalgas.2` compatibility fix is a separate package family.

The new dependency closure contains Activation, Documents, Payment, Shipping,
Inspection, Attachments, ACME, ManualPayments and MyOS. Only Activation authored
BEX changes; other packages receive new versions and dependency identities.
All remain unpublished candidates until an independently authorized release.
