# Independent document processes

This unpublished candidate extends the native Documents factory with one shared
preparation lifecycle. `Document Clause` manages one document; `Documents Clause`
uses an explicit item key and manages a collection. Payment, Shipment and Inspection
adapters are separate follow-on integrations, not qualified by the generic examples.

## Authoring

A receiving template declares its own Activation parties and commercial approval
requirements. The containing clause maps each receiving role to one of its own roles
or to an explicit Party. Role names do not establish identity. Main channels and
nonempty reader-key sets must match; representative differences do not replace the
main identity. Every existing main party, including observers, must be represented.

```yaml
work:
  type: Documents/Document Clause
  parameters:
    obtain: provide
    suppliedBy: seller
    template:
      # A complete independently governed document with Activation and business clauses.
  bindings:
    document: /work
    parties:
      buyer: customer
      supplier: seller
      reviewer: observer
    prepare:
      prepareWork:
        on: workflow
        party: customer
    provide:
      provideWork:
        on: workflow
        party: seller
```

`obtain: create` uses the same construction and frozen-intent path, then initializes
the local child. It preserves the child's declared approvals. `obtain: provide`
retains a prepared requirement and accepts an independently initialized instance.
Provision requires its exact `inResponseTo` request ID and `requirementRef`.
The instance's native origin and execution history are preserved.

`parameters.fieldPaths` maps named `prepare.values` to typed data fields in the
child template. `parameters.suppliedParties` declares roles the supplier may fill;
it is disjoint from the explicit role map and is not valid for local creation.
`parameters.specialization.dataPaths` declares typed provider data slots. The
remaining source and current executable clause policy must match the reviewed
requirement. These slots do not authorize arbitrary extra clauses or operations.

## Sources and selection

Each dependency has a declared name and type, either in the receiving document's
`sources` or in one of its clauses' `parameters.sources`. Repeated declarations must
agree. The containing clause supplies exactly those names through `bindings.sources`:
`self` selects its own native instance; another pointer selects a particular existing
document. An incoming observer never becomes an implicit parent.

The plan freezes these declarations with the template snapshot and compiles native
BEX `$is` checks. Preparation requires the declared type ancestry and field
constraints; structural similarity alone does not make an Agreement an Order.
Validation reads the existing source without replacing its type or copying its
running contracts into a temporary document.

An authorized receiver party calls `bindSource_<role>` with `alias` and a native
`document` reference. For a source already present in the receiver's current graph,
`sourcePath` resolves the current reference during execution. In both cases the
pinned native origin, active state and participant coverage are checked. A prior
reference can become stale when another document advances earlier in an operation;
`sourcePath` avoids reconstructing or substituting that live instance.

Unlinked supplied candidates remain inert in the preparation record. Once required
links are valid, selection installs the actual instance at the managed destination.
The child then observes that selection, and `resume` checks readiness against the
current native graph. This is a resumable handshake: an edge added during a phase
cannot retroactively receive that phase's output. No timing delay or cross-provider
transaction is assumed.

## Participant admission

`Activation.parameters.admission.approvers` names the existing parties who may
approve an additional participant. The shared plan creates a scoped amendment with
zero approvals, even when the supplier is not an approver. It binds the candidate,
prepared requirement, added main identities, reader scope and Activation revision.
The added party separately consents on its actual main channel. Existing commercial
`required` and `approved` values are preserved when admission succeeds.

`approveAdmission_<clause>_<party>` approves the exact pending proposal. Neither a
provider response nor an event containing a party name is an approval. Admission
also rechecks actual access at installation. A queued candidate cannot overwrite
another pending proposal. Declined scopes are retired. A stale Activation revision
requires explicit `rebaseAdmission_<clause>_<party>` and reprovision; old consent
operations cannot authorize the revised scope.

The generic tests cover native channel authority. Signed multi-provider access,
late grant registration, graph-wide admission propagation, domain outcomes and
hosted agent/UI journeys still require separate qualification. Do not treat these
native unit cases as evidence that those integrations are finished.

## Retry and cancellation boundaries

The item key, request ID, prepared requirement and native document origin identify
different things. Equivalent prepare/provide retries return `duplicate` before
configured `before` and `after` effects. Conflicting use of an occupied item is
rejected. A selected or uncertain external obligation is never silently replaced.
Cancellation currently records a request for an unselected item; selected processes
require their domain's cancellation and reconciliation protocol.

Run Core's `scripts/import-independent-processes.py --source <blue-packages>` to
copy a closed, integrity-checked package selection for the generic native tests.
Its `--verify` mode checks the retained fixture bytes. The implementation ledger and
ignored reports in the Core worktree distinguish passing evidence from pending work.


Identity-sensitive channel and contract reconciliation compares exact Blue
identities (`$nodeBlueId`), including authored declarations and captured effective
views. Existing identical declarations are accepted and unchanged contracts are
not rewritten. Absent contracts are installed; different exact declarations keep
the existing conflict behavior. Pending activation channels may be refreshed and
replaced by their admitted transport. This does not change BEX structural equality.
