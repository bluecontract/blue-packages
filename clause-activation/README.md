# Activation

Authored native Blue proposal package. See the top-level evidence and catalogue for tested scope. No JavaScript business interpreter.


Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.


## Connections before activation

Use `parameters.preActivationConnections` to admit specific Connections actions
while commercial activation is pending. Name the clause instance and its action.
Use `automatic: true` for the action's automatic declaration, or `connection`
for one named binding. Use `observations: true` to cover the dedicated internal
sources of an action declared with `observation: true`.

```yaml
parameters:
  preActivationConnections:
    - clause: reservation
      action: initialize
      automatic: true
    - clause: cancellation
      action: refreshAvailability
      observations: true
```

Connections resolves these references against the composed document, including
default bindings and configurable actions. The referenced clause's hook must
use the Connections planner, as the Schedule and Commerce planning hooks do.
Unknown references fail planning. An individual entry identifies a declaration
by exact name. An observation entry expands the action's event, embedded,
collection, change, initialized and activated connections, including an eligible
automatic connection. Workflows, timers and shared channels keep their own
dispatch rules.
Keep generated source channels private to the planner. A custom raw handler
on a generated channel shares that channel's native dispatch decision.

A workflow reference validates the declaration. To let an external caller run
it before activation, include the operation key in `preActivationOperations`.
A shared channel cannot be admitted through a logical reference because
dispatch grants apply to the whole channel. Timers deliver their firing
through a native external channel and cannot be admitted through a logical
reference. Existing timer and external operation rules continue to apply.
Activation checks document access and closure for every resolved connection.

A lawful composition change retains grants for the same clause declaration and
drops grants when that declaration is removed. A replacement needs its own
explicit policy. Adding a connection to a replacement does not extend the
original grant. Activation's own amendment rules and the target clause's
lifecycle rules still apply.

`preActivationChannels` remains available for existing documents and
channel-level configurations. When both fields are supplied, Activation
combines the explicitly listed channels with the resolved connection grants.
Invalid logical references still fail planning. New Connections configurations
can use the logical references so their authors do not need generated names.
Historical package identities retain their existing behavior.

## Review approval using a local signed decision

A required role can use `parameters.reviewedApprovals.<role>` to approve
through a mounted local clause. For example, configure the seller of a
scheduled Order to use the signed review of its single booking group:

```yaml
reviewedApprovals:
  seller:
    event:
      type: Schedule/Reservation Reviewed
      clause: reservation
      subject: booking-1
    source: /reservations/booking-1
    basis: /amountMinor
    acceptanceBy: customer
```

The selector uses the exact type, source clause and subject. `source` and
`basis` are absolute document pointers. Every configured selector belongs to
one required role. For that role, Activation guards the direct `approve`,
`activate` and `proposeAndActivate` operations. Ordinary operations remain
available for other roles under their existing rules.

The handler checks live access, the signed exact-version operation's actor and
request digest, the saved record digest and the current basis. An `approve`
from the configured role approves its current terms. An `offer` from that role
records a grant. Only the declared `acceptanceBy` role can accept the exact
current grant. It binds the approver, document, revision, terms reference,
source, subject, proposal, basis and acceptance role. Activation consumes the
grant when applying the approval. Omit `acceptanceBy` to allow direct reviewed
approval only.

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
configured approvals. Confirmed access controls channel installation. Once a
channel is installed, its history is evaluated under the existing native rules
and the ordinary access, consent and actor/authority checks. Activation does not
add a timestamp cutoff. Previously settled rejections remain settled; this does
not change native child-birth boundaries or target-history requirements.

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
