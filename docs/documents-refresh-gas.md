# Documents refresh gas investigation

The package fix removes unnecessary definition reads from canonical Documents
refresh handlers. It does not change the Core gas limit, event delivery,
activation checks, source validation, or financial rules.

## Reproduction and cause

Baseline packages: `2ad628b294762179031d2ed11a83d0532213db8b` (PR #31).
Matched Core runtime: `6a44f9bda061c62dc0b5f6bb17291e613110489d`.
The candidate was also tested on Core `964a48f83`.

A parent with two Documents collections receives four events from an embedded
child. Both preparation stores are empty. Before the fix, this exhausts the
10,000,000 gas budget; after it, the transaction commits using **35,451 gas**.
The existing execution limit remains 10,000,000. Since the baseline is truncated
by that limit, this is not an exact measurement of its total required gas.

`refreshProcesses_*` and `refreshEmbeddedProcesses_*` load the entire action
definition before executing `sharedRefresh`. The cost is incurred even if the
function finds no prepared entries. In the earlier hosted diagnostic, definition
walking accounted for 9,565,070 of the exhausted 10,000,000 gas. The latest PR #31
baseline still fails at the same hosted stage despite its commission event filters.
There is no evidence here of an infinite Order/PI event loop.

## Change and compatibility

- `Documents/Refresh Functions` contains the seven functions reachable from the
  canonical `sharedRefresh`. Existing libraries reuse the exact function bodies.
- The planner selects that closure only after checking the immutable canonical
  library identity and every selected function identity. It copies the actual
  action definition's constants.
- Overrides, additional helper dependencies, missing anchors, and replaced
  anchors retain the full action definition. No custom hook is silently replaced
  with the default implementation.
- The existing admission projection uses the same identity-checking helper.
  Its generated function bodies and custom-definition fallback are preserved.
- `$blue:functionFrom` gains an authoring-time function selector. It publishes an
  ordinary exact native reference and introduces no Core execution capability.
- The legacy Customer Orders Bootstrap profile's `providedAdmissionProof` pin and
  provenance are refreshed because that function references Preparation Plan.
  All 106 copied native function pins pass verification.

The changed distribution archives, dependency locks and catalogues are derived
artifacts. Package versions are unchanged; nothing has been released or deployed.
Existing documents keep their pinned definitions. To use this optimization, new
instances must select the rebuilt packages; changing local source does not rewrite
already-created agreements.

## Comparison and tradeoffs

For the same four-event fixture on both tested Core revisions:

- Baseline: `GAS_LIMIT_EXCEEDED`, 10,000,000 gas consumed.
- Candidate: `APPLIED`, 35,451 gas consumed.
- Initialization: 1,850,363 → 1,976,968 gas (+126,605, approximately 6.84%).
  The identity checks and projection are paid once at initialization/planning.
- A custom refresh definition is preserved and remains comparatively expensive:
  the one-event fallback controls use about 1.42 million gas. This fix makes no
  performance promise for arbitrary custom libraries or an unlimited number of
  prepared entries. Refresh still visits the collection's entries.

The selected approach preserves event observation and domain behavior. Broad
filtering would be smaller but could suppress custom `domainNextActions` reactions.
Raising the gas limit would leave repeated library reads in place and change the
runtime budget. Runtime caching can reduce physical work but must preserve logical
gas; the measured gas is identical on the two Core revisions. A general-purpose
function-closure compiler is unnecessary for this bounded canonical optimization.

## Validation

Passed:

- Native four-event regression and five definition variants: canonical, overridden
  entry, overridden helper, replaced canonical anchor, missing anchor.
- Exact function identity comparisons for both generated refresh handlers.
- Existing native admission definition variants, preparation/retry, provision
  validation, source observation, source admission and foreign-source rejection.
- Both package builders' authoring input tests, including inherited function
  selection, exact identity, and rejection of malformed/missing selectors.
- Static refresh and admission call-closure checks.
- Byte-identical Documents rebuild, all 106 legacy Reseller function pins,
  `tools/release.py check`, and `git diff --check`.

The existing `documents-paymentPreparation` case fails with gas exhaustion on
both the unchanged PR #31 baseline and this candidate. It is not counted as a pass
and was not weakened or assigned a larger budget.

## Hosted integration boundary

The matched baseline stops in Agreement during late-guarantor replay with
`GAS_LIMIT_EXCEEDED`. The candidate passes that stage, replays Order and PI,
installs the guarantor's consent, then encounters a separate Core failure when
Agreement receives the Order change that attaches PI:
`SOURCE_BIRTH_REQUIRES_OWNER_COMMIT`.

This occurs on Core `6a44f9bda` without the cancellation clauses and on
`964a48f83` with them. It is therefore not evidence of a refund-rule defect.
The Core guard requires every retained source-completion member to have existed
in its before-snapshot (`ContractCompletions.capture`). Coordination expands the
selected member set to the complete execution unit before loading that completion
(`CoordinationEngine.loadCompletion`). Handling an expanded source graph needs an
owner-commit-aware path; removing the guard or dropping members would weaken
provenance/atomicity checks. No such bypass is part of this package fix.

The hosted probe uses separate seller, partner, customer and guarantor journals,
real provider signatures, a disposable PostgreSQL projection, and the normal
prepare → bootstrap → provide path. It validates a multi-product total of 93.10 USD,
no quote store, and scoped guarantor access that excludes the private Agreement.
It simulates guarantor outcomes; it does not exercise Business UI or a PSP.

A separate control deliberately skips attaching Order to Agreement, while retaining
the same prepared multi-product Order, new-guarantor admission, and cancellation
clauses. On Core `964a48f83` it passes authorization (9,310), capture (9,310), seller
confirmation, cancellation, automatic full-refund request, guarantor refund
confirmation (9,310), Order settlement propagation, and duplicate-cancellation
idempotency. Amounts are USD minor units. This isolates a working Order/PI cycle;
it does **not** qualify Agreement observation or commission accrual/reversal.
Skipping the Agreement attachment is a test control, not a product workaround.

Hosted evidence is retained under
`reports/pr31-reseller-cancellation/{latest-baseline,candidate-complete,latest-core-full,latest-core-detached-order}`.
The matched gas logs, native qualification reports and comparison are under
`reports/gas-refresh`. These are local probe artifacts, not published packages.
