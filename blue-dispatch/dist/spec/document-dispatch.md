# Document Dispatch Policy — deterministic edition


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

