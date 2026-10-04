# Immediate Termination

Independent data-only Blue package, namespace `ImmediateTermination`.

`Immediate Termination Terms` is the negotiable clause configuration:

```yaml
type: ImmediateTermination/Immediate Termination Terms
allowedParty: A
```

`A` means the first party, `B` the second party, and `EITHER` means either one
acting alone. `EITHER` does not require both signatures. The parameter has no
silent default. The clause provides termination without a cause, notice period,
or counterparty acceptance; an optional reason is retained as evidence only.

`Immediate Termination Clause` is the executable embedded instance. A containing
agreement installs it only after approval, with the approved option, accepted
terms ID / round, both party actors and authenticated Timeline channels. This
separation keeps negotiating a clause from executing it. Do not independently
install a child and treat its event as proof that an unrelated agreement ended.

Call `terminateA` on channel `partyA`, or `terminateB` on channel `partyB`, with
`request: {requestId: ..., termsId: ..., reason: ...}`. The receiver is the
embedded clause's document, not the agreement's activation clause. The actor is
determined by the authenticated channel, never by a caller-supplied party field.
The current `Runtime.agreements()` profile supplies Coordination authentication;
plain Contracts processing is not an authentication boundary.

A permitted first call changes the child from OPEN to TERMINATED and emits
`Termination Exercised`. The parent must check the genuine embedded source,
completed state, exact clause type, approved policy, actors, channels and revision;
only then may it emit `Agreement Terminated` and change its phase. The reseller
package contains that composition. Events forged on an external Timeline are not
embedded completions. Exact request retries have no additional business effect;
reuse of the same request ID with altered content and subsequent fresh termination
requests are rejected. Business termination does not use `Terminate Processing`:
state and evidence remain readable, and exact retries remain recognizable.

There is no native termination plugin, package-specific Python/Java SDK, copied
foundation source, environment, credential or install hook. The dependency pins
are in `blue-package.lock.json`; the data-only publication is `dist/package.bluepkg`.
