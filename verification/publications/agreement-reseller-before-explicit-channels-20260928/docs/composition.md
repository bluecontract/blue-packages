# Reseller composition

The application consists of a root Reseller Agreement, its embedded Mutual
Activation Clause, and an optional Immediate Termination Clause installed after
mutual activation. A is Supplier; B is Reseller.

```text
Reseller Agreement
  defaultTerms                    proposed wording stored on the type
  terms                           settled business terms mirrored at the root
  acceptedRevision                exact terms ID, round, and both approvals
  activation                      managed Mutual Activation Clause
  clauses.immediateTermination    managed termination clause, only after approval
  termination                     final root evidence, initially empty
```

The author copies `/defaultTerms` into a plain object and supplies it as
`/activation/initialTerms`. This is deliberate: inheriting optional proposed terms
would allow a removed clause to reappear through type resolution. A missing
`clauses.immediateTermination` in the actual proposed terms means no automated
immediate-termination right.

During negotiation, `actA` and `actB` operate on the activation document. A proposal
can edit the commercial schedule and add, remove or parameterize the passive
termination terms. Accepting an edit settles it; it does not activate. READY is
not approval. Activation requires both principals' approvals for the same settled
revision and review round.

The root extends the existing Agreement type without modifying that publication.
Its initialization and activation workflow retain the inherited program and add
known-type validation and installation. On consent, it constructs the executable
termination child itself from the approved configuration and authenticated
channels. It never copies negotiated `contracts` into that child and never treats
a name in a clauses map as a native handler.

`terminateA` or `terminateB` then operates on the termination child. Its genuine
completed progress reaches a dedicated Embedded Node Channel. The root validates
context and evidence before committing ACTIVE -> TERMINATED. A guard prevents
late activation progress from reactivating a terminated root. The accepted terms
and activation approvals remain unchanged.

## Test map

| Test | Main assertion |
|---|---|
| 01 | Full requested signed-Timeline story: negotiate addition, activate, unilateral termination, retry |
| 02 | A-only, B-only, EITHER-by-A, and EITHER-by-B on separate fresh agreements |
| 03 | Initially absent clause is still absent after activation |
| 04 | READY and one approval do not activate or install termination |
| 05 | Wrong signer cannot select the permitted side's operation/channel |
| 06 | Wrong revision and caller-supplied party do not grant authority |
| 07 | Exact retry has no duplicate outcome; changed reuse and later requests fail |
| 08 | Late approval or negotiation cannot reopen a terminated agreement |
| 09 | Negotiated permission change invalidates old approval and stale round |
| 10 | Negotiated removal is not undone by inherited defaults |
| 11 | SQLite-backed engine restart retains evidence and retry semantics |
| 12 | Data availability does not grant native support or leak imported aliases |
| Provenance | External notices, forged embedded delivery and an unrelated clause cannot terminate the root |

All business state changes in these tests run in the existing Blue processor and
automatic Coordination engine. `examples/session.py` only creates ephemeral signed
Timelines, publishes/reads content, and submits operations. It is a test fixture,
not a mandatory per-package SDK. No test should manually patch runtime phase,
acceptedRevision, clause state or root termination evidence.

See the overlay's `VERIFICATION.md` for the actual run outcome and remaining
application integration. Browser lesson installation and consumer catalogue
registration are Codex tasks, not changes hidden inside these packages.
