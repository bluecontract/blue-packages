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
`RISC Zero Succinct Receipt Profile` (a `Coordination/Evidence Profile`) and
`Mandate Commitment Authority` (a `Mandates/Authority` with the salted mandate
commitment and no `mandate` reference). The normative rules are the two `spec/` files.

| Item | Version | BlueId |
| --- | --- | --- |
| Coordination package | 0.2.0-access-events.1.evidence.1 | `FF7vQrNAZSATL6GwxYXdwtuR9xSiBTYMizvraBEExAQc` |
| Coordination protocol | | `5e4NgPeAqS4ToVDiRJdPScNKGQGahjzBKuUR85uaQJLP` |
| Coordination rules | | `DKSQLfTLQncVfoJL85NQHoShR36YD5U5t8zdqPgUdEcr` |
| Mandates package | 0.3.0-preview.1.evidence.1 | `EktwAbNdM6fUF1GqYzzSjAgXqiLLpHSt5VVpT7zM5rxY` |
| Mandates protocol | | `AkK3aMRA7ZtBkPx7kYNLo7v9gbJ3fyMu37m4KqmnFwnn` |
| Time package | 0.2.0-gas10m.1.finalgas.1.evidence.1 | `B6FT4ipNEtGsnj5d3mMura6B1sfobnfZpARHYqJLRdaP` |
| Time protocol | | `8RsWVecPqq8vkz5Q7hFu3ViQKq4sY8cUEDjrmoZGU88K` |
| Private Mandates package | 0.1.0-preview.1 | `EmNKZCSCP6nNc8fgC1fczGmQj7gm3GwTYfgWvPWA9nR1` |
| Private Mandates protocol | | `FXXMkCiha8hS3HBNyN8r6s873kUao93bk274HFku31rV` |
| Private Mandates rules | | `3PZprGbDbtCagSYTK8raSDdEMCftFgkfcLpvhGYap7t3` |

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
edition keep their runtime. The ten packages that do not embed Coordination are
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

Closed and typed by the Language schema: the channel (three required fields, key
length, profile of the base type), the profile (exact field set, lengths, distinct
provider keys, the facts rule value) and the commitment authority (exact field set,
so a clear `mandate` field is rejected; commitment length).

Open by design: `Proof Entry` and `Rejection Entry` name their fields and constrain
nothing. A malformed entry is still Blue content, so it cannot fail the import of an
evidence timeline. The processor checks the field set and form and skips an entry
that is not well formed; a skipped entry never causes a wait or a halt of its own.

`document` and `operationEntry` are references by content BlueId, declared as an
`Operation Request` declares `document`: free fields with no type. Language opens a
`{blueId: …}` value wherever it stands. An evidence timeline serves exactly one
document and its readers are that document's participants, so a reference in a
well-formed entry resolves, possibly after a wait for the operation entry. Known
limit: an entry whose reference is not a valid BlueId, or can never be resolved by
the readers, blocks that evidence timeline until timeline import can skip an entry
it cannot read. The conformance tool records these admission outcomes.

Decided by a Core implementation, with the outcomes the specifications state:

| Value | Outcome |
| --- | --- |
| `mandateProcessorKey`, `programImageId` or a provider key that is not 64 characters `0-9a-f` | The channel lacks that field: operations under a commitment authority on it are rejected from the document state |
| `allowedProviders` not strictly ascending by key bytes | Same |
| `evidenceProfile` whose exact type is the base type | Same |
| `mandateCommitment` that is not 64 characters `0-9a-f` | The operation is rejected from the document state, without reading the evidence timeline |
| An entry of one of the two types that is not well formed | The entry is skipped |
| A predicate of the mandate that ends in an error | "The mandate does not admit": the operation is rejected and the document continues. A deliberate difference from mandates named in clear |

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
the single value `FULL(D)`.
