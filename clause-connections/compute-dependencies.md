# Qualified Compute dependency selection

This candidate can reduce the definition passed to a generated Connections
handler before Contracts charges its materialization. It does not change the
Contracts or BEX runtime, its gas schedule, or any previously published type.

The publisher and planner form one feature:

1. `OperationInputs.publish` verifies the complete reachable standard
   `Connection Plan.plan` function graph and its used constants against the
   current exact Connections publication. It resolves the effective
   `actionDefinition` in the same native read context, then `ComputeDependencies` validates the complete library
   with the existing BEX compiler. This includes unused functions, static
   declarations, unknown calls/constants and recursion.
2. The publisher adds dependency metadata to the executable hook's
   `constants.computeDependencyIndexes`, keyed by exact definition identity.
   Derived clauses add entries without replacing their parent's frozen entries.
   The index contains exact references to complete functions and constants, plus
   the identity of each complete argument declaration. It also binds the complete
   effective hook function map and its used constants. It contains no projected
   function implementation and does not depend on its own identity.
3. `planConnections` constructs the actual Compute, including its local functions
   and constants, and invokes `selectConnectionCompute`. The selector follows
   every possible call branch and helper. It retains every local declaration,
   applies local overrides before selecting shared dependencies, and retains a
   used shared constant in full. Argument values remain fresh on every call.
4. The resulting smaller definition is present in the document before the
   operation enters `ContractRun.computeDefinition`. Ordinary BEX compilation and
   execution still occur. A later connection using another function receives
   its own closure.

Authors keep using `actionDefinition`, `actions` and `bindings`; there is no list
of reseller-specific function names. The existing publication commands invoke
the qualifier. Rebuild the new Connections candidate and each dependent package
in dependency order; an old exact hook with pinned planning functions retains
its old behavior. No release or import into Core/Business is part of this change.

## Qualification boundary

The guarantee applies to publisher output and an unchanged executable hook,
including its constants. An ordinary `connectionDependencies` document field is
ignored. Changing the library without a matching qualified entry uses the full
definition. Rewriting the executable hook or its code constants is a change to
the author's program, not a trusted publication certificate.

The planning wrapper rechecks the current candidate's complete hook function
identity and the witnessed used constants before using an index. Thus a child
with the same `actionDefinition` but a changed planner cannot reuse an inherited
matching entry. Neither the function-map identity nor the witnessed constants
include the index slot itself, so the qualification has no identity cycle.

A custom `plan`, modified reachable helper or changed used planner constant is
not qualified. It retains its ordinary full path, including the ability to add
custom local functions/constants after calling `planConnections`. This avoids
prematurely rejecting a library that depends on custom generated slots or
pruning a helper that the custom hook later uses. The only exempt used constant
is the documented publisher-owned index map. Complete function identity includes
argument declarations and defaults/pattern data. This is a generic standard
planner boundary, not a domain/type allowlist.

The compiler receives only the actual external constant/function slots that
Connections constructs. Existing library declarations are validated too. If a
generated override repairs an otherwise invalid library, publication preserves
the existing full path without claiming qualification. Missing external slots
at selection time likewise retain the full definition. Local constants and
functions are never removed, so their real values and code remain subject to
normal runtime validation. Removing/changing argument names, patterns or other
argument declaration data forces full fallback.

Unsupported intrinsic capabilities, unavailable exact records, a missing or
mismatched index, unproven dynamic reads and introspection use the full path.
The selector rejects reachable `$currentContract` and reads that might observe
the generated `/contracts` subtree. Static paths and safe prefixes from final
local constants can be proven safe; arbitrary variables are not guessed. AST
traversal has a conservative 32-level bound; reaching it means fallback, never
truncated dependencies. The original specification identity is preserved.

## Validation and measurements

Run after building the candidate with the qualified native runtime classpath:

```sh
python3 tools/check_operation_inputs.py --case compute-dependencies
python3 tools/check_operation_inputs.py --case compute-dependencies-reseller
```

`ComputeDependenciesConformance` also accepts an optional baseline Connections
archive after the repository root. It checks native inheritance, both branches,
calls inside arguments, complete declarations, local overrides, used constants,
literal data, full validation of invalid unused code, depth/introspection
fallback, forged ordinary data, changed-library compiler rejection, fresh
arguments and stable logical gas with warm caches. It checks custom generated
slots and a derived hook that retains the qualified parent's library but adds
an otherwise unused function call. Its native scenario uses
actual Connections-generated handlers.

`ComputeDependenciesResellerConformance ROOT [BASELINE_ARCHIVES] [REPORT_JSON]`
uses the first existing bootstrap-preparation scenario and the Adventures in
Paradise source unchanged apart from that scenario's declared source patches.
Baseline archives are named `connections.bluepkg`, `clause-documents.bluepkg`
and `clause-reseller.bluepkg`. It measures initialization and `prepareOrder`
separately at the unchanged 10M limit and compares the complete frozen quote.

The feature is **not qualified for adoption in the reseller flow**. Its Documents
hook has a custom planning graph and therefore retains the full path. A diagnostic
projection of the real `prepareOrder` closure also includes `checkPreparation` reads of paths returned by
`processContext`, and `configureSources` can read the whole document or an
arbitrary configured binding. These force the full path. The qualified index
and additional planning still cost gas. Recognizing a safe `bindings.catalog`
read alone cannot prove this whole closure safe.

Publication work is physical CPU/allocation outside contract execution; planning
is charged during initialization; subsequent Compute materialization is charged
per operation. These are reported separately. A smaller isolated Compute is not
evidence that initialization plus one operation is cheaper, and cache warmth is
not a semantic discount. Keep the existing manual optimizations until a real
flow comparison demonstrates a net benefit. Broader proof would require
interprocedural value/branch analysis or a separately specified runtime approach.
