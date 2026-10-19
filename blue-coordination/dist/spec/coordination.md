# Coordination: timelines and timestamped inputs to Contracts

Version 1.0.0-deterministic.1. Exact Blue types select the protocol semantics.
Status: implementation candidate for providers, verifiers, feeders and executing hosts.

## 1. Purpose: supplying timestamped inputs to Contracts

Contracts calculates a document's state by processing original events with supplied
timestamps: `process(document, originalEvent, eventTimestamp)`. It defines what
execution does with those inputs. It does not discover external events, query a
provider, establish publication order, or certify that an earlier input is missing.
Contracts itself does not impose chronological ordering on distinct events.

Coordination supplies that missing agreement about input acquisition and ordering.
For documents adopting this protocol, state at a time is calculated from the
applicable, authenticated inputs in an established order. Before processing an
entry at timestamp T, the feeder must know that all required sources are complete
through T and that it has every needed earlier entry. Seeing a new entry, or seeing
no new entries in a network response, is not enough to establish either fact.

For example, Alice's source contains an entry at 120. If Bob's source is known only
through 110, Bob might still have an entry at 115 which must be considered first.
The feeder waits for Bob's authenticated completeness beyond 120 and acquires the
missing history before choosing the next input. It also checks the public sources
that establish whether the document's required parties still have read access.

This specification defines structures called **timelines** that can provide these
facts, and the rules for using them. A **timeline entry** is an immutable occurrence
on a timeline. A **timeline provider** accepts and preserves occurrences and attests
to their history. A **feeder** acquires and verifies that history, then supplies the
appropriate original entries and timestamps to Contracts. Provider and feeder may
be separate services; a provider does not have to execute documents.

The same interface can serve a personal timeline, a company system, or a government
publication register. How those systems create their entries is their own concern.
Their interoperable obligation is to expose verifiable history, completeness and
Timeline Access through the common public interface defined here. A public endpoint
means publicly reachable HTTPS; a private timeline still requires an authorized
reader's Ed25519 signature. The publication of an endpoint does not publish its data.

### 1.1 Authority and conformance

MUST, MUST NOT, SHOULD and MAY express requirements. Cross-field rules below are
normative even where a Blue schema cannot express them. A conforming consumer
validates both the schema and these rules.

Language defines BlueIds, exact values, ancestry and referenced content. Contracts
is the sole authority for initialization, handlers, operations, embedded-document
execution, cycles, gas, rollback and completed execution records. Coordination
neither duplicates those algorithms nor changes its three-input processing API.
It establishes which original entry and historical context may be offered next.

Provider, evidence-verifier, feeder and executing-host conformance are separate claims. Loading
these types does not install a runtime. AWS services, polling intervals, databases,
publication workflows and owner login mechanisms are deployment choices. Business
participant clauses, delegated operations and timers need their own adopted rules.

Every conforming provider implements the baseline in sections 2–9 and 11, including
Timeline Access and the combined signed read operation. Section 4.2's
owner-ingest creation/append interface and section 10's
committed update-stream interface are optional extensions. Section 12 defines
feeder obligations; section 13 defines package use and validation. Sections 14–16 define execution history, conditional publication and role-specific qualification. See the
[worked examples](../docs/examples.md) for a timeline, entries, and a complete
signed HTTP exchange using these types.

## 2. Timelines, entries, providers and time

### 2.1 A timeline and its entries

A timeline identifies one immutable, append-only publication history. Its identity
is stable as entries arrive; the timeline object is not a mutable array of entries.
An entry names its timeline, timestamp, publishing actor, exact original message,
and (except at genesis) immediate predecessor. The predecessor links form its
history. Different timelines can carry occurrences with the same timestamp.

This profile uses `Signed Timeline`, a timeline whose provider promises a single
strictly increasing chain and authenticates its accepted history. The name does
not mean the timeline descriptor contains a signature or each returned entry needs
a separate signature: a signed checkpoint plus its verified chain can authenticate
many entries at once. Provider attestations can also authenticate individual entries.

The entry, including its occurrence identity and provenance, is the original event
passed to Contracts; the feeder must not replace it with just `entry.message`.
An event may concern a document, but a timeline can contain entries for many
documents. Fetching and verifying its chain must not silently omit the others.

### 2.2 Exact content and provider identity

A BlueId is calculated by the selected Language implementation, never by hashing
arbitrary JSON. A reference is resolved and verified against its BlueId. JSON and
YAML are representations of Blue content; labels, aliases and URLs are not identity.
Aliases in examples use `Coordination/`. Consumers bind them to exact exports.

`Timeline Provider` contains its public verification key and required `endpoint`:
the base HTTPS URL of the common REST API for all its public and private timelines.
Its exact BlueId is its identity. A domain subtype may supply the endpoint as an
inherited value, along with company name, address or website. Clients resolve
inherited Blue values rather than reading only fields physically present in JSON.
Exact Blue types define semantics and versions; no separate protocol version or
provider identifier is required.

A `Timeline` contains that provider, a canonical HTTPS `url`, and `publicRead`.
The URL is a real resource address for that history, not a second arbitrary ID.
Its exact BlueId identifies the complete timeline. `Signed Timeline` selects the
strict-chain rules. Different histories need different canonical URLs; URLs and
identities MUST NOT be recycled. Access documents refer to timelines using ordinary
Blue references. There are no accessId, timelineId, grantId or streamId fields.
The remaining `blueId` keys are Language content references, not extra identifiers.

An `Ed25519 Public Key` is Text containing exactly 64 lowercase hexadecimal
characters (32 bytes); an `Ed25519 Signature` is exactly 128 (64 bytes). These are
scalar refinements, not records with an invented `value` property in their schema.
`Actor` describes the identified entity responsible for an occurrence. Its two
standard categories are `Principal Actor` (human) and `Agent Actor` (non-human:
application, automated service or institution). Neither category requires provider,
principalId, a key or a fixed identity-field layout. Providers attest the attribution
in their accepted entries; the provider is already identified by the timeline.

Domain types extend these categories through normal Blue type ancestry. A government
service might define `Polish Citizen` extending Principal Actor with given names,
family name and a domain-specific citizen identifier. A bank might define `Bank
Access Service` extending Agent Actor with service and deployment details. These
are domain choices, not extra universal Coordination actor categories. Consumers
accept valid descendants, not just values with exactly the base type's BlueId.
Entity details alone do not prove authority or authentication. In particular,
labelling an actor Agent Actor does not let it publish provider control facts;
that authority comes from the provider-owned control timeline and verified
provider evidence. Reader keys remain separate from actor descriptions.

### 2.3 One provider API for public and private timelines

`Timeline Provider.endpoint` is the one REST API base. For an endpoint of
`https://timeline.acme.example`, the standard addresses are:

| Operation | Address |
| --- | --- |
| Provider discovery | GET https://timeline.acme.example/provider |
| Entries and completeness | POST https://timeline.acme.example/timelines/read |
| Exact entry | POST https://timeline.acme.example/timelines/entry |
| Referenced content | POST https://timeline.acme.example/timelines/content |
| Create Timeline Access | POST https://timeline.acme.example/access/create |
| Update Timeline Access | POST https://timeline.acme.example/access/update |
| Retrieve Timeline Access | POST https://timeline.acme.example/access/get |

The read address serves **both public and private timelines**. The request names
the exact target timeline. A public timeline accepts a bare Read Timeline Request;
a private timeline requires an authorized Ed25519 Signed Reader Request. Both
return the same provider-signed response, page and completeness checkpoint.
There is no separate public API, custom read URL or per-timeline endpoint override.

A `Public Timeline Channel` is a Contracts external channel with `provider` and
`url`. It denotes exactly `Signed Timeline(provider, url, publicRead=true)`.
The canonical `url` identifies that specific history; clients fetch it through
its provider's `/timelines/read` API. It is not another REST base. Reconstruct
document state by executing the applicable verified entries; a mutable JSON
snapshot is not a substitute for public history.

Both the endpoint and canonical timeline URL are absolute HTTPS, without userinfo,
query, fragment, whitespace, dot segments or a trailing slash. An endpoint may
contain a path prefix: `https://acme.example/api` + `/timelines/read` becomes
`https://acme.example/api/timelines/read`. The provider type may supply the endpoint,
but it must resolve to a concrete value on every provider instance. Changing an
adopted provider or timeline creates a different Blue identity; clients do not
silently substitute it. HTTPS redirects must retain the exact requested timeline
and independently pinned provider identity in the verified response.

GET `<provider.endpoint>/provider` returns an attested Provider Descriptor whose
provider and endpoint match the adopted provider. It declares the public control
timeline reserved for provider access operations. A Timeline Access channel must
match that reserved timeline; a customer-owned public timeline cannot issue
provider grants. Discovery cannot silently replace a provider.

### 2.4 Time and order

Timestamps are integer Unix microseconds in [0, 9007199254740990]. Exclusive bounds
may also be 9007199254740991. The top safe Language integer is reserved for the exclusive final bound, so even
the last permitted entry can be closed without an unsafe numeric literal. A -1 timestamp is allowed only as the genesis lower
bound of a read request. Comparisons are integer comparisons. BlueId ordering is
bytewise ordering of canonical ASCII BlueId text. Displayed wall-clock time is not
an independently certified time source; the provider is trusted for its clock.

For entries from different timelines the total order key is:
`(timestamp, timelineBlueId, entryBlueId)`. Within one timeline timestamps MUST be
strictly increasing: at most ONE accepted entry is allowed in a given microsecond
on a given timeline. If two publications arrive during the same clock microsecond,
the provider assigns distinct later microseconds or rejects/delays acceptance; it
cannot assign both the same timestamp. Different timelines may share timestamps.
The Order Key type carries the timeline and entry as Blue references; compare
their derived BlueIds as above. The full key, not just its timestamp, identifies
processing progress. The same entry can have multiple legitimate document recipients.

## 3. Authentication and signed objects

There are three separate authorities:

* the provider's authenticated publishing authority controls acceptance, and the
  timeline owner controls sharing; these may be the same account;
* a reader proves possession of a public key that currently has read access;
* the provider signs accepted facts with its pinned provider signing key.

A read grant never permits append, resharing or changing provider metadata. Owner
sessions/API tokens are deployment authentication mapped to the account allowed
to manage that timeline. This mapping must be enforced on every owner operation.
The optional owner-ingest extension also authorizes that principal to append; other
providers may publish through an internal pipeline with no external append API. Signing with a reader key
does not turn a reader into an owner. Public-read endpoints need no reader proof.
Transport confidentiality is required for private data and credentials.

A read request contains its operation type, target timeline (or the operation's
binding/access target), and query parameters. It does NOT carry requestId, provider,
createdAt, expiresAt or nonce. The target already determines the provider, and the
receiving endpoint MUST reject targets belonging to another provider. Read-only
operations need no caller-generated idempotency label. Responses correlate through
an exact Blue reference in `response.request`; identical requests have the same identity.

`Signed Reader Request` contains the exact typed request, publicKey and signature.
The Ed25519 signature signs exactly:

```
UTF8("blue.coordination.reader-request\n" + requestBlueId)
```

The signed request binds the exact operation, parameters and target; the target
binds the provider. Only read operations may use this envelope. For private reads,
the provider verifies the signature and the signing key's CURRENT Timeline Access
on EVERY use, including cursor continuation. Read permission never authorizes a
mutation. Public reads need no reader envelope or key.

This deliberately simple read signature is reusable for the same query. It is not
a proof that the signer is present now: someone obtaining the signed request can
repeat that exact read while the key remains authorized. HTTPS protects it in
transit; clients treat private signed requests as credentials. Revocation blocks
subsequent uses, and replay cannot change the signed query or authorize a write.
No nonce store or client clock synchronization is part of this baseline.

Request freshness and history completeness are separate. When a consumer needs a
prefix closed through T, it asks for minimumCompleteBefore > T and verifies the
returned bound. Replaying an old signed response below that minimum fails. Without
a minimum, an authentic older checkpoint remains evidence only of its stated
historical bound, not proof of wall-clock freshness. A provider may add stronger
session authentication as an extension, but must support this baseline.

`Provider Attestation` contains provider, object and signature. The signature is:

```
UTF8("blue.coordination.object\n" + providerBlueId + "\n" + objectBlueId)
```

The object MUST be an allowed accepted entry, provider descriptor, protocol
response, stream binding, or access-state assertion under these rules. A provider
MUST NOT expose a generic signing oracle. Every timeline governed by the signed fact must belong to that provider. Actor
details and domain message content are not redundant provider identity fields. Signatures are outside the
signed content, so no signature/BlueId self-reference exists.

`Timeline Attestation` preserves the dedicated guarantee-signing convention:

```
UTF8("blue.coordination.guarantee\n" + guaranteeBlueId)
```

Its timeline must equal guarantee.timeline; verify using that timeline's provider
key. Ed25519 here means pure Ed25519 per RFC 8032, not Ed25519ph. A valid signature
establishes a claim by the adopted provider, not honesty independent of it.

Every successful protocol response is carried in a Provider Attestation. Its
provider MUST match the adopted provider, and the response object's `request` reference
MUST identify the exact outstanding request.
Authentic cached results may be reused as historical evidence; freshness is only
what the signed bound/request actually establishes. Old evidence proves no later
state. HTTP status alone is never a completeness or access proof.

Malformed unauthenticated requests may receive unsigned errors. A signed failure
is still not evidence of an empty history. Signature checks reject wrong lengths,
noncanonical key encodings, modified content, wrong domains and mismatched sources.
Implementations MUST use a maintained Ed25519 implementation.

For this preview the provider key is immutable for the lifetime of its timelines.
Routine deployments preserve it. A lost or replaced key requires a new provider
identity and explicit consumer adoption; no URL, descriptor refresh, cross-signing
or new advertised key silently migrates old history. Reader-key rotation is an
ordinary access-set change, with old/new keys simultaneously granted if needed.

## 4. Accepted history and provider publication choices

### 4.1 Required properties of every published history

A provider decides how to establish a timeline and accept occurrences. A government
provider may approve publications through a statutory workflow; a company may
import committed records from its internal system; a personal provider may offer
an owner-only append API. None of those ingestion mechanisms is mandated here.
A reader's signature and a Timeline Access grant never confer publishing authority.

Whatever the ingestion mechanism, every accepted `Timeline Entry` contains timeline,
timestamp, actor and exact message. prevEntry is absent at genesis; otherwise it
identifies the immediately preceding accepted entry. The provider authenticates the
publishing actor; a caller-supplied actor label alone is not sufficient. `source`
may carry authenticated submission provenance. If the message is a recognized
Contracts Operation Request, entry.operation identifies that same exact complete
request; otherwise it is absent. Acceptance does not assert business execution.

The timestamp is greater than the predecessor's timestamp and at least the
provider's durably sealed completeBefore boundary. It is the provider-assigned
publication position. An occurrence's earlier real-world time belongs inside the
message, not in a backdated insertion into a closed prefix. No in-flight or later
acceptance may insert behind the accepted head or a sealed boundary.

The provider durably commits the entry and head before attesting to acceptance.
Concurrent acceptance, read/seal and access-change operations have a consistent
linearization order, including after restart. Accepted entries cannot be edited,
deleted, forked or reordered. A correction is a later entry. IDs cannot be recycled,
and a public timeline cannot retrospectively become private. Archival must retain
promised evidence or report unavailability, never invent an empty replacement.

Every provider exposes the common read interface and the Timeline Access operations
in sections 6, 7 and 11, regardless of how it accepts entries. A public history's
publicRead flag grants everyone access. Private histories use confirmed executable
Timeline Access documents. Reader grants never give publishing or owner authority.

### 4.2 Optional owner-ingest interface

A provider advertising the owner-ingest operation types additionally implements `Create Timeline
Request` and `Append Entry Request` through the routes in section 11. These types
are conveniences for providers such as the planned AWS service, not prerequisites
for a government or existing enterprise source to participate in Coordination.

Creation is owner-only, takes explicit publicRead, and returns the exact Signed
Timeline in `Timeline Created Response`. Append is owner-only, takes timeline,
message and optional expectedLastEntry, and derives the actor from authentication.
`Append Entry Response` returns the accepted entry and its Provider Attestation.
An expectedLastEntry mismatch is HEAD_CONFLICT with no acceptance. Entry content,
head, result identity and request deduplication commit atomically.

### 4.3 Idempotent mutations

Standard owner-ingest and Timeline Access mutation requests carry a required
idempotencyKey, scoped by authenticated owner and operation. The stored fingerprint
covers their logical parameters. Reusing the key with the same parameters returns
the original accepted result; different parameters yield IDEMPOTENCY_CONFLICT.
Records live for the affected timeline or access document's lifetime. This key is
not part of read requests, actor identity or public access-update operations.
Rejected uncommitted operations do not reserve successful result identities.
Provider-specific ingestion must still satisfy section 4.1.

## 5. Completeness: two valid proof forms

### 5.1 Explicit guarantee

`Timeline Completeness Guarantee(timeline, completeBefore, lastEntry?)` means all
accepted entries with timestamp < completeBefore are fixed and no future entry
can appear there. lastEntry is the last entry INSIDE that prefix, not necessarily
the current head. Its absence positively asserts an empty prefix.

The combined `Read Timeline Request` MAY specify minimumCompleteBefore. Its
`Timeline Read Response` always contains a Timeline Attestation meeting that bound
or returns BOUND_UNAVAILABLE. Use limit=0 when only the checkpoint is needed;
positive limits fetch entries under the same checkpoint (section 6). It MUST NOT invent a distant future clock value merely
to satisfy a request. Without a minimum it seals a current logical frontier.
Bound advancement and appends use the same durable serialization mechanism; a
bound cannot overtake an uncommitted earlier append that may still succeed.
Completeness bounds do not decrease. At the maximum bound, further append fails
TIME_EXHAUSTED. Silent timelines MUST support explicit bound advancement.

The verifier resolves the attested guarantee and every newly needed entry from an
already established prefix (or genesis) to lastEntry. It checks identities, same
timeline, predecessor adjacency, strict times, each entry below the bound and exact
final head equality. A headless guarantee needs no entries and proves the empty
prefix. A hash is not a substitute for missing content needed by a consumer.

### 5.2 Authenticated successor evidence

`Timeline Successor Evidence` contains a Provider Attestation of an accepted entry
S and the ordered entries extending an optional already-established `after` anchor
through S. Check the attestation, exact adjacency, source identity, strict time
order and agreement with all retained history.

The strict-chain promise then establishes completeness strictly BEFORE S.timestamp.
The resulting prefix head is S.prevEntry, or absent when S is genesis. S itself is
not within this derived prefix. Its content may be retained as authenticated, but
a bound > S.timestamp is needed to settle S's complete cross-timeline time group.

Example: A.timestamp = T-1, S.timestamp = T+1, S.prevEntry = A. Once A's prefix is
established and S is authenticated as accepted, there is no entry at T; the derived
completeBefore is T+1. Merely receiving two sorted records, a submitted append
request, or an unauthenticated link proves nothing. A direct predecessor link
proves the gap; it does not supply an unknown earlier prefix. An authenticated
later checkpoint committing to S can also authenticate S without an entry-specific
signature, provided the full required chain is verified.

An entry exactly at T establishes only completeBefore=T by this rule, insufficient
to finish processing timestamp T. A quiet source offers no future successor; use
an explicit guarantee. These two proof forms feed the SAME retained-prefix model.
A provider MUST implement explicit guarantees and accepted-entry attestations;
consumers SHOULD accept both forms.

## 6. One read operation: entries and completeness

Every provider MUST support `Read Timeline Request` at `/timelines/read`.
`Timeline Read Response` always contains a signed checkpoint for the requested
timeline, correlated to the exact request. There is no separate mandatory
completeness operation. A reader can both acquire entries and establish the closed
frontier in one exchange, including when no new entries have appeared.

limit is a required nonnegative integer. With limit=0, return only the checkpoint:
page MUST be absent, and the request MUST NOT contain afterEntry, afterTimestamp or
cursor. This is a completeness-only query, not an empty-history assertion. The
checkpoint may name a lastEntry which the reader still needs to acquire. With
limit>0, page MUST be present (even for an empty history), and its checkpoint MUST
be exactly the response checkpoint. The provider's advertised maxPageSize is the
maximum positive limit.

minimumCompleteBefore is an optional integer exclusive bound in the permitted
range. It applies to a fresh read, with or without entries. It MUST NOT accompany
a cursor: continuation preserves its original checkpoint. The provider either
seals a frontier at least as large as requested or returns BOUND_UNAVAILABLE; the
client cannot force future timestamps. A checkpoint-only response does not prove
that the feeder already possesses the closed prefix's contents.

For limit>0, the request accepts at most one of:
afterEntry, afterTimestamp, or cursor. With none, start at genesis. afterTimestamp
is EXCLUSIVE and may be -1; return entries with timestamp > it. Within a strict
timeline timestamps are unique, but exact-entry/cursor continuation is preferred.
A read starting at a timestamp makes no claim about earlier unestablished history.
An afterEntry anchor must belong to the requested timeline and selected checkpoint;
unknown or later anchors fail rather than silently seek elsewhere.

The first request seals/selects a complete prefix ending at an immutable checkpoint
(a Timeline Attestation). A `Timeline Entries Page` contains that checkpoint,
ordered entries, optional predecessor, hasMore and optional nextCursor. The
predecessor is the immediate entry before the first returned entry, if any. For an
empty result it is the last accepted entry in the selected prefix at or before the
requested lower position, if any. The response attests this boundary selection.

A `Timeline Read Cursor` binds the timeline, checkpoint, and exact next position
by afterEntry or the initial afterTimestamp. It is an identified value, not an
authority-bearing bearer token. The server verifies/recognizes the checkpoint,
validates the anchor within it and rechecks the reader's CURRENT authorization on
every page. Cursor signatures do not bypass revocation. A cursor cannot switch
sources, bounds or anchors. A checkpoint-bound cursor remains valid as long as
its promised history is available; this profile has no artificial cursor expiry.

Pages enumerate EVERY successor after the selected lower position below the
checkpoint bound. They MUST NOT filter by document ID, actor or message while
claiming unfiltered completeness. The server may return fewer entries than limit
for byte constraints, but a nonterminal page has at least one entry and advances
the cursor. A single entry that cannot fit returns LIMIT_EXCEEDED, not an empty
successful page. Maximum entries per page is advertised in Provider Descriptor; there
is no protocol maximum total history length.

hasMore is true exactly when another matching entry remains in THIS checkpoint.
A successful hasMore=false is a permanent assertion: every accepted entry in the
requested suffix strictly before the signed completeBefore bound has been returned
across this read's pages,
and no future acceptance can add another entry below that bound. This applies to
empty results as well. "Until then" means this explicit bound, not an unstated
HTTP arrival time. For a continuation page it is the original checkpoint's bound,
not a newer clock time. Earlier entries before the requested lower position may
exist; a timestamp seek does not claim to have returned them.
When hasMore=true, nextCursor is required and anchored at the page's last entry. When false,
nextCursor is absent and the final returned/predecessor position agrees with the
checkpoint's head (subject to an empty interval when lower bound >= checkpoint).
Concurrent appends beyond the checkpoint do not appear in continuation pages.
Start a fresh request after that checkpoint head to acquire them.

For timestamp seeking, predecessor.timestamp <= afterTimestamp and the first entry
(if any) has a greater timestamp. The attested boundary identifies the selected
suffix. To extend an existing contiguous prefix the consumer MUST reconcile that
predecessor with its own exact anchor; an arbitrary timestamp seek cannot certify
that skipped older history was processed. A lower bound beyond the checkpoint is
an empty query interval, not completeness beyond the checkpoint.

`Timeline Range Evidence` is an assembled proof: checkpoint plus every contiguous
entry after a previously established anchor through the guarantee's lastEntry.
Only after all pages/links and the ending head are verified may a consumer advance
usable completeness. hasMore=false, a page count, a cursor or max(timestamp) alone
is not evidence. Loss, duplication, reordering or mixing pages from different
checkpoints cannot silently advance it.

`Fetch Timeline Entry Request` and `Resolve Timeline Content Request` provide exact
entry/content retrieval. Their `entry` and `content` fields are required exact
Blue references. Private content resolution is scoped by an authorized
timeline and reachability from its accepted entries or its access document. Knowing
a BlueId or finding the same blob in storage grants no extra access. Public access
histories publish their complete required content closure; private message bodies
are not part of that closure merely because an access document names the timeline.

## 7. Timeline Access is an executable Blue document

### 7.1 Document structure and authority

`Timeline Access` has two lists, `allowedTimelines` and `allowedKeys`, and a real
`contracts` section. Each listed key is permitted to read every listed timeline,
including entries, referenced content and completeness. Either list may be empty;
values must be distinct. Every timeline's provider must equal the provider declared
in `contracts.provider`. The lists contain exact timeline references and Ed25519
public keys. There are no invented document or grant IDs.

`contracts.provider` is a Public Timeline Channel: provider and URL of the provider's
reserved public control timeline. The adopted, signed Provider Descriptor must
confirm that source. A customer's public timeline and an arbitrary Agent Actor
label cannot confer this authority. The provider is not repeated at the root of
the access document or alongside each reference in its allowed list.

`contracts.update` has type `Update Timeline Access`, a specialization of the
standard Contracts Sequential Workflow Operation. It is bound to channel `provider`.
Its typed Timeline Access Update arguments contain BOTH replacement lists. Its
ordinary BEX checks reject foreign-provider timelines and duplicates; its standard
Update Document step replaces both fields in one atomic Contracts transition.
It does not mutate contracts, the provider channel, or unrelated document content.
The type supplies this executable definition; the examples show the two contract
members explicitly for readability. Instances must preserve this definition and
channel binding. A document containing a different update program is not evidence
under these rules, even if it claims the base type.

### 7.2 Publication, updates and current state

The initial exact document is published as the message of an accepted entry on
that provider control timeline. This publication confirms the initial lists and
establishes its initial Blue identity. The publisher is an Agent Actor or a domain
subtype. A self-authored document with no confirmed publication grants nothing.
The public control history needs no access document of its own: it is unconditionally
public. Several access documents may share this history.

An update is a standard Contracts Operation Request carried as the message of a
later control entry, also copied exactly into the entry's `operation` field:

- `document` references the original, published access document;
- `channel` is `provider`, and `operation` is `update`;
- `request` is a Timeline Access Update with both replacement lists.

The original document is the stable target for every update. The feeder resolves
it through established Contracts lineage to the current execution state. There is no version precondition,
revision counter or previousChange chain. Each accepted operation replaces both
lists completely, in immutable control-timeline order. If two valid replacements
are accepted, the later one determines the lists; they are not merged. An owner
that wants to preserve an earlier change includes it in its desired replacement.
Contracts supplies execution, checkpoints, rollback and the resulting exact
document. Feed the complete original Timeline Entry, never just its message.
An invalid update fails atomically. The provider MUST validate the operation
before committing an accepted permission update; it cannot publish success and
then enforce different permission sets. Already accepted control history cannot be
rewritten to repair a bad update. Treat a contradictory provider assertion as an
integrity failure, not as permission to skip it.

A verifier starts from the confirmed initial document, initializes it under
Contracts with this exact channel implementation, and processes the complete
applicable history in established order. Shared-history entries for other documents
are retained for chain verification, then dispositioned by their exact target
lineage. Processing yields an actual current Timeline Access document, not a
separate custom access-state record. To establish state as of B, acquire complete
control history strictly through B. A signed current snapshot alone establishes
only the provider's claim; it does not replace publication and replay evidence.

### 7.3 Owner requests and enforcement

`Create Timeline Access Request` asks the provider to publish the initial lists.
`Update Timeline Access Request` names the initial access document and both desired
replacement lists. These are owner-authenticated requests, not reader-signed
requests. A provider verifies that the owner may manage
the access document and every affected timeline, including both removed and added
ones. An empty initial timeline list must not allow claiming another owner's
resource later. The provider constructs and publishes the standard operation.
The same idempotency rules as other owner mutations apply. Repeating identical
initial content may reuse its identical Blue document; never invent an arbitrary
ID just to make identical permission documents distinct.

A `Timeline Access Response` contains `access` (initial exact document), `current`
(executed document), `publication` (attestation of its initial control entry), and
`lastEntry` (attestation of the latest relevant publication/update). The public
Get Timeline Access Request names `access` by exact reference. Multiple documents
may grant the same key access to the same timeline: effective private read access
is the union of current confirmed documents. Removing one grant cannot revoke a
separate still-valid grant. Public timelines and owner reads retain their own
independent authority.

Publishing the accepted change, updating the enforced permissions, and recording
the owner request's result MUST be one logical durable transition. Every private
read, including cursor continuation, rechecks the resulting current grants.
Removing a timeline or key revokes the corresponding pairs unless another grant
still permits them. Re-adding them restores access to retained history. A read
grant never confers append, update, reshare or owner capability.

The provider publishes the initial documents, operation arguments, definitions,
control entries and evidence through public read/content routes. Everything needed
to locate and verify them is included in the shared document or its public content
closure. This remains available after revocation. Keys, timeline references and
changes on public control history are public metadata.

## 8. Using access evidence as an input dependency

Consumers can embed the executable access document and verify its public source
alongside other timeline inputs. Keep acquisition of that public source independent
of access to private data: revoking a private key must not prevent observing a
later restoration. Establish current permissions from confirmed execution and
complete public history, not a Boolean supplied by a caller.

Participant definitions, required party keys, business admission/amendment rules
and how an application represents a pending state belong to the consuming document.
They are not defined here. Coordination provides permission facts and their input
dependencies; it does not authorize changes to a business agreement.

## 9. Portable evidence and response failures

Mandatory failure codes are INVALID_REQUEST, UNAUTHENTICATED, ACCESS_DENIED,
NOT_FOUND, HEAD_CONFLICT, IDEMPOTENCY_CONFLICT,
BOUND_UNAVAILABLE, LIMIT_EXCEEDED, TIME_EXHAUSTED, UNAVAILABLE and INTEGRITY_ERROR.
`Provider Failure` contains code, retryable and optional safe detail. INVALID_REQUEST
includes malformed cursor, wrong identity and invalid field combinations. Unknown
required types/profile behavior fails closed. A public error need not disclose
whether an inaccessible private timeline exists; NOT_FOUND may mask ACCESS_DENIED.
Neither can be interpreted as an authenticated headless guarantee.

An adopted verifier detects mismatched content, gaps, equivocation against a
retained prefix, and contradicting bounds or executed access states. It retains the
conflicting evidence and stops that source; it does not choose a new history by
arrival order. Nondecreasing bounds alone cannot detect every dishonest fork.
Operators controlling keys and storage can sign competing histories to isolated
readers. Signatures/commitments do not prevent that; witnesses, comparison or
attested continuity may be added only as explicit stronger evidence profiles.
No reader requiring such a profile may silently accept the baseline instead.

## 10. Optional committed update stream

### 10.1 Reuse ordinary timelines, add explicit coverage

A push connection, SSE notification or WebSocket is just transport. It proves no
absence. An ordinary strict timeline already supports successor/guarantee evidence
for ITS OWN entries; it cannot prove completeness of other timelines without an
explicit coverage promise. This optional profile defines that promise.

`Timeline Update Stream` contains its provider, generation and a public,
provider-owned Signed Timeline used as its feed. `Timeline Stream Batch` is an
ordinary message on that feed, containing stream, sequence, fromInclusive,
completeBefore and a list of announcements. Feed predecessor links and normal
provider attestations authenticate the batches; there is no second block hashing
algorithm. The feed is dedicated to batch messages for that stream generation and each entry
is attributed to an Agent Actor or its subtype, published by the provider itself. A batch may not announce its own feed entries: only
other bound data timelines are covered, avoiding self-referential commitments.

The first batch has sequence=0. Each next batch has sequence+1 and fromInclusive
exactly equal to the preceding completeBefore. Windows are nonempty [fromInclusive,
completeBefore); empty announcements still advance coverage. Their boundary times
are DATA timeline time, not the enclosing feed entry's timestamp. A quiet provider
can publish empty batches. A later feed entry alone cannot advance data coverage
beyond its explicit batch bound.

### 10.2 Membership and commitments

A provider-attested `Timeline Stream Binding` maps a timeline to stream,
generation (via stream), opaque timelineTag and immutable [fromInclusive,
untilExclusive) eligibility. Its span is nonempty. Bindings are available to that
timeline's authorized readers; knowledge of a tag is not read permission. The tag
is 32 random bytes encoded as 64 lowercase hex, unique per stream generation and
binding; tags are not reused. A timeline has at most one selected binding for a
given timestamp. The provider must fulfill that entire interval even if it stops
advertising the binding. Switching feeds/tags uses adjacent nonoverlapping binding
intervals and explicit consumer adoption. There is no silent shortening, generation
reset or reassignment of an already attested binding. Outside known coverage use
normal timeline acquisition. Bindings may be finite and renewed.

Each accepted data entry within a binding's interval has exactly one announcement
in the matching batch. All appends/in-flight acceptances covered by a batch must be
settled before its window is sealed, and future acceptance behind that boundary is
forbidden. The provider coordinates this fence across all bound timelines; there
is no obligation to list all timeline identities publicly.

`Timeline Announcement` contains timelineTag, timestamp and entryCommitment.
Announcements sort by (timestamp, timelineTag, entryCommitment) using ASCII for
text. This order only makes the batch deterministic. Document input order remains
(timestamp, actual timelineBlueId, actual entryBlueId). In particular, a tag order
cannot settle cross-timeline timestamp ties for a document.

For each announcement choose an independent cryptographically random 32-byte salt.
It is not in the public feed. Define LP(s) = 4-byte unsigned big-endian UTF-8 byte
length followed by UTF-8(s). Define U64(n) as 8-byte unsigned big-endian. Then:

```
entryCommitment = lowercaseHex(SHA256(
    ASCII("blue.coordination.stream-entry\n")
    || LP(streamBlueId) || LP(timelineTag) || U64(timestamp)
    || LP(entryBlueId) || saltBytes))
```

streamBlueId already commits to provider and generation. Lengths must fit U32;
fixed numeric bounds remain those of section 2. SHA-256 here is a separately named
commitment, never a BlueId. The provider retains the salt and exact entry.

A `Fetch Stream Entry Request` identifies binding, exact batch feed entry and
zero-based announcementIndex. It requires current target read access. The response
contains exact data entry and salt. Verify the feed entry, index bounds, binding
span, tag, timestamp, recomputed BlueId and commitment. Global BlueId/content
lookup MUST NOT bypass access to this opening. Stable tags reveal activity patterns;
this is pseudonymization, not traffic secrecy. Stronger privacy can use no stream.

### 10.3 Proof, acquisition and restart

`Timeline Stream Evidence` contains the binding and its provider attestation,
afterBatch (optional previously established anchor), and every authenticated feed
entry needed to cover the claimed window. Without afterBatch, start at batch 0.
With it, first establish that exact prior batch and its complete chain; never trust
an arbitrary latest block. Check sequences, feed links, adjacent windows, signatures
and overlap consistency. Only the intersection of binding eligibility and verified
batch coverage proves anything about the target timeline. All announcements in
those windows must be examined for that tag. An inclusion proof for one row does
not prove absence of omitted rows. Filtered-proof formats are not defined in v1;
servers may offer hints, but complete batch verification remains required.

Maintain distinct announcedThrough and usableCompleteBefore. Persist all matching
announcements and outstanding fetch obligations before exposing announcedThrough.
An announcement with unavailable content blocks processing wherever it could be the
next required input; it is not an absent event. For a usable contiguous source
prefix, resolve all needed openings, verify data-chain adjacency against the
established anchor, and reconcile checkpoint heads and overlapping explicit
proofs. Coverage may advance partially before a known later missing entry, but
never through it. Announcements for other documents do not require re-verification
per document, yet every document retains its own processing obligations.

A new timeline subscription may need historical backfill even when the stream's
global cursor is advanced: previously ignored announcements may be needed now.
Replay retained batches or acquire normal ranges. Restart resumes durable exact
feed/data anchors; duplicate import is idempotent. A stopped stream proves only its
last covered interval. Feed gaps, unavailable openings and binding expiry use
ordinary acquisition or WAITING, never an assumption of no entries. Streaming is
optional acceleration; the minimal provider and all correctness tests work by
polling. No stream is required to implement the accepted-successor proof.

## 11. Required public interface and optional publication API

Every provider MUST expose the publicly reachable HTTPS API declared by its
endpoint, however it accepts entries internally. The endpoint may be supplied by
the provider type or instance. `GET <provider.endpoint>/provider` returns an attested
Provider Descriptor with that API base, its public control timeline, maxPageSize,
and optional operation type BlueIds encoded as Text. The descriptor, provider identity/public key and control timeline
are included inline for public bootstrap; this request needs no authentication. Initial provider adoption is an independent trust decision; a URL
or discovery response cannot replace a pinned provider identity.

All operations below use POST, `Content-Type: application/json`, and Blue JSON
request bodies. Private reader operations MUST accept `Signed Reader Request`
with Ed25519 proof under section 3. Owner login is not a prerequisite for a granted
reader to use these operations. Public timelines and access discovery also accept
unsigned requests. A supplied signature is still validated, even on a public
source. POST keeps signatures and structured cursors out of URLs. Providers may
rate limit but cannot require their proprietary login as a substitute for this
portable authorized-reader path.

### 11.1 Baseline operations (required)

| Path | Request | Response | Authority |
| --- | --- | --- | --- |
| /timelines/read | Read Timeline Request | Timeline Read Response | reader/public |
| /timelines/entry | Fetch Timeline Entry Request | Timeline Entry Response | reader/public |
| /timelines/content | Resolve Timeline Content Request | Timeline Content Response | reader/public |
| /access/create | Create Timeline Access Request | Timeline Access Response | owner of affected timelines |
| /access/update | Update Timeline Access Request | Timeline Access Response | owner of affected timelines |
| /access/get | Get Timeline Access Request | Timeline Access Response | public |

All paths are appended to Timeline Provider.endpoint.
For access requests, use the provider named by its reserved public channel;
an existing access document contains this channel. Before creating the first access
document, discover that reserved channel through a known timeline's API base.

The read operation combines bulk entries and completeness; entry/content routes
resolve individual evidence or referenced bodies without rereading a range.
Access creation/change use the provider's owner authentication and policy; a
reader signature alone never authorizes them. The provider may approve public
register entries through its internal system while separately authorizing a
principal to manage Timeline Access. A denied owner mutation is a typed failure,
not a false confirmation of a grant.

Access get returns the initial document, latest executed document and publication/update evidence.
The caller reads the public control timeline to establish a complete history and
freshness. It must not treat an unconfirmed arbitrary document as provider-issued evidence.

### 11.2 Keyless public reads and pagination

Every baseline provider MUST support the following path for every public timeline,
including its Timeline Access control history:

1. Read the Public Timeline Channel, derive its exact public Signed Timeline, and
   resolve the provider endpoint using section 2.3. Verify the signed descriptor
   from `GET <provider.endpoint>/provider` against the adopted provider and channel.
2. POST a bare `Read Timeline Request` to `<provider.endpoint>/timelines/read`, selecting
   that exact public timeline. Omit the Signed Reader Request wrapper entirely. No reader
   publicKey, signature, requestId, timestamp, nonce, account, API token, cookie, client certificate, private
   target-timeline permission or owner session may be required.
3. Receive the same `Provider Attestation` of `Timeline Read Response` used for a
   private read. Verify the response and checkpoint with the already public
   provider key. Keyless access means the caller owns no key; it does not remove
   the provider signatures which make the history portable evidence.
4. If hasMore=true, submit page.nextCursor in another bare request to the SAME
   endpoint. The request BlueId correlates the response; the cursor fixes the
   checkpoint. No new client label, clock value, nonce or signature is required.
5. If hasMore=false, the selected suffix at that checkpoint is exhausted. Poll
   later using afterEntry equal to the known head, or no selector for a still-empty
   timeline. Use limit=0 without a selector for a checkpoint-only refresh.

The baseline deliberately uses POST for both public and private reads so requests,
filters, cursors, responses and verification have one definition. Discovery uses
GET. A provider MAY offer additional GET snapshots or feeds, but clients cannot assume they
exist, and an arbitrary JSON list is not baseline completeness evidence. No
nextPage URL is required: nextCursor names a position in this timeline, not another
server or an authorization token. Providers MUST NOT substitute redirects to a
login page for public data or condition public access on the target grant still
being active. Ordinary public rate limits may return typed availability failures;
those failures are never interpreted as an empty history.

Public access discovery (`/access/get`), exact-entry retrieval and required
public content resolution likewise accept bare requests. A supplied reader
signature, if any, is validated; silently ignoring an invalid supplied signature
is not an alternate path into the private API. Local clauses continue receiving
public access changes while the private timeline is revoked or unavailable.

For concrete actors, both Hello entries, a complete Timeline Access document and
public requests/responses, see [the worked examples](../docs/examples.md).

### 11.3 Optional extensions

| Extension | Path | Request | Response | Authority |
| --- | --- | --- | --- | --- |
| owner ingest | /timelines/create | Create Timeline Request | Timeline Created Response | owner |
| owner ingest | /timelines/append | Append Entry Request | Append Entry Response | owner of affected timelines |
| committed update stream | /streams/binding | Get Stream Binding Request | Stream Binding Response | reader/public |
| committed update stream | /streams/entry | Fetch Stream Entry Request | Stream Entry Response | reader/public |

Only advertised operation types require their optional routes. The descriptor
uses their exact BlueIds, not independently versioned capability labels. Read an optional stream's own
history through the ordinary combined read endpoint. A provider can conform with
no public append operation and no aggregate stream. Additional GET conveniences,
owner list/UI APIs or ingestion workflows must preserve the baseline semantics.

### 11.4 Content transport and results

A wire request MUST include its typed request body inline in the reader envelope.
Definitions are identified by exact exported BlueIds, not unbound type aliases.
Providers and timelines may be referenced by their adopted BlueIds. Other client
inputs (such as a cursor) must be inline or already known to the provider; servers
do not fetch arbitrary client-supplied URLs to interpret a request.

A successful wire response MUST include its typed response inline in the Provider
Attestation. The read response includes its checkpoint and guarantee inline; for
a page it also includes the page, returned entries, immediate predecessor (if any)
and next cursor inline. The page may reference the identical top-level checkpoint.
A lastEntry/prevEntry link remains a BlueId reference: transmitting it does not
recursively transmit all older history. Original message bodies and actors may be
inline or retrieved through authorized content resolution. Inline expansion must
preserve the Language identity of the referenced value; it is never a license to
rewrite signed content. A receiver verifies identities before using any content.

Responses attest the stated response type or Provider Failure. Success is HTTP
200; invalid request 400; missing authentication 401; denied access 403 (or
nondisclosing 404); unknown resource 404; state/idempotency conflict 409; size limit
413; rate limit 429 with Retry-After and UNAVAILABLE; temporary availability/bound
failure 503; detected integrity failure 500. Typed failure codes, not status or
localized text, determine failure handling. Failures never establish absence.

Cache private responses only in authorized scopes. Each read page, single-entry
fetch, salt opening and content fetch rechecks current access. A public copy of a
grant is evidence, not a bearer credential. Complete HTTP examples and public test
signatures are included in [docs/examples.md](../docs/examples.md).

## 12. Feeders: calculating document state from established history

A feeder is the host-side component that turns acquired history into valid inputs
for a particular document. It combines acquisition, evidence verification and
input selection; implementations may split those jobs into separate components.
To calculate state through a requested timestamp T, it must establish all required
history through T, process or explicitly dispose of every relevant entry in order,
and retain the evidence and positions behind that result. It must not claim state
through T while a required source, access history or earlier input is unresolved.

The installed Public Timeline Channel implementation must authenticate the
original entry against its exact declared provider and derived public timeline,
verify the timestamp equals the original entry's timestamp, and establish its
required prefix and completeness beyond that timestamp. Its invocation evidence
is bound to the exact receiver state, channel declaration and original event.
Only then may it accept the entry as external input. It does not unwrap or rewrite
that entry. Contracts remains responsible for operation dispatch, lineage
resolution and execution checkpoints. A mere URL match, claimed actor or caller-supplied
acceptance Boolean is insufficient. For Timeline Access, additionally confirm the
provider's reserved control timeline and provider publication as section 7 requires.

An importer is keyed by adopted provider, exact timeline and evidence policy. It
polls or streams independently of the number of documents consuming that history.
It retains verified content, exact prefix head, completeBefore, evidence and
outstanding obligations durably. It can share verification across 100 documents;
it MUST preserve authorization boundaries when exposing private content to them.
One reader's permission does not grant another document or tenant access.

For each next step:

1. Establish the required source set for the exact current/historical Contracts
   view, including active channels, required embedded views and pending historical
   attachment obligations. Include public access-control sources needed for its
   adopted access requirements. Do not inspect only currently noisy sources.
2. Acquire contiguous history and enough verified coverage to identify the least
   unresolved candidate K. For every relevant ordinary source, require
   completeBefore > K.timestamp; equality does not close a cross-source tie.
3. Verify required access at the appropriate established control position. Account
   for public revocation/restoration inputs without deadlocking their acquisition
   on unavailable private sources. Business progress can remain pending while the
   separately declared public control path advances.
4. Reconcile actor, timeline, full order key and target-operation addressing with
   the receiver's exact context. The original entry remains the original event;
   recognized operation fields must agree with its message. Access to read a
   timeline is not business authority to invoke an operation.
5. Freeze the selected entry, exact dependency views, admission evidence and
   source-set version. Invoke Contracts with its original three-input interface.
   Use only completed results admitted under Contracts' own rules.
6. Durably publish result/progress together, or preserve a retry obligation. Record
   skipped/nonmatching entries as explicit receiver dispositions, not invented
   Contracts execution. Recompute affected requirements after topology changes.

An Operation Request's document target, when present, must resolve through
established exact lineage. Missing lineage waits. Unaddressed operations use the
declared channel and participant rules; malformed operations cannot be reclassified as harmless
messages. This baseline covers direct authority. Any delegated authority needs its
separately adopted semantics and evidence; unknown delegation fails closed.

`Source Coverage` and `Input Selection` are portable descriptions of the facts used
by a verifier (source, anchor/head/bound, evidence, selected original entry and order
key). They are not new Contracts completion formats or self-authenticating execution
certificates. A dishonest caller cannot set ready=true to install trusted progress.

The required-source set is a set over the finite established graph, not a count of
infinitely many paths through cycles. Multiple occurrences can share acquisition
but retain distinct processing/history obligations. Adding a dependency requires
its relevant history even if it predates the receiving document's latest step.
Removing an edge never erases obligations of earlier captured occurrences. Select
historical child results appropriate to the receiving position, not ambient latest
state. Raw child inputs do not automatically become parent business inputs.

Cycles, local rounds and embedded result incorporation execute exactly as specified
by Contracts. Coordination adds no alternate SCC execution, global FIFO barrier or
recursive document evaluator. Hosts may index dependency membership however they
choose as long as these historical and coverage obligations hold.

Notifications only wake acquisition/processing; they are not proof or durable work.
A crash between acquisition and publication cannot lose an obligation or expose an
unverified bound. Resumption never rewinds a committed document merely to fit a new
provider claim. Contradictions are integrity failures; missing resources are WAITING;
a confirmed access deficit is PENDING_ACCESS under the participating clause rules.

## 13. Package use and validation

This is an explicitly selected candidate with new package, rules and type BlueIds.
Do not silently rebind old identities or load old and new Coordination aliases
in the same context. A package import supplies definitions, not an implemented
provider, feeder or Contracts runtime extension.

The accompanying reference model and tests check identity, signatures, actor
ancestry, immutable history, completeness, pagination, access and feeder ordering.
The worked access document also executes through the pinned Contracts processor
with this package's public-channel verifier; updates are not simulated by a custom
list-assignment interpreter.
The builder checks pinned dependencies, frozen rules and reproducible distribution.
Live provider conformance additionally requires durable crash recovery, concurrent
acceptance/seal/access serialization, availability and an interoperating client.

Ed25519 signatures use the algorithm in RFC 8032. Language defines Blue content
identity; Contracts defines execution. No alternative cycle or execution algorithm
is introduced here.

This edition selects the exact 10M gas prerequisites. Previously published content retains its original semantics.

## 14. Execution history and frozen obligations

### 14.1 Authority and identity

This chapter belongs to the same Coordination publication as sections 1–13.
There is one Coordination namespace and one selected rules identity. It adds no
second execution protocol or alternate provider signature format. In particular,
the provider's `blue.coordination.guarantee\n` domain, provider key selection,
entry bounds, full ordering key and strict completeness rules remain unchanged.
An older signed object cannot be relabelled as an object of this edition.

Executing hosts MUST select the exact Contracts edition required by this
publication. Contracts owns initialization, local turns, admission, receiving,
event occurrences, work order, gas and atomic rollback. A Coordination host
MUST NOT reconstruct those results with its own business-state mutations.
Repository availability is separate from executable role registration. Every
snapshot, source completion and restored invocation MUST have the exact selected
active binding sequence. A superset of available implementations is not permission
to promote a snapshot. Timer roles are optional capabilities outside the non-timer
profile. Ordinary supplied timestamps and ordering remain mandatory.

`Document Epoch` identifies a stable result by original document identity, exact
current document, epoch and History Position. Epoch zero is the first committed
initialization result. `History Position` additionally identifies each retained
processing or receiving transition by its monotonically increasing position,
immediate predecessor, stable flag and Processing Receipt. Position zero has no
predecessor; every later position names exactly the preceding committed position
of that owner. A catch-up position may retain the last stable epoch. No counter
alone proves ancestry, completeness or commitment. Exact operands may be unvalued
Blue definitions: protocol presence is checked as exact content, not truthiness.

`Processing Receipt` retains the original Contracts receipt commitment and exact
before/after projections, source receipts, member results and ordered emitted
occurrences. INITIALIZE has no external cause; PROCESS retains the original entry
and its timestamp; APPLY retains the ordered source receipts and attachment
obligation being discharged. It MUST NOT claim a second execution of the source's
operation. `Member Result` describes only that owned member. Equal event values
retain distinct `Emitted Occurrence` ordinals and native occurrence identities.
The full Contracts evidence, including Dispatch decisions when present, is retained
without removing fields or sorting output lists. A summary is not a substitute.

### 14.2 Independent owners and receiver prefixes

The publication policy is `independent-owner-prefix/1`. An acyclic source may
commit once its own applicable inputs and dependencies are ready. A waiting or
failed consumer MUST NOT invalidate, roll back or prevent an independently sealed
source result. The consumer records its obligation to that result. Consumers of
that consumer wait for its missing prefix, not for an invented global barrier.
Publication order among independent owners is physical; each owner's logical
input/result order and each receiver's required prefix are invariant.

A receiver applies source results in the order prescribed by Contracts receiving,
from contiguous established source history and exact activation lifetimes. It
MUST NOT skip an earlier required source result in favor of a later visible result.
An entry can be supplied only when every applicable source has the strictly
sufficient coverage required by section 12, including all members of the full-key
tie. A checkpoint at timestamp T does not imply completeness beyond T. An empty
poll, a worker's READY status, or an absence of notifications proves nothing.

Actual strongly connected owning components use the Contracts atomic cyclic unit.
Their local rounds, preceding-round views, shared/member gas limits and publication
are atomic. No host commits a strict subset of such a unit. A terminated member
inside a live cyclic unit may receive silent structural updates as allowed by
Contracts; that is not autonomous execution of a terminated root. Discovering or
joining a historical cycle without sufficient exact ownership/history evidence
fails explicitly; a current-view SCC helper does not establish that support.

### 14.3 Attachments, catch-up and historical authority

An Attachment binds consumer occurrence, decoded path, generation, exact source
operand, source initialization, selected source timeline and source History Position.
It freezes its activation entry or initialization cause and finite target goal.
Removing and recreating the same path produces a new lifetime. An old obligation
cannot be reassigned to the new lifetime. Shared acquisition never merges distinct
occurrences or their delivery identities.

An already initialized source requires its relevant history from the established
initial position through the frozen goal. Catch-up verifies every predecessor,
before/after relation, selected runtime, source receipt and required timeline
coverage. The receiver installs child state before exposing its corresponding
emissions to handlers. Child initialization may cause the subsequent receiving
work specified by Contracts; the host does not synthesize an extra external seed.
An exact operand and a latest snapshot with the same business fields are not
interchangeable evidence.

Historical authority and admission use the original receiving before-state at the
selected full-key position, including the appropriate authority/access histories.
Later grants, revocations, topology or document versions cannot retroactively
authorize an earlier input. A source's successful independent result survives a
receiver's authority denial or application failure. The receiver retains the exact
obligation and last stable result for retry. A rebase freezes the ordered affected
source scopes and target positions; it cannot silently skip a gap, mix epochs or
replace frozen views with ambient latest state. Unknown delegation is rejected;
Mandates is an optional separately selected protocol, not a dependency of this one.

### 14.4 Terminal closure

Once the root is terminated, direct PROCESS-equivalent LIVE receiving is rejected
as specified by Contracts. Finite HISTORICAL receiving obligations already frozen
before terminal closure may still be discharged without external seeds. The host
MUST NOT create a new rebase or attachment goal merely because a child later
advances, nor keep chasing an unfrozen latest child position.

Closure requires positive evidence: the exact terminal head equals its last stable
document and position; a committed stable history row seals that same document,
position and sequence number; and no frozen attachment or rebase goals remain.
This sealed prefix, rather than worker state or a terminal Boolean alone, permits
the terminal owner to satisfy later dependency readiness checks. Missing or
contradictory evidence waits or fails explicitly. Subscriptions may then be retired
without losing frozen work. The parent-terminal-at-20/child-at-30 case retains the
same parent epoch, position and stable document when these conditions hold.

### 14.5 Input dispositions and Dispatch

Hosts retain a disposition for each exact original entry and each applicable
receiving channel lifetime. Nonmatching/addressed-elsewhere input is INAPPLICABLE;
it is not a fabricated Contracts invocation. Eligible input carries its verified
admission projection into Contracts. Missing history/content is WAITING; an
established read-access deficit is PENDING_ACCESS. Malformed input, contradictory
evidence and deterministic execution failure remain distinguishable.

Dispatch policy decisions come only from the selected Contracts completion. A
validated denial is reported with standard code `DISPATCH_REJECTED`; authored
reason strings and allow/deny rows remain in ordered details with their native
delivery identity. An empty or arbitrary authored reason cannot replace this code.
For one delivery any false decision denies its handler work; all valid policies
still run. An addressed operation whose delivery is denied reports
`DISPATCH_REJECTED`. Raw or mixed inputs with both allowed and denied deliveries
report `PARTIAL`, retaining every delivery's disposition and allowed progress,
including deliveries without policy rows. Each denied delivery still carries
`DISPATCH_REJECTED`; an aggregate never changes the native Contracts status.
Raw external events follow these same rules; no Operation Request is required.
The enclosing Contracts status can remain APPLIED and retain child/native progress.
External denial is consumed only on enclosing commit. Later execution error or gas
exhaustion rolls back the whole tentative Contracts attempt, including tentative
checkpoint/child installations, but not independent source commits.

### 14.6 Exact native channel binding and admission commitment

The executing profile registers the exported Timeline Channel type against this
Coordination rules identity. Its binding is `role: external-channel`,
`header_fields: [timeline, actor]`, `body_fields: []`,
`namespace: coordinationTimeline`, `tariff: [[accept, 1]]`,
`inherits_to_subtypes: false`, `peer_fields: []`, `meter_mode: live`.
The profile also preselects the published Dispatch binding when policies may be
authored later. Merely mounting another package does not add an executable role.

Public Timeline Channel uses the same rules identity and `external-channel` role,
with `header_fields: [provider, url]`, `body_fields: []`,
`namespace: coordinationPublicTimeline`, `tariff: [[accept, 1]]`,
`inherits_to_subtypes: false`, `peer_fields: []`, and `meter_mode: live`.
Its source is the exact Signed Timeline with that provider and URL and
`publicRead: true`; it accepts authenticated entries without a holder-actor filter.
It confers no additional write or business permission. Both exact native channel
bindings are selected before initialization in the non-timer executing profile.

Timeline admission first authenticates exact ranges and verifies history against
the original receiver. The closed returned record contains `snapshot`, `entry`,
`timestamp`, `runtime`, `decisions`, `assessments`, and `operationAudience`.
The first three values identify that original snapshot and entry/time; `runtime`
is the complete selected binding record. A decision key is the compact JSON array
`[member, document, channel, generation]`; its value is a Boolean. Assessments
are ordered by member then channel in Contracts code-point order and each has
exactly `member`, `document`, `channel`, `generation`, `disposition`, and `reason`.
`operationAudience` maps each participating member to its addressed Boolean.
All validated assessments, including negative decisions, enter the Contracts
canonical admission commitment. Credentials, signatures, transport pages and
local cache/capability identifiers do not. The supplied range evidence alone is
not an authority decision. A missing host history verifier fails explicitly.

The optional Timeline Entry `onBehalfOf` operand is an exact authenticated claim.
It grants no authority by itself. Interpreting it requires a separately selected
authority protocol and its historical evidence; unsupported claims are rejected.
Coordination does not require Mandates or define a competing Authority type.

## 15. Portable executing-host obligations

### 15.1 Conditional publication and fencing

A host binds each attempted publication to its exact input head, owner set,
selected runtime, relevant source-set revision, frozen goals and dependency
positions. Immediately before commit it MUST establish that these still match.
An ownership token/fence must exclude an expired or superseded worker from
publishing. A changed read set causes retry from a coherent view, not merging
tentative results. For an actual cyclic unit the condition covers the whole unit.
No particular SQL schema, lock algorithm, journal or machine allocation is required.

One atomic durable publication contains all owned result heads, history rows,
receipts, input dispositions/checkpoints, outstanding goals, dependency changes
and output work needed to recover the next step. No observer may see a result
head whose required evidence or history predecessor is absent. An interrupted
attempt before publication exposes none of its tentative effects.

Notifications are hints. The durable obligation/outbox is authoritative. Delivery
can be retried; occurrence identity is the deduplication key, never message-content
equality. Receipt publication and durable output intent are atomic. Acknowledgment
cannot precede successful delivery. Restart reconstructs undispatched output and
unfulfilled receiver obligations without rerunning committed business operations.
Conditional retries must neither duplicate committed occurrences nor lose them.

### 15.2 Storage, admission and restart

Publicly uploaded content and replay proofs are untrusted. Verify exact content,
provider signatures, contiguous ranges, completion/profile commitments and all
logical context before granting an in-process capability. A locally protected
completion reader may rely on its own authenticated atomic publication provenance;
an arbitrary hash, read-model flag or caller-supplied JSON is never such provenance.
Every protected read still verifies the exact requested history/runtime association.

A Processing Proof contains sufficient actual initial content, source ranges,
history positions, authority positions, assessments and Contracts evidence to
replay its target. Its container or self-reported receipt does not establish
authority. Unsupported portable receiving, historical cycle joining, restart or
migration paths fail explicitly rather than accepting a weaker projection.

Source acquisition may retain verified pages privately under one exact checkpoint;
public completeness advances only after the complete authenticated chain to its
selected anchor has been verified. Replacement checkpoints cannot splice partial
chains. Durable stores preserve input positions, contiguous history, frozen goals,
outbox and selected profile across restart. A store claiming only process-local
durability must state that limitation and must not advertise crash recovery.

The host keeps account/tenant storage keys, credentials and private signing keys
outside Blue business content. Reads, subscriptions, capability caches, protected
history lookups and retry work are scoped to their authorized account. Knowing
a BlueId or another account's public handle does not authorize private content.
Sharing immutable public verification results is permitted only when this does not
cross access boundaries or change semantic outcomes. Timeline read access and
authority to invoke business operations remain separate.

### 15.3 Operational incompleteness and retained editions

The selected Contracts maximum/default is 10,000,000. Hosts preserve charge-before-
work, member budgets, admitted-prefix gas, first rejection and atomic rollback.
Physical cache state, cancellation, resource exhaustion or a missing dependency
does not become a successful semantic result. A host interruption retains the last
stable state and exact pending input as HOST_INCOMPLETE; retry uses the same logical
policy. It does not publish a partial gas receipt or silently raise the budget.

Every saved context carries its exact edition/profile. Reopening it selects that
edition or reports explicit unsupported history. New-context defaults cannot
rewrite old context identities. Migration, if implemented, is a separate explicit
operation with its own evidence; installing another runtime is not migration.
Old provider and execution archives remain immutable and are not aliases for this
publication.

## 16. Conformance claims

A provider qualifies the signature, append/seal/access, range and optional stream
interfaces it actually implements. An evidence verifier qualifies exact identities,
signatures, continuity, full-key ordering and strict completeness. A feeder qualifies
historical source selection, access/authority context, original-entry identity and
per-input dispositions. An executing host additionally qualifies sections 14–15
under its declared storage and ownership model. Passing one role does not establish
another. In-memory, SQLite, journal and remote durability claims are separate.

Qualification compares typed full results: state/graph, ordered events, native work,
checkpoints, completions, dispositions, selected runtime commitments, final gas,
first rejected charge, diagnostics and validated receipts. It includes Unicode
ordering, simultaneous source ties, frozen attach/detach/rebase, independent source
progress on receiver failure, real cyclic atomicity, terminal finite closure,
crash/restart, stale-fence publication, durable output retry and account isolation.
Warm/cold caches and alternate physical schedules must preserve those observations.
Timer-dependent cases are explicitly outside a non-timer claim. Missing resources,
unsupported histories and unexecuted cases are reported, never treated as passes.
