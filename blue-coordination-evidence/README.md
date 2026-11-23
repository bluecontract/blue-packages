# Coordination evidence channels

`blue-coordination-evidence` **0.1.0-preview.2** is an additive package. It requires
the exact `blue-coordination` 0.2.0-access-events.1 publication and adds one channel
type, the evidence profile base type and two entry types. No existing Coordination
type, archive or identity changes, and that publication remains selectable on its own.

It defines no transport type. An evidence timeline and the timeline of an evidence
channel are ordinary `Coordination/Signed Timeline` values with ordinary
`Coordination/Timeline Entry` entries, guarantees and provider descriptors, under the
exact identities of the required Coordination publication. A timeline provider needs
no support for this package.

- [Specification](spec/coordination-evidence.md): the channel, the evidence timeline
  and how a processor decides an operation from it.
- `Timeline Channel with Evidence`: a `Coordination/Timeline Channel` that also
  names `evidenceTimeline`, `mandateProcessorKey` and `evidenceProfile`.
- `Evidence Profile`: base type of the profile a channel declares; concrete
  profiles are specialisations published by other packages.
- `Proof Entry` and `Rejection Entry`: the two defined messages on an evidence
  timeline. Their schemas are open: the processor checks an entry and skips one that
  is not well formed. A Proof Entry requires only `receipt`; `document` and
  `operationEntry` are optional there and are an advisory hint with no force.
- A rejection decided from the evidence timeline has one of two durable reasons,
  the same on every processor: `AUTHORITY_EVIDENCE_DENIED` for a verified proof
  that denies and `AUTHORITY_EVIDENCE_REJECTED` for a Rejection Entry.
- `mandateProcessorKey` must be a well-formed Ed25519 key: canonical encoding of a
  curve point that is not of small order.

The package's protocol identity is the capability a host must support for a
document that declares the new channel. A host without it must refuse such a
document. Installing this data package grants no native support.

Concrete evidence profiles and the authority type that is decided from an evidence
timeline are defined by `blue-private-mandates`, which requires this package.

Type names, field names and encodings are fixed; what is not decided is listed in
section 8 of the specification. This is an unpublished candidate. Build and verify from the
repository root:

```sh
python3 tools/build_final_gas.py blue-coordination-evidence
python3 tools/build_final_gas.py blue-coordination-evidence --check
```
