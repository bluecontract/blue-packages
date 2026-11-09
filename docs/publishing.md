# Preparing a publication

`PACKAGES.json` selects the standard Access Events source set. All archives remain unpublished
candidates until an explicit reviewed release.

Run `python3 tools/sync_catalogues.py --check`, `python3 tools/release.py check`
and `python3 -m unittest discover -s tools -p test_release.py`. Rebuild changed
source packages in dependency order with Java 21 and `python3 tools/build_final_gas.py all`; compare exact
archive hashes on a second build. Native changes additionally require runtime
qualification; data installation cannot grant native support.

Run `python3 tools/check_admission_scope.py` with Python 3.13 when preparing a
Documents edition. The release job uses the checked-in Language reference and
the compiler pinned by the BEX publication to read the selected archive,
verify the whole-function references and empty effective constants, and
compile the Plan and its three admission steps. The gate derives the exact
scope from the compiled calls and models the selector with archive identities
to check the stock read trap and custom fallback. Java runtime qualification
covers native definition reads and the original admission and Reseller flows
at the published gas limit.

`python3 tools/release.py assets --output build/release` prepares the selected
archives, their catalogue and checksums. It does not overwrite existing output
or publish anything. The release workflow prepares artifacts for pull requests
and main. A separately authorized `blue-packages-*` tag publishes its exact
reviewed collection through GitHub Releases. Never reuse a published version
or BlueId for changed content. Retain upstream notices and resolve licensing
before public distribution.

[Public semantic cards](semantic-cards.md) are committed separately from package
archives and published to S3 by their own workflow. Missing descriptions or a
failed model/upload job do not block this package release. Locally generated
cards are reused; GitHub generates only missing exact type identities.

Demand builds, release preparation and reference-model gates for Demand are
currently deferred. There is no active Demand CLI selector or parallel build
tree. Preserve the historical bytes and follow [reactivation provenance](demand-reactivation.md)
when Demand is enabled again. Current Java behavior qualification uses Access
Events and remains a separate local/Core gate.
