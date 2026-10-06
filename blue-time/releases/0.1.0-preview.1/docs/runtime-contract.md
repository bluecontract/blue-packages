# Runtime integration contract

## Exact roles

Install exact bindings only after approving this package and all dependencies.
The generated `docs/integration-selection.json` identifies the package, rules,
protocol and exports. It is a candidate selection, not native approval.

| Export | Contracts role | Header fields | Body fields |
| --- | --- | --- | --- |
| Time/Timer Channel | external-channel | none | none |
| Time/Schedule Timer | step | none | request |
| Time/Cancel Timer | step | none | request |

The channel is external relative to the Contracts machine. It does not require a
Timeline entry. It must use the engine's verified admission SPI. A processor-channel
binding in the attached release is limited to existing internal event families;
pretending a timer is an initialization or triggered event would change its meaning.

For each custom step evaluate the request exactly once as an expression, using the
same BEX frame as Contracts/Trigger Event (call/event/document/steps included).
Reject effects, an explicit type, absent mandatory fields or unknown request fields.
Attach the exact message type only AFTER evaluation; this avoids validating an
unevaluated expression as an Integer. Stage the completed message as an event.
The wrapper must not acquire an independent gas budget or invoke a scheduler.

The attached Contracts runtime rejects extra fields on an inherited Compute or
Trigger Event step. Therefore these types derive from Contracts/Contract and
require explicit step bindings. They are not disguised arbitrary subclasses that
happen to work because a validator ignores their fields. Timer Channel similarly
derives from Channel to fail closed without its binding.

## Integration points in the supplied Python source

- `src/blue_packages/runtime.py`: approved native feature selection and dependency closure.
- `src/blue_contracts/reference/runtime.py`: existing RuntimeBinding and verified
  external admission API; keep process(document,event,eventTimestamp) unchanged.
- `src/blue_coordination/engine/admission.py` and `admission_evidence.py`: pattern
  for binding authentic evidence, not just accepting a payload shape.
- `src/blue_coordination/engine/work.py`, `readiness.py`, `source_records.py`,
  `history.py`, `dispositions.py`, `waits.py`, `store.py`, `outbox.py`:
  use the existing scheduler, retained histories and durable progress. Inspect
  actual ownership before placing hooks; these filenames are integration leads,
  not a claim that a specific unimplemented method already exists.

Add timer discovery at committed effect publication, including epoch-0 lifecycle
effects. Validate proposed requests before commit. A pending candidate must block
later input selection BEFORE the wall-clock alarm fires. Wake-ups must not restart
an in-flight invocation. Publish complete-prefix boundaries accounting for pending
timers. Reselect prerequisites after graph/channel topology changes.

No production source in the supplied ZIP was modified for this data package.
`tests/support.py` installs explicit fixture bindings only in its own processor.
Its synthetic completeness values are NOT signed provider evidence, its state is
not durable, and its owner-channel fixture is not an authorization implementation.
It proves message construction, workflow execution and selected scheduler rules,
not production eligibility, restart safety, graph cycles, throughput or Java parity.

## Unsupported configurations

The supplied native Runtime.agreements()/Runtime.mandates() must reject executing
this unapproved Time protocol. Merely mounting definitions is allowed. Do not edit
existing supported-package selections to claim otherwise. Candidate integration
selection includes Language, BEX, Contracts, Coordination and Time, not Time alone.

The protocol numeric range follows the attached Contracts `SAFE = (1 << 53) - 1`
timestamp check. This is not a newly invented graph or workload limit.
