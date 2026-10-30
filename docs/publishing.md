# Preparing a publication

`PACKAGES.json` selects the standard Access Events source set. All archives remain unpublished
candidates until an explicit reviewed release.

Run `python3 tools/sync_catalogues.py --check`, `python3 tools/release.py check`
and `python3 -m unittest discover -s tools -p test_release.py`. Rebuild changed
source packages in dependency order with Java 21 and `python3 tools/build_final_gas.py all`; compare exact
archive hashes on a second build. Native changes additionally require runtime
qualification; data installation cannot grant native support.

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

Demand is an explicit alternative, preserved without overwriting prior archives:

```sh
python3 tools/build_final_gas.py all --edition demand-scoped
python3 tools/release.py assets --edition demand-scoped --output build/release-demand
```

The second command uses the same isolated rebuilt candidate. A change to shared
business source requires the full build first. Interface changes require updating
the explicit Demand overlay and its declared expected Access Events configuration;
they are never silently discarded. The release workflow prepares Access Events
assets by default and separately checks the explicit Demand archive closure and
reference models. Java behavior qualification is a separate local/Core gate.
