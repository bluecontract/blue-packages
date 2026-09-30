# Root-local clauses: executable package design

## Purpose

Author one `Reseller/Reseller Agreement` with two business parameters. Its exact type
supplies initial Mutual Activation and Immediate Termination clauses. The base
Agreement initializes their root state and root contracts. Edits to the live clause
configuration or its parameter sources reconcile the generated implementation.
There are no separately managed clause documents and no new native executable role.

This is a candidate edition of the four existing business packages, built against
`blue-python-with-packages-20260929-233520.zip`. It does not change Language, BEX,
Contracts, Coordination, the runtime dispatch tables, or the 100,000 gas ceiling.
The source and test results in this bundle, rather than the older reference ZIPs,
define what is implemented here.

## Source → resolution → initialization → execution

```yaml
type: Reseller/Reseller Agreement
parameters:
  resellerDiscountBps: 1500
  terminationAllowedParty: B
```

Workbench provides `agreementId` plus `/channels/A` and `/channels/B`, using its
existing signed Timeline providers. These are infrastructure inputs, not Python
implementations of business rules.

Resolution alone is read-only. It exposes the inherited bootstrap and initial
clause templates; it does not emit events or populate execution state. Creating
and initializing the managed document runs the inherited lifecycle workflow.
The first stable result is epoch 0 and contains the generated contracts and state.
A generated operation cannot be used to bootstrap a source that has not yet been
initialized: operation validation happens before that missing operation exists.

## Why `initialClauses` and `clauses` are distinct

The Reseller type stores immutable startup configuration in `/initialClauses`.
The base initializer copies that exact data to the mutable `/clauses` field.
The resulting `/clauses` update invokes reconciliation.

This is intentional, not a second negotiation model. Under the supplied Language,
a literal inherited from a type is a fixed requirement. Placing a fixed binding
such as `/contracts/terminateA` directly in the Reseller type's `/clauses` and then
trying to replace it produces a FixedValueConflict. Omitting an inherited clause
from a replacement also does not remove the inherited clause.

`initialClauses` is the recipe; `/clauses` is the live configuration instantiated
from it. The root remains a Reseller Agreement and is never retyped or generalized
to escape Language checks. A caller can supply an initial `/clauses` configuration
explicitly, but the demo needs none. Thereafter only authorized draft amendment
operations modify that field. Startup templates are not edited at runtime.

## Named parameters and bindings

The Reseller's termination clause configuration includes:

```yaml
type: ImmediateTermination/Immediate Termination Clause
parameters:
  allowedParty:
    from: /parameters/terminationAllowedParty
  acceptedPolicyPointer:
    literal: /terminationAllowedParty
bindings:
  activated: /activated
  terminated: /terminated
  acceptedTerms: /acceptedTerms
  acceptedRevision: /acceptedRevision
  record: /terminationRecord
  policy: /terminationPolicy
  channelA: partyA
  channelB: partyB
  initialize: /contracts/initializeTermination
  terminateA: /contracts/terminateA
  terminateB: /contracts/terminateB
```

Parameter sources have exactly one of `from` or `literal`. `from` may select only
`/parameters` or a descendant; it is not arbitrary root-state access or dynamic
BEX evaluation. Source fields are checked against the exact clause type's declared
parameter kinds, enumeration and numeric bounds.

Bindings are named features or state dependencies, not a list of related fields.
`terminateA` places a specific exported workflow. `terminated` identifies the
Boolean written by the termination implementation and read by activation guards.
`channelA` resolves to the root's actual authenticated channel.

A clause blueprint declares:

- `parameterDefinitions`: admitted parameter shapes.
- `bindingDefinitions`: named contract/state/channel binding slots.
- `stateDefinitions`: fields this clause owns, their kinds and initial values.
- `features`: exact ordinary contract templates, their category, substitutions and
  locations at which to attach resolved clause constants.
- `freezeBindings`: bound Boolean states that prevent material reconfiguration.

Example of a feature declaration (schematic excerpt; exact complete types are in
the candidate sources):

```yaml
features:
  terminateA:
    category: handler
    template:
      type: Contracts/Sequential Workflow Operation
      channel: partyA
      steps:
        - type: Contracts/Compute
          definition:
            type: ImmediateTermination/Root Termination Logic
          entry: terminateA
    fills:
      - path: /channel
        binding: channelA
    constantsAt:
      - /steps/0/constants
```

The installer attaches `parameters`, `bindings` and `clauseKey` to generated step
constants, preserving its fixed entry/side. This is template placement, not eval.
Business logic uses ordinary BEX and current Compute-definition import semantics.
The installer does not dispatch on names such as activation or termination.

The approved exact clause type is the executable blueprint. Instance fields cannot
supply a different feature program by shadowing inherited templates. Editors should
submit only `type`, optional text, parameters and bindings, not an expanded display
projection containing all inherited executable definitions.

## Initialization and reconciliation

The base type contributes seven reserved bootstrap contracts: a lifecycle channel,
an initializer, two update channels, two reconciliation handlers, and a completion
channel watching `/clauseRuntime/revision`.

The base also generates partyA/partyB from the explicit channel inputs, plus the
two draft amendment operations. A and B must have distinct channels; for Timeline
channels their actor identities must also differ. The demo deliberately binds
separate providers and identities.

For each changed configuration, the installer:

1. Computes an exact configuration identity from clause type/parameters/bindings,
   wording when supplied, root parameters and participant channels. Identical input
   is a no-op, even after termination; it cannot reset state.
2. Applies the previously installed clauses' freeze guards. Active, declined or
   terminated configurations cannot be materially rewritten by this preview's
   draft amendment operations.
3. Verifies the exact clause allowlist, parameter sources, named bindings, state
   ownership and generated-path ownership. Collisions and missing prerequisites
   reject the whole processing attempt.
4. Initializes previously absent state, never overwrites established state merely
   to regenerate a workflow. State rebinding/removal requires a migration and is
   rejected in this preview.
5. Installs channels before their dependent workflows, retires obsolete workflows
   before their obsolete channels, and replaces only owned generated entries.
   Bootstrap contracts and processor markers are preserved.
6. Updates installation bookkeeping, then patches the revision descendant. The
   generated setup handlers run only after all features exist.

An operation failure or gas exhaustion rolls back the entire attempt, including
its source amendment. Every intermediate patch must nevertheless be valid. A newly
installed lifecycle handler does not retroactively join the already-running init
dispatch, so setup deliberately uses a distinct post-install update event.

`/clauseRuntime` stores resolved parameters, binding ownership and revision data.
It is not part of `/clauses`; normal business state and bookkeeping therefore do
not recursively trigger clause compilation.

## Live root state and workflows

```
Reseller Agreement                       one managed document
├── parameters                           current draft source inputs
├── initialClauses                       fixed startup templates inherited from type
├── clauses                              instantiated, editable draft configuration
├── activationState / activationHistory  negotiation state and previous configurations
├── activated / negotiationClosed        activation outcomes
├── acceptedTerms / acceptedRevision     exact mutually accepted result
├── terminated / terminationRecord       independent business termination outcome
├── terminationPolicy                    initial input binding, for inspection
├── clauseRuntime                        generated ownership/revision bookkeeping
└── contracts                            inherited bootstrap + generated root features
```

Mutual Activation installs initialize, actA, actB, a state update channel, and
completeActivation. It retains the existing package's negotiation action machine:
propose/accept/reject/withdraw a change, ready, approve, withdraw approval, reject
approval and decline. READY and acceptance of a change are not activation.

The original exact-review helper is adapted to include root agreement identity,
configuration identity, participant channels and candidate terms. Changing draft
parameters or bindings starts a new review and archives the old one. Old approvals
cannot activate a different configuration. Both parties must approve the same
settled terms in the same round.

Immediate Termination installs setup plus terminateA/terminateB. Each operation
has its side fixed by its declared workflow and channel. It requires activation,
the exact accepted terms identity, and an allowed party from the **accepted**
terms. `terminationPolicy.initialAllowedParty` is an inspection value, not an
authoritative override of a later negotiated policy.

Business termination writes `/terminated = true` and evidence to the bound record.
It does not install `/contracts/terminated` or stop ordinary root processing.
Root installer/activation/termination notification events in this preview are
ordinary data tagged with `kind`; they are not implicitly the legacy embedded
event interface. The retained activation action machine still emits its original
typed events.

The original request is idempotent; a conflicting retry is rejected. The first
record's timestamp and processing-event identity are retained on retries.

## Amendment authorization and scope

`amendA` and `amendB` permit either draft participant to replace exactly one of
`parameters` or `clauses`, on its authenticated root channel. A draft is not a
binding agreement; any material change invalidates earlier approvals. Neither
operation accepts arbitrary JSON patches or writes to generated `/contracts`.
They do not implement postactivation bilateral amendments.

A listener that repairs arbitrary contract edits is not a security boundary.
This Agreement simply exposes no operation for such edits. Its bootstrap detects
unowned initial contracts and protected bootstrap overrides. A caller who creates
a different root definition has created a different agreement, not amended an
existing accepted one.

## Current limits, deliberately explicit

This is a functional package candidate, not a generalized plugin sandbox. It
supports named ordinary workflow/channel features and owned root state. State
bindings are single root fields; contract bindings are single `/contracts/key`
paths. This is a package authoring constraint, not a new Language/Contracts limit.
Only A/B party channels are supported by this candidate Agreement scaffold.

State migrations, removing a state-owning clause, postactivation amendment,
arbitrary third-party clause admission, deeply nested state bindings, and generic
logic-slot injection are not implemented. The exact clause types are approved by
the agreement. Full Java parity and large-catalogue performance are not claimed.
See measured gas and test scope in `../verification`.

The old tiny Order proof is retained separately under `reference/`. The current
reseller demo intentionally has exactly two clauses, no products, Orders or
commission processes. A future Order clause can read the same activation and
termination state and manage a single `/orders` collection without embedding
those Orders elsewhere merely to observe them.

## Local implementation references

Source of truth: `blue-packages/*/types/*.blue` and the target's exact protocol
archives. The design relies on target `blue-contracts/spec/contracts.md` §§8, 11,
12, 13, on BEX's ordinary data/patch operators, and on Language's fixed-contribution
rules. `tools/author_candidates.py` is a development-only formatter/authoring aid;
it is not a required client SDK and is never imported by business execution.
