## Deterministic ordering correction (ordering-1)

This explicitly selected edition retains the 10M edition's gas weights, limits,
receipt schemas, authority rules, receiving modes, ordered lists and business
operations. It does not replace any historical publication or select itself for
existing documents. Its gas profile is `contracts-deterministic-gas-6-ordering`.

Language canonical objects and typed enum scalar keys use unsigned UTF-16 order.
Contracts declaration traversal, stable merge-sort input, member ordering,
validation field scans and private canonical JSON use Unicode code-point order,
as already defined by the preceding specification and executable appendix.
Semantic pointers compare decoded segment tuples; stored edge inventories retain
their specified raw-pointer ordering. Explicit lists retain their original order.

Resolve the following previously implementation-dependent callback orders:

* Examine present runtime type aliases in `itemType`, `keyType`, `type`,
  `valueType` order. Report the first invalid alias.
* Examine count predicates in `minItems`, `maxItems`, `minFields`, `maxFields`,
  `minLength`, `maxLength` order. Do not add a charge for sorting.
* Within each effective enum group, examine canonical typed scalar keys in
  unsigned UTF-16 order; retain first-occurrence group ordering, deduplication and
  comparison short circuiting. Never reorder the authored enum list.
* Construct inline type/specification slots bottom-up in Language input-key
  order, then pass their established references into node normalization. Collect
  reference-only constructor callbacks and pay their unchanged identity
  prerequisites in exact BlueId ASCII order before establishing the next node.
  Preserve duplicate occurrences and flush the remainder before returning.
  Apply the same rule to multi-contribution captured-recipe synthesis.

Admission/opening/construction witnesses are logical evidence. They cannot be
inferred from physical caches, lost when a captured view is reused, or borrowed
from an unrelated invocation. Preserve the existing reuse inventory and direct
manifest prerequisites, including charge-before-work and atomic rollback.

Lazy BEX collection access follows the existing executable BEX rule: fetch the
item before its `forEachItem` charge. Boolean scalar comparisons cost the scalar
comparison debit; they are not numeric coercions.

Only this edition selects the newly specified callback/count/alias/enum order.
Corrections to already explicit code-point ordering and BEX access rules do not
introduce a new tariff or evidence format. Previously nonconforming Java results
containing supplementary-character keys may not replay identically; preserve
that evidence and do not migrate stored receipts automatically.
