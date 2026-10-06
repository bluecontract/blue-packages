# Blue Mandates

Owner-approved operation delegation, implemented as Blue definitions and ordinary
Contracts/BEX workflows with explicitly selected native Coordination support.

Read [installation and runnable checks](docs/installation.md), the [guide](docs/guide.md)
and [normative protocol](spec/mandates.md). Definitions are in `types/`; the exact
published data archive is `dist/package.bluepkg`. Dependencies are pinned sibling
packages, not copied implementations. Native code lives in blue-python.

Use `Runtime.mandates().coordination()` to select the full supported dependency set:
Language, BEX, Contracts, Coordination and Mandates. Mounting data alone grants no
execution authority. A holder must approve the exact program; the delegate remains
the actual actor. The historical complete scope must contain one whole matching grant.

The Workbench lesson demonstrates A owning increment/decrement and B receiving an
increment grant plus a decrement grant controlled by an independently processed flag
embedded in the Mandate. `Qualification Mandate` also provides typed evidence requests
and correlated provider responses. No external connector or Java implementation is
included. This is a Python integration preview.
