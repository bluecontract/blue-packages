# Blue packages

One current package set lives at the repository root. `PACKAGE-SOURCES.json` selects source directories; `PACKAGES.json` pins the built archives. `PUBLIC-CLAUSES.json` is the public catalogue: 13 feature families, including one payment family with provider-specific variants.

Start with the [complete clause tutorial](docs/clauses-tutorial.md) and the [executable examples](examples/apps). They use Activation and clauses throughout. Raw contracts are implementation details of reusable packages. The Payment clause exposes requests; guarantor operations belong to the Payment Instruction.

The foundations are Language, BEX, Contracts (deterministic final gas, 10,000,000 maximum), Coordination, Time and Mandates. **Mandates remains its own package, `blue-mandates`.** Business packages do not redefine native execution, transport or delegation.

## Runtime editions

The standard source tree, build and release preparation use **Access Events**.
Contracts and Coordination retain the exact Access Events native identities.
Compatible business fixes are rebuilt from current authored sources; see the
[publication comparison](docs/access-events-default.md).

Demand remains explicit: pass `--edition demand-scoped` to the builder, release
preparation or operation qualification. Its exact native sources, configurations
and previous archives are preserved under `editions/demand-scoped`; tools
materialize an isolated candidate in `build/demand-scoped`. Shared business source
changes require a full Demand rebuild before release preparation. Changes to
shared package interfaces fail until their explicit Demand overlays are updated.
No command uploads or deploys a runtime. Existing documents keep their runtime.

## Build and verify

```sh
# Java 21 and a qualified Blue Java runtime classpath are required.
BLUE_JAVA_CLASSPATH=... python3 tools/build_final_gas.py all
python3 tools/sync_catalogues.py
python3 tools/release.py check
# Explicit alternative; outputs remain isolated from the standard Access Events set.
BLUE_JAVA_CLASSPATH=... python3 tools/build_final_gas.py all --edition demand-scoped
python3 tools/release.py check --edition demand-scoped
python3 tools/check_payment_family.py
python3 tools/check_clause_tutorial.py
python3 -m unittest discover -s tools -p 'test_release.py'
```

The builder packages the BEX authored in `.blue` files. It does not generate business logic in JavaScript. Java execution and authenticated integration tests live in the companion Core checkout. The isolated runner uses `blue.core.ClauseAppsExamples`; full Core validation uses `bash scripts/check.sh`.

The final-gas edition enforces every charge but omits per-charge receipt histories.
It has new exact identities; existing documents must keep their original runtime.
See [Contracts migration](blue-contracts/MIGRATION.md).

[Semantic cards](docs/semantic-cards.md) can be prepared locally and committed with
package changes. GitHub generates only exact type BlueIds missing from both the
repo and S3, then publishes committed cards independently of package releases.

Core integration must explicitly select the matching Access Events or Demand
runtime and catalogue. Package build and release preparation do not import into
Core, change deployed defaults, or qualify a production rollout.

These are unpublished candidates, not a production certification or a live financial service. See the tutorial for execution boundaries and the distinction between protocol requests and confirmed external outcomes.
