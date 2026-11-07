# Reseller clauses

Native Blue/BEX catalog and reservation clauses extending the existing reseller agreement. The existing reseller-percentage 3.2.0 profile owns partner commission and payouts; this package does not replace that logic. This is an unpublished preview.

The package exports reusable clauses and shared function definitions. The following catalog and fulfilment types have generated semantic cards:

- [Description Clause](types/description-clause.blue) — independent authored content: a title, text and optional sections with their own titles, text and bullet items. It declares no actions, guards, effects or mutable state. [Semantic card](../semantics/cards/6KwmfuRrit267m3cr56FHdVGEmgNrZ9SboSMgUb3KTz6.json).
- [Catalog Clause](types/catalog-clause.blue) — an optional offer description and groups together with product variants, prices, guest discounts and immutable quotes. [Semantic card](../semantics/cards/3gkrAmyYAz2Zvnpok3CHgwCATdQC4o5EFLi2YjezXaGS.json).
- [Fulfilment Terms Clause](types/fulfilment-terms-clause.blue) — preserve the selected quote, description, confirmation mode, optional date requirement and any configured cancellation policy when preparing an order. [Semantic card](../semantics/cards/5H7tk8XhysZgR9tHttFPtYHk88aLg1WVuKySQE2Dzheh.json).
- [Confirmation Clause](types/confirmation-clause.blue) — supplier confirmation, alternatives, customer consent, response deadlines and recorded fulfilment. [Semantic card](../semantics/cards/EWMrPZWUi46vyUu6gcw3k5xZRPFMxWPfoC9mGwFvXPFz.json).
- [Cancellation Clause](types/cancellation-clause.blue) — customer/supplier cancellation, expiry, no-show and monetary decisions, separate from actual settlement. [Semantic card](../semantics/cards/4Jo5puA4Rb4yuMr2jAd6PUKVEXzJ72djA1KMeaDaom83.json).
- [Catalog Functions](types/catalog-functions.blue) — shared catalog validation and pricing. [Semantic card](../semantics/cards/2aE614qR9AoVX6NgkwBfSGRdbboy7w7irK5WYLWkuJTc.json).
- [Order Functions](types/order-functions.blue) — shared order, confirmation, cancellation and settlement-observation operations. [Semantic card](../semantics/cards/9uaNLT6DfnQ8EXeozaJQZgCy84P3m8E1fkb3YekMUieb.json).

## Examples and qualification scope

[The reservation execution fixture](../examples/reseller/agreement.blue) exercises the four new clauses with native Blue execution. Its catalog updates and changes to future fulfilment terms use the existing Amendments clause with both seller and partner as approvers. One approval, including a repeated approval by the same party, does not apply a price change. Earlier quotes and order snapshots retain their terms. The standalone catalog fixture intentionally exposes direct publication to test that component in isolation.

[The Adventures in Paradise UI fixture](../examples/reseller/adventures-in-paradise-preview.blue) retains the reseller agreement's commission and payout logic. One Catalog Clause owns the offer description at `clauses.catalog.parameters.offer` and the product variants. Descriptive groups use `title`, `text` and optional `bullets`; this content adds no booking or payment requirement. The independent Description Clause remains available for documents without a catalog. Its two cruise variants are read from `/products/entries`, including the 5% customer discount. `prepareOrder` validates selections against the current catalog and computes the price in the same operation. These agreements have no separate quotation operation or `/quotes` collection.

The optional `fulfilment` clause declares the proposed date and seller confirmation requirement. The Customer Orders Clause prepares its exact terms and quote for independent Core bootstrap and adds the Confirmation Clause only when that parent clause exists. Without it, the same catalog can produce an order without a date or confirmation workflow. The order request records the customer’s proposed date without requiring a second order approval; a supplier alternative requires separate customer acceptance. Free entries create zero-price orders without a payment instruction. Confirmation without a cancellation policy does not manufacture cancellation charges or a free-cancellation deadline.

The local [Terms/Overview and semantic-card preview](../reports/reseller-20261103/business-preview/index.html) uses the Business generators, validators, value resolver and presentation components, with source-bound repeated items added in an isolated Business worktree. The model selects the source and row fields, not copies of products or prices. Both Overview and clause Terms iterate `/products/entries`, using `/products/currency` to format prices. The description and its groups are also read from the document under the same Catalog Clause. Long descriptions and priced lists beyond six options have native disclosures; Terms use flat clause details and collapsible child-document sections. The overview includes complete order and payout collection counts, including known zeros, while unknown counts stay absent. Payout records are not presented as confirmed transfers. Generated Terms and Overview are accepted only after Business validation. A presentation regression check covers 40 variants, a price change and a newly added variant using the same template, including 0% and 5% customer discounts. This is local presentation qualification, not a deployed or end-to-end qualified customer agreement.

The four [booking requirement scenarios](../examples/reseller/tests/preview-booking.case.json) pass on native Contracts: required date and seller confirmation, absence of the clause, customer acceptance of an alternative and a free variant. The native baseline and bilateral-amendment scenario passed. All 33 reservation regression scenarios pass with optional cancellation policies and the date requirement. After correcting the payment fixture's clause edition, four of six settlement scenarios passed; failed/unknown reversal requests still require correction. Settlement observation is not qualified end to end. Generated semantic cards describe implementation, not proof of successful execution.

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

`provideOrder` retains native Documents request, requirement, source, terms,
Party, access and activation validation. In the email branch it requires the
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

The constructor is the only customization of the standard shared preparation lifecycle; `tools/test_reseller_composition.py` checks this seam against the selected Documents source. Shared function references use exact native node identities. See `examples/reseller/README.md` for the request contract and historical fixture boundary. Earlier execution results above apply to the previous embedded factory edition, not this transport contract.
