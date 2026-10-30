# Execution profiles v1

## Scope

An executable node has one effective execution profile for the lifetime of its
instance. The profile identifies its Language, native protocols, exact rules,
capabilities and supported native package set. A worker runs each node with an
installed implementation of that exact profile. Installing profile content does
not install an implementation.

Different profiles in one graph are permitted. No equality or compatibility
relation between parent and child Language, BEX, Contracts or capabilities is
implied or required. Each node must satisfy its own exact dependencies and
requirements. Existing completion provenance, ordering, metering aggregation,
atomic publication, permissions and graph ownership rules continue to apply.

## Declaration

For profile-aware admission, the ordinary `executionProfile` field is a sibling
of `contracts` in an executable node. Its value is either an inline typed
`Execution/Profile` descriptor or an exact reference to such a descriptor.
Normal Language resolution can inherit this field from the node's definition.
Aliases must be resolved using the pinned preparation publication context.

The initial reader accepts only its explicitly registered Source/Exact formats
and Language. It resolves the effective field without running document code.
Unsupported readers/formats fail before runtime selection. Unavailable content
is not absence and must not trigger a default.

The complete node, including its declaration, is passed unchanged to the
selected native runtime. The declaration is not placed in the contracts map,
treated as an executable contract, or removed to obtain acceptance by an older
Contracts parser. Ordinary non-executable data needs no profile binding.

## Descriptor

The effective schema type is exactly the published `Execution/Profile` export.
A profile subclass is not silently converted to that base type. The following
six fields are required and each contains only an exact `{blueId: id}` reference,
without an alias, version selector or refinement overlay:

- `executionSpecification`: the exact Text identity of these outer execution
  profile rules, independently of the retained native runtime protocols.
- `language`: the Language package identity.
- `bex`: the BEX protocol identity.
- `bexSpecification`: the normative rules identity bound to that BEX protocol.
- `contract`: the Contracts protocol identity. The wire name is singular because
  `contracts` is reserved Language metadata, not an ordinary descriptor field.
- `contractsSpecification`: the normative rules identity bound to Contracts.

No implicit protocol or rules ID is supplied.

`coordination` and `coordinationSpecification` are optional exact references
to the native coordination execution protocol and its rules. They must appear
together. `provider` is an optional exact reference to the public provider
protocol. It does not select or replace the native coordination protocol.

`capabilities` is a required list of exact references to optional native
semantics. `supportedPackages` is a required list of exact references to the
native package identities accepted by this implementation profile. Both lists
may be empty. Duplicate entries are rejected. The reader sorts unique entries
lexicographically by BlueId when deriving the effective profile in both Source
and Exact input modes; it does not modify the original node or source identity. An
unlisted capability is unavailable even if another node or worker supports it.
The supported native package set does not replace ordinary package installation
or the complete exact dependency closure of a node.

Only the declared descriptor fields and its schema type are allowed. Display
names, versions, deployment identifiers and implementation build identifiers
are not descriptor fields. The referenced protocol/rules pairs must agree with
the exact admitted publications. Loading a similarly named/newer publication
cannot satisfy a different exact reference.

The reader resolves the effective descriptor fields and constructs a canonical
profile record using the exact base schema type, exact references and the
ordered lists. The BlueId of that record is the effective profile identity.
Source spelling and a node's source identity remain separate. A profile record
or source reference with unavailable content cannot be replaced with a guess.

## Selection and preparation

An explicit effective source declaration selects the profile. An explicit API
selection may confirm it; a different selection is a conflict. Without a source
declaration, an explicit API selection selects the profile. Otherwise a newly
created child's supplied parent default is used, followed by the account
default, followed by the host's explicitly installed stable profile.

A default must satisfy the new node's requirements. Preparation resolves the
profile and alias context before dependent parsing/normalization. It preserves
the original client-intent fingerprint separately from the prepared result.
The chosen profile is durably bound to the instance atomically with admission.
Retry, competing preparation and changed defaults reuse the accepted result.

Existing source/version aliases identify existing instances. A different
requested profile is a conflict; it must not create a new source identity to
bypass deduplication. Creating a genuinely new instance is a separate action.

## Instance lifetime and restoration

The native authoritative record commits the profile identity for each member,
including members sharing a path or reachable through several parents. A new
instance at an old path has its own identity. Sharing, detach/reattach, aliases,
snapshot copy/rooting and completed-source import preserve the original
instance's binding. A source completion is opened in its source context and
the receiver's reaction runs in the receiver's context.

The profile is immutable during an instance's lifetime. A patch, type change,
inherited-definition change, contracts replacement, repair or removal of the
declaration cannot change the effective binding. Such a change fails atomically
without publishing a partially changed graph. A new executable child resolves
its own profile before its first semantic processing step.

The new outer execution/container edition binds these exact rules and commits
each member profile independently of the container's version. Its rules
identity agrees with each member's `executionSpecification`. Restoration,
replay, metering and capability checks use the recorded member profile. Mutable
contexts and semantic caches do not cross profiles. Resource budgets remain
shared at the owning account/process; profiles do not create extra journal
owners or multiply those budgets.

Legacy records are interpreted with their retained reader and historical
binding evidence. An ordinary `executionProfile` field in a legacy record is
not retroactively a selector. Missing legacy evidence must not be replaced by
today's default. Profile-aware admission of new input is a distinct path;
legacy sources, snapshots and receipts are not rewritten to add declarations.

## Diagnostics

The reader distinguishes unsupported input format, invalid descriptor,
unavailable referenced content, unknown profile, absent implementation, unmet
exact requirement, unavailable capability, conflicting selection and attempted
profile change. Native missing-content/type errors retain their information.
No such error falls back to a parent, account or newer runtime. Host error-code
spelling may follow its established API; these distinctions are normative.

## Publication identity

This is the normative Text asset of a Language-only schema package. It adds no
native execution prerequisite to the schema publication. The profile-aware
outer runtime binds this Text's exact BlueId in its own normative edition;
that edition and installed profile records are constructed downstream.
The schema/rules contain no future Core profile or bridge identifier.
