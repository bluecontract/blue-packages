# Reseller agreement preview

`adventures-in-paradise-preview.blue` is one configured agreement between Adventures in Paradise and Manatee Bay Inn. Its document contains the parties, business terms, catalog, order and payout templates, and clause bindings. Executable order, negotiation, commission and payout behavior lives in the exported `clause-reseller/types/` definitions.

These examples qualify the maintained catalog-priced `Customer Orders Clause`
from main. They are not alternate versions of MyOS hosted checkout. The current
hosted reseller flow uses `Customer Orders Bootstrap Clause`; see
[Hosted reseller checkout](../../clause-reseller/README.md#hosted-reseller-checkout)
for that boundary and its native component tests. Neither this example nor a
package build proves a completed Stripe payment.

## Clause configuration

- `Customer Orders Clause` reads the template, order collection, catalog and optional fulfilment parameters through pointer bindings. Moving or renaming these fields requires updating a binding, not copying implementation. Removing the fulfilment clause removes the date and confirmation requirement from new orders.
- `Commercial Terms Negotiation Clause` invalidates earlier approvals when terms change before activation. Both parties must approve the resulting version. `Commercial Terms Validation Clause` checks the commission range and this example's USD currency.
- `Commission Clause` reads confirmed net payment results and the configured commission rate. `Commission Payouts Clause` prepares a payout and reserves its amount once. A payout document is not evidence of a completed transfer.
- `Catalog Clause` owns the authored offer description and points to the catalog. These agreements do not configure a separate quote collection. Descriptive content does not introduce executable booking requirements.

## Independent customer orders

The exported Customer Orders Clause specializes `Documents/Documents Clause`. The partner calls `prepareOrder` once with a typed `Documents/Preparation Input`: `key`, `requestId` and `values` containing `catalogRevision`, `lines`, `description`, optional fulfilment `groups`, and exactly one of `customer` (account ID) or `customerEmail` (contact metadata). Each line selects an `itemId`, `quantity` and any catalog-required date or duration. The clause checks the current catalog revision, item membership and quantity/duration constraints, calculates prices and discounts using the shared Catalog Functions, and freezes the result in the prepared Order. Currency also comes from that catalog. Caller-supplied amounts, prices, `quoteKey`, `orderAccess` and prepared fields are rejected.

There is no `createQuote` operation or `/quotes` collection in these three agreements. The Order retains its calculated line breakdown under `quote` and its exact identity under `quoteBlueId`, as required by the existing fulfilment snapshot contract; these fields are calculation evidence, not a separate quotation workflow. A new preparation uses current prices and rejects a stale revision. Repeating the same preparation returns the existing result without repricing it; conflicting reuse is rejected.

In preview.4, `values.customerEmail` retains its exact 1–320 character text under `/customerEmail` in the prepared Order, without an account pin. The customer Party stays supplied at bootstrap. Business authorizes and retains the checkout-to-actual-account association, then uses the ordinary bootstrap participant mapping, such as `{channelName: customer, email: guest@example.test}`. The email is contact/correlation metadata, not verified identity. Provision checks the actual initialized/current customer and requires an account distinct from seller and partner. The existing `values.customer` branch still freezes `/customerAccountId` and requires that account at provision. Earlier exact package editions retain their original behavior.

Handle `Documents/Document Provision Requested` for the orders clause, bootstrap the exact `requirementRef` using the seller, partner and customer account mappings, then call `provideOrder` as partner with `key`, `inResponseTo`, `requirementRef` and `document: {blueId: ...}`. Native Documents validates the mapped parties and their representatives against the fresh transports before linking the independently hosted Order. An identical preparation or provision is idempotent; conflicting reuse is rejected. The retained `newOrder` operation is a preparation alias, no longer an embedded factory.

The Adventures in Paradise example has two catalog lines in one order: two child tickets at USD 49 and one free infant ticket. Its frozen quote totals USD 93.10 after a USD 4.90 discount. `massage-preview.blue` and `watersports-preview.blue` configure the same clauses for the other review examples.

`bootstrap-preparation.case.json` checks direct multi-line pricing, invalid selections and stale revisions, absence of stored quotes, cold-restore retries and rejection of forged amounts/access. The older `preview-booking`, `preview-card` and `preview-multi-item-order` cases describe the former embedded factory and are not qualification for this independent bootstrap edition. Hosted bootstrap, representative channels and PI provision are qualified separately in the Core integration branch.

## Card Payment Instruction

The order uses the existing `Payment/Payment Clause`, with `obtain: provide`, `suppliedBy: seller`, an immediate one-shot preparation after native Order initialization and seller-only `providePayment`. The PI template uses `PaymentInstruction/Payment Instruction with Clauses` and `Payment/Payment Process Clause` with `method: card`. Its amount, limit and currency are mapped from the created order; a zero-price order has no payment clause or PI.

The example follows MyOS Core's `examples/independent-processes/corpus/payments/12-agreement-orders-payments.blue` for party bindings and `14-existing-authorized-card-pi.blue` for the card process. `payments@example.test` is the example MyOS account constrained in the PI template’s guarantor declaration. The guarantor is a supplied party at bootstrap, so no channel from another document is copied. It is not a production payment service. Replace it with the admitted guarantor account for an actual integration; the guarantor does not become a party to the reseller agreement.

Orders do not require a second customer approval. The cancellation-enabled Agreement requires seller acceptance (`required: [seller]`), which also confirms the proposed dates through its Confirmation Clause. The earlier preview agreements retain `required: []` and separate date confirmation. The Payment Clause uses `prepareFor: bootstrap`; its prepared PI must receive fresh participant transports through Core bootstrap. Access and exact party matching remain required.

The integration must handle `Documents/Document Provision Requested`, retrieve the prepared document identified by `requirementRef`, bootstrap it, and call `providePayment` as seller with the original `inResponseTo`, `requirementRef`, and the bootstrapped document reference. Deduplicate bootstrap by the originating document and preparation correlation; reuse the same PI when retrying. The native scenario exercises provision validation and a repeated response. It does not implement or qualify a hosted provisioning handler.

`Payment Observation Clause` reuses the existing Payment Base's event relay behavior to expose native PI events to the containing order. Commission continues to depend on confirmed receipts and reversals, not preparation or attachment.

## Local verification and preview

Run the selected cases with `tools/run_reseller.py`, a qualified `BLUE_JAVA_CLASSPATH` and `JAVA_HOME`. `bootstrap-preparation.case.json` covers the current independent Order preparation; `cancellation-settlement.case.json` qualifies native settlement and retries. The older preview cases retain evidence for the former embedded factory, not the current hosted flow.

The local generated document, clause definitions, semantic cards, Overview and Terms are in `reports/reseller-20261103/business-preview/index.html`. These are local review artifacts, not a deployed agreement or proof of real card processing.

The `onOrderCreated` binding uses `on: timer`, `timestamp: 0` and requires the
initialized marker and an empty preparation registry. The PI retains the Order
as a named source, so preparing it inside Order initialization is too early:
that source does not yet have a native process origin. The timer starts the same
prepare step immediately after initialization, without customer approval or a
manual payment action. The Activation configuration permits the timer and its
arming channel while ordinary consent and access requirements remain in force.

The [cancellation-enabled Agreement](cancellation-enabled-agreement.blue) adds
Order settlement observation and the PI cancellation reconciliation clauses.
The automatic preparation was qualified on Core 64abcd6de with the current
package selection: one multi-product Order of 93.10 USD initialized and prepared
exactly one PI. The former `on: initialized` version fails Order initialization.
The cancellation-enabled example requires seller acceptance through
`approve_seller`, with the current Activation revision and exact reviewed document.
Its PI requests full capture when the Order is active and authorization is available.
An embedded Order event or a payment state change can wake this request, so either
acceptance or authorization may arrive first. Its Confirmation Clause binds
`confirmAcceptance` to `Activation/Terms Accepted` for the seller. In the same
atomic transition, pending groups receive their exact proposed start as the
confirmed start. Different groups may have different dates. A passed start,
expired response deadline, or outstanding customer consent rejects the entire
approval, including Activation, all group changes and payment effects.
An alternative date or an immediate cancellation charge still needs the existing
customer `acceptProposal` step; `confirmReservation` remains available to request
that consent before approval. Confirmed, fulfilled and cancelled/closed groups
are not changed or revived. Orders without the Confirmation Clause require no
date confirmation. `confirmReservation` and an optional customer approval do not
replace seller acceptance. Repeating acceptance does not create new confirmations
or a second capture request. The manual capture action applies the same Activation
and cancellation conditions.

Cancellation reconciliation retains its separate request path: a full-price
capture condition must not prevent collection of a valid cancellation fee.
The mandatory `paymentTerms.captureGate` points to
`/sources/order/activation/active`. Every capture route therefore waits for seller
acceptance, including collection of a retained cancellation charge. Cancellation
reconciliation additionally requires resolved groups before collecting that charge.
A cancellation before acceptance can release an authorization without approval.
The full-price request remains blocked once cancellation settlement has begun;
a late acceptance cannot revive it. Reciprocal document and frozen-terms checks
still apply in the managed provider.
Payment preparation freezes the native Order origin, revision and terms reference
in `businessContext`. The terms reference is a `Text` field: an empty object
cannot be refined with its string value. These template slots remain unfilled
until the Order exists; marking them required in the nested Agreement template
would reject that Agreement before preparation can supply them.
The payment process and top-level `sources/order` use the same Order type
declaration. Different declarations for that alias are rejected by Documents.
`tools/test_reseller_automatic_capture.py` uses the example's actual payment
and confirmation configuration with the native component fixture. Twelve cases
cover both orderings, multiple reservation groups and dates, atomic rollback,
alternative-date and immediate-charge consent, an Order without a date clause,
customer approval, stale or unauthorized seller approval, exact-review enforcement,
cold restoration, cancellation before capture, fee capture after a failed full-price
request, later recipient approval and rejection of conflicting source declarations.
The fixture calculates a basket using the retained legacy factory, then processes
the Order as its own native root. It uses the current `sourcePaths` configuration
and delivers the preparation's native source completion to the bootstrapped PI
before provision. Omitting that delivery imports an older Order occurrence instead
of joining the current Order/PI cycle. This is native component qualification,
not a qualification of the hosted Reader provisioning path.
Payment state changes also wake the capture binding, so a changed payment lock
or recipient approval cannot leave an otherwise eligible request asleep.
Separate local Business evidence on 9 November verified the previous,
reservation-confirmation-based multi-product flow:
partner preparation, independent Order bootstrap and provision, seller PI creation,
managed Test authorization of USD 93.10, seller confirmation, automatic capture,
customer cancellation, automatic full refund, settled Order and reversed commission.
Core used `2f44c4f1d` with the imported package selection from `766f39d`; Business
retains the browser ledger and results in `reports/cancellation-flow/`.
This is managed Test-provider evidence, not a real card or Stripe qualification.
