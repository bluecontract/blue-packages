# Preserve exact source references in both package editions

Baseline: `97b00234140bec8dcbdfc5b4600adb8dec1cf70f`. Selectively integrated
source fix `5d81c077fcd27a95b50daf28e8a53a13e0494391`; no generated publication
was imported from that branch. Core validation uses
`19820cfdc01325aa119a162fa95f7e054608e3f8`, freshly built Java 21 artifacts.

`Documents/Source Binding Input.document` now preserves the exact supplied
reference instead of intersecting it with a structural initialized-document
matcher. For a real initialized cyclic document, that intersection could change
the native identity and request unrelated history, returning `NEEDS_RESOURCES`
instead of binding the supplied source. Initialization, source identity, owner,
party and admission validation remain in the existing execution functions.
The public input accepts an unconstrained reference; runtime rejection of invalid
sources remains tested. Consumers need the new Documents publication and its
reverse dependency closure. Existing immutable publications remain available.

Access Events remains the standard build/release default. Demand is explicit
`--edition demand-scoped`; this source fix is compatible with both editions and
does not require Demand replay semantics. Activation's earlier timestamp-cutoff
fix is unchanged, including its Access Events publication BlueId.

## Independently rebuilt publications

Exactly eight packages changed per edition; all other 27 archive hashes and
identities are unchanged from the baseline. Full before/after versions, BlueIds
and archive hashes are in [the provenance mapping](../provenance/source-binding-access-events-20261030/publications.json).

All eight Access Events versions advance `0.8.0-preview.7.access-events.1` →
`0.8.0-preview.7.access-events.2`; their Demand versions advance
`0.8.0-preview.8.cutoff.1.demandscoped.9` → `0.8.0-preview.8.cutoff.1.demandscoped.10`.

| Package | New Access Events BlueId | New Demand BlueId |
|---|---|---|
| acme-bank | `APzDLFNUgeyHP5wJ4brf5VCFpvvpuY9FcRfQAbvx2fe4` | `9qCNbzG6Dx4Seop1YZER3mnQM7xsPESanUD45B4PP5RZ` |
| clause-attachments | `ELRG8m6da1ksH5B7mkCchefd2oEjXzaxTCwidFS5rKXG` | `FqnbdL8ZXGhFtQ7ZDNWvj78BwMCjzsLahFfXguCDcjqy` |
| clause-documents | `5QVeHmuCN2YhE4fkLvxkbNdLAFWnsMhHqcUpR3PzesXm` | `74sTGLoXFQMwbMm9v1Tjnivd6caCiFUXG9z7a9Ut2VTU` |
| clause-inspection | `7bA8gsDi8wgJLVav4rBoWx9ZBcS192jByXCod9LqwURK` | `CmyJ6Lux8kG3g315K7fpixSLr8WrLZ4gLkBT4wYKDaZx` |
| clause-payment | `6Ltp1WA5C68VrFaNoSjGwKxwSf81mMteUFgFD8Ufw1Q4` | `DMQ421terR3iy6r637iXtncgP6vgwrP7sLC8FbkCQBz4` |
| manual-payments | `8UmfvSGCGnu1GkrSUNVEHC5Tmfjvt5kBg6x71PUnJaoJ` | `C3Cd1dMp6DQAnNhj3Fx1hjPW6c5ontAoEQLHYffXYhEr` |
| myos | `AZLWngUht4rEF1t8wD1hcUBmRrL3KMFoKYyKrkfoBwQ` | `wANKV4unK9rMMdJdemb8nxW1Lr28JNts2WXZeJhCqXo` |
| shipping-instruction | `HDHoWNZeDcKFbqoSAbSBzkgpMjKffXFJcJ31sbtoFFVh` | `EPTdqAcWJU7GPEVhfiroFAg76XG4Vxumfc2HYxurcDfr` |

Old Access Events archives are retained under
`retained/source-binding-access-events.1`; old Demand archives are retained under
`retained/source-binding-demandscoped.9` and their original edition archive paths
remain untouched. Both edition indexes declare their retained publications.
New Demand archives use `editions/demand-scoped/archives/source-binding.10`.
The Demand shared-source hash and active snapshot were updated only after the
complete explicit Demand build succeeded.

## Verification boundary

Both ordinary `python3 tools/build_final_gas.py all` and explicit Demand full
build completed successfully. Complete graph builds and both runtime editions
exceed the usual local six-minute target because the requested compatibility and
immutable publication evidence require those independent rebuilds.
Behavioral regressions use actual native Core processing, including public
DocumentClause prepare/configureSources-generated requests; they are not HTTP,
Business E2E or deployed-production checks. No release, deployment or merge is
performed by these local checks. Demand-specific frozen-anchor, original-time
access and source catch-up semantics remain Demand-only as recorded in the
[default migration report](access-events-default.md).

Local package/CI preparation checks passed: 13 release tests, five edition tests,
four build-order tests, 48 semantic tests and `semantic_cards.py check`; release
checks, asset preparation and generated asset SHA256SUMS for both editions.
The CI Demand and Receiver reference scripts passed using installed Python 3.13
(the system Python is older and cannot run their bootstrap). Those reference
scripts retain their own `NOT_VERIFIED` scope declarations; they do not substitute
for the native Java behavior regressions. Remote CI for this follow-up commit is
pending until it is pushed.

Native RED→GREEN evidence: both direct cyclic binding and the actual generated
public request failed on baseline `97b0023` with `NEEDS_RESOURCES` for a synthetic
history identity. The rebuilt Access Events candidate passes eight cases: public
binding, cyclic and noncyclic binding, rejection guards, routing, history, replay,
and the earlier Activation business regression. Explicit Demand passes cyclic
and public binding plus all six Activation execution scenarios. The final
failure-diagnostic helper was also rechecked on the Access Events public case;
it formats details lazily to avoid an eager successful-result diagnostic dump
exhausting the test JVM heap. No behavior assertions or heap limits were relaxed.
Local logs/reports are under `reports/source-binding-exact-reference/`, including
`public-red.log` and the `ae`, `demand`, `demand-diagnostics-fixed`, and
`ae-diagnostics-fixed` report directories; these are local evidence, not deployed
checks or newly committed artifacts.
