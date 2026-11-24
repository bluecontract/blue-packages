# One refund action for two commercial decisions

This native composition proof uses two independently initialized documents. The Order
owns cancellation and price amendments. The Payment Instruction owns requests and
financial outcomes, using the published `PaymentInstruction/Payment Request Actions`
and its unchanged `requestRefund` action.

The [Order](order.blue) lets the customer accept the fixture's reviewed cancellation
terms on the exact Order version. The cancellation action records a retained amount
and releases the balance. A separate stock Amendments clause requires both seller
and customer approval for an agreed price reduction. Each reduction offers the
difference between the native update's previous and resulting prices.

The Order emits the same typed `Credit Approved` event in each case through an
explicit local adapter. The [Payment Instruction](payment.blue) subscribes only to
that event on its exact embedded Order source. The binding supplies the request key
and amount to the same stock `requestRefund` action. A separate guarantor operation
confirms the effect. The credit adapter uses existing Blue event and connection
types. The cancellation action is a fixture-owned policy, independent of Schedule.

| Native scenario | Approved effect | Confirmed amounts in USD minor units |
| --- | --- | --- |
| Customer cancels a captured Order | Retain 2,000 of 10,000 | Refund 8,000 and retain 2,000 |
| Both parties reduce the agreed price | Change the price from 10,000 to 2,000 | Refund 8,000 and retain 2,000 |
| Both parties approve a second reduction | Change the price from 2,000 to 1,000 | Refund a further 1,000 |
| Customer cancels a complimentary Order | Record the decision against the zero price | No Payment Instruction is needed |

The runner performs ordinary native operations via actor-scoped fixture channels.
It checks that a seller cannot cancel for the customer, an external event cannot
simulate an embedded credit, one party's approval leaves the price and payment
unchanged, and a repeated source operation gives no second refund. The native
financial ledger stays at zero reversed while the refund request is pending.

The runner supplies the initialized Order's exact reference to the Payment
Instruction before either commercial decision. It supplies fixture guarantor
success responses to exercise native capture and refund confirmation. This proof
qualifies the in-process joined native graph. Each paid case starts from its own
Order and Payment Instruction. The complimentary case mounts the exact same
cancellation clause alongside Activation. Its source omits both the credit
adapter and the price amendment. Hosted signature verification,
commercial checkout admission, late attachment after an emitted credit, and an
external provider are outside this fixture.

## Reproduce

From the repository root with Java 21 and the qualified Core runtime and test-support
classpath in `BLUE_JAVA_CLASSPATH`:

```sh
proof_dir=verification/independent-clauses/financial
result_dir=reports/independent-clauses/financial
mkdir -p "$result_dir/classes"
"$JAVA_HOME/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" -d "$result_dir/classes" \
  tools/QualificationRuntime.java "$proof_dir/FinancialComposition.java"
"$JAVA_HOME/bin/java" -Xmx1500m -cp "$result_dir/classes:$BLUE_JAVA_CLASSPATH" \
  FinancialComposition "$PWD" > "$result_dir/evidence.json"
```

The [captured evidence](evidence.json) names the exact catalogue, fixture and
payment library identities. Each paid
case records separate Order and Payment Instruction origins, the native refund
intent, and the confirmed amounts.

## A single refund source

The same runner also qualifies the direct binding used when the Order has only
one refund-producing decision. The Payment Instruction listens for
`Order Cancellation Accepted` on its embedded Order and uses the positive
`releasedMinor` from that Order's immutable decision. Its fixed
`order-cancellation-refund` key belongs to this one terminal decision. The
runner checks a captured amount of 7,200 with 1,800 retained, a zero-release
fixture, and replay. The multiple-source example above uses the original
templates.

Run the compiled proof with `direct-refund` to capture the binding and results:

```sh
"$JAVA_HOME/bin/java" -Xmx1500m -cp "$result_dir/classes:$BLUE_JAVA_CLASSPATH" \
  FinancialComposition "$PWD" direct-refund > "$result_dir/direct-refund.json"
```

## Native adjustment eligibility

Run the compiled proof with `request-readiness` against a catalogue containing
`Payment/Payment Process Functions` and connection profiles. The fixture
supplies a neutral retained target. The stock PI waits for an unknown hold or
capture to finish, then requests the corresponding native void or refund. An
earlier pending refund reduces the additional refund after confirmation. A
manual refund workflow without a profile retains its native request arguments.
The selection probe checks the exact prepared obligation even when its stable
key and business request ID differ.

The catch-up action listens for the stock `PaymentInstruction/Payment Response`
after the ledger update. A document-wide change listener can see individual
balance changes within a transition. It can request void prematurely after a
capture reservation clears and before the captured amount is written.

```sh
"$JAVA_HOME/bin/java" -Xmx1500m -cp "$result_dir/classes:$BLUE_JAVA_CLASSPATH" \
  FinancialComposition "$PWD" request-readiness
```
