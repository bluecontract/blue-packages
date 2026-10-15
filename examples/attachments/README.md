# Attachment-based processes — experimental candidate

This directory exercises `clause-attachments@0.1.0-preview.1`. It is a separate,
opt-in package; the published Payment and Shipping clauses are unchanged.
The same sources are tested by `DocumentAttachmentsTest` in MyOS Core.

## Variations

| Example | Business purpose | Who attaches | Relationship |
| --- | --- | --- | --- |
| 01-bank-workflows | Payer brings a bank instruction; authorization and release requests run inside it. | Customer | Agreement embeds PI; no return link. |
| 02-card-parent-state | Merchant offers a €2 payment whose capture request depends on the agreement becoming ready. | Merchant | Reciprocal embedding. |
| 03-manual-payment | Create an instruction from the exact agreed template without a bank/card creation API. | Customer | One-way; explicit creation operation. |
| 04-shipment-parent-state | Request dispatch when the agreement becomes ready; carrier confirms actual progress. | Merchant | Reciprocal embedding. |
| 05-shipment-workflows | Book and manage shipping directly in the shipping instruction. | Merchant | One-way. |

`customer`, `seller`, and `reviewer` are deliberately separate parties. The
third party must also reach the instruction: matching only payer and payee
is insufficient. Examples leave primary channels unresolved for deployment;
the native unit tests supply explicit local test transports.

## The authored difference

An action owned entirely by the instruction needs no return link:

```yaml
hooks:
  requestCapture:
    confirm:
      on: workflow
      party: customer
      params:
        $object: {$var: trigger}
```

An action observing the parent explicitly names that source:

```yaml
hooks:
  requestCapture:
    whenReady:
      in: parent
      on: state
      path: /x
      equals: 1
      params: {requestId: capture, amountMinor: 200}
```

The latter installs a parent change signal, a reciprocal embedded reference,
and a listener in the instruction. The hook waits until the parent has actually
selected this instruction: the reverse link alone is insufficient. A plain local document-update listener
cannot observe changes in an independently processed parent. The instruction
handles the parent's signal and evaluates the completed parent state.

The card example also handles acceptance before funds are secured:

```yaml
hooks:
  requestCapture:
    whenReady:
      in: parent
      on: state
      path: /x
      equals: 1
      recheckOn: [/payment/secured]
      when: {$gte: [{$document: /payment/secured}, 200]}
      params: {requestId: capture, amountMinor: 200}
```

`recheckOn` names local instruction fields whose changes should reevaluate the
same condition. A parent signal still arrives through its Embedded Node Channel;
local changes use Document Update Channels. Every attempt reads **current** parent
state. If the customer withdraws acceptance before funds arrive, capture does not
start. Stable request IDs let the existing payment protocol suppress duplicates.
A capture request still does not mean money moved: the guarantor confirms that.

This opt-in form accepts document-based expressions and constants. It rejects
transient trigger/event/call inputs, helper calls, and hook `before`/`after` effects;
those cannot safely be repeated with a different triggering event. Put business
effects in the reviewed instruction action. `recheckOn` is supported only for
parent-state hooks and local non-root paths, not `/sources` or its descendants.
It does not queue past events or guarantee a failed financial request will retry.

## Reading the attachment requirements

After `prepare_instruction`, `/instructionRequest/requirements` gives a compact
snapshot containing `relationship`, `attachBy`, `instructionType`, `terms`,
`parties`, `authority`, and `parentDependencies`. `parties` contains primary
channel IDs and keys, without representative or executable document expansion.
`authority.mustJoinParent` describes the cross-embedding requirement; it does not
assert that admission or access is complete. Use current Activation and the
normal checked operations for that decision. The exact source is still supplied
through `/instructionRequest/documentBlueId`.

For shipping, replace the subtype with `Attachments/Shipment Clause`, use a
`Shipping/Shipping Instruction with Clauses` template, set `authority: carrier`,
and use `requestShipment`. The relationship and identity checks remain shared. The base contains no
payment/shipping type switch: a subtype supplies `instructionType`, `requestType`,
`allowedActions`, `termsPath`, `authorityRole`, `partyFields`, and `actorParameter`.

## Lifecycle

For a clause called `instruction`, use this sequence when introducing a new
processor or carrier:

1. Obtain its primary party profile and arrange real timeline read grants for
   the complete intended roster. If new access documents are needed, call
   `registerAccess_instruction` with `documents: [...]` containing actual Timeline
   Access documents. Import/start these documents and let them process their
   provider history first (Core's normal access-import flow does this). The clause
   requires initialization and a provider checkpoint; a bare descriptor is
   rejected. This records evidence; it does not grant permission.
2. Call `prepare_instruction` with `authorityParty: <profile>` (omit it when the
   authority is already in the parent). The request contains the reviewed source,
   parties, terms and hooks. A processor initializes the exact source identified
   by `instructionRequest.documentBlueId`; do not reconstruct it from an expanded
   display projection. The native operation does not call a bank or carrier API.
3. For reciprocal attachments, call `addAuthority_instruction` with
   `replacement: <profile>` if the authority is not yet a parent party.
   `allowNewParties` must be enabled. This installs its channel and approval
   handlers together, increments the Activation revision and clears prior
   approvals. Complete Activation's required exact-revision approvals.
4. For reciprocal attachments, call `attachDocument` on the instruction with
   `document: <parent reference>`.
5. Call `attach_instruction` on the parent with
   `document: <initialized instruction reference>`.

One-way attachments skip steps 3 and 4: the authority can remain outside the
parent, but its primary identity must still match the reviewed request. The
prepared instruction needs valid access for its whole roster even before it is
attached. Merely registering the authority's grant does not give it access to
other parties' timelines; those parties must share their timelines too.

Manual payments also expose `create_instruction`, which builds from the prepared
source. A workflow can initiate this creation; `createOn` can request creation
on an explicit parent state condition:

```yaml
createOn: {on: state, path: /x, equals: 1}
```

For creation when clauses initialize, use `createOn: {on: initialized}`.
One-way instructions can be created when clauses initialize or from `createOn`.
Reciprocal manual creation uses explicit `prepare_instruction` and
`create_instruction` operations on an initialized parent. The create operation
uses its exact reviewed parent reference. Automatic reciprocal creation is
rejected during clause planning (`ATTACHMENT_CROSS_CREATE_REQUIRES_EXPLICIT_OPERATION`):
a state hook can run inside an unfinished parent update, whose intermediate
snapshot is not a published document that a new child can import.

Each operation that accepts a user request requires exact-document review.
An identical repeated attachment is a duplicate; replacing the instruction is
not permitted by this candidate.

## What is checked

- Every parent party exists in the instruction, and every requested primary identity—including an authority outside the parent—matches.
- Each party's primary channel and reader keys match. Key order may differ; empty or duplicate primary key lists are rejected. Representatives can differ.
- No undeclared additional party is introduced, except the selected authority in
  a one-way instruction. In a reciprocal relationship that authority must also
  be a parent party.
- The initialized instruction matches the reviewed source, including its terms
  and hooks. Extra workflows cannot be silently added to bypass those hooks.
- Both Activation states are active when links are established. Parent-driven
  requests also check current parent activation and primary identities.
- A reciprocal parent link names the expected initialized parent.

Core's native coordination runtime requires confirmed provider publication for
newly embedded Timeline Access documents. A self-authored lookalike grants nothing.
`DocumentAttachmentAccessTest` exercises the signed provider path with SQLite,
including preparing before authority admission, reciprocal attachment and grant
revocation. Its four timelines use one test account: this fixture checks signing and
grant enforcement, not multi-account convergence.

`attachWhen: {path: /merchantApproved, equals: true}` can guard the attachment
moment without moving the condition into a bank integration.

Timeline Access proves read grants. Native operation Mandates are a separate
mechanism for delegating operations to representatives. The participants use
ordinary Timeline Channels.

The fixtures use `required: []` to isolate attachment behavior. Real agreements
should specify their required approval policy. A payment request is not evidence
that money moved; only the guarantor records financial outcomes. A shipment
request is not evidence of dispatch or delivery; those are carrier responses.

## Current limits

This is an unpublished native package candidate, not a payment gateway or carrier
integration. Terms and source are exact; accepting a provider-specific extension
requires an explicitly reviewed template. Parent attachment policy is immutable.
Attachment and request storage use distinct, non-reserved top-level paths.
One attachment has one designated authority and one access-registration batch
(up to 16 documents). Replacing an attached instruction is intentionally excluded.
The new package is not installed into Core's default package catalog; the native
integration tests load the exact candidate archive explicitly.

## Reproducing the native checks

In the sibling Core worktree, run from `runtime/` with JDK 21:

```text
./gradlew :blue-core-service:test --tests blue.core.DocumentAttachmentsTest --tests blue.core.DocumentAttachmentAccessTest --no-daemon
```

The tests load the candidate archive from
`runtime/blue-core-service/src/test/resources/attachment-packages/`.
`source.json` records its identity, source base revision and source-file hashes;
`catalog-entry.json` supplies its exact package dependency closure.

## Alternative implementation review

The October 11 `myos-attachment-base` candidate contributed the compact requirement
projection idea. The `myos-generic-attachment-clause` candidate contributed the
mutual-selection gate, strict key-set validation and setup-order/current-state
checks. These ideas are implemented in the existing native package and tested
against actual initialized document graphs rather than imported wholesale.

The fresh-body-only attachment path, reader-only substitution for a required
party, and the separate pending-action protocol were not adopted. This candidate
keeps initialized references, actual Timeline Access evidence, explicit additional
parties and the existing payment/shipping request protocols. Published Activation
approval policy and all existing package identities remain unchanged.
