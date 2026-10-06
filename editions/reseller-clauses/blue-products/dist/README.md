# Products

Define what is supplied without requiring a separate Product document.

- **Fixed Product** describes a voucher, physical good or fixed service. Give it a useful name. `amountMinor` is an integer in `currency`; no payment is implied.
- **Bookable Product** describes a named resource and the interval `startsAt` to `endsAt` (UTC microseconds). The Product Clause rejects empty or reversed intervals. It does not reserve external inventory.
- **Product Clause** keeps these terms in `parameters.product`; it adds no duplicate runtime configuration.
