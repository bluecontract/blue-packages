# Mandates — owner-approved operation authority

Protocol name: `owner-approved-operation-authority/1`  
Package namespace: `Mandates`  
Release status: scope-reduced unpublished candidate, 19 October 2026

## 1. Scope and layer boundary

This edition supports Mandates documents: participant configuration, protected
owner approval, scope updates, termination and typed evidence workflows. These
workflows execute through Contracts/BEX and the explicitly installed native
Mandates validator. Loading definitions alone does not register execution roles.

Delegated Timeline input is outside this edition. A Mandate, an authority wrapper,
or Active status does not authorize another actor to use a holder's operation
channel. Coordination accepts only the declared direct Timeline sources. There is
no delegated-entry transport field, authority-source subscription or historical
authorization path. Unsupported entry fields fail before execution.

The package depends on the exact Coordination import. Its protocol descriptor
requires that import's protocol; Contracts, BEX and Language are selected by that
pinned dependency graph. No existing instance is rebound to these new identities.

## 2. Participants

Every Mandate has two concrete Timeline Channels: `authorityHolderChannel` and
`authorizedActorChannel`. Both require admitted Timeline and Actor bindings;
the actors must be distinct. They describe the protected document participants.
The holder approves and terminates its own Mandate through direct operations.
The authorized actor can use only operations on its own declared channel; its
presence and the Mandate's scope do not grant target-channel access.

## 3. Exported model

`Mandate` owns the protected lifecycle and participant channels. It grants no
operation by itself. `Operation Mandate` adds typed `scope` and optional immutable
`grantTemplates`. One instance may grant multiple operations on multiple logical
documents, but has only one holder and one authorized actor.

`Operation Grant` contains `target: Operation Target` and optional
`validation: Request Validation`. `Operation Target` contains optional
`initialDocument`, required nonempty `channel` and `operation`, and optional
`documentValidation: Document Validation`.

`Scope` is a Dictionary with Text keys and Operation Grant values. Keys identify
grants for inspection; they are not implicit operation names, priorities, or
consumption counters. `{}` is no delegated target authority. A grant outside the
current scope is not current authority.

`Document Validation` has optional `document` (static Blue pattern) and `function`
(read-only BEX predicate). `Request Validation` has optional `request` (static
Blue pattern) and `function`. Each supplied condition applies; an omitted optional
condition adds no restriction. Explicit empty patterns are permitted as wildcards.

`Mandate Authority` extends `Mandates/Authority` and refers to the original
pre-initialization Mandate through `mandate`. Its inherited `actor` describes the represented
holder as data. No Timeline Entry field accepts this wrapper in this edition.

`Status` is the value vocabulary Pending, Active, Terminated. The packaged native
identities, not friendly names, identify these definitions.

### 3.1 Patterns are definitions, not fabricated complete instances

The supplied guides show bare static patterns in `documentValidation.document`
and `validation.request`. A pattern containing required-but-unvalued fields is
not a complete ordinary Blue instance. This package therefore adds the ordinary
empty-Dictionary type `Mandates/Pattern` as an explicit type witness:

```yaml
documentValidation:
  document:
    type: Mandates/Pattern
    valueType:
      phase: Proposed
      total:
        type: Integer
        schema: {required: true}
  function:
    expr:
      $lte: [{$binding: targetDocument/total}, 1000]
```

The witness has no ordinary entries (`maxFields: 0`). Its `valueType` MUST be
present and is admitted in Language's normal type-definition position. The
Mandates native matcher extracts that exact pattern and applies the existing
Blue match operation to the actual candidate. This is not a new Language schema
meaning, a serialized pattern string, or an executable BEX escape. Simple bare
patterns that are themselves admissible values, such as `{amount: 2}`, remain
supported. A witness without `valueType` is invalid, not an unrestricted match.

This representation adaptation is explicit. The older guide's bare pattern
syntax is not claimed universally executable on the bundled Language revision.
The complete package exports 19 definitions, including this witness.

## 4. Admission and program integrity

The processor MUST validate the required participants, exact supported marker,
protected inherited lifecycle declarations, current scope and configured grant
templates before publishing initialized state. It MUST compile configured predicate
programs before they enter an authoritative scope. Every installed scope is checked
again as part of the same local result; invalid changes cannot become authority.

This implementation accepts read-only expression-root BEX programs, with optional
pure constants/functions. Side-effect operators and native intrinsics are excluded
from authority predicates. Runtime evaluation must yield the Boolean value true,
not truthy text, an integer, or an object. A runtime error, unprovided binding,
non-Boolean result or exhausted budget never authorizes. Predicate BEX uses the
same pinned evaluator as the selected Contracts implementation. Each evaluation
retains the unchanged 10,000,000 gas ceiling; this does not implement a cumulative
user-level spending or resource budget.

The authority-predicate host MUST provide Language-backed matching for `$is`
and pure function argument patterns, and Language exact identity for `$nodeBlueId`.
These are required read-only capabilities of both document and request predicates.
They MUST use the same pinned Language implementation and resolution context as
Contracts; a missing host callback is an invalid predicate host, not permission
to skip a condition. This requirement does not enable effects or native intrinsics.

The host MUST preserve exact operands, including nested references and their
captured resolution context. `$nodeBlueId` MUST use Language identity, not a hash
of a materialized JSON value; Integer and Number identities remain distinct.
The document and candidate bindings MUST be the actual values defined in §6.

Each evaluation MUST use one fresh ledger with the 10,000,000-gas limit above.
Context view construction, demanded reads, Language matching (including function
argument matching), identity construction and BEX evaluation MUST all debit that
ledger using the selected Contracts logical-work tariffs and pinned BEX costs.
The predicate ledger is separate from the target Contracts invocation and from
other predicate evaluations. Physical caching MUST NOT change these logical charges.
Invalid operands, unavailable required content, host interruption or exhausted gas
MUST NOT confer authority. Required-content and host-incomplete failures MUST keep
their existing waiting/incomplete classification rather than becoming permission
or a semantic rejection.

The standard lifecycle and Operation Mandate housekeeping declarations are protected.
Concrete Mandates may add owner-reviewed workflows and state, but cannot replace
those standard declarations, change either principal/channel binding, replace the
protocol marker, or write protected status/timestamp fields themselves. The runtime
checks actual completion writer evidence, not a caller-supplied writer name.

`grantTemplates`, `evidenceRequirement`, and `scopeOnSuccess`, when supplied, are
owner-reviewed immutable configuration in this release. Store varying business
state in other fields. There is no generic external `setScope`, patch, program-edit,
or participant-replacement operation. New scope can be selected/computed only by
the approved workflows, and its complete grants are validated before publication.

A holder approves the whole exact pending document: all workflow code, participant
bindings, future grant configuration, and provider-gating settings—not only the
currently visible scope. Adding a workflow remains a real authority-program choice
for the holder to review; a structural type match is not an external security audit.

## 5. Lifecycle and emitted events

A fresh initialized Mandate is Pending. Initialization resets supplied status and
approval/termination timestamps; it cannot import fabricated approval history.
Its actual pre-initialization identity is the stable document reference.

`approveMandate` belongs to `authorityHolderChannel`, accepts `{}`, and requires
`requireExactDocumentVersion: true` with the exact reviewed pending head. The
processor additionally proves a direct owner action on that channel and genuine
pre-action lineage. Self-approval through this or another Mandate is not supported.
Only Pending can become Active. The workflow records `approvedAt` and emits
`Mandate Approved {timestampUs, reviewedDocumentId}`. Approval does not require the
agent to countersign; it is a delegation by the holder, not a bilateral agreement.

`terminateMandate` also belongs to the holder and takes `{reason: Text}` with a
nonempty reason. Pending or Active can terminate. It emits an internal
`Mandate Termination Requested` signal. That signal is an Event on the local
Triggered Event Channel, not a Request addressed to an external actor.

The base consumes that signal, empties operation scope, writes Terminated and
`terminatedAt`, emits `Mandate Terminated {timestampUs, reason}`, and terminates
this Mandate's processing. Terminated cannot return to Active. New commands do not
revive it. A terminal source may no longer execute a duplicate callback; that is
not an extra business effect or a revived grant.

The package emits these concrete event types:

| Type | Kind | Meaning |
|---|---|---|
| Mandate Initialized | Mandates/Event | Genuine local initialization to Pending, no delegation yet |
| Mandate Approved | Mandates/Event | Owner's exact-program approval was processed |
| Mandate Termination Requested | Mandates/Event | Internal request to the base lifecycle |
| Mandate Terminated | Mandates/Event | Permanent end, with time and reason |
| Scope Changed | Mandates/Event | Scope identity after an observed authority-scope update |
| Evidence Requested | Mandates/Request | Addressed, fixed evidence job opened by the approved program |
| Evidence Responded | Mandates/Response | Exact-request-correlated provider outcome accepted by its operation |

Scope notifications are ordinary workflow events. An Active scope update is observed
through a Document Update Channel; termination explicitly reports its cleared scope
before processing ends. Initialization/approval events establish their own lifecycle
facts. Consumers MUST inspect the committed completed state, not combine intermediate
notifications into a fictitious authority state. A failed invocation publishes none
of its candidate state changes or events.

Timestamps are the causal Coordination event timestamp supplied to Contracts,
including for internal and embedded reactions. No wall-clock timestamp is read by
BEX. Initialization itself has no fabricated external causal timestamp.

An event named Approved, a copied Request, or a forged scope notification does not
establish a legitimate source occurrence or change authorization. Authority is
verified against the protected source history, not inferred from event naming.

## 6. Direct input only

Inputs retain the actual actor, declared Timeline, timestamp, predecessor and
ordinary message. Only direct source/channel eligibility applies. Approval or
revocation of a Mandate does not alter another document's input eligibility.
Grant predicates may be compiled, validated and inspected as document data;
there is no delegated target action for them to authorize in this edition.

## 7. Scope that follows independently processed work

An approved workflow may replace scope after a holder acknowledgment, an accepted
provider Response, or a verified managed child's completed event. Scope changes
are document outcomes and do not add source subscriptions to other documents.

Independent owners retain the selected `independent-owner-prefix/1` scheduling
policy. A source publishes independently; its Mandate observer consumes that exact
historical result in order. Missing prerequisite history blocks that observer.
Terminating an observing Mandate does not terminate an independent target owner.
Ordinary Contracts operation guards remain authoritative for target transitions.

## 8. Proper Request / Response evidence gating

`Qualification Mandate` is an optional reusable preset over Operation Mandate.
It starts with no target grants and stage AwaitingEvidence. Its fixed
`evidenceRequirement` specifies operation ID, revision and exact subject. Its fixed
`scopeOnSuccess` is reviewed by the holder. `evidenceProviderChannel` names the
responsible provider as an additional participant, not an implicit guarantor.

After owner approval, the agent invokes `requestEvidence` through its own channel
with `{}`. The workflow constructs, stores and emits one complete Evidence Requested
with a causal requestId, recipientChannel, responseOperation, operationId, revision,
subject `document`. The `requestId` is the exact original signed causal Timeline
Entry BlueId. The actual performer remains that verified entry's actor, established
alongside the real committed Request occurrence. It is deliberately not duplicated
as a caller-selectable `performedBy` actor value in the public Request. A consumer
must inspect that attributable source or a separately trusted permitted projection;
it must not treat the requestId string alone as authentication. The agent cannot
replace the recipe or subject or select an easier operation. Another request operation cannot open another
independent attempt for the same Mandate.

The provider submits an Evidence Responded value as the `request` payload of the
ordinary `provideEvidence` operation on `evidenceProviderChannel`. Its
`inResponseTo` MUST identify the exact stored emitted Request. It carries required
nonempty executionId, executionStatus in Succeeded/Failed/Refused/Unknown, and a
required result Dictionary. Typed input is actually consumed, recorded and emitted;
the response is not merely a post-hoc notification synthesized from an untyped
accept/reject command. A bare Response without the operation envelope is inert.

The fixed internal `evidenceRequirement.document` slot is required by native
preparation, rather than adding instance refinements to the copied exact subject.
The emitted Request and consumed Response have required-field schemas. Substituting
another subject or request with the same human operation name is not correlation.

The preset uses a closed canonical Response encoding. It reconstructs the expected
whole Response from the exact stored Request, the submitted execution ID/status,
and its validated result, then compares native whole-value BlueIds. This proves
that the actual incoming `inResponseTo` is that exact Request, not a contextual
field projection whose inherited schema may refine its identity. The emitted
Response is the exact accepted input value. Unknown extra envelope fields,
metadata refinements, or a different Response subtype are not accepted by this
particular preset; use a separately defined protocol for those extensions.
The Request's subject may be inline exact content or an equivalent exact reference;
transport spelling does not replace the native identity check.

Initialization sets `pendingEvidence` and `evidenceResponse` to empty state objects,
not fabricated message instances. The successful operations replace them with
complete typed values; their presence as empty state adds no permission.

For this qualification preset:

* Succeeded requires exactly `{qualified: Boolean}`. Only true installs
  scopeOnSuccess and moves to EvidencePassed. False leaves no grant, NeedsReview.
* Failed or Refused requires `{}` and leaves no grant, NeedsReview.
* Unknown requires `{}`, leaves no grant, and remains EvidencePending. A later
  outcome must answer the same Request and retain the same executionId.

An exact duplicate accepted response is a business no-op, with no re-emission or
scope rewind. A different final response cannot overwrite a final result. Unknown
is never silently converted to success, failure, or permission. These are Blue
workflow guarantees; no external API call is implemented by a type name.

A copied request is not authority for external execution. The runner must verify
the committed source occurrence, admitted source/tenant configuration and its own
service execution authority, then retain deduplication/reconciliation evidence.
The test provider signs illustrative local outcomes; no model, CRM, bank or HTTP
service is contacted by the examples.

## 9. Fit with integration documents

Prefer the supplied integration-document design for new governed integrations:
agent operation -> committed Request -> external connector -> correlated Response
through the executor's channel -> recorded result. An Operation Mandate can grant
operations on an Order and multiple integrations in one scope/program, provided the
holder and agent are the same and their purposes/lifecycles fit.

A Mandate may follow an accessible integration as a verified managed dependency,
or receive an explicitly trusted and privacy-limited outcome projection. A projection
which is not answering a new Request is an Event, not a fabricated Response. Its
source claims alone are not cryptographic verification: the named publication
service must establish the source occurrence, original attributed entry, exact job,
accepted response, originating Mandate and permitted disclosure before publishing.

Agent call authority is distinct from connector/service authority to use credentials,
spend money, access inputs and publish results. This package implements protected Mandate documents
and a provider-evidence preset; it does not implement a Document Responder
Mandate or a connector dispatch authorization engine. Those need an explicitly
supported aligned protocol, not an alias for Operation Grant.

Terminating a Mandate ends its document workflows and clears scope. It does not
undo committed business actions or cancel external effects. Connector execution,
cancellation and reconciliation require a separately selected service policy.

Addressing is not confidentiality. Secrets and private prompts stay outside public
Blue values; permitted projection happens before Timeline append. Missing private
source access means wait or use an explicitly trusted projection, never infer truth.

## 10. Versioning and implementation boundary

This package does not mutate or relabel the old Coordination-bundled Mandate IDs.
It publishes new native definitions and a new protocol requirement. Historical
implementations remain evidence only and are not supported runtime selections. The new package requires explicit selection by exact
Package BlueId and a matching native implementation binding. The selected package
set is stored in the engine context; restart with a different set is rejected.

The source guides' illustrative `Mandate/Mandate v2` becomes `Mandates/Mandate` in
this versioned package. Their scope-bearing examples instantiate Operation Mandate.
Their older `Coordination/Sequential Workflow Operation` spellings become the actual
current `Contracts/Sequential Workflow Operation`, and BEX operation payload reads
use `$binding: call/request`. Status is the current Text vocabulary, not the guides'
unpublished status-subtype placeholders. Empty operation payloads use `{}` plus
explicit key checks rather than claiming untyped empty Blue objects automatically
match a concrete `Dictionary` annotation. The embedded-processing contract uses
the current reserved key `embedded`. Guide semantics are preserved where stated;
these syntax and support-boundary adaptations are explicit, not inferred releases.

The optional qualification preset uses the later integration guide's Unknown /
reconciliation distinction, not the earlier guide's terminal Unavailable vocabulary.
The preferred integration execution path does not request a second confirmation of
an already managed call; the direct evidence preset is for a genuinely separate
attestation/evidence job. Actual connector execution, responder authority, privacy
bridges and cross-provider deployment are outside this artifact's executed scope.

## 11. Required acceptance evidence

A conforming implementation must demonstrate package/type admission, rejection
without explicit support, exact-context restart binding, fresh Pending initialization,
exact direct owner approval, rejection of fabricated activation/writer/program changes,
participant and scope validation, invalid/impure predicate rejection, rejection
of delegated entry claims, and preservation of the actual actor and original
initial reference.

It must also demonstrate typed emitted lifecycle messages, scope changes, genuine
Request/Response ancestry and exact inResponseTo correlation, provider-channel
restriction, false/unknown/error outcomes, duplicate/stale callbacks, termination,
managed child-driven scope progression, target survival and unchanged business
operation guards. The verification report distinguishes executed tests, retained
document workflow regressions and unimplemented external deployment requirements.

Passing the included tests is not a security certification, a legal enforceability
claim, Java parity, exhaustive distributed crash testing, or a production benchmark.


## 12. Implementation obligations outside the passing local examples

The local native implementation has one exact supported package/runtime binding.
It does not implement arbitrary package-version compatibility, delegation chains,
co-signing guarantors, aggregate-channel delegation, or an external Document
Responder Mandate executor. Importing a future package is not evidence that its
authority semantics are implemented. Owner consent to external credential use,
connector execution, permitted disclosure and reconciliation remains a separate
service obligation. The example evidence provider is a locally authenticated test
participant; no real model, CRM, payment, or HTTP connector is called.

Current/future grants in standard `scope`, `grantTemplates`, and `scopeOnSuccess`
are prepared, and every resulting live scope is revalidated. This does not claim
that arbitrary future data assembled by a custom program can be exhaustively
predicted: invalid computed scope cannot publish. The holder must review custom
workflows and intended mutable parameters before approval. Whole-program approval
is meaningful only with that reviewed behavior, not with a friendly type name.

The inherited Contracts gas ceiling remains 10,000,000. Native admission, historical
proof preparation, predicate compilation and scope validation are also host work;
this delivery does not claim that all such host CPU/memory is included in Contracts'
per-invocation gas or implement aggregate customer resource budgeting. Apply host
resource admission separately. Physical inability must not become a fabricated
semantic denial or permission to skip an unresolved input.

This edition selects the exact 10M gas prerequisites. Previously published content retains its original semantics.

## Package ownership

Mandates defines its own Event, Message, Request, Response and Authority base types.
Coordination provides authenticated actors, signed timelines and timeline channels;
it does not own application messages or delegation policy. This revision retains
the owner-approved protected program and exact-review rules above. Historical
Mandates identities remain immutable evidence; current runtimes do not replay them.
