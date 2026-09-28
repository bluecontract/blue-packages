# Verification and provenance

Current checks are documented in [publishing](../docs/publishing.md).
Run `python3 tools/release.py check` for selected archive, source-inventory and
distribution integrity; use `tools/verify_packages.py` with the installed Blue
Python reader for semantic identities and original source locks.

* [Foundation evidence](foundation-20260926/README.md) records the September 26
  Language/BEX/Contracts publication checks and their limits. The reports and logs
  are historical outputs, not a new full-runtime qualification.
* `reference/` retains the three original, independently source-locked reference
  snapshots used by foundation conformance tools. They stay outside release bundles.
* `publications/` retains historical exact data releases, including the original
  Mutual Activation publication used by older Java pins.
* `provenance/` contains the original Agreements import record and reseller build
  selection. Current archive selection is `../SHARED-PACKAGES.json`.
* Package-local `verification/` directories retain each package's own evidence.

Package integrity does not establish behavioral parity, complete scheduler support,
performance or production qualification. Consult the live consumer repositories
for their current runtime reports. Time's fixture explicitly does not approve native
scheduling. Empty error captures and generated caches are not retained as evidence.
