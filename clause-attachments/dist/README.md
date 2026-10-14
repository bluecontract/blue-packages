# Explicit document attachments (unpublished candidate)

This library connects an agreement to an independently processed instruction. Payment and shipment policies share the same relationship, identity and hook rules.

## Intended contract

- Prepare a request containing the complete parent party roster, exact primary channels and keys, selected instruction terms and hooks.
- Workflow hooks execute on the instruction. Parent-state hooks require a reciprocal embedded reference and consume an explicit parent signal through an Embedded Node Channel. Parent-driven hooks wait until the parent has selected this instruction. A declared `recheckOn` also reevaluates current state when a local instruction field changes.
- A bank instruction is attached by the payer; a card instruction is attached by the merchant. Manual instructions can be constructed from the agreed template. The payment institution still owns financial responses.
- Attachment checks the instruction type, terms, request identity, installed hook policy and every parent party's primary channel and keys. Primary key lists must be nonempty and contain no duplicates; their order is immaterial. Representatives are independently chosen; they do not substitute for primary identity.
- Reciprocal attachment additionally requires the instruction's authority party (guarantor or carrier) in the parent, with matching primary identity, current access and required approvals.
- Adding a party and granting timeline access are separate, explicit actions. A descriptor claiming permission is not permission. Timeline Access documents provide the existing read-grant mechanism; native Mandates retain their separate operation-delegation semantics.
- Repeated identical attachment is idempotent; replacement, wrong actor, stale request, missing access and wrong reciprocal parent must fail without partial effects.
- Parent signals can request an instruction action, but cannot fabricate bank or carrier outcomes.

Sources and executable tests define the implemented subset; this candidate is not a live bank, card processor or shipping integration.

Preparation also publishes a compact `requirements` snapshot for a UI or agent:
the expected instruction type, terms, primary party identities, attaching role,
authority-admission rule and declared parent dependencies. This describes the
reviewed request, not a live permission or financial-readiness flag. The complete
source and `documentBlueId` remain authoritative.

## Preparation facade

`Payment Preparation Clause`, `Shipment Preparation Clause` and `Document
Preparation Clause` use the same preparation lifecycle. An authorized workflow
or local business event freezes a correlated requirement. `obtain: create`
constructs the child locally; `obtain: provide` asks `suppliedBy` for an initialized
instance of that exact source. Explicitly mapped `fieldPaths` can parameterize
business terms at preparation time.

The provider workflow retains a validated candidate while admission is pending.
An ordinary Amendments clause approves the exact candidate, authority profile and
Activation revision. Admission still requires real read access and fresh
Activation consent; reciprocal attachment still requires the actual reverse link.
The adapter uses the existing Activation functions and does not redefine timeline
access or Mandate delegation.

Preparation state and correlated events distinguish requests, pending work and
completed attachment. `ready` does not mean payment or shipment completion.
One clause owns one obligation. Collections, arbitrary provider extensions,
replacement/cancellation and provider API integrations are outside this iteration.
See `examples/preparation` in the source repository for twelve complete examples
and the quick sheet. Existing low-level attachment clauses remain available.
