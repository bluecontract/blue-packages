# Direct Customer Payment Instruction authorization expiry

Additive expiry-aware direct PI using the immutable stage-one JBK publication and
its original root-party layout. This publication is selected independently from
the Order/bootstrap MyOS publication; their incompatible alias families must not
be combined in an explicit authored package selection.

The expiry function source is shared with MyOS. The guarantor validates the same
Stripe authorization is expired and canceled, then requests the full remaining
VOID using sessionId, secureRequestId and requestId. Native guards reject paid,
pending, mismatched or non-Stripe requests. Existing cancelBeforeCompletion reports
the outcome. No new charge, attempt, payment completion, or document migration.
