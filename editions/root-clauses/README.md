# Agreement with root-local clauses

Explicit business-data edition `root-clause-bindings-20260929-1` (package version
`0.2.0-preview.clause-bindings.1`). The four compiled archives are byte-for-byte
from `codex-root-clause-agreements.zip`, SHA-256
`3babcfaddbe353d525fcf56df5bb0972bceb36968dae760643e954026076e2bb`.

[Selection](../../ROOT-CLAUSE-PACKAGES.json) pins this edition. The existing
SHARED-PACKAGES selection, native protocol requirements, and published archives
are unchanged. The four foundation archives here are exact copies of the selected
foundations, retained to make the supplied source locks directly reproducible.
The old 20 exports remain available, with five former short names explicitly
prefixed `Embedded`. No saved document is migrated.

Python Workbench exposes **Clauses generate the Agreement**. It mounts these
archives under private `Root*` authoring prefixes. A minimal Reseller instance
resolves without executing, then ordinary Coordination initialization installs
Blue-generated root state and contracts at epoch zero. Amendments are signed
operations; Python and JavaScript do not implement clause generation or policy.

See [design](docs/DESIGN.md), [migration](docs/MIGRATION.md) and
[lesson](docs/WORKBENCH_DEMO.md). These are supplied design notes, not new claims
of browser or runtime qualification. Fresh integration evidence lives in the
Python repository's `docs/root-clauses-integration-20260930.md`.

From this directory, with the editable Blue Python installation:

```sh
python tools/verify_candidates.py
python tools/build_candidates.py --check
python tests/test_root_clauses.py
```

The check build is read-only. Test and integrity commands write their reports in
`verification/`. `BLUE_SOURCE_WORKSPACE` can override the common parent of
`blue-packages` and `blue-language-python`. No runtime semantics are supplied here.
