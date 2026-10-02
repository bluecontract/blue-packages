# Blue package archives

This collection contains the selected Contracts C1/gas5 import closure and its
retained predecessors: Language, BEX, Contracts, Coordination, Agreements, clauses,
Reseller Agreement, Agreement Examples, Mandates, Time and commerce functions.
The `selection` field separates current, root-clause, preview and retained
publications. `CATALOG.json` records each package's exact identity, version, exports,
imports and archive SHA-256. When prepared as GitHub Release attachments, it also
maps each package to its `<name>-<version>.bluepkg` filename via `releaseAsset`.
Where historical editions share a display version, an explicit identity suffix
disambiguates the filename: `<name>-<version>-<packageBlueId>.bluepkg`. This does
not change any byte inside the archive or relax checksum/identity verification.
All compatible language implementations use the same published documents.

Inside the ZIP, `SHA256SUMS` checks every other bundled file. Alongside the Release
attachments, the standalone `SHA256SUMS` checks the individual archives, ZIP,
catalogue and distribution notices. Verify with `sha256sum --check SHA256SUMS`
(on macOS, `shasum -a 256 --check SHA256SUMS`).

Load individual `.bluepkg` files with a compatible Blue package reader. Native
execution support must be selected separately in the Java or Python runtime.
Time is a conformance preview, outside the shared runtime selection; these files
do not install a production timer service or grant native protocol authority.

The archives are unchanged from their selected publications. The October successor
binds the existing exact document-target correction and deterministic gas5 enum
order, including the dependent Coordination/Mandates/business import closure.
Historical archives retain their original identities and bytes. This is a distribution
of data artifacts, not a source checkout or an assertion of runtime parity. Tests,
reference runtimes, historical compatibility releases and package build tools are
available separately in the source repository. Older consumer selections can need
those historical releases; do not repoint their pinned package IDs at new archives.

Each archive includes its release-specific README and any published specification
and documentation. Some original reading instructions describe the source checkout.

The project has no declared repository-wide license. Existing provenance and notices
are retained in `THIRD-PARTY-NOTICES.md`; its referenced implementation snapshot is
source-repository material and is not part of this data bundle. Confirm publication
rights and licensing before public redistribution.

The four `root-clause-contracts-c1-gas5-20261002-1` business archives have their own
explicit selection. Their `root-clause-bindings-20260929-1` predecessors remain
available separately. Business-package availability does not expand approved
native protocol support. Changing a release pin alone does not select a new
runtime edition or migrate saved state.
