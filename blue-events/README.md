# Shared event hierarchy

Domain request types derive from `Events/Request`, and domain response types derive
from `Events/Response`. Both derive from `Events/Event`. A concrete message then
extends the appropriate domain type, for example `PaymentInstruction/Payment
Request` or `Shipping/Shipping Response`.

Type identity identifies meaning. The receiving document still verifies the
input channel, participant authority, request correlation and transition rules.
