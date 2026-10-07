# Ten-million-gas edition adoption

Version 1.0.0-rc.2 selects a shared default and maximum of 10,000,000 gas units for an entire atomic Contracts attempt. Numerical tariffs, charge ordering, rollback and explicit smaller budgets are unchanged. Language and BEX dependencies retain their exact identities.

The former publication and its 100,000 maximum remain under `editions/gas-100k/blue-contracts`. Existing snapshots and invocations must keep that edition. The new specification, all 32 native types and dependent packages receive new identities; replacing references inside already published data is not migration.

The executable specification uses the frozen reference plus the two explicit source overrides and gas manifest in `reference/`, listed in `docs/sources.json`. `runtime-copy` constructs an isolated executable tree with these exact bytes. Never alter the frozen reference.

Consumers must select the new native edition and republish dependent authored documents. Validate portable replay, exact and restrictive budgets, and physical resource use before upgrading a persistent host. Raising gas does not correct host memory failures.
