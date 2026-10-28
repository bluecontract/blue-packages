# Blue Definition Read v1

Edition: `blue-definition-read/1.0.0-preview.1`.

This optional execution capability extends the exact imported Blue BEX and Blue
Contracts protocols. It does not change either imported protocol's historical
identity or the behavior of existing value reads. A document using this capability
must select this protocol explicitly through its package execution requirements.
An execution runtime without this capability must reject that selection.

## Starting-document definition read

The expression `$document: {path: E, view: definition}` evaluates E using the
existing document path rules. It selects that path in the starting document
snapshot, using canonical native type inheritance and exact references. A path
with no selected native subtree returns the existing BEX undefined value. A
schema-only subtree is present for this operation even when it has no business
value. Empty definitions remain available; absent native paths return undefined. Source
null follows canonical Language admission and is not reinterpreted by this read.

The result for a selected subtree is a short reference `{blueId: ID}` to the exact
canonical effective native definition at that path. It preserves the definition's
native types, inherited restrictions, field presence, fixed values, descriptions,
references and numeric precision. It must not project only present business
values, infer a request, or materialize a modified payload. Consumers can retain
the reference as a native matcher; this capability does not make arbitrary BEX
object lookup dereference references.

The runtime must establish the returned node in its existing native node/evidence
store before exposing the identity. The node and its required dependency closure
must remain available after publication, cold export/import and replay. Reading
the definition never changes document state, sends an operation or creates an
Admission.

## Metering and boundaries

The read uses the existing deterministic document-read and path-member metering,
including canonical manifest resolution, construction of the effective exact
node, and identity/evidence work. It has no unmetered resolution path and does not
introduce a separate gas schedule. Missing dependency resources and canonical
resolution failures retain their existing concrete errors rather than returning
a fabricated definition or pretending that a missing resource is an absent path.

The new view applies only to `$document`. `$resultValue` with view `definition`
is rejected explicitly; this edition defines no overlay-definition semantics.
Existing omitted, `canonical` and `resolved` document value views retain their
existing behavior. The capability must not silently activate for an older
execution selection.
