# Mapping the two supplied proposals to this implementation

Sources are retained byte-for-byte under `sources/`; they are design proposals,
not evidence that their shown aliases or field spellings already ran on this stack.
This package follows their owner-approved operation model, with these explicit choices.

| Source proposal | Implementation / deliberate boundary |
|---|---|
| Holder and authorized actor, both Timeline Channels | Required distinct actors, concrete channels in Mandate; actual agent source also required in target |
| No mandatory guarantor | Preserved; optional co-approval not implemented |
| Owner approves whole authority program | Exact direct Pending-state approval plus protected native publication evidence |
| `Mandate/Mandate v2` | New versioned `Mandates/Mandate`; scope-bearing values use `Mandates/Operation Mandate` |
| Typed multi-operation current scope | `Scope`, `Operation Grant`, `Operation Target`, both validation types |
| Bare static required-field patterns | Explicit `Mandates/Pattern` empty-Dictionary witness using a normal type-position `valueType`; simple admissible bare patterns still work |
| BEX `$event: /message/request` examples | Current operation binding `$binding: call/request` |
| `Coordination/Sequential Workflow Operation` etc. | Current exact `Contracts/` definitions; no changed workflow semantics |
| Empty Dictionary request patterns | Untyped `{}` payload plus explicit empty-key check, matching current Blue object semantics |
| Lifecycle status subtypes | New package Text enum Pending / Active / Terminated |
| Same initial Mandate on every call | Preserved; exact historical pre-action lineage resolver |
| Stage 1 static / counter by two | Executed with amount, shape, document and functional checks |
| Stage 2 owner acknowledgement | Executed; the agent cannot acknowledge on the holder channel |
| Stage 3 provider confirmation | Optional `Qualification Mandate`; typed Request and typed Response operation payload, recorded and re-emitted |
| Earlier Unavailable status | Later integration guide's Unknown/Failed/Refused distinction; same-execution reconciliation |
| Repeated `performedBy` in Request | Omitted; exact causal signed-entry identity and committed source occurrence retain actual performer without copying a contextually refined Actor value |
| Exact `inResponseTo` | Preserved and tested; whole Response reconstructed around exact stored Request to avoid comparing contextually refined subfield identities |
| Stage 4 managed Order reactions | Executed using independently processed Order and reserved `contracts.embedded` declaration |
| Event filtering | Typed original-event filters on separate Embedded Node Channels; workflow receives normal wrapped delivery |
| MyOS performs external work | Described boundary only; local signed test provider does not call LLM/HTTP/CRM |
| Integration records original Request/Response | Recommended composition retained; no redundant second evidence request for an already recorded managed call |
| Separate responder/credential execution authority | Required outside the operation grant; an external Document Responder executor is not supplied |
| Private outcome projection | Described as attributable Event, not a fabricated Response; no disclosure bridge implemented |
| Multiple targets in one Mandate | Executed; no implicit cumulative budget across them |
| Third-party/agent-created fake Active | Initialization reset and actual protected writer checks prevent usable authority |
| Scope cleanup versus one-use business operation | Target guards remain responsible for repeat business transitions |

## Representation issues found while making the proposal executable

The current exact-value implementation distinguishes a definition/pattern from an
instance and distinguishes raw exact content from contextual inherited refinements.
These distinctions matter at required fields and nested event identities. The code
does not relax required message schemas to avoid them: patterns use a type witness,
evidence subjects are required at native configuration admission, outgoing messages
are complete typed values, and callbacks compare the complete response identity.

The first event assertion expected the Request subject to remain a one-field ref.
Execution legitimately transported it inline with the same native identity. The
corrected assertion checks the actual native subject identity, not JSON spelling.
A preliminary embedded handler filter over a contextual nested event did not match;
the final example filters the original event at the supported channel boundary.
The retained development notes distinguish these discoveries from final passing runs.

## Not imported as external factual claims

The integration guide contains vendor model/API names and proposed infrastructure
configuration. This delivery does not repeat them as verified current facts and
does not require those APIs. Its evidence protocol is vendor-neutral. All response
values in local examples are deliberately supplied test outcomes.
