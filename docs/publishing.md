# Preparing a distribution

Distribute the existing `dist/package.bluepkg` archives. They contain identified data,
specifications, documentation and supporting exact records; they do not install a
runtime. The repository also contains source and qualification material for maintainers.

## Check the selected release

From the repository root:

```sh
python3 tools/release.py check
PYTHONDONTWRITEBYTECODE=1 python tools/verify_packages.py
```

The first command uses only Python 3.10+ standard libraries. It checks exact selected
hashes and manifest IDs, archive-member checksums, every unpacked distribution file,
and dependency availability. It also reports Time separately from the shared runtime
selection. It does not calculate semantic BlueIds; the second command uses the installed
Blue Python reader to validate those identities, definition closure and source locks.
That command needs Python 3.13+ and the Blue Python library.

For a source change, also run the affected package's source/rebuild and acceptance
checks. For example, using that same interpreter:

```sh
python tools/build_reseller_packages.py check
BLUE_PYTHON=python blue-mandates/blue-package check-source
BLUE_PYTHON=python blue-time/blue-package check-source
```

Foundation packages expose `blue-package verify` and their own release/conformance
commands. Run expensive reference or runtime campaigns only when the change needs them.
Historical qualification is not a claim that those campaigns ran for a new release.

## Build the data-only bundle

```sh
python3 tools/release.py bundle --output build/blue-packages.zip
```

The command verifies inputs first, preserves every archive byte, and produces a ZIP
with fixed timestamps and ordering. Its explicit contents are:

* The 14 current archives at their package-relative paths.
* `CATALOG.json`: each version, package BlueId, archive SHA-256, exports and imports,
  with Time marked as a preview outside the shared selection.
* `SHA256SUMS`: checksums for every other file in the bundle.
* A distribution README and the existing Language third-party notice.

No source snapshots, unpacked duplicates, tests, logs, credentials, environments or
historical releases are added. An existing output is never overwritten. This bundle
is an artifact collection; source-checkout consumers can need additional files and
compatibility publications, so do not point them at the extracted bundle as a drop-in
replacement for this repository.

## Publication policy

Transport can be a file server, a release attachment or an artifact registry. Pin both
the archive hash and BlueId. Transport digests are separate from Blue identity. Upload
the existing bytes; never reuse an old identity or released version for changed content.
Keep native-runtime adoption and consumer-lock changes explicit.

No remote publication is performed by these tools. This repository has no declared
project-wide license, and its existing source provenance does not grant additional
redistribution rights. Set the project's license and confirm upstream permissions
before public redistribution. Existing notices remain preserved under
`blue-language/THIRD-PARTY-NOTICES.md` and the frozen references.
