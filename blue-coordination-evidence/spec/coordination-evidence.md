# Coordination evidence channels: evidence timelines for operations decided by evidence

Protocol name: `Coordination / timeline channels with evidence/1`
Package namespace: `CoordinationEvidence`
Release status: Core Java integration preview, 26 November 2026

This package is additive. It requires the exact Coordination publication it was
built against and adds four types to it. It defines no transport type and changes
none: transport, access, ordering, completeness and admission of every document
that declares no channel of section 3 are exactly as the Coordination
specification states. Every Coordination type keeps its exact identity, so a
document that uses this package and a document that does not consume the same
signed timelines, entries, guarantees and provider descriptors.

The type names, the field names and the encodings of this text are fixed. Changing
one of them produces new exact type identities and a new protocol identity of this
package. It never changes an identity of Coordination. What is not decided is
listed in section 8.

Terms: E is an operation entry and K its full Coordination input key (timestamp,
source timeline, entry). D is the state of the target document strictly before E.
T is the evidence timeline named by the channel the operation is performed on.

This text is neutral about the form of the evidence. A *profile* (section 3)
defines three things, and this text uses them under these names:

- the *evidence encoding*: the one byte encoding of a piece of evidence that the
  profile admits;
- *verification*: a check of those bytes under the profile's rules, with exactly
  three results. *Verified*: the bytes are evidence under the profile, and the
  result carries the *stated values* of the evidence, among them a *verdict* that
  admits or denies. *Not evidence*: the bytes are not evidence under the profile;
  this is final for the entry. *Unfinished*: the processor could not finish the
  check for a reason outside the bytes; this is never a decision;
- when verified evidence *matches* E: a comparison of the stated values with the
  processor's own values.

The type name `Proof Entry` and its field name `receipt` are kept whatever the
form of the evidence is. A profile may make the evidence a signed statement; the
`receipt` then carries that statement.

## 1. Scope and layer boundary

A participant may be represented by agents whose authority the other participants
cannot read. For such a participant the document's channel names where the decisions
about those operations appear (T), whose signature on a private authority state the
participant accepts, and under which published rules a piece of evidence is checked.
This package defines that channel, the base type of an evidence profile, the two
entry kinds on T, and how a processor reads T. It does not define any authority type
or any concrete evidence profile. Those are defined by packages whose protocol
requires this one.

An operation is *evidence-decided* when its authority claim (`onBehalfOf`) has a type
that a supported protocol requiring this package defines as decided from T. This
package alone defines no such type. Direct operations and operations under an
authority that names its mandate keep their existing Coordination and Mandates rules.

**Transport is the required Coordination publication's.** T and the channel's
`timeline` are ordinary `Coordination/Signed Timeline` values. Their entries are
ordinary `Coordination/Timeline Entry` values, and descriptors, guarantees,
attestations and every request and response of a provider are the types of the
required Coordination publication with their exact identities. A provider needs no
support for this package: it issues and serves a timeline used by a document of
this package exactly as it does for any document of that publication. A processor
MUST accept such transport objects under their Coordination identities and MUST
NOT require other identities for them because the document declares a channel of
section 3.

A processor MUST explicitly support this exact package and protocol. Loading the
definitions for inspection is not support. A host that does not support this
protocol, or the protocol of the profile a channel declares, MUST refuse the document
rather than process it differently. It refuses where the channel or that profile
first appears: for a channel in the initial document it processes nothing; for a
channel added later, or a profile changed later to such a type, it stops before
the input that adds or changes it. It MUST NOT treat the channel as a plain
`Timeline Channel`.

## 2. Exported types

| Type | Kind | Purpose |
|---|---|---|
| Timeline Channel with Evidence | `Coordination/Timeline Channel` | Participant channel that also names T, the mandate processor key and the evidence profile |
| Evidence Profile | base type | Published, immutable rules under which evidence on a channel is checked; it has no fields and is used only through its specialisations |
| Proof Entry | message of a Timeline Entry on T | Carries one whole piece of evidence in the profile's encoding |
| Rejection Entry | message of a Timeline Entry on T | States that one operation is not to be processed in one document |

## 3. The channel

`Timeline Channel with Evidence` inherits `timeline` and `actor` from
`Coordination/Timeline Channel` and adds three required fields:

| Field | Content |
|---|---|
| `evidenceTimeline` | The evidence timeline T of this channel, a `Coordination/Signed Timeline` |
| `mandateProcessorKey` | The public key whose signature on a private authority state the participant accepts, a `Coordination/Ed25519 Public Key`, well formed as stated below |
| `evidenceProfile` | The published evidence profile under which evidence for this channel is checked, an `Evidence Profile`. The exact specialisation is defined by the profile's own package and selects the native part a host must implement; its content carries the profile's data. A name such as "latest" is never a profile |

Rules:

1. The channel is an ordinary input source for its `timeline`, exactly as a
   `Timeline Channel`. T is not an input source (section 4).
2. The three fields are read from the document state strictly before K, like every
   other part of the document. An operation is therefore decided with the channel
   and its fields as they are in the state on which it is evaluated. This is not a
   rule of its own: it follows from the order in which Coordination processes the
   inputs of a document.
3. Which channels are evidence channels is decided by the Language: a contract is
   an evidence channel exactly when its type is, by ancestry,
   `Timeline Channel with Evidence`. A contract of any other type is not, also one
   that had this type in an earlier state.
4. Same-provider rule: T MUST be at the provider of the channel's `timeline`. This
   is part of what makes `evidenceTimeline` well formed (below).
5. A channel names one T, whatever the number of representatives. A representative
   writes on its own timeline; the operation is performed on the participant's
   channel, and that channel names T.
6. Each participant declares the three fields of its own channel. The other
   participants accept them by accepting the document. This package adds no rule
   about changing the fields or the type of a channel. A channel's fields or type
   change only through the document's own program, which its participants
   accepted, and Contracts and the Language decide whether such a change is
   valid and what follows from it. When, in the state on which an operation is
   evaluated, the channel is no evidence channel (rule 3), the operation is
   rejected at once (section 6). A changed field takes effect from the state in
   which it changed (rule 2).
7. An evidence timeline serves exactly one document. It MUST NOT be named by a
   channel of another document. A reader of another document could not obtain the
   content its entries name (section 5), and would learn from it that a mandate
   was used in this document.
8. Two channels of the same document MAY name the same T. Each operation is decided
   under the fields (`mandateProcessorKey`, `evidenceProfile`) of the channel it is
   performed on. An entry on T counts for a channel only if T's provider attributes
   it to that channel's `actor` (section 6). The first considered entry decides
   per operation, so the entries for one channel's operations are skipped for the
   other channel's operations.

A participant with no representatives may use a plain `Timeline Channel`.

**What the Language enforces, and what the processor checks.** The type marks the
three fields `required: true` and fixes the length of the key. An instance that
lacks one of the three is therefore not valid Blue content: Language admission
refuses it as a schema violation, and so it does a key of another length, a
profile that is a text, a number or a list, a profile whose exact type is the base
`Evidence Profile` with no field, and a profile that carries only a type. This
text does not repeat those checks.

The Language admits more than this protocol accepts. A processor checks the rest
itself, from the document state alone. The three fields of an evidence channel are
*well formed* only if all hold:

1. `mandateProcessorKey` is a well-formed key (below). The schema fixes only its
   length.
2. `evidenceTimeline` is a `Coordination/Signed Timeline` at the provider of the
   channel's `timeline` (rule 4).
3. `evidenceProfile` has a profile type and well-formed content. Language typing of
   this field is structural: the schema admits a value with no type and values of
   unrelated types, such as an untyped object, a `Signed Timeline` or a channel,
   and a value of the base `Evidence Profile` with a field. It is decided from the
   exact type first and from the content second, in three cases, in this order:
   - *No profile type.* The exact type is absent, is the base `Evidence Profile`,
     or is not a specialisation of `Evidence Profile` by ancestry. The profile is
     not well formed, on every host.
   - *A profile type the host does not implement.* The exact type is a
     specialisation of `Evidence Profile` by ancestry, and the host does not
     implement the protocol of the package that defines that exact type. The host
     refuses the document (section 1). It does not look at the content.
   - *A profile type the host implements.* The host checks the content under the
     rules of that profile, its field set included. Content that is not well
     formed makes the profile not well formed. Every host that implements the
     profile decides this alike.

*The consequence.* A document may hold an evidence channel whose fields are not
well formed; no input is rejected for producing one, and a document that starts
with one is started. An evidence-decided operation performed on such a channel is
rejected at once from the document state, without reading T, and the document
continues with the next input (section 6). The second case of the profile is not a
rejection: a host that does not implement the profile's type refuses the document,
whatever else the state holds, and finalises nothing.

Whether a host *implements* a profile depends on the exact type alone: on whether
the host has the native part for the protocol that defines it. It never depends on
the content of the value. A profile MUST NOT make support depend on an installed
file, on configuration or on the platform.

A refusal finalises nothing. A host that refuses records no outcome for the input
that declares the channel or changes its profile, or for any later one, and when it
implements the profile
it continues from the same point. A host that does not run the document's package
selection at all does not process the document; that is the same outcome.

**Well-formed key.** An Ed25519 public key named by a channel, or by a profile that
refers to this rule, is well formed only if all four hold:

1. it is 32 bytes written as 64 characters `0-9a-f` (lower case), the first byte
   first;
2. the bytes decode to a point of edwards25519 as RFC 8032 section 5.1.3 states;
3. the encoding is canonical: the 255-bit little-endian y is below 2^255 − 19, and
   the sign bit (bit 255) is clear when x = 0. RFC 8032 decoding already fails in
   these two cases; they are stated because common libraries decode leniently;
4. the point is not of small order. Given 3, exactly these eight encodings are
   refused:

       0100000000000000000000000000000000000000000000000000000000000000
       ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f
       0000000000000000000000000000000000000000000000000000000000000000
       0000000000000000000000000000000000000000000000000000000000000080
       26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05
       26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85
       c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a
       c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa

A point that is the sum of a point of prime order and a point of small order is
not refused. A `mandateProcessorKey` that fails any of the four makes the
channel's fields not well formed, with the consequence stated above. The rule is decided from the key alone, so
every processor decides it alike. It concerns the
keys this package and its profiles name; it changes nothing in how Coordination
verifies a provider's signature.

## 4. What the evidence timeline is to the processor

T delivers no input to the document and takes no part in establishing which entries
are safe to process: it is not part of completeness, candidate selection or ordering.
There is no requirement on T before the document starts. T is read only to decide an
evidence-decided operation performed on the channel that names it.

No timestamp of T is compared with a timestamp of any other timeline. An entry on T
may appear at any time; only its place in T's own authenticated chain matters.

Anything may be written on T. Whoever can write on T was allowed to by the
participant; the processor does not ask who that is. The readers of T are the
participants of the one document T serves. Reader access to T uses T's own
Timeline Access document, handled like those of the document's other timelines.

## 5. Entries on the evidence timeline

Both kinds are the `message` of an ordinary `Timeline Entry` on T. The fields
`document` and `operationEntry` name a document and an operation by content
BlueId. In a Rejection Entry the two fields are required and are the content of the
entry. In a Proof Entry they are optional and are an advisory hint with no force
(below):

| Field | Content |
|---|---|
| `document` | The document, named by its initial BlueId, the same for every participant. It is normally written as the reference `{blueId: …}`, the convention an `Operation Request` uses for its `document` |
| `operationEntry` | The operation's `Timeline Entry` E, named by its BlueId and normally written as the reference `{blueId: …}` |

**Naming is by BlueId, never by wire form.** An entry *names this document* when the
BlueId of its `document` field node equals the document's initial BlueId. It *names
E* when the BlueId of its `operationEntry` field node equals the BlueId of E. A
reference and the same content written in full have the same BlueId and are the same
Blue content, so an entry cannot be told apart by which of the two was written, and
no rule of this section depends on it. A field that holds anything else, a text for
example, has another BlueId and names neither.

**Open schemas.** The Blue definitions of `Proof Entry` and `Rejection Entry` name
their fields and constrain nothing: no field is typed or required, and the field set
is not closed. The schema of these two types therefore never makes a message
inadmissible as Blue content, whatever its fields. Whether such a message is a
well-formed entry is decided by the processor alone, under the rules of this
section. The channel, the profile specialisations and the authority claims of
requiring protocols keep their schema constraints.

**Proof Entry.** The whole evidence is the content of the entry, so an
authenticated entry never lacks its evidence.

| Field | Content |
|---|---|
| `receipt` | The complete evidence in the evidence encoding of the declared profile, as canonical base64 text: RFC 4648 §4 standard alphabet, with padding, zero pad bits, no line breaks or other characters, so that decoding and re-encoding gives the same text. Required |
| `document` | As above. Optional |
| `operationEntry` | As above. Optional |

A well-formed Proof Entry has the field `receipt`, a non-empty text in that
canonical base64 form. It may also have `document`, `operationEntry` or both; each may be absent. The
message has no other field. Only `receipt` is required. Whether the decoded bytes
are evidence is not a matter of form: it is the result of verification
(section 6).

**The hint is optional and advisory.** In a Proof Entry `document` and
`operationEntry` are a lookup aid and have no force. A Proof Entry without them is
as good as one with them. Every decision about a Proof Entry rests only on the
stated values of its evidence, as the declared profile defines. A processor MUST
classify each well-formed Proof Entry by those stated values and MUST NOT skip,
or classify differently, an entry because `document` or `operationEntry`
names another document or another operation, names nothing or is absent. What the two fields
hold is not compared with anything. A processor MAY use them to find entries or to
choose the order of its own work; the outcome MUST be the one it reaches by
classifying every well-formed Proof Entry of T in chain order from its stated
values alone.

**Rejection Entry.** "E is not to be processed in this document", with no
evidence.

A well-formed Rejection Entry has exactly the two fields `document` and
`operationEntry`, each present, and no other field. A rejection needs no signature
of its writer. It counts because it is on the participant's timeline.

**Well-formedness is checked by the processor.** For every message on T that
carries one of the two types, the processor itself checks the field set and the
form of `receipt` stated above and, for a Rejection Entry, whether the entry names
this document and E. The check uses the entry alone, so every processor decides
it alike. An entry that is not well formed —
a field beside those named, a missing required field (`receipt` of a Proof Entry;
`document` or `operationEntry` of a Rejection Entry), or a `receipt` that is not a
text, is empty or is not canonical base64
— conforms to neither kind and is skipped (section 6). A skipped entry never
causes a wait or a halt of its own. No size limit is imposed on an entry by these
rules. The byte-exact grammar is not stated in this preview (section 8).

**Who holds the named content.** The writer of an entry holds the document and the
operation entry, since it made the evidence or the rejection for them. The readers of
T are the participants of the one document T serves (section 3 rule 7): they
hold the document and receive the operation entry as an input of the document. In
an entry that names this document and E, both references therefore resolve for
every reader, possibly after a wait for the operation entry. This holds for the
hint of a Proof Entry, when it is written, as for a Rejection Entry: the hint
decides nothing, but Language still opens a reference written in it (known limit,
below). A Proof Entry that omits the hint carries no such reference.

**Known limit.** The open schemas do not cover what Language itself requires of any
Blue content, and the skip rule applies only to an entry that was admitted:

- A `{blueId: …}` value is a reference wherever it stands in an entry: in
  `document`, in `operationEntry`, in `receipt`, or in any other field at any depth.
  Language opens every reference when the entry is admitted. If the content of one
  of them cannot be obtained, admission of the entry is incomplete for that reader
  and stays so until the content is available.
- A reference that carries anything beside `blueId`, or whose `blueId` is not a
  BlueId, is invalid: the entry is not Blue content.

An entry with a reference that the readers can never resolve, or with an invalid
reference, therefore blocks the reading of T for them. This lasts until timeline
import can skip an entry it cannot read (section 8). Writing such an entry is the
fault of the channel's party, on whose timeline T it stands. Its effect is not
limited to that party: the first operation that is decided from that T then stays
undecided, and the document processes no later input before it, also not an input
of another participant (section 6, "Waiting"). A message on T of any other type is likewise
outside the open schemas: whether it is Blue content is decided by its own type.

## 6. Deciding an evidence-decided operation

**Immediate rejection from the document state.** E is rejected at once, without
reading T, when at the position of E:

- the channel E is performed on is not an evidence channel (section 3 rule 3), for
  example a plain `Timeline Channel`;
- the channel's three fields are not well formed (section 3), unless the host does
  not implement the channel's profile type, in which case it refuses instead;
- the authority claim of E is malformed under the rules of its own protocol.

Every processor reads the same document state at that position, so the rejection is
deterministic.

**Considered entries.** Otherwise the processor considers an entry on T for E only
if both hold:

1. T's provider attributes the entry to the channel's `actor`;
2. the entry is a well-formed Proof Entry whose evidence is verified under the
   declared profile and matches E, whatever its `document` and `operationEntry`
   hold, or a well-formed Rejection Entry that names this document and E
   (section 5).

Everything else on T is skipped. A skipped entry is the same as no entry.

| What is on T | Treatment |
|---|---|
| An entry attributed to another actor | Skipped |
| An entry of one of the two types that is not well formed (section 5) | Skipped |
| An entry that carries neither type | Skipped |
| A well-formed Proof Entry whose verification gives "not evidence" | Skipped; never retried |
| Verified evidence that does not match E | Skipped as mismatching; never a denial |
| A well-formed Proof Entry whose `document` or `operationEntry` names another document or operation, names nothing or is absent | Classified by the stated values of its evidence like every other Proof Entry; the hint changes nothing |
| A well-formed Rejection Entry that does not name this document and E | Skipped |
| Verified evidence that matches E | Considered; carries its verdict |
| A well-formed Rejection Entry that names this document and E | Considered; E is rejected in this document only |

**Which entry decides.** The first considered entry for E in T's authenticated
chain, counted from the beginning of the chain, also when it precedes E. Later
entries for the same E are ignored, whatever their verdict. T is read from its first
entry in chain order, not in the order in which data happens to arrive.

Matching evidence with an admitting verdict lets E proceed to the target document's
own rules. Matching evidence with a denying verdict, or a considered rejection,
rejects E. A rejected E is a deterministic rejected input: the document continues
with the next input.

**The durable reason of a rejection.** A processor records the rejection of E with
one of two reasons, and every processor of the document records the same one,
because the deciding entry is the first considered entry of T's authenticated
chain:

| Reason | When |
|---|---|
| `AUTHORITY_EVIDENCE_DENIED` | The deciding entry is a Proof Entry whose evidence is verified, matches E and has a denying verdict |
| `AUTHORITY_EVIDENCE_REJECTED` | The deciding entry is a considered Rejection Entry |

The reason says which kind of entry decided and nothing about why. A rejection
that is decided from the document state without consulting T carries neither of
the two: an immediate rejection above (a channel that is not an evidence channel,
fields that are not well formed, the shape of the claim), and a rejection under a
check that the
claim's own protocol makes before T is read (for example the holder, the target
channel, the delegate participant or the actor policy). These rules name no reason
for such a rejection; they require only that it is not one of the two.

The party that writes on T chooses which of the two reasons the others record: it
MAY write a Rejection Entry where it could write evidence with a denying verdict.
The two have the same effect on E. `AUTHORITY_EVIDENCE_DENIED` tells an observer
that evidence about the authority existed and denied; `AUTHORITY_EVIDENCE_REJECTED`
tells nothing about why. The time between E and the deciding entry can differ
between the two kinds and is visible to the readers of T.

**What is recorded is not part of the document.** The reason of a rejection, and
any value a profile has a processor record with a decision, is kept by the
processor beside its decision. A processor MUST NOT write either into the
document state. Neither can therefore change the BlueId of a state.

**Which outcome applies when several could.** For one operation E, in this order:

1. A host that does not implement the declared profile refuses the document where
   the channel is declared (section 3). Nothing below is reached.
2. An outcome decided from the document state without reading T: an immediate
   rejection above, or the outcome of a check that the claim's own protocol makes
   before T is read. An evidence channel whose fields are not well formed is one of
   these immediate rejections.
3. Otherwise T decides, by its first considered entry for E in chain order. For
   each entry on T the processor checks, in this order and stopping at the first
   that fails: attribution to the channel's actor; that the message carries one of
   the two types and is well formed; for a Rejection Entry, that it names this
   document and E; for a Proof Entry, verification, and then whether the evidence
   matches E. An entry that fails one of these is skipped. Verification that is
   unfinished is none of these: the entry is neither skipped nor considered, and
   the processor does not go on to a later entry until verification has given one
   of its other two results.

**When there is no decision.**

| Situation | What the processor does |
|---|---|
| No considered entry for E on T | Waits. Absence of an entry is never a denial |
| No access to T | Waits. A local read failure of T is never a denial. With access it reads T from the start |
| Verification of a well-formed Proof Entry is unfinished | Retries and finalises nothing. It does not pass over that entry to a later one. A local resource limit may only interrupt and retry; it is never part of a classification |
| The processor holds two chains of T | Halts; earlier results stand |

**Waiting.** The document processes inputs in full-key order and stops at the first
unresolved evidence-decided operation. A later operation, also of another
participant, is not processed before it. There is no deadline in this preview. A
party that writes nothing on its T therefore stops the document for everyone at
the first evidence-decided operation on its channel, and while the document waits
it can read the later entries of the others before it decides (section 8).

## 7. Host support and compatibility

The protocol identity of this package is the capability a host must support for a
document that declares `Timeline Channel with Evidence`. A host learns that a
document needs it from the exact type identity of that channel, which names these
rules. There is no separate capability declaration. A host that supports this
package processes a document that declares no such channel exactly as the
Coordination specification states.

This package requires one exact Coordination publication and is rebuilt, with new
identities of its own four types, for another one. It does not replace that
publication: Coordination, and every package built on it, keeps its archive and
its identities, and a plain `Coordination/Timeline Channel` in a document of this
package is the same type as in any other document.

## 8. Not decided in this preview

- The byte-exact entry grammar.
- An `evidenceTimeline` that does not exist at the provider: reject or wait.
- A deadline, or another rule that ends the wait for an operation whose party
  writes nothing on T (section 6, "Waiting").
- Whether the reason of a rejection (section 6) is visible to the document's
  contracts.
- How a participant supplies T, and how a channel added later gets its T
  provisioned and consented to by the others.
- A message on T whose own type makes it inadmissible as Blue content still fails
  the reading of T at the provider or the host; the open schemas of section 5
  remove this only for the two entry types.
- An entry on T that holds, in any field, a reference the readers can never resolve
  or an invalid reference blocks the reading of T (section 5). This lasts until
  timeline import can skip an entry it cannot read.
