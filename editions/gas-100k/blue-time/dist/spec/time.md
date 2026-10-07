# Time: ordered timer inputs / 2

Status: integration preview. This publication defines data and the required runtime
behavior. A package import does not install a scheduler or authorize an executable
binding. Native support is an explicit host selection. The MyOS Java adapter implements
this publication; other runtimes must qualify their own integration.

## 1. Layering and inputs

Language stores and validates Blue values. Contracts runs lifecycle handlers,
operations and workflows. BEX computes effects. This Time protocol introduces a
channel for processor-derived inputs and steps for emitting requests. Coordination
must integrate pending timers into its existing input selection, complete-prefix
publication, durable progress and account-scoped execution. No separate graph
scheduler, global ancestor barrier, per-timer Timeline, or external business entry
is introduced.

Starting management runs Contracts initialization without an incoming Timeline
entry and without an initialization timestamp. A lifecycle workflow may emit a
complete Timer Request already stored in the document. BEX does not read a clock.
An operation may also emit a request; its arrival timestamp is not used to derive
the requested deadline. A Timer Request merely stored somewhere in document data
is not active until emitted by a successful managed-document invocation.

## 2. Timestamp

The field is `timestamp`: a nonnegative Integer Unix timestamp in microseconds
since 1970-01-01T00:00:00Z, using the same unit as the selected Coordination
Timeline timestamps. For example, `1790931600000000` is a requested deadline, not
a measured execution time. Text dates, seconds, floating point values and booleans
are not interchangeable with this field. There is no `at`, `atUs`, `afterUs`,
implicit `now`, relative-delay base, or worker-clock field in this protocol.

The selected Contracts edition accepts external processing timestamps from 0 to
2^53 - 1 inclusive. This preview uses that existing numeric representation bound;
it does not introduce a structural, cardinality or depth limit. A different
numeric domain requires a compatible Contracts/Coordination edition and a new
Time publication, rather than silently truncating an Integer.

The processor may wake late. Once eligible, a Timer Fired input occupies the
requested deadline's logical position. Its Contracts eventTimestamp is the
request's timestamp, NOT a wall-clock observation and NOT an originating
initialization/operation timestamp. This supplies the existing three-input
Contracts interface only when the future firing is processed. Initialization
still supplies no external event or timestamp.

## 3. Messages

A Timer Request has exactly type, channel, timestamp and optionally key and
context. channel is the local Time channel key, not a Timeline ID. A supplied key
is nonempty Text. context is arbitrary valid captured Blue data, not code to
reevaluate later. Reserved metadata is interpreted under Language rules; unknown
ordinary top-level request fields are rejected by the Time runtime.

A Timer Fired has exactly type, registrationId and request. Its request is the
original committed Timer Request, preserved as an exact Blue value. An inline
presentation and a verified exact reference may differ physically without
changing that identity. No callback/workflow name is stored, and no execution
clock or inferred relative deadline is added.

A Cancel Timer Request has exactly type, channel and key. This version cancels
by key only. Cancellation by registration ID, recurrence, cron and relative
delays are outside this version. Applications may emit subsequent explicit
requests to implement their own bounded repetition.

## 4. Event effects and custom steps

Contracts/Trigger Event and BEX $appendEvent can emit a fully constructed Timer
Request. Both use normal Contracts commit/rollback behavior. A native Time/Schedule
Timer step accepts a single `request` body field, interpreted as a read-only BEX
expression. The expression returns an untyped object containing channel,
timestamp, optional key and context. The step attaches the exact Timer Request
type, validates the completed message, and returns one staged emitted event.
A result with its own type or unsupported fields is rejected, not overwritten.

Time/Cancel Timer follows the same procedure, with channel and key. Evaluating
arguments may read the current event, call, document and earlier step results
using the current Contracts expression frame. It may not read a wall clock,
perform host I/O, register a timer immediately, or reinterpret its context as
future executable code. Standard BEX gas must be charged before work, against
the same invocation budget; the step does not receive a second 100,000 budget.
Any effects in an expression-root evaluation are rejected.

A helper emitting the same completed request through ordinary Compute must have
the same registration meaning. Emitting a request is NOT a firing. A Triggered
Event Channel observing that request does not constitute a Time channel firing.
A conditional BEX program can choose whether to append a request. A preceding
step returning false is not implicitly a workflow branch.

## 5. Registration, scope and identities

Only effects surviving the originating document's commit create or cancel
registrations. The Time runtime must validate the entire staged effect batch
before making it eligible to commit. Malformed requests or an invalid local
channel reject the originating attempt atomically; earlier changes and requests
from that attempt do not become effective. The emitter is the managed document
that actually produced the effect, not each ancestor that later observes it.
Use Contracts provenance/effect occurrences, not a scan of public payloads.

A registration belongs to an engine/account context, managed-document identity,
Time channel key, and that channel's generation. It is not keyed by the changing
current document BlueId alone. An unrelated business update does not rearm or
invalidate it. Replacing/removing the channel or ending the managed lifetime
invalidates that generation's pending registrations. Ordinary embedding attach
or detach is not by itself removal of the separately managed child.

The canonical identity descriptor is the Blue value:

    { domain: "Time/registration/1", contextId: <stable context identity>,
      documentId: <stable managed identity>, channel: <key>,
      channelGeneration: <generation>, occurrenceId: <committed effect identity> }

registrationId is its Language BlueId. occurrenceId identifies the source commit
and local effect position using existing committed-effect provenance. It is not
just the emitted payload's content BlueId. Two identical emitted requests at
different occurrences create different unnamed timers; replaying the same
occurrence yields the same registration. Independent contexts need not share a
registration ID. They reproduce it when replaying the same identified context.

A key selects at most one pending registration within this scope. Reusing the key
replaces that pending registration with a new identity. Without a key each
occurrence is independent. Cancellation of a missing key is an idempotent no-op.
Replacement and cancellation only affect a registration they precede in logical
input order; they cannot undo an already prior firing. One source commit's
requests and cancellations apply in their emitted order. Thus schedule-then-
cancel leaves no pending timer; cancel-then-schedule leaves the new one pending.

## 6. Eligibility, completeness and deterministic order

A host alarm is only a wake-up hint. Firing requires evidence that authoritative
time has reached the requested timestamp, relevant histories are closed through
the required boundary, all predecessors/prerequisites have been processed, and
the registration is still pending. A fetched latest head or silence on an idle
Timeline is insufficient. Strictly increasing append timestamps alone do not
prove that an earlier unobserved entry cannot arrive. A completeness promise
must establish both availability of the required prefix and that future accepted
entries cannot be inserted into that closed prefix.

The required source set is the document's current dependency/history selection,
not a list frozen when the timer was first emitted and not every Timeline on the
platform. Missing authorized history means WAITING, not permission to ignore a
possible earlier cancellation. Reevaluate dependencies after earlier inputs or
topology changes. Preserve exact historical child outcomes and the existing
cyclic dependency/group rules; a new Time feature must not reintroduce a global
parent-completion barrier or deadlock a cycle by demanding impossible mutually
final completeness.

Pending timers occupy candidate positions as soon as their source commit is
visible. Every input uses Coordination's lexicographic order
(timestamp, sourceBlueId, entryBlueId). An ordinary entry uses its Timeline ID;
a timer uses its Timer Source ID and Timer Entry ID. There is no input-class
priority. At equal timestamps a cancellation wins only when its entry precedes
the timer. Dependency prerequisites still take precedence; this is not a new
global order across unrelated documents.

Each managed document has one immutable Timer Source with exactly type,
contextId and documentId (the stable managed identity, not its current state ID).
A Timer Entry has exactly type, source (an exact Timer Source reference),
timestamp (the requested deadline), and message (an exact Timer Fired reference).
Its message contains the registration identity and original request. Neither
object contains arrival time, worker identity, mutable status or a predecessor.
Multiple timers may have the same source and timestamp. Pending entries are
candidates, not append operations on a strictly increasing Signed Timeline.

The Time adapter admits this exact Timer Entry type wherever the selected
Coordination receipt/history/attachment format records the effective input.
It preserves the existing order tuple and receipt construction. This extension
is enabled only for the exact approved Time publication; arbitrary entry types
remain invalid. The outer Timer Entry is the durable input identity, whereas
Contracts receives its Timer Fired message and deadline. Retained completion
records preserve both identities so receivers verify the original invocation.
Ordinary Signed Timeline validation and its strict timestamp rule are unchanged.

A newly emitted request must have a timestamp strictly greater than the
invocation's logical timestamp, regardless of whether its cause is an operation,
a timer or a received child outcome. New child initialization inherits the
causal floor of the attaching invocation. Requests at or before that floor are
rejected as TIME_DEADLINE_BEFORE_POSITION before publication. No fixed minimum
interval is imposed beyond strict increase. Hosts may fairly throttle processing
without changing logical timestamps or skipping backlog positions. Pending
registration quotas are host resource limits, not automatic recurrence rules.

A genuinely new standalone document with no committed external position may
initialize with an already elapsed absolute deadline. Process it as due once
time and input completeness are established. A previously committed overdue
registration after downtime also retains its original candidate position; it
is not a new backdated registration.

## 7. Admission and authority

Time/Timer Channel derives from Contracts/Channel, NOT from a generic accepting
External Channel. Bind its exact type and rules identity to a trusted
external-channel implementation. This is an external input to the Contracts
machine, but it is generated by the document processor, not appended by a user
to a Timeline. Unsupported Time channels and steps must fail explicitly.
Loading the package data must never enable them automatically.

Before preparation, the runtime binds admission evidence to the exact receiver
snapshot, managed identity, channel and generation, event identity, registration,
requested timestamp, prerequisite coverage, and engine context. Recheck it on
replay. A Timer Fired-shaped payload on a Timeline, a forged client evidence
object, wrong generation, replaced key, duplicate completed registration, or
mismatched request cannot create a timer firing. Ordinary Timeline inputs can
still be observed by ordinary Timeline workflows, but never impersonate Time
channel admission. Timer firing conveys only the agreed document transition;
it cannot impersonate a party or bypass another document's operation authority.

## 8. Durable progress, parents and failure

The authoritative state is committed effects plus durable per-registration
progress. Pending wake-up indexes are reconstructible projections. Persist the
source cursor, registration identity, generation, key replacement/cancellation,
selected input and terminal disposition with idempotent writes and the engine's
existing publication/receipt protocol. Do not require cross-table PostgreSQL
transactions or treat multiple uncoordinated writes as atomic.

A crash before the source commit exposes no timer. A crash after commit but before
index update must rediscover it. Commit results and firing disposition through
the existing durable publication protocol so a crash cannot create a second
committed firing or lose the first. An old alarm after cancel/replace is harmless.
Do not mark a timer done before its outcome is durable. This publication does
not prescribe a new journal implementation in the data package.

An unresolved timer at T holds the receiver's complete-prefix publication before
its position. A parent must not be told its child is complete through T while the
child still owes a timer-driven transition there. This is a per-dependency
completeness requirement, not a rule that the child waits for all parents before
continuing. Shared parents consume the retained completed child history without
rerunning that child once per embedding.

One-shot timers become terminal after their committed processing disposition.
A successful firing with no matching workflow is terminal NO_MATCH. A deterministic
Contracts failure or gas exhaustion follows the selected Coordination terminal
input policy, with rollback and recorded disposition; it must not permanently
block later input or retry forever as though it were a missing wake-up. Host
crash, resource shortage, unavailable proofs or unfunded account are not such
terminal semantic results. Preserve account-scoped authority/access and budgets.

## 9. Metering and qualification

The Contracts 100,000 shared gas ceiling is unchanged. BEX evaluation, message
construction, validation and accepted effect processing must be charged through
the chosen runtime before proportional work. Candidate discovery/proof retrieval
is host work subject to host and account budgets, not an invented unbounded
free background workload. No new universal timer-count, graph-depth or collection
cardinality ceiling is introduced. Exact native tariffs, metering of admission
validation, cyclic progress, durable storage and cross-language parity must be
qualified before native support is advertised. The conformance harness's fixture
counters are not a calibrated production gas policy.
