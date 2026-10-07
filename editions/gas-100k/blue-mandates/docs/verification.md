# Current Python integration verification

The incoming preview's report is retained as `provenance/incoming-verification.md`.
Its counts, Python version and package identity describe that older delivery.

Current package: `HCpgCrquNyV5iVfFZnq2XqMfjoqiqftz5AzQCN9zqsP9`.
Runtime profile: `blue-runtime/2026-09-27-mandates-1`.
The current integration preserves all 19 type identities and the normative Mandates
protocol while rebinding the Coordination dependency to the shared publication.

Verified with Python 3.13.15:

- 52 owned Mandates acceptance tests passed against the installed current Python implementation.
- The application's 14-step Counter/flag lesson and SQLite restart/picker checks passed.
- Selected existing authority/order/connected/Workbench regression tests passed.
- All eleven shared archives and preserved historical reference locks verified.
- Language, BEX and Contracts package release verifiers passed after relocation.
- A byte-identical Mandates rebuild passed.
- A fresh installed Python wheel verified all eleven bundled archives and started
  the native engine with all five required packages, without a sibling checkout.

Run this package's tests and examples from an environment with blue-python installed:

```sh
python -m unittest discover -s ../blue-packages/blue-mandates/tests -v
python ../blue-packages/blue-mandates/examples/run_examples.py
```

The four executable examples passed: revoked bounded counter (count 4), manual
Order (Released), provider-qualified counter (count 2 after Unknown then success),
and connected Order (Released, Mandate Terminated). Current generated sources are
in `examples/generated/`; `verification/examples.json` retains their public entries,
responses and histories. No private provider keys are included.

The full integration report, exact commands, local logs and limitations are in
blue-python's `docs/mandates-integration-20260927.md` and its provenance record.
This is a targeted integration campaign, not a complete four-layer conformance,
Java parity, remote-provider interoperability or production-security certification.
