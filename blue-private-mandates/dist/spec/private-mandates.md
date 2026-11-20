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
| Mandate State Attestation | document signed by the mandate processor | What the mandate processor states about one state of a mandate (§4.2) |
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
| `mandateCommitment` | M = SHA-256(salt ‖ BlueId of the mandate before initialization), as 64 lower-case hexadecimal characters (*provisional*: field name and text encoding). The salt is at least 16 bytes; with a shorter salt no proof can be made. The byte encoding of the two inputs is fixed by the proving program of the channel's profile |

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
evidence-decided in the sense of section 14 of the Coordination specification. The
claim is recognised by its exact type: the type of the claim must be exactly
`Mandate Commitment Authority` of this package. A claim of a subtype, of a parent
type or with no type is not evidence-decided, and no proof can be made for it.

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

**Conditions before any verdict.** A verdict, admitting or denying, exists only for
a state that is shown to be the mandate's state strictly before E. The signature of
the mandate processor, the position and its provider evidence, and the timer
comparisons of §4.2 are therefore checked before anything is decided from the
mandate. If one of them fails no proof can be made, whatever the mandate holds. In
particular a fault of the mandate (case 3 below) gives "does not admit" only when
the attested position covers the channel timelines of the attested state.

**How the grants decide.** The grants of the scope are taken in the order of their
keys, compared as sequences of UTF-16 code units. The Mandates specification does
not state an order; this is the order the first program and the Mandates processor
use. A grant *applies* to E when its target names the channel and the operation of
E and, if it pins an initial document, that document is the target document. For
each grant that applies, the document validation is evaluated first and the request
validation only when the document validation passed; a grant passes when every
validation it has passes. A grant that has a request `validation` does not pass
when E carries no request payload. Every grant that applies is evaluated, also after the
decision is made. The verdict is taken from the outcomes in key order: the first
grant that passes admits E; if none passes the mandate does not admit E.

**When the mandate or a predicate is at fault.** The statement ends in a verdict in
these cases; none of them is a missing proof:

1. *A grant that cannot match.* A predicate that ends in an execution error or meets
   an invalid operand makes that grant not match. So does a completed result that
   is not the Boolean true, as in Mandates today, and so does a predicate that is
   statically inadmissible. A validation node that is not an object, a Text or a
   list for example, likewise makes its grant not match. The other grants are tried.
2. *Exhausted gas.* A predicate that exhausts its gas ledger ends the decision with
   "the mandate does not admit E", unless a grant earlier in key order has already
   passed. This is the one case in which the verdict depends on the order of the
   grants: a gas-exhausting grant before an admitting grant denies, the same grant
   after it does not change the admission.
3. *A fault of the mandate.* The signed state is not an Operation Mandate; it belongs
   to another Mandates package than the profile's program was built with; it has no
   approved program, or its approved program is not the program of the state; it
   lacks its participants or its scope; or a grant of its scope has no target. The verdict is "the mandate does not admit E", whatever the other grants
   are.

In every such case the proof carries a denying verdict or, in case 1, the verdict
the other grants give. E is decided at its own time and the target document
continues with the next input. Repairing the mandate needs an update of the mandate,
which applies to later operations.

**A validation node that is not well formed.** A validation node that fails strict
certification (it violates its schema or the compatibility of its types) and for
which the mandate processor signed no certified row (§4.2) gives no proof for E: the
proof would have to certify the node itself and cannot. An honest mandate processor
does not approve a mandate with such a node. When the mandate processor did sign a
row for such a node, it is at fault, and the outcome is whatever the evaluation of
that grant gives under the rules above.

**A grant that cannot be evaluated.** A grant that applies to E and whose evaluation
needs content that cannot be supplied to the proving program is different: it is
not a fault the statement can establish, because the statement cannot tell content
that does not exist from content that is withheld. No proof can then be made for E,
whatever the order of the grants and also when another grant would admit. So
withholding content can never choose a verdict: for one S, D and E at most one
verdict is provable. The party ends the wait with a Rejection Entry (Coordination
section 14.5); repairing needs an update of the mandate.

This is a deliberate difference from mandates named in clear. For a
`Mandates/Mandate Authority` the Mandates specification says only that an error
never authorizes, and a processor that evaluates the predicate or reads the mandate
itself may give no verdict and stop processing the target document. Here the
represented party answers for its own mandate: the other participants cannot read
it, so a faulty mandate must not stop the document for everyone. A local
interruption of proving is not a fault of the mandate: it gives no proof, never a
verdict.

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
| `factsRule` | How the proof commits to the validation facts about D it reuses: `FULL(D)` or `MERKLE(FULL(D))`. A profile names exactly one, and it must be the rule the program of `programImageId` was built with |

The value has exactly these three fields. (*Provisional*: the field names and the
type name.)

The type itself fixes what is not data: the receipt kind (a succinct RISC Zero
receipt, in one canonical encoding with no other bytes), the verifier, the
comparison rules of §5, the provider set digest function and the facts algorithms.

**The receipt.** `receipt` of a Proof Entry decodes to exactly one canonical
encoding of a succinct receipt. A byte string that is not that encoding is skipped,
also when a verifier would accept it: trailing or altered bytes, another receipt
kind, and a receipt whose `control_inclusion_proof.index` has a bit set above the
length of its path. The verifier reads one bit of that index per digest of the path
and ignores the bits above, three bytes in the receipts of the first program, so
such a receipt verifies like the original; it is skipped all the same. Any failure
or fault while a receipt is decoded or verified, a panic of the verifier included,
is a skip of that entry and never a retry (§5.1).

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
three, that `programImageId` and every key are 64 characters `0-9a-f`, that the
list is strictly ascending by key bytes, and that `factsRule` is one of the two
values. A
profile that fails any of these is malformed; under section 14 of the Coordination
specification the channel then lacks its profile, and every operation with
a `Mandate Commitment Authority` on it is rejected from the document state.

**The fact set.** FULL(D) is the least set of rows (recipe key, goal, root flag)
closed under the step of `validate`, starting from the definition row of every
non-core type and specification reachable from D and from the definition row of D
itself. It depends on D alone. The goal of a row is `definition` or `value`. A
recipe key is a JSON text; neither it nor a goal contains a tab or a line feed.
The rows are ordered by recipe key, then goal, then root flag (false before true),
keys and goals compared as byte strings; a set has no two equal rows.

Both facts rules commit to this same set. They differ only in the digest that the
public output carries. Below `D` is the BlueId of D as text, `count` the number of
rows in decimal, `flag` the character `1` for a true root flag and `0` for false,
`TAB` the byte 0x09, `LF` the byte 0x0A, and `hex` lower-case hexadecimal.
(*Provisional*: the domain texts, which are those of the first program.)

`FULL(D)` — one hash over all rows in order:

    digest = hex SHA-256( "blue.research.validation-facts/1" LF "target" LF D LF count LF
                          ( key TAB goal TAB flag LF )  for each row in order )

`MERKLE(FULL(D))` — a Merkle tree over the rows in the same order:

    leaf(row)   = SHA-256( 0x00 || key || TAB || goal || TAB || flag )
    node(l, r)  = SHA-256( 0x01 || l || r )
    MTH({})     = SHA-256( "" )
    MTH({d})    = leaf(d)
    MTH(d[0:n]) = node( MTH(d[0:k]), MTH(d[k:n]) ),  k the largest power of two smaller than n
    digest      = hex SHA-256( "blue.research.validation-facts-tree/1" LF "target" LF D LF
                               count LF hex(MTH) LF )

This is the Merkle Tree Hash of RFC 9162 section 2.1 with the leaf content above.
The row count is inside the digest. Under this rule a proof is given only the rows
it uses. Each comes with its index and its audit path, and the program uses a row
only when the path gives the root for that index in a tree of `count` leaves
(RFC 9162 section 2.1.3.2); otherwise no proof is made.

**The empty set.** A proof may reuse no facts and validate what it reads itself. It
then carries the digest of the empty set under the profile's rule: for `FULL(D)`
the first formula with `count` 0 and no row; for `MERKLE(FULL(D))` the last formula
with `count` 0 and MTH({}).

**What a processor accepts.** Exactly two digests, both under the rule the profile
names: that of the empty set, and that of FULL(D), which it computes itself from its
own records of D (under the Merkle rule it builds the tree and compares count and
root through the digest). Any other digest is a mismatch and the entry is skipped.
This includes a proof made under the other rule: a profile names one rule, and a
proof made under the other never matches.

Worked example for D = the one-character text `D` and the three rows, in order,
(`[["A"],[]]`, `definition`, false), (`[["A"],[]]`, `value`, true),
(`[["B"],[]]`, `definition`, true):

    leaf 0 = 54719cff97ae9a8ce6528246b84deb21c543d785171c4f951722f01253d1b204
    leaf 1 = 3b174bcda93ca72fe37d88515041263eab7dd8afbd08af397e481a393d627d38
    leaf 2 = 870819661e900fe1f0e0b1cd64b1cb514078b1a59ec4cf023a6bc7bb7cc5faad
    node(leaf 0, leaf 1) = 30454d725d79c97d0297fab76e5ab0cbb25528c263d99d632326d339c5347e6f
    MTH    = ce0af5187a4b1be1f76521a68712900f2c1bfde5d2de49484c12fb0e27cb8b17
    MERKLE(FULL(D)) digest = 23edefcd70cd8dd859d44786601a93b7c8c6b4bce2dbbe53056db84e38ce8829
    FULL(D) digest         = b85228f7a7f16ff78440f3cad17208781fc01dc5baee9109352927c96cfdc4ce
    empty set, MERKLE(FULL(D)) = 5fc080ad098dbbf7389835369c2e4a0d9fb667dac5f7d6aaa35d5e19d21d1789
    empty set, FULL(D)         = ee8f53183e62b992d9ce00caaa933ce3351898099888df5ca250d10a3011fe7a

The audit path of leaf 2 is [node(leaf 0, leaf 1)]; that of leaf 0 is [leaf 1, leaf 2].

**Scope.** This profile excludes mandates with Time anywhere in the dependency graph
that affects authorisation. For a mandate inside this scope the three timer fields
of the attestation (§4.2) are absent. The proof does not enforce the exclusion; it
only applies the two timer comparisons of §4.2 to what the mandate processor
attests.

### 4.2 What the mandate processor signs, and what stays trusted to it

The mandate processor states one thing per mandate state: a document of the exact
type `Mandate State Attestation` of this package. It signs the BlueId of that
document with the key that is `mandateProcessorKey` of the channel:

    signed bytes = UTF8( "blue.private-mandates.mandate-state-attestation" ) LF UTF8( BlueId of the attestation )
    signature    = Ed25519( signed bytes )

Pure Ed25519 of RFC 8032, LF the byte 0x0A, no byte after the BlueId. The signature
is outside the signed content: the attestation has no signature field. There is no
other serialisation: the canonical form and the hash are the BlueId of the Language.
The public output of a proof carries a salted commitment to what was signed:
SHA-256 over the salt bytes followed by the signed bytes. (*Provisional*: the domain
text, the type name and the field names.)

The proving program is not given the attestation. It builds the document from the
values it uses and has checked, computes its BlueId and verifies the signature. A
value the proof uses can therefore not differ from the signed one, and a document
with any further field has another BlueId and cannot be reproduced.

| Field | Content | What it binds in the proof |
|---|---|---|
| `mandate` | Reference: the initial BlueId of the mandate | Read from the `initialized` marker of S, never from the prover; also the preimage of M |
| `state` | Reference: S, the root document of the mandate processor's snapshot | The state the proof opens and evaluates |
| `documents` | List of references to the further documents of the snapshot (embedded documents), strictly ascending by BlueId text; absent when there is none | Position completeness: the channel timelines of S and of each listed document must be rows of `position` |
| `authorityPackage` | Text: BlueId of the Mandates package the mandate is established under | Must be the Mandates package the profile's program was built with, else "does not admit" |
| `mandateProgram` | Text: identity of the program of the state | Compared with `approvedProgram` |
| `approvedProgram` | Text: identity of the approved program; absent when none is approved | The mandate is approved exactly when it is present and equals `mandateProgram`, else "does not admit" |
| `position` | List of rows, strictly ascending by the BlueId text of the timeline. A row has `timeline` (reference to the Signed Timeline) and, unless no entry of that timeline is included, `lastEntry` (reference to the last included Timeline Entry); no other field and no type | The history position N, checked against provider evidence and E (below) |
| `timerRegistrations` | Text: digest of the pending timer registrations; absent when none is pending | Carried only |
| `lastTimerFiring` | `Coordination/Order Key` of the latest timer firing already applied in S; absent when none | Must precede K, else no proof |
| `nextTimerFiring` | `Coordination/Order Key` of the earliest pending timer firing; absent when none | K must precede it, else no proof: an operation is decided only on a state in which no timer is due before it |
| `certifiedNodes` | `count` (Integer) and `root` (64 characters `0-9a-f`) of the tree of certified rows (below) | A certified row is used only with an audit path to `root` in a tree of `count` leaves |
| `sequence` | Integer: 0 for the first attestation of this mandate by this processor, then the previous one plus one | Carried only (the chain, below) |
| `previous` | Reference: the BlueId of the mandate processor's preceding attestation of the same mandate; absent only in the first | Carried only |

A value that does not exist is an absent field, never an empty list. The content
of the two program identities is not interpreted by the proof (*provisional*: how a
program is identified).

**The field set is closed and is checked by the verifier.** The Language schema of
the type requires the fields marked required in the type and fixes lengths, but
like the other types of this package it does not close the field set. The proof
closes it by construction, as said above. Anyone else who checks an attestation
MUST check that it has exactly these fields and the exact type.

Not in the attestation, on purpose: the provider list (it is the profile's, and the
public output carries its digest); the mandate processor key (the public output
carries it and the processor compares it with the channel's); D, E and the salt (an
attestation is about S alone and serves every operation decided on that state).

**Certified rows.** Beside the state, the mandate processor attests facts about the
validation nodes of the grants. For each grant in the scope of S, for each
validation node V of that grant (its `validation` and its
`target.documentValidation`) for which strict certification succeeds, there is one
row

    key = [["<BlueId of V>"],[]]     goal = certified:value     root flag = true

and it means: strict certification of V succeeds. Every node reachable from V is
present and hashes to its BlueId, every type definition among them is valid, and V
passes its schema. The mandate processor signs exactly rows of this goal; a row of
any other goal is refused by the proof. The rows are distinct and ordered by key as
byte strings, and `certifiedNodes` is the row count and the root of the Merkle tree
over them in the construction of `MERKLE(FULL(D))` (§4.1): the same leaf and node
hashes and the same MTH, with the count and `hex(MTH)` as the two fields instead of
the outer digest. With no row the count is 0 and the root is `hex SHA-256("")`.

A mandate processor MUST include a row only for a node for which it performed this
certification and it succeeded. The proof relies on a row only for a validation
node that it reaches itself from S, through scope, grant and target; a row about any
other node has no effect. Without a row for a node the proof certifies that node
itself. Pattern matching and predicate evaluation are always done in the proof,
from S. This is asserted by the mandate processor, not proved.

**Position completeness.** The proof shows that `position` covers every timeline S
depends on through a channel. For S and for every document of `documents`, every
contract of that document whose type is, by ancestry, a Coordination
`Timeline Channel` or `Public Timeline Channel` names a timeline, and each such
timeline must be a row of `position`. The position has at least one row. For every
row the proof shows, by exactly one kind of evidence, that the row's last entry is
on that timeline, is before K, and is the last entry of that timeline before K: by
a provider guarantee whose last entry is the row's and which is complete to after
the timestamp of K, or by the provider-signed successor entry after K, or, on E's
own timeline and only there, by E itself whose previous entry is the row's. The
provider of every row's timeline, that of E's own timeline included, must have its
key in `allowedProviders`. If a timeline is not covered, or a provider is not in the
list, no proof is made.

**The chain.** `sequence` and `previous` link the attestations of one mandate by one
mandate processor into a hash chain. There is no timeline of the mandate processor.
The proof checks nothing about the chain beyond that both fields are inside the
signed document: it needs one attestation, does not follow the chain, and does not
check that `previous` is absent exactly when `sequence` is 0. The chain is for
audit. Two different attestations signed by one key for one `mandate` with the same
`previous`, or with the same `sequence`, prove equivocation by the mandate
processor, from the two signatures alone and without the mandate's content. A chain
with every link present shows the states the mandate processor claims, in order. A
missing link is the mandate processor's to explain; the chain does not prove that
every attestation was published.

**What stays trusted to the mandate processor.** The proof does not replay the
mandate's history. Not shown by the proof, and asserted by the signature alone:

- that S is the state that results from processing exactly the entries up to the
  last entry of each row, and each row's last entry itself;
- `documents`: the channel timelines of a listed document are required, but nothing
  shows the list complete;
- dependencies that are not a channel contract of S or of a listed document:
  documents S refers to without embedding them, sources reached through another
  channel type, and anything a contract reads when it runs;
- the three timer fields;
- `authorityPackage`, the two program identities and the certified rows.

## 5. When a proof matches

The public output of a proof is a closed list: the BlueId of D, the BlueId of E, M,
the mandate processor key, the provider set digest, a salted commitment to the
bytes the mandate processor signed (§4.2), the digest of the validation facts about D
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
| 7 | The validation-facts digest in the public output | The digest of the empty set or of FULL(D) computed by the processor from D, each under the `factsRule` of the profile (§4.1) |

- A proof that verifies but fails any comparison is skipped as mismatching. It is
  never counted as a denial.
- A receipt that cannot be decoded or does not verify is skipped (§5.1). It is never
  retried.
- The values a processor compares with MUST come from its own accepted state before
  K, the authenticated operation and the authenticated history of T.
- One profile means one classification of one entry on every host.

A matching proof carries its verdict. With an admitting verdict the processor
applies the target document's own rules to E; with a denying verdict it rejects E
and the document continues. A denying verdict includes the cases of §3 in which
the mandate or a predicate is at fault.

### 5.1 Result classes of the receiver

The part of a host that checks one receipt under this profile (the receiver) ends in
exactly one of four classes:

| Class | Meaning | When |
|---|---|---|
| MATCH, admitting | A matching proof whose verdict admits | All comparisons hold |
| MATCH, denying | A matching proof whose verdict denies | All comparisons hold |
| SKIP | The entry is skipped; never a denial | The bytes are not the canonical encoding of a succinct receipt; the receipt is of another program; it does not verify, or decoding or verifying it failed or faulted; the public output is not the closed output of the program; any of comparisons 2 to 7 differs |
| RETRY | No result; nothing is finalised | The receiver could not do its work for a reason of its own |

RETRY only ever reflects the receiver's own environment or a bug of the processor
that called it: a file it cannot read, own records of D that are missing or altered
so that FULL(D) cannot be computed, an own value that is malformed, a profile that
is malformed (a processor must reject from the document state before it reads T and
must never ask for such a check), a fault of the receiver outside decoding and
verification, or a receiver that was stopped from outside. RETRY never has its cause
in the bytes of the receipt, in the proof or in the content of a document: with
correct own data no receipt, whatever its bytes, gives RETRY. A processor that gets
RETRY does not pass over the entry (Coordination section 14.6).

Whether a byte string is SKIP or MATCH depends on the code of the receiver, not only
on the profile's data: the canonical-encoding rule of §4.1 is such code. All
processors of a document MUST therefore run the same pinned receiver build for a
profile.

## 6. Compatibility

Documents that use `Mandates/Mandate Authority` keep their rules, and every earlier
publication is unchanged and remains selectable. This package and its protocol are
unused unless a document declares a channel with a profile of this package or an operation carries a
`Mandate Commitment Authority`. On a channel without the three evidence fields an
operation with this claim is rejected from the document state.

## 7. Not decided in this preview

- The names listed as provisional, and the text encodings of M, of the image
  identifier and of the digests.
- How a program is identified in `mandateProgram` and `approvedProgram`; the domain
  text of the signature; whether position rows are typed.
- Whether the proof checks that `previous` is absent exactly when `sequence` is 0.
- Whether the timer fields stay, or the proof refuses every mandate with timers.
- Binding each row's last entry to the mandate's own checkpoint, which would remove
  one item from what stays trusted to the mandate processor.
- Mandates with timers; a second prover; the duty to reject an operation whose M
  matches no mandate.
- How the one receiver build that §5.1 requires is named, pinned and distributed.
