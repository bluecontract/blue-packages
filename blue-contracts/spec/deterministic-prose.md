# Blue Contracts 1.0

**Edition:** `blue-contracts/2026-10-19-deterministic-4`  
**Normative form:** one complete specification with executable algorithm appendices

## Abstract

Blue Contracts defines deterministic, gas-bounded transitions over exact Blue documents. It specifies channels, operation selection, sequential workflows, local updates, child-first managed composition, cyclic component rounds, initialization, atomic failure, replay and completion reuse. Effects are published only after a complete successful transition.

## Contents

- [1. Scope and conformance](#scope)
- [2. Exact dependencies and interpretation](#dependencies)
- [3. Scope and central rule](#section-3)
- [4. Public API, outcomes and document representation](#section-4)
- [5. Exact graph and occurrence records](#section-5)
- [6. Standard categories and complete type catalogue](#section-6)
- [7. Actual-value filtering](#section-7)
- [8. One selected operation call](#section-8)
- [9. External channel acceptance, lifetimes and checkpoints](#section-9)
- [10. Deterministic completion machine](#section-10)
- [11. Nested steps and BEX effects](#section-11)
- [12. Patches, validation and local Document Updates](#section-12)
- [13. Local FIFO, output batches and lifecycle](#section-13)
- [14. Dynamic graphs, collections, shared members and cycles](#section-14)
- [15. Generalization and explicit valid retyping](#section-15)
- [16. Lazy content and installed runtime extensions](#section-16)
- [17. Logical gas and host-independent resource semantics](#section-17)
- [18. Atomicity, replay and chunking equivalence](#section-18)
- [19. Conformance and integration](#section-19)
- [20. Normative algorithms and provenance](#section-20)
- [21. Generic Coordination integration boundary](#section-21)
- [22. Lazy immutable host values](#section-22)
- [23. Exact-value transfer accounting](#section-23)
- [24. Selected descendant evidence](#section-24)
- [Appendix A. Complete transition model](#transitions)
- [Appendix B. Logical metering and schedule](#metering)
- [Appendix C. Complete executable algorithms](#algorithms)

<a id="scope"></a>
## 1. Scope and conformance

This specification defines the protocol identified by this edition. Its prose, tables and algorithm appendices form one normative contract. It is independent of source-repository branches, release tags, installation paths and prior discussions. Named external semantics are selected exactly in §2. Where an implementation uses another programming language, it MUST preserve the same specified observations; matching internal classes or diagnostic wording is not required unless explicitly identified as an observation.

**MUST** and **REQUIRED** express requirements. **MUST NOT** and **PROHIBITED** express prohibitions. **SHOULD** and **SHOULD NOT** express recommendations whose departures require understood consequences. **MAY** and **OPTIONAL** express permissions. Examples marked informative do not add requirements. A conflict between normative prose and algorithms is a defect, not permission to choose an outcome. A finite conformance corpus is evidence, not a proof for every possible input.

A package distributes this specification; it does not install a processor. The package's BlueId, this specification Text's BlueId and the OCI/archive digests identify different content. This document does not contain its own calculated identity or the generated identities of types that refer to it.

<a id="dependencies"></a>
## 2. Exact dependencies and interpretation

This edition selects Blue Language package `8XGYNufx24r7Dc5bGoeobcGNCn9roLzSfZCQyHBTaTx4` and its complete specification Text `H7WiYQ6GiWypRdFyWRcv99dsvTv6WnJYnu9eLYPQmWnc`. Language is a direct prerequisite: document admission, effective types, specialization, exact references, specification metadata, cyclic identities and BlueIds use its defined operations.

This edition requires Blue BEX package `6L2cQG3oSX4WPkXoTvGXeTEjn41WYnjdNKSo1F61xonc`, protocol specification `9X3Ws96pyH1SdP4yuXpkNfWPfW3vJCzDzhdza3u9NpoB`, and normative rules Text `8ncKHLULWkzyNKEHfzpswF6iKZfc3H1DzDpgH8UC1hV`. Every BEX-bearing position in an invocation uses that evaluator contract and the host interfaces defined here. Selecting another package or operator table MUST NOT substitute another BEX mode. BEX values and proposed effects are not automatically admitted Blue values; the output boundaries below are mandatory.

Coordination is not a prerequisite of Contracts. A higher-level host may establish external ordering, authority and durable histories; it supplies the original accepted event and timestamp through the public transition defined here. Contracts does not query a timeline provider or assign actor authority on its own.

Package imports supply exact content. Authoring prefixes are local bindings and do not leak through transitive imports. An imported definition retains its exact references. Mounting another package cannot change the selected interpreter or replace an existing type reference. Within this edition's interpreted package graph, the selected Language release MUST agree throughout; cross-Language conversion and mixed-rule cyclic sets are not defined. One selected Language governs a complete cyclic identity set and its owning proof.

<a id="section-3"></a>
## 3. Scope and central rule

**C01.** The public transition remains:

```text
process(document, event, eventTimestamp)
    -> resulting document, emitted events, gas
```

`document` is the selected exact root and its required managed graph. The event is one complete original external Blue value. Time is supplied as integer microseconds. A successful attempt finishes required initialization, local turns, child-batch applications, cyclic feedback and exact finalization. All returned changes remain one atomic result.

**Completion boundary.** Within a document, updates are immediate and application events are queued. Across a managed boundary, only a **sealed completion** is observable. A sealed completion contains the source's completed document/view and its ordered output occurrences. It is not necessarily durably committed. A child producing no events still supplies its resulting state.

No standalone channel parameter, delivery-list ingress, payload selector or alternate request selector is introduced. The chunk protocol in the annex is a processor-internal decomposition of this same transition; a completion is not an external event and cannot invoke an operation by masquerading as one.

**C02.** Contracts defines all processing described here, including child incorporation and cycle turns. Obtaining, ordering and authorizing external inputs, worker ownership, persistent-history scheduling, billing and external delivery are outside this specification.

**C03.** Language retains sole authority for Source, exact content, identities, resolution, cyclic sets and type validity. BEX retains its evaluation, numbers, functions, bindings and effect accumulation. Contracts chooses views and applies effects. Missing exact evidence is not an empty object or an ordinary filter mismatch.

<a id="section-4"></a>
## 4. Public API, outcomes and document representation

### 2.1 Three inputs

The Python-compatible public API remains `Processor.process(document, event, eventTimestamp)`. Its bound method has exactly these three parameters. Processor construction configures the exact runtime registry, resolver, gas ceiling and optional member-local ceilings; those are fixed execution configuration rather than extra per-event routing arguments.

`document` can be a verified `Snapshot`, the SDK representation of the selected exact rooted document, or a fresh Source object. The latter is admitted and initialized within the attempt. It is not permissible to author protected processor markers in a fresh Source object. Use verified snapshot restoration for an already managed document.

The required SDK-compatible returned `Outcome.document` is the resulting `Snapshot`. Its selected root BlueId is `result.document.documents[result.document.root].blue_id`. `processor.read(result.document, path)` reads business content. `Outcome.emitted_events` contains exact references to the selected root's publicly emitted values. `processor.emitted(result)` opens those values for display. Tuple unpacking yields `(document, emitted_events, gas)` in the order in C01; the `Outcome` additionally carries diagnostics and replay evidence.

These SDK records do not add inputs to the Contracts transition. Optional `begin / next_chunk / execute_chunk / accept_chunk / finish` methods implement the internal protocol in the executable appendix; they do not publish partial state or add another external ingress. A storage host may use a different representation if it preserves the same exact content, managed-occurrence evidence and semantics.

### 2.2 Time and identities

**C04.** `eventTimestamp` MUST be an integer from 0 through 2^53−1, in microseconds. Booleans, floating-point values, strings, negative numbers and out-of-range integers are rejected. Contracts never substitutes a wall clock or an event field for this argument. This range preserves the defined's portable timestamp representation; BEX Integer arithmetic is not narrowed by it.

The original event's identity is established with the unchanged validated Language operations. Selection of an inner call does not alter this identity. Equal timestamps do not imply equal events. No timestamp-only external ordering relation is inferred.

### 2.3 Result states

| Status | Document and public events | Meaning |
|---|---|---|
| `APPLIED` | Complete resulting state and selected-root emissions | The attempt can commit, including graceful termination. |
| `FAILED` | Original input snapshot; no public events | Invalid call, invalid effect, validation failure, explicit BEX failure, unsupported demanded executable or another defined Contracts error. |
| `GAS_LIMIT_EXCEEDED` | Original input snapshot; no public events | The next logical charge exceeds the shared or owner-local remaining allowance. The admitted prefix and rejected charge are reported. |
| `NEEDS_RESOURCES` | Original input snapshot; no public events | Required exact content or managed-view evidence is unavailable. This suspended attempt reports no completed semantic gas result; rerun from the original inputs after evidence is supplied. |
| `TERMINATED` | Original input snapshot; no public events | The selected root was already legitimately terminated. |

Invalid SDK arguments, invalid fresh Source admission and invalid configuration may raise `ContractError` before a runnable attempt exists. They are never a successful partial processing result. Gas and the compact rejection details returned with a failed runnable attempt are diagnostic, not committed application effects.

An explicit `initialize(document)` lifecycle action is also provided. It has no invented external event or timestamp. It returns an `Outcome`. `create(document)` is a convenience that requires successful initialization and returns its document. `admit(members, root, bindings)` is a graph authoring facility, not an alternative event ingress. Its `Link` objects and symbolic member labels are not legal runtime patch values.

<a id="section-5"></a>
## 5. Exact graph and occurrence records

**C05.** A snapshot contains a root member key, exact document records, exact embedding edges, revision and topology-generation numbers, the Contracts specification identity and installed runtime bindings. Member keys and these commitments are platform records, not replacement BlueIds.

A member record contains its stable key, exact body and BlueId, current external-channel lifetimes, monotonically increasing channel and edge serials, and an optional immutable creation-cause token. A cause token is the original event identity, not an external ordering proof. The initial member set is finite.

An embedding edge is `(source member, relative path, target member, generation)`. That tuple identifies an occurrence. The same child may have several explicit incoming occurrences. A member's state changes can change its BlueId without changing its member key or continuing occurrences. Conversely, removing and recreating an occurrence at the same path must not revive an earlier occurrence's work.

The snapshot wire form is defined by `Snapshot.wire`, `Document.metadata`, `ChannelLife.wire` and `Edge.wire`. These field shapes and validation obligations are retained, with the commitment domains in A00. This design package does not supply published new replay identities. The platform commitment uses a tagged canonical JSON representation and SHA-256; **it is not the BlueId algorithm**. Language remains the sole authority for document and cyclic-member BlueIds.

Restoring a snapshot verifies its commitment, release, runtime bindings, every exact body, each edge's selected content and target identity, channel lifetime signatures and protected markers. Possession of an unverified body containing `initialized` or `checkpoint` is insufficient to restore a managed history. Unknown or ambiguous managed-view bindings fail or require evidence; they are not silently bound to the latest document.

### 3.1 Private working state versus sealed views

For each active member, keep its last exact **sealed view** separate from the writable **local frame** used for one turn. A frame may read its own evolving state (stable during one Compute) and the exact dependency views selected for the turn. It cannot read another active frame, an ambient latest pointer, a container's unsealed state, or a resolver alias that changes behind an exact BlueId.

In a DAG, children finish before their container's turn. In a cycle, peer reads use the preceding completed component-round view. Ordinary self-reference through a separately managed self-edge also means that completed view, not an alias to the writable frame.

Exact managed bindings are updated from completed results by the processor. This changes containing content identities, but is **not** a business patch, does not recreate child Document Updates and does not invoke arbitrary callbacks.

### 3.2 Completion records

`TurnCompletion`, `RoundSeal` and `UnitCompletion` are closed processor records defined in the annex, not new top-level contract categories or user-authored business documents. A completion binds exact before/after views, the original cause, relevant frozen local inputs, the profile, ordered event occurrences and its scalar gas contribution. Its source events contain no parent paths. Each receiver supplies and checks its own captured occurrence tickets.

A value shaped like a completion is not evidence it was executed. Accept only a result produced through the current attempt's verified chunk protocol, or an implementation's explicitly verified equivalent result with all the same bindings. Merely verifying the after-document's BlueId does not establish the calculation. This revision defines no public third-party proof-admission protocol.

<a id="section-6"></a>
## 6. Standard categories and complete type catalogue

**C06.** **Marker**, **Channel** and **Handler** are the ordinary top-level categories; an exact registered `dispatch-policy` Compute subtype is also permitted under the Dispatch role rules in this edition. `Contract` is an abstract common ancestor. `Operation` specializes Handler. A Sequential Workflow Operation is therefore a Handler. Process Embedded is a Marker. Standard steps inherit the abstract Contract definition solely to share declarations; their executable role is nested step, and placing them directly in `contracts` is invalid.

All registered definitions include the exact specification reference. `name` and `description` are Language labels, not inherited business defaults. Runtime contracts may carry these labels. `order` is an optional signed 32-bit Integer; omitted means zero. Unknown standard runtime fields are rejected, including `when`. Catalogue declaration holes do not cause absent options to appear configured.

The catalogue retains these **32 definition shapes**, including the reusable Compute Definition marker. The `publish_catalogue` algorithm in the executable appendix defines the complete Language Source field-definition recipe of each. Tables below specify the additional closed runtime field and presence rules which cannot be expressed by an unvalued optional declaration alone. The current publication contains validated BlueIds and exact definition bodies. The catalogue generator in the executable appendix supplies the standard definitions.

### Core authoring names

Language scalar/container types and this Contracts catalogue are mandatory in the
standard Python authoring environment. Use bare names: `Integer`, `Channel`,
`Compute`, `Compute Definition`, `Sequential Workflow`, and so on. Every catalogue
name is installed before application repositories. Conflicting aliases fail;
repositories cannot silently replace a core name. Legacy `Contracts/NAME` spellings
remain aliases for the same current exact definition. This is name resolution,
not execution registration or network discovery. Exact documents store BlueIds.
`Language(core_contracts=False)` is the explicit low-level bootstrap/historical
profile, not the standard application environment. A Processor always installs
and binds its exact Contracts catalogue, including bare names.

### 4.1 Abstract categories and executable handlers

| Type | Parent | Fields and rules |
|---|---|---|
| Contract | none | Optional `order: Integer`. Abstract; not a top-level runtime implementation. |
| Marker | Contract | Abstract structural/policy/processing category. |
| Channel | Contract | Abstract observation category. |
| Handler | Contract | `channel: Text`; concrete executable handlers require a nonempty valid channel key. |
| Operation | Handler | Abstract named external-call handler. |
| Sequential Workflow | Handler | Required `channel`, required `steps: List`; optional `event` actual-value filter. |
| Sequential Workflow Operation | Operation | Required `channel`, required `steps: List`; optional `request` argument definition. No `event` or `when` field. Its name for dispatch is its raw key in `contracts`, not its label. |

Empty `steps: []` is permitted. Step order is list order. Standard handler discovery loads the header and verifies that steps are configured but does not compile an unused executable body. A selected operation MUST exist and be bound to the request's target external channel.

### 4.2 Channels

| Type | Parent | Fields, defaults and observed family |
|---|---|---|
| External Channel | Channel | Optional `event` filter against the complete original event. Without a filter, accepts every external event offered to this member. No special source, actor or outer routing field. |
| Composite External Channels | Channel | `channels: List[Text]`, default empty. Names other external primitive or composite/all channels in this member. Duplicate names and composition cycles are invalid. Acceptance is a set union. |
| All External Channels | Channel | No additional fields. Union of this member's primitive External Channels and installed external-channel extensions. Excludes internal channels. |
| Triggered Event Channel | Channel | Optional `event` filter. Observes application emissions from this same member while its local queue drains; never calls a container. |
| Embedded Node Channel | Channel | Optional `sourcePath: Text` exact relative direct-edge path; optional `event` filter on the child's inner application emission. With no sourcePath, observes all direct-child occurrences. Delivery occurs only after the child completion is incorporated. |
| Document Update Channel | Channel | Optional `path: Text`, default empty pointer; optional `event` filter against Document Update. Path matches that location and ordinary descendants within this managed document, not changes within separately managed descendants or an update to an ancestor. |
| Lifecycle Event Channel | Channel | Optional `event` filter against the current initialization or termination notification. |

A composite's members must be external channels in the same document. All External Channels is not a subscription to every internal event. A union's role is observation and optional explicit operation binding; traversing a union never redispatches an operation bound to one of its members.

External selection and runtime acceptance are specified in sections 6–8. Applications discriminate external recipients with actual event fields, for example `event: {location: desk}`. The processor does not extract a payload or supply a channel value that the external event lacks.

### 4.3 Nested steps

| Type | Required fields | Optional fields and effect |
|---|---|---|
| Compute | A valid BEX program using `expr` or `do`, as required by BEX | `constants`, `functions`, `definition`, `entry`; optional step `name`; executes unchanged BEX, returns a value and proposed changes/events. |
| Update Document | `changeset`, an effect-free BEX expression evaluating to a List of patches | Optional step `name`; applies evaluated patches in order. |
| Trigger Event | `event`, an effect-free BEX expression evaluating to a valid Blue value | Optional step `name`; creates one immutable application-event occurrence. Explicit `{}` is present, not missing. |
| Terminate Processing | `cause: Text` | Optional `reason: Text`, optional `name`; requests graceful termination. |

There is no `when`. A condition controlling effects must be placed in Compute around those effects. Returning no effects from one Compute does not skip a later unconditional step. A BEX `$call` is an intra-program function call, not a synchronous call to another managed document's operation.

### 4.4 Markers

| Type | Required fields and placement | Semantics |
|---|---|---|
| Compute Definition | Optional `constants` and `functions` objects | Nonexecuting reusable BEX declaration; may be a named member of `contracts`. No initialization or effects. |
| Process Embedded | Raw key `embedded`; optional `paths: List[Text]` and `collectionPaths: List[Text]`, each default empty | Declares managed boundaries. Existing explicit paths and each direct map member under a collection path become occurrences. |
| Processing Initialized Marker | Raw key `initialized`; `document: {blueId: exactPreInitializationDocument}` | Protected processor state; written silently after initialization work. |
| Processing Terminated Marker | Raw key `terminated`; `cause: Text`, optional `reason: Text` | Protected successful graceful termination; blocks future ordinary processing. |
| Channel Event Checkpoint | Raw key `checkpoint`; `entries: Dictionary` | Protected map from external channel keys to exact checkpoint records. |
| Type Generalization Policy | Raw key `generalization`; `defaultMode`, default `reject`; `rules: List[Type Generalization Rule]`, default empty | Protected policy for controlled automatic ancestor selection. |

Checkpoint entries are closed records:

```yaml
timestamp: 1000000
event:
  blueId: <exactOriginalExternalEvent>
```

The angle-bracket value is descriptive notation, not an admitted BlueId. Runnable conformance fixtures must use actual admitted identities. A checkpoint row has exactly `timestamp` and `event`; `event` is a pure exact reference. An absent checkpoint is not synthesized before successful consumption. A checkpoint with no entries may be omitted. Internal notifications do not obtain external checkpoints.

Generalization Rule has required `path: Text`, required `mode` equal to `reject` or `nearest-valid-ancestor`, and optional `mustRemainSubtypeOf: {blueId: exactTypeDefinition}`. The policy's own definition and inherited effective identity are protected from ordinary patches.

### 4.5 Requests, notifications and effect records

| Type | Fields and complete shape |
|---|---|
| Operation Request | Required `channel: Text`, required `operation: Text`; optional `request`; optional `document` exact reference; optional `requireExactDocumentVersion: Boolean`, default false. True requires document. The precondition is not a target-selection instruction. |
| Document Processing Initiated | `document: {blueId: exactPreInitializationDocument}`. Internal lifecycle notification. |
| Document Processing Terminated | `cause: Text`, optional `reason: Text`. Internal lifecycle notification. |
| Document Update | `op` in add/replace/remove; relative `path`; `beforePresent: Boolean`, `afterPresent: Boolean`; `before` iff present; `after` iff present. Sides are exact immutable values, inline or exact references. |
| Embedded Event Delivery | `sourcePath: Text` identifying one direct child edge; `event`, the immutable inner child application emission, inline or exact reference. |
| Json Patch Entry | Closed record `{op, path, val}` for add/replace; `{op, path}` for remove. `val` is a runtime value, not Source syntax to preprocess again. |
| Contract Execution Result | Optional `patches: List[Json Patch Entry]` and `events: List`, each default empty; optional `termination: {cause, reason?}`; optional runtimeLedger subject to the extension metering protocol. Unknown keys are invalid. |
| Type Generalization Rule | The policy-entry definition described above. |

Standard Operation Request recognition requires the registered type or a valid installed descendant recognized by its ancestry, not merely similar fields. Runtime request members are closed to the five standard fields, inherited `specification`, and Language labels. A typed but malformed request fails rather than silently becoming an ordinary event.

<a id="section-7"></a>
## 7. Actual-value filtering

**C07.** A filter is a Language definition tested against the actual event. It MUST NOT be merged into the event as a way to create missing event data. The selected exact algorithm is `Bridge.matches`:

1. Obtain the actual exact value and validate it as a value; obtain the filter as a definition. Resolve required exact evidence.
2. Walk actual and filter recipes together. For every authored or concrete inherited filter field, require the corresponding actual field and a present actual value. Typed declaration holes contributed only by a standard definition are not invented required business fields.
3. For filter list positions, require the corresponding actual positions. Extra actual positions or fields are allowed unless applicable Language constraints forbid them.
4. When the pattern names an explicit type, require that exact type in the actual value's type ancestry. This prevents unrelated registered notification types with structurally compatible fields from becoming indistinguishable. This is a Contracts filter guard, not a change to Language structural refinement.
5. With presence established, apply the selected Language refinement/validation operation to check fixed values, types and constraints. Return false for the defined compatibility, fixed-value, schema, list-shape and present-value mismatch categories. Propagate missing resources, invalid evidence and unsupported conditions as errors rather than false matches.
6. Never replace or alter the actual value.

Pairwise visited-recipe tracking makes repeated/cyclic structure finite. There is no universal filter-depth ceiling. Demand-driven matching charges its prescribed logical work, retains repeated-pair cycle detection, and may be physically interrupted only as incomplete execution. Event fields inherited from the actual event's own valid type count as actual fields. Fields introduced only by the filter do not.

A filter `{kind: paid, amount: {type: Integer, schema: {minimum: 100}}}` matches an actual paid event with amount 120, not one with amount 20 or no amount. A filter on a containing event must use its actual nested shape. `call` does not silently redirect ordinary filters to the operation request.

For Embedded Node Channel only, its channel-level filter tests the inner application event. Its workflow-level filter and `$event` see the complete Embedded Event Delivery wrapper. This difference is explicit and does not apply to external events.

<a id="section-8"></a>
## 8. One selected operation call

**C08.** Before external handler effects, perform precisely this recognition:

```text
if originalEvent is a recognized Operation Request:
    call := originalEvent
else if originalEvent's immediate operation field is a recognized Operation Request:
    call := that complete field value
else:
    call := absent
```

The first branch has precedence. There is no recursive search, configurable selector, message extraction or second processing invocation. Unrelated ordinary events may still trigger ordinary workflows.

Validate a recognized request's complete shape, nonempty channel and operation keys, optional Boolean precondition flag, and required exact-document reference when the flag is true. Its request arguments are not synthesized. During accepted-channel selection, freeze ordinary observer channels separately from operation recipients. An unaddressed request selects members whose accepted external channel key equals its channel; the named operation is checked only after selecting those candidates. A differently named observing channel does not make its member an operation target. For an explicitly addressed request, the installed verifier establishes the target lineage, independently of ordinary observation rights. On an actual recipient require the target channel to exist and be accepted. When that target channel is fresh, require the named Sequential Workflow Operation, its exact declared channel, and its optional argument definition to match the actual request value. All selected calls are validated before any event's business handler effects in this attempt.

**C09.** `requireExactDocumentVersion: true` compares `document.blueId` with the exact target member BlueId from the **input graph**, before this attempt's initialization, another member's work or handler effects. Equality of resolved business projections is insufficient. No retargeting occurs. When the flag is false or absent, the optional document field imposes no exact-version restriction.

When the operation's declared request definition is present, actual `request` must be present and satisfy actual-field matching. Without a declared request definition, absent request arguments are permitted. On an actual recipient a wrong type, missing required field, unknown operation or target-channel mismatch rejects before observer effects; it is not a partially accepted call.

**C10.** At external execution, combine the named operation and all matching ordinary workflows on each consuming channel in their defined handler order. Only the operation on its declared fresh target channel is eligible. Observing this event through another primitive or union channel does not invoke it again. A new observer union seeing an already consumed call does not repeat the target channel's operation, request validation or exact-version precondition.

<a id="section-9"></a>
## 9. External channel acceptance, lifetimes and checkpoints

### 7.1 Deterministic acceptance

**C11.** Offer the complete external event to primitive external channels in every active member of the input graph. A standard External Channel accepts when its optional filter matches. An installed deterministic external-channel runtime returns a Boolean acceptance decision from its frozen header, complete original event, timestamp, previous checkpoint and explicitly declared peer access. It cannot replace the event.

Compute each union's transitive primitive-leaf set, rejecting non-external members, missing names, duplicate direct members and composition cycles. A union accepts if at least one of its leaves accepted. Set semantics ensure that overlapping paths contribute one acceptance for that union. Empty composites and All External Channels over no primitives accept nothing.

A document that accepts no primitive does not execute or validate a local named call. A document that accepts the event must have a compatible target for its recognized call when fresh work is selected. Thus broad bare channels on several members deliberately expose the same event to those members; intended discrimination belongs in channel acceptance filters, not a hidden documentPath parameter.

### 7.2 Freshness and no invented ordering protocol

**C12.** This revision's built-in local checkpoint rule suppresses an exact repeat of the **last successfully consumed event** in a channel lifetime. If checkpoint event ID equals incoming original event ID, timestamps must also equal; equality produces no new consumption, and a changed timestamp produces `EVENT_TIMESTAMP_CONFLICT`. If the event ID differs, the input is fresh for this built-in rule.

This is not an all-history deduplication service or a source-order protocol. Contracts does not reject a distinct event solely because its timestamp is lower. A host requiring ordered history or permanent occurrence uniqueness must establish it outside Contracts, or install a precisely bound deterministic channel runtime that verifies the relevant actual event evidence. Equal business payloads used as different external occurrences need distinct original external content; changing only the supplied timestamp does not give an identical checkpointed event a new identity.

Primitive and union checkpoints are independent. Consuming a union does not advance a leaf that did not consume this event. Accepted input with no matching business handler still advances its checkpoint. Internal events do not.

### 7.3 Channel lifetime identity

A primitive lifetime signature binds its exact runtime type and acceptance definition. Extension signatures also bind the complete extension specification and header fields. A union signature binds its exact type, sorted leaf names and the current leaf signatures. A changed acceptance or membership signature starts a new serial generation; removal retires the lifetime. Ordering-only edits do not create a fresh acceptance lifetime.

A frozen seed is eligible only while the same member activation and channel generation remain live. Removal, replacement or changed acceptance cancels remaining old work. Checkpoints belonging to retired generations are reset during final settlement. This prevents an old checkpoint from being silently transferred to a different channel at the same key.

<a id="section-10"></a>
## 10. Deterministic completion machine

**C13.** All implementations execute the same logical machine:

```text
verify exact inputs, configuration and the input graph
freeze primitive/union acceptance and validate selected calls
if the root is already terminated: return TERMINATED
establish input initialization using completed child results
process dependency units before their containers
    run document-local turns
    drain only that document's local queue
    settle its eligible markers and checkpoints
    seal the completed result
    incorporate completed child results before their parent observes events
finish required cyclic rounds and dynamic initialization
finalize the exact graph and verify every affected containing context
return one atomic APPLIED result
```

A dependency unit is initially a strongly connected component of the active managed graph. A singleton without a self-edge is an acyclic unit. Units run dependency-first. Internal graph membership and queues are private processor state; no public delivery wrapper is added.

For a static DAG and one input phase, a member with work has one local turn: it first incorporates all required completed direct-child results, processes their queued events, then handles its frozen external seeds. Its output is not handed upward between channels, patches, steps or event handlers. Initialization is a separate no-external-input phase; its output is not replayed as external work.

A member with neither new child state/events, initialization nor fresh seeds is carried unchanged. Every required header and acceptance fact is still verified; an optimization cannot skip ordinary workflows or another accepting channel merely because one operation name is known.

### 8.1 Fixed ordering

Use the defined exact member keys, NFC token rules, decoded pointer rules and Unicode code-point comparisons. Condensation dependencies precede containers; among ready components choose the lexicographically smallest sorted member-key tuple. Within a cyclic round, visit members in key order. Physical completion order is never a tie-break.

For each receiving turn, order source completions by source member key; within a source, order its completed batches by source turn serial. Within a batch, iterate event ordinal first, then the receiver's eligible occurrence paths and generations. Thus two occurrences of one child see `E1/path1, E1/path2, E2/path1, E2/path2`. Equal-content emissions remain distinct occurrences.

Install all required incoming source states before invoking any receiving handler, validate the resulting receiving view, and append all initial incoming event occurrences in that order before draining. Events emitted by the receiver append to its queue tail. After that drain, execute its surviving external seeds in channel order, draining local events after each seed as in the defined. Incoming work can terminate the receiver or retire a seed before its direct external handling.

Channels and handlers retain `(order, raw contract key, exact runtime type ID)` with zero default order. The stable bottom-up merge comparator in `LogicalWork.ordered` fixes comparison gas. Freeze channel-dispatch candidates and their headers; check each actual-value filter immediately before that handler. Newly installed handlers cannot join an already frozen dispatch.

### 8.2 Execution contexts

**C14.** Context access is unchanged except for the newly specified sealed dependency views:

| Access | External handling | Internal/lifecycle handling |
|---|---|---|
| `$event` | Complete original external event. | Current update, lifecycle or embedded delivery / local event. |
| `$binding: call` | Complete selected Operation Request, where applicable. | Absent. An embedded event cannot become another operation. |
| `$binding: call/request/amount` | Selected request argument. | Not an alternative internal-event accessor. |
| `$binding: processingEvent` | Original external event. | Same attempt cause, when one exists; absent for explicit initialization. |
| `$binding: timestamp` | Supplied microseconds. | Same causal timestamp when present; no fabricated initialization time. |
| `$document` | Current member's frame and pinned exact dependencies. | Same rule. |
| `$steps: name` | Prior named step result in this handler. | Same rule; each handler has its own result map. |

There are no `operationRequest` or `request` bindings. Immediate local continuations restore the suspended event context. A child-batch receiver sees the existing Embedded Event Delivery shape, not a source intermediate read view. The immutable event payload can report an earlier value while `$document` reads the child's completed state.

<a id="section-11"></a>
## 11. Nested steps and BEX effects

**C15.** A handler initializes an empty named-results map and executes its steps in written order. A step result key is its `name`, or its decimal list index when unnamed. Duplicate keys within that handler fail. Names and numeric defaults share one namespace. Returning from Compute returns from that program, not from the whole workflow.

For Compute, execute the existing BEX program and collect its value, changeset and events. The defined's return-object convention remains: when the returned value is an object, present `changeset` and `events` members override the corresponding accumulated result lists; otherwise the accumulated lists are used. Both lists must validate. This convention is a Contracts interpretation of a BEX result, not a BEX operator change. Store the named result, apply all selected patches with their immediate local continuations, then enqueue its events in order.

`$document` remains stable during a single Compute; `$resultValue` reads that Compute's accumulated changes over its starting value according to BEX. A later step sees the applied state and all completed immediate **local** update continuations. A program that alternates appendChange and appendEvent still returns separate changes and events; Contracts applies its changes before recording those returned events.

### Shared Compute definitions

`definition` is optional. An inline object or exact Blue reference selects a
library of `constants` and `functions`. A nonempty Text beginning with `/` is a
Language JSON Pointer relative to the current managed document; other nonempty
Text names a sibling in that document's `contracts` map. A named sibling can use
`type: Compute Definition`. No registry alias, external URL or mutable global
lookup is performed. Resolve the operand afresh when the step executes, after
all preceding steps and their completed local continuations. Unused handlers do
not resolve or compile their definition bodies.

Only `constants`, `functions` and ordinary Blue labels/type/specification/order
metadata are allowed in a definition. Its maps must be objects. Missing paths,
wrong shapes, cyclic executable definitions and unavailable exact evidence never
become an empty library. Missing evidence retains the existing NEEDS_RESOURCES
classification; malformed inputs fail atomically.

Merge each imported map with the step-local map, with local names taking
precedence. Validate/compile the merged program, including its function graph.
`entry` selects a zero-argument function; otherwise the step's inline `expr` or
`do` is used. A definition supplies no implicit entry or executable root body.
Functions use this step's context, effect accumulators and shared gas. `$resultValue`
in an imported function sees the same step overlay as an inline function.
Definition lookup/extraction charges the existing manifest, member/item-read and
Text-work counters before reads; compilation retains its zero semantic tariff.
No program cache may skip these charges or use an earlier document's definition.
`$currentContract` observes the configured step; imported functions are available
for execution without being invented as locally configured step fields.
Effects commit only through the existing atomic Contracts result.

Update Document evaluates its changeset expression with no allowed BEX effects, validates the resulting list, saves `{changeset: ...}` as its step result and applies each patch in sequence. Trigger Event similarly requires an effect-free expression and records one resulting immutable value. Terminate Processing enters termination handling and stops further ordinary steps for that member.

<a id="section-12"></a>
## 12. Patches, validation and local Document Updates

**C16.** Retain add, replace and remove; nonempty relative JSON pointers; exact `~0`/`~1` decoding; canonical list indices; normalized list append; absent before/after sides; and exact no-op detection from the defined. Root replacement through an empty patch path remains invalid. Runtime list pointers are `/lines/0`, not Source `/items` paths.

A parent cannot patch strictly inside a separately managed child. It may replace/remove the whole attachment or an allowed ordinary enclosing structure. A patch validates the current member's own exact local result under Language and its retained generalization policy; it does not mutate or validate a containing member against the source's intermediate state.

Retain the defined protected-state checks. Ordinary effects cannot forge/change initialization, termination, checkpoints or protected policy. Apply the requested patch and any permitted generalization as one valid tentative local change. A failed local validity obligation fails the attempt. There is no temporary-invalid-patch exemption.

Reconcile the current member's occurrence declarations after a structural patch. Retire old generations immediately. Initialize genuinely new children to local completion through the initialization barrier in the annex, using only sealed dependency views. Incorporate their completed state silently; enqueue their completed event batches without re-entering the current handler. Then deliver the creating member's local patch notifications. The next normal step cannot see an uninitialized newly created child. If a newly forming cycle prevents recursive initialization, initialize its uninitialized members in deterministic rounds against their last exact pre-initialization views, as defined in A08; do not recurse indefinitely or expose the creator's live frame.

**C17.** A Document Update is delivered **only in the managed document that produced the business patch**. First deliver generated generalization type updates, then the triggering value update. Each notification completes its immediate local continuations before the next patch, step or ordinary handler.

A channel path matches a change iff its decoded segments are a prefix of that change's decoded local pointer. Ordinary nesting is still observable. A separately managed boundary is not ordinary nesting. No reverse embedding-route traversal, translated `/child/...` path or forwarded update occurs.

For `A → B`, B changing `/count` invokes B's local update handlers only. A's own explicit replacement/removal of `/b` is an A-local patch and can invoke A's handler at `/b`; an A handler at `/b/count` does not hear an ancestor replacement. Automatic incorporation of B's completed state invokes neither.

### Receiving validation is separate from source calculation

B must be valid under B's own exact admitted definition and dependency context. When A incorporates B's completed state, A must remain valid under **all** its own local/inherited contextual requirements. Incorporation does not erase a constraint, generalize automatically, or replay intermediate child changes. An invalid completed incorporation fails before A's observers run and rolls back this attempt. Parent-specific constraints therefore can reject the composed attempt without changing B's local calculation. Any enclosing refinement that Language includes in B's extracted exact local definition/context must travel with B and still constrains B's intermediate local patches. Do not strip such requirements to make a cached result reusable; a differently refined B is a different chunk input.

<a id="section-13"></a>
## 13. Local FIFO, output batches and lifecycle

### 11.1 Application emissions

**C18.** Maintain a FIFO and an output list **per local turn**. Emission captures an exact immutable Blue value, allocates a source-local occurrence ordinal, appends it to that turn's output list and enqueues it for that document's Triggered Event Channels. An event produced by local handling is another output occurrence and joins the tail. Draining local work never removes an occurrence from the output list.

No origin callback routes directly into a container. A source turn finishes all required local work and marker settlement before its output is sealed. The receiver first incorporates the completed source state, then queues the complete incoming batch through its own eligible direct-child occurrences. Queue the whole batch before executing any handler for it. Queue entries are tagged LOCAL or EMBEDDED: imported events are not automatically this receiver's own emissions, do not use its Triggered Event Channels, and do not enter its output list.

Embedded Node Channel's filter checks the inner exact child event. Its workflow sees `Embedded Event Delivery {sourcePath, event}` through `$event`; its local emitted responses subsequently use the receiver's own Triggered Event Channels. Internal Operation Request-shaped events never trigger external operation recognition.

Only direct-child application events cross an embedding boundary. In `P → A → B`, P hears B only if A explicitly emits its own corresponding event. B's completed state can still change A's and P's exact contained content **silently**, including when every output batch is empty.

Example: B emits E1; its E1 handler emits E2. B drains E1 and E2 before A receives `[E1,E2]`. A queues both. If A's E1 handler emits P1, A handles embedded E2 before local P1. All A reads of B use B's completed view, not B's view when E1 was emitted. Receiving one event, draining A, and only then supplying the next event is nonconforming.

Source-local occurrences and receiver occurrences are different identities. A source packet contains no ancestor paths. The receiver binds `(source completion, event ordinal, edge occurrence)` and consumes each such delivery at most once inside this attempt. Snapshot reuse alone must not redeliver it. In a cycle, newly emitted responses are new occurrences; loop suppression is not global deduplication by event content.

### 11.2 Initialization

**C19.** Capture every newly discovered uninitialized member's exact pre-initialization BlueId **before any initialization in that discovered group changes its content**, including initialization of its descendants. For input members this is the initialization-phase starting view; for runtime-created members it is their discovered creation view. A current exact cyclic set is captured as a set before any member's lifecycle writes. Mark initialization in progress before invoking callbacks. Deliver Document Processing Initiated with `document: {blueId: capturedPreInitializationDocument}`; no external event or timestamp is invented.

An acyclic initializer first obtains completed child initialization results. It silently incorporates their states, runs its own initialization lifecycle dispatch, then drains the prequeued child events and locally generated events in FIFO order. Child events that were prequeued remain ahead of events emitted by that lifecycle handler. Settle its protected initialized/termination markers before sealing its initialization result. Cyclic initialization uses the round rules in section 12 and A08, with exactly one initialization dispatch per new activation.

During an ordinary handler, a newly created child's initialization is a nested completion barrier, not a second external seed. The creating parent retains its suspended frame; the child reads only exact sealed targets, never that frame. The child result is incorporated before the creator's next normal step; its events join the creator's local queue in a complete batch. The creator does not publish a result until this work and its own queue finish.

Already legitimately initialized members are not initialized again. Attaching a supplied initialized version does not replay old output. Failed initialization rolls back all effects and protected markers. Initialization marker writes themselves are silent.

### 11.3 Termination

**C20.** Request termination once; run the member's termination lifecycle handlers through the same local effect rules. They may produce valid changes and events. Stop further ordinary processing in that member, discard its not-yet-dispatched ordinary local work, settle its protected termination marker, and seal the resulting output if the attempt succeeds. Already emitted values remain in the output list; termination is not erasure of the source's completed emissions.

The parent may observe a terminated child's final state/output only after completion. A terminated parent installs required completed reference changes silently if its containing state remains required, but does not run ordinary handlers. A root already terminated at entry returns TERMINATED as before. An error or gas failure is rollback, not an emergency termination marker.

<a id="section-14"></a>
## 14. Dynamic graphs, collections, shared members and cycles

**C21.** The `paths` and `collectionPaths` expansion rules require maps for collections, absent paths contribute none, lists at collection paths fail, nonempty valid pointers outside `contracts`, no duplicate or overlapping boundaries. Reconcile structural changes and allocate new edge generations in member/path order. There is no fixed maximum on active documents, edges, contracts, steps, effects, routes, turns or rounds. Retired history is not active work. Charge the required logical graph and processing work to the same invocation ledger before its charged action. Actual membership, complete validation and occurrence lifetime rules still apply; omitting a count check does not authorize pruning the graph or skipping recipients.

**C22.** Resolve a target using an unambiguous current exact binding, then an explicitly selected verified archived exact view, otherwise a valid unmarked fresh child. Marked content without required managed-state evidence needs resources. No automatic latest-state lookup and no merging members merely because business values match. Explicit equal-content distinct members and repeated occurrences of one shared member remain representable.

For a shared DAG child, calculate its compatible local result once for the selected attempt, then bind it separately to each surviving parent occurrence. Repeated references do not duplicate its operation. Distinct exact starting views or seed/context requirements are not one reusable calculation. Stable keys and occurrence generations are never replaced by a bare content-hash deduplication rule.

**C23.** Use the real Language cyclic-set builder and owning-set proofs for exact cyclic content. Distinguish identity finalization from handler execution: rebuilding cyclic references does not emit a business update or by itself schedule another turn. A10 → B7 → A5 keeps A5; it is not a live A10 alias.

### 12.1 Cyclic processing: complete turns, common rounds

An acyclic document can finish before its containers. Members of a live cyclic component cannot all finish before each other. A cyclic **unit** therefore runs deterministic rounds:

1. Freeze a coherent exact component view for the round. All peer/self managed reads use that completed round view.
2. Take the pending batches for each member and, on its one eligible seed round, its still-live frozen external seeds. Process each member's complete local turn in member-key order. No peer sees that member's intermediate state or locally generated events.
3. At the round boundary, merge member-local owned changes, not whole overlapping graph snapshots; reconcile generations and finalize the actual cyclic sets with Language. Validate the resulting exact component. New member outputs become complete input batches for eligible peers in the **next** round, ordered as in section 8.1.
4. Repeat while an internal batch, pending initialization or unconsumed eligible seed remains. A state-only reference refresh does not create an endless sequence of empty rounds.

External seeds and initialization notifications occur at most once per live activation/generation. Feedback can cause further local turns but not redispatch the original operation. The common gas budget bounds feedback. No member commits independently inside the unit.

All outputs to containers outside the unit are held until it quiesces. An outside parent receives the final exact component view plus the ordered output occurrences of the member(s) it directly embeds. It does not receive snapshots from intermediate rounds. A one-member self-cycle follows these same rules.

The preceding-round peer view is an explicit new rule, not a claim that the old shared FIFO already behaved this way. It prevents deadlock and gives a precise completed-view meaning in cycles.

### 12.2 Dynamic joins and splits

Apply topology changes at the safe boundaries in A09. Existing occurrences retire immediately in their producing frame and at the next relevant dispatch check. A newly created child is initialized through its creation barrier; it gets no retroactive external seed.

At a sealed local/round boundary recompute the live SCC partition. If a new cycle spans current execution units, merge those units, retain already consumed seed/delivery identities and sealed local states, and continue round processing for their pending work. A suspended creator is not a sealed peer: new children use its pre-turn sealed view until the creator itself finishes. Do not release a completion across a boundary now inside an unfinished merged unit.

Once units merge, keep that execution-unit union until this attempt ends, even if an edge is later removed. Final **Language identity** components still use the actual resulting graph, not the retained execution grouping. Next invocations start with the new graph's ordinary partition.

New routes cannot receive past output merely because a packet is retained. Initial-phase routes are captured before its source work; a fresh child's initialization routes are captured when that attachment becomes active. At each use require the same occurrence generation. A join carries pending eligible deliveries; it does not regenerate previously delivered ones or replay completed seeds.

**C24.** Removing/replacing an occurrence invalidates its pending **receiving** work. It cannot undo an already sealed source turn or interrupt that turn retrospectively. If A removes B while handling E1 from `[E1,E2]`, the E2 delivery through that retired occurrence is discarded; a replacement does not inherit it. Another surviving occurrence can still receive its batch. A source no longer reachable gets no later local turns through the retired route; its retained sealed evidence is not active capacity.

These rules cover both collections and cycles. An indefinitely responding loop must reach deterministic gas exhaustion through the prescribed positive per-turn/event/round charges. A physical interruption before that boundary is incomplete execution, not a semantic resource-limit failure. No partial success per lap, member or component is introduced.

<a id="section-15"></a>
## 15. Generalization and explicit valid retyping

**C25.** A patch must leave a valid document under the selected Language. The default automatic-generalization mode is reject. Invalid documents are not admitted just because a workflow requested them.

When a change fails only a defined semantic compatibility, fixed-value or schema check, inspect the changed subtree bottom-up and then its containing spine. For each affected explicitly typed node, select the most specific matching policy path by decoded prefix length; equal-specificity ties choose the first rule in the policy list. `defaultMode` applies when no rule matches.

In nearest-valid-ancestor mode, try the current type first, then immediate ancestors in order. At each candidate, charge candidate work and require the implementation to remain a subtype of the policy floor when present. Validate the implementation node with its unchanged local and enclosing requirements; a local rule, enclosing schema or required field cannot disappear just because a type is generalized. Stop at the first permitted valid candidate. An evidence error is not permission to keep searching. Detect type ancestry cycles. There is no independent candidate-count ceiling: charge each candidate and required validation through the existing logical meter before continuing. Stop at the first permitted valid candidate, established failure of the permitted search, or actual gas exhaustion. Missing evidence or operational interruption is not proof that no valid ancestor exists.

Collect generated `/type` changes for all repaired affected nodes; finally validate the complete changed **local member**. Commit the requested value plus generated type changes as one valid tentative result. Local observers see the valid result; notify the type changes before the requested change's update. Failure of any remaining requirement rejects the whole patch and attempt.

**C26.** Explicit retyping is a normal controlled patch: a valid target definition and resulting content may be installed when the inherited/local context permits it and protected policy and managed boundaries are preserved. It does not imply automatic widening. Unknown target types, contradictory fixed requirements and incompatible enclosing declarations fail. A complete replacement can avoid depending on an invalid intermediate two-patch state; individually invalid intermediate patches are not temporarily accepted.


Enclosing constraints **within** the member continue to apply. A separate container is validated when it incorporates the completed member; it does not contribute an invisible mutable parent context to source execution. This changes the Contracts observation/validation boundary, not Language's validity relation.

<a id="section-16"></a>
## 16. Lazy content and installed runtime extensions

### 14.1 Lazy executable bodies

**C27.** Every contract header must resolve to an understood exact role. The runtime may retain separately addressed data and executable-body references. At discovery, read required headers, configured fields and type evidence, not every unused BEX body. At selection, demand the chosen workflow steps and each executable step, and compile/validate the demanded BEX. An invalid unused program is not executed speculatively; calling it must expose the error.

This is not a claim that first-time admission validates nothing beneath a reference. Full initial Language admission and cold restoration may require referenced content. Initial admission and restoration establish complete admitted state; executable loading and compilation occur when demanded. A physical page cache does not change these obligations. Previously established exact evidence may be reused only when bound to the same content, requirements and release. Missing required resources suspend rather than becoming empty objects or zero-cost successful work.

An unchanged large value retains its exact BlueId. Any eager/cached implementation must preserve the same state, events and logical gas. Cache warmth and network time are not semantic gas tariffs.

### 14.2 Extension registry and immutable bindings

**C28.** A RuntimeBinding pins the exact custom type ID, exact semantics-document ID, role, header/body field names, private gas namespace and tariff, optional inheritance to descendants, explicit peer fields, and live or ledger meter mode. The full record is immutable and committed in snapshots. Installing new types does not install their executable behavior. Standard implementations cannot be rebound. Conflicting bindings fail.

Roles are external-channel, processor-channel, handler, marker, nested step and dispatch-policy. A dispatch-policy must descend from Compute; its selected exact binding is the only exception to nested Compute placement. A channel type must descend from Channel; a handler from Handler; a marker from Marker; a step from Contract. Standard abstract catalogue types do not count as concrete implementations. Descendant inheritance is enabled only by the binding's explicit flag.

An external-channel callback receives read-only header, complete original event, integer timestamp, prior checkpoint, bounded declared-peer lookup and live meter. It returns exactly a Boolean. It cannot return another event, a payload path or a delivery plan.

A processor-channel extension explicitly declares one or more internal families from TRIGGERED, EMBEDDED, UPDATE, INITIALIZATION and TERMINATION. Its accepted current internal payload is constructed through its installed deterministic `channelize_internal` semantics; this is internal notification handling, not external request extraction. Peer lookup is limited to fields explicitly declared in the immutable binding. All callback behavior is part of the installed semantics.

Handler/step extensions receive frozen event, header, selected body, previous step results, original cause identity, timestamp, member-local read function, gas meter and selected external call when applicable. They return a closed Contract Execution Result. Validate the entire staged result before applying effects, then use the same patch, continuation, FIFO, termination, boundary and rollback machinery as standard handlers.

Runtime implementations are trusted deterministic code; read-only Python wrappers are not a security sandbox. They must not depend on unrecorded clocks, randomness, I/O or hidden global state. A production host must provide the corresponding isolation outside these Contracts semantics. No authorization power follows from installing an extension.


All extension callbacks obey the same frame and completion boundary. An UPDATE extension sees local updates only. An EMBEDDED extension sees complete-batch entries after sealed source incorporation. No callback receives a live parent frame, enters another member recursively as an event side effect, or mutates the output list after sealing. Runtime ledger merging uses the same ordered logical work protocol as standard handlers.

<a id="section-17"></a>
## 17. Logical gas and host-independent resource semantics

This edition retains the shared default and maximum of 10,000,000 gas units per entire atomic attempt, including embedded members and cyclic rounds. Numerical tariffs, debit ordering, rejected-charge accounting and rollback are unchanged. Explicit smaller invocation budgets and member-local ceilings remain supported.

Prior editions retain their original identities and their specified maximum: 100,000 for the earlier editions and 10,000,000 for the preceding gas-10m edition. Hosts MUST select the rules and budget maximum bound to a document's edition and MUST NOT silently upgrade retained snapshots, invocations or receipts. The allowance is permission for logical work, not a CPU or memory reservation or a guarantee of physical completion.

**C29.** the logical gas schedule appendix and the metering appendix define the exact logical meter. The shared maximum and default remain **10,000,000**. There are no unrelated structural/resource ceilings. Gas MUST NOT be increased beyond the specified maximum, disabled, or charged by host time or memory. Existing numerical tariffs are retained unless an explicitly recorded and qualified metering correction is necessary. Any such correction must define its exact counter, units, charge position and order before publication; preserve BEX value/evaluation semantics and distinguish the changed gas edition from physical optimization.

One shared scalar gas meter covers the complete rooted attempt; the default/maximum shared allowance remains 10000000. Member ceilings are additional constraints on that same meter. Charge the specified amount before its work; update the total and any configured member-local total. Accepted charges have no canonical row, ordinal or transcript. Retain the shared/local exhaustion tie-break and one compact first-rejected-charge diagnostic. Rollback does not refund admitted work.

This edition removes accepted-charge traces from outcomes, receipts, portable chunks and completion records. The deterministic final admitted `gas` total is the public metering result. Optional debug traces are noncanonical, off by default, and MUST NOT affect identities, replay, state or charge decisions. They are not required for conformance or durable publication. Prior editions and their receipts keep their original meanings.

Turn and unit records carry a scalar `gas` contribution instead of `workSegment`. Continuation commitments bind the current shared total and configured member-local totals, not an accepted-charge transcript. A scalar supplied by an untrusted worker is not proof of execution. Verify execution against the captured input and current remaining budgets, or use an unchanged trusted in-process result; re-execute when a cached result cannot establish the exact exhaustion boundary. Never debit an unaffordable completed scalar and claim it is the first rejected primitive charge.

The canonical logical schedule is the dependency order, local turn order and component-round order in the annex. Chunk dispatch, transport, wall time and physical cache reads create no extra semantic charges. A cached chunk supplies the same verified execution and scalar gas contribution; verify it against the attempt's current meter **before** accepting any effects. It cannot skip work, reset allowances, erase a rejected prefix or be merged twice. Runtime callback namespaces and sealed runtimeLedger rules follow the metering appendix.

A standalone `process(B, e, t)` includes its own setup and root projection. Its scalar gas is not blindly added to another standalone `process(A, ...)`. Full equivalence uses one normalized attempt: shared preflight/finalization once, each logical member computation once per prescribed turn, each receiver's required application work, and the selected root's projection once.

The protocol has no separate maximum document/edge count, contract-map size, workflow-step count, patch/emission/route/dispatch count, turn/round count, content/path/filter/program depth, executable-body size, token length or generalization-search length. Keep the required syntax/normalization and exact value/format rules; remove only the unrelated resource ceilings. Explicit authored constraints and supported stricter member gas budgets remain enforceable.

The standard whole-attempt gas maximum is still 10,000,000, not 10,000,000 per member, page, chunk or component round. Existing explicitly selected lower test/invocation budgets and member-local ceilings remain supported and bound into execution evidence; a machine-specific shortage must not silently lower the authoritative budget. Exactly spending the remaining gas is allowed if no further charged work is required; the next unaffordable charge is rejected before its corresponding work. Retain the existing tie-break and rejected-charge fields except the legacy ordinal; this edition does not record an accepted-charge position.

All repeatable semantic progress formerly protected only by a removed count guard must have a defined positive logical charge or a finite structural termination argument. A scalar-expression base charge is not evidence that arbitrary-size arithmetic, copying or materialization is adequately metered. Review these paths before claiming gas-bounded processing. Reuse defined counters/quantities where they already describe the work; do not derive costs from Language's physical step count, a worker timeout, cache warmth or bytes actually fetched from a warm/cold database.

Gas is a portable work rule, not a promise of a fixed number of milliseconds, bytes of RAM or I/O calls. A correctly supplied under-budget invocation remains the same computation on every conforming host. Local inability to finish it is not a new semantic outcome; the host must improve capacity or implementation and retry the original pending work without increasing its gas allowance.

<a id="section-18"></a>
## 18. Atomicity, replay and chunking equivalence

**C30.** A sealed child or component completion is a **calculated value**, not a separately committed document. All affected state, output, protected markers, channel lifetimes and graph identities remain tentative until the entire selected attempt succeeds. Any failure rolls back the entire attempt; public events are empty on failure. Retain admitted gas diagnostics under the stated failure policy.

**Physical interruption is not a completed failure.** Memory/stack exhaustion, a configured host work cutoff, timeout/cancellation, unavailable storage or a failed worker before completion must not be translated into `GAS_LIMIT_EXCEEDED`, semantic `FAILED`, `TERMINATED` or invalid input merely because execution stopped. Unwind or abandon the tentative attempt and communicate a typed host/incomplete condition outside the canonical Outcome. The original committed state and input remain authoritative. A partial gas total is diagnostic evidence only, not a completed receipt or terminal input disposition. Missing exact content continues to use the supported `NEEDS_RESOURCES` mechanism. If publication may already have committed, reconcile its original identity before another execution.

Checkpoint settlement occurs at the end of the eligible member turn so its completed state contains the consumed-original-event checkpoint. Validate the same activation and channel generation; retire old checkpoints on generation change. Later structural edits cannot transfer these records to a replacement. Final graph verification still runs before returning APPLIED. A parent that merely receives a child batch gets no external checkpoint from that receipt.

**C31.** Replay fixes the exact starting snapshot, original event, microsecond time, release, Language/BEX profiles, runtime bindings, selected exact dependency views and gas policy. It reproduces the exact resulting documents, root output occurrence order, checkpoints, status and canonical logical work evidence and final gas total. Physical task identifiers, storage fetch order and cache statistics are not semantic trace fields.

### 16.1 Required composition property

For identical fixed inputs under this edition:

```text
reference rooted processing
    ==
execution of its ready complete chunks, followed by verified incorporation
```

The equality covers exact Blue documents, event occurrences/order, legitimate processing metadata, success/failure and logical gas. Both paths execute the same A01–A12 algorithms. A monolithic processor is an eager driver of that machine; it is not an alternate interleaving implementation.

For an acyclic `A → B` where only B accepts the input, obtain B's complete compatible result, incorporate its state and complete batch in A, and finish A. For `P → A → B`, use A's **own** resulting batch in P. A's other children are pinned dependencies, not automatically operation recipients. The processor nevertheless checks every relevant accepting header, validation and read requirement.

An independently calculated B result is reusable only when its exact before-view, cause/time, local seed selection, runtime profile, dependency bindings, completion boundary and logical work agree. Retyping context, distinct archived view, another source turn, old channel lifetime or cyclic peers can invalidate reuse. A final state plus event values is the semantic payload; exact bindings and work evidence make it safe to substitute. No intermediate source-patch transcript is required under this new boundary.

The guarantee is not that arbitrary standalone commits, arbitrary root relabelling, arbitrary per-event application, or arbitrary graph cuts are equivalent. A cyclic component is a complete external chunk; its internal turns use the specified rounds. A dynamic join removes a former acyclic cut and must expand the chunk boundary before further external exposure. Chunk partitioning cannot change these boundaries.

### 16.2 Read-only exact content and persistence

Existing snapshot/invocation export concepts remain, but their release and changed record domains must be regenerated. A saved chunk is not accepted as a public event. Missing or incompatible evidence fails closed. Immutable bytes can be stored before success without publishing application state. Storage may atomically commit the final snapshot, receipt and output; it may not publish a chunk prefix as the whole attempt.

<a id="section-19"></a>
## 19. Conformance and integration

`CONFORMANCE.md` is the required acceptance matrix. `EXAMPLES.md` gives worked expected results and small Source YAML examples. The illustrative model retained under `inputs/contracts-completion-1-design/model/` is not the runtime. The actual executable qualification uses `tests/contracts_event/` and the website’s shared guide fixtures.

A conforming runtime must compare a direct driver and a chunked driver of this same new machine for exact state, occurrence order, checkpoint state, gas and failures. Conformance cases MUST cover local Document Update boundaries, child-first completion and parent observation of completed child states. Do not silently delete lifetime, shared-graph, cycle, resource or extension tests.

The executable appendix contains the exact reference algorithms; the package supplies finite conformance evidence separately.

<a id="section-20"></a>
## 20. Normative algorithms and provenance

The prose, detailed transitions, executable algorithms and gas schedule in this document form one normative contract. A contradiction is a specification defect, not an alternative implementation mode.


`inputs/contracts-completion-1-design/CURSOR_PROMPT.md` records the implementation and publication assignment. It does not delegate the decisions about local updates, batch placement, final child read views, cycle rounds, occurrence retirement or atomicity: those are specified above and in A01–A12.

<a id="section-21"></a>
## 21. Generic Coordination integration boundary

This edition adds read-only runtime context and controlled retained completion application. It does not add Timeline semantics to Contracts and does not alter `process(document, event, eventTimestamp)`.

An external channel receives its exact member, input document, channel key and generation, and a deeply immutable admission observation. The installed runtime verifier derives that observation from frozen evidence bound to the input snapshot, original event/time and registered runtime semantics before any seed is selected. A caller-supplied Boolean is not evidence. Portable invocation restoration repeats verification. Primitive channel acceptance remains Boolean and cannot replace the original event or the selected complete call.

`capture_source_outcome` issues an opaque capability only for an unchanged successful outcome produced by this Processor. `install_completion_reader` is a privileged one-time host integration hook for protected local storage, never an upload API. A reader must establish the retained before/after snapshot, exact receipt, event/time and runtime bindings. Unverified foreign results cannot enter through it. Retained receiving application requires the exact source predecessor, original member identities and complete inseparable source unit. It installs all eligible source state before callbacks, routes complete own-event batches through the same local kernel and supplies no receiver external seed or source business execution. Duplicates, incompatible runtime bindings, conflicting views and unsupported cyclic cuts fail atomically. This edition defines no portable receiving-export protocol; implementations MUST NOT fabricate such evidence.

`begin_live_application(document, source_completions, evidence=...)` is the corresponding combined LIVE preparation. It verifies admission and freezes external seeds against the original receiver input, then installs the complete required retained dependency results. Adopted owners and their already completed dependency closure are excluded from local execution. Receiving reactions run before the receiver's surviving own seeds, as required by C13. Only the completed invocation is publishable. Historical receiving remains seedless. Both preparation paths require the same protected completion provenance and exact predecessor checks; neither changes the public three-input processor interface or combines independent gas totals.

The hardening edition corrects a reference defect in the source-turn commitment used by emitted occurrences. Execution certificates include invocation-wide logical work and remain bound and checked as execution evidence. Such a certificate must not rename a member's application emissions merely because a different containing root drove the same semantic turn. The semantic incoming commitment binds each ordered batch's source member, serial, completed after-view, ordered emitted occurrences and captured occurrence tickets, together with the turn's existing cause, local before-view, dependencies, seeds, phase and lifecycle. The complete certificate remains in `turnInput` for replay verification. The full certificate remains required execution evidence; its encoding is distinct from the semantic occurrence key.

The local driver can complete an untouched local attempt without allocating portable token/candidate envelopes. It executes the same readiness, work-unit and finalization transitions, including every logical charge and first rejected charge. An attempt that has issued a token or accepted chunk history cannot change driver. Transport identifiers and copies are not logical work. Equivalence qualification compares outcomes, occurrence order, checkpoints, final gas totals, rollback and low-budget failures.

Committed local turns retain exact handler/declaration attribution for each patch. This is protected execution evidence used by higher-layer lifecycle policies; submitted documents cannot author trusted attribution. Archive imports preserve original managed-member keys when unambiguous, so independently selected historical roots retain occurrence identity. Exact historical addresses still select their archived state, never an arbitrary newer live alias.


<a id="section-22"></a>
## 22. Lazy immutable host values

An event, call, processingEvent or selected document collection is an immutable exact view bound to its effective Language recipe and captured resolver. Scalars are ordinary BEX values. Reading a root returns a view, not a recursively expanded JSON tree. Member/item access follows only the demanded path. Keys and presence retain Language meaning, including inherited values and absent declaration holes; missing evidence needed to establish presence remains a resource dependency. References are not ordinary business objects containing a blueId key. `$get`, `$keys`, `$var`, function arguments and subsequent pointer reads use the same collection interface as direct paths. Copies retain the captured view.

Serialization across a Blue output boundary retains the selected exact node and finite reference boundaries. It must not unfold predecessor history, replace a referenced value by null, truncate its meaning, or hash a display projection as its exact identity. Referenced and inline values have the same effective observation. Cyclic exact references retain their owning evidence. User programs cannot manufacture host capabilities.

Logical document/event member and item reads use the Contracts counters; node manifests are charged once per invocation logical inventory, independent of physical cache warmth. BEX arithmetic and control tariffs are unchanged. Size-dependent BEX output charges for an exact host value use the canonical exact-transfer accounting token specified in the metering appendix, independent of its inline/reference storage form; demanded traversal has separate logical charges. The shared meter does not reset on path reads. Any explicitly selected physical Language control remains out of band and cannot create a semantic rejection. Explicit BEX `$fail` / `$failIf` reports EXECUTION_REJECTED, distinct from invalid executable syntax or an internal runtime error.

There is no protocol depth ceiling on demanded access. A selected subview keeps its exact resolver, logical meter and read context when copied, bound to a variable or passed as an argument; splitting a path cannot reset gas or skip required logical member/item charges. Untouched reference ancestry remains unopened. Host recursion failure is an implementation inability to complete, not proof that a valid deep value violates Contracts.

A well-formed unaddressed request with zero operation candidates does not invoke an operation. Eligible ordinary observers can still run, preserving the original event and call. A same-channel candidate missing the operation remains an error. Union observation does not repeat an already consumed operation. Runtime-certified operation audiences are internal verified data bound to input snapshot, original event, exact runtime and channel generations, not a fourth caller input.


<a id="section-23"></a>
## 23. Exact-value transfer accounting

Compute may transfer an existing exact object or list without recursively pricing
its physically inline body. The captured Language recipe selects the exact
originating value, not its effective display and not a mutable latest head.
A single complete contribution carries verified admission/opening identity
evidence; a composition of contributions must first establish its exact result
with the prepaid runtime normalization/identity boundary. Requirements inherited
from a container do not rename its originating exact identity.

The BEX host accounting form is `{blueId: exactIdentity}`. This is a private
host interface, not another authored protocol or a validation assertion.
Generic host values and authored reference-shaped objects receive no admission
privilege. Scalars retain BEX scalar semantics; literal metadata and a bare
items slot are not independent exact-node capabilities. Runtime effect
normalization, target-context certification, and exact content/owning-proof
retention remain mandatory. Missing/invalid evidence has its specified
outcome. Captured cyclic identities stay finite and preserve their owning sets.

This metering selection does not redefine Language identity or BEX value semantics. A receipt is bound to its selected specification and tariff; it MUST NOT be reinterpreted under another edition.

<a id="section-24"></a>
## 24. Selected descendant evidence

A Language child recipe contains existing exact contributions, even when a
cached effective head returns different immutable instances of those contributions.
For a witnessed parent recipe, successful Language selection derives exact identity
evidence for each selected complete child part. Type/requirement resolution must
have succeeded against the captured resolver. Derive this evidence at the selected
boundary; do not recursively prescan or mark unrelated descendants. A physical
handle indexes the derived evidence but does not define it. Reconstruct it from
bound parent evidence after transport, independently of cache and cut placement.

This derivation applies to complete ordinary members, list elements and the
complete contracts node, not literal metadata or the items sequence slot. It does
not combine multiple contributions or discharge contextual requirements. Unknown
parents confer no descendant capability. A genuinely synthesized exact result
still uses prepaid establishment; only its successful ordinary result may issue
a reusable identity witness. A cyclic token-context hash is not an ordinary
identity. Incomplete or rejected establishment must not issue a result witness.

Canonical transfer tokens and value semantics are defined by the exact-value transfer accounting rules. Read,
normalization, validation and effect tariffs still apply in their prescribed order.
The same selected exact descendant has equal final gas and rejection behavior under
inline, reference, mixed, cached, restored and transported representations.
<a id="transitions"></a>
## Appendix A. Complete transition model

### A00. Values, identities and retained helpers

Use the selected Language bridge for exact values, contextual recipes, actual-field matching, valid type ancestry, pointer reads/writes and cyclic-set finalization. Retain BEX evaluation unchanged. The executable appendix supplies the complete helper implementations; A12 defines their integration responsibilities. Do not use a mutation pattern that exposes working state through `Run.patch`, `Run.drain` or global graph finalization to reintroduce parent observation of a working frame.

Comparison of member keys and raw keys is Unicode code-point comparison after the Language validity/NFC checks. Pointers compare by decoded segment tuple; segment strings use that comparator. Integer ordinals compare numerically. Empty values, absence and null retain their different defined meanings.

For private processor commitments, use the defined `canonical` and `digest` functions, with the following domains. These SHA-256 commitments are **not BlueIds**:

```text
contracts.snapshot/completion-1
contracts.invocation/completion-1
contracts.turn-input/completion-1
contracts.turn-result/completion-1
contracts.round-result/completion-1
contracts.event/completion-1
contracts.embedded-observation/completion-1
contracts.work/completion-1
contracts.unit-result/completion-1
contracts.chunk/completion-1
```

The invocation descriptor binds the exact input snapshot commitment, original event identity or absence, supplied timestamp or absence, profile and gas policy. A snapshot uses the stable member/edge/serial records, with the selected release and record domain. Scheduling state is not injected into business documents.

### Private records

| Record | Closed required contents |
|---|---|
| `Cause` | `kind` PROCESS or INITIALIZE; PROCESS has exact `event` and `timestamp`; INITIALIZE has neither. |
| `OccurrenceTicket` | `parent`, `parentActivation`, `path`, `source`, `sourceActivation`, `generation`. |
| `TurnInput` | `member`, `activation`, `beforeView`, `profile`, `cause`, `phase`, `turnSerial`, ordered `dependencies`, ordered `incoming`, ordered `seeds`, `lifecycle` (`{kind:NONE}` or `{kind:INITIALIZE,document:exactPreInitializationRef}`), and exact `logicalContext`. |
| `EventOccurrence` | `sourceTurn`, zero-based `ordinal`, exact `event`, `identity`. |
| `TurnCompletion` | `turnInput`, `afterView`, ordered `output`, `memberMetadata`, ordered `edgeChanges`, `consumedSeeds`, `retiredTickets`, scalar `gas`, `identity`. |
| `RoundSeal` | exact preceding and resulting component vectors, round ordinal, ordered local completion identities, their finalized member projection, changed live bindings and identity. |
| `UnitCompletion` | sorted `members`, exact `beforeViews` and `afterViews`, ordered per-member `turnResults`, per-member `output`, scalar `gas`, `identity`. |
| `QueueItem` | `kind` LOCAL or EMBEDDED; exact `event`; LOCAL has source occurrence identity; EMBEDDED additionally has source completion and occurrence ticket. |
| `Frame` | owned working body/metadata; immutable dependency view; local FIFO; own output; suspended handler stack; pending initialization barriers; retired routes; consumed seeds. Mutable and never exported. |
| `ChunkToken` | attempt identity, selected unit, exact TurnInput/round descriptors, logical sequence position, expected input/output dependencies, meter/logical-proof prefix commitments; one-use token. |

`beforeView`/`afterView` mean exact local content **plus** selected managed bindings/required component proof, not only a projected business object. An `incoming` row is closed: `{kind:DAG, sourceCompletion, tickets}` for an acyclic/outside-unit source, or `{kind:CYCLIC, sourceCompletion, roundSeal, tickets}` for an intra-unit source. `tickets` is the ordered receiver-ticket list. The cyclic variant carries the exact finalized source projection and is not a new external event. Seeds keep the existing member, activation, channel, generation and selected operation identity/key facts. `logicalContext` binds the canonical metering proof/manifest inventory, not physical cache residency.

Compute `sourceTurn = digest(turn-input-domain, semantic TurnInput fields excluding logicalContext)`; accounting-prefix evidence must not change the identity of the same semantic local turn; `EventOccurrence.identity = digest(event-domain, {sourceTurn, ordinal, event})`. The source key is retained when rerooting an existing managed snapshot. Do not rebuild B as a fresh differently initialized root and call it the same reusable turn. A receiver observation identity binds the source occurrence identity and the full occurrence ticket. Turn-result identities bind the listed content excluding their own identity field; unit and round identities likewise bind all listed fields except their own identity field, using their respective versioned domains. Gas contributions inside a completion are scalars; verify them against the captured execution and budgets on acceptance. No accepted-charge rows are serialized. Snapshot record roots/revisions remain attempt-specific.

Before a closed record is admitted, reject unknown fields and invalid variants, verify content identities, validate monotonic serials and prove every referenced component/binding. `identity` fields never authenticate execution by themselves.

### A01. Public PROCESS / INITIALIZE

```text
PROCESS(input, event, time):
    validate SDK arguments and configured immutable runtime bindings
    establish exact event identity and original input graph
    S := new isolated Attempt(input, Cause(PROCESS, event, time))
    charge processInvocation; charge closureInvocation
    verify input graph and required contract headers
    freeze input member activations and external channel acceptance
    select and validate all fresh calls using input member identities
    if root was already terminated: return original-state TERMINATED
    INITIALIZATION_PHASE(S)
    PROCESS_PHASE(S)
    require no runnable local work, unsealed frame or pending init barrier
    finalize changed exact components and containing references
    validate all affected owned/containing contexts and protected records
    settle topology/revision bookkeeping once for this invocation
    project only selected-root output occurrences in canonical creation order
    return APPLIED with the complete graph, output and final gas total

INITIALIZE(input):
    open the same isolated machine with Cause(INITIALIZE)
    no external event, time, call, seed or external checkpoint is invented
    perform INITIALIZATION_PHASE and final validation/projection as above
```

Every exception follows A10. Initial operation recognition and input-version checking stay in the unchanged C08–C12 helpers. A child produced during this attempt cannot enter the frozen original seed set. A dynamically created channel cannot accept this same external event retroactively.

`INITIALIZATION_PHASE` runs before `PROCESS_PHASE`; each has its own dependency-unit work set. Initializer output is handled exactly once in the initialization phase and is not re-imported during the process phase. Capture the pre-initialization references for all newly discovered uninitialized members before initializing any member of that discovered group, including descendants. Initial cyclic-member captures use the coherent input component. These captured values are carried in lifecycle descriptors and never replaced by a post-child-initialization view.

The selected root's total output concatenates its own initialization-phase outputs and process-phase outputs in canonical order. No child's values become public merely by passing through a parent.

### A02. Build and drive the dependency units

1. Derive the exact finite managed-edge graph with the defined explicit/map-collection rules and verified bindings. Maintain a separate active-processing mask: terminated members accept no ordinary work; their declared content is still verified where required. Never enumerate external incoming observers to enlarge the selected rooted graph.
2. Compute SCCs. An initial unit is an SCC; order dependencies before containers. Keep the lexicographically smallest ready member-key tuple as the canonical next unit.
3. For a singleton with no self-edge, wait until all its required outgoing dependency units for the phase have sealed. Carry untouched dependencies without opening unused bodies. Then run A03 once for all its pending input-phase work.
4. For a cyclic unit run A07. Every unit outside it sees only its final UnitCompletion.
5. Feed a sealed source result to each eligible containing unit in the selected graph. A source may have many consumers, but its compatible selected calculation is not rerun for each edge. Bind per-edge receiver tickets separately.
6. A structural change calls A09. A changed pending dependency prevents sealing the affected unit until its required initialization/view work has completed. Unchanged exact historical references are not silently redirected.
7. Process units until the selected root and every required pending consequence have sealed. Retired, unreachable work is discarded by its recorded lifetime; discarded work is not reassigned.

A unit can be carried without a business turn if it has no incoming changed state/events, no initialization and no fresh seed. Exact containing-reference changes still make a result available upward, even without handlers or emissions. In a static DAG all changed direct dependencies are installed before the container's input-phase turn. Thus sibling completion timing cannot affect a parent's reads or queue order.

### A03. Complete one local document turn

```text
RUN_LOCAL(TurnInput I):
    verify the exact before-view, dependencies and input binding
    charge localTurnOpened
    F := private frame for I.member; no other frame is writable or readable
    INSTALL_INPUTS(F, I.incoming)                 # A04, all source states first
    if I.lifecycle.kind == INITIALIZE:
        use I.lifecycle.document captured at discovery, not the current frame
        mark this activation initialization-in-progress
        dispatch local lifecycle initialization once
        # incoming child events were prequeued; lifecycle emissions append
    DRAIN_LOCAL(F)                               # A05
    for seed in I.seeds in prescribed channel order:
        if same activation/channel generation survives and member can run:
            dispatch selected operation + ordinary workflows
            DRAIN_LOCAL(F)
            mark this seed consumed
    finish required initialization barriers and local continuations
    DRAIN_LOCAL(F)
    settle this member's eligible markers/checkpoints
    verify local state/protected records and required bindings
    require empty local queue and no unfinished handler/barrier
    charge localTurnSealed
    return immutable TurnCompletion
```

The lifecycle dispatch uses existing handler/channel ordering and effects. A frame's local queue is empty on entry except for the preloaded incoming batches. After a normal seed dispatch, locally emitted events drain as before. No parent is called during this routine.

If the member was legitimately terminated before its turn, skip ordinary/lifecycle reinitialization work, discard its ordinary incoming deliveries, and only synchronize required completed references/bookkeeping under the validation rules. If termination is requested during the turn, run termination lifecycle once, stop ordinary work and retain already emitted output. In all cases the completed result must be valid; termination is not a validity bypass.

Within each handler, use the defined dispatch/step semantics. A Compute sees a stable view of the member at that Compute's start; BEX evaluates with its existing result overlay. It returns separate effects. Apply its patches with immediate **local** continuations, then record its events. Subsequent steps see completed local continuations. No new BEX operator or cross-document operation call is introduced.

### A04. Incorporate completed source states and queue complete batches

For a DAG or outside-unit incoming set, perform the following steps. For an intra-cycle batch, first verify its RoundSeal and use that seal's finalized source member in the coherent previous-round view; A07 specifies the receiving view and prohibits installing an isolated old member over it. The same queue, route and event rules still apply.

1. Verify each source completion against the selected exact source before-view, cause, profile and phase. Verify every selected source dependency, body, component proof and completion capability. A completed result from another incompatible view cannot satisfy the ticket.
2. Reject a mixed/conflicting set: one continuing occurrence cannot be advanced along two incompatible source outcomes. A declared sequence of source turns must form its exact predecessor chain; preserve its ordinal order. Within a static DAG phase there is one final result per source. An outside consumer of a cyclic unit receives its final view and accumulated output, not intermediate round states.
3. Filter retired receiver tickets. Require the same parent activation, source binding and edge generation. A removed occurrence has no work; it is not an integrity failure to discard already captured but now retired work. Wrong supplied evidence for a **live** ticket is an error.
4. Replace only the surviving occurrence's selected reference/binding with the completion's exact after-view. Keep the occurrence generation. This is structural incorporation, not a business patch. Rebuild affected containing identity paths. When several dependencies arrive, install the complete coherent set before validation or callbacks.
5. Validate the complete receiving document with Language, including its enclosing constraints. Do not generalize automatically or send Document Updates. Failure aborts this selected attempt before receivers run.
6. For each ordered source batch, for each event ordinal, for each sorted eligible occurrence ticket, append an EMBEDDED QueueItem. Perform this full append before invoking any receiving handler. Charge completionBatchInstalled once per installed source batch/receiver and completionRouteChecked per considered ticket.
7. Bind each pending row to its exact source occurrence and receiver generation. Record queue membership, not successful delivery, now. A05 rechecks lifetime before dispatch.

An empty event list still performs steps 1–5 and updates state. A state-identical source that emits events still performs steps 6–7. Duplicate event **values** do not collapse occurrences. Already accepted packet replay in the same attempt cannot append its rows twice; use the explicit receiver observation keys, never just event BlueId.

Do not put a completion packet into `$event`. An EMBEDDED item constructs exactly the existing `Embedded Event Delivery {sourcePath, event}`. Incoming occurrences do not enter the receiving output list.

### A05. Per-document emission and FIFO

```text
EMIT(F, exactValue):
    capture and verify the immutable exact event
    allocate next source-local ordinal in F.output
    append EventOccurrence to F.output
    charge internalEventEnqueued
    append LOCAL occurrence to F.queue

DRAIN_LOCAL(F):
    while F.queue is not empty:
        item := pop_front(F.queue)
        if item.kind == LOCAL:
            charge internalEventDequeued
            if member can receive ordinary events:
                dispatch its matching Triggered Event Channels/extensions
        else:
            recheck the same source/receiver occurrence lifetime
            if retired or receiver terminated: continue
            construct existing Embedded Event Delivery
            dispatch matching Embedded Node Channels/extensions only
        finish each dispatch's immediate local update continuations
        # any event emitted above was appended to the tail by EMIT
```

Freeze candidate channels/handlers at their prescribed discovery point. Check route liveness before every resumed embedded handler and step; a handler can retire the occurrence. If A's E1 handler removes B, A's queued E2 from that occurrence is dropped. B's E2 local handler already ran before B sealed; A cannot undo that. Other surviving occurrences retain their own work.

LOCAL events never call parent observers. EMBEDDED events never call the receiver's Triggered Event Channels unless a receiver explicitly emits a new value. All output is captured at creation, remains immutable and is kept even after its local notification has been drained.

For input batches `[E1,E2]`, A's E1-generated P1 is behind E2. If two source batches are preloaded, A's emitted work also stays behind the rest of the initial incoming queue. The standard does not permit processing each input value as a separate standalone attempt.

### A06. Local patch and exact view isolation

```text
APPLY_LOCAL_PATCH(F, patch):
    validate effect shape; account the existing patch/boundary work through the shared meter (no patch-count ceiling)
    normalize pointer/list append; charge boundary/path/patch work
    reject strictly-inside-managed-child and protected-record writes
    capture exact before-side and protection identity
    apply patch to F.ownedBody only
    run retained generalization search, if permitted, on this local document
    validate exact local result; protection identity must be unchanged
    reconcile this member's declared edges and retire replaced generations
    run A08 for newly created uninitialized children
    silently install their completed views; queue their complete ready batches
    capture the final exact after-side of the completed local patch boundary
    if exact before/after equal: no business update
    dispatch generated type updates locally, then original local update
    complete these immediate local continuations before returning
```

Capture `after` after the new-child initialization barrier, so a handler reacting to the parent's own `/child` attachment patch does not observe an unfinished new child. A user-authored patch to an ordinary enclosing object remains locally observable. A descendant's own patches and automatic exact-reference rebuilding remain unobservable to the parent as Document Updates.

`Graph.finalize` must not synchronize source working bodies into other member frames at every patch. Replace that use with (a) local exact validation against pinned dependencies, and (b) safe-boundary sealed graph finalization. The finalizer can construct temporary Language values/proofs to validate a local view, but those objects are not externally visible member completions and cannot authorize peer callbacks.

### A07. Cyclic units

A unit has a pending inbox per member, a consumed seed/init set, a turn serial per member, a coherent last sealed component view, and buffered external output.

```text
RUN_CYCLIC_UNIT(U):
    repeat:
        charge componentRoundOpened before the round; no independent round-count ceiling
        V := immutable coherent view of U's last completed round
        inputs := snapshot pending per-member batches and remaining seed/init work
        clear only those pending items included in inputs
        results := []
        for member in U.members in key order:
            if member has eligible inputs:
                results += RUN_LOCAL(input using V for all peer reads)
        merge each result's OWNED member changes into V
        reconcile member edge declarations and retire invalid generations
        use Language to finalize ACTUAL resulting cyclic components
        validate the resulting coherent component; create immutable RoundSeal
        # RoundSeal maps local after-views to the exact finalized member vector
        retain output per source in round/member/turn/local-ordinal order
        route each new output batch to surviving captured intra-unit tickets
        place those batches, each bound to RoundSeal, in NEXT-round inboxes
        # never invoke this round's peer callbacks
        absorb topology joins and pending initialization via A08/A09
    until no pending batch, initialization or external seed remains
    expose one UnitCompletion to outside containers
```

A member without work does not rerun its external operation merely because a peer changed state. At the round boundary all member references are made coherent; pure identity/reference changes do not create another round. Internally generated events and lifecycle work do. All applicable member-local gas ceilings and the shared 10,000,000 maximum remain live across rounds; no independent structural turn/round limit applies.

Within a round, peer and self-edge reads use V, never a result produced earlier in the member-key loop. Local owned-field reads use the current frame as usual. At the next round, peers see the just sealed V'. This is deterministic even if turn calculations are physically parallel; logical acceptance/metering remains member-key ordered.

Cyclic incoming messages are notifications of completed prior turns. Their immutable payload remains exact. The receiving cyclic frame reads the current coherent previous-round component view, which includes all completed sources at that boundary; it does not install an older isolated peer body over a newer coherent component. Each pending batch is verified through its source completion and RoundSeal; its source turn must be included in the current component history. A local after-view before cyclic reference rebinding is not asserted equal to the finalized member BlueId. RoundSeal supplies that exact projection without changing or forging the immutable local output. The final outside batch always uses the final complete component view. This explicitly states the cyclic read rule instead of pretending a single member can independently finish a feedback loop.

A split keeps U's execution group until quiescence, but finalizes identities under the actual split graph. New joins are handled below. No special wave, epoch or host scheduling concept is part of this algorithm.

### A08. Initialization and dynamic creation barrier

For initial initialization, build dependency units and capture all discovered uninitialized member references before any initialization writes or descendant refreshes. Initialized members are carried, not reinitialized. A03 lifecycle dispatch happens once per new activation. Cyclic initialization uses A07's round-0 lifecycle work and subsequent local-event feedback.

For a child created by an in-progress parent patch:

1. Record its exact creation body, new occurrence generation and creation cause. Do not invent an external input or checkpoint. `created during this attempt` alone does not change Language admission rules.
2. Discover its uninitialized dependency closure. Distinguish new members from existing initialized members and ancestors already initializing. The latter are **read-only pins to their last sealed/pre-initialization exact views**, not recursive initialization requests.
3. Initialize the new-only closure dependency-first; use rounds for SCCs among the new members. Capture all such members' pre-initialization IDs once. A back-reference to the suspended creator reads its sealed pre-turn view, never its private patched body. Mark any resulting live join for A09 rather than recursively entering the creator.
4. Seal the newly initialized members and supply their completed states to the suspended creator. Queue all eligible direct-child initialization outputs as complete batches behind existing queue items. Do not drain the creator's queue inside its current handler; local Document Update continuations still run at A06's boundary.
5. Resume the creator's patch/handler. Its next normal step sees the child initialized. It cannot seal upward until this barrier and its own work are complete.
6. When the creator seals, activate the pending live bindings coherently and recompute units. A cyclic join uses the completed creator view and retained child result; internal messages already delivered during the barrier are not redelivered. Remaining feedback becomes subsequent group-round work.

If evidence is missing, fail/suspend the whole attempt under A10 rather than expose an incomplete child. The same deterministic gas ledger applies to this process. Any physical allocation/work interruption remains an incomplete attempt, not a child-initialization rejection. A child later removed by its creator can have consumed calculation gas without surviving in the resulting active graph.

### A09. Topology changes, unit promotion and route capture

Maintain monotonically increasing member-activation and edge-generation counters as in the defined. Whenever a declared edge changes, retire the previous occurrence and allocate the next generation in deterministic source/path order. Keep retired records for evidence without treating their inventory as active processing work. There is no universal active-graph capacity ceiling.

**Route capture:** for original phase work, capture the source's incoming edge tickets from the coherent phase-start graph. For newly initialized children, capture the newly active direct tickets at the creation barrier. A later edge never acquires source events already emitted/sealed before it existed. A continuing source's subsequent turn captures then-current tickets. Source output values themselves contain no route paths.

At a sealed turn/round boundary:

```text
compute actual active SCC partition
for any actual SCC touching more than one current execution unit:
    U := union of all touched units (including prior sticky unions)
    retain each member's last sealed local state and any in-progress creator pin
    collect undelivered intra-U tickets and unconsumed seeds/init work
    remove pending outward packets whose receivers are now inside U
    retain their unconsumed observations as U inbox work
    retain already consumed observation IDs; do not enqueue them again
    continue U using A07 after all current frames reach their local boundary
mark all affected containing pending units as depending on U
```

Unit merges are monotonic inside an attempt; at most the finite number of member unions can occur. A split changes actual edges/identities but not the current execution-unit union. At the next input start there is no sticky grouping from the previous attempt.

Previously sealed source turns remain valid completed turns. A merge does not replay their operation or undo past local observation. It changes which further work is internal before the unit may expose its **final** result outside. If a receiving member already ran in this attempt, new eligible incoming work creates a new reaction turn with no repeated external seed; its accumulated output retains the prior turn order.

A unit may not seal outward while it has a pending dependency that can still supply required work. A whole-root result waits for all required units even if a chunk finished earlier. This is why arbitrary database task completion is not the chunk-ready predicate.

### A10. Atomic failure and finalization

Keep the original input snapshot immutable. APPLIED alone authorizes publication of the full attempt result. Any invalid request, patch, received completion, identity, protected state, callback or final containing constraint rolls back every tentative frame/completion/marker/output in the attempt. Deterministic gas exhaustion has its existing exact rollback and rejected-charge behavior. A physical resource/cancellation exception abandons the tentative attempt without constructing a canonical semantic failure.

For GAS_LIMIT_EXCEEDED preserve the admitted gas total and the first rejected charge, not speculative suffix work. For NEEDS_RESOURCES preserve the original state and the defined missing-resource disposition; do not invent a completed gas receipt or a successful prefix. A physical cancellation is not a fabricated protocol gas error. Propagate a typed incomplete/host condition through every callback, Language bridge, BEX boundary, chunk driver and receiving adapter; do not let a broad exception wrapper turn it into invalid evidence or invalid input. No terminal result, input-disposition or checkpoint is issued from the unfinished attempt.

Finalization uses only sealed owned states. Substitute current verified member-local edges, run the real Language cyclic-set finalizer, retain owning-set proofs, rebuild outside references dependency-first, validate every affected context, and write invocation revision/topology generation once. No finalizer invokes business update/event handlers. Root projection records only root-origin occurrences; other completions remain internal result evidence.

A source turn calculated earlier can remain retained as non-authoritative immutable evidence after a larger attempt fails; its mere existence does not change the returned original state or commit any effect. A separate earlier successful standalone call has its own atomic boundary and is not rolled back by an unrelated later call.

### A11. Chunked execution and the equivalence argument

The optional chunk driver is:

```text
begin(document, event, time) -> opaque Attempt
next_chunk(Attempt) -> verified ChunkToken | no-more-work
execute_chunk(ChunkToken) -> sealed candidate completion
accept_chunk(Attempt, ChunkToken, completion) -> updated private Attempt
finish(Attempt) -> the same public Outcome as PROCESS
```

This is not a second public event format. `next_chunk` chooses exactly the ready unit/turn/round prescribed above; it supplies frozen local seeds and dependency views, not a caller-selected external delivery list. `accept_chunk` checks the one-use token, exact inputs, profile, result capability, occurrence lifetimes and logical work prefix. Duplicate acceptance cannot duplicate effects or charges. `finish` rejects unfinished attempts.

An acyclic subgraph may be calculated in a separate process and transported as exact completed data when all token bindings remain the same. Parent-independent semantic payloads are final state and own output. Binding metadata, initial exact view and metering evidence prevent stale/forged substitution. A root-level standalone Outcome is not accepted blindly as a local completion: its setup/root projection and snapshot-root commitments differ and must be normalized through the supported extraction/verification path.

**Induction for a static DAG:** leaves execute identical local turns; therefore their state/output pairs agree. Given identical completed dependencies, their container installs the same states, prequeues the same occurrences, executes the same BEX and handlers against the same views, and seals the same result. Induct to the root. Every logical charge is accepted in the same normal-form sequence, yielding identical successful and failing prefixes. There is no parent callback into an unfinished source frame, so an interleaving cannot invalidate the substitution.

**Cycles:** induct over A07 rounds instead of graph depth. Each round begins with the same component vector and inboxes, runs identical local turns and finalizes the same exact component. Stop or fail on the same boundary. The component, not an individual cyclic member, is the independently completed external chunk.

**Dynamic graphs:** chunk acceptance follows A08/A09. A join can invalidate a formerly independent cut. Preserve completed turns and promote the remaining work; never force a precomputed stale partition to finish as if topology had not changed. Equivalence covers identical execution of this state machine, not arbitrary regrouping that changes its semantic turns.

A native implementation can use a single heap, an explicit continuation object, serialization between chunks, or verified computation reuse. It must have no visibility into another member's unsealed frame and must preserve the logical work evidence and final gas total. Parallel wall-clock completion order is ignored.

### A12. Helper contracts and integration

| Helper operation | Required meaning |
|---|---|
| `reference/channels.py` | Retain recognition, exact-input precondition, actual checkpoint freshness, union membership and lifetime signatures. Build seeds once from input state; route no completed child as external input. |
| `reference/registry.py`, `catalogue.py` | Retain 31 type shapes, roles, closed headers, step discovery and actual-value filters. Bind regenerated definitions to completion-1. |
| `reference/language.py` | Retain exact reads/writes, identity, admission, reference and cyclic proofs. Supply pinned frames/dependencies; never latest-state aliases. |
| `reference/policy.py`, `generalization.py` | Retain policy matching/floor/nearest-valid search. Apply to owned local patches only; receiving validation is not automatic generalization. |
| `reference/runtime.py` | Retain deterministic role registration and sealed ledger contract. Restrict contexts to local frames/completed dependencies and route outputs through A05. |
| `reference/work.py` | Retain low-level charge formulas and stable sort. Split logical proof inventories from physical caches and attach their exact prefix to chunk tokens. |
| `reference/model.py` | Retain tokens, safe integers, pointers, charge/rejection and public Outcome shape. Add private completions/frames and version commitment domains. |
| `reference/processor.py` | Replace global queue, cross-boundary updates, lifecycle/seed loop and final-only checkpoints with A01–A11. Retain actual handler/step execution inside the local kernel. |
| `reference/graph.py` | Replace eager cross-frame propagation during patches with local reconciliation and sealed finalization. Preserve true cyclic identities, explicit bindings and retirement; fix active-count accounting. |
| `reference/storage.py` | Rebind snapshot/receipt/invocation formats and compare the new canonical observations. Never claim the old digest/release certifies new records. |

The helper reference defines primitive operations; it does not license old scheduling side effects. All helper accesses go through the frame/sealed boundary. The primary runtime migration is a structural refactor, not deleting one call to `graph.routes` while leaving a shared mutable graph visible through readers.

### A13. Gas-only protocol bound and interruption discipline

This is an integration rule for A00–A12, not a second document-processing algorithm.

```text
for the next prescribed logical work item:
    derive its counter and units from exact inputs and the specified logical inventory
    debit the unchanged shared/member meter before the corresponding charged action
    if the meter rejects:
        retain the admitted prefix and exact rejected charge
        roll back the whole selected attempt using existing GAS_LIMIT_EXCEEDED rules
    perform the work without a second universal size/depth/cardinality guard

on physical resource interruption before completion:
    do not create a canonical Outcome or charge a synthetic gas suffix
    unwind/discard mutable frames and any unpublished candidate
    retain only host diagnostics and the original pending obligation
    if a publication was attempted and may have committed, reconcile first
```

Logical-work inventory is not physical cache inventory. Keep the old meter for work whose charge is already specified; optional cached results must produce the same successful/rejected prefix as uncached execution. Any uncovered input-dependent primitive needs an explicitly specified metering correction before final conformance is claimed, not an arbitrary size ceiling or a hardware-dependent tariff. Work done by a standalone Language authoring call or provider prefix acquisition is not silently put into an unrelated Contracts invocation's 10,000,000 ledger.

<a id="metering"></a>
## Appendix B. Logical metering and schedule

### Common ledger

There is one shared live ledger for the entire `process` or `initialize` attempt, maximum/default 10000000, plus optional member-local ceilings. Charge before work. Retain configured member-local totals, the admitted total, first rejected charge, tie-break, domain-integer checks and extension namespace rules in `reference/model.py` and `reference/runtime.py`.

Failed state rolls back, not admitted work. NEEDS_RESOURCES has an incompatible's no-completed-ledger disposition. Physical queue storage, network transfer, cache hits and task IDs are not tariffs. Logical input facts and validation proofs are distinct from physical caches.

### Counter placement

| Counters | Exact placement in the new machine |
|---|---|
| `processInvocation`, `closureInvocation` | Once each at A01 entry, ownerless; not once per chunk or component. |
| `scopeOpened`, `managedDocumentOpened` | Once per active member first opened by this attempt; retain the defined opened-set rule. |
| `contractHeaderRecognized`, `objectMemberRead`, `typeEdgeFollowed` | At complete required header discovery; dedupe by the same exact member/header key, not physical cache. |
| `deliverySnapshotEntry`, channel candidate/acceptance/checkpoint counters | At frozen external selection and exact freshness/precondition work in retained channels helpers. |
| `localTurnOpened` = 2 | Before starting each actual local turn, owner = its member. No charge for carrying a wholly untouched node. |
| `localTurnSealed` = 2 | After its final local validation and marker work, immediately before sealing that turn, owner = its member. No successful seal charge for failed turns. |
| `completionBatchInstalled` = 2 | Once per source batch installed in a receiving turn, including an empty-event state-changing batch; owner = receiver. Several paths to that source batch do not multiply this counter. |
| `completionRouteChecked` = 1 | Per occurrence ticket checked at installation, before each pending embedded occurrence, and before each resumed embedded handler/step; owner = receiver. Retired tickets still cost their check. |
| `componentRoundOpened` = 2 | At the beginning of every nonempty-work cyclic round, ownerless. No final empty polling round. |
| `patchBoundaryChecked`, `pointerSegmentTraversed`, patch add/remove | Retain the defined normalized pointer and per-patch charging in A06. Automatic completed-reference installation is not charged as a business patch. |
| `documentUpdateDelivered` | Per actual local Document Update channel dispatch only. There are no deep parent-update delivery charges. |
| `internalEventEnqueued`, `internalEventDequeued` | At own emission and LOCAL FIFO removal, respectively. Each locally emitted occurrence incurs these once; incoming EMBEDDED rows use completion/delivery counters instead. |
| `triggeredEventDelivered`, `embeddedEventDelivered`, `lifecycleDelivered` | Per actual dispatched matching channel, using the defined `work_record` counter placement. |
| `closureWorkOccurrenceEnqueued`, `closureWorkOccurrenceDequeued` | Once each per actual channel work record. Retain channel/handler candidate and call counters at discovery/dispatch. |
| `rootEventRecorded` | Once per selected-root own occurrence at final successful root projection. Never for a child merely because its output packet is stored. |
| `processorMarkerWritten`, `checkpointWritten` | At actual changed marker/eligible checkpoint write at the corresponding member seal. No artificial writes per receiving child event. |
| `terminationRequested`, `scopeInitialization` | At their once-per-activation lifecycle entry, retaining defined repeated-request suppression. |
| `processEmbeddedEdgeExamined`, `closureExpanded` | At changed edge reconciliation and newly active member introduction, respectively; keep defined source ownership. |
| `managedOccurrenceBindingVerified` | At first exact binding verification per occurrence within the attempt. |
| `componentMemberPartitioned`, `componentEdgePartitioned`, `componentPartitionChanged` | When A02/A09 establishes a new actual partition, use defined per-member/per-edge quantities and the explicit changed-partition test. Logical graph edges, not an all-history inventory. |
| `containingReferenceUpdated` | Per changed live exact attachment reference at sealed incorporation/finalization, owner = containing member. Deduplicate the identical update within that boundary. No charge for an unchanged exact reference. |
| `tentativeComponentFinalization`, `cyclicMemberFinalized` | For each required changed Language cyclic-set finalization at a sealed round/unit/final boundary. Acyclic finalization does not receive the cyclic counters. A final already exact unchanged set is not refinalized/charged again. |
| Low-level identity, list-fold, comparison, schema, validation, sort counters | Retain exact quantities in `LogicalWork`/generalization helpers. Execute those logical calls against the specified local or sealed view, never against a prematurely refreshed ancestor. |

For new-child initialization, source initialization work belongs to the child; receiver batch/incorporation/update work belongs to the creator. A cyclic round has ownerless round/whole-component overhead and member-owned local work. Distinct parent receiving work is not charged to the source.

### Normal form and cached completions

The reference logical order is A01 setup, initialization units, input units, member/round order, and final projection. Each completed unit has a scalar gas contribution and an input logical-proof commitment. On chunk acceptance, verify the same execution under the captured current budgets; physical completion order is irrelevant.

A cached segment with a different logical proof inventory, dependency context, profile, seed selection or budget-prefix semantics cannot be copied unchanged. Re-execute the local kernel or derive/verify its exact normal-form work through the implementation's supported equivalent path. It is never sufficient to set gas to the cache lookup cost. A previously admitted segment cannot merge twice for the same logical chunk; distinct receiving occurrences still have their own application costs.

Retain the defined rejected-charge behavior: stop before the first work item that exceeds shared or owner-local remaining gas, return its exact rejected charge, and expose no state/output. Speculative work beyond that point is physical diagnostic work only. Do not execute an unbounded speculative callback merely to discover its cost. A live callback charges the parent before work. A sealed callback enforces its captured allowance before every primitive, then merges its admitted scalar once and reproduces any first rejected charge; the 10,000,000 shared ceiling is not reset for it. Physical interruption abandons speculation and is not a semantic rejection.

Consequently:

```text
gas(rooted attempt) = gas(chunked execution of that attempt)
```

but not necessarily:

```text
gas(standalone B call) + gas(standalone A call)
```

The latter contains repeated top-level setup/root projection and can be a different declared atomic context. Use the shared attempt driver for exact total/rejected-prefix comparisons.

### Required gas qualification

Run direct/chunk differential cases at ample gas, exact-success allowance, one unit below it, and restrictive member-local ceilings. Compare admitted total, first rejection, configured member-local budget enforcement, state and public output. Accepted-charge row sequences are not observations. Include zero-event state propagation, duplicate paths, cold storage, callbacks, cyclic rounds, initialization, late failure and a retired receipt. Generated runtime totals must come from that implemented profile; none are supplied as invented golden numbers here.

### No unrelated protocol ceilings

The structural `limits` entries are removed from the current manifest. Preserve `sharedMaximum: 10000000`, all existing numerical weights, the default maximum, legitimate smaller bound budgets and member ceilings. Keep caches and I/O pages bounded independently: their size changes neither legal content nor completed logical gas.

A valid computation may exceed an old document, step, depth or numeric-text limit while remaining within gas. It must not hit that obsolete semantic guard. A computation whose prescribed logical work exceeds 10,000,000 still fails at the real first unaffordable charge. Neither a bigger machine nor more chunks changes that boundary.

A host unable to calculate or retain a valid under-budget outcome has not established a gas failure. Report incompleteness/operational fault, preserve pending input and stable state, and retry only with valid captured semantics. Do not publish a completed gas result assembled from an incomplete computation or estimate missing work using CPU time.

### Metering conformance

Meter every operation before performing its charged work. Existing graph/header, turn/round, effect, path, schema/validation, text, Integer-limb and identity counters already cover substantial work. Check their actual placement: post-hoc measurements do not necessarily prevent the expensive work before its rejection. In particular review BEX Integer conversion/arithmetic, collection copying/construction, `estimated_size`, comparison scans, validation, exact hashing and graph preflight. Conformance evidence MUST identify counter coverage and the position of every required charge. Do not invent a new public profile/limit document to hide this obligation.

### Resource-proportional charging

The standard/default maximum remains 10000000. Structural `limits` is empty.
BEX adds the unit-weight counters `integerWork`, `textWork`, `valueMember`, with
quantities and debit ordering defined in its resource-revision section. The same
Contracts meter and current owner receive those debits; no nested budget resets.

`textBlockExamined` now debits one block for each operand before comparing that
at-most-64-code-point block, stopping at the first different block. The prior
implementation scanned the matching prefix before charging; the new rejection
prefix is intentional. Identity lookup is protected by the prerequisite debits defined below. The original child work, text construction and established-identity accounting retains its logical reuse rules. `objectMemberRebuilt` precedes helper construction; `directIdentityHashBlock` precedes the final serialization/hash. Canonical helper size is computed
from bounded fragments after their text/member accounting, before hashing.
Previously established exact identities keep the same invocation-local reuse rule.

Gas quantity and amount arithmetic uses unbounded nonnegative Integers. This
changes internal receipt number encoding only beyond the former safe-integer
quantity range; it does not widen Timeline timestamps or any authored domain.
Operational inability has no canonical completed receipt or terminal disposition.

### Canonical identity prerequisites

The finite exact-value walk uses the stopping
at Ref boundaries made storage projection change the tariff. Use the direct
logical Merkle manifest and the invocation's bound identity evidence instead.
The Language identity algorithm is unchanged.

At an `establish` entry, obtain the direct exact manifest (a Ref is opened through
the verified Language interface; an owning-set cyclic Ref or Local is already an
exact token). Debit `identityInputMember` by its field count before enumerating
fields. In Language field order, debit `identityInputTextBlock` by
ceil(codePointCount/64) for each key, then the same quantity for a direct Text
literal or mergePolicy Text. For an items tuple debit `identityInputMember` by
its item count before examining items. Both counters have weight 1 and the
current Contracts member owns the charge. Child identities are tokens in this
manifest, regardless of whether their verified bodies are inline. This root
prerequisite remains payable even when the subsequent delta is empty.

Identity construction follows the exact-ID delta against the supplied previous
subject. An unchanged child, a previously established identity in this invocation,
a core identity, a carried admitted root/original event, or an exactly installed
standard type/specification identity needs no descendant reconstruction. The
installed-definition inventory is bound in the logical-prefix commitment and
MUST NOT be used as completed-value validation evidence. Arbitrary resolver or
physical-cache contents are not reusable logical evidence. Ordinary and cyclic
(token plus component scope) establishment keys remain separate.

For any other new/changed descendant, use its direct verified manifest even when
it is a Ref, pay the same direct prerequisite before processing that manifest,
and perform the existing recursive identity-construction accounting. Thus a new
reference does not erase required construction work. Previously proved exact identities are reusable within the invocation; an unknown
candidate must first establish its identity by the prepaid procedure below. The
reuse inventory is independent of cache warmth. Preserve the existing pure-list prefix/fold rules, Text construction,
node establishment, object-member rebuild and direct hash-block quantities.
`objectMemberRebuilt` precedes helper construction; count canonical UTF-8 helper
size without allocating its serialization, then debit `directIdentityHashBlock`
before that serialization/hash. Contextual validation keeps its separately bound
subject, goal, requirements and coverage obligations.

Exact-input verification/identity evidence comes from Language admission and
verified exact opening; it is not inferred from presence in a physical cache.
An unavailable or invalid required manifest remains a resource/evidence failure.
Do not open an unchanged referenced child or an unselected body simply to imitate
an inline traversal. Physical recomputation of already established Language facts
is not another semantic construction debit. New candidate direct-manifest work
is paid before the corresponding inspection; no whole-tree prerequisite walk or
post-hoc total adjustment is permitted.

For a direct manifest with one `value` field containing 65 ASCII characters,
the entry prerequisite is 1 member and 3 text blocks (key plus two value blocks).
The first unaffordable charge is rejected before its action, under the unchanged
shared/member cap precedence. These quantities are deliberate tariff corrections,
not new document-size, recursion-depth or elapsed-time limits.


### Guarded identity construction and runtime normalization

A sealed dependency installation or graph-finalization pass reads each source
document's existing body and collects its disjoint containing-reference changes.
Debit `containingReferenceUpdated` once per changed occurrence in the prescribed
edge order. Apply those replacements together and establish the resulting
candidate once, before retaining, hashing or exposing it. No partial dependency
inventory is observable and its intermediate identities are not constructed.
This rule does not batch authored patches, event reactions or checkpoint writes.

This section corrects the implementation order of the preceding rules. It is
normative for all runtime-produced values, patches, processor markers, emitted
records, generated type changes and changed containing references. Compilation,
external exact admission and verified acquisition remain outside execution;
normalizing a new execution result is **not** external admission.

`establish` pays the direct root prerequisites described above. For each direct
Integer literal it additionally pays `integerLimbOperation=limbs^2`, with
`limbs=max(1,ceil(bitLength(abs(value))/32))`, before decimal helper sizing.
Reuse an identity without visiting its descendants only when it is bound by
verified admission/opening, a successfully established construction, or a
protected completed-result transfer. Physical cache membership and an arbitrary
authored ID are insufficient. An admitted parent's children inherit identity
witnesses on opening its direct manifest; these are not value-validation proofs.
Copying a protected completed result preserves that witness through its sealed
exact identity. Weak native handles are just indexes to that evidence.

For an **unknown** candidate, never call Language identity, use it as an
identity-cache key, or recursively search for cyclic locals before the guards.
Visit its fields in Language canonical field order, paying each new descendant's
direct prerequisite before its work. Propagate a cyclic-local flag from this
paid traversal; do not perform a separate free scan. Literal Text construction
retains its existing changed-value block debit. Recursively establish child IDs
before constructing a parent helper. Build that helper from literals and child
**tokens**, never by recursively hashing the original candidate. Admit
`nodeIdentityEstablished`, then for a non-pure-list node `objectMemberRebuilt`
by the direct field count, and `directIdentityHashBlock=ceil((canonicalUTF8Size+9)/64)`
before serialization and hashing. Helper size scanning is covered by the prepaid
literal/key blocks; the scanner does not allocate the whole serialized Text.
Do not publish the establishment inventory entry if any guard or host operation
fails. A repeated unknown occurrence still executes this procedure; it cannot
reuse a proof solely because the host reused a Python object.

A pure list starts with the fixed empty-list identity. Establish each item token
before comparing it with the corresponding **verified previous** item token.
An unchanged verified prefix may reuse its fold; after the first different or
appended item, admit one `listFoldStepRecomputed` before each append hash. The
logical node-establishment charge follows the items. A non-pure-list `items`
field uses a pure-list child helper. `mergePolicy` uses its Text-node helper.
These are the existing Language helper/fold algorithms, not a new identity.
Local edges use the supplied token function. Ordinary and cyclic entries are
separate; a cyclic entry binds component members and their sealed before IDs.
All member `cyclicMemberFinalized` charges are admitted in component order before
the actual Language component finalization begins.

Runtime normalization is bottom-up and deterministic. Each value occurrence pays
`identityInputMember=1` before inspection. Native or host object normalization pays
`identityInputMember=n` before enumerating its direct keys, then
`identityInputMember=n*r` and
`identityInputTextBlock=(r+1)*sum(ceil(keyCodePoints/64))` before Language UTF-16
key ordering (`r=ceil(log2(n))`, zero for empty objects). Read values in that
order. Literal/Text inputs pay `identityInputTextBlock=ceil(codePoints/64)` before
Unicode checking, encoding or conversion; Integers pay the limb-square debit
before decimal conversion. Lists and explicit `items` tuples pay
`identityInputMember=itemCount` before child traversal, then normalize each
occurrence in index order. Omitted Undefined and null fields retain their
existing absence rules. Runtime type aliases remain rejected.

Already exact operands retain their reference boundaries. For newly normalized
nodes, the Language remember callback first invokes prepaid establishment;
only then may it retain/hash the node or convert it into a type-position token.
Value certification keeps the separately metered contextual validation path.
No full free recursive prewalk, serialization or materialization is permitted.
Normalization and later changed-ancestor establishment are distinct operations,
so their explicit prerequisites remain payable at each prescribed call site.
All charges belong to the current Contracts member and use the same live ledger,
first rejection and rollback rules. An interruption is HostIncomplete, never a
completed identity or validation certificate. A rejection cannot perform the
operation it failed to pay for, even when that operation would have been followed
by rollback.


### Canonical exact-value transfers

A BEX ExactObject/ExactList is a captured Language recipe with its resolver
and, during execution, this invocation's logical ledger. Access has already
opened its contributing manifests under the ordinary read charges. Admission,
verified opening or successfully prepaid construction supplies identity evidence,
not a physical cache hit. For one exact contribution, use its established ID.
The accounting form is the one-field object `{blueId: ID}`; apply the BEX
ordered finite-sizing algorithm to that form. A plain 44-character ID costs
60 in an append sizing call: base 5, size fragments 1+6+44, valueMember 1+0,
and textWork 1+1+1. A cyclic member token uses its actual full identity length.
Do not traverse or serialize the materialized body to determine that size.

For multiple contributing parts, first refine them in Language's existing
ordered exact-recipe algorithm. Its normalization remember callback invokes
prepaid establishment before retaining or hashing every synthesized node.
Only complete node bodies may populate the body's identity index; references
retain their verified provider target. Remember the successfully composed result
in an invocation-local inventory keyed by the ordered exact part identities
and contextual requirement identities (the Language recipe key). This inventory
carries the established identity alongside its immutable body, including through
continuation copies. Bind the recipe key and established identity into the
protected logical-prefix commitment. Rebind that construction witness after
transport; a changed native handle must not trigger new construction charges.
This is logical evidence, not resolver cache state.
Repeating that recipe reuses its established result; failed/interrupted
composition adds no entry. Its identity does not incorporate effective fields
that the exact recipe never contributed.

The effect base is admitted before requesting this accounting form. Required
composition/identity work occurs next, on the same owner and shared/member-local
ledger, before token sizing. All ordinary fragment, key-order, text and rejection
rules then apply. Native new containers continue to pay normalization and
construction; nested established children use the same transfer token. Newly
constructed native BEX data cannot claim that token before establishment.
Demanded reads, transformations, effects, certification, checkpoints and
publication retain their independent tariffs and order.

This rule applies uniformly to singular/plural append operators, step/binding
values, result overlays and effect snapshots. The emitted/copied exact value
remains the captured value, with necessary provider content and cyclic proofs
retained for cold restoration. Destination-context constraints must still be
validated. Arbitrary authored blueId syntax and generic HostValue implementations
do not confer the Contracts evidence capability.

### Selected descendant evidence

Opening a witnessed exact manifest propagates evidence to its immediate complete
children. Effective Language head/child selection can return equivalent instances
from a captured resolution plan. When every parent contribution has established
identity evidence and Language resolution succeeds, derive that same evidence for
the selected child's exact contributions. No new logical construction charge is
introduced by a changed handle or reference cut. No unrelated child traversal is
required. Metadata literals and a bare items slot cannot receive this capability.

Known exact identity and the invocation's established-construction inventory are
distinct: identity provenance allows a canonical transfer token but does not erase
normalization prerequisites, first-use logical establishment or target validation.
A multi-contribution exact result is still synthesized using the exact-transfer accounting prepaid
path, rather than assigning an existing child's ID to its effective projection.
After successful ordinary postorder establishment, retain its exact identity
witness. An interrupted/rejected hash cannot issue that witness; a token-context
cyclic identity remains scoped to its cyclic construction proof.

Native continuation copies rederive selected contribution evidence from the bound
parent/recipe; successfully composed results additionally retain the existing
recipe-key/established-ID inventory. Portable continuations verify execution by
replay. Neither a resolver cache nor native handle survival changes the ledger.
The canonical 44-character transfer sizing vector remains 60 gas; this specification
removes accidental duplicate establishment, not actual reads or new construction.

### Exact counter schedule

```json
{
  "profile": "contracts-deterministic-gas-6",
  "status": "Ten-million-gas edition: shared default and maximum 10000000; numerical tariffs, charge ordering and rollback are unchanged.",
  "sharedMaximum": 10000000,
  "weights": {
    "processInvocation": 20,
    "deliverySnapshotEntry": 1,
    "scopeOpened": 5,
    "contractHeaderRecognized": 1,
    "channelCandidateTested": 1,
    "channelAccepted": 1,
    "handlerCandidateTested": 1,
    "handlerCall": 5,
    "scopeInitialization": 2,
    "embeddedPathEntryRead": 1,
    "embeddedPathSegmentValidated": 1,
    "pointerSegmentTraversed": 1,
    "patchBoundaryChecked": 1,
    "patchAddOrReplace": 5,
    "patchRemove": 5,
    "documentUpdateDelivered": 2,
    "internalEventEnqueued": 2,
    "internalEventDequeued": 2,
    "triggeredEventDelivered": 2,
    "embeddedEventDelivered": 2,
    "rootEventRecorded": 2,
    "lifecycleDelivered": 2,
    "checkpointCompared": 1,
    "checkpointWritten": 2,
    "processorMarkerWritten": 2,
    "terminationRequested": 2,
    "closureInvocation": 100,
    "managedDocumentOpened": 10,
    "managedOccurrenceBindingVerified": 5,
    "processEmbeddedEdgeExamined": 2,
    "componentMemberPartitioned": 2,
    "componentEdgePartitioned": 1,
    "closureWorkOccurrenceEnqueued": 5,
    "closureWorkOccurrenceDequeued": 5,
    "closureExpanded": 20,
    "componentPartitionChanged": 20,
    "tentativeComponentFinalization": 20,
    "cyclicMemberFinalized": 10,
    "containingReferenceUpdated": 10,
    "nodeManifestOpened": 1,
    "objectMemberRead": 1,
    "listItemRead": 1,
    "textBlockExamined": 1,
    "textBlockConstructed": 1,
    "scalarComparison": 1,
    "integerLimbOperation": 1,
    "sortComparison": 1,
    "typeEdgeFollowed": 1,
    "schemaPredicateEvaluated": 1,
    "validationMemberExamined": 1,
    "validationProofReused": 1,
    "subtypeCandidateTested": 5,
    "nodeIdentityEstablished": 1,
    "objectMemberRebuilt": 1,
    "listFoldStepRecomputed": 1,
    "directIdentityHashBlock": 1,
    "localTurnOpened": 2,
    "localTurnSealed": 2,
    "completionBatchInstalled": 2,
    "completionRouteChecked": 1,
    "componentRoundOpened": 2,
    "identityInputMember": 1,
    "identityInputTextBlock": 1
  },
  "limits": {}
}
```

<a id="algorithms"></a>
