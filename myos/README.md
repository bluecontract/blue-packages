# MyOS

MyOS Party specializes Party with myosAccountId. MyOS Customer Payment requires a recipient. MyOS Account to Account Payment requires distinct payer and recipient accounts. Either locator can be a direct account ID or a party object. Each account must map unambiguously to an existing /parties entry and admitted channel. Core bootstrap verifies account IDs against its account directory. These fields do not themselves grant authority. Selected parties and method details are copied into the PI and never follow later parent edits.

The package emits adapter requests. It does not call a bank, move real funds, or implement a checkout website.

Customer payment setup binds `requestCustomerFunding` to the selected payer
channel (`parameters.payer`, default `customer`), matching the instruction's
`paymentTerms.payerChannel`. It does not invent a separate `payer` participant.
The instruction type leaves this channel as a required Text slot; setup supplies
its value before the instruction is initialized.

Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.
