# Explicit Contracts edition adoption

This publication creates new identities because the governing specification is now one complete normative document. The original publication used an older rules Text plus external supplements. The new Text includes the same selected algorithms, transition model, metering rules and exact BEX dependency.

`migration.json` lists all 32 old/new native type IDs and the specification identities. It is an audit diff, not an instruction to retarget old references. All 32 recipes retain their original structural role and fields; their governing specification and references to regenerated parents are deliberately rebound.

To run this edition in the included Python example:

1. Preserve the frozen reference.
2. Create a separate runtime source tree with `./blue-package runtime-copy /absolute/path/to/new-runtime/src`.
3. In that derived tree only, the complete Contracts specification resource is replaced with this edition's `SPECIFICATION.md`; all algorithm source bytes remain unchanged.
4. The unchanged catalogue generator calculates the new native types. The demonstration checks all 32 against package exports before processing.
5. Compile source aliases to exact events before sending them to fresh workers. A consumer does not inherit the author's aliases.

The ordinary `./blue-package demo` performs these steps in a temporary directory, runs a counter operation, transports chunks to fresh workers, compares cold replay, and checks a one-less-gas rollback. It is an integration demonstration, not a production profile installer.

Java adoption must register this precise specification/type collection under a new supported selection and qualify it through the same tests. Do not append arbitrary package IDs to a whitelist while leaving old native bindings in use. Old snapshots and Coordination histories must remain with their previous selection unless an explicit migration is designed.
