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
