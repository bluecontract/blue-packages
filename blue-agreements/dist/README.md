# Agreements

Version **0.3.0-rc.1** composes reusable clauses inside one managed Agreement.
A clause declares parameters, bindings, persistent state and named contract features.
The installer validates the complete configuration and installs its root contracts.
Business logic is ordinary Blue/BEX data; this package introduces no native protocol.

Use `Agreements/Agreement` and `Agreements/Clause` for new documents. The separately
named `Embedded Agreement` and `Embedded Clause` exports retain the older model.
Old published archives remain available; existing instances are not migrated automatically.

Read [the clause authoring and amendment guide](docs/root-clauses.md) for the API,
examples, trust model, state retention and compatibility limits.
