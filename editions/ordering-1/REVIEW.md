# Determinism-only extraction, 2026-10-25

This is an additive, explicitly selected **Contracts** correction. It is not the
broad determinism candidate, a production catalogue replacement, or a new
Coordination/authority protocol. Existing default selections and immutable
publications remain in place. The new archive is a local review artifact, not a
registry publication.

## Reviewed baselines

All four branches start at the owner's local `main`. Read-only fetches failed
with SSH authentication errors; no claim is made about a newer remote main.
Original dirty worktrees and the previous candidate branches were preserved.

| Repository | Local main | Excluded broad candidate |
|---|---|---|
| myos-core (`myos-aws-test`) | `94b0788c1c7167d2a6e60c5863af515626e82a6a` | `857fbcaa4a9aea7504081270dac47fdb8a397b04` |
| blue-java | `96931942c6c077bbc41538c5296076863898ab92` | `cb22cc62ba78323a48c997ee3004047840b166dc` |
| blue-language-python | `c6ceb3ad260a3914d44a1f36d59aca018ec0ada1` | `61d32eb8d1165e2e9b086739f1e4904f877f0ac8` |
| blue-packages | `b59fcf08121d29a2171c50e606004dd7d7c93e2f` | `eb5b500180ce1ccb98e937c3a6e6128bcc816933` |

MyOS executes its own `runtime/` modules. Its patches were applied individually,
not by replacing that directory with standalone Java. Existing newer MyOS
bindings, timers, D15 support and other main-branch work remain intact.

## Retained corrections

A denotes an implementation correction; B denotes the minimal new normative
rule, publication, binding or regression fixture needed to resolve an ambiguity.
The existing executable appendices remain authoritative where already explicit.

| Class | Reproducer / first divergence | Rule and correction | Affected implementation |
|---|---|---|---|
| A | Declaration names U+E000/U+10000, both invalid: Java reports `badSupplementary`; Python reports `badBmp` | Contracts uses code-point traversal and first-error precedence; Language's separate UTF-16 ordering is unchanged | Java, MyOS |
| A | Merge-sort input `a`, U+E000, U+10000 with orders 2,0,1: Java costs 8 versus Python 12 | Use the specified initial code-point order before the metered stable merge; use it for Contracts graph/member traversal as well | Java, MyOS |
| A | Private `unicode-audit` record: Java digest begins `d7bed8e3`, Python `8e5e440c` | Private Contracts JSON keys use code points. The Language BlueId codec is unchanged | Java, MyOS |
| A | Lazy `$includes` trace index 46 and `$objectFromEntries` index 45 debit `forEachItem` before `listItemRead` | Existing BEX executable rule fetches the item before debiting iteration | Java, MyOS |
| A | Boolean enum produces Java `FAILED` at gas 241 | Boolean scalar comparison is not numeric conversion; only the prescribed scalar debit applies | Standalone Java; already fixed on MyOS main |
| A | Reading a captured reference view writes witnesses into its parent scope | Retain the captured evidence owner and prepaid synthesis identity; reuse must not depend on physical cache state | Standalone Java; backport the narrow existing MyOS correction |
| B | Constructor at budget 245 consumes 245 or 234 depending on Python hash seed; rejected debit changes from 1 to 18 units | Queue reference prerequisites by exact BlueId, preserve occurrences, and construct inline slots bottom-up | Python, Java, MyOS, new edition |
| B | Invalid aliases report `Integer` or `List` | Explicit itemType/keyType/type/valueType first-error order | All, new edition |
| B | Enum gas 665/657 or Unicode enum 657/665 | Traverse typed scalar keys in unsigned UTF-16 order; preserve authored lists and group order | Python needs the ordering correction; Java/MyOS already traverse these keys in that order |
| B | Text/list count trace first differs at index 81/114: 2 versus 3 limb units | Explicit minItems/maxItems/minFields/maxFields/minLength/maxLength order, without a sorting charge | All, new edition |

The canonical `work.py`, embedded executable appendix, source inventory and
installed Python code are byte-bound. The builder uses the existing native
package builder. All gas weights, the 10,000,000 ceiling and receipt schemas stay
unchanged. Constructor/alias/count/enum order changes are gated on
`contracts-deterministic-gas-6-ordering`.

## Identity changes

`selection.json` is generated, never hand-assigned. Only Contracts is rebuilt.
Its specification/protocol/package identity changes directly because of the
ordering rules and executable source. Its exported definition identities change
transitively through their specification metadata. `identity-changes.json`
lists every changed export. Language and the retained 10M BEX archive are exact,
unchanged inputs. No Coordination, Mandates, Time or business package is rebuilt.
The root package catalogue and all historical archive bytes are unchanged.

## Explicit exclusions and compatibility boundary

Excluded candidate hunks include new Activation/admission/access recovery,
payer channels and business clauses, channel-conflict policy, receiving or
termination eligibility, dispatch outcomes, Execution Requirements/governance,
proof-delivery/ZK policies, new D15 work, storage/migrations/fleet/scheduling,
performance work, tariff/ceiling changes and removal of delegated execution or
timers. Existing versions of such features already on a selected main are not
reverted. Candidate branches remain separately available.

No default is switched to ordering-1. The explicit selection is a Contracts-only
conformance edition; it must not replace a production Coordination selection.
Standalone Java and Python retain delegated execution; MyOS retains its native
Mandates and timers. Standalone Java and Python baselines do not contain the
MyOS timer implementation. This work does not invent one or claim timer parity.

The implementation corrections to already specified private JSON/Unicode order
can change previously nonconforming Java receipts, including under old pins.
A new edition name does not make those old receipts replayable. Preserve them;
there is no migration or reinterpretation of stored evidence. Existing ASCII
stored-state and pinned-edition paths are exercised by compatibility tests.

## Verification and limits

`conformance/determinism/cases.json` is the one shared input corpus. Each runner
uses exact published identities, event `{}`, timestamp 1 (terminal follow-up 2),
and identical budgets. `tools/check_determinism.py` checks full JSON types,
values, ordered outputs, traces, rejection details, snapshots and receipts. It
also verifies the package copies and source inventory. No semantic fields are
normalized away. Exact-gas and one-below cases assert atomic rollback.

The corpus includes enum/constructor/count/alias cases, Unicode declarations and
graphs, multiple invalid fields, lazy collections, ordered emitted events,
failed termination rollback and a successful terminal-state follow-up. Physical
variants cover Python process hash seeds, cache disabled/enabled, reused runtimes
after unrelated work, Java cleared caches and cold serialized snapshot replay.

This proves those Contracts cases, not all determinism or cross-runtime
Coordination interoperability. Existing authority, receiving, history, timer and
restart tests qualify preservation within each baseline. Cross-runtime
Coordination receiving/acquisition schedules under a shared new dependency
closure remain unqualified. No publication/deployment is authorized by these
results. Full Core validation was attempted but its disposable PostgreSQL
fixture did not become ready; CI and full integration remain release blockers.

See the local handoff for exact tested commits, output identities, first-divergence
controls, command logs, patch files, hunk disposition inventory and final counts.
