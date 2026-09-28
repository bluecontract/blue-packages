# Coordination integration and explicit support

## Supported package selection

Select the installed native profile and its complete dependency set:

```python
from blue_packages import Runtime
runtime = Runtime.mandates()
engine = runtime.coordination(
    supported_packages=runtime.supported_packages,
).start()
# Language, BEX, Contracts, Coordination and Mandates are all selected.
engine.close()
```

That is host configuration selecting a trusted native implementation, not a field
in an agent's request, a custom business SDK, or an independently authored Execution
Profile document. `dist/package.json` and the verification evidence
identify the actual immutable package; `docs/native-support.json` describes its binding to this
implemented protocol. Do not infer support from a version label or package name.

Loading definitions permits inspection. Execution requires the native
`Mandates/Authority Protocol` marker. The supported package set is persisted in the
engine context; a different set on restart is rejected. The loader checks the pinned
Coordination and Contracts semantics. Downloaded data cannot install native code or
register itself as a trusted authority implementation.

The existing Coordination-bundled legacy Mandate implementation is left unchanged
for its old IDs. Supporting it does not imply support for the new package. This
preview is additive; it does not pretend to migrate existing histories.

## Responsibilities

| Layer | Responsibility |
|---|---|
| Language | Exact values, identities, type admission, ordinary pattern matching |
| BEX | Deterministic workflow and predicate evaluation |
| Contracts | Local operations, managed-child delivery, staged writes/events, unchanged gas ceiling |
| Mandates data | Protected lifecycle workflows, typed grants/messages, optional evidence gate |
| Native Coordination Mandates support | Package recognition, participants, protected write evidence, historical authority and grant matching |
| Timeline Provider | Authenticate appends, timestamp, preserve/prove history and completeness |
| MyOS / external executor | Credentials, effect dispatch, execution permission, idempotency, outcome publication |

The Timeline Provider does not interpret Mandates or authorize business operations.
The target's Contracts processor does not fetch a Mandate as an ad hoc network
check. Coordination establishes eligibility from evidence before handing the
original attributed input to the ordinary target operation.

## Authorization algorithm

For a candidate K, first establish source authentication, completeness, document
lineage, source generation and targeting. The operation identifies the effective
holder channel. A direct holder call retains ordinary authority. A delegated call
requires the exact supported authority wrapper, matching represented holder and
actual delegate, a concrete holder target channel, and a concrete target source
channel for the actual delegate and Timeline.

Resolve the original Mandate lineage and its complete historical state strictly
before the full ordering key K. Use all required earlier scope/provider/managed-child
history, not the latest head or the worker's current wall clock. Check owner approval,
Active state, protected program identity and one complete grant. Apply the target's
own delegation policy and ordinary operation validation. Preserve the actual agent
in the original entry and receipts.

The agent's Timeline used for this target can differ from its Timeline in the
Mandate; actor identity must match, and each document must admit its own actual
source. Composite/All effective channels are not supported for delegation in this
package version. Co-approval, re-delegation and automatic migration are not implied.

Missing evidence waits. A completed mismatch denies. A completed non-Boolean
predicate value is not truthy authority and is treated as a failed grant condition.
Interpreter failures and resource inability retain explicit error/incomplete
classification; this package does not turn missing facts into negative evidence.

## Protected publication

The native validator inspects actual Contracts completion write records, including
handler/declaration/causal-input identities. It does not trust a document merely
claiming `status: Active` or emitting an Approved event. Only the base direct owner
approval can establish `approvedProgram`. The protected declarations, participant
bindings, exact type and standard future-grant configuration cannot be replaced by
a later write. The result's scope is validated before publication.

`scope` itself may change through the owner-approved program. Approval covers those
rules and any permitted mutable parameters; the holder must review custom behavior.
No unrestricted setScope is provided. Custom data assembled into future scope must
still pass validation before becoming current authority.

## Scheduling and independent targets

This extension preserves `independent-owner-prefix/1`. It does not restore an
all-ancestor execution barrier. An Order independently publishes its exact completed
result. The Mandate consumes the required historical successor. Its reaction may
remove the permission that authorized the triggering action, but that change cannot
retroactively make that action unauthorized. Later calls need their own correct
pre-action authority prefix.

The examples use an independently surviving Order with a verified managed occurrence
inside the Mandate. Ending the Mandate does not stop the original Order owner. An
out-of-stage direct holder action ends the delegation, not the valid Order transition.

## Resource and production boundaries

Contracts keeps the 100,000 maximum. Native preparation, scope validation, history
proofs and authority predicates also consume host resources; aggregate user budgeting
and a full CPU/memory metering audit are not implemented here. Admission must be
resource controlled by the host, without fabricating semantic outcomes on exhaustion.

The local SQLite checks exercise the bundled store only. They are not a new AWS or
PostgreSQL design and do not establish a cross-document transaction requirement.
No Java implementation, remote-provider proof exchange, full crash-injection matrix,
production credential gateway or distributed security certification is claimed.
