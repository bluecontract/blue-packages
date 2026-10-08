# Distribution

`PACKAGES.json` is the complete current catalogue. Every package has one selected
root directory, a BlueId and an archive SHA-256. `tools/release.py check` verifies
each archive, unpacked distribution, dependency lock and catalogue closure.

`tools/release.py assets --output build/release` prepares deterministic archives
for review. Preparation does not publish them. These candidates require a
separate reviewed release; package installation does not install native handlers.
Older exact publications remain immutable replay inputs in consumer runtimes.
