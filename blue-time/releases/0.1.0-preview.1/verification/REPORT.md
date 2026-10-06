# Blue Time package — verification and handoff

Version: `0.1.0-preview.1`. Prepared against the supplied
`blue-python-and-packages-20260927-2325(3).zip` on September 28, 2026.

## Delivered

A new sibling `blue-packages/blue-time`, following the attached source manifest,
exact dependency lock, type/specification, examples, tests and immutable `.bluepkg`
publication layout. It does not modify the supplied foundation packages or their
native support selections. Imports are Language, BEX, Contracts and Coordination.

The sample has one initialization `Contracts/Trigger Event` and one operation
`Time/Schedule Timer` custom step. Both emit Time/Timer Request. Timestamps are
unquoted Integer Unix microseconds, with no `afterUs`, initialization timestamp or
reported wall-clock firing time. Two workflows match different request purposes.

## Executed results

| Check | Result |
| --- | --- |
| Package test suite | 35 passed; no failures, errors or skips |
| Immutable archive verification | Passed |
| Export definition audit | 6 of 6 passed |
| Rebuild from exact locked sources | Byte-for-byte match |
| Full two-timer example | Passed on real Contracts/BEX with fixture bindings |
| Returned request's exact identity in BEX | Matches original emitted request |
| Authored and published examples | Byte-for-byte match |
| Original files checked | 695 unchanged |

The full example starts pending, registers activation during initialization without
an incoming Timeline entry, and registers the reminder via its operation. After
the simulated reminder deadline and complete prefix, reminderCount is 1 and the
captured message is stored. After the activation deadline, status is active.

Tests cover initial no-input registration, both scheduling styles, direct BEX,
separate workflow matching, exact identity, cancellation/replacement, duplicate
and stale fixture admissions, timestamp validation, local ordering/completeness,
rollback and shared gas exhaustion. They also confirm that mounting this package
does not silently install or approve native Time support.

`verification/tests.log`, `verification/example.json`,
`verification/archive-verification.json` and `verification/check-source.log` contain
the actual outputs. Development corrections are recorded separately in
`verification/development-notes.md`.

## Scope boundary

**This is a built data/protocol package and executable conformance fixture, not a
native production Time scheduler.** The runner uses the supplied Python Contracts
and BEX, explicitly installed test bindings, an in-memory pending registry and
simulated trusted time/completeness. Its owner channel is also a test fixture.

No production worker, durable timer journal, provider-proof verifier, account
integration, shared-parent/cyclic scheduler integration or Java implementation
was added or qualified. The complete existing-stack regression suite was not run.
There is no claim of automatic wake-ups simply from importing the archive.

`docs/IMPLEMENTATION-TASK.md` is the implementation handoff, and
`docs/acceptance.md` specifies ten native gates before approval. The exact candidate
selection is in `docs/integration-selection.json`, with approval explicitly false.

## Identities

Package BlueId: `ENnw8FULDL7o6WjBaJsNedvevNwEqgMn7ZHyUiDTFByo`

Protocol BlueId: `DfTrPqfhocn65pn7eg52RMGQnN8g9vqn2PRwvRe3d7MW`

Rules BlueId: `ArkSFtCk1DEvxYq3yRsT2k5yEQGtHETgA6gdQz3WWDjz`

Archive SHA-256: `0e485bea414e644b1ebdb5f4a97809845348e780e427729ffbde112f00849e1c`

## Reproduce

Extract the source bundle beside the attached foundations, retaining this layout:

```text
blue-python/
blue-packages/
  blue-language/
  blue-bex/
  blue-contracts/
  blue-coordination/
  blue-time/
```

Use Python 3.13 or later. `BLUE_PYTHON` can select the interpreter.

```sh
cd blue-packages/blue-time
./blue-package verify
./blue-package check-source
./blue-package test
./blue-package example
```

The package uses the attached sibling publisher and libraries; it is not a
standalone bundled runtime. No installation changes to the foundations are needed
for these fixture commands. Check SHA256SUMS for the delivered source files.
