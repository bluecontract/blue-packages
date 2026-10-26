# Blue BEX 1.0

**Status: UNPUBLISHED working specification — staged result-value previews.**

**Normative form:** one complete specification with executable algorithm appendices

This candidate defines the corrected `$resultValue` behavior implemented in MyOS
Core. Its prose and six embedded executable modules are the authoritative source
for this candidate; the modules are extracted directly for its focused tests.
It is not selected by `blue-package.yaml` and has no assigned publication BlueId.
The existing final-gas publication, frozen sources, archives, manifests and pins
remain unchanged. Their sparse-overlay algorithms do not implement this candidate.
No runtime edition, dispatch selection, migration or account repinning is installed
by this source change. Publication and host adoption require separate review.

## Abstract

BEX is a deterministic expression and statement language encoded as Blue-compatible data. It evaluates against explicit inputs and produces a value, an ordered changeset, ordered events and a deterministic admitted gas total. BEX does not perform document mutation or select externally ordered inputs.

## Contents

- [1. Scope and conformance](#scope)
- [2. Exact dependencies and interpretation](#dependencies)
- [3. Purpose and imported language](#section-3)
- [4. Machine and invocation](#section-4)
- [5. Value domains and absence](#section-5)
- [6. Numeric and Text rules](#section-6)
- [7. Source classification and static positions](#section-7)
- [8. Evaluation order and laziness](#section-8)
- [9. Reads and observations](#section-9)
- [10. Pointers and ordered changesets](#section-10)
- [11. Collections](#section-11)
- [12. Variables, functions, and return](#section-12)
- [13. Effects and host intrinsics](#section-13)
- [14. Gas](#section-14)
- [15. Blue output boundary](#section-15)
- [16. Errors and determinism](#section-16)
- [17. Executable inventory and conformance](#section-17)
- [18. External capability boundary](#section-18)
- [19. Composition with Language and Contracts](#section-19)
- [20. Release and identity](#section-20)
- [21. Immutable host values](#section-21)
- [22. Shared host metering](#section-22)
- [23. Resource-proportional work accounting](#section-23)
- [24. Equality and conversion ordering](#section-24)
- [25. Occurrence and effect traversal](#section-25)
- [Appendix A. Complete operator reference](#operators)
- [Appendix B. Complete executable algorithms](#algorithms)

<a id="scope"></a>
## 1. Scope and conformance

This working specification defines the candidate protocol; no exact publication identity has been assigned. Its prose, tables and algorithm appendices form one normative contract. It is independent of source-repository branches, release tags, installation paths and prior discussions. Named external semantics are selected exactly in §2. Where an implementation uses another programming language, it MUST preserve the same specified observations; matching internal classes or diagnostic wording is not required unless explicitly identified as an observation.

**MUST** and **REQUIRED** express requirements. **MUST NOT** and **PROHIBITED** express prohibitions. **SHOULD** and **SHOULD NOT** express recommendations whose departures require understood consequences. **MAY** and **OPTIONAL** express permissions. Examples marked informative do not add requirements. A conflict between normative prose and algorithms is a defect, not permission to choose an outcome. A finite conformance corpus is evidence, not a proof for every possible input.

A package distributes this specification; it does not install a processor. The package's BlueId, this specification Text's BlueId and the OCI/archive digests identify different content. This document does not contain its own calculated identity or the generated identities of types that refer to it.

<a id="dependencies"></a>
## 2. Exact dependencies and interpretation

This edition selects Blue Language package `8XGYNufx24r7Dc5bGoeobcGNCn9roLzSfZCQyHBTaTx4`, whose complete specification Text is `H7WiYQ6GiWypRdFyWRcv99dsvTv6WnJYnu9eLYPQmWnc`. Node construction, exact references, specialization, output admission and BlueIds have the meaning defined by that Language release.

BEX is independent of Contracts. A host may supply Language-backed matching, node identity, finite reads and explicit intrinsics. Contracts is one such host and binds the supplied BEX context and meter according to its own specification. BEX MUST NOT substitute ambient state or an unversioned implementation for these declared interfaces.

Package imports supply exact content. Authoring prefixes are local bindings and do not leak through transitive imports. An imported definition retains its exact references. Mounting another package cannot change the selected interpreter or replace an existing type reference. Within this edition's interpreted package graph, the selected Language release MUST agree throughout; cross-Language conversion and mixed-rule cyclic sets are not defined. One selected Language governs a complete cyclic identity set and its owning proof.

<a id="section-3"></a>
## 3. Purpose and imported language

BEX evaluates data-encoded programs against explicit, read-only inputs and produces values, ordered changesets, and ordered events. It neither fetches arbitrary resources nor publishes a document. A Contracts processor decides whether proposed effects can be applied; Coordination determines which authenticated external input is eligible.

The reader is assumed to know Blue Language 1.0. Node admission, effective types, specialization, exact versus Source representations, references, set finalization, and BlueId are imported, not redefined. A BEX value is not a Blue node. In particular, Python object identity, dictionary iteration order, and native truth testing do not define BEX semantics.

The executable algorithm appendix contains the complete evaluator and host-value algorithms. Readable rules and executable algorithms together define this edition; disagreement is a defect, not permission to choose either result.

<a id="section-4"></a>
## 4. Machine and invocation

An invocation has a compiled program; an explicit context; a gas meter; lexical function frames; an ordered changeset; and an ordered event list. Context supplies the selected document snapshot, event, current contract, previous step results, named bindings, and executing scope. Optional adapters provide finite document reads, Blue specialization checks, and exact-type intrinsics.

No process-global variable is a program binding. No Python expression is evaluated from program text. The interpreter recognizes data forms, not Python, JavaScript, or embedded shell commands. An installed intrinsic is trusted host code and is outside that sandbox boundary.

A successful invocation returns `Result(value, changeset, events, gas_used)`. It does not apply its changes. Returned effects remain ordinary BEX values until the Contracts output boundary has validated and converted them.

<a id="section-5"></a>
## 5. Value domains and absence

The domains are undefined, null, Text, Integer, Double, Boolean, Object, and List. `UNDEFINED` is a singleton distinct from Python `None`, which represents internal BEX null. Boolean is not Integer. Objects have Text keys. Integers use exact integer arithmetic; Doubles use finite decimal observations and cross the Blue Double boundary as finite binary64 values.

Missing member lookup yields undefined. Undefined object members are omitted by Blue conversion. Undefined list elements, including sparse `$pointerSet` holes, cannot cross that boundary. Null is not an empty object and is rejected at the Blue output boundary. An actual empty object remains an actual empty object. `$emptyObject` is the explicit empty-object constructor.

`$exists` is false only for undefined. Null therefore exists. Truth is false for undefined, null, false, empty Text, empty Object, and empty List; other values are true, **including numeric zero**. `$empty` and `$isEmpty` test the inverse of this truth rule, not Python's truthiness.

<a id="section-6"></a>
## 6. Numeric and Text rules

Integer conversion accepts integers, integral finite numbers, and canonical decimal integer text. Fractional values and noncanonical integer spellings fail. Numeric conversion rejects Boolean, collections, nonfinite numbers, and malformed numeric text. Arithmetic operators in this edition produce exact Integer results, and division requires an exact Integer quotient. Division by zero or a fractional quotient fails.

Numeric equality compares numeric value across Integer and Double. Other equality is domain-sensitive and recursive. It must not be substituted for BlueId equality or Language specialization. Collections do not stringify implicitly. Null and undefined stringify to empty Text where coercion is allowed; names, paths, keys, and operation names require presence and cannot use that absence coercion.

Text-key ordering is Unicode code-point ordering. Gas size estimation counts UTF-16 code units, not Python string length or UTF-8 bytes. These are different operations and must remain separate. Nonfinite Doubles and lone Unicode surrogates are invalid runtime values at the relevant boundary.

There is no universal source-depth, call-frame, numeric-text, Integer-result-size or Blue-output Integer-length ceiling. Integer arithmetic, finite binary64 values, canonical text, static recursion rejection and output validity remain mandatory. A host that cannot compile or evaluate otherwise valid finite work reports operational incompleteness, not invalid syntax, a false arithmetic error or gas exhaustion. Gas is a logical work rule, not an operating-system resource sandbox. Large operand/allocation paths require correctly placed deterministic work charges and safe host isolation; a local machine failure cannot create a different semantic history.

<a id="section-7"></a>
## 7. Source classification and static positions

A single-key object whose key starts with `$` is an executable form when encountered in expression or statement position. It must name an installed operator valid for that position. Other objects are recursively evaluated data constructors. `$literal` prevents evaluation of its payload as program data, but does not authorize executable material in static Blue definition positions.

Type-related and schema positions are static. Constants and function-argument patterns are static. Compilation rejects unknown operators, invalid operand shapes, unknown variables/constants/functions, malformed static names, reserved user-container names, invalid call argument sets, and recursive function-call graphs. Both sides of a lazy runtime construct still undergo static validation.

A function body selects `expr` ahead of `do`. An explicit named entry must exist and take no arguments. The implementation also validates the root body even when a named entry is selected. Definition constants/functions can be supplied as an already available object to the compiler; loading a referenced program definition is a host integration obligation.

<a id="section-8"></a>
## 8. Evaluation order and laziness

Object constructors evaluate keys in deterministic order; lists evaluate left to right. Function arguments evaluate in key order. Lazy operators evaluate only the branch or subsequent operand needed to establish the result. This applies to Boolean connectives, coalescing/default selection, conditionals, and lookup defaults.

A static error in an unused branch is still an error. A runtime error or gas charge in an unselected branch does not occur. Empty or missing values cannot be replaced by Python idioms such as `value or fallback` unless they implement the particular BEX operator's rule.

<a id="section-9"></a>
## 9. Reads and observations

`$document`, `$event`, `$currentContract`, `$binding`, `$steps`, `$var`, and `$const` read only their designated source. A variable or constant name containing `/` remains a name; its optional pointer is a separate operand. A named step is addressed by the step's actual Language `name` label, not its list position when a name was supplied.

A Compute invocation sees a stable selected-document snapshot. A later Compute step sees effects successfully applied by earlier steps. `$resultValue` projects this invocation's accumulated changes in append order on its snapshot; it does not publish them. Finite managed-document reads use the closure's selected dependency projection, never an independently advancing source's latest public head.

The context's matcher implements `$is` using Blue semantic admission and specialization. The interpreter does not guess that a JSON shape is a valid Blue type. Missing patterns, unknown required definitions, and uninstalled matcher capabilities are not accepted as successful matches.

### Exact node identity

`$nodeBlueId: EXPR` evaluates EXPR once and returns a Text containing the ordinary
Language BlueId. Charge `nodeIdentityRequested = 5` after evaluating the operand
and before calling the host's Language identity boundary. The boundary shares
the invocation meter and cannot use a separate unmetered hash implementation.

An admitted exact host collection retains its selected exact identity, including
owning-set member identity, without expanding its descendants. A newly computed
value passes the existing strict Blue-output validation and Language Exact
admission/identity construction. Newly built containers preserve exact nested
operands and their identity evidence; storage presentation cannot change charges. Null or undefined roots, malformed references,
invalid type slots and incomplete owning-set evidence fail; missing required
content is not replaced by an invented identity. Scalars are ordinary BEX scalar
values and receive their corresponding Language scalar identity; metadata erased
by scalar observation is not reconstructed. Equality and type specialization
remain different operations from exact identity comparison.

The standard Contracts context installs this boundary. Standalone BEX hosts
supply `Context.node_blue_id(value, gas)` backed by the same Language operations;
without it the operator fails with a boundary error. It does not perform network
lookup or register user code. `processingEvent` remains a Contracts binding read
through `$binding`; no `$processingEvent` operator is introduced.

<a id="section-10"></a>
## 10. Pointers and ordered changesets

BEX value pointers use JSON-pointer escaping. Both empty Text and `/` designate the value root in this profile. This differs from the Language query API's empty-key behavior; adapters must not delegate blindly. Relative document paths resolve against the executing scope; already absolute document paths remain absolute. A Contracts processor separately checks whether a proposed absolute path is writable by that scope.

A changeset is an ordered list of add, replace, or remove proposals. Non-remove proposals require a value. Remove ignores no hidden expression: its value operand is not evaluated by the append operation. Appending preserves duplicate operations and their order.

`$resultValue` projects ordered structural List patches. `add` inserts before
an existing index or appends at the current length or `-`. `remove` deletes an
existing element and shifts later indices down by one. `replace` requires an
existing index and replaces that element without shifting. Numeric indices use
canonical nonnegative decimal syntax (`0` or a nonzero digit followed by digits).
Negative indices, leading zeros and out-of-bounds positions fail when projected.
`-` is permitted only for `add` at the final path segment; intermediate List
segments require existing elements. Every patch uses the structure left by its
predecessors, including changed lengths. Duplicate operations remain distinct.

For example, two `remove /queue/0` proposals on `[A, B, C, D, E]` make
`$resultValue: /queue/0` return `C`, and `/queue` return `[C, D, E]`.
A missing read still yields undefined and cannot supply an add/replace value.
Object overlay behavior, including missing-parent construction, is unchanged.
`$pointerSet` retains assignment/sparse-List semantics: removal leaves an undefined
position and does not shift later elements. Such a sparse value can be observed
internally but cannot cross the Blue List output boundary.

This projection is not Contracts mutation. It does not publish, generalize,
validate every native object rule or invoke Document Update reactions. For a
valid changeset on the same starting value, its structural List result matches
native application when no additional reactions intervene. An explicit returned
`changeset` can replace accumulated proposals without changing this preview;
reactions can change the next Compute's actual document. Neither is simulated.
`$document` remains the current Compute's starting snapshot.


Each invocation lazily maintains a projected root and an applied-patch cursor for
each selected starting view (`canonical` and `resolved`). Reads project only the
newly appended suffix; repeated reads without new patches do no projection work.
Functions share the invocation's accumulator and projected state. Appending alone
does not project a patch, and an unexecuted read does no projection work. State
MUST NOT be shared between invocations. Previously exposed roots and descendants
remain unchanged when later patches copy their path containers; untouched
subtrees, including captured host values, remain shared. Replacement-value copying
retains the existing overlay rule.

Every executed read still pays `resultValueRead` and, after successful projection,
performs its requested lookup through the configured host document reader (or the
ordinary pointer lookup if no reader is configured). Caching does not waive
missing capabilities, resource failures or demanded host logical-read obligations.
The resolved view still requires its supplied snapshot. This candidate installs
no definition-view capability; an independently installed host extension must not
interpret staged state as the starting-document definition.

<a id="section-11"></a>
## 11. Collections

Collection operations support Lists in index order and Objects in sorted key order. Query bindings are lexical for that query and are restored afterward. Statement `forEach` uses its declared iteration slots and executes its body for each selected item. An empty collection executes no iteration body.

Map and flat-map produce Lists; flat-map requires a List result per item. Filter preserves the input's collection category. Reduce threads its accumulator. Some, find, and find-entry stop after the first decisive match. Find-entry preserves the selected value and occurrence information rather than replacing occurrence identity with value identity.

Iteration gas is charged for each admitted visited item. Short-circuiting stops both later evaluation and later iteration charges. Collection construction retains its specified logical charges. Host memory/cancellation controls are operational and may interrupt without establishing a semantic rejection; they are not universal collection-size restrictions.

<a id="section-12"></a>
## 12. Variables, functions, and return

`let` declares function-frame slots. Parallel declarations evaluate their initializers against the old frame; an explicit declaration order enables ordered dependency between initializers. `set` updates an existing declared slot. Conditional declaration visibility is checked statically.

Function calls use isolated frames, exact declared argument-name sets, and supplied Blue argument-pattern checks. Functions share the invocation's effect accumulators and gas meter but do not implicitly capture another function's locals. Recursion is rejected during compilation. Business-process cycles therefore arise from Contracts event work, not recursive BEX function calls.

Explicit return exits the current function/body. Without an explicit result, the interpreter returns the accumulated changeset and events. A called function's return does not terminate its caller. Failure exits the invocation and does not authorize partial publication.

<a id="section-13"></a>
## 13. Effects and host intrinsics

Event append preserves multiplicity. Two equal event values are two emission occurrences; their BlueIds may be equal. Occurrence identity belongs to the hosting Contracts closure. The BEX interpreter does not deduplicate by content identity.

An intrinsic must have an exact static type ID present in the invocation's installed capability registry. Unknown IDs fail compilation. Runtime removal of a capability fails execution. Intrinsics receive copied explicit operands and the same gas meter; they must return explicit BEX values and account for bounded work. Files, network, clock, and randomness are not implicit capabilities.

<a id="section-14"></a>
## 14. Gas

Compilation consumes no semantic gas. Each admitted expression, statement, read, call, pointer operation, collection item, append, and size-dependent operation is charged by the algorithm at its specified point. A failed charge is recorded as rejected work and does not increment admitted `used` gas.

Accepted charges update the running scalar only. They have no canonical rows, ordinals or transcript. Results contain `gas_used`, not `gas_trace`. The default standalone allowance remains 10,000,000. A caller-supplied shared meter is never reset; each invocation reports its own admitted contribution. Local counters and the shared total still enforce each charge before work. Retain only the first rejected charge, without a charge ordinal; a failed meter cannot resume accepting work. Optional debug traces are noncanonical, off by default, and never required for conformance, replay or durable publication. A compatibility API may expose an empty trace accessor, but this is not a result field in this candidate.

This candidate retains scalar metering from final gas. Earlier publications keep their original metering and conformance rules. This source does not replace their identities or select new rules for historical replay.

The default scalar tariffs are: expression 1; statement 1; document read 2; event/current-contract/steps/variable read 1; result-value read 2; pointer get base 1; pointer set base 3; object set base 2; append-change/event base 5; iteration item 1; function call 2. Size/path contributions are defined by the algorithms, not by wall-clock time.

A Compute step can impose a positive local cap while charging each admitted operation to a shared Contracts closure meter. A local-cap rejection is distinguished from shared-cap rejection in the first-rejected-charge diagnostic. A cap is checked before work is admitted. Gas allowance, used gas, attempted rejected charge, and operational cancellation are different values.

The charge positions and tariffs in the executable annex define this edition. A conforming implementation preserves the deterministic admitted gas total and first rejected charge for identical inputs. Equivalence to a different BEX release or another tariff is a separate interoperability claim, not an additional unstated rule.

<a id="section-15"></a>
## 15. Blue output boundary

`blue_value` converts runtime values into a JSON-compatible, null-free proposal. It is not semantic admission and does not return a BlueId. Authoring aliases are resolved in an explicit authoring/preparation stage before this proposal enters the runtime output boundary. Runtime type slots MUST contain exact Blue references. The host admits the proposal through Language Exact admission and uses the resulting validated exact value; it MUST NOT resolve aliases, replay Source list construction, or reinterpret a generated string as an installed type at this stage. A BEX program may compute arbitrary Text, but a Text in a runtime type slot is not thereby a type reference. A host accepting raw data-encoded programs with unresolved literal type aliases must reject the resulting effect, not silently reinterpret it.

The corrected boundary does not collapse null to `{}`. A whole null event or null patch value fails. Undefined object members may disappear, but required fields must still satisfy the host effect schema. Effect structural validation precedes mutation, so a later malformed effect cannot cause an earlier effect to be published.

<a id="section-16"></a>
## 16. Errors and determinism

Compilation error, runtime error, invalid Blue output, actual gas exhaustion and host/incomplete execution are distinct failure families. The former portable resource caps are removed. Resource exceptions must propagate as incomplete host work, not be wrapped into ordinary BEX runtime failure and terminally rejected by a feeder. A caller may not turn an unavailable required Language definition or provider proof into a successful computation. A runtime exception never means "no changes" success.

Determinism requires identical admitted inputs, program and definitions, installed capabilities, matcher behavior, selected document projection, and gas schedule. Python hash seed, input-map insertion order, cached parsing, and unrelated documents must not affect the semantic result. Stateful or nondeterministic intrinsics violate this requirement unless their observations are explicit frozen inputs.

<a id="section-17"></a>
## 17. Executable inventory and conformance

the operator appendix lists every installed expression and statement operator. The complete annex supplies their compilation, evaluation, value and gas definitions. Each marked module is extracted without modification. The source table in this specification identifies the exact modules and their dependencies.

Conformance preserves successful results, ordered proposals, short-circuit behavior, static errors, runtime errors, output-boundary errors and gas observations. Required cases include Boolean/Integer distinction; undefined/null/empty-object distinctions; exact arithmetic; type-pattern matching; every operator family; function scope; side-effect order; Unicode ordering and size; output rejection; and local/shared gas limits. Passing a finite corpus is evidence, not a proof for all programs or capabilities.

<a id="section-18"></a>
## 18. External capability boundary

The standard algorithms require no arbitrary external I/O. A host supplies explicit document projections, a Language-backed matcher, and any selected intrinsic registry. A missing required capability or exact definition cannot be converted to successful evaluation. Intrinsics are trusted, explicitly installed code with their own semantics and bounded work; an unknown intrinsic ID is rejected.

This edition defines no production network acquisition service, operating-system sandbox, universal intrinsic package or Java diagnostic mapping. An independent implementation conforms to this edition by preserving its specified results, not by reproducing an undocumented behavior of another runtime. Host memory protection and process isolation remain operational obligations; they cannot change the semantic outcome of an admitted computation.

<a id="section-19"></a>
## 19. Composition with Language and Contracts

User-binding declarations are constants, functions, function arguments, local `$let` slots (both forms), and collection/loop item, key, index and accumulator slots. All reject the reserved names listed by `compiler.RESERVED`, including `$previousItems`. Ordinary literal object keys and host-provided read bindings are not user-binding declarations. `$previousItems` is a reserved Language name in BEX user-binding containers. It is not a BEX instruction and cannot manufacture Language list inheritance at runtime. `$previous` and other Source-only controls likewise do not replace Exact admission of effects.

An unevaluated object containing dynamic expression fields is not an instance of its eventual result type. A repository can author that value through ordinary BEX `$objectFromEntries` construction with exact type references. Resulting events and patch values are admitted only after evaluation. Rewriting a program changes its identity and may change its gas; this does not weaken Language validation.

The Contracts invocation supplies the selected executing document as the BEX document. BEX receives no ambient enclosing process or independently advancing public head. Contracts owns mutation boundaries, internal event occurrence identities, initialization, termination, checkpoint settlement, graph finalization and publication. BEX returns proposed effects and never advances those states itself.

The standard Contracts binding uses its contextual business-value document projection for both `canonical` and `resolved` BEX read modes. This is an explicit Contracts binding, not a redefinition of the Language serialization APIs. Configured program data is distinct from effective business values: inherited specification prose must not be inserted into a literal program or effect.

<a id="section-20"></a>
## 20. Release and identity

The complete specification comprises its readable rules, operator reference, executable algorithms and explicit dependency selection. Its BlueId names that exact Text. The publication manifest records its identity outside the Text, avoiding a self-reference. A normative change creates a new exact specification identity. Test reports, implementation-only packaging, tutorials and provenance notes do not silently amend this edition.


<a id="section-21"></a>
## 21. Immutable host values

The numeric, equality, binding and control semantics are those defined in this specification. A trusted host may supply immutable collections implementing the host-value interface in values.py. Collection kind, keys, reads, variables, function arguments and persistent overlays operate on these values without eager recursive cloning. Output conversion uses the host's finite exact representation. The host must bind coherent resolution and meter demanded work. `$fail` and `$failIf` expose the distinct EXECUTION_REJECTED diagnostic so a host can classify explicit business rejection without treating every BEX error as a user refusal. Arithmetic and control tariffs are defined by the executable gas module.

Collection equality keeps its ordered short-circuit comparisons. A host can provide a stable comparison key for an exact effective recipe in its captured context. Repeated pairs in a cyclic comparison need not be unfolded again; unrelated fields and unequal pairs remain observable. Equality must not eagerly read the remaining values after a decisive mismatch.

<a id="section-22"></a>
## 22. Shared host metering

When invoked by Contracts, BEX uses the same bounded meter: **10,000,000 maximum/default** for the complete Contracts attempt, with supported stricter local limits. No BEX frame, intrinsic, compiled-program cache or lower standalone-Gas setting can detach from or reset the parent meter. Standalone BEX API budget configuration remains a separate API contract; it cannot enlarge the standard Contracts allowance.

Work charges apply independently of physical resource controls. Conversion, Integer arithmetic, collections, strings and output sizing use the exact counters, quantities and charge positions defined here. Implementations MUST NOT substitute after-the-fact bit-length caps or wall-clock timeouts for the specified meter. Any changed tariff requires a separately identified specification and conformance vectors. Preserve ordinary validation failure order and short-circuit behavior; no charges execute in an unselected branch.

Compiler structure checks remain semantically complete, including unused branches and forbidden recursive functions. Compilation still consumes no BEX semantic gas under this schedule; any inability to finish compilation is a prerequisite/host failure, not a fabricated failed debit. This rule neither exempts the containing Contracts work from its existing charges nor makes first-time authoring free in physical resources.

<a id="section-23"></a>
## 23. Resource-proportional work accounting

Contracts continues to supply one shared meter with a maximum of 10000000. BEX
compilation and host prerequisite acquisition are outside that invocation meter.
A host interruption is incomplete execution, never a BEX semantic rejection.

Three additional BEX counters have unit weight 1: `integerWork`, `textWork`, and
`valueMember`. They are charged to the current invoking member before their
corresponding work. Let L(n) = max(1, ceil(bit_length(abs(n))/32)). Addition and
subtraction debit max(L(a),L(b)); multiplication debits L(a)*L(b); division debits
2*L(a)*L(b), before the zero/exact-division check and arithmetic. A conversion
from Integer to decimal Text/Double debits L(n)^2 before conversion. Conversion
from decimal Text to Integer uses max(1,ceil(4*digitCount/32))^2; decimal numeric
values use their coefficient digits plus positive decimal exponent. Text syntax
inspection also debits ceil(codePointCount/64) `textWork` before scanning. An
Integer already represented as Integer needs no conversion debit.

Runtime values are immutable during evaluation: literal reads, variable reads,
function arguments and results share values; operators never mutate them. Program
input and public Result defensive copies are physical boundary work. Explicit
collection construction and snapshots of the accumulating `$changeset`/`$events`
debit one `valueMember` per member before allocation.
Comparison debits one `valueMember` per visited pair before inspecting it. Immutable
host views are retained without traversing their descendants; their actual reads
remain charged by the owning host. Text traversal/construction debits `textWork`
per at-most-64-code-point block; Integer comparison debits the sum of operand
limbs. Equality visits pairs in order and stops on the first mismatch. Concatenation
and split debit their known input/output-bound text blocks before allocation;
collection concatenation/merge debit each copied member before insertion.

Staged projection retains the existing ordered-key/member/text charges for each
copied object. Each List copy charges `valueMember` for its current length before
reading or copying its elements. There is no new patch tariff. Each newly appended
patch is projected at most once per selected view; unaffected reads do not repeat
these copy charges. Existing expression, statement, read and append charges remain.
Removing repeated projection work and changing List lengths can change admitted
gas totals and receipts. No historical-gas or receipt equality is promised for
affected programs. Scalar metering and shared/local ceilings remain as specified.

Specified size-dependent effect/overlay charges retain their base and size
formula, but debit the base first and then each visited size contribution before
traversing that contribution. Scalars use the existing UTF-16 size definition;
Integer decimal conversion is precharged as above. No whole recursive output
walk precedes a single future debit. Exact host transfer uses its canonical accounting form defined below,
independent of inline/reference materialization; it does not expand untouched bodies. A rejected debit is never admitted;
the first failed debit and its complete arbitrary-precision quantity are retained.
Diagnostic size is not saturated. The admitted gas total and first rejected charge are observable results of this schedule; accepted-charge history is not retained.


<a id="section-24"></a>
## 24. Equality and conversion ordering

All equality callers, including `$eq`, `$ne` and `$includes`, use the same
numeric-coercing comparator. Visit object members in Unicode code-point key
order, independently of native insertion order, host enumeration order or Python
hash seed. List order is unchanged. Compare the key inventories before child
values; then stop at the first unequal child. Only active-ancestry cyclic pairs are suppressed, never completed acyclic pairs.
Integer/Double numeric equality is unchanged.

For each object operand, left then right, let n be its exact key count,
r = ceil(log2(n)) for n > 0, otherwise 0, and
b = sum(ceil(codePointCount(key)/64)) over its keys. Debit `valueMember` n before
allocating/enumerating its key inventory; debit `valueMember` n*r and `textWork`
b*(r+1) before sorting or comparing the keys. Sort ascending by Unicode code
points. These prepaid deterministic envelope quantities cover key enumeration,
ordering and key comparisons, not the implementation's actual sort comparison
count. Zero-quantity calls preserve charge ordering and failure checks without creating trace entries. Existing per-pair,
Integer-limb and Text-block comparisons then apply to selected children only.
No descendant value is materialized to sort keys. Lazy host metadata/access
retains its host charges; BEX does not synthesize another host read charge.

`$unwrap` first evaluates its operand under ordinary expression accounting.
Before **each** candidate inspection, including the final non-wrapper candidate,
debit one `valueMember` (weight 1). Then determine its runtime kind. If it is not
an object, return it. Otherwise read `value` exactly once; if absent/undefined,
return the object; if present, continue with that member. Thus d wrappers ending
in a scalar pay d+1 inspections; even a non-wrapper or absent-value object pays
one. There is no absolute-depth multiplier, and no kind inspection or member
read may occur after its debit is rejected. Actual lazy host reads retain their
own charges, once per lookup. Native runtime wrapper objects need not themselves
be admissible Blue scalar documents; the Language output boundary is unchanged.

Both corrections use the existing weight-1 counters and invoking owner, shared
meter and local-before-shared cap precedence. Rejection preserves the admitted
gas total and exact first unaffordable charge. Host interruption is incomplete work,
not an invented completed rejection. A 10000000 allowance is not a time/RAM bound.


<a id="section-25"></a>
## 25. Occurrence and effect traversal

For every equality caller, the pair inventory is the **active ancestry**, not a
memo of completed comparisons. Pay `valueMember` for the pair before inspecting
its kinds or detecting a backedge. Retire its key when its child iterator ends.
Native handles and supported host `comparison_key()` values implement ancestry
only; physical sharing never omits charges for another acyclic occurrence.
Lists visit ascending indices; object equality retains the preceding prepaid
key-inventory rule. Numeric coercion and first-unequal short-circuiting remain.

All finite output sizing uses the same ordered `size_parts` walk. Admit the
caller's effect base (including any pointer-segment quantity) first. For a list,
yield its item count to the effect counter before requesting the first item;
visit children in index order. For an object, yield its direct member count,
then prepay `ordered_keys`: `valueMember=n` before key enumeration,
`valueMember=n*r` and `textWork=(r+1)*sum(ceil(keyCodePoints/64))` before sorting,
where `r=ceil(log2(n))`, or zero for an empty object. Use Unicode code-point key
order. For each sorted key, debit `textWork=ceil(keyCodePoints/64)` before computing
and yielding its UTF-16 length. Only after these key fragments have been paid
request each child, in that same order. Do not materialize descendants to size
the parent. Zero quantities follow the scalar metering rules and create no accepted-charge history.

Undefined/null contribute no scalar fragment. For an Integer, debit
`integerWork=max(1,ceil(bitLength(abs(value))/32))^2` before decimal conversion.
Render other supported scalar values by the existing rule; debit
`textWork=ceil(renderedCodePoints/64)` before UTF-16 encoding and yield
`max(1,renderedUTF16Length)`. The caller admits each yielded effect quantity
before requesting the next fragment. Thus key-order blocks are code-point based,
while effect size remains UTF-16 based. Ownership and shared/local cap precedence
come from the calling meter. Rejection stops this walk at that exact debit;
no subsequent lookup, conversion or encoding is permitted.

A supported host value exposes `accounting_view()`, a finite metering form.
The default delegates to `output_view()` (which defaults to the value itself).
Generic host collections keep ordinary finite traversal; implementing HostValue,
containing a `blueId` key, or being present in a physical cache is not evidence
of an exact value. This method affects **only sizing**: kind, keys, field reads,
equality, returned values, and `blue_output()` retain their existing semantics.

A host that supplies a complete, captured, identity-bound exact node MUST return
`{"blueId": exactIdentity}` for its accounting form, equally for inline and
referenced materialization. The host defines and verifies the necessary admission,
identity and owning-set evidence. It must not manufacture an identity by freely
hashing an unknown value. If composing an exact value requires new construction,
the owning host must admit its prescribed construction charges before that work
and before returning the token. Literal metadata and a raw `items` sequence slot
are not independent referenceable nodes. Scalar runtime values retain their
ordinary BEX size rules.

Sizing recursively uses this rule for each host child of a newly constructed
native object or list. Charge the new enclosing structure normally; transfer each
established exact child by its token. The rule covers every caller of `sized`,
including all singular/plural append effects, object/pointer setting, pending
result overlays and retained effect snapshots. Multiplicity and order remain
unchanged; equal emitted values are distinct occurrences. Ordinary demanded
host reads and transformations remain charged. Target-context validation and
retention of required exact content/proofs remain obligations of the owning host.

For a token with an ASCII identity of length `d`, the size fragments are
`1, 6, d` (object member, `blueId`, identity). Between fragments use the ordinary
object rule: `valueMember=1`, `valueMember=0`, `textWork=1` for key ordering,
`textWork=1` before encoding `blueId`, and `textWork=ceil(d/64)` before encoding
the identity. For `d=44`, an append's sizing cost is independently derived as
base `5` + fragments `51` + member work `1` + text work `3` = **60**.
This excludes expression, read, effect-snapshot and owning host costs. Admit
every row at its normal position; rejection stops before the guarded operation,
with owner, quantity and remaining local/shared allowance preserved.

The same prepaid `ordered_keys` helper is used when copying an object spine for
`$pointerSet` or pending `$resultValue` overlays, `$objectSet`, and each operand
of `$objectMerge`. List spine copies retain their prepaid item counts. Collection
queries, `$keys`, `$entries`, ordinary expression fields and simultaneous `$let`
bindings already use sorted keys; function argument-pattern checks also use
code-point key order. Ordered statement lists, explicit `$let.order`, effect
occurrences and list indices retain their authored order. Boundary defensive
copies and explicit `blue_output()` serialization are not substitutes for these
metered execution walks.

Descendant identity evidence is independent of materialization and transport. The accounting-view algorithm applies to captured exact host values. A host must establish any claimed identity evidence using its selected Language rules; the Contracts specification defines its own derivation boundary.
<a id="operators"></a>
## Appendix A. Complete operator reference



This is the normative operator inventory implemented by the accompanying compiler and runtime. The main sections define value distinctions, effect boundaries and limitations; every executable branch is included in the executable algorithm appendix. The inventory test checks that this reference names all 72 expression and 13 statement operators. An operator present in both positions counts in both inventories.

An executable form is a one-key object whose key begins with `$`. The operand shape below appears as its value. `E` means an expression, `[E…]` an ordered operand list, and `name` a static Text identifier. `{field?: E}` denotes an optional operand field, not literal BEX syntax. Do not interpolate expressions into static Blue type positions. `$literal` protects data from evaluation but does not bypass static-position admission.

### Scalar, value and collection expressions

| Operators | Operand | Delivered behavior |
|---|---|---|
| `$literal` | any admitted data | Return an unevaluated copy. |
| `$null`, `$emptyObject`, `$emptyList` | ignored literal operand | Return distinct null, object or list values. |
| `$changeset`, `$events` | ignored literal operand | Copy the current ordered accumulator. |
| `$unwrap`, `$kind` | `E` | Unwrap scalar `value` observations or report the runtime kind. |
| `$text`, `$integer`, `$number`, `$boolean`, `$object`, `$list` | `E` | Explicit conversions with the value/error rules in `values.py`. Integer conversion is exact. |
| `$not`, `$truthy`, `$empty`, `$isEmpty` | `E` | BEX truthiness, not Python truthiness. In this edition `empty` and `isEmpty` negate truthiness. Integer zero is truthy. |
| `$exists` | `E` | Test against undefined; null still exists. |
| `$keys`, `$entries` | `E` | Sorted object keys or `{key,val}` rows; non-objects produce an empty list. |
| `$size` | `E` | Object/list cardinality, zero for undefined/null, one for other scalar values; not Text character length. |
| `$objectFromEntries` | `E` | Construct an object from entry rows, validating keys. |
| `$concat` | `[E…]` | Concatenate Text conversions. |
| `$pointerJoin` | `[E…]` | Escape Text segments into a JSON Pointer. |
| `$startsWith`, `$sliceAfter` | `[E,E]` | Prefix check or suffix after an actual prefix; missing prefix gives empty Text. |
| `$eq`, `$ne` | `[E,E]` | Numeric-value equality across Integer/Double; otherwise domain-sensitive structural equality, and its negation. |
| `$gt`, `$gte`, `$lt`, `$lte` | `[E,E]` | Numeric comparisons after explicit numeric observation. |
| `$add`, `$subtract`, `$multiply`, `$divide` | nonempty `[E…]` | Left-to-right exact Integer arithmetic; fractional division and zero divisors fail. |
| `$and`, `$or` | `[E…]` | Lazy Boolean truthiness reduction. |
| `$coalesce`, `$default` | `[E…]` | Lazy first-truthy selection in this edition, not a Python `or` or JavaScript null-only assumption. |
| `$listConcat`, `$merge` | `[E…]` | Concatenate lists; shallow merge objects in operand order. |
| `$choose` | `{cond:E,then:E,else?:E}` | Evaluate only the selected branch; absent else is undefined. |
| `$join` | `{list:E,separator:E}` | Join a list using Text conversion. |
| `$split` | `{text:E,separator:E,limit?:E}` | Literal-separator split; empty separator/invalid limit fail. |
| `$listGet` | `{list:E,index:E,default?:E}` | Nonnegative indexed lookup; default is lazy and only evaluated when out of range. |
| `$get`, `$hasKey` | `{object:E,key:E}` | Object lookup or defined-key presence. |
| `$objectSet` | `{object:E,key:E,val:E}` | Copy-on-write; undefined removes the key. |
| `$pointerGet` | `{object:E,path:E,default?:E}` | Pointer lookup with lazy missing default. |
| `$pointerSet` | `{object:E,path:E,op?:E,val?:E}` | Copy-on-write `set`/`remove` overlay. List positions do not shift. |
| `$includes` | `{list:E,val:E}` | Ordered search using the same equality as `$eq` (including Integer/Double numeric equality), charging each visited element. |

### Context, calls and patterns

| Operators | Operand | Delivered behavior |
|---|---|---|
| `$var`, `$const` | `name` or `{name,path?:E}` | Frame or constant lookup; names must be known at compilation. |
| `$document`, `$resultValue` | path expression or `{path?:E,view?:E}` | Stable document view or ordered staged projection with structural List patches. The Contracts host applies patches separately. |
| `$event`, `$currentContract` | path expression or `{path?:E}` | Read the selected event or executing contract. |
| `$binding` | name/path Text or `{name?:E,path?:E}` | Read a provided binding. |
| `$steps` | step/path Text or `{step?:E,path?:E}` | Read a named earlier step result. |
| `$is` | `{node:E,pattern:static}` | Delegate semantic matching to the installed Language matcher; missing capability fails. |
| `$isKind` | `{val:E,kind:static}` | Compare to one kind or a list of kinds. |
| `$call` | `{function:name,args?:{name:E…}}` | Call a statically known, nonrecursive function with an exact argument set. |
| `$intrinsic` | `{type:{blueId:static},…}` | Invoke an explicitly installed exact-type host intrinsic. The default managed host does not authorize arbitrary custom intrinsics. |

### Collection expressions

All take `in`, a static `item` binding, optional static `key` and `index` bindings, and the body listed below. Lists traverse in index order; objects traverse keys in Unicode code-point order. Temporary query bindings are restored after the expression. A visit charges semantic gas even when the predicate rejects it.

| Operators | Additional operands | Delivered behavior |
|---|---|---|
| `$map`, `$flatMap` | `expr:E` | Produce a list of mapped values or concatenate mapped lists. |
| `$filter` | `where:E` | Preserve matching list elements or object entries. |
| `$reduce` | `acc:name,init:E,expr:E` | Ordered accumulator reduction. |
| `$some`, `$find`, `$findEntry` | `where:E` | Stop at the first truthy predicate; return Boolean, original element, or element/index/key information. |

### Statements

A `do` block is an ordered list of statement objects. Local functions are statically acyclic; document/event reaction cycles belong to Contracts/Coordination and are separately gas-bounded.

| Operators | Operand | Delivered behavior |
|---|---|---|
| `$let` | `{name,expr:E}` or `{vars:{name:E…},order?:[name…]}` | Declare frame slots. Explicit order permits ordered dependency; without it initializers use the prior frame. |
| `$set` | `{name,expr:E}` | Assign a previously declared slot. |
| `$if` | `{cond:E,then?:[statements],else?:[statements]}` | Execute the selected block. |
| `$forEach` | `{in:E,item:name,do:[statements],key?:name,index?:name}` | Ordered statement iteration with item charging. |
| `$appendChange` | `{op:E,path:E,val?:E}` | Append one validated `add`/`replace`/`remove` proposal. |
| `$appendChanges` | `E` | Append a list of proposals in order. |
| `$appendEvent`, `$appendEvents` | `E` | Append one event or an ordered list. |
| `$call` | `{function:name,args?:{name:E…}}` | Execute a known function for its effects. |
| `$return` | `E` or null | Return a value; null operand selects the default accumulator result. |
| `$returnIf` | `{cond:E,expr?:E}` | Conditional return; absent expression selects the default result. |
| `$fail` | `E` or `{message:E}` | Raise an execution failure with a message. |
| `$failIf` | `{cond:E,message?:E}` | Conditional execution failure. |

### Host-independent behavior

Undefined is a dedicated singleton, never Python `None`. An effect may use an explicit empty object, but a null effect value cannot be admitted as a Blue child. Native Python truthiness, Boolean-as-Integer behavior, hash iteration order and float rendering must not define the semantics by accident. Gas text sizes use the declared UTF-16 observation; object order uses the specified key ordering instead.

There are no universal source-depth, call-frame, numeric-size or Blue-adapter Integer-size limits. Actual arithmetic, static recursion, exact numeric/Unicode formats and explicit program constraints remain. Implementations must distinguish incomplete host execution from a semantic error and implement the selected deterministic charges. A registered host intrinsic is trusted host code: semantic gas alone is not a CPU/memory/security sandbox. Conformance is to this edition: compare result, error, evaluation order, deterministic admitted gas total and first rejected charge. No implementation may override the selected specification based solely on its own observed result.

### `$nodeBlueId`

Operand: one expression. Result: ordinary Language BlueId as Text. The expression
is evaluated once, then the identity request costs 5 gas plus the Language work
required by the selected exact/transient operand. A host Language identity
boundary is required; invalid or unavailable exact evidence fails without effects.
The exact-node-identity rules apply. Example:

```yaml
expr:
  $nodeBlueId:
    $document: /selected/type
```

<a id="algorithms"></a>
## Appendix B. Complete executable algorithms

The following module blocks define this edition's reference procedures. File names identify modules within the abstract reference system; they are not external normative downloads. The selected Language and BEX operations have the exact bindings in §2. The host-value module is included where used.

### `src/blue_bex/__init__.py`

```python
from .compiler import Compiler, Program, EXPR, STMT
from .runtime import Engine, Context, Result
from .gas import Gas, GasExhausted, DEFAULT
from .values import UNDEFINED, BexError, CompileError, BoundaryError, ResourceError, blue_value
__all__=['Engine','Context','Result','Compiler','Program','Gas','GasExhausted','DEFAULT','UNDEFINED','BexError','CompileError','BoundaryError','ResourceError','blue_value']
```

### `src/blue_bex/compiler.py`

```python
"""Data-only static compilation. There is no Python eval/exec or BEX recursion."""
from __future__ import annotations
from dataclasses import dataclass
from .values import CompileError, clone

RESERVED = set('name description type itemType keyType valueType value items blueId blue schema constraints mergePolicy properties contracts $previous $previousItems $pos $replace $empty'.split())
STATIC = {'type','itemType','keyType','valueType','blue','schema'}
UNARY = set('$nodeBlueId $unwrap $kind $text $integer $number $boolean $object $list $not $truthy $empty $isEmpty $exists $keys $entries $size $objectFromEntries'.split())
ARRAY = set('$concat $pointerJoin $startsWith $sliceAfter $eq $ne $gt $gte $lt $lte $and $or $coalesce $default $add $subtract $multiply $divide $listConcat $merge'.split())
CONSTANT = {'$null','$emptyObject','$emptyList','$changeset','$events'}
READS = {'$document','$event','$currentContract','$resultValue','$binding','$steps','$var','$const'}
QUERY = {'$map','$filter','$flatMap','$reduce','$some','$find','$findEntry'}
EXPR = UNARY | ARRAY | CONSTANT | READS | QUERY | {'$literal','$is','$isKind','$join','$split','$listGet','$get','$objectSet','$pointerGet','$pointerSet','$includes','$hasKey','$choose','$call','$intrinsic'}
STMT = {'$let','$set','$if','$forEach','$appendChange','$appendChanges','$appendEvent','$appendEvents','$call','$return','$returnIf','$fail','$failIf'}
KINDS = {'undefined','null','text','integer','double','boolean','object','list'}


def operator(value):
    if type(value) is dict and len(value)==1:
        key = next(iter(value))
        if type(key) is str and key.startswith('$'): return key
    return None


def object_shape(value, required=(), optional=()):
    if type(value) is not dict: raise CompileError('operator body must be an object')
    if not set(required) <= value.keys(): raise CompileError(f'missing required fields: {set(required)-value.keys()}')
    if value.keys() - set(required) - set(optional): raise CompileError(f'unknown operand fields: {value.keys()-set(required)-set(optional)}')


def name(value, *, container=False):
    if type(value) is not str or not value: raise CompileError('nonempty static name required')
    if container and value in RESERVED: raise CompileError(f'reserved user-container name: {value}')
    return value


def static(value):
    pending=[value]
    while pending:
        current=pending.pop()
        if operator(current):raise CompileError('executable form in static Blue position')
        if type(current) is dict:pending.extend(reversed(tuple(current.values())))
        elif type(current) is list:pending.extend(reversed(current))


def static_positions(value, depth=0):
    pending=[value]
    while pending:
        current=pending.pop()
        if type(current) is dict:
            for k,v in current.items():
                if type(k) is not str:raise CompileError('object keys must be Text')
                if k in STATIC:static(v)
            pending.extend(reversed(tuple(current.values())))
        elif type(current) is list:pending.extend(reversed(current))

@dataclass(frozen=True)
class Program:
    source: dict
    selected_entry: str | None
    operator_inventory: tuple[str,...]

class Compiler:
    def __init__(self, *, intrinsic_ids=()):
        self.intrinsic_ids = frozenset(intrinsic_ids)

    def compile(self, source, *, definition=None, entry=None):
        if type(source) is not dict: raise CompileError('program must be an object')
        merged = clone(source)
        if definition is not None:
            if type(definition) is not dict: raise CompileError('definition must be an object')
            for k in ('constants','functions'):
                if type(definition.get(k,{})) is not dict or type(merged.get(k,{})) is not dict:
                    raise CompileError('name container must be object')
                merged[k] = {**clone(definition.get(k,{})), **merged.get(k,{})}
        self.source = merged
        self.constants = merged.get('constants',{})
        self.functions = merged.get('functions',{})
        if type(self.constants) is not dict or type(self.functions) is not dict: raise CompileError('name container must be object')
        for key in (*self.constants,*self.functions): name(key,container=True)
        for val in self.constants.values(): static(val)
        static_positions(merged)
        self.calls = {key:set() for key in self.functions}
        self.calls['<root>'] = set()
        self.inventory = set()
        for f,body in self.functions.items():
            if type(body) is not dict: raise CompileError('function must be an object')
            args=body.get('args',{})
            if type(args) is not dict: raise CompileError('function args must be a name container')
            for a,pattern in args.items(): name(a,container=True); static(pattern)
            self.body(body,set(args),f)
        selected=entry if entry is not None else merged.get('entry')
        if selected is not None:
            name(selected,container=True)
            if selected not in self.functions: raise CompileError('unknown entry function')
            if self.functions[selected].get('args'): raise CompileError('entry function must have no arguments')
        self.body(merged,set(),'<root>')
        done=set();active=set()
        for f in self.calls:
            pending=[(f,False)]
            while pending:
                key,leave=pending.pop()
                if leave:active.remove(key);done.add(key);continue
                if key in active:raise CompileError('recursive function call graph')
                if key in done:continue
                active.add(key);pending.append((key,True))
                pending.extend((g,False) for g in sorted(self.calls[key],reverse=True))
        return Program(merged,selected,tuple(sorted(self.inventory)))

    def body(self,body,slots,current):
        if 'expr' in body: self.expr(body['expr'],slots,current)
        elif 'do' in body: self.block(body['do'],slots,current)

    def call(self,b,slots,current):
        object_shape(b,('function',),('args',))
        f=name(b['function'],container=True)
        if f not in self.functions: raise CompileError('unknown function '+f)
        args=b.get('args',{})
        if type(args) is not dict:raise CompileError('call args must be object')
        for k in args: name(k,container=True)
        if args.keys()!=self.functions[f].get('args',{}).keys():raise CompileError('call argument set mismatch')
        for v in args.values():self.expr(v,slots,current)
        self.calls[current].add(f)

    def expr(self,v,slots,current):
        op=operator(v)
        if op is None:
            if type(v) is list:
                for a in v:self.expr(a,slots,current)
            elif type(v) is dict:
                for k,a in v.items():
                    if k not in STATIC:self.expr(a,slots,current)
            elif type(v) not in (str,int,float,bool,type(None)):
                from decimal import Decimal
                if type(v) is not Decimal:raise CompileError('invalid literal value')
            return
        if op not in EXPR:raise CompileError('unknown expression operator '+op)
        self.inventory.add(op);b=v[op]
        if op=='$literal' or op in CONSTANT:return
        if op in UNARY:self.expr(b,slots,current);return
        if op in ARRAY:
            if type(b) is not list:raise CompileError(op+' needs an operand list')
            if op in {'$startsWith','$sliceAfter','$eq','$ne','$gt','$gte','$lt','$lte'} and len(b)!=2:raise CompileError('exactly two operands required')
            if op in {'$add','$subtract','$multiply','$divide'} and not b:raise CompileError('at least one arithmetic operand required')
            for a in b:self.expr(a,slots,current)
            return
        if op in {'$var','$const'}:
            if type(b) is str:n=b
            else:object_shape(b,('name',),('path',));n=name(b['name']);self.expr(b.get('path',''),slots,current)
            if n not in (slots if op=='$var' else self.constants):raise CompileError('unknown '+op+' '+n)
            return
        if op in READS:
            if type(b) is dict and operator(b) is None:
                allowed={'path','view'} if op in {'$document','$resultValue'} else {'name','path'} if op=='$binding' else {'step','path'} if op=='$steps' else {'path'}
                object_shape(b,(),allowed)
                for x in b.values():self.expr(x,slots,current)
            else:self.expr(b,slots,current)
            return
        if op=='$is':
            object_shape(b,('node','pattern'));static(b['pattern']);self.expr(b['node'],slots,current);return
        if op=='$isKind':
            object_shape(b,('val','kind'));k=b['kind'];ks=k if type(k) is list else [k]
            if not ks or any(type(x) is not str or x not in KINDS for x in ks):raise CompileError('invalid kind test')
            self.expr(b['val'],slots,current);return
        if op=='$call':self.call(b,slots,current);return
        if op=='$intrinsic':
            if type(b) is not dict or type(b.get('type')) is not dict or set(b['type'])!={'blueId'}:raise CompileError('intrinsic needs static exact type BlueId')
            if b['type']['blueId'] not in self.intrinsic_ids:raise CompileError('unknown intrinsic exact type')
            for k,x in b.items():
                if k!='type':self.expr(x,slots,current)
            return
        if op in QUERY:
            bodykey='where' if op in {'$filter','$some','$find','$findEntry'} else 'expr'
            required=['in','item',bodykey]+(['acc','init'] if op=='$reduce' else [])
            object_shape(b,required,('key','index'))
            self.expr(b['in'],slots,current)
            if op=='$reduce':self.expr(b['init'],slots,current)
            names=[name(b[k],container=True) for k in ('item','key','index','acc') if k in b]
            if len(set(names))!=len(names):raise CompileError('collection bindings must differ')
            self.expr(b[bodykey],slots|set(names),current);return
        shapes={
            '$join':(('list','separator'),()),'$split':(('text','separator'),('limit',)),
            '$listGet':(('list','index'),('default',)),'$get':(('object','key'),()),
            '$objectSet':(('object','key','val'),()),'$pointerGet':(('object','path'),('default',)),
            '$pointerSet':(('object','path'),('op','val')),'$includes':(('list','val'),()),
            '$hasKey':(('object','key'),()),'$choose':(('cond','then'),('else',))}
        req,opt=shapes[op];object_shape(b,req,opt)
        for x in b.values():self.expr(x,slots,current)

    def block(self,statements,slots,current):
        if type(statements) is not list:raise CompileError('statement block must be a list')
        for statement in statements:
            op=operator(statement)
            if op not in STMT:raise CompileError('unknown or malformed statement')
            self.inventory.add(op);b=statement[op]
            if op=='$let':
                if type(b) is not dict:raise CompileError('$let body must be object')
                if 'vars' in b:
                    object_shape(b,('vars',),('order',));variables=b['vars']
                    if type(variables) is not dict:raise CompileError('vars must be object')
                    for n in variables:name(n,container=True)
                    order=b.get('order')
                    if order is not None:
                        if type(order) is not list or len(order)!=len(variables) or set(order)!=variables.keys():raise CompileError('order must name every variable exactly once')
                        for n in order:self.expr(variables[n],slots,current);slots.add(n)
                    else:
                        for expr in variables.values():self.expr(expr,slots,current)
                        slots.update(variables)
                else:
                    object_shape(b,('name','expr'));n=name(b['name'],container=True);self.expr(b['expr'],slots,current);slots.add(n)
            elif op=='$set':
                object_shape(b,('name','expr'))
                if b['name'] not in slots:raise CompileError('$set requires declared variable')
                self.expr(b['expr'],slots,current)
            elif op=='$if':
                object_shape(b,('cond',),('then','else'));self.expr(b['cond'],slots,current)
                a,z=set(slots),set(slots);self.block(b.get('then',[]),a,current);self.block(b.get('else',[]),z,current);slots.update(a&z)
            elif op=='$forEach':
                object_shape(b,('in','item','do'),('key','index'));self.expr(b['in'],slots,current)
                names=[name(b[k],container=True) for k in ('item','key','index') if k in b]
                if len(set(names))!=len(names):raise CompileError('loop bindings must differ')
                slots.update(names);self.block(b['do'],slots,current)
            elif op=='$appendChange':
                object_shape(b,('op','path'),('val',))
                for v in b.values():self.expr(v,slots,current)
            elif op=='$call':self.call(b,slots,current)
            elif op in {'$returnIf','$failIf'}:
                key='expr' if op=='$returnIf' else 'message'
                object_shape(b,('cond',),(key,));self.expr(b['cond'],slots,current)
                if key in b:self.expr(b[key],slots,current)
            elif op=='$fail' and type(b) is dict and 'message' in b:
                object_shape(b,('message',));self.expr(b['message'],slots,current)
            else:self.expr(b,slots,current)
```

### `src/blue_bex/gas.py`

```python
"""Deterministic scalar gas meter. Compilation consumes no semantic gas."""
from dataclasses import dataclass, field
from .values import BexError

DEFAULT = dict(expressionBase=1, statementBase=1, documentRead=2, eventRead=1,
    stepsRead=1, currentContractRead=1, varRead=1, resultValueRead=2,
    pointerGetBase=1, pointerSetBase=3, objectSetBase=2, appendChangeBase=5,
    appendEventBase=5, forEachItem=1, functionCall=2, integerWork=1, textWork=1, valueMember=1, nodeIdentityRequested=5)

class GasExhausted(BexError):
    code = 'GAS_LIMIT_EXCEEDED'

@dataclass
class Gas:
    limit: int = 10000000
    used: int = 0
    rejected: dict | None = None
    schedule: dict = field(default_factory=lambda: dict(DEFAULT))
    owner: str = 'BEX'
    parent: 'Gas | None' = None

    def __post_init__(self):
        if type(self.limit) is not int: raise TypeError('gas limit must be Integer')
        if any(type(v) is not int or v < 0 for v in self.schedule.values()): raise ValueError('invalid tariff')

    def charge(self, counter: str, units: int = 1, *, amount: int | None = None):
        if self.rejected is not None: raise GasExhausted(self.rejected['counter'])
        if type(units) is not int or units < 0: raise BexError('invalid charge units')
        cost = self.schedule[counter] * units if amount is None else amount
        if type(cost) is not int or cost < 0: raise BexError('invalid charge amount')
        if self.limit >= 0 and self.used + cost > self.limit:
            self.rejected = dict(owner=self.owner, counter=counter, units=units, amount=cost, before=self.used,
                                 cap='LOCAL' if self.parent else 'SHARED', remaining=self.limit-self.used)
            if self.parent is not None:
                # Preserve the *local* rejection in the closure receipt without
                # falsely charging it as admitted parent work.
                self.parent.rejected = dict(self.rejected, before=self.parent.used, localBefore=self.used)
            raise GasExhausted(f'{counter}: next {cost}, remaining {self.limit-self.used}')
        if self.parent is not None:
            old = self.parent.owner
            self.parent.owner = self.owner
            try: self.parent.charge(counter, units, amount=cost)
            finally: self.parent.owner = old
        self.used += cost

    @property
    def attempted(self):
        return self.used + (0 if self.rejected is None else self.rejected['amount'])
```

### `src/blue_bex/runtime.py`

```python
"""Executable BEX reference candidate. Effects are data until Contracts applies them."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from .values import (UNDEFINED, BexError, BoundaryError, ResourceError, ExecutionRejected, clone, kind,
    truthy, number, integer, text, required_text, equal, estimated_size,
    segments, escape, pointer_get, pointer_overlay, project_patch, blue_value)
from .compiler import Compiler, Program, operator, STATIC, UNARY, ARRAY, QUERY
from .gas import Gas
from blue_host import host_boundary
from .values import HostValue, size_parts, ordered_keys
from decimal import Decimal

@dataclass
class Context:
    document: Any = field(default_factory=dict)
    event: Any = field(default_factory=dict)
    current_contract: Any = field(default_factory=dict)
    steps: dict = field(default_factory=dict)
    bindings: dict = field(default_factory=dict)
    scope: str = '/'
    resolved_document: Any = UNDEFINED
    read_document: Callable[[str,str,Any],Any] | None = None
    matcher: Callable[[Any,Any],bool] | None = None
    intrinsics: dict = field(default_factory=dict)
    node_blue_id: Callable[[Any, Any], str] | None = None

@dataclass(frozen=True)
class Result:
    value: Any
    changeset: list
    events: list
    gas_used: int

    def blue_output(self):
        return blue_value(self.value)

class _Return(Exception):
    def __init__(self,value): self.value=value

class Engine:
    def __init__(self, *, intrinsics=None):
        self.intrinsics=dict(intrinsics or {})

    @host_boundary
    def compile(self,source,*,definition=None,entry=None):
        return Compiler(intrinsic_ids=self.intrinsics).compile(source,definition=definition,entry=entry)

    @host_boundary
    def execute(self,program,context=None,*,gas=None,gas_limit=10000000,definition=None,entry=None):
        if isinstance(program,Program):
            # Program is a transport value, not an unforgeable admission ticket.
            program=self.compile(program.source,entry=program.selected_entry)
        else:program=self.compile(program,definition=definition,entry=entry)
        run=Invocation(program, context or Context(), gas if gas is not None else Gas(gas_limit),self.intrinsics)
        return run.execute()

class Invocation:
    def __init__(self,program,context,gas,intrinsics):
        self.program=clone(program.source);self.entry=program.selected_entry
        self.context=context;self.gas=gas;self.intrinsics=dict(intrinsics)
        self.constants=self.program.get('constants',{});self.functions=self.program.get('functions',{})
        self.changes=[];self.events=[];self.frames=[{}]
        self.previews={}  # Separate roots/cursors, local to this invocation.
        self.start_gas=gas.used

    def copy(self,value):
        # Values are immutable during evaluation: operators construct new
        # collections and frame updates replace slots, never mutate a value.
        return value

    @staticmethod
    def limbs(n):return max(1,(abs(n).bit_length()+31)//32)

    def to_integer(self,value):
        if type(value) is int:return value
        if type(value) is str:
            self.gas.charge('textWork',(len(value)+63)//64)
            digits=len(value.lstrip('-'))
        else:
            n=number(value);digits=max(len(n.as_tuple().digits),n.adjusted()+1)
        self.gas.charge('integerWork',max(1,(4*digits+31)//32)**2)
        return integer(value)

    def to_text(self,value):
        if type(value) is int:self.gas.charge('integerWork',self.limbs(value)**2)
        return text(value)

    def sized(self,counter,value,extra=0):
        self.gas.charge(counter,amount=self.gas.schedule[counter]+extra)
        for quantity in size_parts(value,self.gas.charge):
            self.gas.charge(counter,amount=quantity)

    @property
    def frame(self):return self.frames[-1]

    def default(self):
        self.gas.charge('valueMember',len(self.changes)+len(self.events))
        return dict(changeset=list(self.changes),events=list(self.events))

    def execute(self):
        self.gas.charge('functionCall')
        if self.entry is not None:value=self.function(self.entry,{},charge=False)
        else:value=self.body(self.program)
        return Result(clone(value),clone(self.changes),clone(self.events),self.gas.used-self.start_gas)

    def body(self,b):
        try:
            if 'expr' in b:return self.expr(b['expr'])
            self.block(b.get('do',[]));return self.default()
        except _Return as r:return r.value

    def function(self,n,args,*,charge=True):
        if charge:self.gas.charge('functionCall')
        body=self.functions[n]
        for key in sorted(body.get('args',{})):
            if not self.matches(args[key],body['args'][key]):raise BexError('function argument pattern rejected: '+key)
        self.frames.append(dict(args))
        try:return self.body(body)
        finally:self.frames.pop()

    def matches(self,node,pattern):
        if node is UNDEFINED:return False
        try:converted=node if isinstance(node,HostValue) else blue_value(node)
        except BoundaryError:return False
        if self.context.matcher is None:raise BexError('Language matching capability unavailable')
        return bool(self.context.matcher(converted,self.copy(pattern)))

    def textarg(self,v):
        return required_text(v if type(v) is str else self.expr(v))

    def path(self,p):
        p=self.textarg(p)
        if p in ('','/'):return self.context.scope
        if p.startswith('/'):segments(p);return p
        base=self.context.scope.rstrip('/')
        result=base+'/'+p;segments(result);return result

    def read(self,op,b):
        if op in {'$var','$const','$binding','$steps'}:
            if op!='$const':self.gas.charge('stepsRead' if op=='$steps' else 'varRead')
            if type(b) is str:
                key,p=b,''
                if op=='$binding' and '/' in b:key,suffix=b.split('/',1);p='/'+suffix
                if op=='$steps' and '.' in b:key,suffix=b.split('.',1);p='/'+suffix.replace('.','/')
            else:
                key=b.get('step' if op=='$steps' else 'name',UNDEFINED)
                key=self.textarg(key);p=self.textarg(b.get('path',''))
            source=self.frame if op=='$var' else self.constants if op=='$const' else self.context.bindings if op=='$binding' else self.context.steps
            return self.copy(pointer_get(source.get(key,UNDEFINED),p))
        if op in {'$event','$currentContract'}:
            self.gas.charge('eventRead' if op=='$event' else 'currentContractRead')
            p=b.get('path','') if type(b) is dict and operator(b) is None else b
            p=self.textarg(p)
            return self.copy(pointer_get(self.context.event if op=='$event' else self.context.current_contract,p))
        self.gas.charge('documentRead' if op=='$document' else 'resultValueRead')
        if type(b) is dict and operator(b) is None:
            p=self.path(b.get('path',''));view=self.textarg(b.get('view','canonical'))
        else:p=self.path(b);view='canonical'
        doc=self.context.resolved_document if view=='resolved' else self.context.document
        if doc is UNDEFINED:raise BexError('resolved document capability unavailable')
        if op=='$resultValue':
            snapshot='resolved' if view=='resolved' else 'canonical'
            if snapshot not in self.previews:self.previews[snapshot]=[doc,0]
            preview=self.previews[snapshot]
            while preview[1]<len(self.changes):
                patch=self.changes[preview[1]]
                preview[0]=project_patch(preview[0],patch['path'],patch.get('val',UNDEFINED),
                                         operation=patch['op'],charge=self.gas.charge)
                preview[1]+=1
            doc=preview[0]
        result=(self.context.read_document(p,view,doc) if self.context.read_document else pointer_get(doc,p))
        return self.copy(result)

    def expr(self,v):
        self.gas.charge('expressionBase')
        op=operator(v)
        if op is None:
            if type(v) is dict:
                out={}
                for k in sorted(v):
                    x=self.copy(v[k]) if k in STATIC else self.expr(v[k])
                    if x is not UNDEFINED:out[k]=x
                return out
            if type(v) is list:return [self.expr(x) for x in v]
            kind(v);return self.copy(v)
        b=v[op]
        if op=='$literal':return self.copy(b)
        if op=='$null':return None
        if op=='$emptyObject':return {}
        if op=='$emptyList':return []
        if op=='$changeset':
            self.gas.charge('valueMember',len(self.changes));return list(self.changes)
        if op=='$events':
            self.gas.charge('valueMember',len(self.events));return list(self.events)
        if op in {'$document','$event','$currentContract','$resultValue','$binding','$steps','$var','$const'}:return self.read(op,b)
        if op in UNARY:
            x=self.expr(b)
            if op=='$nodeBlueId':
                self.gas.charge('nodeIdentityRequested')
                if self.context.node_blue_id is None:
                    raise BoundaryError('Language identity boundary unavailable')
                identity=self.context.node_blue_id(x,self.gas)
                if type(identity) is not str or not identity:
                    raise BoundaryError('Language identity boundary returned an invalid identity')
                return identity
            if op=='$unwrap':
                while True:
                    self.gas.charge('valueMember')
                    if kind(x)!='object':return self.copy(x)
                    child=x.get('value',UNDEFINED)
                    if child is UNDEFINED:return self.copy(x)
                    x=child
            k=kind(x)
            if op=='$kind':return k
            if op=='$text':return self.to_text(x)
            if op=='$integer':return self.to_integer(x)
            if op=='$number':
                if type(x) is int:self.gas.charge('integerWork',self.limbs(x)**2)
                elif type(x) is str:self.gas.charge('textWork',(len(x)+63)//64)
                return number(x)
            if op=='$boolean':
                if x=='true':return True
                if x=='false':return False
                return truthy(x)
            if op in {'$object','$list'}:
                expected='object' if op=='$object' else 'list'
                if k in {'null','undefined'}:return {} if expected=='object' else []
                if k!=expected:raise BexError('wrong collection kind')
                return x
            if op in {'$not','$empty','$isEmpty'}:return not truthy(x)
            if op=='$truthy':return truthy(x)
            if op=='$exists':return x is not UNDEFINED
            if op=='$keys':
                if k!='object':return []
                self.gas.charge('valueMember',len(x));return sorted(x)
            if op=='$entries':
                if k!='object':return []
                self.gas.charge('valueMember',len(x));return [dict(key=a,val=x[a]) for a in sorted(x)]
            if op=='$size':return len(x) if k in {'object','list'} else 0 if k in {'null','undefined'} else 1
            if op=='$objectFromEntries':
                if k!='list':raise BexError('entries must be a list')
                out={}
                for row in x:
                    self.gas.charge('forEachItem')
                    if kind(row) != 'object':raise BexError('entry must be object')
                    key=required_text(row.get('key',UNDEFINED));val=row.get('val',UNDEFINED)
                    if val is UNDEFINED:out.pop(key,None)
                    else:out[key]=self.copy(val)
                return out
        if op in {'$and','$or','$coalesce','$default'}:
            for a in b:
                x=self.expr(a);t=truthy(x)
                if op=='$and' and not t:return False
                if op=='$or' and t:return True
                if op in {'$coalesce','$default'} and t:return x
            return True if op=='$and' else False if op=='$or' else UNDEFINED
        if op in ARRAY:
            args=[self.expr(a) for a in b]
            if op=='$concat':
                strings=[self.to_text(a) for a in args]
                self.gas.charge('textWork',(sum(map(len,strings))+63)//64)
                return ''.join(strings)
            if op=='$pointerJoin':
                strings=[self.to_text(x) if x is not None and x is not UNDEFINED else required_text(x) for x in args]
                self.gas.charge('textWork',(sum(map(len,strings))+len(strings)+63)//64)
                return '/'+ '/'.join(escape(x) for x in strings)
            if op in {'$startsWith','$sliceAfter'}:
                s,p=map(self.to_text,args)
                self.gas.charge('textWork',(len(s)+len(p)+63)//64)
                return s.startswith(p) if op=='$startsWith' else s[len(p):] if s.startswith(p) else ''
            if op in {'$eq','$ne'}:return equal(*args,charge=self.gas.charge) == (op=='$eq')
            if op in {'$gt','$gte','$lt','$lte'}:
                for v in args:
                    if type(v) is int:self.gas.charge('integerWork',self.limbs(v)**2)
                    elif type(v) is str:self.gas.charge('textWork',(len(v)+63)//64)
                a,z=map(number,args);return {'$gt':a>z,'$gte':a>=z,'$lt':a<z,'$lte':a<=z}[op]
            if op in {'$add','$subtract','$multiply','$divide'}:
                ints=[self.to_integer(a) for a in args];r=ints[0]
                for n in ints[1:]:
                    a,z=self.limbs(r),self.limbs(n)
                    self.gas.charge('integerWork',max(a,z) if op in {'$add','$subtract'} else a*z*(2 if op=='$divide' else 1))
                    if op=='$add':r+=n
                    elif op=='$subtract':r-=n
                    elif op=='$multiply':r*=n
                    else:
                        if n==0 or r%n:raise BexError('division requires nonzero divisor and exact integer result')
                        r//=n
                return r
            if op=='$listConcat':
                if any(kind(x) != 'list' for x in args):raise BexError('listConcat requires lists')
                out=[]
                for x in args:
                    for a in x:self.gas.charge('valueMember');out.append(a)
                return out
            if op=='$merge':
                out={}
                for a in args:
                    if kind(a) != 'object':raise BexError('merge requires objects')
                    for key in ordered_keys(a,self.gas.charge):out[key]=a[key]
                return out
        if op=='$choose':
            if truthy(self.expr(b['cond'])):return self.expr(b['then'])
            return self.expr(b['else']) if 'else' in b else UNDEFINED
        if op=='$is':return self.matches(self.expr(b['node']),b['pattern'])
        if op=='$isKind':return kind(self.expr(b['val'])) in (b['kind'] if type(b['kind']) is list else [b['kind']])
        if op=='$call':return self.function(b['function'],{k:self.expr(b.get('args',{})[k]) for k in sorted(b.get('args',{}))})
        if op=='$intrinsic':
            tid=b['type']['blueId']
            processor=self.intrinsics.get(tid)
            if processor is None:raise BexError('intrinsic exact type is not installed at execution')
            payload={}
            for k in sorted(b):
                if k!='type':
                    x=self.expr(b[k])
                    if x is not UNDEFINED:payload[k]=x
            output=processor(clone(payload),self.gas)
            if output is None:raise BexError('intrinsic returned Python None; explicit BEX values required')
            kind(output);return self.copy(output)
        if op in QUERY:return self.query(op,b)
        if op in {'$join','$split'}:
            if op=='$join':
                arr=self.expr(b['list']);sep=self.textarg(b['separator'])
                if kind(arr) != 'list':raise BexError('join requires list')
                self.gas.charge('valueMember',len(arr))
                strings=[self.to_text(x) for x in arr]
                self.gas.charge('textWork',(sum(map(len,strings))+len(sep)*max(0,len(strings)-1)+63)//64)
                return sep.join(strings)
            s=self.textarg(b['text']);sep=self.textarg(b['separator']);lim=self.to_integer(self.expr(b['limit'])) if 'limit'in b else -1
            if not sep or lim==0 or lim < -1:raise BexError('invalid split separator/limit')
            self.gas.charge('textWork',(len(s)+len(sep)+63)//64)
            self.gas.charge('valueMember',len(s)+1)
            return s.split(sep,lim-1 if lim>0 else -1)
        if op=='$listGet':
            arr=self.expr(b['list']);i=self.to_integer(self.expr(b['index']))
            if kind(arr) != 'list' or i<0:raise BexError('listGet requires a list and nonnegative index')
            return self.copy(arr[i]) if i<len(arr) else self.expr(b['default']) if 'default'in b else UNDEFINED
        if op in {'$get','$hasKey'}:
            obj=self.expr(b['object']);key=self.textarg(b['key'])
            return (kind(obj) == 'object' and obj.get(key,UNDEFINED) is not UNDEFINED) if op=='$hasKey' else self.copy(obj.get(key,UNDEFINED)) if kind(obj) == 'object' else UNDEFINED
        if op=='$objectSet':
            key=self.textarg(b['key']);val=self.expr(b['val']);self.sized('objectSetBase',val)
            obj=self.expr(b['object'])
            if obj is None or obj is UNDEFINED:obj={}
            if kind(obj) != 'object':raise BexError('objectSet requires object')
            out={key:obj[key] for key in ordered_keys(obj,self.gas.charge)}
            if val is UNDEFINED:out.pop(key,None)
            else:out[key]=val
            return out
        if op=='$pointerGet':
            obj=self.expr(b['object']);path=self.textarg(b['path']);parts=segments(path)
            self.gas.charge('pointerGetBase',amount=self.gas.schedule['pointerGetBase']+len(parts));out=pointer_get(obj,path)
            return self.copy(out) if out is not UNDEFINED else self.expr(b['default']) if 'default'in b else UNDEFINED
        if op=='$pointerSet':
            operation=self.textarg(b.get('op','set'));path=self.textarg(b['path'])
            if operation not in {'set','remove'}:raise BexError('pointerSet op must be set/remove')
            val=UNDEFINED if operation=='remove' else self.expr(b['val']) if 'val'in b else UNDEFINED
            obj=self.expr(b['object']);self.sized('pointerSetBase',val,len(segments(path)))
            return pointer_overlay(obj,path,val,remove=operation=='remove',charge=self.gas.charge)
        if op=='$includes':
            arr=self.expr(b['list']);val=self.expr(b['val'])
            if kind(arr) != 'list':raise BexError('includes requires list')
            for x in arr:
                self.gas.charge('forEachItem')
                if equal(x,val,charge=self.gas.charge):return True
            return False
        raise BexError('unimplemented operator '+op)

    def collection(self,value):
        if kind(value) == 'list':return ((UNDEFINED,x,i) for i,x in enumerate(value))
        if kind(value) == 'object':return ((k,value[k],i) for i,k in enumerate(sorted(value)))
        raise BexError('collection operation needs object or list')

    def query(self,op,b):
        source=self.expr(b['in']);rows=self.collection(source)
        acc=self.expr(b['init']) if op=='$reduce' else UNDEFINED
        names=[b[k] for k in ('item','key','index','acc') if k in b]
        old={n:self.frame.get(n,UNDEFINED) for n in names};present={n for n in names if n in self.frame}
        output={} if op=='$filter' and kind(source) == 'object' else []
        try:
            for key,val,i in rows:
                self.gas.charge('forEachItem');self.frame[b['item']]=self.copy(val)
                if 'key'in b:self.frame[b['key']]=key
                if 'index'in b:self.frame[b['index']]=i
                if 'acc'in b:self.frame[b['acc']]=acc
                result=self.expr(b['where'] if 'where'in b else b['expr'])
                if op=='$reduce':acc=result
                elif op=='$map':output.append(result)
                elif op=='$flatMap':
                    if kind(result) != 'list':raise BexError('flatMap item is not a list')
                    self.gas.charge('valueMember',len(result));output.extend(result)
                elif truthy(result):
                    if op=='$some':return True
                    if op=='$find':return self.copy(val)
                    if op=='$findEntry':return {'val':self.copy(val),'index':i,**({'key':key} if key is not UNDEFINED else {})}
                    if type(output) is dict:output[key]=self.copy(val)
                    else:output.append(self.copy(val))
            return acc if op=='$reduce' else False if op=='$some' else UNDEFINED if op in {'$find','$findEntry'} else output
        finally:
            for n in names:
                if n in present:self.frame[n]=old[n]
                else:self.frame.pop(n,None)

    def append_change(self,p,*,evaluated=False):
        if kind(p) != 'object' or set(p)-{'op','path','val'} or not {'op','path'}<=p.keys():raise BexError('malformed patch')
        operation=required_text(p['op']) if evaluated else self.textarg(p['op'])
        if operation not in {'add','replace','remove'}:raise BexError('unsupported patch op')
        if evaluated:
            path=required_text(p['path'])
            if not path.startswith('/'):path=self.context.scope.rstrip('/')+'/'+path
            if path in ('','/'):path=self.context.scope
            segments(path)
        else:path=self.path(p['path'])
        val=UNDEFINED if operation=='remove' else p.get('val',UNDEFINED) if evaluated else self.expr(p['val']) if 'val'in p else UNDEFINED
        if operation!='remove' and val is UNDEFINED:raise BexError('patch val is required')
        self.sized('appendChangeBase',val)
        self.changes.append({'op':operation,'path':path,**({'val':self.copy(val)} if operation!='remove' else {})})

    def append_event(self,value):
        if value is UNDEFINED:raise BexError('undefined event')
        self.sized('appendEventBase',value);self.events.append(self.copy(value))

    def block(self,statements):
        for statement in statements:
            self.gas.charge('statementBase');op=operator(statement);b=statement[op]
            if op=='$let':
                if 'vars'in b:
                    vs=b['vars']
                    if 'order'in b:
                        for n in b['order']:self.frame[n]=self.expr(vs[n])
                    else:self.frame.update({n:self.expr(vs[n]) for n in sorted(vs)})
                else:self.frame[b['name']]=self.expr(b['expr'])
            elif op=='$set':self.frame[b['name']]=self.expr(b['expr'])
            elif op=='$if':self.block(b.get('then',[]) if truthy(self.expr(b['cond'])) else b.get('else',[]))
            elif op=='$forEach':
                source=self.expr(b['in'])
                for key,val,i in self.collection(source):
                    self.gas.charge('forEachItem')
                    self.frame[b['item']]=self.copy(val) if kind(source) == 'list' or 'key'in b else dict(key=key,val=self.copy(val))
                    if 'key'in b:self.frame[b['key']]=key
                    if 'index'in b:self.frame[b['index']]=i if kind(source) == 'list' else UNDEFINED
                    self.block(b['do'])
            elif op=='$appendChange':self.append_change(b)
            elif op=='$appendChanges':
                arr=self.expr(b)
                if kind(arr) != 'list':raise BexError('appendChanges needs list')
                for p in arr:self.append_change(p,evaluated=True)
            elif op=='$appendEvent':self.append_event(self.expr(b))
            elif op=='$appendEvents':
                arr=self.expr(b)
                if kind(arr) != 'list':raise BexError('appendEvents needs list')
                for e in arr:self.append_event(e)
            elif op=='$call':self.function(b['function'],{k:self.expr(b.get('args',{})[k]) for k in sorted(b.get('args',{}))})
            elif op=='$return':raise _Return(self.default() if b is None else self.expr(b))
            elif op=='$returnIf':
                if truthy(self.expr(b['cond'])):raise _Return(self.expr(b['expr']) if 'expr'in b else self.default())
            elif op=='$fail':raise ExecutionRejected(self.to_text(self.expr(b['message'] if type(b) is dict and 'message'in b else b)))
            elif op=='$failIf':
                if truthy(self.expr(b['cond'])):raise ExecutionRejected(self.to_text(self.expr(b.get('message','BEX failure'))))
            else:raise BexError('unknown statement '+str(op))
```

### `src/blue_bex/values.py`

```python
"""BEX runtime values, distinct from Blue nodes and Python truthiness.

Null is internal only in this corrected-boundary profile. UNDEFINED is not null.
No function in this module hashes or admits a Blue document.
"""
from __future__ import annotations
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import math
import re
from typing import Any

class BexError(Exception):
    code = 'BEX_RUNTIME_ERROR'

class CompileError(BexError):
    code = 'BEX_COMPILE_ERROR'

class BoundaryError(BexError):
    code = 'BEX_OUTPUT_INVALID'

class ResourceError(BexError):
    code = 'PORTABLE_LIMIT_EXCEEDED'

class ExecutionRejected(BexError):
    code = 'EXECUTION_REJECTED'

class _Undefined:
    def __repr__(self): return 'UNDEFINED'
    def __copy__(self): return self
    def __deepcopy__(self, memo): return self
UNDEFINED = _Undefined()


class HostValue:
    """Trusted immutable host collection, never executable program syntax.

    The host supplies path-local access and a finite, exact Blue output. Copying
    a value retains the same captured view; it must not traverse its children.
    """
    def __copy__(self): return self
    def __deepcopy__(self, memo): return self
    def blue_output(self): raise NotImplementedError
    def output_view(self): return self  # Finite lazy view used for output sizing.
    def accounting_view(self):
        """Finite metering form; only an evidence-bearing host may override.

        This does not change kind, reads, equality, or semantic output. Generic
        host collections retain ordinary traversal/construction accounting.
        """
        return self.output_view()
    def value_kind(self): raise NotImplementedError
    def comparison_key(self): return id(self)


def clone(value: Any) -> Any:
    holder=[None];pending=[(holder,0,value)];memo={}
    while pending:
        target,key,current=pending.pop()
        if type(current) not in (dict,list):target[key]=deepcopy(current);continue
        if id(current) in memo:target[key]=memo[id(current)];continue
        out={} if type(current) is dict else [None]*len(current)
        target[key]=out;memo[id(current)]=out
        rows=current.items() if type(current) is dict else enumerate(current)
        pending.extend((out,k,v) for k,v in reversed(tuple(rows)))
    return holder[0]


def kind(value: Any) -> str:
    if isinstance(value, HostValue): return value.value_kind()
    if value is UNDEFINED: return 'undefined'
    if value is None: return 'null'
    if type(value) is bool: return 'boolean'
    if type(value) is int: return 'integer'
    if type(value) in (Decimal, float):
        if not number(value).is_finite(): raise BexError('non-finite number')
        return 'double'
    if type(value) is str: return 'text'
    if type(value) is dict: return 'object'
    if type(value) is list: return 'list'
    raise BexError(f'not a BEX value: {type(value).__name__}')


def truthy(value: Any) -> bool:
    k = kind(value)
    if k in ('undefined', 'null'): return False
    if k == 'boolean': return value
    if k in ('text', 'object', 'list'): return len(value) != 0
    return True  # In particular, numeric zero is TRUE in BEX.


def number(value: Any) -> Decimal:
    if type(value) is Decimal: result = value
    elif type(value) is int: result = Decimal(value)
    elif type(value) is float:
        if not math.isfinite(value): raise BexError('non-finite Double')
        result = Decimal(repr(value))
    elif type(value) is str:
        if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', value, flags=re.ASCII):
            raise BexError('invalid numeric text')
        try: result = Decimal(value)
        except InvalidOperation as e: raise BexError('invalid numeric text') from e
    else: raise BexError('numeric conversion requires Integer, Double or Text')
    if not result.is_finite(): raise BexError('non-finite number')
    return result


def integer(value: Any) -> int:
    if type(value) is str:
        if not re.fullmatch(r'(?:0|-[1-9][0-9]*|[1-9][0-9]*)', value, flags=re.ASCII):
            raise BexError('integer text is not canonical')
        return int(Decimal(value))
    n = number(value)
    if n != n.to_integral_value(): raise BexError('non-integral number')
    return int(n)


def text(value: Any) -> str:
    k = kind(value)
    if k in ('undefined', 'null'): return ''
    if k == 'boolean': return 'true' if value else 'false'
    if k == 'integer': return str(Decimal(value))  # Avoid Python's configurable int-to-string digit guard.
    if k in ('double', 'text'): return str(value) if type(value) is not float else str(number(value))
    raise BexError('cannot implicitly render a collection as Text')


def required_text(value: Any) -> str:
    if value is UNDEFINED or value is None: raise BexError('missing/null path, name, operation or key')
    return text(value)


def ordered_keys(value, charge=None):
    """Prepay a portable key-order envelope; never inspect child values."""
    n=len(value)
    if charge:charge('valueMember',n)
    keys=list(value)
    rounds=(n-1).bit_length() if n else 0
    if charge:
        charge('valueMember',n*rounds)
        charge('textWork',sum((len(key)+63)//64 for key in keys)*(rounds+1))
    return sorted(keys)


def equal(a: Any, b: Any, charge=None) -> bool:
    def members(x,y,ordered):
        for key in ordered:yield x[key],y[key]
    pending, active = [(iter(((a,b),)),None)], set()
    while pending:
        try:a,b = next(pending[-1][0])
        except StopIteration:
            _,pair=pending.pop()
            if pair is not None:active.remove(pair)
            continue
        if charge:charge('valueMember')
        ka,kb = kind(a),kind(b)
        if ka in ('integer','double') and kb in ('integer','double'):
            both_integers=type(a) is int and type(b) is int
            if charge:
                limbs=[max(1,(abs(x).bit_length()+31)//32) for x in (a,b) if type(x) is int]
                charge('integerWork',sum(n if both_integers else n*n for n in limbs))
            if (a!=b if both_integers else number(a)!=number(b)):return False
            continue
        if ka != kb:return False
        if ka in ('object','list'):
            pair = (a.comparison_key() if isinstance(a,HostValue) else id(a),
                    b.comparison_key() if isinstance(b,HostValue) else id(b))
            if pair in active:continue
            active.add(pair)
            if ka=='list':
                if len(a)!=len(b):return False
                pending.append((iter(zip(a,b)),pair))
            else:
                left,right=ordered_keys(a,charge),ordered_keys(b,charge)
                if left!=right:return False
                pending.append((members(a,b,left),pair))
        elif ka=='text' and charge:
            if len(a)!=len(b):return False
            for offset in range(0,len(a),64):
                charge('textWork',2)
                if a[offset:offset+64]!=b[offset:offset+64]:return False
        elif ka!='undefined' and a!=b:return False
    return True


def utf16_length(s: str) -> int:
    try: return len(s.encode('utf-16-le')) // 2
    except UnicodeEncodeError as e: raise BexError('unpaired Unicode surrogate') from e


def size_parts(v, charge=None):
    """Finite output-size fragments in code-point/index preorder.

    The consumer charges each yielded quantity before resuming this generator.
    Descendant lookups are lazy; key ordering and scalar encoding are prepaid.
    Host accounting views retain established exact identities rather than chase
    their materialized bodies. New native containers still visit every child.
    """
    pending=[iter((v,))]
    while pending:
        try:current=next(pending[-1])
        except StopIteration:
            pending.pop();continue
        if isinstance(current,HostValue):current=current.accounting_view()
        k=kind(current)
        if k in ('undefined','null'):continue
        if k=='list':
            yield len(current)
            pending.append(iter(current))
        elif k=='object':
            yield len(current)
            keys=ordered_keys(current,charge)
            for key in keys:
                if charge:charge('textWork',(len(key)+63)//64)
                yield utf16_length(key)
            pending.append(map(current.__getitem__,keys))
        else:
            if charge and type(current) is int:
                charge('integerWork',max(1,(abs(current).bit_length()+31)//32)**2)
            rendered=text(current)
            if charge:charge('textWork',(len(rendered)+63)//64)
            yield max(1,utf16_length(rendered))


def estimated_size(v):
    return sum(size_parts(v))


def segments(path: str) -> list[str]:
    if type(path) is not str: raise BexError('pointer must be Text')
    # BEX value pointers designate root by both empty and slash. Language's own
    # query API has a different empty-member rule; never delegate blindly.
    if path in ('', '/'): return []
    if not path.startswith('/'): raise BexError('absolute value pointer required')
    out = []
    for part in path[1:].split('/'):
        if re.search(r'~(?![01])', part): raise BexError('invalid JSON pointer escape')
        out.append(part.replace('~1', '/').replace('~0', '~'))
    return out


def escape(part: str) -> str:
    return part.replace('~', '~0').replace('/', '~1')


def index(segment: str, length: int, *, add: bool = False) -> int:
    if add and segment == '-': return length
    if not re.fullmatch(r'0|[1-9][0-9]*', segment, flags=re.ASCII): raise BexError('noncanonical list index')
    result = int(Decimal(segment))
    if result > length or (result == length and not add): raise BexError('list index outside bounds')
    return result


def pointer_get(value: Any, path: str) -> Any:
    at = value
    for s in segments(path):
        if kind(at) == 'object': at = at.get(s, UNDEFINED)
        elif kind(at) == 'list':
            try: at = at[index(s,len(at))]
            except BexError: return UNDEFINED
        else: return UNDEFINED
    return at


def pointer_overlay(value: Any, path: str, replacement: Any, *, remove: bool = False, charge=None) -> Any:
    """Persistent overlay; copy the selected spine, never recursive descendants."""
    parts=segments(path)
    if not parts:return UNDEFINED if remove else clone(replacement)
    spine=[];at=value
    for offset,s in enumerate(parts):
        if at is None or at is UNDEFINED:at={}
        k=kind(at);last=offset==len(parts)-1
        if k not in ('object','list'):raise BexError('scalar pointer target parent')
        if k=='object':out={key:at[key] for key in ordered_keys(at,charge)}
        else:
            if charge:charge('valueMember',len(at))
            out=list(at)
        key=s if k=='object' else index(s,len(out),add=last and not remove)
        spine.append((out,key))
        if not last:at=out.get(key,UNDEFINED) if k=='object' else out[key]
    result=UNDEFINED if remove else clone(replacement)
    for offset,(out,key) in enumerate(reversed(spine)):
        if isinstance(out,dict):
            if offset==0 and result is UNDEFINED:out.pop(key,None)
            else:out[key]=result
        elif key==len(out):out.append(result)
        else:out[key]=result
        result=out
    return result



def project_patch(value: Any, path: str, replacement: Any, *, operation: str, charge=None) -> Any:
    """Project one staged patch; pointer_overlay keeps assignment semantics."""
    parts=segments(path)
    remove=operation=='remove'
    if not parts:return UNDEFINED if remove else clone(replacement)
    spine=[];at=value
    for offset,segment in enumerate(parts):
        if at is None or at is UNDEFINED:at={}
        k=kind(at);last=offset==len(parts)-1
        if k not in ('object','list'):raise BexError('scalar pointer target parent')
        if k=='object':
            out={key:at[key] for key in ordered_keys(at,charge)}
            key=segment
        else:
            length=len(at)
            key=index(segment,length,add=last and operation=='add')
            if charge:charge('valueMember',length)
            out=[at[i] for i in range(length)]
        spine.append((out,key))
        if not last:at=out.get(key,UNDEFINED) if k=='object' else out[key]
    result=UNDEFINED if remove else clone(replacement)
    for offset,(out,key) in enumerate(reversed(spine)):
        if isinstance(out,dict):
            if offset==0 and result is UNDEFINED:out.pop(key,None)
            else:out[key]=result
        elif offset==0 and remove:out.pop(key)
        elif offset==0 and operation=='add':out.insert(key,result)
        else:out[key]=result
        result=out
    return result


def blue_value(value: Any, *, _in_object: bool = False) -> Any:
    """Prepare semantic output; the Language MUST then admit it.

    Undefined object members are omitted. Null is NEVER rewritten to {}.
    Decimal rounds to finite binary64 using Python's correctly-rounded conversion.
    """
    if isinstance(value, HostValue): return value.blue_output()
    k = kind(value)
    if k == 'undefined': raise BoundaryError('undefined is not a Blue value')
    if k == 'null': raise BoundaryError('BEX null is not a Blue node; use $emptyObject explicitly')
    if k == 'object': return {a: blue_value(b) for a,b in value.items() if b is not UNDEFINED}
    if k == 'list': return [blue_value(v) for v in value]
    if k == 'double':
        f = float(value)
        if not math.isfinite(f): raise BoundaryError('Double output overflow')
        return f
    return value
```

### `src/blue_host/__init__.py`

```python
"""Operational control flow shared by the stack; never a semantic rejection.

Hosts may retry the same input with the same gas after fixing capacity or
cancellation. This module has no dependency on any Blue semantic layer.
"""
from concurrent.futures import CancelledError
from asyncio import CancelledError as AsyncCancelledError
from functools import wraps


class HostIncomplete(Exception):
    code = 'HOST_INCOMPLETE'

    def __init__(self, reason, **context):
        self.reason = reason
        self.context = {'reason': reason, **context}
        super().__init__(reason)


HOST_FAILURES = (HostIncomplete, MemoryError, RecursionError, CancelledError, AsyncCancelledError)


def incomplete(error):
    if isinstance(error, HostIncomplete):
        return error
    return HostIncomplete(type(error).__name__)


def host_boundary(fn):
    """Convert incidental host failures without manufacturing an Outcome."""
    @wraps(fn)
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except HOST_FAILURES as error:
            raise incomplete(error) from error
    return run
```

### Source inventory

| Module | SHA-256 of extracted UTF-8 module |
|---|---|
| `src/blue_bex/__init__.py` | `820ef8825a174b5f9666b9b713d51e20bcf8fa6c509b79128fb373433033e8d8` |
| `src/blue_bex/compiler.py` | `6af97e5067510b862cbb0edc808fc7903f4f0be51c8ff45a31df07be9bdfa55d` |
| `src/blue_bex/gas.py` | `78cb48147d907a6b84535563d5dddd543b6bf734447a184e7a50b49b5cc42803` |
| `src/blue_bex/runtime.py` | `3184b935ae68c68bb8850a199142879c8ddac7563a01168b69037f42ca62a012` |
| `src/blue_bex/values.py` | `5d6677df295197343648d6dcbac94c4853f3daf367cab5752911f9fbb5f65b8b` |
| `src/blue_host/__init__.py` | `ac30b5090d56b101150b3bdb9bb05fff265308737c3ea0dd8b9caa22b0b5b607` |

## Candidate verification and publication boundary

Run the focused candidate tests from the repository root with Python 3.13+:

```sh
python3 blue-bex/tests/test_resultvalue_preview.py
```

The runner extracts the six modules above into a temporary directory and executes
them in a separate process. No frozen reference is edited or selected by accident.
The test file is also included by `./blue-bex/blue-package test` where the full
historical package-test prerequisites are installed. Candidate tests do not
replace existing publication-integrity or frozen-reference qualification checks.

The corresponding MyOS Core implementation and regression tests were inspected at
`2992f6c6a92db8c9d2efbda8d923dfefa9a9daa0`: `Engine.Invocation.read`,
`Values.projectPatch`, `blue.bex.ResultValueTest` and `blue.contracts.ResultValueTest`.
This is bounded source-level alignment for the staged-preview correction, not a
claim of complete Python/Java parity or whole-host qualification. This candidate
has no published identity, and current package selections still identify the
unchanged historical specification. Publishing or installing a new selection
requires a separate compatibility and identity decision.
