# Source and identity provenance

`reference/SOURCE-LOCK.json` identifies the uploaded source archive and every included reference/support file. The package tooling checks these bytes before invoking the reference. The frozen source contains older descriptions and resource bindings as historical implementation evidence; they are not additional normative chapters of this release.

`docs/sources.json` lists the algorithms embedded verbatim in the complete specification. `release.json` pins the built package and specification. `blue-package.lock.json` pins direct package dependencies. Registry addresses and local directory names do not select a different semantic identity.

The loader adapter intentionally constructs Language with `core_contracts=False` when auditing a data repository. This prevents an unrelated installed Contracts namespace from being implicitly mounted during generic package validation. The original strict definition-audit algorithm is still used. The package verifier also checks a revisited bootstrap Language against the selected identity. Neither correction changes Language BlueId calculation or relaxes invalid/missing-content checks.

The local `blue-package` launcher is distribution tooling, not part of the interpreter. BEX/Contracts source algorithms remain unchanged. Python >=3.13 is used because the original reference depends on its supported behavior. No Python or Java library per business type is generated.
