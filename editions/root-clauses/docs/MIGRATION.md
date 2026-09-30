# Package migration and compatibility

The candidate versions use `0.2.0-preview.clause-bindings.1`. They are new immutable
packages and new root-local types, not replacements under existing BlueIds.
The complete exact package and export identities are recorded in
`../verification/candidate-packages.json`.

## Preserved legacy exports

| Package | Old export | Candidate alias for exactly the same type |
|---|---|---|
| blue-agreements | Clause | Embedded Clause |
| blue-agreements | Agreement | Embedded Agreement |
| clause-mutual-activation | Mutual Activation Clause | Embedded Mutual Activation Clause |
| clause-immediate-termination | Immediate Termination Clause | Embedded Immediate Termination Clause |
| agreement-reseller | Reseller Agreement | Embedded Reseller Agreement |

All other old exports retain their names and identities. The candidate's new
short names select the new root-local types. `package-integrity.json` verifies
all 20 original export identities, including the renamed aliases.

Do not rewrite already-running source documents, their accepted revisions, or
historical type references. Keep their old package editions and content accessible.
Selecting a candidate for a new authoring session is not a migration of an existing
session. Different packages can be mounted under explicit edition-specific prefixes
when the UI needs both at once; dependent namespace imports remain explicit.

The candidate installer does not migrate an existing embedded activation child or
termination process into root state. Such a live migration is a separate business
and execution transition, outside this handoff.

## Native Runtime selection

Language, BEX, Contracts and Coordination archives bundled under `blue-packages`
are byte-identical to the input archive. The host's supported protocol set is not
changed. Candidate types are ordinary business data and existing Compute programs.
No Python/Java native clause dispatcher or per-package SDK is required.

Mount the exact candidate `.bluepkg` files as data with the current Runtime support
check. Persist their verified content closure so that workers and restarts can
resolve the same IDs. Do not just install aliases in the request thread and assume
another worker or a restart will know the definitions.

The supplied Workbench adapter does this explicitly. When integrating long-term,
put the edition selection in the application's package connection configuration;
do not hard-code the handoff's temporary filesystem path.

## Source repository changes

The four candidate project directories contain full sources, manifest, lock and
dist outputs. Use a feature branch and preserve published historical artifacts.
The source generator is a maintenance convenience; build and runtime consumption
use the generic Blue package format and ordinary APIs. It is not an SDK required
for end users, and its outputs do not depend on a generated Python client library.

`tools/build_candidates.py --check` reconstructs the candidate archives using the
uploaded workspace's generic publisher and compares bytes and exact locks. The
input source checkout is not modified by the handoff's build or tests.

The optional `author_candidates.py` reconstruction helper reads the original
pre-integration snapshot to preserve legacy definitions. Do not run it against an
already-overwritten business-package workspace. Normal rebuilds use the shipped
ready `.blue` sources through `build_candidates.py` and do not require reauthoring.
