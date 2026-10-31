# Independent document processes

This unpublished candidate extends the native Documents factory with one shared
preparation lifecycle. `Document Clause` manages one document; `Documents Clause`
uses an explicit item key and manages a collection. Payment, Shipment and Inspection
adapters are separate follow-on integrations, not qualified by the generic examples.

## Authoring

A receiving template declares its own Activation parties and commercial approval
requirements. The containing clause maps each receiving role to one of its own roles
or to an explicit Party. Role names do not establish identity. In the default inherited mode, main channels and
nonempty reader-key sets must match; representative differences do not replace the
main identity. The explicit bootstrap variant below permits fresh channels while
preserving mapped actors and reader sets. Every existing main party, including observers, must be represented.

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

### Preparation for independent bootstrap

The explicit `parameters.prepareFor: bootstrap` variant was qualified locally on
27 October 2026 for `obtain: provide`. Omit `prepareFor` to retain the existing
inherited-transport behavior; `bootstrap` is the only accepted explicit value.
An explicit `inherited` value, unknown values and nonempty `inheritChannels` are rejected. This option does not change
activation, approvals, source binding or readiness rules.

In this variant, mapped main parties retain their reader keys and identity, but
the prepared child does not copy their parent channels or Timeline Access
documents. Ordinary Core bootstrap supplies fresh child channels, grants and
the declared customer identity, including enrollment of a new reader key.
`provide` compares the resulting native document against the frozen preparation,
checks the mapped actors/readers and child access, then follows the existing
activation and selection lifecycle. The mode is frozen with the preparation;
changing configuration cannot reinterpret an outstanding request.

The customer-facing form can derive its named inputs from `fieldPaths` and the
typed fields in the template. Browsing, editing and reviewing that form does
not call `prepare`. Actual submission starts preparation, bootstrap and provision
under a durable caller-owned request identity. Bootstrap and delivery are host
orchestration, not new activation behavior inside this clause.

Qualification: `tools/check_operation_inputs.py --case bootstrap-preparation`
checks native preparation and rejected inputs. Signed Core
`BootstrappedPreparationTest` subsequently passed both three-account variants
(with/without ordinary Agent representatives): fresh-customer bootstrap, normal
approval gates, provision of the same Order, later child observation, duplicate
provision and denial of customer access to parent timelines. Business's local
browser journey also passed; email delivery and release gates are separate.
The [Core qualification record](https://github.com/bluecontract/myos-core/blob/0b1980346421f70598c1e73a82c2d3db4ffd4d51/docs/bootstrap-compatible-preparation.md)
contains reproduction, provenance, measurements and remaining scope.

Implemented source changes are `Bootstrap Preparation Functions`, Factory Functions'
mode-aware delegation, Preparation Functions' frozen mode/identity/source validation,
and Parties' `accessRecordsValid` helper. Bootstrap access validation requires
canonical paths, initialized proofs, correct provider/timeline and required reader
coverage. This helper validates evidence; it does not grant access. Ordinary Core
bootstrap supplies the fresh transports; no new production Core bootstrap endpoint
or activation option was added. Mapped representatives retain their actor/readers
while obtaining new child channels. Having a representative is not proof of Agent
approval. Later access revocation can still interrupt parent observation.

Packages `a0e1a09` and `6161c99` contain this change; Documents is
`0.8.0-preview.9`. Dependent archive/type IDs were rebuilt, including Activation
`0.8.0-preview.5`, without changing Activation's source behavior in those commits.
These remain unpublished candidate archives. Existing immutable versions and omitted
`prepareFor` behavior remain available; this is not an in-place document migration.

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
