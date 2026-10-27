# Blue packages

One current package set lives at the repository root. `PACKAGE-SOURCES.json` selects source directories; `PACKAGES.json` pins the built archives. `PUBLIC-CLAUSES.json` is the public catalogue: 13 feature families, including one payment family with provider-specific variants.

Start with the [complete clause tutorial](docs/clauses-tutorial.md) and the [executable examples](examples/apps). They use Activation and clauses throughout. Raw contracts are implementation details of reusable packages. The Payment clause exposes requests; guarantor operations belong to the Payment Instruction.

The foundations are Language, BEX, Contracts (deterministic final gas, 10,000,000 maximum), Coordination, Time and Mandates. **Mandates remains its own package, `blue-mandates`.** Business packages do not redefine native execution, transport or delegation.

## Demand-scoped candidate (2026-10-23)

The selected source candidate retains the demand-scoped Contracts semantics and
adds the BEX result-value preview edition. `PACKAGES.json` records exact versions,
identities and archives for the rebuilt dependency closure; prior immutable
publications remain unchanged. Native package construction and
archive/dependency integrity passed; final host integration and whole-edition
qualification are separate gates. Bounded executable reference models and paired
Java vectors do not qualify a second complete Python runtime.

Do not import this candidate with the generic final-gas importer: the host must
install it in its dedicated demand-scoped edition resources and catalogue while
preserving existing final-gas/legacy manifests. Use an explicitly reviewed host
integration for this candidate.

## Build and verify

The [BEX result-value preview specification](blue-bex/spec/bex-resultvalue-preview.md)
defines structural `$resultValue` list operations and incremental projection costs
in both prose and executable algorithms. Run its isolated tests with Python 3.13+:
`python3 blue-bex/tests/test_resultvalue_preview.py`. Historical frozen specifications and reference sources remain unchanged. It is selected by the new `1.0.0-resultvalue-preview.1` package manifest.
The dependency closure is rebuilt for this exact BEX identity; no GitHub Release
or Core deployment is performed by building these artifacts.

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

The matching Core integration installs the generated dependency closure in its
existing demand-scoped runtime with explicit profile registration and catalogue
selection. Do not run the generic final-gas importer for this selection. Existing
saved account manifests and their resources remain supported; building package
archives neither changes those manifests nor deploys Core.

These are unpublished candidates, not a production certification or a live financial service. See the tutorial for execution boundaries and the distinction between protocol requests and confirmed external outcomes.
