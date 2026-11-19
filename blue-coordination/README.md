# Coordination: timelines and timestamped inputs to Contracts

`blue-coordination` **0.2.0-access-events.1.evidence.1** defines how timelines supply verified,
ordered and complete inputs to Contracts. Providers preserve history and access
evidence; feeders establish the next original event and its timestamp.

- [Specification](spec/coordination.md): frozen provider, public channel, read, access and feeder rules.
- Section 14 of the specification: timeline channels with evidence. `Timeline Channel with Evidence`
  is a `Timeline Channel` that also names `evidenceTimeline`, `mandateProcessorKey` and
  `evidenceProfile`; `Evidence Profile` is the base type of a profile; `Proof Entry` and
  `Rejection Entry` are the two messages on an evidence timeline. Their schemas are open: the
  processor checks an entry and skips one that is not well formed.
- [Access-event addendum](spec/timeline-access-events.md): the new exact access program and its ordinary events.
- [Worked example](docs/examples.md): ACME provider subtype, human/agent actors,
  Hello entries, an executable Timeline Access document, atomic updates and reads.
- [Exact example data](examples/protocol.json): complete signed exchanges and actual
  before/after documents executed by the pinned Contracts reference processor.
- `types/`: exported Blue definitions. `tests/` and `tools/`: build and validation.

Timeline Access contains allowedTimelines, allowedKeys and contracts. Its provider
Public Timeline Channel carries the provider and canonical public history URL.
Timeline Provider.endpoint is the single REST API base for all its timelines and
may be inherited from the provider type. The same
read operation serves public requests without reader signatures and private
requests with Ed25519 signatures. Its update operation uses standard Contracts/BEX execution. Exact Blue types define versions;
there are no separate protocol-version, provider-ID, timeline-ID or grant-ID fields.
Updates target the original access document and atomically replace both lists in
accepted timeline order. Every successful update then emits the ordinary
`Timeline Access Updated` event, including unchanged-list updates. Replaying a
consumed request does not emit again. Parent embedded channels read the completed
child state; the event itself is not proof of permission. Private read signatures are reusable for their exact
query while access remains granted; every use rechecks current permissions.

This edition descends from 0.2.0-access-events.1. Sections 1–13 of the rules are unchanged; because
the rules text is part of every exact type identity, all type, rules, protocol and package BlueIds are
new. The earlier publication is retained unchanged under `retained/pre-evidence-20261119/` in the
package repository, and its documents keep their runtime. A host learns that a document needs this
edition from the exact type identities the document uses, as for every edition.

## Build and verify

The current candidate is built by the shared native Java builder:

```sh
python3 tools/build_final_gas.py blue-coordination
python3 tools/build_final_gas.py blue-coordination --check
```

Run these commands from the repository root with Java 21 and
`BLUE_JAVA_CLASSPATH` pointing to the qualified native runtime jars. Rebuild all
dependent packages and synchronize the generated catalogues after a publication
changes. Core's focused provider and access-event regressions validate execution.
The historical Python reference tools and examples describe their pinned edition;
they are not the builder or conformance evidence for this native publication.

The new access program follows the access-event specification addendum.
Transport and admission rules, and their exact type definitions, remain unchanged. Retained Core
archives are immutable; consumers must select this new package explicitly.
