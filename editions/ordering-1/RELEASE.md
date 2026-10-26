# Determinism release boundary

This candidate retains the four determinism-only branches and their existing
production defaults. It adds no migration, capability restriction, business
feature or Coordination edition. The scoped comparison is Contracts conformance,
not cross-runtime Coordination interoperability.

## What deployment changes

| Correction | Existing pins | Explicit ordering-1 |
|---|---|---|
| Code-point traversal, graph/first-error order and private JSON commitments | Corrected in Java and MyOS; Python already supplies the reference behavior | Included |
| Lazy BEX list item read before iteration debit | Corrected in Java and MyOS | Included |
| Captured evidence belongs to its captured resolver | Corrected in standalone Java; already present in MyOS/Python | Included |
| Boolean scalar comparison | Corrected in standalone Java; already present in MyOS/Python | Included |
| Constructor prerequisite callbacks, alias prerequisites, enum traversal and count-predicate order | Historical behavior retained; no blanket parity claim | Newly specified and selected explicitly |

Existing pins therefore do not imply identical old/new results. Selecting
ordering-1 does not update an existing document, and installing these branches
does not select ordering-1 for production accounts.

## Exact selections

Every shared runner output contains `selection`, including the exact profile,
Contracts package/protocol/rules, Language package, BEX protocol and gas profile.
The ordering comparison refuses a different selection.

| Selection | Contracts package | Protocol | Rules | Gas |
|---|---|---|---|---|
| Retained 10M, `blue-runtime/2026-10-07-gas-10m-1` | `7wzRNgYTH2vpDfb8HtGVSwNKLAF19tD2GACCQixnh4br` | `Bwi2Fau5NAGx1PpkGSpG1brSKKRX4QeuEGLC3LdfZ6By` | `ESDxi9qNrWrZXChcdcenhHmPY5UPCJXtwihEvTBChGHV` | `contracts-deterministic-gas-4` |
| Opt-in `blue-runtime/2026-10-25-ordering-1` | `BPGMFxDP9GkKuw8949atiXVTQbveh3x6ZmY45TtwUFf8` | `HqeerbZF7TwTXPUXg9k2AL7TC7Ti7HZqSttP6DbTkKCo` | `BWtZLFuUAbC6gPUpZS79Sx5AA3A7GTxDut3bCFS5tE7c` | `contracts-deterministic-gas-6-ordering` |
| MyOS `AccountRuntimes.defaultBindings()` / `accessEvents()` | `AibxCqz62K19mhRWXuWhnZJx6a3o5UXU7sRnAhoUNnFD` | `DM5qF3m5EhA9qA8TRhGUyYDHS1wap1upfCtBuxsQaRXw` | `Dsxv7hUoGTsTod8gPrHo3iC6VJ2sDhXTeZXThx9r6QPG` | Existing FINAL_GAS edition; no new selection |

The runner argument `production` selects `Runtime.current()` /
`RuntimeProfiles.current()`: the retained 10M Contracts profile. It does **not**
mean MyOS's native account default. Its exact output bindings are authoritative.
MyOS's actual default uses existing final-gas Contracts, BEX package
`6L2cQG3oSX4WPkXoTvGXeTEjn41WYnjdNKSo1F61xonc` and existing native dependencies.
It has a separate old-artifact probe. The shared matrix does not qualify that
entire native dependency closure.

## Observed parity by selection

| Shared fixture group | Retained 10M, four runs | Ordering-1, five runs |
|---|---|---|
| Lazy includes, lazy entries, Unicode declarations, ordered events, invalid termination, termination | Complete outputs agree (6 fixtures) | Complete outputs agree |
| Constructor, aliases, text enum, Unicode enum, Boolean enum, text counts, list counts | Differences remain (7 fixtures) | Complete outputs agree |
| Merge order/gas, private JSON digest, first invalid declaration, graph order, terminal state | Agree | Agree |

The retained comparison includes Python hash seeds 0 and 19, standalone Java and
MyOS's vendored runtime. The ordering comparison adds Python seed 7 with physical
cache disabled, with 13 fixtures and 54 budgeted outcomes per run. Comparisons
retain all JSON values/types, traces, rejection points, receipts and list order;
equal full-budget gas alone does not count as parity. The exact profiles and
individual first differences are in the handoff's `profile-matrix.json`.

## Persisted-artifact restriction

The smallest exercised fixture uses three external channel declarations, with
U+E000 and U+10000 names, and one counter update. The exact old runtime initializes
and commits its outcome into a fresh SQLite journal. It cold-reopens and resumes
that journal with the old runtime first. The corrected runtime receives an
unchanged copy. An otherwise identical ASCII fixture is the positive control.

For the retained 10M selection, Java and the actual vendored MyOS runtime show:

| Boundary | Affected Unicode fixture |
|---|---|
| Original and completed document BlueIds | Unchanged; exact Language content still verifies |
| Counter value, status, gas and gas trace | Unchanged: count 1, APPLIED, 826 gas |
| Snapshot commitment | Changes despite unchanged field schema |
| Invocation commitment and receipt identity | Change under the same package/rules pins |
| JSON decoding and SQLite schema | Readable; no schema migration needed |
| Snapshot verification / journal cold resume | Rejected: `INVALID_SNAPSHOT_COMMITMENT` |
| Saved invocation capsule | Rejected: `INVALID_CAPSULE_COMMITMENT` |
| Hash of unchanged retained receipt observations | Does not match the retained receipt hash |
| Retained completion bound to a corrected equivalent snapshot | Rejected: `CORRUPT_LOCAL_COMPLETION` |
| ASCII control | Full outcome, receipt and cold resume unchanged |

Core's actual `accessEvents()` / FINAL_GAS default was tested separately with
the same old-write/cold-reopen/new-read sequence. It also retains the document
BlueId and 826-gas total, and rejects the old snapshot, capsule, receipt and
journal resume with the same errors. Its unchanged retained observations also
hash differently; no new snapshot is involved in that independent hash check.
Its ASCII control resumes unchanged. FINAL_GAS omits gas traces, so this check
compares its gas total without claiming trace equality.
The full exact native package/protocol/rules set is retained in that output.

These checks establish a real compatibility failure, not merely a theoretical
receipt difference. **Do not deploy the corrected runtime over affected existing
histories.** Preserve their exact old runtime and stored bytes until an owner
chooses an explicitly scoped compatibility strategy or separately reviewed
migration. Neither fallback verification nor migration is implemented here.
Passing the rejection regression is not approval to resume an affected history.
An ASCII positive control is not certification of every existing journal.

The captured-evidence regression reproduces two leaked parent witnesses in old
standalone Java and zero after correction. MyOS already reports zero. This
physical-state observation does not establish another persisted-format change;
the report does not infer universal historical compatibility from it.

## Reproduce without modifying original worktrees

Prepare the repository-declared package inputs, including Java's pinned support
sidecar using `tools/prepare_historical_support.py`. With JDK 21, Python 3.13 and
cached Gradle dependencies:

```sh
python3.13 tools/check_old_artifacts.py \
  --java /path/to/blue-java --myos /path/to/myos-core \
  --output /path/to/new-task-owned-output
```

The script extracts the exact reviewed main commits, uses the versioned probe
and Gradle adapter, preserves old artifact hashes, and reports both successful
reads and expected rejections. It never writes into an original checkout or
changes a historical package publication. Full observations, source pins and
machine-readable release decisions belong in the final handoff.

The final release matrix must distinguish code merge, package publication,
new-document use and old-history resume. A successful Contracts matrix alone
cannot approve a production replacement; the integrated Core gate and the
persisted-artifact restriction remain independent decisions.
