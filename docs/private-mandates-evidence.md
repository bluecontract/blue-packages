# Private mandates as an additive package

This is an unpublished candidate. It lets the participants of a document decide an
agent's operation without reading the mandate: the represented party's own document
processor writes a signed statement on the party's evidence timeline. The rules are
`blue-private-mandates/spec/private-mandates.md`; this page is informative.

## The package

`blue-private-mandates` `0.1.0-preview.3` (namespace `PrivateMandates`) requires the
unchanged `blue-coordination` `0.2.0-access-events.1` and `blue-mandates`
`0.3.0-preview.1`. No other source, archive, identity, lock or catalogue row
changes. It exports five types:

- `Timeline Channel with Evidence`: a `Coordination/Timeline Channel` with
  `evidenceTimeline`, `statementSignerKey` and `mandateProcessorKey`;
- `Statement Entry` (`statement`) and `Rejection Entry` (`document`,
  `operationEntry`): the two messages on an evidence timeline;
- `Mandate Commitment Authority`: a `Mandates/Authority` with the salted mandate
  commitment and no `mandate` reference;
- `Mandate State Attestation`: the document a mandate processor signs about one
  state of a mandate.

| Item | Version | BlueId |
| --- | --- | --- |
| Private Mandates package | 0.1.0-preview.3 | `6v2Jq5LbPxii6PRpLgm2kMThSEyXh6Xm6pDhqA7B3TeE` |
| Private Mandates protocol | | `zU7xbR9p3gPzj8wskiqnt96Usc7KC99pHmdZTmiWz6p` |
| Private Mandates rules | | `7wJyXWUoMaspNhHjHLm2LcKmbJmtNS6KDTPwpXXbEhF6` |
| `Timeline Channel with Evidence` | | `7Scp3gyZPWvcRD3xUy9X75tDpEYXoBkKBMkGDsXdhUnC` |
| `Statement Entry` | | `8bCBQ6uGZoFR5d682qMcTnoyF7PHt3RRWvQmqmp5N9a5` |
| `Rejection Entry` | | `DnNKC6N7iKuhEJmphcR4qm9hrEjmVSqeqTTChn1PCZwD` |
| `Mandate Commitment Authority` | | `BXwkeprUmcuP28mvCregJYoj5FgZzonevuMLNvkEukKe` |
| `Mandate State Attestation` | | `GMahBdjVzyTN5Mb2isyw6qXvbJUEQBGP6gLUJsS47kAi` |
| Coordination package (required, unchanged) | 0.2.0-access-events.1 | `4gmSjwn3DCYBVeDieXxuXgsPvvz2dU6ovFXnnuyv2RjA` |
| Coordination protocol (unchanged) | | `4YRV74QByZidyvspvbhZvx9Mfod16dHNCqCVbkKditGc` |
| Coordination rules (unchanged) | | `26NVkgkaq67dYNCRvZASHJvKQUQe1JM1Q3WcLK1NT5dG` |
| Mandates package (required, unchanged) | 0.3.0-preview.1 | `4kaMxybWTTeTpkzUtoYVUPk8dUo3HxKM5MG5joxN6LFL` |
| Mandates protocol (unchanged) | | `5c8ajquAmaKYGFf4LaZpc89DaNBa2QSDb8A4H7z1zwDk` |

`PACKAGES.json` is the authority for every current package identity and checksum.

The package adds types under its own rules and defines no transport type. A
Coordination type names the exact Coordination rules, so adding the evidence rules
there would give every Coordination type, and every package that embeds one, a new
identity. A document with an evidence channel therefore uses the transport types of
the unchanged Coordination publication, and a timeline provider needs no support
for this package:

| Transport type | BlueId, the same with and without evidence channels |
| --- | --- |
| `Coordination/Signed Timeline` | `EzfsjTUabtmb2KAMy7LHDrM9ffQzbx7JvXsGVSr6wh73` |
| `Coordination/Timeline Entry` | `G4dok8HLuBFPutTwD4h71y3y6ph7esA6qJGtDvoYAxKV` |
| `Coordination/Timeline Provider` | `AT9pX83cgt2mw9EPutC3dHKeWU8Ruj4TXB2cbTkBRxS7` |
| `Coordination/Provider Descriptor` | `kqnzQTYbwKbwvRTR4GT8P1WTfCY7EW6GKizMGT6VwNs` |
| `Coordination/Timeline Completeness Guarantee` | `2j2ZNTZnv3w6GC3XxoUG7pe35gVHJLaKqiHQjdHXAcHH` |
| `Coordination/Timeline Channel` | `GCd3gAEibsaZi1vdhFhTSfRch1HPruFcE1pgm9eAMKwy` |

A host learns that a document needs the protocol from the exact type identity of
`Timeline Channel with Evidence`, which names these rules; there is no separate
capability declaration.

## What is trusted

A statement is a signed assertion and nothing more. No processor other than the
signer checks the evaluation. The mandate processor answers for the attested state,
the signer for the evaluation; the signatures let each be held to what it stated
when the mandate is later disclosed in an inquiry, and `statementCommitment` ties a
statement to the exact bytes the mandate processor signed, so that a wrong state can
be told apart from a wrong evaluation of a rightly attested state. The other
participants accept the two keys by accepting the document: the represented party's
channel names them, and it changes only through the document's own program.

What stays trusted to the mandate processor: that S results from exactly the
entries of `position`, the completeness of `documents`, dependencies that are not a
channel contract (documents referred to without embedding, evidence timelines,
anything a contract reads when it runs), the two timer bounds and
`authorityPackage`. The attestation chain shows equivocation (two attestations with
one `previous` or one `sequence`) without the mandate's content, but not that every
attestation was handed over.

## Confidentiality and known limits

- **A shared timeline discloses the mandate.** A reader is granted whole timelines
  (Coordination §2.1, §7.1). If a timeline that a channel of the mandate binds is
  also bound by a channel of the target document, its readers see the mandate's
  operations in clear. Keep the mandate's timelines, the agent's and the holder's,
  separate from those of the target document; Mandates allows it (§2).
- **The agent can disclose what it knows.** Confidentiality towards the other
  participants holds only as far as the agent keeps it. Handing the agent ready
  values of M limits what it can disclose.
- **Linkage.** With one salt per mandate every operation under it carries the same
  M, and statements made from one attestation carry the same `statementCommitment`.
- **The represented party can stop the document.** With no deciding entry the
  document waits, also for the other participants, and an admitted agent can cause
  this with any M. While it waits, the party can read later entries of the others
  before it decides. There is no deadline.
- **A faulty mandate leaves the operation waiting.** The signer's verdict is the
  one Mandates gives for the mandate named in clear. Where a processor of a mandate
  named in clear stops the document with an error (a mandate fault, a predicate
  error or exhausted gas before a grant passes), the signer has no verdict and signs
  nothing, so the operation waits until the represented party writes a Rejection
  Entry. The verdict is the same; the consequence for the document differs.
- **Two statements.** A signer can sign `true` and `false` for one operation. The
  first deciding entry counts; the two signatures together are evidence against it.
- **What an observer learns.** `AUTHORITY_EVIDENCE_DENIED` tells that a signer
  stated a denial; `AUTHORITY_EVIDENCE_REJECTED` tells nothing about why. The time
  between the operation and the deciding entry is visible to the readers of T.
- **An entry on T that cannot be admitted** (an unresolvable or invalid reference)
  blocks T until timeline import can skip an entry it cannot read.
- **Ed25519 on the host.** A host that implements the protocol needs a working
  Ed25519 routine; without one every classification stays unfinished.

## What the schemas enforce

The Language schemas enforce the required fields, the key and commitment lengths,
at most two valued fields of the claim, and the attestation's required fields, id
lengths, at least one position row and the three parts of a timer bound. Everything
else is a native rule. The conformance tool below records the exact Language outcome
of each boundary case: schema rejections, values the schema admits and the processor
rejects or skips, references that leave admission incomplete, and member-id forms.

## Build and verify

With Java 21 and `BLUE_JAVA_CLASSPATH` set to the qualified Language runtime jars:

```sh
python3 tools/build_final_gas.py all
python3 tools/sync_catalogues.py --check
python3 tools/release.py check
python3 -m unittest discover -s tools -p 'test_release.py'
python3 tools/check_admission_scope.py   # Python 3.13
```

A change of the rules text needs these steps before the build: update
`spec/frozen.json`, build once to read the new rules BlueId, and put it in the
`specification` of every type of the package. No other package is rebuilt.

The native schema check:

```sh
mkdir -p reports/private-mandates/classes
"$JAVA_HOME/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" \
  -d reports/private-mandates/classes tools/PrivateMandatesTypesConformance.java
"$JAVA_HOME/bin/java" -cp "reports/private-mandates/classes:$BLUE_JAVA_CLASSPATH" \
  PrivateMandatesTypesConformance .
```

These checks cover Language schemas, archive integrity and reproducibility. Native
execution, the host capability, the signer and the verification of a statement are
qualified in Core. Semantic cards for the new type identities are produced by the
workflow described in [semantic cards](semantic-cards.md).
