# Native secured amount condition

This fixture attaches a stock Payment Instruction to a managed slot on an
Order and calls the actual Schedule confirmation, alternative and acceptance
operations. A missing or unfunded instruction fails before action effects. A
captured reservation introduced after the seller proposes an alternative
reduces the available hold. The buyer can accept after the guarantor's failure
response releases that reservation.

A separate membership workflow binds the same condition to a managed
collection member and to revision, terms and amount paths outside
Activation. It covers a zero required amount, frozen revision and terms
mismatches, a missing input, a pending void and a closed PI. The guard
must return `ACTION_CONDITION_FAILED` and preserve preflight, before and
action state. The same attached instruction is tested after independent
changes to the current amount, revision and terms, then after restoring them.

The host selection operations are fixtures. The embedded graphs, payment
ledger mutations and Schedule operations execute in the native runtime.

Compile with Java 21 and the qualified Core test classpath. The catalogue
must include the Payment condition and group-local Connections inputs.

```sh
fixture=verification/independent-clauses/secured-amount-condition
classes=reports/independent-clauses/secured-amount-condition/classes
mkdir -p "$classes"
"$JAVA_HOME/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" -d "$classes" \
  tools/QualificationRuntime.java tools/CurrentOperationScenarios.java \
  "$fixture/SecuredAmountConformance.java"
"$JAVA_HOME/bin/java" -Xmx2200m -cp "$classes:$BLUE_JAVA_CLASSPATH" \
  blue.core.SecuredAmountConformance "$PWD" "$PWD/$fixture"
```
