# Hello world: clauses that can change without restarting the Agreement

**Design proposal, not an implemented API.** This replaces the earlier walkthrough
that instructed callers to use `amendA`. The examples below describe the intended
behavior. Clause hooks, the amendment barrier, and the illustrative YAML syntax
still need implementation; these snippets are not runnable package definitions.

The idea is simple: **workflows change `/clauses`; the Agreement reconciles those
changes; each clause decides how an edit affects its existing state.** An
Amendments clause supplies the workflows and their permission rules. The base
Agreement does not supply a mandatory `amendA` or `amendB` operation.

## 1. Start with two tiny business clauses

Our Agreement has a greeting and a counter:

- Calling `sayHello` stores the configured greeting in `message`.
- Calling `increment` adds one to `count`, up to a configurable limit.

The clause declarations are configuration. Their runtime state lives separately.
Both clauses execute inside the same Agreement document; neither is an embedded
document. In the examples, `sayHello` and `increment` are shorthand for operations
exported by `greeting` and `counter`, respectively.

```yaml
# Illustrative document shape for the proposed design.
name: Hello World Agreement
type: Agreements/Agreement

clauses:
  greeting:
    type: Demo/Greeting Clause
    parameters:
      text: "Hello, world!"

  counter:
    type: Demo/Counter Clause
    parameters:
      limit: 5
```

After initialization, the generated state is conceptually:

```yaml
clauseState:
  greeting:
    message: ""
  counter:
    count: 0
```

`Demo/Greeting Clause`, `Demo/Counter Clause`, and the other `Xyz/Name` references
in this document are readable package aliases. A real publication must resolve
them to pinned type BlueIds. Editing a clause must not silently change which
published implementation validates it.

## 2. Define the Greeting Clause

Here is its complete business behavior in pseudocode. `state` means this clause's
state, and `parameters` means its effective configuration.

```text
Demo/Greeting Clause

  parameter: text must be text
  initial state: message = ""              // only if the state field is absent

  operation sayHello():
    state.message = parameters.text
    emit Demo/Greeting Said { message: state.message }

  planEdit(old, proposed, state):
    require proposed.text is text
    accept the proposed configuration
    keep state.message unchanged
    update sayHello's configured text
```

Changing the greeting changes what the **next** call says. It does not rewrite the
last message, clear state, or simulate another initialization.

For example:

```text
sayHello()                  -> message = "Hello, world!"
edit text to "Hello, Alice!" -> message is still "Hello, world!"
sayHello()                  -> message = "Hello, Alice!"
```

## 3. Define the Counter Clause

This clause demonstrates why edit validation needs current state.

```text
Demo/Counter Clause

  parameter: limit must be a non-negative integer
  initial state: count = 0                 // only if the state field is absent

  operation increment():
    require state.count < parameters.limit
    state.count = state.count + 1
    emit Demo/Counter Incremented { count: state.count }

  planEdit(old, proposed, state):
    require proposed.limit is a non-negative integer
    if proposed.limit < state.count:
      reject COUNTER_LIMIT_BELOW_COUNT
        with { proposedLimit: proposed.limit, count: state.count }
    accept the proposed configuration
    keep state.count unchanged
    update increment's configured limit
```

With `count = 2`, reducing the limit from `5` to `3` is legal. Reducing it to `1`
is not. The rule belongs to the Counter Clause, not a generic clause installer.

`planEdit` is a proposed, deterministic planning hook. It reads the old
configuration, candidate configuration, current state, and declared dependencies.
It returns either a rejection or a plan. It does not mutate `/clauses`, call
external services, emit events, or trigger other workflows while validating.
Any state migration it proposes is applied only after the whole plan is accepted.

## 4. Put amendment permission in an Amendments clause

The two clauses above define business behavior. Add a third, separate clause to
define **how this Agreement may be changed**:

```yaml
# Add this entry under /clauses. Still illustrative syntax.
amendments:
  type: Demo/Owner Amendments Clause
  parameters:
    ownerChannel: owner
```

Its intentionally simple policy is:

```text
Demo/Owner Amendments Clause

  operation changeClauses(patch, expectedConfigurationIdentity), on ownerChannel:
    require the event came through the configured authenticated owner channel
    require the affected configuration still has the expected identity
    require every patch target is within /clauses
    apply the patch as one atomic batch
```

`changeClauses` is an operation chosen by this example clause. It is **not a
reserved operation required by Agreements**. Another Amendments clause might
provide `propose`, `approve`, and `execute`; another might allow both parties to
edit selected parameters directly. All eventually make ordinary document changes
under `/clauses`. The same reconciliation mechanism handles them.

The sample channel assumes an authenticated integration; a client-supplied
`owner` string is not authentication. The patch workflow must validate structured
paths, including escaped path segments, and must not permit writes to generated
contracts, state, or the reconciliation infrastructure.

The old, installed permission rules govern the entire batch, including edits to
the Amendments clause itself. A proposed replacement cannot authorize its own
installation. Removing the Amendments clause can deliberately leave the document
with no amendment operation, unless another existing workflow provides one.

## 5. The connector watches `/clauses`

The existing Contracts vocabulary already expresses the subscription:

```yaml
contracts:
  _clauseChanges:
    type: Contracts/Document Update Channel
    path: /clauses
```

The **proposed reconciliation behavior** behind that subscription is:

```text
authorized workflow changes /clauses in an atomic batch
    -> collect the affected clause keys
    -> compare old declarations with the final candidate declarations
    -> validate and plan additions, edits, and removals
    -> atomically apply accepted configuration, wiring, and state migrations
    -> release update notifications and clause lifecycle events
```

A change to `/clauses/counter/parameters/limit` selects `counter`. Replacing the
whole `/clauses` map requires a map diff. Identical before/after content does
nothing. Multiple changes to one clause in a batch produce one edit plan based on
its final candidate configuration. Removing and re-adding the same key within
one batch is therefore an edit when both endpoints exist, not a way to bypass its
edit validator.

### The important addition: an amendment barrier

An ordinary after-write listener is insufficient. Today, Java dispatches document
update listeners after individual patches. A listener that removes and reinstalls
contracts could expose an intermediate configuration to other workflows.

The proposed barrier keeps the candidate configuration tentative and holds
ordinary notifications for the batch. Reconciliation runs before those observers
or the calling workflow continue. If accepted, observers see the coherent result,
never a half-installed clause. Internal reactions then continue within the same
invocation; external publication happens only if that invocation succeeds.

For a single write, the write is the batch. For a workflow's atomic patch batch,
all its writes are reconciled together. Capture old declarations and current state
at the start of this boundary, including any earlier accepted work in the same
invocation. Do not mix observations from different snapshots. If a later reaction
fails, the enclosing invocation still rolls back as a whole.

All writes to the watched configuration need this scheduling rule, whichever
workflow initiated them. Merely adding a new YAML listener does not implement it.

## 6. Make an accepted edit

First call `increment` twice. We now have:

```yaml
clauses:
  counter:
    parameters: {limit: 5}
clauseState:
  counter:
    count: 2
```

For this example's `changeClauses` operation, the patch argument is:

```json
[
  {"op": "replace", "path": "/clauses/counter/parameters/limit", "value": 3}
]
```

The Amendments clause checks its permissions and configuration precondition.
The connector selects `counter`. The installed Counter Clause receives old limit
`5`, proposed limit `3`, and current count `2`. It accepts the edit.

The reconciler keeps `count = 2`, updates the effective limit, and produces one
`Agreements/Clause Edited` event. A subsequent `increment` reaches `3`; another
increment fails the ordinary limit rule.

No clause is removed, no initialization runs, and the unchanged Greeting Clause
is not reinstalled. If the implementation reads effective parameters dynamically,
even replacing the counter's operation definition may be unnecessary.

## 7. Reject an illegal edit

After the accepted edit and next increment above, `count = 3` and `limit = 3`.
Now try the same patch with `value: 1`.

The proposed result is a structured failure such as:

```json
{
  "status": "FAILED",
  "diagnostic": {
    "code": "CLAUSE_EDIT_REJECTED",
    "clause": "counter",
    "path": "/clauses/counter/parameters/limit",
    "reason": "COUNTER_LIMIT_BELOW_COUNT",
    "details": {"proposedLimit": 1, "count": 3}
  }
}
```

The previous committed configuration and state remain in force. The framework
does **not** write the old declaration back through `/clauses`: that would create
another update, potentially recurse, and make other listeners process a reversal.
It discards the tentative invocation instead.

No successful edit event is committed. A diagnostic can explain the rejection;
an audit stream can record failed attempts separately. Emitting a business event
and then throwing in the same transaction cannot create a committed rejection
event. Java currently retains attempted events in failed outcomes as execution
evidence, so consumers must distinguish them from committed business events.

If a batch edits both the greeting and the counter and either edit is illegal,
neither edit is committed.

## 8. Add or remove a clause

To add a second greeting, an authorized workflow applies:

```json
[
  {
    "op": "add",
    "path": "/clauses/farewell",
    "value": {
      "type": "Demo/Greeting Clause",
      "parameters": {"text": "Goodbye!"}
    }
  }
]
```

The reconciler validates its definition and bindings, initializes only its missing
owned state, and installs its behavior. Operation exports are namespaced by clause
key unless explicitly bound to another name, so two greetings do not collide.
It emits `Agreements/Clause Added` once. Existing clauses keep their state and
operations.

To remove the counter, an authorized workflow applies:

```json
[
  {"op": "remove", "path": "/clauses/counter"}
]
```

Removal detaches its owned operations and subscriptions and emits
`Agreements/Clause Removed`. It does not run its edit validator. The framework does
not introduce a business rule saying an active or referenced clause cannot be
removed. If the Agreement needs that restriction, its Amendments clause must
enforce it before writing the patch.

The safe default is to retain the removed clause's state and ownership history.
Removing the counter does not delete its count or any shared document field.
Re-adding the same key and compatible type resumes retained state, after checking
that the proposed configuration is valid for that state. It does not reset the
count to zero. A fresh counter uses a fresh key/state binding; purging or resetting
state is a separate explicit workflow. Different types cannot silently adopt one
another's retained state.

Other clauses' subscriptions are not deleted just because their event source was
removed. They may react to `Clause Removed`; subsequent direct calls to a removed
operation return an unavailable-operation error. Whether that situation should be
prevented or handled is document policy, not an implicit removal veto.

“Add/remove are allowed” still requires well-formed definitions and safe ownership:
adding a clause cannot overwrite another clause's contracts or reset shared state.

## 9. Listen to meaningful events

The lifecycle events below are the proposed public contract. They identify the
affected configuration; they do not require copying the whole Agreement.

| Event | Useful payload |
| --- | --- |
| `Agreements/Clause Added` | clause key, installed type BlueId, configuration BlueId |
| `Agreements/Clause Edited` | clause key, before/after configuration BlueIds, changed relative paths |
| `Agreements/Clause Removed` | clause key, removed type and configuration BlueIds |

For example, a separate audit workflow can listen for `Clause Edited` where the
clause key is `counter`, then store “Counter limit changed.” A separate business
workflow listens for `Demo/Counter Incremented` and reacts to actual counting.
Changing the limit must not falsely emit `Counter Incremented` or `Clause Removed`.

Release lifecycle events after the whole batch has been reconciled, in a defined
stable order by clause key. A handler observes the final coherent configuration.
Further changes requested by a handler start another reconciliation boundary;
they do not modify the plan already being applied. Normal execution limits still
apply to prevent infinite feedback loops.

## 10. Larger clauses follow the same rules

| Change | Required behavior |
| --- | --- |
| Ordinary parameter | Validate the candidate against current state; update only dependent behavior. Unedited parameters remain unchanged. |
| Entire workflow supplied as a parameter | Treat it as configuration data; validate its allowed shape/capabilities and replace that clause's affected workflow. Do not execute it while validating. |
| Binding to an existing document field | Preserve that field. Require an explicit binding-change/migration plan; never assume ownership merely because the clause reads it. |
| Parameter resolved from another field | Declare the dependency. A change to that field must also validate/reconcile affected effective parameters under the same atomic rules. |
| Type/version replacement | Use an explicit upgrade path. The installed type checks whether the transition is legal; the target type validates the migrated result. The candidate cannot supply its own sole approval. |
| Multiple related clause edits | Validate all against the final candidate configuration and one captured state snapshot; merge nonconflicting owned patches, then apply together. |

Missing optional dependencies can be represented explicitly. Required business
relationships, such as “a payment clause must always be present,” belong in the
Amendments policy. State migrations cannot write to another clause's private state
without an explicit coordinated change.

The edit hook is not permission to change configuration through arbitrary paths.
Generated wiring and ownership records are framework-managed. If another workflow
could bypass the watched configuration and overwrite them, the lifecycle rules
would offer no guarantee.

## 11. Keep reconciliation local

Track ownership and dependencies per clause. A targeted edit should inspect that
clause and the behaviors that actually depend on the changed inputs. Reuse compiled
definitions by type/configuration identity. Initialize only missing state and
replace only changed wiring. There is no reason to reinstall 100 unrelated clauses
when the counter's limit changes.

A whole-map replacement still requires finding changed keys. Shared dependencies,
document identity/proof preparation, persistence, and user-defined reactions can
also add work. This design targets local reconciliation; it does not claim that
total coordination time is already constant or that it has been benchmarked.

## 12. What exists today, and what this changes

Today, `Agreements/Agreement` already has a `/clauses` update channel. It also
generates `amendA`/`amendB` and invokes a generic clause installer. Java has atomic
failed outcomes, but dispatches update listeners after individual patches.

This proposal requires:

1. Moving amendment operations and permission policy into an Amendments clause.
2. Adding a deterministic per-clause edit/migration planning contract.
3. Adding an amendment barrier so validation and installation precede ordinary
   observers, including for multi-patch changes and declared parameter dependencies.
4. Applying plans locally with retained state, ownership checks, explicit upgrade
   rules, and lifecycle events that represent the actual change.
5. Testing accepted/rejected edits, batch rollback, re-addition, upgrades,
   dependency changes, and listener behavior before publishing this new contract.

The Markdown is the deliverable for this iteration. The package implementations
and Java runtime have not been changed to implement the proposal.
