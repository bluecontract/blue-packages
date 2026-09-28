# Blue Time

Explicit-timestamp, one-shot triggers for Blue managed documents.

```yaml
type: Time/Timer Request
channel: time
key: activation
timestamp: 1790931600000000
context:
  purpose: activateAgreement
```

`timestamp` is an Integer Unix timestamp in **microseconds**, not an ISO date,
duration, arrival timestamp or measured firing time. The processor determines
when the request is eligible; it returns `Time/Timer Fired` containing the exact
request and registrationId. An idle document needs no business Timeline entry.

## Two ways to schedule

The complete example is [`examples/two-timers.blue`](examples/two-timers.blue).
Initialization uses ordinary `Contracts/Trigger Event`. The scheduleReminder
operation uses the custom `Time/Schedule Timer` step with expression-valued request
arguments. Both produce the same Timer Request protocol. Two workflows match
`request.context.purpose` to perform different changes. `key` is only for replacing
or cancelling pending timers; it is not a workflow name. Direct conditional BEX
is in `examples/direct-bex.blue`.

## Contents

Six exports: Timer Channel, Timer Request, Timer Fired, Cancel Timer Request,
Schedule Timer and Cancel Timer. The package has its own normative spec, examples,
conformance tests, exact dependency lock and data-only distribution. It contains
no copied dependencies, vendor environment or production engine implementation.

## Installation and verification

Place this folder at `blue-packages/blue-time`, beside the four pinned foundations,
with the supplied `blue-python` sibling installed (Python 3.13 or later).
The wrapper also supports the sibling source checkout without an editable install.

```sh
cd blue-packages/blue-time
./blue-package verify
./blue-package check-source
./blue-package test
./blue-package example
```

`BLUE_PYTHON` selects the interpreter. `build` reconstructs the same locked release
and refuses to overwrite different existing distribution bytes. `--refresh-lock`
is an explicit initial authoring action, not a normal rebuild behavior.

## Runtime status — important

This is a **built data/protocol package with an executable conformance fixture**.
The attached Python/Java/MyOS native runtimes do not already implement Time.
Installing the archive alone therefore does not create background wake-ups.
The example runner uses real attached Contracts and BEX with explicit, in-memory
fixture bindings and simulated trusted progress. It does not claim real signed
completeness, durable recovery, automatic native scheduling or graph qualification.

`docs/runtime-contract.md` and `docs/IMPLEMENTATION-TASK.md` specify the integration
work. `docs/acceptance.md` lists production gates not covered by the fixture.
Existing packages and native support selections remain untouched. Approve exact
Language + BEX + Contracts + Coordination + Time dependencies together.
