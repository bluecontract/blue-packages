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

The preview.3 candidate removes the agreement-wide limit of 20 distinct Order
preparations. Each new key can prepare another catalog-priced Order; an identical
retry retains its existing preparation. Catalog, quantity, pricing and request
validation still apply, including the separate limit on lines in one order.
`examples/reseller/tests/preparation-count.case.json` exercises 21 preparations,
retained entries, a retry after the former boundary and cold restoration.

Customer Orders uses native Documents preparation/provision and independent bootstrap. In preview.2, `prepareOrder` takes `catalogRevision` and `lines` instead of a stored `quoteKey`. Shared Catalog Functions validate and price the selected items; the prepared Order retains the frozen calculation, currency and optional fulfilment terms. The `catalog` pointer replaces the `quotes` binding. New preparations require the current revision; identical retries retain the original prepared document even after a catalog change. The standalone Catalog Clause still supports explicit quotation workflows when configured, without requiring a quote store for catalog-only use.

The constructor is the only customization of the standard shared preparation lifecycle; `tools/test_reseller_composition.py` checks this seam against the selected Documents source. Shared function references use exact native node identities. See `examples/reseller/README.md` for the request contract and historical fixture boundary. Earlier execution results above apply to the previous embedded factory edition, not this transport contract.

## Additional hosted bootstrap profile

`Customer Orders Bootstrap Clause` remains a distinct additive profile alongside
preview.3 `Customer Orders Clause`. Its partner `startOrder` request retains
`{key, requestId, customer, quoteKey, description?, groups?}`; the catalog-priced
preview.3 request above is not silently substituted for it. It freezes the exact
quote/customer/commercial snapshot and uses ordinary Documents independent
bootstrap with native source, party, access, requirement and origin validation.
The complete authored connection configuration is frozen during preparation.
Only this profile explicitly selects a valid initialized Order while it is still
commercially inactive. Selection does not approve the Order or make it usable;
missing-party admission still waits for its normal consent and access lifecycle.

`bootstrap-composition.json` records the reused exact native function identities.
Additional fixed-account child roles remain checked against the prepared template;
this does not grant those roles access to the Agreement. The shared admission
proof remains needed by the maintained added-guarantor provision conformance case.
Commission's guarded `attached` action remains for the supported continuation that
provides a current publication after earlier financial outputs; historical receiving
from INITIALIZE is qualified separately with that action disabled only in its test.
An attached Order without a Payment Instruction leaves existing commission targets
unchanged; malformed amounts and invalid identity/access still fail their guards.

`source-import.json` is immutable provenance of the original owner-supplied handoff,
not a claim that all current authored sources still equal that historical import.
The task's native component tests and upstream reservation/catalog examples have
separate qualification boundaries. Package selection and semantic cards alone do
not establish hosted execution or financial acceptance. No semantic model call is
required to build or verify the native archive.

## Automatic cancellation settlement

The Cancellation Clause records the commercial decision on the Order, including
the amount to retain. It does not confirm that money moved. Configure
[Cancellation Payment Clause](types/cancellation-payment-clause.blue) on the PI
with `bindings.order: /sources/order` and
[Cancellation Settlement Clause](types/cancellation-settlement-clause.blue) on
the Order with `bindings.instruction: /payment`. Both use
[Cancellation Settlement Functions](types/cancellation-settlement-functions.blue).

The PI observes the exact bound Order and reconciles its cancellation decision
against the confirmed payment ledger. It requests a refund of confirmed excess,
captures only a retained fee when permitted by the existing capture gate, and
releases unused authorization. Only a guarantor outcome changes settled money.
Pending or unknown requests keep their reservations; replay and repeated
cancellation cannot create a second refund. The Order observes that settlement
separately and remains cancelled while it is pending, blocked or failed.

All 16 [native scenarios](../examples/reseller/tests/cancellation-settlement.case.json)
pass against the current package selection and Core 64abcd6de. They exercise full and partial refunds, void, fee retention, multiple groups, pending
and failed outcomes, replay, and unauthorized refund confirmation. Their
[fixture](../examples/reseller/cancellation-settlement-native.blue) uses the legacy
embedded factory only to qualify the settlement clauses; new hosted Orders use
the `prepareOrder` / independent bootstrap / `provideOrder` contract above.
One PI covers the complete Order. This does not implement installments, calendar
availability, provider checkout, or a Business UI integration.
