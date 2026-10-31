# Access Events standard build and publication preparation

> Historical implementation and validation record. The subsequent user decision
> defers all Demand builds until reactivation. The parallel Demand snapshot,
> selector and newly generated `.demandscoped.10` candidates described below have
> been removed; they are not current supported build/release paths. Access Events
> publications and their validated business fixes are unchanged. See
> [current Demand status and retained provenance](demand-reactivation.md).

This report records the original default migration. The subsequent exact-reference
fix and current rebuilt publication identities are recorded in
[source-binding integration](source-binding-access-events.md).

Verified source HEAD: `4ca6a0a26c233a25e605fa67189c9b428f66af10` (initial working tree clean).
Native Java validation: Core `19820cfdc01325aa119a162fa95f7e054608e3f8`, Java 21;
Core test classes and runtime dependency JARs rebuilt before qualification.

## Default and provenance

Before: root `build_final_gas.py all` and `release.py assets` selected Demand
Contracts `Cj2SnbMNz9VkQg9Dc7hzEoy7GdBUYqTfzh1XCKu5ANSr` and receiver-relative
Coordination `8LBAZGgzAvrDRHxbHDGhb3DTPZyZUgJeKMEq3xBrLo8C`, despite
`PACKAGE-SOURCES.json` declaring the generic `core-java-final-gas` label.
After: those commands and CI asset preparation use Access Events, with exact
Contracts `AibxCqz62K19mhRWXuWhnZJx6a3o5UXU7sRnAhoUNnFD` and Coordination
`4gmSjwn3DCYBVeDieXxuXgsPvvz2dU6ovFXnnuyv2RjA`; source profile is
`core-java-access-events`. Both commands accept explicit `--edition demand-scoped`.
The shell builder retains its namespace-selection arguments and accepts the same
explicit edition option.

The retained AE collection was copied from Core
`75b8c4ddf031c44e66fb096306bfdbef0a559d3b`, recorded in
`semantics/collections.json`; this is provenance, not a claim about today's deployment.
Every one of its 32 archives was matched by exact SHA256 to local Git history.
Activation matches `0f93177de93e655f9393da0ae57970d50f32f735`; Clauses and
Coordination match `ce4b53f468e70794fe6f1dec59b024735fb10784`; Contracts matches
`e260202fb3e6ebdc3f5d5c169980bfc29874b7b5`. Mandates, Representation and Tasks
are absent from the Core collection, so their existing AE publications at
`0f93177de93e655f9393da0ae57970d50f32f735` complete the repository's 35-package set.
The [machine-readable comparison](../provenance/access-events-default-20261030/publications.json)
records every package's source commit, previous AE, current Demand and resulting
version/BlueId/checksum. No remote fetch or deployed inspection was used.

## Business changes and rebuild scope

`ab3fd6af5c6477851a40eefbf08846692c627b02` removes Activation's
`channelsAdmittedAfter` write and `REQUEST_PRECEDES_PARTY_ADMISSION` timestamp
rejection. Comparing each package's actual exported source, README and declared
publication files against its byte-matched AE baseline identifies only Activation
as a direct change. Its HEAD business source is retained unchanged. The fix uses
existing AE bindings and needs no new native operation or protocol semantics.

The late-party consent/access-recovery fix
`eb5b500180ce1ccb98e937c3a6e6128bcc816933`, operation input declarations and
Clauses composition are already present in the retained AE source/artifacts;
they are not new Demand-only business changes. All non-Activation business type
sources match their individual AE source baselines. Clauses therefore retains
`0.8.0-preview.1` / `C9cUTUFLvLGE2eJ7fv4MsMS53ZPvray5Xrkf4XWmG6vL`.

The declared import graph propagates the changed Activation identity to eight
consumers. No unrelated package version was bumped. Full standard build verifies
the complete graph; the other 26 archive files remain byte-identical to their AE
baselines. `blue-time/SHA256SUMS` was stale even for that retained publication;
its inventory was refreshed to the exact retained bytes (no new package identity).

| Commit/change | Package | Rebuild | Result version | Result BlueId |
|---|---|---|---|---|
| `ab3fd6a` cutoff removal | `clause-activation` | yes | `0.8.0-preview.4.access-events.1` | `HCmZUdahMLbWGKP3bpojuonkqw6mxsb5vUBY5L765GtK` |
| New Activation dependency identity | `clause-documents` | yes | `0.8.0-preview.7.access-events.1` | `FYwuFKekhe3xBL9BzAPUQDT8uqtAAmG8uZrxJ8PUhjU8` |
| New Activation dependency identity | `clause-payment` | yes | `0.8.0-preview.7.access-events.1` | `Cu4S5AQXazkEfrbHsPYNW6rjNhvK2RN4JWqcx8PfqUkX` |
| New Activation dependency identity | `clause-inspection` | yes | `0.8.0-preview.7.access-events.1` | `ExGbd7qM8FseN1dR7suuAcKWp2STNL5AzQJSRvN6jmNi` |
| New Activation dependency identity | `myos` | yes | `0.8.0-preview.7.access-events.1` | `AKhnySWTi6mi4RRV5Xjzc5dPt7GnjTjzAdQbNCi6bxNN` |
| New Activation dependency identity | `acme-bank` | yes | `0.8.0-preview.7.access-events.1` | `CBMnkzgxHFKafLzPwmpGgL4GAwzvk6ruAJxyXMKY5V2X` |
| New Activation dependency identity | `manual-payments` | yes | `0.8.0-preview.7.access-events.1` | `ECg8biDDpKSUSicUfcaaERGXC1qeA8XVvBAr95qfWyok` |
| New Activation dependency identity | `shipping-instruction` | yes | `0.8.0-preview.7.access-events.1` | `5AX8Rs4VBTB1Wp8gNkW1z9xeBn7c6X1TRnSEevpofNy6` |
| New Activation dependency identity | `clause-attachments` | yes | `0.8.0-preview.7.access-events.1` | `9Uj86MMcabhuiJntwVoyJwGmftCjirtGafe7irjn3Aa3` |

## Immutable publications and explicit Demand

Existing `semantics/sources/myos-access-events` archives are unchanged. All 35
previous Demand archives remain exact: changed archives are saved under
`editions/demand-scoped/archives`, identical ones are referenced at their existing
paths. The edition manifest preserves configs, locks and differing native source
files. Unchanged business sources are shared. New exports/import changes fail
closed until the explicit overlay is updated; shared source changes require a
full Demand rebuild before assets can be prepared. Rebuilt Demand output lives
in ignored `build/demand-scoped`, so preparing it never switches the standard tree.

Three preexisting source/publication documentation discrepancies were found:
Contracts `spec/contracts-demand-scoped-draft.md`, Contracts
`spec/contracts-demand-scoped-conformance.md`, and Coordination
`docs/reference-algorithms.md`. Commit `169ad6f` clarified metadata-only Contracts
roots without republishing the frozen native edition. Its draft source differs
from the frozen hash, so a plain rebuild first failed `Unfrozen rules`. After
restoring that exact rule text, the other two document differences still changed
archive bytes and propagated archive checksums through consumers.

The explicit Demand overlay preserves all three documents exactly as stored in
the immutable archives (`frozenSourceRepairs` records this), and its Contracts
source checksum inventory is updated to those exact files. All newer root source
documents remain unchanged from HEAD. A complete comparison of all 35 packages'
declared README, documentation and protocol input files found no further drift.
This does not publish newer commentary under an old identity or change normative
semantics. The first failed build and the later non-reproducible full build are
not counted as successful reproducibility evidence.

## Runtime limits and verification

Demand's native scoped execution/replay and receiver-relative source expansion
remain Demand-only: independent original-full-K source catch-up, frozen receiver
anchor, original-time grant/revoke, durable WAIT and terminal denial are specified
in `blue-coordination/spec/receiver-relative-replay-next.md` (248–264). They are
not simulated on AE by ID substitution. New source-transport/compact-receipt/BEX
result-value commits visible on other branches are not ancestors of the inspected
HEAD and were not silently merged.

Passed locally: standard full native AE build; release assets and all asset
checksums; source/dependency/distribution integrity; 13 release, 4 build-order,
5 edition and 30 semantic-card tests; static payment-family and clause-tutorial
checks. The same local commands used by CI prepare AE by default and check Demand
explicitly. Reference Demand/receiver algorithms passed under Python 3.14;
their report explicitly leaves Java paired vectors `NOT_VERIFIED`.

Native AE behavioral qualification passed four cases (`access-events-behavior`,
`activation-inputs`, `activation-effects`, `source-binding`) against the exact Core
commit above. Before rebuilding, the retained AE baseline failed the timestamp
regression with `REQUEST_PRECEDES_PARTY_ADMISSION`; after rebuilding it passes.
Consent, authorization negatives, fresh consent after party replacement,
observation gating and Clauses recomposition remain checked. Local evidence:
`reports/access-events-default/candidate/report.json`.

The final explicit Demand full build also passed. All 35 rebuilt archives match
the preserved originals byte-for-byte, and the entire catalogue including mounts
is identical (`reports/access-events-default/demand-rebuild-comparison.json`).
Demand release preparation and asset checksums passed. Six native Activation
effect scenarios passed with Demand Source Expansion plus DefinitionRead against
that same exact catalogue (`reports/access-events-default/demand-evidence.json`).

Full dual-edition native builds and behavior checks exceed the six-minute target
because this task explicitly requires both complete dependency graphs and runtime
behavior. No remote CI run, production deployment, Business/Core remote E2E or
complete Demand-runtime qualification was performed. No publish, push or deploy.
