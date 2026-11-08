# Commission A2A payout with MyOS fee — contract (stage 1 review draft)

Status: implemented Blue contract of the commission A2A plan (revision 3,
2026-11-08), reviewed with the owner on 2026-11-08. Core operator execution and
Business presentation consume it.

Reviewed bases (all on `codex/payments-minimal-alignment-20261104`):

| Repository | Base SHA |
| --- | --- |
| blue-packages | `a639c3c6164d022c356b308fee4f443feaeaddf6` |
| myos-core | `7fbb70164da7e551ccb27b867e25c07cd43c9092` |
| myos-business | `af496d132b17fbb16fe7e6ddf399c6a567db3f59` |

## 1. Current state (verified at these bases)

- `Reseller/Commission Payouts Clause.preparePayout` validates `amountMinor`,
  blocks a second unresolved payout (`commission.reserved != 0`) and emits
  `Commission Payout Opened`; `Commission Clause.opened` reserves the amount.
- `Reseller/Commission Payout Payment Clause` builds a **manual** PI:
  `method: manual-bank-transfer`, `confirmation: recipient`, guarantor = the
  recipient, and a `retirePayout` action guarded only by request status and
  `reserved/*` totals.
- `Commission Clause.reconcile` settles `paid += completed − reversed`.
- `MyOS/Payment Setup.build` supports `myos-account-to-account` (payer and
  recipient resolved to distinct declared parties) but never sets the concrete
  `MyOS Test/Stripe Account to Account Payment Instruction` root type, and no
  Reseller clause uses it.
- No MyOS fee field exists in Agreement terms. `/terms/commissionBps` is the
  reseller rate on Orders only.
- Business authoring (`upstream-reseller-agreement.ts`) writes `payouts: {}`
  without a payouts clause or template. The Agreement has only `seller` and
  `partner` parties.
- Core: `PaymentGuarantorHandler` rejects any non-customer handler type
  (`CustomerPaymentTypes.sessionType`); `PaymentListingProjection` reports A2A as
  `UNSUPPORTED`; Test `CAPTURE` only credits the recipient
  (`host_payment_ledger`, one row per execution). No MyOS operator/fee account
  exists in the Test ledger.
- CI: Core `ci.yml` and Business `ci.yml` run `pull_request` only for `main`.
  PRs to the feature branch get no automatic Verify (see §8).

## 2. Amounts

All amounts are integral minor units of the Agreement currency.

| Symbol | Meaning |
| --- | --- |
| G | Commission settled by this payout; reserved in the Agreement; nominal seller debit |
| F | MyOS fee = `Money/Rounding.roundBps(G, feeBps)` |
| N | Reseller transfer = G − F; PI `amountMinor`, secured and completed |

Invariants: `G > 0`, `F ≥ 0`, `N > 0`, `G = F + N`, one currency. With the
current constant `feeBps = 2000`, `G = 10000 → F = 2000, N = 8000`. `F = 0`
(rounding of tiny G) produces no fee posting and no zero transfer.

## 3. Single fee source

`resolvePayoutTerms` is a function of `Commission Payouts Clause`, used only by
its prepare action:

- Input: G. Output:
  `{grossMinor, feeMinor, netMinor, feeBps, feePolicy: "myos-commission-fee-v1"}`.
- `feeBps = 2000` is defined once, in this function. Core, BFF and UI read the
  frozen result from the document; none of them recomputes it.
- Rejects `N ≤ 0` (`PAYOUT_NET_NOT_POSITIVE`) and any policy other than
  `myos-commission-fee-v1` (`PAYOUT_FEE_POLICY_UNSUPPORTED`).
- F uses the exact shared `Money/Rounding.roundBps`, pinned by BlueId.
- The per-Agreement rate is follow-up §10 of the plan; there is no optional
  Agreement field and no silent fallback now.

## 4. Profile identities

The PI identities already exist and are reused unchanged:
`MyOS/MyOS Test Account to Account Payment Instruction`
(`EGC2BUWSkPbTGuj2sLfmpUALQnRMtnHTvzJb2zVYr4Nk`) and
`MyOS/MyOS Stripe Account to Account Payment Instruction`
(`9hpsLLvz2pt8nioeMPptomxZY49DW2n2V1q5BxURA86Y`); Core already lists both in
`PaymentInstructionTypes`. The gap is that `MyOS/Payment Setup.build` sets
`rootType` for `myos-customer` alone; the payout payment clause supplies the
concrete A2A root type from the frozen operator.

Decision (review 2026-11-08): the manual payout is **replaced in place**, not
kept beside a new profile. `Reseller/Commission Payout Payment Clause` builds
the A2A PI instead of `manual-bank-transfer` (the recipient-confirmed `retire`
path is removed); `Commission Payouts Clause` and `Commission Clause` gain the
fee snapshot and the G/F/N reconcile. Rebuilding gives these
types new BlueIds; documents created earlier keep their pinned runtime, so
historical manual payouts remain readable but are not reinterpreted.

Only additions: `resolvePayoutTerms` (payouts clause function) and the operator split
report `confirmAccountSettlement` with its event, added as a PI method clause
through `Payment Setup` `methodClauses`, so the concrete A2A instruction types
keep their identities.

The Agreement terms carry the accepted policy by name, not by rate:
`payoutFeePolicy: myos-commission-fee-v1` means "transfer of N to the partner
and collection of F by MyOS settle G", and `payoutOperator` binds the payout to
Test or Stripe. The rate itself exists only in `resolvePayoutTerms`.

## 5. Prepare (`startPayout` → `preparePayout`, seller channel)

Input whitelist: `key`, `amountMinor` (G), `payerPaymentAccountId`,
`recipientPaymentAccountId`. A fee, rate or any other field is rejected
(`UNKNOWN_INPUT_FIELD`).

1. Existing checks: `1 ≤ G ≤ 100000000`, one unresolved payout
   (`PAYOUT_ALREADY_UNRESOLVED`), at most 20 payouts, and the reservation of G
   cannot exceed the available commission (`INSUFFICIENT_UNRESERVED_OBLIGATION`).
2. Payment accounts are non-empty, distinct text (`INVALID_PAYMENT_ACCOUNT`).
   Ownership is verified by the operator before any effect (Core).
3. The Agreement terms name the operator and the accepted fee policy:
   `payoutOperator: test|stripe` (`PAYOUT_OPERATOR_UNSUPPORTED`) and
   `payoutFeePolicy: myos-commission-fee-v1` (`PAYOUT_FEE_POLICY_UNSUPPORTED`).
4. `resolvePayoutTerms(G)` freezes `/payouts/<key>/payoutTerms`:
   `feePolicy, feeBps, grossMinor, feeMinor, netMinor, payoutKey, currency,
   operator, payerPaymentAccountId, recipientPaymentAccountId`, and sets the
   payout `amountMinor = N`.
5. `Commission Payout Opened.amountMinor = G` reserves G. An identical retry of
   the same key reads the existing payout. No PI exists yet.

## 6. Confirm and execute

- The seller's `startPayment` on the exact reviewed payout version is the
  confirmation; it creates the PI from the frozen snapshot only.
- PI: concrete Test/Stripe A2A type from `payoutTerms.operator`,
  `paymentDetails = {method: myos-account-to-account, payoutTerms}`, payer
  seller, payee partner, guarantor the MyOS operator party,
  `paymentTerms.amountMinor = N`.
- Financial requests are guarantor-only connections with fixed request IDs and
  the full amount: `securePayout` (`payout-secure`, N) and `capturePayout`
  (`payout-capture`, N). The payout template binds no refund, void, payee,
  details or final-amount request, so neither a party nor a direct Core call can
  request a partial amount, a reversal or a recipient change.
- Embedded documents inherit channels from the Agreement. The MyOS operator is
  therefore a declared (non-approving) Agreement party; it is the only route by
  which the operator can execute and report on the embedded payout PI.

## 7. Settlement and closure

`confirmAccountSettlement` (guarantor) stores `/accountSettlement` once:
`payoutKey, grossMinor, feeMinor, netMinor, currency, transactionId,
debitReference, transferReference` (the split comes from the frozen terms, the
references from the operator). Identical repeat → no-op; different →
`ACCOUNT_SETTLEMENT_CONFLICT`. It emits `Account Settlement Confirmed`.

`Commission Clause.reconcile` settles a reserved payout only when the payout
terms match G (`INVALID_PAYOUT_TERMS` otherwise), no request is
pending/unknown, the settlement record matches G/F/N, `completed = N` and
`reversed = 0`. Then `reserved −= G`, `paid += G`, and the settlement records
`paidMinor = G, transferredMinor = N, feeMinor = F, status: closed`. The report
and `Payment Completed` may arrive in either order.

Closure without payout: an operator `rejectPaymentInstruction` with nothing
secured or completed releases G with `paidMinor = feeMinor = 0`. Nothing else
(timeouts, `reserved = 0`, `secured = 0`) releases G; there is no manual retire.

Not in this slice: cancelling a prepared payout before its PI, and void after
securing (both need an operator-confirmed return path).

Native evidence: `examples/apps/30-commission-a2a-payout.case.yaml` (29 inputs,
replay checked): 1000/200/800 settlement in both report orders, idempotent and
conflicting reports, fee injection, second unresolved payout, over-available
amount and operator rejection. Preparation uses about 7.7M of the 10M gas
limit in this fixture.

## 8. Delivery and validation

- One branch per repository: `claude/commission-a2a-agreement-fee-20261108`,
  PRs to `codex/payments-minimal-alignment-20261104`; PRs reference each other
  and the package BlueIds/versions they consume.
- Core and Business Verify are scoped to PRs into `main`, so the feature-branch
  PRs have no automatic full validation. That is a confirmed trigger-scope gap:
  one manual Verify per final revision is justified under Core `AGENTS.md`,
  after checking for an existing run on that SHA.
- Packages: `packages-release.yml` and `semantic-cards-check.yml` run on every PR.

## 9. Review decisions (2026-11-08)

1. Manual payout payment is replaced in place by the existing MyOS Test/Stripe
   A2A instruction types (§4).
2. Test fee destination: a dedicated MyOS Test payment account owned by the
   guarantor system account, one per currency. Capture posts seller −G,
   partner +N, MyOS fee account +F in one transaction. Core configuration names
   the account; requests cannot choose it.
3. Refund policy §4.4 of the plan (R/S/H/W, no future deductions) is a separate
   follow-up.
4. Stripe LIVE readiness remains unverified (see §10).

## 10. Stripe constraints (Account Debits)

- Platform and connected account must be in the same region (domestic SEPA/EU,
  or US). One platform therefore cannot debit both PL and US sellers; the
  platform country of `CORE_STRIPE_PLATFORM_ACCOUNT_ID` is unverified here.
- Platform must be the losses collector: current onboarding already creates
  Express accounts with `losses_collector=application` (matching).
- Legally binding seller consent to debits must be collected and recorded.
- Debit currency must equal the connected account default currency; the debit
  cannot make the balance negative (no reserves configured); limit 100,000 USD
  equivalent; extra Stripe cost.
- The reseller needs a transfer-receiving capability; onboarding requests only
  `card_payments` today.
