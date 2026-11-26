# Native reviewed booking approval

`ScheduleReservationConformance` exercises the installed Activation and
Schedule operations with native Contracts processing. The fixture has
its own actor channels and a controlled clock. It checks:

- Schedule confirms an exact booking without Activation.
- A composed direct confirmation records one seller approval in the
  same native result. The ordinary approval route cannot bypass review.
- The exact duplicate preserves the booking, approval and request record
  and emits no new events.
- The seller's alternative retains its proposal revision, price and date.
  It creates a pending Activation grant. Only current buyer review
  records the seller's approval. An actual party update advances the
  Activation revision and makes the grant stale while leaving the
  booking proposal current.
- A mismatched amount, a stale grant, a wrong actor on a same-priced
  group and an offer with no designated acceptance party fail with the
  specific Activation reason. A rejected result commits no state or
  public effects.
- Hotel and restaurant share an Order with separate roles, group IDs
  and service times. The hotel has direct approval only. Both groups
  use the same price so the crossed-role test exercises party scope.
  Each approval leaves the other service's authority independent.
- Valid `case` and `caseHandler` roles each receive their own reachable
  reviewed workflow and emit their own Terms Accepted event.

`CatalogOrderAttachmentConformance` takes the normal Go-emitted dated
source and executes signed Coordination entries for both parties,
the original Payment Instruction, and each buyer or seller review. The
provider responses are controlled native fixture inputs. This runner
observes the resulting capture request. The hosted browser and payment
simulator evidence belong to their own run.

`SecuredAmountConformance` keeps its scheduled fixture on the same
composition. It uses an attached managed Payment Instruction and covers
the recorded hold, an intervening reserved capture, and a buyer acceptance
after the held funds become available again. Its membership contract
continues to exercise the independent stock funding condition.

Run `ScheduleReservationConformance` against the complete candidate
catalogue using Java 21 and the qualified Core test classpath. The
standard `tools/check_operation_inputs.py --case schedule-reservation`
command qualifies the current package checkout. For an immutable
candidate checkout, pass its absolute path to the Java runner.

```sh
"$JAVA_HOME/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" -d "$classes" \
  tools/QualificationRuntime.java tools/ScheduleReservationConformance.java \
  tools/CatalogOrderAttachmentConformance.java
"$JAVA_HOME/bin/java" -Xmx1500m -cp "$classes:$BLUE_JAVA_CLASSPATH" \
  ScheduleReservationConformance "$archive_checkout"
for mode in timed-confirm-funding timed-accept-alternative; do
  "$JAVA_HOME/bin/java" -XX:ActiveProcessorCount=4 -Xmx2400m \
    -Dblue.packages.signedConformanceWaitSeconds=300 \
    -cp "$classes:$BLUE_JAVA_CLASSPATH" \
    blue.core.CatalogOrderAttachmentConformance "$archive_checkout" \
    "$go_emitted_dated_source" "$mode" || exit $?
done
```

## Qualified snapshot

- Blue Packages catalogue commit `09c8208` with catalogue SHA-256
  `5e1d4093379e91b722b78f7fa5cc0b05ba5d3c0d9aa9ed99f3563c77a4e51bf8`.
- Core test runtime from `2f2931de2085996511e1e1eb8aca5aab7f2e5b8e`.
- Actual Go `a8b9be88251f61129df1d751f72a94ab3a9352fa` emitted
  `scheduled-both.source.json` with SHA-256
  `eeec846066b1fdd828961cb7933eaa8156d03f80487169456df64dd5bc0b7812`.

The eight focused native cases and both secured-amount fixture variants
passed on the full catalogue. The signed funded direct case refused the
seller's booking before the hold, then refused the raw seller approval
after the original 7200 hold. The exact confirmation activated the Order
and produced one capture request on the same original Payment Instruction.

Run each signed mode in its own JVM and in-memory store. The first
combined run qualified direct confirmation and later exhausted the
1500 MiB Java heap while qualifying the second fixture's authorization.
The original log retains the successful direct result and the interrupted
second fixture. The isolated alternative run starts from the same
Go source and catalogue. It passed in about three and a half minutes.
The seller offered a new time at the same price. The native result
refused a buyer review of the previous proposal and applied the buyer's
signed review of the current proposal. The same booking group, 7200
minor-unit Order amount, commercial revision and terms stayed in force.
The activated Order requested one capture of 7200 from its original
Payment Instruction.

The first complete candidate, catalogue SHA-256 `58dcd5a623ae98211a08255a5d99638f23832d89c89436895544621625a0a2dd`,
failed composition initialization on the reserved BEX local name
`contracts`. The subsequent thin and full exact runs cover the corrected
declaration. Local logs live under `reports/approval-composition`, including
`schedule-58dcd5a6.log`, `schedule-final-5e1d4093.log`,
`escrow-final-5e1d4093.log`, `signed-go-a8b9be88-5e1d4093.log` and
`signed-alternate-only-a8b9be88-5e1d4093.log`.
[Exact evidence identities and original document references](checkpoint.json)
