## 15. Portable executing-host obligations

### 15.1 Conditional publication and fencing

A host binds each attempted publication to its exact input head, owner set,
selected runtime, relevant source-set revision, frozen goals and dependency
positions. Immediately before commit it MUST establish that these still match.
An ownership token/fence must exclude an expired or superseded worker from
publishing. A changed read set causes retry from a coherent view, not merging
tentative results. For an actual cyclic unit the condition covers the whole unit.
No particular SQL schema, lock algorithm, journal or machine allocation is required.

One atomic durable publication contains all owned result heads, history rows,
receipts, input dispositions/checkpoints, outstanding goals, dependency changes
and output work needed to recover the next step. No observer may see a result
head whose required evidence or history predecessor is absent. An interrupted
attempt before publication exposes none of its tentative effects.

Notifications are hints. The durable obligation/outbox is authoritative. Delivery
can be retried; occurrence identity is the deduplication key, never message-content
equality. Receipt publication and durable output intent are atomic. Acknowledgment
cannot precede successful delivery. Restart reconstructs undispatched output and
unfulfilled receiver obligations without rerunning committed business operations.
Conditional retries must neither duplicate committed occurrences nor lose them.

### 15.2 Storage, admission and restart

Publicly uploaded content and replay proofs are untrusted. Verify exact content,
provider signatures, contiguous ranges, completion/profile commitments and all
logical context before granting an in-process capability. A locally protected
completion reader may rely on its own authenticated atomic publication provenance;
an arbitrary hash, read-model flag or caller-supplied JSON is never such provenance.
Every protected read still verifies the exact requested history/runtime association.

Replay evidence contains sufficient actual initial content, source ranges,
history positions, authority positions, assessments and Contracts evidence to
replay its target. Its container or self-reported receipt does not establish
authority. Unsupported portable receiving, historical cycle joining, restart or
migration paths fail explicitly rather than accepting a weaker projection.

Source acquisition may retain verified pages privately under one exact checkpoint;
public completeness advances only after the complete authenticated chain to its
selected anchor has been verified. Replacement checkpoints cannot splice partial
chains. Durable stores preserve input positions, contiguous history, frozen goals,
outbox and selected profile across restart. A store claiming only process-local
durability must state that limitation and must not advertise crash recovery.

The host keeps account/tenant storage keys, credentials and private signing keys
outside Blue business content. Reads, subscriptions, capability caches, protected
history lookups and retry work are scoped to their authorized account. Knowing
a BlueId or another account's public handle does not authorize private content.
Sharing immutable public verification results is permitted only when this does not
cross access boundaries or change semantic outcomes. Timeline read access and
authority to invoke business operations remain separate.

### 15.3 Operational incompleteness and retained editions

The selected Contracts maximum/default is 10,000,000. Hosts preserve charge-before-
work, member budgets, admitted-prefix gas, first rejection and atomic rollback.
Physical cache state, cancellation, resource exhaustion or a missing dependency
does not become a successful semantic result. A host interruption retains the last
stable state and exact pending input as HOST_INCOMPLETE; retry uses the same logical
policy. It does not publish a partial gas receipt or silently raise the budget.

Every saved context carries its exact edition/profile. Reopening it selects that
edition or reports explicit unsupported history. New-context defaults cannot
rewrite old context identities. Migration, if implemented, is a separate explicit
operation with its own evidence; installing another runtime is not migration.
Old provider and execution archives remain immutable and are not aliases for this
publication.
