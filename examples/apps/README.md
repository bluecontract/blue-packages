# Clause application examples

The source documents and walkthroughs illustrate specific contracts. A native
runner exercises the cases named in its command. The static tutorial checker
only checks that the examples and exact historical selection match the guide.
The complete checked-in corpus includes historical examples and scenarios with
separate execution requirements such as native mandate authority and signed time.

## Current preparation API

The current Payment walkthroughs prepare and resume one independent instruction
or two independently keyed instructions. Both use `Payment/Payment Clause` and
its native Documents lifecycle. The two-obligation case checks that preparing
the deposit publishes evidence for the deposit only and that balance preparation
publishes evidence for the balance only. Replays preserve preparation state.
These walkthroughs end at preparation and resume. Provider authorization,
capture and settlement belong to separate instruction scenarios.
[One obligation](31-current-payment-preparation.blue) · [Two obligations](32-current-two-payment-obligations.blue)

```sh
python3 tools/check_operation_inputs.py --case current-payment-obligations
```

The native [provision check](../../tools/TwoPaymentObligationsConformance.java)
extends example 32 with two independently initialized EUR 1.50 instructions,
each supplied through its own `provide` operation. It rejects substitution,
confirms only the deposit and checks both states after replay. It records
the exact original and executable input hashes. The shorter walkthrough above
continues to demonstrate preparation and resume.

```sh
python3 tools/check_operation_inputs.py --case two-payment-provisions
```

For a current-payment launcher, export the two named walkthroughs to a separate
Core checkout. The default compatibility export keeps the established gallery
selection and fixture paths. Both exports retain the prior source and case files.

```sh
python3 tools/export_core_apps.py --current-payment-launcher /path/to/core-checkout
```

The reseller examples use current Documents preparation and provision, along
with separately confirmed Payment Instruction outcomes. The Ledger example
runs the keyed ledger actions without an Order or receipt projection.
[Declarative reseller](../sales/declarative/README.md) · [Ledger walkthrough](16-ledger.case.yaml)

```sh
python3 tools/check_operation_inputs.py --case configured-actions
```

See the repository's native setup guidance for the qualified Java runtime and
`BLUE_JAVA_CLASSPATH`. [Native operation qualification](../../docs/operation-input-qualification.md)

## Historical payment edition

Examples `01`–`06` and `10` use `start` and the earlier `request*` bindings
under the then-current name `Payment/Payment Clause`. Use the retained
`pre-declarative-reseller` selection, whose Payment package is
`0.8.0-preview.7.access-events.7`, package BlueId
`C4zt6j6D2QHERc5XajmWHL8oLRu5FuQDPCaxGFiP22Dt`. The exact historical
`Payment/Payment Clause` type is `7QsfvCPRi4JqVUgL6U5bwSGjASn9JeyKaz9tmTT9MDLe`.
The manifest records the retained digest and the current bytes of the seven
source/walkthrough pairs. The historical pairs remain available under their original paths and the
compatibility export preserves them. The current-payment launcher publishes
only the two verified Documents walkthroughs.
[Exact historical selection](../../retained/pre-declarative-reseller/PACKAGES.json) · [Identity manifest](historical-payment-edition.json)

To diagnose a named historical file against the retained Payment selection,
compile and run the historical mode with the qualified runtime. The runner
rejects attempts to load a historical case under the current selection.
The retained-control run of `01-order-payment` reports `Unknown property or
action binding: requestAuthorize`; this is a historical comparison, and this
pair has no passing native qualification on that pin. The exact retained
catalogue is distinct from Core's separate historical gallery publication.

```sh
qualified_classes=$(mktemp -d)
"${JAVA_HOME}/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" -d "$qualified_classes" \
  tools/QualificationRuntime.java tools/CurrentOperationScenarios.java
"${JAVA_HOME}/bin/java" -cp "$qualified_classes:$BLUE_JAVA_CLASSPATH" \
  blue.core.CurrentOperationScenarios "$PWD" --historical-payment 01-order-payment
```

A separate historical checkout at `b366d00d262b2d0d611ba85ef36e49d33cc89e15`
contains the qualified `10-net-settlement` source and walkthrough. Its
catalogue SHA-256 is `8b95c8cf42310e06638c2c32c7630b525ee487fd4a8861c72de174cf5920c2dc`
and its Payment package BlueId is `2YcRBqg4xjdRJKQQSnnuhZmj8t3eDFeFfkwAMeGh1RmQ`.
The native runner passed all 27 inputs and their replay checks on that checkout.
Compile the two Java files from that checkout using the same commands above,
then omit `--historical-payment` and pass the named case `10`. This history uses
its own source and package versions.

Example `07` explicitly uses the `Payment/Legacy Payment Clause` compatibility
alias. Method-specific examples use their named method facade. The current
generic Payment preparation API is documented separately from these facades.
[Payment package](../../clause-payment/README.md)
