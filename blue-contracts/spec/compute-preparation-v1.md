# Compute preparation V1

Status: experimental, explicitly installed runtime rules. Not a published package,
default runtime, or adoption qualification. These rules extend the final-gas
Contracts runtime; demand-scoped Contracts is outside this candidate.

## Selection and compatibility

A fresh runtime explicitly installs these exact rules through a non-additive
runtime marker. The marker participates in snapshot, completion and replay
bindings. A runtime without it must reject snapshots requiring it, and vice
versa. Existing final-gas selections retain their exact behavior and charges.
Package labels, document fields and physical caches cannot enable this policy.
There is no automatic account migration or change to the 10,000,000 gas maximum.

## Complete validation and observable state

Resolve the current definition operand using the ordinary native path and
specification checks. Prepare and compile the complete effective library, applying
local functions and constants before BEX validation. Preserve native syntax-cycle
rejection, all argument declarations, invalid unused code rejection, recursive
call graph rejection, required content and contextual native constraints.
Compilation and its structural validation consume physical resources but no
semantic preparation gas in this edition. A host capacity failure remains
incomplete execution; it never proves a valid program.

Do not rewrite any document, definition or contract. Reads through $document,
$currentContract, definition reads and other handlers retain the complete original
library. Every execution uses fresh arguments, context, reads and effects.

## Required preparation units

The existing BEX compiler validates every function and records static calls and
constant references while doing so. Start at the selected entry, or at the root
body if there is no entry, and take the complete transitive call closure. Include
both branches, calls in arguments and constant path expressions. Quoted literals
are data, not executable calls. An entry suppresses root execution as in BEX.

For every required shared constant and function not overridden by a local slot,
prepare its complete native subtree, including complete argument declarations.
Keep each required constant in full. Constants are visited first, then functions;
within each category use sorted names. Local program execution and ordinary BEX
tariffs remain unchanged. This is static dependency selection, not a promise to
charge only the branch selected by current argument values.

Before considering each shared unit, charge one Contracts objectMemberRead for
its lookup. A logical preparation key is the canonical wire encoding of:

    (managed member, contextual definition Recipe key, field, name,
     contextual selected-unit Recipe key)

The invocation's exact installed runtime rules bind this ledger. Recipe keys
include exact contributions and native requirements; JVM addresses, physical
captured-view identities and whole-document revision IDs are not ledger keys.
On a first use, perform the existing recursive definition-visit charges on that
unit, checking every charge before the corresponding work. Add its key only after
successful completion. On reuse, omit only that unit's preparation visit. Resolve
and validate the current complete effective program on every execution regardless
of the ledger. Changed definition contributions or requirements yield new keys;
fresh call values do not change an unchanged shared unit's key.

Unused units have no preparation-visit charge. Manifest opens still share the
ordinary invocation ledger. No instruction, event, permission check, data read,
write or budget check is made free by a preparation hit.

## Lifetime and replay

The preparation ledger belongs to one ContractRun, including events drained in
that invocation. Independent invocations start empty. A fork copies the ledger
by value; discarded branches cannot credit other branches. Sorted preparation
keys participate in the logical continuation commitment only for this policy.
Cold and warm execution of the same input, timestamp and exact runtime selection
must produce identical gas, outcomes and receipts.

No compiled program or deferred value is shared across invocations in this
candidate. Avoiding repeated physical projection/compilation is a separate
optimization; this policy alone does not establish a CPU or latency speedup.

## Qualification boundary

Require small counterexamples for unused code, repeated preparation, complete
validation, local overrides, entry selection, changed requirements, member
isolation, fresh arguments, observer reads, budget rollback, fork isolation and
cold/warm replay. Compare initialization and real Reseller operations separately
on the same packages and runtime source, retaining full business outputs.

Before adoption, qualify the entire receive/completion lifecycle, exact Core
account runtime selection and resource admission for large compilation inputs.
Full-library validation still costs CPU, including at first use; smaller charged
gas does not establish lower physical cost or authorize an unbounded compiler.
