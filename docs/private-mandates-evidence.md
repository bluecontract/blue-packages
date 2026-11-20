# Coordination edition with evidence channels, and private mandates

This is an unpublished candidate. It lets the participants of a document decide an
agent's operation from a proof on an evidence timeline instead of reading the mandate.

## What changed

There is one developed Coordination. Its new edition `0.2.0-access-events.1.evidence.1`
descends from `0.2.0-access-events.1` and adds section 14 to `spec/coordination.md`
with four exported types:

- `Timeline Channel with Evidence`: a `Coordination/Timeline Channel` with
  `evidenceTimeline`, `mandateProcessorKey` and `evidenceProfile`;
- `Evidence Profile`: base type of the profile a channel declares;
- `Proof Entry` (`receipt`, `document`, `operationEntry`) and `Rejection Entry`
  (`document`, `operationEntry`): the two messages on an evidence timeline.

`blue-private-mandates` `0.1.0-preview.1` stays a separate package. It requires this
Coordination edition and the Mandates publication built on it, and adds
`RISC Zero Succinct Receipt Profile` (a `Coordination/Evidence Profile`; its
`factsRule` is `FULL(D)` or `MERKLE(FULL(D))`) and
`Mandate Commitment Authority` (a `Mandates/Authority` with the salted mandate
commitment and no `mandate` reference). The normative rules are the two `spec/` files.

| Item | Version | BlueId |
| --- | --- | --- |
| Coordination package | 0.2.0-access-events.1.evidence.1 | `EfD9Evsy8Uk37sgVW5FoZ7ZHYETETeyDZwKtuCa827vC` |
| Coordination protocol | | `5TH6F74QEEVgL6X2dr6TyqLGkHFCHUff56Z5iTw5Phmc` |
| Coordination rules | | `9MdKsAApwjLjFXTw75necZ5XPuY4o5M7SX2bF5zNrwij` |
| Mandates package | 0.3.0-preview.1.evidence.1 | `844HpnaEGPgJDkaMBL62MMRRSqF1pByLKEKaRA1HAbp1` |
| Mandates protocol | | `GxCcpduSLDenAhsiDD2RLMTR1BjSDVFVchj3WNAzs6Yz` |
| Time package | 0.2.0-gas10m.1.finalgas.1.evidence.1 | `E5DJ6N9ZiTWxdY4cyT7G9R1iMxJezuytic5Q5b8hAjte` |
| Time protocol | | `4E6oq67afbGES738jLoac61UQD2wCWtWuXMNLaV3DS5m` |
| Private Mandates package | 0.1.0-preview.1 | `WnxS6HtCaR8gSXv2iMZLQcMZcAvGNLuwKv4J14WHxcd` |
| Private Mandates protocol | | `5QxEHeuURJgR8JmenYvCKpS5LZGMoTp2YZwGx8ZnqAW6` |
| Private Mandates rules | | `EpB7Vs65aUeM1kHCUqbG9tHYcvVzLE22ApYVo9RsNvN4` |

`PACKAGES.json` is the authority for every current package identity and checksum.

## Why every dependant was rebuilt

A Coordination type names the exact rules it is defined by, and the builder requires
that reference to equal the package's protocol rules. New rules text therefore gives
every Coordination type a new identity, `Timeline Channel` included, and every
package that embeds Coordination a new package identity. Coordination and its 31
dependants carry the version suffix `.evidence.1`; their authored business
definitions are unchanged. The Mandates and Time rules texts are unchanged; their
protocol identities are new because they require the new Coordination protocol.

Two authored files pin exact function identities that include a Coordination type,
and were re-pinned from native package records, not computed:
`clause-documents/types/admission-step-functions.blue` (`accessRecordsValid`) and,
through `tools/refresh_reseller_composition.py`, `clause-documents/types/preparation-plan.blue`
and the Reseller bootstrap composition.

## Earlier editions

The root catalogue selects one edition, now this one. The 32 archives of the
previous edition (Coordination and its 31 dependants) are retained byte for byte
under `retained/pre-evidence-20261119/<package>/package.bluepkg` and pinned in
`PACKAGE-SOURCES.json` under `retainedArchives`; `tools/release.py check` verifies
them and release bundles carry them as `retained-data`. Documents on an earlier
edition keep their runtime. The nine packages that do not embed Coordination are
unchanged. `blue-coordination-evidence`, an earlier unpublished layered candidate,
was removed.

## How a host learns that a document needs this edition

As for every edition: from the exact type identities the document uses. They name
the Coordination rules, and the package manifest names the protocol identity the
host must support natively. No separate capability declaration was added.
Installing the data grants no native support. A host without this protocol must
refuse a document that declares `Timeline Channel with Evidence`; a host with it
processes a document that declares no such channel as sections 1–13 state.

## What the schemas enforce and what the processor decides

Enforced by the Language schema: on the channel, the three required fields and the
key length; on a value whose exact type is the RISC Zero profile, the three required
fields, at most three fields with a value, lengths, distinct provider keys and the
facts rule value; on the commitment authority, the two required fields, at most two
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
content BlueId and are declared as an `Operation Request` declares `document`: free
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
| `mandateProcessorKey`, `programImageId` or a provider key that is not 64 characters `0-9a-f` | The channel lacks that field: operations under a commitment authority on it are rejected from the document state |
| `allowedProviders` not strictly ascending by key bytes; a profile with a further field | Same |
| `evidenceProfile` whose exact type is not a supported specialisation of `Evidence Profile` | Same |
| A commitment authority whose fields are not exactly `actor` and `mandateCommitment`, or whose `mandateCommitment` is not 64 characters `0-9a-f` | The operation is rejected from the document state, without reading the evidence timeline |
| An entry of one of the two types that is not well formed, or that does not name this document and the operation | The entry is skipped |
| A grant whose predicate ends in an error, gives a non-Boolean result or is statically inadmissible | That grant does not match; the other grants are tried |
| Exhausted gas in a predicate, unless an earlier grant already passed; a fault of the mandate itself, a grant without target included | "The mandate does not admit": the operation is rejected and the document continues. A deliberate difference from mandates named in clear |
| A grant that applies and needs content that cannot be supplied | No proof can be made in either grant order; the party ends the wait with a Rejection Entry |
| A receipt that is not the one canonical encoding, or that fails or faults while decoded or verified | The entry is skipped, never retried; all processors run the same pinned receiver build |

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

A change of the Coordination rules text needs these steps before the full build:
update `spec/frozen.json`; build once to read the new rules BlueId and put it in the
`specification` of every Coordination type; do the same for a package whose own
rules changed; re-pin `accessRecordsValid` in `admission-step-functions.blue` from
a Documents build without that export; then alternate
`build_final_gas.py clause-documents` and `tools/refresh_reseller_composition.py`
until the pins stop changing. Refresh `blue-time/SHA256SUMS` after the build.

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

## Provisional choices

Changing any of them gives new exact identities. Field names: `evidenceProfile`,
`receipt`, `document`, `operationEntry`, `mandateCommitment`, `programImageId`,
`allowedProviders`, `factsRule`. Type names: `Proof Entry`, `Rejection Entry`,
`Evidence Profile`, `RISC Zero Succinct Receipt Profile`, `Mandate Commitment
Authority`. Encodings: the proof as canonical base64 text; the commitment, image
identifier and digests as 64 lower-case hexadecimal characters; the facts rule as
one of the two values `FULL(D)` and `MERKLE(FULL(D))`; the layout and domain texts
of the mandate processor's signed message and of the facts digests.
