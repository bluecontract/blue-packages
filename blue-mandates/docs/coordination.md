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

Historical bindings are evidence only. No automatic migration or old runtime is supported.

## Responsibilities

| Layer | Responsibility |
|---|---|
| Language | Exact values, identities, type admission, ordinary pattern matching |
| BEX | Deterministic workflow and predicate evaluation |
| Contracts | Local operations, managed-child delivery, staged writes/events, unchanged gas ceiling |
| Mandates data | Protected lifecycle workflows, typed grants/messages, optional evidence gate |
| Native Coordination Mandates support | Package recognition, participants, protected write evidence, protected lifecycle and scope validation |
| Timeline Provider | Authenticate appends, timestamp, preserve/prove history and completeness |
| MyOS / external executor | Credentials, effect dispatch, execution permission, idempotency, outcome publication |

The Timeline Provider does not interpret Mandates or authorize business operations.
The target's Contracts processor does not fetch a Mandate as an ad hoc network
check. Coordination establishes eligibility from evidence before handing the
original attributed input to the ordinary target operation.

## Direct input eligibility

The actual actor and declared Timeline establish direct eligibility. Mandates
approval does not substitute a represented actor or add another input source.
Delegated entry claims are rejected; no grant matching or historical authority
path runs during target input selection.

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

Mandates observe declared managed-child completions through ordinary Contracts
rules. They do not add authority sources to target documents. Independent owners
retain their own publication boundaries and survive observer termination.

## Resource and production boundaries

Contracts keeps the 10,000,000 maximum. Native preparation, scope validation, history
proofs and authority predicates also consume host resources; aggregate user budgeting
and a full CPU/memory metering audit are not implemented here. Admission must be
resource controlled by the host, without fabricating semantic outcomes on exhaustion.

The local SQLite checks exercise the bundled store only. They are not a new AWS or
PostgreSQL design and do not establish a cross-document transaction requirement.
No remote-provider proof exchange, full crash-injection matrix,
production credential gateway or distributed security certification is claimed.
