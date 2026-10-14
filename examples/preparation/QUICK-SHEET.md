# Preparation clauses — quick sheet

Unpublished candidate; complete executable sources are next to this file.

| Choose a child | Use |
| --- | --- |
| Payment Instruction | `Attachments/Payment Preparation Clause` |
| Shipment | `Attachments/Shipment Preparation Clause` |
| Ordinary business document | `Attachments/Document Preparation Clause` |

All three use one preparation planner and lifecycle. Domain clauses add the
expected child type, terms, parties and permitted action hooks.

| Authoring choice | Meaning |
| --- | --- |
| `parameters.template` | Complete, fixed child source |
| `obtain: create` | Create that child locally |
| `obtain: provide`, `suppliedBy: seller` | Require that party to supply the initialized, active child |
| `parameters.fieldPaths` | Named preparation inputs mapped to explicitly allowed business fields |
| `bindings.begin` | Named workflow or local business event that starts preparation |
| `bindings.provide` | Authorized workflow that submits the candidate |
| `bindings.resume` | Authorized workflow that retries pending checks |
| `parameters.hooks` | Child-local action hooks, or declared parent dependencies |
| `admissionClause: partyChanges` | Ordinary Amendments clause for admission of an additional authority |

**One request, one obligation.** Start with `{requestId: purchase}` and optional
`values` / `authorityParty`. Provide with `{inResponseTo: purchase,
requirementRef: <prepared source Blue ID>, document: {blueId: <instance>}}`.
Replaying the same request is harmless; changing it is rejected.

**How it connects**

- Local hooks → forward embedding only; the authority need not join the host.
- Parent-dependent hooks → reciprocal embedding, matching primary timelines and
  keys, host authority admission, real read access and effective Activation.
- Missing authority → candidate is retained → exact proposal → real approvals →
  `Amendment Applied` → checked admission → fresh Activation consent → provider
  calls child `attachDocument` → provides updated child → attachment.
- Two payments → two named clauses, e.g. `deposit` and `balance`. Collections are
  not part of this iteration.

**Events:** `Document Preparation Requested`, `Document Provision Requested`,
`Party Admission Requested`, `Document Attachment Pending`, `Document Attached`.
All carry clause/request correlation. They are notifications, not permission.
Use ordinary Connections/Features clauses for further business reactions.

**Read:** `/preparation_<key>` for status, reason and candidate;
`<request path>/requirements` for frozen terms and identities.
`ready` means attached, not paid, shipped, or permanently active.

**Independent authorization:** Activation owns participants and effective access;
Amendments owns approved changes; Mandates owns delegated operations. Preparation
neither grants access nor invents a principal's consent.

**Not supported yet:** arbitrary provider extensions, cancellation/replacement,
keyed child collections, real provider APIs or automatic access-grant acquisition.
