# Reseller cancellation timing

An optional companion to Reseller preview.8 for an Order with frozen buyer-accepted cancellation terms and its connected Payment Instruction. It adds an Order-activation window, a confirmed-service window, or both. The native buyer cancellation operation evaluates the configured conditions together, including the boundary. The accepted terms supply the late-cancellation rate.

The historical payment and settlement clauses reconcile the cancellation decisions against the bound Payment Instruction. Confirmed guarantor outcomes establish refunded money, captured funds or released authorization. The cancellation decision and a pending payment request each have their own state. The available settlement operations depend on the payment rail.
