# Qualifying the operation input candidate

The authoritative package coverage register is [operation-input-coverage.md](operation-input-coverage.md).
The cross-repository implementation plan is maintained in Business at
`docs/generic-operations-execution-plan.md`.

## Native deterministic suite

Build the complete unpublished Access Events candidate before testing. Demand
qualification is deferred until reactivation; there is no edition selector. Set `JAVA_HOME` to Java21
and `BLUE_JAVA_CLASSPATH` to the qualified Core native runtime/test classpath. The
classpath must include freshly built runtime JARs and the Core composition fixtures and the explicitly selected
DefinitionReadV1 implementation. The runtime selection is accessEvents plus that
capability; selecting finalGas as a test workaround is not supported.

```sh
python3 tools/check_operation_inputs.py
```

For an iteration, select an actual named case, for example:

```sh
python3 tools/check_operation_inputs.py --case shipping --case activation-effects
```

The default suite also runs `access-events-behavior`: actual native Activation consent,
access denial/recovery, observation gating, Clauses recomposition and the removed
admission-timestamp cutoff regression. All selected native cases use Access Events.

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
`$blue:requestFrom` is a reserved package-authoring instruction and is removed
before native publication. Its value must contain exactly `definition`, `function`
and `argument`. It is resolved and validated even beside an explicit `request`;
that explicit request remains authoritative. The reserved namespace applies to
source templates as well as operation declarations. Ordinary `requestFrom` keys
are business schema or BEX data, including objects shaped like a former link;
they are never interpreted, removed or rewritten. Existing authoring links must
use the reserved spelling; there is no heuristic compatibility fallback. Dynamic generators copy those same
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

## Review corrections

Connections retain the exact selected request provenance: named connections use
an explicit action binding or its inherited default, while `_automatic` uses the
selected type action or configured parameter action. No action-level fallback
supplies a matcher to an unrelated named connection. The `connections-automatic`
case initializes both action sources, checks the installed matcher, preserves an
explicit empty matcher and a genuinely absent matcher, then executes the generated
operation and asserts its native effect.

Both `helper-final` and `helper-payment` additionally qualify an ordinary required
`requestFrom` business field and execute BEX literal data with the former link
shape unchanged, alongside valid and invalid reserved authoring instructions.


The `source-binding` case initializes actual independent source and receiving
documents, approves their owner, then executes the generated binding workflow.
It covers typed reference, typed path, both supplied fields, inherited concrete
sourcePath, missing/uninitialized-source rejection and legacy raw reference/path inputs. The clause's internal adapter
removes only the nominal input root type before reading defaults, so inherited
abstract optional fields do not become supplied values. It retains the exact
source publication and does not mutate the test input object. This native gate does
not establish HTTP transport byte preservation. Document-reference prose belongs
on the enclosing input: adding a child description can decorate an otherwise
unchanged referenced document and change its effective native identity. Initialization is checked by the execution validator; the input document field
must not structurally intersect and change the supplied reference identity.

The expanded `source-binding` suite covers cyclic exact references, history,
replay, guard rejection and routing. Focused cases are `source-binding-cyclic`,
`source-binding-public`, `source-binding-history`, `source-binding-replay`,
`source-binding-guards` and `source-binding-routing`. The public case uses actual
DocumentClause prepare/configureSources and the generated requestFrom matcher,
then binds the supplied cyclic source; it does not substitute a handwritten matcher.

## Admission before commercial activation

`admission-provision` is an unconditional native scenario; it needs no retained
capture. Run it against Java 21 and the Core runtime/test classpath described above:

```sh
python3 tools/check_operation_inputs.py --case admission-provision \
  --report-dir reports/admission-provision
```

The fixture uses an inherited-transport Order prepared by a parent Documents
clause. Its initial Activation profile explicitly permits preparing/providing a
nested document, approving that document's admission, and the two generated
admission-update channels before commercial activation. Consent is deliberately
absent from this allowlist: the generated consent registration must authorize it.
The nested document requires a guarantor. Actual owner approval and guarantor
consent admit that party while the Order remains inactive, at Activation revision
2 and clause-runtime revision 1. The frozen original roster has two parties and
the candidate has three, so outer `provideOrder` exercises the added-party branch
of `providedAdmissionProof`, not its unchanged-roster early return.

The parent must retain the inactive candidate as `awaiting_activation`. After
actual seller/customer approvals, provision selects the active Order. Repeated
provision preserves the exact obligation identity. Independent copies with a
changed consent or operation registration are rejected without changing the
parent or emitting effects; the unmodified copy must preserve native identity.
No positive witness, access grant or consent registration is manually fabricated.

This qualifies the explicitly configured inherited profile in native
`AuthoringRuntime`, not signed hosted transport, arbitrary production templates,
Business clients or a deployed payment flow. The report records package catalogue
identities, classpath, source revision and dirty/untracked source digests. The
initial qualification uses Core `64ae47d21c6ba7064fc60738a4ddc6a1d838fb9e` and
Packages executable artifacts from `5b7d95417285a178ab9a6c811d99010f365387c8`;
subsequent semantic-card and test-only commits do not rebuild those artifacts.
