# Evidence channels and private mandates as additive packages

This is an unpublished candidate. It lets the participants of a document decide an
agent's operation without reading the mandate: the represented party's own document
processor writes a signed statement on the party's evidence timeline.

## What the two packages are

Two packages sit on top of the unchanged current publications. Nothing else
changes: no existing source, archive, identity, lock or catalogue row of
Coordination, Mandates, Time or any other package.

`blue-coordination-evidence` `0.1.0-preview.3` (namespace `CoordinationEvidence`)
requires the exact `blue-coordination` `0.2.0-access-events.1` and exports four types
under its own rules, `spec/coordination-evidence.md`. It is neutral about the form
of the evidence:

- `Timeline Channel with Evidence`: a `Coordination/Timeline Channel` with
  `evidenceTimeline` and `evidenceProfile`;
- `Evidence Profile`: base type of the profile a channel declares;
- `Proof Entry` (`receipt` required; `document` and `operationEntry` optional) and
  `Rejection Entry` (`document`, `operationEntry`): the two messages on an evidence
  timeline. The names `Proof Entry` and `receipt` are kept whatever the evidence is.

`blue-private-mandates` `0.1.0-preview.3` requires that package and the unchanged
`blue-mandates` `0.3.0-preview.1`. It has one rules text, `spec/private-mandates.md`,
and three types:

- `Mandate Commitment Authority`: a `Mandates/Authority` with the salted mandate
  commitment and no `mandate` reference;
- `Mandate State Attestation`: the document a mandate processor signs about one
  state of a mandate; its BlueId is signed, and the attestations of one mandate form
  a hash chain;
- `Signed Statement Profile`: a `CoordinationEvidence/Evidence Profile` with the
  two fields `statementSignerKey` and `mandateProcessorKey`. Under it the `receipt` of a `Proof Entry` is a fixed
  ASCII statement followed by a 64-byte Ed25519 signature of the represented
  party's document processor.

The mandate processor answers for the attested state and the signer for the
evaluation. Every other processor decodes, checks one signature and makes five
comparisons of texts. A statement is a signed assertion and no more.

| Item | Version | BlueId |
| --- | --- | --- |
| Coordination Evidence package | 0.1.0-preview.3 | `92jurrzKryQ3KkrCo5r5rzXLZxzgz1oKFCuz7u913T1X` |
| Coordination Evidence protocol | | `H3puQP7A8zh9B6z7NXUTnpNu9hGPUfW8fxdCw8EqXtyk` |
| Coordination Evidence rules | | `ErvK9PC58CpUcUzdJRfuTQhrYyQdvXFdBrrvzYh4T2Vn` |
| `Timeline Channel with Evidence` | | `CboJK2cNdaboP5MW6xwM9sn6BuxBfbHDTLpMsprEhDqZ` |
| `Evidence Profile` | | `GJ3VeCJXPSSz3biDudF3eCB76vxJJrNDNhwLbYenHqi9` |
| `Proof Entry` | | `95KMR7eZ8Ma4tNeyBii6MHSWZYgRjZByUiTfWERBaDT6` |
| `Rejection Entry` | | `Bcke6mnURaC9ghLj1azZrYxPWnCUTWuDkX5xAYwHdUTg` |
| Private Mandates package | 0.1.0-preview.3 | `3d1PhdbiTvhse5NkyFBroM9AkwQrXdwtSNuev1aAZePW` |
| Private Mandates protocol | | `3cKx66R6qTMQB9pwtBL3U3vdbebH7TYHt8TBpir7Ehj8` |
| Private Mandates rules | | `FLaS74tzzjUgtoD7CunFM9d7mnx6u2VSiAje9VSL6Djq` |
| `Mandate Commitment Authority` | | `8LKNmiL8fsNHrbo6kamG8vH2Bon2T1padWUCyXCU2Fdo` |
| `Mandate State Attestation` | | `9aLeqrVyc51p9ipvNgQ8Vc1FWKXW6e2M9V2uU3iZh3Hh` |
| `Signed Statement Profile` | | `An3eAvv3yW8Sthj4FpMkJMacoLR61wSJ2ZBcEE1gwicu` |
| Coordination package (required, unchanged) | 0.2.0-access-events.1 | `4gmSjwn3DCYBVeDieXxuXgsPvvz2dU6ovFXnnuyv2RjA` |
| Coordination protocol (unchanged) | | `4YRV74QByZidyvspvbhZvx9Mfod16dHNCqCVbkKditGc` |
| Coordination rules (unchanged) | | `26NVkgkaq67dYNCRvZASHJvKQUQe1JM1Q3WcLK1NT5dG` |
| Mandates package (required, unchanged) | 0.3.0-preview.1 | `4kaMxybWTTeTpkzUtoYVUPk8dUo3HxKM5MG5joxN6LFL` |
| Mandates protocol (unchanged) | | `5c8ajquAmaKYGFf4LaZpc89DaNBa2QSDb8A4H7z1zwDk` |

`PACKAGES.json` is the authority for every current package identity and checksum.

## Earlier candidates on this branch

`0.1.0-preview.2` of the two packages (commit `3c75dd3`) decided an operation from a
zero-knowledge receipt of a proving program, with a profile type
`RISC Zero Succinct Receipt Profile`. That line is not developed further. Its
profile type, the fields of the attestation that served the proving program
(`certifiedNodes`, `timerRegistrations`, the two timer bounds as
`Coordination/Order Key`) and the corresponding rules are removed in
`0.1.0-preview.3`; the earlier state stays in the history of the branch.

## Why the evidence types are a separate package

A Coordination type names the exact rules it is defined by, and the builder requires
that reference to equal the package's protocol rules. Adding the evidence rules to
the Coordination rules text would give every Coordination type a new identity:
`Signed Timeline`, `Timeline Entry`, the guarantees and the provider descriptors as
well as `Timeline Channel`, and with them `Mandates/Authority` and every package
that embeds Coordination. A timeline provider issues timelines with the transport
types of the edition in use, so a document on such a rebuilt edition would reject
the timelines the provider issues. The evidence rules are therefore the rules of
`blue-coordination-evidence`, and a document with an evidence channel uses the
transport types of the unchanged Coordination publication:

| Transport type | BlueId, the same with and without evidence channels |
| --- | --- |
| `Coordination/Signed Timeline` | `EzfsjTUabtmb2KAMy7LHDrM9ffQzbx7JvXsGVSr6wh73` |
| `Coordination/Timeline Entry` | `G4dok8HLuBFPutTwD4h71y3y6ph7esA6qJGtDvoYAxKV` |
| `Coordination/Timeline Provider` | `AT9pX83cgt2mw9EPutC3dHKeWU8Ruj4TXB2cbTkBRxS7` |
| `Coordination/Provider Descriptor` | `kqnzQTYbwKbwvRTR4GT8P1WTfCY7EW6GKizMGT6VwNs` |
| `Coordination/Timeline Completeness Guarantee` | `2j2ZNTZnv3w6GC3XxoUG7pe35gVHJLaKqiHQjdHXAcHH` |
| `Coordination/Timeline Channel` | `GCd3gAEibsaZi1vdhFhTSfRch1HPruFcE1pgm9eAMKwy` |

All 54 Coordination exports, and every export of the other existing packages, keep
their identities. The conformance tool asserts the rows above and others.

## How a host learns that a document needs these packages

From the exact type identities the document uses: `Timeline Channel with Evidence`
names the Coordination Evidence rules, the channel's profile names the Private
Mandates rules, and the package manifests name the protocol identities the host
must support natively. No separate capability declaration was added. Installing the
data grants no native support. Whether a host implements a profile depends on the
profile's exact type alone. A host that does not implement it refuses the document
where the channel is declared, or where its profile is changed to such a type, and
finalises nothing; a host with it processes a
document that declares no such channel as the Coordination specification states.

## What the schemas enforce and what the processor decides

Enforced by the Language schema: on the channel, the two required fields; on a
value whose exact type is the Signed Statement Profile, the two required fields, at
most two fields with a value and the key lengths; on the
commitment authority, the two required fields, at most two fields with a value (so
a `mandate` with a value is rejected) and the commitment length; on the attestation,
the required fields, the lengths of the id texts, a position of at least one row
and the three parts of a timer bound.

Not enforced by the schema, and therefore native rules a Core implementation must
apply:

- **The profile and the keys are not fully checked by the schema.** The schema makes
  a channel without one of its two fields invalid content. What it does not check
  is native: the evidence timeline (by ancestry a `Signed Timeline`, at the
  channel's provider, providers compared by BlueId), the profile and the key rule
  for the two keys of the profile. Typing of `evidenceProfile` is structural: an untyped object, a `Signed
  Timeline` or a channel is admitted there. The native rule has three cases, decided
  from the exact type first: no profile type (not well formed), a profile type the
  host does not implement (the host refuses), a profile type the host implements
  (the content is checked). A document may hold a channel whose fields are not well
  formed; an operation on it with a commitment authority is rejected from the
  document state and the document continues. So is such an operation on a channel
  whose profile's exact type is not `Signed Statement Profile` (compared exactly,
  not by ancestry).
- **The document state decides first.** An operation the channel's lifetime has
  already consumed is not processed again: it is skipped, not rejected (Contracts
  C10, C12). Then the ordinary validation of an operation, which is exactly the
  delivery validation of Contracts (C08, C09: target channel, declared operation,
  exact document version, request pattern), runs before the evidence timeline is
  read; an operation that fails it is rejected at once. The operation's execution,
  its handlers, comes only after the evidence timeline decided it.
- **Changes of a channel are the document's own.** This package adds no rule about
  changing a channel's fields or type. A change happens only through the document's
  program, and Contracts decides whether the resulting document is valid and whether
  a retyping is permitted (C25, C26).
- **The field sets are not closed.** The authority, the profile and the attestation
  admit a further field that carries only a type or is a reference that resolves.
  The processor requires the exact field set; for the authority a wrong field set is
  an immediate rejection of the operation. A claim the schema does reject makes the
  whole timeline entry inadmissible, which is existing Coordination behaviour.

Open by design: `Proof Entry` and `Rejection Entry` name their fields and constrain
nothing. The processor checks the field set and form and skips an entry that is not
well formed; a skipped entry never causes a wait or a halt of its own.

Known limit: a `{blueId: …}` value anywhere in an entry, in any field at any depth,
is opened by Language admission. If its content cannot be obtained, admission of the
entry is incomplete; a reference with other content beside `blueId`, or with a
`blueId` that is not a BlueId, is invalid. Such an entry blocks that evidence
timeline until timeline import can skip an entry it cannot read, and with it the
document at the first operation decided from that timeline. The conformance tool
records these outcomes with their exact failure kinds.

| Value | Outcome decided natively |
| --- | --- |
| `mandateProcessorKey` or `statementSignerKey` that is not a well-formed key: not 64 characters `0-9a-f`, not a point of edwards25519, not canonically encoded, or one of the eight small-order encodings | An operation with a commitment authority on that channel is rejected from the document state, without reading the evidence timeline; the document continues |
| A profile with a further field | Same |
| `evidenceProfile` with no profile type | Same |
| `evidenceProfile` whose exact type is a profile the host does not implement | The host refuses the document where the channel is declared, or where its profile is changed to such a type, and finalises nothing |
| A commitment authority on a channel whose profile the host implements but whose exact type is not `Signed Statement Profile` (also a type that extends it) | The operation is rejected from the document state, without reading the evidence timeline |
| A commitment authority whose fields are not exactly `actor` and `mandateCommitment`, or whose `mandateCommitment` is not 64 characters `0-9a-f`; a claim whose exact type is not `Mandate Commitment Authority` | The operation is rejected from the document state, without reading the evidence timeline |
| An entry of one of the two types that is not well formed; a Rejection Entry that does not name this document and the operation | The entry is skipped |
| A Proof Entry whose `document` or `operationEntry` names something else, or that has neither | Decided by its statement like every other; the hint changes no classification. Written as a reference, the hint is opened at admission, and one that cannot be resolved blocks the evidence timeline (known limit); written as id texts it needs no resolution |
| A `receipt` whose content is not a Text value, also when written as a reference to such content | The entry is not well formed and is skipped. A reference to a Text value is that Text and gives the same entry identity |
| A Rejection Entry | Names the document and the operation by final id: a member id `MASTER#i` for a member of a cyclic set, the plain id otherwise |
| A `receipt` whose bytes are not a statement in the fixed layout, or whose signature the rule does not accept | Not a statement: the entry is skipped, never retried, the same on every host |
| A statement whose `profile`, `entry`, `mandateCommitment`, `targetState` or `mandateProcessorKey` differs from the processor's own value | Skipped as mismatching; never a denial |
| A matching statement with `verdict` `false`; a considered Rejection Entry | The operation is rejected with the reason `AUTHORITY_EVIDENCE_DENIED`, respectively `AUTHORITY_EVIDENCE_REJECTED`, the same on every processor. A rejection decided from the document state carries neither |
| The reason, and the `statementCommitment` of the deciding statement | Recorded with the decision, compared with nothing, and never written into the document state |
| An attestation with a further field, an id in a form its position does not allow, or lists out of order | Not used by the signer; whoever checks an attestation checks the exact field set |

Semantic cards for the new type identities are not part of this change; they are
produced by the workflow described in [semantic cards](semantic-cards.md).

## Build and verify

With Java 21 and `BLUE_JAVA_CLASSPATH` set to the qualified Language runtime jars:

```sh
python3 tools/build_final_gas.py all
python3 tools/sync_catalogues.py --check
python3 tools/release.py check
python3 -m unittest discover -s tools -p 'test_release.py'
python3 tools/check_admission_scope.py   # Python 3.13
```

A change of the rules text of one of the two packages needs these steps before the
build: update its `spec/frozen.json`; build once to read the new rules BlueId and put
it in the `specification` of every type of that package; rebuild
`blue-coordination-evidence` before `blue-private-mandates`. No other package is
rebuilt.

The native schema check:

```sh
mkdir -p reports/private-mandates/classes
"$JAVA_HOME/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" \
  -d reports/private-mandates/classes tools/PrivateMandatesTypesConformance.java
"$JAVA_HOME/bin/java" -cp "reports/private-mandates/classes:$BLUE_JAVA_CLASSPATH" \
  PrivateMandatesTypesConformance .
```

These checks cover Language schemas, archive integrity and reproducibility. They do
not qualify native execution: admission from an evidence timeline, the host
capability, the signer and the verification of a statement are qualified in Core.

## Fixed names and encodings

Type names, field names and encodings of the two rules texts are fixed in
`0.1.0-preview.3`: the entry fields and the evidence as canonical base64 text; the
commitment `M = hex(SHA-256(salt || id text))` with a salt of 32 bytes; the layout of
a statement, its domain text and the 64-byte signature after it; the layout and
domain text of the mandate processor's signed message; keys and digests as 64
lower-case hexadecimal characters; ids as final ids, plain or member ids, with a member index of at most 9 digits. Changing one gives new exact
identities. Not decided: how a program is identified in the attestation
(`mandateProgram`, `approvedProgram`), a deadline for an undecided operation, and
the byte-exact entry grammar; see the last section of each rules text.
