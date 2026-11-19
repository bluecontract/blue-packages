# Private mandates: operations decided by a proof instead of a readable mandate

Protocol name: `Private Mandates / proof-decided operation authority/1`
Package namespace: `PrivateMandates`
Release status: Core Java integration preview, 19 November 2026

This package extends Mandates and the Coordination evidence channels. It is
additive: `Mandates/Mandate Authority`, which names its mandate in clear, stays
supported and keeps its rules. Names and grammar details marked *provisional* are
working choices of this preview; changing one produces new exact identities.

Terms: E is an operation entry of the agent and K its full Coordination input key.
D is the state of the target document strictly before E. M is the salted mandate
commitment carried by E. T is the proof timeline named by the channel E is
performed on (`CoordinationEvidence/Timeline Channel with Evidence`).

## 1. Scope and layer boundary

In Mandates an operation names the mandate and every processor reads it. Here the
processors cannot read the mandate. The agent's operation carries a commitment to
the mandate, and a zero-knowledge proof published on T states the verdict:

> S is the mandate state signed by the mandate processor for the mandate with
> commitment M. S is the state strictly before E. The actor of E is the mandate's
> authorized actor and the owner of the target channel is the mandate's holder.
> Evaluated in the canonical grant order, S admits (or does not admit) E on state D
> of the target document.

Every processor verifies the proof and reaches the same decision without the
mandate. The rules for reading T (considered entries, first entry, waiting, halting)
are those of the Coordination evidence channels specification. This specification
defines the authority claim, the evidence profile, and when a proof matches.

A processor MUST explicitly support this exact package and protocol, the required
Coordination evidence protocol and the required Mandates protocol. A host that does
not support the profile type a channel declares MUST refuse the document where the
channel is declared. Installing this data package grants no native support.

## 2. Exported types

| Type | Kind | Purpose |
|---|---|---|
| Mandate Commitment Authority | `Mandates/Authority` | Authority claim that carries M and names no mandate |
| Evidence Profile | base type | Published, immutable rules under which evidence on a channel is checked |
| RISC Zero Succinct Receipt Profile | `PrivateMandates/Evidence Profile` | First profile: a succinct RISC Zero receipt of one pinned proving program |

## 3. The authority claim

The agent writes E with a `Mandate Commitment Authority` as its authority claim, in
the place where `Mandates/Mandate Authority` stands today:

```yaml
type: Coordination/Timeline Entry
actor: {blueId: ACTUAL_AGENT}
timeline: {blueId: ADMITTED_AGENT_TIMELINE}
timestamp: 200
onBehalfOf:
  type: PrivateMandates/Mandate Commitment Authority
  actor: {blueId: HOLDER}
  mandateCommitment: <M>
message:
  type: Contracts/Operation Request
  ...
```

| Field | Content |
|---|---|
| `actor` | Inherited from `Mandates/Authority`: the represented holder |
| `mandateCommitment` | M = SHA-256(salt ‖ BlueId of the mandate before initialization), as 64 lower-case hexadecimal characters (*provisional*: field name and text encoding). The byte encoding of the two inputs is fixed by the proving program of the channel's profile |

The claim has no `mandate` field. The agent announces nothing before writing and
takes no part in the proof flow. M tells the prover which mandate is meant and lets
a processor match a proof to the operation.

An operation whose authority claim is a `Mandate Commitment Authority` is
evidence-decided in the sense of the Coordination evidence channels specification.

**Checked by every processor, outside the proof:** that the actor and timeline of E
belong to a participant of the target document; that the claim's `actor` is the
owner of the target channel; the target document's delegation and actor policy;
ordinary operation validation; protection against executing E twice.

**Checked inside the proof,** because only the mandate shows it: status and approval
of the mandate; that the actor of E is the actor of the mandate's
`authorizedActorChannel` and the owner of the target channel is the actor of its
`authorityHolderChannel`; the grants, evaluated exactly as Mandates defines (in the
order of grant keys, document validation before request validation, each predicate
with its own fresh gas ledger, the first grant that passes admits).

A predicate that ends in an execution error, exhausted gas included, makes the
operation unauthorized at its own time: the proof carries a denial.

## 4. Evidence profiles

A profile is one immutable value. Its exact type identifies the part a host must
implement natively; its content carries the data. Processors compare proofs
deterministically only when they use the same profile, so a channel declares a
profile value and never a name such as "latest". The profile is identified by a
hash of its content: the BlueId of the declared value (*provisional*).

`Evidence Profile` is the base type and has no fields. A channel's
`evidenceProfile` MUST be a value of a supported specialisation.

### 4.1 RISC Zero Succinct Receipt Profile

| Field | Content |
|---|---|
| `programImageId` | Image identifier of the proving program, 64 lower-case hexadecimal characters. It fixes the proved statement, the format of the public output, and the runtime and package bindings, gas limit and error semantics the program was built with |
| `providerSetDigest` | Digest of the profile's allowed timeline provider set, as the proving program publishes it, 64 lower-case hexadecimal characters |
| `factsRule` | The facts definition. The only value is `FULL(D)` |

(*Provisional*: the three field names and the type name.)

The type itself fixes what is not data: the receipt kind (a succinct RISC Zero
receipt, in one canonical encoding with no other bytes), the verifier, the
comparison rules of §5 and the facts algorithm.

**Allowed provider set.** The set belongs to the profile, not to a mandate. The
proving program checks that every provider key the mandate processor signed belongs
to a list given by the prover and publishes the digest of that list; the processor
compares the digest. A mandate with a source at a provider outside the set can never
get a matching proof.

**Facts rule.** FULL(D) is the least set of rows (recipe key, goal, root) closed
under the step of `validate`, starting from the definition row of every non-core
type and specification reachable from D and from the definition row of D itself. It
depends on D alone. A processor accepts two digests: that of the empty set and that
of FULL(D), which it computes itself from D.

**Scope.** This profile excludes mandates with Time anywhere in the dependency graph
that affects authorisation.

## 5. When a proof matches

The public output of a proof is a closed list: the BlueId of D, the BlueId of E, M,
the mandate processor key, the provider set digest, a salted commitment to the
mandate processor's signed statement, the digest of the validation facts about D
that were reused, and the verdict.

A `CoordinationEvidence/Proof Entry` is a matching proof for E only if all hold:

| # | Comparison | Against |
|---|---|---|
| 1 | The receipt has the profile's kind and verifies for `programImageId` | The channel's profile |
| 2 | The BlueId of E in the public output | The operation the processor is deciding |
| 3 | M in the public output | `mandateCommitment` of E's authority claim |
| 4 | The BlueId of D in the public output | The processor's own state D before E |
| 5 | The mandate processor key in the public output | `mandateProcessorKey` of the channel |
| 6 | The provider set digest in the public output | `providerSetDigest` of the profile |
| 7 | The validation-facts digest in the public output | The digest of the empty set, or of FULL(D) computed by the processor from D |

- A proof that verifies but fails any comparison is skipped as mismatching. It is
  never counted as a denial.
- A verification that did not complete locally is retried. It is no result.
- The values a processor compares with MUST come from its own accepted state before
  K, the authenticated operation and the authenticated history of T.
- One profile means one classification of one entry on every host.

A matching proof carries its verdict. With an admitting verdict the processor
applies the target document's own rules to E; with a denying verdict it rejects E.

## 6. Compatibility

Documents that use `Mandates/Mandate Authority`, and every earlier publication,
are unaffected. This package and its protocol are unused unless a document declares
a channel with a profile of this package or an operation carries a
`Mandate Commitment Authority`. On a channel without the three evidence fields an
operation with this claim is rejected from the document state.

## 7. Not decided in this preview

- The names listed as provisional, and the text encodings of M, of the image
  identifier and of the digests.
- The format of the mandate processor's signed statement and of its commitment.
- Whether the profile should carry the allowed provider list itself in addition to
  its digest.
- Mandates with timers; a second prover; the duty to reject an operation whose M
  matches no mandate.
- A pinned receiver build for the rules that are code and not profile data.
