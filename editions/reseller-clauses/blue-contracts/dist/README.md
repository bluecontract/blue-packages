# Blue Contracts

Blue Contracts processes an original event against exact managed Blue documents and returns a complete result, ordered emitted occurrences, gas and replay evidence. It uses Language for content semantics and BEX for evaluation. Coordination, timeline providers, account ownership and transport are outside this protocol.

## Specification and types

`SPECIFICATION.md` is one complete normative document: transition rules, metering, counter schedule and eighteen executable modules. The identical package Text is `spec/contracts.md`. `types/` contains generated views of the 32 standard definitions. The source of those definitions is the unchanged `publish_catalogue` algorithm in the reference; they are not an independently maintained catalogue.

Every exported definition has native `specification` metadata pointing to this complete normative Text. These are new type identities; none of the previously published types are reinterpreted or overwritten. `MIGRATION.md` explains the binding change.

## Local use

```sh
./blue-package verify
./blue-package requirements
./blue-package demo
./blue-package test
./blue-package reference-tests
```

Python 3.13 or newer is required; pytest is required for tests. Normal verification does not update locks. `build` must reproduce the frozen release. The data archive is `dist/package.bluepkg`; the included Python source is build/test tooling and is not installed through package loading.

## Release status

Version `1.0.0-rc.1` is a clean, specification-bound publication candidate. The known enum-metering ordering defect in the supplied Python host boundary prevents an unconditional deterministic-runtime certification. See `QUALIFICATION.md`. This package does not hide that defect by fixing a hash seed or changing the 100,000-gas maximum.

A Java runtime must explicitly bind these new native type identities and specification before it claims support. Successful generic package verification alone is not execution support. Old snapshots and old fixtures remain attached to their previous release.
