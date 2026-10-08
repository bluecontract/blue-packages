# Payment clauses

`Payment/Payment Clause` represents one payment and creates one embedded standard Payment Instruction with Clauses. Its public bindings expose start and request actions, including `requestAuthorize`, `requestCapture`, `requestRefund`, and `requestVoid`, plus control requests. Guarantor operations belong exclusively to the Payment Instruction.

Request workflows execute in the PI by default. A connection with `in: agreement` reads the originating agreement and deliberately creates a cycle. No third evidence document is required. The clause observes typed PI events and echoes them as `Payment Event Received` for other agreement clauses.

MyOS Customer Payment, MyOS Account to Account Payment, ACME Bank Payment and Manual Bank Payment specialize the same family. Activation supplies the party and reader snapshot.

See the [complete tutorial](../docs/clauses-tutorial.md) and [protocol reference](../docs/payment-protocol.md).
