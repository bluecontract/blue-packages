# Native Payment adjustment conformance

The fixture runs the stock Payment Process and Payment Instruction against
an independent Order that publishes a price-correction decision. Its source
operation supplies the selected payment and prepared requirement evidence.
The test drives native capture, refund and release with fixture guarantor
responses and compares the confirmed ledger.

The typed capture test exercises the inherited selected-payment predicate,
the supplemental rule, the service requirement and the accepted-decision
veto. A prior pending refund delays the remaining adjustment until the
provider reports its result. An unknown capture can only be reconciled
after its financial outcome. The held case distinguishes a positive
target, an absent target, an expected zero target, and foreign selection
evidence. A void-only declaration can catch up after later selection.

With the optional `manual-refund-recovery` argument, a payee exercises the
existing native refund request after the provider definitively fails an
automated attempt. The old request and commercial decision survive. Pending
and unknown attempts reserve their amounts; another refund against genuinely
unused capacity remains possible. The manual request is identified by its new
PI request key. The protocol does not add a link from it to the commercial
decision.

Compile against the qualified Core test classpath with Java 21. Pass the
directory containing the selected package catalogue and the fixture directory.

```sh
fixture=verification/independent-clauses/payment-adjustments
mkdir -p reports/independent-clauses/payment-adjustments/classes
classes=reports/independent-clauses/payment-adjustments/classes
"$JAVA_HOME/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" -d "$classes" \
  tools/QualificationRuntime.java tools/CurrentOperationScenarios.java \
  "$fixture/AdjustmentConformance.java"
"$JAVA_HOME/bin/java" -Xmx2200m -cp "$classes:$BLUE_JAVA_CLASSPATH" \
  blue.core.AdjustmentConformance "$PWD" "$PWD/$fixture"
```
