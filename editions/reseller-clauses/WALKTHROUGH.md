# Reseller Agreement: vouchers, purchases, timers and commission

[Open the deployed walkthrough](https://dio5ez9021fgv.cloudfront.net/#documents/4cd43c6e-340a-41da-9578-30aa3395777c).

The Agreement is a relationship between a Merchant and a Reseller. It creates voucher Orders from its own `orderTemplate`. Each Order gets the requested amount, its own original document identity and a one-minute purchase deadline. A confirmed purchase earns the Reseller 10%; an expired Order earns nothing.

This demonstration records purchase confirmation. It does not charge a card, settle money, reserve external inventory or initiate a payout.

The app currently uses a temporary host execution budget of **1,000,000 gas per invocation**. The published Contracts specification and standard 100,000-gas policy have not been changed; replaying these documents elsewhere requires the same host override. The actual budget is included in saved invocation policies and reported by `/api/blue/v1/info`.

## What the clauses say

| Document | Clause | Plain-language explanation |
|---|---|---|
| Agreement | Participants | Merchant and Reseller use separate authenticated timelines. |
| Agreement | Product | We sell EUR gift vouchers. The amount is supplied when an Order starts. |
| Agreement | Amendments | The Merchant can edit draft clauses. Invalid edits are rejected. Activation freezes the configuration. |
| Agreement | Activation | Both parties mark the current terms ready, then approve the same configuration. |
| Agreement | Termination | Either party can end new business; existing Orders retain their own lifecycle. |
| Agreement | Documents | Once active, the Reseller can create uniquely keyed Orders from `/orderTemplate`, stored in `/orders`. |
| Agreement | Listener | Observe Orders in `/orders`; run different steps for readiness, purchase and cancellation. |
| Agreement | Balance | Each distinct purchased Order credits 10% of its amount to the commission balance. |
| Order | Participants | The customer operation uses the Reseller's timeline in this demo. |
| Order | Product | This is a named voucher with the amount supplied in `startOrder`. |
| Order | Purchase | Confirm once, before the deadline; record confirmation and emit Purchase Confirmed. |
| Order | Timer | Start a one-minute timer at Order creation. If the Order is still pending, cancel it. Purchase confirmation cancels this timer. |

The Merchant and Reseller timelines are both controlled by your account for this walkthrough. These demonstrate distinct authorization routes; they are not a claim that two separate real people approved anything.

## 1. Create a fresh Agreement

Open **Documents → Add new**, paste this YAML and start it. The default workspace already includes the packages. Missing source timeline bindings are created automatically. The same source labels inside the Agreement and Order template resolve to the same timelines.

```yaml
name: Reseller Agreement
description: Merchant and Reseller approve these terms. Reseller starts voucher orders;
  each purchase earns 10% commission. Unpurchased orders cancel after one minute.
type: Agreements / Agreement with Clauses
orderTemplate:
  name: Voucher Order
  type: Orders / Order with Clauses
  orderId: template
  instanceKey: template
  startedAt: 0
  clauses:
    participants:
      type: Participants / Participants Clause
      parameters:
        participants:
          customer: &id001
            name: Reseller
            channel:
              type: Coordination / Timeline Channel
              timeline:
                timelineId: voucher-reseller
              actor:
                accountId: reseller
    product:
      type: Products / Product Clause
      parameters:
        product:
          type: Products / Fixed Product
          name: Gift voucher
          description: A voucher for its face value, denominated in EUR.
          currency: EUR
          amountMinor: 10000
    purchase:
      type: Orders / Purchase Clause
      parameters:
        durationMicros: 60000000
        timerChannel: expiryClock
        timerKey: purchase-deadline
      bindings:
        customer: customer
        product: /clauses/product/parameters/product
    expiry:
      type: Timing / Timer Clause
      parameters:
        key: purchase-deadline
        cancelOn:
          type: Orders / Purchase Confirmed
        scheduleAt:
          $add:
          - $document: /startedAt
          - 60000000
        steps:
        - type: Orders / Cancel Purchase Step
      bindings:
        channel: expiryClock
clauses:
  participants:
    type: Participants / Participants Clause
    parameters:
      participants:
        merchant:
          name: Merchant
          channel:
            type: Coordination / Timeline Channel
            timeline:
              timelineId: voucher-merchant
            actor:
              accountId: merchant
        reseller: *id001
  product:
    type: Products / Product Clause
    parameters:
      product:
        type: Products / Fixed Product
        name: Gift voucher
        description: A voucher for its face value, denominated in EUR.
        currency: EUR
  amendments:
    type: Amendments / Amendments Clause
    parameters:
      operations:
        changeClause: merchant
  activation:
    type: MutualActivation / Mutual Activation Clause
    parameters:
      participants:
      - merchant
      - reseller
    bindings:
      state: /activation
      termination: /termination
      ready: ready
      approve: approve
      decline: decline
      reset: resetApproval
  termination:
    type: ImmediateTermination / Immediate Termination Clause
    parameters:
      operations:
        terminate_merchant: merchant
        terminate_reseller: reseller
    bindings:
      state: /termination
      activation: /activation
  orders:
    type: Clauses / Document Factory Clause
    parameters:
      operation: startOrder
      namePrefix: Voucher Order
      keyField: orderId
      arguments:
      - name: amountMinor
        path: /clauses/product/parameters/product/amountMinor
        kind: integer
        minimum: 1
        maximum: 1000000000000
    bindings:
      actor: reseller
      template: /orderTemplate
      context: /orders
      activation: /activation
      termination: /termination
  commission:
    type: Balance / Balance Clause
    parameters:
      currency: EUR
    bindings:
      state: /commission
  ordersListener:
    type: Clauses / Listener Clause
    parameters:
      sources:
      - name: purchase-confirmed
        type: Contracts / Embedded Node Channel
        event:
          type: Orders / Purchase Confirmed
      - name: order-cancelled
        type: Contracts / Embedded Node Channel
        event:
          type: Orders / Order Cancelled
      - name: order-ready
        type: Contracts / Embedded Node Channel
        event:
          type: Orders / Order Ready
      steps: []
      reactions:
        purchase-confirmed:
        - type: Balance / Credit Balance Step
          constants:
            statePath: /commission
            rateBps: 1000
            sourcePath: /input/event/documentId
            amountPath: /input/event/amountMinor
            currencyPath: /input/event/currency
        - type: Contracts / Update Document
          changeset:
          - op: add
            path: /purchasesConfirmed
            val:
              $add:
              - $document: /purchasesConfirmed
              - 1
        order-cancelled:
        - type: Contracts / Update Document
          changeset:
          - op: add
            path: /ordersCancelled
            val:
              $add:
              - $document: /ordersCancelled
              - 1
        - type: Contracts / Trigger Event
          event:
            kind: Voucher order expired
            orderId:
              $event: /input/event/orderId
        order-ready:
        - type: Contracts / Update Document
          changeset:
          - op: add
            path: /ordersReady
            val:
              $add:
              - $document: /ordersReady
              - 1
      states:
        0count:
          path: /purchasesConfirmed
          kind: integer
          initial: 0
        1count:
          path: /ordersCancelled
          kind: integer
          initial: 0
        2count:
          path: /ordersReady
          kind: integer
          initial: 0
    bindings:
      context: /orders
```

The Order template is a definition, not a running Order. The Documents list will show each instantiated Order after `startOrder` runs.

## 2. Try an operation before activation

In **Operations**, choose `startOrder`, keep its allowed Reseller timeline selected, and paste:

```yaml
key: before-activation
amountMinor: 10000
```

The entry is processed, but the operation emits `AGREEMENT_NOT_ACTIVE`. `/orders` remains empty. A rejected business operation is distinct from a server failure: inspect **History** and the emitted event.

## 3. Make an allowed draft amendment

Choose `changeClause` on the Merchant timeline:

```yaml
action: update
key: product
clause:
  type: Products / Product Clause
  parameters:
    product:
      type: Products / Fixed Product
      name: Gift voucher
      description: Gift voucher; amount supplied when each Order starts.
      currency: EUR
```

Expect `Amendment Accepted`, revision 2, and the updated clause. `startOrder.amountMinor` supplies each actual Order's amount through the explicitly configured mapping.

Then try an invalid product:

```yaml
action: update
key: product
clause:
  type: Products / Product Clause
  parameters:
    product:
      type: Products / Fixed Product
      name: Gift voucher
      currency: EUR
      amountMinor: -1
```

Expect `Amendment Rejected` with `INVALID_PRODUCT`; the accepted clause and revision stay unchanged.

## 4. Activate from both timelines

In **State**, copy `clauseRuntime.revision` and `clauseRuntime.configurationId`. Use those exact values in each of these four operations, in order:

1. `ready_merchant` — Merchant timeline.
2. `ready_reseller` — Reseller timeline.
3. `approve_merchant` — Merchant timeline.
4. `approve_reseller` — Reseller timeline.

```yaml
expectedRevision: 2
expectedConfigurationId: REPLACE_WITH_CURRENT_CONFIGURATION_ID
```

If you skipped the accepted amendment, use revision 1 instead. The configuration ID is intentionally different for each fresh Agreement because its authenticated timeline bindings are part of the terms. It cannot be a universal pasted constant.

The operation form shows **Use timeline**. It lists only routes authorized for that operation. If an operation permits multiple timelines, choose one from that dropdown; an operation restricted to one party cannot be sent as the other party. The API enforces the same constraint.

After both approvals, `/activation/active` is true. Repeating the valid amendment above with a changed description now emits `ACTIVATION_CONFIGURATION_FROZEN`. Existing accepted terms remain unchanged. This version intentionally freezes active Agreements; negotiated post-activation amendment is a separate policy.

## 5. Start and purchase a €100 voucher

Run `startOrder` on the Reseller timeline:

```yaml
key: voucher-001
amountMinor: 10000
```

`10000` means €100.00. Keys must be unique within this Agreement. The factory maps only declared request arguments into the Order's clause configuration; callers cannot supply arbitrary contracts or a replacement template.

Open `/orders/voucher-001` by clicking its BlueId, or find **Voucher Order voucher-001** in Documents. It has its own Participants, Product, Purchase and Timer clauses. **Registered timers** shows the purchase deadline.

Run `purchase` on its customer timeline within one minute:

```yaml
{}
```

Expect `/purchase/status: confirmed`, an empty timer list, and a Purchase Confirmed event containing the original Order document ID, amount and currency. Return to the Agreement: `/purchasesConfirmed` increases and `/commission/amountMinor` becomes `1000` (€10.00).

Repeat `purchase`: the Order emits `ORDER_NOT_PENDING`, and no second credit is added.

## 6. Watch an Order expire

Start another Order:

```yaml
key: voucher-002
amountMinor: 25000
```

Do not purchase it. After its one-minute deadline and source completeness are established, the native timer is processed automatically. The Order changes to `cancelled` and emits Order Cancelled. The Agreement increments `/ordersCancelled`; its balance does not change.

A purchase at or after the deadline cannot revive the Order. This remains true if timer and ordinary entries share a timestamp: the common Coordination comparator orders inputs, and Purchase also checks the deadline directly.

## 7. Check fractional-cent rounding

Start and promptly purchase:

```yaml
key: voucher-003
amountMinor: 12345
```

The voucher is €123.45. Its 10% commission rounds down from €12.345 to €12.34. Together with the first Order, the balance is `2234` (€22.34). The ledger retains an entry under each original Order ID, preventing a duplicate event from crediting the same Order twice.

## Reusing these pieces

**Listener steps:** use `parameters.steps` for one shared list. With several sources, `parameters.reactions` selects a list by source name, as above. Each step receives a Listener Delivery: `/input` is the original event, `/source` identifies the subscription. An embedded event is therefore at `/input/event`. Legacy `parameters.do` remains supported, but do not combine it with `steps`.

**Relative timers:** inside a Listener step list, this schedules an event one hour after the triggering input's logical timestamp:

```yaml
- type: Time / Schedule Timer
  request:
    channel: expiryClock
    key: follow-up
    timestamp: {$add: [{$binding: timestamp}, 3600000000]}
```

The document must declare that Timer Channel. Timer Clause provides one and registers an initial one-shot timer; plain Time / Schedule Timer can replace a pending key later. Time / Cancel Timer cancels it. No cron or hidden recurring task is created.

**Bookable Product:** replace the product data, retaining Product Clause:

```yaml
type: Products / Bookable Product
name: Deluxe room for a weekend
currency: EUR
resource: room-305
startsAt: 1791547200000000
endsAt: 1791720000000000
```

This validates the resource and time interval. Availability confirmation, acceptance of alternate dates and payment would be additional business clauses; the Product type does not pretend to perform those actions.

## API equivalent

The default profile is Agreements, including for new accounts. A typical operation is:

```http
POST /api/blue/v1/documents/AGREEMENT_SESSION_ID/operations
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
Idempotency-Key: a-unique-request-id

{"operation":"startOrder","request":{"key":"api-voucher-001","amountMinor":10000}}
```

Use `GET /documents/SESSION_ID/operations` to discover allowed routes. Add `timeline` and `channel` from a route when needed; `actor` can be supplied as a consistency check. When using the document endpoint, MyOS adds the original document ID automatically. When appending an operation directly to a timeline, provide `documentId` explicitly; it must be the original pre-initialization BlueId, not the session ID or a later state ID.

Keep the same Idempotency-Key when retrying a request with an uncertain outcome. Follow the returned admission until it completes, then observe the committed document through the live UI or API. Timer registration and its removal on firing/cancellation are persisted with document publications, so restart recovery does not depend on an in-memory timeout.

## Verified live run

The deployed walkthrough finished with **3 Orders ready, 2 purchases confirmed, 1 Order cancelled, and €22.34 commission**. The cancelled Order reached its one-minute deadline without a purchase. Duplicate and late purchases did not add commission.

| Order | Result | Amount |
|---|---|---|
| [001](https://dio5ez9021fgv.cloudfront.net/#documents/b8d30740-bc85-5fc8-a000-bab77c52fdcc) | Purchase confirmed | €100.00 |
| [002](https://dio5ez9021fgv.cloudfront.net/#documents/d7b900d1-3f19-59e9-8b96-061c00277af0) | Cancelled at deadline | €250.00 |
| [003](https://dio5ez9021fgv.cloudfront.net/#documents/d14a3946-d7ac-5d25-9a7b-a9f3a4334f59) | Purchase confirmed | €123.45 |

Request-to-observed-result timings from the live API check (including network requests and observation):

- Agreement initialization: 8796 ms.
- `startOrder` calls: 3085–4901 ms (includes rejected calls).
- `purchase` calls: 947–1184 ms (includes rejected calls).

These are end-to-end observations from this run, not isolated language-processing benchmarks.
