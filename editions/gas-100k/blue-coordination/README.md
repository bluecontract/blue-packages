# Coordination: timelines and timestamped inputs to Contracts

`blue-coordination` **0.2.0-rc.2** defines how timelines supply verified,
ordered and complete inputs to Contracts. Providers preserve history and access
evidence; feeders establish the next original event and its timestamp.

- [Specification](spec/coordination.md): provider, public channel, read, access and feeder rules.
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
accepted timeline order. Private read signatures are reusable for their exact
query while access remains granted; every use rechecks current permissions.

## Build and verify

Use Python 3.13+ with cryptography installed. Keep this package beside the shared
blue-contracts and blue-language packages, or set BLUE_PACKAGES_DIR to their parent.
The launcher verifies and selects the Contracts dependency's reference runtime in
a temporary directory. It does not assume the installed Contracts library matches.

```sh
export BLUE_PYTHON=/path/to/blue-language-python/.venv/bin/python
./blue-package test
./blue-package build
./blue-package check
```

After intentional source edits, run `./blue-package prepare`, then
`./blue-package examples`, before test/build/check. Ordinary builds never refresh
pins. The distributable is `dist/package.bluepkg`; check reproduces every byte.

This is the selected Coordination package for the standalone timeline provider. Reference execution validates the example and protocol rules;
a live service still needs durable storage, crash recovery and concurrency validation.
