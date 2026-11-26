# Using the current packages

Resolve all imports from `PACKAGES.json` and pin the package BlueIds and archive
hashes. Mount names exactly as written in its `mounts` mapping. Do not combine
source locks from historical revisions with this catalogue.

`SHARED-PACKAGES.json` is a generated name/path view for existing consumers.
`PAYMENT-FAMILY-PACKAGES.json` is a generated view containing current business
packages plus their foundation mounts. Both must match the main catalogue.

Use [the tutorial](payment-family.md) and its runnable YAML examples. Native
Coordination, Time and Mandates descriptors additionally require explicit host
approval. An archive that parses successfully is not evidence of executable
native support.

## Connections before activation

Use `parameters.preActivationConnections` to name the clause instance, action
and binding that may run before approval. Use `automatic: true` in place of a
named binding for an automatic declaration. Activation still requires document
access and checks whether the document is closed. An action marked
`observation: true` can use `observations: true` to authorize its dedicated
internal sources together. See the
[Activation example](../clause-activation/README.md#connections-before-activation).

Logical references support the standard Connections mapping, including default
bindings and configurable actions. Schedule and Commerce use that mapping. A
custom hook can use the same logical references when its effective plan
preserves the referenced declaration, its selector and its dedicated source
channel. Keep generated channels exclusive to the referenced connection.
Native dispatch permission applies to the entire channel.

Activation verifies the exact shared `planConnections` function and resolves
the reference using the standard Connections mapping. A replacement helper or
outer `plan` can pass this identity check and still generate a different
route. In the native conformance example, such a helper installs a renamed
channel while the grant remains on the standard channel, so the action runs
only after approval. Authors of custom hooks are responsible for preserving
the standard mapping when they use logical references.

External workflow permission is declared separately in
`preActivationOperations`. Logical references to shared-channel bindings and
timers are rejected. Explicit channel-level grants continue to use
`preActivationChannels`.

The native conformance test covers renaming author-defined clause, action and
binding keys together with their logical references. The planner's generated
channel naming convention stays fixed in that test.
