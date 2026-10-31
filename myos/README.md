# MyOS

MyOS Party specializes Party with myosAccountId. MyOS Customer Payment requires a recipient. MyOS Account to Account Payment requires distinct payer and recipient accounts. Either locator can be a direct account ID or a party object. Each account must map unambiguously to an existing /parties entry and admitted channel. Core bootstrap verifies account IDs against its account directory. These fields do not themselves grant authority. Selected parties and method details are copied into the PI and never follow later parent edits.

The package emits adapter requests. It does not call a bank, move real funds, or implement a checkout website.

## Customer payment session publication

`0.8.0-preview.10.customer-payment.1` adds correlated preparation to Customer PI.
The prior `0.8.0-preview.7.access-events.2` archive is retained under `releases/`;
existing Core publications and documents must keep their exact identities.

Set `paymentDetails.customerPaymentTerms.provider`, `recipientPaymentAccountId`, and optionally
`paymentWindowDays` (default 30, integral days from 1 to 3650). The Customer
Payment builder accepts the same parameters. After acceptance the PI emits one
`Customer Payment Session Requested` for `customer-session-1`, scoped to that PI,
and records `customerSession.paymentDueAt`. Repeated acceptance does not renew it.

The guarantor supplies `provideSession(requestId, sessionId, expiresAt)`, with
expiry exactly equal to that deadline. Identical responses are idempotent;
conflicting responses fail. `failSessionPreparation(requestId, reason)` records
a known terminal preparation failure. An uncertain result must reconcile the
same request, without calling this failure operation or creating a replacement.

`requestCustomerPayment(sessionId, requestId)` is guarantor-only and creates the
standard Secure Funds Requested using the PI amount. It requires a ready session,
an accepted/initiated PI, and a start before the deadline. One durable financial
attempt belongs to the session; retries reuse its requestId, including after the
deadline. Existing financial outcome operations still reconcile that attempt.
Session readiness does not move money. Capture remains governed by the existing
Payment Process Clause and mandatory capture policy.

The new Customer PI and builder do not require `customerSession.funded`,
`requestCustomerFunding`, or `confirmFunding`. Its `paymentAction.kind` is
`customer-payment` and the action is removed after accepting the attempt.
The retained publication keeps its original funding operations. Account to Account
and Manual Bank Payment remain separate methods; this publication adds no provider
implementation, payment-account storage, public endpoint, or deployment.

Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.

For the embedded Customer Payment example, configure the host's
`paymentDetails.customerPaymentTerms`. The Customer Payment clause reads this
through its declared `customerPaymentTerms` pointer binding, whose default is
`/paymentDetails/customerPaymentTerms`; a different host path may be supplied
through the normal clause bindings. Standard `parameters` contain only Payment
builder fields such as amount, currency and recipient. The builder copies the
configured terms into the child's same canonical path before creating it.
See example 21 for this setup. No dynamic clause subtype is needed.

## Expired Stripe authorizations (new documents)

The additive `MyOS Expiry-Aware Customer Payment Instruction` retains the existing
Order/bootstrap base. The separate `MyOSExpiryDirect/MyOS Expiry-Aware Direct Customer Payment Instruction`
publication retains the exact stage-one direct base and its coherent dependency family.
Existing Customer Payment Instruction identities and documents gain no operation.
New Order documents may use the additive type with either payment provider; the
expiry operation itself rejects every provider except Stripe.

The guarantor-only `requestExpiredAuthorizationVoid` accepts `sessionId`,
`secureRequestId`, and `requestId`. The guarantor adapter must first verify that the
same bound Stripe authorization expired and is canceled. The native document does
not independently know Stripe's `capture_before`. It verifies the session and
successful original SECURE, rejects completed payments and unresolved financial
requests, and derives the entire remaining authorization amount without a caller
amount. The operation initiates the existing VOID protocol; only the existing
`cancelBeforeCompletion` outcome closes the authorization. Neither operation pays
an Order or creates another charge/attempt. Exact request replay remains inert
after closure; a reused request identifier with different intent is rejected.

Select this bootstrap publication for Order documents and the separate direct
publication for direct documents; do not combine their historical alias families.
No existing document migration is implied.
