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
