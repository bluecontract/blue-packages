# Root clauses and amendments

## Composition

An `Agreements/Agreement` has two distinct authenticated channels in `channels.A`
and `channels.B`, an exact-identity `clauseTypes` allowlist, a `clauses` object keyed
by stable clause names, and business `parameters`. Clause types extend
`Agreements/Clause` and declare:

- `parameterDefinitions`: kind, optional min/max, enum and required nested keys.
- `bindingDefinitions`: `state`, `contract`, `channel` or `field` slots.
- `stateDefinitions`: initial values and kinds for state owned by this clause.
- `features`: templates (or whole workflow parameters), explicit fills and constants locations.
- `freezeBindings`: boolean state bindings which prevent material configuration changes.

On initialization, a nonempty explicit `clauses` object wins. Otherwise `initialClauses`
is copied as the default recipe. An empty Agreement is valid and can receive its first
clause later. Caller-supplied `clauseRuntime` or preseeded owned state is rejected.
Generated runtime records are framework state, not authoring input.

Parameters use exactly one source: `{literal: value}`, `{from: /parameters/path}`,
or `{field: /existing/path}`. `from` takes a snapshot from Agreement parameters at
installation. A `pointer` parameter with `field` retains an absolute JSON pointer;
the workflow explicitly reads it when invoked. A `field` binding likewise refers to
existing document data without claiming ownership. Escaped JSON-pointer segments
(`~1` and `~0`) are supported for existing field references. State and contract
bindings use simple root field names and may not target framework-reserved fields.

## Amendment API

Both `amendA` and `amendB` execute on their corresponding authenticated party channel.
The framework does not require two-party consent to propose an amendment. The mutual
activation clause resets pending approval when terms change, and freezes material
changes once activated, declined or terminated.

```yaml
expectedRevision: 1
changes:
  - op: add
    key: reporting
    clause:
      type: MyClauses/Reporting Clause
      parameters:
        threshold: {literal: 100}
      bindings:
        count: /reportCount
        report: /contracts/report
        channel: partyA
```

Use `edit` with a complete replacement clause, or `remove` with only its key. A
request can combine several distinct keys with a complete replacement `parameters`
object. Alternatively supply the complete replacement `clauses` object; do not also
supply `changes`. `expectedRevision` is mandatory and must equal
`/clauseRuntime/revision`. Duplicate keys, malformed requests and stale revisions fail.

The operation validates and installs the final pair of clauses and parameters as
one transaction. Nested document-update listeners do not install intermediate
configurations. Any rejection, including gas exhaustion, rolls back source, state,
generated contracts and emitted events. The framework advances revision once for a
material installation. An identical configuration is a no-op: revision and approvals
stay unchanged and no installation events are emitted.

Example through Java's Coordination API after registering an Agreement:

```java
agreement.call("amendA", Map.of(
    "expectedRevision", 1,
    "changes", List.of(Map.of("op", "remove", "key", "reporting"))), 100L);
var committed = agreement.awaitEpoch(1, Duration.ofSeconds(10));
```

## State and dependencies

Editing parameters or renaming an operation preserves owned state. Removing a clause
removes its generated contracts and retains its state with `retired: true` ownership
metadata. Readding the same clause key, type and state binding resumes that state.
A different owner or type cannot adopt it. Rebinding existing owned state is rejected:
state migration and destructive cleanup need a separate explicit design.

Every active `state` binding must have an active owner. Remove dependent clauses
together, or reconfigure their dependencies in the same batch. Retired state does not
satisfy an active state dependency. A live `field` binding is intentionally unowned;
its target must exist at installation and its continued validity is the author's
responsibility. Removing all clauses is allowed if no freeze condition is set.

Generated contracts are installed with one replacement of the contracts map,
using BlueId references to retained contract nodes. Unowned root contracts are retained.
This prevents intermediate channel/handler inconsistencies and avoids repeatedly
copying and validating whole workflow bodies. The installer still validates the full
active clause configuration on amendment; amendment cost is not constant in clause count.

## Whole workflow parameters

A clause can expose an entire workflow as a parameter:

```yaml
name: Reporting Clause
type: Agreements/Clause
parameterDefinitions:
  workflow: {kind: workflow, type: Contracts/Sequential Workflow Operation}
  price: {kind: pointer}
bindingDefinitions:
  report: contract
  channel: channel
features:
  report:
    category: handler
    parameter: workflow
    fills:
      - {path: /channel, binding: channel}
    constantsAt: [/steps/0/constants]
```

Supply `workflow: {literal: <complete typed workflow>}` and
`price: {field: /commercialTerms/price}`. The configured feature takes the workflow,
sets its channel through the explicit fill and injects `parameters`, `bindings` and
`clauseKey` constants. Inside its Compute step, a live price read is:

```yaml
$document:
  $const: {name: parameters, path: /price}
```

The complete workflow remains data until its installed operation is called. Workflow
parameters are excluded from static Compute constants, which cannot contain executable
forms. The workflow's exact declared type is checked; its BEX body is validated by the
runtime when executed. Custom workflows are trusted business code with the Agreement's
write authority, not sandboxed plugins. Admit reviewed clause type identities; do not
allow untrusted callers to change the allowlist or write framework fields directly.

## Events

Material installations emit typed `Agreements/Clause Added`, `Clause Edited` and
`Clause Removed` events for changed clause specifications, followed by
`Agreements/Clauses Installed`. Events include the committed revision and configuration
identity; individual changes include `clauseKey`. Parameter-only changes emit
`Clauses Installed`. Listeners can match these types and react transactionally.
Business lifecycle events from mutual activation and termination remain available.

## Compatibility and qualification

This is a new immutable release, not an in-place migration. Clients must include
`expectedRevision` in amendment requests. Old publication identities remain available
under the legacy selection. New top-level packages and ROOT-CLAUSE-PACKAGES.json select
this release. Java qualification uses bundled package data, never a Python checkout.
Bounded correctness and performance results are reported in the repository's
`docs/root-clause-amendments.md`. General state migrations, untrusted-code isolation,
and an exhaustive proof over arbitrary custom clauses are outside this release.
