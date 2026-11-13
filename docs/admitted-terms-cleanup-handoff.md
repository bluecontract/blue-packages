# Admission-proof cleanup handoff

Base: `a5f4ef2a59e34c44ef8cb1f153fbfa0779b921f7` (includes PR #47).
The resulting commit is recorded by the final handoff outside tracked content to
avoid a self-reference. This package candidate is for subsequent Core import and
qualification; it does not establish deployment or complete product readiness.

## Behavior and source changes

Ordinary provision validates the prepared source, effective policy, declared
slots and each party's identity. An extra undeclared party fails with
`PREPARATION_UNDECLARED_PARTY`, including after legitimate admission in the
candidate. Admission completion no longer creates `admittedTerms`; an old field
is not independently prohibited. There is no new revision/history restriction,
legacy mode or migration.

Removed from the action library: `providedInitialTerms`, `providedAdmissionPlan`,
`providedAdmissionProof`, both `WithAdmission` validators and the action-only
`assembleAdmissionPlan`/`assembleAdmissionDefinition` copies. `validateProviderSlots`
now contains the complete ordinary validation. Bootstrap provision calls the
unchanged `validateBootstrapAccess`. Reseller action pins and provenance follow
the new Documents definition; hook planner functions remain.

Preserved from the mixed historical commits: static `$nodeBlueId` predicates and
operand restrictions, Activation operation-type checks, normal `initializeTerms`
and `commitState`, the extracted general admission planner and its exact function
reference, admission consent/ledger/access/rebase and token freshness checks,
`maySelectInactiveCandidate` and refresh canonical/custom-library behavior.
`sharedProvide` retains its general record copying.

The retained `Admission Step Functions` library has new exact pins for
`admissionInstallRequest` and `finishAdmission`. Its complete manifest/export
remains. The existing native builder first produced an intermediate package
without that unreferenced export to obtain the changed function identities, then
the full export manifest and library were rebuilt. Intermediate output is not a
deliverable. Historical archives remain unchanged.

## Artifact identities

All paths below are `<directory>/dist/package.bluepkg`; their package manifests,
repository data and locks are committed beside them. `PACKAGES.json` selects the
complete 41-package family; `SHARED-PACKAGES.json` and
`PAYMENT-FAMILY-PACKAGES.json` are regenerated views. Nine archives changed:

| Directory | Package Blue ID | Archive SHA-256 |
| --- | --- | --- |
| clause-documents | `3crc6BXf3goCVoGhpvQ3hpa4VaMedCDC4KWfggdgy8Up` | `364acb2a6be16e1877963553b63156476072d03fa4c6357cbb155ebdc51398d6` |
| clause-payment | `C4zt6j6D2QHERc5XajmWHL8oLRu5FuQDPCaxGFiP22Dt` | `d7277eb8f278037730a2850dfe1719ef839365e58871964b525d05b9b940dfce` |
| clause-inspection | `9hDo24EXwf2Ez5KWRKW4VqtA5usnfPjRevej7BnTN3GY` | `14e0a92e28f4dd07d7dbc2112ef0fe4f187240e8d90c401c1450efd565bbb692` |
| myos | `DpMJRTCbqSdwrWEXyEpMAKfr5oKX9sdA6ZGqiorTYine` | `f0e7d8d66df16a46bcaa886a0dae323d01dd382651b59a3a71618ad1d6fe29fb` |
| acme-bank | `8akC3kPjWP1GqR1ASAQ1cTrL3bL3fj6vLgyPoee32VWe` | `68f7594815fd0cba07213d60d4256c137eaadd2f18c73c2275ed6f010eb75fc3` |
| manual-payments | `4qcMm12xhcf8EDL9MBNYhNTmemHTYJTe2e2BxvkoruvD` | `46b72ddf60612501eabf3a14e7cb1258219288da5543b1f85f991e035c2a7647` |
| shipping-instruction | `GrkVT9veVque4L1a7jJCug34sSuTmFDFhRHqEaAXVsvU` | `7b9c302f76594c52f3f6942e017628662046ba19da1e07a25475d7a7531acdc6` |
| clause-attachments | `HvrQWykPN11hWQcUdcPfDEgo9bpZJT56tq95P5cWuGvg` | `0359bd75848e3323827a662e68245eaaf5249423b784519c3ef7dd15bf8cbaea` |
| clause-reseller | `4jCp51k6cZo2Ev4mHh4a66CFsfmrZANa2MaJHSNsopYD` | `85ced6ceabfd86e774ed15428cc4e403ff09f3fb80bf38b97ba98127716ab247` |

The selected-archive scan checked all 41 complete archive record sets: no
`admittedTerms`, `previousTermsRef` or uniquely named proof helpers remain.
Comparing base and candidate catalogues found no changed archive bytes under an
unchanged package Blue ID. Historical archives and intentional rejection tests
are outside that absence assertion. Exact machine-readable rows are in the local
`reports/admitted-terms-cleanup/candidate-artifacts.json` handoff.

## Build and qualification provenance

Only Blue Packages sources/artifacts changed. Core supplied existing runtime
binaries/classes from its clean checkout at
`13684059ba0cd5744da6d523b338496873eb5ab1`.
The runtime is Access Events with DefinitionReadV1; no Core import or build was run.

```sh
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export BLUE_JAVA_CLASSPATH="$(cat /home/piotr/.codex/worktrees/admission-gas-20261112/myos-core/reports/core-http-test-classpath.txt)"
python3 tools/build_final_gas.py clause-documents
# Refresh the two changed Admission Step Functions pins using native identities;
# restore the complete manifest before producing final artifacts.
python3 tools/refresh_reseller_composition.py
python3 tools/build_final_gas.py all
```

The full dependency-ordered build completed successfully. Its log creation/final
write interval was 295.06 seconds; no separate process stopwatch was installed.
All 157 classpath entries existed at preparation. The colon-joined classpath text
SHA-256 is `a481826136da1cb245bdb47e23b9df79f126a60e733616c0673f67dfb0a1bb83`.
The qualification runner records the complete entry list and tested source bytes.

Behavioral RED on the base candidate failed after real owner approval and consent:
`Ordinary provision must reject an undeclared admitted party` (30.15 seconds).
The final native probe preserves actual admission, adds absence/plausible/tampered
witness rejection, checks unchanged parent/effects, and separately exercises
ordinary provision, actual commercial approvals and idempotent retry. Fresh/stale
token predicates use explicitly modeled consent; they complement actual consent.
Same-count party identity, source, policy, allowed-but-changed slot and requirement
negatives are included. Existing reader account/key/access guards remain in
`BootstrapPreparationConformance`.

`AdmittedTermsConformance` and its obsolete external capture dependency are
removed. `ProvidedOrderAdmissionConformance` now independently qualifies general
planner parity, exact references and custom definitions, without proof recovery.
The native runner exposes `admission-planner` and `reseller-bootstrap-pins`.

Local reports and logs live under `reports/harness/remove-admitted-terms/`,
`reports/admitted-terms-cleanup/` and `reports/operation-input/`.
The reviewed candidate passed these targeted native cases. Seconds below are
native subprocess time; harness command time also includes compilation and
receipt checks.

| Case | Result | Native seconds | Evidence |
| --- | --- | ---: | --- |
| `refresh-definition` | PASS canonical/custom-helper/custom-constants/Reseller | 27.654 | harness log `0006` |
| `admission-provision` | PASS actual admission, all roster/slot/source/policy/requirement negatives, commercial gate and retry | 34.680 | harness log `0014` |
| `admission-planner` | PASS exact references and canonical/custom native declaration parity | 53.582 | harness log `0008` |
| `reseller-bootstrap-pins` | PASS all 109 exact pins and provenance | 3.539 | harness log `0015` |
| `bootstrap-preparation` | PASS modes, reader account/key/scope/access guards | 50.804 | preservation report |
| `static-identity-predicate` | PASS valid source and invalid operand rejection | 1.289 | preservation report |
| `admission-definition` | PASS canonical/custom admission definition selection | 25.174 | preservation report |
| `admission-consent-declarations` | PASS consent declaration identity parity | 9.523 | preservation report |

```sh
python3 tools/check_operation_inputs.py --case refresh-definition \
  --case admission-provision --case admission-planner \
  --case reseller-bootstrap-pins --report-dir reports/admission-cleanup
python3 tools/check_operation_inputs.py --case bootstrap-preparation \
  --case static-identity-predicate --case admission-definition \
  --case admission-consent-declarations \
  --report-dir reports/admitted-terms-cleanup/preservation
python3 tools/build_final_gas.py clause-documents --check
python3 tools/build_final_gas.py clause-reseller --check
python3 tools/build_final_gas.py clause-payment --check
```

The four required native cases were actually run individually through the harness;
the first command groups their selectors for reproduction. Refresh and planner
PASS results were explicitly reused after reviewed test-only changes outside
their compiled source closure. The four preservation selectors ran together
(batch including compilation: 92.667 seconds).

All three selected reproducibility checks passed every distribution byte and
lock: Documents 31.691 seconds, Reseller 37.546 seconds, Payment 19.085 seconds
(harness command time). Other dependent archives were freshly built and included
in the complete checksum/closure scan; separate per-package reproducibility
checks were not run for those unchanged-source dependents. Activation artifacts
were unchanged and its separate rebuild check was not run.

Four focused Python groups passed (admission definition closure, Documents
refresh closure, Reseller refresh closure and Reseller composition). The existing
`check_admission_scope.py` passed the complete Plan and three admission steps,
15-function exact closure, stock read trap and custom selectors.
`sync_catalogues.py --check`, `release.py check` and whitespace checks passed.

Two intermediate qualification failures are retained, separately from the
baseline behavioral RED. Log `0007` lacked the modeled helper's required
`bindings` constant (33.214 native seconds); the fixture now supplies the real
planner's empty bindings. Log `0011` incorrectly expected an undeclared `/size`
field to be an immutable provider slot (50.061 native seconds); the fixture now
explicitly declares that slot and asserts it exists. Neither required tightening
production behavior. The final complete run passed after both test corrections.

| Actual final native operation | Gas |
| --- | ---: |
| prepare Order | 539814 |
| prepare nested payment | 547447 |
| provide nested payment | 598048 |
| owner admission approval | 367255 |
| actual participant consent | 266089 |
| ordinary inactive provision / retry | 548576 / 525274 |
| ordinary active provision / retry | 556190 / 522702 |
| canonical / custom-helper / custom-constants refresh preparation | 517400 / 517573 / 517438 |

Fresh/stale admission-token predicate measurements are 180984/172576 gas; these
are explicitly modeled helper cases, distinct from actual operation measurements.
The existing runtime and per-case gas limits were unchanged; the admission-token
predicates use 10,000,000. No older Core gas number is attributed to this
candidate, and no full `newOrder` gain is claimed.

The before/after evidence verifies unchanged content hashes for all 157 runtime
classpath entries, 41 selected archives and the catalogue. The exact results,
failed attempts and gas lines are in the ignored
`reports/admitted-terms-cleanup/qualification-results.json`; environment hashes
are in `qualification-environment-before.json` and
`qualification-environment-after.json` alongside it. The final ignored candidate
manifest records all task file hashes, including semantic cards, so the eventual
commit can be checked against the tested bytes.

`ActivationNullOperationConformance` and retained-capture probes remain in the
repository; they were not executed in this task. CI, hosted transport, publication,
import, deployment and financial E2E are not established by these local results.

Full reader-flow and four-party `newOrder` qualification remain the next package's
responsibility. No publication, merge, import or deployment occurred here.
