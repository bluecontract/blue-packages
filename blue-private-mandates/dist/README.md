# Blue Private Mandates

`blue-private-mandates` **0.1.0-preview.4** lets the participants of a document
decide an agent's operation without reading the mandate. The agent's operation
carries a salted commitment to the mandate, and the document processor of the
represented party writes a signed statement on the party's evidence timeline that
says whether the mandate authorizes the operation. The package requires the unchanged
`blue-coordination` 0.2.0-access-events.1 and `blue-mandates` 0.3.0-preview.1. No
transport type and no Mandates type has a new identity.

- [Specification](spec/private-mandates.md): the channel, the entries on the
  evidence timeline, the authority claim and its commitment, the attestation, the
  statement and its bytes, how a processor decides an operation, and what the
  signer checks before it signs.
- `Timeline Channel with Evidence`: a `Coordination/Timeline Channel` that also
  names `evidenceTimeline`, `statementSignerKey` and `mandateProcessorKey`.
- `Statement Entry` (`statement`) and `Rejection Entry` (`document`,
  `operationEntry`): the two messages on an evidence timeline. Their schemas are
  open; the processor checks an entry and skips one that is not well formed.
- `Mandate Commitment Authority`: a `Mandates/Authority` that carries the salted
  mandate commitment and the holder actor, with no `mandate` reference.
- `Mandate State Attestation`: the document a mandate processor signs about one
  state of a mandate (its BlueId is signed; attestations of one mandate form a
  hash chain through `sequence` and `previous`).

A statement is a signed assertion, not a demonstration: the mandate processor
answers for the attested state and the signer for the evaluation. Verifying a
statement is a decoding, one signature check and five comparisons of texts. A
rejection decided from the evidence timeline has one of two reasons,
`AUTHORITY_EVIDENCE_DENIED` (a statement with `verdict` `false`) or
`AUTHORITY_EVIDENCE_REJECTED` (a Rejection Entry). While no entry decides an
operation, the document waits; there is no deadline.

`Mandates/Mandate Authority` with a clear mandate reference stays supported and
unchanged. A runtime must explicitly support this package's protocol; a host
without it refuses a document that declares the channel. Installing this data
package grants no native support.

Type names, field names and encodings are fixed; open points are listed in §11
of the specification. This is an unpublished candidate. Build and verify from the
repository root:

```sh
python3 tools/build_final_gas.py blue-private-mandates
python3 tools/build_final_gas.py blue-private-mandates --check
```
