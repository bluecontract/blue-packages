# Ten-million-gas edition

The current Contracts edition gives a new atomic invocation **10,000,000 gas units by default**, with the same **10,000,000 maximum**. A caller may explicitly select a smaller budget. There is still one ledger for the entire invocation, including embedded documents, reactions and cyclic rounds. Moving work between workers or importing an invocation does not replenish its budget.

This is a semantic edition change, not a runtime override. The numerical tariffs, debit ordering, first rejected charge, local ceilings and rollback rules are unchanged. Old published specifications, types and archives retain their identities and their 100,000 maximum. A stored snapshot or invocation must use its original edition; importing it does not silently upgrade it. New identities must be selected explicitly when authoring a new document against the current packages.

The source of truth is `blue-packages`: its BEX and Contracts specifications include the exact executable reference and reviewed source overrides. Language itself has no Contracts gas ceiling, so its publication is unchanged. Historical references to 100,000 in retained specifications, fixtures and reports are intentional.

A cross-language regression performs 20,000 integer additions and writes the result to `/count`. It completes at **160,998 gas** in Core, standalone Java, Python and the published executable reference. Its receipt is `sha256:4f50a677931535abf32ef40ee4695aafe6800933bc1028edc68468aa21425ad5`. Giving the same invocation only 100,000 gas produces `GAS_LIMIT_EXCEEDED` with rollback. Separate tests cover the final affordable charge, rejection above the maximum, historical receipts and replay with a saved 5,000-gas budget.

The higher allowance does not speed up an instruction or reserve memory. It permits up to 100 times the previous logical work before gas exhaustion. CPU time and memory can therefore become the limiting resources. In particular, this change is not a fix for the separately identified receipt/trace memory amplification. Successful completion within the gas allowance still depends on sufficient host resources.

## Publications and reproduction

`blue-bex/` and `blue-contracts/` contain the current edition. `editions/gas-100k/` retains their predecessors. The executable Coordination/Mandates/Time bindings for this edition are under `editions/gas-10m/`; the top-level Coordination package is the separate timeline-provider protocol.

The explicit authoring tools are `tools/prepare_gas_edition.py`, `tools/prepare_gas_coordination.py`, `tools/prepare_gas_dependents.py` and `tools/prepare_gas_business.py`. They produce new publications; ordinary package builds must continue to verify the frozen selected bytes. Per-package `migration.json` files record old and new identities for authors. These maps are not runtime substitutions for stored documents.

Run `blue-contracts/tools/release.py test`, `blue-bex/tools/release.py test` and `blue-contracts/tools/release.py demo` with the repository's supported Python environment. Generated local results belong under ignored `build/`.

`python tools/verify_gas_rebuilds.py editions/gas-10m/blue-mandates editions/gas-10m/blue-time blue-coordination blue-agreements agreement-reseller` stages declared inputs and exact locked dependencies in a temporary directory, then requires byte-identical archives. It preserves the generic builder's package-local path restrictions.
