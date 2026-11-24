# Balance

Authored native Blue proposal package. See the top-level evidence and catalogue for tested scope. No JavaScript business interpreter.

`Target and Settlement Functions` owns the keyed Ledger arithmetic. A document
can mount `Ledger/Ledger Clause` with only the `state` binding and connect
`setTarget`, `reserve`, `settle`, and `closeReservation`. It needs no Order,
catalogue, or receipts. `setTarget` replaces the amount owed for a business
key. `reserve` earmarks available funds for a settlement key. `settle` applies a
verified full settlement. Payment profiles qualifying partial or zero outcomes
use `closeReservation`, which releases reserved funds once and adjusts the paid
balance by the difference from the recorded amount.

The optional `Balance Functions` adapter `accruePercent` connects a
confirmed-receipts event to the same `setTarget` calculation using the
current net receipts for its admitted order. The `receipts`, `orders` and
`orderEntries` bindings identify the receipt projection, keyed order collection
and Documents admission entries. `frozenRate` points to the basis-point value
inside each admission entry. The amount is recomputed from the cumulative
net on each confirmation and rounded once for that order.

`observePayout` and `catchUpPayout` can use a payment method's compute definition
with the `payouts` and `payoutEntries` bindings. The method verifies the outcome
before calling `recordSettlement`, which posts the paid amount and any confirmed
fee and transfer amount. The accounting functions accept qualified settlement amounts.

Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.
