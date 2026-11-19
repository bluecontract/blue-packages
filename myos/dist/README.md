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

Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.

### Stripe bank withdrawals

`MyOS/MyOS Stripe Bank Transfer Instruction` extends `ACME/Bank Transfer Instruction`
for a single self-payout. Set `paymentTerms.amountMinor == limitMinor`, equal payer
and payee channels, and `paymentDetails.externalBankAccountId`; the method is
`myos-stripe-bank-transfer`. Source Stripe account resolution belongs to Core.
Existing bank request, unknown, decline and confirmation operations remain inherited.
The subtype validates these self-payout terms atomically when requesting a transfer.

The guarantor-only `reportPayoutFailureAfterConfirmation` accepts `requestId`,
`reference` (the confirmed payout ID), `failureCode` and optional
`failureBalanceTransaction`. Use native input type `MyOS/Stripe Payout Failure Input`.
It changes `bankTransfer.status` to `failed_after_confirmation`, stores the input
as `bankTransfer.payoutFailure`, and emits `MyOS/Stripe Bank Transfer Event` with
kind `Payout Failed After Confirmation`. Historical confirmation/reference and
`payment.completed`/`payment.reversed` are preserved. An identical correction has
no second effect; conflicting corrections and later confirmations are rejected.
This event records a late failure, never a synthetic refund.

Focused local qualification (requires the qualified companion Core classpath):
`python3 tools/check_operation_inputs.py --case stripe-bank-transfer`.
This checks published input schemas and native BEX effects, not live Stripe payouts.
