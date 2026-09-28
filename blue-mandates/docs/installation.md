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
The Runtime uses the exact shared Coordination publication. The supplied predecessor
Mandates package is preserved by its provenance digest; this package revision rebinds
that dependency while retaining the 19 type identities and normative protocol.

Original verification notes describe the incoming preview. Current integration evidence
is in blue-python/docs/mandates-integration-20260927.md. No old workspace is rebound.

### Locked reconstruction and deliberate revisions

Use the installed Blue Python library (`BLUE_PYTHON` selects its interpreter):

```sh
./blue-package verify        # retained archive only
./blue-package check-source  # current authored source + committed lock + native approval
./blue-package build         # staged locked reconstruction; identical dist is a no-op
./blue-package candidate --output ../releases/mandates-preview-3 --version 0.1.0-preview.3 --revision reviewed-change
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
