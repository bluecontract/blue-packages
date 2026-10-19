# Current final-gas verification

See [qualification](QUALIFICATION.md) and [migration](MIGRATION.md) for the new
final-gas edition. The dated report below is historical; its identities and
unchanged-source statements are not claims about this edition.

---

# Verification — 26 September 2026

## Verdict

Keep the Language package unchanged. It is a verified final publication of the selected local Language edition, not a claim that every conceivable defect has been excluded. Its complete specification, standard definitions and reference bytes are unchanged. The only distribution adjustment is restoring executable permission on its launcher.

BEX and Contracts are new clean `1.0.0-rc.1` publications. Their own normative material is consolidated into single specifications rather than rules-plus-historical-supplement chains. Their exact algorithms are the supplied Python files. New specification identities and Contracts native identities are deliberate and recorded; old packages are not modified.

## Fresh executions

| Scope | Result |
|---|---|
| Language portable corpus | 1,408 cases passed |
| Language portable edge corpus | 52 cases passed |
| Native Language specification metadata | 26 tests passed |
| Selected Language API/admission tests | 128 tests + 146 subtests passed |
| Original Language release tests | 23 passed |
| BEX original unit tests | 164 passed + 25 subtests; one synthetic helper deselected |
| BEX release tests | 12 passed, including byte-identical rebuild |
| Contracts release tests | 12 passed, including all 32 definitions and byte-identical rebuild |
| Contracts original selected EventAPI tests | 12 passed against the new specification-resource binding |
| Contracts direct/chunk/cold example | APPLIED; count 1; emitted `[{"count":1}]`; gas 631 |
| Same Contracts example with gas 630 | GAS_LIMIT_EXCEEDED and rollback |
| Java native package reading | Language, BEX and Contracts verified |
| Java/Python source admission | Same Counter BlueId `5V5uqBDVgwfHj8Y33THHs2pQGxMfb4NZcXcHS5YNneup` |

These groups overlap and have different coverage; do not add them into a claim of exhaustive end-to-end parity. The wider Contracts test run was stopped after 221 seconds with seven completed passes; no complete result is asserted. The completed 12-test EventAPI selection covers exact signature, original event selection, ordering, validation, checkpoint attribution, timestamp rejection, preconditions, replay, tamper rejection, gas rollback and managed-child protection.

## Identity and source evidence

- All 327 Language source-release files compared directly with the uploaded ZIP are byte-identical, ignoring executable permission restoration.
- Language data artifact remains `sha256:a030dd4c88e41a414918ef4895017862e154b438848bd5c0e4f5bc880e7b8a90` and package `8XGYNufx24r7Dc5bGoeobcGNCn9roLzSfZCQyHBTaTx4`.
- BEX includes 95 exact reference/support files; Contracts includes 185. No source-byte differences from the selected input snapshot were found.
- Six BEX algorithm modules and eighteen Contracts algorithm modules are embedded verbatim in their normative documents. The old Language dependency manifests that predated native metadata are not presented as current binding evidence.
- Every old/new Contracts exact type body was compared after replacing only the declared specification/parent reference IDs. All 32 matched; no fields, constraints or type relationships were silently rewritten.
- The Contracts demonstration runs a separate temporary binding. It replaces only the normative specification resource in that tree; the preserved reference remains untouched.

## Limitations and next step

The known enum traversal defect in the supplied reference remains. Its published input evidence shows seed-dependent gas/receipt identities despite the same final document. This work does not call that conforming deterministic behavior, fix a favored seed or alter the gas ceiling. A deterministic reference correction is a separately qualified semantic publication.

The Java source can read these packages, but its existing native runtime still selects earlier Contracts rules/types. Adopt this new collection explicitly and compare the same tests. Do not simply disable support checks or attach a new package label to the old interpreter's native binding. Coordination and old histories are unchanged. No remote publication or runtime deployment was performed.

Detailed evidence is in `verification/`. The current IDs are in `PACKAGES.json`; archive checksums and source inventories accompany the release folders.

This file reports the coordinated review. When this repository is downloaded separately, its own source lock, local tests and examples remain runnable. The full three-package handoff contains the raw verification evidence.

## Clean delivery check

The three individual source ZIPs were extracted into fresh directories, every inventoried file was checked, and `./blue-package verify` passed in all three copies. Their data artifacts match the frozen archive hashes. Subsequent source-report additions do not alter any package data or executable algorithm. The final source/archive inventory is checked again during ZIP creation.
