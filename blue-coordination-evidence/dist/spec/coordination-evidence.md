# Coordination evidence channels: proof timelines for operations decided by evidence

Protocol name: `Coordination / timeline channels with evidence/1`
Package namespace: `CoordinationEvidence`
Release status: Core Java integration preview, 19 November 2026

This is an additive Coordination edition. It is published as a separate package
that requires the exact Coordination publication it was built against. The frozen
Coordination transport, access, ordering and admission rules are unchanged, and no
existing Coordination type identity changes. A document that does not declare a
channel of this edition is processed exactly as before.

Names and grammar details marked *provisional* are working choices of this preview.
Changing one of them produces new exact type identities and a new protocol identity.

Terms: E is an operation entry and K its full Coordination input key (timestamp,
source timeline, entry). D is the state of the target document strictly before E.
T is the proof timeline named by the channel the operation is performed on.

## 1. Scope and layer boundary

A participant may be represented by agents whose authority the other participants
cannot read. For such a participant the document's channel names where the decisions
about those operations appear (T), whose signature on a private authority state the
participant accepts, and under which published rules a piece of evidence is checked.
This edition defines that channel, the two entry kinds on T, and how a processor
reads T. It does not define any authority type or any evidence profile. Those are
defined by packages whose protocol requires this one.

An operation is *evidence-decided* when its authority claim (`onBehalfOf`) has a type
that a supported protocol requiring this edition defines as decided from T. This
edition alone defines no such type. Direct operations and operations under an
authority that names its mandate keep their existing Coordination and Mandates rules.

A processor MUST explicitly support this exact package and protocol. Loading the
definitions for inspection is not support. A host that does not support this
protocol, or the protocol of the profile a channel declares, MUST refuse the document
rather than process it differently. It refuses where the channel is declared: for a
channel in the initial document it processes nothing; for a channel added later it
stops at the entry that adds the channel. It MUST NOT treat the channel as a plain
`Coordination/Timeline Channel`.

## 2. Exported types

| Type | Kind | Purpose |
|---|---|---|
| Timeline Channel with Evidence | `Coordination/Timeline Channel` | Participant channel that also names T, the mandate processor key and the evidence profile |
| Proof Entry | message of a Timeline Entry on T | Carries one whole proof |
| Rejection Entry | message of a Timeline Entry on T | States that one operation is not to be processed in one document |

## 3. The channel

`Timeline Channel with Evidence` inherits `timeline` and `actor` from
`Coordination/Timeline Channel` and adds three required fields:

| Field | Content |
|---|---|
| `proofTimeline` | The proof timeline T of this channel, a `Coordination/Signed Timeline` |
| `mandateProcessorKey` | The public key whose signature on a private authority state the participant accepts, a `Coordination/Ed25519 Public Key` (*provisional*: the key type) |
| `evidenceProfile` | The published evidence profile under which evidence for this channel is checked (*provisional*: the field name). Its type is defined by the profile's own package and selects the native part a host must implement; its content carries the profile's data |

Rules:

1. The channel is an ordinary input source for its `timeline`, exactly as a
   `Coordination/Timeline Channel`. T is not an input source (§4).
2. The three fields are read from the document state strictly before K, like every
   other part of the document.
3. The three fields are fixed for the life of the document. *Provisional* placement
   of the rule: a processor rejects an entry that would change any of the three
   fields of an existing channel; a channel added later with all three fields is
   accepted.
4. Same-provider rule: T MUST be at the provider of the channel's `timeline`.
5. There is one T per participant channel, whatever the number of representatives.
   A representative writes on its own timeline; the operation is performed on the
   participant's channel, and that channel names T.
6. Each participant declares the three fields of its own channel. The other
   participants accept them by accepting the document.

A participant with no representatives may use a plain `Coordination/Timeline Channel`.

## 4. What the proof timeline is to the processor

T delivers no input to the document and takes no part in establishing which entries
are safe to process: it is not part of completeness, candidate selection or ordering.
There is no requirement on T before the document starts. T is read only to decide an
evidence-decided operation performed on the channel that names it.

No timestamp of T is compared with a timestamp of any other timeline. An entry on T
may appear at any time; only its place in T's own authenticated chain matters.

Anything may be written on T. Whoever can write on T was allowed to by the
participant; the processor does not ask who that is. Reader access to T uses T's own
Timeline Access document, handled like those of the document's other timelines.

## 5. Entries on the proof timeline

Both kinds are the `message` of an ordinary `Coordination/Timeline Entry` on T.

**Proof Entry.** The whole proof is the content of the entry, so an authenticated
entry never lacks its proof. It refers to E and to the document only through the
proof's public output, as the declared profile defines.

| Field | Content |
|---|---|
| `receipt` | The complete proof in the single encoding admitted by the declared profile, as canonical base64 text: RFC 4648 standard alphabet, with padding, no line breaks or other characters (*provisional*: field name and text encoding) |

**Rejection Entry.** "E is not to be processed in this document", with no proof.

| Field | Content |
|---|---|
| `documentId` | The document's initial BlueId, the same for every participant, as text |
| `operationEntry` | The BlueId of the operation entry E, as text (*provisional*: the field name) |

A rejection needs no signature of its writer. It counts because it is on the
participant's timeline. No size limit is imposed on an entry by these rules.
Conformance of an entry is decided from the entry alone, so every processor decides
it alike. The byte-exact grammar is not final in this preview (§8).

## 6. Deciding an evidence-decided operation

**Immediate rejection from the document state.** E is rejected at once, without
reading T, when at the position of E:

- the channel E is performed on lacks any of the three fields; this includes a plain
  `Coordination/Timeline Channel`;
- T is at another provider than the channel's `timeline`.

Every processor reads the same document state at that position, so the rejection is
deterministic.

**Considered entries.** Otherwise the processor considers an entry on T for E only
if both hold:

1. T's provider attributes the entry to the channel's `actor`;
2. the entry is a Proof Entry that the declared profile classifies as a matching
   proof for E, or a Rejection Entry whose `documentId` is this document's initial
   BlueId and whose `operationEntry` is the BlueId of E.

Everything else on T is skipped. A skipped entry is the same as no entry.

| What is on T | Treatment |
|---|---|
| An entry attributed to another actor | Skipped |
| An entry that conforms to neither entry kind | Skipped |
| A conforming Proof Entry whose verification completes with "invalid" | Skipped |
| A proof that verifies but that the profile classifies as mismatching | Skipped as mismatching; never a denial |
| A rejection for another document, without `documentId`, or for another operation | Skipped |
| A matching proof for E | Considered; carries its verdict |
| A rejection naming this document and E | Considered; E is rejected in this document only |

**Which entry decides.** The first considered entry for E in T's authenticated
chain, counted from the beginning of the chain, also when it precedes E. Later
entries for the same E are ignored, whatever their verdict. T is read from its first
entry in chain order, not in the order in which data happens to arrive.

A matching proof with an admitting verdict lets E proceed to the target document's
own rules. A matching proof with a denying verdict, or a considered rejection,
rejects E.

**When there is no decision.**

| Situation | What the processor does |
|---|---|
| No considered entry for E on T | Waits. Absence of an entry is never a denial |
| No access to T | Waits. A local read failure of T is never a denial. With access it reads T from the start |
| Verification of a conforming Proof Entry was interrupted locally | Retries and finalises nothing. It does not pass over that entry to a later one. A local resource limit may only interrupt and retry; it is never part of a classification |
| The processor holds two chains of T | Halts; earlier results stand |

**Waiting.** The document processes inputs in full-key order and stops at the first
unresolved evidence-decided operation. A later operation, also of another
participant, is not processed before it. There is no deadline in this edition.

## 7. Host support and compatibility

The protocol identity of this package is the capability a host must support for a
document that declares `Timeline Channel with Evidence`. Supporting it does not
change the processing of any document that declares no such channel. Earlier
Coordination publications remain selectable and their documents keep their runtime.

## 8. Not decided in this preview

- The name of the profile field and of the entry fields, and the byte-exact entry
  grammar including the text encoding of the proof.
- Where the fixed-for-life rule is finally placed (§3 rule 3).
- A `proofTimeline` that does not exist at the provider: reject or wait.
- Whether two channels may share one T.
- Whether the reason for a rejection is visible to the document's contracts.
- How a participant supplies T, and how the others consent to a channel added later.
