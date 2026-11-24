# Schedule

Authored native Blue proposal package. See the top-level evidence and catalogue for tested scope. No JavaScript business interpreter.


Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.

`Reservation Clause` records an Order's reviewed reservation proposals, service
windows and operational decisions. The template assigns roles to the native
booking actions and declares the conditions that apply to them. A separate
commercial cancellation policy can set a charge and connect its decision to a
Payment Instruction.

`Schedule/Order Preparation Functions` extends `Orders/Order Preparation
Functions`. It adds a reservation snapshot when the caller configures a
`fulfilment` binding or the prepared Order template has `reservationPolicy`.
Its `prepareDetails(input)` entry point and the Documents lifecycle use the
same Commerce quote and customer validation as ordinary Order preparation.
Choose the Orders strategy for a template without booking requirements.

## Reviewing one booking

`Reservation Clause` tracks operational state, proposal versions, service start,
response deadlines, and exact seller and customer decisions. For a one-group
reservation, the optional `wholeReservation` pointer publishes `id`, `status`,
and `confirmedStartMicros` when known. A caller can compose with those facts
without reading a particular reservation group's record.

An exact-version `confirm`, `alternative`, or `accept` operation can emit
`Schedule/Reservation Reviewed` after recording a new booking decision. The
event identifies this mounted `clause`, booking-group `subject`, actor,
decision, proposal and amount in minor units. The event carries the exact saved
record and request digests. Activation can bind this event to a configured
role's approval. The booking operation records only Schedule state.

Connections `parameters.conditions` can add action-specific requirements.
`parameters.conditionGroups` can share a condition across the three review
actions, including a typed funding condition for the selected instruction.
`close` accepts `groupId` and `reason` from a configured connection and closes
an open reservation without creating a workflow request or a financial decision.
A missing or already closed group is a no-op. An independent clause can decide
and settle a commercial cancellation and connect its accepted event to `close`.

Order preparation can omit an explicitly named clause for a zero total through
`omitClauseForZeroAmount`. The default retains every clause in the authored
Order template.
