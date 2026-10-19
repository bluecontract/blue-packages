# Final gas qualification

The new edition requires deterministic final gas and charge-before-work budget
checks. It changes canonical receipt and continuation formats. The frozen earlier
reference is retained; explicit source overrides implement this edition. Java host
support must use the new exact package/specification selection.

Local release checks cover package integrity, byte-identical rebuilding, direct
execution, fresh-worker chunks, cold replay and one-less-gas rollback. These checks
are necessary evidence, not a claim of exhaustive cross-implementation conformance.
Historical receipt fixtures are not silently rebound to the new edition.

The earlier report below describes the initial reference delivery. In particular,
its 100,000-gas allowance and unchanged-source statements do not describe this
10,000,000-gas edition. Hash-seed independence remains a host obligation; omitting
charge rows cannot repair nondeterministic execution or nondeterministic totals.

---

## Historical reference report (retained)

# Qualification boundaries

## What is established

The final Language artifact is unchanged and is checked against its preserved reference. The BEX and Contracts packages use that exact Language. They contain complete normative text, exact supporting records and explicit package/protocol prerequisites. All executable algorithm files used for these publications remain the supplied source bytes.

## What changes in the new Contracts binding

The catalogue recipe uses the BlueId of `src/blue_contracts/COMPLETE_SPECIFICATION.md`. Replacing that resource with this publication's complete normative Text generates the new type collection. The demonstration uses a separately created temporary runtime tree for that selection. It never edits the preserved reference in place. New results, markers, receipts and histories refer to this new collection; old identities remain old identities.

## Known reference determinism defect

The uploaded project already contains `tools/reproduce_enum_gas.py`. For one Text-enum update, different `PYTHONHASHSEED` values produce the same document but different gas and/or receipt identities. That affects the host's deterministic metering contract. The BEX evaluator's ordinary finite cases do not cure this cross-layer problem. The complete specification does not authorize variable ordering: a disagreement with deterministic requirements is an implementation defect.

This task preserves the algorithms to keep the edition auditable. It does not select a favorable seed, alter metering, rewrite historical fixtures or claim exhaustive conformance. Correcting the defect requires an explicit reference decision and qualified new identities where the normative content changes. Keep 100,000 as the Contracts default/maximum, and test first-rejected-charge behavior as well as aggregate gas.

## Exclusions

No remote registry publication, MyOS integration, browser run, performance benchmark, or complete multiworker Coordination qualification was performed. The new native Contracts type collection is not automatically registered in the supplied Java runtime. Unchanged Language bytes do not imply every new protocol publication is implicitly accepted.

The vendored source is build/test reference material. Its inclusion is not a license grant. Review the original project's licensing and redistribution permissions before making a public repository or artifact.
