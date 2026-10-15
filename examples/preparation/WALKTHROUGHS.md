# Twelve executable preparation flows

These walkthroughs correspond to the numbered `.blue` sources and native tests.
Alice controls `customer`; Bob controls `seller`. The institution, carrier and
service provider are independent parties. Bootstrap each example with actual
primary timelines, keys and read grants. The example party declarations alone
are not deployable identities.

The common start input is `{requestId: purchase}`. In supplied-document flows,
read `/instructionRequest/document` and `/instructionRequest/documentBlueId`.
Obtain an initialized, active instance of that exact prepared source, then call
`provideDocument` as the configured supplier with:

```yaml
inResponseTo: purchase
requirementRef: <prepared source Blue ID>
document: {blueId: <initialized instance Blue ID>}
```

## 1. An agreed expense — local payment

Source: [01-manual-reimbursement.blue](01-manual-reimbursement.blue).
Alice calls `prepareDocument`. The host prepares and creates the EUR 2 Payment
Instruction, copies the primary parties and selects the initialized child at
`/instruction`. No external supplier or reverse link is needed. The child still
requires its own payment requests and institution confirmations; creation is
not evidence that money moved.

## 2. Course purchase — a business event starts payment

Source: [02-course-business-event.blue](02-course-business-event.blue).
Alice calls `confirmPurchase` with the request ID. The Features workflow emits
`Commerce/Domain Event` with `kind: Purchase Confirmed`. The preparation binding
consumes that local event and creates the PI. Business workflows can therefore
speak in business events without implementing attachment mechanics themselves.

## 3. Card payment — the host controls when capture is requested

Source: [03-card-existing-parties.blue](03-card-existing-parties.blue).
Alice starts preparation; Bob supplies the PI. The institution already belongs
to the host. The candidate remains pending until Bob calls its `attachDocument`
with the host reference and supplies the updated child. After authorization,
Alice's host `setReady` operation makes `/x` equal to 1 and the child requests
capture. Only the institution's `completePayment` records completed payment.

## 4. Buyer-arranged bank payment — forward embedding

Source: [04-buyer-bank.blue](04-buyer-bank.blue).
Alice starts preparation with the bank's real `authorityParty` profile, obtains
the active PI from that bank, and calls `provideDocument` herself. Matching
parties and source are checked. Because the child has no parent-dependent hook,
the bank need not join the host and no reverse link is needed. The example
models the instruction protocol; it does not call a banking API.

## 5. Local delivery — create a shipment

Source: [05-local-delivery.blue](05-local-delivery.blue).
Alice calls `prepareDocument`. The same lifecycle creates the shipment locally
and selects it after initialization and Activation. The carrier still owns
shipment confirmations. This reuses the attachment lifecycle without treating
shipment status as payment status.

## 6. Buyer-arranged collection — the buyer supplies a shipment

Source: [06-buyer-collection.blue](06-buyer-collection.blue).
Alice starts preparation, obtains an active shipment matching the prepared
source, and calls `provideDocument`. The host embeds it with a forward relation.
A buyer can choose the external execution route while the agreement retains
control over the required terms and participant identities.

## 7. Conditional dispatch — a shipment observes the host

Source: [07-carrier-cross-link.blue](07-carrier-cross-link.blue).
Alice starts preparation. Bob obtains the shipment, supplies it, creates its
reverse link to the host, and supplies the updated reference. Alice calls
`setReady`; the parent-dependent hook requests shipment. The carrier calls
`confirmShipment` with tracking details to record acceptance. The native test
checks both the host trigger and the carrier's separate confirmation.

## 8. Local work order — an ordinary document

Source: [08-local-work-order.blue](08-local-work-order.blue).
Alice calls `prepareDocument`. The host creates the prepared work order and
selects it using the same checks. There is no financial or shipment behavior
invented by the base clause. Domain-specific operations belong to the chosen
work-order template.

## 9. Inspection work order — supplied by the seller

Source: [09-provided-inspection.blue](09-provided-inspection.blue).
Alice starts preparation. Bob supplies the initialized, active inspection work
order using the common correlated response. A wrong request ID or prepared
source reference is rejected. Supplying the same accepted instance again is
idempotent. Provider-added arbitrary clauses are not accepted in this version.

## 10. Deposit and balance — two independent obligations

Source: [10-deposit-and-balance.blue](10-deposit-and-balance.blue).
Alice calls `prepareDeposit` with `{requestId: deposit}`, then `prepareBalance`
with `{requestId: balance}`. Each clause creates its own child and status.
The test checks that their origins differ. This expresses two known payments;
it does not pretend that a singleton clause is an unbounded order collection.

## 11. Card payment — admit a missing guarantor

Source: [11-card-admit-guarantor.blue](11-card-admit-guarantor.blue).
Alice starts preparation with the guarantor's primary profile. Bob supplies the
active PI. The clause holds it inert and proposes the exact admission amendment
as Bob, without granting any approval. Alice calls `approveBuyer`, then Bob
calls `approveSeller`, with `{proposalId: instruction_purchase}`.

`Amendment Applied` triggers the access and revision checks. Missing read grants
keep admission pending. After grants cover the expanded roster, an authorized
`resumeDocument` can retry it. Successful admission advances Activation; the new
guarantor calls `approve_guarantor` for the new revision (2 in this fresh
example). Existing required approvers would also need to approve that revision.
Bob then links the child back to the host and supplies the updated instance.
Only then can the host report attachment as ready.

The signed-timeline integration test also revokes a grant after attachment and
checks that the host becomes inactive. A past `ready` event does not override
ongoing authorization.

## 12. Shipment — admit a missing carrier

Source: [12-shipment-admit-carrier.blue](12-shipment-admit-carrier.blue).
The same sequence applies with the carrier profile, the shipment candidate,
the buyer and seller's amendment approvals, real read grants and
`approve_carrier`. Bob creates the reverse link and resubmits the shipment.
Payment-specific code is not responsible for this admission sequence: both
specializations reuse the shared lifecycle.

## What the tests prove

`DocumentPreparationTest` runs all twelve authored sources, including replay,
correlation rejection, preparation-time values, reciprocal links, real
Amendments operations and independent payment/shipment confirmation operations.
`DocumentAttachmentAccessTest` separately exercises signed timelines, SQLite,
real read grants, missing access, consent and revocation. These are local native
checks; they do not establish provider API integration, cross-host deployment,
agent UX, throughput or production readiness.
