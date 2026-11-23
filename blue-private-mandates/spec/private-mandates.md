# Private mandates: operations decided by a signed statement instead of a readable mandate

Protocol name: `Private Mandates / statement-decided operation authority/1`
Package namespace: `PrivateMandates`
Release status: Core Java integration preview, 26 November 2026

This package extends Mandates and the timeline channels with evidence of the
Coordination Evidence package (`blue-coordination-evidence`; "the Coordination
Evidence specification" below). It requires that exact package, the exact
Coordination publication that package requires and the Mandates publication built
on that Coordination publication. It changes no type of any of them and defines no
transport type. It is additive: `Mandates/Mandate Authority`, which names its
mandate in clear, stays supported and keeps its rules. The type names, the field
names and the encodings of this text are fixed; changing one produces new exact
identities. What is not decided is listed in §11.

Terms. E is an operation entry of the agent and K its full Coordination input key.
D is the state of the target document strictly before E. M is the salted mandate
commitment carried by E. T is the evidence timeline named by the channel E is
performed on (`CoordinationEvidence/Timeline Channel with Evidence`). S is a
mandate state that an attestation names. The *mandate processor* is the processor
that processes the mandate and signs attestations. The *signer* is the document
processor of the represented party that signs statements.

Conventions. A *hex* value is written with the characters `0-9a-f` only, two
characters per byte, the first byte first. A *plain id* is the text of a BlueId
that has no `#` (LANG-ID-ENCODING). A text is a plain id exactly when all of these
hold: it has 32 to 44 characters; every character is in the alphabet
`123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz`; read as a base-58
number with that alphabet, most significant digit first, and with one zero byte for
each leading `1`, it gives exactly 32 bytes; and writing those 32 bytes back the
same way gives the same text. `||` joins byte strings with nothing between them. LF
is the byte 0x0A. All texts named here are ASCII and are compared byte for byte.

**Final ids.** A *final id* is the text under which the Language identifies a node
as final content. It has one of two forms (LANG-ID-ENCODING, Language section 12):

- a plain id; or
- a *member id*, the id of a member of a finalized cyclic set: the plain id of
  the set's master, the character `#`, and the member's canonical index. The index
  is written in decimal with the digits `0-9`, with no sign and no other
  character; it is `0` or begins with a digit `1-9`, so it has no leading zero.
  This text admits an index of at most 9 digits. The Language sets no bound on
  the index; the bound is set here so that every text of §6 has a maximum
  length, and a cyclic set never comes near it, since its proof carries every
  member.

So a final id is 32 to 44 characters when plain, and 34 to 54 characters as a
member id. A text with two `#`, with nothing after `#`, with `#01`, `#-1` or
`#+1`, or with a part before `#` that is not a plain id, is not a final id.

**Which id names a node.** A node is named by the final id under which it was
established as final content, and by no other text:

- if the node was established as a member of a finalized cyclic set, its id is its
  member id `MASTER#index`;
- otherwise its id is its plain id.

The ordinary BlueId that hashing a member's detached body would give is never used
to name the member: the Language does not put that identity in the place of the
member id (its section 12.4). A member and its set's master are different
identities, and ids are compared as texts, so `MASTER#0` and `MASTER` never match.

A party knows which case it is in from how it holds the node. It holds a member
under its member id, together with the owning-set proof that the Language requires
to open it, and every reference to it in other content is written with the member
id. It holds any other node under its plain id. For the four nodes this text
compares or hashes by id:

| Node | The id used is |
|---|---|
| E, the operation entry | The id under which the authenticated chain of E's timeline names that entry |
| D, the target state before E | The id under which the processor's own processing names the state it accepted before E |
| The mandate before initialization | The id the mandate state S records as its initial identity |
| S, the attested mandate state | The id under which the mandate processor's snapshot names its root document |

The Language does not say whether a processed document state or a timeline entry
can be a member of a cyclic set. This text does not exclude it: where one is, the
rule above applies. Where a field of this text can only ever hold a plain id, the
text says "plain id"; the table in §5 lists both kinds.

**Order.** Every input of a document has an order key, a triple (timestamp, source
id, entry id). For an ordinary entry the source id is the BlueId text of its
timeline and the entry id the BlueId text of the entry. For a timer firing the
source id is the BlueId text of its Timer Source and the entry id the BlueId text
of its Timer Entry. Two triples are compared by their first parts as integers; if
those are equal, by their second parts as ASCII byte strings; if those are equal
too, by their third parts as ASCII byte strings. This is the one order Coordination
and Time define for the inputs of a document (Coordination section 2.4, Time
section 6). K is the order key of E.

## 1. Scope, roles and trust

In Mandates an operation names the mandate and every processor reads it. Here the
other processors cannot read the mandate. The agent's operation carries a
commitment to the mandate, and a statement on T, signed by the represented party's
own document processor, says whether the mandate admits the operation.

- The **mandate processor** attests mandate states: it signs a
  `Mandate State Attestation` (§5). It knows nothing of the target document or of
  the operation.
- The **signer**, the document processor of the represented party, holds the
  mandate. It evaluates E against an attested mandate state and writes the result
  on T as a statement signed with its own key (§6, §7).
- **Every other processor** decides E from that entry by the rules of the
  Coordination Evidence specification: it takes the first considered entry for E
  on T, makes the comparisons of §8 with its own values, and then applies E,
  rejects it or waits.

**What is trusted, stated plainly.** A statement is a signed assertion and nothing
more. No processor other than the signer checks the evaluation, and nothing in a
statement shows that the verdict is the one the mandate gives.

- The mandate processor answers for the state: that S is the mandate's state at
  the attested position.
- The signer answers for the evaluation: that the conditions of §7 held and that
  the verdict is the one §7 defines for S, D and E.
- The signatures exist so that each of the two can be held to what it stated when
  the mandate is later disclosed in an inquiry. `statementCommitment` ties a
  statement to the exact bytes the mandate processor signed, so the responsibility
  can be split between the two afterwards (§7).
- The other participants accept the signer by accepting the document: the profile
  of the represented party's channel names the signer's key, and the channel's
  fields change only through the document's own program, which they accepted
  (Coordination Evidence section 3).

This package makes no claim of cryptographic soundness of the evaluation. A signer
that signs a wrong verdict, or a mandate processor that attests a wrong state, is
found out only by an inquiry that reads the mandate.

**What this version supports.**

1. *Mandate types.* Mandates of type `Mandates/Operation Mandate` and of its
   subtypes, recognised by ancestry: the type chain of the mandate state contains
   `Operation Mandate` of the required Mandates publication. A mandate composed
   from clauses (`MandateClauses/Mandate with Clauses`) is such a subtype. A state
   of any other type is a fault of the mandate (§7).
2. *Timers.* Mandates with timers are supported (§5, §7).
3. *One edition for both documents.* The mandate and the target document are on
   the same edition: the Coordination publication, the Coordination Evidence
   package and the Mandates publication this package requires. A mandate
   established under another Mandates package is a fault of the mandate (§7).
4. *Identities follow the edition.* Every type identity of this package changes
   with each edition of Coordination, of Coordination Evidence or of Mandates it
   is built on. An operation is decided under the profile of its channel as it is
   in the state on which the operation is evaluated (Coordination Evidence
   section 3).
5. *A channel without evidence.* An operation whose authority claim is a
   `Mandate Commitment Authority` and which is performed on a channel without
   evidence, that is a channel whose type is not, by ancestry, a
   `Timeline Channel with Evidence`, such as a plain `Timeline Channel`, or an
   evidence channel whose fields are not well formed, is rejected from the
   document state, without reading any evidence timeline, and the document
   continues with the next input (Coordination Evidence section 6).
6. *Cyclic sets.* A mandate, a mandate state, a target state and an operation
   entry may be members of cyclic sets; each is named by its final id (Conventions).

A processor MUST explicitly support this exact package and protocol, the required
Coordination Evidence protocol and the required Mandates protocol. Installing this
data package grants no native support.

## 2. Exported types

| Type | Kind | Purpose |
|---|---|---|
| Mandate Commitment Authority | `Mandates/Authority` | Authority claim that carries M and names no mandate |
| Mandate State Attestation | document signed by the mandate processor | What the mandate processor states about one state of a mandate (§5) |
| Signed Statement Profile | `CoordinationEvidence/Evidence Profile` | Profile under which the evidence is a statement signed with the key the profile names (§4) |

The statement itself is not a Blue type. It is the byte string of §6, carried in
the `receipt` of a `CoordinationEvidence/Proof Entry`.

## 3. The authority claim

The agent writes E with a `Mandate Commitment Authority` as its authority claim, in
the place where `Mandates/Mandate Authority` stands in Mandates:

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
| `mandateCommitment` | M, the salted mandate commitment, 64 hex characters (below) |

The claim has exactly these two fields and its type. It has no `mandate` field and
never carries or points to a mandate.

**The commitment, byte for byte.**

    M = hex( SHA-256( salt || id ) )

`salt` is exactly 32 bytes (below). `id` is the final id of the mandate before
initialization, written as its text in ASCII: a plain id, or a member id with its
`#` and index when the mandate is a member of a cyclic set. The hash input is the 32
salt bytes followed directly by the characters of the id: no separator, no length
prefix and no terminator. `hex` writes the 32 bytes of the hash as 64 hex
characters. The claim and a statement (§6) carry M as this same text, and it is
compared as text.

**The salt.** The salt is exactly 32 bytes and the signer holds it. The same salt
is used in `statementCommitment` (§7). The signer signs nothing for an E whose
salt it does not hold or whose salt is not 32 bytes. This is all that is required.
One salt per mandate satisfies it.

What this baseline gives: the mandate's BlueId cannot be confirmed by guessing,
because M does not show it to anyone without the salt, and the protocol does not
disclose the mandate's content. What it does not give: with one salt per mandate
every operation under that mandate carries the same M, and every statement made
from one attestation carries the same `statementCommitment`. An observer
therefore sees which operations use one mandate, and between which of them its
attested state changed.

*Optional extension: a salt per operation.* A salt that is unique for each
operation removes that linkage: no two operations then carry the same M or the
same `statementCommitment`. Such a salt is drawn at random, or derived from a
secret kept per mandate and a value that differs for every operation; it must be
unpredictable to anyone who does not hold the secret it comes from. A repeated
salt links the operations that share it, as above. This is an extension and not a
requirement because no verifying processor can check anything about the salt, and
because confidentiality as a whole holds only as far as the agent keeps it (§9):
the package does not make its correctness depend on it.

No verifying processor can check the length or the uniqueness of a salt: a
verifying processor never sees a salt. What is required of the salt binds
whoever computes M, and the signer.

Who computes M is not prescribed. How a value of M reaches the agent is a matter
of the deployment; the following notes are not normative. With one salt per
mandate the agent simply holds one value of M for each mandate. With a salt per
operation there are two arrangements:

- (a) The represented party's processor derives the salt and issues ready values
  of M to the agent, each for one use. The agent then holds neither a salt nor
  the secret. Recommended where the agent writes through the same operator.
- (b) The agent and the represented party's processor share a secret that is set
  up when the mandate is approved, and each derives the salt of an operation from
  it.

**The field set is checked by the processor.** The Language schema limits the claim
to two fields with a value, but it does not close the field set: it admits a further
field that carries only a type, such as `mandate: {type: Mandates/Operation
Mandate}`, and a further field written as a reference that resolves. A processor
therefore checks the field set itself, from the entry alone: a claim whose fields
are not exactly `actor` and `mandateCommitment`, beside its type, is malformed.
`mandateCommitment` is well formed only as 64 hex characters; the schema fixes the
length and the processor checks the characters. An operation whose claim is
malformed in one of these ways is rejected at once from the document state, without
reading T.

A claim that the schema does reject, for example one with a third field that has a
value or with a `mandateCommitment` of another length, is a different case. The
whole `Timeline Entry` that carries it is then not admissible Blue content. This is
existing Coordination behaviour for any inadmissible entry and is not changed here:
there is no operation to decide, and a reader cannot import the agent's operation
timeline past such an entry. It is the fault of that timeline's writer.

**Which claims are decided from T.** An operation whose authority claim has
exactly the type `Mandate Commitment Authority` of this package is
evidence-decided in the sense of the Coordination Evidence specification. The
exact type decides, not ancestry. A claim whose type extends
`Mandate Commitment Authority` and a claim of the parent type `Mandates/Authority`
alone are not claims of this package. Such an operation is never decided from T. It fails closed, as the Mandates specification requires
of an authority wrapper that is not supported (its section 1): E is rejected from
the document state, without reading T, and the document continues. A claim of
`Mandates/Mandate Authority` keeps the rules of Mandates.

**Checked by every processor, before T is read.** These are the checks a processor
performs for a `Mandates/Mandate Authority` without reading the mandate. They are
unchanged, and a failure has the same outcome as it has for `Mandate Authority`:

1. the claim's `actor` is the actor of the target channel the operation selects;
2. that target channel exists and is a concrete `Coordination/Timeline Channel`
   (which includes `CoordinationEvidence/Timeline Channel with Evidence`);
3. the target document contains a Timeline Channel with the actor and timeline of E
   (the delegate participant);
4. the target document's actor policy admits E as a delegated action.

Ordinary operation validation and protection against executing E twice also remain
with the processor. Everything that needs the mandate is the signer's (§7).

An outcome under one of these four checks, a rejection for a claim that is
malformed or is not of the exact type, and a rejection for a channel that is not
an evidence channel or whose fields are not well formed are decided from the
document state without consulting T.
None of them carries `AUTHORITY_EVIDENCE_DENIED` or `AUTHORITY_EVIDENCE_REJECTED`;
those two reasons belong to an operation that T decided (Coordination Evidence
section 6).

The agent announces nothing before writing and takes no part in what follows. M
tells the signer which mandate is meant and lets a processor match a statement to
the operation.

## 4. The profile

`Signed Statement Profile` is a `CoordinationEvidence/Evidence Profile`.

| Field | Content |
|---|---|
| `statementSignerKey` | The Ed25519 public key under which statements for this channel are verified: a `Coordination/Ed25519 Public Key` that is a well-formed key as section 3 of the Coordination Evidence specification defines it |

The value has exactly this one field. The well-formed key rule is that of the
Coordination Evidence specification and is used here by reference: its four
conditions and its eight refused encodings apply to `statementSignerKey` as they
apply to the channel's `mandateProcessorKey`.

The profile has no list of providers. A processor that verifies a statement
compares nothing with such a list, so a list would bind nothing. Which timeline
providers the mandate's history rests on is checked by the signer and is part of
what the signer answers for (§7).

`statementSignerKey` and the channel's `mandateProcessorKey` name two roles. The
rules do not require the two keys to differ. The two kinds of signature can never
be taken for one another, because their signed bytes begin with different domain
texts (§5, §6).

**When a host supports the profile** is decided as section 3 of the Coordination
Evidence specification states, from the exact type alone:

1. The exact type of the channel's `evidenceProfile` is not
   `Signed Statement Profile` of this package: this text does not apply. A type
   that extends `Signed Statement Profile` is another exact type and is not this
   profile.
2. It is, and the host does not implement this protocol: the host refuses the
   document where the channel is declared. A refusal finalises nothing.
3. It is, and the host implements this protocol: the host checks the content. The
   value is well formed only if its fields are exactly `statementSignerKey` and
   that key is a well-formed key. The Language schema enforces the required
   field, at most one field with a value and the length of the key; it admits a
   further field that carries only a type, so the processor checks the exact
   field set and the rest of the key rule itself. A value that is not well formed
   makes the channel's fields not well formed, with the consequence the
   Coordination Evidence specification states: every operation with a
   `Mandate Commitment Authority` on that channel is rejected from the document
   state, without reading T, and the document continues.

Support depends on nothing but the exact type: no installed file, no
configuration and no platform.

## 5. The attestation

The mandate processor states one thing per mandate state: a document of the exact
type `Mandate State Attestation` of this package. No verifying processor ever
reads an attestation. It is an object between the mandate processor and the
signer, and for a later inquiry.

| Field | Content | Use |
|---|---|---|
| `mandate` | Reference: the final id of the mandate before initialization | The preimage of M (§3) |
| `state` | Reference: S, the root document of the mandate processor's snapshot, by its final id | The state the signer evaluates |
| `documents` | List of references to the further documents of the snapshot (embedded documents), by their final ids, strictly ascending when the id texts are compared as ASCII byte strings; absent when there is none | Position completeness (below) |
| `authorityPackage` | Text: the BlueId of the Mandates package the mandate is established under, a plain id | Must be the Mandates package this package requires, else the mandate is at fault (§7) |
| `mandateProgram` | Text, not empty: identity of the program of the state | Compared with `approvedProgram` |
| `approvedProgram` | Text, not empty: identity of the approved program; absent when none is approved | The mandate is approved exactly when it is present and equals `mandateProgram` as a text |
| `position` | List of rows, at least one, strictly ascending when the BlueId texts of the timelines are compared as ASCII byte strings. A row has `timeline` (reference to the Signed Timeline, a plain id) and, unless no entry of that timeline is included, `lastEntry` (reference to the last included Timeline Entry, by its final id); no other field and no type | The history position, checked by the signer against K (§7) |
| `lastTimerFiring` | The order key of the latest timer firing already applied in S; absent when none has been applied | Must be strictly before K (§7) |
| `nextTimerFiring` | The order key of the earliest pending timer firing; absent when none is pending | K must be strictly before it (§7) |
| `sequence` | Integer: 0 for the first attestation of this mandate by this processor, then the previous one plus one | The chain (below) |
| `previous` | Reference: the BlueId of the mandate processor's preceding attestation of the same mandate, a plain id; absent only in the first | The chain |

A timer bound, `lastTimerFiring` or `nextTimerFiring`, has exactly three fields
when it is present:

| Field | Content |
|---|---|
| `timestamp` | Integer, at least 0: the timestamp of the Timer Entry |
| `source` | Text: the BlueId of the Timer Source, a plain id |
| `entry` | Text: the BlueId of the Timer Entry, a plain id |

The three are the order key of the firing (Order, above). The two ids are texts
and not references: a timer firing is not an entry of a Signed Timeline, and the
attestation only has to place it in the order.

**Plain ids and member ids in the attestation and the statement.**

| Position | Forms | Why |
|---|---|---|
| `mandate`; the id inside M (§3) | Plain or member id | A mandate can be created together with documents that refer to each other |
| `state`; the references of `documents` | Plain or member id | A state or an embedded document may be a member; the Language does not exclude it |
| `lastEntry` of a position row | Plain or member id | It names a Timeline Entry like E; an entry that can be E for one operation is the last entry for the next |
| `targetState` and `entry` of a statement (§6) | Plain or member id | D is a document state and E a Timeline Entry |
| `timeline` of a position row | Plain only | A `Signed Timeline` holds a provider, a URL and a flag and no reference to other content, so it cannot be part of a cycle |
| `source` and `entry` of a timer bound | Plain only | A Timer Source holds two texts and no reference. A Timer Entry is made by the processor after everything it refers to exists, and nothing can refer to it before |
| `previous` | Plain only | An attestation refers only to content that exists before it, so the chain has no cycle |
| The BlueId of an attestation in its signed bytes | Plain only | The same reason |
| `authorityPackage`; `profile` of a statement | Plain only | The identity of a package and of a type of a package are ordinary identities |

Where the table says "plain only", a text of the other form is not well formed in
that position. Lists are ordered by comparing the id texts as ASCII byte strings,
whatever their form: `X#10` comes before `X#9`.

A value that does not exist is an absent field, never an empty list. The content
of the two program identities is not interpreted; they are compared as texts (how
a program is identified is not decided, §11).

**The field set is closed and is checked by whoever uses an attestation.** The
Language schema requires the fields marked required in the type and fixes lengths,
but it does not close the field set. The signer, and anyone else who checks an
attestation, MUST check that it has exactly these fields and the exact type, that
every id has a form the table above allows, and that `documents` and `position`
are in the stated order.

**What the mandate processor signs.** It signs the BlueId of the attestation with
the key that is `mandateProcessorKey` of the channel:

    attestation signed bytes = UTF8( "blue.private-mandates.mandate-state-attestation" ) || LF || UTF8( BlueId of the attestation )
    signature                = Ed25519( attestation signed bytes )

Pure Ed25519 of RFC 8032. The BlueId of an attestation is a plain id, written as
its text in ASCII, and no byte follows it. The signature is outside the signed content: the
attestation has no signature field. There is no other serialisation: the canonical
form and the hash are the BlueId of the Language.

**Which signatures are accepted.** This one rule holds for the signature of an
attestation and for the signature of a statement (§6). The key must be a
well-formed key (Coordination Evidence section 3). A signature is 64 bytes, R
followed by S, over a message under the key A. It is accepted only if all hold:

1. S, read as a little-endian integer, is below the group order L;
2. R decodes to a point of edwards25519 and is not of small order;
3. the encoding of [S]B − [k]A is equal, byte for byte, to the 32 bytes of R, where
   B is the base point and k = SHA-512(R || A || message) read as a little-endian
   integer and reduced modulo L.

This is the equation without the cofactor, compared on encodings. A signature made
by a signer that follows RFC 8032 passes.

**Not in the attestation, on purpose:** the mandate processor key (the statement
carries it and a processor compares it with the channel's); D, E and the salt (an
attestation is about S alone and serves every operation decided on that state).

**Position completeness.** `position` covers every timeline S depends on through a
channel. For S and for every document of `documents`, every contract of that
document whose type is, by ancestry, a Coordination `Timeline Channel` or
`Public Timeline Channel` names a timeline, and each such timeline is a row of
`position`.

**The chain.** `sequence` and `previous` link the attestations of one mandate by one
mandate processor into a hash chain. There is no timeline of the mandate processor.
The signer needs one attestation and does not follow the chain. The chain is for
an inquiry. Two different attestations signed by one key for one `mandate` with
the same `previous`, or with the same `sequence`, show equivocation by the mandate
processor, from the two signatures alone and without the mandate's content. A chain
with every link present shows the states the mandate processor claims, in order. A
missing link is the mandate processor's to explain; the chain does not show that
every attestation was handed over.

**What stays trusted to the mandate processor.** Asserted by its signature alone:

- that S is the state that results from processing exactly the entries up to the
  last entry of each row, and each row's last entry itself;
- `documents`: nothing shows the list complete;
- dependencies that are not a channel contract of S or of a listed document:
  documents S refers to without embedding them, sources reached through another
  channel type, and anything a contract reads when it runs;
- the two timer bounds;
- `authorityPackage` and the two program identities.

## 6. The statement

### 6.1 Content

A statement has seven values:

| Key | Content | Form |
|---|---|---|
| `profile` | The BlueId of the type `Signed Statement Profile` of this package: the exact type of the channel's `evidenceProfile` | Plain id |
| `targetState` | The final id of D | Plain id or member id |
| `entry` | The final id of E | Plain id or member id |
| `mandateCommitment` | M, exactly the text of `mandateCommitment` in E's authority claim | 64 hex characters |
| `mandateProcessorKey` | The key under which the signer verified the attestation, exactly the text of `mandateProcessorKey` of the channel | 64 hex characters, and nothing more is required of it here |
| `statementCommitment` | The salted commitment to the bytes the mandate processor signed (§7) | 64 hex characters |
| `verdict` | Whether the mandate admits E | `true` or `false` |

`mandateProcessorKey` inside a statement is checked for its form only: 64 hex
characters. It is not checked there as a well-formed key. Comparison 5 of §8
requires it to equal the channel's value, and T is read only for a channel whose
key is well formed (Coordination Evidence section 6).

`targetState` and `entry` are final ids. A processor compares them with the final
id of its own state D before E and of the operation entry E, as "Which id names a
node" in the Conventions defines them: the member id when the node is a member of
a cyclic set and the plain id otherwise, never the id of a detached body. A
statement names nothing else: no grant, no status, no reason and nothing of the
mandate.

### 6.2 Bytes

The statement is the following ASCII text, with no white space, no byte before `{`
and no byte after `}`. The seven keys are in this order. Each value is written as
the form above says, between the quotation marks where the layout has them:

    statement = '{"profile":"'             P
                '","targetState":"'        D
                '","entry":"'              E
                '","mandateCommitment":"'  M
                '","mandateProcessorKey":"' K
                '","statementCommitment":"' C
                '","verdict":'             V
                '}'

P is a plain id; D and E are final ids, each a plain id or a member id; M, K and C
are 64 hex characters each; V is the four characters `true` or the five characters
`false`. (In this layout K stands for the
key text, not for the order key of E.) The layout is fixed text, not "any JSON
with this meaning": another key order, a space, an escape sequence, an upper-case
hex digit or a further key is not a statement. None of the values can hold a
character that JSON would escape, and none can hold a quotation mark (the `#` and
the digits of a member id are neither), so a byte string matches the layout in at
most one way.

The fixed text of the layout is 126 bytes. A statement is therefore 418 to 475
bytes long: 126, plus 32 to 44 for P, plus 32 to 54 for each of D and E, plus 64
for each of M, K and C, plus 4 or 5 for V.

The signer signs the statement under a domain text:

    statement signed bytes = UTF8( "blue.private-mandates.statement" ) || LF || statement
    signature              = Ed25519( statement signed bytes )          64 bytes, R followed by S

Pure Ed25519 of RFC 8032, accepted by the rule of §5. The domain text differs from
that of an attestation and from every domain text of Coordination, and the
statement carries the BlueId of the profile type, so a signature made for a
statement can not be presented as a signature over another kind of message, nor
under another edition of this profile.

The `receipt` of the Proof Entry carries the statement and the signature:

    receipt bytes = statement || signature
    receipt       = canonical base64 of the receipt bytes (Coordination Evidence section 5)

The signature is the last 64 bytes; everything before it is the statement. There
is no length field, no separator and no other byte. The receipt bytes are
therefore 482 to 539 bytes long, and the `receipt` text, their canonical base64,
is 644 to 720 characters long. Bytes of any other length are not a statement (§8).
This layout is the evidence encoding of the profile in the sense of the
Coordination Evidence specification, and the seven values are the stated values
of the evidence.

### 6.3 Worked example

The ids below are made up and stand in for real ones; P is not the BlueId of the
profile type of this package. The signer key is the public key of test 1 of RFC
8032 section 7.1 (secret key `9d61b19d…7f60`), and the mandate processor key that
of test 2.

    statementSignerKey  = d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a
    P                   = HhcFVPYPc2TvhvwwVmNAF6qUVBsU7Eex2APjDBUbNHHn
    D                   = HK1RiEymW5yYZy6Y6cquarWa3ncst4EhanHeVvVB1cso
    E                   = HJTyj4yKfEkbZRULXBUmD1mbzibnTeERNVuYfyRXenur
    salt                = 000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
    mandate (initial)   = rab1F73xd7pR5QjhCv1TFAtHpnq3hZPupgT6BTBZ54s
    attestation         = Fo3G5ADUwEeC5UgbC3UTH6WtxxrBQPknAaFQf6HuFUg7
    M                   = 7dbabc5e4f68a135a0d7044a4bf56f4c6203a9636ac67fb9b5727240fc29279d
    K                   = 3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c
    C                   = c72990a40f78bc73e769a7bd0bd0cddb35371d9ec227f4ca1c5843f4b115066c
    V                   = true

M is `hex( SHA-256( salt || mandate ) )` and C is
`hex( SHA-256( salt || attestation signed bytes ) )` for these values.

The statement (454 bytes, one line):

    {"profile":"HhcFVPYPc2TvhvwwVmNAF6qUVBsU7Eex2APjDBUbNHHn","targetState":"HK1RiEymW5yYZy6Y6cquarWa3ncst4EhanHeVvVB1cso","entry":"HJTyj4yKfEkbZRULXBUmD1mbzibnTeERNVuYfyRXenur","mandateCommitment":"7dbabc5e4f68a135a0d7044a4bf56f4c6203a9636ac67fb9b5727240fc29279d","mandateProcessorKey":"3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c","statementCommitment":"c72990a40f78bc73e769a7bd0bd0cddb35371d9ec227f4ca1c5843f4b115066c","verdict":true}

    SHA-256( statement )     = 09d972fe4d477a0d72653db45cfc2a3336c26af6bcde5845f177d8871336139d
    signature                = fd82a8b474211718415fc7a5cbebc8ebdf5d232372ef0b75c42c24902fe1bd39018ba7c36e4e2ff727fb87ec599336e8ec816107d3fc60f2184987d30c24750d
    receipt bytes            = 518 bytes
    SHA-256( receipt bytes ) = 850a143a3982f75cfc5364dac214ea163a985540fb45b541b9a563a73a1f66f3

The `receipt` text (one line):

    eyJwcm9maWxlIjoiSGhjRlZQWVBjMlR2aHZ3d1ZtTkFGNnFVVkJzVTdFZXgyQVBqREJVYk5ISG4iLCJ0YXJnZXRTdGF0ZSI6IkhLMVJpRXltVzV5WVp5Nlk2Y3F1YXJXYTNuY3N0NEVoYW5IZVZ2VkIxY3NvIiwiZW50cnkiOiJISlR5ajR5S2ZFa2JaUlVMWEJVbUQxbWJ6aWJuVGVFUk5WdVlmeVJYZW51ciIsIm1hbmRhdGVDb21taXRtZW50IjoiN2RiYWJjNWU0ZjY4YTEzNWEwZDcwNDRhNGJmNTZmNGM2MjAzYTk2MzZhYzY3ZmI5YjU3MjcyNDBmYzI5Mjc5ZCIsIm1hbmRhdGVQcm9jZXNzb3JLZXkiOiIzZDQwMTdjM2U4NDM4OTVhOTJiNzBhYTc0ZDFiN2ViYzljOTgyY2NmMmVjNDk2OGNjMGNkNTVmMTJhZjQ2NjBjIiwic3RhdGVtZW50Q29tbWl0bWVudCI6ImM3Mjk5MGE0MGY3OGJjNzNlNzY5YTdiZDBiZDBjZGRiMzUzNzFkOWVjMjI3ZjRjYTFjNTg0M2Y0YjExNTA2NmMiLCJ2ZXJkaWN0Ijp0cnVlff2CqLR0IRcYQV/HpcvryOvfXSMjcu8LdcQsJJAv4b05AYunw25OL/cn+4fsWZM26OyBYQfT/GDyGEmH0wwkdQ0=

A second example, with a target state that is a member of a cyclic set. All values
are as above except D and V:

    D                   = HK1RiEymW5yYZy6Y6cquarWa3ncst4EhanHeVvVB1cso#3
    V                   = false

The statement (457 bytes, one line):

    {"profile":"HhcFVPYPc2TvhvwwVmNAF6qUVBsU7Eex2APjDBUbNHHn","targetState":"HK1RiEymW5yYZy6Y6cquarWa3ncst4EhanHeVvVB1cso#3","entry":"HJTyj4yKfEkbZRULXBUmD1mbzibnTeERNVuYfyRXenur","mandateCommitment":"7dbabc5e4f68a135a0d7044a4bf56f4c6203a9636ac67fb9b5727240fc29279d","mandateProcessorKey":"3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c","statementCommitment":"c72990a40f78bc73e769a7bd0bd0cddb35371d9ec227f4ca1c5843f4b115066c","verdict":false}

    SHA-256( statement )     = 959489acc15492b311758414fe5dae7c7566f0d430c804e894f0814e2cff9af7
    signature                = 2cda6711c5ddaa70526bed2e050a76f8d6d26e866e183d5a39539ceda766d04794fa5e7cc0e366a044aeabcf700839795924478a0632d347a9148a5959be1b0e
    receipt bytes            = 521 bytes
    SHA-256( receipt bytes ) = d0326e32e859ed47492dabc634caebf975b8368baff52a9f691f4a47bf63b325

## 7. What the signer does before it signs

The signer signs a statement for E only when every condition below holds. The
conditions are its duty. No other processor repeats them, and a statement that
exists asserts all of them.

**Conditions.** In this order:

1. *The attestation.* The signer holds a document of the exact type
   `Mandate State Attestation` with exactly the fields §5 lists, and a signature
   over its attestation signed bytes that the rule of §5 accepts under the
   channel's `mandateProcessorKey` as in force in the document strictly before K.
2. *The commitment.* The signer holds the salt, it is 32 bytes, and M of E's
   authority claim equals `hex( SHA-256( salt || id ) )` for the attestation's
   `mandate`, byte for byte as §3 defines.
3. *The position.* The attested state S is the mandate's state strictly before K.
   The signer establishes, from timelines it has itself verified under
   Coordination, that `position` is complete (§5, "Position completeness") and
   that for every row the row's last entry is the last entry of that timeline
   strictly before K; a row without `lastEntry` states that the timeline has no
   entry before K. For each row this is established by one of the means
   Coordination defines for completeness (its section 5): a provider's
   completeness guarantee whose last entry is the row's and which is complete to
   after K, or authenticated successor evidence, the provider-signed entry that
   follows the row's last entry and is after K; or, when a timeline of the
   position is E's own timeline, E itself, being the entry whose previous entry
   is the row's. Which providers the signer relies on is its own decision and
   part of what it answers for.
4. *Timers.* The attestation covers E only if both timer comparisons hold, each
   on the full order key and not on the timestamp alone: `lastTimerFiring`, when
   present, is strictly before K; and K is strictly before `nextTimerFiring`,
   when present. An operation whose key is at or after the next firing in that
   order is not covered by this attestation and needs an attestation of the
   state after that firing. This is the position rule a processor applies to a
   mandate named in clear, whose state is resolved from its history strictly
   before the full order key of the action (Mandates section 6), so both forms
   give the same result for the same operation.
5. *The target.* D is the signer's own state of the target document strictly
   before E, and E is an entry the signer itself admitted on its timeline. The
   signer is a processor of the target document, so it knows both itself.

If one of the five fails, the signer signs nothing, whatever the mandate holds.

**The verdict.** When the five hold, the verdict follows from S, D and E by the
authorisation rules of Mandates, as stated here. It is the same verdict a
processor reaches for a mandate named in clear, except where "Differences" below
says otherwise.

*Terms.* The grants are those of the scope of S. A grant *applies* to E when its
target names the channel and the operation of E and, if it pins an initial
document, that document is the target document. A grant has a document validation
(`target.documentValidation`), a request validation (`validation`), both or
neither. Each validation is a predicate, evaluated as Mandates defines (its
section 6), with its own fresh gas ledger. A grant *passes* when every validation
it has passes. A grant that has a request validation does not pass when E carries
no request payload.

*The order in which the outcomes apply:*

1. A mandate that is not Active, or a fault of the mandate, gives `false`. No
   grant is looked at. A fault of the mandate is one of: S is not, by ancestry, an
   Operation Mandate; `authorityPackage` is not the Mandates package this package
   requires; the mandate is not approved (§5); S lacks its participants or its
   scope; a grant of its scope has no target.
2. That the actor of E is not the actor of the mandate's `authorizedActorChannel`,
   or that the owner of the target channel is not the actor of its
   `authorityHolderChannel`, gives `false`. No grant is looked at.
3. Otherwise every grant that applies to E is evaluated, in the order of the grant
   keys compared as sequences of UTF-16 code units: the document validation first,
   the request validation only when the document validation passed. Every grant
   that applies is evaluated, also after one has passed. A grant does not pass,
   and the other grants are still tried, when one of its predicates ends in an
   execution error, meets an invalid operand, completes with a result that is not
   the Boolean true, or is statically inadmissible, or when a validation node is
   not an object.
4. If, for any grant that applies, an evaluation that step 3 calls for cannot be
   completed, there is no verdict and the signer signs nothing, whatever the other
   grants give. This covers a validation node that is not well formed under the
   Language when its evaluation is reached (it violates its schema, its types are
   not compatible, a type it uses is on its own inheritance chain, which the
   Language rejects as LANG-TYPE-CYCLE, or its content is invalid in another way
   the Language defines), and content the evaluation needs and the signer does
   not hold. A node whose evaluation is never reached, because of step 1 or 2 or
   because the document validation of its grant did not pass, does not remove the
   verdict.
5. Otherwise the verdict is `true` when some grant passes and no grant before the
   first passing grant, in key order, exhausted its gas ledger. It is `false` in
   every other case: no grant passes, or a grant that exhausted its gas comes
   before the first grant that passes.

For one S, D and E these rules give at most one verdict.

*Differences from a mandate named in clear, on purpose.* For a
`Mandates/Mandate Authority` the Mandates specification says that an error never
authorizes, and a processor that evaluates the predicate or reads the mandate
itself may give no verdict and stop processing the target document. Here a
faulty mandate gives `false` (steps 1, 2, 3 and 5), E is rejected and the target
document continues: the represented party answers for its own mandate, the other
participants cannot read it, and a faulty mandate must not stop the document for
everyone. Repairing the mandate needs an update of the mandate, which applies to
later operations.

**The statement commitment.** The signer computes

    statementCommitment = hex( SHA-256( salt || attestation signed bytes ) )

with the salt of M and the attestation signed bytes of §5: exactly the bytes the
mandate processor signed, nothing more and nothing less, directly after the 32
salt bytes. The value binds the statement to those bytes without showing the
attestation to anyone. Whoever is later given the salt, the attestation and its
signature can check three things separately: that the mandate processor signed
that attestation, that this statement was made from it, and, with the mandate,
whether the verdict follows. A wrong state is then the mandate processor's; a
wrong evaluation of a rightly attested state is the signer's.

**What the signer keeps.** For every statement it signs, the signer keeps what an
inquiry needs: the salt or the means to derive it again, the attestation, and the
mandate processor's signature over it. For how long, and who may obtain them, is
left to the agreement with the operator and is not a rule of this text. With one
salt per mandate the signer keeps that one salt. Where salts are derived from a
secret kept per mandate, disclosing that secret together with the mandate is
enough to reconstruct the salt of every operation under it.

**When the signer signs nothing.** Then no statement exists for E. The represented
party's side ends the wait with a Rejection Entry (Coordination Evidence section
5). It MAY also write a Rejection Entry where it could sign a denying statement: a
Rejection Entry and a statement with `verdict` `false` have the same effect on E
and differ only in the recorded reason (§8).

**Resources.** The Language sets no ceiling on the size, depth or count of valid
content (LANG-LIMIT), and these rules set none either. The work of evaluating is
the signer's. Its side MAY write a Rejection Entry for an operation whose
evaluation would exceed its own budget; the other participants need not know that
budget.

## 8. How a processor decides a Proof Entry

The rules of the Coordination Evidence specification for T apply unchanged:
attribution to the channel's actor, well-formed entries, the first considered
entry in T's chain, waiting. This section defines what that specification leaves
to the profile: verification, and when verified evidence matches E.

**Verification is a function of the bytes and the key.** It uses no external
program, no installed file and nothing that differs between hosts. Its inputs are
the decoded bytes of `receipt` and the `statementSignerKey` of the channel's
profile as in force in the document strictly before K. That key is a well-formed
key: T is not read for a channel whose profile is not well formed, because the
operation is rejected from the document state before (§4). Verification ends in exactly one of three results, which are the
three results the Coordination Evidence specification names (verified, not
evidence, unfinished):

| Result | Meaning | When |
|---|---|---|
| STATEMENT, with the seven values | The bytes are a statement signed with the profile's key | All of: the bytes are 482 to 539 bytes long; the bytes before the last 64 are exactly a statement in the layout of §6.2, with P a plain id, D and E final ids (a plain id, or a member id with an index of at most 9 digits and no leading zero), M, K and C 64 hex characters each and V `true` or `false`; the last 64 bytes are a signature over the statement signed bytes of §6.2 that the rule of §5 accepts under `statementSignerKey` |
| NOT A STATEMENT | The bytes are no such statement | Everything else that the bytes and the key decide: another length, another layout, a value in another form, a signature that the rule does not accept |
| FAULT | No result | A cause outside the bytes of the entry and of the profile: the processor was stopped, ran out of memory, or could not read its own data |

NOT A STATEMENT is final for that entry: the entry is skipped, is the same as no
entry, and is never retried. FAULT is never a decision: the processor finalises
nothing, retries, and does not pass over the entry to a later one.

Every outcome that depends on the bytes of the entry or of the profile is
STATEMENT or NOT A STATEMENT, and is the same on every host. An implementation
MUST NOT let an error that a library raises on particular bytes become a FAULT:
an exception, a refusal or a panic of a base58 decoder, a hex decoder, a point
decoder or a signature routine on some input is NOT A STATEMENT for that input.
An implementation MUST NOT take a library's own notion of a valid key or a valid
signature in place of the rules named above where the two differ. An
implementation MAY refuse a `receipt` text longer than 720 characters, or decoded
bytes longer than 539 bytes, without looking further; the result is NOT A
STATEMENT, as it would be after looking.

**The comparisons.** With the result STATEMENT the processor compares five values
of the statement with its own values, each as a text, byte for byte:

| # | Value of the statement | Against |
|---|---|---|
| 1 | `profile` | The BlueId of the exact type of the channel's `evidenceProfile`, which is `Signed Statement Profile` of this package |
| 2 | `entry` | The final id of the operation entry the processor is deciding |
| 3 | `mandateCommitment` | The text of `mandateCommitment` in E's authority claim |
| 4 | `targetState` | The final id of the processor's own state D before E |
| 5 | `mandateProcessorKey` | The text of `mandateProcessorKey` of the channel |

`statementCommitment` and `verdict` are compared with nothing. The values a
processor compares with MUST come from its own accepted state before K, the
authenticated operation and the authenticated history of T. The entry's
`document` and `operationEntry`, when present, are an advisory hint with no force
and are not read.

| Verification | Comparisons | The entry |
|---|---|---|
| STATEMENT | All five hold | Matching evidence for E; it carries the `verdict` of the statement |
| STATEMENT | Any differs | Skipped as mismatching; never a denial |
| NOT A STATEMENT | Not made | Skipped; never a denial and never retried |
| FAULT | Not made | Nothing is finalised; the processor retries and does not pass over the entry |

Matching evidence with `verdict` `true` lets E proceed to the target document's
own rules. Matching evidence with `verdict` `false` rejects E with the reason
`AUTHORITY_EVIDENCE_DENIED`; a considered Rejection Entry rejects E with the
reason `AUTHORITY_EVIDENCE_REJECTED`; with no considered entry the processor waits
(Coordination Evidence section 6).

**Which outcome applies when several could** is stated in section 6 of the
Coordination Evidence specification: a host that does not implement the profile
refuses; then an outcome from the document state (§3 here); then T. For a Proof
Entry under this profile the checks on T are, in this order and stopping at the
first that fails: attribution to the channel's actor; the field set of the entry;
the canonical base64 form of `receipt`; verification; the five comparisons.

**What is recorded, and where.** A processor records the `statementCommitment` of
the deciding statement together with its decision, admitting or denying, and
records the reason of a rejection. Neither value is part of the document: a
processor MUST NOT write the reason or the `statementCommitment` into the document
state (Coordination Evidence section 6), so neither can change the BlueId of any
state, and with it the `targetState` of any later statement. Later entries for the
same E are ignored, whatever they carry.

## 9. Confidentiality and known limits

**A shared timeline discloses the mandate, without an error by anyone.** In
Coordination a timeline can carry entries for many documents, and fetching it
must not omit the others (Coordination section 2.1). A read enumerates every
entry and MUST NOT filter by document (Coordination section 6). A reader is
granted whole timelines: each key listed in a `Timeline Access` may read every
listed timeline, with entries, referenced content and completeness (Coordination
section 7.1). So if a timeline that a channel of the mandate binds is also bound
by a channel of the target document D, or of any document with other
participants, those participants read every entry written for the mandate on it:
the payloads of the Operation Requests in clear, the mandate's document id, and
the names of its channels and operations. This needs no mistake and no bad
intent. It matters in practice, because an agent often operates on the mandate
first, to obtain authority, and then uses it.

**Advice to the deployment.** If the mandate is to stay unknown to the
participants of D, use separate timelines for it: no timeline that a channel of
the mandate binds should be one that a participant outside the mandate is
granted, in particular not one that a channel of D binds. This holds for the
agent's timeline and for the holder's alike: the agent writes its operations on
the mandate on one timeline and E on another, and the holder approves and
terminates the mandate on a timeline that D does not bind. Mandates permits
this: the mandate's agent timeline and the target's agent timeline need not be
identical, only the actor is the same (Mandates section 2). This is advice and
not a rule. No processor and no signer checks it, a statement is made and decided
in the same way whether the timelines are separate or shared, and whoever binds
the same timeline on both sides does so at their own risk.

Known limits:

- **The represented party can stop the document.** With no considered entry for E
  a processor waits, and no later input of the document is processed before E,
  also not an input of another participant. A represented party that writes
  nothing on T therefore stops the document for everyone at the first operation of
  its own agent, and an admitted agent can cause this with any M. There is no
  deadline.
- **The represented party has the last look.** While the document waits, later
  entries of the other participants are readable on their timelines. The party
  then chooses between a statement and a Rejection Entry, without a limit of time.
- **Two statements.** A signer can sign a `true` and a `false` statement for one
  E. The first considered entry on T decides and the other is ignored; no
  processor is required to notice. The two signatures together are evidence
  against the signer.
- **What an observer learns.** `AUTHORITY_EVIDENCE_DENIED` tells that the signer
  held an attested state for M and stated that it does not admit E. A statement
  and a Rejection Entry may also differ in how soon after E they appear. With one
  salt per mandate, operations under one mandate are linkable (§3).
- **A mandate bounds what the agent can do, not what it can say.** The agent holds
  its own timeline and can write anything on it. Whatever the agent knows, the
  mandate's BlueId or the mandate's content if it was given it, the agent can
  publish there, by error or on purpose: for example with a claim that names the
  mandate in clear, or with an M computed without a proper salt. No rule of this
  protocol and no check at a processor prevents that. Confidentiality towards the
  other participants therefore holds only as far as the agent keeps it. What
  limits the damage is how little the agent is given: it can be handed ready
  values of M (§3) and then needs neither the salt nor the BlueId. And a BlueId
  alone discloses nothing about the content when the mandate carries a random
  field.
- **Cyclic sets: what remains.** A member of a cyclic set is named by its member
  id everywhere this text allows one. Two things remain. A member whose index has
  more than 9 digits cannot be named in a statement or an attestation, so no
  statement can be made for it. And this text takes from the Language that a
  member is opened only with its owning-set proof: a signer or a mandate processor
  that does not hold the proof of a member it must read cannot proceed, and the
  represented party's side can then only reject the operation.
- **An entry on T that readers cannot read** blocks the reading of T, as the
  Coordination Evidence specification states in its section 5.

## 10. Compatibility

Documents that use `Mandates/Mandate Authority` keep their rules, and every earlier
publication is unchanged and remains selectable. This package and its protocol are
unused unless a document declares a channel whose `evidenceProfile` has the exact
type `Signed Statement Profile`, or an operation carries a
`Mandate Commitment Authority`. On a channel that is not an evidence channel, or
whose fields are not well formed, an operation with this claim is rejected from
the document state and the document continues (§1).

## 11. Not decided in this preview

- How a program is identified in `mandateProgram` and `approvedProgram`. The two
  fields are texts that are only compared. The Mandates specification defines no
  program node with a content BlueId that this text could name.
- Whether a deployment uses one salt per mandate or the optional salt per
  operation, which arrangement it then uses, and the derivation function where
  salts are derived (§3). All are left to the deployment.
- A deadline, or another rule that ends the wait for an operation the represented
  party does not decide (§9).
- Whether a processor should record a second statement for the same E that carries
  another verdict or another `statementCommitment`.
- Whether the reason of a rejection is visible to the document's contracts
  (Coordination Evidence section 8). This text only requires that it is not part
  of the document state.
- Whether a processed document state or a timeline entry can be a member of a
  cyclic set. The Language does not say; this text allows it and names such a node
  by its member id (Conventions).
- The two timer bounds are asserted by the mandate processor alone (§5). Nothing
  here lets the signer check them against the mandate's timer registrations.
- An authority claim with no type at all. Coordination refuses such an entry at
  timeline import as content it cannot read, and the document then stops at it as
  at any range it cannot read; no rule of this text applies to it. Whether such
  an entry should be skipped instead is open, for a change of the import rules
  and of this text together.
- Whether position rows are typed; whether `previous` must be absent exactly when
  `sequence` is 0; binding each row's last entry to the mandate's own checkpoint,
  which would remove one item from what stays trusted to the mandate processor.
- The retention period of what the signer keeps, and the procedure of an inquiry.
- A second signer that can write when the first is unavailable; the duty to reject
  an operation whose M matches no mandate.
