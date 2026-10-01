# Contracts exact-target candidate

This separate candidate clarifies the existing Operation Request document slot
and replaces only its corresponding executable channels listing. The immutable
standalone Contracts release, its Language/BEX imports and gas4 schedule remain
unchanged. The Python current reading edition separately selects gas5; this
candidate does not assert equal gas across those profiles.

Build explicitly from the hash-pinned Python source and this package checkout:

```sh
python tools/build_contracts_exact_target.py --python-source /path/to/blue-python \
  --output /new/candidate-directory
```

Use the Python source's installed dependencies and `src` on `PYTHONPATH`. The
builder verifies candidate.json source hashes, admits the new specification Text
and all 32 definitions through Language, and uses the existing locked package
builder/verifier. The destination must be new. It contains exact source inputs,
archive and review identities. It never changes release.json, inventories,
native approvals or old published bytes. No download occurs.

All new rules/type/protocol/package identities require explicit native support.
Existing Coordination, Mandates and business imports remain bound to their old
Contracts edition. Mounting this archive is not runtime approval and cannot
retarget any of those immutable references. Review the generated import closure
before proposing a coherent successor profile; this candidate is not selected.
