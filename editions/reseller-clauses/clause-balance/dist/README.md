# Balance

**Balance Clause** creates an attributed ledger at `bindings.state` in one immutable currency. **Credit Balance Step** reads a source ID, amount and currency from configured event paths. A repeated source ID is a no-op. `rateBps: 1000` credits 10%, rounded down to the currency's minor unit using integer arithmetic. Supported nonnegative input amounts are at most 1,000,000,000,000 minor units; rates are 0–10,000 basis points.

The balance is a business accounting value. It does not claim bank settlement, execute payouts, or implement refunds.
