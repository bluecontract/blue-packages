# Payment Instruction

One independently governed payment, with explicit PayNote-style requests, typed guarantor responses, reservations, conditional completion and persistent compensation.

The public catalogue contains 52 message types (including the two common envelopes). The Payment Lifecycle Clause exposes 36 named guarantor operations. Shared BEX accounting validates correlation, available capacity and authority. A request never means money has moved.

See [the complete protocol and migration guide](../docs/payment-protocol.md), [payment-family integration](../docs/payment-family.md), and the standalone `examples/payment-family/23-explicit-protocol.blue` walkthrough.

Unpublished candidate. Authored Blue/BEX definitions are authoritative. External execution requires an actual adapter; supplied local scenarios use a test guarantor.
