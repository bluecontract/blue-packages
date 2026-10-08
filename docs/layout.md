# Repository layout

| Location | Purpose |
| --- | --- |
| `PACKAGE-SOURCES.json` | Ordered current source directories and frozen foundations. |
| `PACKAGES.json` | Complete current catalogue, exact identities and archive hashes. |
| `SHARED-PACKAGES.json` | Generated consumer view of the same catalogue. |
| `PAYMENT-FAMILY-PACKAGES.json` | Generated business-package view for Core's demonstration suite. |
| `<package>/blue-package.yaml` | Exports and root-relative dependency sources. |
| `<package>/blue-package.lock.json` | Exact dependency locks. |
| `<package>/types/`, `spec/` | Authored types, BEX programs and protocol rules. |
| `<package>/dist/` | Built archive and its exact unpacked contents. |
| `examples/apps/` | Current clause-based application sources and executable scenario assertions. |
| `catalogue/payment-family.json` | Example descriptions for the walkthrough viewer; no package selection. |
| `verification/reference/` | Frozen foundation conformance implementations and source locks. |
| `verification/publications/` | Exact historical conformance inputs, never current source selections. |
| `build/`, `reports/` | Ignored local outputs and measured evidence. |

There is one `blue-agreements` source directory. The connected clause host is
now its current implementation. Mandates remains separate from both Agreements
and Coordination. Immutable foundation inputs and their original notices are
retained for reproducibility; historical wording inside frozen archives does
not select an alternative current package set.
