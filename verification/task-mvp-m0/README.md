# Task M0 compatibility prototypes

These are experimental source definitions, not released `Tasks` exports. They are
outside `PACKAGE-SOURCES.json` and the current catalogue. M1 must not consume them
as a finished Task protocol. The authoritative design is Business documentation
commit `878c01bf78589ef49ef265e7ef85fa878b197334`.

`source-selection.json` pins the current relevant native and clause definitions.
The full selection remains Core's `packages/current.json`; no historical package
is substituted. `manifest.json` selects the prototype exports in dependency order.
The shared function, two distinct launch policies, sole state claim and separate
native termination policy exist to qualify the composition interface. Fixed
`/work` and `work` bindings are deliberate M0 limitations, not the public M1 API.
The prototype does not implement finality, configuration governance, report-size
limits, complete authorization, dynamic target validation or recurrence.

Export to an explicitly selected Core checkout:

```sh
python3 tools/export_task_m0.py /absolute/path/to/myos-core
```

Then, in that checkout using JDK 21:

```sh
bash runtime/gradlew -p runtime :blue-core-service:test --tests blue.core.TaskM0Test --tests blue.core.TaskM0BootstrapTest --no-daemon
```

The tests build an exact `TaskM0` package under ignored `reports/task-mvp/m0`,
check exported-source hashes, and execute native Contracts and real local signed
provider/bootstrap fixtures. No HTTP authentication or cloud deployment is implied.
Core's `docs/guides/TASK-MVP-M0.md` describes outcomes and unresolved gates.

A passing **gap reproducer** is not a passing acceptance row. In particular,
`dynamicMatcherProjectionAndReferenceGapsAreReproduced` intentionally demonstrates
why its generated matcher paths must not ship. The named-definition fixture separately qualifies exact-node transport and a
common native envelope with native status-specific matching, including cold
snapshot replay. The unsafe anonymous recipe is not a supported fallback. The package contains no invented
Language Definition wrapper, raw-source matcher or witness workaround.
