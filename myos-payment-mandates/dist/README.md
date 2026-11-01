# Seller policy and correlated Order payment preparation

This additive candidate retains the current expiry-aware bootstrap PI semantics and adds
`paymentPreparation`: `orderDocumentId`, `clauseId`, `itemKey`, and `requestId`.
`orderDocumentId` is the native initial Order identity, not its changing state identity.
The correlation contains no private Agreement reference and does not prove Agreement origin.
The root slot is optional so the reusable PI template can be stored in a live Order before
preparation. Whenever a correlation value is present, all four typed fields are required.
This is not permission to bootstrap an unbound PI: Core must reject missing, partial, forged
or mismatched correlation for every actual correlated PI source, including raw, YAML,
reference and inherited-type forms. The native preparation expression injects the complete
object before source hashing. Filled placeholder values are not supported: native field-slot
validation treats them as fixed constraints and rejects replacement.

The new Order profile maps `parameters.fieldPaths.paymentPreparation` to
`/paymentPreparation` and uses `examples/correlated-prepare-params.blue` as its preparation
connection's `params` expression. This expression overwrites caller correlation using the
native Order identity, current clause key and ordinary request/key defaults. The existing
preparation machinery validates the typed slot and computes `requirementRef` from the
resulting source, including correlation. Retry retains the same source and requirement.

The reusable template must explicitly contain the typed, unbound `paymentPreparation` slot
shown in `examples/correlated-template-slot.blue`: native `fieldPaths` validates supplied values
against that source constraint. The optional enclosing property permits this typed-only slot
while the concrete prepared object must contain all four required fields.

Only the new correlated profile is eligible for policy automation. Historical profiles,
publications and documents remain unchanged. Host code must compare the source and every
correlation field with the actual pending requirement before reserving/bootstrap; these fields
alone confer neither authority nor trust. Exact new-type allowlisting, shared reservation and
seller-policy authorization remain Core responsibilities. No account runtime default changes.

## Seller policy mandate

`Seller Payment Policy Mandate` extends the retained Initializable Mandates operation mandate.
Its fixed lifecycle initializer constructs one `seller/providePayment` grant as literal source
and installs it in `grantTemplates.payment` and `scope.payment`. Inherited holder approval is still required; revocation
empties the runtime scope. The policy identifies the seller, its Agent, exact Order profile,
PI type, provider, recipient payment account, guarantor, currency and per-payment amount range.
`bootstrapPreparedPayment: true` is explicit consent for Core's narrow prepared-source flow;
it grants no generic bootstrap, Order approval or customer preparation operation.

`expectedProgram` contains canonical `orderType`, `contracts`, `clauses` and `paymentTemplate`
blueprints, the full executable `timelineAccess` section and a fixed `rootKeys` roster.
Business constructs this recipe for the supported direct or reseller profile;
Core independently qualifies it before accepting bootstrap authority. Initialization pins the
native identities of both policy and recipe in `grantTemplates.payment.target.documentValidation.function.constants`.
Native Mandates program protection freezes `grantTemplates` after initialization. The predicate
reads those protected identities, so later outer policy/recipe changes cannot widen approval.
The Mandates specification permits additional holder-reviewed workflows; type ancestry alone
therefore does not qualify an automation mandate. Core and Business must independently
require the exact supported initial and current executable program before accepting automation
authority. This includes the host-generated Process Embedded and TimelineAccess bindings.
The package does not impose a partial contract-name or root-extension allowlist: such a gate
rejected ordinary Core bootstrap and did not prevent appended Compute statements. Native
whole-program approval and its protected configuration remain separate from application
qualification; only the approved program may drive subsequent scope transitions.
Literal construction is intentional: copying a native grant view materializes inherited function
metadata that the strict authority predicate wire contract rejects. Each section has a
`definition` and enumerated `replacements`. Definitions are parent-first inert rows
(`path`, `kind`, `scalar`); pure references use `kind: reference` and an exact `node` reference.
The fixed decoder reconstructs source data before substitutions, preserving schema and
typed-only fields without traversing them as live Blue objects. The fixed native predicate reconstructs expected
sections using checked primitive scalar replacements and compares their identities with
untouched target sections. It never strips metadata from actual executable definitions.
Only native initialized document/timeline references and the two reconstructed payment-template
snapshots are non-scalar substitutions. A fresh expected root uses the fixed key roster,
canonical Order type and primitive scalar leaves, so root or scalar metadata cannot hide
outside section checks. The expected root type is the exact public Order with Clauses
reference `DXVyaZMh1ohnUF7oY9NgDrwD7VB71WhVu7668Xwam1XS`. The approved
`expectedProgram.orderType` retains its inherited `schema.required: true`; its exact identity
is `FNLBDR37nGH2WGTw8r53RvF2HpAza34xBcy1ygcztG3z`. This identity is reproducible
by refining that public Order definition with only the required-field schema. It does not
depend on the seller mandate package root. Copying the refined field into a target type
would incorrectly change the expected program, so actual and expected field contexts are
checked separately without stripping either operand. Embedded timeline-access documents have their own exact section check. Unknown operations, channels, clauses and metadata
therefore remain part of the comparison. Supported initial profiles use the canonical two-
or three-party roster with one built-in Agent representative per party. Other profiles are
manual; this policy is not an Agreement-origin proof or a cumulative spending budget.

The retained Initializable Mandates archive is copied verbatim from Core's
`runtime/blue-coordination-core/src/main/resources/mandate-initialization/mandates.bluepkg`:
root `4kaMxybWTTeTpkzUtoYVUPk8dUo3HxKM5MG5joxN6LFL`, archive SHA-256
`5dc771ff47b6e2cc59b4043cfb8fb1c8b8bfab288712e693e01b07da9fb8c588`.
It is a retained import, not an editable foundation or a replaced historical publication.
The manifest declares Contracts execution and preserves the imported Mandates specification
closure. Running the mandate additionally requires the matching explicit MandateInitializationV2
execution selection and exact native predicate identity callbacks; this package changes no defaults.

## Local qualification boundary

`tools/PaymentPreparationCorrelationConformance.java` exercises native Contracts preparation
with a generic child carrying the typed correlation slot. It checks the exact initial
parent Blue ID, native clause/item/request values, replacement of forged caller correlation,
different parent requirement identities, the absent optional request-key fallback to `single`,
and unchanged retry. Its `baseline` argument
runs the historical uncorrelated preparation and fails the correlation assertion.
This is not a hosted PI bootstrap, seller mandate, checkout or completed purchase test.

`tools/SellerPaymentPolicyConformance.java` uses signed native holder inputs to verify
Pending initialization, exactly one installed grant, approval to Active and revocation to
Terminated with an empty scope, plus exact native policy/recipe identity pins. Its
`host-embedded` mode includes the exact public Process Embedded contract used by Core bootstrap
and must complete the same lifecycle. The prior package rejected it with BEX_EXECUTION_REJECTED.
The other mutation modes retain counterexamples and conflicting-value checks for application
qualification; they are not a claim that the native mandate type rejects every extension.
In particular append-step/do and self-deleting workflows require exact initial program
qualification before consent or credential issuance. Its empty blueprint is only a lifecycle
fixture; it does not qualify the actual Order predicate or prepared PI bootstrap. A strict-arity
expression guard is insufficient because an added ordinary field changes a singleton BEX
operator into ordinary object data.
Run its packaged class
`blue.core.SellerPaymentPolicyConformance` with repository path and exact package root.

Compile the correlation tool together with `tools/BootstrapPreparationConformance.java` against the
qualified Core Java classpath, then run `PaymentPreparationCorrelationConformance` with this
repository's absolute path. `python3 tools/build_final_gas.py myos-payment-mandates --check`
checks deterministic package reconstruction; catalogue/release integrity checks are separate.

The package root and dependency closure remain provisional until the seller policy
composition completes its native initialization, revocation and actual-Order qualification. Consumers must not treat this
partial candidate as a final runtime selection or automation release.
