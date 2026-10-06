# Timing

**Timer Clause** registers one native timer when its clauses initialize. Configure `key`, a BEX `scheduleAt` expression, `steps`, and `bindings.channel`. An optional `cancelOn` event pattern cancels the pending timer through Time / Cancel Timer. The native Time journal owns pending registrations and recovery.

For an event-relative deadline, put Time / Schedule Timer in a Listener's steps and add the interval to `$binding: timestamp`. There is no cron job. A workflow may explicitly schedule its next event. Changes to clause configuration do not silently move an already registered deadline; replace or cancel it explicitly.
