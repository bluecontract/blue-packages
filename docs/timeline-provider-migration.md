# Timeline-provider package selection

The top-level `blue-coordination` now contains the former temporary package,
version **0.2.0-rc.2**, with 53 exported types. `blue-coordination-temp` is removed.
There is one required `Timeline Provider.endpoint`. Its inherited or instance value
is the REST API base for both public and private timelines. Per-timeline endpoint
and `readUrl` overrides are removed. Types determine versions.

The [specification](../blue-coordination/spec/coordination.md) starts with the
Contracts requirement for timestamped inputs, then defines timelines, entries,
providers, access and the feeder obligations. Cycles remain a Contracts concept.
The [worked examples](../blue-coordination/docs/examples.md) contain the ACME
provider subtype, human and agent actors, Hello entries, real access documents,
signed private reads and keyless public reads.

## Consumer migration

The root Agreements, mutual-activation, immediate-termination, reseller, agreement
examples and Time packages have new publications importing the selected
Coordination package. Their exact identities and archive hashes are in
[TIMELINE-PACKAGES.json](../TIMELINE-PACKAGES.json). Explicit references to changed
export identities were rebuilt along with their dependencies.

Coordination no longer owns generic business Event, Request, Response or Authority
base types. Consumer business messages are standalone definitions; responses keep
an explicit typed `inResponseTo`.
Actor subtypes represent identified entities: Principal Actor for a human and
Agent Actor for a non-human. They do not duplicate provider identity.

These are data-package publications. Native Mandates/Time approvals and prior Java
qualification reports apply only to the exact identities named in those reports.
The historical `native-support.json` is retained as historical evidence and does
not approve the new selection. A live MyOS host must explicitly integrate and
qualify the new Timeline Channel/provider rules before adopting these packages.
The standalone AWS provider uses the new Coordination access protocol directly.

Mandates retains the upstream predicate-context publication and its original
Coordination dependency. Its source lock uses the preserved pre-timeline-provider
archive; it is excluded from the timeline selection and consumer builder.

## Historical imports

The previous top-level publications are retained without changing archive bytes in
`editions/pre-timeline-provider/`. Historical editions retain their old semantic
imports. Source-lock paths point to the matching preserved archives so updating
the current Coordination folder cannot accidentally change their meaning.
`SHARED-PACKAGES.json` continues to include the embedded-clause historical cohort;
`ROOT-CLAUSE-PACKAGES.json` selects the current root-clause cohort.

## Reproduction

The Coordination launcher checks and uses its Contracts dependency's pinned
reference runtime:

```sh
cd blue-coordination
./blue-package test
./blue-package check
```

The consumer data-package builder likewise selects that exact runtime and checks
source/lock/archive equality. It does not register native runtime support:

```sh
python3.13 tools/build_timeline_dependents.py check
python3.13 tools/release.py check
```

The older native qualification/build adapters remain available for historical
releases; use the dedicated timeline consumer builder for this selection.
