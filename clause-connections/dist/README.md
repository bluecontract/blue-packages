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
