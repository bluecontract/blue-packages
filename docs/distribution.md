# Blue package archives

This collection contains 14 current Blue data-package archives: Language, BEX,
Contracts, Coordination, Agreements, Mutual Activation, Immediate Termination,
Reseller Agreement, Agreement Examples, Mandates, Time and three commerce-function
releases. `CATALOG.json` records each package's exact identity, version, exports,
imports and archive SHA-256. `SHA256SUMS` checks every other bundled file.

Load individual `.bluepkg` files with a compatible Blue package reader. Native
execution support must be selected separately in the Java or Python runtime.
Time is a conformance preview, outside the shared runtime selection; these files
do not install a production timer service or grant native protocol authority.

The archives are unchanged from their selected publications. This is a distribution
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
