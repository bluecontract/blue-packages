# Current canonical package candidate — 19 October 2026

One current Contracts publication and one current Coordination publication are
selected. Python and Java consume all 34 catalogue archives, six native archives
and two host catalogues byte for byte. Predecessor runtimes and live migration
are unsupported; historical sources remain evidence only.

Package qualification passed: 34 archives and 965 source files, 133 unit tests,
33 exact native rebuilds, both publication reproduction checks, and all 38
release-asset checksums. Java passed its 735-test clean release, additional
consumer/adapter gates and all 35 selected examples with replay checks.

The full Python comparison and independent final audits are still running.
This branch is a release candidate, not a completed cross-language release.
See `../evidence/single-version-20261018/candidate/status.json` and the adjacent
command, source and completion reports for the recorded qualification snapshot.

Timer execution, live AWS/MyOS integration, MyOS-specific stores and live data
migration are outside scope. No remote push or publication was performed.

## Publication labels

The current Contracts rules Text is
`CtkLgRedUzmATDLLy3JQbbTvrVcK1hgEbk34oAAZEfrp` (deterministic edition 3).
Its complete publication retains an inherited `final-gas-1` opening label.
Coordination's checksummed README similarly retains `0.2.0-access-events.1`,
while selected package metadata is `1.0.0-deterministic.1`. These are disclosed
prose inconsistencies; neither selects a predecessor runtime. Correcting them
requires a reviewed immutable publication/archive revision and updated pins.
