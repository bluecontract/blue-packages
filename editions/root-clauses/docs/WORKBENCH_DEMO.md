# Demo: one source, two clauses, a generated Agreement

## Creation

Business input:

```yaml
type: Reseller/Reseller Agreement
parameters:
  resellerDiscountBps: 1500
  terminationAllowedParty: B
```

Workbench supplies one agreement ID and two distinct authenticated Timeline channels
for Supplier A and Reseller B. It must not supply clause implementations, contract
bodies or the termination/activation flags in Python.

Show a read-only resolution preview first: the base bootstrap and Reseller's
`initialClauses` are visible, but `/activated`, `/terminated`, and generated act/
termination operations do not yet exist. Then initialize normally. The first
stable view is epoch 0 with the live clauses, resolved parameter bindings, generated
root workflows, negotiation state and `activated=false`, `terminated=false`.

## Guided steps and expected results

| Step | Submitted action | Observable result |
|---|---|---|
| 0 | Create and initialize one Reseller Agreement. | One managed document; initial terms use 1500 basis points and B-only termination. |
| 1 | A approves the initial exact review. | A approved, B has not; still inactive. |
| 2 | B invokes amendB with parameters 2000 and A. | `/parameters` listener reconciles features; initial policy now A; prior approval archived/invalidated. |
| 3 | A invokes amendA with a clause binding change: termination.terminateA → `/contracts/endAgreement`. | `/clauses` listener removes terminateA and creates endAgreement; no direct contract patch in the request. |
| 4 | A approves the new exact revision. | One approval; still inactive. |
| 5 | B approves that same revision. | Activated, with exact accepted terms and both approvals; still one document. |
| 6 | B invokes terminateB. | Signed/authenticated input is rejected by accepted A-only policy; business state unchanged. |
| 7 | A invokes endAgreement. | `/terminated=true`; original evidence retained; processor remains ordinary/live. |
| 8 | A sends the same business request in another signed entry. | Idempotent result: no second business termination event or replacement of the original record. |
| 9 | Read state/history, then reload or restart. | Same exact retained outcome, no host-side regeneration on reads. |

Also allow a second creation with `terminationAllowedParty: EITHER` and a different
discount to make parameter-driven composition obvious. The generic processor tests
cover A, B and EITHER seeds; the real provider demonstration uses the sequence above.

The legacy negotiation actions remain available on actA/actB. An additional manual
experiment can propose and accept changed commercial terms rather than using the
draft source editor. Accepting that proposal is still not binding approval. The
termination implementation reads the final accepted policy, not the initial seed.
The supplied processor suite exercises that full negotiation path.

## Presentation

Use source and initialized-state panels side by side, followed by a small binding
table: clause feature, root destination, generated entry, state owner/readers. This
is a UI rendering requirement, not an instruction to alter execution semantics.

Label `/initialClauses` as type defaults and `/clauses` as the instantiated draft
configuration. Label `terminationPolicy.initialAllowedParty` as an initial binding;
after negotiation the accepted terms are authoritative. Show activation and
termination separately rather than inventing a phase field in the Blue document.
The provided inspector derives a display phase without writing it.

## Scope

Exactly two business clauses, exactly one managed Agreement. No Order or commission
is created in this lesson. The earlier tiny Order guard remains a separate reference
so that it does not obscure the requested root parameter/feature-generation demo.
No postactivation clause amendment or automatic state migration is promised.
