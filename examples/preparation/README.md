# Preparing and attaching business documents

Local, unpublished `Attachments` candidate. These examples use the same native
preparation and attachment mechanism for Payment Instructions, Shipments and
ordinary documents. `prepareDocument` is an application workflow name; it is not
Blue initialization and it does not mean that payment or delivery has happened.

## What an application author chooses

1. The complete child template and its fixed business terms.
2. `obtain: create` to construct it locally, or `obtain: provide` to ask the named
   `suppliedBy` party for an initialized, active instance of the exact prepared source.
3. The authorized workflows or local business events that request preparation.
4. Child hooks. A declared parent dependency requests reciprocal embedding;
   child-local hooks need only the forward relation.
5. An ordinary Amendments clause when an additional authority must join the host.

For example, within a complete agreement:

```yaml
instruction:
  type: Attachments/Payment Preparation Clause
  parameters:
    obtain: provide
    suppliedBy: seller
    authority: guarantor
    payer: customer
    payee: seller
    admissionClause: partyChanges
    template: # Complete Payment Instruction source; see the example files.
      type: PaymentInstruction/Payment Instruction with Clauses
    hooks: # Declared child-local or parent-dependent request hooks.
      # ...
  bindings:
    request: /instructionRequest
    instruction: /instruction
    begin:
      confirmPurchase: {on: workflow, party: customer}
    provide:
      providePayment: {on: workflow, party: seller}
    resume:
      resumePayment: {on: workflow, party: seller}
```

The abbreviated template above is explanatory. The numbered `.blue` files contain
the complete terms and behavior; they are the executable inputs.

## The missing-guarantor flow

1. Alice calls `prepareDocument` with a stable `requestId` and the selected
   authority's real primary party profile. The clause freezes the required source
   and emits a correlated provision request for Bob. A profile is not an access
   grant or consent.
2. Bob obtains an initialized, active instance of that exact source and calls
   `provideDocument` with `inResponseTo`, `requirementRef`, and its native document
   reference. The clause verifies the source, all primary party identities and
   keys, and retains the candidate without embedding it.
3. If the guarantor must join, the clause builds one precise admission value. The
   provision workflow calls ordinary `Amendments.propose` only when its actual
   caller is an allowed approver and the proposal slot is available. The proposal
   has **zero approvals**. The code does not forge the caller for an internal
   event or automatically approve its own request.
4. Alice and Bob approve that proposal. `Amendment Applied` wakes preparation.
   Its handler checks the saved proposal, approved value, history, candidate and
   Activation revision. Real timeline grants must cover the expanded roster.
5. Only then is the authority added using the existing Activation machinery.
   Activation advances its revision and requires the new authority's consent
   (and renewed approvals from any previously required Activation approvers).
6. Once Activation is effective, Bob calls the child's `attachDocument` with the
   host reference, then provides that updated instance to the host. Its identity
   must match the retained candidate. The host verifies the reverse relation
   before selecting the child.
7. Native initialization and child Activation must be complete before the host
   emits `Document Attached`. Financial and shipment actions remain governed by
   their own protocols. The guarantor/carrier still confirms actual outcomes.

If Bob is not an amendment approver, or another proposal occupies the slot, the
request remains pending. An authorized approver can use the ordinary proposal
surface, or the authorized provision/resume workflow after the slot is available.
This iteration does not silently replace another proposal, rebase changed
commercial terms, or create a second obligation after a timeout.

## Examples

See [the twelve walkthroughs](WALKTHROUGHS.md) for actors, calls and expected results.

| Source | Business flow |
| --- | --- |
| `01-manual-reimbursement.blue` | Alice requests a locally created manual reimbursement PI. |
| `02-course-business-event.blue` | `confirmPurchase` emits a business event; payment preparation consumes it. |
| `03-card-existing-parties.blue` | Bob supplies a conditional PI when its authority is already a host party. |
| `04-buyer-bank.blue` | Alice supplies a bank instruction, with no reverse dependency. |
| `05-local-delivery.blue` | The agreement creates a local-delivery shipment. |
| `06-buyer-collection.blue` | Alice supplies her collection shipment. |
| `07-carrier-cross-link.blue` | The carrier's shipment observes the host's release condition. |
| `08-local-work-order.blue` | The same mechanism creates an ordinary work order. |
| `09-provided-inspection.blue` | Bob supplies an initialized inspection work order. |
| `10-deposit-and-balance.blue` | Two named clauses represent two distinct payment obligations. |
| `11-card-admit-guarantor.blue` | Candidate → exact amendment → consent → reciprocal PI attachment. |
| `12-shipment-admit-carrier.blue` | The same admission flow for a new carrier. |

`customer`, `seller`, `reviewer` and the authority have independent primary
identities. Native unit fixtures supply explicit local transports; the signed
timeline tests separately exercise provider history and real read grants. Do not
treat the unresolved example party declarations as production credentials.

## Compact reading surface

`/preparation_<clause>` exposes the correlation, status, pending reason, candidate
and exact amendment. `/instructionRequest/requirements` exposes the frozen
terms, primary identities, authority and relationship requirement. Named native
operations provide the action surface; a `clauseId` in an event is never permission
to dispatch an arbitrary operation.

The shared messages are `Clause Request`, `Clause Response`,
`Document Preparation Requested`, `Document Provision Requested`,
`Document Attachment Pending`, `Party Admission Requested`, and `Document Attached`.
They contain references and correlation rather than copied executable documents.

## Current limits

- One child per preparation clause. Two known obligations use two clauses.
  A keyed collection facade and integration into the existing Documents factory
  remain follow-up work; no separate workflow engine was introduced here.
- Reciprocal local creation requires the authority to be an active host party already.
  Use the supplied-candidate flow for admission of a new authority. The ordinary
  document examples demonstrate forward embedding; their facade does not yet
  expose custom parent-dependent domain actions.
- Provider-supplied source must match the frozen source, with the existing checked
  primary-identity/representative normalization. Arbitrary provider-added clauses
  and loose subtype acceptance are not supported.
- `fieldPaths` can expose explicitly named business fields for preparation-time
  values. They do not grant arbitrary document patches or mutate a running child.
- The retained candidate is inert. After modifying its reverse link, the provider
  submits its newer reference; retaining a reference is not a background subscription.
- This iteration uses named workflow and local event preparation connections.
  Rich Connections hooks remain inside the child and in separate business clauses.
- No bank/card/shipping API, checkout URL generation, automated grant acquisition,
  or new Mandate transport is implemented. Existing native authorization still
  governs operations. This is not a hosted delegated-agent acceptance claim.
- `ready` records successful attachment, not a guarantee that the downstream
  business process has completed or will remain active forever.
- Conflicting request IDs, replacements, or changed requirements fail rather than
  silently creating another payment. Cancellation and obligation replacement need
  their own explicit policy.

The Pro archive's `Preparation/*` source is design input. It explicitly lacked the
implementation of those types. This candidate adopts its lifecycle separation,
correlation and checked admission ideas without claiming that every proposed API
in that archive is implemented.

## Reproducing the native checks

In the Core task worktree, import this unpublished package with
`scripts/import-attachment-candidate.py --source <blue-packages checkout>`.
Then run the `:blue-core-service:test` task with filters for
`blue.core.DocumentPreparationTest`, `blue.core.DocumentAttachmentsTest` and
`blue.core.DocumentAttachmentAccessTest`. The first exercises these authored
examples; the second protects the earlier attachment API and payment/shipment
behavior; the third uses real signed timelines, SQLite and read grants.

The fixture records the package's exact Blue ID, archive digest, source base
revision and source file hashes. It does not alter Core's production catalogue.

## Reviewed native operation inputs

Each external connection declares its actual request matcher separately from its
`params` mapping. Named preparation inputs retain their native type on the wire;
the public source entry or the authored `params` mapping removes that type when
forwarding to the existing internal function. The preparation planner invokes the
raw `begin` action, so each typed external `begin` binding explicitly removes its
root `/type`; it does not fabricate an optional authority party. Configured
no-input bindings retain an explicit matcher.

A matcher declaring native `List` requires a native list value, for example
`{type: List, itemType: <exact item type reference>, items: [...]}`. A plain array
is a different native value and remains valid for a positional array matcher.
The form must construct this representation before review; Core and Confirm do
not silently coerce it. Existing Timeline Access references retain their original
nominal type. Initialization, provider authority and history remain executor
checks; matching the public input is not proof of successful registration.

`13-current-payment-document.blue` uses the current `Payment/Payment Clause`
(`Documents/Document Base`) and its `prepare`/`resume` actions. It is distinct from
legacy payment examples using `start` and financial bindings on their host.
