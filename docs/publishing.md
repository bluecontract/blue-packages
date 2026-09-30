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
checks. Native protocol types must declare their own rules reference; see
[specification links](specification-links.md) for the metadata model and regression
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

* The 18 selected archives at their package-relative paths, including the four
  root-clause editions.
* `CATALOG.json`: each version, package BlueId, archive SHA-256, exports and imports,
  with Time marked as a preview outside the shared selection.
* `SHA256SUMS`: checksums for every other file in the bundle.
* A distribution README and the existing Language third-party notice.

No source snapshots, unpacked duplicates, tests, logs, credentials, environments or
historical releases are added. An existing output is never overwritten. This bundle
is an artifact collection; source-checkout consumers can need additional files and
compatibility publications, so do not point them at the extracted bundle as a drop-in
replacement for this repository.

## Prepare GitHub Release assets locally

```sh
python3 tools/release.py assets --output build/release
```

This runs the same integrity checks and creates a new, flat upload directory:

* One `<name>-<version>.bluepkg` file per selected publication, preserving its bytes.
* `blue-packages.zip`, with all selected archives at their original relative paths.
* `CATALOG.json`, with each original path, selection, version, BlueId, archive SHA-256
  and `releaseAsset` filename. The same catalogue is included in the ZIP.
* `SHA256SUMS`, covering every other upload file, including the ZIP.
* `README.md` and `THIRD-PARTY-NOTICES.md`.

Different editions retain their own versions and identities. Duplicate asset names
are rejected. An existing output directory is never overwritten; use a new directory
for a subsequent preparation. Inside the ZIP, its own `SHA256SUMS` covers the bundled
paths; the standalone `SHA256SUMS` covers the flat Release attachments.

These are common Blue documents for all compatible language implementations. Java,
Python and other consumers download the same artifacts and pin their exact identities.
The collection tag identifies a selection; individual package versions and native
runtime support remain independent.

## Publish through GitHub Actions

The workflow in [packages-release.yml](../.github/workflows/packages-release.yml)
runs release-tool tests, verifies pinned archive bytes, member checksums, unpacked
files, source inventories and dependency locks, prepares the assets, and checks their
upload checksums. It uses Python's standard library and does not install a runtime,
rebuild the packages or run the separate semantic verifier. Run the semantic and
affected source checks above before tagging a changed package selection.

Pull requests, pushes to `main`, and manual **Run workflow** invocations only prepare
a downloadable `blue-packages-release` Actions artifact, retained for seven days.
After this workflow is committed and pushed, pushing a `blue-packages-*` tag also
publishes a GitHub Release from that exact tagged revision. For example, from the
intended, clean release commit:

```sh
git tag -a blue-packages-2026.09.30 -m "Blue Packages 2026.09.30"
git push origin blue-packages-2026.09.30
```

The collection tag is a date/version label, not a new version for every package.
The publish job downloads the verified artifact from the same workflow run, checks
its checksums again, uploads all attachments into a temporary draft, and publishes
only after the upload succeeds. It uses the built-in `GITHUB_TOKEN` with
`contents: write` in that job; no npm registry, `read:packages` scope, separate token
or cross-repository runtime installation is required. GitHub Actions must be enabled
and repository/organization policy must allow that token permission.

An existing Release is not replaced, and uploaded assets are never clobbered. If an
upload fails, the Release can remain a draft; remove that incomplete draft and rerun
the failed workflow. Use a new tag for a new collection; do not move published tags.
In a private repository, Releases require repository read access.

## Download a published collection

Using GitHub CLI, including authentication for the private repository:

```sh
gh release download blue-packages-2026.09.30 \
  --repo bluecontract/blue-packages --dir blue-packages-download
cd blue-packages-download
sha256sum --check SHA256SUMS
```

On macOS, use `shasum -a 256 --check SHA256SUMS`. `CATALOG.json` maps each package's
BlueId and original source path to its individual Release attachment. The ZIP is a
convenience collection of the same data; consumers can load the individual `.bluepkg`
files with their language's compatible reader.

## Publication policy

Transport can be a file server, a release attachment or an artifact registry. Pin both
the archive hash and BlueId. Transport digests are separate from Blue identity. Upload
the existing bytes; never reuse an old identity or released version for changed content.
Keep native-runtime adoption and consumer-lock changes explicit.

The local tools only prepare files; tagged publication is performed by the GitHub
Actions workflow above. This repository has no declared
project-wide license, and its existing source provenance does not grant additional
redistribution rights. Set the project's license and confirm upstream permissions
before public redistribution. Existing notices remain preserved under
`blue-language/THIRD-PARTY-NOTICES.md` and the frozen references.
