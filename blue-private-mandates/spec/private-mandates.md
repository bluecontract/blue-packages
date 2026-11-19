# Private mandates: operations decided by a proof instead of a readable mandate

Protocol name: `Private Mandates / proof-decided operation authority/1`
Package namespace: `PrivateMandates`
Release status: Core Java integration preview, 19 November 2026

This package extends Mandates and the timeline channels with evidence of
Coordination (section 14 of the Coordination specification). It requires the exact
Coordination edition that defines those channels and the Mandates publication built
on it. It is additive: `Mandates/Mandate Authority`, which names its mandate in
clear, stays supported and keeps its rules. Names and grammar details marked *provisional* are
working choices of this preview; changing one produces new exact identities.

Terms: E is an operation entry of the agent and K its full Coordination input key.
D is the state of the target document strictly before E. M is the salted mandate
commitment carried by E. T is the evidence timeline named by the channel E is
performed on (`Coordination/Timeline Channel with Evidence`).

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
are those of section 14 of the Coordination specification. This specification
defines the authority claim, the evidence profile, and when a proof matches.

A processor MUST explicitly support this exact package and protocol, the required
Coordination protocol and the required Mandates protocol. A host that does
not support the profile type a channel declares MUST refuse the document where the
channel is declared. Installing this data package grants no native support.

## 2. Exported types

| Type | Kind | Purpose |
|---|---|---|
| Mandate Commitment Authority | `Mandates/Authority` | Authority claim that carries M and names no mandate |
| RISC Zero Succinct Receipt Profile | `Coordination/Evidence Profile` | First profile: a succinct RISC Zero receipt of one pinned proving program |

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

The claim has exactly these two fields and its type. It has no `mandate` field.

**The field set is checked by the processor.** The Language schema limits the claim
to two fields with a value, but it does not close the field set: it admits a further
field that carries only a type, such as `mandate: {type: Mandates/Operation
Mandate}`, and a further field written as a reference that resolves. A processor
therefore checks the field set itself, from the entry alone: a claim whose fields
are not exactly `actor` and `mandateCommitment`, beside its type, is malformed, and
the operation is rejected at once from the document state, without reading T. A
claim never carries or points to a mandate.

A claim that the schema does reject, for example one with a third field that has a
value or with a `mandateCommitment` of another length, is a different case. The
whole `Timeline Entry` that carries it is then not admissible Blue content. This is
existing Coordination behaviour for any inadmissible entry and is not changed here:
there is no operation to decide, and a reader cannot import the agent's operation
timeline past such an entry. It is the fault of that timeline's writer.

`mandateCommitment` is well formed only as 64 characters `0-9a-f`. The schema fixes
the length; the processor checks the characters. An operation whose claim carries a
malformed `mandateCommitment` is rejected from the document state, without reading
T. The agent announces nothing before writing and takes no part in the proof flow. M tells the prover which mandate is meant and lets
a processor match a proof to the operation.

An operation whose authority claim is a `Mandate Commitment Authority` is
evidence-decided in the sense of section 14 of the Coordination specification.

**Checked by every processor, outside the proof.** These are the checks a processor
performs today for a `Mandates/Mandate Authority` without reading the mandate. They
are unchanged, they come before T is read, and a failure has the same outcome as it
has today for `Mandate Authority`:

1. the claim's `actor` is the actor of the target channel the operation selects;
2. that target channel exists and is a concrete `Coordination/Timeline Channel`
   (which includes `Timeline Channel with Evidence`);
3. the target document contains a Timeline Channel with the actor and timeline of E
   (the delegate participant);
4. the target document's actor policy admits E as a delegated action.

Ordinary operation validation and protection against executing E twice also remain
with the processor. Every check that today needs the mandate is in the proof.

**Checked inside the proof,** because only the mandate shows it: status and approval
of the mandate; that the actor of E is the actor of the mandate's
`authorizedActorChannel` and the owner of the target channel is the actor of its
`authorityHolderChannel`; the grants, evaluated exactly as Mandates defines (in the
order of grant keys, document validation before request validation, each predicate
with its own fresh gas ledger, the first grant that passes admits).

**When the mandate or a predicate is at fault.** The statement always ends in a
verdict in these cases; none of them is a missing proof:

1. *An error in a grant's predicate.* A predicate that ends in an execution error
   or meets an invalid operand makes that grant not match. So does a completed
   result that is not the Boolean true, as in Mandates today. The remaining grants
   of the scope are tried, so the verdict does not depend on the order of the
   grants: E is admitted exactly when at least one grant passes.
2. *Exhausted gas.* A predicate that exhausts its gas ledger ends the whole decision
   with "the mandate does not admit E". The remaining grants are not tried.
3. *A fault of the mandate.* The signed state is not an Operation Mandate, it
   belongs to another Mandates package than the profile's program was built with,
   or it lacks its approval, its participants or its scope: the verdict is "the
   mandate does not admit E".

In every such case the proof carries a denying verdict, E is rejected at its own
time, and the target document continues with the next input. Repairing the mandate
needs an update of the mandate, which applies to later operations.

This is a deliberate difference from mandates named in clear. For a
`Mandates/Mandate Authority` the Mandates specification says only that an error
never authorizes, and a processor that evaluates the predicate or reads the mandate
itself may give no verdict and stop processing the target document. Here the
represented party answers for its own mandate: the other participants cannot read
it, so a faulty mandate must not stop the document for everyone. Content that the
prover cannot obtain and a local interruption of proving or of verification are not
faults of the mandate: they give no proof or a retry, never a verdict.

## 4. Evidence profiles

A profile is one immutable value. Its exact type identifies the part a host must
implement natively; its content carries the data. Processors compare proofs
deterministically only when they use the same profile, so a channel declares a
profile value and never a name such as "latest". The profile is identified by a
hash of its content: the BlueId of the declared value (*provisional*).

`Coordination/Evidence Profile` is the base type and has no fields. A
channel's `evidenceProfile` MUST be a value of a supported specialisation.

The Language schema of the channel does not enforce this. Typing of the
`evidenceProfile` field is structural: the schema admits a value with no type and
values of unrelated types. What protects is the native rule of Coordination section
14.3, which a processor MUST implement: the exact type of the value must be a
supported specialisation of `Coordination/Evidence Profile`; anything else counts
as a missing field, and every operation with a `Mandate Commitment Authority` on
that channel is rejected from the document state.

### 4.1 RISC Zero Succinct Receipt Profile

| Field | Content |
|---|---|
| `programImageId` | Image identifier of the proving program, 64 lower-case hexadecimal characters. It fixes the proved statement, the format of the public output, and the runtime and package bindings, gas limit and error semantics the program was built with |
| `allowedProviders` | The profile's allowed timeline provider set: a list of `Coordination/Ed25519 Public Key`, strictly ascending when compared as 32-byte values |
| `factsRule` | The facts definition. The only value is `FULL(D)` |

The value has exactly these three fields. (*Provisional*: the field names and the
type name.)

The type itself fixes what is not data: the receipt kind (a succinct RISC Zero
receipt, in one canonical encoding with no other bytes), the verifier, the
comparison rules of §5, the provider set digest function and the facts algorithm.

**Allowed provider set.** The set belongs to the profile, not to a mandate. The
proving program checks that every provider key the mandate processor signed belongs
to a list given by the prover and publishes the digest of that list. The profile
carries the list; the digest is derived and is not a field:

> provider set digest = SHA-256(key_1 ‖ key_2 ‖ … ‖ key_n), over the raw 32-byte
> keys in list order, written as 64 lower-case hexadecimal characters.

For the empty list this is the SHA-256 of the empty byte string. A mandate with a
source at a provider outside the set can never get a matching proof.

**Well-formed profile.** For a value whose exact type is this profile, the Language
schema enforces the three required fields, at most three fields with a value, the
length of each key and of `programImageId`, distinct list elements and the value of
`factsRule`. As for the authority claim (§3) it admits a further field that carries
only a type. The processor additionally requires that the fields are exactly these
three, that `programImageId` and every key are 64 characters `0-9a-f`, and that
the list is strictly ascending by key bytes. A
profile that fails any of these is malformed; under section 14 of the Coordination
specification the channel then lacks its profile, and every operation with
a `Mandate Commitment Authority` on it is rejected from the document state.

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

A well-formed `Coordination/Proof Entry` (Coordination section 14.5; the processor,
not the schema, decides well-formedness) is a matching proof for E only if all hold.
The entry's `document` and `operationEntry` references are a routing hint and are
not among the comparisons: a processor may skip an entry whose hint does not name
this document and E without verifying it, and an entry whose hint disagrees with
the proof's own public output is skipped (Coordination sections 14.5 and 14.6).
Under this profile the hint disagrees with the public output when `operationEntry`
does not name the entry whose BlueId the public output carries, or when the proof
satisfies comparisons 2 and 4 for this document while `document` does not name this
document's initial BlueId. The public output carries the BlueId of D, not the
document's initial BlueId, so `document` is compared with the document the
processor is processing.

| # | Comparison | Against |
|---|---|---|
| 1 | The receipt has the profile's kind and verifies for `programImageId` | The channel's profile |
| 2 | The BlueId of E in the public output | The operation the processor is deciding |
| 3 | M in the public output | `mandateCommitment` of E's authority claim |
| 4 | The BlueId of D in the public output | The processor's own state D before E |
| 5 | The mandate processor key in the public output | `mandateProcessorKey` of the channel |
| 6 | The provider set digest in the public output | The digest derived from `allowedProviders` of the profile (§4.1) |
| 7 | The validation-facts digest in the public output | The digest of the empty set, or of FULL(D) computed by the processor from D |

- A proof that verifies but fails any comparison is skipped as mismatching. It is
  never counted as a denial.
- A verification that did not complete locally is retried. It is no result.
- The values a processor compares with MUST come from its own accepted state before
  K, the authenticated operation and the authenticated history of T.
- One profile means one classification of one entry on every host.

A matching proof carries its verdict. With an admitting verdict the processor
applies the target document's own rules to E; with a denying verdict it rejects E
and the document continues. A denying verdict includes the cases of §3 in which
the mandate or a predicate is at fault.

## 6. Compatibility

Documents that use `Mandates/Mandate Authority` keep their rules, and every earlier
publication is unchanged and remains selectable. This package and its protocol are unused unless a document declares
a channel with a profile of this package or an operation carries a
`Mandate Commitment Authority`. On a channel without the three evidence fields an
operation with this claim is rejected from the document state.

## 7. Not decided in this preview

- The names listed as provisional, and the text encodings of M, of the image
  identifier and of the digests.
- The format of the mandate processor's signed statement and of its commitment.
- Mandates with timers; a second prover; the duty to reject an operation whose M
  matches no mandate.
- A pinned receiver build for the rules that are code and not profile data.
