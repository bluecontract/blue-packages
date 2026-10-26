# BEX staged list previews — unpublished specification correction

**Status: UNPUBLISHED.** This document specifies the `$resultValue` correction
implemented in MyOS Core. It changes the rules described in §9, §10, §23 and
§25 of [the final-gas specification](bex-final-gas.md) for that implementation.
It is not selected by `blue-package.yaml` and does not amend an existing
content-addressed publication. The archived specification and its executable
algorithms retain their historical sparse-overlay behavior; they do not implement
this correction. No new BlueId, package publication, runtime edition, pin change
or migration is introduced here.

## Ordered list projection

`$resultValue` MUST project the invocation's accumulated patches in append order
onto its selected starting document. At a List target:

- `add` inserts before an existing index, or appends at the current length or `-`.
- `remove` deletes an existing element and shifts later indices down by one.
- `replace` requires an existing index and replaces that element without shifting.

Numeric indices MUST use canonical nonnegative decimal syntax (`0` or a nonzero
digit followed by digits). Leading zeros, negative indices and out-of-bounds
positions fail when projected. `-` is valid only for an `add` at the final path
segment. Intermediate list segments MUST identify existing elements. Every patch
uses the structure left by preceding patches, including changed list lengths.

Starting with `[A, B, C, D, E]`, two `remove /queue/0` proposals therefore make
`$resultValue: /queue/0` return `C` and `/queue` return `[C, D, E]`.
An absent read still returns `undefined`; it cannot supply an add/replace value.
Object overlay rules, including missing-parent construction, remain unchanged.
`$pointerSet` retains its assignment/sparse-list semantics, including its existing
undefined holes; this correction does not turn it into a structural patch API.

## Invocation state, persistence and metering

Each invocation MUST maintain an independent projected root and applied-patch
cursor for each selected starting view (`canonical` and `resolved`). A read
projects only the unapplied suffix. Repeated reads without new patches MUST NOT
replay projection. Functions share the invocation's accumulator and projected
state. Appending alone does not project a patch; an unexecuted read does no work.

Projection MUST copy the containers along each changed path and preserve already
exposed roots and descendants. Untouched subtrees, including captured lazy host
values, remain shared. Replacement-value copying keeps the existing overlay rule.
This state belongs to one invocation and MUST NOT be reused by another execution.

Every read still pays `resultValueRead`, performs its requested lookup and invokes
the configured host document reader. A cached projection does not waive missing
capabilities, resource failures or host logical-read obligations. The resolved
view still requires its supplied snapshot. This correction installs no definition
view capability and does not extend an existing definition view to staged state.

Object copying retains the existing ordered-key/member/text charges. A list copy
MUST charge `valueMember` for its current length before reading or copying its
elements. Existing expression, statement and append charges remain; no new patch
tariff is added. Scalar metering, shared/local limits and failure behavior remain.
Removing repeated projection work and changing list lengths can change total gas
and receipts. Historical gas/receipt equality is not promised for affected programs.

## Host boundary and implementation evidence

`$document` remains the starting snapshot of the current Compute. The preview
does not publish, generalize, validate every Contracts object rule or invoke
Document Update reactions. For a valid changeset on the same starting value,
its structural list result matches native application when no additional
reactions intervene. An explicit returned `changeset` can replace accumulated
proposals; reactions can change the next Compute's actual document. Neither is
simulated by the preview. Effects, captured `$changeset`/`$events` values and
function behavior otherwise keep their existing rules.

The implementation and regression tests are in MyOS Core revision
`2992f6c6a92db8c9d2efbda8d923dfefa9a9daa0`:

- `runtime/blue-bex-core/src/main/java/blue/bex/Engine.java` (`Invocation.read`)
  and `Values.java` (`projectPatch`).
- `runtime/blue-bex-core/src/test/java/blue/bex/ResultValueTest.java` and
  `runtime/verification/src/test/java/blue/contracts/ResultValueTest.java`.

This document records their intended contract, not a claim of Python-reference
parity or completed publication qualification. Published identities, frozen
algorithms and historical vectors remain unchanged. Packaging this correction
would require a separately reviewed specification identity and host compatibility
decision; this documentation change performs neither.
