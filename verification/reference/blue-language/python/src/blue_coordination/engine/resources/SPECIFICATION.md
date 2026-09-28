# Blue Coordination 1.0 — timelines, established history and delegated operations

> **Core authoring and Compute revision:** `2026-09-24-core-compute-1`. Bare mandatory core names, Language-backed node identity and shared Compute definitions. The Contracts maximum remains 100,000. See `docs/core-compute-20260924.md` for qualification.

**Edition 2026-09-24-core-compute-1 · revised runtime and generated type bindings.**

This specification defines portable meaning. `ENGINE-DESIGN.md` defines our automatic engine and storage implementation. `GUIDE.md` explains examples. `TYPES.md` maps the actual YAML definitions. Contracts remains the sole document-processing algorithm. The lower baseline is the supplied document-local-completion revision, not the older deep-update/global-FIFO revision.

## 1. Scope and authority

**Q01.** Coordination establishes which original inputs may be processed, in what order, against which exact history, with what participant authority, and what evidence establishes the outcome. It MUST NOT reimplement Contracts handlers, operation dispatch, child incorporation, initialization, cycles, gas or rollback.

`process(document, originalEvent, eventTimestamp)` retains its three inputs. The original event is never replaced by an inner request. The selected complete request is Contracts' `call`; operation arguments use `call/request/...`. Internal notifications remain internal. There is no separate channel argument or delivery/payload selector.

The exact type definitions determine Timeline, actor, channel and authority semantics. The host must implement every required contract it accepts. Unknown required behavior fails closed; having a definition's bytes does not install behavior. No public Execution Profile, repository manifest, duplicate limits catalogue or worker capability negotiation is required. Lower-runtime semantics and policy bindings still have to be fixed and retained for reproducible execution. Repositories are content/alias services, not semantic authorities.

The YAML folder is an isolated unpublished overlay. Its descriptions bind the exact BlueId of this text; the installed Timeline runtime also binds that exact semantics document. This does not override inherited Contracts specification fields or add record properties to scalar types. Reusing an authoring alias never authorizes changing content beneath an old published BlueId. Normative cross-field rules below supplement Language schemas; schema admission alone is not protocol verification. Optional complex fields are intentionally untyped declaration holes when inherited concrete defaults would materialize absent content; their descriptions name the required ancestry, which the protocol validator checks only when the field is supplied. This avoids inventing absent Operation Requests or Timeline Entries.

## 2. Identities and exact values

**Q02.** Distinguish:

| Identity | Meaning |
|---|---|
| DocumentId | Exact pre-initialization document identity establishing this logical lineage. |
| Document BlueId | Exact content, including legitimate processing markers. |
| History Position | One exact predecessor-linked position in established processing/receiving history. |
| Epoch | Number of the latest established stable revision in that history. |
| Processing instance | Host-local execution/control identity, never inserted into Blue content. |
| Occurrence | Parent, path, source lineage, activation generation and selected source position. |

Same exact initial content denotes the same lineage in this model; independent business instances must have legitimately distinct authored content. Two host accounts can establish independent processing instances without altering semantic identity. Repeated embeddings need not create duplicate authoritative histories. Different historical views are not silently merged.

BlueId comparison uses canonical ASCII identity text bytewise, not locale or database collation. Timestamp/ordinal comparison is numeric. All semantic identities use unchanged Language, including cyclic owning-set/member proofs. A hash of arbitrary JSON is not a BlueId. Physical record hashes and runtime capability commitments remain separately named.

## 3. Actors, submission provenance and Timelines

**Q03.** Actor is an extensible typed attribution value. Principal Actor identifies an account/principal; Agent Actor explicitly identifies automation. Provider-specific subtypes define their own accepted fields and authentication meaning. Exact actor identity, not a matching display name, determines equality. Principal attribution does not prove human presence.

`Timeline Entry.actor` is the actual submitter. `onBehalfOf.actor`, when used, is the represented holder; it never overwrites the submitter. `Source` describes authenticated submission provenance (for example interactive/API context), not a provider endpoint. Optional provenance is usable only when authenticated by the Timeline protocol.

**Q04.** Timeline identifies an ordered source and a supported verification protocol. Concrete provider implementations acquire its entries. Reading a Timeline or knowing its BlueId does not confer append/read permission. Providers authenticate submitters and retain exact accepted content. Their protocols determine evidence needed for those assertions.

The reference Signed Timeline is a strict chain: each new timestamp is greater than its predecessor's timestamp and at least the provider's already promised complete-before bound. The first entry has no `prevEntry`. Its public key authenticates source assertions; the verifier must separately adopt that exact Timeline/provider as authoritative for its claims.

## 4. Original entries and operation addressing

**Q05.** A Timeline Entry has required Timeline, integer timestamp, Actor and original message; optional predecessor, Source, Authority and operation. Time is an integer microsecond within the Contracts accepted range. Required references must resolve and validate; unavailable content is not an untyped general message.

If the message is a recognized Operation Request, `operation` MUST identify that same complete request. Otherwise `operation` MUST be absent. Inline and referenced forms are equivalent only when their exact identified values agree. Author the recognition field before provider authentication. Disagreement, malformed recognized requests, unknown required types and fabricated attribution are not ordinary filter misses.

The provider chain records acceptance, not application success. An entry can be accepted yet inapplicable or denied for a particular receiver. Idempotent append with one request key returns the original accepted entry; different content under that key is a conflict. This is transport bookkeeping outside the entry's business request.

**Q06. Target selection above Contracts.** An Operation Request's optional `document` is used by this Timeline protocol to identify the addressed logical document through its *established* exact history. This does not change Contracts: Contracts still treats its flag as an exact input-state precondition, not an instruction to retarget execution. The feeder narrows receiving contexts before calling it.

When `document` is present, resolve its actual lineage using established initialization/history. Offer the operation only to that lineage's applicable receiving view. If `requireExactDocumentVersion` is true, the original requested ID must equal that target's input-state ID. A stale addressed request is a refusal/failure for its real target, not a broadcast or a match for another document with a similar operation. Missing target lineage is a wait; proven inconsistent history is an error.

When `document` is absent, the request is channel-addressed: each active member with the named Timeline Channel and eligible participant/source is an intended receiver. Contracts validates the named operation on those receivers. Do not silently exclude a real receiver just because it lacks the named operation. Authoring helpers SHOULD include an exact known target reference to avoid accidental multi-target calls.

General messages follow Timeline/actor matching and actual filters, without operation targeting. Operation entries and general messages share one source order.

## 5. Completeness and range evidence

**Q07.** `Timeline Completeness Guarantee(timeline, completeBefore, lastEntry?)` asserts that all accepted entries below the exclusive bound are already fixed and no future acceptance can add one there. `lastEntry` identifies the last entry **inside that closed prefix**, not necessarily today's entire head. Its absence asserts an empty closed prefix. An unverified absence does not count.

`Timeline Range Evidence` contains a guarantee, an ordered entries list, optional `after` anchor and the exact provider attestation. With no anchor, enumerate from genesis. With an anchor, the verifier must already have established its contiguous prefix; enumerate all successors through the guarantee's head. When there are no successors, the anchor must be that head. An empty genesis range requires a headless guarantee. The anchor itself must be below the bound. A truncated physical page is not complete evidence.

Verification checks exact type/content identities, the adopted source authority, signature, same Timeline for every entry, strict source timestamps, each predecessor, final head equality, the bound, and agreement with any overlapping established prefix. An earlier weaker true guarantee can still be used; later assertions cannot rewrite earlier closed history. Contradictions are integrity failures, not an instruction to rewind consumers.

**Q08. Reference authentication.** Signed Timeline's public key and Timeline Attestation signature are lowercase hexadecimal of exactly 32 and 64 bytes respectively. Sign and verify this exact byte string:

```text
UTF8("blue.coordination.guarantee/1\n" + canonicalGuaranteeBlueId)
```

Use Ed25519. The guarantee's own exact content binds its Timeline, bound and closed-prefix head. Chained entry hashes bind all predecessor entries. That signature authenticates the provider's assertion about attribution/completeness; it is not independent proof the provider behaved honestly. Provider adoption/trust and access are explicit configuration. No caller field can install another trusted provider.

The included pure reference verifier implements this wire scheme. Memory providers can sign with a configured key; a production key must not be the deterministic demonstration key. Notifications are unauthenticated hints until their corresponding source facts are verified.

For efficiency, providers may return pages and anchored suffixes, provided the verifier assembles/establishes the identical complete chain. Resource limits produce a requirement/backpressure outcome, not a false empty prefix. No protocol-wide fixed 10,000-entry ceiling is introduced.

## 6. Canonical next-input selection

**Q09.** Order external entries by `K = (timestamp, timelineBlueId, entryBlueId)` with Q02 comparators. Equal-time entries on different Timelines remain distinct. A source-native page cursor is not the merged order key.

For the current exact receiving graph, enumerate every Timeline needed by the supported channel runtimes, occurrence-history obligations and pre-action authority. Use complete ranges sufficient to exclude earlier unresolved input. The aggregate safe interval for a fixed source set is below the minimum established exclusive bound. Settle the candidate's timestamp group before choosing its key; a bound equal to its timestamp is insufficient.

Keep source enumeration progress separate from channel checkpoints. A provider can contain irrelevant entries, denied entries and accepted entries with no business effect. Record their exact assessments in the receiving/lifetime context; never manufacture a Contracts checkpoint for an entry that Contracts did not consume. A full all-history lookup is not required each iteration once an exact prefix is established.

**SELECT**:

1. Verify the committed starting runtime state and the active occurrence lifetimes.
2. Resolve unfinished historical attachment obligations and any earlier source/authority prerequisites.
3. Determine the current relevant source set. Acquire and verify sufficient ranges; retain a precise wait when insufficient.
4. Merge unexamined entries by K; deduplicate the same exact source entry within this selection, not across different legitimate occurrence contexts.
5. Assess addressing and authority for each candidate against its real pre-entry context. Mark conclusively inapplicable/denied receivers examined without changing their business document. Do not execute a malformed or denied operation as a general event.
6. Select the least eligible candidate after all earlier relevant work is accounted for. Freeze entry, exact views, source guarantees and admission decisions.
7. After a complete result changing channels/embeddings, invalidate the unused old selection and repeat against the new topology.

Do not infer no work from an empty current notification queue or from a page limit. A `READY` read means ready through a specified checked boundary, not that no future event can occur.

## 7. Timeline Channel and immutable admission boundary

**Q10.** The feeder establishes admissibility; Contracts performs deterministic processing. A Timeline Channel cannot authorize a claimed Mandate merely by reading `onBehalfOf`.

Establish direct rights to the requested target channel first; a valid direct caller need not exercise a Mandate merely because delegation is supported. Delegated eligibility is not a fallback after failed operation validation. Direct authority requires the original Timeline and actor to match the intended channel under the supported source and target policies. Delegated authority requires Q12 and a legitimate originating channel/source for the actual actor in the target context. On an operation-bearing entry, its addressed member's declared source channels may observe the same original event as ordinary observers; the named operation executes only on its declared effective target channel. Unrelated members/channels cannot become recipients by sharing a type name.

The runtime integration consumes a **frozen verified admission set**, keyed by exact input member/view, channel key and generation, original entry and timestamp. It is produced by the verifier, never accepted as a user-supplied Boolean. It covers every relevant channel; a missing demanded decision is an error/wait, not an implicit denial that could hide a workflow. Primitive decisions are fixed before Contracts derives Composite/All External Channels. A replay reconstructs or verifies the identical decisions and their evidence.

Required narrow integration: the registered external-channel runtime needs the input member identity and channel key in its read-only context and access to this exact admission evidence. The supplied runtime's `ExternalChannelContext` has header/event/time/checkpoint/peer lookup but not those self identifiers. The implementation must add this **generic read-only context/evidence hook**, retaining the three-input public transition and all Contracts algorithms. It must record the evidence in the invocation dependency bundle. No Mandate evaluator, mutable global allowlist, database authorization lookup during BEX, replacement actor or extra `process` channel argument is permitted.

An implementation using another existing supported hook is conforming only if it proves the same binding, complete decision coverage and replay behavior. The single-document guide harness is deliberately narrower and is not evidence that this graph-aware bridge already exists.

Channel freshness uses the complete order key established from the original checkpoint entry and receiving generation. Comparing only checkpoint timestamp is wrong once delegated entries from several source Timelines may exercise the same target channel. All-history examined progress and occurrence application cursors remain Coordination records.

## 8. Mandates and scope

**Q11.** `Mandate` is a genuine processed owner-approved authority program. `Operation Mandate` adds a typed current `scope: Dictionary[Text, Operation Grant]`; it can permit multiple operations and targets. One initial Mandate reference is used as scope evolves. No mandatory guarantor or separate approval token is required for this base.

The lifecycle is Pending → Active → Terminated; Pending may terminate. Owner approval is an authenticated direct `approveMandate({})` operation pinning the exact reviewed pending state. It approves the whole program, participants, stored future grants and allowed state evolution, not just today's scope. A child/factory-created Mandate is not automatically approved. A specialized independently reviewed co-approval protocol can be added under a new type.

The YAML base supplies executable initialization, approval and termination. A supported authority implementation additionally enforces: genuine initialization/history, unchanged base lifecycle code/roles, protected lifecycle fields and participant channels, and owner-approved customization rules. An unrelated added handler cannot set Active or replace the holder. Every accepted authority-state transition must be checked against those rules using the actual Contracts result/handler evidence; superficial current-shape validation is insufficient.

Reserved writes are `status`, `approvedAt`, `terminatedAt`, the holder/delegate channels and base lifecycle handler declarations. Status/time writes are allowed only from the exact base lifecycle handlers. Scope changes from owner-approved additional workflows are allowed after their complete result validates every grant. Base operation scope-clearing is part of termination. Ordinary contract amendments to this approved program are not supported in v1: create and explicitly approve a replacement Mandate. Runtime failures cannot create approval.

**Q12. AUTHORIZE operation delegation**:

1. Preserve actual entry actor. Resolve the initial Mandate lineage; require a supported Operation Mandate.
2. Establish its exact state immediately before candidate K, including all relevant earlier own and embedded inputs, using complete provider ranges. Do not substitute latest or worker-time state.
3. Require genuine owner approval, Active state, unchanged protected program, actual actor equal to authorized actor, and represented actor equal to holder.
4. Establish that the holder actually controls the effective target channel and that its exact policies permit delegation. A Mandate cannot override a nondelegable target policy.
5. Match one complete scope grant: initialDocument if specified; exact channel key; operation key; actual target pattern/function; actual request pattern/function.
6. Each configured pattern must match actual values without filling omissions. Each predicate is read-only BEX and must return Boolean true. `$document` is the processed Mandate; document validation additionally binds `targetDocument`; request validation additionally binds `request`. These are authority-evaluation bindings, not extra target-workflow bindings. Missing evidence waits; false rejects; invalid code/result rejects as invalid authority rather than granting.
7. Do not mix pieces of different grants. Empty scope grants nothing. A future grant outside scope is inert.
8. Record the exact authority position and matching grant with the frozen entry assessment. Process the target only after eligibility is established.

The action's own subsequent effect can remove the grant. Do not apply that change backward. A revocation before K denies the call; one after K does not undo it. Histories with identical timestamps still use full K. An authority dependency cycle requiring the candidate itself to produce its own approval is invalid; earlier independent prerequisites can be computed, but no assumption of success closes the cycle.

The local Actor Policy is a Marker with an `operations` dictionary. `requiresActor` is principal, agent or any (exact supported Actor ancestry); `requiresSource`/`excludeSource` name the authenticated browserSession, apiCall or documentRequest Source specialization. Missing dimensions impose no extra policy restriction. `allowsDelegation:false` forbids use of a Mandate for that operation; absent/true allows checking one but never grants authority by itself. All applicable restrictions conjunct. Principal attribution alone does not imply a human: use the required authenticated Source policy where needed. The feeder inspects all such known policy markers; a validator/runtime registration recognizes the marker even though it emits no effects. Supported Actor/Source policies are ordinary exact contract types. This package does not reinterpret legacy policy or mandatory-guarantor IDs. Unknown required policy behavior stops admission. Target-side single-use, budget consumption and business guards remain the target's responsibilities; Mandates are not an implicit global consumable token.

## 9. Full-history establishment and initialization

**Q13.** Every managed document is established from its genuine pre-initialization content. Existing trusted local history can be reused; an uploaded initialized snapshot or alleged epoch is not authority to skip its prefix. No frontier-import admission mode or proof-trust shortcut is supplied in v1.

Top-level initialization has no fabricated Timeline event or timestamp. Its actual admitted original content and creation context are retained. Genuinely new runtime-created members use their Contracts-captured pre-initialization reference and causal creation context. Entries before a genuine birth boundary are not retroactively delivered. An existing document has its old birth; discovering it now is not a new birth.

Before using a supplied initialized version, prove its exact lineage, all required predecessors and exact position from reconstructed/local established history. A marked body without required evidence is `CONTENT_MISSING`/`DEPENDENCY_PENDING`, not a fresh document. Exact disagreement with an established immutable history is an error.

**Q14. Automatic managed membership.** Every surviving reachable occurrence declared by Process Embedded, including collection members and descendants introduced during processing, is included in the engine's managed collection. This is an implementation obligation of the selected engine, with the semantic identity/lifecycle restrictions of this section. Ordinary references are not automatically active subscriptions.

For a genuine new child, publication of the creating result atomically includes its legitimate initialized runtime, unique managed binding, source discovery and durable work. If the creating attempt fails, no successful child is exposed. For an existing child, reuse the unique binding and establish the required historical view; do not initialize it again. Missing content can create a provisional requirement/handle, never a fabricated stable document. If Contracts cannot finish the parent without it, the parent's prior stable state remains unchanged.

Removing an occurrence does not delete the source's authoritative session or retained history. Reattaching at the same path has a new generation, even for identical source content. Old pending applications cannot migrate to it. A node created and removed within one attempt need not remain an active managed listing entry; retain its attempted/committed lifecycle evidence as required, not a falsely surviving attachment.

## 10. Source history, receiving history and attachment cutoff

**Q15.** The receiving history of a new occurrence is distinct from the source history being proven. Let A attach source position Bp during entry a with boundary K(a). Determine the last source position established from work strictly before K(a), including prerequisites of that source's own earlier attachments. This is the frozen join goal. If supplied Bp lies beyond this goal, reject `FUTURE_ATTACHMENT_POSITION`; never expose future state to the earlier parent.

If Bp is older, apply the required contiguous successors after Bp through the goal in source-history order. Do not replay transitions already represented by Bp, initialization output already represented there, or previously retired occurrence work. A no-entry top-level attachment completes full-history establishment of the starting exact graph, then ordinary source selection begins; it does not invent a wall-clock attachment event. Its explicit initialized reference is the initial selected position. A runtime attachment caused by an internal reaction retains the actual external creation/activation entry (or no-event initialization origin) rather than the wall clock.

**Q16. APPLY retained completed source work** uses the Contracts completion kernel, not arbitrary patches or one `process(parent,event)` call per emitted value. Prepare one exact receiving turn with the complete eligible source-state set and full batches for a single recorded causal step, no receiver external seed, and the original causal entry/time when present. Install all those source states before callbacks. Preserve local updates, FIFO, occurrence generation checks and the selected root's own output. Preserve the lower logical work/gas schedule for that application. The source operation and source epoch are not performed again.

The current `begin/execute/accept/finish` API is scoped to an invocation and its exact tokens. Rebinding a committed source result to a new receiving invocation therefore requires a **supported completion-adoption / receiving-turn API** in the adapter. Its closed input includes receiver before-view, source predecessor/result evidence, source cause, occurrence tickets and source order. It verifies compatibility, seeds only permitted internal receiving work and returns a complete atomic result with captured member projections. This is a bounded runtime integration feature to implement/test; `snapshot = patch(parent, childAfter)` is not a substitute. Do not add an external wrapper or rewrite Contracts event recognition.

A source result from a different before-view, channel generation, refinement or cyclic context is not reusable. Match lower semantic turn descriptors and normalize logical setup/application work through the supported driver. Portable data-only chunks in the current code re-execute for verification; trusted persisted results need an explicit controlled local provenance path before execution can actually be avoided.

Merge historical prerequisites across changed sources by original cause K while respecting exact predecessor chains. Steps from the same original cause needed by one receiving turn are grouped so sibling state and whole-batch ordering match Contracts. No source can leap over another earlier required cause. A source's initialization position is a prerequisite, not an entry with invented K.

A historical reaction after attachment is recorded at that attachment's effective logical boundary for `stateBefore` queries, while retaining the original source cause/time for Contracts. This prevents the engine from falsely asserting that A had observed B's old event before A attached it. Parent direct checkpoints are not rewound or advanced by internal application. A subsequent parent input runs only after the attachment plan is complete. Topology changes during application cause reevaluation of remaining obligations; retired obligations end without transfer.

## 11. Completed processing, cyclic owners and failure

**Q17.** For LIVE work use the Contracts completed-document algorithm: local-only Document Updates; sealed state and whole own-event batches; parent state-first/batch-before-handlers; direct-child observation; coherent cyclic rounds. Exact accepted input and checkpoint provenance are unchanged.

A child completion is not a commit. One selected Contracts attempt keeps its complete rollback and shared gas boundary. Independently committed source and receiver attempts have distinct boundaries; a later parent failure does not undo an earlier separately committed source. An engine must not expose a tentative prefix of one attempt as a success.

In a live cyclic group, select one complete compatible component view and one canonical orchestration representative (smallest canonical DocumentId among the actual owners). Member semantics remain their own. Publish every required owner and genuine newborn together. Derive live membership from exact current evidence, never the union of historical backreferences. Sticky joins/splits within the attempt follow Contracts; later selection uses the resulting graph. One-way observers are not automatically added to the semantic atomic owner set.

Member runtime keys must be stable across rerooting of an established view. For first top-level uninitialized admission, use the canonical DocumentId as the initial root key. For runtime-created children retain the exact key produced by the Contracts vertex constructor (the baseline binds cause/input, creator key, path, allocation ordinal and initial value). Never reallocate this key on source promotion or cold reopening. Store this origin mapping as retained runtime evidence. A conflicting second birth origin for the same DocumentId is rejected as AMBIGUOUS_LINEAGE_ORIGIN rather than silently merged. Distinct business instances require distinct initial content. For archived duplicate views retain their already established separate exact runtime bindings; do not rename them during proof export. The adapter uses the captured Contracts keys/bindings; it cannot create B as a new root named `root` and claim source occurrence identity parity. New source/instance registration maps a canonical DocumentId to an existing verified slot; incompatible historical slots retain their exact declared bindings. Independent language implementations must use the origin-key rules in this paragraph and the pinned Contracts archived-view constructor and pass reroot/duplicate-view fixtures before claiming portable result identity. No random account/worker label may affect event order.

**Q18. Failure/progress.** Provider verified-prefix progress, feeder terminal/examined progress and successful Contracts checkpoints are separate facts. Against complete verified context, a bad operation, bad arguments, wrong actual target channel, stale exact precondition or established authority denial is durably REJECTED for its receiving continuation. An explicit business guard or direct deterministic gas exhaustion is EXECUTION_REJECTED. Retain the actual diagnostic, admitted gas and first rejected charge; no automatic budget escalation occurs. Neither outcome changes business state, creates an epoch/checkpoint, emits a success outbox item nor fabricates a successful source completion. The continuation automatically considers later ordered input after atomic decision publication.

The private InputDisposition binds original entry/full K, receiving instance and lineage, member/channel generations, exact evaluation prestate, verified authority/source evidence, structured reason and any real failed Contracts observations. Its stable lookup key is scoped to receiving history/lifetime and original entry, not the mutable current head. Later state cannot resurrect a terminal decision. New lifetimes and historical attachments retain their separately verified applicability. Admission consults the same retained decisions, preventing graph replay of rejected work in that continuation. Independent receivers are not globally blacklisted. Original evidence and terminal decisions participate in exact pre-time completeness without invented successful document history.

Missing content, incomplete coverage/history, unavailable providers, invalid signatures or contradictory prefixes are never converted to a terminal user rejection. Integrity and internal/unsupported execution faults retain their precise failure. CAS conflicts, transient I/O and unknown publication use conditional retry/reconciliation. A host parser/work/fetch limit, memory/stack failure, cancellation or worker death below actual deterministic gas exhaustion is an operational interruption, not `REJECTED`, `EXECUTION_REJECTED`, `NO_MATCH`, a successful History Position, or a consumed checkpoint. Preserve the original unresolved obligation and last stable state. Only the meter's authentic failed debit can establish a gas-exhaustion result; do not convert `OperationLimitExceeded`, `ResourceError`, elapsed timeout or missing evidence into gas failure. Partial trace data is host diagnostics, not a completed processing receipt. Reconcile an uncertain publication before repeating execution. A rejected direct attempt containing no committed source obligation can release its wave reservation; failed required receiving application cannot.

Missing content, source coverage or authority history waits. Last stable state remains readable. Completeness/provider facts are not rolled back by a document failure. Exported proofs must contain any denial assessments necessary to justify passage over accepted source entries; those assessments must be reproducible under the same earlier authority.

## 12. Receipts, positions and epochs

**Q19.** A Processing Receipt is a canonical computation claim. It is not proof of source order, issuer honesty or database publication. It contains the exact initial lineage, before/after documents, kind, ordered output occurrences and gas, with all actual owner/newborn projections in `members` sorted by DocumentId.

Variants are closed by these rules:

| Kind | Required additional fields | Forbidden |
|---|---|---|
| INITIALIZE | No event/time; before is captured original content. | sourceReceipts, attachment, fabricated event/time. |
| PROCESS | Original event and identical eventTimestamp. | sourceReceipts, attachment. |
| APPLY | Nonempty exact sourceReceipts, exact attachment; event/time iff its source causal step has them. | Receiver external checkpoint or fabricated source input. |

The top-level emitted list contains only selected root-origin output. Member projections preserve each member's output with zero-based distinct occurrence ordinals; equal values are not deduplicated. Source processing and receiving application are different receipts. Source gas is not copied as receiver gas or multiplied by number of owners. Actual integers come from execution. Failed runnable attempts retain diagnostics separately, not a successful Processing Receipt.

**Q20.** History Position forms an exact append-only predecessor chain. Position 0 records initialization. Every later retained complete transition increments `position` by one. `documentId` is constant; before must agree with the selected predecessor document/view under its declared transition. A stable revision advances `epoch`; a catch-up continuation can keep the previous stable epoch with `stable:false`. This extra coordinate prevents assigning new stable epochs to intermediate catch-up bookkeeping.

A Document Epoch references one stable History Position with matching documentId, document and epoch. Epoch 0 is the completed stable initialized result. Each subsequent stable logical change increments by one. Checkpoint-only changes count; physical collapse/reencoding, waiting, polling and unchanged carry do not. Final completion of a catch-up interval creates at most the next stable epoch, even if it had several intermediate positions. No unchanged cyclic companion receives an invented epoch.

`effectiveEntry` on a position is the receiving logical boundary: the external entry for PROCESS or attachment entry for its catch-up APPLY. Original source causes remain in their receipts. No-event initialization has none. `stateBefore(K)` replays/selects complete receiving transitions effective strictly before K, including their required catch-up, never simply the largest receipt timestamp less than K. Incomplete required history returns WAITING.

**Q21.** Processing Proof is an index to available exact content, positions, ranges, reproducible assessments and authority positions, plus the lower-runtime evidence necessary to reproduce member keys and exact graph commitments. Stronger sufficient range proofs do not change the same semantic processing receipt. Runtime evidence is supporting exact content, not an opaque assertion accepted as execution. Its codec must be the supplied lower-runtime snapshot/completion format or a verified equivalent; arbitrary dictionaries are invalid.

V1 verifies a foreign package by establishing initialization and replay, not by trusting its final snapshot. Provider authentication, source completeness, legal-next selection, authority, execution and host publication are different claims. Nothing here requires a zk-proof, trusted remote execution service, blanket signature of a result or extra Execution Profile type.

## 13. Conformance boundary

`CONFORMANCE.md` specifies source, authority, history, lifecycle, engine and performance cases separately. An implementation claiming Coordination support must pass protocol/source/authority/history cases. Our automatic-engine release additionally requires automatic progress, state/listing, wave scheduling, crash and bulk-loading cases.

The guide's executed reference examples are evidence only for the exercised single-document path and predicate checks. They do not certify unimplemented automatic workers, the generic graph admission bridge, cross-attempt completion adoption, database publication, cycles in the new engine or production throughput.

Authority order for this package is this specification for Coordination semantics; current Contracts for all document processing; YAML definition shapes plus the explicit cross-field rules here; then the engine design for the selected host policy. Disagreement is a defect to correct before publication, not a mode chosen by Codex.


## 16. Lazy input access and failed receiving obligations

The processor observes exact values through the Contracts immutable host-value interface. Timeline admission requires current entry facts and authenticated prefix evidence, not recursive expansion of prevEntry or inherited specification text. A demanded predecessor path follows that exact link. Authentication still verifies all newly supplied predecessor links/signatures; established prefixes can support anchored suffixes. There is no protocol maximum on a finite Timeline history, source count or logical prefix-verification task. Acquire and verify large histories incrementally using exact contiguous pages and retained verification state. Page sizes and per-worker acquisition effort are physical choices, not proof boundaries. An established prefix may anchor a later suffix. No intermediate page or partial candidate prefix becomes source completeness before all required links, bodies, authentication and the claimed end boundary are verified.

Operation audience and ordinary observation authority are independent. An addressed request selects only its established lineage for invocation. Other members with ordinary workflows on authorized source channels can observe the complete original entry. An operation-only channel outside the invocation audience has no ordinary workflow observation to schedule. Missing target lineage waits. A malformed typed request is not an ordinary message.

After a separately committed source result, receiving failure belongs to the actual receiver continuation. Retain its exact before-position, occurrence generations, source receipts, original cause, phase, gas and diagnostic, while keeping the source result successful. A deterministic receiver fault is ERROR; genuinely missing resources are WAITING and rechecked automatically. Ancestors and a source held by the strict wave barrier can be WAITING with DEPENDENCY_FAILED referencing that receiver. Do not mark the wave complete or drop its pending application. Leases are released while the durable reservation remains. Explicit retry revalidates the retained obligation without repeating the source operation. Unrelated work remains eligible. An entirely tentative rooted Contracts call still rolls back atomically.

Historical authority is evaluated strictly before the candidate full order key. A later terminal rejection or a precisely bounded later operational fault does not invalidate an independently established earlier prefix. Missing/corrupt earlier authority, or a failure with unknown relevant boundary, blocks. The candidate cannot authorize itself through its resulting scope change.

## 17. Fixed Contracts budget; host-independent progress

The current Contracts invocation default and maximum remain **100,000 gas**, shared across its entire required calculation including children, cyclic rounds and equivalent chunks. Lower gas ceilings already supported by the selected invocation/policies are explicit semantic conditions; host capacity must not silently choose a smaller budget. Native/reused execution must reproduce the same logical charge prefix. This rule does not create a 100,000 limit on the total Timeline lifetime or on all catch-up invocations combined.

Standalone content admission and provider history verification are prerequisites, not synthetic document operations. Their host controls may yield, stream or stop acquisition; incomplete acquisition cannot consume a candidate or become an authentication denial. Preserve source consistency, complete range verification and exact canonical ordering through page continuation and cold reopening.

A deficient host may stop an instance with an operational reason without changing the semantic history. Use the existing four-state engine model and a structured issue reason; do not add public resource-profile types. Release active worker capacity, retain required propagation/reservation obligations, permit unrelated work, and retry the original pending cause after capacity/implementation correction or explicit resume. Do not automatically increase gas, hot-retry unchanged insufficiency, or skip the cause so that later conflicting work passes it.

For an already committed child and an interrupted parent, retain the child's true success and the parent's outstanding receiving application. For one entirely tentative invocation, retain no partial state success. If execution finished but its database acknowledgement is unknown, original-publication reconciliation takes precedence over this retry path.

---

# Exact imported specification bindings

```json
{
  "edition": "2026-09-24-core-compute-1",
  "files": {
    "bex/COMPLETE_SPECIFICATION.md": "dc478556d2e18a3c0c12d010a9539bfd4ec87891da0dd9a25102a75b1638dfb1",
    "contracts/COMPLETE_SPECIFICATION.md": "c7cf9c28ca437701e1be27c925e4152cadce0eb6a3b4dc59e3cebbba4a63746a",
    "language/COMPLETE_SPECIFICATION.md": "445297a8da200d5644069cf009ab5374e46156b3d6d407fa663a048da6c7e30b"
  }
}
```
