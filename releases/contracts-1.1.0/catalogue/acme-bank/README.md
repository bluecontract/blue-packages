# ACME Bank

An illustrative bank-confirmed payment profile. No real bank adapter is included.

`Bank Transfer Instruction` is a direct-transfer profile. After the instruction is accepted, the payer calls `requestTransfer` with one stable request ID. The guarantor alone can confirm the exact amount/currency/reference, decline the transfer, or report an unknown outcome. Unknown outcomes reconcile against the same request; a request is never treated as money received. A configured `paymentTerms.transferGate` is checked before dispatch. Cross-document conditions require explicit named sources and readiness.

The profile does not create card authorization/capture state. Refunds are separate transfer instructions with reversed parties; they are not an automatic reversal of a completed bank transfer. Main-party approval and access remain required for its operations.

The older `ACME Bank Payment` reservation-style profile is retained for compatibility. All changes are unpublished candidates.
