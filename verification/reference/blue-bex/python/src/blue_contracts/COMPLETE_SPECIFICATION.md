# Blue Contracts — document-local completion

> **Core authoring and Compute revision:** `2026-09-24-core-compute-1`. Bare mandatory core names, Language-backed node identity and shared Compute definitions. The Contracts maximum remains 100,000. See `docs/core-compute-20260924.md` for qualification.

**Revision:** `2026-09-24-core-compute-1` (resource edition)
**Status:** implemented candidate. Earlier qualification remains baseline evidence; consult the source-bound resource revision report for current results and limits.
**Baseline:** the immutable design input and predecessor source hashes are retained in `inputs/contracts-completion-1-design/BASELINE.json`.

This is a complete replacement of the Contracts prose specification. `ALGORITHMS.md` defines the new execution machine; `GAS_PROFILE.md` defines its metering sites. Compute gains the optional definition operand, and Compute Definition is a new Marker. Other public type shapes are retained. Their specification bindings and catalogue identities are regenerated from the admitted definitions in `TYPE_CATALOGUE.json`. The completion behavior is retained. Runtime resource handling and the executable annex must be updated together before this revision can be called implemented.

The predecessor Python listings remain unchanged under `inputs/contracts-completion-1-design/baseline/`. The current executable listings are embedded in `ALGORITHMS.md` and the complete publication. No predecessor test result certifies this revision.

## Reading the central change

A managed document finishes its own processing before its containing documents observe the result. An enclosing document receives **the completed child state and its complete ordered emitted-event batch**, never the child's unfinished patches or partially drained event queue.

The reference algorithm itself is expressed using this boundary. Processing an acyclic rooted graph in one call or calculating its ready chunks bottom-up therefore uses the same local algorithm. Chunking changes physical execution, not the logical order, visible states, gas budget or atomic result. Cyclic dependencies use complete local turns within a common component, not impossible recursive child-before-parent completion.

## 1. Scope and central rule

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

## 2. Public API, outcomes and document representation

### 2.1 Three inputs

The Python-compatible public API remains `Processor.process(document, event, eventTimestamp)`. Its bound method has exactly these three parameters. Processor construction configures the exact runtime registry, resolver, gas ceiling and optional member-local ceilings; those are fixed execution configuration rather than extra per-event routing arguments.

`document` can be a verified `Snapshot`, the SDK representation of the selected exact rooted document, or a fresh Source object. The latter is admitted and initialized within the attempt. It is not permissible to author protected processor markers in a fresh Source object. Use verified snapshot restoration for an already managed document.

The required SDK-compatible returned `Outcome.document` is the resulting `Snapshot`. Its selected root BlueId is `result.document.documents[result.document.root].blue_id`. `processor.read(result.document, path)` reads business content. `Outcome.emitted_events` contains exact references to the selected root's publicly emitted values. `processor.emitted(result)` opens those values for display. Tuple unpacking yields `(document, emitted_events, gas)` in the order in C01; the `Outcome` additionally carries diagnostics and replay evidence.

These SDK records do not add inputs to the Contracts transition. Optional `begin / next_chunk / execute_chunk / accept_chunk / finish` methods implement the internal protocol in ALGORITHMS.md; they do not publish partial state or add another external ingress. A storage host may use a different representation if it preserves the same exact content, managed-occurrence evidence and semantics.

### 2.2 Time and identities

**C04.** `eventTimestamp` MUST be an integer from 0 through 2^53−1, in microseconds. Booleans, floating-point values, strings, negative numbers and out-of-range integers are rejected. Contracts never substitutes a wall clock or an event field for this argument. This range preserves the baseline's portable timestamp representation; BEX Integer arithmetic is not narrowed by it.

The original event's identity is established with the unchanged validated Language operations. Selection of an inner call does not alter this identity. Equal timestamps do not imply equal events. No timestamp-only external ordering relation is inferred.

### 2.3 Result states

| Status | Document and public events | Meaning |
|---|---|---|
| `APPLIED` | Complete resulting state and selected-root emissions | The attempt can commit, including graceful termination. |
| `FAILED` | Original input snapshot; no public events | Invalid call, invalid effect, validation failure, explicit BEX failure, unsupported demanded executable or another defined Contracts error. |
| `GAS_LIMIT_EXCEEDED` | Original input snapshot; no public events | The next logical charge exceeds the shared or owner-local remaining allowance. The admitted prefix and rejected charge are reported. |
| `NEEDS_RESOURCES` | Original input snapshot; no public events | Required exact content or managed-view evidence is unavailable. This suspended attempt reports no completed semantic gas ledger; rerun from the original inputs after evidence is supplied. |
| `TERMINATED` | Original input snapshot; no public events | The selected root was already legitimately terminated. |

Invalid SDK arguments, invalid fresh Source admission and invalid configuration may raise `ContractError` before a runnable attempt exists. They are never a successful partial processing result. Gas and traces returned with a failed runnable attempt are diagnostic, not committed application effects.

An explicit `initialize(document)` lifecycle action is also provided. It has no invented external event or timestamp. It returns an `Outcome`. `create(document)` is a convenience that requires successful initialization and returns its document. `admit(members, root, bindings)` is a graph authoring facility, not an alternative event ingress. Its `Link` objects and symbolic member labels are not legal runtime patch values.

## 3. Exact graph and occurrence records

**C05.** A snapshot contains a root member key, exact document records, exact embedding edges, revision and topology-generation numbers, the Contracts specification identity and installed runtime bindings. Member keys and these commitments are platform records, not replacement BlueIds.

A member record contains its stable key, exact body and BlueId, current external-channel lifetimes, monotonically increasing channel and edge serials, and an optional immutable creation-cause token. A cause token is the original event identity, not an external ordering proof. The initial member set is finite.

An embedding edge is `(source member, relative path, target member, generation)`. That tuple identifies an occurrence. The same child may have several explicit incoming occurrences. A member's state changes can change its BlueId without changing its member key or continuing occurrences. Conversely, removing and recreating an occurrence at the same path must not revive an earlier occurrence's work.

The reference snapshot wire form is defined by `Snapshot.wire`, `Document.metadata`, `ChannelLife.wire` and `Edge.wire`. These field shapes and validation obligations are retained, with the new commitment domains in A00. This design package does not supply published new replay identities. The platform commitment uses a tagged canonical JSON representation and SHA-256; **it is not the BlueId algorithm**. Language remains the sole authority for document and cyclic-member BlueIds.

Restoring a snapshot verifies its commitment, release, runtime bindings, every exact body, each edge's selected content and target identity, channel lifetime signatures and protected markers. Possession of an unverified body containing `initialized` or `checkpoint` is insufficient to restore a managed history. Unknown or ambiguous managed-view bindings fail or require evidence; they are not silently bound to the latest document.

### 3.1 Private working state versus sealed views

For each active member, keep its last exact **sealed view** separate from the writable **local frame** used for one turn. A frame may read its own evolving state (stable during one Compute) and the exact dependency views selected for the turn. It cannot read another active frame, an ambient latest pointer, a container's unsealed state, or a resolver alias that changes behind an exact BlueId.

In a DAG, children finish before their container's turn. In a cycle, peer reads use the preceding completed component-round view. Ordinary self-reference through a separately managed self-edge also means that completed view, not an alias to the writable frame.

Exact managed bindings are updated from completed results by the processor. This changes containing content identities, but is **not** a business patch, does not recreate child Document Updates and does not invoke arbitrary callbacks.

### 3.2 Completion records

`TurnCompletion`, `RoundSeal` and `UnitCompletion` are closed processor records defined in the annex, not new top-level contract categories or user-authored business documents. A completion binds exact before/after views, the original cause, relevant frozen local inputs, the profile, ordered event occurrences and its logical work segment. Its source events contain no parent paths. Each receiver supplies and checks its own captured occurrence tickets.

A value shaped like a completion is not evidence it was executed. Accept only a result produced through the current attempt's verified chunk protocol, or an implementation's explicitly verified equivalent result with all the same bindings. Merely verifying the after-document's BlueId does not establish the calculation. This revision defines no public third-party proof-admission protocol.

## 4. Standard categories and complete type catalogue

**C06.** Only **Marker**, **Channel** and **Handler** are permitted top-level contract categories. `Contract` is an abstract common ancestor. `Operation` specializes Handler. A Sequential Workflow Operation is therefore a Handler. Process Embedded is a Marker. Standard steps inherit the abstract Contract definition solely to share declarations; their executable role is nested step, and placing them directly in `contracts` is invalid.

All registered definitions include the exact specification reference. `name` and `description` are Language labels, not inherited business defaults. Runtime contracts may carry these labels. `order` is an optional signed 32-bit Integer; omitted means zero. Unknown standard runtime fields are rejected, including `when`. Catalogue declaration holes do not cause absent options to appear configured.

The catalogue retains these **32 definition shapes**, including the reusable Compute Definition marker. The publication recipe in `src/blue_contracts/reference/catalogue.py` preserves the complete Language Source field-definition recipe of each. Tables below specify the additional closed runtime field and presence rules which cannot be expressed by an unvalued optional declaration alone. The current publication contains validated BlueIds and exact definition bodies. The input package’s baseline catalogue remains historical provenance.

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

## 5. Actual-value filtering

**C07.** A filter is a Language definition tested against the actual event. It MUST NOT be merged into the event as a way to create missing event data. The selected exact algorithm is `Bridge.matches`:

1. Obtain the actual exact value and validate it as a value; obtain the filter as a definition. Resolve required exact evidence.
2. Walk actual and filter recipes together. For every authored or concrete inherited filter field, require the corresponding actual field and a present actual value. Typed declaration holes contributed only by a standard definition are not invented required business fields.
3. For filter list positions, require the corresponding actual positions. Extra actual positions or fields are allowed unless applicable Language constraints forbid them.
4. When the pattern names an explicit type, require that exact type in the actual value's type ancestry. This prevents unrelated registered notification types with structurally compatible fields from becoming indistinguishable. This is a Contracts filter guard, not a change to Language structural refinement.
5. With presence established, apply the unchanged Language refinement/validation operation to check fixed values, types and constraints. Return false for the defined compatibility, fixed-value, schema, list-shape and present-value mismatch categories. Propagate missing resources, invalid evidence and unsupported conditions as errors rather than false matches.
6. Never replace or alter the actual value.

Pairwise visited-recipe tracking makes repeated/cyclic structure finite. There is no universal filter-depth ceiling. Demand-driven matching charges its prescribed logical work, retains repeated-pair cycle detection, and may be physically interrupted only as incomplete execution. Event fields inherited from the actual event's own valid type count as actual fields. Fields introduced only by the filter do not.

A filter `{kind: paid, amount: {type: Integer, schema: {minimum: 100}}}` matches an actual paid event with amount 120, not one with amount 20 or no amount. A filter on a containing event must use its actual nested shape. `call` does not silently redirect ordinary filters to the operation request.

For Embedded Node Channel only, its channel-level filter tests the inner application event. Its workflow-level filter and `$event` see the complete Embedded Event Delivery wrapper. This difference is explicit and does not apply to external events.

## 6. One selected operation call

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

## 7. External channel acceptance, lifetimes and checkpoints

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

## 8. Deterministic completion machine

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

Use the baseline exact member keys, NFC token rules, decoded pointer rules and Unicode code-point comparisons. Condensation dependencies precede containers; among ready components choose the lexicographically smallest sorted member-key tuple. Within a cyclic round, visit members in key order. Physical completion order is never a tie-break.

For each receiving turn, order source completions by source member key; within a source, order its completed batches by source turn serial. Within a batch, iterate event ordinal first, then the receiver's eligible occurrence paths and generations. Thus two occurrences of one child see `E1/path1, E1/path2, E2/path1, E2/path2`. Equal-content emissions remain distinct occurrences.

Install all required incoming source states before invoking any receiving handler, validate the resulting receiving view, and append all initial incoming event occurrences in that order before draining. Events emitted by the receiver append to its queue tail. After that drain, execute its surviving external seeds in channel order, draining local events after each seed as in the baseline. Incoming work can terminate the receiver or retire a seed before its direct external handling.

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

## 9. Nested steps and BEX effects

**C15.** A handler initializes an empty named-results map and executes its steps in written order. A step result key is its `name`, or its decimal list index when unnamed. Duplicate keys within that handler fail. Names and numeric defaults share one namespace. Returning from Compute returns from that program, not from the whole workflow.

For Compute, execute the existing BEX program and collect its value, changeset and events. The baseline's return-object convention remains: when the returned value is an object, present `changeset` and `events` members override the corresponding accumulated result lists; otherwise the accumulated lists are used. Both lists must validate. This convention is a Contracts interpretation of a BEX result, not a BEX operator change. Store the named result, apply all selected patches with their immediate local continuations, then enqueue its events in order.

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

## 10. Patches, validation and local Document Updates

**C16.** Retain add, replace and remove; nonempty relative JSON pointers; exact `~0`/`~1` decoding; canonical list indices; normalized list append; absent before/after sides; and exact no-op detection from the baseline. Root replacement through an empty patch path remains invalid. Runtime list pointers are `/lines/0`, not Source `/items` paths.

A parent cannot patch strictly inside a separately managed child. It may replace/remove the whole attachment or an allowed ordinary enclosing structure. A patch validates the current member's own exact local result under Language and its retained generalization policy; it does not mutate or validate a containing member against the source's intermediate state.

Retain the baseline protected-state checks. Ordinary effects cannot forge/change initialization, termination, checkpoints or protected policy. Apply the requested patch and any permitted generalization as one valid tentative local change. A failed local validity obligation fails the attempt. There is no temporary-invalid-patch exemption.

Reconcile the current member's occurrence declarations after a structural patch. Retire old generations immediately. Initialize genuinely new children to local completion through the initialization barrier in the annex, using only sealed dependency views. Incorporate their completed state silently; enqueue their completed event batches without re-entering the current handler. Then deliver the creating member's local patch notifications. The next normal step cannot see an uninitialized newly created child. If a newly forming cycle prevents recursive initialization, initialize its uninitialized members in deterministic rounds against their last exact pre-initialization views, as defined in A08; do not recurse indefinitely or expose the creator's live frame.

**C17.** A Document Update is delivered **only in the managed document that produced the business patch**. First deliver generated generalization type updates, then the triggering value update. Each notification completes its immediate local continuations before the next patch, step or ordinary handler.

A channel path matches a change iff its decoded segments are a prefix of that change's decoded local pointer. Ordinary nesting is still observable. A separately managed boundary is not ordinary nesting. No reverse embedding-route traversal, translated `/child/...` path or forwarded update occurs.

For `A → B`, B changing `/count` invokes B's local update handlers only. A's own explicit replacement/removal of `/b` is an A-local patch and can invoke A's handler at `/b`; an A handler at `/b/count` does not hear an ancestor replacement. Automatic incorporation of B's completed state invokes neither.

### Receiving validation is separate from source calculation

B must be valid under B's own exact admitted definition and dependency context. When A incorporates B's completed state, A must remain valid under **all** its own local/inherited contextual requirements. Incorporation does not erase a constraint, generalize automatically, or replay intermediate child changes. An invalid completed incorporation fails before A's observers run and rolls back this attempt. Parent-specific constraints therefore can reject the composed attempt without changing B's local calculation. Any enclosing refinement that Language includes in B's extracted exact local definition/context must travel with B and still constrains B's intermediate local patches. Do not strip such requirements to make a cached result reusable; a differently refined B is a different chunk input.

## 11. Local FIFO, output batches and lifecycle

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

## 12. Dynamic graphs, collections, shared members and cycles

**C21.** Keep the baseline `paths` and `collectionPaths` expansion rules: maps for collections, absent paths contribute none, lists at collection paths fail, nonempty valid pointers outside `contracts`, no duplicate or overlapping boundaries. Reconcile structural changes and allocate new edge generations in member/path order. There is no fixed maximum on active documents, edges, contracts, steps, effects, routes, turns or rounds. Retired history is not active work. Charge the required logical graph and processing work to the same invocation ledger before its charged action. Actual membership, complete validation and occurrence lifetime rules still apply; omitting a count check does not authorize pruning the graph or skipping recipients.

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

## 13. Generalization and explicit valid retyping

**C25.** A patch must leave a valid document under the unchanged Language. The default automatic-generalization mode is reject. Invalid documents are not admitted just because a workflow requested them.

When a change fails only a defined semantic compatibility, fixed-value or schema check, inspect the changed subtree bottom-up and then its containing spine. For each affected explicitly typed node, select the most specific matching policy path by decoded prefix length; equal-specificity ties choose the first rule in the policy list. `defaultMode` applies when no rule matches.

In nearest-valid-ancestor mode, try the current type first, then immediate ancestors in order. At each candidate, charge candidate work and require the candidate to remain a subtype of the policy floor when present. Validate the candidate node with its unchanged local and enclosing requirements; a local rule, enclosing schema or required field cannot disappear just because a type is generalized. Stop at the first permitted valid candidate. An evidence error is not permission to keep searching. Detect type ancestry cycles. There is no independent candidate-count ceiling: charge each candidate and required validation through the existing logical meter before continuing. Stop at the first permitted valid candidate, established failure of the permitted search, or actual gas exhaustion. Missing evidence or operational interruption is not proof that no valid ancestor exists.

Collect generated `/type` changes for all repaired affected nodes; finally validate the complete changed **local member**. Commit the requested value plus generated type changes as one valid tentative result. Local observers see the valid result; notify the type changes before the requested change's update. Failure of any remaining requirement rejects the whole patch and attempt.

**C26.** Explicit retyping is a normal controlled patch: a valid target definition and resulting content may be installed when the inherited/local context permits it and protected policy and managed boundaries are preserved. It does not imply automatic widening. Unknown target types, contradictory fixed requirements and incompatible enclosing declarations fail. A complete replacement can avoid depending on an invalid intermediate two-patch state; individually invalid intermediate patches are not temporarily accepted.


Enclosing constraints **within** the member continue to apply. A separate container is validated when it incorporates the completed member; it does not contribute an invisible mutable parent context to source execution. This changes the Contracts observation/validation boundary, not Language's validity relation.

## 14. Lazy content and installed runtime extensions

### 14.1 Lazy executable bodies

**C27.** Every contract header must resolve to an understood exact role. The runtime may retain separately addressed data and executable-body references. At discovery, read required headers, configured fields and type evidence, not every unused BEX body. At selection, demand the chosen workflow steps and each executable step, and compile/validate the demanded BEX. An invalid unused program is not executed speculatively; calling it must expose the error.

This is not a claim that first-time admission validates nothing beneath a reference. Full initial Language admission and cold restoration may require referenced content. The predecessor implementation verifies complete admitted state and performs lazy executable loading/compilation; that source observation is not a claim that this proposed revision has a finished persistent page cache. Previously established exact evidence may be reused only when bound to the same content, requirements and release. Missing required resources suspend rather than becoming empty objects or zero-cost successful work.

An unchanged large value retains its exact BlueId. Any eager/cached implementation must preserve the same state, events and logical gas. Cache warmth and network time are not semantic gas tariffs.

### 14.2 Extension registry and immutable bindings

**C28.** A RuntimeBinding pins the exact custom type ID, exact semantics-document ID, role, header/body field names, private gas namespace and tariff, optional inheritance to descendants, explicit peer fields, and live or ledger meter mode. The full record is immutable and committed in snapshots. Installing new types does not install their executable behavior. Standard implementations cannot be rebound. Conflicting bindings fail.

Roles are external-channel, processor-channel, handler, marker and nested step. These are runtime roles within the three top-level categories, not additional contract categories. A channel type must descend from Channel; a handler from Handler; a marker from Marker; a step from Contract. Standard abstract catalogue types do not count as concrete implementations. Descendant inheritance is enabled only by the binding's explicit flag.

An external-channel callback receives read-only header, complete original event, integer timestamp, prior checkpoint, bounded declared-peer lookup and live meter. It returns exactly a Boolean. It cannot return another event, a payload path or a delivery plan.

A processor-channel extension explicitly declares one or more internal families from TRIGGERED, EMBEDDED, UPDATE, INITIALIZATION and TERMINATION. Its accepted current internal payload is constructed through its installed deterministic `channelize_internal` semantics; this is internal notification handling, not external request extraction. Peer lookup is limited to fields explicitly declared in the immutable binding. All callback behavior is part of the installed semantics.

Handler/step extensions receive frozen event, header, selected body, previous step results, original cause identity, timestamp, member-local read function, gas meter and selected external call when applicable. They return a closed Contract Execution Result. Validate the entire staged result before applying effects, then use the same patch, continuation, FIFO, termination, boundary and rollback machinery as standard handlers.

Runtime implementations are trusted deterministic code; read-only Python wrappers are not a security sandbox. They must not depend on unrecorded clocks, randomness, I/O or hidden global state. A production host must provide the corresponding isolation outside these Contracts semantics. No authorization power follows from installing an extension.


All extension callbacks obey the same frame and completion boundary. An UPDATE extension sees local updates only. An EMBEDDED extension sees complete-batch entries after sealed source incorporation. No callback receives a live parent frame, enters another member recursively as an event side effect, or mutates the output list after sealing. Runtime ledger merging uses the same ordered logical work protocol as standard handlers.

## 15. Logical gas and host-independent resource semantics

**C29.** `GAS_MANIFEST.json` and `GAS_PROFILE.md` define the exact logical meter. The shared maximum and default remain **100,000**. This amendment removes unrelated structural/resource ceilings; it does not authorize increasing gas, disabling metering, or charging by host time/memory. Existing numerical tariffs are retained unless an explicitly recorded and qualified metering correction is necessary. Any such correction must define its exact counter, units, charge position and order before publication; preserve BEX value/evaluation semantics and distinguish the changed gas edition from physical optimization.

One shared ledger covers the complete rooted attempt; the default/maximum shared allowance remains 100000. Member ceilings are additional constraints on that same logical ledger. A charge is `(ordinal, namespace, counter, units, amount, owner)` and is debited before its work. Retain the baseline shared/local exhaustion tie-break and rejected-charge accounting. Rollback does not refund admitted work.

The canonical logical schedule is the dependency order, local turn order and component-round order in the annex. Chunk dispatch, transport, wall time and physical cache reads create no extra semantic charges. A cached chunk supplies the same verified logical segment; replay it against the attempt's current ledger **before** accepting any effects. It cannot skip work, reset allowances, erase a rejected prefix or be merged twice. Runtime callback namespaces and sealed runtimeLedger rules remain unchanged.

A standalone `process(B, e, t)` includes its own setup and root projection. Its scalar gas is not blindly added to another standalone `process(A, ...)`. Full equivalence uses one normalized attempt: shared preflight/finalization once, each logical member computation once per prescribed turn, each receiver's required application work, and the selected root's projection once.

The protocol has no separate maximum document/edge count, contract-map size, workflow-step count, patch/emission/route/dispatch count, turn/round count, content/path/filter/program depth, executable-body size, token length or generalization-search length. Keep the required syntax/normalization and exact value/format rules; remove only the unrelated resource ceilings. Explicit authored constraints and supported stricter member gas budgets remain enforceable.

The standard whole-attempt gas maximum is still 100,000, not 100,000 per member, page, chunk or component round. Existing explicitly selected lower test/invocation budgets and member-local ceilings remain supported and bound into execution evidence; a machine-specific shortage must not silently lower the authoritative budget. Exactly spending the remaining gas is allowed if no further charged work is required; the next unaffordable charge is rejected before its corresponding work. Do not change the existing tie-break or first-rejected-charge record.

All repeatable semantic progress formerly protected only by a removed count guard must have a defined positive logical charge or a finite structural termination argument. A scalar-expression base charge is not evidence that arbitrary-size arithmetic, copying or materialization is adequately metered. Review these paths before claiming gas-bounded processing. Reuse existing counters/quantities where they already describe the work; do not derive costs from Language's physical step count, a worker timeout, cache warmth or bytes actually fetched from a warm/cold database.

Gas is a portable work rule, not a promise of a fixed number of milliseconds, bytes of RAM or I/O calls. A correctly supplied under-budget invocation remains the same computation on every conforming host. Local inability to finish it is not a new semantic outcome; the host must improve capacity or implementation and retry the original pending work without increasing its gas allowance.

## 16. Atomicity, replay and chunking equivalence

**C30.** A sealed child or component completion is a **calculated value**, not a separately committed document. All affected state, output, protected markers, channel lifetimes and graph identities remain tentative until the entire selected attempt succeeds. Any failure rolls back the entire attempt; public events are empty on failure. Retain admitted gas diagnostics under the stated failure policy.

**Physical interruption is not a completed failure.** Memory/stack exhaustion, a configured host work cutoff, timeout/cancellation, unavailable storage or a failed worker before completion must not be translated into `GAS_LIMIT_EXCEEDED`, semantic `FAILED`, `TERMINATED` or invalid input merely because execution stopped. Unwind or abandon the tentative attempt and communicate a typed host/incomplete condition outside the canonical Outcome. The original committed state and input remain authoritative. A partial gas trace is diagnostic evidence only, not a completed receipt or terminal input disposition. Missing exact content continues to use the supported `NEEDS_RESOURCES` mechanism. If publication may already have committed, reconcile its original identity before another execution.

Checkpoint settlement occurs at the end of the eligible member turn so its completed state contains the consumed-original-event checkpoint. Validate the same activation and channel generation; retire old checkpoints on generation change. Later structural edits cannot transfer these records to a replacement. Final graph verification still runs before returning APPLIED. A parent that merely receives a child batch gets no external checkpoint from that receipt.

**C31.** Replay fixes the exact starting snapshot, original event, microsecond time, release, Language/BEX profiles, runtime bindings, selected exact dependency views and gas policy. It reproduces the exact resulting documents, root output occurrence order, checkpoints, status and canonical logical work/gas trace. Physical task identifiers, storage fetch order and cache statistics are not semantic trace fields.

### 16.1 Required composition property

For identical fixed inputs under this revision:

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

## 17. Conformance and integration

`CONFORMANCE.md` is the required acceptance matrix. `EXAMPLES.md` gives worked expected results and small Source YAML examples. The illustrative model retained under `inputs/contracts-completion-1-design/model/` is not the runtime. The actual executable qualification uses `tests/contracts_event/` and the website’s shared guide fixtures.

A conforming runtime must compare a direct driver and a chunked driver of this same new machine for exact state, occurrence order, checkpoint state, gas and failures. Old tests that assert deep updates or parent interruption of unfinished child work must be replaced with the explicit new oracles; unchanged functionality must retain regression coverage. Do not silently delete lifetime, shared-graph, cycle, resource or extension tests.

The publication generator uses `specification-src/contracts/` and the actual current runtime. It checks Language/BEX dependency hashes and generates a complete executable annex. Qualification must include an extracted/installable candidate; no prior passing count is inherited.

## 18. Normative algorithms and provenance

Authority order within this package: this specification, the detailed transition definitions in `ALGORITHMS.md`, and `GAS_PROFILE.md`/`GAS_MANIFEST.json`. The annex elaborates the requirements rather than preserving the superseded global FIFO. Any contradiction is a defect to fix, not a choice of implementation mode.

The exact predecessor sources and the original handoff are preserved in `inputs/contracts-completion-1-design/`. They are non-normative for changed behavior. No old source hash or old specification-bound type identity is reused to claim completion-1 semantics.

`inputs/contracts-completion-1-design/CURSOR_PROMPT.md` records the implementation and publication assignment. It does not delegate the decisions about local updates, batch placement, final child read views, cycle rounds, occurrence retirement or atomicity: those are specified above and in A01–A12.

## 19. Generic Coordination integration boundary

This edition adds read-only runtime context and controlled retained completion application. It does not add Timeline semantics to Contracts and does not alter `process(document, event, eventTimestamp)`.

An external channel receives its exact member, input document, channel key and generation, and a deeply immutable admission observation. The installed runtime verifier derives that observation from frozen evidence bound to the input snapshot, original event/time and registered runtime semantics before any seed is selected. A caller-supplied Boolean is not evidence. Portable invocation restoration repeats verification. Primitive channel acceptance remains Boolean and cannot replace the original event or the selected complete call.

`capture_source_outcome` issues an opaque capability only for an unchanged successful outcome produced by this Processor. `install_completion_reader` is a privileged one-time host integration hook for protected local storage, never an upload API. A reader must establish the retained before/after snapshot, exact receipt, event/time and runtime bindings. Unverified foreign results cannot enter through it. Retained receiving application requires the exact source predecessor, original member identities and complete inseparable source unit. It installs all eligible source state before callbacks, routes complete own-event batches through the same local kernel and supplies no receiver external seed or source business execution. Duplicates, incompatible runtime bindings, conflicting views and unsupported cyclic cuts fail atomically. Portable receiving export is explicitly unsupported in this candidate; it must not fabricate replay evidence.

`begin_live_application(document, source_completions, evidence=...)` is the corresponding combined LIVE preparation. It verifies admission and freezes external seeds against the original receiver input, then installs the complete required retained dependency results. Adopted owners and their already completed dependency closure are excluded from local execution. Receiving reactions run before the receiver's surviving own seeds, as required by C13. Only the completed invocation is publishable. Historical receiving remains seedless. Both preparation paths require the same protected completion provenance and exact predecessor checks; neither changes the public three-input processor interface or combines independent gas totals.

The hardening edition corrects a reference defect in the source-turn commitment used by emitted occurrences. Execution certificates include invocation-wide logical work and remain bound and checked as execution evidence. Such a certificate must not rename a member's application emissions merely because a different containing root drove the same semantic turn. The semantic incoming commitment binds each ordered batch's source member, serial, completed after-view, ordered emitted occurrences and captured occurrence tickets, together with the turn's existing cause, local before-view, dependencies, seeds, phase and lifecycle. The complete certificate remains in `turnInput` for replay verification. This is an explicit corrective reference edition, with a new specification identity; predecessor publications and their identities are preserved.

The local driver can complete an untouched local attempt without allocating portable token/candidate envelopes. It executes the same readiness, work-unit and finalization transitions, including every logical charge and first rejected charge. An attempt that has issued a token or accepted chunk history cannot change driver. Transport identifiers and copies are not logical work. Equivalence qualification compares outcomes, occurrence order, checkpoints, gas traces, rollback and low-budget failures.

Committed local turns retain exact handler/declaration attribution for each patch. This is protected execution evidence used by higher-layer lifecycle policies; submitted documents cannot author trusted attribution. Archive imports preserve original managed-member keys when unambiguous, so independently selected historical roots retain occurrence identity. Exact historical addresses still select their archived state, never an arbitrary newer live alias.


## 21. Lazy immutable host values (lazy-inputs-1)

An event, call, processingEvent or selected document collection is an immutable exact view bound to its effective Language recipe and captured resolver. Scalars are ordinary BEX values. Reading a root returns a view, not a recursively expanded JSON tree. Member/item access follows only the demanded path. Keys and presence retain Language meaning, including inherited values and absent declaration holes; missing evidence needed to establish presence remains a resource dependency. References are not ordinary business objects containing a blueId key. `$get`, `$keys`, `$var`, function arguments and subsequent pointer reads use the same collection interface as direct paths. Copies retain the captured view.

Serialization across a Blue output boundary retains the selected exact node and finite reference boundaries. It must not unfold predecessor history, replace a referenced value by null, truncate its meaning, or hash a display projection as its exact identity. Referenced and inline values have the same effective observation. Cyclic exact references retain their owning evidence. User programs cannot manufacture host capabilities.

Logical document/event member and item reads use the existing Contracts counters; node manifests are charged once per invocation logical inventory, independent of physical cache warmth. BEX arithmetic and control tariffs are unchanged. Size-dependent BEX output charges for an exact host value use the canonical exact-transfer accounting token specified in GAS_PROFILE.md, independent of its inline/reference storage form; demanded traversal has separate logical charges. The shared meter does not reset on path reads. Any explicitly selected physical Language control remains out of band and cannot create a semantic rejection. Explicit BEX `$fail` / `$failIf` reports EXECUTION_REJECTED, distinct from invalid executable syntax or an internal runtime error.

There is no protocol depth ceiling on demanded access. A selected subview keeps its exact resolver, logical meter and read context when copied, bound to a variable or passed as an argument; splitting a path cannot reset gas or skip required logical member/item charges. Untouched reference ancestry remains unopened. Host recursion failure is an implementation inability to complete, not proof that a valid deep value violates Contracts.

A well-formed unaddressed request with zero operation candidates does not invoke an operation. Eligible ordinary observers can still run, preserving the original event and call. A same-channel candidate missing the operation remains an error. Union observation does not repeat an already consumed operation. Runtime-certified operation audiences are internal verified data bound to input snapshot, original event, exact runtime and channel generations, not a fourth caller input.


## Exact-value transfer correction (gas-3)

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
retention remain mandatory. Missing/invalid evidence has its existing specified
outcome. Captured cyclic identities stay finite and preserve their owning sets.

This explicitly changes the metering edition, not Language identity or BEX
value semantics. Prior receipts and workspaces remain bound to their prior
release; reinterpreting them under this tariff is not an implicit migration.

## Selected descendant evidence correction (gas-4)

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

Canonical transfer tokens and value semantics remain as defined in gas-3. Read,
normalization, validation and effect tariffs still apply in their prescribed order.
The same selected exact descendant has equal traces and rejection behavior under
inline, reference, mixed, cached, restored and transported representations.


## 20. Exact executable reference binding


---

# Reference source hashes

```json
{
  "specifications/contracts/GAS_PROFILE.md": "83b4d23dc7f75f6d37bc0bc9dafcbcc59549863ec563e74a8b8ffabe35ef5bad",
  "specifications/contracts/TRANSITIONS.md": "8f93948681f2d53209a77546858ec1e3c370368589644a0109477f115e9c321d",
  "src/blue_contracts/GAS_MANIFEST.json": "2c72a406e4f342c2e4f53dee206592b3c4253b962e561ae436907b335246e3bb",
  "src/blue_contracts/reference/__init__.py": "78bed996244ac5fab47a02c2455614e69b920a4268f0a7fda241a54702b34bef",
  "src/blue_contracts/reference/catalogue.py": "51e75dfa01394a8b2493292d2dfc4c79c3b2031c8035a85882b284126c7585df",
  "src/blue_contracts/reference/channels.py": "1af7e3f1ba921fe0c4adac9d60f0b26e7b0e5c106d8c58fd3a801c3c0310160c",
  "src/blue_contracts/reference/chunks.py": "d1b3c588fb98c0ebaf5b18e2105384c3a38037dba58f2406228d994ad2e3af4e",
  "src/blue_contracts/reference/completion.py": "c46ac5fb09b69ba71d5284f47aed55251acff7aa958e8f1ee2f65d102ec3bd63",
  "src/blue_contracts/reference/compute.py": "147caf84e70bebb5e3dec2bd3f5d437a25b85e172d3d12e1b4c3725f79fa76ba",
  "src/blue_contracts/reference/generalization.py": "1f24b86271755ae5f1b5132c31de85d12d05d2a19c7c4b5d493201b953dff887",
  "src/blue_contracts/reference/graph.py": "106b07e478bf77e2314b28044e0338429958ac58397db83f142ae0d5d8247b17",
  "src/blue_contracts/reference/language.py": "2ae90402ede1299c0cd43c770406e0572ea8b68a384ce0d4bc01734da4b2f889",
  "src/blue_contracts/reference/model.py": "5dc49fa84e457f8c362b88b961e9036a1812a5697958a76cf0f3119a9dcdc145",
  "src/blue_contracts/reference/policy.py": "2423e9d280e20db1d08d8d6c42a8a8e4ab8e53d5f335866a27dd0eb7f2433121",
  "src/blue_contracts/reference/processor.py": "f9f8e70373d970f7cc0ee1a8322317418da154934af2506c8731ebbed755952c",
  "src/blue_contracts/reference/receiving.py": "f5d56b66afd83cc0128883018b412282145238f6a956e4077bb530996039c7ff",
  "src/blue_contracts/reference/registry.py": "93a3b8bad491d80782778e8032798f4671ee2a996f39694d44baa2f700bced6a",
  "src/blue_contracts/reference/runtime.py": "0b33f51fb2d99a01d1867ac24767b4158139de9165eef0f93f86750bf24b9196",
  "src/blue_contracts/reference/storage.py": "eae5dc318c226628d2a68a37175b10232846ed2611b1a8db4a007bbd6266458f",
  "src/blue_contracts/reference/work.py": "bdff38e23e770ce1cd47d99535cd668c59865c301f97b5622bc5c0812e64ff5f",
  "src/blue_host/__init__.py": "ac30b5090d56b101150b3bdb9bb05fff265308737c3ea0dd8b9caa22b0b5b607"
}
```
