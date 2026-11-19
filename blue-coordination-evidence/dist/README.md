# Coordination evidence channels

`blue-coordination-evidence` **0.1.0-preview.1** is an additive Coordination
edition. It requires the exact `blue-coordination` 0.2.0-access-events.1
publication and adds one channel type and two entry types. No existing
Coordination type, archive or identity changes, and the earlier publication
remains selectable on its own.

- [Specification](spec/coordination-evidence.md): the channel, the proof timeline
  and how a processor decides an operation from it.
- `Timeline Channel with Evidence`: a `Coordination/Timeline Channel` that also
  names `proofTimeline`, `mandateProcessorKey` and `evidenceProfile`.
- `Proof Entry` and `Rejection Entry`: the two defined messages on a proof timeline.

The package's protocol identity is the capability a host must support for a
document that declares the new channel. A host without it must refuse such a
document. Installing this data package grants no native support.

Evidence profiles and the authority type that is decided from a proof timeline
are defined by `blue-private-mandates`, which requires this package.

Field names and the entry grammar are provisional; see §8 of the specification.
This is an unpublished candidate. Build and verify from the repository root:

```sh
python3 tools/build_final_gas.py blue-coordination-evidence
python3 tools/build_final_gas.py blue-coordination-evidence --check
```
