# Blue packages

One current package set lives at the repository root. `PACKAGE-SOURCES.json`
selects the source directories; `PACKAGES.json` pins the complete built set.
There are no alternative source editions to choose between.

Start with [the payment and clauses guide](docs/payment-family.md),
[the repository layout](docs/layout.md), and [consolidation notes](docs/consolidation.md).

The foundation is Language, BEX, Contracts (10,000,000 default gas), Coordination,
Time and Mandates. **Mandates is its own package, `blue-mandates`.** Coordination
owns authenticated timeline transport and access, not business delegation rules.

Business packages cover clauses, agreements, orders, document collections,
parties, access participants, state, activation, termination, amendments,
balances, referrals, schedules and the payment family. Payment Instruction is
provider-neutral; MyOS, ACME Bank and Manual Payments contain specific processes.
Adapters remain test implementations, not live financial integrations.

## Build and verify

```sh
# JAVA_HOME must select Java 21; classpath must use the qualified Blue Java runtime.
BLUE_JAVA_CLASSPATH=... bash tools/build-payment-family.sh
python3 tools/sync_catalogues.py
python3 tools/release.py check
python3 tools/check_payment_family.py
python3 -m unittest discover -s tools -p 'test_release.py'
```

The builder reads `.blue` definitions. It packages BEX programs and never
implements their business rules in Java or JavaScript. `SHARED-PACKAGES.json`
and `PAYMENT-FAMILY-PACKAGES.json` are generated views of `PACKAGES.json`, not
independent selections. Do not edit their pins manually.

These sources are unpublished candidates. Package consolidation is not a
publication or production qualification. Native protocol support must be
explicitly installed and tested by each runtime.
