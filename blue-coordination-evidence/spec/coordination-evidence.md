# Coordination evidence channels: evidence timelines for operations decided by evidence

Protocol name: `Coordination / timeline channels with evidence/1`
Package namespace: `CoordinationEvidence`
Release status: Core Java integration preview, 23 November 2026

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
rather than process it differently. It refuses where the channel is declared: for a
channel in the initial document it processes nothing; for a channel added later it
stops at the entry that adds the channel. It MUST NOT treat the channel as a plain
`Timeline Channel`.

## 2. Exported types

| Type | Kind | Purpose |
|---|---|---|
| Timeline Channel with Evidence | `Coordination/Timeline Channel` | Participant channel that also names T, the mandate processor key and the evidence profile |
| Evidence Profile | base type | Published, immutable rules under which evidence on a channel is checked; it has no fields and is used only through its specialisations |
| Proof Entry | message of a Timeline Entry on T | Carries one whole proof |
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
   other part of the document.
3. The three fields are fixed for the life of the document: a processor rejects an
   entry that would change any of the three fields of an existing channel; a
   channel added later with all three fields is accepted.
4. Same-provider rule: T MUST be at the provider of the channel's `timeline`.
5. A channel names one T, whatever the number of representatives. A representative
   writes on its own timeline; the operation is performed on the participant's
   channel, and that channel names T.
6. Each participant declares the three fields of its own channel. The other
   participants accept them by accepting the document.
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

**Values the type system cannot exclude.** The Language schema fixes the length of
`mandateProcessorKey`. It cannot express a character set. It does not type the
profile: Language typing of the `evidenceProfile` field is structural, so the schema
admits a value with no type and values of unrelated types, such as an untyped
object, a `Signed Timeline` or a channel, as well as a value whose exact type is
the base `Evidence Profile`. The schema is no protection here. The native rule
below is, and a processor MUST implement it, from the document state alone:

1. `mandateProcessorKey` is well formed only as a well-formed key (below).
2. `evidenceProfile` is well formed only if its exact type is a supported
   specialisation of `Evidence Profile`, not the base type, no type or any other
   type, and its content is well formed under that specialisation's own rules.
   Anything else counts as a missing field.
3. A host that does not support the specialisation's protocol refuses the document
   (section 1). A host that supports it and finds the value malformed under
   rules 1–2 does not refuse and does not wait: for section 6 the channel lacks
   that field.

**Well-formed key.** An Ed25519 public key named by a channel, or by a profile that
refers to this rule, is well formed only if all four hold:

1. it is 32 bytes written as 64 characters `0-9a-f` (lower case);
2. the bytes decode to a point of edwards25519 as RFC 8032 section 5.1.3 states;
3. the encoding is canonical: the 255-bit little-endian y is below 2^255 − 19, and
   the sign bit (bit 255) is clear when x = 0;
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
not refused. A channel whose `mandateProcessorKey` fails any of the four has no
usable evidence fields: for section 6 the channel lacks that field. The rule is
decided from the key alone, so every processor decides it alike. It concerns the
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

**Proof Entry.** The whole proof is the content of the entry, so an authenticated
entry never lacks its proof.

| Field | Content |
|---|---|
| `receipt` | The complete proof in the single encoding admitted by the declared profile, as canonical base64 text: RFC 4648 §4 standard alphabet, with padding, zero pad bits, no line breaks or other characters, so that decoding and re-encoding gives the same text. Required |
| `document` | As above. Optional |
| `operationEntry` | As above. Optional |

A well-formed Proof Entry has the field `receipt`, a non-empty text in that
canonical base64 form whose decoded bytes are the profile's one admitted encoding.
It may also have `document`, `operationEntry` or both; each may be absent. The
message has no other field. Only `receipt` is required.

**The hint is optional and advisory.** In a Proof Entry `document` and
`operationEntry` are a lookup aid and have no force. A Proof Entry without them is
as good as one with them. Every decision about a Proof Entry rests only on the
public output of its proof, as the declared profile defines. A processor MUST
classify each well-formed Proof Entry by the public output of its proof and MUST
NOT skip, or classify differently, a proof because `document` or `operationEntry`
names another document or another operation, names nothing or is absent. What the two fields
hold is not compared with anything. A processor MAY use them to find entries or to
choose the order of its own work; the outcome MUST be the one it reaches by
classifying every well-formed Proof Entry of T in chain order from its public
output alone.

**Rejection Entry.** "E is not to be processed in this document", with no proof.

A well-formed Rejection Entry has exactly the two fields `document` and
`operationEntry`, each present, and no other field. A rejection needs no signature
of its writer. It counts because it is on the participant's timeline.

**Well-formedness is checked by the processor.** For every message on T that
carries one of the two types, the processor itself checks the field set and the
form of `receipt` stated above and, for a Rejection Entry, whether the entry names
this document and E. The check uses the entry alone (and, for the receipt encoding, the declared
profile), so every processor decides it alike. An entry that is not well formed —
a field beside those named, a missing required field (`receipt` of a Proof Entry;
`document` or `operationEntry` of a Rejection Entry), a `receipt` that is not a
text, is empty or is not canonical base64, or decoded bytes that are not the
profile's one admitted encoding
— conforms to neither kind and is skipped (section 6). A skipped entry never
causes a wait or a halt of its own. No size limit is imposed on an entry by these
rules. The byte-exact grammar is not stated in this preview (section 8).

**Who holds the named content.** The writer of an entry holds the document and the
operation entry, since it made the proof or the rejection for them. The readers of
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
fault of the channel's party, on whose timeline T it stands, and it stops only the
operations decided from that T. A message on T of any other type is likewise
outside the open schemas: whether it is Blue content is decided by its own type.

## 6. Deciding an evidence-decided operation

**Immediate rejection from the document state.** E is rejected at once, without
reading T, when at the position of E:

- the channel E is performed on lacks any of the three fields; this includes a plain
  `Timeline Channel` and a field whose value is malformed (section 3);
- the authority claim of E is malformed under the rules of its own protocol;
- T is at another provider than the channel's `timeline`.

Every processor reads the same document state at that position, so the rejection is
deterministic.

**Considered entries.** Otherwise the processor considers an entry on T for E only
if both hold:

1. T's provider attributes the entry to the channel's `actor`;
2. the entry is a well-formed Proof Entry that the declared profile classifies,
   from the public output of its proof, as a matching proof for E, whatever its
   `document` and `operationEntry` hold, or a well-formed Rejection Entry that
   names this document and E (section 5).

Everything else on T is skipped. A skipped entry is the same as no entry.

| What is on T | Treatment |
|---|---|
| An entry attributed to another actor | Skipped |
| An entry of one of the two types that is not well formed (section 5) | Skipped |
| An entry that carries neither type | Skipped |
| A well-formed Proof Entry whose verification completes with "invalid" | Skipped |
| A proof that verifies but that the profile classifies as mismatching | Skipped as mismatching; never a denial |
| A well-formed Proof Entry whose `document` or `operationEntry` names another document or operation, names nothing or is absent | Classified by the public output of its proof like every other Proof Entry; the hint changes nothing |
| A well-formed Rejection Entry that does not name this document and E | Skipped |
| A matching proof for E | Considered; carries its verdict |
| A well-formed Rejection Entry that names this document and E | Considered; E is rejected in this document only |

**Which entry decides.** The first considered entry for E in T's authenticated
chain, counted from the beginning of the chain, also when it precedes E. Later
entries for the same E are ignored, whatever their verdict. T is read from its first
entry in chain order, not in the order in which data happens to arrive.

A matching proof with an admitting verdict lets E proceed to the target document's
own rules. A matching proof with a denying verdict, or a considered rejection,
rejects E. A rejected E is a deterministic rejected input: the document continues
with the next input.

**The durable reason of a rejection.** A processor records the rejection of E with
one of two reasons, and every processor of the document records the same one,
because the deciding entry is the first considered entry of T's authenticated
chain:

| Reason | When |
|---|---|
| `AUTHORITY_EVIDENCE_DENIED` | The deciding entry is a matching proof, verified, whose verdict denies |
| `AUTHORITY_EVIDENCE_REJECTED` | The deciding entry is a considered Rejection Entry |

The reason says which kind of entry decided and nothing about why. A rejection
that is decided from the document state without consulting T carries neither of
the two: an immediate rejection above (the evidence fields of the channel, the
shape of the claim, the provider of T), and a rejection under a check that the
claim's own protocol makes before T is read (for example the holder, the target
channel, the delegate participant or the actor policy). These rules name no reason
for such a rejection; they require only that it is not one of the two.

**When there is no decision.**

| Situation | What the processor does |
|---|---|
| No considered entry for E on T | Waits. Absence of an entry is never a denial |
| No access to T | Waits. A local read failure of T is never a denial. With access it reads T from the start |
| Verification of a well-formed Proof Entry was interrupted locally | Retries and finalises nothing. It does not pass over that entry to a later one. A local resource limit may only interrupt and retry; it is never part of a classification |
| The processor holds two chains of T | Halts; earlier results stand |

**Waiting.** The document processes inputs in full-key order and stops at the first
unresolved evidence-decided operation. A later operation, also of another
participant, is not processed before it. There is no deadline in this preview.

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
- Whether the reason of a rejection (section 6) is visible to the document's
  contracts.
- How a participant supplies T, and how the others consent to a channel added later.
- A message on T whose own type makes it inadmissible as Blue content still fails
  the reading of T at the provider or the host; the open schemas of section 5
  remove this only for the two entry types.
- An entry on T that holds, in any field, a reference the readers can never resolve
  or an invalid reference blocks the reading of T (section 5). This lasts until
  timeline import can skip an entry it cannot read.
