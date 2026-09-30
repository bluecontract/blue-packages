# Validation boundaries and issues caught during construction

Use the machine-readable reports in `../verification` for the final artifacts.
Reports from older reference proofs are not evidence for this candidate.

The implementation was developed against the supplied runtime without patching it.
Testing caught and corrected several relevant constraints:

- Inherited fixed clause binding literals cannot be edited. The Reseller type now
  supplies `initialClauses`, instantiated into live root `/clauses` on initialization.
  There is no automatic type generalization or weakened Language validation.
- A generated channel must exist before any workflow referring to it is installed;
  obsolete handlers are removed before their channels. Atomic rollback does not
  make invalid intermediate patches acceptable.
- Generated lifecycle handlers do not join an already-frozen initialization
  dispatch. A separate post-install revision update invokes setup once the full
  generated implementation exists.
- Reusing one direct external event at two different timestamps is invalid event
  evidence, not a business idempotency test. The local fixture uses distinct event
  envelopes containing the same Operation Request; the Workbench test uses separate
  signed Timeline entries containing the same business request.
- A literal `false` return is not a failure, and returning from one Compute step is
  not a substitute for aborting an operation. Guards use actual failure effects and
  the test suite checks snapshot rollback.
- Early monolithic generation exceeded the existing gas ceiling. Feature placement
  now reads exact blueprint data, avoids hashing expanded template projections, and
  uses small setup/completion definitions separate from the full negotiation logic.
  No gas limit or protocol rule was increased.

The final suite includes package admission, one-root initialization, parameter and
binding amendment, exact-review reset, full negotiation, allowed-party enforcement,
retry semantics and failure atomicity. The headless Workbench test exercises its
real provider/SQLite/worker path and restart, but does not replace a browser test of
the new navigation/card. Codex must register that UI and run browser regressions.

Performance measurements are observed gas for this small candidate, not a proof
of cost proportionality, a production throughput claim, or a maximum supported
clause count. This handoff does not qualify Java parity, arbitrary third-party
blueprints, large Order collections, state migration or postactivation amendments.
