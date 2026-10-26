# Payment clauses

In the unpublished `0.8.0-preview.1` API, `Payment/Payment Clause` prepares or
receives one independent Payment Instruction. `Payment/Payments Clause` manages
keyed payment obligations. Both specialize the shared Documents lifecycle; the
instruction retains its own identity, parties, approvals and financial protocol.

## Authoring a payment

Declare a complete `parameters.template`, choose `parameters.obtain: create` or
`provide`, and map receiving roles explicitly in `bindings.parties`. For supplied
instructions, identify the authorized supplier with `parameters.suppliedBy` and
list any provider-filled roles in `parameters.suppliedParties`. Other business
terms remain fixed by the prepared requirement.

The singleton uses `bindings.instruction`; the collection uses
`bindings.collection`. Connect `prepare`, `provide` and `resume` to the appropriate
workflows or business events. A collection's stable key identifies the economic
obligation; a new request ID does not create another payment for an occupied key.

Preparation freezes the effective amount, currency, limit, financial roles and
conditional policy. Provision checks the original source, supplied slots and
current state. A candidate remains inert while required participant consent,
commercial approvals or access are missing. Attachment is not payment success.

## Choose the instruction's financial behavior

- A standard Payment Instruction supports authorization, capture, refund and void
  requests. Only its guarantor confirms the corresponding financial outcomes.
- `MyOS/MyOS Customer Payment Instruction` adds a provider-supplied funding session
  and payer action. Opening a session or requesting funding does not confirm it.
- `ACME/Bank Transfer Instruction` requests a direct transfer and records the bank's
  confirmation. It does not reserve or capture card funds.
- `ManualPayments/Manual Receipt Instruction` records a reported transfer and the
  recipient's acknowledgment. It makes no claim of independent bank settlement.

A conditional instruction uses its own process clause: `Payment/Payment Process
Clause` for capture, or `ACME/Bank Transfer Process Clause` for transfer. Conditions
read either local state or explicitly declared named sources. For live external
sources, the shared lifecycle checks identity, parties, consent and access before
making the relationship ready. A workflow trigger alone does not determine
whether cross-linking is required.

Payment completion comes from the instruction's native confirmed outcome. Preparing,
selecting, admitting or attaching a payment never establishes money movement.

## Earlier API and verification

`Payment/Legacy Payment Clause` retains the earlier start-and-observe facade in this
preview. Its `start`, `requestAuthorize`, `requestCapture`, `requestRefund` and
`requestVoid` bindings are not the new preparation API. Existing published editions
retain their exact identities.

The [clause tutorial](../docs/clauses-tutorial.md) documents the earlier connection
and domain facade examples; use the API distinction above when migrating. The
[payment protocol reference](../docs/payment-protocol.md) describes the instruction
protocol. Full hosted journeys, recovery and the complete application corpus are
still being qualified; package compilation alone does not certify those flows.
