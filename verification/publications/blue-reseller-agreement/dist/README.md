# Reseller Agreement

A data-only `Reseller/Reseller Agreement` derived from `Agreements/Agreement`.
Party A is the Supplier; party B is the Reseller. The type includes the full
commercial schedule and twelve readable clauses. It explicitly imports and uses
`MutualActivation/Mutual Activation Clause` and the independent
`ImmediateTermination` package. The original Agreements and Mutual Activation
publications are neither edited nor republished.

Read `docs/agreement-content.md` for the complete proposed business wording.
These are demonstration terms, not a jurisdiction-qualified legal instrument.
Prices, products, territory, contacts, authority and legal requirements need to
be completed/reviewed before real transactions. Text-only obligations are not
silently represented as automated fulfilment, payment or enforcement.

## Composition

* Copy the type's `/defaultTerms` into a plain proposed terms object, edit it, and
  supply it as `/activation/initialTerms`. Defaults are not inherited into the
  negotiated terms: an omitted optional clause must actually stay absent.
* `/activation` is the managed Mutual Activation Clause. Bind both principal actors, their
  Timeline channels, `agreementId`, and `agreementType` when constructing it.
* Negotiable content lives in `/activation/state/target` and `settled`; the root
  mirrors settled terms at `/terms`. A proposed clause remains passive data.
* The optional `/terms/clauses/immediateTermination` is a typed
  `ImmediateTermination/Immediate Termination Terms` value, parameterized by
  `allowedParty: A | B | EITHER`. The published template includes EITHER; authors
  may choose A/B at creation or remove the option before initialization and
  negotiate its addition. The demo takes the latter route.
* Only mutual consent to settled terms activates the agreement and installs the
  executable `/clauses/immediateTermination` child from the exact approved
  parameter, revision and authenticated channels. An absent clause installs
  nothing. Caller-supplied contracts in negotiated data are not executed.
* Invoke `terminateA`/`terminateB` on that child's `partyA`/`partyB` channel. The
  permitted principal acts alone. The root verifies the completed child before
  changing ACTIVE to TERMINATED and emitting Agreement Terminated.

The lifecycle is NEGOTIATING -> ACTIVE -> TERMINATED, with DECLINED as the other
negotiation outcome. Termination cannot re-open negotiation, reactivate the
agreement, rewrite accepted terms or automatically cancel unrelated orders.
No extra `terminateProcessing` action, counterparty approval or timer is needed.

The template has concrete, immutable lifecycle glue in its derived Blue type;
it does not assume that adding a name to a clauses list installs executable
behaviour. The extension specifically recognizes this known termination type.
It is not a generic loader for arbitrary negotiated programs.

The exact runtime profile and Coordination requirements must be supported as
well as the business archives. Mount aliases explicitly: importing Reseller does
not implicitly expose the ImmediateTermination or MutualActivation namespaces.
Use the provided integration scenario and Codex prompt for the signed-Timeline
story and the browser lesson. No package-specific SDK is required.
