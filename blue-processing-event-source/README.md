# Processing-event source reads

This unpublished optional native capability exposes `processingEventSource` to
BEX. It preserves source operands when traversing an admitted processing event,
so the identity of an authority reference is not replaced by the identity of a
contextually specialized field. Existing `processingEvent` reads are unchanged.

This is read-only evidence. A source view is not an authority grant and does not
turn a lookalike request or emitted event into an authenticated timeline entry.
See the pinned specification for traversal, identity and metering rules.
