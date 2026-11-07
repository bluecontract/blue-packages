# Execution profile integration contract

Status: G0 agreed by the Packages, Core and integration owners, 2026-10-30.
The pre-merge repair uses Text BlueIds for every identifier inside a descriptor;
the declaration itself remains inline or an exact descriptor reference.

The normative public rules are in
[`blue-execution-profile/spec/execution-profile-v1.md`](../blue-execution-profile/spec/execution-profile-v1.md).
They define the declaration, exact descriptor, selection and preservation rules.
The package exports the ordinary Language-only `Execution/Profile` schema.
Its normative rules are an identified Text asset, not a Contracts prerequisite.
The descriptor's required `executionSpecification` field pins that exact Text.
Core binds and validates the same identity in its new outer container edition.

## Publication ownership and ordering

1. Packages publishes the schema and its rules using the qualified native builder.
   It imports only the exact Language package. Existing Contracts, BEX,
   Coordination and business publications are not changed by adding this schema.
2. Core imports that immutable package, selects its actual supported native
   protocols and publishes its new outer execution rules/bridge as needed.
3. Core constructs canonical concrete profile records from those finished IDs,
   registers their implementation and exposes the exact content to resolution.
4. Integration binds the parameterized conformance cases to those real records.

There is no dependency from the schema or its normative text to a future Core
profile ID. A descriptor cannot contain its own containing package ID. An own
protocol reference is not inherently cyclic: the native builder constructs the
protocol descriptor before exports. The complete dependency graph still must be
acyclic, including exact IDs embedded in normative text.

The initial package base is `0187d35fb76fb8ec9207adfad3800d08c8da295b`.
It selects Access Events/final-gas, not the earlier demand-scoped source tree.
`PACKAGES.json` and archive manifests are the identity authority.
Historical Demand bytes remain retained; this change does not reactivate them.

## Reader and native integration

`executionProfile` is an ordinary sibling of `contracts` in an executable node.
It is not a new contract role and is never removed before selected Contracts
processing. A retained engine receives the complete unchanged node. Profile
selection, immutability and per-member snapshot commitments are rules of the
new outer execution edition; they do not rewrite a retained Contracts release.

Core obtains the effective field through a supported Source/Exact reader and
the contextual Language head, so a node type can contribute the declaration.
The reader does not execute BEX or document contracts. The initial reader's
accepted Language/format is explicitly registered; it does not infer how to
read an unknown Language from content it cannot decode.

The outer edition must commit its exact normative rules identity and each
member's effective profile. The source/version identity, instance identity,
profile identity and implementation build identity remain distinct. Native
runtime modules receive a runtime-owned selection interface; they do not depend
on host service classes.

Core's agreed wire container is `contracts.profile-snapshot/1`. Its top level
contains `format`, `executionProtocol`, `executionSpecification`, `root`,
`documents`, `edges`, `generation` and `revision`. The exact `executionProtocol`
binds Core's downstream outer native wire rules. Every document carries its own
`executionProfile`, `release` and `runtimes` alongside its existing metadata;
there is no top-level release/runtime selector for all members. The new snapshot
hash domain is `contracts.snapshot/profile-1`; invocation and receiving domains
are versioned separately. The legacy container and domains remain unchanged.
Core documents the implementation in `docs/EXECUTION-PROFILES.md`; the integration
handoff pins that repository's tested commit.

Core's descriptor mapping uses `RuntimeBindings.identities()` with one explicit
wire mapping: descriptor `contract` maps to native identity key `contracts`.
The plural name is reserved Language metadata and cannot be a profile field. Public `provider` and native `coordination`
have distinct meanings. A deployment/build ID is provenance, not profile input.
The additional `executionSpecification` distinguishes new outer semantics from
the retained Contracts/BEX identities. The effective profile type is the exact
base schema export. Node type inheritance is supported; arbitrary profile
subclasses are not erased. Both input modes canonicalize list order and reject
duplicate capabilities/native package IDs without changing source identity.

Descriptor scalars and list entries are ordinary primitive Text values carrying
final BlueIds. A pure reference to a plain Text-ID value resolves normally;
references directly to packages or protocols do not satisfy this grammar.
Canonical values contain plain typed Text, without labels, overlays or subtypes.
The native catalogue explicitly resolves every carried dependency in its proper
role and exports its complete closure. Language value admission of a descriptor
does not itself verify these identifier targets. In particular, Time packages
and interpreted-capability approvals can contain required definitions without
being incorrectly interpreted as instance values through the declaration.

## Conformance ownership

[`blue-execution-profile/conformance/cases.json`](../blue-execution-profile/conformance/cases.json)
contains structural reader/selection cases. A value of the form
`{"$fixture":"parameter"}` is a harness substitution for a complete Blue value,
not Blue syntax or a fake BlueId. Parameterized cases are not directly admitted.
Core supplies the actual profile records, references, node type and instances
before native verification. All final concrete fixtures contain actual IDs.

These cases cover declaration and durable selection. Core additionally proves
actual execution with observably different native profiles, parent reactions,
three-profile selection, shared children, supported cycles, metering, atomic
failure, replay, restoration, capabilities and every host preparation path.
Successful package validation alone does not qualify that execution.

## Handoff and rollback

The package handoff identifies its committed source revision, builder source
revision, Java version, classpath/JAR checksums, commands, archive SHA-256,
package ID, schema export ID, normative Text ID and dependency closure.
It also records unchanged historical publication IDs and archive checksums.

Core adds the concrete profile records and IDs, exact bridge identity, completed
fixtures, authoritative snapshot format/version, minimum reader, SQL migration
decision and tests at the tested revision. Newly written mixed-profile containers
must never be presented to an older reader as a homogeneous legacy snapshot.
Legacy snapshot bytes and their hash domain retain their existing reader.

The new package is a candidate. Merging a PR, changing a stable default, tagging
a release, publishing SDKs and deploying a worker are separate actions.
