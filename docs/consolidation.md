# Consolidation to one current source set

The previous audited state is Git commit
`f1ebdf4caa7b62edaed00ea1ee508e600a61c08f`. Its complete source tree is also in the
`myos-payment-family-audit-ca52050-f1ebdf4.zip` audit supplied separately.

The root now contains the tested connected clause architecture, the payment
family and the 10M-gas foundation. `blue-agreements-connected` was promoted to
`blue-agreements`. The data packages receive new `0.5.0-preview.2` identities;
old archive bytes are never relabelled as the new version.

Removed alternative source trees: embedded clauses, first root clauses, the
root-clause performance experiment, reseller clauses, the pre-provider
foundation, the 100K-gas set and the duplicate 10M-gas set. Obsolete migration
scripts and competing selection files were removed too. Existing Core fixtures
retain their exact package archives and regression cases; current sources do
not have to carry those old editable implementations.

Coordination at the root remains the current provider/access specification.
Current business packages import it directly. Mandates owns Event, Message,
Request, Response and Authority definitions for its own protocol and imports
Coordination only for actors, timelines and channels. Its protected approval
program remains explicit and requires exact document review.

Time's eight exported type identities and rules are unchanged by the dependency
consolidation. Its package/protocol descriptor now selects current Coordination.
Core must explicitly approve that descriptor; matching exported types alone
never grant native support.

Core retains historical Coordination, Time and Mandates identities to read and
replay existing journals. Only the exact previous complete default capability
set may gain the two current native descriptors automatically. Deliberately
restricted capability sets must not silently acquire new permissions. Once a
journal uses current packages, rolling back to an older binary is not supported.

This change does not deploy AWS, publish packages, enable real payment rails,
or claim Python runtime parity. Current native qualification uses Java. Frozen
reference sources are retained only for their existing conformance purpose.
