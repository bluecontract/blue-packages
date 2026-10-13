# Native Tasks — M1 preview

This unpublished preview is selected by PACKAGE-SOURCES.json for reproducible
archive generation. Core catalogue adoption is a separate reviewed change.
It is not a published release or a claim of complete application qualification.
The separately reviewed M0 prototypes remain unchanged under verification/task-mvp-m0.

Task extends DocumentsDomain/Document with Clauses and declares root owner and
performer Timeline Channels before bootstrap. Work Requested and Report Accepted
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
contributed `taskReportFunctions` Compute Definition for bounded report size,
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

The 32 KiB bound is applied to the full canonical report envelope by a versioned
native measurement intrinsic; the comparison and failure decision remain Blue.
The draft descriptor is included as exact content. Explicit native runtime
selection is required. The capability implementation has been independently
reviewed and committed in Core. Core exposes explicit registration execution
selection for new documents in eligible existing accounts, with local API/SDK
qualification. This package still requires separate Core catalogue adoption, release approval
and coordinated live qualification; it does not migrate historical documents.
Current/historical default bindings and the owned application journal are unchanged.
Native workflow tests cover exact success/failure boundaries, finality, replay,
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
