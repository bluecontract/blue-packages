# Clause connections preview

Directly authored BEX, lowered by `Connected Clause` into existing Contracts and
Time definitions during the ordinary clause planning hook. There is no JavaScript
or Python business-code generator. `Hello Clause` is a tiny reusable action.

Exports: Connected Clause, Hello Clause, Hello Said, Greeting Request, Ping, and
Other Ping. The last two provide distinct nominal event types for the examples.

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

## Conditions on a named action

`parameters.conditions.<actionName>` adds a BEX predicate to every connection of
that action. It is evaluated after the action's original requirement and typed
arguments, before preflight or any `before`, action or `after` effects. It can only
add a restriction. A false result fails with `ACTION_CONDITION_FAILED`; an unknown
action name is rejected during planning. Omitting a condition adds no restriction.
Conditions use the action's own document and selected named sources, not an
incoming observer's state. Cross-document changes require explicit application
events when they are intended to trigger an action automatically.

## Structural state

A clause type can declare `initialState`, keyed by a pointer binding name, with an
object initial value. Connection planning contributes that state through the
ordinary Clauses state-ownership checks. This installs data without dispatching
a business action and does not grant an exception to Activation. Ledger and
Amendments use it for their empty initial state. A state-only clause may omit
`actions`; a supplied action declaration must still be an object. Only the admitted clause type
supplies this declaration; runtime requests cannot inject a state initializer.
