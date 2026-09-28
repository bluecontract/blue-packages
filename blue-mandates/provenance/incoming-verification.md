# Executed verification

**PASS: 86 tests on Python 3.13.5.**

52 new application/native-support test methods and
34 selected unchanged engine tests were freshly executed against
this final package and runtime. There were 0 failures and 0 errors.
Subcases are not counted as extra test methods. The four example runs are additional,
not double-counted tests.

| Suite | Tests | Failures | Errors |
|---|---:|---:|---:|
| support | 12 | 0 | 0 |
| authority | 18 | 0 | 0 |
| evidence | 11 | 0 | 0 |
| connected | 11 | 0 | 0 |
| foundation | 34 | 0 | 0 |

## Package admission and exact identity

19/19 exported definitions passed strict package admission. The generic verifier
checked the native Package identity, exact imports, documentation/specification
content binding, and transitive protocol requirements. This is not by itself
execution support; the native support tests separately prove the opt-in boundary.

```
Package: 6eAzRWrXEpF2mocfZEoSThW4qco9uejrtCuYcFkCZwND
Protocol: GPBbobZsoKSAAbmnxeq5VrPU5GstFaXTmaQR8sJxaB5S
Archive: sha256:873036244589da3dd0fcf638d5b9af95c15df7a8c768f6307157f6e32163ba96
Runtime tree SHA-256: 63d791fc06fd981a889840736f09e5f639b52c3708d408cf13f55701bfb1a667
```

`evidence/final-identity-checks.json` additionally confirms that the frozen spec equals
the packaged spec, the producer runtime binding matches the actual tree, and the
trusted native support binding names this exact Package.

## What was executed

The examples and application tests use real package definitions, Contracts/BEX
workflows, authenticated signed local Timeline Entries, actual native Coordination
eligibility, stable states, retained histories, dispositions and outbox occurrences.
The test helper does not implement lifecycle transitions or grant matching.

Tests cover import-without-support, unknown package rejection and restart binding;
required message fields, Pattern witnesses and pure predicates; actual owner approval,
protected writers, bounded/multi-target grants and no cross-grant mixing; target agent
participation, target delegation policy, revocation, preserved actor identity;
exact typed Request/Response correlation, provider restrictions, Unknown reconciliation,
negative/false results, duplicate callbacks and bare-response rejection;
real child-driven scope changes, target survival, out-of-stage owner progress;
both same-timestamp source orderings, delayed-worker revocation, incomplete-prefix
waiting and SQLite restart. See `docs/test-map.md` and individual JSON/log reports.

The unchanged engine tests include source-driven processing, missing-content recovery,
exact historical attachment, managed admission, publication recovery, independent
producer/consumer scheduling, prefix proof reuse, and legacy Mandate authority/order.
No full Language/BEX/Contracts/Coordination conformance campaign was run in this task.

## Four complete examples

| Example | Established final state |
|---|---|
| Static bounded counter | Count 4: one delegated +2, later direct owner +2; Mandate Terminated |
| Manual Order progression | Order Released; owner acknowledgment changed the scope |
| Provider-gated counter | Unknown then correlated positive Response; count 2 |
| Connected provider-gated Order | Order Released; its events changed scope and terminated the Mandate |

All four examples asserted their expected states. `evidence/examples.json` contains
actual entries, exact emitted occurrences, Request/Response identities and histories.
Eight generated initial source documents are included under `examples/generated/`.
They contain public identities, not private signing keys.

The largest successful history gas value observed in these **four examples** was
**19,486**, under the unchanged 100,000 Contracts ceiling. This is not a benchmark,
not the maximum over all possible Mandates, and not a claim that native host authority
preparation or aggregate user resources are completely metered by Contracts gas.

## Source changes

Three pre-existing Coordination engine modules changed; three runtime files were
added. 367 pre-existing runtime files remain byte-identical.
Language/BEX/Contracts code and gas, signing, scheduling and store implementations
were not changed. The added semantics and all deliberate source-guide adaptations
are documented in `PROVENANCE.md` and `docs/source-mapping.md`.

## Limits of these results

This is a local Python integration preview on the earlier locally rebound Coordination
dependency, not a released or independently certified runtime. No Java parity,
remote provider interoperability, exhaustive concurrent/crash-injection proof,
production authentication onboarding, connector dispatch, credential permission,
external Document Responder executor, private disclosure bridge, aggregate budget,
or legal enforceability is established. A signed local provider supplied test
qualification outcomes; no real model, CRM, REST API or payment service was called.

A successful test suite supports the tested boundaries. It does not make unknown
packages supported or prove arbitrary custom Mandate programs safe to approve.

## Repeat

```
python tools/check_bundle.py
python examples/run_examples.py
python tools/verify.py
```

Check the bundle before deliberately regenerating evidence. Verification runs suites
and validates their common source/archive bindings; it does not refresh package locks
or expected results. `--collect` only reassembles already completed bound reports and
is marked collection-only in its JSON, never described as a fresh test run.

## Extracted-bundle check

Four representative tests were also freshly run from a separately extracted copy:
unsupported-package execution, actual typed Request/Response correlation, connected
provider-gated Order progression, and delayed-worker historical revocation. All four
passed, with zero errors/failures. The imported module path and source/package hashes
were checked against that extracted directory. This is additional verification, not
four extra tests counted into the 86-test suite. The final ZIP includes this evidence
without changing the tested runtime or data package.
