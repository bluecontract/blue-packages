# Reseller clauses

Unpublished catalogue, fulfilment and commission clauses imported from the
owner-supplied reseller handoff. Fourteen original authored exports are retained
byte-for-byte; the additive fifteenth export is the hosted Order bootstrap profile.

`source-import.json` records the archive SHA, its recorded Packages base and dirty
source digest, and every original definition hash. The original ZIP and its native
examples remain external historical evidence. Their prior qualification counts do
not qualify this new package or its hosted profile. This worktree does not include
the archive author's separate reports, semantic cards or legacy example directory.

The current package uses the already qualified dependency composition recorded in
`blue-package.lock.json`; it does not overwrite those dependency packages. The
original embedded Customer Orders source is retained as a distinct historical
profile. Current hosted behavior and tests are described below.

## Hosted Order bootstrap candidate

`Customer Orders Bootstrap Clause` is an additive hosted profile. The original
`Customer Orders Clause` remains the historical embedded factory and retains its
exact authored source. Successful authenticated hosted provision remains pending;
the passing component harness does not complete hosted qualification.

Bind `startOrder` to the ordinary partner `newOrder` workflow and `provide` to a
separate partner `provideOrder` workflow. The input to `newOrder` is
`{key, requestId, customer, quoteKey, description?, groups?}`. `customer` is the
verified Core account identity, not a marketing email or a freely replaceable
provider slot. The exact request, quote, authoritative price and fulfilment
snapshot are retained natively. Repeating that request returns its original
obligation, including after later catalogue/date changes; changed input for its
key is rejected.

The clause uses the existing Documents `prepareFor: bootstrap` / `obtain: provide`
lifecycle. It prepares an uninitialized Order and preserves the template's
`required` approvers. Only the three separate corrected example templates use
`required: []`. Core performs its ordinary bootstrap for all mapped parties and
representatives. Provision must satisfy the unchanged Documents source, policy,
requirement, origin and full access checks, plus the frozen customer identity and
commercial snapshot. The source does not implement a manual channel binder.

`bootstrap-composition.json` identifies the exact reused native function nodes.
The new constructor and domain hooks are local to this profile; no generic
Documents, Parties, Activation or Core source is changed. Native quote/group and
rounding helpers are also reused by exact references. One process has separate
stable operation keys for preparation, bootstrap and provision.

Supplier confirmation of dates remains separate. An Order's Payment Instruction
preparation and `providePayment` are unchanged, separate processes; Order provision
is not payment execution. The inherited generic preparation action is routed
through the same checked customer-order input and cannot accept arbitrary prices.

## Review candidate and verification

This adaptation is based on repository main `4450364dc9497bee1f97fb9eac9f7c514504562f`.
The import-time facts in `source-import.json` remain historical provenance. All
thirteen imported dependency archives match the component-qualified `cd3bbfa9`
composition byte-for-byte. The original component evidence is retained under
`reports/reseller-bootstrap-integration/` locally: five preparation scenarios,
source integrity and exact replay/access checks passed. Earlier failures remain
recorded; successful authenticated hosted provision and payment execution remain
unqualified.

The committed distribution is a review candidate. `clause-reseller` is deliberately
absent from `PACKAGE-SOURCES.json` and the current release catalogues. The ordinary
collection CI therefore does not build, publish or qualify this new package.
Selecting or releasing it is a separate reviewed change.

With Python dependencies from `tools/requirements.txt`, Java 21 and the qualified
`BLUE_JAVA_CLASSPATH`, reproduce the package checks explicitly:

```sh
python3 tools/build_final_gas.py clause-reseller --check
python3 -m unittest discover -s clause-reseller/tests -p 'test_*.py' -v
```

`tests/BootstrapOrdersConformance.java` is the component harness; it uses the
qualified Core `CompositionPackages` test helper and stops at `awaiting_provider`.
It is not a replacement for the pending authenticated hosted integration proof.
