# Offer hosts and Business presentation

`Offers/Offer` is a plain commercial domain type, analogous to Agreement and Order. It identifies a proposition independently of its distribution channel or commercial model. It declares no fields, clauses or automatic execution. A specialization defines application inputs and the resulting process. Creating or distributing an Offer does not start that process. Business stores editable marketing presentation separately from the commercial document.

`Offers/Offer with Clauses` adds the standard clause-host initialization lifecycle,
using the same Clauses and Contracts machinery as Order and Agreement hosts. An
authored Offer can install publication operations with a standard Feature Clause.
The host itself does not prescribe those operations, their authority or commercial
terms. An Offer still identifies exactly one application path.

The `0.2.0-local.1` candidate adds this host while preserving the original plain
Offer type identity. This does not retrofit existing immutable Offer instances.
Native Business qualification covers publication/withdrawal, idempotent recovery
after withdrawal and prior-Mandate publication of subsequently created Offers.
Hosted Agent authentication without a Task and deployment are separate gates.

This is an unpublished local candidate. Build with the repository native builder; installing its exact archive requires no public registry or release.

The qualified archive retains its original README bytes. This guide documents the
additional clause host and Business integration without changing that archive or
its package identity merely to update explanatory documentation.
