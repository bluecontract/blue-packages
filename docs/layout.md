# Repository layout

Each package owns its definitions and distribution. Keep package directory names
stable: Java and Python consumers pin these paths as well as archive hashes.

| Location | Purpose |
| --- | --- |
| `README.md` | Current package catalogue and starting point. |
| `SHARED-PACKAGES.json` | Current shared consumer selection: 13 archives. Its historical profile labels do not approve every package for execution. |
| `PACKAGES.json` | Additional release metadata retained for foundation verification and existing tooling. It is not the complete catalogue. |
| `AGREEMENTS-PACKAGES.json`, `AGREEMENTS-PROFILE.json` | Agreement build/export metadata and case-sensitive alias mappings used by existing Java maintenance tools. |
| `docs/` | Repository layout, consumption, publishing and agreement guides. |
| `<package>/blue-package.yaml` | Authored package configuration, exports and imported packages. |
| `<package>/blue-package.lock.json` | Exact imported package identities and archive hashes. |
| `<package>/types/`, `spec/` | Owned definitions and normative protocol rules, where applicable. |
| `<package>/docs/`, `examples/`, `tests/` | Package explanations, examples and acceptance checks. |
| `<package>/dist/` | Immutable `package.bluepkg` and its exact unpacked content. |
| `functions/` | Three deliberately separate commerce function release examples. |
| `tools/` | Local authoring, building, verification and distribution tools. |
| `verification/foundation-20260926/` | Historical foundation reports and recorded outputs, labelled by their original scope. |
| `verification/reference/` | Frozen reference implementations with their original `SOURCE-LOCK.json` files. Required by foundation conformance tools, never loaded from a published data package. |
| `verification/publications/` | Historical exact publications retained for old consumers and provenance. |
| `verification/provenance/` | Original import and reseller build records. |
| `build/` | Ignored, regenerable local release outputs. |

Not every package needs every optional directory. The foundation packages retain
their complete `SPECIFICATION.md` reading editions and file inventories. Package
READMEs included in immutable archives describe those releases' original layouts;
historical `reference/python` locations now live under `verification/reference/`.
The current tools already resolve that location.

## Files intentionally retained

* `blue-mutual-activation` is a relative symlink to the original release in
  `verification/publications/`. It serves exact-pinned older Java consumers.
  New authoring uses `clause-mutual-activation`; these are different package IDs.
* Each commerce project keeps `dist.bluepkg` as a relative symlink to
  `dist/package.bluepkg` for older consumer locks.
* Frozen `inputs/*.bluepkg` files are pinned build inputs, not copied implementations.
  Removing them or retargeting a lock would break byte-identical foundation builds.
* Unpacked `dist/` files are inspected by source/distribution verification and some
  consumer resource tasks. Release bundles include only the archive, once.
* Reference source locks, upstream notices, meaningful verification logs and previous
  releases remain reproducibility inputs. Do not prune them as build caches.

Repository cleanup does not edit published README/specification bytes, regenerate
BlueIds, change native support or update Java/Python selections. Changes to authored
release content need a separately reviewed publication.
