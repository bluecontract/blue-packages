# Blue Private Mandates

`blue-private-mandates` **0.1.0-preview.1** lets the participants of a document
decide an agent's operation from a proof instead of reading the mandate. It
requires the exact `blue-coordination-evidence` and `blue-mandates` publications
it was built against.

- [Specification](spec/private-mandates.md): the authority claim, evidence
  profiles and when a proof matches.
- `Mandate Commitment Authority`: a `Mandates/Authority` that carries the salted
  mandate commitment and the holder actor, with no `mandate` reference.
- `Evidence Profile`: base type of the profile a
  `CoordinationEvidence/Timeline Channel with Evidence` declares.
- `RISC Zero Succinct Receipt Profile`: the first profile, with `programImageId`,
  `providerSetDigest` and `factsRule`.

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
