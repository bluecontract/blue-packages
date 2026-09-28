# Blue Language

Blue Language defines immutable typed content graphs, exact BlueIds, specialization, schemas, reusable packages, and references to additional protocol semantics.

## Read the specification

`SPECIFICATION.md` is the complete normative document for Blue Language 1.0, edition `blue-language/2026-09-26-specification-metadata-1`. It includes the core registry, ordinary Package and Protocol Specification definitions, and complete executable algorithms. No separate Blue specification is needed to determine this edition's Language rules.

`SPECIFICATION.html` in the source workspace is a generated reading view of the same Markdown. The Markdown is the identified normative Text. In the data-only `.bluepkg` artifact, read `spec/language.md`; it contains exactly the same document.

## Contents

- `types/` contains the six core registry bodies and the two ordinary standard definitions. Package and Protocol Specification are the package's two named exports; core names are established by the Language registry itself.
- `conformance/` contains unchanged portable Language cases and additional release checks.
- `dist/` contains the built package archive, exact package root, records, and manifest. Its `spec/language.md` is byte-identical to the source `SPECIFICATION.md`; `docs/types/` contains the same type sources. Archive conformance JSON arrays preserve the original case objects from the source JSONL files.
- `reference/python/` preserves the selected Python implementation and the support resources it imports. Those source copies are implementation evidence; older prose files retained inside that snapshot are not additional normative documents for this publication.
- `tools/` contains a local publisher and verifier. It performs no remote publication.
- `verification/` records the scope and results of the actual checks for this delivery.

## Local use

The commands below run from this source workspace, not from the unpacked data-only artifact. Python 3.13 or newer is required. The reference includes its YAML reader. Running the metadata regression tests also requires pytest.

```sh
./blue-package verify
./blue-package inspect
./blue-package test
python3.13 examples/use_package.py
```

A deliberate package build is:

```sh
./blue-package build
```

Normal verification and testing do not update pins, regenerate expected results, or change any referenced implementation source. Package acquisition is independent of Language interpretation; this project does not contact a registry.

## Identity and versioning

The package has a BlueId calculated under the selected Language. Archive and file checksums are separate integrity identifiers. This complete publication has a new package identity; it does not automatically replace the Language package referenced by existing BEX, Contracts, Coordination, or application packages.

Published definitions retain their exact IDs. The eight supplied registry/standard definitions and the executable Language algorithms are unchanged from the selected reference. Adoption by a dependent package is an explicit new dependency selection, not an identity rewrite.

This edition defines no automatic cross-Language import or cycle conversion. One selected interpretation governs an entire cyclic identity set and its proof. Compatible behavior, if introduced by a later Language edition, must be specified by that edition; no compatibility registry or version-range resolver is required here.

## Publication

The package can be retained locally or distributed through any file or artifact service. `dist/package.bluepkg` is the data artifact. GitHub and OCI are optional distribution infrastructure, not authorities that assign its BlueId. Nothing in this delivery has been published to an external registry.
