# Shared Agreements and Mutual Activation

These are local integration candidates. They add reusable Blue data to the existing shared package home. They do not install package-supplied Java/Python implementation code.

## Package ownership and names

| Folder | Import prefix | Responsibility |
|---|---|---|
| `blue-coordination` | `Coordination` | Exact clean-Contracts native type binding and protocol data |
| `blue-agreements` | `Agreements` | Agreement, Clause, Clause Progress and Agreement lifecycle events |
| `clause-mutual-activation` | `MutualActivation` | Bilateral negotiation, review rounds, consent and activation events |
| `blue-agreement-examples` | `AgreementExamples` | Portfolio Agreement and selective onboarding example |

Use `Agreements/Agreement` and `MutualActivation/Mutual Activation Clause`. Import prefixes are case-sensitive. `AGREEMENTS-PROFILE.json` contains the mappings; `AGREEMENTS-PACKAGES.json` contains verified exports and archive identities. Every source project imports dependencies by shared relative path. No `src/`, Python runtime, Java implementation, copied dependency tools or sibling source project is added inside these four packages.

A distributable `.bluepkg` contains supporting exact records required by its package format, including normative specification Text records. Those records are content-addressed data. They are not runtime implementations or executable install hooks. The build stages dependency inputs temporarily, then deletes the staging directory.

## Select the runtime explicitly

Java uses `RuntimeProfiles.agreements()`; Python uses `Runtime.agreements()`. Both select the same final Language, clean BEX/Contracts, and the new Coordination binding. Older saved editions remain unchanged. Loading a package never grants it permission to register native runtime roles.

The clean Coordination catalogue has the same 41 supplied definitions and is checked against the shared publication. Runtime context checks remain enabled. Reopening incompatible stored state fails rather than changing its semantics.

## The agreement story

An agreement contains a designated `/activation` clause. Two authenticated principal actors have separate Timeline channels. An operation request names a party's operation (`actA` or `actB`) and supplies `requestId`, `action`, the exact current `round`, and `termsId`.

`activationType` and the clause's `agreementType` are BlueId **text values** binding the reviewed programs. The actual `type` fields remain ordinary Blue type references. Keeping program identity in a Text field avoids treating an unfilled type definition as an Agreement instance.

The available actions are `proposeChange`, `acceptChange`, `rejectChange`, `withdrawChange`, `ready`, `approve`, `withdrawApproval`, `rejectApproval`, and `decline`. Proposal decisions also name the exact `proposalId`.

- READY expresses readiness; it does not grant consent.
- Accepting an edit installs terms; it does not implicitly approve activation.
- A proposer can conditionally approve the exact candidate. Acceptance preserves that approval.
- Counterproposals and new review rounds invalidate old signals.
- Both parties must approve the same settled revision before the clause reaches CONSENTED and the root reaches ACTIVE.
- An exact retry has no further business effect. Reusing a request ID with different content is rejected.
- Changes apply only within the terms value. Executable-looking terms stay passive.
- A trusted derived type declares its allowed contracts. An instance cannot add or replace executable declarations.

The package implements pre-activation negotiation between two principals. It does not add post-activation amendments, n-party consent, mandate delegation, or a remote provider service.

## Typed events

| Event | Emitted when / useful fields |
|---|---|
| `MutualActivation/Change Proposal` | A candidate opens: candidate, explanation, changes, round, termsId, proposedBy, recipientChannel |
| `MutualActivation/Change Decision` | A proposal is accepted/rejected/withdrawn/superseded/declined; exact inResponseTo correlation |
| `MutualActivation/Activation Decision Recorded` | A business action succeeds: agreementId, action, party, round, termsId, requestId |
| `MutualActivation/Activation Succeeded` | Both approvals bind settled terms: agreementId, round, termsId, requestId |
| `MutualActivation/Activation Declined` | Negotiation closes: agreementId, message, requestId |
| `Agreements/Clause Progress` | A committed clause update asks the root to verify current clause state |
| `Agreements/Agreement Progressed` | The root consumes a clause update: agreementId, resulting phase, round |
| `Agreements/Agreement Activated` | The root installs acceptedRevision: agreementId, termsId, round |
| `Agreements/Agreement Declined` | The root records a declined negotiation: agreementId, message |

All Activation events inherit `MutualActivation/Activation Event`; all Agreement lifecycle events inherit `Agreements/Agreement Event`. A filter can select a concrete event or its parent event type. Invalid actions and exact retries emit none of these business events.

Use a `Contracts/Embedded Node Channel` to observe genuine managed children. Its handler receives the delivery wrapper: `$event('/sourcePath')` identifies the embedded location and `$event('/event/...')` reads the child's event. An event forged onto an external Timeline does not become a child completion.

## The portfolio example

`AgreementExamples/Portfolio Agreement` extends Agreement, keeps its own activation clause, and embeds an object collection at `/agreements`. It listens to `Agreements/Agreement Event` from every direct child agreement, counts progress/activation/decline, and emits `AgreementExamples/Onboarding Requested` only for activated IDs listed in `priorityAgreementIds`. All reactions execute as Contracts/BEX workflows; no host callback performs business transitions.

The scenario first initializes each independently managed subagreement and then embeds its exact established version in the portfolio. It does not fabricate initialized markers or raise the Contracts gas limit. A signed, seeded scheduler interleaves the nine operations across the portfolio's children. It also retries accepted requests and verifies that a rejected child input cannot stall subsequent receiving.

## Source and runtime checks

From the package home, use a Python 3.13+ environment with the live Blue Python
library installed:

```sh
python tools/verify_packages.py
python tools/build_reseller_packages.py check
```

The authoring generators and `build_agreements.py` are explicit maintenance tools
for creating changed source/publications. They are not installation steps and must
not be run merely to use these packages. Keep changed releases separate until their
new identities and consumer selections have been reviewed.

The Java and Python repositories own runtime examples, acceptance scenarios and
performance qualification. Their current commands and reports are documented there.
The historical portfolio scenario used signed Timelines and a temporary SQLite
database, with 128 independently initialized child agreements and seeded actions.
Those recorded measurements are evidence for that runtime and package selection,
not a new benchmark performed by this repository cleanup.
