# Agreement performance edition

Candidate `root-clause-performance-20260930-1`, version
`0.2.0-preview.clause-performance.1`. The original root-clause archives remain
in `../root-clauses` unchanged. Foundation dependencies are reused by exact locks.

Agreement's installer functions are reusable inherited Compute steps, avoiding
repeated Compute Definition import traversal. The initializer transfers the exact
initial-clause value by BlueId using ordinary BEX object construction. The existing
clause programs remain ordinary Compute Definitions; a prototype which also made
those inherited steps increased validation/retention time and was rejected.

Initialization, patch order, reconciliation, ownership checks and all business
choices remain in Blue. No saved Agreement is retyped or migrated. Logical gas
remains fully metered by the unchanged runtime. The lower gas target is a measured
engineering objective, not a new limit or a changed tariff.

Rebuild with `python tools/build_candidates.py`; check determinism with
`python tools/build_candidates.py --check`; run the inherited 24 compiled tests
with `python tests/test_root_clauses.py`. `BLUE_SOURCE_WORKSPACE` names the common
parent of the Python and packages checkouts. `tools/verify_candidates.py` checks
exact dependency locks, retained legacy exports, foundations and original archives.
Reports under `verification/` identify their tested inputs. Python's performance
report and raw Workbench campaigns distinguish engine-only and new-edition results.
