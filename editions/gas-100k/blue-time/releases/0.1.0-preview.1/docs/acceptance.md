# Acceptance and qualification

The package-owned automated tests distinguish executable Contracts/BEX tests from
native integration requirements. A passing fixture is never native support approval.

## Executed package and fixture checks

Verify the immutable archive and exported definitions; check exact sibling locks
and deterministic source rebuild; reject unknown/mismatched native requirements;
initialize without a Timeline entry or initialization timestamp; emit the first
request through Contracts/Trigger Event; emit the second through the custom step;
run the same request through direct BEX; route different contexts to separate
workflows and return captured request data; reject bad timestamps and malformed
requests; cancellation/replacement/unnamed occurrences; rollback; stale/duplicate
fixture admissions; completeness and local ordering; delayed firing retains its
requested timestamp. See `verification/results.json` for the actual executed count.

## Native gates before approval (not claimed as executed)

1. **Idle source evidence.** With no business entries, signed/provider-trusted
   progress past T permits firing; a latest-head read alone does not. Provider
   restart cannot reopen the closed prefix. Loss of access or missing proof waits.
2. **Late earlier cancellation.** A cancellation timestamped T-1 but fetched after
   wall time T precedes the timer. A cancellation at T wins under the tie rule;
   one at T+1 cannot overtake. Prove this through real Timeline admission.
3. **Crash windows.** Kill the process before/after effect commit, before/after
   index write, before/after firing publication and before terminal cursor update.
   Restart from durable store; no lost timer, duplicate committed transition, or
   falsely terminal host failure. No cross-table PostgreSQL transaction assumption.
4. **Snapshot/evidence binding.** Reuse proofs with a different snapshot, account,
   document, generation, request, deadline or cancelled/replaced registration.
   All fail admission. Uploaded Time-shaped Timeline payloads cannot fire Time.
5. **Shared parents.** B has a timer and A embeds B; ten documents embed A.
   No parent claims completeness past B's unresolved timer. B/A can advance
   independently while parents consume retained exact results, without reruns.
6. **Cycles and topology.** Use A<->B plus an outside parent; establish progress
   without circular completeness waits. Add/remove channels and dependencies
   before T; reselect proofs. Removing an embedding is not terminating the child.
7. **Timestamp boundaries.** Initialization with an elapsed deadline and no
   prior position works; an attached child's backdated schedule is rejected;
   timer-triggered equal-time rearming is rejected; earlier Timeline input may
   arm at its own timestamp without skipping earlier equal-time external inputs.
8. **Budgets and charge-before-work.** Exhaust gas during expression construction,
   validation and event staging. Roll back all effects. Test proportional memory
   work and account-level limits over many timers; no arbitrary timer-count cap.
9. **Failure progression.** FAILED/GAS_LIMIT_EXCEEDED/NO_MATCH dispositions do not
   permanently block later inputs. Resource outages and funding waits do not
   become semantic rejections. Recovery does not replay terminal one-shot timers.
10. **Python/Java parity.** Same pinned definitions, exact requests, registration
    descriptors, admitted inputs, resulting documents, event batches and gas
    policy. Do not compare only final business field values.
