# Native runtime contract

The exact package, protocol, rules and exports are pinned in
`integration-selection.json`. Native MyOS enables this publication in its
agreements and mandates profiles; the standard profile remains unsupported.

| Export | Contracts role | Body fields |
| --- | --- | --- |
| Timer Channel | external-channel | none |
| Schedule Timer | step | request |
| Cancel Timer | step | request |

Steps evaluate `request` once with the ordinary BEX call/event/document/steps frame
and the same invocation meter. Effectful expressions, explicit types, missing
fields and unknown fields fail. The resulting typed request is an ordinary staged
event. Direct Trigger Event and Compute emissions follow the same commit path.

The committed event occurrence identifies a registration. Registration, keyed
replacement/cancellation, source state and wake-up index commit in one conditional
journal publication. A firing's resulting document, receipt and terminal timer
status also commit together. Worker leases recover abandoned attempts; replays
cannot create an extra committed firing.

The virtual Timer Source is scoped by engine context and stable initial document
identity. Its immutable Timer Entry stores source, deadline and exact Timer Fired
message. Receipts retain the entry; Contracts processes the message at the deadline.
The native Time adapter extends receipt/history input validation only for this
approved exact type. Signed Timeline rules are unchanged.

Every pending entry participates in ordinary input selection immediately. A clock
alarm only wakes the owner. Selection uses the common three-part order, current
sources, existing dependency readiness and SCC ownership. Pending child timers
prevent parents from advancing through their position. Receiving a child's
completion does not register its emitted requests again in the parent.

MyOS advances only its own timeline providers' signed closed prefixes. It serializes
that advance with admission and caps it before any prepared, unpublished entry.
External sources must provide their own proof. `completeBefore > deadline` is
required, including all ties. Host time is used for eligibility, never as a
replacement for logical event time. There is no independent EventBridge schedule
per timer and no AWS resource created per timer.

The host wakes due timers on a 100 ms scan; unavailable prerequisites retry with a
250 ms minimum alarm delay. Per-document and per-account token buckets prevent
one self-rescheduling document monopolizing workers (10 and 100 firings/second,
with bursts of 16 and 100). Pending defaults are 1,024 per document and 16,384 per
account/profile, configurable with `blue.time.maxPendingPerDocument` and
`blue.time.maxPendingPerAccount`. These are host admission/resource policies,
not a minimum logical timer interval. Over-limit attempts roll back atomically.
Restarting a process resets rate-limit bursts but not durable timer state.

`GET /documents/{sessionId}/timers` returns pending registrations, requested
microsecond timestamps, immutable entry/message/source IDs and channel generation.
Cancellation is a document operation, not an administrative timer-delete API.
Paused documents retain their timers and resume in logical order. Removed channel
generations invalidate timers. Detaching an independently managed document does not.

Adding these exact runtime bindings does not reinterpret old binding semantics.
Existing saved snapshots remain readable; introducing Time attaches the new
bindings. The engine release marker is advanced so old binaries reject a journal
containing this new input format instead of silently ignoring it.
