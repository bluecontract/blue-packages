# Evidence channels and private mandates as additive packages

This is an unpublished candidate. It lets the participants of a document decide an
agent's operation from a proof on an evidence timeline instead of reading the mandate.

## What changed

Two packages are added on top of the unchanged current publications. Nothing else
changes: no existing source, archive, identity, lock or catalogue row.

`blue-coordination-evidence` `0.1.0-preview.2` (namespace `CoordinationEvidence`)
requires the exact `blue-coordination` `0.2.0-access-events.1` and exports four types
under its own rules, `spec/coordination-evidence.md`:

- `Timeline Channel with Evidence`: a `Coordination/Timeline Channel` with
  `evidenceTimeline`, `mandateProcessorKey` and `evidenceProfile`;
- `Evidence Profile`: base type of the profile a channel declares;
- `Proof Entry` (`receipt` required; `document` and `operationEntry` optional) and
  `Rejection Entry` (`document`, `operationEntry`): the two messages on an evidence
  timeline.

`blue-private-mandates` `0.1.0-preview.2` requires that package and the unchanged
`blue-mandates` `0.3.0-preview.1`, and adds
`RISC Zero Succinct Receipt Profile` (a `CoordinationEvidence/Evidence Profile` with
`programImageId`, `allowedProviders` and `receiverReleaseSha256`),
`Mandate Commitment Authority` (a `Mandates/Authority` with the salted mandate
commitment and no `mandate` reference) and `Mandate State Attestation`, the
document a mandate processor signs about one state of a mandate: its BlueId is
signed, and the attestations of one mandate form a hash chain. The normative rules
are the two `spec/` files.

| Item | Version | BlueId |
| --- | --- | --- |
| Coordination Evidence package | 0.1.0-preview.2 | `3oVELEaZZFY2qyqm2hE7EX78c1cbwp7zpd5PzAL5DA2F` |
| Coordination Evidence protocol | | `2Ng3dRWB1vYa6b1tKoj4AjYe2uXaCmJnSGM9XbGPFSX8` |
| Coordination Evidence rules | | `QRsRSvNRCCthA3W3wDGzAvBayR7dNMNC4g9RGiuBQWU` |
| `Timeline Channel with Evidence` | | `EJ74XzRGiBXcH9uj7LRtBsK7Cpc9KUx8K41hbGNJ93Qt` |
| `Evidence Profile` | | `G7gRXeu89Y6VR4oNhj711VK677o3QEhrphakKKtmjFFn` |
| `Proof Entry` | | `Gk1azozPa6SohYmDVh12hyjnH6bY6m8UjW8bxYPwvoRz` |
| `Rejection Entry` | | `AjBTUscaHD4CY9TCdjKrXhS2YbFYFenfWsMe21dsNWY` |
| Private Mandates package | 0.1.0-preview.2 | `ErMeenKWWo5h3E1eJZyWuxjNUrk9KRajZ4FaW5wkecet` |
| Private Mandates protocol | | `7FCEfX6NVAE1B5wxrzExy8jQkGK7rcxrVf5ThRD2i44` |
| Private Mandates rules | | `ATvszg5CCxLJT25Ke8525i63LUuf6Hux6mzVLc7LNycb` |
| `Mandate Commitment Authority` | | `GHPvv8vBopbbXKwVxbkpYaswWv76pAVnRvVR6RmBwN3c` |
| `RISC Zero Succinct Receipt Profile` | | `2YrJCcT5iJhYdRjB6bCrPki5gSXfx2pGjyUGWHDeKBsE` |
| `Mandate State Attestation` | | `8FvdQEVH9SMpwSdv6oxneucHjhfBxXexsA56gMNuBebe` |
| Coordination package (required, unchanged) | 0.2.0-access-events.1 | `4gmSjwn3DCYBVeDieXxuXgsPvvz2dU6ovFXnnuyv2RjA` |
| Coordination protocol (unchanged) | | `4YRV74QByZidyvspvbhZvx9Mfod16dHNCqCVbkKditGc` |
| Coordination rules (unchanged) | | `26NVkgkaq67dYNCRvZASHJvKQUQe1JM1Q3WcLK1NT5dG` |
| Mandates package (required, unchanged) | 0.3.0-preview.1 | `4kaMxybWTTeTpkzUtoYVUPk8dUo3HxKM5MG5joxN6LFL` |
| Mandates protocol (unchanged) | | `5c8ajquAmaKYGFf4LaZpc89DaNBa2QSDb8A4H7z1zwDk` |

`PACKAGES.json` is the authority for every current package identity and checksum.

## Why the evidence types are a separate package

A Coordination type names the exact rules it is defined by, and the builder requires
that reference to equal the package's protocol rules. Adding the evidence rules to
the Coordination rules text therefore gave every Coordination type a new identity:
`Signed Timeline`, `Timeline Entry`, the guarantees and the provider descriptors as
well as `Timeline Channel`, and with them `Mandates/Authority` and every package
that embeds Coordination. A timeline provider issues timelines with the transport
types of the edition in use, so a document on such a rebuilt edition rejected the
timelines the provider issues.

An earlier candidate on this branch did that (Coordination
`0.2.0-access-events.1.evidence.1` with 31 rebuilt dependants). It is withdrawn. The
root catalogue again selects Coordination `0.2.0-access-events.1` and its dependants
with their exact archives, and the evidence rules are the rules of
`blue-coordination-evidence`. A document with an evidence channel uses the transport
types of the unchanged Coordination publication:

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

The archives kept under `retained/pre-evidence-20261119/` by the withdrawn candidate
were byte for byte the archives the root catalogue selects again; that directory and
its pins are removed. The other retained archives are unchanged.

## How a host learns that a document needs these packages

From the exact type identities the document uses: `Timeline Channel with Evidence`
names the Coordination Evidence rules, and the package manifests name the protocol
identities the host must support natively. No separate capability declaration was
added. Installing the data grants no native support. A host without the Coordination
Evidence protocol must refuse a document that declares `Timeline Channel with
Evidence`; a host with it processes a document that declares no such channel as the
Coordination specification states.

## What the schemas enforce and what the processor decides

Enforced by the Language schema: on the channel, the three required fields and the
key length; on a value whose exact type is the RISC Zero profile, the three required
fields, at most three fields with a value, lengths and distinct provider keys; on the
commitment authority, the two required fields, at most two
fields with a value (so a `mandate` with a value is rejected) and the commitment
length.

Not enforced by the schema, and therefore native rules a Core implementation must
apply:

- **The profile is not typed by the schema.** Typing of `evidenceProfile` is
  structural: an untyped object, a `Signed Timeline` or a channel is admitted there.
  The rule that protects is native: the exact type must be a supported
  specialisation of `Evidence Profile`; anything else counts as a missing field.
- **The field sets are not closed.** The authority and the profile admit a further
  field that carries only a type (for example `mandate: {type: Mandates/Operation
  Mandate}`) or is a reference that resolves. The processor requires the exact
  field set; for the authority a wrong field set is an immediate rejection of the
  operation. A claim the schema does reject makes the whole timeline entry
  inadmissible, which is existing Coordination behaviour.

Open by design: `Proof Entry` and `Rejection Entry` name their fields and constrain
nothing. The processor checks the field set and form and skips an entry that is not
well formed; a skipped entry never causes a wait or a halt of its own.

`document` and `operationEntry` name the document and the operation entry by
content BlueId. In a `Rejection Entry` they are required and are its content. In a
`Proof Entry` they are optional and are an advisory hint with no force: every Proof Entry is classified by the
public output of its proof, and a proof is never skipped because the hint names
something else. They are declared as an `Operation Request` declares `document`: free
fields with no type. Naming is decided by the BlueId of the field node, never by the
wire form: a reference and the same content written in full are the same entry.
An evidence timeline serves exactly one document (two channels of that document may
share it) and its readers are that document's participants, so the named content
resolves for them, possibly after a wait for the operation entry.

Known limit: a `{blueId: …}` value anywhere in an entry, in any field at any depth,
is opened by Language admission. If its content cannot be obtained, admission of the
entry is incomplete; a reference with other content beside `blueId`, or with a
`blueId` that is not a BlueId, is invalid. Such an entry blocks that evidence
timeline until timeline import can skip an entry it cannot read. The conformance
tool records these outcomes with their exact failure kinds.

| Value | Outcome decided natively |
| --- | --- |
| `mandateProcessorKey` or a provider key that is not a well-formed key: not 64 characters `0-9a-f`, not a point of edwards25519, not canonically encoded, or one of the eight small-order encodings | The channel lacks that field: operations under a commitment authority on it are rejected from the document state |
| `programImageId` or `receiverReleaseSha256` that is not 64 characters `0-9a-f` | Same |
| `receiverReleaseSha256` that is not the SHA-256 of the release manifest the host has installed, or an installed build that the manifest does not list | The host does not implement the declared profile and refuses the document where the channel is declared |
| `allowedProviders` not strictly ascending by key bytes; a profile with a further field | Same |
| `evidenceProfile` whose exact type is not a supported specialisation of `Evidence Profile` | Same |
| A commitment authority whose fields are not exactly `actor` and `mandateCommitment`, or whose `mandateCommitment` is not 64 characters `0-9a-f` | The operation is rejected from the document state, without reading the evidence timeline |
| An attestation with a further field, or not in its canonical construction | Not reproducible by the proof, so no proof can be made with it; other verifiers must check the exact field set |
| An entry of one of the two types that is not well formed; a Rejection Entry that does not name this document and the operation | The entry is skipped |
| A Proof Entry whose `document` or `operationEntry` names something else, or that has neither | Classified by its public output like every other; the hint changes nothing |
| A proof whose `targetState` or `entry` is not the BlueId of the processor's own state before the operation, or of the operation | Skipped as mismatching. The proof shows neither that the state is valid nor that the entry is a valid entry, and its verification does not check them: they are premises |
| A matching proof with a denying verdict; a considered Rejection Entry | The operation is rejected with the reason `AUTHORITY_EVIDENCE_DENIED`, respectively `AUTHORITY_EVIDENCE_REJECTED`, the same on every processor. A rejection decided from the document state carries neither |
| A validation node of the mandate that is not well formed under the Language, a type inheritance cycle included, with no certified row | No proof can be made; the refusal is final and the party ends the wait with a Rejection Entry |
| A proof that would exceed the represented party's proving budget | The party may write a Rejection Entry; the rules set no ceiling of their own |
| A grant whose predicate ends in an error, gives a non-Boolean result or is statically inadmissible | That grant does not match; the other grants are tried |
| Exhausted gas in a predicate, unless an earlier grant already passed; a fault of the mandate itself, a grant without target included | "The mandate does not admit": the operation is rejected and the document continues. A deliberate difference from mandates named in clear |
| A grant that applies and needs content that cannot be supplied | No proof can be made in either grant order; the party ends the wait with a Rejection Entry |
| A receipt that is not the one canonical encoding, or that fails or faults while decoded or verified | Not a proof: the entry is skipped, never retried. All processors use a build of the pinned release whose manifest hash the profile carries; the five comparisons of the public output are the processor's own |
| The `statementCommitment` of the deciding proof | Recorded with the decision; compared with nothing |

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
capability and proof verification are qualified in Core.

## Fixed names and encodings

Type names, field names and encodings of the two rules texts are fixed in
`0.1.0-preview.2`: the entry fields and the proof as canonical base64 text; the
commitment `M = hex(SHA-256(salt || id text))`; the image identifier, the receiver
release hash and the digests as 64 lower-case hexadecimal characters; the layout and
domain text of the mandate processor's signed message; the seven keys of the public
output; the rule by which the proving program re-derives a reused validation result
from the target state. Changing one gives new exact identities. Not decided: how a
program is identified in the attestation (`mandateProgram`, `approvedProgram`) and
the byte-exact entry grammar; see the last section of each rules text.
