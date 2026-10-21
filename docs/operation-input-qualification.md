# Qualifying the operation input candidate

The authoritative package coverage register is [operation-input-coverage.md](operation-input-coverage.md).
The cross-repository implementation plan is maintained in Business at
`docs/generic-operations-execution-plan.md`.

## Native deterministic suite

Build the complete unpublished candidate before testing. Set `JAVA_HOME` to Java21
and `BLUE_JAVA_CLASSPATH` to the qualified Core native runtime/test classpath. The
classpath must include the Core composition fixtures and the explicitly selected
DefinitionReadV1 implementation. The runtime selection is accessEvents plus that
capability; selecting finalGas as a test workaround is not supported.

```sh
python3 tools/check_operation_inputs.py
```

For an iteration, select an actual named case, for example:

```sh
python3 tools/check_operation_inputs.py --case shipping --case activation-effects
```

The full suite runs both authoring builders, native argument semantics, generated
Activation inputs and effects, all Payment response/request-action effects,
Shipping, provider families, configured additional actions, and Documents/Attachments.
It compiles maintained Java probes into a temporary directory and writes each
command, elapsed time, exit status and log to ignored
`reports/operation-input/qualification/report.json`. The report records the exact
package catalogue, source HEAD, dirty diff digest and untracked file digests.
Use `--report-dir reports/operation-input/<run-name>` to retain separate qualification
runs without replacing an earlier report.
A failed case makes the command fail; an isolated successful rerun is not a full
suite result. No native probe is a substitute for the Business deterministic
Confirm and real-model suites, whose entrypoints live in the Business repository.

## Reproducibility

`tools/build_final_gas.py <package> --check` rebuilds a selected candidate package
in isolation using its pinned import archives, compares every distribution byte
and its dependency lock, and fails on any difference. Run it for every changed
package and the additional support package after the final serialized build.
`tools/sync_catalogues.py --check` checks the generated catalogue views.
Do not run source publication concurrently with native tests reading the catalogue.

## Why the source model changed

Standard operation `request` definitions and their descriptions are now published
from explicit library/function/argument links by the shared authoring helper.
`requestFrom` is removed during publication. Dynamic generators copy those same
native definitions; explicitly mapped public workflows retain their own input
shape instead of guessing that an action argument equals the external request.

Document-level `operationPreparation` and automatic technical bindings were removed.
The model can use unambiguous current technical state, while user business choices
remain explicit. Confirm still sends the exact reviewed request; package public
adapters perform only their declared native representation conversion during
execution. Core and Business do not repair or enrich the submitted request.

The new `blue-definition-read` support package declares an explicit execution
capability for reading an exact native definition reference, including schema-only
fields and empty objects. It is required by the generic generators that read
configured matchers. It extends the 34-package acceptance baseline with one support
protocol; historical BEX/Contracts/Coordination packages and behavior remain pinned.

## Native list representation

A homogeneous native matcher `{type: List, itemType: T}` uses the explicitly
reviewed native list envelope `{type: List, itemType: T, items: [...]}`. A raw JSON
array is a different native value; admission alone does not prove that it matches
a homogeneous typed List. Raw arrays remain supported for native positional list
matchers such as `[T]`. The form constructs the appropriate representation before
review. Prepare and Confirm must not coerce one representation into the other.
Public Access-operation adapters preserve the original internal raw-array caller
ABI while declaring their external typed-list input explicitly.
