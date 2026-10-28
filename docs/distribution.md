# Distribution

`PACKAGES.json` is the complete current catalogue. Every package has one selected
root directory, a BlueId and an archive SHA-256. `tools/release.py check` verifies
each archive, unpacked distribution, dependency lock and catalogue closure.

`tools/release.py assets --output build/release` prepares deterministic archives
for review. Preparation does not publish them. These candidates require a
separate reviewed release; package installation does not install native handlers.
Older exact publications remain immutable replay inputs in consumer runtimes.

`PACKAGE-SOURCES.json` may additionally pin `retainedArchives` by repository-relative
`path`, `packageBlueId` and `archiveSha256`. These immutable data dependencies are
not current namespace selections and are never rebuilt. Builds and release checks
validate their exact bytes, member inventory and embedded dependency closure.
An importing prefix must not appear in `executionRequires` or `protocol.requires`;
its source path and generated lock must match the retained pin. Release bundles
include these archives as `retained-data` entries, separately from the active
catalogue. An undeclared or changed archive remains an error.
