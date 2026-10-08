# Payment Instruction: explicit requests and guarantor responses

The `0.6.0-preview.4` payment family implements the public lifecycle as distinct Blue message types and named guarantor operations, following the supplied PayNote design. One Payment Instruction governs one transaction. It emits requests; an external guarantor executes or reconciles them and reports results through its admitted channel. Executing the Blue document itself never moves money or calls a banking API.

## What changed

Previously the public surface exposed `Payment Event` with `kind: Payment Requested` or `kind: Payment Outcome`, and the guarantor called `confirm` with an arbitrary outcome. New instructions expose `secureFunds`, `completePayment`, `declineCompletePayment`, `failCompletePayment`, `reverseAfterCompletion`, and the rest of the named operations below. Financial accounting remains shared BEX, but emitted messages have distinct exported Blue identities.

The common ancestors are `PaymentInstruction/Payment Request` and `PaymentInstruction/Payment Response`, both deriving from `PaymentInstruction/Payment Event`. A host Payment clause therefore continues to echo all protocol messages, preserving the exact inner type. The `kind`, `action`, `amountMinor`, and `outcome` projections remain available to existing policy/listener code; they are no longer the only way to distinguish messages.

## Client migration at a glance

| Previous call | New call |
| --- | --- |
| `accept` | `acceptPaymentInstruction` |
| `reject` | `rejectPaymentInstruction` with a reason |
| `initiate` | `recordTransactionInitiated` |
| `confirm` a successful securing request | `secureFunds` |
| `confirm` a successful capture request | `completePayment` |
| `confirm` a successful refund request | `reverseAfterCompletion` |
| `confirm` a successful cancellation request | `cancelBeforeCompletion` |
| `confirm` a declined capture | `declineCompletePayment` with a reason |
| `confirm` a failed capture | `failCompletePayment` with a reason |
| `confirm` an uncertain capture | `recordPaymentCompletionUnknown` with a reason |

Keep the recorded `requestId`; do not generate a new ID when retrying delivery of the same response. The operation now determines the outcome, so clients no longer send a free-form `outcome` selector.

## A complete exchange

A PI-local clause action can request completion after a customer operation or another bound trigger. `requestCapture` remains a convenient synonym for `requestCompletePayment`:

```yaml
requestCapture:
  acceptDelivery:
    on: workflow
    channel: customer
    params:
      requestId: {$var: {name: trigger, path: /requestId}}
      amount: {$var: {name: trigger, path: /amount}}
```

After policy and available-capacity checks, this creates a pending ledger entry, reserves the amount, and emits `PaymentInstruction/Complete Payment Requested` containing the request ID and amount. An external executor processes that request with the same idempotency identity. The guarantor then invokes:

```yaml
operation: completePayment
request:
  requestId: capture-001
```

The requested amount is read from the recorded request; the guarantor cannot confirm a different amount by supplying another value. The PI releases the reservation, changes the confirmed totals, and emits `PaymentInstruction/Payment Completed` with `amountCompleted`. A host listener can match the concrete inner event type:

```yaml
event:
  type: Payment/Payment Event Received
  event:
    type: PaymentInstruction/Payment Completed
```

These are connection/event-pattern fragments, not complete standalone documents. Runnable complete sources and input sequences are linked below.

## Guarantor operations

Every operation below is channel-restricted in generated Payment instructions. A response must match the action of the recorded request. For example, `completePayment` cannot settle a `Secure Funds Requested` request ID.

| Operation | Meaning / result |
| --- | --- |
| `acceptPaymentInstruction` | `PaymentInstruction/Payment Instruction Accepted` |
| `rejectPaymentInstruction` | `PaymentInstruction/Payment Instruction Rejected` |
| `recordTransactionInitiated` | `PaymentInstruction/Transaction Initiated` |
| `recordTransactionInitiationFailed` | `PaymentInstruction/Transaction Initiation Failed` |
| `secureFunds` | `PaymentInstruction/Funds Secured` |
| `declineSecureFunds` | `PaymentInstruction/Funds Securing Declined` |
| `failSecureFunds` | `PaymentInstruction/Funds Securing Failed` |
| `recordFundsSecuringUnknown` | `PaymentInstruction/Funds Securing Unknown` |
| `completePayment` | `PaymentInstruction/Payment Completed` |
| `declineCompletePayment` | `PaymentInstruction/Payment Completion Declined` |
| `failCompletePayment` | `PaymentInstruction/Payment Completion Failed` |
| `recordPaymentCompletionUnknown` | `PaymentInstruction/Payment Completion Unknown` |
| `cancelBeforeCompletion` | `PaymentInstruction/Payment Cancelled Before Completion` |
| `declineCancelBeforeCompletion` | `PaymentInstruction/Payment Cancellation Declined` |
| `failCancelBeforeCompletion` | `PaymentInstruction/Payment Cancellation Failed` |
| `recordPaymentCancellationUnknown` | `PaymentInstruction/Payment Cancellation Unknown` |
| `reverseAfterCompletion` | `PaymentInstruction/Payment Reversed After Completion` |
| `declineReverseAfterCompletion` | `PaymentInstruction/Payment Reversal Declined` |
| `failReverseAfterCompletion` | `PaymentInstruction/Payment Reversal Failed` |
| `recordPaymentReversalUnknown` | `PaymentInstruction/Payment Reversal Unknown` |
| `confirmPayeeAssignment` | `PaymentInstruction/Payee Assignment Confirmed` |
| `rejectPayeeAssignment` | `PaymentInstruction/Payee Assignment Rejected` |
| `confirmTransactionDetailsUpdated` | `PaymentInstruction/Transaction Details Updated` |
| `rejectTransactionDetailsUpdate` | `PaymentInstruction/Transaction Details Update Rejected` |
| `failTransactionDetailsUpdate` | `PaymentInstruction/Transaction Details Update Failed` |
| `resolveFinalAmount` | `PaymentInstruction/Final Amount Resolved` |
| `rejectFinalAmountResolution` | `PaymentInstruction/Final Amount Resolution Rejected` |
| `lockPaymentCompletion` | `PaymentInstruction/Payment Completion Locked` |
| `failPaymentCompletionLockChange` | `PaymentInstruction/Payment Completion Lock Change Failed` |
| `unlockPaymentCompletion` | `PaymentInstruction/Payment Completion Unlocked` |
| `lockPaymentReversal` | `PaymentInstruction/Payment Reversal Locked` |
| `failPaymentReversalLockChange` | `PaymentInstruction/Payment Reversal Lock Change Failed` |
| `unlockPaymentReversal` | `PaymentInstruction/Payment Reversal Unlocked` |
| `lockTransactionDetailsUpdate` | `PaymentInstruction/Transaction Details Update Locked` |
| `failTransactionDetailsUpdateLockChange` | `PaymentInstruction/Transaction Details Update Lock Change Failed` |
| `unlockTransactionDetailsUpdate` | `PaymentInstruction/Transaction Details Update Unlocked` |

## Control proposals and decisions

Recipient assignment, transaction details, final amounts, and locks have durable request/response exchanges. The standard Payment setup exposes these request operations on the payer channel. Custom lifecycle bindings can choose other authorized request routes. Requesting a change stores its proposal under `controlRequests`; it does **not** immediately change authoritative payment state.

```yaml
operation: requestPayeeAssignment
request:
  requestId: merchant-choice-1
  payeeRef: seller2
```

This emits `Payee Assignment Requested`. The proposed recipient must be predeclared in the PI. The guarantor calls `confirmPayeeAssignment` or `rejectPayeeAssignment` with that request ID. A successful decision applies the exact stored proposal. It resets recipient approval when the recipient changes. Assignment obeys the transaction-details lock and cannot change the recipient after confirmed or pending completion.

Likewise:

```yaml
operation: requestTransactionDetailsUpdate
request:
  requestId: details-1
  transactionDetails:
    merchantReference: invoice-173
    recipientTargetRef: merchant-account
    displayLabel: Consulting invoice
```

The guarantor uses `confirmTransactionDetailsUpdated`, `rejectTransactionDetailsUpdate`, or `failTransactionDetailsUpdate`. Accepted details are recorded as one object. A technical failure is distinct from a business rejection.

For final amounts, use `requestFinalAmountResolution` with `requestId`, `finalAmount` in minor units and `reason`; the guarantor uses `resolveFinalAmount` or `rejectFinalAmountResolution`. Accepted totals remain within the original limit and cannot undercut already completed or reserved completion amounts.

For each lock, request lock/unlock and wait for the named guarantor decision. A failed lock change leaves the prior lock state intact. The confirmed lock/unlock timestamp comes from the deterministic input timestamp (Unix microseconds), never the local wall clock. Locking does not undo an already emitted external request: late authoritative outcomes must still be reconciled.

## Correlation, retries and uncertainty

- Request IDs identify intent within an instruction. An identical request is a no-op; conflicting reuse is rejected. Financial and control requests cannot reuse each other's IDs.
- An exact duplicate final response is a no-op. Conflicting terminal results are rejected.
- `decline...` means the guarantor rejected the operation. `fail...` means a definitive execution failure. Both release the corresponding financial reservation.
- `record...Unknown` means execution is unresolved. It retains the reservation. Only reconciliation may resolve it; blindly creating a new request risks executing twice.
- Non-success financial responses require a reason. The existing retry policy still requires a definitive failed request and grants at most one retry entitlement for that failure.
- An instruction starts by emitting `Payment Instruction Acceptance Requested` with the natural request ID `acceptance`. Acceptance/rejection is terminal and mutually exclusive.
- `recordTransactionInitiated` attaches one transaction and its rail metadata. An identical report is idempotent; a different attachment is rejected. Initiation failures have their own request/attempt IDs and do not create a transaction.
- Confirmations use the amount reserved by the request. Partial completion is represented by a request for that smaller amount; a confirmation cannot silently settle a different amount. A cancellation request needs only its ID and reason: it pins the remaining secured amount on first admission, including zero before funds are secured. Cancellation closes further charges and releases the outstanding amount; it never erases a previously completed amount. An unresolved zero-value cancellation still blocks new charges.

## Public message catalogue

The two base envelopes and all concrete messages are exported directly by `payment-instruction/blue-package.yaml`. `Payment Instruction` replaces the PayNote name for acceptance messages; rail-neutral lifecycle vocabulary is preserved. Payee-assignment decisions and explicit unknown outcomes supplement the supplied PayNote catalogue.

### Requests

- [`Payment Instruction Acceptance Requested`](../payment-instruction/types/messages/payment-instruction-acceptance-requested.blue).
- [`Payee Assignment Requested`](../payment-instruction/types/messages/payee-assignment-requested.blue) — `payeeRef`.
- [`Transaction Details Update Requested`](../payment-instruction/types/messages/transaction-details-update-requested.blue) — `transactionDetails`.
- [`Secure Funds Requested`](../payment-instruction/types/messages/secure-funds-requested.blue) — `amount`.
- [`Complete Payment Requested`](../payment-instruction/types/messages/complete-payment-requested.blue) — `amount`.
- [`Cancel Before Completion Requested`](../payment-instruction/types/messages/cancel-before-completion-requested.blue) — `reason`.
- [`Reverse After Completion Requested`](../payment-instruction/types/messages/reverse-after-completion-requested.blue) — `amount`, `reason`.
- [`Final Amount Resolution Requested`](../payment-instruction/types/messages/final-amount-resolution-requested.blue) — `finalAmount`, `reason`.
- [`Payment Completion Lock Requested`](../payment-instruction/types/messages/payment-completion-lock-requested.blue) — `reason`.
- [`Payment Completion Unlock Requested`](../payment-instruction/types/messages/payment-completion-unlock-requested.blue) — `reason`.
- [`Payment Reversal Lock Requested`](../payment-instruction/types/messages/payment-reversal-lock-requested.blue) — `reason`.
- [`Payment Reversal Unlock Requested`](../payment-instruction/types/messages/payment-reversal-unlock-requested.blue) — `reason`.
- [`Transaction Details Update Lock Requested`](../payment-instruction/types/messages/transaction-details-update-lock-requested.blue) — `reason`.
- [`Transaction Details Update Unlock Requested`](../payment-instruction/types/messages/transaction-details-update-unlock-requested.blue) — `reason`.
### Responses

- [`Payment Instruction Accepted`](../payment-instruction/types/messages/payment-instruction-accepted.blue).
- [`Payment Instruction Rejected`](../payment-instruction/types/messages/payment-instruction-rejected.blue) — `reason`.
- [`Payee Assignment Confirmed`](../payment-instruction/types/messages/payee-assignment-confirmed.blue) — `payeeRef`.
- [`Payee Assignment Rejected`](../payment-instruction/types/messages/payee-assignment-rejected.blue) — `reason`.
- [`Transaction Details Updated`](../payment-instruction/types/messages/transaction-details-updated.blue) — `transactionDetails`, `payeeRef`, `recipientTargetRef`, `merchantReference`, `displayLabel`.
- [`Transaction Details Update Rejected`](../payment-instruction/types/messages/transaction-details-update-rejected.blue) — `reason`.
- [`Transaction Details Update Failed`](../payment-instruction/types/messages/transaction-details-update-failed.blue) — `reason`.
- [`Transaction Initiated`](../payment-instruction/types/messages/transaction-initiated.blue) — `transactionId`, `railType`, `attachmentPoint`, `providerReference`, `initiatedAmount`.
- [`Transaction Initiation Failed`](../payment-instruction/types/messages/transaction-initiation-failed.blue) — `reason`.
- [`Funds Secured`](../payment-instruction/types/messages/funds-secured.blue) — `amountSecured`.
- [`Payment Completed`](../payment-instruction/types/messages/payment-completed.blue) — `amountCompleted`.
- [`Payment Cancelled Before Completion`](../payment-instruction/types/messages/payment-cancelled-before-completion.blue).
- [`Payment Reversed After Completion`](../payment-instruction/types/messages/payment-reversed-after-completion.blue) — `amountReversed`.
- [`Final Amount Resolved`](../payment-instruction/types/messages/final-amount-resolved.blue) — `finalAmount`.
- [`Final Amount Resolution Rejected`](../payment-instruction/types/messages/final-amount-resolution-rejected.blue) — `reason`.
- [`Funds Securing Declined`](../payment-instruction/types/messages/funds-securing-declined.blue) — `reason`.
- [`Funds Securing Failed`](../payment-instruction/types/messages/funds-securing-failed.blue) — `reason`.
- [`Funds Securing Unknown`](../payment-instruction/types/messages/funds-securing-unknown.blue) — `reason`.
- [`Payment Completion Declined`](../payment-instruction/types/messages/payment-completion-declined.blue) — `reason`.
- [`Payment Completion Failed`](../payment-instruction/types/messages/payment-completion-failed.blue) — `reason`.
- [`Payment Completion Unknown`](../payment-instruction/types/messages/payment-completion-unknown.blue) — `reason`.
- [`Payment Cancellation Declined`](../payment-instruction/types/messages/payment-cancellation-declined.blue) — `reason`.
- [`Payment Cancellation Failed`](../payment-instruction/types/messages/payment-cancellation-failed.blue) — `reason`.
- [`Payment Cancellation Unknown`](../payment-instruction/types/messages/payment-cancellation-unknown.blue) — `reason`.
- [`Payment Reversal Declined`](../payment-instruction/types/messages/payment-reversal-declined.blue) — `reason`.
- [`Payment Reversal Failed`](../payment-instruction/types/messages/payment-reversal-failed.blue) — `reason`.
- [`Payment Reversal Unknown`](../payment-instruction/types/messages/payment-reversal-unknown.blue) — `reason`.
- [`Payment Completion Locked`](../payment-instruction/types/messages/payment-completion-locked.blue) — `lockedAt`.
- [`Payment Completion Unlocked`](../payment-instruction/types/messages/payment-completion-unlocked.blue) — `unlockedAt`.
- [`Payment Completion Lock Change Failed`](../payment-instruction/types/messages/payment-completion-lock-change-failed.blue) — `reason`.
- [`Payment Reversal Locked`](../payment-instruction/types/messages/payment-reversal-locked.blue) — `lockedAt`.
- [`Payment Reversal Unlocked`](../payment-instruction/types/messages/payment-reversal-unlocked.blue) — `unlockedAt`.
- [`Payment Reversal Lock Change Failed`](../payment-instruction/types/messages/payment-reversal-lock-change-failed.blue) — `reason`.
- [`Transaction Details Update Locked`](../payment-instruction/types/messages/transaction-details-update-locked.blue) — `lockedAt`.
- [`Transaction Details Update Unlocked`](../payment-instruction/types/messages/transaction-details-update-unlocked.blue) — `unlockedAt`.
- [`Transaction Details Update Lock Change Failed`](../payment-instruction/types/messages/transaction-details-update-lock-change-failed.blue) — `reason`.

## Composition and method packages

`Payment/Payment Clause` still creates the PI and echoes its events. `Payment/Conditional Payment` and the MyOS/ACME methods install the named guarantor operations into the PI, not the outer agreement. PI-local workflows, explicit host cycles, and shared evidence retain their existing placement rules. A guarantor does not gain authority over the host merely because it can report a PI result.

The MyOS customer-session protocol remains in `myos`; manual payer-report/recipient-receipt confirmation remains in `manual-payments`; ACME execution notifications remain in `acme-bank`. They reuse the new core protocol where applicable. The manual direct-transfer profile does not pretend that a recipient confirmation is bank authorization.

## Complete runnable examples

- [Explicit protocol document](../examples/payment-family/23-explicit-protocol.blue): a standalone PI, all named guarantor operations, participant request routes, and predeclared recipients.
- [Financial outcomes](../examples/payment-family/23-explicit-protocol.case.yaml): success, decline, definitive failure, unresolved execution and reconciliation for all four financial actions; wrong-operation rejection; duplicate handling; replay/restore checks.
- [Control exchanges](../examples/payment-family/24-control-protocol.case.yaml): recipient assignment, details, final amount, all locks/unlocks, failure, duplicate responses, blocked updates, initiation failure and recovery.
- [Instruction rejection](../examples/payment-family/25-rejected-instruction.case.yaml): rejection cannot be followed by acceptance or attachment.
- [Hosted control request](../examples/payment-family/26-hosted-control.case.yaml): a payer requests a completion lock through the standard generated PI; the host receives the typed request and confirmed result.
- [Cancellation before securing funds](../examples/payment-family/27-zero-cancellation.case.yaml): a zero-value cancellation blocks competing charges, closes the instruction, and remains idempotent after completion.
- [Customer-accepted payment](../examples/payment-family/01-simple-payment.blue) and [input sequence](../examples/payment-family/01-simple-payment.case.yaml): the simple authoring experience, including assertions that concrete PI response types survive host echo.

## Compatibility and qualification

This is a new unpublished preview, not an in-place rewrite of existing instruction identities. Core retains prior package archives; existing documents keep their exact package dependencies. Newly authored instructions use the new operations. Integrations calling `confirm`, `accept`, or `initiate` must migrate to the named operations before selecting the new package set. Existing short request-action names are preserved.

The authored Blue/BEX files are the implementation. The package builder only packages those sources. No runtime JavaScript generator implements the protocol. Local tests exercise document behavior and a test guarantor; they do not certify any live payment provider or claim exactly-once external banking execution. This change does not deploy AWS or migrate existing documents.
