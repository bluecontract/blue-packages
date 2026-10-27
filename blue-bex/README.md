# Blue BEX

BEX evaluates explicit inputs into a value, ordered proposed changes and events,
and a deterministic admitted gas total. It does not apply document changes.

## Result-value preview edition

`1.0.0-resultvalue-preview.1` uses structural List removal and lazy immutable
preview roots. Each read retains its fixed charge and demanded host obligations.
The selected rules are `spec/bex-resultvalue-preview.md`; its six embedded modules
are executed directly by `tests/test_resultvalue_preview.py`. Earlier frozen
specifications and exact archives retain their identities. Core adoption is separate
from building this package; package data cannot install a native evaluator.

## Historical final gas edition

`1.0.0-final-gas.1` checks each charge before work and accumulates scalar gas.
Results have `value`, `changeset`, `events` and `gas_used`; accepted-charge rows
and `gas_trace` are not part of this edition. The default standalone allowance
remains 10,000,000. A supplied shared meter is never reset. Local and shared caps
retain their rejection order and one compact first-rejected-charge diagnostic.
A meter that has rejected work cannot resume accepting charges.

The historical `spec/bex-final-gas.md` retains that edition’s complete
normative text and six executable modules. `docs/sources.json` now records the
selected result-value preview modules and overrides. The earlier specification remains in `spec/bex.md`
and the frozen references remain unchanged for historical qualification.

This is a new exact protocol identity. Hosts must retain the old edition when
replaying old histories. Loading package data does not install an evaluator or
authorize an intrinsic. Optional debug traces are noncanonical and off by default.

## Local verification

With Python 3.13+, pytest, PyYAML, Java 21 and `BLUE_JAVA_CLASSPATH` pointing to
the qualified native Language runtime:

```sh
./blue-package verify
./blue-package test
python ../tools/build_final_gas.py blue-bex --check
```

The new-edition tests execute the finite conformance vectors and cover shared
meters, exact budgets, rejection and the absence of charge history. Historical
reference tests must run against their original frozen edition. Passing a finite
corpus does not establish universal conformance; see `QUALIFICATION.md`.
