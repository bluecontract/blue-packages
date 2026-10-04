# Root-clause amendments — Java qualification, 2026-10-04

The current Agreements, Mutual Activation, Immediate Termination and Reseller
packages are 0.3.0-rc.1. They are business data on the unchanged Language, BEX,
Contracts and Coordination protocols. The current selection is
`blue-packages/ROOT-CLAUSE-PACKAGES.json`.

## Behavior

The Agreement installs clause blueprints into one document. Empty initialization
works, explicit clauses are honored, and initialClauses supplies the default recipe.
An amendment uses amendA or amendB with expectedRevision and either individual
add/edit/remove changes or a complete replacement clauses object. A complete
parameters replacement can be included in the same transaction.

Sources and generated contracts commit together. Intermediate source changes do
not trigger partial installation. Stale revisions, malformed requests, invalid
bindings, conflicting owners, dependency violations and gas exhaustion roll back.
A no-op preserves the clause revision and pending approval. Active, declined and
terminated clauses retain their freeze policy.

Removal retires generated contracts while retaining owned state. Reattaching the
same clause key and type resumes it. State cannot be silently moved or claimed by
another type or owner. Dependencies must be removed or rewired in the same batch.

Whole typed workflows can be clause parameters. Explicit feature fills and constant
injection install them without executing their body during initialization. Pointer
parameters and field bindings can read existing live document fields. Unowned root
workflows, including typed event listeners, survive installation; generated features
cannot overwrite them. Installation emits typed per-clause changes and Clauses Installed.

## Performance changes

- Reuse inherited Compute steps for installer functions.
- Transfer initial clauses and amendment source values using retained BlueId references.
- Install the complete generated contracts map atomically using references instead
  of repeatedly patching and validating expanded workflow bodies.
- Index prior state ownership once per reconciliation.
- Transfer runtime metadata by reference and avoid leaving amendment guard state behind.

The new checks and events also have a cost. This is not constant-time reconciliation:
the installer validates the complete active clause configuration. Ordinary business
operations do not rerun it unless they amend clauses or parameters.

## Verification

The full offline Java build passed **303 tests, zero failures and zero skips** in
84 seconds. The 64 focused publication tests cover empty/default initialization,
add/edit/remove and full replacement, combined parameter changes, rollback and
exhaustion, malformed requests, stale revisions, wrong channels, parameter bounds,
state ownership and retirement, missing dependencies, invalid blueprints, freeze
rules, whole workflows, live/escaped pointers, event listeners and contract collisions.

The signed integration test uses a temporary SQLite coordination service, submits
an amendment, approves from both parties and terminates the Agreement. The public
library example separately verifies YAML/JSON identity and activation at clause
revision 2. Every test runs Java against the bundled immutable reseller publication;
no test reads or executes a Python implementation.

The shared catalog check passed for 18 selected packages and 901 inventoried source
files. All four new package archives and dependency locks rebuilt byte-for-byte.
All four previous top-level archive checksums remained unchanged after relocation.

## Measured timings

JDK 21 on the local Mac, same Java implementation for both package releases.
Each run reuses one Blue/Contracts engine and creates a fresh one-document reseller
agreement per iteration, with two clauses and no embeddings. Nine iterations were
run per release; these are medians of the last six. Package loading is outside the
measurements. These are bounded engineering samples, not latency guarantees.

| Operation | Original root-clause preview | Current 0.3.0-rc.1 |
| --- | ---: | ---: |
| Prepare document | 15.2 ms | 18.1 ms |
| Initialize clauses | 291.3 ms | 285.9 ms |
| Amend discount parameter | 242.1 ms | 288.5 ms |
| First party approval | 56.7 ms | 64.3 ms |

The business amendment is the same discount change; the new edition additionally
checks expectedRevision, supports batched changes, tracks richer ownership and emits
installation events. It is therefore not an identical logical-gas workload.

Initialization median logical gas: **91,987 → 87,968**.

Amendment median logical gas: **75,676 → 88,334**.

The final implementation reduces initialization work but does not make amendments
instant. Material amendment still takes roughly 0.3 seconds in this workload and
validates the complete configuration. Treat the timing difference as directional:
these small samples do not establish a statistical speedup. The next optimization
would need to reduce repeated reconciliation/validation while preserving dependency,
freeze and ownership checks; it must not skip them to manufacture constant time.

## Compatibility and limits

The previous embedded-clause projects are preserved under
`blue-packages/editions/embedded-clauses`, with unchanged archive bytes and identities.
The old root-clause preview remains under editions/root-clauses. Source import paths
and legacy selectors point to retained releases; existing instances are not migrated.

This is a release candidate with bounded Java qualification. It is not an exhaustive
proof for arbitrary custom code. Workflow parameters carry the Agreement's write
authority and must come from trusted authors. State migrations, destructive state
cleanup, automatic migration of live agreements and arbitrary third-party channel
binding are not provided. The named channel slots currently select partyA or partyB.
Large configurations remain subject to the host's gas policy. Python runtime code
was neither changed nor used to run the tests.

## Reproduce

From blue-java with JDK 21:

```sh
./gradlew --offline :verification:test --tests blue.contracts.RootClauseAmendmentTest
./gradlew --offline :verification:agreementExample
./gradlew --offline :benchmarks:rootClauseLifecycle
./gradlew --offline :blue-package-tools:packageToolClasspath
java -Xmx2g --class-path "$(cat build/package-tool-classpath.txt)" \
  ../blue-packages/tools/BuildAgreements.java ../blue-packages --check
```

The last command rebuilds all four packages in a temporary directory and compares
publication bytes and locks. It does not rewrite the selected release. Omit --check
only when intentionally preparing a new package release; rebuilds also repin the
reseller's exact clause type identities.
