## Deterministic execution context and traversal (2026-10-17)

This edition retains the 10,000,000 shared default and maximum, charge-before-work,
member ceilings, admitted-prefix gas, shared-cap tie precedence and atomic rollback.
Accepted charge histories remain excluded from canonical final-gas evidence.
The following refinements govern this edition; historical publications remain
unchanged and are not compatible substitutions for this specification.

### Ordering domains

| Domain | Required order |
| --- | --- |
| Language canonical objects and BlueIds | Existing unsigned UTF-16 Language order |
| Typed enum scalar keys | Unsigned UTF-16, `Language.ordered`; outer effective group order unchanged |
| Contracts declarations, members, channels and error scans | Unicode code points |
| Contracts semantic pointer comparisons | Decoded-segment tuples, each segment in code-point order |
| Stored graph edge/vector serialization keys | `(source, raw pointer)` in code-point order, as in the executable reference |
| Private Contracts JSON object keys | Unicode code points; this is not Language canonicalization |
| Explicit source, emission, checkpoint and batch arrays | Their prescribed sequence; never sorted after execution |
| Runtime type-slot alias precheck | Present slots in `itemType`, `keyType`, `type`, `valueType` order |
| Count-predicate metering | Present `minItems`, `maxItems`, `minFields`, `maxFields`, `minLength`, `maxLength` |

Every traversal affecting gas, a selected error, a commitment or output sequence
uses its specified order, independent of map insertion, process seed, locale,
worker completion or cache state. The metered bottom-up declaration merge begins
in raw-key code-point order and preserves its `(order, key, typeID)` comparisons.
Enum ordering adds no physical-sort charge and preserves typed scalar keys,
duplicate/group elimination, first effective group occurrence and primitive
category/payload comparison stopping behavior. Source enum lists are unchanged.
Text count comparisons remain before enum examination; List counts remain before
item traversal. Language validation remains authoritative for exact admission.

Private canonical JSON accepts null, Boolean, arbitrary exact Integer, Text,
sequences and Text-keyed objects. It rejects floating and Decimal carriers.
The private encoder, including streaming/digest paths, uses the executable
`canonical` function's bytes and error rules. Language/BEX numeric and UTF-16
identity rules are unchanged.

### Complete invocation identity

Successful preparation freezes verified logical admission context against the
original receiver before child installation, allocations or local turns. The
private projection is keyed by exact binding identity and contains only the
binding verifier's closed semantic result. Verifiers must reject unrecognized
fields and must exclude signatures, credentials, local capability tokens,
physical cache state and other proof-encoding details. Arbitrary submitted
evidence is never made authoritative by hashing it.

The ordinary `contracts.invocation/2` record is closed over `input`, `event`,
`timestamp`, `gas`, `release`, and `admissions`. The receiving
`contracts.receiving/2` record is closed over `input`, `mode`, `sources`, `policy`,
and `admissions`; mode is exactly HISTORICAL or LIVE. Sources retain the supplied
validated descriptor sequence. HISTORICAL has empty admissions. The original
snapshot commits the exact active runtime profile. Both records are sealed after
admission verification and before invocation-derived allocations.

Before verification succeeds, validation and metering failures use a distinct
`contracts.attempt/2` or `contracts.receiving-attempt/2` identity committing the
same selected inputs but no purported verified admissions. The failure outcome
and receipt commit the diagnostic and admitted gas prefix. The attempt identity
is not a claim that unverified evidence has semantic authority. Preparation keeps
its existing charged preflight order. The public process interface remains the
three-input document/event/timestamp interface.

### Terminal receiving

After the required original-input validation, admission and seed checks, LIVE
rejects an already terminated root with the direct PROCESS terminal disposition;
it does not install later child results. HISTORICAL may perform exact seedless
structural adoption for finite previously frozen host obligations. Active
receivers retain historical callbacks. Structural installation into a silent
terminated member of an actual live cyclic unit remains permitted and does not
reopen that member's external handlers.

### Exact active profiles

Runtime availability does not activate execution. The selected active binding
sequence is fixed before initialization and must exactly match snapshots,
received source completions and chunks. No implicit additive promotion is
defined. New binding authors order validated type IDs by ASCII bytes and tariff
counter names by Unicode code points, preserving specified header/body/peer
field sequences and rejecting duplicates. This normalization is not execution
work. Retained binding arrays are never normalized during restore.


### Dispatch role and native integration


### E1. Role, ownership and binding

Contracts defines the `dispatch-policy` role and the hook below. The concrete Document Dispatch Policy type is a subtype of the selected Contracts/Compute and carries this specification as its governing rules. Runtimes select its exact published type and rules IDs.

Select the binding before document initialization. Preserve the concrete role's current non-inherited exact type support, no header/peer fields, `body_fields` sequence `expr, do, constants, functions, entry, definition`, live meter mode and `dispatchPolicyCheck` price 1 in this edition. The namespace is `documentDispatchV1`; tariff is the ordered vector `[["dispatchPolicyCheck", 1]]`. Binding type_id and semantics_id are respectively the published policy type and this rules Text.

The concrete policy remains a subtype of `Contracts/Compute` and is admitted as an exact top-level `/contracts` `dispatch-policy` declaration. Arbitrary subtype inheritance or nested executable roles do not acquire this policy behavior.

### E2. Delivery hook and immutable context

Run the gate after existing liveness checks, native work-occurrence recording/charging and channel-existence checking, before any handler-candidate matching for that delivery. The local document includes completed child results required by the schedule. There is no new implicit parent lookup.

Use the ordinary Compute context plus a runtime-owned closed object `{kind, channel, operation}`. `kind` is one of EXTERNAL, TRIGGERED, EMBEDDED, UPDATE, INITIALIZATION, TERMINATION; `channel` is the selected exact local key; `operation` is the natively selected operation or null. Never derive native kind from payload strings. Original processing event, current payload, current declaration, explicit timestamp, call, scope and no-prior-step-results follow existing Compute rules; preserve initialization's absence semantics.

### E3. Order, purity and errors

If no policies exist, no extra policy sorting pass or charge occurs. Otherwise, freeze the local declaration map, execute the metered Contracts sort over **all** declarations, then filter policies. Evaluate every policy in that order. Charge its check before evaluation. Require no staged document changes, events or termination effects. Require a closed result `{allowed: Boolean, reason?: Text}`, without coercion.

A valid false does not skip later policies. A BEX failure, gas interruption or malformed result interrupts via its proper error path. Preserve the validation precedence: evaluation/interruption; effect rejection; record shape; Boolean field; optional Text reason. Current matching codes are `EFFECTFUL_DISPATCH_POLICY`, `INVALID_RECORD`, `INVALID_DISPATCH_DECISION` and `INVALID_DISPATCH_REASON`. If all policies allow, ordinary handler scheduling performs its separate prescribed sorting pass. Physical reuse must not remove logical gas.

### E4. Denial and checkpoint

A valid denial skips handlers for that delivery. It does not cancel independent child progress or all other deliveries. A denied external seed is consumed/checkpointed **if the enclosing attempt commits**. Later access restoration does not replay it; a caller submits a new occurrence to retry. Thus Contracts may return APPLIED while the requested business operation is denied. A later error/exhaustion rolls back the enclosing tentative attempt's checkpoint/state, while previously sealed independent source results survive.

Missing resources are incomplete work, not a false policy result. Pre-Contracts authority rejection is also distinct and must not invent a successful native checkpoint.

### E5. Committed evidence and reporting

Add `dispatchDecisions` to the local-completion schema. It is present if and only if at least one policy decision was validated in that completed local turn; otherwise it is omitted. Its order is native delivery order, then canonical policy order. Each row contains:

`delivery`, `policy`, `declaration`, `channel`, `kind`, `operation`, `allowed`, `reason`.

`delivery` references the existing `contracts.work/completion-1` occurrence identity; it is not a second event wrapper. `declaration` is the policy declaration's exact BlueId. `operation` is Text or explicit null. Normalize absent `reason` to empty Text for allow and `DISPATCH_REJECTED` for deny. Validate field types and closed records. Only validated decisions in a completed local result enter this successful-completion sequence; failure evidence follows the selected existing failed-attempt schema and never fabricates a completed decision.

Bind this field through every completion, chunk, source-receiving, export/restore and receipt verifier. Detached decision rows do not grant authority.

Each `delivery` must identify a work occurrence in the same local turn/member. `channel` and `kind` must match that occurrence; `operation` must match native selection; `declaration` must match the selected policy. Reject missing, duplicated, reordered or mismatched decisions. Record-shape checking and hashing alone do not establish this correspondence.

Coordination derives per-delivery rejection information from these rows. Preserve one row per delivery/policy, including operation-less raw external events. For a requested operation's aggregate report, a denial on its addressed delivery produces the standardized disposition code `DISPATCH_REJECTED`. Authored reasons such as `DOCUMENT_ACCESS_UNAVAILABLE` remain in the rejected decision details in canonical order; they do not replace that code or the native Contracts `APPLIED` status. Unrelated allowed child/delivery work remains represented as committed. For raw events or mixed deliveries, per-delivery evidence is authoritative and aggregate labels must preserve partial allowed progress. For an addressed operation report `DISPATCH_REJECTED` if any decision on its addressed delivery denies. For a raw or mixed input retain ordered per-delivery decisions and report `PARTIAL` when allowed work and denied work coexist; an aggregate does not erase committed progress.

### E6. Activation remains authored

Keep Timeline Access as a provider-controlled document; update both permission lists before its ordinary `Coordination/Timeline Access Updated` event. Activation uses the existing Embedded Node Channel and completed child state. Recovery requires the true native EMBEDDED path and the authored access-control channel/instance checks. Direct approvals, amendments and business requests remain non-executing while required access is lost; preserve approvals and channel history. Do not add the removed Embedded State Channel/EMBEDDED_UPDATE mechanism or native business-state hooks.



### Constructor reference prerequisite order (2026-10-17 correction 2)

A metered Language constructor callback MUST NOT expose host-set iteration as
logical gas order. Runtime normalization constructs inline type and specification
slots first in the already prescribed input-key order and passes their established
exact references to Language. During each resulting node construction, collect
all reference-only `remember` occurrences; before establishing the next node,
pay their unchanged direct identity prerequisites in exact BlueId ASCII order.
Preserve occurrence multiplicity. Flush any remainder before the constructor
returns. Sorting this inventory adds no gas. Node construction and validation
remain in their existing order, with charge-before-work and atomic rollback.
The same rule applies while synthesizing a multi-contribution captured recipe.
It does not alter Language identity, admission, refinement or output values.

This corrects a further observable ordering defect in the first deterministic
candidate: normalization of a Dictionary with Integer `valueType` completed with
the same total gas but, with budget 245, failed at admitted gas 245 for seed 0 and
234 for seed 7. The original candidate and failed observations remain evidence.
The four-slot runtime alias check retains its separate explicit slot order.


### Effective document reads and staged overlays (2026-10-17 correction 3)

Direct document reads, selected exact subviews and ordinary BEX member/item
access MUST use the same effective collection interface. The presence of
`$resultValue` elsewhere in a Compute program MUST NOT change an unrelated
`$document` observation. In particular, a non-core `type` member is a captured
effective reference view, not an ordinary object whose sole member is `blueId`.
Its Blue output remains the finite exact reference. Contracts, labels and
ordinary members use their existing effective visibility; hidden core metadata
does not become an enumerated business field. Scalars use BEX scalar semantics.

Charge `objectMemberRead` once before each attempted exact object member access,
including a missing member and the special type/contracts/label members. Charge
`listItemRead` once for a selected in-bounds exact list item. BEX validates index
syntax and bounds before selecting an item; an invalid or out-of-range index
does not charge an item access. Preserve BEX value-pointer parsing, including
both empty and slash root paths, non-NFC field spellings and arbitrary-length
index text. Contracts graph/semantic pointer validation remains a different
boundary. Split reads retain the same invocation manifest inventory and the
same per-access tariffs; they cannot bypass special-member charges. These are
intentional logical-count and effective-projection corrections, not only a
physical optimization. Prices, maximum budget and rollback remain unchanged.

Every selected exact subview, and every saved Compute document-read callback,
retains its captured resolver together with the invocation logical ledger.
Opening through that ledger uses the captured source, never a later refreshed
processor resolver. A staged overlay copies only changed ancestors; untouched
exact children keep that captured context. Missing evidence propagates as the
existing resource outcome. Finite wire views and exact-transfer accounting are
not effective document views and remain unchanged.

Staged authored BEX dictionaries are not exact host capabilities. The existing
document overlay pointer interface can interpret a one-field `blueId` dictionary
when continuing through it, using the captured resolver and the same logical
ledger. A terminal such dictionary, or its explicitly requested `blueId` field,
remains authored data; generic BEX access to that dictionary remains ordinary
BEX access. The direct/split equivalence above applies to exact effective views,
not to an assertion that arbitrary staged dictionaries have already undergone
Language normalization or admission. No trusted provenance is inferred from
reference-shaped authored data.
