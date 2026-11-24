# Payout restoration qualification

Use the exact candidate package catalogue and a Core test classpath.

```sh
classes=$(mktemp -d)
javac -cp "$BLUE_JAVA_CLASSPATH" -d "$classes" tools/QualificationRuntime.java \
  verification/independent-clauses/payout-restore/PayoutLedgerRecoveryConformance.java
java -cp "$classes:$BLUE_JAVA_CLASSPATH" PayoutLedgerRecoveryConformance "$CATALOGUE"
java -cp "$classes:$BLUE_JAVA_CLASSPATH" PayoutLedgerRecoveryConformance "$CATALOGUE" 256
```

The fixture initializes managed payout instructions, invokes the ordinary
stock Ledger reserve action and supplies modeled provider outcomes and
admission records. Native Contracts processes the agreed readiness signal and the existing Ledger closes
each qualifying reservation. The test checks two distinct payouts of equal
gross amount, one terminal void, partial and unverified evidence, distinct
ledger connections, the inherited Connections default and an explicit
opt-out, and an exact replay. A separate signed Go fixture covers normal
Agreement readiness, embedded payout channel delivery and the two independent
guarantor decisions.
The optional count adds already closed settlement rows to measure the cost of
checking a larger history with the same unresolved cases.
