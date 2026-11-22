# Reseller clauses

Native Blue/BEX catalog and reservation clauses extending the existing reseller agreement. The existing reseller-percentage 3.2.0 profile owns partner commission and payouts; this package does not replace that logic. This is an unpublished preview.

The package exports reusable clauses and shared function definitions. These catalog, order and fulfilment types have semantic cards.

- [Description Clause](types/description-clause.blue) — independent authored content: a title, text and optional sections with their own titles, text and bullet items. It declares no actions, guards, effects or mutable state. [Semantic card](../semantics/cards/6KwmfuRrit267m3cr56FHdVGEmgNrZ9SboSMgUb3KTz6.json).
- [Catalog Clause](types/catalog-clause.blue) — an optional offer description and groups together with product variants, prices, guest discounts and immutable quotes. [Semantic card](../semantics/cards/26yN2WMST4rgx3o5ErKuJSQ6rzkiGBwcXkvNacDbWT7d.json).
- [Customer Orders Clause](types/customer-orders-clause.blue) — price selections from the current catalog, prepare an independent Order and attach its initialized publication to the agreement. [Semantic card](../semantics/cards/6eb8apwuLdkyTnXs9jzFE9snMuvZgSA2iTTn8MgDxkJ1.json).
- [Fulfilment Terms Clause](types/fulfilment-terms-clause.blue) — configure fulfilment text, confirmation mode, date requirements and cancellation policy. [Semantic card](../semantics/cards/GPQftM9sk5ii77qcbqr8t3igTewwTqTQPHsH8vGHhezk.json).
- [Confirmation Clause](types/confirmation-clause.blue) — supplier confirmation, alternatives, customer consent, response deadlines and recorded fulfilment. [Semantic card](../semantics/cards/HFHDWrJHEi8sbG2ab6a2RC9ts2kYjuFmdQbJUgA1fEqC.json).
- [Cancellation Clause](types/cancellation-clause.blue) — customer/supplier cancellation, expiry, no-show and monetary decisions, separate from actual settlement. [Semantic card](../semantics/cards/GPnCY1kNrBoPjNUkP1bmpgks1fhnAGtvaKqEmvjCU43X.json).
- [Catalog Functions](types/catalog-functions.blue) — shared catalog validation and pricing. [Semantic card](../semantics/cards/Hnw3FqVrPQPZZPavvnEAZUL8rWweJZTAVyKgThT26bPd.json).
- [Order Functions](types/order-functions.blue) — shared order, confirmation, cancellation and settlement-observation operations. [Semantic card](../semantics/cards/9Qu5i1YyM9Jby5SL4vDmBXZynpaiGUZWSqStztaFyfJX.json).

## Examples and qualification scope

[The historical reservation execution fixture](../examples/reseller/historical/agreement.blue) exercised the original clauses with native Blue execution. Its catalog updates and changes to future fulfilment terms use the existing Amendments clause with both seller and partner as approvers. One approval, including a repeated approval by the same party, does not apply a price change. Earlier quotes and order snapshots retain their terms. The standalone catalog fixture intentionally exposes direct publication to test that component in isolation.

[The Adventures in Paradise UI fixture](../examples/reseller/adventures-in-paradise-preview.blue) retains the reseller agreement's commission and payout logic. One Catalog Clause owns the offer description at `clauses.catalog.parameters.offer` and the product variants. Descriptive groups use `title`, `text` and optional `bullets`; this content adds no booking or payment requirement. The independent Description Clause remains available for documents without a catalog. Its two cruise variants are read from `/products/entries`, including the 5% customer discount. `prepareOrder` validates selections against the current catalog and computes the price in the same operation. These agreements have no separate quotation operation or `/quotes` collection.

The optional `fulfilment` clause declares the proposed date and seller confirmation requirement. The Customer Orders Clause prepares its exact terms and quote for independent Core bootstrap and adds the Confirmation Clause only when that parent clause exists. Without it, the same catalog can produce an order without a date or confirmation workflow. The order request records the customer’s proposed date without requiring a second order approval; a supplier alternative requires separate customer acceptance. Free entries create zero-price orders without a payment instruction. Confirmation without a cancellation policy does not manufacture cancellation charges or a free-cancellation deadline.

The local [Terms/Overview and semantic-card preview](../reports/reseller-20261103/business-preview/index.html) uses the Business generators, validators, value resolver and presentation components, with source-bound repeated items added in an isolated Business worktree. The model selects the source and row fields, not copies of products or prices. Both Overview and clause Terms iterate `/products/entries`, using `/products/currency` to format prices. The description and its groups are also read from the document under the same Catalog Clause. Long descriptions and priced lists beyond six options have native disclosures; Terms use flat clause details and collapsible child-document sections. The overview includes complete order and payout collection counts, including known zeros, while unknown counts stay absent. Payout records are not presented as confirmed transfers. Generated Terms and Overview are accepted only after Business validation. A presentation regression check covers 40 variants, a price change and a newly added variant using the same template, including 0% and 5% customer discounts. This is local presentation qualification, not a deployed or end-to-end qualified customer agreement.

The four [booking requirement scenarios](../examples/reseller/historical/preview-booking.case.json) pass on native Contracts: required date and seller confirmation, absence of the clause, customer acceptance of an alternative and a free variant. The native baseline and bilateral-amendment scenario passed. All 33 reservation regression scenarios pass with optional cancellation policies and the date requirement. After correcting the payment fixture's clause edition, four of six settlement scenarios passed; failed/unknown reversal requests still require correction. Settlement observation is not qualified end to end. Generated semantic cards describe implementation, not proof of successful execution.

Catalog prices originate in the user handoff. Dates and descriptive text do not enforce supplier availability. The cancellation implementation has one cutoff and one percentage charge; the source offer's holiday, group-size and booking-fee exceptions remain descriptive. No calendar tariffs or security-deposit collection are implemented. Local execution does not establish hosted delegation, a real booking or payment confirmation.

## Integration edition

The preview.4 candidate adds a deferred customer selection. `prepareOrder` accepts
exactly one of `values.customer` (an account ID) or `values.customerEmail` (1–320
characters of contact and correlation metadata). For example, a partner can
prepare a basket with `customerEmail: guest@example.test` before a customer
account exists. The exact text is retained at `/customerEmail` in the prepared
Order and in its preparation intent. It is not a Party locator or verified
identity. The actual customer is supplied by the normal bootstrap participant
mapping, after Business authorizes the checkout/account association.

`provideOrder` checks the native Documents request, requirement, source, terms,
Party and access rules. In the email branch it requires the
actual initialized/current customer account to be present and distinct from
seller and partner. It does not compare that account with the contact email.
The first accepted Order remains immutable and an identical provision remains
idempotent. Explicit `values.customer` preparations retain their exact account
pin. Earlier package editions and their pending preparations keep their own
exact definitions.

The preview.3 candidate removes the agreement-wide limit of 20 distinct Order
preparations. Each new key can prepare another catalog-priced Order; an identical
retry retains its existing preparation. Catalog, quantity, pricing and request
validation still apply, including the separate limit on lines in one order.
`examples/reseller/tests/preparation-count.case.json` exercises 21 preparations,
retained entries, a retry after the former boundary and cold restoration.

Customer Orders uses native Documents preparation/provision and independent bootstrap. In preview.2, `prepareOrder` takes `catalogRevision` and `lines` instead of a stored `quoteKey`. Shared Catalog Functions validate and price the selected items; the prepared Order retains the frozen calculation, currency and optional fulfilment terms. The `catalog` pointer replaces the `quotes` binding. New preparations require the current revision; identical retries retain the original prepared document even after a catalog change. The standalone Catalog Clause still supports explicit quotation workflows when configured, without requiring a quote store for catalog-only use.

In preview.10 the first valid provision can attach the initialized Order before
commercial approval. The agreement can then receive later Order and payment
publications. The selection policy is frozen during preparation. The Order
becomes usable when its commercial activation, access and source requirements
are satisfied.

The catalog constructor uses the shared preparation lifecycle.
`tools/test_reseller_composition.py` checks the preparation and provision seams
against the selected Documents source. See `examples/reseller/README.md` for
the request contract and historical fixture boundary.

## Retained checkout editions

New agreements use `Customer Orders Clause` with catalog selections. Earlier published
agreements and pending preparations keep their exact definitions. The [historical
fixtures](../examples/reseller/historical) exercise previously published stored-quote
checkout through its retained archive.

The guarded commission attachment reads a current Order publication during the
supported continuation after earlier financial outputs. An attached Order without
a Payment Instruction leaves existing commission targets unchanged.

`source-import.json` is immutable provenance of the original owner-supplied handoff,
not a claim that all current authored sources still equal that historical import.
The task's native component tests and upstream reservation/catalog examples have
separate qualification boundaries. Package selection and semantic cards alone do
not establish hosted execution or financial acceptance. No semantic model call is
required to build or verify the native archive.

## Account-to-account commission payout profile (preview.7)

`Commission Account Payouts Clause` prepares an independent MyOS Test or Stripe
Payment Instruction. Existing `Commission Payouts Clause` and its manual payment
profile remain available. The Agreement explicitly accepts `payoutOperator`,
`payoutOperatorAccountId`, `payoutFeePolicy: myos-commission-fee-v1` and required
`payoutFeeBps` (an integer from 0 through 9999). Missing or invalid rates reject
preparation; the policy identifies the rounding algorithm, not a fixed rate.

`preparePayout.startPayout` accepts `{key, amountMinor, accountContext}` where
`amountMinor` is gross commission G. `accountContext` contains concrete
`payerBinding`, `payeeBinding`, `platformAccountId` and `environment` returned by
Core for the Agreement parties. Preparation freezes those bindings, the party
account IDs and channels, Agreement origin, payout key, currency and G/F/N.
The only fee resolver reads the agreed `terms.payoutFeeBps` and uses Money
rounding: F = roundBps(G, payoutFeeBps), N = G-F, requiring N > 0. The prepared
instruction freezes that rate and split; later execution uses the frozen values. The Payment Instruction authorizes N; the operator reserves/debits G.
Operator costs are not added to G.

The seller bootstraps the prepared instruction, provides the inactive candidate,
approves that exact instruction, then provides the same instruction again.
Current Documents activation, source and reader validation are unchanged.
Core executes only after the Agreement has linked the exact approved instruction.
Before linking, native `cancelPayout` permanently closes the attempt and releases
G once. After linking, only a terminal no-effect result or confirmed full void
releases G. An unresolved operator result keeps the commission reserved.

The instruction includes `Commission Payout Profile Clause` to enforce full-N
requests and reject inherited changes of amount, recipient and details, as well
as refunds. `Commission Payout Settlement Clause` binds the guarantor's debit and
transfer references to the exact frozen context and instruction origin. Shared
Commission reconciliation requires both that report and completed N with no
reversal or unresolved financial request, in either arrival order. Only then is
G paid and its reservation released exactly once.

Example 30 and `CommissionPayoutConformance` exercise native document behavior;
the conformance runner models attachment and does not move funds. Hosted Core
qualification owns actual bootstrap/provision, financial execution and recovery.
