# Declarative reseller Agreement

The Go reseller template, version `19`, composes direct checkout, optional whole-Order cancellation, and partner payouts using ordinary Blue clauses. The seller and partner agree on commission for customer purchases. A customer Order and its Stripe Payment Instruction have independent identities. A separate MyOS account-to-account Payment Instruction pays the partner. The bicycle-rental configurations use 1,250 basis points of commission and require supplier confirmation where configured. The two-hour rental `harbor-bike` costs USD 80 before a 10% guest discount. [Undated bicycle rental](bicycle-rental-agreement.blue) · [Scheduled bicycle rental with cancellation terms](timed-bicycle-rental-agreement.blue) · [Automatic bicycle rental with an elapsed cancellation window](automatic-bicycle-rental-agreement.blue)

| Step | Authoring declaration | Authoritative state |
| --- | --- | --- |
| Agree on initial terms | `Activation/Activation Clause` requires seller and partner approval. A small `Features/Feature Clause` copies the negotiated initial commission rate into the effective terms on first activation. | The Agreement's activation revision and accepted terms, followed by the effective `/terms/commissionBps`. |
| Prepare an Order | `Commerce/Catalog Clause` validates the catalog. `Documents/Documents Clause` prices current selections, prepares the Order and accepts it on provision. | The prepared Order preserves its price and currency. The Agreement stores the rate in the private preparation entry for that Order. |
| Admit an Order and payment | The partner provides the prepared Order through Documents. The `selectBeforeActivation` setting allows an admitted Order to be linked while waiting for seller approval. `Payment/Payment Clause` prepares and provides the matching instruction. | Documents records `selected` for an admitted early link and `usable` once activation and readiness checks pass. The instruction confirms collection separately. |
| Accept or reject | When supplier confirmation is required, `Orders/Order with Seller Decision` binds rejection to the seller, the activation revision and the exact reviewed document. Activation owns the approval. Scheduled Orders requiring supplier confirmation use signed review evidence from Reservation. The capture condition checks the active Order and its admitted instruction. | The Order's activation and decision state. The instruction separately records requested and confirmed financial outcomes. |
| Reconcile receipts and commission | `Payment/Receipts Clause` projects confirmed customer payments. A connection invokes Ledger's `accruePercent` action for a changed receipt target. | Receipt totals and per-Order targets in `/receipts`. Ledger uses the frozen rate for that Order to update its absolute commission target under `/commission`. |
| Pay the partner | The seller prepares a separate keyed payout. Documents and Ledger reserve the available commission requested for that payout. The MyOS account-to-account instruction supplies the settlement evidence. | The Ledger reservation and its settled amount. Customer receipt totals continue to describe the customer Orders. |

The automatic bicycle-rental example is also available as annotated YAML. Its
header records the source file SHA-256 and the canonical document SHA-256
verified after loading the YAML.
[Automatic two-hour window with a 25% late charge](reseller-2h-25pct.yaml)

## Catalog and Order inputs

A buyer's selection consists of a catalog revision and lines. Each line selects
an item and a positive whole quantity. An item with a maximum quantity applies
that cap. Additional selection fields depend on its pricing and service terms.
The Agreement binds `prepareOrder` and `provideOrder` to the partner. Call
`prepareOrder` with a `Documents/Preparation Input` containing the Order `key`,
a `requestId` and `values`. Supply `catalogRevision`, `lines` and either the
customer's account ID or contact email in `values`. The cancellation and
scheduled examples group the Order lines under `booking-1`. The scheduled
example includes a requested start. Reservation records the confirmed service
start after a reviewed booking decision. The customer identity comes from the
admitted participant mapping.

When Documents emits `Documents/Document Provision Requested`, prepare the independent instance with the declared roles. The partner's `provideOrder` operation receives `key`, `inResponseTo`, `requirementRef`, and `document: {blueId: ...}`. The preparation request, requirement and native instance have separate identities. Repeat the same intent to recover the original preparation. A new intent under a used key requires a different key.

The seller calls `preparePayment` and `providePayment` on the Order. The
workflow's `documentParams` carries the Order amount, currency, initialized
identity and reviewed terms into the payment preparation. Its `inputParams`
selects the supplied provider reference. The customer is payer, the seller is
payee, and the admitted provider is guarantor. The cardholder's checkout and
authorization can precede seller approval. Only the active, admitted Order and
its matching instruction can satisfy the configured capture condition.
The guarantor's later financial confirmation establishes the amount captured.

After activation, seller and partner can approve separate amendments for the
catalog and effective commission. Both use `Amendments/Amendments Clause`.
The catalog sets `parameters.replacementValidator` to the
`validateCatalogReplacement` function from `Commerce/Catalog Functions`.
The function takes the current and proposed catalog values. The proposed
catalog must advance the revision by one and preserve the currency and supplier.
The emitted Agreement pins the clause and the function definition by BlueId.

```yaml
replacementValidator:
  definition:
    type: Commerce/Catalog Functions
  function: validateCatalogReplacement
```

The commission replacement must satisfy the configured rate schema, including
its minimum when declared. Both approvers review the exact proposal document.
A competing amendment that has already advanced the same revision prevents a
stale proposal from replacing it. New preparations use the amended price and
rate. A preparation already recorded in the Agreement keeps its original
amount and rate.

## Compose supplier approval with a reviewed reservation

A scheduled Order requiring supplier confirmation has one reviewed-approval
entry at `/orderTemplate/clauses/activation/parameters/reviewedApprovals/seller`.
The authored names below correspond to exact public BlueIds in the emitted
Agreement. The event selector uses a published type, the mounted Schedule clause
and the booking group. The standard Contracts channel accepts that type and
its subtypes. Give independently approved roles distinct source-clause and
subject combinations to avoid overlapping matches. The other pointers refer
to the current Order. A direct-only review can omit `acceptanceBy`.

```yaml
reviewedApprovals:
  seller:
    event:
      type: Schedule/Reservation Reviewed
      clause: reservation
      subject: booking-1
    source: /reservations/booking-1
    basis: /amountMinor
    acceptanceBy: customer
```

Reservation records the decision for the signed, reviewed booking and emits
`Schedule/Reservation Reviewed`. Activation checks the event against the signed
operation actor and request digest, configured booking record digest, current
amount and current access. Direct seller confirmation can approve the seller's
current Order terms. A seller alternative records a scoped grant. The customer
can accept that exact alternative through the configured `acceptanceBy` role.
Activation checks the grant against the current party roster, Order identity,
revision and terms, exact proposal and amount, then consumes it when approving
the seller's role. Activation guards ordinary direct approval and activation for
that role so the selected review governs its acceptance. The booking record and
Activation state retain their separate meanings.

The public event card describes the exact reference.
[Reservation Reviewed](../../../semantics/cards/4sVucwHteBZg8zTK6sEE8ezV8Wzg9g4rMhRPZswg9Ujc.json)

The `fundedReview` group guards all three native Schedule actions.
Scheduled Orders without supplier confirmation do not mount a reviewed-approval
entry. Undated supplier confirmation continues through the ordinary Activation
operation. Capture continues to require the active Order and its exact selected
Payment Instruction, and scheduled capture requires a confirmed reservation.

## Compose an optional cancellation policy

A captured bicycle rental costs USD 72 after the guest discount. The automatic
example grants two free cancellation hours and retains 25% on late cancellation.
The template also supports checkout without a cancellation policy and a cutoff
before confirmed service. The Order accepts the commercial decision. Its
Payment Instruction applies the financial adjustment. The Agreement derives
receipts and commission from confirmed amounts.

| Clause | Declaration in this template | State in this template |
| --- | --- | --- |
| `Connections/Remember First Timestamp` | `startFromEntry` observes the Order's first activation. The automatic elapsed variant also configures `startFromFallback` and supplies the verified selected instruction's authorization time. | `result` points to `/clockStartMicros`. The optional `unavailable` binding points to `/clockStartUnavailable`. |
| `Payment/Secure Timestamp Projection` | Connects `record` to the instruction's own `Funds Secured` event and validates the full original `secureFunds` on the guarantor channel. | `fact` stores `timestampMicros` and `requestId` at `/securedTimestamp`. |
| `Commerce/Whole Order Cancellation Policy` | The customer calls `cancelOrder` through `accept`. The seller calls `cancelBySupplier` through `acceptWithoutCharge`. Both require the exact reviewed Order version. | `/cancellationDecision` records the accepted decision. `/cancellationAvailability` projects timing and readiness. |
| `Payment/Payment Process Clause` | A named `parameters.adjustments` entry links the accepted decision and selected original instruction. One `adjust` connection group can reevaluate it on the configured order and payment events. | The instruction records native requests and their separately confirmed outcomes under `/payment`. |

### Select the start of the elapsed window

The first native Order activation supplies the primary time. For example, if
the selected instruction was fully authorized at **10:00** and the first Order
activation has native time **10:03**, the two-hour window starts at **10:03** and
remains free through **12:03**. The native clock proof selects **10:03** when
the fallback fact is observed before, during, or after that activation.

Only the automatic elapsed configuration supplies an authorization fallback.
An actual activation without a native timestamp sets
`/clockStartUnavailable`. An invalid primary timestamp leaves that marker unset. The fallback requires
true at both `ready` (`/activation/active`) and `sourceReady`
(`/activation/accessReady`). It reads the verified timestamp from
`/payment/securedTimestamp/timestampMicros` on the selected instruction.
Its connections recheck the fact on authorization, attachment, access
restoration, or when the marker first appears. The first accepted result stays
fixed. An absent `/clockStartMicros` means the elapsed window has no recorded
start.

For a scheduled Order, `serviceStart` reads
`/wholeOrderReservation/confirmedStartMicros` through Reservation's
`wholeReservation` projection. A service-relative window uses the confirmed
start to compute its cutoff. The earlier cutoff governs when both timing
conditions apply, and cancellation at the cutoff remains free. Ordinary
cancellation closes when confirmed service starts. An explicit zero-hour
service cutoff allows cancellation at the exact start time.

A shared `Payment/Secured Amount Condition` guards `confirm`, `alternative`,
and `accept`. In the emitted Order template it is mounted at
`/orderTemplate/clauses/reservation/parameters/conditionGroups/fundedReview`.
The group supplies four current-Order pointers.

| Input | Path in this template |
| --- | --- |
| `instruction` | `/payment` |
| `amountMinor` | `/amountMinor` |
| `revision` | `/activation/revision` |
| `termsRef` | `/activation/terms/ref` |

Documents selects and manages the initialized Payment Instruction at `/payment`.
The condition reads that slot at execution time. Its frozen Order revision and
terms reference must match the current review. Its charging state must be open with no cancellation
pending. Available secured funds equal the current secured amount minus
capture and void reservations. They must cover the reviewed amount in minor
units. Unsatisfied funding rejects the workflow before a booking change, using
the ordinary `ACTION_CONDITION_FAILED` result.

The emitted condition type is `55uaSTukUDkmtxRzCWRmXZuT7SF1MTfuxCYiCmQbNDiv`. Its public card is available by that
exact BlueId. [Secured Amount Condition](../../../semantics/cards/55uaSTukUDkmtxRzCWRmXZuT7SF1MTfuxCYiCmQbNDiv.json)

The customer can cancel free before required supplier confirmation. The
automatic elapsed variant configures `beforeWindowStarts: free` while the
clock is still unstarted. A positive late charge in this template requires the
confirmed capture of the original instruction to match the whole Order amount.
The Order supplies that evidence through `retentionBasis`.

The policy records the key, reason, basis, retained amount and amount to release
in one accepted decision. A matching retry leaves the accepted decision fixed.
The policy emits `Commerce/Domain Event` with kind `Order Cancellation Accepted`
and the decision key as `entityId`. A single grant for Cancellation's
`refreshAvailability` action uses `observations: true` to let its declared
observations and automatic refresh run before activation.

The seller-confirmed Order inherits the `orderOpen` policy from its type.
Its `contracts.orderOpen.constants` supplies the accepted cancellation state
when cancellation is configured and the Reservation actions when a booking is
scheduled. The policy blocks relevant seller approval, rejection and booking
operations when the Order has closed. Commerce binds `orderStatus` to
`/orderDecision/status` and sets
`closedOrderStatuses: [REJECTED]`. A matching status rejects either new decision
action with `ORDER_CLOSED`. The seller rejection replaces `/orderDecision`, so
`refreshAvailability.afterOrderStatusChange` watches that object. The
`orderStatus` binding reads `/orderDecision/status`. Before acceptance,
the refresh projects `unavailable` with reason `order_closed` after rejection.
An accepted decision keeps its `cancelled` projection and supports matching replay.

A scheduled cancellation also connects the accepted event to Reservation's
`close` action. Its `params.reason` reads the immutable
`/cancellationDecision/reason` so the booking records the reason actually
accepted on the Order.

### Declare the payment adjustment

The Payment Instruction's `parameters.adjustments` describes the decision to
observe, its accepted status and the field supplying the retained amount.
The shared `parameters.selectedPayment` names the Order source, its expected
origin and the exact prepared payment selection for both rules. The declared
`requestIds` identify each refund and authorization release. The ordinary
`bindings.adjust` reacts to the Order decision and changes in the linked
documents or payment results. When the Order emits `Documents/Document Selected`
for its `payment` clause and `single` item, the instruction checks for a decision
that was already accepted before the link. This can release a hold while the
Order is still pending. Attachment and access recovery also wake reconciliation.

`capture.blockedBy` names the adjustment whose matching decision closes the
automatic capture route. A scheduled Order also declares `capture.requires`
for confirmed service. Both checks apply in addition to the existing capture
predicate for the active Order and selected instruction. The separate seller
rejection mapping specifies zero retained amount and enables authorization
release.
The `Selected Order Capture` type supplies the capture mode, and
`paymentDetails.method` selects the MyOS customer payment provider method.

The adjustment reduces confirmed net collection to the declared retained
amount. A captured payment refunds the excess of confirmed capture after prior
confirmed refunds. A zero target can also release the remaining confirmed
authorization. Native payment guards wait for outstanding requests and use stable request IDs
on replay. Each enabled leg can be requested only under its declared ID. The guarantor separately confirms the native
refund or release.

For example, late cancellation of the captured USD 72 Order sets the target
to 1,800 minor units and asks for a refund of 5,400. If 1,200 has already been
refunded, the remaining refund is 4,200. While the new refund is pending, the
confirmed net receipts and commission stay at their last confirmed values.
After the whole 5,400 refund is confirmed, receipts record 7,200 gross and
1,800 net. Ledger applies the frozen 1,250 basis-point rate and updates the
commission target to 225 minor units.

### Authored BEX in the generated examples

These counts compare the same eight authoring configurations before typed
funding (`dff068b3`) and with the reviewed approval composition
(`a8b9be88`). The newer composition adds no authored BEX to the eight cases
compared with `08643a2c`.
The metric counts each occurrence of an object key beginning with `$` in the
emitted document, including embedded Order and instruction templates.

| Configuration | Earlier source | Reviewed approval source |
| --- | ---: | ---: |
| Automatic, no cancellation policy | 2 | 2 |
| Supplier confirmation, no cancellation policy | 2 | 2 |
| Automatic, elapsed window | 2 | 2 |
| Supplier confirmation, elapsed window | 2 | 2 |
| Scheduled, no cancellation policy | 19 | 2 |
| Scheduled, elapsed window | 20 | 3 |
| Scheduled, service-relative cutoff | 20 | 3 |
| Scheduled, elapsed and service-relative cutoffs | 20 | 3 |

The two operators in the small commission initialization Feature remain in
every example. Scheduled Orders reuse Payment’s typed secured-amount condition.
When they include cancellation, one more operator reads the accepted reason
for closing the booking. The current Payment Instructions, payout templates
and clock declarations have zero authored BEX occurrences.

## Payout inputs and accounts

The seller calls `startPayout` with a stable `key`, gross `amountMinor` and
the integration's `accountContext`. It supplies `payerBinding`,
`payeeBinding`, `platformAccountId` and `environment`. Preparation freezes
the gross, fee and net split under `/paymentDetails/payoutTerms` on the
payout instruction. The seller provides the payout under the matching
Documents requirement. The partner is the payee and the authorized operator
is the guarantor. The Agreement must provide the admitted operator account before payout preparation. The instruction amount is the net transfer. A payout
smaller than the available commission still executes its own full frozen
net amount.

The guarantor calls `confirmAccountSettlement` on the payout instruction's
MyOS payment method. It supplies `debitReference` and `transferReference`
for the accepted transaction. Ledger counts the gross
amount as paid after the report and confirmed net transfer both match the
frozen payout. It records fee and transferred amounts separately. Pending
or unknown financial requests keep the reservation open. An authoritative
rejection, failed securing or confirmed void can release it when there is
no outstanding effect or settlement report.

## What an authorized reader can show

The Receipt clause binds `orders` to the managed collection and `entries` to its Documents preparation entries. Its `instruction` points inside each Order. The defaults are `/orders`, `/process_orders/entries` and `/payment`. The clause reads the linked Payment Instruction when the Order emits a matching completion or post-completion reversal. It can also catch up when a usable Order is attached after the payment changes. The maintained target uses the instruction's cumulative `/payment/completed` and `/payment/reversed` amounts. The same target can be observed again without adding money twice.

| Default path | Meaning |
| --- | --- |
| `/receipts/currency` | Currency from the contributing Payment Instruction. It must match the configured currency when one is set and the currency already projected. Before any projection, the currency is absent. |
| `/receipts/grossConfirmedMinor` | Cumulative confirmed customer captures in minor units, before refunds. |
| `/receipts/refundsMinor` | Cumulative confirmed customer refunds in minor units. |
| `/receipts/netReceivedMinor` | Confirmed customer captures less confirmed refunds in minor units. |
| `/receipts/targets/<orderKey>` | The same three amounts for one Order. A missing target means no projection has been recorded for that Order. |
| `/commission/accrued`, `/commission/reserved`, `/commission/paid` | Ledger totals for commission targets, outstanding payout reservations and settled commission, in Agreement currency. |

For example, a confirmed partial capture of 6,000 minor units contributes 6,000 gross and net. If the seller requests a 2,500 refund, both figures stay at 6,000 while the request is pending. Once the instruction confirms the refund, the contribution is 6,000 gross, 2,500 refunds and 3,500 net. At the Order's frozen 1,000 basis points, its commission target moves from 600 to 350. A payout reservation is a commitment against accrued commission. The matching payment outcome settles the reservation. A later customer refund
can reduce accrued commission. Paid commission continues to record the
confirmed payout outcome.

Use the field names, descriptions, units, binding metadata and the current authorized document to present these values. Resolve binding overrides from the instance. Missing data is unknown. The initial zero totals apply after initialization. Private data requires access to its owning Agreement. The Order and its Payment Instruction carry the customer's price and payment terms. The effective commission snapshot stays in the Agreement and is absent from their customer-facing source and payment terms. A semantic card describes shared behavior for one exact public type, while the authorized document supplies values and permissions.

## Current and Better authoring

The current example uses ordinary package types, parameters, pointers, connections and typed requests. The Receipt clause and the prepared-document and Ledger actions own reusable behavior. The local Feature carries the Agreement-specific rule for moving its negotiated rate into its active terms. The generated source uses exact BlueIds. The declaration below uses its type name.

```yaml
quoteCommission:
  type: Features/Feature Clause
  parameters:
    actions:
      initializeRate:
        do:
        - $appendChange:
            op: add
            path: /terms/commissionBps
            val: {$document: /terms/initialCommissionBps}
  bindings:
    initializeRate:
      firstActivation: {'on': activated, once: true}
```

The Better source comparison uses `blue-packages-better` at `249c22b4cb6ee96265756e606b93ea99fa0fd05e` and `blue-java-better` at `c946cf43f820ddd7902ab19f9feeef2931f5f432`. Better already provides authored BEX Features, typed connection arguments and conditions, explicit document sources, separate selection and readiness, and keyed Ledger targets. Better's Commerce package provides Product Clause for document-owned quotes. Better's Complete Evidence and Attested Observation packages provide distinct models for observing independent sources.

The current Agreement uses the active Access Events catalogue's catalog snapshots, receipt projection and MyOS payout settlement. An equivalent Better profile would need those authored workflows verified under its own execution declarations, package identities and observation strategy.

Saved agreements use their original exact definitions. [Legacy checkout editions](../../reseller/README.md)

## Reproduce the source

From the matching Go checkout, generate the example with the normal authoring
entry point. Set `BLUE_PACKAGES_ROOT` to the Blue Packages checkout that supplies
the exact pins.

```sh
node --import tsx --input-type=module - <<'JS'
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { configuredSource } from "./server/v2/agreement-drafts/template.ts";

const configuration = process.env.RESELLER_EXAMPLE ?? "bicycle-rental-configuration.json";
const fixture = JSON.parse(readFileSync(join(
  process.env.BLUE_PACKAGES_ROOT,
  "examples/sales/declarative",
  configuration,
), "utf8"));
const source = configuredSource(fixture);
process.stdout.write(`${JSON.stringify(JSON.parse(source), null, 2)}\n`);
JS
```

From the Blue Packages root, render the tracked automatic example with English role
comments using Python and PyYAML. The renderer names the active package exports
beside their literal BlueIds and compares the loaded YAML to the source before
printing it.

```sh
python3 examples/sales/declarative/render-annotated.py examples/sales/declarative/automatic-bicycle-rental-agreement.blue > reseller-2h-25pct.yaml
```

Use `timed-bicycle-rental-agreement.blue` for a scheduled Order with supplier
confirmation and `bicycle-rental-agreement.blue` for a plain Order without cancellation terms.

From Blue Packages, use Java 21 and the qualified `BLUE_JAVA_CLASSPATH` to
run the focused native cases against the matching built packages.

```sh
python3 tools/check_operation_inputs.py \
  --case declarative-order-preparation --case declarative-commerce \
  --case declarative-order-decision --case declarative-receipts \
  --case whole-order-cancellation --case schedule-reservation \
  --case declarative-timed-payment-init --case connections-condition-groups \
  --case declarative-account-payouts --case declarative-stripe-payout-preparation
```

Native checks exercise the authored rules and modeled outcomes in the local
runtime. Stripe checkout and account transfers use their provider integration.
