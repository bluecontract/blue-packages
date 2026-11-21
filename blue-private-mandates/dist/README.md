# Blue Private Mandates

`blue-private-mandates` **0.1.0-preview.1** lets the participants of a document
decide an agent's operation from a proof instead of reading the mandate. It
requires the exact `blue-coordination` edition that defines timeline channels with
evidence (0.2.0-access-events.1.evidence.1) and the `blue-mandates` publication
built on it (0.3.0-preview.1.evidence.1).

- [Specification](spec/private-mandates.md): the authority claim, evidence
  profiles and when a proof matches.
- `Mandate Commitment Authority`: a `Mandates/Authority` that carries the salted
  mandate commitment and the holder actor, with no `mandate` reference.
- `Mandate State Attestation`: the document a mandate processor signs about one
  state of a mandate (its BlueId is signed; attestations of one mandate form a
  hash chain through `sequence` and `previous`).
- `RISC Zero Succinct Receipt Profile`: the first
  `Coordination/Evidence Profile`, with `programImageId` and
  `allowedProviders`. The provider set digest is derived from the list and is
  not a field.

The validity of the target document state is a premise of every proof: the proof
does not show it and the receiver does not check it. A processor accepts a proof
only for a state it produced or admitted itself. This version supports mandates
of type `Mandates/Operation Mandate` and its subtypes, on the same edition as the
target document; see §1 and §4.1 of the specification.

A faulty mandate never stops the document. A grant whose predicate ends in an
error does not match and the other grants are tried; exhausted gas or a fault of
the mandate itself gives "the mandate does not admit". The operation is then
rejected and the document continues. This differs on purpose from mandates named
in clear; see §3 of the specification.

This is an extension. `Mandates/Mandate Authority` with a clear mandate reference
stays supported and unchanged. A runtime must explicitly support this package's
protocol, including the verifier of a declared profile, before a proof decides
anything. Installing this data package grants no native support.

Type and field names are provisional; see §7 of the specification. This is an
unpublished candidate. Build and verify from the repository root:

```sh
python3 tools/build_final_gas.py blue-private-mandates
python3 tools/build_final_gas.py blue-private-mandates --check
```
