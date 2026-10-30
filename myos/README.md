# MyOS

MyOS Party specializes Party with myosAccountId. MyOS Customer Payment requires a recipient. MyOS Account to Account Payment requires distinct payer and recipient accounts. Either locator can be a direct account ID or a party object. Each account must map unambiguously to an existing /parties entry and admitted channel. Core bootstrap verifies account IDs against its account directory. These fields do not themselves grant authority. Selected parties and method details are copied into the PI and never follow later parent edits.

The package emits adapter requests. It does not call a bank, move real funds, or implement a checkout website.

## Customer Payment Instruction provider selection

`MyOS/MyOS Customer Payment Instruction` accepts an explicit provider policy in
its immutable payment terms:

```yaml
paymentTerms:
  allowedProviders: [test]
  provider: test
```

These are additional terms, not a complete instruction. Keep the amount, currency,
limit, financial roles, allowed payees and recipient-approval policy alongside
them. The instruction validates the policy on `Document Processing Initiated`,
before clause installation and its Activation dispatch gate. This rejects invalid
terms even when commercial consent is still pending.

- `allowedProviders` must be a nonempty list of nonempty text identifiers.
- `provider` must be nonempty text and belong to that list.
- Omitting both fields preserves the earlier provider-unspecified contract.
  Configuring either field requires both; an empty or malformed policy is not a
  fallback to unspecified execution.

The failures are `MYOS_PAYMENT_ALLOWED_PROVIDERS_REQUIRED`,
`MYOS_PAYMENT_PROVIDER_REQUIRED` and `MYOS_PAYMENT_PROVIDER_NOT_ALLOWED`,
respectively. Validation belongs to the PI even when it is created directly,
without a parent Payment clause. The provider policy identifies a configured
adapter; it does not grant that adapter financial authority. The configured
guarantor still owns acceptance and confirmed financial outcomes.

For `Payment/Payment Clause` with `parameters.obtain: create`, put the allow-list
in `parameters.template.paymentTerms.allowedProviders`. A request may select
`provider` through an explicitly declared field/value binding into
`/paymentTerms/provider`; it must not be able to replace the allow-list. Automatic
preparation can pass the same selected value from its Order, using the same
`prepare` action as an explicit workflow request. The existing preparation
contract freezes the complete effective `paymentTerms`, including these two
fields, and supplied candidates must preserve those terms exactly. No additional
seller input or execution-mode flag is needed.

Provider, kind and account answer different questions:

- **Provider** is the selected adapter identifier, such as `test`; it is not a
  payment rail, a party channel or proof that money moved.
- **Kind** describes an action or event. For example,
  `paymentAction.kind: customer-funding` tells the payer what action is available.
  It does not choose a provider.
- **Payment Account** is a separate account/mandate integration concept, not a
  prerequisite for this customer-funded instruction. `MyOS Party.myosAccountId`
  identifies a MyOS party account; it is not a bank account or Payment Account.
  This provider policy introduces neither an account nor a mandate.

For a local flow without new seller approvals, declare and map the customer,
seller and separate system guarantor in the creating document's existing roster.
The PI can use activation `required: []` and
`paymentTerms.recipientApprovalRequired: false`, with `payerChannel: customer`,
`payeeChannel: seller`, `guarantorChannel: guarantor` and
`allowedPayees: [seller]`. Do not introduce unresolved parties, live source links
or new admission requirements merely to copy fixed accepted commercial terms.
This is an explicit no-additional-consent policy, not a bypass of access checks:
all declared timelines still need genuine access and admitted channels. An
Agreement's existing seller/reseller acceptance is separate; neither that
acceptance nor PI creation accepts the PI on behalf of its system guarantor,
funds the customer session or confirms settlement.

When qualifying this contract, initialize a direct PI with the allowed provider,
reject an outside provider, missing selection, empty selection and malformed
allow-lists, and retain a fixture omitting both fields. Also check that parent
request bindings cannot overwrite the frozen policy and that later parent edits
do not alter the created PI's selected provider.
Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.
