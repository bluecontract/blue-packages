# Orders

Authored native Blue proposal package. See the top-level evidence and catalogue for tested scope. No JavaScript business interpreter.


Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.

`Order with Seller Decision` composes the standard Orders host with an exact
seller `rejectOrder` workflow. The request names the current activation revision.
A seller can retry a rejection of the same revision without another event.
Rejection prevents subsequent public activation of that Order.

`Order with Lifecycle Guards` lets an Order apply a closing decision to
selected operations. Use the plain `Order with Clauses` when the Order has no
such guards. `Order with Seller Decision` inherits the guarded host and
supplies its own rejection rule. An exact retry of seller rejection remains
available after rejection.

A stand-alone Order can combine Schedule and Commerce without a seller
rejection workflow, using the same selection to close reservation review
after cancellation.

```yaml
contracts:
  orderOpen:
    constants:
      closedStates:
        cancelled:
          path: /cancellationDecision/status
          equals: accepted
          reason: ORDER_CANCELLED
      actions:
        reservation: [confirm, alternative, accept]
```

Each `closedStates` key is a descriptive label. Its `path` and `equals`
identify a decision recorded by this Order. Failed operations return the
native dispatch rejection with the configured `reason` or `ORDER_CLOSED`.
`actions` names the clause and actions
that need an open Order. The guard follows their public workflow bindings
even when the workflow names change. Authors may also list custom workflow
names in `contracts.orderOpen.constants.operations` or add action groups under one closing
state's `actions`. The earlier
`clauses.orderDecision.parameters.activationOperations` list continues to
apply only to seller rejection.

The Seller Decision type guards seller approval and rejection after every
configured closing decision. Each state can select different Activation
roles with `approvals`; the guarded host without Seller Decision defaults to
no roles. Use role names or `all`. The built-in seller rejection guard
applies to every installed Activation approval role.
Use the matching catalogue's Activation edition for role-based guards.
Its installed definitions identify external approvals and local reviewed
approval deliveries. Draft proposals and participant access are
independent of approval. Payment, reconciliation and other workflows outside
the selected groups can continue.

## Prepare an independent Order

Set `Documents.parameters.preparationDefinition.type` to
`Orders/Order Preparation Functions` for a catalog-priced Order without
reservation groups. The strategy accepts either a current `catalogRevision`
and `lines`, or an exact stored `quoteKey`. It validates the customer account
or email, applies Commerce pricing, and passes the frozen amount, currency,
quote and customer fields to the standard Documents bootstrap lifecycle.

`prepareDetails(input)` is the read-only checkout preview entry point. The
stateful Documents preparation checks existing keys and request IDs before
consulting the current catalog. A matching replay keeps the original terms.
Documents remains responsible for preparing, providing and admitting the Order.

Use `Schedule/Order Preparation Functions` for a reservation policy from the
Order template or a `fulfilment` binding. It reuses the same catalogue
calculation and lifecycle and adds the reservation snapshot. The ordinary
strategy rejects reservation configuration or group inputs.
