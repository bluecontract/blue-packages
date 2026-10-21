# Using Mandates

This guide describes protected documents. Scope records are data; delegated
Timeline calls are unavailable in the current edition.

## 1. Start with two different actors

The holder controls an operation channel in a target document. The agent has its
own Timeline Channel in that document. Being present does not give it the holder's
rights. A separate Mandate contains `authorityHolderChannel` and
`authorizedActorChannel`; both must have real authenticated Timeline/Actor bindings.
The two actors are distinct. Their per-document Timelines can differ.

An Order or Agreement controls the business transition. The Mandate records an owner-reviewed scope. It does not authorize
the agent to exercise the holder's operation in this edition. It cannot create rights the
holder lacks or override a target that forbids delegation.

## 2. Approve the whole program

```
Created and initialized       Pending        No delegated operation is usable
Holder approveMandate({})     Active         Current scope is recorded
Holder terminateMandate(...)  Terminated     No future use; no reactivation
```

Approval is direct, owner-attributed, and pins the exact reviewed Pending state with
`requireExactDocumentVersion: true`. It covers the executable rules and their future
grant configuration, not just today's scope. An empty current scope can later become
powerful; that future behavior must be reviewed too.

Initialization discards fabricated Active status and approval timestamps. Native
publication checks prevent an extra workflow from assigning Active or rewriting the
approved program. Termination goes through an internal event consumed by the base;
the base writes the terminal state and emits the completion event.

An agent need not countersign a unilateral delegation. A guarantor is not mandatory.
Additional co-approval policy must be implemented explicitly rather than inferred
from another participant's mere presence.

## 3. One complete grant must match

Illustrative authored shape; the runnable examples calculate the actual identifiers:

```yaml
type: Mandates/Operation Mandate
scope:
  incrementByTwo:
    type: Mandates/Operation Grant
    target:
      initialDocument: {blueId: COUNTER_INITIAL}
      channel: ownerChannel
      operation: increment
      documentValidation:
        document:
          type: Mandates/Pattern
          valueType:
            count:
              type: Integer
              schema: {required: true}
        function:
          expr:
            $and:
              - $gte: [{$binding: targetDocument/count}, 0]
              - $lte: [{$binding: targetDocument/count}, 98]
    validation:
      request: {amount: 2}
      function:
        expr:
          $eq: [{$keys: {$binding: request}}, [amount]]
```

The target is this logical counter, the channel is ownerChannel, the operation is
increment, the pre-action count is 0–98, and the actual payload contains only
`amount: 2`. Every configured condition must pass within one grant. Matching the
target of one grant and the request of another is not permission.

The `Pattern` type witness is an empty Dictionary whose `valueType` is the actual
pattern definition. It permits required-but-unvalued pattern fields without treating
them as completed message instances. This is a deliberate current-Language adaptation,
not a new pattern syntax silently imposed on the attached guide.

Several grants are alternatives. `scope: {}` means none. Future grants in
`grantTemplates` or `scopeOnSuccess` are not usable until an approved workflow puts
them in scope. One Mandate can cover multiple targets and multiple operations.
It does not automatically make a permission single-use or provide a shared budget.

## 4. Direct operations

Use an ordinary Operation Request on the actual actor's declared channel.
The current edition has no delegated Timeline entry field. Approving the Mandate
changes its own lifecycle state but does not enable cross-channel calls.

## 5. Typed Request/Response gate

`Qualification Mandate` starts with empty scope. Its reviewed configuration fixes an
operation ID, revision, exact subject, permitted provider channel, and `scopeOnSuccess`.
The agent's `requestEvidence({})` operation emits and stores:

```yaml
type: Mandates/Evidence Requested
requestId: CAUSAL_SIGNED_ENTRY_BLUE_ID
recipientChannel: evidenceProviderChannel
responseOperation: provideEvidence
operationId: customer-qualification
operationRevision: 1
document: {blueId: EXACT_SUBJECT}
```

The performer is established by the exact causal signed entry and real source
occurrence, not a repeated, caller-selectable actor field. The Request's subject
may be transported inline; the invariant is its native exact identity.

The provider supplies a real typed Response **as the operation payload**:

```yaml
type: Contracts/Operation Request
channel: evidenceProviderChannel
operation: provideEvidence
document: {blueId: CURRENT_MANDATE}
request:
  type: Mandates/Evidence Responded
  inResponseTo: {blueId: EXACT_EMITTED_REQUEST}
  executionId: execution-042
  executionStatus: Succeeded
  result: {qualified: true}
```

The workflow consumes that typed payload, verifies exact correlation and result
shape, records it, changes scope if permitted, and emits the **same exact Response**.
A bare Response appended without the operation envelope does not accept evidence.
An agent cannot call the provider-owned response operation.

| Accepted outcome | Scope and stage |
|---|---|
| Succeeded / qualified true | Install reviewed scopeOnSuccess; EvidencePassed |
| Succeeded / qualified false | Empty; NeedsReview |
| Failed or Refused / empty result | Empty; NeedsReview |
| Unknown / empty result | Empty; EvidencePending; reconcile the same execution |

The same Request cannot be replaced with an easier one retaining only its requestId.
Unknown can become final only for the same executionId. An exact callback retry
produces no second business message. A final result cannot be overwritten. The
agent cannot open repeated independent checks to cherry-pick a favorable result.

This preset deliberately uses a closed exact Response shape. Unknown extra envelope
fields/subtypes do not pass its whole-response identity check. A separate protocol
must define extensibility rather than silently accepting it.

## 6. Historical examples

The earlier static, manual-order, provider-gated and connected delegation examples
are preserved in `provenance/incoming-examples/`. Their cross-channel calls are
unsupported by the current edition. Approval, evidence and scope progression can
still execute as document workflows with direct participant operations.

## 7. Integrations fit beside this package

An integration document can own requests and accepted outcomes. The same Operation
Mandate can grant `qualifyCustomer` on one integration, `approveOrder` on an Order,
`registerOrder` on another integration, and `releaseForFulfilment` on the Order.
Ordinary Mandate workflows decide which grant is current.

The runner still needs its own permission to use credentials, incur costs, execute
committed Requests, and publish results. This package does not pretend the agent's
operation grant is that service permission. When the integration already records
its result, observe that original result or a permitted projection; do not require
a fictional second confirmation. A privacy projection is an Event, not a Response
to a Request that never existed.

See `coordination.md` for the host boundary and `source-mapping.md` for precise changes
from the source proposals. No actual connector or disclosure bridge is shipped here.
