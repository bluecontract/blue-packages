# Blue packages

Current runtime review candidate: [Blue Contracts 1.1.0](releases/contracts-1.1.0/REVIEW.md), including compact receipts and exact rebuilt native/application dependencies. Prior publications remain immutable.

One current package set lives at the repository root. `PACKAGE-SOURCES.json` selects source directories; `PACKAGES.json` pins the built archives. `PUBLIC-CLAUSES.json` is the public catalogue: 13 feature families, including one payment family with provider-specific variants.

Start with the [complete clause tutorial](docs/clauses-tutorial.md) and the [executable examples](examples/apps). They use Activation and clauses throughout. Raw contracts are implementation details of reusable packages. The Payment clause exposes requests; guarantor operations belong to the Payment Instruction.

The foundations are Language, BEX, Contracts (deterministic final gas, 10,000,000 maximum), Coordination, Time and Mandates. **Mandates remains its own package, `blue-mandates`.** Business packages do not redefine native execution, transport or delegation.

## Build and verify

```sh
# Java 21 and a qualified Blue Java runtime classpath are required.
BLUE_JAVA_CLASSPATH=... python3 tools/build_final_gas.py all
python3 tools/sync_catalogues.py
python3 tools/release.py check
python3 tools/check_payment_family.py
python3 tools/check_clause_tutorial.py
python3 -m unittest discover -s tools -p 'test_release.py'
```

The builder packages the BEX authored in `.blue` files. It does not generate business logic in JavaScript. Java execution and authenticated integration tests live in the companion Core checkout. The isolated runner uses `blue.core.ClauseAppsExamples`; full Core validation uses `bash scripts/check.sh`.

The final-gas edition enforces every charge but omits per-charge receipt histories.
It has new exact identities; existing documents must keep their original runtime.
See [Contracts migration](blue-contracts/MIGRATION.md).

For the matching Core branch, run its `scripts/import-final-gas.py --packages
/path/to/blue-packages` after validation. This preserves Core's authored examples
and retained 10M publications, builds its internal Coordination bridge and Task
fixture, and updates the new default pins. The general example exporter should
only be used when intentionally replacing Core's example sources.

These are unpublished candidates, not a production certification or a live financial service. See the tutorial for execution boundaries and the distinction between protocol requests and confirmed external outcomes.
