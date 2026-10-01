# Use the shared Mandates package

Install blue-python in editable mode, then use its selected native implementation:

```python
from blue_packages import Runtime
runtime = Runtime.mandates()
engine = runtime.coordination().start()
print(engine.supported_packages)
engine.close()
```

The support selection includes exact Language, BEX, Contracts, Coordination and Mandates
package IDs. Package availability and native support are separate. Supplying only the
Mandates ID is rejected because its executable dependencies are missing.

Run owned checks against the installed blue-python implementation:

```sh
python -m unittest discover -s ../blue-packages/blue-mandates/tests -v
python ../blue-packages/blue-mandates/examples/run_examples.py
```

The Workbench Coordination tutorial includes “A delegates to B · a flag controls decrement”.
The Runtime uses the exact shared Coordination publication. The current preview.3
specifies the predicate host capabilities required by `$is`
and `$nodeBlueId`, including function argument patterns and shared Language/BEX
metering. It selects new rules, protocol, package and type identities. The exact
preview.2 archive and authored inputs remain under
`verification/publications/mandates-before-predicate-context-20260929/`.

Original verification notes describe the incoming preview. Initial integration evidence
is in blue-python/docs/mandates-integration-20260927.md; the current correction is
documented in blue-python/docs/mandate-predicates-20260929.md. No old workspace is
rebound: the corrected runtime selects `blue-runtime/2026-09-29-mandate-predicates-1`.

### Locked reconstruction and deliberate revisions

Use the installed Blue Python library (`BLUE_PYTHON` selects its interpreter):

```sh
./blue-package verify        # retained archive only
./blue-package check-source  # current authored source + committed lock + native approval
./blue-package build         # staged locked reconstruction; identical dist is a no-op
./blue-package candidate --output ../releases/mandates-preview-4 --version 0.1.0-preview.4 --revision reviewed-change
```

A candidate is a complete new directory, published by one rename. It does not
replace the selected distribution, refresh its lock, or register native code.
`--refresh-lock` is allowed only with `candidate`; the new lock stays inside that
candidate. Review `REVIEW.json`, the source diff, dependency closure and tests.
A runtime maintainer must explicitly approve the new protocol/types in native
support and update consumer/inventory pins to the new immutable archive path.
Keep the old artifact available. Old consumer pins deliberately reject the new
bytes until updated. Arbitrary data-package publication never enables authority.

Ordinary `build` will not overwrite an existing mismatching distribution: fix the
source or prepare a revision. If the approved dist is absent, it constructs the
complete approved set in staging and renames that directory once. Interruption
therefore leaves no advertised partial distribution. Build/check never write
source locks, support manifests or inventories. `check-source` also checks every
advertised loose dist file against the archive. Archive verification alone cannot
establish that current authored source produced those bytes.

Repeated equal flag assignments in the Workbench lesson emit no business flag
or Scope Changed event. Checkpoints can still advance for processed inputs.
The lesson synchronizes its embedded flag during initialization, after the base
Operation Mandate initialization, and then on real embedded flag events.

## Current authored predicate/scalar candidate

The authored source now prepares `0.1.0-preview.4`, protocol
`Mandates / owner-approved-operation-authority/3`, revision
`shared-mandates-20261001-predicate-scalar-1`. Section4 retains the existing
Language callback/shared-ledger requirements byte-for-byte; section6 adds the
reviewed scalar lexical grant order, first complete match and reached error/WAIT
rule, plus a cross-reference to section4. The four locked dependencies are unchanged.
The exported types explicitly reference the new rules Text identity.

The retained `dist`, inventory and native-support approval still describe the
previous published edition. Use the explicit candidate command above to create
new artifacts; ordinary check-source intentionally cannot certify this authored
revision against an older native approval. Candidate generation does not adopt a
runtime. Java implements and qualifies this edition first, followed by actual
MyOS opt-in qualification and the matching Python/existing-spec port. Keep prior
published IDs and archives immutable throughout that sequence.
