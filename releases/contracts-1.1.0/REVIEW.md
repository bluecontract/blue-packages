# Blue Contracts 1.1.0 default selection

The supported default now selects the corrected constructor, alias, count and
enum ordering together with compact metering receipts. A successful result keeps
the admitted gas total; a failure also keeps its rejected charge and diagnostic.
Accepted-charge histories are absent from canonical outcomes, receipts, chunks
and completion records. Numerical tariffs and the 10,000,000 maximum are unchanged.
Required event, checkpoint, completion and receiving evidence remains available.

This receipt representation is independent of physical execution-history reuse.
MyOS still uses protected retained history/completions. That optimization does
not require keeping a list of every gas charge.

## Exact publication

| Identity | Value |
|---|---|
| Version | `blue-contracts@1.1.0` |
| Gas selection | `blue-contracts/1.1.0` |
| Package | `4qxube4dhH5bvYQeApsbfuGr1Tqkq6KHt273So9CVm1U` |
| Protocol | `Cp5YJEgoR2uPbRJCn6kQ1rAiLRoHpPa1GKgc6Akyx1q7` |
| Rules | `8XFSqhtdE4ohsKjS1vJQ9PuDFoCcgiTbwrQVPuASxGT1` |
| Archive SHA-256 | `051be27c5582caf9cf280f7048797867d330e972e921c55460d5ed7914e435d3` |

Language and BEX use their exact existing publications. In blue-packages, see
`releases/contracts-1.1.0/selection.json`, `dependencies.json` and
`catalogue/selection.json` for the complete native/SDK/application pins.
The application sources come from Core's recorded package commit
`8e074c9bd1e1a8a2154aa41988b18a94a4dde218`; `catalogue/SOURCE.json` verifies
unchanged authored files. Only release versions and dependency bindings change.

## Default entry points

- Python: `Runtime()` / `Runtime.current()`, followed by `.contracts()` or
  `.coordination()`. The installed package contains the same pinned release.
- Standalone Java: `new Contracts(language)` and the default Coordination
  engine select `RuntimeProfiles.current()` and Contracts `V1_1`.
- Hosted MyOS: `AccountRuntimes.defaultBindings()` keeps the native
  `RuntimeBindings.accessEvents()` application binding and selects `V1_1`.
  Its provider operation recognition uses that same hosted default.
  Native Mandates, timers, signed inputs and receiving remain installed.

No opt-in ordering selector is needed. Earlier selectors/resources and immutable
reports keep their original names; they are not new product modes. See the
package release's `NAMING-AUDIT.md` and `NAMING-OCCURRENCES.json` for the prior
literal occurrence classification. No new legacy verifier, migration,
dual-runtime implementation or Execution Requirements framework is introduced.

## Focused qualification and limits

The default 13-fixture corpus covers 54 budget outcomes, exact/one-below limits,
Unicode ordering, cold snapshot replay, warm/cache variations, terminal state,
input immutability and graph acquisition order. Python and standalone Java match
recursively across the complete JSON, including receipts and snapshots.

MyOS matches full document metadata/state, emitted events, gas, status, rejection,
checkpoints and completion observations. Its snapshot additionally commits the
native Document Dispatch binding; snapshot, invocation, work and receipt hashes
therefore differ. This difference is reported, not normalized into a three-way
receipt-equality claim. Each implementation reproduces its own receipts on cold
snapshot replay. Use `blue-packages/tools/check_contracts_release.py` for this
explicit comparison, not the earlier experiment's verifier.

Focused checks cover approved and rejected native Mandates, scope/revocation in
standalone Java, supported timer firing, signed initialization/processing and
fresh-state SQLite restart. A separate Core catalogue test exercises complete
starter-package installation; native runtime smoke alone is not application
bootstrap qualification.

This is an unpublished review candidate, not production qualification. Required
PR CI and the full repository/release gates remain outstanding. No release,
package publication, main merge, live-data change or deployment is authorized by
these checks. Existing histories are preserved but compatibility with them is
not required or qualified. No SQL schema migration is introduced.

## Rebuild commands

Set `JAVA_HOME` and `BLUE_JAVA_CLASSPATH` to the maintained Java package builder's
qualified runtime classpath. No network is used by ordinary builds/checks.

```sh
python tools/build_contracts_release.py --check
python tools/build_contracts_dependencies.py --core ../myos-core --python ../blue-language-python --check
python tools/build_contracts_catalogue.py --check
```

The catalogue keeps a separate source snapshot and new distribution paths. The
root catalogue and earlier edition archives are not overwritten. Rebuilding the
current application closure does not alter its authored business rules.
