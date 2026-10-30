# Blue Processing Event Source v1

Edition: `blue-processing-event-source/1.0.0-preview.1`.

This optional execution capability extends the exact imported Blue BEX and Blue
Contracts protocols. A package using it must declare its execution requirement.
A runtime lacking the capability rejects that selection. Existing protocol
identities, binding reads and persisted runtime selections remain unchanged.

## Read-only binding

`$binding: processingEventSource` reads the same immutable native processing
event as `processingEvent`, through a source-operand view. No processing event
means undefined. Request fields, emitted events and document state cannot set or
replace this binding. When Contracts processes an observed effect from an
embedded document, the binding still designates the original processing event,
not the emitted payload. It grants no additional authority.

An object-member lookup selects the nearest explicitly supplied operand, starting
at that exact node and following its type chain only when that member is absent.
The selected operand is read independently: enclosing field declarations and
their contextual schemas are not merged into it. A member absent throughout the
chain returns undefined. Cyclic ancestry is visited once per lookup. This does
not strip schemas authored on the selected operand itself. Ordinary scalar
observation remains scalar observation; it does not recover erased metadata.

Collection views retain the exact source node and its captured evidence. List
positions follow ordinary native list interpretation of that source node.
Object key enumeration returns the union of its own and inherited supplied
members, excluding structural `value` and `items` representation fields. Source
metadata members, including `type` and `schema`, remain readable. These are source
operands, not a projection of only present business values.

`$nodeBlueId` applied to a collection view identifies its selected exact source
node. In particular, an authority's `mandate: {blueId: M}` yields `M`, even if the
authority's field definition requires that Mandate. It does not identify the
current processed state of M. Consumers compare M with the original document
reference in the Mandate's initialization marker.

Source collection views remain immutable and lazy. Copying them does not expand
their descendants. Retaining a selected collection in a generated Blue value
preserves its exact operand and dependency evidence; cold export/import and
replay must not depend on a warm resolver cache.

## Accounting and failure

Source reads share the invocation's existing logical meter. Selected manifests,
type edges, object-member and list-item lookup/enumeration, and ordinary native
identity/evidence work use the corresponding existing charges. There is no
unmetered whole-event conversion, new hashing algorithm or new gas schedule.
Resource exhaustion and missing or invalid dependency evidence retain their
ordinary failures; they must not become an absent field or a fabricated ID.
Installing the capability does not eagerly resolve the source binding, so a
program using only historical bindings retains its historical read charges.
