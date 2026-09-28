# Acceptance case map

Each number below corresponds to an executable `test_XX_...` in `tests/test_mandates.py`.
Tests use real package definitions, signed local Timelines, actual Coordination history
and native authority support. They are not a Python reimplementation of the Mandate state machine.

| Cases | Assertion group |
|---|---|
| 01–03 | Importing data does not enable native authority; unknown package rejection; persisted support selection |
| 04–08 | Required message fields and enums; distinct roles; future-predicate preparation; side effects excluded; contextual typed scope |
| 10–13 | Direct owner approval, actual agent identity, Pending/empty scope denial, amount/key/document restrictions |
| 14–18 | No cross-grant field mixing, correct logical target and holder, target source participation, different per-document Timelines |
| 19–23 | Target can forbid delegation; exact reviewed head, no agent self-approval, reset fabricated Active, reject extra lifecycle writer |
| 24–27 | Revocation, prior effect survival and direct owner authority; multi-target grant; invalid new scope rollback; restart |
| 30–35 | Request/Response ancestry, exact request/response identities, causal source; Unknown reconciliation; false/error outcomes; forgery, wrong provider, exact retry |
| 36–40 | Fixed recipe and one attempt; result schema, bare Response not an operation, final-result immutability, owner approval prerequisite |
| 50–56 | Real child-driven scope progression/termination, phase order, forged root event, provider+Order composition, legitimate owner action, manual acknowledgement and early-call guards |
| 60–63 | Both same-time source orderings, earlier/later revocation with delayed worker, incomplete prefix wait/resume, SQLite restart |
| 70–73 | Required-field Pattern witness, invalid witness, strict non-Boolean result and later owner progress, protected future-grant configuration |

52 application test methods execute additional subcases where recorded. Subcases are
not counted as separate top-level tests. The current integration also runs selected unchanged engine tests. Their exact
commands and observed counts are recorded in blue-python/docs/mandates-integration-20260927.md.

The canonical generic example harness (`examples/session.py`, `order_flow.py`)
and 52 package acceptance cases (`tests/test_mandates.py`) live here. Python keeps
synchronized acceptance copies with only local import adapters. From the Python
checkout, `python tools/check_mandates_examples.py` detects drift. Neither runtime
nor standalone package examples import a sibling tests directory. The Workbench
conditional-flag tests are host/application-specific and remain in Python.
