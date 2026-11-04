# Reseller agreement preview

`adventures-in-paradise-preview.blue` is one configured agreement between Adventures in Paradise and Manatee Bay Inn. Its document contains the parties, business terms, catalog, order and payout templates, and clause bindings. Executable order, negotiation, commission and payout behavior lives in the exported `clause-reseller/types/` definitions.

## Clause configuration

- `Customer Orders Clause` reads the template, order collection, catalog and optional fulfilment parameters through pointer bindings. Moving or renaming these fields requires updating a binding, not copying implementation. Removing the fulfilment clause removes the date and confirmation requirement from new orders.
- `Commercial Terms Negotiation Clause` invalidates earlier approvals when terms change before activation. Both parties must approve the resulting version. `Commercial Terms Validation Clause` checks the commission range and this example's USD currency.
- `Commission Clause` reads confirmed net payment results and the configured commission rate. `Commission Payouts Clause` prepares a payout and reserves its amount once. A payout document is not evidence of a completed transfer.
- `Catalog Clause` owns the authored offer description and points to the catalog and quote collections. Descriptive content does not introduce executable booking requirements.

## Independent customer orders

The exported Customer Orders Clause specializes `Documents/Documents Clause`. The partner calls `prepareOrder` once with a typed `Documents/Preparation Input`: `key`, `requestId` and `values` containing `catalogRevision`, `lines`, `customer`, `description` and optional fulfilment `groups`. Each line selects an `itemId`, `quantity` and any catalog-required date or duration. The clause checks the current catalog revision, item membership and quantity/duration constraints, calculates prices and discounts using the shared Catalog Functions, and freezes the result in the prepared Order. Currency also comes from that catalog. Caller-supplied amounts, prices, `quoteKey`, `orderAccess` and prepared fields are rejected.

There is no `createQuote` operation or `/quotes` collection in these three agreements. The Order retains its calculated line breakdown under `quote` and its exact identity under `quoteBlueId`, as required by the existing fulfilment snapshot contract; these fields are calculation evidence, not a separate quotation workflow. A new preparation uses current prices and rejects a stale revision. Repeating the same preparation returns the existing result without repricing it; conflicting reuse is rejected.

Handle `Documents/Document Provision Requested` for the orders clause, bootstrap the exact `requirementRef` using the seller, partner and customer account mappings, then call `provideOrder` as partner with `key`, `inResponseTo`, `requirementRef` and `document: {blueId: ...}`. Native Documents validates the mapped parties and their representatives against the fresh transports before linking the independently hosted Order. An identical preparation or provision is idempotent; conflicting reuse is rejected. The retained `newOrder` operation is a preparation alias, no longer an embedded factory.

The Adventures in Paradise example has two catalog lines in one order: two child tickets at USD 49 and one free infant ticket. Its frozen quote totals USD 93.10 after a USD 4.90 discount. `massage-preview.blue` and `watersports-preview.blue` configure the same clauses for the other review examples.

`bootstrap-preparation.case.json` checks direct multi-line pricing, invalid selections and stale revisions, absence of stored quotes, cold-restore retries and rejection of forged amounts/access. The older `preview-booking`, `preview-card` and `preview-multi-item-order` cases describe the former embedded factory and are not qualification for this independent bootstrap edition. Hosted bootstrap, representative channels and PI provision are qualified separately in the Core integration branch.

## Card Payment Instruction

The order uses the existing `Payment/Payment Clause`, with `obtain: provide`, `suppliedBy: seller`, `prepare.onOrderCreated.on: initialized` and seller-only `providePayment`. The PI template uses `PaymentInstruction/Payment Instruction with Clauses` and `Payment/Payment Process Clause` with `method: card`. Its amount, limit and currency are mapped from the created order; a zero-price order has no payment clause or PI.

The example follows MyOS Core's `examples/independent-processes/corpus/payments/12-agreement-orders-payments.blue` for party bindings and `14-existing-authorized-card-pi.blue` for the card process. `payments@example.test` is the example MyOS account constrained in the PI template’s guarantor declaration. The guarantor is a supplied party at bootstrap, so no channel from another document is copied. It is not a production payment service. Replace it with the admitted guarantor account for an actual integration; the guarantor does not become a party to the reseller agreement.

Orders do not require a second customer approval (`required: []`). Seller date confirmation remains a separate operation when the Agreement includes fulfilment terms. The Payment Clause uses `prepareFor: bootstrap`; its prepared PI must receive fresh participant transports through Core bootstrap. Access and exact party matching remain required.

The integration must handle `Documents/Document Provision Requested`, retrieve the prepared document identified by `requirementRef`, bootstrap it, and call `providePayment` as seller with the original `inResponseTo`, `requirementRef`, and the bootstrapped document reference. Deduplicate bootstrap by the originating document and preparation correlation; reuse the same PI when retrying. The native scenario exercises provision validation and a repeated response. It does not implement or qualify a hosted provisioning handler.

`Payment Observation Clause` reuses the existing Payment Base's event relay behavior to expose native PI events to the containing order. Commission continues to depend on confirmed receipts and reversals, not preparation or attachment.

## Local verification and preview

Run the selected cases with `tools/run_reseller.py`, a qualified `BLUE_JAVA_CLASSPATH` and `JAVA_HOME`. `preview-booking.case.json` covers conditional booking requirements and the free variant; `preview-card.case.json` covers card preparation/provision and a renamed fulfilment clause; `preview-clauses.case.json` covers bilateral approval and invalid commercial terms.

The local generated document, clause definitions, semantic cards, Overview and Terms are in `reports/reseller-20261103/business-preview/index.html`. These are local review artifacts, not a deployed agreement or proof of real card processing. The separate broader settlement qualification remains incomplete.
