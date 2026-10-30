# Execution profiles

`Execution/Profile` is an ordinary Language-only description of one exact
runtime selection. The declaration is the `executionProfile` sibling of an
executable node's `contracts`. It can be inline, referenced or contributed by
the node's type. The complete node remains unchanged for native processing.
Identifiers inside the descriptor are Text BlueIds. They name exact native
dependencies; the runtime validates those dependencies in their proper roles.

See [normative rules](spec/execution-profile-v1.md) and
[conformance cases](conformance/cases.json). Profile records are produced only
after all referenced native publications are available. This package installs
no runtime and changes no existing package or account default.
