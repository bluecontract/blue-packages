# Blue Language 1.0

## Specification — 26 September 2026

**Edition:** `blue-language/2026-09-26-specification-metadata-1`  
**Publication:** complete specification, including standard definitions and normative algorithms

### Abstract

Blue is a language for immutable, content-addressed graphs. Its nodes describe values, reusable definitions, constraints, and references to other nodes. A node may be used as a type: it contributes compatible structure and requirements without losing the identity of either the type or its instance. A BlueId identifies exact content, not a mutable name, a location, or a resolved interpretation.

This specification defines the node model, portable input representations, exact identity, specialization, schemas, list construction, graph access, validation, specification metadata, and the standard package model. It also defines how a processor associates additional meaning with identified specifications. Particular workflow, coordination, rendering, query, and other application protocols define their own behavior; installing their content does not install an implementation.

### Status and authority

This document is the complete normative definition of this edition. Its prose, tables, standard definitions, and normative algorithm annex form one contract. No separate Blue document, source-repository branch, release tag, implementation guide, or project discussion supplies an unstated rule. Examples marked informative illustrate the rules and do not extend them.

A conformance claim identifies this edition and the implemented role. Publishing this document or a package containing it does not certify an implementation. A conflict between normative prose and algorithms is a specification defect; it is not permission to choose a convenient interpretation or regenerate expected results.

### Requirement terms

**MUST** and **REQUIRED** state absolute requirements. **MUST NOT** and **PROHIBITED** state absolute prohibitions. **SHOULD** states a recommendation that may be departed from only after understanding and documenting the consequences. **SHOULD NOT** recommends against a practice under the same condition. **MAY** and **OPTIONAL** indicate permitted alternatives. Requirements expressed with these terms apply only to the role and operation being specified.

### Contents

- [1. Scope, conformance roles, and interpretation](#scope)
- [2. Nodes, graphs and operation roles](#model)
- [3. Serialization, scalar codecs and empty content](#parsing)
- [4. Exact normalization and BlueId](#identity)
- [5. References, verified graph access and materialization](#graph)
- [6. Types, specialization and validation goals](#types)
- [7. Schemas: predicates, narrowing and conjunction](#schemas)
- [8. Lists and specialization](#lists)
- [9. Preprocessing and Source preparation](#preprocessing)
- [10. Complete and selected resolution](#resolution)
- [11. Validated creation, canonical authoring, minimization and export](#admission)
- [12. Cyclic identities and owning-set proofs](#cycles)
- [13. Diagnostics and safe operation boundaries](#diagnostics)
- [14. Conformance and operation equivalence](#conformance)
- [15. Worked examples — informative](#worked-examples)
- [16. Authoring bindings and exact content availability](#authoring-bindings)
- [17. Specification metadata](#specification-metadata)
- [18. Standard packages and protocol descriptors](#packages)
- [19. Edition selection and cyclic identity boundaries](#edition-boundaries)
- [20. Protocol interpretation and document processors](#processors)
- [Appendix A. Algorithm notation and primitive operations](#notation)
- [Appendix B. Exact registry and preprocessing selectors](#registry)
- [Appendix C. Ordinary standard definitions](#standard-definitions)
- [Appendix D. Complete normative algorithms](#algorithms)
- [Appendix E. Portable conformance-request protocol](#fixture-protocol)
- [Appendix F. Exact repository carrier](#repository-carrier)


<a id="scope"></a>
## 1. Scope, conformance roles, and interpretation

### 1.1 Content model

Blue represents information as a graph of immutable typed nodes. A document is one root together with the portion of the graph presently materialized. Types are themselves nodes. Using a node as a type contributes requirements, fixed content, and compatible structure to the instance.

Language operations establish exact content, its identity, or specific conclusions about its meaning. They do not grant authority or perform external business actions. This edition defines no workflow scheduler, transaction coordinator, network service, database layout, or portable execution gas tariff.

**LANG-SCOPE.** An implementation MUST apply the structural Language rules to all reserved fields, including `contracts`, without inferring execution behavior from the field name. Application protocols MUST NOT change the Language rules used to parse, identify, or resolve content in an established interpretation context.

### 1.2 Conformance roles

A **Language implementation** provides the content and operation semantics defined in this document. A **package processor** additionally constructs, verifies, or mounts packages according to §18. A **protocol processor** performs a stated task under additional identified protocol rules, according to §20. A single program may perform several roles; a reader may perform only the Language role.

**LANG-AUTHORITY.** Full Language conformance requires the operation contracts in this document, not only structural hashing. An implementation MAY organize its APIs, records, storage, caches, and algorithms differently, provided that it preserves the required observations, identities, proof obligations, and failure distinctions. A subset implementation MUST identify its supported subset and MUST NOT advertise omitted behavior as supported.

The executable notation in Appendix D specifies complete Blue-specific procedures. Python allocation, private attributes, diagnostic English, and reference cache layout are not required interfaces. The selected mathematical and serialization behavior is required. The six core registry bodies in Appendix B are exact content; they are not illustrative substitutes.

### 1.3 Selecting Language

An **interpretation context** fixes the Language edition, core registry, input role, explicitly selected authoring bindings, and the evidence and resource controls available to an operation. The Language selection is established before processing identity-bearing content. An ordinary `type` reference or a document's `specification` metadata does not retroactively choose a different parser, identity algorithm, or registry.

**LANG-VERSION.** All steps of one identity, resolution, or admission calculation MUST use one coherent selection of Language rules. A content address MUST NOT be reassigned to different exact content. Retained content and validation evidence MUST NOT be silently reinterpreted under a different edition. Compatibility and cyclic identity boundaries are specified in §19.

A bootstrap Language package identifies its selected rules and standard definitions; it is verified by an implementation already able to interpret those rules. It does not install or derive that implementation. Its own identifier is not embedded into the content from which that same identifier is calculated.

### 1.4 Exact identity, availability, and trust

An identifier and a body are different kinds of evidence. A correct identifier identifies content. It neither makes the content available nor establishes its author's authority. A correctly identified body is not necessarily a valid completed value or a supported protocol. Admission and support assertions MUST distinguish these claims.

Registry addresses, source paths, release labels, timestamps, and display aliases are not alternative BlueIds. An established provider result is interpreted only in the role and context under which its content can be verified.

---

<a id="model"></a>

## 2. Nodes, graphs and operation roles

### Purpose

Separate **what a node contains**, **how it is represented**, and **what an operation proves**. These distinctions determine whether two inputs should have the same identity and whether successful hashing is enough to admit a document.

### 2.1 Exact content and an effective view

An exact node has its own fields, literal metadata, scalar payload or list elements. Its effective view additionally applies the inherited declarations and compatible constraints relevant to that node. Resolution retains the exact origin; it does not overwrite that origin with its view.

**LANG-EXACT-VIEW.** Two distinct exact nodes MAY resolve to identical effective views. An implementation MUST NOT infer identity equality from that observation alone, or recover a lost exact origin by guessing from a bare resolved view. The ordinary hasher identifies exact content, not a resolver object.

For example, Text PLN and Currency PLN retain different own type edges. An enclosing Holder declaration may interpret either as Currency PLN. Their exact child identities remain different. All five complete instance inputs appear in §15.

### 2.2 A reference is not an overlay

A pure reference has exactly one member:

```yaml
blueId: GX7CFUmSDrE2MzptunLCCdZwnuwwrenRQqEnHL4x3uoC
```

The same object with a sibling, even a null sibling, is invalid. To specialize a referenced node, place the reference under `type` and supply instance fields outside it. Expansion reveals an existing node; specialization creates a new, more constrained node.

**LANG-REFERENCE.** A reference and its verified exact materialization denote the same node. At a complete node-valued position, replacing one with the other MUST preserve exact identity. A semantic operation MUST NOT expose the reference wrapper as an ordinary `blueId` field. Its conclusions depend on the selected operation and verified content, not expansion state.

A reference to a compiled list result is exact content. It is not a reusable Source instruction that should be executed at its new location. Representation equivalence applies to a node and its exact representation, not to an unevaluated constructor expression and an unrelated exact operand.

### 2.3 The node model

A materialized node contains reserved metadata and at most one primary payload. Scalars use `value`; lists use `items`; objects use direct ordinary child fields. A metadata-only node may have no payload. The empty map `{}` is a present empty object, not a missing declaration. Bare objects do not acquire a Dictionary type, and bare lists do not acquire a List type, merely through normalization.

**LANG-NODE-SHAPE.** A node MUST NOT combine scalar, list and ordinary-object payloads. The reserved-invalid fields `properties` and `constraints` MUST be rejected. Ordinary keys colliding with reserved fields cannot be represented directly as application map keys; an application-defined escaped structure is required.

| Field | Role and permitted shape | Identity contribution |
|---|---|---|
| `name`, `description` | Literal Unicode string | Literal string |
| `specification` | Complete reference-valued metadata; explicit node in Source, exact reference after preparation; see §17 | Exact target identity |
| `type`, `itemType`, `keyType`, `valueType` | Complete node; Source alias before preprocessing; exact reference afterward | Exact defining-node identity |
| `value` | Scalar literal, never an object or sequence | Own-type encoded literal |
| `items` | Sequence slot, not a separately replaceable node slot | Ordered payload-list identity |
| `blueId` | Final identifier, exclusively in a pure reference | The identifier itself |
| `blue` | Source-root preprocessing configuration only | Absent from the resulting content |
| `schema` | Exact node interpreted using §7 | Exact child identity |
| `mergePolicy` | Literal `positional` or `append-only` | Identity of the corresponding core Text scalar |
| `contracts` | Exact node interpreted as a content map when needed | Exact child identity |
| Any ordinary field | One complete child node | Exact child identity |

For example, `name: {blueId: ...}` is invalid: a label is literal metadata, not a node slot. To reference a list, replace the whole list node, not the `items` sequence slot.

### 2.4 Input roles

| Role | Meaning | May execute Source construction? |
|---|---|---|
| **Source** | Authored document with optional directive, aliases and construction expressions | Yes, once |
| **Preprocessed Source** | Baseline-normalized Source; controls can remain | Yes, at compilation |
| **Exact** | Already-established complete content, possibly partially materialized | No |
| **Direct** | Exact input with every type and specification position already a pure reference | No |
| **Compact canonical wire** | Explicit codec using verified list-prefix records | Decode, never replay Source |
| **Effective result** | Interpretation bound to exact origins and coverage | Not an exact-input replacement |

**LANG-INPUT-ROLE.** Every operation MUST establish the role of its input before interpreting it. JSON versus YAML does not select the role. Loading a published exact body MUST NOT execute its contents as new Source. A failed verification MUST NOT be retried under other modes until an identity happens to match.

### 2.5 Abstract operations

The names below identify contracts, not mandatory SDK method names. `Context` means the fixed Language/registry/bindings, any explicitly selected out-of-band resource controls and available verified or verifiable evidence. Returning an identity alone never establishes semantic validity.

| Operation | Input role | Output | Evidence | Guarantee |
|---|---|---|---|---|
| EXACT_ID | prepared exact Node/Ref | exact identity | identities of complete child contributions; bodies only for preparation that requires them | none |
| PREPARE_SOURCE | Source and fixed environment | constructed exact node + new dependencies | preprocessing and actual construction dependencies | structural preparation; not whole admission |
| ADMIT_SOURCE | Source + explicit definition/value goal | validated canonical exact result + artifacts | complete required graph/type evidence | whole-graph admission; root duplicate normalization |
| ADMIT_EXACT | existing exact input + goal | validated same exact node + artifacts | complete required graph/type evidence | whole-graph admission; no migration |
| ADMIT_DIRECT | strict Direct input + goal | validated same exact node + artifacts | complete required graph/type evidence | Direct type-slot grammar plus admission |
| ADMIT_CANONICAL | compact wire + goal | decoded validated exact node + artifacts | prefix, type and required graph evidence | admission after the declared codec |
| RESOLVE_COMPLETE / CERTIFY | prepared exact input/recipe + goal | effective head and certified obligations | requested definition/active value closure | specified semantic closure |
| OBSERVE | exact input, path and question | established / absent / incomplete / invalid | dependency closure of this question | only declared coverage |
| LOOKUP_EXACT | exact graph and pointer | exact child, literal, sequence or absence | required direct navigation evidence | no contextual Source reconstruction |
| SPLIT_FRAGMENTS | exact graph and complete-node cuts | same root plus exact fragment map | selected nodes and structural ancestors | identity-preserving materialization |
| REFINE_EXACT | ordered exact base and overlay | complete exact compatible result | required exact operands and declarations | preserves inherited guarantees; not arbitrary edit |
| CHECK_SUBTYPE | candidate and parent definitions | Boolean or invalid/incomplete result | needed type and preservation evidence | specified subtype relation |
| REFINE_SCHEMA | ordered inherited/authored schemas | constraints or refined exact schema | schema operands and required domains | no explicit weakening |
| CONJOIN_SCHEMA | independent constraint descriptors | combined internal constraints | previously established predicates | conjunction, not override admission |
| EXPAND / COLLAPSE | exact graph + complete-node paths | another materialization | navigation and selected exact nodes | same exact identities |
| MINIMIZE | certified exact origin + goal | valid Source and available dependencies | enough evidence for the round trip | same required effective view; ID may change |
| ENCODE_EXACT / DECODE_EXACT | exact content / exact wire | identity-preserving exact representation | declared dependencies | codec, not Source compilation |
| ENCODE_COMPACT / DECODE_COMPACT | exact content / compact wire | identity-preserving compact representation | selected prefix evidence | codec, not Source replay |
| FINALIZE_SET / VERIFY_MEMBER | symbolic set / owning-set proof | master/mapping or verified member | complete set boundary and proof | exact set addressing; admission separate |


**LANG-ADMISSION-CLAIM.** Structural naming MUST NOT be presented as semantic admission. An operation claiming whole-document admission MUST establish the required exact graph and type definitions, then certify its explicit goal. A selected observation MUST NOT be used as whole-document certification. Definition and completed-value goals are distinct proof obligations, not different Blue node kinds.

### 2.6 Fundamental relationships

| Relationship | Required distinction |
|---|---|
| Exact equality | Includes own labels, type and all identity-bearing content |
| Scalar predicate comparison | Uses effective domain and the specified payload rules |
| Preservation | May permit additional object fields while retaining inherited guarantees |
| Subtype | Uses the specified structural/nominal relation, not a matching name |
| Semantic round trip | Preserves the observations defined by `same_view`; need not preserve Source ID |
| Availability | Missing evidence is neither an absent field nor a valid target |

**Algorithm:** A01 defines records and invariants; A03 defines exact identity; A06 defines effective recipes. `OPERATIONS` in the annex composes existing algorithms into the abstract operation contracts without a storage or receipt dependency.

---

<a id="parsing"></a>
## 3. Serialization, scalar codecs and empty content

### Purpose and input

Parse one JSON or portable YAML document into the shared node model without losing distinctions that determine identity. Formatting outside strings is not content. Parsed strings and number categories are content-bearing inputs to the subsequent codec.

### 3.1 Text parsing

**LANG-PARSE.** Read exactly one document. Reject duplicate decoded keys, non-string map keys, malformed Unicode and invalid syntax. A document root MUST NOT be null. JSON `\u` escapes use ASCII hexadecimal digits; valid surrogate pairs decode to one Unicode scalar, and unpaired surrogates fail. A parser MUST NOT replace malformed input with replacement characters.

Numeric tokens retain this complete ASCII grammar until scalar encoding:

```text
-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?
```

A token with neither point nor exponent is integer-spelled. A token with either is decimal/exponent-spelled. Thus bare `1` and `1.0` are not interchangeable inference inputs.

**LANG-YAML.** YAML supplies presentation syntax only. Quoted and block scalars are strings. An empty plain scalar or exactly `null` is null; exactly `true` and `false` are Boolean; a full JSON-number match is a retained number token; other permitted plain text is a string. Reject anchors, aliases, explicit tags, directives, merge-key syntax, multiple documents and non-JSON data types. Quoted `"<<"` is an ordinary string key. Plain `True`, `~`, `01`, `.inf` and date-looking text are not implicit Boolean, null, numeric or timestamp values.

**LANG-TEXT.** Preserve parsed strings exactly. Do not trim, case-fold, normalize Unicode, normalize line endings inside parsed strings, or remove block-scalar trailing newlines. YAML folding and chomping determine the parsed string. Different resulting strings may identify different nodes even when they look similar.

### 3.2 Wrappers and nulls

A bare scalar and a `value`-only wrapper normalize alike. A bare list and an `items`-only wrapper normalize alike. Explicit additional metadata remains content.

**LANG-EMPTY.** In ordinary objects, remove null-valued members but preserve an object left empty. Never remove a list position. Source list null becomes the designated hole. Exact and Direct list null is invalid. `{}`, `[]`, absence, empty Text and the hole are distinct.

| Input | Exact-normalization consequence |
|---|---|
| `{x: null}` | `{}` |
| `{x: {y: null}}` | `{x: {}}`; the `x` edge remains |
| `{value: null}` | `{}` |
| `{blueId: X, extra: null}` | Invalid mixed reference, before null removal |
| Source `[null, {}, []]` | `[HOLE, {}, []]`, three positions |
| `[1,2]` and `{items:[1,2]}` | Same payload-only list |
| `{type: List, items:[1,2]}` | Different exact node with an explicit type edge |

The hole is the ordinary exact object `{$empty:true}`. Its exact identity is `6V647wzsPU3zXvrc5AwKsqbFmkgHWV8WAeyBfNG1T8Rx`. A reference to that node has the same hole behavior. `{$empty:false}` or the same object with additional metadata is ordinary different content. Hole-filling permission applies only at the list-specialization positions specified in §8.

### 3.3 Own-type scalar encoding

**LANG-SCALAR-INFERENCE.** Without an own type, strings infer Text, Booleans infer Boolean, safe integer-spelled numbers infer Integer, and decimal/exponent numbers infer Double. No automatic container type is inferred. Converting an untyped decimal token to an integer because its current value is integral is not permitted.

The safe unquoted Integer interval is `[-9007199254740991, 9007199254740991]`, inclusive.

| Exact own type | Admitted input and exact output |
|---|---|
| **Integer** | Decode an integral numeric token exactly, or a canonical decimal Integer string. Store safe results as numbers and larger results as quoted canonical decimal strings. |
| **Double** | Decode an admitted decimal token/string to the nearest finite binary64 value, ties to even. Both zero signs have one commitment. |
| **Text** | Require a string. No automatic stringification. |
| **Boolean** | Require a Boolean. No truthiness or string-to-Boolean conversion. |
| **Custom type** | Retain the exact own type ID. Strings and Booleans stay their literal category; safe integral numeric spellings share the canonical numeric payload; other finite numeric values use binary64. Do not fetch ancestry merely to choose an intrinsic identity codec. |

**LANG-INTEGER-CODEC.** An unsafe integer-spelled token fails; quoted canonical decimal with explicit Integer is the portable representation. An explicit-Integer decimal/exponent token is evaluated as an exact decimal rational and must be integral. Canonical Integer strings forbid `+`, whitespace, leading zeros, `-0`, fractions and exponents. Numeric zero spellings normalize to zero. A natively tagged mathematical Integer is not a parsed unsafe number token.

**LANG-DOUBLE-CODEC.** Binary64 parsing uses round-to-nearest, ties-to-even. Nonfinite results fail; finite underflow to zero is permitted. Do not use an implementation-specific epsilon or decimal rounding during later comparisons. Integer-looking helper output does not change a Double node's type. Formatting follows the exact algorithm in A03, not a host's default floating-point display.

**LANG-CUSTOM-CODEC.** Intrinsic own-type encoding and contextual interpretation are separate. Resolution may interpret canonical Text under an inherited Integer requirement without rewriting that exact Text node. Core Integer and core Double remain nominally distinct, even when their payloads compare numerically equal.

### Outcomes and algorithm

Successful parsing returns values preserving these categories. Normalization returns `Node`/`Ref` values and newly established dependencies. Syntax, Unicode, grammar and codec errors are invalid input; reaching a declared resource bound is incomplete, not permission to truncate. Complete procedures: A02 and A03; contextual scalar decoding: A06.

---

<a id="identity"></a>
## 4. Exact normalization and BlueId

### Purpose

Calculate a content address from an established exact node. This operation neither proves type validity nor replaces content with the effective view. Source creation, strict admission and codecs are separate compositions over this same identity function.

### 4.1 Exact input preparation

**LANG-NORMALIZE.** Normalize permitted wrappers, own scalar encodings, null omission and type slots. In Exact mode, identify an inline type from its own exact content, retain its body as a dependency and place its reference in the parent. Direct mode requires all four type slots and the `specification` metadata slot already to contain pure references. Unresolved Source aliases are not Exact or Direct input.

Preserve complete explicit child nodes. Do not insert inherited fields, subtract a child's inherited fields, apply contextual type narrowing, or silently remove an explicit field during exact hashing. The separately named canonical authoring operation in §11 permits only its specific root-duplicate transformation.

**LANG-SCHEMA-IDENTITY.** `schema` and `contracts` use ordinary exact child identities. Predicate evaluation does not change their exact content. Exact enum order and duplicates remain identity-bearing; effective enum interpretation is a separate operation. Explicit false keyword values are not removed merely because a predicate appears neutral.

### 4.2 Hash helper

Let `I(n)` identify a prepared node. Let `H(m)` hash raw canonical JSON helper `m`. A helper is not Blue content and is never passed through primitive inference again.

**LANG-HASH.** A reference contributes its target identity directly. For a materialized node, retain `name`, `description` and `value` as literals. `items` contributes its payload-list identity; `mergePolicy` contributes the exact core Text identity of its literal; every other retained field contributes its child identity. Hash the resulting helper once.

```python
def helper(n,token=None):
    m={}
    for k,v in n.fields:
        if k in LITERALS: m[k]=v
        elif k=='items': m[k]={'blueId':list_id(v,token)}
        elif k=='mergePolicy': m[k]={'blueId':identity(scalar('Text',v),token)}
        else: m[k]={'blueId':identity(v,token)}
    return m
```

For an `items`-only node the result is the payload-list identity itself. A metadata-bearing list additionally hashes the outer object helper. The root's identity is the document identity; there is no filename or document-envelope hash.

### 4.3 List fold

**LANG-LIST-HASH.** Preserve order, multiplicity, nesting and all exact elements. Start with `H({"$list":"empty"})`. For each element, update the accumulator with the domain-separated pair of the previous payload identity and the element identity. Do not hash an array of elements or an array of IDs instead.

```python
def append_id(p,e): return H({'$listCons':{'prev':{'blueId':p},'elem':{'blueId':e}}})
```

```python
def list_id(xs,token=None):
    p=H({'$list':'empty'})
    for x in xs: p=append_id(p,identity(x,token))
    return p
```

A known exact payload-prefix ID can seed further fold steps. It does not by itself establish the prefix's length, element contents or type validity. A prefix reference used as an ordinary element denotes a nested list, not concatenation.

### 4.4 Canonical helper bytes

**LANG-CANONICAL-BYTES.** Apply the canonical helper encoding defined here and in Appendix D to each helper. Order decoded object names by unsigned UTF-16 code units; preserve array order. Use required JSON escapes, exact Unicode content and the specified shortest binary64 rendering. Encode as UTF-8 without BOM, optional whitespace or trailing newline. Hash those bytes with SHA-256 once.

The binary64 formatter searches exact rational candidates. Fixed notation applies from decimal exponent −6 through 20; otherwise use lowercase `e`, a `+` for a nonnegative exponent and no redundant leading zeros. The full candidate-selection and tie rules are executable in `number_text`. Neither a locale formatter nor default whole-object serialization supplies the required behavior automatically.

**LANG-ID-ENCODING.** Base58-encode the 32 digest bytes using `123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz`. Leading zero bytes become leading `1` characters. Do not add a checksum, multibase prefix, byte reversal or hexadecimal intermediate. Incoming plain IDs must canonically decode to exactly 32 bytes. A cyclic-member ID is a plain master followed by `#` and a canonical nonnegative decimal index.

### 4.5 Why representation substitution works — informative

A complete child and its reference supply the same child ID to the same helper position. Consequently the parent helper bytes are unchanged. Repeating the argument upward proves substitution for finite acyclic structure; repeating the fold proves it for lists. This is an identical-preimage argument, not a claim that finite digests are injective. Cyclic finalization has the separate ordering and proof rules in §12.

The premise matters: replacing content with an inherited delta or replaying a Source constructor does not preserve the exact child. The hash rule cannot make those transformations correct.

**Outputs:** exact ID; helper traces may be exposed separately. **Evidence:** the reference identity itself suffices for structural naming; requested interpretation or admission can require bodies. **Full algorithm:** A03. Worked bytes appear in §15.

---

<a id="graph"></a>
## 5. References, verified graph access and materialization

### Purpose

Obtain the exact content needed for an operation without making its meaning depend on whether that content was inline, cached or fetched. Address verification establishes that a body belongs to an ID. Semantic certification establishes different facts and follows §§6–10.

### 5.1 Evidence required to open a node

**LANG-VERIFY.** Before using a fetched plain body, normalize it in the explicitly selected role and recompute its exact ID. Require equality with the requested ID. A body consisting only of a reference repeating the requested ID is not materialization evidence. A fetched child may remain referenced; authenticating its parent's direct commitment does not require recursively fetching it.

An ordinary exact provider supplies already-established content. A separately selected Source provider must bind the interpretation environment and establish the requested exact result through that declared preparation path. Neither interface may retry under alternate modes or substitute a different registry after a mismatch. The provider-record procedures in Appendix D define the required interpretation and evidence checks. An adapter may use another carrier while preserving those checks.

**LANG-EVIDENCE-OUTCOME.** Required unavailable or incomplete content yields an incomplete operation. Wrong or malformed content yields invalid evidence. Neither is semantic absence. A complete direct manifest must authenticate every direct contribution needed to establish its identity; a partial map cannot establish a missing key by omission. No body is trusted merely because it came from a cache or a configured database.

A finalized cyclic member requires an owning-set proof. Hashing its detached materialized body as an ordinary node does not authenticate its `MASTER#index` identity.

### 5.2 Logical paths

**LANG-PATH.** Paths use slash-separated components and tilde escaping over the abstract node as follows. `""` denotes the root; `/` denotes an empty-named child; `/items/0` denotes a list element. Only `~0` and `~1` are valid escapes. Traversal must open a referenced container when its structure is required. The syntax wrapper's `blueId` is not a semantic child.

Literal slots can be inspected where the operation permits them. They cannot be collapsed into child references. The `items` sequence is not an independently addressable node slot; its complete enclosing list is.

### 5.3 Expansion, collapse and fragments

**LANG-MATERIALIZATION.** Expansion reveals selected verified nodes; collapse replaces selected complete nodes by their exact references. Both preserve root identity and the identities of retained exact children. Navigational ancestors may be opened; unrelated child payloads need not be opened solely to carry their references. A cyclic handle preserves its member identity and owning proof during these operations.

The fragment operation cuts a declared set of complete-node positions. Its structural ancestors are materialized as needed, selected non-root nodes are collapsed and the returned fragment map supplies their bodies under their own IDs. A cut is a request to export the selected complete node, including when that node is already a reference. Verify and include its body under the requested exact ID; do not silently omit an available referenced cut. Required missing evidence makes the split incomplete and wrong evidence invalid. Unselected referenced children remain opaque unless another required navigation opens them. For cyclic members, retain the member address and supply the owning-set proof with the exported body, rather than hashing the detached body into a new address. The order of the requested cuts does not select different fragment content. Literal slots and the `items` sequence slot are not valid cuts.

### 5.4 Immutable evidence and caches

**LANG-CACHE.** Reusing immutable verified content may eliminate physical retrieval. It MUST NOT change successful semantic results, erase a validation obligation or turn incomplete evidence into established absence. Interpreted results are bound to the exact input, requirements, goal and selected rules, not solely to a display body. A changed exact node requires a new identity and any newly necessary checks.

Whole-graph admission can require substantially more evidence than a selected read. This does not make selected reads invalid: their result must state the scope of what was established. No selected result becomes a whole-document certificate by being stored in a cache.

**Inputs:** an exact node/reference, selected paths or a requested body, and the fixed evidence context. **Outputs:** the verified node, changed materialization or declared observation. **Failures:** invalid paths/content/evidence; incomplete evidence or limits. **Algorithms:** A04, A06 and A12.

---

<a id="types"></a>
## 6. Types, specialization and validation goals

### Purpose

A type contributes guarantees. A descendant may add compatible information, fill permitted declarations and narrow constraints, but cannot contradict those guarantees. Whether a node is used as a definition or a completed value is a property of the operation, not an extra serialized node category.

### 6.1 Any admitted node may be used as a type

**LANG-TYPE-CONTRIBUTION.** Using node T as a type contributes its declared structure, fixed values, nested requirements, collection metadata and schemas. Retain T's exact identity separately from the effective requirements it supplies. A complete type's `items` are its complete exact payload, not a suffix to append again.

A type need not look like a programming-language class. A node representing a particular individual may itself become a type; its fixed content then constrains descendants.

### 6.2 Definition and completed value

**LANG-GOAL.** Definition admission establishes valid declarations, fixed contributions and specified local consistency while allowing future payloads to remain unspecified. Completed-value admission additionally checks all active value obligations. Neither goal exempts malformed shapes, unknown required type definitions, incompatible fixed content or explicit weakening. The caller must select the goal; a failed value request MUST NOT silently fall back to definition admission.

```yaml
name: Currency
type: Text
```

This is a valid definition. It is not a completed Text scalar because no payload was supplied. Its `name` does not itself select definition mode. A value of that type can supply `value: PLN`.

```yaml
name: Two to four integers
type: List
itemType: Integer
schema:
  minItems: 2
  maxItems: 4
```

This is a valid list definition with an unspecified future payload. Adding `items: []` supplies a concrete empty list, which violates the minimum even during definition admission. Omitted payload and explicit empty payload are different.

### 6.3 Preservation versus equality

**LANG-PRESERVATION.** A descendant must retain all inherited guaranteed fields, fixed scalar values, applicable types, collection requirements, schema obligations and list-prefix guarantees. Fixed scalar comparisons use effective scalar type and value. Object refinement may add fields without contradicting any inherited child; it does not require the whole object's ID to remain equal. List preservation follows §8.

For parent `x: 1`, supplying `x: 2` fails. For parent `address: {city: Warsaw}`, adding a `street` within `address` may succeed if no additional rule forbids it; changing `city` does not.

An omitted contribution inherits what is already guaranteed. It does not remove a requirement. A referenced child is not exempt from comparison, and its effective enrichment must not overwrite its exact content.

### 6.4 Names and descriptions

**LANG-LABELS.** Own `name` and `description` affect identity. At every type-to-instance boundary, the type root's labels do not flow to the new instance. Matching ignores root labels, but exact fixed-node preservation includes its identity-bearing labels. Reused inherited declaration children carry their own labels until permitted override; present labels on fixed child content cannot be changed incompatibly. An absent label may be supplied where the merge permits it.

The own `specification` metadata also does not become an instance field. Its governing association remains discoverable on the exact referenced type and its ancestry; a subtype cannot erase a base protocol by declaring different own metadata. See §17 for definition-valid target checks and atomic preservation.

An instance of Address may be named Delivery Address or have no name. Expanding its type may reveal `name: Address` inside that type node; this does not name the instance Address. Expanding a reference to the instance reveals the instance's own labels.

### 6.5 Type compatibility

**LANG-SUBTYPE.** The six core types are nominal exact registry identities. Distinct cores are not interchangeable. Declared ancestry establishes a subtype relationship, and the specified structural comparison can establish compatible specialization by checking kind/core, guaranteed content, constraints and collection metadata. Matching a human-readable type name is not evidence. Merely finding one common accepted value is not a subtype proof.

The procedure is a defined structural simulation over this vocabulary, not an unrestricted theorem prover. `guarantees_schema` can establish requirements from fixed scalars, finite alternatives and guaranteed structure. Applicability remains binding: `uniqueItems: false` still describes a list predicate, not an unconstrained scalar type.

A supplied primitive may acquire a compatible contextual domain in its effective view. Canonical Integer text is interpreted under an inherited Integer requirement by `scalar_effective`. No contextual conversion changes the exact operand used for identity. The code supplies the complete decoder and compatibility cases.

### 6.6 Type chains, recursive graphs and termination

**LANG-TYPE-CYCLE.** Resolve own-type ancestry depth-first and reject a type repeated on its active inheritance chain. Completed reuse in another branch is sharing, not a cycle. Supported recursive object/list references do not automatically make an inheritance cycle. Structural comparisons use the specified guarded repeated-pair algorithm; recursively unfolding declarations must not manufacture presence or a completed value.

Recipes retain ordered exact contributions and contextual requirements for one position. A head is its local effective interpretation with deferred child recipes. The exact same contribution is not merged twice merely because it was reached through two equivalent materializations. These records are notation; production implementations may store equivalent information differently.

### 6.7 Collections and content maps

**LANG-COLLECTION-TYPES.** `itemType`, `keyType` and `valueType` inherit when omitted and may only be narrowed when supplied. Every applicable list element and Dictionary value must satisfy its requirements. Direct Dictionary keys must be canonical text of a supported scalar key domain; reject noncanonical keys rather than renaming them. The default key domain is Text when no key type is inherited or authored.

A collection child has one contextual recipe: its exact own/inherited contributions plus the enclosing `itemType` or `valueType` requirement. Construction, validation, complete resolved export, selected query and semantic comparison MUST use that same recipe. A complete export cannot describe the raw child alone while a query describes the constrained child. Requirements retain their nested fields, schemas and nominal type, not only their primitive kind.

For `type: Dictionary`, `valueType: {type: Integer}`, `foo: "3"`, both complete and selected effective observations describe Integer 3. The exact admitted child is still the supplied Text "3"; contextual interpretation is not an identity rewrite. Adding `schema: {minimum: 2}` to `valueType` must preserve that constraint in both observations.

Strict admission establishes all declared type definitions even for empty collections. A Dictionary key domain that is not a supported scalar is invalid even when there are no keys. This is distinct from selected resolution of an unrelated field.

**Algorithms:** A06 for types/heads/preservation and A07 for exact refinement. **Results:** effective declaration/value or a compatibility, schema, type-cycle or evidence outcome. Examples do not override the procedural checks in the annex.

---

<a id="schemas"></a>
## 7. Schemas: predicates, narrowing and conjunction

### Purpose

A schema is ordinary exact content with a separately defined interpretation. Refining an inherited schema is not the same operation as conjoining independent requirements. This distinction prevents an invalid authored weakening from being hidden by a stronger inherited predicate.

### 7.1 Vocabulary and operands

**LANG-SCHEMA-VOCABULARY.** Interpret only the keywords in the following table. Establish referenced schemas and operand nodes before using them. Inline, wrapped and referenced operands must select the same predicate when they identify the same admitted scalar or sequence. Unknown keywords and wrong operand types fail; there is no implicit `const`, general expression language or `enumAll` keyword.

| Keywords | Operand | Predicate domain |
|---|---|---|
| `required` | Boolean | Child presence; root existence already satisfies root requiredness |
| `minItems`, `maxItems` | Safe nonnegative Integer | Number of effective list elements |
| `uniqueItems` | Boolean | Exact element identities in an effective list |
| `minFields`, `maxFields` | Safe nonnegative Integer | Present ordinary object fields |
| `minLength`, `maxLength` | Safe nonnegative Integer | Unicode scalar count in Text |
| `minimum`, `maximum` | Numeric scalar | Inclusive exact-rational endpoints |
| `exclusiveMinimum`, `exclusiveMaximum` | Numeric scalar | Exclusive exact-rational endpoints |
| `multipleOf` | Positive numeric scalar | Integral exact-rational quotient |
| `enum` | Payload-only sequence of scalar restrictions | Required primitive payload and compatible type domain |

Every scalar operand MUST itself be certified as a completed value, including its own fixed data, nominal ancestry and schemas, before its scalar description is used or memoized. Describing a number without checking its own minimum, enum or other constraints is not sufficient. This obligation applies even when the containing node is being admitted only as a definition. The same rule applies to numeric, count, Boolean and enum operands, whether inline or referenced. A successful address check is not operand admission. Reentrant operand validation is an invalid recursive operand dependency, not provisional success; reaching an operation limit remains incomplete. Operand diagnostics identify the relevant schema keyword and, for enum, the item path.

A numeric-looking Text is not automatically a numeric bound. Use an explicit Integer node for large Integer bounds. Schemas affect validity, not the identity codec of their enclosing scalar.

### 7.2 Presence and applicability

**LANG-SCHEMA-PRESENCE.** A metadata-only declaration does not by itself supply a completed payload. Fixed inherited content can establish presence. `{}` and `[]` are present content. An optional absent child's value obligations remain inactive, while definition checks still apply. A pure reference cannot be classified as an absent field merely because its body is unavailable.

**LANG-SCHEMA-APPLICABILITY.** A predicate's domain must match the effective known kind. Do not silently ignore a string predicate on a number or a list predicate on an object. A seemingly neutral operand, such as `minLength: 0`, retains its domain requirement. For a nominal scalar with no established primitive ancestor, a supplied effective scalar payload nevertheless establishes the predicate carrier: Boolean, Integer, Double or Text according to its already normalized scalar category. Apply applicable predicates to that carrier and reject incompatible predicates; do not skip them merely because `core` is absent. This does not synthesize a nominal ancestry edge or rewrite the exact type. A payload-free definition may defer that carrier until a payload is supplied; ordinary local-consistency and definition obligations still apply. Enum domain compatibility remains the declared subtype check, not host-language coercion.

Count present ordinary fields only; reserved metadata does not contribute to `minFields` or `maxFields`.

### 7.3 Numeric predicates

**LANG-SCHEMA-NUMERIC.** Integer values are exact mathematical integers. Double values and bounds use their exact binary64 rational values. Compare rationals exactly. `multipleOf: m` requires positive m and an integral quotient. No epsilon, decimal-display rounding or host floating-point modulo is permitted.

For positive reduced rationals `p1/q1` and `p2/q2`, independent divisibility requirements combine to `lcm(p1,p2)/gcd(q1,q2)`. This is an internal exact constraint, not permission to emit a rounded Double schema. The constraint descriptor may retain exact numerator/denominator values without inventing new identity-bearing Blue fields.

### 7.4 Explicit refinement

**LANG-SCHEMA-NARROW.** Check the authored facets against inherited facets before conjunction. Omission inherits. An explicitly supplied facet must retain or increase strictness; incompatible or weaker facets fail even if conjoining them with the parent would restore the parent's restriction.

| Inherited facet | Allowed explicit descendant facet |
|---|---|
| Lower endpoint | Equal or higher; inclusive at an equal inherited exclusive endpoint is weaker |
| Upper endpoint | Equal or lower; inclusive at an equal inherited exclusive endpoint is weaker |
| Minimum length/count | Equal or higher |
| Maximum length/count | Equal or lower |
| `required: true` or `uniqueItems: true` | Repeat true; omission inherits; explicit false fails |
| `multipleOf: m` | A positive integral multiple of m under exact rational comparison |
| Enum alternatives | Alternatives covered by the inherited domain/payload restrictions according to the algorithm |

When both inclusive and exclusive endpoints are written on one side, check **each authored endpoint separately** against the inherited effective endpoint before selecting the stronger resulting endpoint. Over inherited `minimum: 5`, authored `{minimum: 4, exclusiveMinimum: 6}` is invalid: the second facet does not excuse the first. Likewise inherited `maximum: 10` rejects `{maximum: 11, exclusiveMaximum: 9}`. Raw authored-facet provenance is distinct from the conjoined effective constraint descriptor.

Thus `[5,10] → [6,9]` succeeds, while `[5,10] → [4,11]`, `[4,9]` or `[6,11]` fails. `multipleOf: 4 → multipleOf: 6` is not narrowing: 6 itself violates the parent. Requiring both independently is a different operation and yields multiples of 12.

The decisive call order is the executable rule:

```python
def refine_schema(parent,authored,c=None):
    check_schema_narrowing(parent,authored,c)
    return conjoin_schema(parent,authored)
```

### 7.5 Independent conjunction

**LANG-SCHEMA-CONJOIN.** Independent applicable obligations all remain in force. Combine requiredness and uniqueness with OR, minimum sizes with maximum, maximum sizes with minimum, numeric endpoints with the stronger bound, and divisibility by exact rational LCM. Exclusivity wins at an equal endpoint. This operation does not admit an explicitly invalid override.

Exact schema refinement retains the ordered base/overlay's supplied keyword encodings after successful admission. Independently combined internal constraints need not be serialized as one new exact schema node. There is no universal semantic-schema minimizer in the identity calculation.

### 7.6 Enumerations

**LANG-SCHEMA-ENUM.** An entry denotes its scalar domain and canonical primitive payload. A candidate must match the primitive payload and have an equal or narrower established domain. Labels do not select another scalar predicate. A referenced restriction has the same meaning as its verified inline form. Exact enum order/multiplicity remains content; effective interpretation may eliminate duplicate alternatives.

Independent enum requirements are conjunctions of alternative groups: every group must accept. The internal descriptor may retain those groups rather than invent a type representing their intersection. An established empty primitive-payload intersection fails. Equal primitive payloads do not by themselves prove compatible type domains; the specified subtype procedure still applies.

### 7.7 Consistency versus existence of a future value

**LANG-SCHEMA-LOCAL.** Definition preparation checks the specified local contradictions: keyword forms and applicability, size-bound order, numeric endpoint consistency, nonpositive divisibility, empty alternatives and violations by supplied fixed data. It does not prove the existence of every possible completing value. A supplied fixed prefix below its minimum is invalid; an omitted future payload retains its obligations. Completed values must satisfy every active predicate.

**Algorithm:** A05, with scalar domain/type procedures in A06. **Outcome:** normalized internal constraints or a specific invalid/incomplete result. The algorithm never changes schema content merely to make its own acceptance test succeed.

---

<a id="lists"></a>
## 8. Lists and specialization

### Purpose

Separate an exact list's complete payload from Source authoring and from compatibility checking. Append-only Source explicitly declares its inherited prefix. Ordinary positional Source presents indexed elements or a separate, pure edit sequence. Neither mode guesses intent from how many values happen to be written. The exact element fold remains §4; authoring is not a second list hash.

### 8.1 Complete candidates preserve inherited guarantees

**LANG-LIST-PRESERVE.** A complete positional descendant of `[N, HOLE, R]` must retain at least that prefix. Its elements are `[N′, V, R′, ...]`, where N′ preserves N and R′ preserves R. The hole supplies no fixed-value guarantee; applicable element types, schemas and container rules still apply. `{}` is an ordinary object, not a hole. Neither a repeated scalar nor `$replace` may contradict inherited fixed content.

**LANG-LIST-POLICY.** Omitted policy inherits; absent any selected policy, the default is positional. An explicitly conflicting inherited policy fails. Under append-only, every inherited element retains its exact identity, including a hole. Positional edits are forbidden. The suffix remains subject to `itemType`, bounds and uniqueness. `$previousItems: false` does not switch policy or remove a prefix.

### 8.2 Select the Source mode from established context

**LANG-SOURCE-LIST-CONTEXT.** Apply authoring rules only to Source expressions. Exact handles, pure references and explicitly Exact/Direct content are already complete operands, not programs to replay. Compile type-expression positions before establishing the enclosing declaration. A supplied item sequence always uses both the node's own type and its containing context, including collection metadata even when that context has no fixed items.

| Condition | Required action |
|---|---|
| Exact handle or pure reference | Retain the complete exact operand; do not recompile its body as Source |
| No authored `items` slot | Inherit normally without injecting a complete inherited payload into exact identity |
| Contextual declaration has an inherited list payload | Establish its complete exact prefix and collection requirements, even with local `type: List` or omitted local type |
| Established policy is append-only and `items` is authored | Require exactly one initial verified prefix assertion, then compile only suffix elements |
| Established policy is positional and any top-level item is an edit | Require an edit-only sequence; edits address the original base |
| Established policy is positional and there are no controls | Interpret ordinary elements at indices 0 through n−1, retaining/refining each inherited position |

Unavailable evidence needed to establish the declaration is incomplete, not an empty prefix. The spelling or placement of the same admitted type must not drop `itemType` requirements. Unrelated siblings cannot select another list's authoring mode.

### 8.3 Establish the inherited base

**LANG-LIST-BASE.** Combine the own type and independently applicable containing declaration using the ordinary requirement rules. Keep complete exact base elements separate from their effective interpretation. Conflicting fixed contributions fail; traversal order does not choose a winner. A published type's exact items are already complete. An anchor verifies that selected payload; it cannot choose another provider list as a base.

### 8.4 Disjoint Source grammars

**LANG-LIST-CONTROLS.** Recognize controls in their instruction position before ordinary element inference. A sequence belongs to exactly one of the following grammars. Reject malformed, misplaced, repeated or mixed controls; never silently reinterpret them as ordinary data.

| Mode | Sequence | Meaning |
|---|---|---|
| Append-only shorthand | `[{$previousItems: true}, X, Y, ...]` | Assert a nonempty inherited prefix; append the new elements |
| Append-only empty-prefix shorthand | `[{$previousItems: false}, X, Y, ...]` | Assert that there are zero inherited elements; supply the new elements |
| Append-only exact assertion | `[{$previous: {blueId: P}}, X, Y, ...]` | Verify P is the payload-only ID of the selected inherited prefix; append the new elements |
| Positional presentation | `[X0, X1, ..., Xn]` | Present successive positions, refining inherited entries and then extending beyond the inherited length |
| Positional edits | `[{$pos: i, ...overlay}, {$pos: j, $replace: X}, ...]` | Edit only specified original inherited positions; retain all other positions |

`$previousItems` has exactly one member whose value is a Boolean literal, not a string, wrapper, reference or truthy value. It must be first and unique, and it is legal only for an established append-only list. `true` requires at least one inherited element; `false` requires zero. Both an absent inherited payload and an established empty payload have zero elements, but unavailable evidence establishes neither. `$previousItems` and `$previous` cannot be combined.

Whenever append-only `items` is authored, an initial assertion is REQUIRED, including for a new list, an empty suffix or an empty resulting list. Thus `items: []` and an unmarked `[C]` are not valid append-only Source. Omit `items` to inherit without a local list contribution. Use `[{$previousItems: true}]` to explicitly contribute no suffix over a nonempty prefix, and `[{$previousItems: false}]` for an empty prefix with no new elements. These remain distinct authoring forms and may retain distinct own payload contributions.

The `$previous` record has exactly one `blueId` member containing a valid plain content ID. Its identity must match the complete payload-only inherited sequence, not the surrounding typed List node. It is an assertion, not a reference element or a base selector. Prefix controls are forbidden in positional Source even when they happen to name its inherited payload.

For positional edits, index i is a safe nonnegative Integer token, not a decimal/exponent token, string or Boolean. It must address an existing position in the original inherited base. Duplicate indices fail. `$replace` requires `$pos` and cannot be combined with overlay fields. The concise `{$pos: i, value: v, ...scalar metadata}` form and compatible object overlays remain supported. An edit sequence cannot append, and ordinary positional elements cannot be mixed with edits, including an edit at a fifth or later position. To extend and refine in one authoring expression, use the full positional presentation.

A normal exact reference in an element position always supplies a complete element, even when its body has control-looking keys. Literal control-looking exact content can be published separately and referenced; it is not a way to inject another authoring instruction.

### 8.5 Construct once, then validate

**LANG-LIST-CONSTRUCT.** Prepare each Source operand once in its final position's context. For append-only, retain the exact base unchanged and append in written order. Suffix item j is compiled at absolute position `len(base) + j`, not without an index. For pure edits, process distinct original indices in increasing order. For positional presentation, the number of elements must be at least the inherited length: each inherited element is refined by the candidate at the same index, and elements beyond that length are appended. A shorter presentation is invalid, not an implicit suffix or truncation.

A positional hole supplies no payload-kind constraint for its replacement, but the enclosing `itemType` still applies. Both replacements and positional overlays preserve fixed inherited guarantees. Retain base-only object fields; do not manufacture deltas that lose the complete child. At the admission boundary, validate the complete constructed node and all applicable containing declarations before returning success. Source construction alone does not certify validity: raw structural naming need not fetch opaque child references solely because a list is present. The exact result retains its own explicit metadata; do not copy every effective schema or a type root's labels into stored content.

### 8.6 Nested list context — informative example

The following Source selects append-only behavior at the inner list and supplies both prefix assertions explicitly:

```yaml
type: List
itemType:
  type: List
  mergePolicy: append-only
  items:
    - $previousItems: false
    - 1
items:
  - - $previousItems: true
    - 2
```

Its effective items are `[[1, 2]]`. Moving `type: List` and the same `itemType` declaration into an inline or separately published enclosing type retains the inner context and the same effective result. Different explicitly supplied metadata need not produce the same outer exact ID.

Without `mergePolicy: append-only`, the inner list is positional. Its full presentation is `[1, 2]`; `[2]` attempts to replace fixed 1 with 2 and fails in both declaration placements. This is an intentional grammar distinction, not a remaining context bug.

**Algorithms:** A07 defines preservation and pure edits; A09 defines Source construction and contextual child selection; A13 defines compact wire. Exact/Direct loading never executes these Source controls.

---

<a id="preprocessing"></a>
## 9. Preprocessing and Source preparation

### Purpose

Turn authored syntax into a single, explicitly interpreted Source expression, then construct exact content where the language requires it. Preprocessing does not change what an already-published exact reference means.

### 9.1 Directive and bindings

**LANG-PREPROCESS-DIRECTIVE.** With no root `blue` field, apply the mandatory baseline using the selected environment. A present directive is an inline configuration, a verified reference or an explicitly configured directive-alias string. A null root directive is invalid. Nested or transformation-introduced `blue` fields fail. Unknown directive fields are not silently ignored.

The directive permits `imports`, `transformations` and its own identifying `name`, `description` and exact `type`. These metadata identify the configuration; they do not become fields of the resulting document. Null optional members denote omission, not a Boolean/number/string fallback to an empty configuration.

**LANG-ALIASES.** Directive imports map aliases to pure final-ID references, including finalized cyclic-member addresses. Their target bodies are required when a later operation needs them, not merely to bind a name. Do not rebind a core alias to another ID. Automatic alias substitution applies only in `type`, `itemType`, `keyType` and `valueType`; an ordinary Text with the same spelling is unchanged. A matching node `name` does not create an alias.

Directive aliases are explicitly selected environment bindings. URL-looking text is not permission to fetch and execute unverified content. Exact IDs, not provider locations, select configuration.

### 9.2 Establish the entire plan before execution

**LANG-PREPROCESS-ORDER.** Resolve and verify required directive/configuration operands, establish imports and validate the complete ordered transformation plan before running its first transformation. Remove root `blue`; run transformations once in order; then run mandatory wrapper/null normalization, alias substitution and primitive inference. A transformation sees Source before automatic baseline inference and may emit Source shorthand for the baseline to normalize.

| Stage | Output or stopping condition |
|---|---|
| Parse | One Source value with retained numeric tokens |
| Establish configuration | Verified directive, imports and complete supported transformation plan |
| Remove directive | Working Source, not a document carrying `blue` as ordinary content |
| Execute transformations | Complete result of each prior transform, exactly once |
| Mandatory baseline | Valid prepared Source expressions; construction controls may remain |
| Compile | Exact node, with actual constructors selected by §8 |

A preflight failure runs no transformation. A transformation failure does not yield a successful partial document. An implementation may fuse steps only when the same ordering and outcomes are preserved.

### 9.3 Transformation semantics

**LANG-TRANSFORMS.** Select transformations by their exact registered selector, never by a human name. Required unsupported selectors fail explicitly. Configuration operands are exact content and use the same rules inline or referenced. Transforms are deterministic functions of the fixed input and verified operands; no clock, locale, randomness, mutable database or unverified network data selects the result.

The selected reference environment implements primitive inference, mapped alias replacement, root-field renaming, root-Text suffix appending and root Source-expression assignment. Selector IDs, precise fields and procedures are in A08 and Appendix B.2. This is not a generic executor for unspecified extensions.

The Set Root Source Field transformation stores its input expression as Text under `expression`, with an explicit `json`/`yaml` format. It does not place arbitrary object content in reserved scalar `value`. Expression parsing happens during preflight; assignment happens during execution; baseline alias/type inference follows execution.

### 9.4 Compilation is not full-view replacement

**LANG-SOURCE-COMPILATION.** Compile authored inline definitions once in their own context, retain dependency bodies, preserve ordinary explicit content and execute only the constructors selected in §8. A complete exact handle/reference is retained, not recompiled. A constructor can demand inherited operands; the hasher still receives the newly constructed exact result rather than an effective resolver record.

A node with no supplied items does not acquire its inherited list payload for identity solely because resolution can reveal that payload. An authored supplied sequence at a contextually inherited list path is different: §8 selects construction and produces the complete exact sequence. This distinction is part of Source meaning and does not apply to exact loading.

Source preparation itself does not certify the entire result. `ADMIT_SOURCE` performs the additional checks and canonical root normalization in §11. Preprocessing configuration is not recoverable from the final node; applications needing source provenance retain it separately.

**Inputs:** Source, fixed aliases/directive bindings, selected transform definitions and evidence. **Outputs:** preprocessed expression or constructed exact node and retained dependencies. **Algorithms:** A08 and A09. **Failures:** syntax/configuration, unsupported required transformation, invalid construction, invalid or unavailable evidence, declared limits.

---

<a id="resolution"></a>

## 10. Complete and selected resolution

### Purpose

Interpret a node under its own and contextual requirements without changing the node's exact identity. A query can establish one answer; definition preparation and completed-value certification establish broader guarantees. Coverage belongs to the result, not to the node.

### 10.1 Effective contributions

**LANG-RESOLVE-MERGE.** Resolve required own-type plans before combining them with instance contributions. Merge ordinary child fields recursively, preserve compatible fixed scalars and list guarantees, narrow authored metadata and retain all independent requirements. No conflicting fixed requirement wins by traversal order. Keep exact origins and the required contribution relationships available for subsequent checks.

The local effective result includes kind, type, scalar value or deferred child recipes, labels, collection metadata, merge policy and constraints. Child recipes are opened only when the requested operation requires their semantic facts. A fully known local head does not by itself certify every child target.

### 10.2 Certification order

**LANG-CERTIFY.** Certification first checks the definition and its fixed data. A value goal then certifies active completed values. Optional absent value subtrees remain inactive; definitions are not manufactured into present values. Strict admission additionally verifies the reachable exact graph and every declared type slot, including empty collection definitions.

The decisive goal ordering is:

```python
def certify(exact,c,goal='value'):
    require(goal in ('value','definition'),'InvalidOperation','validation goal')
    validate(exact,c,'definition')
    return validate(exact,c,'value') if goal=='value' else head(recipe(exact),c)
```

The finite traversal memoizes exact recipe/goal obligations. An identical exact child used under different contextual requirements does not inherit a certificate for requirements that were never checked. Missing proof cannot be replaced with a provisional success.

### 10.3 Selected observations

**LANG-OBSERVE.** To establish a selected answer, resolve its semantic dependency closure: the relevant source/type contributions, path ancestors and constraints needed for that question. The answer must agree with complete processing on the declared coverage when the same evidence is available. In particular, traversing a Dictionary child through `valueType`, or a List child through `itemType`, retains the same contextual type, scalar value, constraints and nested requirements as complete resolved export. Use the contextual `child_recipe` rule, not independent copies of field traversal. Do not resolve an unrelated sibling payload solely because it exists.

The reference observation vocabulary includes exact identity, effective kind, existence, literal/value observations, object keys, list length or an item, effective type, constraints and validity. Each question has its own evidence requirements. An exact identity can be known while an effective kind or value remains unavailable. A field's absence requires evidence of the relevant direct and inherited contributions.

**LANG-OUTCOME.** A requested operation establishes a result, establishes absence where applicable, is incomplete, or finds invalid content/evidence. Those outcomes are distinct. A limit, unavailable reference or incomplete manifest must not become normal absence. A partial observation must not be promoted into whole-node canonical creation, completed-value admission or unrestricted minimization.

Concrete SDK result objects may have different shapes. The semantic conclusion, required diagnostic facts and claimed coverage must remain the same. A result containing only some observations is not a second, partially valid Blue node.

### 10.4 Resource controls and repeatability

**LANG-LIMIT.** Language imposes no universal resource/cardinality ceiling on otherwise valid finite input. Text size, parsed depth and value count, Integer text length, decimal normalization scale, internal work counters and provider-demand counts are not content-validity or identity rules. Explicit schemas, numeric kinds, canonical encodings and actual semantic errors remain binding.

An implementation may expose host resource controls. An omitted resource control means no library-imposed ceiling for that operation, not an implicit reference default. Such controls are out of band. Exhaustion, allocation failure, recursion failure, cancellation or an unavailable required resource before the requested conclusion is established yields incomplete work, never a truncated successful value, normal absence, invalid-content conclusion or alternative BlueId. A host unable to establish a result must report its inability; another adequately provisioned conforming host may establish the same result.

Controls must be applied consistently to equivalent Source/Exact spellings and every relevant helper; no helper silently reinstalls the old defaults. A requested export either completes in its declared exact format and can be verified, or remains incomplete. An export-envelope or transport-size restriction is operational, not a smaller domain of Blue values.

Language physical work/fetch counts are not Contracts gas and must not be converted into a gas rejection. In a Contracts invocation, the caller's deterministic meter remains authoritative for semantic processing. Physical Language optimizations and private admission evidence do not change that meter's prescribed charges or justify accepting invalid or missing content. Standalone Language parsing, identity, admission and source-proof acquisition do not acquire an invented 100,000-gas charge merely because Contracts has that budget.

Implementations should use lazy exact references and iterative/incremental processing where required to avoid incidental stack or materialization failures. This requirement does not promise completion on every machine or change type inference, constraints, canonicalization or BlueId algorithms.

**Algorithms:** A06 defines type plans and merging; A05 defines constraints; A12 defines selected operations and outcomes; A13 supplies strict graph/type admission. Revise their resource-control plumbing and incomplete-result handling coherently; resource controls add no identity-bearing fields.

---

<a id="admission"></a>
## 11. Validated creation, canonical authoring, minimization and export

### Purpose

Make normal document creation safe while retaining low-level structural calculation. Distinguish a new canonical authoring result from existing exact content and from an alternative rendering of that content.

### 11.1 Admission

**LANG-ADMIT.** An admitted result must establish the exact graph, all declared type definitions and the selected definition/value goal. Missing required type content is incomplete. Fixed-value contradictions, invalid evidence, malformed types and explicitly weaker schemas are rejected before canonical cleanup. A failed admission must not be presented as successful publication.

`ADMIT_SOURCE` parses/preprocesses/constructs, performs strict admission, removes only the canonical duplicates permitted below and rechecks when removal occurs. `ADMIT_EXACT` validates existing content without running Source compilation or authoring normalization. `ADMIT_CANONICAL` decodes its declared wire codec, then admits the resulting exact node without migrating its identity.

```python
def admit_document(text, context, *, goal="value", mode="source", format="json"):
    """Construct or decode, validate, normalize permitted duplicates, and export.

    The context is an operation-local fixed environment. No persistent provider
    write occurs here. Authentication or reuse of this result is a host boundary.
    """
    try:
        with B.error_scope(context, "", "operation"):
            context.diagnostic_goal = goal
            exact = read_input(text, context, mode=mode, format=format)
            context.diagnostic_root = exact
            original_id = B.identity(exact)
            B.strict_certify(exact, context, goal)
            if mode == "source":
                exact, removed = B.omit_root_duplicates(exact, context)
            else:
                removed = ()
            if removed:
                B.strict_certify(exact, context, goal)
            exact_text = B.export_exact(exact, context)
            compact_text = B.canonical_export(exact, context)
            records = B.admitted_records(exact, context)
            return AdmissionResult(
                B.identity(exact), original_id, goal, exact_text, compact_text,
                tuple(removed),
                json.dumps(records, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False),
            )
    except RecursionError as error:
        raise B.Failure("OperationLimitExceeded", "recursion") from error
```

The composition returns semantic content, role and associated artifacts. SDK capability tickets, storage installation and receipt authentication are not part of this abstract procedure.

### 11.2 Whole-root duplicate normalization

**LANG-ROOT-DUPLICATE.** For a newly authored materialized Source root with its own type, compare each explicitly supplied ordinary child with the complete exact child supplied by that type. Omit the edge only when the exact child IDs match, after the authored specialization has passed validation. Require semantic-view preservation. Do not remove labels, rewrite own type, reduce a partly inherited child to a delta, normalize exact schemas as semantic sets, recursively migrate independently addressed children or rewrite an existing root reference.

If T fixes exact Integer 42 at `amount`, new Source roots with and without the repeated `amount: 42` create the same canonical node. A named or differently typed 42 is not that exact duplicate. Text PLN and Currency PLN remain distinct under Holder because neither complete value is an exact duplicate of the inherited payload-free declaration.

This rule applies at the creation root, not every nested node. Creating a child independently as a new Source root is a separately selected authoring operation. Existing Exact, Direct and Compact inputs retain their existing exact identities. The created result should retain the original structural ID and removed paths as out-of-band transformation facts; they are not fields of the node.

This is a limited normalization contract, not a theorem that all logically equivalent Source programs have one identity. General minimization is not substituted for it.

### 11.3 Exact and compact exports

**LANG-EXPORT.** Export the identified exact content, not its helper or effective view. Type slots contain exact references and newly established definitions remain available as dependencies. Preserve numeric category on reload: an integer-looking binary64 wire payload uses a decimal marker where the exact codec requires it; helper bytes do not acquire that marker. Verify the exported representation reloads to the same exact ID.

Different permitted child materializations may yield different wire bytes with the same identity. Serialization-inspection choices are not canonical authoring choices. A provider returning an exact export must label it as exact content, not Source.

**LANG-COMPACT-PREFIX.** Compact canonical wire may encode an unchanged nonempty inherited **append-only** list prefix as its first item `{$previous:{blueId:P}}`. P identifies the payload-only prefix. Decode the verified sequence and concatenate the suffix; the marker is not an element. A bare reference in an ordinary element position remains a nested node. Metadata-bearing outer List identity is not a payload-prefix identity.

The reference exporter selects this compression only for an established append-only policy and the complete inherited base at that path, with identical prefix element IDs. It emits ordinary full item sequences for positional lists and for append-only lists without a nonempty prefix. `$previousItems` is Source-only and is never emitted as a canonical prefix control. The compact decoder rejects that shorthand and positional prefix anchors, verifies the payload-only prefix and its equality to the selected inherited base, then validates the resulting exact content. It does not choose a random provider list or an arbitrary longest prefix. This codec tightens prefix acceptance without changing the exact list fold.

Literal exact elements with top-level control-looking fields are escaped as ordinary exact references with supplied bodies. Noninitial or mixed compact controls fail. The codec is explicitly selected; exact-body failure must not trigger guessed compact decoding.

**LANG-DEPENDENCIES.** A result promising reusable serialization must retain or return bodies for newly introduced references and required cyclic proofs. Returning an ID does not publish its dependencies automatically. A reference known only to a temporary calculation context is not a self-contained public round trip. Existing dependencies may remain externally supplied under the documented provider contract.

### 11.4 Minimization

**LANG-MINIMIZE.** Return valid Source that re-resolves to the same required effective observations as the certified input. Exact Source identity may change. A bare effective view cannot uniquely recover an original exact input; retain the certified exact origin required by the operation. Different valid renderings are permitted; no globally shortest serialization is required.

The reference strategy constructs a lossless Source representation, proposes finite smaller reductions in a fixed order, re-prepares and certifies each candidate, and accepts only candidates passing `same_view`. Each accepted reduction decreases size. Append-only output retains a valid initial assertion: a bound `$previous` for a selected nonempty prefix, or `$previousItems: false` for a zero-element base. Positional output uses a complete indexed presentation or a valid pure edit form. Reductions cannot erase a required assertion, introduce mixed modes or replay an append-only complete payload as a suffix. Nested candidates retain their applicable collection context. Newly introduced replacement values must remain available across the output boundary.

`same_view` compares types, kinds, labels, policy, collection requirements, constraints, scalar payloads, presence, fields, items and `contracts`. It does not compare only business-value displays or require equal origin IDs. A caller cannot ignore missing evidence encountered in establishing a purported equivalent result.

### 11.5 Reusable validation evidence

**LANG-VALIDATION-EVIDENCE.** Previously established validation may be reused only for the same exact content, selected rules, validation goal, applicable requirements and adequate coverage. A caller's unchecked `valid: true` assertion is not such evidence. A definition proof cannot certify a completed value; a standalone proof cannot establish new contextual requirements. Evidence reuse changes work, not canonicalization or the resulting ID.

The abstract obligation is independent of authentication mechanism. HMAC records, in-process issued handles, storage atomicity and trusted issuer configuration belong to the separately documented SDK/host contract. A library may expose raw storage for untrusted content, but that operation must not imply semantic admission.

**Algorithms:** A04 for exact export; A11 for minimization; A13 for strict certification, root duplicates and compact wire; `OPERATIONS` for storage-independent composition.

---

<a id="cycles"></a>
## 12. Cyclic identities and owning-set proofs

### Purpose

Ordinary child-first identity cannot assign mutually dependent new node IDs. A cyclic-set operation establishes one master and a stable member mapping for an explicitly bounded symbolic set. This does not make cyclic inheritance valid.

### 12.1 Symbolic input

**LANG-CYCLE-INPUT.** Supply a finite nonempty strongly connected set with explicit local edges `this#i`. A one-member self-loop is permitted. No member root is a pure reference. Local indices must be in range. Local-edge text is allowed only by this symbolic operation; literal strings that merely contain it are not graph edges. Caller-supplied ZERO sentinels fail.

Keep every path containing a local edge visible through symbolic normalization, including inline type definitions. External children use ordinary exact identity. Do not hash away a local dependency before the masking and relabeling steps.

### 12.2 Preliminary order

**LANG-CYCLE-ORDER.** Temporarily map each local edge to the private 44-character ASCII-zero token for preliminary calculation. Sort by preliminary identity text, then by canonical root-commitment bytes whose child contributions are their exact identities. If both keys tie for distinct members, reject ambiguity. Do not use input order, file name, visible expansion depth or allocation identity as a tie-breaker.

The zero token is not a plain BlueId. Its temporary contribution behavior is confined to this algorithm. The commitment projection makes external exact expansion independent of the ordering key. It is not the canonical JSON of arbitrarily expanded member bodies.

### 12.3 Master and member identities

**LANG-CYCLE-FINALIZE.** Return to the original symbolic members, arrange them in canonical order and relabel local targets to canonical indices. Identify that ordered payload-only list with local `this#j` strings as the scoped temporary contributions. Its ordinary list identity is MASTER. Original member i receives `MASTER#canonicalIndex(i)`.

Final materialization replaces symbolic edges with the final member IDs. Retain the complete symbolic proof needed for verification. No local token or ZERO sentinel may escape as a finalized ordinary reference.

### 12.4 Verification

**LANG-CYCLE-PROOF.** A member proof contains the complete symbolic member set in canonical order. Re-finalize it, require the expected master and canonical member mapping, check the index range and derive the selected final body. An optional separately supplied body must be a materialization and have the same ordinary body commitment as that derivation. A repeated member reference is not body proof.

The ordinary identity of a detached member body generally differs from its `MASTER#index`. The comparison authenticates two materializations of the derived body; it does not substitute the detached-body identity for the member ID. The proof establishes the set's exact addressing, not semantic validity of every external dependency. Strict admission performs additional type/content checks as required.

This protocol does not infer hidden symbolic boundaries, discover arbitrary compressed proofs or solve graph isomorphism for indistinguishable members. Those are not implicit capabilities of Language 1.0.

**Algorithms:** A10, with normalization and helper functions A03. **Errors:** invalid set shape/edges, ambiguous ordering, invalid proof or missing required evidence. **Worked result:** the single node `name: Loop; self: {blueId: this#0}` has master `7Ydx3cm8uySLmzNyTcbpM5fufGaLSKnEs9cUcMMxRkeC`.

---

<a id="diagnostics"></a>
## 13. Diagnostics and safe operation boundaries

### Purpose

Report what failed, where it failed and which established facts explain it. Diagnostic metadata is not Blue content and must not require speculative resolution or alter the operation's outcome.

### 13.1 Semantic result categories

**LANG-DIAGNOSTIC-FACTS.** Preserve a machine-readable category, the failing logical path when established, the selected operation/validation goal and known expected/actual facts. Incomplete evidence/limits remain distinct from invalid content. Do not invent a constraint origin, payload or type name that the failing comparison did not establish. Do not fetch additional data merely to make an error message prettier.

The reference error record includes `category`, `detail`, `path`, `phase`, `goal`, `expected`, `actual`, and optional document/declaration identity context. Another carrier may encode equivalent facts. Human wording, colors, preview lengths and stack traces are not part of semantic conformance.

| Example | Required useful facts |
|---|---|
| Inherited Text PLN supplied as USD | `/currency`, expected Text PLN, received Text USD, fixed-value category |
| Integer field supplied as Text | `/bar`, exact expected Integer identity and actual Text identity |
| Payload-free Currency admitted as a value | Root path `""`, value goal, missing Text payload |
| Explicit interval weakening | Authored endpoint/facet and inherited endpoint it violates |
| Missing referenced type | Required identity and incomplete/unavailable outcome, not successful node ID |

**LANG-DIAGNOSTIC-NAMES.** Label an exact core type with its canonical registry name. A custom type merely named Integer remains custom; its full ID must remain available. Human names are display context, never evidence for a subtype decision. Preserve the distinction between the root pointer `""`, empty-named child `/` and escaped member paths.

### 13.2 Validation intent

**LANG-EXPLICIT-GOAL.** An interface may offer an explicit action to validate as a definition after a missing-value error. It MUST NOT silently change the requested goal, insert a fabricated payload or publish after a failed value admission. A displayed success must state the goal actually established.

A declaration without a payload is not necessarily illegal. `name: Currency; type: Text` is valid as a definition but does not satisfy completed Text-value admission. This is an invalid value request, not an unavailable-evidence result. The correct explanation is the operation mismatch, not a suggestion that primitive types cannot be specialized.

### 13.3 Security and implementation boundary

**LANG-FAIL-CLOSED.** Neither a supplied address, a transport success nor a locally available cache entry establishes semantic validity. No invalid or incomplete result may carry a successful admitted-document claim. Keep receipt/storage metadata outside content and preserve the selected input role across APIs and persistence.

A host decides transport, keys, persistence and external trust. The Language decides the exact identities and semantic checks. SDK-specific proof authentication must implement the abstract evidence obligations of §11; it cannot redefine them. The Language defines no network-fetched executable code or ambient authority discovery.

**Algorithms:** A01 records/scopes and error sites throughout the annex. The annex retains the reference renderer as explicitly marked support; another implementation need not reproduce its English sentences.

---

<a id="conformance"></a>
## 14. Conformance and operation equivalence

### 14.1 Required behavior

**LANG-CONFORMANCE.** A full implementation MUST implement all defined input roles, scalar codecs, core registry identities, normalization, Source preparation, exact identity, type and schema semantics, list construction, graph operations, definition and completed-value admission, selected observations, minimization, export, and cyclic proof verification. It MUST implement `specification` as metadata rather than an ordinary field.

The standard package model is defined in the same Language release. A tool claiming package-processing conformance MUST also implement §18. A Language-only tool need not perform package acquisition or execute additional protocols.

The normative algorithms and standard definitions are included in this document. Conformance data accompanying a release is evidence for these rules, not an alternative source of semantics. An implementation MUST NOT select behavior from a test identifier or substitute an expected result for executing the stated operation.

### 14.2 Required cross-operation relationships

**LANG-CROSS-OPERATION.** Under the same interpretation context and adequate evidence, the following relationships MUST hold:

| Operations | Required relationship |
|---|---|
| Expand and collapse | Preserve exact root and selected child identities. |
| Inline and referenced access | Establish the same selected semantic observations. |
| Selected and complete resolution | Agree on observations established by both. |
| Source creation followed by Exact loading | Execute construction once; do not replay append operations. |
| Exact and compact-canonical loading | Recover the same exact node and BlueId. |
| Specialization | Preserve all applicable inherited guarantees. |
| Minimization and subsequent resolution | Preserve the defined effective view; a minimized Source identity need not equal the input identity. |
| Cyclic finalization and member verification | Agree on master identity, canonical member indices, and derived bodies. |
| Failed admission and publication | Do not issue a successful admitted-document claim or install a partial publication as admitted. |
| Alias renaming | Preserve exact results when the replacement names bind the same identities. |
| Package relocation | Preserve its semantic identity independently of the retrieval location. |

### 14.3 Host independence

**LANG-PORTABILITY.** An independent implementation MUST follow the arithmetic, Unicode, key ordering, input-role, evidence, and comparison rules defined here. It MUST NOT use locale, pointer identity, nondeterministic traversal, or cache state to select a content identity or semantic result. Mathematical Integer and finite binary64 are distinct categories. A native adapter MUST preserve those categories or reject an ambiguous input.

Native adapters MUST reject unsupported host values such as nonfinite numbers, undefined or sparse elements, functions, symbols, non-string map keys, and pointer cycles in an ordinary builder graph. Such pointer cycles are not symbolic cyclic-set input. A different data representation MAY be used only if it preserves the declared operation contract.

### 14.4 Outcomes and comparison

Conformance observations distinguish **Established**, **Absent**, **Incomplete**, and **Invalid**. Expected absence requires evidence sufficient to establish absence at the selected location. Missing content and exhausted physical work budgets are not absence. Structural identity alone is not an admission certificate.

Identity strings and canonical bytes compare exactly. Ordered sequences compare by length, order, and element values. Scalar comparisons retain their prescribed categories. Effective views are compared as specified by `same_view` in Appendix D, not by discarding type and constraint information. Minimization is checked by its semantic round trip; a different permitted Source spelling is not itself a failure.

Portable fixture requests and their comparison rules are specified in Appendix E. Tests for package roles and public admission additionally exercise the stronger admission guarantees, rather than confusing structural fixture `identify` with completed-value admission.

### 14.5 Incomplete implementation and resources

A missing implemented feature is not permission to approximate a successful result. A processor MUST expose unsupported behavior or incomplete work without issuing an invalidity or success assertion that was not established. Host resource limits, parser protection, transport bounds, and diagnostic preview sizes MUST NOT become universal structural restrictions on Blue content.

A conforming invocation either returns a result established by the selected rules or reports why it did not establish one. Finite tests, independent test vectors, and repeatability checks provide evidence; a count of passing tests is not proof for every possible document.

---

<a id="worked-examples"></a>
## 15. Worked examples — informative

These examples illustrate the named rules. All identifiers are complete values. Core aliases are the bindings in Appendix B; any custom alias is introduced explicitly below. Reproducing a displayed address checks that calculation, not the correctness of every Language operation.

### 15.1 One scalar and one parent

Source:

```yaml
x: 1
```

Integer 1 uses this raw helper, with no newline:

```json
{"type":{"blueId":"E2LM6qgzWG9ttagq2xTmiZkgYEAgkYedFCmU9v7NnVEq"},"value":1}
```

Its SHA-256 is `e936d1ae0ff11c0d83ace6f49770f7efcc729825bcab83405b62a025c458c749`; its BlueId is `GhNUbi6oXA1HArr2uTqwpcgegPv8kxUuj11riBtoMJXz`.

The parent helper is:

```json
{"x":{"blueId":"GhNUbi6oXA1HArr2uTqwpcgegPv8kxUuj11riBtoMJXz"}}
```

Its SHA-256 is `e3804019b55df5a3bc7bc552785a6fd4d61aa6d926a29621f6d00d522222c517`; the document BlueId is `GK4yR8GtLdg9y97uEPUAbepLF3M8qXsbgXRt7Kb3yQAr`.

Replacing the child with that exact reference leaves the parent helper unchanged. The reference alone does not certify its unseen target; admission establishes the additional evidence required by its goal.

### 15.2 Two exact scalar classes, one effective domain

Admit this definition:

```yaml
name: Currency
type: Text
```

Its ID is `A6bEQcVduDsMYqrecotcG1NPMXeYf8PncRbqe3CFTUXN`.

Admit Holder with the exact Currency reference:

```yaml
name: Holder
currency:
  type:
    blueId: A6bEQcVduDsMYqrecotcG1NPMXeYf8PncRbqe3CFTUXN
```

Holder identifies as `3WZswxQosL5XB2akb3qLKjgiz2jL1ZvBJWsfVMx2xHTA`. Establish these scalar bodies in the provider for reference variants:

| Scalar | Exact BlueId |
|---|---|
| Text PLN | `6UPPMcrAfJFYCHyS1gxf5MasLBqQ7qqWkwp6bqucmnXm` |
| Currency PLN | `GTS7MAC6UEn97shNfD3j88ybsNNzaMgyCJVEBLMwF7Uf` |

Every following input is a **complete Holder instance Source**, not a detached currency child.

**A — bare Text:**

```yaml
type:
  blueId: 3WZswxQosL5XB2akb3qLKjgiz2jL1ZvBJWsfVMx2xHTA
currency: PLN
```

**B — explicit core Text:**

```yaml
type:
  blueId: 3WZswxQosL5XB2akb3qLKjgiz2jL1ZvBJWsfVMx2xHTA
currency:
  type: Text
  value: PLN
```

**C — reference to Text PLN:**

```yaml
type:
  blueId: 3WZswxQosL5XB2akb3qLKjgiz2jL1ZvBJWsfVMx2xHTA
currency:
  blueId: 6UPPMcrAfJFYCHyS1gxf5MasLBqQ7qqWkwp6bqucmnXm
```

**D — reference to Currency PLN:**

```yaml
type:
  blueId: 3WZswxQosL5XB2akb3qLKjgiz2jL1ZvBJWsfVMx2xHTA
currency:
  blueId: GTS7MAC6UEn97shNfD3j88ybsNNzaMgyCJVEBLMwF7Uf
```

**E — explicit Currency PLN:**

```yaml
type:
  blueId: 3WZswxQosL5XB2akb3qLKjgiz2jL1ZvBJWsfVMx2xHTA
currency:
  type:
    blueId: A6bEQcVduDsMYqrecotcG1NPMXeYf8PncRbqe3CFTUXN
  value: PLN
```

A, B and C identify as `844qf3Ye22h84i9vMm5Jpg8t5M6UFBBo5AaBhbsCawMq`. D and E identify as `3vZvAB5unPV5z3vp1wTXCz461tNjBJGErasewFhARM7F`. Their effective Currency payload can agree while the supplied own scalar types remain different.

### 15.3 Exactly redundant inherited content

Define:

```yaml
name: Example
amount: 42
currency: PLN
```

The type ID is `2EgiMQBQBKBUVtsgEbzwwgtjbZnA34u86jWNCKd3Nc1D`.

```yaml
# Newly authored Source with a repeated exact child
type:
  blueId: 2EgiMQBQBKBUVtsgEbzwwgtjbZnA34u86jWNCKd3Nc1D
x: 1
amount: 42
```

```yaml
# Newly authored Source without the repeated child
type:
  blueId: 2EgiMQBQBKBUVtsgEbzwwgtjbZnA34u86jWNCKd3Nc1D
x: 1
```

Validated Source creation returns the shorter canonical root for both, with ID `JUhfQvQwZgS3bqRRYbpyvahHBAdrbhUvL116W2BgZXW`. The longer existing exact graph retains its raw ID `4XcwPnGoUZDxkS2WS8uuAJt37JdCQToPNWPixeVmW4za`; exact loading does not migrate it. Neither instance inherits the type root's name Example.

Changing the supplied currency to USD is rejected before normalization, because the type fixes PLN. An error can therefore report `/currency`, expected Text PLN and received Text USD rather than a bare scalar-conflict label.

### 15.4 Append-only Source and canonical prefix wire

The type supplied in `examples/append-only-type.yaml` is named Tutorial/Append-Only Pair, contains typed append-only entries `[A,B]`, and identifies as `9ExKbrHq1ZMpFiEESUPLpfoRegzkReCV9164BuUJoDEh`. Admit and publish that definition before the following Source:

```yaml
name: Append-only C example
type:
  blueId: 9ExKbrHq1ZMpFiEESUPLpfoRegzkReCV9164BuUJoDEh
entries:
  type: List
  items:
    - $previousItems: true
    - C
```

The contextual declaration selects append-only construction and the Boolean asserts that its prefix is nonempty. The base definition's own authored item sequence starts with `$previousItems: false`; the assertions do not change the published type or result IDs. Its full exact entries are `[A,B,C]`. Compact canonical wire is:

```yaml
entries:
  items:
    - $previous:
        blueId: 49W45qY1LKK66NNRDF8k3W75zd8mj48Fh9wBs31ZNceB
    - type:
        blueId: GX7CFUmSDrE2MzptunLCCdZwnuwwrenRQqEnHL4x3uoC
      value: C
  type:
    blueId: 85ip88snCGrgUNdi1rUFqqAxcxwVGKV2g4LjsKoyKmXK
name: Append-only C example
type:
  blueId: 9ExKbrHq1ZMpFiEESUPLpfoRegzkReCV9164BuUJoDEh
```

The prefix ID identifies payload-only `[A,B]`. Full exact, decoded compact, original Source and published-root reload identify the resulting document as `EDEm6BiWq1YTaCHUSbxtSakf3Ebi7Tar1TLuHArkhru6`. Compact and exact formats use their declared decoders. The result has three elements, not a nested prefix plus C.

### 15.5 Constraint tightening and a definition without payload

A definition of an Integer range 5–10 may be specialized by an explicitly supplied range 6–9. It may not be specialized by 4–11, even though intersecting both would yield 5–10. Validate the authored specialization before considering any cleanup.

A list definition with no `items` and `minItems: 2` leaves a future obligation. The same definition with `items: []` supplies a concrete violating payload. This is why a definition goal is not interchangeable with value admission or with filling missing payloads automatically.

### 15.6 One cyclic member

Symbolic set with one member:

```yaml
name: Loop
self:
  blueId: this#0
```

Its master is `7Ydx3cm8uySLmzNyTcbpM5fufGaLSKnEs9cUcMMxRkeC`; its member is that master followed by `#0`. The complete proof retains the symbolic set in canonical order. A detached body containing its finalized self-reference does not independently hash to that member string.

### 15.6 Positional presentation and pure edits

Given a published type whose field `x` is positional `[N, HOLE, R]`, a descendant can write:

```yaml
x:
  - N
  - $empty: true
  - R
  - another element
```

This is a presentation at indices 0–3, not four append instructions. The hole may instead be filled with any value satisfying its other requirements. N and R may be repeated or compatibly refined, not contradicted. No `$replace` is required. To modify only the inherited hole, a separate pure edit form is:

```yaml
x:
  - $pos: 1
    $replace: filled value
```

Mixing these forms, or putting an edit after ordinary entries, is invalid. A pure edit cannot target a new out-of-bounds fifth position; use the full positional form to extend the list.

---

<a id="authoring-bindings"></a>
## 16. Authoring bindings and exact content availability

### 16.1 Local names

An authoring environment may supply a finite map from names to final BlueIds. A name is local syntax, not a type identity. Automatic substitution applies only at the type positions specified in §9. Ordinary text, `name`, and `description` are not rewritten because their values resemble an alias.

A package mount assigns a prefix to selected exports. Mounting package X does not mount the aliases used by X's author or by X's dependency packages. To use dependency Y by name, the consumer MUST establish its own binding, for example `xyz/Order`. Definitions already published by X retain their exact references to Y, regardless of the consumer's bindings.

**LANG-BINDING-SCOPE.** Binding addition MUST reject a name that is already bound to a different identity, without partially changing the environment. Repeating the same name-to-identity binding is permitted. Core aliases MUST NOT be rebound to different identities. Removing a mount removes its names and contributed provider layer; it does not revoke or delete separately retained immutable content.

A mount prefix is a local name, not an instruction to execute code or fetch a URL. Prefix syntax for the package model is defined in §18. Independent applications may use different prefixes for identical definitions and obtain identical exact results.

### 16.2 Finalized cyclic-member aliases

Alias targets may be plain final BlueIds or finalized cyclic-member IDs. A symbolic `this#i` is not a final alias target. Access to a finalized member requires its owning-set proof when the selected operation needs the member's body. A loader MUST preserve the member identity and MUST NOT replace it with the ordinary hash of the detached body.

### 16.3 Supporting content without additional names

A content environment may contain definitions that have no authoring alias. A self-contained package may supply the exact definitions required by its exports without exposing the names of every supporting definition. Availability, naming, and execution support remain separate.

Every supplied definition has the same identity, specialization, schema, collection-context, and admission rules as a definition supplied individually. Package membership creates neither an additional type kind nor an exemption from validation. Missing required content remains incomplete.

### 16.4 Reuse of established results

Within an operation, verified immutable exact content and completed semantic obligations may be reused under keys that include the exact input, selected rules, recipe, goal, and root context. Active plans and unfinished obligations MUST NOT be cached as successful results.

Reusing content across environments is permitted only under the evidence conditions of §5. Reusing a semantic result requires the same relevant interpretation. An ordinary-value cycle can establish structural presence as defined by the algorithms; a cycle of type edges cannot manufacture a concrete value.

---

<a id="specification-metadata"></a>
## 17. Specification metadata

### 17.1 Meaning and shape

`specification` is an OPTIONAL reserved metadata field alongside `name` and `description`. It identifies normative semantic context associated with the exact node. Unlike the two literal labels, its value is a node reference.

In Source, the field accepts an explicit reference or an inline node. An inline target is prepared in its own context, retained as exact content, and replaced by its reference. Bare text is not a specification reference. To supply normative text inline, use an explicit Text node. Exact input may materialize the target; Direct input requires its pure reference. Symbolic local references are permitted only within the cyclic-set procedures in §12.

```yaml
name: Example declaration
description: A reusable declaration.
specification:
  type: Text
  value: The additional rules governing this declaration.
```

This example defines the shape of the metadata; it does not establish a particular processor protocol. A plain field named `spec` is ordinary content and has no reserved metadata meaning.

### 17.2 Identity and payload structure

**LANG-SPECIFICATION-IDENTITY.** The target's exact identity contributes to the containing node's identity as specified by the ordinary child-reference helper. Changing the target changes that contribution. An exact reference and a verified materialization of its target are interchangeable for identity.

The metadata is permitted on object, scalar, list, and payload-free nodes. It does not create an object payload, establish value presence, or count toward ordinary field constraints. It is excluded from the ordinary business-field collection of an effective view. Resolution does not expand or merge the target's contents into the containing node.

### 17.3 Inheritance and refinement

**LANG-SPECIFICATION-INHERITANCE.** A type's root specification is not copied into an instance as the instance's own metadata or as an ordinary field. Its association remains available through the exact type relation. A subtype may declare its own specification without deleting the base type's association.

For a type A associated with SA, a subtype B associated with SB, and an instance x whose type is B and which has no own specification:

| Observation | Result |
|---|---|
| x's own specification | Absent |
| B's own specification | SB |
| A's own specification | SA |
| Declared associations along x's type chain | SB followed by SA |

A specification association does not override the underlying type's content guarantees. If a concrete inherited child already has fixed metadata, an explicit refinement cannot substitute conflicting metadata. The comparison is atomic: it is not a recursive merge of two normative documents.

### 17.4 Observations and required evidence

`query` of `/specification` or a root `specification` observation reports the node's own reference or Absent. Traversal below that metadata explicitly requests the referenced content. The processor must obtain the necessary verified evidence to answer such a traversal.

Structural identity can use a final reference without its body. Strict admission verifies reachable content, declared types, and the specification target in the definition role. A missing target is incomplete evidence; a body with a mismatching identity is invalid evidence. A reference to reusable normative structure is not required to satisfy every completed business-value obligation merely because it appears as metadata.

**LANG-SPECIFICATION-ROLE.** Definition-valid target content is not proof that the target is a complete protocol descriptor, that its prose is consistent, or that a processor implements it. Those conclusions require their own role-specific checks.

### 17.5 Discovery through a type chain

The following procedure defines the direct type-chain association observation. It does not recursively activate every specification in an arbitrary content graph and does not resolve semantic prerequisites beyond that chain.

```python
"""Read governing metadata along a selected type chain; not a support assertion.
Does not activate protocols, execute code, or scan unrelated provider records.
"""
from algorithms import blue as B

def declared_requirements(node, context):
    result=[]; seen=set(); current=node
    while current is not None:
        identity=B.identity(current)
        B.require(identity not in seen, 'TypeCycle', identity)
        seen.add(identity)
        body=B.open_exact(current,context)
        link=body.get(B.SPECIFICATION)
        if link is not B.ABSENT:
            B.require(isinstance(link,B.Ref), 'InvalidNodeShape', 'specification position')
            result.append({'definedOn':identity,'specification':link.id})
        parent=body.get('type')
        current=parent if isinstance(parent,B.Ref) and parent.id not in B.CORE_NAME else None
    return tuple(result)
```

The result identifies both the definition declaring the association and the target specification identity. Identical target specifications on different declaring types may appear more than once. Type cycles remain invalid according to §6.

### 17.6 Normative rules versus informative documentation

A governing specification establishes additional semantic obligations. A guide explains use without introducing such obligations. A package may contain guides, examples, and specialized programs without defining a new protocol.

A program fully expressed using existing primitives need not declare a new native protocol merely because it is published independently. Its existing type and primitive associations remain applicable in their defined roles. Conversely, an unrecognized executable declaration does not become interpretable merely by omitting specification metadata.

---

<a id="packages"></a>
## 18. Standard packages and protocol descriptors

### 18.1 Package model

A **package** is an immutable Blue document that identifies a selected collection of exports, exact imports, specifications, and documentation. A **source repository** is an authoring workspace; it is not itself the package identity. A **bundle** is an explicit selection of package mounts. A **registry** is a retrieval or discovery service.

Package and Protocol Specification are ordinary standard definitions. Their complete Source definitions are included in Appendix C. Their identities are calculated using ordinary admission and identity operations. No core primitive, reserved `Package` keyword, or alternative hash function is introduced by those definitions.

A package processor applies the role checks in this section in addition to Language checks. Package roots are admitted in the definition role because their graphs contain reusable definitions. The package-role checks then establish complete package structure, export validity, and supplied evidence. A tool MUST NOT reinterpret failed value admission as successful package admission without selecting the package role explicitly.

### 18.2 Semantic root and witness

This edition uses the package model identifier `blue-package-model/2-specification-metadata`. The identifier is an exact format label, not a compatibility range. The root has the following fields. A semantic witness is the complete authoring-shaped record used to reproduce and verify the exact root; null optional witness slots are omitted by normal Source preparation.

| Field | Required meaning |
|---|---|
| `type` | Exact reference to the ordinary Package definition in Appendix C. |
| `format` | The exact package model identifier above. |
| `name` | The package's identifying literal name. It is not a globally unique authority or a registry locator. |
| `version` | A human-facing release label. It does not perform dependency resolution or establish compatibility. |
| `identityProfile` | The exact supported Language algorithm profile selected before admission. For this edition: `blue-language/2026-09-26-specification-metadata-1`. |
| `bootstrapLanguage` | Boolean indicating a bootstrap Language release. |
| `language` | Reference to the exact selected bootstrap Language package, or null in the bootstrap witness. |
| `exports` | Map from local export names to exact definition references. |
| `imports` | Map from explicit local prefixes to exact imported package references. |
| `protocol` | Reference to this package's governing protocol descriptor, or null when it defines no new protocol. |
| `specBindings` | Verified associations from exported type identities to native specification references and the selected descriptor. |
| `declaredRequirements` | List of exact protocol-descriptor references required by the package's declared use. |
| `documentation` | Map from safe logical paths to identified Text assets and their byte descriptors. |

Semantic witness keys are exactly those listed. Additional distribution metadata belongs outside the semantic root. The exact Blue document is the normal admitted result of this record, not its raw JSON byte hash.

The release-label grammar is `major.minor.patch`, with nonnegative decimal components having no leading zeros except zero itself, and an optional hyphen followed by dot-separated alphanumeric/hyphen prerelease identifiers. Numeric prerelease identifiers have no redundant leading zeros. The label is descriptive; comparisons of labels MUST NOT substitute one identity for another.

### 18.3 Language bootstrap

A bootstrap Language package has `bootstrapLanguage: true`, no `language` reference, no imports, and no protocol descriptor. Its rule selection comes from the implementation establishing that bootstrap context. It may export ordinary standard definitions and carry this complete specification as documentation.

A non-bootstrap package has `bootstrapLanguage: false`, an exact Language reference, and an explicit direct import of that same Language package. Every semantically interpreted imported package must have the same Language selection. An imported bootstrap must be that exact selected package. These checks also apply to transitive dependencies and previously visited dependencies; a foreign bootstrap cannot bypass the check by being reached through another branch.

This is the supported interpretation of this edition, not an assertion that every possible later Language edition must have identical representation or algorithms. §19 defines the versioning boundary.

The bootstrap Package and Protocol Specification nodes need not point back to their containing Language package. Their standard role is established by the selected Language. Publishing them does not impose a package-to-type-to-package cycle.

### 18.4 Exports and scoped imports

An export name is a nonempty string associated with one final BlueId. Exported targets MUST be available as verifiable exact definitions, including required cyclic proofs. There is no automatic historical-to-current identity substitution.

An import binds one exact package to an explicit prefix within the importing author's source environment. For this package model a prefix matches:

```text
@?[A-Za-z0-9][A-Za-z0-9_.-]*(/[A-Za-z0-9][A-Za-z0-9_.-]*)*
```

For example, `orders`, `company/workflows`, and `@repo.blue` are permitted. A consumer constructs a local name by appending `/` and a selected export name. The resulting binding is a normal Language alias, subject to collision checks and the reserved core bindings.

**LANG-PACKAGE-SCOPE.** Importing X does not introduce the aliases that X used for its imports. If X refers to Y1, mounting Y2 directly does not retarget that reference. A consumer may mount multiple exact package versions under distinct prefixes. Such coexistence does not establish that their types are interchangeable or that all associated protocols can be combined.

Package import graphs MUST be acyclic in this model. Cyclic definitions within packages use §12; they are not cyclic package imports. Multiple paths to the same exact package are permitted and MUST be verified consistently. Retrieval locations, package version labels, and mount order do not select a different target.

### 18.5 Supporting exact content

Supporting records provide the exact definitions and evidence required to establish exports and identified package content. They do not automatically add aliases, authorize actions, or install processor code. A selected package can therefore make an unnamed referenced Order definition available without mounting any `Orders/Order` alias.

A self-contained package supplies the required exact content and owning-set proofs. A partial content delivery MAY be retained as partial evidence, but MUST NOT be represented as a successfully verified self-contained package. A receiver MUST distinguish a missing body from a known absent field.

A package's own exported definitions and supplied supporting definitions retain their exact identities independently of which package distributes them. A package that re-exports a definition MUST NOT modify its description or metadata while asserting that the original identity is preserved.

### 18.6 Protocol Specification role

A protocol descriptor uses the ordinary Protocol Specification type. Its required fields are `type`, `name`, `language`, `rules`, `requires`, and `status`. Its optional fields are `effectiveRules` and `schedulingPolicy`. This is a descriptor schema, not an instruction to execute new behavior.

| Field | Meaning |
|---|---|
| `type` | Exact reference to the Protocol Specification definition in Appendix C. |
| `name` | Literal protocol name; not a dispatch or authority key. |
| `language` | The same selected Language reference as the package context. |
| `rules` | Exact reference to accessible Text containing the governing normative material. |
| `requires` | Map from local requirement labels to exact protocol-descriptor references. Labels are local explanatory names. |
| `status` | Publisher's Text classification of the descriptor. It is not certification or a trust grant. |
| `effectiveRules` | Optional exact Text reference to an explicitly identified complete statement or supplement. |
| `schedulingPolicy` | Optional exact Text reference to an explicitly selected policy. The field's existence does not make scheduling a Language operation. |

A descriptor is admitted in the definition role, then checked for its complete descriptor structure. Its referenced rule documents MUST be established as Text. All protocol prerequisites use the same Language selection. The prerequisite graph MUST be acyclic. A descriptor cannot authorize an arbitrary replacement of its required protocol by a later release.

Where supplementary rule documents are supplied, the protocol's normative content must define how they apply. The field names do not provide a generic override or precedence mechanism. A contradictory or incomplete prose contract is not repaired by a matching package hash.

A package may define no new protocol. Specialized programs, clauses, schemas, or forms expressed through existing semantics may use informative documentation alone. An empty export set is permitted for an explicitly declared protocol package; the package need not invent operator types solely to distribute a specification.

### 18.7 Native specification associations

In this package profile, a protocol package associates each of its own exports with its governing rules using native `specification` metadata. Its `specBindings` map is keyed by each exported definition identity and contains:

```json
{
  "specification": {"blueId": "RULES_ID"},
  "protocol": {"blueId": "DESCRIPTOR_ID"},
  "binding": "native-metadata"
}
```

The symbolic strings in this example stand for valid final identities. `RULES_ID` MUST equal the descriptor's `rules` target. The definition's own exact `specification` MUST contain that reference. `DESCRIPTOR_ID` MUST equal the package's selected protocol. Bindings cover exactly the package's exports when it has a protocol; otherwise the binding map is empty.

Imported definitions retain their own associations in their imported package witnesses. A package does not acquire a new native implementation merely by copying these records. A bootstrap Language package is governed by its selected Language role rather than by a self-referential protocol descriptor.

Changing the native rules reference changes the containing definition's identity. Adding a guide to the package without changing that reference does not change the definition. A package descriptor MUST NOT assign conflicting native semantics to an unchanged type through uncommitted explanatory metadata.

### 18.8 Declared requirements

`declaredRequirements` is separate from `imports`. A library may import a protocol's data definitions without declaring that every consumer performs that protocol's task. A publisher selects direct imported protocol requirements explicitly; it may include the selected package's own protocol. Transitive prerequisites are followed through exact descriptor references.

The package-level requirement list is an inventory for the declared use. It is not a proof of document-specific support, structural validity, or authorization. A processor still applies the relevant checks to actual content in the roles defined by its protocols. Omitting an execution requirement does not enable an unknown executable primitive.

### 18.9 Documentation and package identity

Every included asset in this package profile is valid UTF-8 Text. A documentation entry contains exactly `content`, `sha256`, and `size`:

```json
{
  "content": {"blueId": "TEXT_DOCUMENT_ID"},
  "sha256": "sha256:HEX_DIGEST_OF_UTF8_BYTES",
  "size": 123
}
```

The Text value is encoded as UTF-8 to establish the byte digest and byte count. The package processor verifies the Text identity, byte descriptor, and delivered file contents. A source publisher in this profile uses LF line endings and no UTF-8 BOM; it must not silently normalize an already identified Text value.

A logical path is relative, nonempty, uses `/` separators, and cannot address a parent, root, drive, or external location. Archive consumers also reject unsafe paths, duplicates, symbolic links, and file-type tricks before installation. Host-specific byte and extraction limits are operational safeguards, not alternative Language identity rules.

The package BlueId commits to its exact semantic root and referenced definitions, imports, and documentation. It does not commit to registry hostname, cache path, archive compression, CI run, credential, or source-checkout path unless such text is deliberately included as declared content. The root's own computed identity is not inserted into that root before hashing.

### 18.10 Verification procedure

**LANG-PACKAGE-VERIFY.** A package processor claiming a verified package MUST:

1. Establish the supported Language/profile and the expected package identity, when one is supplied, before semantic interpretation.
2. Parse the carrier without duplicate keys or unsafe file entries; verify its declared byte inventory.
3. Admit the exact package root in the definition role and require its recomputed BlueId to equal the requested package identity.
4. Verify each semantic package witness as the same ordinary admitted content it describes. Enforce the root field set, format, version shape, bootstrap rules, imports, and Language consistency.
5. Traverse package imports and protocol prerequisites with cycle detection. Revisited nodes do not bypass context checks.
6. Establish every selected rule document and the native specification associations.
7. Admit every export as a definition, preserving owning-set evidence for cyclic members.
8. Establish every documentation target as Text and verify its byte descriptor and, for files supplied by this artifact, exact file bytes.
9. Verify all supplied records and their agreement between indexes, package evidence, and exported-content evidence. Do not certify extra unrelated witnesses as part of the root's identified closure.
10. Return a verified package result only after those checks succeed. A partial or failed operation does not install a successful mount.

This procedure does not certify that a protocol's requirements are implemented or that an author is trusted. Expected identity must be selected through the caller's own trusted context. Matching a checksum shipped beside an untrusted archive alone does not establish that it is the artifact the caller intended to obtain.

### 18.11 Reference archive profile

The implemented archive profile is identified by the literal string `blue-package/0.3-local`. This historical format label identifies the byte carrier; it is not an instruction to use an earlier interpretation or a publication-status assertion. An equivalent implementation may use another transport while preserving the package-role requirements.

The ZIP contains four structural files plus the identified Text assets:

| File | Role |
|---|---|
| `package.blue.json` | Exact normalized package-root document. |
| `package-records.json` | Exact provider records and owning-set evidence for the root's required content. |
| `repository.json` | Explicit exported alias map and backing definition records. |
| `package.json` | Distribution manifest containing file inventory, semantic witnesses, and provenance. |

The distribution manifest records `packageBlueId`, `languageProfile`, `language`, `protocol`, exports, exact import pins, semantic package/specification witnesses, file byte descriptors, and validation information. These claims MUST agree with the identified root and verified records. Producer source hashes and URLs are provenance, not alternative semantic identities or proof of conformance.

The repository carrier has `format`, `name`, `aliases`, `records`, `metadata`, and `identity`. Its format is `blue-python-repository/1`. Its `identity` is a SHA-256 checksum of the canonical envelope without that identity field, not a BlueId. The profile's precise envelope serialization and verification procedures are included in Appendix F. The same data can be consumed by implementations in languages other than Python.

The semantic witness for an imported package is not a source program to be reparsed under a different registry. Reconstructing and admitting its declared root must produce its existing package BlueId. A registry's readable tag is only a lookup hint. Normal verification never upgrades an import, edits a lock, or rewrites an exported type.

---

<a id="edition-boundaries"></a>
## 19. Edition selection and cyclic identity boundaries

### 19.1 Scope of an edition

A Language edition fixes the node model, input interpretation, registry, exact-identity procedures, type and schema semantics, and operation evidence rules. A document or package is interpreted under an established edition, not under the most recently available package with a matching name.

The exact Language release is selected out of band before semantic processing. An envelope may identify a package and the required profile; the interpreter must verify those claims under a supported selection. Nested references do not select alternate interpreters independently.

### 19.2 Compatibility

**LANG-EDITION-COMPATIBILITY.** This edition defines no general cross-edition conversion or semantic-import mechanism. Its package processor uses the exact Language selection required by §18. A release label, matching major version, equal-looking schema, or compatibility claim in untrusted package content does not relax that requirement.

A later Language specification may define compatibility with an earlier one. Such a specification must state the operations covered, the preserved identities and observations, and how earlier evidence is verified. No machine-readable compatibility vocabulary, automatic version solver, or generic permission to mix editions is defined here.

An implementation that merely stores or transfers a foreign artifact need not interpret it. Supporting two editions in separate contexts does not itself establish semantic composition between them. A processor that cannot establish the required interpretation reports unsupported processing; it does not recalculate old references under another edition or treat unavailable interpretation as a malformed original document.

### 19.3 Cyclic sets

**LANG-CYCLE-EDITION.** A symbolic set, its preliminary ordering, master identity, canonical member mapping, final materializations, and owning-set proof MUST be constructed and verified under one selected Language interpretation. The algorithm cannot switch editions between members or between finalization and verification.

External references in that set must be interpretable under the same established context. A foreign member body is not evidence of a current-edition member identity. A resolver MUST NOT hash an older detached body using a newer procedure and treat the result as verification of its former `MASTER#index` address.

A specification that permits cross-edition composition must define the behavior of complete owning sets, external references, canonical ordering, and proof verification. Compatibility of acyclic scalar values alone is insufficient to establish that behavior. This edition grants no implicit compatibility for those cases.

### 19.4 Publication boundaries are not cyclic-identity boundaries

Ordinary package imports and protocol prerequisite graphs are acyclic in this package model. A package may nevertheless contain definitions whose ordinary content references form finalized cyclic sets. These are different graphs and different checks.

A cyclic member may be exported under several names or distributed in several artifacts. Its owning set and proof do not change merely because its publication location changes. An artifact claiming self-contained use must retain the required proof. The package or filename is not a substitute for that proof.

### 19.5 Revision and identity preservation

A package-only documentation change may change the package BlueId while retaining unchanged type and specification identities. A change to exact type content changes the type identity. A changed governing-specification reference also changes any exact node that carries it. A dependency mount does not migrate previously published content.

A processor MUST retain the edition and scope of validation evidence. A new Language selection does not retroactively validate old admission receipts, even when an exact node happens to retain the same BlueId. Migration is an explicitly established new operation, not a display conversion or a consequence of loading another package.

---

<a id="processors"></a>
## 20. Protocol interpretation and document processors

### 20.1 Additional interpretations

A **document processor** interprets Blue content to perform a defined task under a selected Language and applicable protocol specifications. A task may evaluate expressions, execute workflows, coordinate histories, render a form, evaluate a query, run a simulation, or verify a proof. No universal event-processing method or effect model is imposed by Language.

A **protocol specification** identifies the additional rules and their exact prerequisites. It may govern several kinds of nodes and the relationships between them. It is not necessarily a predicate applied independently to each node.

The standard Protocol Specification type and descriptor role are defined in §18. A Language implementation may store or inspect such content without implementing the protocol itself.

### 20.2 Support claims

**LANG-PROCESSOR-SUPPORT.** A processor claiming to perform a protocol task MUST implement the exact required rules and the applicable prerequisites for that task. Availability of specification text, a matching package name, or a successfully verified type is not evidence of implementation support.

Support declarations identify exact specifications and, where necessary, supported combinations and roles. A tool MUST NOT claim complete support while silently ignoring an applicable required interpretation. It MAY expose unsupported content as data without claiming the unsupported result.

A provider or user-supplied package cannot install trusted runtime bindings by declaring that it is compatible. A support decision is made by the installed implementation and the selected context. This specification does not define a standard HTTP capability endpoint or an executable plugin installation protocol.

### 20.3 Applicability

The selected protocol determines the roles and boundaries at which additional meaning applies. A processor MUST account for the relevant definitions, their inherited requirements, and declared semantic prerequisites in those roles. It MUST NOT globally activate all specifications mentioned in every mounted package, example, or supporting record.

Package imports provide names and content. Declared protocol requirements provide semantic prerequisites. Neither alone proves that a particular document is valid or that a business operation is authorized. A document-specific support check is distinct from a package-level requirement inventory.

Introducing a new required executable or managed structure requires support checking before that structure is interpreted or activated. A prior check of a different exact state is not evidence about arbitrary future content.

### 20.4 Structural extension boundary

This edition reserves `contracts` as a structural attachment that may accompany scalar, list, or object payloads. Language parses, identifies, and refines it; Language does not execute it. An application protocol may assign interpretation to that content in a defined task.

Other application names remain ordinary fields unless listed as reserved in this Language edition. A package cannot add a Language-reserved word, change payload classification, or change identity contribution by placing a declaration in its documentation. A different structural attachment mechanism requires a Language specification that defines it.

### 20.5 Examples of independent protocol roles — informative

A rendering protocol can define a Form and Text Field, with their types identifying the rendering rules. An application package can specialize Text Field with a fixed label without creating a new rendering protocol. A generic Language reader can inspect the resulting form; a rendering processor is required to produce the specified interaction.

A query protocol can define filters, projections, and their evaluation rules. A library of queries using those primitives supplies programs rather than a new evaluator. A scientific-transformation package can likewise supply computations, units, or input constraints through an existing expression protocol.

A workflow protocol can define step order and effects. A coordination protocol can add source evidence, authority, and history rules. A package of commercial workflows may use those rules without requiring an implementation for every exported commercial type. A newly defined native scheduling rule, however, is additional behavior that an implementation must support explicitly.

### 20.6 Authority and consistency

A protocol dependency does not authorize redefinition of the required protocol. Two incompatible rules cannot be combined merely by importing both packages. The selected task must have an explicitly defined, coherent interpretation; import order is not a conflict-resolution procedure.

No Language operation proves arbitrary prose specifications mutually consistent. It establishes exact content and the checks within its defined role. Conformance, domain validation, authenticity, and authorization remain distinct claims.


<a id="notation"></a>
## Appendix A. Algorithm notation and primitive operations

The code in Appendix D is normative executable notation. `Node` is an immutable set of uniquely named exact contributions; `Ref` is a final content reference; `Local` is a temporary cyclic-set edge. `ABSENT` is a distinguished sentinel, not JSON null. Lists and tuples are ordered. Maps have unique string keys. Sets are used for membership and logical conjunction; their physical iteration order does not establish a different portable content result.

`int` denotes an arbitrary-precision mathematical integer, distinct from Boolean. `Fraction` denotes an exact reduced rational with positive denominator. `float` denotes a finite IEEE 754 binary64 value where admitted. `struct` bit conversions use the indicated fixed byte order. `Decimal` is used only to construct or inspect exact decimal candidates as specified; it does not authorize rounding where exact rational comparison is required. Integer division, remainder, greatest common divisor, bit shifts, and bit length have their usual exact mathematical meanings.

Strings are sequences of Unicode scalar values. Strict UTF-8 decoding rejects malformed encodings and unpaired surrogate content. `key_order` encodes UTF-16 code units solely to determine the required object-key order. JSON `\\u` escapes decode to scalar values; decoded keys, not their source spelling, determine duplicates. Required JSON escapes are quotation mark, reverse solidus, and control characters U+0000–U+001F; the canonical encoder uses the specified short escapes and lowercase four-digit hexadecimal escapes for the remaining controls.

Input JSON uses objects, arrays, strings, decimal number tokens, `true`, `false`, and `null`. Object names are strings. Insignificant whitespace consists of space, tab, carriage return, and line feed. There is exactly one root value and no trailing non-whitespace. A number uses the complete grammar in §3.1. The decoder must preserve number-token spelling until the Blue scalar codec selects its category. Comments, trailing commas, hexadecimal numbers, NaN, and Infinity are not JSON tokens.

Portable YAML is a presentation of the same mappings, sequences, and scalars. Its indentation, flow collections, quoted strings, block folding, and chomping produce a syntax tree; the Blue scalar resolver in §3 is applied rather than a schema-dependent native YAML resolver. Anchors, aliases, tags, directives, implicit timestamps, merge keys, and multiple documents are excluded. The reference parser in Appendix D rejects those constructs before node normalization. Parser implementation choice does not authorize accepting additional Blue scalar types.

`hashlib.sha256` denotes SHA-256 of exactly the supplied byte string, producing 32 digest bytes; it is not a generic selectable hash. Padding is a one bit, zeros to leave 64 bits in the final 512-bit block, and the original bit length in big-endian form. The 64 rounds use 32-bit words, addition modulo 2^32, the SHA-256 choice/majority functions, and its fixed initial values and constants. Blue then applies its independently specified base58 encoding, not hex encoding or a multihash wrapper.

`copy` operations preserve values; object identity is not content. `lru_cache` and context memoization are optimizations whose reuse must obey §§5 and 16. `dataclass` and `typing` describe records, not additional wire fields. Exceptions carry the defined semantic outcomes; an equivalent implementation may use tagged return values.

The only non-Blue syntax composition supplied by a library in the executable notation is the permitted JSON/YAML parser. All Blue-specific scalar resolution, canonical formatting, identity, structural validation, schema processing, graph access, and cyclic-set decisions are included below. A host's default serializer or numeric coercion is not a replacement for these procedures.

### A.1 SHA-256 compression definition

The eight initial words, written in hexadecimal, are:

```text
6a09e667 bb67ae85 3c6ef372 a54ff53a
510e527f 9b05688c 1f83d9ab 5be0cd19
```

The sixty-four round constants are:

```text
428a2f98 71374491 b5c0fbcf e9b5dba5 3956c25b 59f111f1 923f82a4 ab1c5ed5
d807aa98 12835b01 243185be 550c7dc3 72be5d74 80deb1fe 9bdc06a7 c19bf174
e49b69c1 efbe4786 0fc19dc6 240ca1cc 2de92c6f 4a7484aa 5cb0a9dc 76f988da
983e5152 a831c66d b00327c8 bf597fc7 c6e00bf3 d5a79147 06ca6351 14292967
27b70a85 2e1b2138 4d2c6dfc 53380d13 650a7354 766a0abb 81c2c92e 92722c85
a2bfe8a1 a81a664b c24b8b70 c76c51a3 d192e819 d6990624 f40e3585 106aa070
19a4c116 1e376c08 2748774c 34b0bcb5 391c0cb3 4ed8aa4a 5b9cca4f 682e6ff3
748f82ee 78a5636f 84c87814 8cc70208 90befffa a4506ceb bef9a3f7 c67178f2
```

For each padded block, let W[0..15] be its big-endian 32-bit words. For t from 16 to 63:

```text
small0(x) = ROTR(x,7) XOR ROTR(x,18) XOR (x >> 3)
small1(x) = ROTR(x,17) XOR ROTR(x,19) XOR (x >> 10)
W[t] = small1(W[t-2]) + W[t-7] + small0(W[t-15]) + W[t-16]
```

Initialize a..h from the current eight hash words. Each round t performs:

```text
big0(x) = ROTR(x,2) XOR ROTR(x,13) XOR ROTR(x,22)
big1(x) = ROTR(x,6) XOR ROTR(x,11) XOR ROTR(x,25)
Ch(x,y,z) = (x AND y) XOR ((NOT x) AND z)
Maj(x,y,z) = (x AND y) XOR (x AND z) XOR (y AND z)
T1 = h + big1(e) + Ch(e,f,g) + K[t] + W[t]
T2 = big0(a) + Maj(a,b,c)
(h,g,f,e,d,c,b,a) = (g,f,e,d+T1,c,b,a,T1+T2)
```

All additions and complements are 32-bit. Add the final a..h to the current hash words modulo 2^32. Concatenate the final words in big-endian order to obtain the digest. For the empty byte string, its hexadecimal rendering is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

<a id="registry"></a>
## Appendix B. Exact registry and preprocessing selectors

### B.1 Core definitions

The following six definitions and addresses are fixed by this edition. The JSON bodies are exact content. Changing their labels changes their content; a similarly named custom type is not a core type.

#### Text

BlueId: `GX7CFUmSDrE2MzptunLCCdZwnuwwrenRQqEnHL4x3uoC`

```json
{
  "name": "Text",
  "description": "Core Blue Language 1.0 primitive scalar representing Unicode text. Text values are exact Unicode code-point sequences after parsing. Blue Language performs no Unicode normalization, case folding, locale-sensitive collation, whitespace normalization, or line-ending normalization by default. String schema constraints minLength and maxLength count Unicode code points. The empty string is valid unless restricted by schema. Applicable schema constraints are minLength, maxLength, and enum."
}
```

#### Integer

BlueId: `E2LM6qgzWG9ttagq2xTmiZkgYEAgkYedFCmU9v7NnVEq`

```json
{
  "name": "Integer",
  "description": "Core Blue Language 1.0 primitive scalar for exact mathematical integer values. Integer values are arbitrary precision in the language model. Unquoted integer tokens are portable only in the safe JSON numeric integer range [-9007199254740991, 9007199254740991]. Integer values outside that range are represented as quoted canonical decimal text with explicit or inherited effective Integer type. The canonical decimal text form uses an optional leading minus sign followed by decimal digits, with no leading zeros except the single digit zero. Applicable schema constraints are minimum, maximum, exclusiveMinimum, exclusiveMaximum, multipleOf, and enum."
}
```

#### Double

BlueId: `9eWaHYz2vKrFofdHTHAizNNu8xP6QE3WQ5y7DGrGZvyJ`

```json
{
  "name": "Double",
  "description": "Core Blue Language 1.0 primitive scalar for finite IEEE 754 binary64 floating-point values. NaN, positive Infinity, and negative Infinity are invalid Blue values. Double parsing uses round-to-nearest, ties-to-even binary64 semantics; numeric tokens that overflow to Infinity or parse as NaN are invalid. Source numeric tokens with a decimal point or exponent infer Double when no explicit type is provided, even when their mathematical value is integral. Negative zero and positive zero compare as the same numeric value and canonicalize as JSON number zero, while the effective Double type remains part of canonical BlueId input. Applicable schema constraints are minimum, maximum, exclusiveMinimum, exclusiveMaximum, multipleOf, and enum."
}
```

#### Boolean

BlueId: `AwvXD961fmnmqcSQhjMA7r15HpVh39cefb6ZTyUz2Fm2`

```json
{
  "name": "Boolean",
  "description": "Core Blue Language 1.0 primitive scalar with exactly two values: true and false. Blue Language defines no truthiness conversion for Boolean values. Only the literal parsed boolean values true and false are Boolean values. Applicable schema constraint is enum."
}
```

#### List

BlueId: `85ip88snCGrgUNdi1rUFqqAxcxwVGKV2g4LjsKoyKmXK`

```json
{
  "name": "List",
  "description": "Core Blue Language 1.0 ordered collection type. Surface array form and wrapped items form are equivalent authoring forms. Order and multiplicity are preserved. List BlueId calculation uses a domain-separated streaming fold over element BlueIds. itemType is optional; if omitted and no effective itemType is inherited, elements are not constrained by itemType. If mergePolicy is omitted and no effective mergePolicy is inherited, resolvers assume positional. append-only forbids changes to the inherited prefix. positional allows $pos overlays within the inherited prefix. $previous, $pos, $replace, and $empty are recognized only at the top level of items when the node's effective type is List. Source list null elements normalize to $empty: true and are not deleted. Empty object and empty list elements are ordinary content and remain distinct from that placeholder. Applicable schema constraints are minItems, maxItems, and uniqueItems."
}
```

#### Dictionary

BlueId: `5WQ4tVb4gUUdZa7EfaiUa2XKQwgAurvfYY3ALPauxcAF`

```json
{
  "name": "Dictionary",
  "description": "Core Blue Language 1.0 object-map collection type. A Dictionary is encoded as a Blue object node whose ordinary child fields represent direct keys when those keys do not collide with reserved language fields. Direct object encoding cannot represent data keys named name, description, type, itemType, keyType, valueType, value, items, blueId, blue, schema, mergePolicy, contracts, properties, or constraints. Direct object encoding cannot represent reserved language keys as data keys. Applications needing arbitrary keys use an escaped entry representation such as a list of { key, val } entries. keyType is optional; if omitted and no effective keyType is inherited, keys default to Text for direct object encoding. For direct object encoding, keyType must resolve to a scalar key type with a canonical textual form, such as Text, Integer, Double, or Boolean. valueType is optional; if omitted and no effective valueType is inherited, values may be any Blue node. A Dictionary with zero direct keys is the exact present empty object `{}`; it is distinct from an absent field. Applicable schema constraints are minFields and maxFields."
}
```

### B.2 Preprocessing selectors

The following selectors invoke exactly the behaviors in §9 and algorithm group A08. A label is not a selector. All alias selectors in a listed set are the exact explicitly supported selectors, not a version range.

**`INFER_IDS`**

```json
[
  "49hrWpkoXavNmK8PpZag11zB2vYwzhQZahwioz6vDk2i",
  "FGYuTXwaoSKfZmpTysLTLsb8WzSqf43384rKZDkXhxD4"
]
```

**`ALIAS_IDS`**

```json
[
  "27B7fuxQCS1VAptiCPc2RMkKoutP5qxkh3uDxZ7dr6Eo",
  "53yFLQ3dpuGwa2svHubDyzyhYz9RQNmctiJRdi3gRYr7"
]
```

**`RENAME_ID`**

```json
"7kEewGH6vogsgUXw3Gdyi73rtb5oQK1L8LWtHbYcG7pB"
```

**`APPEND_TEXT_ID`**

```json
"D2DxVxaddbJT5k2YYj3sG35cSdotw1Mz9GpxrdP43nzN"
```

**`SET_SOURCE_FIELD_ID`**

```json
"3uVsScHAE36fm2Knz3P6tWY94nuEA7cVDWxci8bY2zGg"
```

The exact Source-field-assignment transformation definition is:

```json
{
  "name": "Blue Language Set Root Source Field Transformation",
  "description": "Deterministic preprocessing transformation. Configuration fields are field (Text), expression (Text containing exactly one JSON or portable Blue YAML Source expression), and optional format (Text json or yaml, default json). All configuration and expression syntax is validated before any transformation runs. The Source root must be an object. The parsed expression defensively replaces the named direct root field before baseline preprocessing. The target blue is forbidden and the expression must not contain a blue directive. Type aliases and primitive inference in the assigned expression are processed by the document baseline afterward. Name and description are optional identity metadata. No other configuration fields are accepted."
}
```

<a id="standard-definitions"></a>
## Appendix C. Ordinary standard definitions

These are Source definitions under the six core aliases in Appendix B. Admission in the definition role produces the stated exact identities. The package and protocol-role constraints in §18 are additional to the ordinary, intentionally open structural declarations below.

### C.1 Package

BlueId: `BtkqqUJi6NmqaxFNHUeRyFrLVRZAgKTui3VanimT2B7M`

```json
{
  "name": "Package",
  "description": "The ordinary standard Blue package type. Its root is admitted in definition role because exports identify reusable definitions. Package-role verification validates the complete manifest and every export separately; there is no special package hashing or resolver branch.",
  "format": {
    "type": "Text"
  },
  "version": {
    "type": "Text"
  },
  "identityProfile": {
    "type": "Text"
  },
  "bootstrapLanguage": {
    "type": "Boolean"
  },
  "exports": {
    "type": "Dictionary"
  },
  "imports": {
    "type": "Dictionary"
  },
  "declaredRequirements": {
    "type": "List"
  },
  "documentation": {
    "type": "Dictionary"
  }
}
```

### C.2 ProtocolSpecification

BlueId: `G3rso4aSK92VAYcgHFj76tgN92YV6CgSQ5DFVDy67PM1`

```json
{
  "name": "Protocol Specification",
  "description": "Ordinary standard description of exact normative rules and their prerequisites. Its nativeSpecification may name an existing runtime rules Text; rules may also include the complete selected publication and a separately bound scheduling policy. Loading content does not install a processor.",
  "status": {
    "type": "Text"
  },
  "requires": {
    "type": "Dictionary"
  }
}
```

<a id="algorithms"></a>
## Appendix D. Complete normative algorithms

### D.1 Algorithm groups

The following module contains every Blue-specific helper used by the normative procedures. `A01` through `A13` identify its internal algorithm groups. The names are notation, not required public SDK methods. The standard-library meanings are fixed by Appendix A.

- A01: Values, failures and constants
- A02: Parsing, token preservation and rational arithmetic
- A03: Canonical bytes, hashes and exact normalization
- A04: Lossless export and verified graph access
- A05: Constraint records, exact predicates and monotone schema refinement
- A06: Declaration recipes, type ancestry and effective head resolution
- A07: Exact refinement and Language list specialization
- A08: Preprocessing with fixed, content-addressed transform selection
- A09: Source compilation and exact canonicalization
- A10: Symbolic cyclic identity and complete owning-set proofs
- A11: Semantic equivalence and minimization
- A12: Portable observations, demand outcomes and entry points
- A13: Strict admission, root duplicate normalization and prefix wire

### D.2 Content algorithms

```python
"""Executable algorithms of Blue Language Specification 1.0.
The Markdown specification embeds this file without a separate translation.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import re
import struct
from decimal import Decimal
from dataclasses import dataclass, field, replace
from fractions import Fraction
from functools import lru_cache
from typing import Any
from contextlib import contextmanager

# === A01: Values, failures and constants ===
CORE = {
    'Text': 'GX7CFUmSDrE2MzptunLCCdZwnuwwrenRQqEnHL4x3uoC',
    'Integer': 'E2LM6qgzWG9ttagq2xTmiZkgYEAgkYedFCmU9v7NnVEq',
    'Double': '9eWaHYz2vKrFofdHTHAizNNu8xP6QE3WQ5y7DGrGZvyJ',
    'Boolean': 'AwvXD961fmnmqcSQhjMA7r15HpVh39cefb6ZTyUz2Fm2',
    'List': '85ip88snCGrgUNdi1rUFqqAxcxwVGKV2g4LjsKoyKmXK',
    'Dictionary': '5WQ4tVb4gUUdZa7EfaiUa2XKQwgAurvfYY3ALPauxcAF',
}
CORE_NAME = {v:k for k,v in CORE.items()}
TYPES = frozenset(('type','itemType','keyType','valueType'))
LABELS = frozenset(('name','description'))
# specification is a reference-valued, non-inherited metadata slot.
# It is not a literal label, a type-position alias, or an ordinary field.
SPECIFICATION = 'specification'
REFERENCE_METADATA = frozenset((SPECIFICATION,))
METADATA = LABELS | REFERENCE_METADATA
LITERALS = LABELS | {'value'}
HEADERS = TYPES | METADATA | {'schema','mergePolicy','contracts'}
RESERVED = HEADERS | {'value','items','blueId','blue','properties','constraints'}
CONTROLS = frozenset(('$pos','$replace','$previous','$previousItems'))
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
SAFE = 9007199254740991
ZERO = '0' * 44
NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z', re.ASCII)
INTEGER_TEXT = re.compile(r'(?:0|-[1-9][0-9]*|[1-9][0-9]*)\Z', re.ASCII)
INDEX = re.compile(r'(?:0|[1-9][0-9]*)\Z', re.ASCII)
ABSENT = object()

class Failure(Exception):
    """A semantic failure with non-identity-bearing, portable diagnostic data.

    None means an unestablished location; the empty pointer means the root.
    The legacy category/detail remain stable for programmatic comparisons.
    """
    def __init__(self, category, detail='', path=None, *, expected=None, actual=None,
                 keyword=None, phase=None, goal=None, hint=None):
        self.category, self.detail, self.path = category, detail, path
        self.expected, self.actual = expected, actual
        self.keyword, self.phase, self.goal = keyword, phase, goal
        self.hint = hint
        self.document_type = None
        self.node_name = None
        super().__init__(category + (': '+detail if detail else ''))

    @property
    def message(self):
        return failure_message(self)

    def __str__(self):
        return self.category + ': ' + self.message

    def as_dict(self):
        result = {'category':self.category, 'detail':self.detail,
                  'path':self.path, 'message':self.message}
        for key,value in (('expected',self.expected),('actual',self.actual),
                          ('keyword',self.keyword),('phase',self.phase),
                          ('goal',self.goal),('hint',self.hint),
                          ('documentType',self.document_type),('nodeName',self.node_name)):
            if value is not None: result[key]=copy.deepcopy(value)
        return result


def require(test, category, detail='', **diagnostic):
    if not test: raise Failure(category, detail, **diagnostic)


def diagnostic_type(tid, c=None):
    """Display exact identities; never fetch merely to improve an error message."""
    if tid is None: return None
    if tid in CORE_NAME:
        return {'blueId':tid, 'name':CORE_NAME[tid], 'core':True}
    result={'blueId':tid, 'core':False}
    n=c.bodies.get(tid) if c is not None else None
    if isinstance(n,Node) and n.has('name'):
        # c.bodies contains independently established exact content only.
        result['name']=diagnostic_literal(n.get('name'))
    return result


def diagnostic_literal(value):
    """Bound output size without altering a validation input or Blue content."""
    if value is ABSENT: return None
    if isinstance(value,NumberToken): return {'numberToken':value.text[:256]}
    if isinstance(value,Ref): return {'blueId':value.id}
    if isinstance(value,Node): return {'blueId':identity(value),'kind':value.kind()}
    if isinstance(value,Fraction):
        return {'numerator':integer_text(value.numerator),'denominator':integer_text(value.denominator)}
    if type(value) is int and abs(value)>SAFE: return {'integer':integer_text(value)}
    if isinstance(value,str) and len(value)>256:
        return {'preview':value[:256], 'truncated':True, 'length':len(value)}
    if type(value) in (str,bool,int,float) or value is None: return value
    if isinstance(value,(tuple,list)):
        return {'length':len(value),'preview':[diagnostic_literal(x) for x in value[:8]]}
    return {'kind':type(value).__name__}


def diagnostic_value(value=ABSENT, tid=None, c=None, kind=None):
    result={'present':value is not ABSENT}
    if tid is not None: result['type']=diagnostic_type(tid,c)
    if kind is not None: result['kind']=kind
    if value is not ABSENT: result['value']=diagnostic_literal(value)
    return result


def diagnostic_type_name(value):
    if not isinstance(value,dict): return 'a compatible type'
    if value.get('core'): return value['name']
    name=value.get('name')
    if isinstance(name,str): return name + ' (custom type ' + value['blueId'] + ')'
    return 'type ' + value.get('blueId','<unknown>')


def diagnostic_display(value):
    if isinstance(value,dict) and 'numerator' in value and 'denominator' in value:
        return value['numerator'] if value['denominator']=='1' else value['numerator']+'/'+value['denominator']
    if isinstance(value,dict) and 'integer' in value: return value['integer']
    if isinstance(value,dict) and 'numberToken' in value: return value['numberToken']
    if isinstance(value,dict) and 'preview' in value and value.get('truncated'):
        return json.dumps(value['preview'],ensure_ascii=False)+' [truncated]'
    return json.dumps(value,ensure_ascii=False,separators=(',',':'))


def failure_message(error):
    where = ('the document root' if error.path=='' else error.path or 'the requested node')
    expected=error.expected or {}; actual=error.actual or {}
    et=diagnostic_type_name(expected.get('type'))
    at=diagnostic_type_name(actual.get('type'))
    if error.category=='FixedValueConflict' and 'value' in expected and 'value' in actual:
        msg='The value at '+where+' is fixed to '+diagnostic_display(expected['value'])
        if expected.get('type'): msg+=' ('+et+')'
        msg+='; received '+diagnostic_display(actual['value'])
        if actual.get('type'): msg+=' ('+at+')'
        return msg+'. An inherited fixed value cannot be changed.'
    if error.category=='TypeCompatibilityViolation' and expected.get('type') and actual.get('type'):
        msg='Expected '+et+' at '+where+'; received '+at
        if 'value' in actual: msg+=' ('+diagnostic_display(actual['value'])+')'
        return msg+'.'
    if error.category=='SchemaViolation' and error.detail in ('scalar payload required','list payload required','payload required'):
        label=et if expected.get('type') else expected.get('kind','payload')
        return 'A '+label+' value is required at '+where+', but no payload was supplied.'
    if error.category=='SchemaWeakening':
        msg='The schema at '+where+' weakens the inherited '+(error.keyword or error.detail)+' requirement'
        if 'value' in expected and 'value' in actual:
            msg+=' (inherited '+diagnostic_display(expected['value'])+', supplied '+diagnostic_display(actual['value'])+')'
        return msg+'. A subtype may only retain or tighten it.'
    if error.category=='SchemaViolation' and error.keyword:
        msg='The value at '+where+' violates '+error.keyword
        if 'value' in actual: msg+=' (received '+diagnostic_display(actual['value'])+')'
        if 'value' in expected: msg+='; required '+diagnostic_display(expected['value'])
        return msg+'.'
    if error.category=='ProviderUnavailable':
        return 'Required content is unavailable at '+where+': '+error.detail+'. Validation is incomplete; the document was not admitted.'
    if error.category=='ProviderBlueIdMismatch':
        return 'Content supplied for '+error.detail+' could not be verified at '+where+'. It cannot be used as trusted content.'
    # Core names are used for display only; retained detail and exact IDs are not edited.
    detail=error.detail
    for tid,name in CORE_NAME.items(): detail=detail.replace(tid,name)
    return (detail or error.category)+' at '+where+'.'


@contextmanager
def error_scope(c, path=None, phase=None):
    old_path,old_phase=c.diagnostic_path,c.diagnostic_phase
    if path is not None: c.diagnostic_path=path
    if phase is not None: c.diagnostic_phase=phase
    try:
        yield
    except Failure as error:
        if error.path is None: error.path=c.diagnostic_path
        if error.phase is None: error.phase=c.diagnostic_phase
        if error.goal is None: error.goal=c.diagnostic_goal
        root=c.diagnostic_root
        if isinstance(root,Node):
            t=root.get('type')
            if error.document_type is None and isinstance(t,Ref):
                error.document_type=diagnostic_type(t.id,c)
            if error.node_name is None and root.has('name'):
                error.node_name=diagnostic_literal(root.get('name'))
        if error.hint is None and error.goal=='value' and error.category=='SchemaViolation' and error.detail in ('scalar payload required','list payload required','payload required'):
            error.hint='Supply a payload for a completed value. To declare a type without a payload, explicitly validate as Definition instead.'
        raise
    finally:
        c.diagnostic_path,c.diagnostic_phase=old_path,old_phase

@dataclass(frozen=True)
class NumberToken:
    text: str
    @property
    def decimal(self): return any(c in self.text for c in '.eE')

@dataclass(frozen=True)
class Ref:
    id: str
    # A body is installed only by successful verification, never by public input.
    body: Any = field(default=None, compare=False, repr=False)

@dataclass(frozen=True)
class Local:
    index: int

@dataclass(frozen=True)
class Node:
    fields: tuple
    def get(self,k,default=ABSENT): return dict(self.fields).get(k,default)
    def has(self,k): return k in dict(self.fields)
    def keys(self): return tuple(k for k,_ in self.fields)
    def ordinary(self): return tuple(k for k,_ in self.fields if k not in RESERVED)
    def kind(self):
        if self.has('value'): return 'scalar'
        if self.has('items'): return 'list'
        if self.ordinary() or not self.fields: return 'object'
        return 'none'

def key_order(s): return s.encode('utf-16-be','strict')
def ordered(xs): return sorted(xs, key=key_order)
def node(m): return Node(tuple((k,m[k]) for k in ordered(m)))
def changed(n, /, **updates):
    m=dict(n.fields)
    for k,v in updates.items():
        if v is ABSENT: m.pop(k,None)
        else: m[k]=v
    return node(m)
def obj_fields(n): return {k:n.get(k) for k in n.ordinary()}
def scalar(t,v): return node({'type':Ref(CORE.get(t,t)), 'value':v})
def list_node(xs): return node({'items':tuple(xs)})
def pointer(path,k): return path+'/'+str(k).replace('~','~0').replace('/','~1')

@dataclass
class Limits:
    # Optional host controls: exceeding one establishes incomplete work only.
    text_bytes: int | None = None
    depth: int | None = None
    values: int | None = None
    numeric_chars: int | None = None
    decimal_scale: int | None = None
    steps: int | None = None
    fetches: int | None = None

    def __post_init__(self):
        for value in vars(self).values():
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError('host limits must be nonnegative integers or None')


def within(value, bound):
    return bound is None or value <= bound


def integer_text(value):
    return str(Decimal(value))


def parse_integer(text):
    return int(Decimal(text))

@dataclass
class Context:
    provider: dict = field(default_factory=dict)
    aliases: dict = field(default_factory=lambda:dict(CORE))
    directive_aliases: dict = field(default_factory=dict)
    limits: Limits = field(default_factory=Limits)
    bodies: dict = field(default_factory=dict)
    proofs: dict = field(default_factory=dict)
    demands: list = field(default_factory=list)
    plans: dict = field(default_factory=dict)
    presence_cache: dict = field(default_factory=dict)
    heads: dict = field(default_factory=dict)
    validation_cache: set = field(default_factory=set)
    plan_active: list = field(default_factory=list)
    operand_active: set = field(default_factory=set)
    operand_descriptions: dict = field(default_factory=dict)
    work: int = 0
    diagnostic_path: str = ''
    diagnostic_phase: str = 'operation'
    diagnostic_goal: str|None = None
    diagnostic_root: Any = None
    def step(self):
        self.work += 1
        require(within(self.work, self.limits.steps),'OperationLimitExceeded','steps')
    def remember(self,n):
        if isinstance(n,Node): self.bodies[identity(n)]=n
        return n

# === A02: Parsing, token preservation and rational arithmetic ===
def checked_unicode(s):
    require(isinstance(s,str),'InvalidSyntax','string expected')
    require(not any(0xD800 <= ord(c) <= 0xDFFF for c in s),'InvalidSyntax','unpaired surrogate')
    return s

def pairs_no_duplicates(pairs):
    m={}
    for k,v in pairs:
        checked_unicode(k)
        require(k not in m,'DuplicateKey',k)
        m[k]=v
    return m

def parse(text, fmt='json', limits=None):
    lim=limits or Limits()
    try:
        if isinstance(text,bytes): text=text.decode('utf-8','strict')
        require(isinstance(text,str),'InvalidSyntax','text expected')
        require(within(len(text.encode('utf-8','strict')), lim.text_bytes),'OperationLimitExceeded','text bytes')
        if fmt == 'json':
            def num(s):
                require(NUMBER.fullmatch(s) is not None,'InvalidSyntax','number')
                require(within(len(s),lim.numeric_chars),'OperationLimitExceeded','number token')
                return NumberToken(s)
            def bad(s): raise Failure('InvalidSyntax','non-JSON number '+s)
            x=json.loads(text,parse_int=num,parse_float=num,parse_constant=bad,object_pairs_hook=pairs_no_duplicates)
        elif fmt == 'yaml': x=parse_yaml(text)
        else: raise Failure('UnsupportedFormat',fmt)
        count=0
        pending=[('value',x,1)]
        while pending:
            task,v,d=pending.pop()
            if task=='key':checked_unicode(v);continue
            count+=1
            require(within(d,lim.depth) and within(count,lim.values),'OperationLimitExceeded','parse bounds')
            if isinstance(v,str):checked_unicode(v)
            elif isinstance(v,NumberToken):
                require(within(len(v.text),lim.numeric_chars),'OperationLimitExceeded','number token')
            elif isinstance(v,dict):
                for k,a in reversed(tuple(v.items())):
                    pending.append(('value',a,d+1));pending.append(('key',k,0))
            elif isinstance(v,list):pending.extend(('value',a,d+1) for a in reversed(v))
        require(x is not None,'InvalidRoot')
        return x
    except RecursionError as e:
        raise Failure('OperationLimitExceeded','parser recursion') from e
    except (UnicodeError,json.JSONDecodeError,ValueError) as e:
        if isinstance(e,Failure): raise
        raise Failure('InvalidSyntax',str(e)) from e

def plain_scalar(s):
    if s in ('','null'): return None
    if s == 'true': return True
    if s == 'false': return False
    if NUMBER.fullmatch(s): return NumberToken(s)
    return s

def parse_yaml(text):
    # Only YAML presentation/folding is delegated; scalar resolution is above.
    from vendor import yaml
    try:
        for t in yaml.scan(text,Loader=yaml.BaseLoader):
            require(not isinstance(t,(yaml.tokens.TagToken,yaml.tokens.AnchorToken,yaml.tokens.AliasToken,yaml.tokens.DirectiveToken)),
                    'InvalidSyntax','YAML tag, alias, anchor or directive')
        docs=list(yaml.compose_all(text,Loader=yaml.BaseLoader))
        require(len(docs)==1 and docs[0] is not None,'InvalidSyntax','one YAML document required')
        def convert(n):
            if isinstance(n,yaml.nodes.ScalarNode):
                return n.value if n.style is not None else plain_scalar(n.value)
            if isinstance(n,yaml.nodes.SequenceNode): return [convert(a) for a in n.value]
            require(isinstance(n,yaml.nodes.MappingNode),'InvalidSyntax','YAML node')
            pairs=[]
            for k,v in n.value:
                key=convert(k)
                require(isinstance(key,str) and not (key=='<<' and getattr(k,'style',None) is None),'InvalidSyntax','YAML key')
                pairs.append((key,convert(v)))
            return pairs_no_duplicates(pairs)
        return convert(docs[0])
    except yaml.YAMLError as e: raise Failure('InvalidSyntax',str(e)) from e

def decimal_rational(s,limits=None):
    lim=limits or Limits()
    require(isinstance(s,str) and NUMBER.fullmatch(s),'InvalidScalar','decimal syntax')
    require(within(len(s),lim.numeric_chars),'OperationLimitExceeded','number length')
    neg=s.startswith('-'); s=s[1:] if neg else s
    q=re.split('[eE]',s); mant=q[0]; exponent=parse_integer(q[1]) if len(q)==2 else 0
    p=mant.split('.'); digits=''.join(p); exponent-=len(p[1]) if len(p)==2 else 0
    require(within(abs(exponent),lim.decimal_scale),'OperationLimitExceeded','decimal scale')
    a=parse_integer(digits) * (-1 if neg else 1)
    return Fraction(a*10**exponent,1) if exponent>=0 else Fraction(a,10**(-exponent))

def nearest_integer(q):
    n,r=divmod(q.numerator,q.denominator)
    return n+(2*r>q.denominator or (2*r==q.denominator and n%2==1))

def pow2(e): return Fraction(2**e,1) if e>=0 else Fraction(1,2**(-e))
def round_binary64(q):
    q=Fraction(q)
    if not q: return 0.0
    sign=1<<63 if q<0 else 0; q=abs(q)
    e=q.numerator.bit_length()-q.denominator.bit_length()
    if q<pow2(e): e-=1
    if e < -1022:
        m=nearest_integer(q/pow2(-1074)); bits=m
    else:
        m=nearest_integer(q/pow2(e-52))
        if m==2**53: m//=2; e+=1
        require(e<=1023,'InvalidScalar','binary64 overflow')
        bits=((e+1023)<<52)+(m-2**52)
    return struct.unpack('>d',(sign+bits).to_bytes(8,'big'))[0]

def rational(v):
    require(type(v) in (int,float),'InvalidScalar','numeric value required')
    require(type(v) is int or math.isfinite(v),'InvalidScalar','nonfinite')
    return Fraction(v)

def encode_scalar(own,x,limits=None):
    lim=limits or Limits()
    if own is None:
        if isinstance(x,str): own=CORE['Text']
        elif type(x) is bool: own=CORE['Boolean']
        elif isinstance(x,NumberToken): own=CORE['Double' if x.decimal else 'Integer']
        elif type(x) is int: own=CORE['Integer']
        elif type(x) is float: own=CORE['Double']
        else: raise Failure('InvalidScalar')
    if own==CORE['Integer']:
        if isinstance(x,str):
            require(INTEGER_TEXT.fullmatch(x),'InvalidScalar','canonical Integer text')
            require(within(len(x),lim.numeric_chars),'OperationLimitExceeded','Integer length')
            value=parse_integer(x)
        elif isinstance(x,NumberToken):
            if not x.decimal: require(abs(parse_integer(x.text))<=SAFE,'InvalidScalar','unsafe integer token')
            q=decimal_rational(x.text,lim)
            require(q.denominator==1,'InvalidScalar','fractional Integer')
            value=q.numerator
        elif type(x) is int: value=x
        else: raise Failure('InvalidScalar','Integer payload')
        require(within(len(integer_text(value)),lim.numeric_chars),'OperationLimitExceeded','Integer length')
        return own, value if abs(value)<=SAFE else integer_text(value)
    if own==CORE['Double']:
        if isinstance(x,NumberToken): v=round_binary64(decimal_rational(x.text,lim))
        elif isinstance(x,str): v=round_binary64(decimal_rational(x,lim))
        elif type(x) is int: v=round_binary64(Fraction(x))
        elif type(x) is float: v=x
        else: raise Failure('InvalidScalar','Double payload')
        require(math.isfinite(v),'InvalidScalar','nonfinite')
        return own, 0.0 if v==0 else v
    if own==CORE['Text']:
        require(isinstance(x,str),'InvalidScalar','Text payload'); return own,checked_unicode(x)
    if own==CORE['Boolean']:
        require(type(x) is bool,'InvalidScalar','Boolean payload'); return own,x
    # An opaque custom type does not authorize contextual conversion during naming.
    if isinstance(x,NumberToken):
        if not x.decimal:
            v=parse_integer(x.text); require(abs(v)<=SAFE,'InvalidScalar','unsafe integer token')
        else: v=round_binary64(decimal_rational(x.text,lim))
    else: v=x
    require(type(v) in (str,bool,int,float),'InvalidScalar','literal expected')
    if type(v) is int: require(abs(v)<=SAFE,'InvalidScalar','unsafe custom integer')
    if type(v) is float:
        require(math.isfinite(v),'InvalidScalar','nonfinite')
        # Under a custom own type, these spellings have the same numeric
        # commitment. Do not retain a host category that identity erased.
        if v.is_integer() and abs(v)<=SAFE: v=int(v)
    return own, (0.0 if type(v) is float and v==0 else v)

# === A03: Canonical bytes, hashes and exact normalization ===
@lru_cache(maxsize=8192)
def number_text(v):
    if v==0: return '0'
    sign='-' if v<0 else ''; q=Fraction(abs(v))
    e=len(str(q.numerator))-len(str(q.denominator))
    def ten(k): return Fraction(10**k,1) if k>=0 else Fraction(1,10**(-k))
    while q<ten(e): e-=1
    while q>=ten(e+1): e+=1
    for k in range(1,18):
        choices=[]
        for n in (e,e+1,e+2):
            scale=ten(n-k); a=q//scale
            for s in (a,a+1):
                if 10**(k-1)<=s<10**k:
                    try: match=round_binary64(s*scale)==abs(v)
                    except Failure: match=False
                    if match: choices.append((abs(s*scale-q),s%2,s,k,n))
        if choices:
            _,_,s,k,n=min(choices); d=str(s)
            if k<=n<=21: result=d+'0'*(n-k)
            elif 0<n<=21 and n<k: result=d[:n]+'.'+d[n:]
            elif -6<n<=0: result='0.'+'0'*(-n)+d
            else: result=d[0]+('.'+d[1:] if k>1 else '')+'e'+('+' if n-1>=0 else '-')+str(abs(n-1))
            return sign+result
    raise Failure('InternalError','shortest decimal')

def json_quote(s): return json.dumps(checked_unicode(s),ensure_ascii=False,separators=(',',':'))
def canonical_text(x):
    if x is None: return 'null'
    if type(x) is bool: return 'true' if x else 'false'
    if type(x) is str: return json_quote(x)
    if type(x) is int:
        require(abs(x)<=SAFE,'InvalidHashHelper','unsafe numeric Integer')
        return str(x)
    if type(x) is float:
        require(math.isfinite(x),'InvalidHashHelper','nonfinite')
        return number_text(x)
    if isinstance(x,(list,tuple)): return '['+','.join(canonical_text(a) for a in x)+']'
    if isinstance(x,dict): return '{'+','.join(json_quote(k)+':'+canonical_text(x[k]) for k in ordered(x))+'}'
    raise Failure('InvalidHashHelper',type(x).__name__)

def b58(data):
    z=len(data)-len(data.lstrip(b'\0')); n=int.from_bytes(data,'big'); out=''
    while n: n,r=divmod(n,58); out=ALPHABET[r]+out
    return '1'*z+out

def plain_id(s):
    require(isinstance(s,str) and s and all(c in ALPHABET for c in s),'InvalidBlueId')
    n=0
    for c in s: n=n*58+ALPHABET.index(c)
    z=len(s)-len(s.lstrip('1'))
    data=b'\0'*z+(n.to_bytes((n.bit_length()+7)//8,'big') if n else b'')
    require(len(data)==32 and b58(data)==s,'InvalidBlueId')
    return s

def final_id(s):
    require(isinstance(s,str),'InvalidBlueId')
    if '#' not in s: return plain_id(s)
    p=s.split('#'); require(len(p)==2 and INDEX.fullmatch(p[1]),'InvalidBlueId')
    plain_id(p[0]); return s

def H(raw): return b58(hashlib.sha256(canonical_text(raw).encode('utf-8')).digest())
def append_id(p,e): return H({'$listCons':{'prev':{'blueId':p},'elem':{'blueId':e}}})
def list_id(xs,token=None):
    p=H({'$list':'empty'})
    for x in xs: p=append_id(p,identity(x,token))
    return p

def helper(n,token=None):
    m={}
    for k,v in n.fields:
        if k in LITERALS: m[k]=v
        elif k=='items': m[k]={'blueId':list_id(v,token)}
        elif k=='mergePolicy': m[k]={'blueId':identity(scalar('Text',v),token)}
        else: m[k]={'blueId':identity(v,token)}
    return m

def identity(n,token=None):
    if isinstance(n,Ref): return n.id
    if isinstance(n,Local):
        require(token is not None,'InvalidBlueId','local edge outside cyclic operation')
        return token(n.index)
    require(isinstance(n,Node),'InvalidBlueIdInput')
    if n.keys()==('items',): return list_id(n.get('items'),token)
    return H(helper(n,token))

def contains_local(n):
    if isinstance(n,Local): return True
    if isinstance(n,Ref): return False
    if isinstance(n,Node):
        return any(contains_local(a) for k,v in n.fields if k not in LITERALS|{'mergePolicy'}
                   for a in (v if k=='items' else (v,)))
    return False

def normalize(x,c=None,mode='exact',symbolic=False):
    c=c or Context(); c.step()
    if isinstance(x,(Node,Ref,Local)):
        require(symbolic or not contains_local(x),'InvalidBlueId')
        return x
    require(x is not None,'InvalidExactNode')
    if isinstance(x,dict) and 'blueId' in x:
        require(set(x)=={'blueId'},'InvalidReferenceShape')
        s=x['blueId']
        if symbolic and isinstance(s,str) and re.fullmatch(r'this#(?:0|[1-9][0-9]*)',s):
            return Local(int(s[5:]))
        return Ref(final_id(s))
    if isinstance(x,list): x={'items':x}
    elif not isinstance(x,dict): x={'value':x}
    require(not set(x)&{'blue','properties','constraints'},'InvalidNodeShape','reserved key')
    m={k:v for k,v in x.items() if v is not None}
    require(all(isinstance(k,str) for k in m),'InvalidNodeShape','keys')
    for k in LABELS:
        if k in m: checked_unicode(m[k])
    if 'mergePolicy' in m: require(m['mergePolicy'] in ('positional','append-only'),'InvalidNodeShape','mergePolicy')
    ordinary=set(m)-RESERVED
    require(sum(('value' in m,'items' in m,bool(ordinary)))<=1,'InvalidNodeShape','payload kinds')
    for k in (TYPES|REFERENCE_METADATA)&set(m):
        if mode=='direct': require(isinstance(m[k],dict) and set(m[k])=={'blueId'} or isinstance(m[k],Ref),'InvalidBlueIdInput','type position')
        require(not isinstance(m[k],str),'UnknownTypeAlias')
        with error_scope(c,pointer(c.diagnostic_path,k)):
            n=normalize(m[k],c,'exact',symbolic)
        if contains_local(n): m[k]=n
        else:
            c.remember(n); m[k]=Ref(identity(n))
    if 'value' in m:
        t=m.get('type'); tid=t.id if isinstance(t,Ref) else ('symbolic' if t is not None else None)
        with error_scope(c):
            try: tid,val=encode_scalar(tid,m['value'],c.limits)
            except Failure as error:
                if error.expected is None: error.expected=diagnostic_value(tid=tid,c=c,kind='scalar')
                if error.actual is None: error.actual=diagnostic_value(m['value'])
                raise
        if t is None: m['type']=Ref(tid)
        m['value']=val
    for k in list(m):
        if k in TYPES|LITERALS|{'mergePolicy'}: continue
        if k=='items':
            require(isinstance(m[k],(list,tuple)),'InvalidNodeShape','items')
            values=[]
            for i,v in enumerate(m[k]):
                with error_scope(c,pointer(pointer(c.diagnostic_path,'items'),i)):
                    values.append(normalize(v,c,mode,symbolic))
            m[k]=tuple(values)
        else:
            with error_scope(c,pointer(c.diagnostic_path,k)):
                m[k]=normalize(m[k],c,mode,symbolic)
    n=node(m)
    if not contains_local(n): c.remember(n)
    return n

HOLE = node({'$empty':scalar('Boolean',True)})
HOLE_ID = identity(HOLE)
def is_hole(n): return identity(n)==HOLE_ID

# === A04: Lossless export and verified graph access ===
def export_tree(n):
    if isinstance(n,Ref): return {'blueId':n.id}
    if isinstance(n,Local): return {'blueId':'this#'+str(n.index)}
    m={}
    for k,v in n.fields:
        if k in LITERALS|{'mergePolicy'}: m[k]=v
        elif k=='items': m[k]=[export_tree(a) for a in v]
        else: m[k]=export_tree(v)
    return m['items'] if set(m)=={'items'} else m

def wire_text(x):
    if isinstance(x,NumberToken): return x.text
    if type(x) is float:
        t=number_text(x)
        return t+'.0' if not any(c in t for c in '.eE') else t
    if isinstance(x,list): return '['+','.join(wire_text(a) for a in x)+']'
    if isinstance(x,tuple): return '['+','.join(wire_text(a) for a in x)+']'
    if isinstance(x,dict): return '{'+','.join(json_quote(k)+':'+wire_text(x[k]) for k in ordered(x))+'}'
    return canonical_text(x)

def canonicalize_node(n,c):
    if isinstance(n,Ref): return n
    require(isinstance(n,Node),'InvalidExactNode')
    m={}
    for k,v in n.fields:
        if k in LITERALS|{'mergePolicy'}: m[k]=v
        elif k in TYPES:
            c.remember(v);m[k]=Ref(identity(v))
        elif k=='items': m[k]=tuple(canonicalize_node(a,c) for a in v)
        else: m[k]=canonicalize_node(v,c)
    return node(m)


def export_exact(n,c=None):
    c=c or Context()
    n=canonicalize_node(n,c)
    text=wire_text(export_tree(n))
    m=normalize(parse(text,limits=(c.limits if c else None)),Context(limits=(c.limits if c else Limits())))
    require(identity(m)==identity(n),'InternalError','export changed identity')
    return text

def open_exact(n,c):
    c.step()
    if isinstance(n,Node): return n
    require(isinstance(n,Ref),'InvalidExactNode')
    final_id(n.id)
    if n.body is not None: return n.body
    if n.id in c.bodies: return c.bodies[n.id]
    require(within(len(c.demands)+1,c.limits.fetches),'OperationLimitExceeded','provider count')
    c.demands.append(n.id)
    if n.id not in c.provider: raise Failure('ProviderUnavailable',n.id)
    response=c.provider[n.id]
    if isinstance(response,dict) and 'partialObject' in response:
        require(set(response)=={'partialObject','completeDirectManifest'},'InvalidProviderMode','manifest envelope')
        require(type(response['completeDirectManifest']) is bool,'InvalidProviderMode','manifest completeness')
        if not response['completeDirectManifest']:
            raise Failure('ProviderUnavailable',n.id)
        response={'text':wire_text(response['partialObject']),'mode':'exact'}
    if isinstance(response,dict) and 'outcome' in response:
        require(set(response)=={'outcome'},'InvalidProviderMode','outcome envelope')
        if response['outcome'] in ('NotFound','Unavailable'):
            raise Failure('ProviderUnavailable',n.id)
        if response['outcome']=='InvalidEvidence': raise Failure('ProviderBlueIdMismatch',n.id)
        raise Failure('InvalidProviderMode','unknown provider outcome')
    if '#' in n.id:
        require(isinstance(response,dict) and 'proof' in response and set(response)<={'proof','body'},'InvalidCyclicProof')
        h=verify_member(n.id,response['proof'],response.get('body'),c)
        return h.body
    if isinstance(response,Node): body=response
    else:
        require(isinstance(response,dict) and 'text' in response and
                set(response)<={'text','format','mode','environment'},'InvalidProviderMode','content envelope')
        mode=response.get('mode','exact')
        require(mode in ('exact','source'),'InvalidProviderMode','content role')
        try:
            raw=parse(response['text'],response.get('format','json'),c.limits)
        except Failure as failure:
            if failure.category in ('OperationLimitExceeded','ProviderUnavailable'): raise
            raise Failure('ProviderBlueIdMismatch',n.id) from failure
        if mode=='source':
            expected={'specification':'1.0','aliases':c.aliases,'directiveAliases':c.directive_aliases}
            require(response.get('environment')==expected,'InvalidProviderMode','unbound Source environment')
            body=prepare_source(raw,c)
        else:
            require('environment' not in response,'InvalidProviderMode','environment on exact body')
            try:
                body=normalize(raw,c)
            except Failure as failure:
                if failure.category in ('OperationLimitExceeded','ProviderUnavailable'): raise
                raise Failure('ProviderBlueIdMismatch',n.id) from failure
    require(isinstance(body,Node) and identity(body)==n.id,'ProviderBlueIdMismatch',n.id)
    c.bodies[n.id]=body
    return body

def path_parts(p):
    require(isinstance(p,str) and (p=='' or p.startswith('/')),'InvalidPath')
    if not p: return []
    result=[]
    for s in p[1:].split('/'):
        require(not re.search(r'~(?![01])',s),'InvalidPath')
        result.append(s.replace('~1','/').replace('~0','~'))
    return result

def exact_at(n,parts,c):
    if not parts: return n
    body=open_exact(n,c); k=parts[0]
    if k=='blueId': return ABSENT
    v=body.get(k)
    if v is ABSENT: return ABSENT
    if k=='items':
        if len(parts)==1: return tuple(v)
        require(INDEX.fullmatch(parts[1]),'InvalidPath','list index')
        i=int(parts[1]); return ABSENT if i>=len(v) else exact_at(v[i],parts[2:],c)
    if k in LITERALS|{'mergePolicy'}: return v if len(parts)==1 else ABSENT
    return exact_at(v,parts[1:],c)

def map_at(n,parts,c,fn):
    if not parts: return fn(n)
    b=open_exact(n,c); k=parts[0]; v=b.get(k)
    require(v is not ABSENT and k!='blueId','PathAbsent')
    if k=='items':
        require(len(parts)>=2 and INDEX.fullmatch(parts[1]),'InvalidPath')
        i=int(parts[1]); require(i<len(v),'PathAbsent')
        a=list(v); a[i]=map_at(a[i],parts[2:],c,fn); b=changed(b,items=tuple(a))
    else:
        require(k not in LITERALS|{'mergePolicy'},'InvalidPath','not a node position')
        b=changed(b,**{k:map_at(v,parts[1:],c,fn)})
    return Ref(n.id,b) if isinstance(n,Ref) and '#' in n.id else b

def expand(n,paths,c):
    out=n
    def reveal(x):
        b=open_exact(x,c)
        return Ref(x.id,b) if isinstance(x,Ref) and '#' in x.id else b
    for p in sorted(set(paths),key=lambda p:(len(path_parts(p)),key_order(p))):
        out=map_at(out,path_parts(p),c,reveal)
    require(identity(out)==identity(n),'InternalError','expansion')
    return out

def collapse(n,paths,c):
    out=n
    for p in sorted(set(paths),key=lambda p:(-len(path_parts(p)),key_order(p))):
        out=map_at(out,path_parts(p),c,lambda a:Ref(identity(a)))
    require(identity(out)==identity(n),'InternalError','collapse')
    return out


def split_fragments(exact,paths,c):
    """Split selected nodes and their structural ancestors, preserving exact IDs."""
    selected={()}
    for path in paths:
        parts=tuple(path_parts(path))
        target=exact_at(exact,parts,c)
        require(isinstance(target,(Node,Ref)),'InvalidPath','fragment node')
        for end in range(1,len(parts)+1):
            prefix=parts[:end]
            value=exact_at(exact,prefix,c)
            if isinstance(value,(Node,Ref)): selected.add(prefix)
    out=exact;fragments={}
    for parts in sorted(selected,key=lambda p:(-len(p),tuple(key_order(x) for x in p))):
        value=exact_at(out,parts,c)
        require(isinstance(value,(Node,Ref)),'InvalidPath','fragment path')
        rid=identity(value)
        # A selected reference is a demand, not a reason to silently omit a cut.
        # Cyclic bodies stay indexed by the member ID; the SDK also exports proofs.
        fragments[rid]=open_exact(value,c)
        if parts: out=map_at(out,parts,c,lambda old:Ref(identity(old)))
    require(identity(out)==identity(exact),'InternalError','fragment identity')
    return out,dict(sorted(fragments.items()))

# === A05: Constraint records, exact predicates and monotone schema refinement ===
SCHEMA_KEYS = frozenset(('required','minItems','maxItems','uniqueItems','minFields','maxFields',
                        'minimum','maximum','exclusiveMinimum','exclusiveMaximum','multipleOf',
                        'minLength','maxLength','enum'))
COUNT_PAIRS = (('minItems','maxItems'),('minFields','maxFields'),('minLength','maxLength'))
COUNT_KEYS = frozenset(k for p in COUNT_PAIRS for k in p)
NUMERIC_KEYS = frozenset(('minimum','maximum','exclusiveMinimum','exclusiveMaximum','multipleOf'))

@dataclass(frozen=True)
class Bound:
    value: Fraction
    exclusive: bool

@dataclass
class Constraint:
    required: bool|None = None
    unique: bool|None = None
    counts: dict = field(default_factory=dict)
    lower: Bound|None = None
    upper: Bound|None = None
    lower_facets: tuple = ()       # authored endpoints, before effective conjunction
    upper_facets: tuple = ()
    multiple: Fraction|None = None
    enum: tuple|None = None   # conjunction of finite alternative groups
    enum_values: dict = field(default_factory=dict)

def stronger_lower(a,b):
    if a is None: return b
    if b is None: return a
    return max((a,b),key=lambda x:(x.value,x.exclusive))
def stronger_upper(a,b):
    if a is None: return b
    if b is None: return a
    return min((a,b),key=lambda x:(x.value,not x.exclusive))
def lower_implies(a,b):
    return b is None or (a is not None and (a.value>b.value or
           a.value==b.value and (a.exclusive or not b.exclusive)))
def upper_implies(a,b):
    return b is None or (a is not None and (a.value<b.value or
           a.value==b.value and (a.exclusive or not b.exclusive)))
def lcm_int(a,b): return abs(a//math.gcd(a,b)*b)
def lcm_rational(a,b):
    return Fraction(lcm_int(a.numerator,b.numerator),math.gcd(a.denominator,b.denominator))

def scalar_description(n,c):
    """Read a schema operand only after certifying its own completed value."""
    rid=identity(n)
    if rid in c.operand_descriptions: return c.operand_descriptions[rid]
    require(rid not in c.operand_active,'SchemaVocabularyError','recursive schema operand')
    require(within(len(c.operand_active)+1,c.limits.depth),'OperationLimitExceeded','schema operand depth')
    c.operand_active.add(rid)
    try:
        result=certified_scalar_description(n,c)
        c.operand_descriptions[rid]=result
        return result
    finally:
        c.operand_active.remove(rid)


def certified_scalar_description(n,c):
    n=open_exact(n,c)
    require(n.kind() in ('scalar','none'),'SchemaVocabularyError','scalar operand')
    own=n.get('type'); tid=own.id if isinstance(own,Ref) else None
    require(tid is not None,'SchemaVocabularyError','scalar type required')
    core=domain_core(tid,c)
    require(core in ('Text','Integer','Double','Boolean'),'SchemaVocabularyError','scalar domain')
    values=[]
    if n.has('value'): values.append(n.get('value'))
    for t in ancestry(tid,c):
        if t in CORE_NAME: break
        b=open_exact(Ref(t),c)
        require(b.kind() in ('none','scalar'),'SchemaVocabularyError','scalar ancestry')
        if b.has('value'): values.append(b.get('value'))
    require(values,'SchemaVocabularyError','scalar payload required')
    vals=[scalar_effective(v,core) for v in values]
    require(all(type(v)==type(vals[0]) and v==vals[0] for v in vals),'FixedValueConflict','scalar operand')
    certify(n,c,'value')
    return tid,core,vals[0]

def scalar_key(type_id,core,value):
    # Labels do not participate in scalar predicate equality; the exact type does.
    wire = integer_text(value) if core=='Integer' and abs(value)>SAFE else value
    return canonical_text({'type':{'blueId':type_id},'value':wire})

def primitive_key(core,value):
    v=integer_text(value) if core=='Integer' and abs(value)>SAFE else value
    return canonical_text({'core':core,'value':v})

def enum_accepts(entry,type_id,core,value,c):
    t,k,v=entry
    return primitive_key(k,v)==primitive_key(core,value) and type_subtype(type_id,t,c)

def enum_groups_imply(a,b,c):
    if b.enum is None: return True
    if a.enum is None: return False
    c=c or Context()
    for parent_group in b.enum:
        covered=False
        for child_group in a.enum:
            if all(any(enum_accepts(b.enum_values[p],*a.enum_values[q],c)
                       for p in parent_group) for q in child_group):
                covered=True;break
        if not covered: return False
    return True


def read_schema(n,c):
    if n is ABSENT: return Constraint()
    n=open_exact(n,c)
    require(n.kind()=='object' and set(n.keys())<=SCHEMA_KEYS,'SchemaVocabularyError','schema map')
    s=Constraint()
    for k,v in n.fields:
        if k=='enum':
            a=open_exact(v,c)
            require(a.kind()=='list' and a.keys()==('items',),'SchemaVocabularyError','enum sequence')
            vals={}
            for i,item in enumerate(a.get('items')):
                with error_scope(c,pointer(pointer(pointer(c.diagnostic_path,k),'items'),i)):
                    tid,core,value=scalar_description(item,c)
                key=scalar_key(tid,core,value); vals[key]=(tid,core,value)
            require(vals,'SchemaViolation','empty enum')
            s.enum=(frozenset(vals),); s.enum_values=vals
        elif k in ('required','uniqueItems'):
            with error_scope(c,pointer(c.diagnostic_path,k)):
                _,core,value=scalar_description(v,c)
            require(core=='Boolean' and type(value) is bool,'SchemaVocabularyError',k)
            if k=='required': s.required=value
            else: s.unique=value
        elif k in COUNT_KEYS:
            with error_scope(c,pointer(c.diagnostic_path,k)):
                _,core,value=scalar_description(v,c)
            require(core=='Integer' and type(value) is int and 0<=value<=SAFE,'SchemaVocabularyError',k)
            s.counts[k]=value
        else:
            with error_scope(c,pointer(c.diagnostic_path,k)):
                _,core,value=scalar_description(v,c)
            require(core in ('Integer','Double'),'SchemaVocabularyError',k)
            q=rational(value)
            if k=='multipleOf':
                require(q>0,'SchemaVocabularyError','positive multipleOf');s.multiple=q
            elif k in ('minimum','exclusiveMinimum'):
                b=Bound(q,k.startswith('exclusive'));s.lower_facets+=(b,);s.lower=stronger_lower(s.lower,b)
            else:
                b=Bound(q,k.startswith('exclusive'));s.upper_facets+=(b,);s.upper=stronger_upper(s.upper,b)
    check_consistency(s)
    return s

def check_consistency(s):
    for lo,hi in COUNT_PAIRS:
        if lo in s.counts and hi in s.counts:
            require(s.counts[lo]<=s.counts[hi],'SchemaViolation',lo+' > '+hi)
    if s.lower is not None and s.upper is not None:
        require(s.lower.value<s.upper.value or
                s.lower.value==s.upper.value and not (s.lower.exclusive or s.upper.exclusive),
                'SchemaViolation','empty interval')
    require(s.multiple is None or s.multiple>0,'SchemaVocabularyError','multipleOf')
    require(s.enum is None or all(len(g)>0 for g in s.enum),'SchemaViolation','empty enum')


def check_schema_narrowing(parent,authored,c=None):
    # Omission inherits. An explicitly weaker replacement is an error.
    if parent.required is True and authored.required is not None:
        require(authored.required is True,'SchemaWeakening','required',keyword='required',expected={'value':True},actual={'value':authored.required})
    if parent.unique is True and authored.unique is not None:
        require(authored.unique is True,'SchemaWeakening','uniqueItems',keyword='uniqueItems',expected={'value':True},actual={'value':authored.unique})
    for lo,hi in COUNT_PAIRS:
        if lo in parent.counts and lo in authored.counts:
            require(authored.counts[lo]>=parent.counts[lo],'SchemaWeakening',lo,keyword=lo,expected={'value':parent.counts[lo]},actual={'value':authored.counts[lo]})
        if hi in parent.counts and hi in authored.counts:
            require(authored.counts[hi]<=parent.counts[hi],'SchemaWeakening',hi,keyword=hi,expected={'value':parent.counts[hi]},actual={'value':authored.counts[hi]})
    for bound in authored.lower_facets or (() if authored.lower is None else (authored.lower,)):
        require(lower_implies(bound,parent.lower),'SchemaWeakening','lower bound',
            keyword='exclusiveMinimum' if bound.exclusive else 'minimum',
            expected={'value':diagnostic_literal(parent.lower.value),'exclusive':parent.lower.exclusive} if parent.lower else {},
            actual={'value':diagnostic_literal(bound.value),'exclusive':bound.exclusive})
    for bound in authored.upper_facets or (() if authored.upper is None else (authored.upper,)):
        require(upper_implies(bound,parent.upper),'SchemaWeakening','upper bound',
            keyword='exclusiveMaximum' if bound.exclusive else 'maximum',
            expected={'value':diagnostic_literal(parent.upper.value),'exclusive':parent.upper.exclusive} if parent.upper else {},
            actual={'value':diagnostic_literal(bound.value),'exclusive':bound.exclusive})
    if authored.multiple is not None and parent.multiple is not None:
        require((authored.multiple/parent.multiple).denominator==1,'SchemaWeakening','multipleOf',keyword='multipleOf',
                expected={'value':diagnostic_literal(parent.multiple)},actual={'value':diagnostic_literal(authored.multiple)})
    if authored.enum is not None and parent.enum is not None:
        require(enum_groups_imply(authored,parent,c),'SchemaWeakening','enum')


def conjoin_schema(a,b):
    # This combines independently applicable obligations; it is not override admission.
    s=Constraint()
    s.required=None if a.required is None and b.required is None else bool(a.required or b.required)
    s.unique=None if a.unique is None and b.unique is None else bool(a.unique or b.unique)
    for lo,hi in COUNT_PAIRS:
        vs=[z.counts[lo] for z in (a,b) if lo in z.counts]
        if vs: s.counts[lo]=max(vs)
        vs=[z.counts[hi] for z in (a,b) if hi in z.counts]
        if vs: s.counts[hi]=min(vs)
    s.lower=stronger_lower(a.lower,b.lower); s.upper=stronger_upper(a.upper,b.upper)
    s.multiple=lcm_rational(a.multiple,b.multiple) if a.multiple is not None and b.multiple is not None else a.multiple or b.multiple
    groups=tuple(dict.fromkeys((a.enum or ())+(b.enum or ())))
    s.enum=groups or None
    s.enum_values={**a.enum_values,**b.enum_values}
    if groups:
        # A primitive payload mismatch proves emptiness without guessing domain overlap.
        common=None
        for g in groups:
            payloads={primitive_key(s.enum_values[k][1],s.enum_values[k][2]) for k in g}
            common=payloads if common is None else common&payloads
        require(common,'SchemaViolation','enum payload intersection is empty')
    check_consistency(s)
    return s

def refine_schema(parent,authored,c=None):
    check_schema_narrowing(parent,authored,c)
    return conjoin_schema(parent,authored)


def schema_implies(candidate,parent,c=None):
    # Complete procedural refinement relation for this vocabulary, facet by facet.
    if parent.required and not candidate.required: return False
    if parent.unique and not candidate.unique: return False
    for lo,hi in COUNT_PAIRS:
        if lo in parent.counts and candidate.counts.get(lo,0)<parent.counts[lo]: return False
        if hi in parent.counts and candidate.counts.get(hi,math.inf)>parent.counts[hi]: return False
    if not lower_implies(candidate.lower,parent.lower) or not upper_implies(candidate.upper,parent.upper): return False
    if parent.multiple is not None:
        if candidate.multiple is None or (candidate.multiple/parent.multiple).denominator!=1: return False
    if parent.enum is not None and not enum_groups_imply(candidate,parent,c): return False
    return True


def schema_kinds(s):
    groups=[]
    if s.lower is not None or s.upper is not None or s.multiple is not None: groups.append({'Integer','Double'})
    if any(k in s.counts for k in ('minLength','maxLength')): groups.append({'Text'})
    if any(k in s.counts for k in ('minItems','maxItems')) or s.unique is not None: groups.append({'List'})
    if any(k in s.counts for k in ('minFields','maxFields')): groups.append({'Dictionary'})
    if s.enum is not None:
        for group in s.enum: groups.append({s.enum_values[k][1] for k in group})
    return set.intersection(*groups) if groups else None


def validate_schema(h,present,goal,is_root,c):
    s=h.constraints; check_consistency(s)
    applicable=schema_kinds(s)
    known=h.core or {'object':'Dictionary','list':'List'}.get(h.kind)
    if known is None and h.kind=='scalar' and h.value is not ABSENT:
        known={bool:'Boolean',int:'Integer',float:'Double',str:'Text'}.get(type(h.value))
    if applicable is not None:
        require(known is None or known in applicable,'SchemaViolation','wrong payload kind')
        require(bool(applicable),'SchemaViolation','incompatible keyword kinds')
    if goal=='definition':
        if applicable is None: return
        if not concrete(h,c): return
    if not is_root and s.required and not present:
        raise Failure('SchemaViolation','required',keyword='required',expected={'present':True},actual={'present':False})
    if not present: return
    if goal=='value':
        if h.kind=='scalar': require(h.value is not ABSENT,'SchemaViolation','scalar payload required',
                    expected={**diagnostic_value(tid=h.type_id or CORE.get(h.core),c=c,kind='scalar'),'present':True},
                    actual=diagnostic_value())
        if h.kind=='list': require(h.items is not None,'SchemaViolation','list payload required',
                    expected={**diagnostic_value(tid=h.type_id or CORE.get(h.core),c=c,kind='List'),'present':True},
                    actual=diagnostic_value())
    dependent=applicable is not None
    if dependent: require(h.kind!='none' and (h.kind!='scalar' or h.value is not ABSENT),'SchemaViolation','payload required',
                    expected={**diagnostic_value(tid=h.type_id or CORE.get(h.core),c=c,kind=h.kind),'present':True},actual=diagnostic_value())
    if h.kind=='scalar' and h.value is not ABSENT:
        v=h.value
        if known in ('Integer','Double'):
            q=rational(v)
            if s.lower: require(q>s.lower.value or q==s.lower.value and not s.lower.exclusive,'SchemaViolation','lower bound',
                    keyword='exclusiveMinimum' if s.lower.exclusive else 'minimum',
                    expected={'value':diagnostic_literal(s.lower.value)},actual=diagnostic_value(v,h.type_id,c))
            if s.upper: require(q<s.upper.value or q==s.upper.value and not s.upper.exclusive,'SchemaViolation','upper bound',
                    keyword='exclusiveMaximum' if s.upper.exclusive else 'maximum',
                    expected={'value':diagnostic_literal(s.upper.value)},actual=diagnostic_value(v,h.type_id,c))
            if s.multiple is not None: require((q/s.multiple).denominator==1,'SchemaViolation','multipleOf',
                    keyword='multipleOf',expected={'value':diagnostic_literal(s.multiple)},actual=diagnostic_value(v,h.type_id,c))
        if known=='Text': check_count(s,'minLength','maxLength',len(v))
        if s.enum is not None:
            require(all(any(enum_accepts(s.enum_values[k],h.type_id or CORE[known],known,v,c) for k in g) for g in s.enum),'SchemaViolation','enum')
    if h.kind=='list' and h.items is not None:
        check_count(s,'minItems','maxItems',len(h.items))
        if s.unique:
            ids=[]
            for i,a in enumerate(h.items):
                with error_scope(c,pointer(pointer(c.diagnostic_path,'items'),i)):
                    ids.append(recipe_exact_id(a,c))
            require(len(ids)==len(set(ids)),'SchemaViolation','uniqueItems',keyword='uniqueItems',
                    expected={'value':True},actual={'value':False})
    if h.kind=='object':
        count=0
        for k,r in h.fields.items():
            with error_scope(c,pointer(c.diagnostic_path,k)):
                count+=bool(present_recipe(r,c))
        check_count(s,'minFields','maxFields',count)


def check_count(s,lo,hi,n):
    keyword=lo if n<s.counts.get(lo,0) else hi
    require(n>=s.counts.get(lo,0) and n<=s.counts.get(hi,math.inf),'SchemaViolation',lo+'/'+hi,
            keyword=keyword,expected={'value':s.counts.get(keyword)},actual={'value':n})


def describe_constraints(s):
    def q(x): return {'numerator':integer_text(x.numerator),'denominator':integer_text(x.denominator)}
    out={}
    if s.required is not None: out['required']=s.required
    if s.unique is not None: out['uniqueItems']=s.unique
    out.update(s.counts)
    if s.lower: out['lower']={**q(s.lower.value),'exclusive':s.lower.exclusive}
    if s.upper: out['upper']={**q(s.upper.value),'exclusive':s.upper.exclusive}
    if s.multiple is not None: out['multipleOf']=q(s.multiple)
    if s.enum is not None: out['enumAll']=[[json.loads(k) for k in sorted(g)] for g in sorted(s.enum,key=lambda g:tuple(sorted(g))) ]
    return out

# === A06: Declaration recipes, type ancestry and effective head resolution ===
@dataclass(frozen=True)
class Recipe:
    parts: tuple
    requirements: tuple = ()        # exact type identities required by a container
    def key(self):
        return (tuple(identity(x) for x in self.parts),self.requirements)

@dataclass
class Head:
    type_id: str|None = None
    core: str|None = None
    kind: str = 'none'
    labels: dict = field(default_factory=dict)
    specification: Ref|None = None
    constraints: Constraint = field(default_factory=Constraint)
    authored_schema: Constraint|None = None
    policy: str|None = None
    item_type: str|None = None
    key_type: str|None = None
    value_type: str|None = None
    value: Any = ABSENT
    fields: dict = field(default_factory=dict)
    items: tuple|None = None
    contracts: Any = None
    empty_object: bool = False
    origin: Any = None
    origins: tuple = ()


def recipe(*parts,requirements=()):
    # Repeating an identical contribution does not duplicate content or obligations.
    flat=[]
    req=list(requirements)
    for p in parts:
        if isinstance(p,Recipe): flat.extend(p.parts);req.extend(p.requirements)
        elif p is not None: flat.append(p)
    seen=set(); keep=[]
    for n in reversed(flat):
        k=identity(n)
        if k not in seen: keep.append(n);seen.add(k)
    return Recipe(tuple(reversed(keep)),tuple(dict.fromkeys(req)))


def copy_head(h):
    # Exact nodes/recipes are immutable; never deepcopy the ABSENT sentinel.
    return replace(h,labels=dict(h.labels),fields=dict(h.fields),
                   constraints=copy.deepcopy(h.constraints))


def ancestry(t,c):
    out=[];seen=set()
    while t is not None:
        require(t not in seen,'TypeCycle',t)
        seen.add(t);out.append(t)
        if t in CORE_NAME: break
        n=open_exact(Ref(t),c)
        r=n.get('type')
        t=r.id if isinstance(r,Ref) else None
    return out


def domain_core(t,c):
    if t is None: return None
    a=ancestry(t,c)
    if a[-1] in CORE_NAME: return CORE_NAME[a[-1]]
    last=open_exact(Ref(a[-1]),c)
    return {'object':'Dictionary','list':'List'}.get(last.kind())


def type_plan(t,c):
    # Prepare an ordinary parent chain bottom-up, without using Python's call
    # stack as a type-depth ceiling. Cross-field/schema recursion retains the
    # existing active-plan cycle checks in _type_plan_one.
    chain=[];seen=set();current=t
    while current not in c.plans:
        require(current not in seen and current not in c.plan_active,'TypeCycle',current)
        require(within(len(c.plan_active)+len(chain)+1,c.limits.depth),'OperationLimitExceeded','type depth')
        seen.add(current);chain.append(current)
        if current in CORE_NAME:break
        parent=open_exact(Ref(current),c).get('type')
        if not isinstance(parent,Ref):break
        current=parent.id
    for current in reversed(chain):_type_plan_one(current,c)
    c.step()
    return copy_head(c.plans[t])


def _type_plan_one(t,c):
    c.step()
    if t in c.plans: return copy_head(c.plans[t])
    require(t not in c.plan_active,'TypeCycle',t)
    require(within(len(c.plan_active)+1,c.limits.depth),'OperationLimitExceeded','type depth')
    c.plan_active.append(t)
    try:
        if t in CORE_NAME:
            core=CORE_NAME[t]
            h=Head(core=core,kind=('list' if core=='List' else 'object' if core=='Dictionary' else 'scalar'))
        else:
            h=single_head(open_exact(Ref(t),c),c)
        c.plans[t]=copy_head(h)
        try:
            if schema_kinds(h.constraints) is not None:
                validate_schema(h,True,'definition',True,c)
        except Exception:
            c.plans.clear()
            raise
        return h
    finally: c.plan_active.pop()


def as_requirement(t,c):
    h=type_plan(t,c)
    h.labels={}; h.specification=None; h.type_id=t; h.authored_schema=None
    return h


def scalar_effective(v,core):
    if core=='Integer':
        if isinstance(v,str):
            require(INTEGER_TEXT.fullmatch(v),'TypeCompatibilityViolation','Integer text')
            return parse_integer(v)
        if type(v) is float:
            require(math.isfinite(v) and Fraction(v).denominator==1,'TypeCompatibilityViolation','Integer value')
            return Fraction(v).numerator
        require(type(v) is int,'TypeCompatibilityViolation','Integer value')
        return v
    if core=='Double':
        require(type(v) in (int,float),'TypeCompatibilityViolation','Double value')
        f=round_binary64(Fraction(v)) if type(v) is int else v
        require(math.isfinite(f),'InvalidScalar'); return f
    if core=='Text': require(type(v) is str,'TypeCompatibilityViolation','Text value')
    if core=='Boolean': require(type(v) is bool,'TypeCompatibilityViolation','Boolean value')
    return v


def choose_type(parent,child,value,c):
    if parent is None: return child
    if child is None or child==parent: return parent
    pc=domain_core(parent,c);cc=domain_core(child,c)
    # Primitive spelling of a value may receive a narrower contextual interpretation.
    # This is not a subtype declaration and never rewrites its exact origin.
    if value is not ABSENT and child in CORE_NAME:
        if pc==cc: return parent
        if pc=='Integer' and cc=='Text' and type(value) is str and INTEGER_TEXT.fullmatch(value): return parent
    require(type_subtype(child,parent,c),'TypeCompatibilityViolation',str(child)+' is not a subtype of '+str(parent),
            expected=diagnostic_value(tid=parent,c=c), actual=diagnostic_value(value,child,c))
    return child


def single_head(n,c):
    c.step(); n=open_exact(n,c)
    t=n.get('type');tid=t.id if isinstance(t,Ref) else None
    inherited=as_requirement(tid,c) if tid else Head()
    h=Head(type_id=tid,core=domain_core(tid,c) if tid else {'object':'Dictionary','list':'List'}.get(n.kind()),kind=n.kind(),origin=n,origins=(n,),
           labels={k:n.get(k) for k in LABELS if n.has(k)},
           specification=None if n.get(SPECIFICATION) is ABSENT else n.get(SPECIFICATION),
           policy=None if n.get('mergePolicy') is ABSENT else n.get('mergePolicy'),
           empty_object=(n.kind()=='object' and not n.ordinary()))
    for field_name,attr in (('itemType','item_type'),('keyType','key_type'),('valueType','value_type')):
        x=n.get(field_name)
        if isinstance(x,Ref): setattr(h,attr,x.id)
    if n.has('schema'):
        with error_scope(c,pointer(c.diagnostic_path,'schema')):
            h.authored_schema=read_schema(n.get('schema'),c)
        h.constraints=h.authored_schema
    if n.has('value'):
        try: h.value=scalar_effective(n.get('value'),h.core)
        except Failure as error:
            error.expected=error.expected or diagnostic_value(tid=tid,c=c)
            error.actual=error.actual or diagnostic_value(n.get('value'),c=c)
            raise
    h.fields={k:recipe(n.get(k)) for k in n.ordinary()}
    if n.has('items'): h.items=tuple(recipe(x) for x in n.get('items'))
    if n.has('contracts'):
        h.contracts=recipe(n.get('contracts'))
    return merge_heads(inherited,h,c)


def concrete_node(n,c,active=None,type_depth=0):
    # Presence is reachability of an actual payload, or a cycle made solely of
    # ordinary-value edges. Type-declaration cycles do not manufacture values.
    # A finite graph walk avoids exponential unfolding of recursive repositories.
    root=identity(n)
    if root in c.presence_cache: return c.presence_cache[root]
    pending=[n]; seen=set(); ordinary={}
    while pending:
        value=pending.pop(); key=identity(value)
        if key in seen: continue
        c.step(); seen.add(key)
        if key in c.presence_cache:
            if c.presence_cache[key]: c.presence_cache[root]=True; return True
            ordinary[key]=(); continue
        body=open_exact(value,c)
        if body.has('value') or body.has('items') or not body.fields:
            c.presence_cache[root]=True; return True
        children=[body.get(k) for k in body.ordinary()]
        ordinary[key]=tuple(identity(x) for x in children)
        pending.extend(children)
        parent=body.get('type')
        if isinstance(parent,Ref) and parent.id not in CORE_NAME: pending.append(parent)
    # Remove all acyclic ordinary-edge vertices. Remaining vertices contain an
    # ordinary-value cycle, equivalent to the former same-type-depth back edge.
    indegree={key:0 for key in seen}
    for targets in ordinary.values():
        for key in targets: indegree[key]+=1
    queue=[key for key,value in indegree.items() if value==0]; removed=0
    while queue:
        key=queue.pop(); removed+=1
        for target in ordinary.get(key,()):
            indegree[target]-=1
            if indegree[target]==0: queue.append(target)
    result=removed<len(seen)
    c.presence_cache[root]=result
    return result


def concrete(h,c,seen=None):
    return any(concrete_node(n,c) for n in h.origins)


def present_recipe(r,c): return concrete(head(r,c),c)


def head(r,c):
    c.step()
    if not isinstance(r,Recipe): r=recipe(r)
    key=r.key()
    cacheable=not c.plan_active and not getattr(c,'subtype_active',()) and not c.operand_active
    if cacheable and key in c.heads: return copy_head(c.heads[key])
    h=Head()
    for t in r.requirements:
        h=merge_heads(h,as_requirement(t,c),c)
    for n in r.parts: h=merge_heads(h,single_head(n,c),c)
    if cacheable: c.heads[key]=copy_head(h)
    return h


def narrow_type_slot(p,q,c):
    if q is None: return p
    if p is None or p==q: return q
    require(type_subtype(q,p,c),'TypeCompatibilityViolation','collection type widening',
            expected=diagnostic_value(tid=p,c=c),actual=diagnostic_value(tid=q,c=c))
    return q


def merge_heads(p,q,c):
    c.step(); out=copy_head(p)
    out.type_id=choose_type(p.type_id,q.type_id,q.value,c)
    out.core=domain_core(out.type_id,c) if out.type_id else p.core or q.core
    if p.core is not None and q.core is not None and p.core!=q.core:
        require(q.value is not ABSENT and p.core=='Integer' and q.core=='Text',
                'TypeCompatibilityViolation','nominal core mismatch')
    out.item_type=narrow_type_slot(p.item_type,q.item_type,c)
    out.key_type=narrow_type_slot(p.key_type,q.key_type,c)
    out.value_type=narrow_type_slot(p.value_type,q.value_type,c)
    if q.authored_schema is not None: check_schema_narrowing(p.constraints,q.authored_schema,c)
    out.constraints=conjoin_schema(p.constraints,q.constraints)
    out.authored_schema=q.authored_schema
    if p.policy is not None and q.policy is not None: require(p.policy==q.policy,'TypeCompatibilityViolation','mergePolicy')
    out.policy=q.policy or p.policy
    for k,v in q.labels.items():
        if k in p.labels and p.labels[k]!=v:
            require(not concrete(p,c),'FixedValueConflict',k)
        out.labels[k]=v
    if q.specification is not None:
        if p.specification is not None and p.specification != q.specification:
            require(not concrete(p,c),'FixedValueConflict',SPECIFICATION)
        out.specification=q.specification
    if q.kind=='none': pass
    elif p.kind=='none':
        out.kind=q.kind;out.value=q.value;out.fields=dict(q.fields);out.items=q.items;out.empty_object=q.empty_object
    elif p.kind!=q.kind:
        # A core declaration has a required kind but no payload; kind remains binding.
        raise Failure('TypeCompatibilityViolation','payload kind')
    elif q.kind=='scalar':
        pv=scalar_effective(p.value,out.core) if p.value is not ABSENT else ABSENT
        qv=scalar_effective(q.value,out.core) if q.value is not ABSENT else ABSENT
        if pv is not ABSENT and qv is not ABSENT:
            require(type(pv)==type(qv) and pv==qv,'FixedValueConflict','scalar',
                    expected=diagnostic_value(pv,p.type_id or CORE.get(p.core),c),
                    actual=diagnostic_value(qv,q.type_id or CORE.get(q.core),c))
        out.value=qv if qv is not ABSENT else pv
    elif q.kind=='object':
        out.fields={k:recipe(p.fields.get(k),q.fields.get(k)) for k in ordered(set(p.fields)|set(q.fields))}
        out.empty_object=p.empty_object or q.empty_object
    elif q.kind=='list':
        if q.items is None: pass
        elif p.items is None: out.items=q.items
        else:
            require(len(q.items)>=len(p.items),'FixedValueConflict','list prefix removed')
            a=[]
            for i,r in enumerate(q.items):
                if i>=len(p.items): a.append(r)
                elif out.policy=='append-only':
                    require(recipe_exact_id(p.items[i],c)==recipe_exact_id(r,c),'FixedValueConflict','append-only prefix')
                    a.append(r)
                elif recipe_is_hole(p.items[i],c): a.append(r)
                else: a.append(recipe(p.items[i],r))
            out.items=tuple(a)
    out.contracts=recipe(p.contracts,q.contracts) if p.contracts is not None or q.contracts is not None else None
    out.origin=q.origin if q.origin is not None else p.origin
    out.origins=recipe(*(p.origins+q.origins)).parts
    known=out.core
    if known:
        kind='list' if known=='List' else 'object' if known=='Dictionary' else 'scalar'
        require(out.kind in ('none',kind),'TypeCompatibilityViolation','core payload kind')
        if out.kind=='none': out.kind=kind
    if out.item_type:
        require(out.kind in ('none','list'),'TypeCompatibilityViolation','itemType on non-list')
        if out.kind=='none': out.kind='list'
    if out.key_type or out.value_type:
        require(out.kind in ('none','object'),'TypeCompatibilityViolation','dictionary metadata on non-object')
        if out.kind=='none': out.kind='object'
    return out


def recipe_is_hole(r,c): return len(r.parts)==1 and not r.requirements and is_hole(r.parts[0])


def type_subtype(child,parent,c):
    if child==parent: return True
    a=ancestry(child,c)
    if parent in a: return True
    if child in CORE_NAME and parent in CORE_NAME: return False
    ch=type_plan(child,c);ph=type_plan(parent,c)
    ch.labels={};ph.labels={};ch.specification=None;ph.specification=None
    if ph.core is not None and ch.core!=ph.core: return False
    if not hasattr(c,'subtype_active'): c.subtype_active=set()
    pair=(child,parent)
    # Recursive field declarations use guarded simulation, not cyclic inheritance.
    if pair in c.subtype_active: return True
    c.subtype_active.add(pair)
    try: return preserves_heads(ch,ph,c,check_type=False)
    finally: c.subtype_active.remove(pair)


def guarantees_schema(h,required,c):
    applicable=schema_kinds(required)
    known=h.core or {'object':'Dictionary','list':'List'}.get(h.kind)
    if known is None and h.kind=='scalar' and h.value is not ABSENT:
        known={bool:'Boolean',int:'Integer',float:'Double',str:'Text'}.get(type(h.value))
    if applicable is not None:
        if known is not None and known not in applicable: return False
        if known is None:
            own_kinds=schema_kinds(h.constraints)
            if own_kinds is None or not own_kinds<=applicable: return False
    # Structural guarantees include fixed payload facts, not only written schema.
    established=copy.deepcopy(h.constraints)
    if concrete(h,c): established.required=True
    if h.items is not None:
        established.counts['minItems']=max(established.counts.get('minItems',0),len(h.items))
    if h.kind=='object':
        guaranteed=sum(bool(head(r,c).constraints.required) or present_recipe(r,c) for r in h.fields.values())
        established.counts['minFields']=max(established.counts.get('minFields',0),guaranteed)
    if schema_implies(established,required,c): return True
    if h.kind=='scalar' and h.value is not ABSENT:
        test=copy_head(h);test.constraints=required
        try:
            validate_schema(test,True,'value',True,c)
            return True
        except Failure as e:
            if e.category=='SchemaViolation': return False
            raise
    # Finite scalar alternatives can prove numeric/string facets without a
    # general satisfiability solver. Domain obligations are still compared.
    if h.kind=='scalar' and h.constraints.enum is not None:
        if required.required and not established.required: return False
        if required.enum is not None and not enum_groups_imply(h.constraints,required,c): return False
        candidates=None;values={}
        for group in h.constraints.enum:
            keys=set()
            for key in group:
                tid,core,value=h.constraints.enum_values[key]
                pk=primitive_key(core,value);keys.add(pk);values[pk]=(core,value)
            candidates=keys if candidates is None else candidates&keys
        viable=0
        for key in sorted(candidates or ()):
            core,value=values[key]
            if h.core is not None and core!=h.core: continue
            own=copy_head(h);own.core=core;own.value=value
            own.constraints.enum=None;own.constraints.enum_values={}
            try: validate_schema(own,True,'value',True,c)
            except Failure as e:
                if e.category=='SchemaViolation': continue
                raise
            viable+=1
            test=copy_head(own);test.constraints=copy.deepcopy(required)
            test.constraints.enum=None;test.constraints.enum_values={}
            try: validate_schema(test,True,'value',True,c)
            except Failure as e:
                if e.category=='SchemaViolation': return False
                raise
        return viable>0
    return False


def preserves_heads(candidate,parent,c,check_type=True):
    # A finite obligation worklist. A repeated pair is processed once after
    # its local obligations have been checked; it is not unconditional success.
    work=[(candidate,parent,check_type)]; seen=set()
    while work:
        a,b,ct=work.pop(); c.step()
        if b.core and a.core!=b.core: return False
        if b.kind!='none' and a.kind!=b.kind: return False
        if ct and b.type_id and (not a.type_id or not type_subtype(a.type_id,b.type_id,c)): return False
        if not guarantees_schema(a,b.constraints,c): return False
        for attr in ('item_type','key_type','value_type'):
            p=getattr(b,attr);q=getattr(a,attr)
            if p and (not q or not type_subtype(q,p,c)): return False
        if b.policy and a.policy!=b.policy: return False
        if b.value is not ABSENT:
            if a.value is ABSENT or type(a.value)!=type(b.value) or a.value!=b.value: return False
        if concrete(b,c):
            for k,v in b.labels.items():
                if a.labels.get(k,ABSENT)!=v: return False
        if concrete(b,c) and b.specification is not None and a.specification != b.specification:
            return False
        pairs=[]
        if b.kind=='object':
            if not set(b.fields)<=set(a.fields): return False
            pairs.extend((a.fields[k],b.fields[k]) for k in b.fields)
        if b.items is not None:
            if a.items is None or len(a.items)<len(b.items): return False
            for i,r in enumerate(b.items):
                if b.policy=='append-only':
                    if recipe_exact_id(a.items[i],c)!=recipe_exact_id(r,c): return False
                elif not recipe_is_hole(r,c):
                    pairs.append((a.items[i],r))
        if b.contracts is not None:
            if a.contracts is None: return False
            pairs.append((a.contracts,b.contracts))
        for x,y in pairs:
            key=(x.key(),y.key())
            if key in seen: continue
            seen.add(key)
            work.append((head(x,c),head(y,c),True))
    return True


def check_key(s,tid,c):
    core=domain_core(tid,c)
    require(core in ('Text','Integer','Double','Boolean'),'TypeCompatibilityViolation','keyType')
    if core=='Text': value=s;canonical=s
    elif core=='Integer':
        require(INTEGER_TEXT.fullmatch(s),'SchemaViolation','noncanonical Integer key')
        value=parse_integer(s);canonical=integer_text(value)
    elif core=='Boolean':
        require(s in ('true','false'),'SchemaViolation','Boolean key')
        value=s=='true';canonical=s
    else:
        value=round_binary64(decimal_rational(s,c.limits));canonical=number_text(value)
    require(s==canonical,'SchemaViolation','noncanonical key')
    literal=integer_text(value) if core=='Integer' and abs(value)>SAFE else value
    validate(recipe(scalar(core,literal),requirements=(tid,)),c,'value')


def validate(r,c,goal='value'):
    r=r if isinstance(r,Recipe) else recipe(r)
    root_path=c.diagnostic_path
    work=[(r,True,root_path)]; seen=set()
    while work:
        q,is_root,path=work.pop()
        with error_scope(c,path,'validation'):
            c.step();key=(q.key(),goal,is_root)
            if key in seen or key in c.validation_cache: continue
            seen.add(key)
            h=head(q,c);present=True if is_root else concrete(h,c)
            validate_schema(h,present,goal,is_root,c)
            if goal=='value' and not present: continue
            for k,ch in reversed(list(h.fields.items())):
                if h.core=='Dictionary' or h.key_type:
                    with error_scope(c,pointer(path,k)):
                        check_key(k,h.key_type or CORE['Text'],c)
                work.append((child_recipe(h,k),False,pointer(path,k)))
            if h.contracts is not None:
                with error_scope(c,pointer(path,'contracts')):
                    ch=head(h.contracts,c)
                    require(ch.kind in ('object','none'),'InvalidNodeShape','contracts map')
                work.append((h.contracts,False,pointer(path,'contracts')))
            if h.items is not None:
                for i,ch in reversed(list(enumerate(h.items))):
                    if goal=='definition' and recipe_is_hole(ch,c): continue
                    work.append((child_recipe(h,i),True,pointer(pointer(path,'items'),i)))
    # Publish successful obligations only after the whole worklist succeeded.
    # Contexts contain fixed immutable inputs and are not shared across calls.
    c.validation_cache.update(seen)
    with error_scope(c,root_path,'validation'):
        return head(r,c)


def child_recipe(h,k):
    """The same independently required child for every effective traversal."""
    if isinstance(k,int):
        part=h.items[k] if h.items is not None and k<len(h.items) else None
        tid=h.item_type
    else:
        part=h.fields.get(k);tid=h.value_type
    return recipe(part,requirements=((tid,) if tid else ())) if part is not None or tid else None


def resolved_at(r,parts,c):
    if not parts: return head(r,c)
    h=head(r,c);k=parts[0]
    if k=='blueId': return ABSENT
    if k=='items':
        if h.items is None: return ABSENT
        if len(parts)==1: return h.items
        require(INDEX.fullmatch(parts[1]),'InvalidPath')
        i=int(parts[1])
        if i>=len(h.items): return ABSENT
        with error_scope(c,pointer(pointer(c.diagnostic_path,'items'),i)):
            return resolved_at(child_recipe(h,i),parts[2:],c)
    if k in ('name','description'): return h.labels.get(k,ABSENT) if len(parts)==1 else ABSENT
    if k==SPECIFICATION:
        if h.specification is None: return ABSENT
        if len(parts)==1: return h.specification
        with error_scope(c,pointer(c.diagnostic_path,k)):
            return resolved_at(recipe(h.specification),parts[1:],c)
    if k=='value': return h.value if len(parts)==1 else ABSENT
    if k=='type': return Ref(h.type_id) if h.type_id and len(parts)==1 else ABSENT
    if k=='schema': return h.constraints if len(parts)==1 else ABSENT
    if k in ('itemType','keyType','valueType'):
        t=getattr(h,{'itemType':'item_type','keyType':'key_type','valueType':'value_type'}[k])
        return Ref(t) if t and len(parts)==1 else ABSENT
    if k=='mergePolicy': return (h.policy or 'positional') if h.kind=='list' and len(parts)==1 else ABSENT
    if k=='contracts':
        if h.contracts is None: return ABSENT
        with error_scope(c,pointer(c.diagnostic_path,'contracts')):
            return resolved_at(h.contracts,parts[1:],c)
    child=h.fields.get(k)
    if child is None: return ABSENT
    with error_scope(c,pointer(c.diagnostic_path,k)):
        return resolved_at(child_recipe(h,k),parts[1:],c)

# === A07: Exact refinement and Language list specialization ===
def merge_schema_exact(a,b,c):
    if a is ABSENT: return b
    if b is ABSENT: return a
    if identity(a)==identity(b): return a
    pa=read_schema(a,c);pb=read_schema(b,c)
    refine_schema(pa,pb,c)
    x=open_exact(a,c);y=open_exact(b,c)
    # The constructor has an ordered base/overlay, not unordered input schemas.
    # Missing keywords inherit; a supplied keyword is retained after narrowing.
    return node({**dict(x.fields),**dict(y.fields)})


def refine_exact(base,overlay,c,allow_hole=False):
    if identity(base)==identity(overlay): return base
    if allow_hole and is_hole(base): return overlay
    b=open_exact(base,c);o=open_exact(overlay,c)
    require(b.kind()=='none' or o.kind() in ('none',b.kind()),'TypeCompatibilityViolation','refinement payload kind')
    # Merge the complete explicit operands, not their type-enriched bodies.
    m=dict(b.fields); bh=single_head(b,c)
    for k,v in o.fields:
        if k in LABELS:
            if k in m and m[k]!=v: require(not concrete(bh,c),'FixedValueConflict',k)
            m[k]=v
        elif k==SPECIFICATION:
            if k in m and identity(m[k])!=identity(v):
                require(not concrete(bh,c),'FixedValueConflict',SPECIFICATION)
            m[k]=v
        elif k in TYPES:
            if k in m:
                if k=='type': m[k]=Ref(choose_type(m[k].id,v.id,o.get('value'),c))
                else: m[k]=Ref(narrow_type_slot(m[k].id,v.id,c))
            else: m[k]=v
        elif k=='schema': m[k]=merge_schema_exact(m.get(k,ABSENT),v,c)
        elif k=='mergePolicy':
            require(k not in m or m[k]==v,'TypeCompatibilityViolation','mergePolicy');m[k]=v
        elif k=='value':
            effective=domain_core(m['type'].id,c) if 'type' in m else None
            nv=scalar_effective(v,effective)
            if k in m:
                old=scalar_effective(m[k],effective)
                require(type(old)==type(nv) and old==nv,'FixedValueConflict','scalar',
                        expected=diagnostic_value(old,m.get('type').id if isinstance(m.get('type'),Ref) else None,c),
                        actual=diagnostic_value(nv,o.get('type').id if isinstance(o.get('type'),Ref) else None,c))
            m[k]=v
        elif k=='items':
            if k not in m: m[k]=v
            else:
                p=m[k]; require(len(v)>=len(p),'FixedValueConflict','list prefix removed')
                if m.get('mergePolicy')=='append-only':
                    require(all(identity(x)==identity(y) for x,y in zip(p,v)),'FixedValueConflict','append-only prefix')
                    m[k]=v
                else:
                    merged=[]
                    for i,(x,y) in enumerate(zip(p,v)):
                        with error_scope(c,pointer(pointer(c.diagnostic_path,'items'),i)):
                            merged.append(refine_exact(x,y,c,allow_hole=True))
                    m[k]=tuple(merged)+tuple(v[len(p):])
        elif k not in m: m[k]=v
        else:
            with error_scope(c,pointer(c.diagnostic_path,k)):
                m[k]=refine_exact(m[k],v,c)
    result=normalize_raw_node(m,c)
    require(b.kind()=='none' or result.kind()==b.kind(),'TypeCompatibilityViolation','lost explicit payload')
    # Keep exact results and their effective checks separate.
    validate(recipe(result),c,'definition')
    return c.remember(result)


def normalize_raw_node(m,c):
    return normalize({k:(list(v) if k=='items' else v) for k,v in m.items()},c)


def recipe_exact_value(r,c):
    require(r.parts,'InvalidOperation','a declaration does not supply an exact value')
    result=r.parts[0]
    for a in r.parts[1:]: result=refine_exact(result,a,c)
    return result

def recipe_exact_id(r,c): return identity(recipe_exact_value(r,c))


def anchor_id(value):
    try: return plain_id(value)
    except Failure as failure:
        if failure.category!='InvalidBlueId': raise
        raise Failure('ListControlViolation','anchor requires a plain valid BlueId') from failure


def specialize_payload(base,edits,appends,policy,anchor,c,prepare_operand):
    require(policy in ('positional','append-only'),'ListControlViolation','policy')
    require(not(edits and appends),'ListControlViolation','mixed edits and elements')
    require(anchor is None or policy=='append-only','ListControlViolation','positional anchor')
    if anchor is not None:
        anchor_id(anchor)
        require(list_id(base)==anchor,'ListControlViolation','anchor mismatch')
    require(len({i for i,_,_ in edits})==len(edits),'ListControlViolation','duplicate index')
    for i,op,value in edits:
        require(type(i) is int and 0<=i<len(base),'ListControlViolation','index')
        require(policy=='positional','ListControlViolation','append-only edit')
    out=list(base)
    for i,op,value in sorted(edits,key=lambda e:e[0]):
        with error_scope(c,pointer(pointer(c.diagnostic_path,'items'),i)):
            operand=prepare_operand(value,i)
        if op=='overlay':
            b=open_exact(base[i],c);o=open_exact(operand,c)
            require(is_hole(base[i]) or b.kind() in ('object','none') and o.kind() in ('object','none'),
                    'ListControlViolation','map overlay needs object operands')
        # Both paths preserve the base. A replacement is not arbitrary mutation.
        with error_scope(c,pointer(pointer(c.diagnostic_path,'items'),i)):
            out[i]=refine_exact(base[i],operand,c,allow_hole=True)
    for value in appends:
        with error_scope(c,pointer(pointer(c.diagnostic_path,'items'),len(out))):
            out.append(prepare_operand(value,len(out)))
    return tuple(out)


def parse_controls(items):
    """Classify syntax only; policy and prefix truth require the inherited head."""
    anchor=None;previous=None;edits=[];values=[]
    for position,x in enumerate(items):
        if isinstance(x,(Ref,Node)): values.append(x);continue
        if isinstance(x,dict) and ('$previous' in x or '$previousItems' in x):
            require(position==0 and anchor is None and previous is None and len(x)==1,
                    'ListControlViolation','prefix assertion must be first and unique')
            if '$previousItems' in x:
                require(type(x['$previousItems']) is bool,'ListControlViolation','previousItems requires Boolean')
                previous=x['$previousItems']
            else:
                a=x['$previous']
                require(isinstance(a,dict) and set(a)=={'blueId'},'ListControlViolation','anchor shape')
                anchor=anchor_id(a['blueId'])
        elif isinstance(x,dict) and '$pos' in x:
            t=x['$pos']
            require(isinstance(t,NumberToken) and not t.decimal,'ListControlViolation','Integer index token')
            i=int(t.text);require(0<=i<=SAFE,'ListControlViolation','index')
            if '$replace' in x:
                require(set(x)=={'$pos','$replace'},'ListControlViolation','replacement shape')
                edits.append((i,'replace',x['$replace']))
            else:
                o={k:v for k,v in x.items() if k!='$pos'}
                require(not set(o)&CONTROLS,'ListControlViolation','mixed control')
                edits.append((i,'replace' if 'value' in o else 'overlay',o))
        elif isinstance(x,dict) and set(x)&CONTROLS:
            raise Failure('ListControlViolation','malformed control')
        else: values.append(x)
    require(not(edits and (values or anchor is not None or previous is not None)),
            'ListControlViolation','positional edits cannot mix with elements or prefix assertions')
    require(len({i for i,_,_ in edits})==len(edits),'ListControlViolation','duplicate index')
    return anchor,previous,edits,values

# === A08: Preprocessing with fixed, content-addressed transform selection ===
INFER_IDS=frozenset(('FGYuTXwaoSKfZmpTysLTLsb8WzSqf43384rKZDkXhxD4','49hrWpkoXavNmK8PpZag11zB2vYwzhQZahwioz6vDk2i'))
ALIAS_IDS=frozenset(('27B7fuxQCS1VAptiCPc2RMkKoutP5qxkh3uDxZ7dr6Eo','53yFLQ3dpuGwa2svHubDyzyhYz9RQNmctiJRdi3gRYr7'))
RENAME_ID='7kEewGH6vogsgUXw3Gdyi73rtb5oQK1L8LWtHbYcG7pB'
APPEND_TEXT_ID='D2DxVxaddbJT5k2YYj3sG35cSdotw1Mz9GpxrdP43nzN'
SET_SOURCE_FIELD_ID='3uVsScHAE36fm2Knz3P6tWY94nuEA7cVDWxci8bY2zGg'


def source_walk(x,bindings,infer=True,substitute=True,in_item=False,path='',limits=None):
    try:
        if isinstance(x,(Node,Ref)): return x
        if isinstance(x,dict) and 'blueId' in x:
            require(set(x)=={'blueId'},'InvalidReferenceShape');final_id(x['blueId']);return copy.deepcopy(x)
        if x is None: return HOLE if in_item else None
        if isinstance(x,list): return [source_walk(a,bindings,infer,substitute,True,pointer(pointer(path,'items'),i),limits=limits) for i,a in enumerate(x)]
        if not isinstance(x,dict): x={'value':x}
        require('blue' not in x and not set(x)&{'properties','constraints'},'InvalidNodeShape','reserved key')
        if in_item and set(x)&CONTROLS:
            if '$previous' in x or '$previousItems' in x:
                require(len(x)==1,'ListControlViolation','prefix assertion shape');return copy.deepcopy(x)
            require('$pos' in x,'ListControlViolation')
            if '$replace' in x:
                require(set(x)=={'$pos','$replace'},'ListControlViolation')
                return {'$pos':x['$pos'],'$replace':source_walk(x['$replace'],bindings,infer,substitute,path=pointer(path,'$replace'),limits=limits)}
            o=source_walk({k:v for k,v in x.items() if k!='$pos'},bindings,infer,substitute,path=path,limits=limits)
            return {'$pos':x['$pos'],**o}
        require('$previousItems' not in x,'ListControlViolation','prefix assertion outside list items')
        m={k:v for k,v in x.items() if v is not None}
        for k in list(m):
            if k in TYPES:
                if isinstance(m[k],str):
                    if substitute:
                        require(m[k] in bindings,'UnknownTypeAlias',m[k]);m[k]={'blueId':bindings[m[k]]}
                else: m[k]=source_walk(m[k],bindings,infer,substitute,path=pointer(path,k),limits=limits)
            elif k==SPECIFICATION:
                require(isinstance(m[k],(dict,Node,Ref)), 'InvalidNodeShape', 'specification requires an explicit node or reference')
                m[k]=source_walk(m[k],bindings,infer,substitute,path=pointer(path,k),limits=limits)
            elif k=='items':
                require(isinstance(m[k],list),'InvalidNodeShape','items')
                m[k]=[source_walk(a,bindings,infer,substitute,True,pointer(pointer(path,k),i),limits=limits) for i,a in enumerate(m[k])]
            elif k not in LITERALS|{'mergePolicy'}: m[k]=source_walk(m[k],bindings,infer,substitute,path=pointer(path,k),limits=limits)
        for k in LABELS&set(m): checked_unicode(m[k])
        if 'mergePolicy' in m: require(m['mergePolicy'] in ('positional','append-only'),'InvalidNodeShape','mergePolicy')
        require(sum(('value' in m,'items' in m,bool(set(m)-RESERVED)))<=1,'InvalidNodeShape','payload kinds')
        if 'value' in m: require(isinstance(m['value'],NumberToken) or type(m['value']) in (str,bool,int,float),'InvalidScalar')
        if 'items' in m and any(isinstance(a,dict) and set(a)&CONTROLS for a in m['items']): parse_controls(m['items'])
        if infer and 'value' in m and 'type' not in m:
            tid,_=encode_scalar(None,m['value'],limits);m['type']={'blueId':tid}
        return m
    except Failure as error:
        if error.path is None: error.path=path
        raise

def config_object(x,c):
    n=normalize(x,c);n=open_exact(n,c)
    require(n.kind() in ('object','none'),'InvalidPreprocessing','configuration object')
    return n


def config_text(n,c):
    n=open_exact(n,c)
    require(n.kind()=='scalar' and set(n.keys())<={'type','value'},'InvalidPreprocessing','Text configuration')
    require(n.get('type')==Ref(CORE['Text']) and type(n.get('value')) is str,'InvalidPreprocessing','Text configuration')
    return n.get('value')


def preprocess(root,c):
    c.step()
    for name,tid in c.aliases.items():
        final_id(tid)
        require(name not in CORE or CORE[name]==tid,'InvalidPreprocessing','core alias rebind')
    if isinstance(root,dict) and 'blueId' in root:
        require(set(root)=={'blueId'},'InvalidReferenceShape')
    raw_directive=root.get('blue',ABSENT) if isinstance(root,dict) else ABSENT
    if raw_directive is ABSENT: d=node({})
    else:
        require(raw_directive is not None,'InvalidPreprocessing','null directive')
        if isinstance(raw_directive,str):
            require(raw_directive in c.directive_aliases,'InvalidPreprocessing','unknown directive alias')
            raw_directive=Ref(plain_id(c.directive_aliases[raw_directive]))
        d=config_object(raw_directive,c)
        require(set(d.keys())<={'imports','transformations','type','name','description'},'InvalidPreprocessing','directive fields')
    bindings=dict(c.aliases)
    if d.has('imports'):
        imports=open_exact(d.get('imports'),c)
        require(imports.kind()=='object' and not set(imports.keys())&RESERVED,'InvalidPreprocessing','imports')
        for alias,r in imports.fields:
            require(isinstance(r,Ref),'InvalidPreprocessing','import target')
            final_id(r.id)
            require(alias not in bindings or bindings[alias]==r.id,'InvalidPreprocessing','alias collision')
            bindings[alias]=r.id
    plans=[]
    if d.has('transformations'):
        ts=open_exact(d.get('transformations'),c)
        require(ts.keys()==('items',),'InvalidPreprocessing','transformation sequence')
        for x in ts.get('items'):
            t=open_exact(x,c);r=t.get('type')
            require(isinstance(r,Ref),'InvalidPreprocessing','exact transformation type')
            tid=r.id;allowed={'type','name','description'}
            if tid in INFER_IDS: plan=('infer',None)
            elif tid in ALIAS_IDS:
                allowed.add('mappings');m=open_exact(t.get('mappings'),c)
                require(m.kind()=='object' and not set(m.keys())&RESERVED,'InvalidPreprocessing','mappings')
                mapping={k:final_id(config_text(v,c)) for k,v in m.fields}
                require(all(k not in CORE or CORE[k]==v for k,v in mapping.items()),'InvalidPreprocessing','core alias rebind')
                plan=('alias',mapping)
            elif tid==RENAME_ID:
                allowed|={'from','to'};plan=('rename',(config_text(t.get('from'),c),config_text(t.get('to'),c)))
            elif tid==APPEND_TEXT_ID:
                allowed|={'field','suffix'};plan=('appendText',(config_text(t.get('field'),c),config_text(t.get('suffix'),c)))
            elif tid==SET_SOURCE_FIELD_ID:
                allowed|={'field','expression','format'}
                require(t.has('field') and t.has('expression'),'InvalidPreprocessing','assignment operands')
                target=config_text(t.get('field'),c)
                require(target!='blue','InvalidPreprocessing','assignment cannot introduce blue')
                fmt=config_text(t.get('format'),c) if t.has('format') else 'json'
                require(fmt in ('json','yaml'),'InvalidPreprocessing','assignment format')
                expression=parse(config_text(t.get('expression'),c),fmt,c.limits)
                require(not has_blue(expression),'InvalidPreprocessing','assignment contains blue')
                plan=('setSourceField',(target,expression))
            else: raise Failure('UnsupportedPreprocessingTransform',tid)
            require(set(t.keys())<=allowed,'InvalidPreprocessing','transformation fields')
            plans.append(plan)
    s=copy.deepcopy(root)
    if isinstance(s,dict): s.pop('blue',None)
    for op,arg in plans:
        if op=='infer': s=source_walk(s,{},True,False,limits=c.limits)
        elif op=='alias': s=substitute_available_aliases(s,arg)
        elif op=='setSourceField':
            target,expression=arg
            require(isinstance(s,dict),'InvalidPreprocessing','assignment requires object Source root')
            s[target]=copy.deepcopy(expression)
        elif op=='rename':
            a,b=arg;require(isinstance(s,dict) and a in s and b not in s,'InvalidPreprocessing','rename')
            s[b]=s.pop(a)
        else:
            k,suffix=arg;require(isinstance(s,dict) and k in s,'InvalidPreprocessing','append Text')
            v=s[k]
            if isinstance(v,dict):
                require(set(v)<={'type','value'} and type(v.get('value')) is str,'InvalidPreprocessing','Text source')
                if 'type' in v: require(v['type'] in ('Text',{'blueId':CORE['Text']}),'InvalidPreprocessing','Text source')
                v['value']+=suffix
            else:
                require(type(v) is str,'InvalidPreprocessing','Text source');s[k]=v+suffix
        require(not has_blue(s),'InvalidPreprocessing','introduced blue')
    return source_walk(s,bindings,True,True,limits=c.limits)


def has_blue(x):
    if isinstance(x,(Node,Ref)): return False
    if isinstance(x,dict): return 'blue' in x or any(has_blue(v) for k,v in x.items() if k not in LITERALS|{'mergePolicy','blueId'})
    if isinstance(x,list): return any(has_blue(v) for v in x)
    return False


def substitute_available_aliases(x,mappings,in_item=False):
    if isinstance(x,(Node,Ref)): return x
    if isinstance(x,list): return [substitute_available_aliases(a,mappings,True) for a in x]
    if not isinstance(x,dict): return x
    if 'blueId' in x: return copy.deepcopy(x)
    out={}
    for k,v in x.items():
        if k in TYPES and isinstance(v,str) and v in mappings: out[k]={'blueId':mappings[v]}
        elif k in LITERALS|{'mergePolicy','$pos'}: out[k]=v
        elif k=='items' and isinstance(v,list): out[k]=[substitute_available_aliases(a,mappings,True) for a in v]
        else: out[k]=substitute_available_aliases(v,mappings)
    return out

# === A09: Source compilation and exact canonicalization ===
def inherited_head(s,lazy_context,c):
    selected=lazy_context() if lazy_context is not None else None
    base=head(selected,c) if selected is not None else Head()
    if isinstance(s,dict) and 'type' in s:
        r=normalize(s['type'],c)
        base=merge_heads(base,as_requirement(identity(r),c),c)
    # Container obligations authored here apply to nested constructors too.
    if isinstance(s,dict):
        headers={k:v for k,v in s.items() if k in {'itemType','keyType','valueType','schema','mergePolicy'}}
        if headers:
            nh=single_head(normalize(headers,c),c)
            # Metadata-only headers are merged against the established container kind.
            if nh.kind=='none': nh.kind=base.kind
            base=merge_heads(base,nh,c)
    return base


def child_context(s,lazy_context,k,c):
    def get():
        h=inherited_head(s,lazy_context,c)
        if k=='contracts': return h.contracts
        result=child_recipe(h,k)
        if isinstance(k,int) and result is not None and (h.policy or 'positional')=='positional':
            # A positional hole supplies no payload-kind requirement. Container
            # itemType obligations remain binding when its replacement is built.
            return recipe(*(n for n in result.parts if not is_hole(n)),requirements=result.requirements)
        return result
    return get

def prepare_source(root,c):
    with error_scope(c,phase='preprocessing'): prepared=preprocess(root,c)
    with error_scope(c,phase='source-construction'): return compile_source(prepared,None,c)


def compile_source(s,lazy_context,c):
    c.step()
    if isinstance(s,(Node,Ref)): return s
    if isinstance(s,dict) and 'blueId' in s: return normalize(s,c)
    if isinstance(s,list): s={'items':s}
    if not isinstance(s,dict): s={'value':s}
    s=dict(s)
    for k in ordered((TYPES|REFERENCE_METADATA)&set(s)):
        if k==SPECIFICATION:
            require(isinstance(s[k],(dict,Node,Ref)), 'InvalidNodeShape', 'specification requires an explicit node or reference')
        with error_scope(c,pointer(c.diagnostic_path,k)):
            d=compile_source(s[k],None,c)
        c.remember(d);s[k]=Ref(identity(d))
    if c.diagnostic_path=='':
        c.diagnostic_root=node({k:v for k,v in s.items() if k in LABELS or k in TYPES and isinstance(v,Ref)})
    if 'items' in s:
        a=s['items'];require(isinstance(a,list),'InvalidNodeShape','items')
        base=inherited_head(s,lazy_context,c)
        require(base.kind in ('none','list'),'TypeCompatibilityViolation','items on non-list')
        policy=base.policy or 'positional'
        elements=tuple(recipe_exact_value(r,c) for r in (base.items or ()))
        anchor,previous,edits,values=parse_controls(a)
        if policy=='append-only':
            require(not edits,'ListControlViolation','append-only edit')
            require(anchor is not None or previous is not None,'ListControlViolation',
                    'append-only items require $previousItems or $previous',
                    path=pointer(c.diagnostic_path,'items'),
                    hint='Use $previousItems: true for a nonempty inherited prefix; false only when it is empty.')
            if previous is not None:
                require(previous is bool(elements),'ListControlViolation','previousItems assertion mismatch',
                        path=pointer(pointer(c.diagnostic_path,'items'),0),
                        expected={'value':bool(elements),'inheritedItems':len(elements)},actual={'value':previous})
            if anchor is not None:
                require(base.items is not None,'ListControlViolation','anchor requires an established inherited payload')
            # Appends use their final index and the container itemType, never None.
            payload=specialize_payload(elements,[],values,policy,anchor,c,
                lambda value,index:compile_source(value,child_context(s,lazy_context,index,c),c))
        else:
            require(anchor is None and previous is None,'ListControlViolation','prefix assertions require append-only policy')
            if edits:
                payload=specialize_payload(elements,edits,[],policy,None,c,
                    lambda value,index:compile_source(value,child_context(s,lazy_context,index,c),c))
            else:
                # A supplied positional sequence presents positions 0..n-1.
                # An omitted items slot inherits; a supplied short sequence truncates
                # the required prefix and is invalid. It never means a suffix.
                require(len(values)>=len(elements),'FixedValueConflict','list prefix removed')
                result=[]
                for i,value in enumerate(values):
                    with error_scope(c,pointer(pointer(c.diagnostic_path,'items'),i)):
                        operand=compile_source(value,child_context(s,lazy_context,i,c),c)
                        result.append(refine_exact(elements[i],operand,c,allow_hole=True) if i<len(elements) else operand)
                payload=tuple(result)
        m={k:v for k,v in s.items() if k!='items'}
        for k in list(m):
            if k not in LITERALS|TYPES|{'mergePolicy'}:
                with error_scope(c,pointer(c.diagnostic_path,k)):
                    m[k]=compile_source(m[k],child_context(s,lazy_context,k,c),c)
        m['items']=list(payload);n=normalize(m,c)
        # Construction is not admission. The public boundary certifies the whole
        # result with its context; structural naming must not fetch unrelated
        # opaque children merely because a Source list was supplied.
        return c.remember(n)
    for k in list(s):
        if k in TYPES|LITERALS|{'mergePolicy','items'}: continue
        with error_scope(c,pointer(c.diagnostic_path,k)):
            s[k]=compile_source(s[k],child_context(s,lazy_context,k,c),c)
    return normalize(s,c)

# === A10: Symbolic cyclic identity and complete owning-set proofs ===
def locals_in(n):
    if isinstance(n,Local): return {n.index}
    if isinstance(n,Ref): return set()
    out=set()
    for k,v in n.fields:
        if k in LITERALS|{'mergePolicy'}: continue
        for a in (v if k=='items' else (v,)): out|=locals_in(a)
    return out


def local_map(n,fn):
    if isinstance(n,Local): return fn(n.index)
    if isinstance(n,Ref): return n
    m={}
    for k,v in n.fields:
        if k in LITERALS|{'mergePolicy'}: m[k]=v
        elif k=='items': m[k]=tuple(local_map(a,fn) for a in v)
        else: m[k]=local_map(v,fn)
    return node(m)


def root_commitment(n,token):
    if n.keys()==('items',): return {'kind':'list','elements':[identity(x,token) for x in n.get('items')]}
    return {'kind':'map','helper':helper(n,token)}


def finalize_set(raw_members,c):
    require(isinstance(raw_members,list) and raw_members,'CircularSetError','members')
    ns=[normalize(x,c,symbolic=True) for x in raw_members]
    require(all(isinstance(x,Node) for x in ns),'CircularSetError','reference root')
    edges=[locals_in(n) for n in ns];size=len(ns)
    require(any(edges) and all(all(0<=v<size for v in es) for es in edges),'CircularSetError','local target')
    for start in range(size):
        seen=set();todo=[start]
        while todo:
            i=todo.pop()
            if i in seen: continue
            seen.add(i);todo.extend(edges[i])
        require(len(seen)==size,'CircularSetError','not strongly connected')
    records=[]
    for i,n in enumerate(ns):
        records.append((identity(n,lambda _:ZERO),canonical_text(root_commitment(n,lambda _:ZERO)).encode('utf-8'),i))
    records.sort()
    require(all(records[i][:2]!=records[i-1][:2] for i in range(1,size)),
            'CircularSetError','ambiguous preliminary members')
    positions={r[2]:j for j,r in enumerate(records)}
    canonical=[local_map(ns[r[2]],lambda i:Local(positions[i])) for r in records]
    master=list_id(canonical,lambda i:'this#'+str(i))
    ids=[master+'#'+str(positions[i]) for i in range(size)]
    bodies=[]
    for n in canonical:
        symbolic_final=local_map(n,lambda i:Ref(master+'#'+str(i)))
        bodies.append(normalize(export_tree(symbolic_final),c))
    return {'master':master,'ids':ids,'canonical':canonical,'bodies':bodies}


def verify_member(expected,proof,body,c):
    final_id(expected);require('#' in expected,'InvalidCyclicProof')
    master,index=expected.split('#');j=int(index)
    if isinstance(proof,str): proof=parse(proof,limits=c.limits)
    require(isinstance(proof,dict) and set(proof)=={'members'},'InvalidCyclicProof','proof envelope')
    z=finalize_set(proof['members'],c)
    require(z['master']==master and 0<=j<len(z['ids']),'InvalidCyclicProof','master/index')
    require(z['ids']==[master+'#'+str(i) for i in range(len(z['ids']))],'InvalidCyclicProof','canonical proof order')
    derived=z['bodies'][j]
    if body is not None:
        if isinstance(body,str): body=parse(body,limits=c.limits)
        if isinstance(body,dict) and 'text' in body: body=parse(body['text'],body.get('format','json'),c.limits)
        given=normalize(body,c)
        require(isinstance(given,Node) and identity(given)==identity(derived),'InvalidCyclicProof','member body')
        derived=given
    c.bodies[expected]=derived;c.proofs[expected]=proof
    return Ref(expected,derived)

# === A11: Semantic equivalence and minimization ===
def same_view(a,b,c):
    a=a if isinstance(a,Recipe) else recipe(a);b=b if isinstance(b,Recipe) else recipe(b)
    todo=[(a,b)];seen=set()
    while todo:
        x,y=todo.pop();key=(x.key(),y.key());c.step()
        if key in seen or x.key()==y.key(): continue
        seen.add(key);p=head(x,c);q=head(y,c)
        if (p.type_id,p.core,p.kind,p.labels,p.specification,p.policy,p.item_type,p.key_type,p.value_type)!=(q.type_id,q.core,q.kind,q.labels,q.specification,q.policy,q.item_type,q.key_type,q.value_type): return False
        if describe_constraints(p.constraints)!=describe_constraints(q.constraints): return False
        if (p.value is ABSENT)!=(q.value is ABSENT): return False
        if p.value is not ABSENT and (type(p.value)!=type(q.value) or p.value!=q.value): return False
        if concrete(p,c)!=concrete(q,c): return False
        if set(p.fields)!=set(q.fields) or (p.contracts is None)!=(q.contracts is None): return False
        if (p.items is None)!=(q.items is None): return False
        if p.items is not None:
            if len(p.items)!=len(q.items): return False
            todo.extend((child_recipe(p,i),child_recipe(q,i)) for i in range(len(p.items)))
        todo.extend((child_recipe(p,k),child_recipe(q,k)) for k in p.fields)
        if p.contracts is not None: todo.append((p.contracts,q.contracts))
    return True


def source_for_exact(n,c,lazy_context=None):
    if isinstance(n,Ref): return {'blueId':n.id}
    raw=export_tree(n)
    if isinstance(raw,list): raw={'items':raw}
    for k in list(raw):
        if k in LITERALS|TYPES|{'mergePolicy','items'}: continue
        raw[k]=source_for_exact(n.get(k),c,child_context(raw,lazy_context,k,c))
    if n.has('items'):
        base=inherited_head(raw,lazy_context,c)
        xs=n.get('items');bs=tuple(recipe_exact_value(r,c) for r in (base.items or ()))
        if base.policy=='append-only':
            require(len(xs)>=len(bs) and all(identity(a)==identity(b) for a,b in zip(bs,xs)),
                    'FixedValueConflict','minimize append-only prefix')
            marker={'$previous':{'blueId':list_id(bs)}} if bs else {'$previousItems':False}
            raw['items']=[marker]+[source_for_exact(xs[i],c,child_context(raw,lazy_context,i,c)) for i in range(len(bs),len(xs))]
        else:
            raw['items']=[source_for_exact(x,c,child_context(raw,lazy_context,i,c)) for i,x in enumerate(xs)]
    return raw['items'] if set(raw)=={'items'} else raw

def reductions(raw):
    # Finite, ordered one-step reductions. No global shortest-source claim.
    if isinstance(raw,dict):
        if set(raw)=={'blueId'}: return
        for k in ordered(raw):
            if k in CONTROLS: continue
            out=dict(raw);del out[k];yield out
        if set(raw)=={'value'}: yield raw['value']
        if set(raw)=={'items'}: yield raw['items']
        for k in ordered(raw):
            if k in CONTROLS|{'blueId'} or k in TYPES: continue
            for v in reductions(raw[k]):
                out=dict(raw);out[k]=v;yield out
    elif isinstance(raw,list):
        for i,x in enumerate(raw):
            for v in reductions(x):
                out=list(raw);out[i]=v;yield out


def minimize(exact,c,goal='value'):
    certify(exact,c,goal)
    c.remember(exact)
    original=recipe(exact)
    raw=source_for_exact(exact,c)
    try:
        candidate=prepare_source(raw,c)
        if not same_view(original,candidate,c): raw={'blueId':identity(exact)}
    except Failure as f:
        if f.category in ('ProviderUnavailable','OperationLimitExceeded','ProviderBlueIdMismatch'): raise
        raw={'blueId':identity(exact)}
    while True:
        before=len(wire_text(raw).encode('utf-8'));accepted=None
        for smaller in reductions(raw):
            if len(wire_text(smaller).encode('utf-8'))>=before: continue
            try:
                prepared=prepare_source(smaller,c)
                certify(prepared,c,goal)
                if same_view(original,prepared,c): accepted=smaller;break
            except Failure as f:
                if f.category in ('ProviderUnavailable','OperationLimitExceeded','ProviderBlueIdMismatch'): raise
        if accepted is None: break
        raw=accepted
    result=prepare_source(raw,c)
    require(same_view(original,result,c),'InternalError','minimization roundtrip')
    return wire_text(raw)

# === A12: Portable observations, demand outcomes and entry points ===
def literal_output(v,core=None):
    if v is ABSENT: return {'outcome':'Absent'}
    if core=='Integer' or type(v) is int: return {'kind':'Integer','decimal':integer_text(v)}
    if core=='Double' or type(v) is float: return {'kind':'Double','bits':struct.pack('>d',float(v)).hex()}
    if type(v) is bool: return {'kind':'Boolean','value':v}
    if type(v) is str: return {'kind':'Text','value':v}
    raise Failure('InvalidOperation','not a literal')


def observe(exact,path,query,c):
    parts=path_parts(path)
    if query=='exactId':
        n=exact_at(exact,parts,c)
        if n is ABSENT: return {'outcome':'Absent'}
        require(isinstance(n,(Node,Ref)),'InvalidOperation','exact node required')
        return {'outcome':'Established','blueId':identity(n)}
    v=resolved_at(recipe(exact),parts,c)
    if v is ABSENT: return {'outcome':'Absent'}
    if isinstance(v,Head):
        if query=='kind': result=v.kind
        elif query=='type':
            if v.type_id is None: return {'outcome':'Absent'}
            result=v.type_id
        elif query=='value':
            if v.value is ABSENT: return {'outcome':'Absent'}
            result=literal_output(v.value,v.core)
        elif query=='constraints': result=describe_constraints(v.constraints)
        elif query=='keys': result=ordered(k for k,r in v.fields.items() if present_recipe(r,c))
        elif query=='length':
            require(v.items is not None,'InvalidOperation','not a list');result=len(v.items)
        elif query=='present':
            if parts and not concrete(v,c): return {'outcome':'Absent'}
            result=True
        elif query==SPECIFICATION:
            if v.specification is None: return {'outcome':'Absent'}
            result={'blueId':v.specification.id}
        elif query in ('name','description'):
            if query not in v.labels: return {'outcome':'Absent'}
            result=v.labels[query]
        else: raise Failure('InvalidOperation',query)
    else:
        require(query=='value','InvalidOperation','literal slot observation')
        result=literal_output(v) if not isinstance(v,(Constraint,Ref)) else describe_constraints(v) if isinstance(v,Constraint) else {'blueId':v.id}
    return {'outcome':'Established','value':result}


def outcome(fn):
    try: return fn()
    except RecursionError:
        return {'outcome':'Incomplete','category':'OperationLimitExceeded'}
    except Failure as e:
        status='Incomplete' if e.category in ('ProviderUnavailable','OperationLimitExceeded') else 'Invalid'
        return {'outcome':status,**e.as_dict()}


def initialize(registry,provider=None,aliases=None,limits=None):
    c=Context(provider=dict(provider or {}),limits=limits or Limits())
    for name,raw in registry.items():
        n=normalize(raw,c)
        require(identity(n)==CORE[name],'RegistryMismatch',name)
        c.bodies[CORE[name]]=n
    require(set(registry)==set(CORE),'RegistryMismatch','six core entries required')
    if aliases:
        for k,v in aliases.items():
            final_id(v);require(k not in CORE or CORE[k]==v,'InvalidPreprocessing','core alias rebind')
            c.aliases[k]=v
    c.work=0
    return c


def input_node(record,c):
    require(set(record)<={'mode','format','text'},'InvalidOperation','input fields')
    require('text' in record,'InvalidOperation','input text')
    mode=record.get('mode','source')
    raw=parse(record['text'],record.get('format','json'),c.limits)
    if mode=='source': return prepare_source(raw,c)
    require(mode in ('exact','direct'),'InvalidOperation','input mode')
    return normalize(raw,c,mode)


def certify(exact,c,goal='value'):
    require(goal in ('value','definition'),'InvalidOperation','validation goal')
    validate(exact,c,'definition')
    return validate(exact,c,'value') if goal=='value' else head(recipe(exact),c)

def check_subtype(child,parent,c):
    validate(Ref(child),c,'definition');validate(Ref(parent),c,'definition')
    return type_subtype(child,parent,c)

# === A13: Strict admission, root duplicate normalization and prefix wire ===
def strict_certify(exact,c,goal='value'):
    """Verify the reachable exact graph, its type definitions, then the requested role."""
    require(goal in ('definition','value'),'InvalidOperation','validation goal')
    root_path=c.diagnostic_path
    todo=[(exact,root_path)];seen=set();type_paths={};key_type_paths={};specification_paths={}
    while todo:
        value,path=todo.pop()
        with error_scope(c,path,'dependency-verification'):
            rid=identity(value);c.step()
            if rid in seen: continue
            seen.add(rid)
            body=open_exact(value,c)
            if path==root_path and c.diagnostic_root is exact:
                c.diagnostic_root=body
            children=[]
            for k,v in body.fields:
                if k in TYPES:
                    require(isinstance(v,Ref),'InvalidNodeShape','type position')
                    p=pointer(path,k);type_paths.setdefault(v.id,p);children.append((v,p))
                    if k=='keyType': key_type_paths.setdefault(v.id,p)
                elif k==SPECIFICATION:
                    require(isinstance(v,Ref),'InvalidNodeShape','specification position')
                    p=pointer(path,k);specification_paths.setdefault(v.id,p);children.append((v,p))
                elif k=='items':
                    children.extend((ch,pointer(pointer(path,k),i)) for i,ch in enumerate(v))
                elif k not in LITERALS|{'mergePolicy'}: children.append((v,pointer(path,k)))
            todo.extend(reversed(children))
    for tid in sorted(type_paths):
        if tid in CORE_NAME: continue
        with error_scope(c,type_paths[tid],'type-definition'):
            certify(Ref(tid),c,'definition')
    for sid in sorted(specification_paths):
        with error_scope(c,specification_paths[sid],'specification-content'):
            certify(Ref(sid),c,'definition')
    for tid in sorted(key_type_paths):
        with error_scope(c,key_type_paths[tid],'type-definition'):
            require(domain_core(tid,c) in ('Text','Integer','Double','Boolean'),
                    'TypeCompatibilityViolation','keyType')
    with error_scope(c,root_path,'validation'):
        certify(exact,c,goal)
    return tuple(sorted(seen))


def omit_root_duplicates(exact,c):
    """Canonical authoring at this creation root; never contextualize child IDs.

    Only an entire ordinary child exactly equal to a child already supplied by
    the root's own type can be omitted. Referenced/existing exact roots are not
    migrated. Never recursively turn a complete child into an ancestor delta.
    Canonicalizing a child as a new root is a separate explicit creation operation.
    """
    if isinstance(exact,Ref) or not exact.has('type'): return exact,()
    inherited=as_requirement(exact.get('type').id,c)
    if not inherited.fields: return exact,()
    m=dict(exact.fields);removed=[]
    for key in exact.ordinary():
        contribution=inherited.fields.get(key)
        if contribution is None or not contribution.parts: continue
        base=recipe_exact_value(contribution,c)
        if identity(m[key])==identity(base):
            del m[key];removed.append(pointer('',key))
    result=node(m)
    if removed:
        require(same_view(exact,result,c),'CanonicalizationError','duplicate removal changed effective view')
        c.remember(result)
    return result,tuple(removed)


def payload_body(prefix,c):
    """Open an exact payload-only prefix; its ID is never an outer typed-list ID."""
    prefix=plain_id(prefix)
    if prefix not in c.bodies:
        # A verified type may already contain that sequence inline.
        for body in tuple(c.bodies.values()):
            if isinstance(body,Node) and body.has('items'):
                candidate=list_node(body.get('items'))
                if identity(candidate)==prefix:
                    c.remember(candidate);break
    body=open_exact(Ref(prefix),c)
    require(body.keys()==('items',),'InvalidCanonicalList','prefix must identify a payload-only list')
    return body


def decode_canonical(raw,c,depth=0,lazy_context=None):
    """Decode the explicitly selected compact canonical wire, not ordinary exact data."""
    c.step();require(within(depth+1,c.limits.depth),'OperationLimitExceeded','canonical depth')
    if isinstance(raw,(Node,Ref)): return raw
    if isinstance(raw,dict) and 'blueId' in raw: return normalize(raw,c)
    if isinstance(raw,list): raw={'items':raw}
    if not isinstance(raw,dict): return normalize(raw,c)
    m=dict(raw)
    # Establish inline/exact type definitions before prefix lookup. This also
    # makes a prefix embedded in an already verified type body discoverable.
    for k in TYPES&set(m):
        require(not isinstance(m[k],str),'UnknownTypeAlias','canonical type position')
        t=decode_canonical(m[k],c,depth+1)
        require(isinstance(t,(Node,Ref)),'InvalidNodeShape','type')
        if isinstance(t,Node): c.remember(t)
        m[k]=Ref(identity(t));open_exact(m[k],c)
    for k,v in tuple(m.items()):
        if k in TYPES|LITERALS|{'mergePolicy'}: continue
        if k=='items':
            require(isinstance(v,list),'InvalidNodeShape','items')
            prefix=();start=0
            if v and isinstance(v[0],dict) and '$previous' in v[0]:
                a=v[0]
                require(set(a)=={'$previous'} and isinstance(a['$previous'],dict)
                        and set(a['$previous'])=={'blueId'},'InvalidCanonicalList','anchor shape')
                base=inherited_head(m,lazy_context,c)
                require(base.policy=='append-only' and base.items is not None,
                        'InvalidCanonicalList','prefix anchor requires an inherited append-only payload')
                pid=anchor_id(a['$previous']['blueId'])
                bs=tuple(recipe_exact_value(r,c) for r in base.items)
                # Validate the payload-only shape first, then the selected-base assertion.
                prefix=payload_body(pid,c).get('items')
                require(list_id(bs)==pid,'InvalidCanonicalList','anchor does not identify the selected inherited prefix')
                start=1
            suffix=[]
            for item in v[start:]:
                require(not(isinstance(item,dict) and set(item)&CONTROLS),
                        'InvalidCanonicalList','controls must be escaped as exact references')
                suffix.append(decode_canonical(item,c,depth+1,child_context(m,lazy_context,len(prefix)+len(suffix),c)))
            require(within(len(prefix)+len(suffix),c.limits.values),'OperationLimitExceeded','canonical items')
            m[k]=list(prefix)+suffix
        else: m[k]=decode_canonical(v,c,depth+1,child_context(m,lazy_context,k,c))
    return normalize(m,c)


def canonical_wire(exact,c,lazy_context=None,depth=0):
    """Return compact exact wire: a prefix anchor contributes no element.

    Compression never changes the exact node. Its full expanded body remains the
    authoritative stored exact representation. The root type's verified base,
    not an arbitrary longest shared prefix, selects the emitted anchor.
    """
    c.step();require(within(depth+1,c.limits.depth),'OperationLimitExceeded','canonical export depth')
    if isinstance(exact,Ref): return {'blueId':exact.id}
    raw=export_tree(exact)
    if isinstance(raw,list): raw={'items':raw}
    m={k:v for k,v in raw.items() if k in LITERALS|TYPES|{'mergePolicy'}}
    for k,v in exact.fields:
        if k in LITERALS|TYPES|{'mergePolicy'}: continue
        if k=='items':
            base=inherited_head(raw,lazy_context,c)
            bs=tuple(recipe_exact_value(r,c) for r in (base.items or ())) if base.kind=='list' else ()
            shared=base.policy=='append-only' and bool(bs) and len(v)>=len(bs) and all(identity(a)==identity(b)for a,b in zip(bs,v))
            output=[];start=0
            if shared:
                prefix=c.remember(list_node(bs));start=len(bs)
                output.append({'$previous':{'blueId':identity(prefix)}})
            for i in range(start,len(v)):
                item=v[i]
                # Escape literal control-shaped exact objects so canonical wire
                # cannot interpret a content element as a prefix instruction.
                if isinstance(item,Node) and set(item.keys())&CONTROLS:
                    c.remember(item);output.append({'blueId':identity(item)})
                else:
                    output.append(canonical_wire(item,c,child_context(raw,lazy_context,i,c),depth+1))
            m[k]=output
        else: m[k]=canonical_wire(v,c,child_context(raw,lazy_context,k,c),depth+1)
    return m['items'] if set(m)=={'items'} else m


def canonical_export(exact,c):
    wire=wire_text(canonical_wire(exact,c))
    rebuilt=decode_canonical(parse(wire,limits=c.limits),c)
    require(identity(rebuilt)==identity(exact),'InternalError','canonical wire changed identity')
    return wire


def admitted_records(exact,c):
    """All exact bodies reachable from a successful root, including list payloads.
    Each response is independently hash-verifiable. No intermediate Source object
    or enriched view is published. Cyclic identities retain owning-set proofs.
    """
    records={};todo=[exact];seen=set()
    while todo:
        n=todo.pop();rid=identity(n);c.step()
        if rid in seen: continue
        seen.add(rid);body=open_exact(n,c)
        if rid not in CORE_NAME:
            if '#' in rid:
                require(rid in c.proofs,'InvalidCyclicProof','publication proof unavailable')
                records[rid]={'proof':wire_text(c.proofs[rid]),'body':export_exact(body,c)}
            else: records[rid]={'text':export_exact(body,c),'mode':'exact'}
        for k,v in body.fields:
            if k=='items':
                p=c.remember(list_node(v));pid=identity(p)
                records[pid]={'text':export_exact(p,c),'mode':'exact'}
                todo.extend(reversed(v))
            elif k not in LITERALS|{'mergePolicy'}: todo.append(v)
    # Canonical export may use a prefix that is only a derived subsequence of a
    # type's complete payload. Retain exactly the additional referenced prefixes.
    compact=canonical_wire(exact,c)
    def prefix_walk(x):
        if isinstance(x,list):
            for z in x: prefix_walk(z)
        elif isinstance(x,dict):
            if set(x)=={'$previous'}:
                rid=x['$previous']['blueId'];b=payload_body(rid,c)
                records[rid]={'text':export_exact(b,c),'mode':'exact'}
            else:
                for v in x.values(): prefix_walk(v)
    prefix_walk(compact)
    return records
```

### D.3 Admission compositions

The module below imports the content algorithms above as `B`. Its result record is an abstract admission result, not a trusted transport receipt or authority token.

```python
"""Storage-independent operation compositions for Blue Language 1.0.

These procedures compose the unchanged normative algorithms. Results are ordinary
semantic records, not authentication receipts or library-issued trust tickets.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
from algorithms import blue as B


@dataclass(frozen=True)
class AdmissionResult:
    blue_id: str
    original_blue_id: str
    goal: str
    exact_text: str
    canonical_text: str
    removed_fields: tuple[str, ...]
    dependency_records_json: str

    def dependency_responses(self) -> dict:
        """Return a defensive copy of the reference evidence carrier."""
        return json.loads(self.dependency_records_json)


def read_input(text, context, *, mode="source", format="json"):
    """Decode an explicitly selected input role; never guess a fallback role."""
    with B.error_scope(context, phase="parsing"):
        parsed = B.parse(text, format, context.limits)
    if mode == "source":
        return B.prepare_source(parsed, context)
    if mode == "canonical":
        return B.decode_canonical(parsed, context)
    B.require(mode in ("exact", "direct"), "InvalidOperation", "input role")
    return B.normalize(parsed, context, mode)


def admit_document(text, context, *, goal="value", mode="source", format="json"):
    """Construct or decode, validate, normalize permitted duplicates, and export.

    The context is an operation-local fixed environment. No persistent provider
    write occurs here. Authentication or reuse of this result is a host boundary.
    """
    try:
        with B.error_scope(context, "", "operation"):
            context.diagnostic_goal = goal
            exact = read_input(text, context, mode=mode, format=format)
            context.diagnostic_root = exact
            original_id = B.identity(exact)
            B.strict_certify(exact, context, goal)
            if mode == "source":
                exact, removed = B.omit_root_duplicates(exact, context)
            else:
                removed = ()
            if removed:
                B.strict_certify(exact, context, goal)
            exact_text = B.export_exact(exact, context)
            compact_text = B.canonical_export(exact, context)
            records = B.admitted_records(exact, context)
            return AdmissionResult(
                B.identity(exact), original_id, goal, exact_text, compact_text,
                tuple(removed),
                json.dumps(records, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False),
            )
    except RecursionError as error:
        raise B.Failure("OperationLimitExceeded", "recursion") from error


def admit_source(text, context, *, goal="value", format="json"):
    return admit_document(text, context, goal=goal, mode="source", format=format)


def admit_exact(text, context, *, goal="value", format="json"):
    return admit_document(text, context, goal=goal, mode="exact", format=format)


def admit_canonical(text, context, *, goal="value", format="json"):
    return admit_document(text, context, goal=goal, mode="canonical", format=format)


def admit_direct(text, context, *, goal="value", format="json"):
    return admit_document(text, context, goal=goal, mode="direct", format=format)
```

<a id="fixture-protocol"></a>
## Appendix E. Portable conformance-request protocol

A case is a JSON object containing a nonempty `id`, one `request`, and an `expected` result. Optional `description` is informative; optional `environment` supplies the selected aliases, exact evidence, declared definitions, and host-resource controls. Each input supplies original `text` plus its explicit format and operation role. The default input role is Source and the default presentation is JSON.

Unknown case fields, unsupported request names, unknown expectation fields, and invalid fixture environments are harness errors, not skipped successful tests. The case identifier never selects semantics. Core registry initialization uses Appendix B. `B` below is the algorithm module in Appendix D. The procedures define the complete closed request/response transport used by the portable corpus.

A fixture `identify` performs structural naming, not strict admission. Fixture `validate` exercises its specified certification composition. Separate admission and metadata tests establish the stronger public-admission contract; they must not be collapsed into structural-hash tests. Expected mappings compare asserted members, lists compare all positions and length, and scalar types compare exactly. A test report must state whether it ran complete outcomes or selected observations.

```python
def make_context(case):
    e=case.get('environment',{})
    lim=B.Limits(**e.get('limits',{}))
    c=B.initialize(registry(),e.get('provider',{}),e.get('aliases',{}))
    c.directive_aliases=dict(e.get('directiveAliases',{}))
    for d in e.get('definitions',[]):
        n=B.input_node(d['input'],c)
        if 'blueId' in d: B.require(B.identity(n)==d['blueId'],'FixtureEnvironmentError','definition identity')
        c.remember(n)
        if 'alias' in d:
            B.require(d['alias'] not in B.CORE,'FixtureEnvironmentError','core alias')
            c.aliases[d['alias']]=B.identity(n)
    c.limits=lim;c.work=0;c.demands=[]
    return c

def request(req,c):
    op=req['operation']
    def input_(key='input'): return B.input_node(req[key],c)
    if op=='preprocess':
        i=req['input'];s=B.preprocess(B.parse(i['text'],i.get('format','json'),c.limits),c)
        # Preprocessing may still contain Source controls; do not identify them as data.
        def show(x):
            if isinstance(x,(B.Node,B.Ref,B.Local)): return B.export_tree(x)
            if isinstance(x,list): return [show(a) for a in x]
            if isinstance(x,dict): return {k:show(v) for k,v in x.items()}
            return x
        return {'outcome':'Established','text':B.wire_text(show(s))}
    if op in ('identify','canonicalize'):
        n=input_();return {'outcome':'Established','blueId':B.identity(n),'text':B.export_exact(n,c)}
    if op=='validate':
        n=input_();B.certify(n,c,req.get('goal','value'))
        return {'outcome':'Established','valid':True,'blueId':B.identity(n)}
    if op in ('resolve','resolveLimited','resolveComplete'):
        n=input_();results=[]
        if op=='resolveComplete': B.certify(n,c,req.get('goal','value'))
        for q in req['queries']:
            results.append(B.outcome(lambda q=q:B.observe(n,q.get('path',''),q['query'],c)))
        return {'outcome':'Established','observations':results}
    if op=='subtype':
        a=input_('candidate');b=input_('parent');c.remember(a);c.remember(b)
        return {'outcome':'Established','subtype':B.check_subtype(B.identity(a),B.identity(b),c)}
    if op=='preserves':
        a=input_('candidate');b=input_('parent')
        B.certify(a,c,'definition');B.certify(b,c,'definition')
        return {'outcome':'Established','preserves':B.preserves_heads(B.head(B.recipe(a),c),B.head(B.recipe(b),c),c,check_type=False)}
    if op=='schemaRefine':
        a=input_('parent');b=input_('candidate')
        v=B.refine_schema(B.read_schema(a,c),B.read_schema(b,c),c)
        n=B.merge_schema_exact(a,b,c)
        return {'outcome':'Established','constraints':B.describe_constraints(v),'blueId':B.identity(n),'text':B.export_exact(n,c)}
    if op=='schemaConjoin':
        a=input_('left');b=input_('right')
        v=B.conjoin_schema(B.read_schema(a,c),B.read_schema(b,c))
        return {'outcome':'Established','constraints':B.describe_constraints(v)}
    if op=='fold':
        p=B.plain_id(req['prefix'])
        for item in req['suffix']:
            p=B.append_id(p,B.identity(B.input_node(item,c)))
        return {'outcome':'Established','blueId':p}
    if op=='verify':
        rid=B.final_id(req['blueId']);b=B.open_exact(B.Ref(rid),c)
        return {'outcome':'Established','blueId':rid,'bodyBlueId':B.identity(b)}
    if op in ('expand','collapse'):
        n=input_();out=(B.expand if op=='expand' else B.collapse)(n,req['paths'],c)
        return {'outcome':'Established','blueId':B.identity(out),'text':B.wire_text(B.export_tree(out))}
    if op=='lookupExact':
        n=input_();a=B.exact_at(n,B.path_parts(req['path']),c)
        if a is B.ABSENT: return {'outcome':'Absent'}
        if isinstance(a,(B.Node,B.Ref)): return {'outcome':'Established','blueId':B.identity(a)}
        if isinstance(a,tuple): return {'outcome':'Established','length':len(a)}
        return {'outcome':'Established','value':B.literal_output(a)}
    if op=='minimize':
        n=input_();text=B.minimize(n,c,req.get('goal','value'))
        again=B.prepare_source(B.parse(text,limits=c.limits),c)
        return {'outcome':'Established','text':text,'sameView':B.same_view(n,again,c),'blueId':B.identity(again),'originalBlueId':B.identity(n)}
    if op=='finalize':
        ns=[B.parse(d['text'],d.get('format','json'),c.limits) for d in req['documents']]
        z=B.finalize_set(ns,c)
        return {'outcome':'Established','master':z['master'],'blueIds':z['ids'],
                'proofText':B.wire_text({'members':[B.export_tree(n) for n in z['canonical']]}),
                'bodyTexts':[B.export_exact(n,c) for n in z['bodies']]}
    if op=='verifyMember':
        h=B.verify_member(req['blueId'],req['proof'],req.get('body'),c)
        return {'outcome':'Established','blueId':h.id,'bodyBlueId':B.identity(h.body)}
    if op=='roundtrip':
        n=input_();text=B.export_exact(n,c)
        m=B.normalize(B.parse(text,limits=c.limits),c)
        return {'outcome':'Established','blueId':B.identity(n),'reloadedBlueId':B.identity(m),'equal':B.identity(n)==B.identity(m)}
    raise B.Failure('UnknownFixtureOperation',op)

REQUEST_FIELDS = {
 'preprocess': ({'input'},set()),
 'identify': ({'input'},set()), 'canonicalize': ({'input'},set()),
 'validate': ({'input'},{'goal'}),
 'resolve': ({'input','queries'},set()),
 'resolveLimited': ({'input','queries'},set()),
 'resolveComplete': ({'input','queries'},{'goal'}),
 'subtype': ({'candidate','parent'},set()), 'preserves': ({'candidate','parent'},set()),
 'schemaRefine': ({'candidate','parent'},set()), 'schemaConjoin': ({'left','right'},set()),
 'fold': ({'prefix','suffix'},set()), 'verify': ({'blueId'},set()),
 'expand': ({'input','paths'},set()), 'collapse': ({'input','paths'},set()),
 'lookupExact': ({'input','path'},set()), 'minimize': ({'input'},{'goal'}),
 'finalize': ({'documents'},set()), 'verifyMember': ({'blueId','proof'},{'body'}),
 'roundtrip': ({'input'},set())
}

class FixtureError(Exception): pass

def strict_record(value, required, optional, label):
    if not isinstance(value,dict) or not required<=set(value) or set(value)-(required|optional):
        raise FixtureError(label+': invalid fields')

def check_input(value):
    strict_record(value,{'text'},{'mode','format'},'input')
    if not isinstance(value['text'],str) or value.get('mode','source') not in ('source','exact','direct') or value.get('format','json') not in ('json','yaml'):
        raise FixtureError('input: invalid role, format or text')

def check_fixture(case):
    strict_record(case,{'id','request','expected'},{'description','environment'},'case')
    if not isinstance(case['id'],str) or not case['id']: raise FixtureError('case id')
    r=case['request'];op=r.get('operation') if isinstance(r,dict) else None
    if op not in REQUEST_FIELDS: raise FixtureError('unknown fixture operation')
    required,optional=REQUEST_FIELDS[op]
    strict_record(r,required|{'operation'},optional,'request')
    for key in ('input','candidate','parent','left','right'):
        if key in r: check_input(r[key])
    for key in ('suffix','documents'):
        if key in r:
            if not isinstance(r[key],list): raise FixtureError(key+' must be a list')
            for a in r[key]: check_input(a)
    if 'goal' in r and r['goal'] not in ('definition','value'): raise FixtureError('goal')
    if 'queries' in r:
        if not isinstance(r['queries'],list): raise FixtureError('queries')
        for q in r['queries']:
            strict_record(q,{'query'},{'path'},'query')
            if q['query'] not in ('exactId','kind','type','value','constraints','keys','length','present','name','description'): raise FixtureError('query name')
            if not isinstance(q.get('path',''),str): raise FixtureError('query path')
    if 'paths' in r and (not isinstance(r['paths'],list) or not all(isinstance(p,str) for p in r['paths'])): raise FixtureError('paths')
    if 'path' in r and not isinstance(r['path'],str): raise FixtureError('path')
    if 'proof' in r and not isinstance(r['proof'],str): raise FixtureError('proof must be original JSON text')
    if 'body' in r and not isinstance(r['body'],str): raise FixtureError('body must be original exact JSON text')
    e=case.get('environment',{})
    strict_record(e,set(),{'limits','provider','aliases','definitions','directiveAliases'},'environment')
    for d in e.get('definitions',[]):
        strict_record(d,{'input'},{'alias','blueId'},'definition');check_input(d['input'])
    for v in e.get('provider',{}).values():
        if not isinstance(v,dict): raise FixtureError('provider response envelope')
        if 'outcome' in v:
            strict_record(v,{'outcome'},set(),'provider outcome')
            if v['outcome'] not in ('NotFound','Unavailable','InvalidEvidence'): raise FixtureError('provider outcome')
        elif 'proof' in v:
            strict_record(v,{'proof'},{'body'},'member response')
            if not isinstance(v['proof'],str) or 'body' in v and not isinstance(v['body'],str): raise FixtureError('proof/body text')
        else:
            strict_record(v,{'text'},{'format','mode','environment'},'provider text response')
    if not isinstance(case['expected'],dict) or case['expected'].get('outcome') not in ('Established','Absent','Incomplete','Invalid'):
        raise FixtureError('expected outcome')
    # These are result fields, not a catch-all implementation-specific expectation.
    allowed={'outcome','category','blueId','bodyBlueId','text','valid','observations','subtype','preserves','constraints','length','value','sameView','originalBlueId','master','blueIds','proofText','bodyTexts','reloadedBlueId','equal'}
    if set(case['expected'])-allowed: raise FixtureError('unknown expected field')

def execute(case):
    check_fixture(case)
    try:
        c=make_context(case)
    except (B.Failure,TypeError,ValueError) as e:
        raise FixtureError('environment setup: '+str(e)) from e
    result=B.outcome(lambda:request(case['request'],c))
    result['caseId']=case['id']
    return result

def match(actual,expected,path=''):
    if isinstance(expected,dict):
        if not isinstance(actual,dict): return [path+': object expected']
        out=[]
        for k,v in expected.items():
            if k not in actual: out.append(path+'/'+k+': absent')
            else: out.extend(match(actual[k],v,path+'/'+k))
        return out
    if isinstance(expected,list):
        if not isinstance(actual,list) or len(actual)!=len(expected): return [path+': list length/type']
        return [msg for i,(a,b) in enumerate(zip(actual,expected)) for msg in match(a,b,path+'/'+str(i))]
    return [] if type(actual)==type(expected) and actual==expected else [path+': '+repr(actual)+' != '+repr(expected)]
```

<a id="repository-carrier"></a>
## Appendix F. Exact repository carrier

This appendix fixes the integrity and evidence rules of the `blue-python-repository/1` carrier used by §18.11. It is an interoperable data carrier, not a requirement to use Python and not a separate Blue identity scheme. Its envelope checksum is the lowercase hexadecimal SHA-256 of UTF-8 JSON with keys ordered as Unicode scalar strings, no optional whitespace, unescaped non-ASCII scalar characters, and no nonfinite numeric values, after omitting the `identity` field. The checksum is prefixed by `sha256:`. This envelope encoding must not be substituted for the Language helper encoding when calculating a BlueId.

The envelope contains exactly `format`, `name`, `aliases`, `records`, `metadata`, and `identity`. `name` is a nonempty package/repository label. `aliases` maps strings to valid final identities; core names cannot be rebound. `records` maps final identities to declared exact bodies or owning-set proofs. A non-core alias needs its target record. A record cannot be accepted merely because its key has a valid identifier spelling. Each record is independently opened under the selected Language and verified against its key.

A Text record has `mode: "exact"`, `format: "json"` or `"yaml"`, and `text` containing the original body. A cyclic record contains the complete `proof` and may include a separately supplied `body`; its verification follows §12. Inline and referenced bodies use the same evidence rules. Metadata is non-authoritative carrier information unless separately committed by the package root. It must not install aliases or imply executable support.

Structural carrier verification is distinct from `audit`, which admits every exported target as a definition. A package processor also verifies the ordinary Package root, its documentary assets, semantic witnesses, and reachable-record agreement. No carrier checksum or audit count replaces those steps.

Implementations can transmit equivalent verified content using a different physical record carrier. A consumer that claims this particular envelope format must follow its exact checksum, required-key, alias, and record-verification rules.
