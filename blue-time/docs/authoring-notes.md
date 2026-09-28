# Authoring notes from verification

The custom step's `request` field is a BEX expression, not a completed typed
Timer Request. Its source declaration is deliberately an unconstrained hole.
Mandatory request fields are enforced after evaluation by the step runtime.

In the supplied library, a description or schema placed directly on that
expression-valued declaration can become part of the inherited literal body
returned to the runtime. It then becomes unintended data in the evaluated object.
This was found by executing the example, not by merely parsing its YAML. Keeping
expression-field documentation at the enclosing type/specification avoids it.
The captured `context` declaration is also left unconstrained and undecorated.
Completed message fields such as timestamp retain their strict schemas.

The conformance fixture retains each emitted request's exact content reference.
Timer Fired contains that reference; its displayed JSON may expand it. A BEX
handler checks `$nodeBlueId` on the received request against the original emitted
event identity. Displaying equivalent fields alone is not an exact-identity test.

Runtime integration must use the same expression-frame, validation and metering
semantics as the core Contracts evaluator; the fixture is not a substitute for
that native implementation or for signed completeness and durable scheduling.

The returned `Timer Fired.request` is an unconstrained exact-value slot, not a
new typed/schema-required refinement of the old request. With the latter design,
`$nodeBlueId` observed a different refined value even when the envelope contained
the original reference. The Time admission runtime enforces presence and exact
identity against the already validated registration instead. Timestamp and other
completed Timer Request data retain their strict schemas. This is an explicit
separation of payload identity from envelope validation, not permission to accept
a missing or substituted request.

The supplied Language reader normalizes numeric source text to an Integer under
an Integer field declaration, including a Text-shaped numeric source value. This
was checked by inspecting the projected value: its Python type is int and its
value is the requested timestamp. Time validates this resolved semantic integer;
it does not change Language parsing or claim stricter lexical validation. Raw
string/object values at the Time runtime validation boundary are rejected. The
example uses unquoted integers. ISO dates, booleans, fractions, negative values
and out-of-range values are rejected. The parser observation is reported rather
than changing the foundation or asserting that explicit source type labels are
never normalized.
