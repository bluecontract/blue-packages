# Blue Mandates

Owner-approved operation delegation is a separate package. Its lifecycle and
scope transitions are ordinary Contracts/BEX workflows. A runtime must explicitly
support its native authority protocol before those claims grant any permission.

`Mandate` has an authority holder and an authorized actor. `Operation Mandate`
adds a scope of permitted target operations; `Qualification Mandate` adds
correlated evidence requests. A holder must approve the exact document version.
The approved program and designated lifecycle writers are protected by the host.

Mandates owns its Event, Message, Request, Response and Authority base types.
Coordination supplies authenticated actors, signed timelines and channels.
Agreement and Payment packages do not implicitly enable delegation.

The current package is an unpublished Core Java integration candidate. Current
Python native support is not claimed. See `spec/mandates.md` for the normative
rules and `../docs/consolidation.md` for compatibility and validation scope.
Build from `types/*.blue` using `../tools/build-payment-family.sh Mandates`;
then regenerate consumer catalogues using `../tools/sync_catalogues.py`.
