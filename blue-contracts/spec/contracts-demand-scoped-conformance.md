# Demand-scoped Contracts — conformance proposal and release gates

Companion to [normative design draft](contracts-demand-scoped-draft.md). Status: required cases proposed for a new immutable edition; no claim that current Java/reference algorithms pass. Old final-gas cases remain unchanged. These cases must be represented in the canonical executable reference and Java tests before publication is qualified.

## Comparison rules

A is the preserved old build/edition/packages/journal. B is the candidate build with exactly those old inputs. Compare complete observations, BlueIds, snapshots, receipts, scalar gas, checkpoints, terminal decisions and subsequent cold operations exactly.

C uses the candidate build and the same new exact input sources/publications across variants. Compare full/missing-unused content, inline/reference, warm/cold, embedded/standalone and same-edition participants exactly. Do not compare differing publication IDs between A and C as though they were the same document. Do not normalize gas, checkpoints or internal observation fields to obtain equality.

Each failure test must distinguish missing resources from invalid content and unsupported semantics. Fixture/setup failures are not evidence for the intended assertion. Keep the original signed bytes, target flags and source order.

## Native obligations and evidence

| ID | Construction / action | Required observation |
| --- | --- | --- |
| DS01 | Plain counter with original event Ref and unavailable unused historical operand | Normal new-edition process and export succeed; full/missing results and gas agree; ordinary full Language strict still requires that operand |
| DS02 | Exact native type discovery on an unused workflow whose step body is unavailable | Discover handler role/order without opening step body; selecting that handler later produces exact resource demand |
| DS03 | Conditional expression selects x; y body unavailable | x branch executes without fetching y; condition or contextual schema that actually requires y instead waits; no missing-to-false coercion |
| DS04 | Count constrained by parent `valueType`, typed field, inherited constraint and own schema | Standalone scalar certificate is insufficient; contextual valid value succeeds, invalid mutation fails, missing applicable definition waits |
| DS05 | `contracts` map schema `maxFields:0`; analogous list `itemType` and governing required fields | Invalid container rejected although every child would pass independently; constraints survive inline/reference representations |
| DS06 | Missing/invalid selected-node `specification`, type ancestry, labels, fixed values or merge metadata | Same native outcomes as complete contextual Language checks; no hand-written approximation or broad metadata omission |
| DS07 | Patch changes enclosing schema/type/valueType while child exact ID remains unchanged | Prior contextual success cannot be reused; new obligations fail/wait before exposing candidate to next step |
| DS08 | Same missing BlueId appears as unused historical target and current required operand | Historical identity observation succeeds; required role demands exact content; caches and delivery order do not alter result |
| DS09 | Ordinary event observer with selected metadata filter, nested filter and explicit private operand read | Native match/mismatch semantics preserved; required reads wait; ordinary observer not suppressed merely because operation routing skips |
| DS10 | Partial restore then full strict, warm repeated failure, cold restore, cache-pressure/reuse control | No partial fact is a full certificate; same logical decisions/gas and exact required IDs under all variants |
| DS26 | Initialize `{}`, `{"name":"TEST"}`, `{"description":"TEST"}` and ordinary-field `{"title":"TEST"}` documents through the public API; export each result and restore it in a fresh processor. Include scalar/list roots, typed scalar/list declarations without values, violated root constraints and unavailable governing definitions as negative controls | Valid empty/metadata-only roots initialize and survive finalization and cold restore without adding ordinary fields; exact document identities are preserved by export/restore. Invalid effective root shapes and constraints remain rejected; missing required definitions remain resource demands. The generic required-container observation remains strict. This checks the preserved root contract clarified in section 12.4, not a new edition behavior |

## Restore, atomicity and retention

| ID | Construction / action | Required observation |
| --- | --- | --- |
| DS11 | Tampered envelope/commitment/release/runtime/member key/edge/lifetime/protected marker | Restore rejects for the actual corruption, with state/evidence/cache rollback |
| DS12 | Checkpoint subtype adds constraints; timestamp is an exact scalar reference | Apply actual contextual constraints; selected scalar projection validates integer; no identity or persisted-byte rewrite |
| DS13 | Excluded private operand inline inside a retained ancestor vs ordinary reference | Same exact IDs and results; exported records contain no excluded private body; shallow serialization does not drop required evidence |
| DS14 | Genuine cyclic member and owning-set proof; altered proof/body; historical A(T)→B(T)→A(T−1) | Correct proof/body survives cold restore; invalid proof fails; no acyclic exact record emitted for a cyclic identity; history remains historical |
| DS15 | First patch installed/finalized, then BEX read needs unavailable exact resource | NEEDS returns original state/checkpoint, previous context/evidence/prepared output/archive/provenance; first mutation demonstrably occurred, not only a failed candidate |
| DS16 | Same process receives only required record and retries exact input/event/time | One successful effect, complete strict/full reference equality within new edition; repeat committed event follows actual reference idempotency behavior |
| DS17 | Real required-retention failure, plus explicit fault injection after APPLIED calculation | No capturable completion, archive/progress/effects or evidence from failed attempt; distinguish natural missing-resource repro from injected transaction test |
| DS18 | Scoped export alone into empty process, then real next operation | No parent test runtime/evidence leaks; required content demand and constraints reconstructed from exact records; original event Ref retained |

## Completion and integration

| ID | Construction / action | Required observation |
| --- | --- | --- |
| DS19 | Successful local new-edition outcome, capture complete owned unit, normal receive and dependent reaction | Actual provenance established after required retention; received state/effects correct without pretending source closure is fully certified |
| DS20 | Foreign issuer, copied descriptor, modified receipt/event/time/release/runtime, expired capability, partial unit or wrong predecessor | Existing integrity checks reject; an exact after-body alone does not establish execution |
| DS21 | Atomically committed local record, fresh worker CompletionReader, receive then next operation | Trusted local origin plus descriptor/commitment checks re-established; arbitrary imported snapshot cannot manufacture provenance |
| DS22 | Crash before/after content fetch and before/after durable publication | One journal transaction owns completed state/evidence/progress/effects; pending demand survives; no lost wake or duplicate effect |
| DS23 | Actual authorized provider supplies required content after wait | Native continuation succeeds; unauthorized/missing provider response remains waiting or denied under existing host rules; manual addEvidence alone is not acceptance evidence |
| DS24 | Same process alternates old/new accounts with shared package caches | A/B old results remain exact; new policy never contaminates old bindings/certificates; incompatible cross-edition document processing is not silently enabled |
| DS25 | New-edition actual typed Order with Activation, existing timelines, exact Order mandate | Seller/Partner embedded and Customer standalone equal at all stable prefixes, both operations and restart; no unnecessary Agreement-version fetch; normal completion/journal, not overlay |

DS25 additionally requires Coordination's separately specified Q06/Q13 cases: exact/nonexact/no target, stale/future/foreign, incomplete own history, ordinary observer, child birth/prebirth/ties, initialized attach/rebase and historical cycles. Contracts-only PASS does not discharge those cases. Agent absent, Agreement-only, revoked and temporarily missing required proof are distinct cases; admission is not business execution.

## Experimental evidence and migration of assertions

The preserved run97407 demonstrates DS15/DS16 only for an isolated fixed two-step counter. It records assigned/finalized count2, NEEDS for the actual private record, rollback to count1, one-record retry and exact strict observations/gas708; repeat committed event gas160 matches strict reference. Run85630 adds repeated overflow/replay/capture refusal within that restricted overlay. Run51631 validates the plain profile after the shared compiler change. None establishes new-edition completion or signed Order integration.

Keep these artifacts and old tests unchanged as historical evidence. Port their assertions into normal edition-selected Java tests. The new normal completion tests expect established capture; historical overlay tests continue to expect `UNESTABLISHED_SOURCE_COMPLETION`. Do not reinterpret them as the same API guarantee.

## Publication gate

Before changing canonical package selection or generating a candidate publication:

1. Resolve D1–D5 in the design draft and inventory the actual native handler primitives.
2. Integrate the prose and obligation algorithms into a complete new specification with executable reference routines; reconcile every inherited full-certification/closure call explicitly.
3. Give restore/event/patch/finish/retain/export/cold/receive equivalent implementations and meaningful negative cases, not only YAML changes.
4. Build exact IDs using repository tooling, preserve old archives, then bind the candidate runtime to those generated identities.
5. Record which cases are PASS, FAIL, NOT_RUN or BLOCKED with exact source/publication IDs. Missing tests are not implicit passes.
6. Qualify A/B and C separately, including actual network/provider and journal restart; then enable the qualified new binding only for new registrations.

No external registry publication, account migration, push, merge or deployment is authorized by this proposal.
