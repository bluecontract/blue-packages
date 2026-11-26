# Private Mandates: operations decided by a signed statement

Protocol name: `Private Mandates / statement-decided operation authority/1`
Package namespace: `PrivateMandates`
Release status: Core Java integration preview, 26 November 2026

This package lets the participants of a document decide an agent's operation
without reading the mandate. The agent's operation carries a salted commitment to
the mandate. The represented party's document processor evaluates the mandate and
writes a signed statement of the result on the party's evidence timeline. Every
other processor decides the operation from that statement.

The package requires the exact Coordination publication and the exact Mandates
publication it was built against. It is additive: it changes no type of either,
defines no transport type, and `Mandates/Mandate Authority`, which names its
mandate in clear, keeps its rules. The type names, field names and encodings of
this text are fixed; changing one gives new exact identities. Open points are
listed in §11.

**Conformance.** The key words MUST, MUST NOT, SHOULD and MAY are to be
interpreted as in BCP 14 (RFC 2119, RFC 8174) when, and only when, they appear in
capitals. A sentence in the present tense that states what a processor or signer
does is a requirement as well. Paragraphs headed *Note* are informative.
Explanations, trust model and deployment advice are in
`docs/private-mandates-evidence.md` and are not part of this text.

## 1. Conventions and terms

**Bytes and texts.** A *hex* value is written with the characters `0-9a-f` only,
two characters per byte, the first byte first. `||` joins byte strings with nothing
between them. LF is the byte 0x0A. Every text named here is ASCII and texts are
compared byte for byte.

**Ids.** A *plain id* is the text of a BlueId without `#`: 32 to 44 characters that
decode canonically to exactly 32 bytes (LANG-ID-ENCODING, Language §4.4). A
*member id* names a member of a finalized cyclic set (Language §12.3): a plain id,
`#`, and the member's index in decimal with the digits `0-9`, either `0` or
beginning with `1-9`. This text admits an index of at most 9 digits, so a member id
is 34 to 54 characters. A *final id* is a plain id or a member id.

The final id of a node is the id under which the Language established it as final
content: its member id when it is a member of a finalized cyclic set, and its
plain id otherwise. The BlueId of a member's detached body is never its final id
(Language §12.4). A reference `{blueId: …}` and the same content written in full
have the same final id (LANG-REFERENCE). Two final ids are equal only as texts, so
`X#0` and `X` differ. Where a position admits only a plain id, this text says so,
and a member id there is not well formed.

**Order.** The *order key* of an input is the one Coordination and Time define
(Coordination §2.4, Time §6): (timestamp, source id, entry id), compared by the
timestamp as an integer, then by the source id and then by the entry id as ASCII
byte strings. For a timer firing the source id is the plain id of its Timer
Source and the entry id that of its Timer Entry.

**Symbols.** These symbols have one meaning throughout:

| Symbol | Meaning |
|---|---|
| E | The agent's operation entry, a `Coordination/Timeline Entry` |
| K | The order key of E |
| D | The state of the target document strictly before K |
| M | The mandate commitment E carries (§4) |
| T | The evidence timeline of the target channel (§3) |
| S | A mandate state named by an attestation (§6) |

The *target channel* of E is the channel that the Operation Request of E names, as
in Mandates §6; it belongs to the represented party. "In force before K" means as
held in D.

**Roles.**

- The *agent* writes E on its own timeline with a `Mandate Commitment Authority`.
- The *represented party* is the holder the claim names and owns the target
  channel.
- The *signer* is the document processor of the represented party that holds the
  mandate and signs statements (§9).
- The *mandate processor* processes the mandate and signs attestations of its
  states (§6). It knows nothing of the target document.
- A *processor* is any processor of the target document. It decides E by §7.

## 2. Exported types

| Type | Kind | Content |
|---|---|---|
| Timeline Channel with Evidence | `Coordination/Timeline Channel` | Participant channel that also names T and the two keys (§3) |
| Statement Entry | message of a Timeline Entry on T | One signed statement (§5, §8) |
| Rejection Entry | message of a Timeline Entry on T | "E is not to be processed in this document" (§5) |
| Mandate Commitment Authority | `Mandates/Authority` | Authority claim that carries M and names no mandate (§4) |
| Mandate State Attestation | document signed by the mandate processor | What the mandate processor states about one mandate state (§6) |

The Language schema of these types enforces part of the rules below: required
fields, lengths and value types. Content it refuses is not Blue content, and a
`Timeline Entry` that holds such content is inadmissible as Coordination states
for any entry. Every other rule of this text is checked by the processor or the
signer itself, from the content named, and MUST NOT be left to the schema.

**Host support.** A processor MUST explicitly support this exact protocol before
it decides anything under it; installing this data package grants no native
support. A host that does not support it MUST refuse a document whose state holds
an evidence channel (§3). It refuses where such a contract first appears: for the
initial document it processes nothing; for a contract added later it stops before
the input that adds it. A refusal finalises
nothing, and a host that later supports the protocol continues from the same
point. A host MUST NOT treat the channel as a plain `Timeline Channel`. A host
that supports the protocol processes a document without such a contract exactly
as Coordination states.

## 3. The channel

`Timeline Channel with Evidence` inherits `timeline` and `actor` from
`Coordination/Timeline Channel` and adds three required fields:

| Field | Content |
|---|---|
| `evidenceTimeline` | T, a `Coordination/Signed Timeline` |
| `statementSignerKey` | The Ed25519 public key under which statements for this channel are verified, a `Coordination/Ed25519 Public Key` |
| `mandateProcessorKey` | The Ed25519 public key whose attestation signatures the participant accepts, a `Coordination/Ed25519 Public Key` |

1. A contract is an *evidence channel* exactly when its type is, by ancestry,
   `Timeline Channel with Evidence` of this package. A contract of any other type
   is not, also when it had this type in an earlier state.
2. The channel is an ordinary input source for its `timeline`, as a
   `Timeline Channel` is. In its role as evidence timeline T delivers no input and
   takes no part in completeness, candidate selection or ordering of the
   document; nothing is required of T before the document starts. T is read only
   in step 4 of §7. When T is also the `timeline` of a channel, its entries are
   inputs through that channel as for any channel's timeline.
3. The three fields are read from D. A field changes only through the document's
   own program; Contracts and the Language decide whether such a change is valid.
   A changed field applies to operations evaluated on a state that holds it.
4. The fields are *well formed* only if all hold:
   - `evidenceTimeline` is, by ancestry, `Signed Timeline` of the required
     Coordination publication, and the BlueId of its `provider` equals the BlueId
     of the `provider` of the channel's `timeline`, compared as texts;
   - `statementSignerKey` and `mandateProcessorKey` are well-formed keys (§10.1).

   A document may hold an evidence channel whose fields are not well formed. No
   input is rejected for producing one; an operation decided on it is rejected by
   §7 step 2.
5. Two channels of the same document MAY name the same T. An entry on T counts
   for a channel only when T's provider attributes it to that channel's `actor`.
6. An evidence timeline SHOULD be named by channels of one document only.
7. Reader access to T is given by T's own Timeline Access document, handled as
   for the document's other timelines.

A participant without representatives may use a plain `Timeline Channel`.

## 4. The authority claim

The agent writes E with a `Mandate Commitment Authority` where Mandates places a
`Mandates/Mandate Authority`:

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
| `actor` | Inherited from `Mandates/Authority`: the represented party |
| `mandateCommitment` | M: 64 hex characters |

The claim is *well formed* only if its fields, beside its type, are exactly
`actor` and `mandateCommitment` and `mandateCommitment` is 64 hex characters.

**The commitment.**

    M = hex( SHA-256( salt || id ) )

`salt` is 32 bytes. `id` is the final id of the mandate before initialization,
written as its ASCII text. Nothing separates, prefixes or ends the two. A
statement carries M as this same text.

**The salt.** The salt is 32 bytes and is held by the signer; one salt per mandate
is the baseline. No processor other than the signer sees a salt, so no processor
checks it.

**Which claims this text decides.** An operation is *commitment-decided* when the
exact type of its authority claim is `Mandate Commitment Authority` of this
package; ancestry does not count. Section 7 decides every commitment-decided
operation. An operation whose claim's exact type extends
`Mandate Commitment Authority` has an authority wrapper that no supported protocol
decides and fails closed, as Mandates §1 requires: it is rejected from D with the
reason `AUTHORITY_DENIED`, without reading any evidence timeline. A claim of
`Mandates/Mandate Authority` keeps the rules of Mandates, also on an evidence
channel. An operation of the represented party itself on its own channel is a
direct operation and keeps the rules of Coordination; T is not read for it.

## 5. Entries on the evidence timeline

Both entry kinds are the `message` of an ordinary `Timeline Entry` on T. Their
schemas name the fields and constrain nothing, so they never make a message
inadmissible as Blue content. Whether a message of one of the two types is well
formed is decided by the processor from the entry alone; an entry that is not
well formed is skipped (§7).

**Statement Entry.**

| Field | Content |
|---|---|
| `statement` | The entry bytes of §8.3 as canonical base64 text |

A Statement Entry is well formed only if its only field is `statement` and its
content is a non-empty Text in canonical base64: the standard alphabet of RFC
4648 §4, with padding, zero pad bits and no other character, so that decoding and
encoding again gives the same text. This is decided on Blue content: a reference
to a Text is that Text, and a value of any other type is not well formed, also
when written as a reference.

**Rejection Entry.**

| Field | Content |
|---|---|
| `document` | The target document, named by the final id of its initial state; usually written as `{blueId: …}` |
| `operationEntry` | E, named by its final id; usually written as `{blueId: …}` |

A Rejection Entry is well formed only if its fields are exactly `document` and
`operationEntry`. It *names this document and E* when the final id of the node in
`document` equals the final id of the target document's initial state and the
final id of the node in `operationEntry` equals the final id of E. It needs no
signature: it counts because T's provider attributes it to the channel's actor.

**References in entries.** A `{blueId: …}` value anywhere in an entry, in any
field and at any depth, is a reference that the Language opens when the entry is
admitted. A reference whose content the reader cannot obtain leaves admission of
the entry incomplete until the content is available; a reference with content
beside `blueId`, or whose `blueId` is not a final id, makes the entry not Blue
content. Either blocks the reading of T at that entry (§7 step 4). A message of
any other type is admissible or not by its own type.

## 6. The attestation

The mandate processor states one thing per mandate state: a document of the exact
type `Mandate State Attestation` of this package. No processor reads an
attestation; the signer and an inquiry do.

| Field | Content | Form |
|---|---|---|
| `mandate` | Reference to the mandate before initialization | Final id |
| `state` | Reference to S, the root document of the mandate processor's snapshot | Final id |
| `documents` | References to the further documents of the snapshot (embedded documents), strictly ascending by id text; absent when there is none | Final ids |
| `authorityPackage` | Text: the BlueId of the Mandates package the mandate is established under | Plain id |
| `position` | List of rows, at least one, strictly ascending by the id text of `timeline`. A row has `timeline` (reference to a Signed Timeline) and, unless no entry of it is included, `lastEntry` (reference to the last included Timeline Entry); no other field and no type | `timeline` plain id, `lastEntry` final id |
| `lastTimerFiring` | The order key of the latest timer firing applied in S; absent when none was applied | Timer bound (below) |
| `nextTimerFiring` | The order key of the earliest pending timer firing of S; absent when none is pending | Timer bound (below) |
| `sequence` | Integer: 0 for the mandate processor's first attestation of this mandate, then the previous one's plus one | |
| `previous` | Reference to the mandate processor's preceding attestation of this mandate; absent exactly when `sequence` is 0 | Plain id |

A *timer bound* has exactly the fields `timestamp` (an Integer, at least 0),
`source` (Text: the plain id of the Timer Source) and `entry` (Text: the plain id
of the Timer Entry). It is the order key of the firing (§1).

Lists are ordered by comparing id texts as ASCII byte strings, whatever their
form: `X#10` comes before `X#9`. A value that does not exist is an absent field,
never an empty list.

An attestation is *well formed* only if all hold: its exact type is
`Mandate State Attestation` of this package; it has `mandate`, `state`,
`authorityPackage`, `position` and `sequence`, has `previous` exactly when
`sequence` is above 0, and has no field beside those of the table; every row of
`position` and every timer bound has exactly the fields stated; every id has the
form the table gives; and `documents` and `position` are in the stated order.

**Signature.** The mandate processor signs

    attestation signing input = UTF8( "blue.private-mandates.mandate-state-attestation" ) || LF || UTF8( A )

where A is the plain id of the attestation as its ASCII text and no byte follows
it. The signature is pure Ed25519 (RFC 8032), 64 bytes, accepted by the rule of
§10.2. It is held outside the attestation, which has no signature field.

**Position completeness.** `position` has a row for every timeline that S depends
on through a channel: for S and for every document of `documents`, every contract
whose type is, by ancestry, a Coordination `Timeline Channel` or
`Public Timeline Channel` names a timeline (for a `Public Timeline Channel`, the
timeline its `provider` and `url` denote), and that timeline is a row. These are
the timelines of the required source set of Coordination §12 step 1. An
`evidenceTimeline` is not required as a row, since it is not an input source (§3).

**The chain.** `sequence` and `previous` link one mandate processor's
attestations of one mandate into a hash chain.

## 7. How a processor decides a commitment-decided operation

A processor decides every commitment-decided E by these steps, in this order. The
first step that ends the procedure decides E.

1. **Newness.** The newness rules of the channel through which E is delivered
   apply first, as Mandates §6 step 1 states: the checkpoint of the channel's
   lifetime (Contracts C12) and Coordination's rules for an input that the
   lifetime has already passed, that belongs to another lifetime or whose
   decision there is terminal. An E that is not new is skipped: it is not
   processed again, nothing below is checked for it, it is not rejected and T is
   not read for it. End.

2. **Rejection from the claim and the channel.** E is rejected from D with the
   reason `AUTHORITY_DENIED`, without reading T, when any of these holds:
   - the claim is not well formed (§4);
   - the target channel does not exist in D or is not an evidence channel (§3);
   - the fields of the target channel are not well formed (§3);
   - the claim's `actor` is not the `actor` of the target channel;
   - D holds no `Timeline Channel` with the actor and timeline of E (the delegate
     participant);
   - D's actor policy does not admit E as a delegated action.

   End.

3. **Delivery validation.** E is rejected from D, without reading T, when the
   delivery validation of Contracts on the target document fails (C08, C09): the
   target channel exists and is accepted, the named operation is declared on that
   channel, a required exact document version is D, and a declared request
   definition matches the request. The reason is the one Contracts gives that
   failure: `INVALID_TARGET_CHANNEL`, `INVALID_TARGET_OPERATION`,
   `STALE_DOCUMENT_PRECONDITION` or `INVALID_REQUEST`. End.

   Nothing else is checked before T is read. In particular the execution of E's
   operation and its handlers come only after T has decided E.

4. **The evidence timeline.** The processor reads T from its first entry in its
   authenticated chain order, not in order of arrival, and takes each entry X in
   turn, also an entry that precedes E:
   1. X is not attributed by T's provider to the target channel's `actor`: take
      the next entry.
   2. X is a well-formed Rejection Entry that names this document and E: E is
      rejected with the reason `AUTHORITY_EVIDENCE_REJECTED`. End.
   3. X is a well-formed Statement Entry: classify it by §8.
      - *Unfinished*: the processor finalises nothing, repeats the
        classification of X later, and does not take a later entry before it.
        End for now.
      - *Matching* with `verdict` `true`: E is admitted and executed under the
        target document's own rules. End.
      - *Matching* with `verdict` `false`: E is rejected with the reason
        `AUTHORITY_EVIDENCE_DENIED`. End.
      - *Skipped*: take the next entry.
   4. Otherwise (an entry of another type, or an entry of one of the two types
      that is not well formed, or a Rejection Entry that names another document
      or operation): take the next entry.

   When the processor has taken every entry of T it holds, E waits: the processor
   reads T again when T has grown. E also waits while the processor has no access
   to T, while T is not found at its provider, and while an entry of T cannot be
   admitted (§5). Absence, a read failure or a missing entry is never a decision.
   When the processor holds two contradictory chains of T, that is an integrity
   failure of the source (Coordination §9, §12): the processor retains the
   evidence and stops reading T, and decisions already recorded stand.

Later entries for an E that step 4 has decided are ignored, whatever they carry.

**Waiting.** The document processes its inputs in order-key order. While E waits,
no input after K is processed, also not an input of another participant. No rule
of this text ends the wait (§11).

**What is recorded.** A processor records a rejection with its reason. With a
decision of step 4 by a Statement Entry it also records that statement's
`statementCommitment`. Every processor records the same reason for the same E,
because the steps decide from D and from T's authenticated chain only. A processor
MUST NOT write a reason or a `statementCommitment` into the document state, so
neither changes the BlueId of any state.

## 8. The statement

### 8.1 Values

| Key | Content | Form |
|---|---|---|
| `channelType` | The BlueId of `Timeline Channel with Evidence` of this package | Plain id |
| `targetState` | The final id of D | Final id |
| `entry` | The final id of E | Final id |
| `mandateCommitment` | M, the text of `mandateCommitment` in E's claim | 64 hex characters |
| `mandateProcessorKey` | The `mandateProcessorKey` of the target channel in force before K, under which the signer verified the attestation | 64 hex characters |
| `statementCommitment` | `hex( SHA-256( salt || attestation signing input ) )` (§9) | 64 hex characters |
| `verdict` | Whether the mandate admits E (§9) | `true` or `false` |

### 8.2 Layout

The *statement* is the following ASCII text, with the seven keys in this order, no
white space, no byte before `{` and no byte after `}`. Each placeholder is the
value of its key in the form of §8.1:

    statement = '{"channelType":"'          <channelType>
                '","targetState":"'         <targetState>
                '","entry":"'               <entry>
                '","mandateCommitment":"'   <mandateCommitment>
                '","mandateProcessorKey":"' <mandateProcessorKey>
                '","statementCommitment":"' <statementCommitment>
                '","verdict":'              <verdict>
                '}'

The layout is fixed text, not any JSON with this meaning: another key order, a
space, an escape sequence, an upper-case hex digit or a further key is not a
statement. No value can hold a quotation mark or a character JSON escapes, so a
byte string matches the layout in at most one way. The fixed text is 130 bytes,
so a statement is 422 to 479 bytes long.

### 8.3 Signature and entry bytes

    statement signing input = UTF8( "blue.private-mandates.statement" ) || LF || statement
    signature               = Ed25519( statement signing input )      64 bytes, R followed by S
    entry bytes             = statement || signature

The signature is pure Ed25519 (RFC 8032) with the signer's key, accepted by the
rule of §10.2. The entry bytes have no length field and no separator; they are
486 to 543 bytes long, and the `statement` text of a Statement Entry, their
canonical base64, is 648 to 724 characters long.

### 8.4 Classification of a Statement Entry

The processor decodes the `statement` text into bytes B and classifies the entry
with the key `statementSignerKey` of the target channel in force before K, which
is a well-formed key (§7 step 2). The entry is *matching* only if all hold:

1. B is 486 to 543 bytes long;
2. the bytes of B before its last 64 are a statement in the layout of §8.2, with
   each value in its form of §8.1;
3. the five comparisons below hold, each as a text, byte for byte;
4. the last 64 bytes of B are a signature over the statement signing input that
   the rule of §10.2 accepts under `statementSignerKey`.

| # | Value of the statement | Equals |
|---|---|---|
| 1 | `channelType` | The BlueId of `Timeline Channel with Evidence` of this package |
| 2 | `entry` | The final id of E |
| 3 | `mandateCommitment` | The text of `mandateCommitment` in E's claim |
| 4 | `targetState` | The final id of D, the processor's own state |
| 5 | `mandateProcessorKey` | The `mandateProcessorKey` of the target channel in force before K |

The values compared with MUST come from the processor's own D and from E as
authenticated, never from the entry. `statementCommitment` and
`verdict` are compared with nothing. A matching entry carries its `verdict`.

An entry that is not matching is *skipped*: it is the same as no entry, is never a
denial and is never classified again. The classification is a function of B, E,
D and the channel; it uses no installed file, configuration or other host state,
and every processor reaches the same result.

The classification is *unfinished* only when the processor cannot complete a
check whose result it needs for a cause outside B and the key: it was stopped,
ran out of memory or could not read its own data. An implementation MUST NOT
turn an error that a library raises on particular bytes into an unfinished
classification: an exception or refusal of a base58, hex or point decoder or of a
signature routine on some input means that the condition it checks does not hold.
An implementation MUST NOT take a library's notion of a valid key or a valid
signature in place of §10 where the two differ. It MAY skip an entry whose
`statement` text is longer than 724 characters without decoding it.

### 8.5 Worked example

The ids are made up; `channelType` is not the BlueId of the channel type of this
package. The signer's key is the public key of test 1 of RFC 8032 §7.1 (secret key
`9d61b19d…7f60`) and the mandate processor's key that of test 2 (secret key
`4ccd089b…a6fb`).

    statementSignerKey   = d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a
    mandateProcessorKey  = 3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c
    channelType          = HhcFVPYPc2TvhvwwVmNAF6qUVBsU7Eex2APjDBUbNHHn
    targetState          = HK1RiEymW5yYZy6Y6cquarWa3ncst4EhanHeVvVB1cso
    entry                = HJTyj4yKfEkbZRULXBUmD1mbzibnTeERNVuYfyRXenur
    salt                 = 000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
    mandate (initial)    = rab1F73xd7pR5QjhCv1TFAtHpnq3hZPupgT6BTBZ54s
    attestation          = Fo3G5ADUwEeC5UgbC3UTH6WtxxrBQPknAaFQf6HuFUg7
    mandateCommitment    = 7dbabc5e4f68a135a0d7044a4bf56f4c6203a9636ac67fb9b5727240fc29279d
    statementCommitment  = c72990a40f78bc73e769a7bd0bd0cddb35371d9ec227f4ca1c5843f4b115066c
    verdict              = true

`mandateCommitment` is `hex( SHA-256( salt || mandate ) )` and
`statementCommitment` is `hex( SHA-256( salt || attestation signing input ) )`.
The mandate processor's signature over the attestation signing input is

    72de8f9158ecb778c717b9a44b904a5241af13b88000f23dcf998f647b4af4deafe6e572c6eeb885dca38b95860ff36ca177e4dc55b36f7f5cb1d45204481503

The statement (458 bytes, one line):

    {"channelType":"HhcFVPYPc2TvhvwwVmNAF6qUVBsU7Eex2APjDBUbNHHn","targetState":"HK1RiEymW5yYZy6Y6cquarWa3ncst4EhanHeVvVB1cso","entry":"HJTyj4yKfEkbZRULXBUmD1mbzibnTeERNVuYfyRXenur","mandateCommitment":"7dbabc5e4f68a135a0d7044a4bf56f4c6203a9636ac67fb9b5727240fc29279d","mandateProcessorKey":"3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c","statementCommitment":"c72990a40f78bc73e769a7bd0bd0cddb35371d9ec227f4ca1c5843f4b115066c","verdict":true}

    SHA-256( statement )   = 6ab8de30b9b129787c76f39f14d7e61c1cce3b051ac5c9f43adac3754c3817f6
    signature              = a38f01c27b070cc22f912931c553c34cd9d4234d08ffaf05658055ece929bc125fbb3ef2abc96b4d428737400f9f596e35154adb5edb3ab3498ce7fb3cd8ab02
    entry bytes            = 522 bytes
    SHA-256( entry bytes ) = 0057a36391b0dc43fcf1b8f7725e4c61b854fa2ed0c00994e2b54707f0df749e

The `statement` text of the Statement Entry (696 characters, one line):

    eyJjaGFubmVsVHlwZSI6IkhoY0ZWUFlQYzJUdmh2d3dWbU5BRjZxVVZCc1U3RWV4MkFQakRCVWJOSEhuIiwidGFyZ2V0U3RhdGUiOiJISzFSaUV5bVc1eVlaeTZZNmNxdWFyV2EzbmNzdDRFaGFuSGVWdlZCMWNzbyIsImVudHJ5IjoiSEpUeWo0eUtmRWtiWlJVTFhCVW1EMW1iemliblRlRVJOVnVZZnlSWGVudXIiLCJtYW5kYXRlQ29tbWl0bWVudCI6IjdkYmFiYzVlNGY2OGExMzVhMGQ3MDQ0YTRiZjU2ZjRjNjIwM2E5NjM2YWM2N2ZiOWI1NzI3MjQwZmMyOTI3OWQiLCJtYW5kYXRlUHJvY2Vzc29yS2V5IjoiM2Q0MDE3YzNlODQzODk1YTkyYjcwYWE3NGQxYjdlYmM5Yzk4MmNjZjJlYzQ5NjhjYzBjZDU1ZjEyYWY0NjYwYyIsInN0YXRlbWVudENvbW1pdG1lbnQiOiJjNzI5OTBhNDBmNzhiYzczZTc2OWE3YmQwYmQwY2RkYjM1MzcxZDllYzIyN2Y0Y2ExYzU4NDNmNGIxMTUwNjZjIiwidmVyZGljdCI6dHJ1ZX2jjwHCewcMwi+RKTHFU8NM2dQjTQj/rwVlgFXs6Sm8El+7PvKryWtNQoc3QA+fWW41FUrbXts6s0mM5/s82KsC

A second example, with a target state that is a member of a cyclic set. All
values are as above except:

    targetState          = HK1RiEymW5yYZy6Y6cquarWa3ncst4EhanHeVvVB1cso#3
    verdict              = false

The statement (461 bytes, one line):

    {"channelType":"HhcFVPYPc2TvhvwwVmNAF6qUVBsU7Eex2APjDBUbNHHn","targetState":"HK1RiEymW5yYZy6Y6cquarWa3ncst4EhanHeVvVB1cso#3","entry":"HJTyj4yKfEkbZRULXBUmD1mbzibnTeERNVuYfyRXenur","mandateCommitment":"7dbabc5e4f68a135a0d7044a4bf56f4c6203a9636ac67fb9b5727240fc29279d","mandateProcessorKey":"3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c","statementCommitment":"c72990a40f78bc73e769a7bd0bd0cddb35371d9ec227f4ca1c5843f4b115066c","verdict":false}

    SHA-256( statement )   = acfe6c2fa99a38da0ad161a6c91eb3cc6a4f1a26b360e4334b0fb973f59e3adc
    signature              = 49cc1e622f46723d147c6e21073e3e7433c1057569d9be82daafe82940e8c09e4f2a7f1b2f79dbb2c3a4913885b07d8d69fbee00d07ba93c81147ad316d53c0c
    entry bytes            = 525 bytes
    SHA-256( entry bytes ) = 83a90e5c2df0076e187e7e5746404e2fb8f5990e1982f38d7f3e79e4e666034e

The `statement` text (700 characters, one line):

    eyJjaGFubmVsVHlwZSI6IkhoY0ZWUFlQYzJUdmh2d3dWbU5BRjZxVVZCc1U3RWV4MkFQakRCVWJOSEhuIiwidGFyZ2V0U3RhdGUiOiJISzFSaUV5bVc1eVlaeTZZNmNxdWFyV2EzbmNzdDRFaGFuSGVWdlZCMWNzbyMzIiwiZW50cnkiOiJISlR5ajR5S2ZFa2JaUlVMWEJVbUQxbWJ6aWJuVGVFUk5WdVlmeVJYZW51ciIsIm1hbmRhdGVDb21taXRtZW50IjoiN2RiYWJjNWU0ZjY4YTEzNWEwZDcwNDRhNGJmNTZmNGM2MjAzYTk2MzZhYzY3ZmI5YjU3MjcyNDBmYzI5Mjc5ZCIsIm1hbmRhdGVQcm9jZXNzb3JLZXkiOiIzZDQwMTdjM2U4NDM4OTVhOTJiNzBhYTc0ZDFiN2ViYzljOTgyY2NmMmVjNDk2OGNjMGNkNTVmMTJhZjQ2NjBjIiwic3RhdGVtZW50Q29tbWl0bWVudCI6ImM3Mjk5MGE0MGY3OGJjNzNlNzY5YTdiZDBiZDBjZGRiMzUzNzFkOWVjMjI3ZjRjYTFjNTg0M2Y0YjExNTA2NmMiLCJ2ZXJkaWN0IjpmYWxzZX1JzB5iL0ZyPRR8biEHPj50M8EFdWnZvoLar+gpQOjAnk8qfxsveduyw6SROIWwfY1p++4A0HupPIEUetMW1TwM

## 9. The signer

The signer signs a statement for E only when all five conditions hold, in this
order. No processor repeats them; a statement asserts them.

1. *The attestation.* The signer holds a well-formed attestation (§6) and a
   signature over its attestation signing input that §10.2 accepts under the
   `mandateProcessorKey` of the target channel in force before K.
2. *The commitment.* The signer holds the salt, it is 32 bytes, and M equals
   `hex( SHA-256( salt || id ) )` for the final id of the attestation's
   `mandate` (§4).
3. *The position.* S is the mandate's state strictly before K. For every row of
   `position` the signer has established, from timelines it verified itself
   under Coordination, a complete prefix of the row's timeline (Coordination §5:
   an explicit guarantee or authenticated successor evidence) with
   `completeBefore > K.timestamp`, and the row's `lastEntry` is the last entry of
   that prefix whose order key is below K; a row without `lastEntry` states that
   there is no such entry. For the row of E's own timeline, if there is one, E
   itself establishes this: the row's `lastEntry` is the entry before E in that
   timeline's chain, absent when E is its first entry. The signer also
   establishes that `position` is complete (§6). Which providers it relies on is
   its own decision.
4. *Timers.* When `lastTimerFiring` is present, its order key is below K; when
   `nextTimerFiring` is present, K is below its order key. Both comparisons use
   the full order key (§1).
5. *The target.* D is the signer's own state of the target document strictly
   before K, and E is an entry the signer itself admitted.

**The verdict.** When the five hold, the signer evaluates S for E as follows. The
*grants* are the entries of the scope of S. A grant *applies* to E when its target
names the target channel and the operation of E and, if it pins an initial
document, that document's final id is the final id of the target document's
initial state. A grant has a document validation (`target.documentValidation`), a
request validation (`validation`), both or neither. Each validation is evaluated
as Mandates §4 and §6 define, with S as `$document`, D as `targetDocument` and the
request payload of E as `request`, and with its own fresh gas ledger of
10,000,000 gas. It has one of three outcomes:

- *passes*: the evaluation completes with the Boolean true;
- *fails*: it completes with any other result, or a pattern of the validation
  does not match;
- *no result*: it ends in an execution error, meets an invalid operand, exhausts
  its gas ledger, or its predicate is statically inadmissible; the validation
  node is not an object or is not well formed under the Language (it violates
  its schema, its types are not compatible, a type it uses is on its own
  inheritance chain, LANG-TYPE-CYCLE, or its content is invalid in another way
  the Language defines); or the evaluation needs content the signer does not
  hold.

The verdict is given by the first of these steps that applies, in this order:

1. S is not, by ancestry, `Operation Mandate` of the required Mandates
   publication, or `authorityPackage` is not the BlueId of that publication: no
   verdict.
2. The status of S is not `Active`: `false`.
3. S lacks `authorityHolderChannel` or `authorizedActorChannel`: no verdict.
4. The actor of E is not the actor of the `authorizedActorChannel` of S, or the
   actor of the target channel is not the actor of its `authorityHolderChannel`:
   `false`.
5. S lacks its scope: no verdict.
6. Otherwise the signer takes the grants of the scope in the order of their keys
   compared as sequences of UTF-16 code units, and for each in turn:
   - a grant that has no target gives no verdict;
   - a grant that does not apply is passed over;
   - otherwise the signer evaluates the document validation, if any, and then,
     only when that passed, the request validation, if any; a grant with a
     request validation does not pass when E carries no request payload, and
     that validation is not evaluated. A grant *passes* when each of its
     validations passes. The first grant that passes gives `true`. An evaluation
     with no result gives no verdict. A grant with a validation that fails does
     not pass, and the next grant is taken.

   In each case that ends the step, later grants are not looked at.
7. No grant passes: `false`.

For one S, D and E these steps give exactly the result Mandates gives for the
mandate named in clear: `true` where a processor of the mandate named in clear
admits E, `false` where it denies E, and no verdict where it stops with an error
or waits for content.

**No verdict, no statement.** When a condition fails or there is no verdict, the
signer signs nothing for E. This includes an M that matches no mandate the signer
holds. No rule requires the represented party to write a Rejection Entry then; E
waits (§7 step 4). The represented party MAY write a Rejection Entry for E at any
time, also where the signer could sign a statement; a Rejection Entry and a
statement with `verdict` `false` both reject E and differ in the recorded reason.

**The statement commitment.**

    statementCommitment = hex( SHA-256( salt || attestation signing input ) )

with the salt of M and exactly the bytes the mandate processor signed (§6).

**What the signer keeps.** For every statement it signs, the signer keeps the
salt, or the means to derive it again, the attestation and the mandate
processor's signature over it.

**Resources.** The Language sets no ceiling on the size, depth or count of valid
content (LANG-LIMIT), and this text sets none. The represented party MAY write a
Rejection Entry for an operation whose evaluation would exceed the signer's own
budget.

## 10. Keys and signatures

### 10.1 Well-formed key

An Ed25519 public key of the channel is well formed only if all hold:

1. it is 32 bytes written as 64 hex characters;
2. the bytes decode to a point of edwards25519 as RFC 8032 §5.1.3 states;
3. the encoding is canonical: the 255-bit little-endian y is below 2^255 − 19, and
   bit 255 is clear when x = 0;
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
not refused. The rule changes nothing in how Coordination verifies a provider's
signature.

*Note.* RFC 8032 decoding already fails in the cases of condition 3; they are
stated because common libraries decode leniently.

### 10.2 Accepted signature

This rule holds for the signature of an attestation and of a statement. A
signature is 64 bytes, R followed by S, over a message under a well-formed key A.
It is accepted only if all hold:

1. S, read as a little-endian integer, is below the group order L;
2. R decodes to a point of edwards25519 and is not of small order;
3. the encoding of [S]B − [k]A equals the 32 bytes of R, where B is the base point
   and k = SHA-512(R || A || message) read as a little-endian integer and reduced
   modulo L.

This is the equation without the cofactor, compared on encodings. A signature made
by a signer that follows RFC 8032 is accepted. The two signing inputs begin with
different domain texts, so neither signature can be taken for the other, also
when the two keys are equal.

## 11. Not decided in this preview

- A deadline, or another rule that ends the wait for an operation that the
  represented party does not decide (§7).
- Whether the reason of a rejection is visible to the document's contracts.
- Whether a processor records a second statement for the same E.
- How a participant supplies T, and how a channel added later gets its T.
- Skipping an entry of T that cannot be admitted (§5); today it blocks T.
- The retention period of what the signer keeps and the procedure of an inquiry.
