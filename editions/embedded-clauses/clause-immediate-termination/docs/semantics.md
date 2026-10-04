# Immediate termination: integration contract

## Parameters and phases

`Immediate Termination Terms` is passive proposed business data. Its required
`allowedParty` is `A`, `B`, or `EITHER`. A and B refer to the containing agreement's
first and second principals, not arbitrary actors who happen to submit a request.
`EITHER` gives each principal a separate unilateral right. It does not give
outsiders permission and does not require both principals to act.

The executable `Immediate Termination Clause` is a separate managed document. It
must be installed by the containing agreement after approval, with the accepted
option, exact accepted terms ID and round, agreement ID/type, and both principal
actors and authenticated channels. Initialization creates OPEN. The first
permitted call changes it to TERMINATED. Initialization of a standalone clause
cannot itself establish that any other agreement approved that right.

## Operations

| Operation | Channel | Permitted `allowedParty` |
|---|---|---|
| `terminateA` | `partyA` | `A` or `EITHER` |
| `terminateB` | `partyB` | `B` or `EITHER` |

The Operation Request targets the managed clause document. Its `request` contains
`requestId`, the accepted `termsId`, and optional textual `reason`. Additional
request fields are rejected. In particular, a caller cannot select an actor using
a `party` field. The operation supplies the side; Coordination authenticates the
Timeline actor against the channel.

A successful operation retains a termination record containing agreement ID,
party, actor, request ID/hash, accepted terms ID/round, approved permission,
optional reason, event timestamp, and original processing-event identity. It
emits `Termination Exercised` once.

Submitting the same request, with the same side, ID and exact body, has no second
business effect. Altering the body under the same ID is rejected. A new request
after termination is also rejected. These are business semantics; the host may
still record a new input disposition or checkpoint for a repeated delivery.

## Parent responsibilities

The containing agreement must consume genuine completed embedded-child progress,
not arbitrary external messages bearing the same event type. Before committing
termination it must establish the known clause type, embedded path, agreement
context, parties, channels, accepted revision, approved permission, completed state
and matching notice. Only then can it change its own phase and emit
`Agreement Terminated`. The Reseller package supplies this explicit composition.
Adding a passive term to an unrelated agreement does not install this behaviour.

The event records an immediate authorized outcome, not a request for counterparty
acceptance. No proof of cause, waiting period, or second signature is required.
Business termination does not stop Contracts processing, erase evidence, cancel
orders, discharge payments, or establish jurisdiction-specific legal effect.

## Tests

`tests/test_terms.py` checks valid options and rejects missing, unknown and
wrongly typed values through the actual Language facade. The sibling Reseller
package's acceptance suite exercises signed calls, A/B/EITHER permissions,
revision binding, failed actor impersonation, duplicate semantics, and parent
propagation. `VERIFICATION.md` in the overlay states which tests were executed;
the Codex prompt specifies additional application and adversarial coverage.
