# Receipts restoration qualification

Use the exact candidate package catalogue and a matching Core test classpath.

```sh
classes=$(mktemp -d)
javac -cp "$BLUE_JAVA_CLASSPATH" -d "$classes" \
  tools/QualificationRuntime.java \
  tools/BootstrapPreparationConformance.java \
  tools/DeclarativeReceiptsConformance.java \
  verification/independent-clauses/receipt-restore/ReceiptCapacityProbe.java \
  verification/independent-clauses/receipt-restore/ReceiptNativeCapacityProbe.java
java -cp "$classes:$BLUE_JAVA_CLASSPATH" DeclarativeReceiptsConformance "$CATALOGUE" --restore
java -cp "$classes:$BLUE_JAVA_CLASSPATH" ReceiptNativeCapacityProbe "$CATALOGUE" 80
java -cp "$classes:$BLUE_JAVA_CLASSPATH" ReceiptCapacityProbe "$CATALOGUE"
```

The first check prepares and admits independent Orders and uses real native
Contracts dispatch. It models cumulative PI effects whose relay the Agreement
missed, then delivers a restoration signal and verifies both receipt and
commission targets, aggregate totals, source checks and replay.

The second check initializes 80 managed Orders with distinct native origins,
then seeds controlled admission and payment facts. It measures the same
receipt and Ledger operations through the full Contracts dispatch, including
the Agreement Activation gate and native document updates. It asserts every
target and aggregate, then repeats the restoration on the same state and
checks that no receipt event is published.

The third check executes the exact compiled Receipts reconcile action and
the exact stock Ledger accrual function on controlled state. It requires 80
changed Orders and repeats the action on the same restored state. The test
checks every receipt and commission target, aggregate totals, and zero
new patches or events on replay. Its gas numbers cover these BEX invocations.
Contracts dispatch, document writes, evidence resolution and restoration of
transport permissions have separate costs. Larger samples are exploratory.
