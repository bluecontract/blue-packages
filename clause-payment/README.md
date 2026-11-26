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

## Observe the selected instruction

Opt in to native payment events on `Payment/Payment Clause` by connecting its
`observe` action to the path declared by `bindings.instruction`.

```yaml
bindings:
  instruction: /payment
  observe:
    selectedPayment:
      'on': embedded
      path: /payment
      embed: false
```

`embed: false` observes the existing managed instruction link. Documents
retains ownership of selection and admission. The connection checks the native
delivery path against the instruction binding. It emits `Payment Event Received`
with the observing clause, instruction path and exact original event reference.
Without a connection the preparation clause emits no payment relay events.

When an instruction is selected after it has already recorded an outcome, use
the native Documents selection or attachment event to read its current state.
The observation is for native events from the selected link. Financial
projections should reconcile cumulative confirmed amounts.

`Payment/Payment Observation Clause` is the standalone observer and retains its
automatic connection at the bound instruction path.

## Reconcile Agreement receipts after access returns

Bind the Receipts Clause's optional `reconcile` action to the containing
Agreement's local `Parties/Document Access Restored` event.

```yaml
bindings:
  reconcile:
    afterAccessRestored:
      'on': event
      event: {type: Parties/Document Access Restored}
```

Dispatch uses the Agreement's usual access and activation policy. Restoration
sweeps the configured Order preparation entries once and uses each usable
Order's current, qualified Payment Instruction at the configured path.
Ordinary payment events and Order attachment still update only the affected
Order. Reconciliation emits a receipt change for each changed cumulative
target so the configured ledger can update the same corresponding obligation.

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

`Payment/Selected Order Capture` requires the original selected instruction
and the matching active Order revision and terms. This type supplies
`mode: when`. A capture configuration can
use `whenAlso` to add a condition to the supplied `when`. Both predicates read
statically declared paths and are enforced for every capture route.

For a standard MyOS customer instruction, the adapter reads
`paymentDetails.method: myos-customer`. The process clause's optional `method`
parameter retains its existing configuration checks and default.

## Adjust a selected payment

Declare an adjustment with the linked decision, the original payment
selection and the native request IDs. This example brings a paid amount
down to the price in an accepted correction.

```yaml
parameters:
  selectedPayment:
    source: /sources/order
    expectedSourceOrigin: /businessContext/orderOrigin
    entries: /sources/order/process_payment/entries
    path: /payment
    key: single
  adjustments:
    correction:
      decision:
        path: /sources/order/priceCorrection
        when: {field: status, equals: accepted}
        retainMinorFrom: retainedMinor
      requestIds: {refund: price-correction-refund}
bindings:
  adjust:
    afterDecision:
      'on': embedded
      path: /sources/order
      event: {type: Events/Event, name: Price correction accepted}
    afterSelection:
      'on': change
      path: /sources/order/process_payment/entries
    afterPaymentResponse:
      'on': event
      event: {type: PaymentInstruction/Payment Response}
```

One action can observe several declarations. Each adjustment can declare its
own complete `selectedPayment` to override the shared selector. A connection may set
`params.adjustment` to a specific name. Keep the identifiers stable for
each payment and decision. A missing retained amount or incomplete
selection leaves the request unchanged. The action waits for native
pending outcomes. It refunds confirmed net payment above the retained
amount, accounting for earlier refunds. When the retained amount and net
payment are both zero, a configured `void` releases the entire available
hold. Missing request IDs disable their respective actions. An explicit
`retainMinor: 0` is supported for a declaration with a void request only.

Use `capture.blockedBy` to name an adjustment whose accepted decision
must stop new capture. The request plan keeps the supplied capture
predicate and `whenAlso`. It can also require one published fact with
`capture.requires: {path: /sources/order/serviceStatus, equals: confirmed}`.
The adjustment itself only requests refund or void.

## Require secured funds before an action

`Payment/Secured Amount Condition` applies to the named actions in a
Connections condition group. Bind the selected managed Payment Instruction
and the current values being reviewed. The Payment Instruction must carry
the same frozen revision and terms reference.

```yaml
parameters:
  conditionGroups:
    fundedReview:
      type: Payment/Secured Amount Condition
      actions: [confirm, alternative, accept]
      inputs:
        instruction: /payment
        amountMinor: /amountMinor
        revision: /activation/revision
        termsRef: /activation/terms/ref
```

Use the live slot already selected by Documents. The condition reads that
instruction when the action runs. It requires an open instruction with no
pending cancellation and a secured balance covering the amount after the
capture and void reservations are deducted. Missing facts and review
mismatches fail the existing action condition before preflight or other
action effects.

`Payment/Secure Timestamp Projection` can connect its `record` action to a
native `PaymentInstruction/Funds Secured` event. Its `fact` binding names where
to retain `timestampMicros` and `requestId` for the first successful full
authorization. The timestamp comes from the guarantor's native operation and
remains available when the instruction is attached after authorization.

The Payment Process exposes pure helpers for authored request bindings.
`isSelectedPayment` compares the initialized source, the expected source,
the original obligation and the selected instruction. Pass the collection,
source, expected origin, path and key together under its `input` argument.
An incomplete link returns false. `refundAbove` returns
the confirmed net charge above the supplied target. `voidableFunds` returns
the current full hold. Both amount helpers return zero while outstanding
requests or locks prevent the adjustment. Connect the stock `requestRefund`
and `requestVoid` actions to issue requests with durable IDs. Financial
completion still comes from the guarantor's confirmed response.

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
