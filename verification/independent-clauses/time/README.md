# Reusable clock input

The stock Payment Instruction processes its ordinary acceptance, transaction
initiation, authorization request and guarantor `secureFunds` operations.
`secure-timestamp.blue` is a prototype payment-side projection of the first
successful full authorization. It checks the Payment Instruction's own outcome
and the native processing event, then retains the request ID and the timestamp
from that operation. It has no dependency on the agreement that consumes it.

`start-clock.blue` is a separate prototype. Its `startAt` action accepts a
positive integer timestamp in microseconds and remembers the first value. The
choice of input belongs to `agreement-bindings.blue`. An automatic agreement
binds native activation and can also read the retained authorization fact on
an embedded event or when the source is attached. A merchant-confirmed
agreement binds its own actual activation and keeps the clock absent until
that happens, even when payment is already authorized.

The Java harness runs the native Contracts processor at explicit test times.
The live case uses only the embedded authorization input. The late case
uses only the attachment change input.
The late case attaches the exact publication produced by the earlier real
native `secureFunds` operation and inspects the resulting live document.
Its attachment operation supplies that publication under the fixture's
merchant channel. Hosted Documents selection, independent account transport,
and provider signing are outside this run. The fixture does not model pricing,
refunds, custody policy, or a cancellation cutoff.

Run with Java 21 and the test classpath from a matching Core checkout.

```sh
bash verification/independent-clauses/time/run.sh \
  /path/to/frozen/blue-packages \
  /path/to/frozen/core/reports/core-http-test-classpath.txt
```

The three cases passed with Blue Packages
`c59b02950286364dbfa03814d8807eab4023a934` and Core
`f1202f28a1fd532c9637c78512460c7c442958c1`. The selected `PACKAGES.json`
SHA-256 was `da13966ee66e9217e424a4cbe0d86d52edc2f720fba7e3b735352a5b6d461670`.

| Case | Native observations |
| --- | --- |
| Already attached | The clock is absent before SECURE. Embedding the real guarantor outcome at 30,000,000 µs sets the clock to 30,000,000 µs. |
| Attached after SECURE | A duplicate successful response leaves the stored time intact. Attachment at 60,000,000 µs reads the original SECURE fact at 30,000,000 µs. |
| Merchant confirmation | An already authorized source supplies no start while approval is pending. Native approval starts the clock at 90,000,000 µs. |

## Published primary and fallback

Pass `--exported` as the third argument when testing a catalogue with the
`startFromEntry` and `startFromFallback` actions in
`Connections/Remember First Timestamp` and `Payment/Secure Timestamp Projection`.
The read-only fixture binds the clock paths, completion event, and catch-up
triggers without an authored BEX expression. A native seller activation at
10:03 wins over a retained SECURE time of 10:00 observed before, during, or
after activation. An actual initialization with no entry timestamp uses the
original 10:00 value on that turn if attached, or once the projection arrives.
An invalid zero primary cannot establish the missing-entry condition. Zero,
negative, and text fallback values are ignored even after missing primary was
established.

The access test changes a fixture readiness value and emits the typed
`Parties/Document Access Restored` event through a native operation. The event
alone cannot bypass readiness. Ready state recovers the original stock
authorization timestamp, which survives a repeated event. This covers the
native action and declared catch-up trigger with fixture readiness. Hosted
Coordination access transport is a separate check. The legacy `startAt` mode,
unknown connection profiles, and conflicting local/profile declarations stay
in the same runner.
