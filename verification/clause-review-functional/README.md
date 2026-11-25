# Native qualification of clauses and templates from the November 24, 2026 review

`CancellationRefreshConformance`, `ScheduleReservationConformance`, and `WholeOrderCancellationConformance` run native Contracts operations on types from the exact pinned, locally built archives. `CatalogOrderAttachmentConformance` also creates documents from an Agreement emitted by Go and runs signed operations in Coordination. An authorized test guarantor supplies payment confirmations.

## Baseline

- Packages archives from commit `09c8208ecafc56c9c32b4233c145b2882be6a98b`, index `5e1d4093379e91b722b78f7fa5cc0b05ba5d3c0d9aa9ed99f3563c77a4e51bf8`.
- Go `a8b9be88251f61129df1d751f72a94ab3a9352fa` (`/15`) emitted the `service-only` Agreement with SHA-256 `e8b9cf1a459a4d076006573fad37236da536b7eb12f0decea7d857a33fc35e03`.
- The `scheduled-both` Agreement from the same Go revision has SHA-256 `eeec846066b1fdd828961cb7933eaa8156d03f80487169456df64dd5bc0b7812`.
- Native Core runtime `376059aa2f9230795c46bf4c4aa6c096c557a56a`. The classpath file has SHA-256 `de672b5a92868adec8ed6e92c68772972ef627853df806fdec52e6bfba1517a4`.
- Local logs are in `reports/clause-review-functional/`. The T01 comparison against `/15` ends in the expected test failure after reservation approval. The Order is active and has a confirmed time, but `beforeConfirmation=true` remains and there is no free cancellation deadline.
- C17, relay and catch-up for a real Payment Instruction, signed rejection of a payment replacement, and the Commerce and clock boundary checks pass on the previous index. `T08-T10-baseline-plus-identical-selectors.log` confirms T08–T10 for standard Schedule and Activation. The last run in that log deliberately uses the new R02 references, which that index cannot resolve.

## Qualification pins

- Source for Packages archives `41153640c83cf498907f6fc00d249cbf2e8a8b9b`, based on `53ad03e`. Index SHA-256 `60ee068db2bde828c35e41edb0289bc562b36adeeffbf82ad74512ad88c23898`.
- Go `71698777b5dbc2ef255332c2c406b3c2d89eb33c` emitted the `/16` Agreement sources. SHA-256 for `service-only` is `220dfa09ec06bf4c3e3c688d21aa39ce10a8663b7254b25187ea168237f1b33c`, for `scheduled-both` `6ce6d1b6086a9f94f4182698e680424dbeb33f5ead64f3482048dd4fdba14590`, and for `manual` `c0348f7c2e947e7e827b605db62c770e30d8ae58533e4df1940faa8d07b21f76`.
- Native Core runtime `376059aa2f9230795c46bf4c4aa6c096c557a56a`. The qualified local file `core-schedule-activation-runtime/reports/core-http-test-classpath.txt` has SHA-256 `823d488c28fdbd5dbd31b88a4274b7b61233596fc76d88007f35107895fc1e79`.
- The first run with the diagnostic `service-only` artifact (`405252f9…`, Go `4c3264b…`) stopped before initialization. The evidence generator copied the pin from the retained `/15` artifact into the `/16` artifact. The attempt is recorded in `candidate-60ee068d/T01-T02-service-only-signed-go16.log`.

The next local archives, built from `99de8755f36e02cf445c640db79880098ed0b356`, have index SHA-256 `b66096cfc04ba9495ba853a50f6e4cccc7f97ed4c7e09ba30069de2b47b01ed9`. Compared with `60ee068d…`, the `clause-payment` and `myos` archives changed, and the other 40 have identical SHA-256 hashes. A comparison of ten common Agreement sources from Go `71698777…` and `1d8eaeb0fa0ad05f0ef032b2c96cf4db8163af7d` shows a change only at `/clauses/receipts/type/blueId`. The `service-only` source from the latter Go revision has SHA-256 `3b4bbc9cf1154a018efd218b7764adc1a937287548dddd624e3c9200f31c44e6`.

## Test cases

| Case | Input and expected result |
| --- | --- |
| T01 | Signed `timed-cancellation-service-refresh` on a standard `service-only` Agreement. Confirming the funded reservation updates both cutoffs and removes the pre-confirmation exemption. The source omits an elapsed clock. |
| T02 | `CancellationRefreshConformance` distinguishes two actual managed Payment Instructions with the same amount. A confirmed capture on the selected source removes the block on the late charge. The signed T01 variant also confirms the refresh through a standard Agreement emitted by Go. |
| T03 | `CancellationRefreshConformance baseline` confirms that the local field observer misses an ancestor replacement and a write from a managed Payment Instruction. A parent observer and a write to the exact field are separate positive controls. |
| T04 | `CancellationRefreshConformance` attaches a completed Payment Instruction through native `provide` and reads the retained outcome after a typed `Document Attached` event. Attachment does not emit the operator outcome again. A retry preserves availability and the absence of a decision. Separate financial tests confirm accounting. |
| T05–T07 | Independent `ActivationConnectionReferencesConformance` suite. `ScheduleReservationConformance` also exercises actual Commerce and Schedule composition with logical references. |
| T08 | `ScheduleReservationConformance` checks the exact actor, the identities of the record and request, the proposal, and the revision. A failed attempt rolls back without lasting effects. Signed `timed-accept-alternative` checks the successful seller and buyer flow. |
| T09 | `ScheduleReservationConformance` runs independent approvals for a hotel and a restaurant at the same amount. It tests changing the basis for the second reservation and exercises the standalone Schedule clause. |
| T10 | `ScheduleReservationConformance` allows changing either the SKU or the quantity at the same total. It checks rejection for changes to the amount, currency, or seller, as well as for the wrong actor and a stale proposal. Signed `timed-accept-alternative` changes both SKU and quantity at the same amount, preserves the original `orderSnapshot`, and checks rejection before the selected Payment Instruction actually secures the funds. |
| T11 | Signed `timed-payment-admission` rejects a wrong request, a wrong prepared requirement reference, and a second Payment Instruction with the same amount and currency before selection. It accepts the original and rejects a later replacement without changing the selection. `OrderDecisionConformance` separately tests the capture predicate for identity, terms, and revision fields. |
| T12 | Independent financial tests include `DeclarativeReceiptsConformance` and signed runs with a confirmed outcome. |
| T13 | Signed `timed-reject-first` and `timed-cancel-first` confirm a single VOID on the selected Payment Instruction and no new capture. Separate Payment tests check a late outcome for a capture already in progress. |
| T14 | `WholeOrderCancellationConformance` checks window boundaries, rounding, and that retries preserve the decision. `ClockCompositionProof` checks the actual first approval, missing time and fallback, and retry behavior. |

R04 covers rejection of identical event selectors. The planner compares selector values. Whether two different filters remain disjoint under type inheritance was outside this qualification.

T05–T07 passed on the reduced index `f79fe52dbfd2bebeac2c180cb5d7227605991cf43782f9778855fa6649083390` with Core `376059aa…`. A copy of the original log is at `reports/clause-review-functional/T05-T07-r02-reduced-native.log`, SHA-256 `71904f9ef3f21ae59beab4569bb33d0625880ff743fa206cd5ce3d6a49c8ce75`. The index includes Schedule, Orders, and Commerce. The table below includes the combined T06 run on the full index.

## Results on index `60ee068d…`

Logs for these runs are in `reports/clause-review-functional/candidate-60ee068d/`.

| Log | Result |
| --- | --- |
| `T01-T02-service-only-71698777-recovered.log` | PASS. With signed approval after a full hold, the confirmed start `1796126169000000` yields `beforeConfirmation=false` and `freeUntil=1796039769000000` (24 hours before the start). Confirmation of a 7,200 minor-unit capture on the same Payment Instruction updates availability without an Order action. |
| `T02-T04-native.log` | PASS. Two managed Payment Instructions have the same amount and different origins. Confirmation on the other instruction leaves the projection for the selected instruction unchanged. The correct capture and attachment of the retained outcome refresh availability. The C17 negative controls and retry checks pass. |
| `T06-T08-T10-native.log` | PASS. Standalone Schedule, actual Commerce and Schedule logical references, rejection of a mismatched record or request without partial effects, separate approvals at the same amount, a broader alternative, and rejection of identical selectors. |
| `T08-T10-reviewed-alternative-71698777-signed.log` | PASS. The proposal is rejected before the original hold. After the hold, the seller signs a proposal with a different SKU and quantity at USD 72. The buyer can accept the current proposal. The original `orderSnapshot`, revision, and terms are preserved. The original Payment Instruction receives one capture request. |
| `T09-T10-funding-native.log` | PASS. Standard Schedule confirms, proposes an alternative, and accepts it based on the outcome of the selected managed Payment Instruction. A missing hold, capture in progress, changed terms or revision, pending void, and closed Payment Instruction fail to provide the required basis. |
| `T11-capture-predicate-native.log` | PASS. The selected instruction, requirement, original provenance, current revision, terms, amount, currency, and access must match the defined capture rule. The local predicate test complements signed `providePayment`. |
| `T11-payment-admission-71698777-signed.log` | PASS. Signed `providePayment` rejects a wrong request, a wrong requirement reference, and a different USD 72 Payment Instruction. The original preparation remains intact. After the actual instruction is accepted, a second replacement attempt leaves the selection unchanged. |
| `T13-timed-reject-first-71698777-signed.log` | PASS. Signed rejection blocks both cancellation operations and later approval. The original USD 72 Payment Instruction receives one VOID even after a repeated rejection. The guarantor’s confirmation closes the VOID with zero capture and refund. |
| `T13-timed-cancel-first-71698777-signed.log` | PASS. Signed customer cancellation closes the scheduled reservation with the given reason. Later rejection and approval requests fail. Repeating cancellation leaves one VOID on the original Payment Instruction. Capture and refund remain zero. |
| `T14-boundaries-recovered.log`, `T14-clock-recovered.log` | PASS. Six Commerce cases and eight clock cases. The first approval at 10:03 takes precedence over SECURE at 10:00. The fallback applies when the activation time is missing and preserves the original value after attachment or retry. |
| `T01-T02-service-only-71698777-signed.log` | The app interrupted the run after successful preparation and attachment of the Payment Instruction and the expected approval rejection before the hold. The resumed run uses a separate log. |

## Results on index `b66096cf…`

- The signed T01 and T02 `service-only` run passed. The confirmed start `1796127143000000` yields `beforeConfirmation=false` and `freeUntil=1796040743000000`. Native capture confirmation on the original Payment Instruction updates availability without another Order operation. Log `reports/clause-review-functional/final-b66096cf/T01-T02-service-only-1d8eaeb0-signed.log`. SHA-256 `95eb26e7aa0e2665531587a89f447c20547e91cddbe8a0a19ec4e3848a9077d9`.
- T02–T04 passed again on the full index. Log `reports/clause-review-functional/final-b66096cf/T02-T04-native.log`. T05–T07 also passed on the full index, including resolution of standard Schedule and Commerce and the amendment cases. Log `reports/clause-review-functional/final-b66096cf/T05-T07-native.log`.
- The signed T12 financial run confirms zero receipts and commission after a hold and while capture is pending. The first confirmed capture yields 7,200 minor units in receipts and 900 minor units in commission. A retry preserves the result. Log `reports/review-finance/final-b66096cf/signed/timed-late-refund-after-payout-agreement-readiness/native.log`.
- T13 has separate Payment evidence. An actual outcome from the test guarantor following an ambiguous result for a capture already in progress leads to one full refund, with no concurrent VOID. Log `reports/review-finance/final-b66096cf/standalone/refund-readiness.log`.

## Reproduction commands

In the Blue Packages checkout with the tests, set `archives` to the directory containing the exact index and archives, `core_cpfile` to the Core classpath file, and `source` to the specified file emitted by Go. Run each signed case in a separate JVM. Use JDK 21.

```bash
classes=$(mktemp -d)
classpath=$(cat "$core_cpfile")
javac -cp "$classpath" -d "$classes" tools/{QualificationRuntime,ActivationConnectionReferencesConformance,CancellationRefreshConformance,ScheduleReservationConformance,WholeOrderCancellationConformance,CatalogOrderAttachmentConformance,OperationInputs,BuildPaymentFamily,BuildFinalGas,OperationInputConformance,OrderDecisionConformance}.java
classpath="$classes:$classpath"
java -XX:ActiveProcessorCount=4 -Xmx1800m -cp "$classpath" CancellationRefreshConformance "$archives"
java -XX:ActiveProcessorCount=3 -Xmx1700m -cp "$classpath" ActivationConnectionReferencesConformance "$archives"
java -XX:ActiveProcessorCount=4 -Xmx1800m -cp "$classpath" ScheduleReservationConformance "$archives"
java -XX:ActiveProcessorCount=4 -Xmx1500m -cp "$classpath" WholeOrderCancellationConformance "$archives"
java -XX:ActiveProcessorCount=3 -Xmx1500m -cp "$classpath" OrderDecisionConformance "$archives"
bash verification/independent-clauses/time/run.sh "$archives" "$core_cpfile" --exported
java -XX:ActiveProcessorCount=4 -Xmx2400m -Dblue.packages.signedConformanceWaitSeconds=300 \
  -cp "$classpath" blue.core.CatalogOrderAttachmentConformance "$archives" "$source" "$mode"
```

For the T03 control, add `baseline` after the archive path. Use the `service-only` source for `timed-cancellation-service-refresh` and `timed-payment-admission`. Use `scheduled-both` for `timed-accept-alternative` and `timed-cancel-first`. Use the unscheduled `manual` source with cancellation for `timed-reject-first`.
