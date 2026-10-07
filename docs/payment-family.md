# Payment family and connected commercial documents

This is an **unpublished candidate**, version `0.5.0-preview.1`. Its package sources live in this repository. Core consumes exact compiled distributions; it does not maintain a second authoritative copy of these definitions. No release tag or external publication is created by the build.

## Package boundaries

| Project | Authoring namespace | Purpose |
| --- | --- | --- |
| `payment-instruction` | `PaymentInstruction` | Payment Instruction, clause-enabled host, financial lifecycle, conditional policy, reservations and compensation. |
| `clause-payment` | `Payment` | General `Payment Clause` for an explicit PI template; `Conditional Payment` for a standard condition-driven authorization/capture process. |
| `blue-parties` | `Parties` | Provider-independent business `Party` data. |
| `myos` | `MyOS` | `MyOS Party`, `MyOS Customer Payment`, `MyOS Account to Account Payment`, customer-session behavior and account-locator normalization. |
| `acme-bank` | `ACME` | An illustrative bank-confirmed payment profile. ACME is an abstract provider name. |
| `manual-payments` | `ManualPayments` | A direct-transfer process with payer reporting and recipient confirmation. |
| `clause-connections` | `Connections` | Reusable actions connected to workflows, events, embedded documents, collections, changes, initialization or timers. |
| `clause-documents` | `DocumentsV3` | Idempotent document creation, explicit inherited channels, shared sources and nested instance identity. |
| `clause-state-machine`, `clause-activation`, `clause-amendments`, `clause-termination` | `State`, `Activation`, `AmendmentsV3`, `Termination` | Independent state transitions, exact acceptance, governed data changes and wind-down. |
| `clause-commerce`, `clause-features`, `clause-balance`, `clause-referrals`, `clause-schedule`, `blue-money` | Corresponding manifest namespaces | Product and business features, attributed obligations, financial projections, time actions and exact money arithmetic. |
| `clause-participants`, `clause-participants-access` | `Participants`, `AccessParticipants` | Existing admitted-channel validation and explicit Timeline Access guards, rebuilt against this clause edition. |

`PAYMENT-FAMILY-SOURCES.json` is the build order. `PAYMENT-FAMILY-PACKAGES.json` records exact identities, archives and the qualified native dependency selection. `blue-agreements-connected` provides the clause-enabled Agreement host without replacing the older `blue-agreements` publication. Old editions and existing documents keep their identities.

## One payment, one PI

The host clause creates one independently processed Payment Instruction and echoes its typed events with the host clause key and instruction path. The PI owns accepted terms, operation authority, financial requests, outstanding reservations and confirmed results. Several payments require several clause instances or generated documents.

A request is not money movement. Native BEX emits an instruction; an external executor performs and reconciles the corresponding work, then reports through its admitted channel. These packages never call an HTTP payment API while replaying a document.

The supplied method examples are executable **document protocols with test confirmations**, not live bank adapters. There is no checkout website, banking connection or real account-balance service included here.

Method packages share `Payment/Conditional Payment Base` and its common setup functions. The standard preset and each method supply their own setup definition. They do not overwrite an inherited BEX function body: Blue inheritance preserves fixed content, so replacing such a body would incorrectly merge two programs. This separation keeps the common financial behavior in Payment Instruction while allowing different initialization protocols.

## MyOS Party and account locators

```yaml
parties:
  customer:
    type: MyOS/MyOS Party
    partyId: alice
    displayName: Alice
    myosAccountId: alice
  seller:
    type: MyOS/MyOS Party
    partyId: bob-school
    displayName: Bob Language School
    myosAccountId: bob
```

`MyOS Party` specializes `Parties/Party` with `myosAccountId`. A Party identifies the business participant; an account locates its representative in this initial profile. Names and account IDs do not prove legal identity or grant operation authority.

For MyOS payments, each selected account must resolve to exactly one declared party and corresponding admitted channel. A direct ID and a party object are alternative inputs to the same resolver:

```yaml
clauses:
  lessonPayment:
    type: MyOS/MyOS Customer Payment
    parameters:
      recipient: bob
      amountMinor: 10000
      currency: EUR
      requireAll:
        satisfied:
          on: workflow
          channel: customer
```

For a payment between accounts:

```yaml
clauses:
  milestonePayment:
    type: MyOS/MyOS Account to Account Payment
    parameters:
      payer: alice
      recipient:
        type: MyOS/MyOS Party
        partyId: bob-school
        displayName: Bob Language School
        myosAccountId: bob
      amountMinor: 10000
      currency: EUR
      requireAll:
        approveMilestone:
          on: workflow
          channel: customer
```

These fragments require the surrounding party declarations and participant channels. Complete fixture-bound documents are in `examples/payment-family`. The resolver takes the canonical party snapshot from the declared roster, not arbitrary extra fields submitted in a locator object. Unknown or ambiguous accounts fail. An account-to-account payment cannot use the same account on both sides.

For authenticated Core bootstrap use `15-myos-customer.bootstrap.blue` or `16-myos-account.bootstrap.blue`. They omit fixture `External Channel` declarations so bootstrap can supply the real timeline channels. Resolve `customer`, `seller` and `guarantor` to real accounts, and replace `alice`, `bob` and `payment-operator` in the party roster with those same account IDs. Do not submit fixture-only external channels as account identity claims.

Core bootstrap resolves real accounts through its account directory and requires each root MyOS Party to match the corresponding resolved participant. A raw document using fixture channels does not acquire that authentication guarantee. An executor must use verified channel/account binding, not trust an arbitrary account-ID string in an imported document.

The selected parties and payment details are copied into the new PI. Editing the parent roster does not silently change an existing PI. This initial Party type does not implement the entire proposed lead/delegate governance model. Required readers, operation actors and business parties remain separate concerns; a reader does not acquire payment authority.

## The four concrete flows

### MyOS Customer Payment

1. The host starts a PI and it emits a customer-session request.
2. The operator accepts the instruction through `accept`.
3. The operator supplies a stable session reference through `provideSession`.
4. After the external customer flow, the operator reports `confirmFunding` for that same session.
5. Only then can `initiate` bind the payment transaction and cause the authorization request.
6. The operator confirms authorization. Capture waits for all configured evidence.
7. A capture request is followed by a separately confirmed result.

`confirmFunding` is an attributable operator report that the customer funding flow is ready; it is not itself a captured-money result. The package does not invent a payment URL or accept a browser redirect as proof of success. Initiating before this stage, or confirming a different session ID, is rejected.

### MyOS Account to Account Payment

There is no customer-session phase. Both payer and recipient must resolve to declared MyOS parties. The operator accepts and initiates the instruction. In this profile, `secure` requests an external funds reservation and `capture` requests execution of the transfer. The PI tracks outstanding requests and confirmed amounts; it does not itself hold or reserve a bank-account balance. Confirmations come from the operator. A real adapter must enforce balances, authorization and idempotent external execution.

### ACME Bank Payment

The nominated bank/guarantor channel accepts the instruction and confirms authorization, capture, release and refund results. The package emits bank-specific execution requests while reusing the financial ledger and mandatory conditions. ACME is an illustrative bank contract, not an installed live integration.

### Manual Bank Payment

```yaml
clauses:
  invoice:
    type: ManualPayments/Manual Bank Payment
    parameters:
      payer: customer
      recipient: seller
      amountMinor: 2500
      currency: EUR
```

The recipient accepts; the payer invokes `reportTransfer` with a stable reference; the recipient invokes `confirmReceipt`. Only receipt confirmation marks the payment paid. A repeated reference is harmless, and a conflicting replacement is rejected. For a full refund, the recipient invokes `requestRefund` and the original payer confirms receipt with `confirmRefund`.

This process does not create an artificial card authorization. Receipt confirmations are participant assertions. Partial manual refunds, disputes and independent bank reconciliation are outside this profile.

## Connections and conditions

A clause action supplies reusable BEX steps. Connections specify when to invoke them, how to obtain parameters and what local validation or follow-up to perform:

```yaml
bindings:
  requestCapture:
    capturePart:
      on: workflow
      channel: customer
      params:
        requestId: {$var: {name: trigger, path: /requestId}}
        amountMinor: {$var: {name: trigger, path: /amountMinor}}
      before:
        - $failIf:
            cond: {$lte: [{$var: {name: params, path: /amountMinor}}, 0]}
            message: Positive amount required
      after:
        - $appendEvent: {kind: Capture Request Admitted}
```

This is an explicit PI lifecycle-clause fragment, not a new public field on every payment preset. The lifecycle still enforces its mandatory capture gate and available amount. `after` records a newly admitted local request, not a completed external payment.

Available source forms remain `workflow`, `event`, `embedded`, `collection`, `change`, `initialized`, `timer` and `channel`. Mapped `params` are evaluated before `before`. `when` skips an inapplicable connection; `before` validates; the action returns an explicit result; `after` runs only for `acceptedNew` on actions using `outcome-v1`. A one-time connection is not a substitute for a financial idempotency key.

Several connections are alternative routes to an action. Several named entries in `requireAll` are distinct prerequisites that must all hold. Workflow/event facts are retained; `observe` reads current accepted state from an explicitly included source. It does not fabricate an earlier event.

The examples use pure validation in `before`. This release does not claim a compiler-enforced effect sandbox through arbitrary called functions.

## Shared documents and cycles

PI-local workflows require no parent cycle. A PI that must inspect its host can explicitly include the host through `includeOrder`; `sources` supplies other initialized document references. In the general Payment Clause, the corresponding controls are `hostSource` and `sourcePaths` on an explicit PI template.

These are references to independently identified documents, not recursive YAML copies. Access to every required input is still necessary. A production cycle must satisfy Timeline Access for its required readers; copying a public key or account ID into these parameters does not grant access.

## Failure, retry and accounting guarantees

- New financial commands reserve capacity; pending and unknown results retain it.
- Every new capture checks the configured PI gate, including custom manual request routes.
- Duplicate financial requests are recognized by ID and intent before fresh financial eligibility checks.
- A failed service retains its compensation obligation. A late successful capture produces a refund request rather than leaving captured funds unnoticed.
- A retry identifies both its own command ID and a definitive failed ledger request. A failure can authorize one new attempt; unresolved requests must be reconciled first.
- Completion uses cumulative confirmed amounts and business prerequisites. A partial capture does not imply complete payment.
- Commission corrections preserve previously confirmed payouts. A negative remaining obligation is not silently treated as money recovered.
- Wind-down stops new admissions while allowing already accepted obligations to settle.

These local guarantees do not provide exactly-once bank execution. The external adapter needs durable request discovery, transaction correlation, idempotency, bounded retry and reconciliation.

## Executable examples

| Example | Demonstrates |
| --- | --- |
| `00-hello` | Small action/connection baseline. |
| `01-simple-payment` | Standard conditional payment without provider-specific identity. |
| `02-custom-service` | Explicit PI, partial capture and mandatory policy gates. |
| `03-compensation` | Failure while capture is pending, followed by late success and refund. |
| `04-preexisting-evidence`, `14-late-evidence` | Current-state observation and late evidence. |
| `05-booking-amendments`, `06-smart-property` | Accepted amendments and external document conditions. |
| `09-membership`, `10-ledger`, `11-custom-hooks`, `13-explicit-failure-filter` | Generated periods, obligations, hooks and filtered reactions. |
| `15-myos-customer`, `17-myos-party` | Recipient supplied by ID or by Party; customer-session guards. |
| `16-myos-account` | Account-to-account payment with mixed locator forms. |
| `18-acme-bank`, `19-manual-bank` | Bank-confirmed and manually confirmed methods. |
| `20-partnership` | Nine documents, customer payments, a separate account payout, compensation and commission correction, without mandates. |
| `21-retry-entitlements` | A definitive failed financial request permits one retry; unresolved work and reused entitlements are rejected. |
| `22-frozen-parties` | Changing the host party's description does not rewrite the existing PI's party snapshot. |

In the partnership, seller and referrer approve a referral agreement. Customer and seller approve procurement. The customer directly creates two Orders. Each Order has independent delivery evidence and a PI. Delivery plus acceptance permits collection; confirmed collection earns commission. A separate PI pays the referrer. A later failed Order is refunded and the commission is corrected without erasing the payout. Winding down rejects another Order.

## Build and verify

Use JDK 21 and the qualified Core Java classpath:

```sh
export JAVA_HOME=/path/to/jdk-21
export BLUE_JAVA_CLASSPATH='/path/to/qualified-runtime-jars/*'
bash tools/build-payment-family.sh
python3 tools/check_payment_family.py
```

The optional comma-separated namespace argument to the build script is a development-only partial rebuild. Before distribution, rebuild the complete selection and check every dependency lock. The shared repository contains data packages and authoring sources, not copied runtime JARs.

From the corresponding Core branch:

```sh
python3 scripts/payment-family-import.py --packages-dir /path/to/blue-packages --write
./runtime/gradlew -p runtime :blue-core-service:paymentFamilyExamples \
  -PbluePackagesDir=/path/to/blue-packages --no-daemon
```

The import is opt-in catalogue preparation; it does not alter existing accounts or migrate live PIs. Native scenarios check resulting state, rejected operations, exact replay gas/receipts/snapshots and selected snapshot restores. Core's authenticated bootstrap and timer/restart integration tests are separate checks. Detailed results belong to ignored local reports and must name the tested revisions.

## Remaining product boundaries

This package edition is not a production payment service. Live rails, customer web sessions, full representative governance, general read-only observer bootstrap, deployment-specific reliability, disputes and regulatory requirements are not established by these document scenarios. Java/Python behavioral parity is not claimed by Java-only qualification. All proposed future capabilities must remain distinguishable from exported, tested types.
