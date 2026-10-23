# Receiver-relative admission and per-node replay — edition draft

Status: frozen normative candidate for the next local, unqualified publication.
This is a distinct rules source; the frozen v3 publication remains unchanged.
Not a published edition, implementation claim, or modification of any frozen
Coordination rules. Publication requires synchronized Contracts completion rules,
reference algorithms, new package identities and passing conformance evidence.
Old editions retain their original Q06/Q13 and publication behavior.

The full provider protocol in the included `coordination.md` remains normative
except where this document explicitly replaces a rule. That baseline has SHA-256
`194550d8dc90bb5a591d8e9cb05ec7c7c16e328ffe29c5517948538aac8a84b6`.
In particular, retain its wire schemas, signatures, authenticated range chains,
access grants, operations and provider content authorization. Its global
operation-target history prerequisite is replaced by section 2 below, and its
Contracts execution dependency is the exact demand-scoped edition selected by
this publication. Provider entry admission validates every required envelope,
type/contextual constraint, signature, chain and binding obligation without
assuming full certification of opaque payload references; payload constraints
that actually require content still demand that content. This is a new-edition
boundary policy, not a change to Language `strict_certify`.

## Retained transport boundary

This edition consumes the existing provider transport without replacing its signed
objects. The explicit data-only `RetainedTransport` dependency is package
`BS8vv7BS6hd3ecLyouphhMoPokPAjzzwVLPd83WjHL3x`, archive SHA-256
`b96ec4011bb0512d896a58e37d3c63ca3531c06244b2d0777cfdd5a106198b88`.
It supplies exact definition and specification witnesses, not an execution
protocol requirement or permission to install the previous execution handlers.

The executable Timeline Access and Timeline Access Update accept retained Signed
Timeline identities in `allowedTimelines`. The new Public Timeline Channel binds
the retained Timeline Provider; the new Timeline Channel binds retained Signed
Timeline and Actor values. The new Timeline Access Response carries retained
Provider Attestation values in `publication` and `lastEntry`. Their existing
signature, chain, actor, grant and reachability checks remain mandatory. Raw key
and signature values retain their existing constraints. The Get Timeline Access
request and access document remain members of this new edition.

Provider transport entries, timeline identities, actor identities, checkpoints,
range evidence and signatures are not rewritten or re-signed for this edition.
This boundary does not equate distinct exported type identities or declare fresh
transport exports to be subtypes of retained definitions. Producers of the
supported retained transport continue to use its original exact types. Other
exports retain their explicit authored schemas; their presence is not a claim
that an arbitrary mixed-edition envelope satisfies those schemas.

## 1. Inputs and evidence boundaries

An input has its original signed Timeline entry and full canonical order
`K = (timestamp, timelineId, entryId)`. Contracts receives the original
`event: {blueId: entryId}` and original time; neither a replacement entry nor a
proof sidecar is introduced. Authenticating the entry, establishing a verified
source prefix, authorizing its actor, and executing it are separate obligations.
Knowing an entry identity is not evidence that its payload or authority is valid.

A receiver is a logical document lineage with a specific member/channel lifetime.
A receiving occurrence additionally identifies its source, path and generation.
Source processing history and an occurrence's history of receiving source work
are distinct. Sharing an acquisition does not merge these obligations.

`PRE(R,K)` is the exact receiver view established from work strictly before K,
including earlier attachment prerequisites and terminal input dispositions.
It includes the genuine original document identity, the ordered established
versions of that lineage before K, and the applicable declarations and authority.
It does not include a later version merely because its content is locally cached.
Completeness requires the existing verified source-prefix conditions, pending
work checks and exact predecessor proofs. A timestamp alone is not a boundary.

Missing evidence needed to establish PRE is a wait. A recursive visit is not a
proof of completeness. An uploaded initialized body is not a substitute for its
required history. Contextual constraints and actual reads remain obligations of
the selected Contracts edition; opaque references do not discharge them.

## 2. Q06: request selection relative to the receiver

The following classifier concerns operation dispatch, not ordinary event
observation. First establish the entry's framing, signature, source membership,
canonical order and complete PRE(R,K). If these prerequisites are missing, wait;
if they are invalid, retain the existing specific rejection. Do not fetch the
request's target body simply to classify an exact-version mismatch.

Let `current` be the exact document identity in PRE and `ownPast` the genuine
original identity plus every established own-lineage version strictly before K.
These are identities established by the receiver's history, not all identities
known to a global store. The original identity remains usable for non-exact
requests after initialization and subsequent changes.

```
classifyOperation(request, R, K):
    pre = requireCompletePRE(R, K)
    if request has no document target:
        return SELECT_USING_CURRENT_DECLARATIONS
    t = request.document
    if request.requireExactDocumentVersion:
        if t == pre.current: return ELIGIBLE
        if t in pre.ownPast: return REJECT_STALE_EXACT
        return OUTSIDE_EXACT_PRE_VIEW
    if t == pre.current or t in pre.ownPast:
        return ELIGIBLE
    if authenticated established lineage evidence proves t belongs elsewhere:
        return OUTSIDE_LINEAGE
    return WAIT_TARGET_HISTORY
```

`OUTSIDE_EXACT_PRE_VIEW` is an operation no-match for this receiver at K. It
makes no claim that t is globally foreign, invalid, or unavailable. In particular,
a future own version mismatches at K whether or not it is cached. This is an
explicit new-edition rule. It is not the old rule with a missing-content error
caught and converted to no-match. An incomplete own prefix cannot use this rule.

`ELIGIBLE` is not authorization or success. Resolve the actual operation/channel,
its schema, actor/mandate and business prerequisites in PRE. Missing required
operands wait; established denial rejects. A non-exact request to an unknown
identity still waits unless actual evidence establishes a different lineage.
Neither inequality nor inability to fetch proves that distinction.

Independently select ordinary observer channels from the same original entry.
An operation outside the receiver's audience does not suppress an otherwise
eligible observer. Such an observer may legitimately need payload data and wait
for it. Operation-path rejection/no-match is scoped separately from any real
observer processing; a feeder must not stamp a whole-entry rejection that hides
an eligible observer. All applicable paths must settle before this input is
complete for the receiver. If observation executes, only its actual Contracts
result may establish a checkpoint. A pure operation rejection/no-match establishes
only a private InputDisposition, never a fictitious Contracts checkpoint.

A disposition binds original entry and K, receiver lineage/lifetime, member and
channel generations, exact PRE and verified source/authority evidence. A settled
path cannot be resurrected by later state in that lifetime. Other receivers and
new generations remain independently evaluated. Publish decisions atomically
with any actual receiver result; do not advance past unresolved selected work.

## 3. Q13: raw node establishment and replay

Every lineage starts from its genuine pre-initialization content. Record that
exact reference before initialization. An already initialized reference follows
the existing-history attachment algorithm below; it is never treated as raw.

For a genuinely new raw child captured by a parent attempt at Kbirth:

1. Retain Contracts' raw source and actual creation provenance. Establish the
   child's own initialization semantics as for standalone admission of that raw
   source. Do not inject a fabricated event/time into initialization. Creation
   provenance remains host/runtime evidence and is not substituted for raw input.
2. Discover the child's required sources using the new edition's ordinary
   source/authority rules. Its replay frontier starts at its own initialization,
   not the parent's last processed order, inherited channel cursor or birth time.
3. Establish its ordered history from the beginning through Kbirth **inclusive**.
   Execute each selected original entry once for its own lineage/channel lifetime.
   Lack of relevant access, authority or content remains a real prerequisite.
4. Deliver retained child results through the completion receiving kernel to the
   eligible occurrence. This turn has no external parent seed. It must not invoke
   the parent's creating operation again or replay the parent's direct history.
5. Record source processing and occurrence receiving separately. Persist pending
   prerequisites and source/receiving positions so a restart resumes the same
   obligations. Do not expose the creating graph as stable while required child
   catch-up or receiving work remains unfinished.

The creating attempt still has its normal rollback boundary: a failed attempt
cannot expose a successful child. Separately committed source work can survive a
later receiving failure; it is reused through verified completion provenance,
not executed again. Intermediate positions retain their non-stable status.
Publication of a stable result must include all required owner/member results,
origin mappings and completed receiving obligations atomically.

Equal timestamps use the full K ordering: earlier ties precede the birth, the
birth entry is eligible exactly once for the child, and later ties remain later
work. The parent is not reseeded at any tie. If a child declaration appears while
processing Kbirth, the dispatcher must not also deliver that same entry as an
additional external live seed after replay has covered it.

### Historical channel activation: scan, causal and attachment coordinates

A newly installed channel lifetime is an ACTIVATION continuation, distinct from
raw-node INITIAL replay. Retain its member/channel/generation, exact committed
activation snapshot and receipt, scanActivationBound A, causalVisibilityBound V,
and original examined full-K cursor. A is the installing invocation's original
input K; V is the maximum full-K bound of the installing invocation itself and all its
causal ancestors.
Outer child attachment visibility Kbirth remains a separate coordinate.

ACTIVATION examines authenticated source entries strictly before A. Raw INITIAL
replay examines its own sources inclusively through Kbirth. Neither boundary is
changed by cached future content or wall-clock time. Installing an existing
channel does not silently consume the installing entry a second time.

For an activation delivery of original K, PRE_ACTIVATION is the exact invocation
prestate established by a contiguous shared receiver causal publication chain
anchored at the activation receipt. Include all earlier scheduled applicable
lifetime turns and receiving results, not merely this lifetime's own turns.
Select operation declarations, receiver actor-policy/business state and exact
current/own-past target classification from that proved prestate. The original
lineage identity remains available for nonexact targeting. Original-K source,
signature, mandate, grant and revocation history remains the authority bound;
a later grant at A never retroactively authorizes the original K.

For a supported canonical Mandates/Mandate Authority, signed-prefix admission and authority-header reads require the contextual authority header, its actor, its closed field set, and an authored original-mandate identity. Only an exact reference occurrence governed solely by the canonical Mandate Authority.mandate declaration may defer that declaration's Mandate value/type obligation until owned original-mandate history before the entry's order key is available. Additional contextual contributions, requirements, type narrowing, or inline governing metadata retain ordinary required-value validation. After resolving that history and before granting authority, the original contextual mandate occurrence MUST satisfy its full value/type obligations. Header admission, retention, and reuse establish neither a whole-value certificate nor authorization; signature, actor, history, approval, status, participant, and scope checks remain mandatory.

A deterministic worklist completes activation prerequisites before the next
ordinary receiver input. Select the minimum original full K within ready
obligations, retaining per-lifetime cursors and exact predecessor receipts.
Equal-K deliveries may share an invocation only if their actual receiver
prestate is proved identical; otherwise execute in ascending `(member identifier, channel name, generation)`
order: the first two use the existing canonical string ordering, followed by the
numeric generation. Map iteration order is not a scheduling rule.
Nested activation retains its own strictly-before scan bound and inherits causal
visibility. For example, L3 installed at original K10 during A100 replay scans
before K10 but remains visible at100, never at10. An earlier logical input cannot
observe effects from a future causal ancestor merely because they were cached.

Operation dispositions bind these coordinates and their exact receiver prestate.
Terminal-only progress, retired/replaced lifetimes and actual receipts remain
separate. A repeated worklist key is unresolved until every local/source/receiving
premise is proved. No global original-K monotonicity shortcut, latest-head
substitution, checkpoint rewrite or parent reseeding establishes completeness.

Conformance additionally covers shared L1/L2 state, nested decreasing scan bounds,
exact-current/stale and nonexact-original targeting, original-time grant/revoke,
full-K ties and persisted restart between installation and historical delivery.

### Existing source and occurrence attachment

An established source retains its original birth, identity and source history.
Attaching it at K freezes the last established source position from work strictly
before K, including that source's earlier attachment prerequisites. Reject a
supplied initialized position beyond this goal. Apply contiguous missing source
successors through the goal without repeating initialization or source effects.
A K-live step then uses its own exact checkpoint/disposition and is not duplicated.

Receiving old source work is effective at the receiving attachment boundary for
receiver history queries, while Contracts keeps the source's original cause/time.
Do not rewind parent checkpoints. Finish required attachment work before the
parent's next input. Detach retires an occurrence, not source history; reattach
creates a new generation and cannot inherit retired pending receiving tickets.

Member origin keys remain exact across promotion/re-root/cold restore. Runtime
constructor keys and independent standalone root keys must not be silently
merged. State-equality conformance compares the child document projections;
completion reuse additionally requires compatible member origins and before-view.
Exact state parity requires the same raw source, applicable semantic context and
relevant authenticated histories. Different parent-imposed constraints are not
assumed equivalent. The same raw source in an independent account is independently
established, not a portable capability to adopt another account's local completion.

## 4. Temporal dependency algorithm and cycles

A pending history obligation is keyed by logical lineage, exact bound, phase
(initialization, before-view, source execution or receiving), and occurrence
generation when applicable. Dependencies retain their bounds; do not collapse
`A before K1` and `A before K2` into one visited document flag.

Maintain unresolved obligations and exact dependency edges. A completed memo can
be reused only for the same obligation and verified evidence. On a repeated
unresolved key, record the edge and analyze the component; never return complete
just because a DFS has encountered it before.

- A historical edge that reduces the bound is ordinary predecessor work. Resolve
  its finite established prefix, then its dependents. Example: A before K30 needs
  B before K20, whose earlier attachment needs A before K10. A's established
  initialization/K5 prefix terminates this chain; this is not a live cycle.
- A missing predecessor, content record or verified prefix is a resource/history
  wait. Repetition does not turn it into an error or authorize a guessed state.
- A live cyclic component may use the existing Contracts component algorithm
  only after every member's exact compatible pre-view and external prerequisites
  are established. Select the canonical representative and publish the complete
  atomic owner set. This resolves simultaneous live computation, not absent past.
- A same-bound proof cycle with no established pre-view is not evidence that any
  member exists or is ready. If it is only waiting for an external predecessor,
  keep that concrete wait. If closed immutable lifecycle evidence proves mutually
  dependent creation with no legal predecessor/initialization, reject that
  inconsistent history with `INVALID_CAUSAL_HISTORY`; do not manufacture a member or spin until success. This error requires a closed proof of contradiction, not merely an unresolved SCC or unavailable predecessor.

No arbitrary new iteration ceiling is part of this rule. Native deterministic
work/gas limits still apply to actual execution. The implementation must retain a
bounded diagnostic for an unresolved dependency component without calling it a
success. Ordinary graph recursion alone does not prove inconsistent history.

### 4.1 Reference procedure for established local history

The following procedure consumes authenticated local journal history, not
caller-authored proof claims. It does not replace raw establishment in section 3.

```
proveBefore(receiver, K, journalView):
    queue := [(receiver, K, BEFORE, rootOccurrence)]
    checked := empty map
    while queue is not empty:
        obligation := removeFirst(queue)
        select exact last history position with effectiveOrder < obligation.bound
        require its binding, contiguous predecessors and committed completion link
        read member/edge generations from that position's immutable completion.after
        require the exact expected source version for an incoming occurrence
        require local prefix and earlier timer/attachment/rebase work to be settled
        derive source channels from this selected member, not current-head channels
        if any requirement is unavailable: return its bounded unresolved obligation
        if this exact obligation was checked with the same evidence: continue
        record its checked local premises
        enqueue every selected edge's source-view obligation, retaining generation
    return a token bound to receiver, K and this immutable journal view
```

The checks on an incoming edge also occur on repeated keys. Repetition cannot
hide incompatible expected source positions. A token can select only the entry
whose full K and journal view match it. Future cached versions are not own-past
facts. A source completion that the receiver has not applied cannot satisfy an
edge merely because both document rows exist. Terminal input decisions are
retained prefix evidence, not successful source transitions.

Receiving prerequisites retain the source's original cause bound separately from
the receiving effective boundary. For example, receiving source event100 at
attachment300 may require a source prefix through100 (completeBefore101); it
cannot demand301 solely because the receive is published at300. Conversely, that
completed receive does not prove the receiver's later PRE301: later relevant
source work still needs its own prefix and receiving evidence. These are distinct
obligations in the same time-indexed procedure, not one document-wide visited bit.

## 5. Completion, persistence and resource origin

Use the new Contracts edition's normal completion/receiving API. A result binds
before/after state, original cause, executing edition/runtimes, member origins,
operation scope and the actual validated obligations. A data-only snapshot or
source-prefix witness is not a completion. Local durable recovery may rehydrate
only authenticated journal provenance for that edition and exact result.

Receiving installs the eligible source states before callbacks, preserving
whole-batch order, owner boundaries, generation checks and gas accounting. It
never substitutes direct snapshot patches or an extra parent external seed.
Cold recovery must reconstruct pending admission, source execution and receiving
without granting full Language certification to an operation-scoped result.

A required content identity does not identify a provider. Original cause timeline
alone does not authorize fetching every reference encountered while processing
that cause, especially a reference reached through older history. Provider
selection must use existing authenticated/adopted source provenance and access
mechanisms. Invocation-local required-read provenance also covers native matcher
opens: it relates reported missing identities only through ordinary authored edges
of bodies actually opened by that evaluation. A wrapper-specific read path is not
the only source of such observations. This collector supplies an observed path,
not authenticated provider authority; it does not search imported/provider
inventory or infer authored paths from inherited type fields. This draft does not introduce a wire proof sidecar or unrestricted
search over imported timelines. The exact host mapping for historical obligations
is an implementation gate to resolve with source-access owners before publishing.

## 6. Required executable conformance cases

Each test runs old and new selections where behavior changes; do not update old
expected outcomes. Missing/cached variants use identical admitted logical input.

| Case | Minimal fixture and required outcome in the new edition |
| --- | --- |
| Exact current | Complete PRE at K, target current: dispatch plus normal authority checks. |
| Exact stale | Known own predecessor, exact=true: durable operation rejection, no operation checkpoint/effect. |
| Exact future absent | A future target identity signed into K, future body unavailable: exact mismatch, no fetch. |
| Exact future cached | Same K/PRE/entry as preceding case, later body/history cached: identical decision. |
| Exact other receiver | Private Agreement exact target then child-target operation: child reaches later input without parent fetch. |
| Incomplete PRE | Repeat exact mismatch with required earlier prefix absent: WAIT, then settle after that prefix arrives. |
| Non-exact original | Agent request targets original raw Order after initialization: normal authorized dispatch. |
| Non-exact unknown | Unknown target with no lineage proof: WAIT; no false foreign/no-match. |
| Mixed audience | Exact operation mismatch plus matching ordinary observer: observer receives original event, including real operand WAIT. |
| Raw birth | Counter observer sees K100, birth K200: standalone and embedded raw child have identical complete state/BlueId; parent birth executes once. |
| Ties | Three entries at one timestamp ordered before/equal/after birth: each eligible child effect once, no parent reseed. |
| Existing attach | Attach an established earlier position; contiguous receive only; initialized future position rejected. |
| Reattach | Detach/recreate same path: new generation, source effects unchanged, no transfer of old pending ticket. |
| Decreasing history | A@30 -> B@20 -> A@10 with established K5 prefix: resolves, including after cold reopen. |
| Live SCC | Two established mutually embedded members: coherent component result and atomic publication, no recursion shortcut. |
| Missing cycle predecessor | Same-bound dependency component with one missing external predecessor: durable wait and automatic resume after exact evidence. |
| Invalid birth cycle | Closed lifecycle evidence requires each of two unestablished members to precede the other's initialization: `INVALID_CAUSAL_HISTORY`, no invented stable member. |
| Unproven birth cycle | Same apparent cycle but missing one lifecycle predecessor/witness: WAIT, never `INVALID_CAUSAL_HISTORY`; adding the witness may prove consistency or contradiction. |
| Full acceptance | Real original raw Order, separate Seller/Partner/Customer stores, Seller Agent exact-original mandate, second operation and cold reopen: full state/BlueId equality and no private Agreement acquisition. |

## 7. Publication gates and source anchors

This draft selects exact mismatch-at-PRE semantics rather than claiming universal
foreign-target detection. Implementation must expose path-scoped operation and
observer outcomes or prove its existing admission representation can express
section 2 without suppressing observers. The immutable inconsistent lifecycle diagnostic is `INVALID_CAUSAL_HISTORY`;
a missing witness must remain WAIT. This distinction is mandatory even when a
worklist encounters the same unresolved key repeatedly.

Required design checks before reference implementation: bounded child-only
catch-up/receiving without parent reseeding; initialized child equality without
forged origin adoption; historical demand-to-authorized-source mapping; and the
Contracts completion contract for operation-scoped outputs. None is proven by
this prose. They must be settled in code-backed fixtures before publication.

Baseline anchors (retained, not edited): canonical `coordination.md`, source
coverage/admission around lines 865–925; Core `runtime/final-gas-bridge/spec/
prior-rules.md` Q06 and Q13–Q20. Current reference implementation anchors:
`CoordinationAdmission.verifyAdmission` (global target-known gate and separate observer
selection), `CoordinationHistory.belongs/before/completeBefore` (global version
membership, historical views and recursion), `CoordinationEngine` attachment,
receiving and member publication; `ContractGraph.freshKey` for member origins.
Existing small starting repros are `MinimalRawBirthBoundaryTest` and
`MinimalTemporalHistoryViewTest`; a cached future view test is not by itself an
admission conformance test.
