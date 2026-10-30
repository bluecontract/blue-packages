# Mandate clauses

This unpublished candidate requires the exact `blue-mandates@0.3.0-preview.1`
initialization-aware authority edition. It reuses the Clauses installer and
Connections planner; it does not supply a separate Business compiler.

`MandateClauses/Mandate with Clauses` installs its clauses on first native
initialization. The resulting Pending document is reviewed through the standard
exact-version `approveMandate` operation. No amendment entry point is exposed.
Core freezes the installed program and `clauses` configuration before owner
approval. Scope and other execution state remain mutable only through that
approved program. Existing Mandates retain their original authority edition.

Identity checks use `/contracts/initialized/document`, the native marker's
reference to the pre-initialization document. They do not hash the Mandate's
current state or retain a duplicate identity field. The entry's
`onBehalfOf.mandate` already points to that pre-initialization document; the
referenced initial content itself does not contain an initialization marker.

The package also requires the optional `blue-processing-event-source` capability.
Attribution reads `processingEventSource/onBehalfOf/mandate`, preserving the exact
source reference instead of adding the authority field's contextual schema. A
runtime without this capability must reject the package before execution.

## Composition

| Clause | Configuration and effect |
| --- | --- |
| Document Scope Clause | Qualifies an initialized document against `parameters.documentPattern` or a snapshotted `bindings.pattern`; registers it in the collection at `bindings.documents`; adds exact operation scopes from `parameters.grants`. Each scope rechecks the document pattern at execution. When `bindings.budget` is supplied it also checks that shared usage limit; an omitted budget means no usage cap. |
| Usage Limit Clause | Initializes the counter at `bindings.usage` with `parameters.limit`. Its `record` connection observes the chosen successful effect and counts only this Agent using this exact Mandate. The configurable key deduplicates effects; the default identifies the original processing event. |
| Mandate Termination Clause | Its `terminate` connection emits native termination when the approved workflow, local change or embedded event condition holds. Termination clears scope immediately, without draining in-flight work. |

For example, an Order Mandate can use a pattern with shoe size 40 or 41, grant
`owner/approve` on each qualified Order, and share a limit of ten across all those
scopes. Registering eleven qualifying Orders is permitted: registration is not a
reservation. Only ten successful approvals under this Mandate may spend the
allowance. An owner approval or the same Agent acting under another Mandate does
not count. Observing the shared counter can optionally terminate the Mandate at
ten; otherwise its scopes remain present but cannot authorize further approvals.

An embedded producer can supply candidates through a Connections `on: embedded`
or `on: collection` connection. Set `parameters.requireAttributed: true` when only
results produced by this Agent under this Mandate may become new targets. The
document's birth mechanism is separate from qualification: bootstrap,
prepare/provide and an embedded factory still yield initialized documents.

`parameters.embedDocuments` defaults to `true`: the registered collection is
embedded, so independently registered Orders remain live native dependencies.
Set it explicitly to `false` when an already embedded producer supplies both
the candidate and the successful effects. The registry then retains qualification
snapshots, while the producer remains the live observation path. For example,
Mandate → Outreach → Prospect needs no additional Mandate → Prospect edge.
Connect Usage Limit to Outreach's committed result event in that composition.
Registration, exact Agent/Mandate attribution, operation scopes, current target
validation and the shared limit are unchanged. Only Boolean values are accepted.

This option does not acquire access or promise live updates to a registry
snapshot. The reviewed configuration must supply the live observation path.
The current Core experiment cannot attach a second edge to a Prospect born in
that same causal event: it waits for source history preceding the document's
birth. That Core correctness issue is deferred; default embedding is still used
for independently registered Orders.

Qualification uses actual native content and access; a matching description or
an arbitrary client-supplied document ID does not substitute for them. The host
alone grants no operation. The reviewed composition must choose meaningful
successful effects, deduplication keys, qualification patterns and termination
conditions. This is an unpublished candidate; see the Core composed-Mandate
tests and application qualification records before enabling a particular flow.

## Optional usage budget

Preview edition 0.1.0-preview.2 separates exact document qualification from a usage
cap. Omit `bindings.budget` only when the owner-reviewed permission intentionally
has no successful-use limit, for example continuing application tracking on
children of one embedded initiative. This does not widen the target set or bypass
Active status, the approved document pattern, actor checks or request validation.
No fake counter or large sentinel allowance is created.

When the binding is present, the existing behavior remains mandatory: the pointed
state needs an integer `limit`, and every generated scope checks `used < limit`.
A missing/malformed bound budget fails registration; it is not treated as an omitted
budget. The separate Usage Limit Clause continues to count the configured committed
effects. Existing bounded research/send compositions keep their explicit binding.

This is not a new child-provenance mechanism. Producer observation already supplies
the exact initialized document; `requireAttributed` independently determines whether
the producing Agent and Mandate must match this authorization.
