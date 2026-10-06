# Mandates predicate host — 29 September 2026

An owner could approve a read-only predicate using `$is` or `$nodeBlueId`, but the
Python authority host supplied neither Language callback. Delegated execution
then failed with `INVALID_AUTHORITY_PREDICATE`. Contracts Compute already supplied
both capabilities. Mandates permitted pure BEX without specifying the complete
host contract; this revision makes that requirement explicit in §4.

Both document and request predicates require Language matching (including pure
function argument patterns) and exact identity. Nested exact operands retain
their resolution context; identity is not a materialized-JSON hash. §6's bindings
remain the historical processed Mandate and the actual pre-action target/request.
One fresh 100,000-gas ledger covers BEX, view construction, demanded reads, matching
and identity using the pinned BEX costs and Contracts logical-work tariffs. Missing
resources and host interruption keep their distinct incomplete paths. Effects and
native intrinsics remain excluded; failure cannot confer authority.

## Reviewed publication

This is `0.1.0-preview.3`, built with revision
`shared-mandates-20260929-predicate-context-1`. The normative text changes identity:

- Package: `6HTzReYUxeSzyQhkrHag3tcYC482vo2EDxbT2qSRJ4N6`.
- Rules Text: `5aLyxVDGR4ToKSMDoaXKFBWUPBcp3yCF8rdXfAoTT4nQ`.
- Protocol descriptor: `6R5aoirVDjJLnaajjr34S4oCb8H3hV8rnrjN83qW31bh`.
- Archive SHA-256: `7a3c54b492abe7fec421ac8d26eee186abc833fd358d02386cde794ba1b7d6e5`.

All 19 authored types reference the new rules Text, so each has a new identity.
`docs/native-support.json` records the explicit approval proposed with the Python
companion change, selecting `blue-runtime/2026-09-29-mandate-predicates-1`.
The four dependency imports and the other 12 shared package pins are unchanged.
No Language, BEX or Contracts algorithm is modified.

The previous preview.2 archive remains byte-for-byte intact at
`verification/publications/mandates-before-predicate-context-20260929/dist/package.bluepkg`.
Its package ID is `HCpgCrquNyV5iVfFZnq2XqMfjoqiqftz5AzQCN9zqsP9` and its SHA-256 is
`ebb150b7e7a474924fb7c462b3cad9cb660f6416692c3158026e007a132f7538`.
The retained directory also contains the exact old rules, authored types, locks
and support manifest, with 26 file checksums. It is historical evidence; the
current source project is the reconstructible publication.

The source was compiled to a new candidate directory first. Promotion to current
`dist/`, shared inventory and consumer pins is explicit in these PRs; ordinary
build/check still cannot overwrite a mismatching distribution or approve new IDs.
Old stored workspaces require the original runtime; automatic migration/replay is
not implemented. The Python Workbench opens a separate workspace and preserves
saved Content.

## Verification

Using Python 3.14.7 and the companion Blue Python checkout installed editable:

```sh
python tools/build_mandates.py candidate --output build/mandates-predicate-context \
  --version 0.1.0-preview.3 --revision shared-mandates-20260929-predicate-context-1
python -m unittest discover -s tools -p 'test_mandates_build.py' -v
python tools/release.py check
python tools/verify_packages.py
```

The nine builder tests passed with zero failures, errors or skips (68.873 seconds).
They reconstruct the archive and every loose file from locked source, reject
unapproved identities, missing/wrong specification references and dependency drift,
and preserve complete publications when candidate construction is interrupted.
Release integrity checked 14 packages and 901 retained source files; semantic
verification checked 14 packages and 524 historical reference files. The 26
predecessor checksums and unchanged dependency lock were verified independently.

Behavioral regression evidence belongs to the companion Python PR and
`docs/mandate-predicates-20260929.md`, including signed Memory/SQLite delegation,
restart, invalid predicates and gas rollback. This package does not claim a Java
campaign, automatic migration, public hosting or production qualification.
