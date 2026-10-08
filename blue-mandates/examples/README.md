# Mandate template

`operation-mandate.blue` is a binding template, not a ready-to-run document.
Supply concrete signed timelines, actors and the initial target document.
The holder calls `approveMandate` against the exact Pending document version.

The Java integration scenario `CanonicalPackagesTest` constructs real current
provider channels and proves Pending → Active → Terminated. Historical delegated
execution and cold reopen remain covered by `NativeRuntimeBindingsTest`.
The old Python example runner targeted a different exact native protocol; its
source remains in the pre-consolidation Git revision rather than appearing as
a runnable current implementation.
