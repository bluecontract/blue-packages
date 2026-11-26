# MyOS

MyOS Party specializes Party with myosAccountId. MyOS Customer Payment requires a recipient. MyOS Account to Account Payment requires distinct payer and recipient accounts. Either locator can be a direct account ID or a party object. Each account must map unambiguously to an existing /parties entry and admitted channel. Core bootstrap verifies account IDs against its account directory. These fields do not themselves grant authority. Selected parties and method details are copied into the PI and never follow later parent edits.

The package emits adapter requests. It does not call a bank, move real funds, or implement a checkout website.

Four concrete instruction identities distinguish Stripe and Test adapters:
`MyOS Stripe Customer Payment Instruction`, `MyOS Test Customer Payment Instruction`,
`MyOS Stripe Account to Account Payment Instruction` and
`MyOS Test Account to Account Payment Instruction`. Customer variants inherit the
existing funding session and initiation gate unchanged. Account-to-account variants
inherit Payment Instruction with Clauses without customer funding. These identities
do not implement Stripe transfers, account debits or commission payouts, and add no
separate provider field or operation permissions.

Choose `Account Transfer Preparation Functions` for a Documents clause that
prepares one account payout against a ledger. Its parameters name the ledger,
the transfer terms and the three participant channels. The preparation keeps the
gross reservation distinct from the net instruction amount and checks the frozen
terms again when accepting the supplied instruction.

In an account transfer instruction, bind `validateAccountTransfer` and
`confirmAccountSettlement` on `Payment Method Events`. The ledger can use
`Payout Ledger Functions` to close the reservation once both a
verified immutable settlement breakdown and the matching payment outcome exist.

Mount `MyOS/Payout Ledger Clause` to combine that profile with the ordinary
Ledger actions. To opt into recovery, bind `reconcilePayouts` to the
Agreement's local readiness events, for example `Parties/Document Access Restored`
and `Activation/Terms Accepted`. Recovery requires an active Agreement and uses
the payout collection and Documents admission entries named by `payouts` and
`payoutEntries`. Recovery uses the frozen terms validated by
`Account Transfer Preparation Functions`. It checks existing reservations against the same verified
transfer facts as ordinary settlement. The clause handles each eligible
reservation separately so Ledger totals include every settled key. Pending
or missing evidence preserves the reservation.
A mismatch in the admitted payout key, reserved gross or frozen split rejects
the triggering update, as it does during ordinary settlement.
An authored `after` on the readiness connection follows discovery of one or
more eligible payouts. It can precede the individual Ledger updates in that
same processing turn. Use the existing `Settlement Closed` event for an action
that depends on a posted result.

Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.
