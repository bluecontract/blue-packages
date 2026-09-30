# Specification links in authored types

Native protocol types declare an own `specification` reference to the BlueId of
their normative **rules Text**. This is separate from the protocol descriptor:

* A type's `specification.blueId` identifies the rules Text.
* A package's `protocol.blueId` identifies a `Protocol Specification` document
  containing `language`, `rules`, `requires` and `status`.
* The package's `specBindings[typeBlueId]` records `binding: native-metadata`,
  a `protocol` reference to the descriptor and a `specification` reference to
  the rules Text. Export `specificationMetadata` records the rules identity.

These references belong to the semantic package model and exact type definitions.
The legacy `specification: null` transport-manifest field does not mean that the
current metadata is missing. Do not replace a rules reference with the descriptor
ID: that changes the type's meaning and identity.

The Mandates predicate-host revision on 29 September 2026 intentionally selects
new rules and rebinds all 19 types. See [the current release note](../blue-mandates/docs/predicate-context-20260929.md).
The identities and unchanged-publication results below describe the prior release.

## Source correction on 28 September 2026

The supplied `Blue_specification_audyt_i_typy_20260928.zip` audit identified 25
authoring omissions: 19 Mandates types and six Time types. Both builders previously
inserted the specification unconditionally. Their published definitions already
contained the correct reference.

The source files now declare those same references explicitly:

| Package | Types | Rules Text BlueId |
| --- | ---: | --- |
| Mandates | 19 | `FoLy66wEKoXF1hbmhx7FCGFCC56n62VtNR8x3LMEQWo3` |
| Time | 6 | `ArkSFtCk1DEvxYq3yRsT2k5yEQGtHETgA6gdQz3WWDjz` |

The builders validate these declarations and reject missing or conflicting
references before admitting a type. They no longer synthesize or replace the
field. Ordinary builds also check the frozen normative source before admission.
When deliberately preparing new rules, update their type references as part of
the new revision; Mandates' candidate command still requires separate native
approval before adoption.

This correction preserves published BlueIds, archives, unpacked distributions,
dependency locks and runtime selections. Time remains a conformance preview with
no native scheduler approval.

The other native protocol exports already carry their specification: Contracts
has 32 and Coordination has 41, for 98 across the four packages. Language's two
bootstrap standard types and BEX's protocol with no named type exports are
separate cases. Agreements, clauses and commerce functions compose existing
protocols; this correction does not assign them invented native specifications.

The archive was used as audit evidence, not as instructions to change the
language model or runtime. Its SHA-256 is
`f425cbd5d1cbdadcea813fd3ef525ebb3d89a0da43662cbd8fd70a91f0c82779`.

## Verification

Use Python 3.13+ with the current Blue Python library installed:

```sh
PYTHONDONTWRITEBYTECODE=1 python tools/release.py check
PYTHONDONTWRITEBYTECODE=1 python tools/verify_packages.py
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tools -p 'test_mandates_build.py' -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tools -p 'test_time_build.py' -v
PYTHONDONTWRITEBYTECODE=1 python blue-time/tools/package.py test
```

The builder tests include source-to-publication byte equality and reject omitted
specifications, descriptor IDs used in place of rules IDs, and edits to frozen
rules. Negative cases retain the existing publication and selection files.
These checks do not claim Java behavioral conformance or production Time support.

## Local results — 28 September 2026

Run with Python 3.13.15 from the sibling Blue Python editable installation. All
commands above passed: release integrity covered 14 packages and 901 retained
source files; semantic verification covered 14 packages and 524 historical
reference files. The Mandates builder suite passed nine tests and the Time builder
suite passed four. The existing Time fixture suite passed 35 tests. All 48 test
methods passed with no skips; Time coverage is an in-memory Contracts/BEX fixture,
not native scheduler qualification. Each builder reproduced the existing archive
and every unpacked distribution file from the corrected sources.

An additional comparison checked all 98 native type specification references and
their package bindings, all 25 corrected source references, 49 Time checksums and
204 unchanged publication/selection files against a pre-edit hash snapshot. No
published identity, archive, lock or runtime approval was changed.

The initial Time build-test run had three failures and one pass. It exposed the
existing macOS temporary-path problem:
`/var/...` resolves to `/private/var/...`, so the source-containment check rejected
valid files. The builder now resolves its staging root before checking containment.
The successful four-test rerun used the command's normal cache scope. Initial
failures are separate from that successful rerun; no expected results were relaxed.
The initial system `python3` invocation exited 137 before reporting results, and
an ad hoc metadata check initially assumed the wrong `specBindings` record shape.
The documented successful checks used the project interpreter and actual record
structure. The audit archive's historical test claims were not counted as local
verification.
