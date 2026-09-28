# Selecting and using packages

`BLUE_PACKAGES_DIR=/absolute/path/to/blue-packages` selects the package home for the
Java and Python repositories. Java additionally supports `-PbluePackagesDir=...`.
Both support a sibling checkout in development. A selected root with missing or
incorrectly pinned archives fails verification; it must not silently fall back to
another edition.

The consumers maintain their own selections. The shared inventory describes available
selected data, not a requirement that Java and Python support every package equally.
Current Python selects the renamed clause packages and Reseller. Older Java selections
still use the original Mutual Activation publication through a compatibility path.
Time remains a separately pinned preview, with native approval explicitly false.

## Authoring names

Mount exports under explicit, case-sensitive names such as `Language/Package`,
`Contracts/Sequential Workflow`, `Agreements/Agreement` and
`MutualActivation/Mutual Activation Clause`. The prefix is local to the importing
document. Importing a package does not automatically import its dependencies' aliases.
The suggested names in the root README are for new authoring; immutable older packages
may internally use different aliases.

This fragment uses the Immediate Termination export after mounting that package with
the `ImmediateTermination` prefix:

```yaml
type: ImmediateTermination/Immediate Termination Terms
allowedParty: EITHER
```

It describes negotiable terms. Installing an executable clause and authenticating
actions are separate responsibilities of the agreement and selected runtime.

## Available data versus executable support

Loading or verifying an archive exposes definitions and checks their identities.
It does not install native code, grant authority or schedule background work. Use a
runtime profile that approves the exact protocol dependency closure. Then apply that
runtime's ordinary repository, provider, BEX, Contracts or Coordination APIs.

Java and Python production implementations remain in their own repositories. Historical
Python copies in this repository are frozen conformance inputs, outside distributions.
They are not the live Python installation. Current runtime qualification results belong
in the consumer repositories; historical evidence here is described in
[verification/README.md](../verification/README.md).
