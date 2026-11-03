# Customer Payment bootstrap composition

The payment-integration candidate restores the authored independent-bootstrap
preparation feature to the current Access Events source closure. This is needed
for an Order to prepare a standalone Customer Payment Instruction that the normal
Core bootstrap path can initialize and the Order can subsequently accept.

## Provenance and compatibility

Source implementation: `a0e1a0991f182f6ace9035fd443c519a25ea32c0`, with participant
and native access validation corrections from
`6161c9914d380fa7295aa3a151d1479d31325e73`. The feature had been absent from the
older Access Events source baseline selected by the later default-edition change.
The port uses authored `.blue` sources, not retained archives as execution imports.
Current source-reference preservation and Customer Payment session/capture policy
sources remain in place. Native Contracts, Coordination and runtime selection are
unchanged. The package tests use Access Events with DefinitionReadV1.

The opt-in `parameters.prepareFor: bootstrap` is accepted only with
`obtain: provide` and no inherited channels. It preserves mapped actor/readers
and representatives while preparing fresh child channels. Core performs ordinary
bootstrap separately. Provision validates matching actor/readers/representatives,
canonical initialized access proofs, and unchanged executable source policy.
Omitting `prepareFor` preserves inherited transport behavior. Other explicit
values are rejected. This does not grant access, bypass approvals, initialize a
child during preparation, or migrate existing documents.

The Parties access-record validation helper is extracted without changing its
existing path-based caller. Documents adds Bootstrap Preparation Functions and
mode-aware preparation/provision hooks. New version suffix `.bootstrap.1` applies
only to these packages and their 19 transitive import dependents. Exact dependency
identities are rebuilt together; mixed historical Payment/PI ancestry is invalid.
Existing retained publication bytes and deployed/default account runtimes are not
changed. Candidate consumers must select the complete new compatible closure.
No publication or deployment is performed by the local package build.

## Qualification boundaries

`tools/check_operation_inputs.py --case bootstrap-preparation` checks native
preparation, inherited behavior, idempotency, invalid input, participant identity
and access proof guards. Its historical assertions are retained. The Core
`OrderCustomerPaymentPreparationTest` provides the concrete pre-port failure:
the Stage 1 closure ignores `prepareFor`, while mixing the archived newer Payment
clause with Stage 1 MyOS fails Payment Instruction ancestry validation.

A green preparation test is not proof of a hosted checkout, provider execution,
Order settlement or Agreement Ledger settlement. These are separate Core/Business
integration gates. Check the accompanying run evidence for actual pass/fail state.
