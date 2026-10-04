# Blue Packages

Reusable Blue definitions, protocol specifications and executable business documents,
shared by the Java and Python implementations of Blue.

A package gives content an exact identity and a set of named exports. It can describe
a language, define a protocol, supply reusable types or contain an entire agreement.
Packages are data: native protocol implementations live in the consuming runtime.
Loading a package makes its definitions available; execution requires a runtime that
explicitly supports its exact protocol dependencies.

## Available packages

There are **14 baseline package projects**, including three versions of the commerce
function example. Historical immutable editions are retained separately. Follow the package links for sources, specifications and examples.

| Package | Suggested import prefix | What it provides |
| --- | --- | --- |
| [Language](blue-language/) | `Language` | Immutable typed content graphs, BlueId calculation, references, specialization and schemas. Exports `Package` and `Protocol Specification`; primitive types belong to the Language registry. |
| [BEX](blue-bex/) | `BEX` | The deterministic expression and program language used by workflows: values, functions, changesets, events and metered execution. This package defines a protocol and has no named type exports. |
| [Contracts](blue-contracts/) | `Contracts` | Document processing: channels, operations, workflows, compute steps, document updates, event delivery and embedded documents. Contains 32 type exports and the processing specification. |
| [Coordination](blue-coordination/) | `Coordination` | 41 definitions for authenticated timelines, independently managed documents and coordinated processing. Its scheduler and storage are implemented by the host runtime. |
| [Agreements](blue-agreements/) | `Agreements` | The reusable `Agreement` and `Clause` model, progress notifications and typed agreement lifecycle events. Independent of any particular activation clause. |
| [Mutual Activation](clause-mutual-activation/) | `MutualActivation` | Two-party negotiation, proposed edits, review rounds, approvals and decline. Emits typed events including `Activation Succeeded` and `Activation Declined`. |
| [Immediate Termination](clause-immediate-termination/) | `ImmediateTermination` | Separates negotiable termination terms from the executable clause. Allows party A, party B or either party to terminate, with authenticated actions and typed evidence. |
| [Reseller Agreement](agreement-reseller/) | `Reseller` | A concrete agreement combining commercial terms, mutual activation and optional immediate termination. Demonstrates the NEGOTIATING → ACTIVE → TERMINATED lifecycle. |
| [Agreement Examples](blue-agreement-examples/) | `AgreementExamples` | A portfolio containing subagreements. Observes their lifecycle events and requests onboarding for selected activated agreements. |
| [Mandates](blue-mandates/) | `Mandates` | Owner-approved conditional delegation of operations, including correlated evidence requests and responses. Requires explicitly supported native Coordination/Mandates behavior. |
| [Time](blue-time/) | `Time` | Six timer definitions for scheduling, firing, cancelling and replacing one-shot timers using explicit Unix timestamps in microseconds. **Conformance preview:** a data package and test fixture; native scheduling is not approved by this package. |
| [Commerce Functions v1](functions/commerce-functions-v1/) | `CommerceFunctions` | `Totals`: an exact integer line-total calculation implemented as ordinary Contracts/BEX data. |
| [Commerce Functions v1.1](functions/commerce-functions-v1_1/) | `CommerceFunctions` | Adds `Double` while preserving the original `Totals` export; demonstrates an additive package release. |
| [Commerce Functions v2](functions/commerce-functions-v2/) | `CommerceFunctions` | Changes the total function's arguments to include a fee; demonstrates explicitly selecting a different release. |

The foundation is Language → BEX → Contracts → Coordination. Agreements and the
business clauses compose on top of it. Mandates and Time specify additional protocol
requirements. Exact imports are recorded in each `blue-package.lock.json`; the table
is an overview, not a substitute for those pins.

## Current Agreement model

The four top-level Agreement projects now use **root clauses, version 0.3.0-rc.1**.
[ROOT-CLAUSE-PACKAGES.json](ROOT-CLAUSE-PACKAGES.json) pins their exact publications.
Clauses install state and workflows into one managed root document. The installer
supports atomic add/edit/remove amendments, revision checks, typed change events,
whole workflow parameters and references to existing fields.

Start with [the authoring guide](blue-agreements/docs/root-clauses.md) and
[Java qualification results](docs/root-clause-amendments.md).

The previous top-level embedded-clause projects are preserved in
[editions/embedded-clauses](editions/embedded-clauses/). SHARED-PACKAGES.json keeps
those legacy identities, so existing consumers can continue using that selection.
The original root-clause preview remains in editions/root-clauses with its own
SELECTION.json. Selecting the new release does not migrate an existing instance.

## Identities, names and content

An export is addressed by its BlueId. A readable name such as
`MutualActivation/Mutual Activation Clause` is a local, case-sensitive alias for that
identity. Mount each namespace explicitly; importing an agreement does not expose all
its dependencies' names. Use capitalized prefixes in new documents, as shown above.
Some immutable foundation releases retain older lowercase authoring aliases internally.

The package BlueId identifies its semantic package content. The archive SHA-256
checks the exact transported bytes. A changed release gets new identities and an
explicit dependency selection; existing IDs are never rebound to new content.

A package is a convenient way to group reusable definitions. It does not limit Blue
to predefined types: applications can also store and resolve arbitrary content,
including collapsed references, through their runtime's repository/provider API.

## Using the packages

For development, place the repositories beside one another:

```text
workspace/
  blue-packages/
  blue-java/
  blue-language-python/
```

Both consumers can select this directory with `BLUE_PACKAGES_DIR`; Java also accepts
`-PbluePackagesDir=/absolute/path/to/blue-packages`. Keep each consumer's exact package
lock. Changing this repository's inventory does not automatically migrate a runtime,
its stored state or its execution permissions.

The current shared selection is in [SHARED-PACKAGES.json](SHARED-PACKAGES.json).
Time has a [separate preview selection](blue-time/docs/integration-selection.json)
and is not silently added to either runtime. Historical Java consumers also use the
preserved `blue-mutual-activation` compatibility path. See
[consumer selection and aliases](docs/using-packages.md) for these distinctions.

## Checking and preparing a release

Run these commands from this repository:

```sh
# Fast archive, unpacked-file, inventory and dependency integrity checks; Python 3.10+.
python3 tools/release.py check

# Semantic package/definition checks; Python 3.13+ with Blue Python installed.
PYTHONDONTWRITEBYTECODE=1 python tools/verify_packages.py

# A deterministic data-only bundle of the 18 selected package archives.
python3 tools/release.py bundle --output build/blue-packages.zip
```

The bundle includes a catalogue, checksums and distribution notes. It excludes
runtime snapshots, tests, logs, unpacked duplicates and historical publications.
Individual `dist/package.bluepkg` files remain the units to distribute and pin.
The bundle is an artifact collection, not a replacement source checkout.

See [publishing](docs/publishing.md) for release checks and licensing status,
[layout](docs/layout.md) for source ownership, and
[the agreement walkthrough](docs/agreements.md) for typed events and composition.
Recorded qualification belongs to its specific release and runtime; package integrity
alone does not assert complete Java/Python behavioral parity or production readiness.

## Repository maintenance

Package folders contain authored content and their exact distributions. `docs/`
contains current repository guidance; `tools/` contains build and release utilities;
`verification/` retains reproducibility evidence and older publications. The root
JSON files remain at stable paths because existing consumer tools read them.
The [layout guide](docs/layout.md) explains their distinct purposes and the few
compatibility paths. Generated caches and local build outputs are ignored.

No repository-wide license has been declared. Existing provenance and third-party
notices are retained; select appropriate licensing before public redistribution.
