# Shipping

An unpublished shipment protocol and its authoring clause. Requests and confirmed carrier outcomes have different types. The carrier operations are on Shipping Instruction; the host clause starts an instruction and relays its events. No real carrier adapter is included.

## Independent process preview

`Shipment Clause` uses the shared Documents engine to create or receive one
independent Shipping Instruction. `Shipment Process Clause` belongs inside that
instruction. It exposes the native booking, cancellation and address-change
actions and refuses booking until declared named sources are ready. Additional
`parameters.conditions` apply to every connection of each named action. Booking
is an intent; carrier operations still exclusively confirm acceptance, dispatch
and delivery. These additions are unpublished and require separate hosted and
complete-example qualification.
