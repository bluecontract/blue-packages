# Demand builds deferred

Access Events is the sole current source, build, release-preparation and runtime
qualification path. The user deferred Demand package builds until Demand is
enabled again. There is no active edition selector, source overlay, isolated
materializer or automatic Demand CI requirement. Newly generated Demand `.10`
candidates from the earlier PR iteration are removed. No Demand packages were
rebuilt for this simplification.

## Preserved history

`retained/demand-scoped-baseline/publications.json` identifies all 35 original
Demand publications selected at source commit
`4ca6a0a26c233a25e605fa67189c9b428f66af10`, with exact versions, BlueIds and archive
SHA256 values. Its 32 differing archives are retained beside the manifest; the
three identical native archives refer to their unchanged root paths. These
historical bytes are checked by release-tool tests, but are not active release
selections. The original `retained/blue-coordination-v1` archive and previously
committed semantic source collections remain untouched.

Exact authored Demand source/configuration is recoverable from that Git commit.
The later integrated source-binding fix is shared in the current root source
(and introduced in `1baec803648d2e11ee61a95f80b8027d33a6c5e9`); Activation's
compatible cutoff fix also remains in the current Access Events publications.
Existing root Demand specification/reference documents remain available. There
is deliberately no second live authored source tree. The retained archive set
alone is not a standalone checkout or a currently qualified Demand rebuild.

## Reactivation requires an explicit change

When Demand is enabled again, recover its exact native authored sources and
configuration from the recorded commit, reconcile current business-source and
interface changes, select the intended exact Core Demand runtime, and build
only the genuinely affected dependency closure under new immutable versions.
Requalify behavior and release preparation before selecting those publications.
Do not infer compatibility by changing a suffix or BlueId. Demand's source
catch-up, original-time access and frozen receiver-anchor guarantees still
require its native runtime semantics.

This simplification changes build tooling and historical storage only. Current
Access Events archive hashes, selections, dependency locks and business sources
remain unchanged from `d494a0385885c5ef7cc7d672cfb32579735b598e`; the earlier native
behavior evidence therefore remains applicable to those publications.

## Simplification validation

The passive publication manifest is checked against all 35 original archive
SHA256 values. The simplification removes 191 tracked paths and adds 34 (32
historical archives, their manifest and this document): net 157 fewer files and
about 52.29 MiB less tracked content than `d494a03`. The original PR's 181-file
Demand overlay/materialization tree is gone. Older implementation reports are
marked historical and do not advertise active Demand support.

Release and build-tool tests pass, including rejection of the removed shell
`--edition` option before Java starts. The operation probes compile and pass
Access Events public source binding and native argument qualification. The
retained earlier eight-case Access Events behavior results apply to unchanged
publication identities and exact Core
`19820cfdc01325aa119a162fa95f7e054608e3f8`. Demand was not built or executed during
this simplification; remote CI is assessed separately on the pushed commit.

The ordinary full build completed successfully and reproduced all 35 Access
Events archives byte-for-byte, with the complete package catalogue unchanged.
Standard release asset preparation, asset checksums, catalogue consistency,
semantic-card integrity, payment-family and tutorial checks passed.
