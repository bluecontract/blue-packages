# Independent owner scheduling — `independent-owner-prefix/1`

**Selected host scheduling policy for this candidate.** This document deliberately
supersedes strict affected-set-wave scheduling in the predecessor engine design
and its Coordination receiving-failure paragraph. The legacy `waves` record name
is retained for storage compatibility; it no longer reserves acyclic consumers.
Language, BEX and Contracts algorithms, gas tariffs, application types, provider
signatures and immutable historical receipts are not redefined.

This is an explicit Coordination **scheduling-policy correction**, not a claim
that all operational observations match the old strict-wave scheduler. The
engine context records `scheduling: independent-owner-prefix/1`. Existing contexts
cannot silently opt into it. The signed protocol catalogue remains unchanged. This policy is consolidated
into the 2026-09-25-independent-owner-1 Coordination publication and its release
manifest binds the exact policy bytes. The immutable protocol resource retains
its predecessor identity. Engine contexts bind both that catalogue and the new
scheduling policy; the Workbench uses a separate workspace directory.

## 1. The rule

A document waits for its own required inputs, not for the documents that consume
its output. Each successful step publishes its exact state and ordered output
batch, then makes that result available to its direct containing documents.
A producer may start its next eligible step while those consumers are behind.

For `D1 -> D2 -> D3`, arrows mean “embeds.” After D3 completes E10, D2 may consume
that completion even while D3 processes E20. D2 must not use E20's state when
processing its own E15. It selects the exact E10 history position, processes E15,
then selects E20. D1 has the corresponding independent ordered obligation for
D2's results. There is no requirement that D3 first drains its backlog or reports
READY, and no requirement that D3 waits for D1 or D2.

## 2. Durable worker loop

```text
on entry/source evidence change:
    persist a newer requested generation for relevant subscribed documents
    do not restart an already owned valid attempt

worker:
    deliver some durable completed-step wake notices
    claim one due document, with a fenced lease
    read its authoritative state and actual dependency graph
    determine its earliest currently required external input or child successor
    prove that no required earlier prerequisite is missing
    if not proved: record the wait and release the CPU/claim
    otherwise: execute that one step and publish its complete result atomically
    retain a durable wake notice for direct consumers in the same publication
    acknowledge only the generation captured by this claim
    keep due work when a newer generation/backlog remains; release the claim
    let another worker or the next queue turn choose the next ready document
```

This implementation yields at each step; it does not retain a worker until all
backlog is drained. With multiple configured workers, a source's next step and
a consumer's preceding step can overlap. With one worker, they interleave fairly
through the same durable queue. A wake is a hint, never a substitute for history,
completeness or authorization evidence.

## 3. Ready for K is not globally READY

The full ordering key retains the protocol's timestamp and source/event ties.
A receiver considers its own earliest eligible external entry and the next
contiguous retained completion for each active occurrence. It selects the
least currently required key, not any later item that happens to be ready.

Readiness for K means the relevant source and receiving histories account for
all required earlier work (including K when the receiver needs that completion).
A sealed source position at or beyond K can establish the processed prefix
while a later source step is active. The receiver still selects its exact next
predecessor; a newer source head cannot replace it. Otherwise verified source
coverage, examined progress, pending entries, attachment/rebase goals and child
successors establish whether that prefix is complete. Missing evidence is not
empty history. Same-time candidates use the complete ordering key.

A changing `work` row, lease renewal or future diagnostic is not semantic
pre-action authority evidence. Authority verification continues to inspect the
exact approved program, strict pre-action history, source coverage and every
unresolved earlier obligation. Polling by a consumer cannot invalidate an
otherwise justified producer publication merely by changing its worker status.

## 4. Exact history, not latest

The consumer's occurrence carries its selected source identity and generation.
The next source position is contiguous. The outcome and exact source metadata
come from that retained version, not the source's mutable current head. Different
original causes are not merged merely because historical activation gives them
the same effective receiving boundary.

`positions.stableNumber` identifies a published sealed prefix even while a newer
attachment/rebase position is provisional. Historical content does not silently
become a live alias. A genuinely new occurrence does not inherit retired pending
work. Removed occurrences are absent from subsequent receiving selection.

For a LIVE original cause, existing Contracts live-application machinery handles
the exact child completions and the receiving document's matching external
handlers together once. Historical receiving uses the existing receiving path.
There is no new public Contracts input or a second operation request.

## 5. Notification and failure boundaries

Source publication stores its successful history/receipt and a completion notice
in the same conditional atomic store publication. It does not read or modify
acyclic consumers' work records. A separate idempotent notice transaction finds
current direct reverse memberships in the same engine context and wakes those
consumers. Deleting the notice and registering those wakes are atomic together.
A crash before notice delivery cannot lose the retained result. A newly attached
consumer discovers existing backlog through its own occurrence registration.

A completion with no emitted event still carries state and wakes consumers.
Terminal examined/no-match progress and newly checked completeness can wake
consumers without fabricating a successful business checkpoint.

A deterministic receiving error belongs to that receiver; a host interruption
is HostIncomplete. Its producer's committed result remains successful, and the
acyclic producer may continue. A consumer of the failed receiver waits for its
actual unresolved history. Explicit retry reuses retained source results and the
same allowance. It does not repeat an independently committed source operation.

## 6. Cycles and changes to topology

Owner reservation is the source's actual strongly connected component in the
captured forward graph, not its reverse transitive closure. A singleton without
a self-loop is independently owned. A true cyclic owner group still uses the
existing Contracts component turns, exact member identities, previous-completed-
round reads and atomic owner publication. One-way consumers outside that group
are not reserved.

All actual written owners remain fenced against their exact predecessors,
control/lease and reservation state. Dynamic graph changes can require new
owners and must revalidate that acquisition. New actual owners discovered during a cycle join are reserved conditionally
before repeating the tentative turn. This prevents a waiting peer’s polling
from starving that acquisition; the peer’s active attempt remains fenced at
publication. A current-view cycle creation/split is covered by real-processor fixtures. This package does not claim
an exhaustive proof of every historical divergent-version cycle join. A historical duplicate-owner join that cannot preserve the retained origin key
fails with `AMBIGUOUS_LINEAGE_ORIGIN` and the explicit
`UNSUPPORTED_HISTORICAL_OWNER_JOIN` limitation. It publishes no business result.
Other unproved joins wait on their specific dependency/owner evidence; it does not
justify reserving unrelated acyclic ancestors globally.

## 7. Migration

New contexts select this policy explicitly. Old contexts are rejected rather
than silently clearing their reservations or losing retained receiving failures.

`blue_coordination.engine.migration.migrate_quiescent_context(store, hub,
context=...)` implements an **offline, idle-context** migration. Stop all old
worker processes and keep exclusive administrative ownership while using it.
It refuses pending registration, active claims, reservations, failed work,
provisional histories and attachment/rebase goals. It preserves exact documents,
history, receipts and occurrence generations, fences stale claims, adds stable
position pointers and wakes backlog under the new policy. Repeating a completed
migration is idempotent.

This is not a rolling migration for an in-flight old wave. Such a wave must be
completed with the old scheduler or migrated by an explicitly verified tool that
retains every source receipt and pending occurrence; no such general conversion
is claimed here.

## 8. Preserved limits and boundaries

Contracts remains `process(document, event, eventTimestamp)`, maximum/default
100,000 gas with the existing member-local/shared ledger and all prior gas
representation and charge-before-work fixes. Local child Document Updates stay
local; parents observe sealed completed states/event batches. Provider/authority
validation, context/access scoping, generalization, paging, uncertain publication
and exact identity rules remain. No PostgreSQL transaction requirement, new
public Channel Input, global READY barrier or ecosystem-wide gas pool is added.

## 9. Acceptance cases

The added tests exercise two paused ancestors with an advancing child; receipt
parity under delayed/interleaved consumption; parent progress while a later child
turn is held open; an earlier unfinished child blocking a later parent input;
merge of two child histories and a parent entry; durable notice recovery; and
continued source progress after receiver HostIncomplete. The updated failure
tests require a successful source to continue after a deterministic receiver
failure. Existing storage/lease, source/authority, historical attachment, dynamic
cycle, shared-diamond and recovery tests remain part of qualification.
