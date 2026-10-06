# Composable clauses — MyOS edition 3

`/clauses` is the configuration authority. A clause's exact type selects its code;
there is no per-document type registry, copied accepted configuration, retired
clause archive, or stored amendment history. Older package editions remain
immutable and existing documents continue to use their pinned definitions.

## Change protocol

An authorized operation emits `Clauses / Clause Change Requested`. Its request
contains `action: add | update | remove`, `key`, and a complete `clause` for add
or update. `requestId`, `expectedRevision`, and `expectedConfigurationId` are
optional for this single-change interface. Supply the expected values when an
edit must reject concurrent configuration changes. The operation supplies
`actorChannel`; a request cannot override it.

The host's dedicated listener processes this event through the atomic amendment
pipeline. The existing batch interface remains available: `requestId`,
`expectedRevision`, `expectedConfigurationId`, and `changes`. Batch changes also
accept the old spelling `replace` for `update`.

The outgoing clauses validate the transition; at least one outgoing amendment
authority must authorize it. Candidate clauses validate configuration and
produce plans. All validation completes before installing business changes.
Replacing a clause's implementation type is allowed when these validators allow
it. Removing the authority itself requires that authority's outgoing approval.
An accepted change emits `Amendment Accepted`; a rejected change emits
`Amendment Rejected` and leaves configuration, state, and installed behavior
unchanged. An identical configuration emits `Amendment Unchanged`.

## Authoring a clause

A clause instance has `type`, `parameters`, and `bindings`. Its immutable type
provides `hookDefinition`, a native `Contracts / Compute Definition` containing
three zero-argument functions: `validateTransition()`, `validateConfiguration()`,
and `plan()`. They read `$document` and the `clauseKey` and `mode` constants;
this avoids repeatedly identifying a large context argument. Legacy types using a context argument or exposing a root `functions` table
are also supported through a compatibility wrapper. Source lowering reads only the context fields a hook needs. Immutable types may declare `transitionUnconditional` or `configurationUnconditional` to omit a constant-allow hook; real governance and veto hooks must not use these flags. Inline instance fields other than type, parameters, bindings, name and description are discarded and never select executable code. Validators return `{allowed: Boolean, code: Text}`. A plan returns
`contracts`, `states`, and `reads`.

Hooks are pure planning code. The host discards effects from a hook that attempts
to append changes or events and rejects the amendment. Business workflows may
have effects. They have the ordinary authority of code in the document; clauses
are a composition convention, not a sandbox for hostile workflow code. Install
only code approved by the document's governance. Workflows must not directly edit
`/clauses`, `/clauseRuntime`, or another clause's generated contracts.

`Clauses / Collection Clause` provides a reusable embedding collection with an append operation, child-event reporting, and Document Update Channel reporting. Its parameters are `field`, `family`, and `operation`; `bindings.actor` names an existing channel.

`Clauses / Composable Clause` is a generic implementation: its `parameters`
contain the desired plan. Use it to supply native workflow contracts and BEX
steps directly, without publishing a new type. Reusable domain packages can
provide their own validation and build the same plan from simpler parameters.

## Channels and embedded documents

Contract contributions contain `kind` and `contract`. A `definition` contribution
installs a shared native Compute Definition for workflows to reference. Channel and handler
contributions install ordinary native Contracts definitions. Identical
contributions to the same key are shared; incompatible definitions reject the
whole amendment. A generated handler may reference a channel already declared
by the document or supplied by another clause. Host-declared contracts survive
clause removal. Generated contracts remain while any active plan needs them.

Every embedding contribution uses key `embedded`, kind `embedding`, and native
`Contracts / Process Embedded`. The host unions and deduplicates all `paths` and
`collectionPaths`, including host-declared paths. Removing a clause removes only
its exclusively contributed paths. Native Coordination manages the resulting
dependencies, child epochs, and event propagation. Removing an attachment does
not delete the independently running child or erase business data.

Document Update Channels are supported. Their paths should observe the intended
business fields. A workflow that writes back into its own observed path can
create a reaction loop and exhaust its invocation budget, just as ordinary
native Contracts code can.

## State and history

A state claim contains `path`, `kind`, and `initial`. An existing value of the
right kind is adopted; initialization does not reset it. Removing a clause keeps
its business data. Another approved clause may adopt that data, including under
a different implementation type or clause key.

Use `from: /existingField` instead of `initial` to copy existing state into a new
field when moving behavior. The old field is retained. `replace: true` explicitly
allows overwriting the destination when that clause's configuration changes;
it does not rerun on unrelated amendments. Retiring or deleting business data is
an explicit business workflow, not an implicit consequence of removing a clause.

`/clauseRuntime` holds only the revision, configuration digest, generated contract
keys, and ownership of generated embedding paths. Its empty `work` field is an
execution guard; candidate data exists there only during an atomic attempt.
Validation results and plans pass through workflow step results and never need
to be stored in the document. History lives in timeline entries, emitted outcomes and saved document
epochs, not in another copy inside the business document.

## Execution and compatibility

This edition uses the existing Language, BEX, Contracts and Coordination rules.
No native package or gas tariff is changed. Contract initialization and each
operation retain the native shared 100,000-unit limit. Local caps can lower that
budget, but cannot raise it to one million under this runtime. Large BEX programs
or self-triggering workflows may therefore reject an invocation. Processing
remains atomic, durable, and replayable under the exact pinned package code.
