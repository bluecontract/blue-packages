# Rivermill Packaging and Alder Street Café

Alder Street Café buys cartons of takeaway cups and lids from Rivermill
Packaging. A standing agreement holds the parties’ current EUR catalogue and
gives the café a buyer-only operation for saving a restock quote. Both parties
must accept the agreement before it activates.

## One basket, two catalogue revisions

Each carton contains 500 cups or 500 lids. The buyer selects the same basket
twice, with three cartons of cups and two cartons of lids.

| Saved quote | Catalogue revision | Price per carton of cups | Price per carton of lids | Basket total |
| --- | ---: | ---: | ---: | ---: |
| `restock-01` | 1 | EUR 24.00 | EUR 12.50 | **EUR 97.00** |
| `restock-02` | 2 | EUR 26.50 | EUR 12.50 | **EUR 104.50** |

1. The buyer calls `saveQuote` with a unique key, the catalogue revision they
   intend to use and the product quantities. Commerce stores the priced lines,
   total, revision and exact catalogue identity under that key.
2. The supplier proposes revision 2 and approves it. The current cup price
   stays at EUR 24.00 with the buyer’s approval outstanding.
3. The buyer approves the exact document version they reviewed. Amendments
   validates and applies the replacement, raising the cup price to EUR 26.50.
4. A fresh request with the current revision saves `restock-02`. The full
   `restock-01` snapshot is still the same. Repeating the original request under
   the original key preserves the saved quotes and emits no new quote event.

An attempted supplier approval on the buyer’s route fails with
`INVALID_TARGET_OPERATION`. A buyer approval targeting an older document
version fails with `STALE_DOCUMENT_PRECONDITION`. After revision 2 goes live,
a new key on revision 1 fails with `STALE_CATALOG_REVISION`, and reusing the
original key with revision 2 fails with `QUOTE_KEY_CONFLICT`. Each rejected
attempt preserves the document version and emits no event.

The example ends at a saved purchase quote. Placing an order, reserving stock,
tax, invoicing, delivery and payment are separate steps.

## Blue source and native evidence

[The agreement](cafe-supply-agreement.blue) configures
`Activation/Activation Clause`, `Commerce/Catalog Clause` and
`Amendments/Amendments Clause`. The latter uses the published
`Commerce/Catalog Functions.validateCatalogReplacement` to validate a
replacement against the live catalogue. The workflow bindings forward request
objects with `input: true`. The parties, the workflow bindings and the
catalogue live in one document, and the price calculation and approval logic
come from the named packages.

[Operation inputs](operations.yaml) contain the parties, requests and expected
changes for the 12-step scenario. The [native verifier](VerifyCafeSupply.java)
reports the actual requests, document versions, results, package archive pins
and the two full quote snapshots. The fixture uses local demo channels. A
hosted deployment must bind the parties to authenticated transports.

Follow the [reproduction instructions](../README.md#run-the-three-checks) to
generate the runtime classpath and run the verifier.
