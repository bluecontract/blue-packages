# Clause connections preview

Directly authored BEX, lowered by `Connected Clause` into existing Contracts and
Time definitions during the ordinary clause planning hook. There is no JavaScript
or Python business-code generator. `Hello Clause` is a tiny reusable action.

Exports: Connected Clause, Hello Clause, Hello Said, Greeting Request, Ping, and
Other Ping. The last two provide distinct nominal event types for the examples.

`Remember First Timestamp` writes the first positive microsecond value supplied
as `timestampMicros` to its `startAt` action. The author places the result with
`bindings.result` and connects sources using ordinary named bindings. The
supplied-time action also supports `recordUnavailable: true` and an optional
`bindings.unavailable` pointer for existing configurations.

Connect the primary event to `startFromEntry` to use its native processing
timestamp. A valid primary timestamp becomes the permanent result. A primary
event with no timestamp records `true` at the optional `unavailable` pointer.
An invalid timestamp records neither value.

When configured, `startFromFallback` reads a positive timestamp from the
`fallback` pointer only after that missing-primary fact. The optional `ready`
and `sourceReady` pointers each require a true Boolean. Connect the action to
the changes and events that make the original fallback publication visible,
including changes at the missing-primary pointer and any later readiness
event. The catch-up turn contributes no timestamp. Keep the result and
missing-primary paths under the clock's control.

```yaml
type: Connections/Remember First Timestamp
bindings:
  result: /clockStartMicros
  unavailable: /clockStartUnavailable
  fallback: /source/firstTimestampMicros
  ready: /activation/active
  sourceReady: /activation/accessReady
  startFromEntry:
    activation: {'on': activated}
  startFromFallback:
    sourceAttached: {'on': change, path: /source}
    sourceUpdated: {'on': change, path: /source/firstTimestampMicros}
    primaryMissing: {'on': change, path: /clockStartUnavailable}
    accessRestored: {'on': event, event: {type: Parties/Document Access Restored}}
```

The Java `ClauseConnectionsTest` builds and mounts an exact preview package from
these files against this repository's pinned dependencies. It does not add the
package to the application's default catalog. Run from the repository root:

```bash
runtime/gradlew -p runtime :blue-core-service:test --tests blue.core.ClauseConnectionsTest --no-daemon
```

Use JDK 21. The archive and observations are written under ignored
`reports/clause-connections/`. See `docs/guides/CLAUSE-CONNECTIONS.md` for the
source matrix, execution rules, complete examples, testing boundaries, and
preview restrictions. Python runtime qualification is deferred.

The `blue-package.yaml` manifest selects version 0.2.0-preview.1 for the
composition kit. This version adds explicit library-owned automatic actions,
managed embedding bindings, shared Compute Definitions, `actionResult`, and
`embed: false` for observers of already managed documents. See the companion
`docs/guides/COMPOSITION-TUTORIAL.md` for Payment and business examples.


Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.

## Activation references

Activation can name a clause instance, an action and a specific connection to
admit it before commercial activation. Connections resolves those names using
the same action selection, binding selection and channel derivation as its own
planner. For the author-facing syntax and dispatch rules, see
[Connections before activation](../clause-activation/README.md#connections-before-activation).

## Conditions on a named action

`parameters.conditions.<actionName>` adds a BEX predicate to every connection of
that action. It is evaluated after the action's original requirement and typed
arguments, before preflight or any `before`, action or `after` effects. It can only
add a restriction. A false result fails with `ACTION_CONDITION_FAILED`; an unknown
action name is rejected during planning. Omitting a condition adds no restriction.
Conditions use the action's own document and selected named sources, not an
incoming observer's state. Cross-document changes require explicit application
events when they are intended to trigger an action automatically.

## Connection profiles

A clause instance can share `params` and `when` between connections. Each
connection keeps its own event, path or workflow. A profile does not modify
action requirements or supply routing fields. Unknown names and mixing a
profile with local `params` or `when` are rejected.

```yaml
parameters:
  connectionProfiles:
    knownStart:
      params:
        timestampMicros: {$document: /recordedStartMicros}
      when: {$exists: {$document: /recordedStartMicros}}
bindings:
  startAt:
    attached:
      'on': change
      path: /recordedStartMicros
      profile: knownStart
```

## Structural state

A clause type can declare `initialState`, keyed by a pointer binding name, with an
object initial value. Connection planning contributes that state through the
ordinary Clauses state-ownership checks. This installs data without dispatching
a business action and does not grant an exception to Activation. Ledger and
Amendments use it for their empty initial state. A state-only clause may omit
`actions`; a supplied action declaration must still be an object. Only the admitted clause type
supplies this declaration; runtime requests cannot inject a state initializer.

## Workflow input and exact review

A workflow connection may set `input: true` to pass its operation request as an
object. The action's defaults are applied first and explicit connection
`params` take precedence over request fields. The workflow's existing
`request` pattern still describes the public input.

Set `requireExactDocumentVersion: true` on a workflow connection to require
a native exact-version request. Contracts still compares the supplied document
reference to the target version. A caller that omits the exact-version flag
receives `EXACT_REVIEW_REQUIRED` before the connection runs.

Workflow connections may also project fields with `inputParams` and
`documentParams`. Each maps a destination JSON Pointer in the action
parameters to a source JSON Pointer in the operation request or local
document, respectively. The action defaults, forwarded request and explicit
`params` are merged first. Input mappings apply next, then document mappings.
Each mapping applies in canonical key order and skips absent source values.
