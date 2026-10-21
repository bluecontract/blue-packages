# Blue Contracts

This directory contains the single current Contracts package. Its canonical
rules are `spec/contracts-deterministic-4.md`, generated from `reference/`,
`reference-host.py` and the prose inputs by
`python ../tools/build_deterministic_reference.py`. `SPECIFICATION.md` is an
identical reading copy, checked by that builder. `docs/sources.json` binds every
executable appendix module. Python installs these exact modules; Java implements
these same rules and is checked by native differential tests.

`dist/package.bluepkg` is the compiled package. Rebuild the complete current
closure with `python ../tools/build_final_gas.py all` from the package home.
There are no supported predecessor runtime editions or automatic migrations.
Historical review evidence is kept separately from this package's inputs.
