# Executable clause tutorial

Read [the complete handbook](../../docs/clauses-tutorial.md) first. These sources use
the canonical root package set. They are local fixtures, not deployment credentials.

| Source | What the walkthrough verifies |
| --- | --- |
| `01-hello` | Requests, typed and filtered events, a channel signal, local change, and one-time handling. |
| `02-embedded` | A selected embedded document, a collection, and path-boundary isolation. |
| `03-atomic` | Before/after rejection rolls back; conditions and once behave as specified. |
| `04-native-steps` | A native multi-step workflow publishes an event consumed by a clause action. |
| `05-first-clause` | The smallest complete callable Hello document. |
| `06-service-desk` | Quotes, counters, stale-edit checks, state transitions, frozen instructions and follow-ups. |
| `07-work-items` | Two original clause factories and two independently scoped listeners. |
| `08-contributions` | Participant channels and two locally owned composable features. |
| `09-collections` | Two embedded collections with separate event families. |
| `10-connected-factories` | Two simpler connected factories; operation routing to a created child. |
| `11-consulting-terms` | Activation, mutually approved amendments and controlled termination. |
| `12-english-lesson` | A provider-neutral conditional payment with an operation installed in PI. |
| `13-design-milestones` | Idempotent creation of two independently payable child documents. |
| `14-timers` | Native test: signed completeness, first/latest event timing, cancellation and fixed deadline. |
| `15-access.template` | Native test: real signed access grants, revocation blocking and restored operation. |
| `16-manual-consulting` | Manual transfer reporting, receipt confirmation, duplicate/conflict handling and refund. |
| `17-acme-milestone` | Illustrative bank method, condition workflow and separately confirmed financial outcomes. |

The fifteen `.case.yaml` files are executable instructions for the existing Java
`CompositionExamples` runner. They are not part of the Blue language itself.
Expected `FAILED` rows are intentional negative tests. They must preserve the
previous snapshot and emit no committed events. Every input is replayed; selected
steps additionally restore their starting snapshot into a fresh processor.

`14-timers.blue` uses the controlled clock in `ClauseTutorialTest` and receives a
real Timeline Channel from that fixture. `15-access.template.blue` intentionally
contains empty provider-specific placeholders, filled from real local provider
responses by the same test. Neither should be submitted unchanged as a production
schedule or access configuration.

Run from the matching Core branch:

```sh
./runtime/gradlew -p runtime :blue-core-service:test \
  --tests blue.core.ClauseTutorialTest --no-daemon
```

Or run one ordinary case directly against this repository:

```sh
./runtime/gradlew -p runtime :blue-core-service:paymentFamilyExamples \
  -PbluePackagesDir=/absolute/path/to/blue-packages \
  -PpaymentCases=examples/clause-tutorial/05-first-clause.case.yaml --no-daemon
```

See also the larger [payment-family applications](../payment-family) and the
[coverage index](coverage.json). The index covers all exported clause descendants,
including base types and internal helpers; it does not claim exhaustive coverage
of every parameter combination. Runtime evidence belongs in Core's ignored
`reports/` directory and must identify the tested source revisions.
