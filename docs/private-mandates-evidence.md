# Private mandates: evidence channels and proof profiles

Two additive, unpublished packages let the participants of a document decide an
agent's operation from a proof on a proof timeline instead of reading the mandate.

| Directory | Namespace | Version | Requires |
| --- | --- | --- | --- |
| `blue-coordination-evidence` | `CoordinationEvidence` | 0.1.0-preview.1 | exact `blue-coordination` 0.2.0-access-events.1 |
| `blue-private-mandates` | `PrivateMandates` | 0.1.0-preview.1 | exact `blue-coordination-evidence` and `blue-mandates` 0.3.0-preview.1 |

`blue-coordination-evidence` is the Coordination edition that supports the new
channel type: `Timeline Channel with Evidence` (a `Coordination/Timeline Channel`
with `proofTimeline`, `mandateProcessorKey` and `evidenceProfile`), `Proof Entry`
and `Rejection Entry`. `blue-private-mandates` adds `Evidence Profile`, its first
specialisation `RISC Zero Succinct Receipt Profile`, and `Mandate Commitment
Authority`, a `Mandates/Authority` that carries the salted mandate commitment and
no `mandate` reference. The normative rules are each package's `spec/` file.

## Why the edition is a separate package

A Coordination type names the exact rules it is defined by, and the builder
requires that reference to equal the package's protocol rules. New rules inside
`blue-coordination` would therefore change the identity of every Coordination
type, `Timeline Channel` included, and of every package that imports them. The
evidence edition instead imports the exact current Coordination publication and
adds its own rules and protocol identity on top. `Timeline Channel with Evidence`
is a real subtype of the unchanged `Timeline Channel`.

The catalogue selects one archive per namespace, so the edition has its own
namespace and mount. `Coordination` keeps selecting the earlier publication.

## Compatibility

- No existing source, archive, package identity, type identity, dependency lock or
  `PACKAGES.json` row or mount changes. The two packages are appended to the
  foundations in `PACKAGE-SOURCES.json`; the generated views gain two rows.
- `Mandates/Mandate Authority` with a clear mandate reference stays supported.
- A document that declares no channel of the new type, and carries no commitment
  authority, does not involve either package.
- Each package has its own protocol identity. A host must explicitly support it
  for a document that declares the new channel; installing the data grants no
  native support, and a host without it must refuse such a document.

## Build and verify

With Java 21 and `BLUE_JAVA_CLASSPATH` set to the qualified Language runtime jars:

```sh
python3 tools/build_final_gas.py blue-coordination-evidence
python3 tools/build_final_gas.py blue-private-mandates
tools/build-payment-family.sh __index_only__
python3 tools/sync_catalogues.py
python3 tools/build_final_gas.py blue-coordination-evidence --check
python3 tools/build_final_gas.py blue-private-mandates --check
python3 tools/release.py check
python3 -m unittest discover -s tools -p 'test_release.py'
```

The native schema check admits one valid value of each new type, rejects values
with a missing or malformed field, checks inheritance and pins the earlier
Coordination and Mandates identities:

```sh
mkdir -p reports/private-mandates/classes
"$JAVA_HOME/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" \
  -d reports/private-mandates/classes tools/PrivateMandatesTypesConformance.java
"$JAVA_HOME/bin/java" -cp "reports/private-mandates/classes:$BLUE_JAVA_CLASSPATH" \
  PrivateMandatesTypesConformance .
```

These checks cover Language schemas, archive integrity and reproducibility. They
do not qualify native execution: admission from a proof timeline, the host
capability and proof verification are qualified in Core.

## Provisional choices

The protocol specification leaves these open; changing any of them gives new
exact identities. Field names: `evidenceProfile`, `receipt`, `operationEntry`,
`mandateCommitment`, `programImageId`, `providerSetDigest`, `factsRule`. Type
names: `Proof Entry`, `Rejection Entry`, `Evidence Profile`, `RISC Zero Succinct
Receipt Profile`, `Mandate Commitment Authority`. Encodings: the proof as
canonical base64 text; the commitment, image identifier and digests as 64
lower-case hexadecimal characters; `mandateProcessorKey` as a
`Coordination/Ed25519 Public Key`; the facts rule as the single value `FULL(D)`.
The profile carries the digest of the allowed provider set, not the list.
