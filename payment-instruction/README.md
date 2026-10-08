# Payment Instruction

One payment, with a complete typed request and response protocol. Concrete payment requests inherit `Payment Request` → `Events/Request` → `Events/Event`; responses follow the corresponding response hierarchy.

`Payment Instruction` owns the financial ledger and 36 named guarantor operations. `Payment Instruction with Clauses` extends that standard document and adds clause assembly. The internal Payment Request Actions clause contributes only requested behavior. It does not grant guarantor authority.

The protocol contains 50 concrete message types plus its two domain bases. Requests reserve eligible capacity; only authorized outcomes establish what happened. Unknown outcomes remain available for reconciliation.

Read the [protocol reference](../docs/payment-protocol.md), the [clause tutorial](../docs/clauses-tutorial.md), and executable scenarios `examples/apps/27-payment-protocol`, `28-payment-controls`, and `29-payment-rejection`.

These are unpublished package candidates and provider-neutral test workflows, not a live payment adapter.
