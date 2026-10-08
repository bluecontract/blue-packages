# Preparing a publication

`PACKAGES.json` selects the one current source set. All archives remain unpublished
candidates until an explicit reviewed release.

Run `python3 tools/sync_catalogues.py --check`, `python3 tools/release.py check`
and `python3 -m unittest discover -s tools -p test_release.py`. Rebuild changed
source packages with Java 21 and `tools/build-payment-family.sh`; compare exact
archive hashes on a second build. Native changes additionally require runtime
qualification; data installation cannot grant native support.

`python3 tools/release.py assets --output build/release` prepares the 30 selected
archives, their catalogue and checksums. It does not overwrite existing output
or publish anything. The release workflow prepares artifacts for pull requests
and main. A separately authorized `blue-packages-*` tag publishes its exact
reviewed collection through GitHub Releases. Never reuse a published version
or BlueId for changed content. Retain upstream notices and resolve licensing
before public distribution.
