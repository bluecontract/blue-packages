# Development and verification notes

The final results are recorded separately in results.json and tests.log. Earlier
local candidates were not delivered as qualified publications. The implementation
checks found and corrected the following issues before the final rerun.

1. Metadata on the custom step's expression-valued request field was inherited
   into BEX data. The field is now an undecorated expression slot; the step runtime
   validates the evaluated, complete request and then supplies its exact type.
2. A typed declaration on Timer Fired.request refined the original request and
   changed the value observed by BEX $nodeBlueId. The envelope now preserves an
   unrefined exact reference, with mandatory presence and identity checked by the
   Time admission runtime. The automated test compares actual emitted and observed
   Blue identities, not just equivalent projected JSON.
3. The test fixture now privately copies admission tickets and tracks processed
   effect occurrences. Test evidence cannot mutate the expected ticket by aliasing;
   rediscovering the same committed effect does not replace or duplicate a timer.
4. Negative tests were corrected to exercise the intended boundaries. An explicit
   type is constructed dynamically from a known type, not an invalid source alias.
   Replacement uses a distinct operation value: the supplied Contracts runtime
   rejects assigning a second timestamp to the same event identity. Neither
   correction changes Contracts behavior or dependency sources.
5. The attached Language reader normalizes an untyped numeric string under an
   Integer declaration. The tests preserve that rule, require the resulting integer,
   and check the same normalization of Text-shaped numeric source values. Raw
   noninteger values at the Time admission boundary are rejected. Dates, booleans,
   fractions, negative values and numbers beyond the selected Contracts domain
   fail source preparation. No foundation parser behavior was changed.

These observations are about the supplied release. They do not constitute native
Time scheduler, Java, security-proof or performance qualification.
