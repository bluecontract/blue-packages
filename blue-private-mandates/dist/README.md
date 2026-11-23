# Blue Private Mandates

`blue-private-mandates` **0.1.0-preview.3** lets the participants of a document
decide an agent's operation without reading the mandate. The agent's operation
carries a salted commitment to the mandate, and the document processor of the
represented party writes a signed statement on the party's evidence timeline that
says whether the mandate admits the operation. The package requires the exact
`blue-coordination-evidence` package (0.1.0-preview.3), which defines timeline
channels with evidence on the unchanged `blue-coordination` 0.2.0-access-events.1,
and the unchanged `blue-mandates` 0.3.0-preview.1. No transport type and no
Mandates type has a new identity.

- [Specification](spec/private-mandates.md): the authority claim, the commitment,
  the attestation, the statement and its bytes, what the signer checks before it
  signs, how a processor decides, and the known limits.
- `Mandate Commitment Authority`: a `Mandates/Authority` that carries the salted
  mandate commitment and the holder actor, with no `mandate` reference.
- `Mandate State Attestation`: the document a mandate processor signs about one
  state of a mandate (its BlueId is signed; attestations of one mandate form a
  hash chain through `sequence` and `previous`). It names the two timer bounds of
  the state by timestamp, Timer Source id and Timer Entry id.
- `Signed Statement Profile`: the `CoordinationEvidence/Evidence Profile` of this
  package, with one field, `statementSignerKey`.

A statement is a signed assertion, not a demonstration. The mandate processor
answers for the attested state and the signer for the evaluation; the signatures
let each be held to its statement when the mandate is later disclosed. Verifying a
statement needs no external tool: it is a decoding, one signature check and five
comparisons of texts.

A faulty mandate never stops the document: it gives a denying statement, the
operation is rejected and the document continues. The represented party can stop
the document by writing nothing; see §9 of the specification for this and the
other known limits.

`Mandates/Mandate Authority` with a clear mandate reference stays supported and
unchanged. A runtime must explicitly support this package's protocol before a
statement decides anything. Installing this data package grants no native support.

Type names, field names and encodings are fixed; what is not decided is listed in
§11 of the specification. This is an unpublished candidate. Build and verify from
the repository root:

```sh
python3 tools/build_final_gas.py blue-private-mandates
python3 tools/build_final_gas.py blue-private-mandates --check
```
