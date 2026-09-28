# Blue BEX

Blue BEX evaluates data-encoded expressions and statements using explicit inputs. It produces values, ordered proposed effects and a logical gas ledger. It does not mutate or publish documents.

## Specification

`SPECIFICATION.md` is the complete specification, including the operator reference and six executable modules. The identical identified Text is `spec/bex.md` in the data package. Its exact Language dependency is Blue Language package `8XGYNufx24r7Dc5bGoeobcGNCn9roLzSfZCQyHBTaTx4`.

This is a protocol package with no artificial operator types and no exported Java/Python classes. Ordinary function libraries can publish their own definitions using these semantics without changing the evaluator.

## Local use

```sh
./blue-package verify
./blue-package requirements
./blue-package demo
./blue-package test
./blue-package reference-tests
```

Python 3.13 or newer is required by the included reference; pytest is required only for tests. `build` reconstructs the pinned release and refuses to silently replace its identity. The data artifact is `dist/package.bluepkg`. It contains no executable installation hooks; the reference in this source repository is build/test material.

## Release qualification

This distribution is version `1.0.0-rc.1`. Its specification is complete; passing finite cases is not a universal conformance certificate. See `QUALIFICATION.md` and `VERIFICATION.md` in the source workspace for tested scope and host-integration limits.

Changing the documentation changes package identity, not the evaluator's selected native rules. Changing this normative specification changes its identity. Loading the package does not install a BEX implementation or authorize an intrinsic.
