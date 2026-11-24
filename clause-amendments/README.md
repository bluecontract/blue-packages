# Amendments

Authored native Blue proposal package. See the top-level evidence and catalogue for tested scope. No JavaScript business interpreter.

An agreement author can configure stock `Amendments/Amendments Clause` to
validate replacements with a named function in a reusable Compute Definition.

```yaml
parameters:
  replacementValidator:
    definition:
      type: Commerce/Catalog Functions
    function: validateCatalogReplacement
```

The pure BEX function receives `current` from the configured amendment path
and `replacement` from the proposal. It can fail with a domain error or return
`false` to reject. Amendments runs it before recording a new proposal and
before applying a fully approved proposal, against the current value each time.
The agreement configuration selects the exact definition. Operation requests
supply the replacement value.

The validator runs in its own native Compute scope with the library's own
functions and constants. The workflow commits the original amendment effects
only after validation succeeds. Omitting `replacementValidator` uses the
clause's default validation, including any existing `replacementSchema`.

See [payment-family integration](../docs/payment-family.md) for the tested
package selection and boundaries.
