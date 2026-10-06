# Implement the Time package in the native runtimes

Use this new blue-packages/blue-time publication and its exact integration-selection
candidate. Do not rewrite the foundations, weaken strict validation, copy source
from dependencies into the package, or enable arbitrary uploaded executable roles.

Read spec/time.md, docs/runtime-contract.md, examples/two-timers.blue and the
package's fixture tests. Treat fixtures as examples, not an approved production
scheduler. Add the native implementation to blue-python/src and the equivalent
Java runtime, following existing exact package support rather than dynamic code
loading. Register Timer Channel, Schedule Timer and Cancel Timer by exact IDs.
Maintain the complete supported-package closure including Coordination.

Implement custom steps as normal BEX expression evaluation and staged events.
Use existing same-invocation gas and frame semantics, including call and prior
step output. Emit fully evaluated typed messages. Trigger Event and direct
$appendEvent must have the same registration behavior. Do not read a clock in BEX,
introduce afterUs or invent an initialization timestamp.

Integrate committed effects, pending deadlines, wake-ups, per-registration durable
terminal states, evidence verification, ordering and complete-prefix publication
into the existing independent scheduler. Validate effects before their commit.
Use trusted provider history/time evidence, not a client boolean. Register initial
lifecycle emissions without an incoming Timeline entry. Recover missed wake-ups
from durable effects. No separate root/ancestor barrier or graph-wide scheduler,
no in-flight restarts, and no PostgreSQL transaction requirement.

Preserve account-scoped processing, exact historical child consumption, topology
reselection, cyclic group rules, 100,000 gas and user-level budgets. Keep provider
responsibilities to authentication, timestamping, preserving/serving history and
completeness, not business authorization.

Execute all native gates in docs/acceptance.md and actual regression suites.
Add a Workbench lesson using the unmodified two-timers example: initialize,
submit scheduleReminder, inspect the two requests, advance trusted test time,
observe reminder then activation, and show cancellation/replacement. Display
numeric timestamps with units; a human-readable date may be secondary UI only.
Tests may inject trusted time/proofs; production must not expose that as a user
operation that forges elapsed time.

Report exact package IDs, commands/counts, failed tests, unqualified paths and
runtime approval changes. Do not claim Java parity without running it, or automatic
wakes/durable recovery based only on the package fixture. Update source/publication
pins deliberately under a new release if semantics change; never rewrite bytes
under a published BlueId.
