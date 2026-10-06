# Blue Time

One-shot, explicit-timestamp timers for managed Blue documents. Native MyOS support
is available in the `agreements` and `mandates` profiles. Importing the package into
another runtime does not install a scheduler.

`Time / Schedule Timer` evaluates a read-only BEX request under the current
invocation's gas budget. `Time / Cancel Timer` cancels a pending key. A firing
arrives on `Time / Timer Channel` with its original request and registration ID.
Timestamps are Unix **microseconds**. There is no cron or implicit recurrence.

```yaml
- type: Time / Schedule Timer
  request:
    channel: clock
    key: reminder
    timestamp: {$add: [{$binding: timestamp}, 15000000]}
```

The complete [example](examples/two-timers.blue) starts with an operation, fires
15 seconds later, then schedules a second firing 20 seconds after the first.
A late worker retains those exact logical timestamps.

All inputs share Coordination's `(timestamp, sourceBlueId, entryBlueId)` order.
At equal timestamps a cancellation wins only if it sorts before the timer.
New requests must be strictly later than their invocation; there is no fixed
15-second or one-minute minimum. Idle timelines must supply trusted completeness
through the deadline before a timer can fire.

Eight exports: Timer Channel, Timer Request, Timer Fired, Cancel Timer Request,
Schedule Timer, Cancel Timer, Timer Source and Timer Entry. The last two are
immutable identities for the virtual source and its ordered inputs.

## Build and verification

The supported native implementation and publisher are in the sibling MyOS checkout.
Use JDK 21 and set `BLUE_MYOS` if that checkout is not `../../myos-aws-test`.

```sh
./blue-package verify
./blue-package check-source
./blue-package test
```

`verify` validates the archive and unchanged foundation locks. `check-source`
rebuilds into a temporary directory and compares every publication byte. `build`
refuses to replace different published bytes. `test` executes the native Java
coordination and durable restart tests. `example` prints the source example.

[Runtime contract](docs/runtime-contract.md), [qualification](docs/acceptance.md)
and [normative rules](spec/time.md) describe the precise boundaries. The previous
0.1 preview and its Python fixture are preserved in `releases/0.1.0-preview.1`.
That fixture tests the old ordering rules; it is not current runtime evidence.
The Language, BEX, Contracts and Coordination publications are unchanged.
