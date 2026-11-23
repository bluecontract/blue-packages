# Private mandates: operations decided by a proof instead of a readable mandate

Protocol name: `Private Mandates / proof-decided operation authority/1`
Package namespace: `PrivateMandates`
Release status: Core Java integration preview, 23 November 2026

This package extends Mandates and the timeline channels with evidence of the
Coordination Evidence package (`blue-coordination-evidence`; "the Coordination
Evidence specification" below). It requires that exact package, the exact
Coordination publication that package requires and the Mandates publication built
on that Coordination publication. It changes no type of any of them and defines no
transport type. It is additive: `Mandates/Mandate Authority`, which names its mandate in
clear, stays supported and keeps its rules. The type names, the field names and the
encodings of this text are fixed; changing one produces new exact identities. What
is not decided is listed in §7.

Terms: E is an operation entry of the agent and K its full Coordination input key.
D is the state of the target document strictly before E. M is the salted mandate
commitment carried by E. T is the evidence timeline named by the channel E is
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
are those of the Coordination Evidence specification. This specification
defines the authority claim, the evidence profile, and when a proof matches.

A processor MUST explicitly support this exact package and protocol, the required
Coordination Evidence protocol and the required Mandates protocol. A host that does
not support the profile type a channel declares MUST refuse the document where the
channel is declared. Installing this data package grants no native support.

**What this version supports.**

1. *Mandate types.* This version supports mandates of type
   `Mandates/Operation Mandate` and of its subtypes, recognised by ancestry: the
   type chain of the mandate state contains `Operation Mandate` of the required
   Mandates publication. A mandate composed from clauses
   (`MandateClauses/Mandate with Clauses`) is such a subtype and is supported. A
   state of any other type is a fault of the mandate (§3).
2. *One edition for both documents.* The mandate and the target document are on
   the same edition: the Coordination publication, the Coordination Evidence
   package and the Mandates publication this package requires. A mandate established under another Mandates package is a
   fault of the mandate (§3). A proof for a mandate of another edition is not
   defined in this version.
3. *One edition, one proving program, one profile.* One edition has exactly one
   proving program and one profile type. The program is built with the exact
   identities of that edition, and its image identifier is the `programImageId` of
   the profile (§4.1). Every type identity of this package,
   `Mandate Commitment Authority` included, therefore changes with each
   Coordination or Mandates edition, and the profile type also with each edition
   of the Coordination Evidence package. A document pins its proving program for its
   whole life through the profile of its channel: `evidenceProfile` is fixed for
   the life of the document (Coordination Evidence section 3).
4. *A channel without evidence.* An operation whose authority claim is a
   `Mandate Commitment Authority` and which is performed on a channel without
   evidence (a plain `Timeline Channel`, or a channel that lacks any of the three
   well-formed evidence fields) is rejected from the document state, without
   reading any evidence timeline, and the document continues with the next input.

## 2. Exported types

| Type | Kind | Purpose |
|---|---|---|
| Mandate Commitment Authority | `Mandates/Authority` | Authority claim that carries M and names no mandate |
| Mandate State Attestation | document signed by the mandate processor | What the mandate processor states about one state of a mandate (§4.2) |
| RISC Zero Succinct Receipt Profile | `CoordinationEvidence/Evidence Profile` | First profile: a succinct RISC Zero receipt of one pinned proving program |

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
| `mandateCommitment` | M, the salted mandate commitment, as 64 lower-case hexadecimal characters (below) |

**The commitment, byte for byte.**

    M = hex( SHA-256( salt || id ) )

`salt` is the salt as raw bytes, at least 16 of them; with a shorter salt no proof
can be made. `id` is the BlueId of the mandate before initialization, written as
the text of that BlueId in ASCII: its base58 characters and, when the mandate is a
member of a cyclic set (§4.2), the character `#` and the index that follow them. The hash input is the
salt bytes followed directly by those characters: no separator, no length prefix
and no terminator. `hex` writes the 32 bytes of the hash as 64 characters `0-9a-f`.
The claim and the public output of a proof (§5) carry M as this same text and it
is compared as text.

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
T. The agent announces nothing before writing and takes no part in the proof flow.
M tells the prover which mandate is meant and lets a processor match a proof to
the operation.

An operation whose authority claim is a `Mandate Commitment Authority` is
evidence-decided in the sense of the Coordination Evidence specification. The
claim is recognised by its exact type: the type of the claim must be exactly
`Mandate Commitment Authority` of this package. A claim of a subtype, of a parent
type or with no type is not evidence-decided, and no proof can be made for it.

**Checked by every processor, outside the proof.** These are the checks a processor
performs today for a `Mandates/Mandate Authority` without reading the mandate. They
are unchanged, they come before T is read, and a failure has the same outcome as it
has today for `Mandate Authority`:

1. the claim's `actor` is the actor of the target channel the operation selects;
2. that target channel exists and is a concrete `Coordination/Timeline Channel`
   (which includes `CoordinationEvidence/Timeline Channel with Evidence`);
3. the target document contains a Timeline Channel with the actor and timeline of E
   (the delegate participant);
4. the target document's actor policy admits E as a delegated action.

Ordinary operation validation and protection against executing E twice also remain
with the processor. Every check that today needs the mandate is in the proof.

A rejection under one of these four checks, for a claim that is malformed, or for
a channel without usable evidence fields is decided from the document state without
consulting T. It carries neither `AUTHORITY_EVIDENCE_DENIED` nor
`AUTHORITY_EVIDENCE_REJECTED`; those two reasons belong to an operation that T
decided (Coordination Evidence section 6).

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
3. *A fault of the mandate.* The signed state is not, by ancestry, an Operation
   Mandate (§1); it belongs to another Mandates package than the profile's program
   was built with; it has no approved program, or its approved program is not the
   program of the state; it lacks its participants or its scope; or a grant of its
   scope has no target. The verdict is "the mandate does not admit E", whatever the
   other grants are.

In every such case the proof carries a denying verdict or, in case 1, the verdict
the other grants give. E is decided at its own time and the target document
continues with the next input. Repairing the mandate needs an update of the mandate,
which applies to later operations.

**A validation node that is not well formed.** A validation node of the mandate
that is not well formed under the Language fails strict certification: it violates
its schema, its types are not compatible, a type it uses is on its own inheritance
chain (a type inheritance cycle, which the Language rejects: LANG-TYPE-CYCLE), or
its content is invalid in another way the Language defines. When the mandate
processor signed no certified row for such a node (§4.2), no proof can be made for
E: the proof would have to certify the node itself and cannot. This refusal is
final. It does not depend on the prover's resources or on content it might still
obtain, and the represented party's side ends the wait with a Rejection Entry
(Coordination Evidence section 5). An honest mandate processor does not approve a
mandate with such a node. When the mandate processor did sign a row for such a
node, it is at fault, and the outcome is whatever the evaluation of that grant
gives under the rules above. A cyclic identity of the Language (its section 12) is
not a type inheritance cycle and is no fault: a node that is, or reaches, a member
of a cyclic set is well formed.

**A grant that cannot be evaluated.** A grant that applies to E and whose evaluation
needs content that cannot be supplied to the proving program is different: it is
not a fault the statement can establish, because the statement cannot tell content
that does not exist from content that is withheld. No proof can then be made for E,
whatever the order of the grants and also when another grant would admit. So
withholding content can never choose a verdict: for one S, D and E at most one
verdict is provable. The party ends the wait with a Rejection Entry (Coordination
Evidence section 5); repairing needs an update of the mandate.

This is a deliberate difference from mandates named in clear. For a
`Mandates/Mandate Authority` the Mandates specification says only that an error
never authorizes, and a processor that evaluates the predicate or reads the mandate
itself may give no verdict and stop processing the target document. Here the
represented party answers for its own mandate: the other participants cannot read
it, so a faulty mandate must not stop the document for everyone. A local
interruption of proving is not a fault of the mandate: it gives no proof, never a
verdict.

**Resources.** The Language sets no ceiling on the size, depth or count of valid
content (LANG-LIMIT), and these rules set none either: no rule here makes a
document, a mandate, an operation or a proof invalid because of its size or the
work it needs. The work of proving is the represented party's. Its side MAY write
a Rejection Entry for an operation whose proof would exceed its own proving budget.
The other participants need not know that budget; for them the entry is a
considered rejection like any other. A budget never produces a verdict, and a
processor never classifies a proof by the work that making or verifying it took.

## 4. Evidence profiles

A profile is one immutable value. Its exact type identifies the part a host must
implement natively; its content carries the data. Processors compare proofs
deterministically only when they use the same profile, so a channel declares a
profile value and never a name such as "latest". The profile is identified by a
hash of its content: the BlueId of the declared value.

`CoordinationEvidence/Evidence Profile` is the base type and has no fields. A
channel's `evidenceProfile` MUST be a value of a supported specialisation.

The Language schema of the channel does not enforce this. Typing of the
`evidenceProfile` field is structural: the schema admits a value with no type and
values of unrelated types. What protects is the native rule of Coordination
Evidence section 3, which a processor MUST implement: the exact type of the value
must be a supported specialisation of `CoordinationEvidence/Evidence Profile`;
anything else counts
as a missing field, and every operation with a `Mandate Commitment Authority` on
that channel is rejected from the document state.

### 4.1 RISC Zero Succinct Receipt Profile

| Field | Content |
|---|---|
| `programImageId` | Image identifier of the proving program, 64 lower-case hexadecimal characters. It fixes the proved statement, the format of the public output, and the runtime and package bindings, gas limit and error semantics the program was built with |
| `allowedProviders` | The profile's allowed timeline provider set: a list of `Coordination/Ed25519 Public Key`, each a well-formed key, strictly ascending when compared as 32-byte values |
| `receiverReleaseSha256` | SHA-256 of the manifest of the receiver release whose builds perform the pinned verification of §5.1 for this profile, 64 lower-case hexadecimal characters |

The value has exactly these three fields. `programImageId` and
`receiverReleaseSha256` are data supplied by the document that declares the
profile; this specification names no image identifier and no release.

The type itself fixes what is not data: the receipt kind (a succinct RISC Zero
receipt, in one canonical encoding with no other bytes), the comparison rules of §5
and the provider set digest function. The code that decodes and verifies a receipt
is fixed by `receiverReleaseSha256`.

**The receiver release is part of the profile.** A receiver release is a set of
builds of the pinned verification, one per platform. All builds of one release are
made from the same sources and the same verifier version, and MUST return the same
result for the same input (§5.1). A release is described by its manifest, and
`receiverReleaseSha256` is the SHA-256 of the bytes of that manifest.

The manifest is UTF-8 text with one line per build of the release and no other
byte:

    <SHA-256 of the bytes of the build, 64 characters 0-9a-f> SP SP <platform name> LF

SP is the byte 0x20 and LF the byte 0x0A; the two spaces are exactly two. The
platform name is the Rust target triple the build is made for, for example
`aarch64-apple-darwin` or `x86_64-unknown-linux-gnu`. The lines are sorted by
platform name, compared as byte strings, and a platform name occurs once. The last
line ends with LF like every other. This is the text format of `sha256sum`. A
manifest lists the builds of one release only.

Example of a manifest with two builds (the hashes stand in for real ones):

    1111111111111111111111111111111111111111111111111111111111111111  aarch64-apple-darwin
    2222222222222222222222222222222222222222222222222222222222222222  x86_64-unknown-linux-gnu

A processor installs the manifest and one build that the manifest lists. Where the
channel is declared it checks both of these:

1. the SHA-256 of the bytes of its manifest equals `receiverReleaseSha256`;
2. the SHA-256 of the bytes of its installed build is the hash on a line of that
   manifest.

A processor for which either fails, or that has no manifest or no build, does not
implement the declared profile and MUST refuse the document where the channel is
declared, exactly as a host refuses a profile type it does not implement
(Coordination Evidence section 1). It MUST NOT verify a receipt for that channel
with a build that the manifest does not list.

**The receipt.** `receipt` of a Proof Entry decodes to exactly one canonical
encoding of a succinct receipt. A byte string that is not that encoding is skipped,
also when a verifier would accept it: trailing or altered bytes, another receipt
kind, and a receipt whose `control_inclusion_proof.index` has a bit set above the
length of its path. The verifier reads one bit of that index per digest of the path
and ignores the bits above, three bytes in the receipts of the first program, so
such a receipt verifies like the original; it is skipped all the same. Any failure
or fault while a receipt is decoded or verified, a panic of the verifier included,
makes the bytes not a proof: the entry is skipped and never retried (§5.1).

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
length of each key, of `programImageId` and of `receiverReleaseSha256`, and distinct
list elements. As for the authority claim (§3) it admits a further field that
carries only a type. The processor additionally requires that the fields are
exactly these three, that `programImageId` and `receiverReleaseSha256` are 64
characters `0-9a-f`, that every key of `allowedProviders` is a well-formed key as
Coordination Evidence section 3 defines (64 characters `0-9a-f`; a point of
edwards25519; canonical encoding; not of small order), and that the list is
strictly ascending by key bytes. Every listed key must be well formed, whether or
not any proof uses it. A
profile that fails any of these is malformed; under the Coordination Evidence
specification the channel then lacks its profile, and every operation with
a `Mandate Commitment Authority` on it is rejected from the document state.

**Two premises.** A proof states its verdict under two premises. Neither the
proving program nor the pinned verification checks them:

1. *D is valid.* The target state D, the record whose BlueId is `targetState` of
   the public output, passes Language strict certification with goal `definition`
   (LANG-CERTIFY): the exact graph reachable from D is present and addressed
   correctly, every type that is not a core type and every specification reached
   from D is a valid definition, and D itself is.
2. *E is a valid entry.* The record whose BlueId is `entry` of the public output is
   a valid `Coordination/Timeline Entry` on its timeline, written by its actor. The
   verdict is for the operation that this record describes. The program opens the
   record by its BlueId and reads the fields the statement uses. It does not
   validate E, does not check that E is a Timeline Entry and verifies no signature
   over E.

> A proof is meaningful only for a target state that the receiving processor has
> itself produced or admitted under an edition that certifies every document state
> completely, and for an operation entry that the same processor has itself
> admitted as an entry of its timeline. A processor MUST NOT accept a proof for any
> other state or any other entry.

A conforming processor satisfies this by comparisons 2 and 4 of §5 and by nothing
else: it compares `entry` with the BlueId of the operation it is deciding, which it
admitted itself, and `targetState` with the BlueId of its own state D before E. A
host MUST NOT apply this profile to a document it processes under an edition that
does not certify every state completely. An edition that certifies every state
with goal `value` satisfies premise 1, because certification with goal `value`
first establishes the definition. The premise names `definition` because that is
all the derivation below relies on.

A proof states its verdict relative to the premises: someone who holds only a
proof and the two BlueIds learns the verdict for the case that D is valid and E is
such an entry, and nothing about whether they are.

**Reused validation results about D.** The program may validate every node of D it
reads itself. It may instead be given validation results about D, to save work. A
validation result is a row (recipe key, goal, root flag). The recipe key is the
JSON text `[[part BlueIds],[required type BlueIds]]` and names the node obtained
by merging the parts under the listed type requirements. The goal is `definition`
or `value`. The row means: Language validation of that node for that goal, at a
root position (flag true) or a nested position (flag false), succeeds for the node
and for everything below it.

The program accepts such a row only if it re-derives the row itself from the
target state, starting from the one assumed row "the target state is valid"
(premise 1: strict certification of D with goal `definition`). A row
the program cannot re-derive is refused and no proof is made. A derivation is a
start row followed by any number of steps:

- *Start row.* Either (`[[D],[]]`, `definition`, true), where D is the BlueId the
  public output carries as the target state; or (`[[X],[]]`, `definition`, true),
  where X is reached from D by hops through the exact content, each hop read from
  the record bound by the BlueId of the current node. A hop goes to the node under
  one key of the current node's content, any key except `name`, `description`,
  `value`, `mergePolicy` and `items`, or to one item of its `items`. The last hop
  must go through a type key (`type`, `itemType`, `keyType`, `valueType`) to a type
  that is not a core type of the Language, or through `specification`; X is the
  BlueId found there.
- *Steps.* Each step starts from the head h of the current row, which is the node
  Language validation builds for the row's recipe, and gives the next row:

| Step | Condition | Next row |
|---|---|---|
| Field k | h has the field k | (the recipe of that field under h, the same goal, false) |
| Contracts | h has `contracts` | (the recipe of h's `contracts`, the same goal, false) |
| Item n | h has the item n; under goal `definition` the item is not a hole | (the recipe of that item under h, the same goal, true) |
| Key k | h has the field k, and h is a Dictionary or declares a key type | (`[[S],[T]]`, `value`, true): T is the key type of h, the core type Text when h declares none, and S is the BlueId of the scalar of T's core domain (Text, Integer, Double or Boolean) whose value is k read in that domain, exactly as the Language reads a dictionary key of that key type. A k that the Language does not accept as a key of that domain gives no row |

- A row with goal `value` whose head is neither at a root position nor concrete
  has no rows below it.

These are the start rows and the step of Language validation itself: strict
admission of D with goal `definition` succeeds only if validation succeeds on
every row reached this way. Every row that can be derived is therefore true
whenever D is valid, and the premise above is the only thing assumed. A derivation
reads the records bound by BlueId from the target state and the heads and child
recipes computed from them. It reads nothing of the mandate or of E and no
validation result supplied by anyone. A row whose key is built from the mandate,
from E or from a node merged with a mandate pattern cannot be derived, and is
refused whatever its form.

The prover gives no digest of these rows and the public output carries none (§5).
Validation results about the mandate are a separate input: the certified rows the
mandate processor signs (§4.2). They are not derived and are unchanged by this
rule.

The rule is fixed as stated. The encoding in which a prover hands a derivation to
the program is private input and is fixed by the program. Two things about it are
not established and are listed in §7: that every derivable row follows from the
validity of D is argued from the validation algorithm and is not proved, and that
the processor's validation and the program's validation accept the same nodes is
shown by differential runs only.

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

Pure Ed25519 of RFC 8032, LF the byte 0x0A, no byte after the BlueId. The BlueId is
written as its text in ASCII. The signature is outside the signed content: the
attestation has no signature field. There is no other serialisation: the canonical
form and the hash are the BlueId of the Language.

The public output of a proof carries a salted commitment to what was signed:

    statementCommitment = hex( SHA-256( salt || signed bytes ) )

with the same salt bytes as in M (§3), followed directly by the signed bytes above,
with no separator; `hex` as in §3.

**Which signatures the statement accepts.** The key must be a well-formed key
(Coordination Evidence section 3). A signature is 64 bytes, R followed by S, over
the message M' (the signed bytes), under the key A. The statement accepts it only
if all hold:

1. S, read as a little-endian integer, is below the group order L;
2. R decodes to a point of edwards25519 and is not of small order;
3. the encoding of [S]B − [k]A is equal, byte for byte, to the 32 bytes of R, where
   B is the base point and k = SHA-512(R ‖ A ‖ M') read as a little-endian integer
   and reduced modulo L.

This is the equation without the cofactor, compared on encodings. A signature made
by a signer that follows RFC 8032 always passes. The statement applies the same
rule to every provider signature it verifies (position completeness, below). With
a signature that fails, no proof can be made.

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
of the two program identities is not interpreted by the proof (how a program is
identified is not decided, §7). No proof can be made from values the document cannot
hold: a `mandateProgram` or an `approvedProgram` that is an empty text, an
`authorityPackage` that is not the text of a BlueId, or a `documents` list that
names S itself.

**Plain ids and member ids.** A final BlueId has one of two forms: a plain id (the
base58 text of 32 bytes, 32 to 44 characters), or the id of a member of a cyclic
set, which is a plain id, the character `#` and the canonical index of the member
(Language section 12). Where a document can stand, either form is allowed:

| Position | Forms |
|---|---|
| `targetState` and `entry` of the public output (§5) | Either. The public output carries the id as its text, with `#` and the index when it has them |
| `mandate` and `state` of the attestation; the references of `documents` | Either |
| `timeline` and `lastEntry` of a position row; the timelines and entries inside `lastTimerFiring` and `nextTimerFiring`; `previous`; `authorityPackage` | Plain only. With another form in one of these no proof can be made |

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
byte strings; a key contains no tab and no line feed. `certifiedNodes` is the row
count and the root of the Merkle tree over the rows in that order. Below `TAB` is
the byte 0x09, `flag` the character `1` (the root flag of a certified row is
true), and `hex` lower-case hexadecimal:

    leaf(row)   = SHA-256( 0x00 || key || TAB || goal || TAB || flag )
    node(l, r)  = SHA-256( 0x01 || l || r )
    MTH({})     = SHA-256( "" )
    MTH({d})    = leaf(d)
    MTH(d[0:n]) = node( MTH(d[0:k]), MTH(d[k:n]) ),  k the largest power of two smaller than n
    count       = n          root = hex( MTH(d[0:n]) )

This is the Merkle Tree Hash of RFC 9162 section 2.1 with the leaf content above.
With no row the count is 0 and the root is `hex SHA-256("")`. A proof is given only
the rows it uses. Each comes with its index and its audit path, and the program
uses a row only when the path gives `root` for that index in a tree of `count`
leaves (RFC 9162 section 2.1.3.2); otherwise no proof is made.

Worked example with the three rows whose keys are `[["A"],[]]`, `[["B"],[]]` and
`[["C"],[]]` (`A`, `B`, `C` stand in for BlueIds), each with goal
`certified:value`:

    leaf 0 = e4b0a83e3f8f90f9e7f277bc81bcfd9162996ea3f8464f5bb66f56c798d0ffa2
    leaf 1 = edd172232e33ad3931647a39b4ff3a8e11bc3fae24de8a4788733099a62b3935
    leaf 2 = e742b75585d6b048b806948423a2878e04765af3014ee7070d961c3d5b5a9b8a
    node(leaf 0, leaf 1) = fecc5a5ee3e078f4da2c2f4a69eb98203e02da3836e50d15634c84ecdc48a9cc
    count  = 3
    root   = 4945afc7018775e7694c57bea07d2dc8e92790e6447c59fb45f0e34e5d26d219

The audit path of leaf 2 is [node(leaf 0, leaf 1)]; that of leaf 0 is [leaf 1, leaf 2].

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

The public output of a proof is closed: one JSON object with exactly these seven
keys, in this order, as UTF-8 text with no white space and no other byte.

| Key | Content |
|---|---|
| `targetState` | The BlueId of D, plain or a member id (§4.2) |
| `entry` | The BlueId of E, plain or a member id (§4.2) |
| `mandateCommitment` | M, as in the authority claim (§3) |
| `mandateProcessorKey` | The key whose signature on the attestation the proof verified, 64 lower-case hexadecimal characters |
| `providerSetDigest` | The provider set digest (§4.1) |
| `statementCommitment` | The salted commitment to the bytes the mandate processor signed (§4.2), 64 lower-case hexadecimal characters |
| `verdict` | The Boolean true when the mandate admits E, false when it does not |

The public output carries nothing about the validation of D: no digest of
validation results and no statement that D is valid (§4.1).

The public output carries nothing about E beyond its BlueId either (premise 2 of
§4.1).

**Deciding one Proof Entry has two parts.**

(a) *Pinned verification.* A build of the receiver release that
`receiverReleaseSha256` of the profile names (§4.1) is given two things: the bytes of the receipt and the `programImageId` of
the channel's profile. It answers with exactly one of three results (§5.1): the
receipt is verified, together with its public output; the bytes are not a proof;
or it did not finish. It is given nothing else and reads nothing else: no record
of D, of E or of the mandate, and none of the processor's values.

(b) *The processor's comparisons.* The processor compares the public output that
(a) returned with its own values, as the table below lists. These five comparisons
are defined by this text alone. They are not part of the pinned build, and every
implementation writes them itself. They compute nothing from the content of a
document: of D and of E they need only the BlueIds.

A well-formed `CoordinationEvidence/Proof Entry` (Coordination Evidence section 5;
the processor, not the schema, decides well-formedness) is a matching proof for E
only if (a) returns "verified" and all comparisons of (b) hold. The entry's
`document` and `operationEntry`, when present, are an advisory hint with no force
(Coordination Evidence section 5). They are not among the comparisons, neither
part reads them, and a proof is never skipped or classified differently because of
what they hold or because they are absent: each Proof Entry is classified by its
public output alone.

| # | Comparison | Against |
|---|---|---|
| 1 | Part (a): the receipt is the canonical encoding of the profile's kind and verifies for `programImageId` | The channel's profile; decided by the pinned build |
| 2 | `entry` of the public output | The BlueId of the operation the processor is deciding (premise 2 of §4.1) |
| 3 | `mandateCommitment` of the public output | `mandateCommitment` of E's authority claim |
| 4 | `targetState` of the public output | The BlueId of the processor's own state D before E (premise 1 of §4.1) |
| 5 | `mandateProcessorKey` of the public output | `mandateProcessorKey` of the channel |
| 6 | `providerSetDigest` of the public output | The digest derived from `allowedProviders` of the profile (§4.1) |

- Comparisons 2 to 6 are part (b). The texts are compared as texts.
- A proof that verifies but fails any comparison is skipped as mismatching. It is
  never counted as a denial.
- Bytes that are not a proof are skipped (§5.1). They are never retried.
- The values a processor compares with MUST come from its own accepted state before
  K, the authenticated operation and the authenticated history of T.

A matching proof carries its verdict. With an admitting verdict the processor
applies the target document's own rules to E; with a denying verdict it rejects E
and the document continues, with the reason `AUTHORITY_EVIDENCE_DENIED`
(Coordination Evidence section 6). A denying verdict includes the cases of §3 in
which the mandate or a predicate is at fault.

**The statement commitment is recorded.** A processor records the
`statementCommitment` of the deciding proof together with its decision, admitting
or denying. It compares the value with nothing. It is kept for audit: whoever
holds the salt and an attestation can check that the deciding proof used that
attestation. A processor is not required to detect a later proof for the same E
that carries another value, and such a proof changes nothing: later entries for
the same E are ignored (Coordination Evidence section 6).

### 5.1 The pinned verification and its results

The pinned verification (part (a) of §5) ends in exactly one of three results:

| Result | Meaning | When |
|---|---|---|
| VERIFIED, with the public output | The bytes are a proof of the profile's program | The bytes are the one canonical encoding of a succinct receipt (§4.1), the receipt verifies for `programImageId`, and its public output is the closed output of §5 |
| NOT A PROOF | The bytes are no such proof | Anything else that the bytes themselves decide: not the canonical encoding; a receipt of another program; a receipt that does not verify; decoding or verifying failed or faulted, a panic of the verifier included; a public output that is not the closed output |
| UNFINISHED | No result | The build could not do its work for a reason of its own |

The processor turns the result into the treatment of the entry:

| Pinned verification | Comparisons 2 to 6 | The entry |
|---|---|---|
| VERIFIED | All hold | A matching proof; it carries the verdict of its public output, admitting or denying |
| VERIFIED | Any differs | Skipped as mismatching; never a denial |
| NOT A PROOF | Not made | Skipped; never a denial and never retried |
| UNFINISHED | Not made | Nothing is finalised. The processor retries and does not pass over the entry (Coordination Evidence section 6) |

UNFINISHED only ever reflects the environment of the build or a bug of the
processor that called it: a file it cannot read, a malformed `programImageId` (a
processor must reject from the document state before it reads T and must never ask
for such a check), a fault outside decoding and verification, or a build that was
stopped from outside. It never has its cause in the bytes of the receipt, in the
proof or in the content of a document: for the builds of one release, the same
receipt bytes and the same image identifier never give UNFINISHED on one host and
a result on another because of what the bytes are.

**What must be the same on every host.** Whether a byte string is VERIFIED or NOT A
PROOF depends on code and not only on the profile's data: the canonical-encoding
rule of §4.1 is such code, and so is the verifier. All processors of a document
MUST therefore use a build of the same pinned release for part (a), the release
whose manifest hash the profile carries (§4.1). The builds of one release differ
only in the platform they run on and give the same result for the same input.
Part (b) needs no pinned build: it is five comparisons of
texts that this specification defines completely. One profile then means one
classification of one entry on every host.

## 6. Compatibility

Documents that use `Mandates/Mandate Authority` keep their rules, and every earlier
publication is unchanged and remains selectable. This package and its protocol are
unused unless a document declares a channel with a profile of this package or an operation carries a
`Mandate Commitment Authority`. On a channel without the three evidence fields an
operation with this claim is rejected from the document state and the document
continues (§1).

## 7. Not decided in this preview

- The derivation rule for reused validation results about D (§4.1) is fixed, but
  its soundness is argued and not proved, and agreement between the processor's
  validation and the program's validation is shown by differential runs only.
- Whether the premise about D (§4.1) needs a statement for a host that admits a
  state from earlier admissions instead of certifying it afresh.
- The image identifier and the receiver release of a program built for this text.
  A profile's `programImageId` and `receiverReleaseSha256` are supplied by the
  document.
- How a receiver release and its manifest are distributed to hosts, and how it is
  shown that the builds of one release come from the same sources and give the
  same result (a reproducible build procedure). The rules require the property
  and do not say how it is established.
- How a program is identified in `mandateProgram` and `approvedProgram`. The two
  fields are texts that the proof only compares. The Mandates specification
  defines no program node with a content BlueId that this text could name, so the
  identity is not defined here as a BlueId.
- Whether position rows are typed.
- Whether the proof checks the key shape of a certified row.
- The audit procedure that uses the chain of attestations: what the delegating
  party keeps, for how long, and how an auditor obtains it.
- A proof for a mandate on another edition than the target document (§1).
- Whether the proof checks that `previous` is absent exactly when `sequence` is 0.
- Whether the timer fields stay, or the proof refuses every mandate with timers.
- Binding each row's last entry to the mandate's own checkpoint, which would remove
  one item from what stays trusted to the mandate processor.
- Mandates with timers; a second prover; the duty to reject an operation whose M
  matches no mandate.
- The byte-exact grammar of the receipt encoding beyond the rule of §4.1.
