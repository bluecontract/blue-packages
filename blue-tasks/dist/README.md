# Native Tasks — clause-composed final-gas edition

This package is selected by PACKAGE-SOURCES.json for reproducible archive generation.
It uses the current final-gas dependency edition. Publication is identified by the
reviewed collection release tag; Core adoption and agent execution are separate
release steps.
The separately reviewed M0 prototypes remain unchanged under verification/task-mvp-m0.

`Task` is the plain domain base, extending `DocumentsDomain/Document`. It declares
instructions and root owner/performer Timeline Channels before bootstrap, with no
clause initialization or automatic work issuance. `Task with Clauses` extends
`Task` and adds the same opt-in root-local clause initialization and amendment
wiring as `Agreement with Clauses`. Add Work, launch, termination and other
compatible clauses to this reusable host; the supplied examples select it.

Execution is driven by the Task family's native Work Requested event and report
protocol, not the presence of a `clauses` field or one concrete Task subtype.
A plain Task can supply its own workflows implementing that protocol. The event
alone does not replace performer authority, request identity or report validation. Work Requested and Report Accepted
retain the native Events Request/Response ancestry. There is no Task Activation,
mandatory authored taskId, Business session requirement, or task-kind enum.

The M1 implementation adds one Work ledger owner, package-owned request/report
behavior, separate initialization/manual policies and native final-report
termination. Request slots remain individually pending/final and are not pruned;
latest report rotation must preserve original content and old finality. The single named `parameters.reportRequest` success request definition is carried
unchanged by exact native BlueId into `reportSuccess.request` and the shared
validation function. Its explicit required envelope declares nonempty Text
requestId, Text status with the singleton succeeded enum, and a required result.
Work rejects missing or weakened envelope invariants. Result specializations and
additional narrowing stay in this one discoverable definition; its name label
does not create result type ancestry. `reportFailure` has its own package-owned
matcher requiring requestId, failed status and nonempty Text error. Its three
business fields exclude result and extras. Both performer operations call one
contributed `taskReportFunctions` Compute Definition for
slot/finality validation, retention and accepted-event emission. Native validation
remains mandatory. Launch functions require the exact supplied Work clause type
and matching ledger owner; arbitrary Work subtypes are outside this preview.

This unreleased preview replaces the single `report` operation with `reportSuccess`
and `reportFailure`. The pinned Language has no conditional union schema; ordinary
BEX value projection must not copy away definition holes. No Core schema extension
or Business-side replacement matcher is introduced.

Qualification targets are TASK-01–TASK-21 and native REF-01–REF-04 from Business
canonical design revision ccf1e0ff09c6e66fdf8954bd9d2c2f1ef00311ce. Event, delegated
Order and report-relative timer products remain later stages. Qualification uses isolated tests against the exact exported definitions.
Selecting this archive does not deploy Core or change an owned live runtime.

Report acceptance has no package-level byte-size cap. Both successful and failed
reports are validated against their native matcher, request identity and finality.
Host execution still follows the selected native runtime's resource accounting.
Prior 0.1.0-preview.1, 0.1.0-preview.2 and 0.1.0-preview.3 archives are retained under
`releases/` with their exact bytes; this new publication does not rewrite existing
documents or reports. The new plain Task has a new content identity; consumers
must recognize its ancestry while retaining historical Task identities.

Native workflow tests cover successful and failed reports above the former 32 KiB boundary, finality, replay,
manual/out-of-order reports, and native termination. Bootstrap and complete case
tests also use distinct native accounts with genuine participant Timeline
Channels, including cold reopen of the same SQLite journals and retained keys.
These checks do not qualify HTTP/Cognito deployment or existing-account adoption.

The owner clarified configuration immutability on 2026-10-09: supplied MVP Task
types and clauses expose no configuration-editing operation. Native amendment and
clause-change paths reject edits atomically. This guarantee does not cover
arbitrary additional author-written BEX workflows. The existing native rejection
assertions remain required; no Task-specific Core policy, generic protection
primitive or editing-UI restriction substitutes for them.

`examples/` contains complete source and case inputs for initialization/human and
manual/out-of-order scenarios. They are draft qualification inputs and are not
in the default Core gallery or exported catalogue yet. Root channels come from
Task and must be genuinely bound by participant bootstrap. Ordinary workflow
unit runners may bind their own test transport only when reporting that narrower
scope explicitly.
