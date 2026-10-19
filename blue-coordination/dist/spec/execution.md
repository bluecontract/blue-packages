## 14. Execution history and frozen obligations

### 14.1 Authority and identity

This chapter belongs to the same Coordination publication as sections 1–13.
There is one Coordination namespace and one selected rules identity. It adds no
second execution protocol or alternate provider signature format. In particular,
the provider's `blue.coordination.guarantee\n` domain, provider key selection,
entry bounds, full ordering key and strict completeness rules remain unchanged.
An older signed object cannot be relabelled as an object of this edition.

Executing hosts MUST select the exact Contracts edition required by this
publication. Contracts owns initialization, local turns, admission, receiving,
event occurrences, work order, gas and atomic rollback. A Coordination host
MUST NOT reconstruct those results with its own business-state mutations.
Repository availability is separate from executable role registration. Every
snapshot, source completion and restored invocation MUST have the exact selected
active binding sequence. A superset of available implementations is not permission
to promote a snapshot. Timer roles are optional capabilities outside the non-timer
profile. Ordinary supplied timestamps and ordering remain mandatory.

`Document Epoch` identifies a stable result by original document identity, exact
current document, epoch and History Position. Epoch zero is the first committed
initialization result. `History Position` additionally identifies each retained
processing or receiving transition by its monotonically increasing position,
immediate predecessor, stable flag and Processing Receipt. Position zero has no
predecessor; every later position names exactly the preceding committed position
of that owner. A catch-up position may retain the last stable epoch. No counter
alone proves ancestry, completeness or commitment. Exact operands may be unvalued
Blue definitions: protocol presence is checked as exact content, not truthiness.

`Processing Receipt` retains the original Contracts receipt commitment and exact
before/after projections, source receipts, member results and ordered emitted
occurrences. INITIALIZE has no external cause; PROCESS retains the original entry
and its timestamp; APPLY retains the ordered source receipts and attachment
obligation being discharged. It MUST NOT claim a second execution of the source's
operation. `Member Result` describes only that owned member. Equal event values
retain distinct `Emitted Occurrence` ordinals and native occurrence identities.
The full Contracts evidence, including Dispatch decisions when present, is retained
without removing fields or sorting output lists. A summary is not a substitute.

### 14.2 Independent owners and receiver prefixes

The publication policy is `independent-owner-prefix/1`. An acyclic source may
commit once its own applicable inputs and dependencies are ready. A waiting or
failed consumer MUST NOT invalidate, roll back or prevent an independently sealed
source result. The consumer records its obligation to that result. Consumers of
that consumer wait for its missing prefix, not for an invented global barrier.
Publication order among independent owners is physical; each owner's logical
input/result order and each receiver's required prefix are invariant.

A receiver applies source results in the order prescribed by Contracts receiving,
from contiguous established source history and exact activation lifetimes. It
MUST NOT skip an earlier required source result in favor of a later visible result.
An entry can be supplied only when every applicable source has the strictly
sufficient coverage required by section 12, including all members of the full-key
tie. A checkpoint at timestamp T does not imply completeness beyond T. An empty
poll, a worker's READY status, or an absence of notifications proves nothing.

Actual strongly connected owning components use the Contracts atomic cyclic unit.
Their local rounds, preceding-round views, shared/member gas limits and publication
are atomic. No host commits a strict subset of such a unit. A terminated member
inside a live cyclic unit may receive silent structural updates as allowed by
Contracts; that is not autonomous execution of a terminated root. Discovering or
joining a historical cycle without sufficient exact ownership/history evidence
fails explicitly; a current-view SCC helper does not establish that support.

### 14.3 Attachments, catch-up and historical authority

An Attachment binds consumer occurrence, decoded path, generation, exact source
operand, source initialization, selected source timeline and source History Position.
It freezes its activation entry or initialization cause and finite target goal.
Removing and recreating the same path produces a new lifetime. An old obligation
cannot be reassigned to the new lifetime. Shared acquisition never merges distinct
occurrences or their delivery identities.

An already initialized source requires its relevant history from the established
initial position through the frozen goal. Catch-up verifies every predecessor,
before/after relation, selected runtime, source receipt and required timeline
coverage. The receiver installs child state before exposing its corresponding
emissions to handlers. Child initialization may cause the subsequent receiving
work specified by Contracts; the host does not synthesize an extra external seed.
An exact operand and a latest snapshot with the same business fields are not
interchangeable evidence.

Historical authority and admission use the original receiving before-state at the
selected full-key position, including the appropriate authority/access histories.
Later grants, revocations, topology or document versions cannot retroactively
authorize an earlier input. A source's successful independent result survives a
receiver's authority denial or application failure. The receiver retains the exact
obligation and last stable result for retry. A rebase freezes the ordered affected
source scopes and target positions; it cannot silently skip a gap, mix epochs or
replace frozen views with ambient latest state. Unknown delegation is rejected;
Mandates is an optional separately selected protocol, not a dependency of this one.

### 14.4 Terminal closure

Once the root is terminated, direct PROCESS-equivalent LIVE receiving is rejected
as specified by Contracts. Finite HISTORICAL receiving obligations already frozen
before terminal closure may still be discharged without external seeds. The host
MUST NOT create a new rebase or attachment goal merely because a child later
advances, nor keep chasing an unfrozen latest child position.

Closure requires positive evidence: the exact terminal head equals its last stable
document and position; a committed stable history row seals that same document,
position and sequence number; and no frozen attachment or rebase goals remain.
This sealed prefix, rather than worker state or a terminal Boolean alone, permits
the terminal owner to satisfy later dependency readiness checks. Missing or
contradictory evidence waits or fails explicitly. Subscriptions may then be retired
without losing frozen work. The parent-terminal-at-20/child-at-30 case retains the
same parent epoch, position and stable document when these conditions hold.

### 14.5 Input dispositions and Dispatch

Hosts retain a disposition for each exact original entry and each applicable
receiving channel lifetime. Nonmatching/addressed-elsewhere input is INAPPLICABLE;
it is not a fabricated Contracts invocation. Eligible input carries its verified
admission projection into Contracts. Missing history/content is WAITING; an
established read-access deficit is PENDING_ACCESS. Malformed input, contradictory
evidence and deterministic execution failure remain distinguishable.

Dispatch policy decisions come only from the selected Contracts completion. A
validated denial is reported with standard code `DISPATCH_REJECTED`; authored
reason strings and allow/deny rows remain in ordered details with their native
delivery identity. An empty or arbitrary authored reason cannot replace this code.
For one delivery any false decision denies its handler work; all valid policies
still run. An addressed operation whose delivery is denied reports
`DISPATCH_REJECTED`. Raw or mixed inputs with both allowed and denied deliveries
report `PARTIAL`, retaining every delivery's disposition and allowed progress,
including deliveries without policy rows. Each denied delivery still carries
`DISPATCH_REJECTED`; an aggregate never changes the native Contracts status.
Raw external events follow these same rules; no Operation Request is required.
The enclosing Contracts status can remain APPLIED and retain child/native progress.
External denial is consumed only on enclosing commit. Later execution error or gas
exhaustion rolls back the whole tentative Contracts attempt, including tentative
checkpoint/child installations, but not independent source commits.

### 14.6 Exact native channel binding and admission commitment

The executing profile registers the exported Timeline Channel type against this
Coordination rules identity. Its binding is `role: external-channel`,
`header_fields: [timeline, actor]`, `body_fields: []`,
`namespace: coordinationTimeline`, `tariff: [[accept, 1]]`,
`inherits_to_subtypes: false`, `peer_fields: []`, `meter_mode: live`.
The profile also preselects the published Dispatch binding when policies may be
authored later. Merely mounting another package does not add an executable role.

Public Timeline Channel uses the same rules identity and `external-channel` role,
with `header_fields: [provider, url]`, `body_fields: []`,
`namespace: coordinationPublicTimeline`, `tariff: [[accept, 1]]`,
`inherits_to_subtypes: false`, `peer_fields: []`, and `meter_mode: live`.
Its source is the exact Signed Timeline with that provider and URL and
`publicRead: true`; it accepts authenticated entries without a holder-actor filter.
It confers no additional write or business permission. Both exact native channel
bindings are selected before initialization in the non-timer executing profile.

Timeline admission first authenticates exact ranges and verifies history against
the original receiver. The closed returned record contains `snapshot`, `entry`,
`timestamp`, `runtime`, `decisions`, `assessments`, and `operationAudience`.
The first three values identify that original snapshot and entry/time; `runtime`
is the complete selected binding record. A decision key is the compact JSON array
`[member, document, channel, generation]`; its value is a Boolean. Assessments
are ordered by member then channel in Contracts code-point order and each has
exactly `member`, `document`, `channel`, `generation`, `disposition`, and `reason`.
`operationAudience` maps each participating member to its addressed Boolean.
All validated assessments, including negative decisions, enter the Contracts
canonical admission commitment. Credentials, signatures, transport pages and
local cache/capability identifiers do not. The supplied range evidence alone is
not an authority decision. A missing host history verifier fails explicitly.

The optional Timeline Entry `onBehalfOf` operand is an exact authenticated claim.
It grants no authority by itself. Interpreting it requires a separately selected
authority protocol and its historical evidence; unsupported claims are rejected.
Coordination does not require Mandates or define a competing Authority type.
