# Demand-scoped required-object presence lowering — candidate amendment

This amendment is intended for the next candidate rules publication. It does not change any existing immutable publication or its identity. It narrows the blanket native-evaluation rule in §3 and §12.5 of `contracts-demand-scoped-draft.md`.

A container/header obligation MUST retain the original contextual Recipe and discharge its governing definitions. After constructing the native effective Head and establishing presence using the existing native occurrence/root rules, it MAY discharge the effective constraint without invoking native object-field counting if and only if:

- the effective Head kind is `object`;
- the checked occurrence is present;
- the effective constraints description contains exactly `required`, with a Boolean value.

In this case the required-presence predicate is satisfied. There is no field-count predicate to evaluate. The logical tariff MUST still charge the existing `schemaPredicateEvaluated` obligation for `required`; this lowering does not establish a whole-value certificate or a reusable value obligation.

Absent occurrences, scalar/list/none kinds, and every other effective constraint combination MUST continue through native validation. Inherited constraints are included in the effective description. In particular, `minFields`, `maxFields`, key/value/item rules and required scalar/list payload checks MUST NOT be bypassed. Governing metadata and observed ordinary records retain their existing obligations.

Legacy Language and Contracts validation and tariffs are unchanged. This amendment does not authorize treating every object-shaped definition as a present value: native presence remains authoritative.

Evidence: the cold History Position fixture reaches the required typed Processing Receipt header and previously demanded an unconsumed document child through incidental native object counting (`91973`). The amendment's scoped implementation and negative controls require separate verification before publication qualification.
