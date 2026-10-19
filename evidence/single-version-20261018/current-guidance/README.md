# Blue packages

One current package set lives at the repository root. `PACKAGE-SOURCES.json` selects source directories; `PACKAGES.json` pins the built archives. `PUBLIC-CLAUSES.json` is the public catalogue: 13 feature families, including one payment family with provider-specific variants.

Start with the [complete clause tutorial](docs/clauses-tutorial.md) and the [executable examples](examples/apps). They use Activation and clauses throughout. Raw contracts are implementation details of reusable packages. The Payment clause exposes requests; guarantor operations belong to the Payment Instruction.

The foundations are Language, BEX, Contracts (immutable deterministic edition 3, 10,000,000 maximum), canonical Coordination, Time data and Mandates. The selected execution profile excludes timer roles. **Mandates remains its own package, `blue-mandates`.** Business packages do not redefine native execution, transport or delegation.

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

The deterministic edition enforces every charge but omits accepted per-charge receipt histories.
It has new exact identities; existing documents must keep their original runtime.
See [Contracts migration](blue-contracts/MIGRATION.md).

Canonical deterministic sources are in `blue-contracts/reference-deterministic`;
`tools/build_deterministic_reference.py --check` verifies their complete
publication. `tools/build_coordination_spec.py --check` verifies the single
canonical Coordination publication. Earlier publications and archive bytes are
retained in `releases/`; never replace published content under an existing BlueId.
Python and standalone Java select exact current profile identities independently
of catalogue availability. See `docs/deterministic-source-inventory-revision.json`
for the reviewed release-inventory metadata update.

These are unpublished candidates, not a production certification or a live financial service. See the tutorial for execution boundaries and the distinction between protocol requests and confirmed external outcomes.
