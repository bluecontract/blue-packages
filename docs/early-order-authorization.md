# Early Order authorization candidate

The `myos-payment-mandates` 0.3 candidate adds an opt-in
`myos-order-customer-payment/5` composition. Existing correlated PI, seller policy
and mandate exports retain their exact identities. The previous 0.2 outreach
archive is retained byte-for-byte in
`retained/early-authorization-baseline/myos-payment-mandates/package.bluepkg`.

The early PI uses the existing Connected Clause `initialState` mechanism to start
with `customerOrderState.captureAllowed=false` and `customerOrderState.status=WAITING`.
These are mutable native state, not inherited fixed values. Preparation freezes
`customerOrderTerms.revision` and `termsRef` from the native Order review along
with the existing four-field `paymentPreparation` correlation.

The `Early Order Payment Observer` reads the actual native Order source. Capture
requires the original Order identity, a reciprocal link to this PI's original
identity, the same review revision/reference, matching payment terms and customer
payment configuration, and current seller approval and active source. Missing
source, access/readiness, wrong linkage or changed terms keeps capture closed.
The existing Payment Process Clause still owns financial requests and reservation
checks; this observer neither authorizes a financial actor nor publishes a
financial outcome. It must be connected to native source events and initial
state evaluation by the qualified compositor.

A seller may `rejectOrder` only before seller acceptance, with exact document
review and the current native revision. The accompanying dispatch policy blocks
subsequent external approval or amendment while preserving internal updates and
ordinary provision recovery under the original policies. The action records the
native decision and emits one typed `Early Order Rejected` event; exact replay
emits none. This event is only a wake-up: the observer ignores its payload as
an authority source and reads the actual Order decision. Rejection sets
`cancellationRequested` and the original Order/revision/review tuple. It does not
mean that VOID completed, that the PI is closed, or that funds were returned.
Core must reconcile outstanding financial requests through the existing protocol.

A newly approved early policy and mandate are required. They retain seller,
Agent, provider, account, guarantor, amount and currency restrictions and permit
only the exact canonical program. Prior policy approval does not gain early
bootstrap authority. This package does not change generic runtime activation,
source-access rules, existing standalone PI capture, or financial event types.

## Qualification boundary

Local native tests establish pending-host explicit preparation, seller rejection,
replay and late approval denial, native observer event delivery, and immutable
source/backlink comparisons. The late-link helper in the observer test emits the
same `Document Selected` notification as ordinary provision, but is deliberately
an event-delivery fixture, not proof of hosted ordinary provision. Twelve BEX
predicate cases exercise spoofed payloads, missing/wrong sources and backlinks,
changed terms/account/provider/revision, and access inactivity.

Direct preparation during `Clauses Initialized` is too early for the native
`contracts/initialized` marker; its failing local and hosted evidence is retained.
The new Activation `preActivationTimerChannels` option defaults to an empty list.
Only an explicitly listed, nominal Time/Timer Channel may run an external timer
dispatch before business activation, after the existing access and closed guards.
Native timer ticket validation is unchanged. An existing one-shot native Time
callback and access-change retry are being qualified as the post-initialization
composition. They introduce no payment
expiry or automatic cancellation deadline. Full hosted B0, actual separate PI
bootstrap/provision, guarantor session, secure-before-approval, gated capture and
financial cancellation remain separate required Core/Business evidence. Local
package tests alone do not establish those outcomes or deployment readiness.

Core must support and qualify the new exact profile before Business emits it.
The owner confirmed that the payment flows were never deployed or used; no old
payment migration or runtime fallback is required. No package publication,
deployment or mutation of existing documents is implied here.

The ten replaced dependency archives are retained by exact root and SHA-256 in
`PACKAGE-SOURCES.json`; these are historical data, not alternative active mounts.
Their retention does not require shipping an old payment execution path. Published
identities must not be rewritten; removing retained archives from a future delivery
requires checking actual references, including nonpayment users of shared packages,
rather than assuming every archive is needed for old payments.
