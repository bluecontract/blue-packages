# Root-clause edition release checks — 30 September 2026

All 201 Python test methods pass, with no skips: Language package 24, BEX 13,
Contracts 13, build tools 16, Mandates 52, Time 35, legacy Reseller 21,
Immediate Termination 3, and the root-clause edition 24.

The shared release checker validates all 18 selected archives. Semantic package
witnesses and the unchanged native support closure pass. All four root-clause
source builds reproduce the supplied archives byte for byte. No existing
published archive or legacy export identity was replaced.

The initial three foundation runs failed because locked builds with an empty
source URL picked up the local Git remote. The builders now distinguish an
omitted URL from an explicitly empty URL. Complete reruns and three independent
regressions pass; expected archives were not regenerated.

Machine-readable results are in
[release-gates-20260930.json](../editions/root-clauses/verification/release-gates-20260930.json),
with the complete root-clause cases in
[tests.json](../editions/root-clauses/verification/tests.json).
No Java campaign is claimed. Detailed disposable logs remain outside this repository.

The final integrity check also detected the source inventories still describing
the previous compiler/test files. Exactly nine reviewed tooling/test entries were
updated. Their original bytes and all three original checksum inventories remain
in [the review ledger](../provenance/build-reproducibility-20260930/revision.json).
Published archives, data Sources and test business expectations are unchanged.
