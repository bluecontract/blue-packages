# Activation

Authored native Blue proposal package. See the top-level evidence and catalogue for tested scope. No JavaScript business interpreter.


Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.


## Owner-mediated party admission

An approved admission can emit `Party Addition Requested` with its exact
`admissionRef`, `expectedRevision`, new `parties`, `accessDocuments`, `itemPath`
and `clauseKey`. Each real main and representative timeline requires a matching
public Timeline Access document, keyed by role (`role__representative` for a
representative). The access document must contain a native provider-history
checkpoint, cover that exact timeline and preserve the standard access-update
program. Missing, unrelated or modified evidence is rejected.

Activation embeds these histories under `/partyAccess` and installs ordinary
embedded Timeline Access event listeners. This registers public evidence only;
it does not grant access to a private business timeline.
Activation compares the proposed roster's reader groups with its current access
witnesses. It emits a separate `Party Access Update Requested` for each existing
party with missing access and retains those requests under
`/activation/accessRequests/<admissionRef>`.

These events request owner action. They are neither access evidence nor approval
to impersonate the owner. An account adapter may perform the requested grant
under that owner's settings; manual approval remains possible. The request's
`expectedAccessEntry` identifies the observed history state, so a delayed grant
must not overwrite a later revocation. Readiness is recomputed only from native
Timeline Access documents after their embedded update events.

Admission approval, owner grants, newcomer consent and final roster installation
remain separate. `Documents` waits for the required checks before calling the
native admission operation and proceeding to linking/embedding. Losing existing
required access still blocks direct requests; genuine embedded access updates
can recover it. A successful account-side grant response does not activate the
document by itself.

## Regular start waits for access before admitting channels

A regular document start does not create timelines or grant keys. Supply the
complete `parameters.parties`, their reader-key groups, and the public Timeline
Access documents listed in `parameters.accessPaths`. Activation keeps this
roster as declared state even while it is not usable.

For example, Buyer and Seller have existing main timelines. Seller declares
reader key `1234` (a shortened label here; actual keys must be well-formed), but
Buyer's Timeline Access does not grant that key. The initialized host has
`status: WAITING_FOR_ACCESS`, `accessReady: false` and `active: false`. Its party
ports are empty `Contracts/Composite External Channels`: they have no members,
no private timeline subscriptions and no callable routes. The actual transports
remain declared only in `activation.parties` until access is valid. Operations
(including fixed inherited PI/Shipment operations) keep their declared channel
names; Activation does not rewrite or copy their logic. This initial roster is
admitted together, only when every required timeline has a matching access
witness granting at least one key from each required reader group. A missing
or empty reader group never counts as permission.

The embedded access documents and their ordinary `Timeline Access Updated`
listeners remain installed. A genuine provider update that adds Seller's key
causes Activation to re-evaluate the complete access matrix. An unrelated key,
wrong timeline or wrong provider cannot satisfy it. When ready, Activation
replaces the empty ports with the declared timeline channels together. Required
commercial approvals still apply: access readiness alone does not accept terms.
An immediate document becomes active; a consent-based document waits for its
configured approvals. Once channels are installed, previously unprocessed entries
are evaluated under the normal operation, access, actor, authority and consent
rules. Admission does not record a timestamp boundary or reject a request solely
because it predates admission. Native timeline ordering uses the verified provider
timestamp, never a timestamp claimed in the request payload. Requests already
resolved as denied remain denied; granting access does not retry them.

An approved later `Party Addition Requested` uses the same full-roster access
check, including the proposed party and its mandatory access documents. While
any required grant is missing, the host is unusable and the newcomer is not
installed. The existing owner-update requests remain independent. Embedded
access events restore readiness; newcomer consent and final admission remain
required. Pending proposals from an older Activation revision do not block a
newer roster.

After channels have been admitted, revocation closes dispatch but retains the
established channels and their native history/checkpoints. This preserves
canonical ordering and durable rejection of requests during suspension. It does
not drop a history dependency merely because access is temporarily unavailable.
Recovery still comes only from embedded access updates; it neither replays
rejected business requests nor repeats first-activation startup.
