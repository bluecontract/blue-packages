# Commerce package

[Product Clause](types/product-clause.blue) applies an integer unit price to
a positive whole-unit quantity and writes a simple product quote.

[Catalog Clause](types/catalog-clause.blue) validates a single supplier's
catalog and stores immutable keyed quotes in the same document. The
`state` and `quotes` bindings default to `/catalog` and `/quotes`. The
catalog has a revision, supplier ID, currency and keyed entries. A quote
selects that revision and specifies an item ID, quantity and any service
date or duration on each line. Repeating the same intent under the same
quote key returns the existing quote. A different intent requires a new key.

An entry can specify a positive integer `maxQuantity` to limit each line.
Omitting the field leaves the line quantity uncapped by the entry. Selections
of the same product with different dates or durations use their own line
quantities. Hourly entries list the whole-hour durations they offer in
`allowedDurationHours`. A two-unit, three-hour selection is billed for six
units. Per-line guest discounts use half-up rounding in minor units.

The catalog, quote lines, stored quotes and duration choices have no fixed
item-count quotas in this clause. Operations still run under the Contracts
gas budget and platform limits. Money rounding supports item prices and
per-line gross subtotals up to 1,000,000,000,000 minor units. Payment
instructions apply the same limit to the quote's payable total after
discounts. The gross subtotal across all lines can exceed that amount.

See the [clause tutorial](../docs/clauses-tutorial.md) for composition and
[distribution](../docs/distribution.md) for exact runtime and package identities.

## Whole-order cancellation

`Commerce/Whole Order Cancellation Policy` accepts a single reviewed
`{key, reason}` request on an author-bound party workflow. It writes an
immutable decision with the whole price, retained amount and released amount,
then emits `Commerce/Domain Event` with kind `Order Cancellation Accepted`,
the clause name and the decision key. Exact replay of the same request
preserves the decision. The named `acceptWithoutCharge` action lets the
author bind a separate fee-waived route.

The author binds the whole order amount, decision and any required timing
facts. The policy uses the earlier elapsed or service deadline when both are
configured. The deadline itself is free. A bound confirmation fact permits
free cancellation before confirmation. An elapsed window can explicitly
allow cancellation before its start.

`retentionBasis` is an optional readiness guard. A bound value must match the
full order amount before a positive late fee can be retained. A missing bound
value defers that decision with `CANCELLATION_AWAITING_CAPTURE`. Omitting the
binding permits an independent commercial decision. Payment requests and
confirmed financial outcomes belong to the separately composed payment.
For new Order compositions, select the protected actions on
`Orders/Order with Lifecycle Guards` or `Orders/Order with Seller Decision`.
Standalone callers can still supply `blockedOperationsAfterAcceptance` to
select the external operations blocked after cancellation.

With `availability` bound, `refreshAvailability` publishes the effective
deadline, timing readiness and whether a positive late fee would need full
retention proof. Connect it to changes on the declared sources. The policy
rechecks authoritative facts on acceptance.
