# Commission A2A payout with MyOS fee — contract (stage 1 review draft)

Status: implemented Blue contract of the commission A2A plan (revision 3,
2026-11-08), reviewed with the owner on 2026-11-08. Core operator execution and
Business presentation consume it.

Operator stage: **Test** is implemented end to end. **Stripe** (Account Debit
of G, Transfer of N, return of G on void) is still missing; Core rejects a
Stripe payout before any effect, which releases G.

Reviewed bases (all on `codex/payments-minimal-alignment-20261104`):

| Repository | Base SHA |
| --- | --- |
| blue-packages | `a639c3c6164d022c356b308fee4f443feaeaddf6` |
| myos-core | `f796e2160c89eaab871d2a6ec9a30284324ebe1c` (initially `7fbb70164da7e551ccb27b867e25c07cd43c9092`) |
| myos-business | `38d169cefc49bcdce0c472e89d931dbca61c2b22` (initially `af496d132b17fbb16fe7e6ddf399c6a567db3f59`) |

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
kept beside a new profile. `Reseller/Commission Payout Payment Clause` (manual
`manual-bank-transfer` PI with the recipient-confirmed `retire` path) is
removed. Rebuilding gives the Reseller types new BlueIds; documents created
earlier keep their pinned runtime.

Decision (review 2026-11-08, implementation): the payout PI is a **separate
document**, bootstrapped like the order PI, not embedded in the Agreement.
Embedded documents inherit the parent's parties, and every parent party must be
represented in each child, so an operator party in the Agreement would also be
required in every Order. The Agreement therefore stays private to `{seller,
partner}`; the MyOS operator joins only the payout PI as its hosting-supplied
`guarantor`.

Additions: `resolvePayoutTerms` (payouts clause function) and
`Reseller/Commission Payout Settlement Clause` (operator split report
`confirmAccountSettlement` with its event), declared by the payout PI template.
The concrete A2A instruction types keep their identities.

The Agreement terms carry the accepted policy by name, not by rate:
`payoutFeePolicy: myos-commission-fee-v1` means "transfer of N to the partner
and collection of F by MyOS settle G", and `payoutOperator` binds the payout to
Test or Stripe. The rate itself exists only in `resolvePayoutTerms`.

## 5. Prepare (`startPayout` → `preparePayout`, seller channel)

`Commission Payouts Clause` is a `Documents/Document Base` clause:
`prepareFor: bootstrap`, `obtain: provide`, `suppliedBy: seller`,
`suppliedParties: [guarantor]`, keyed collection `/payouts`, template
`/payoutTemplate`. Input whitelist: `key` and `amountMinor` (G). A fee, rate,
payment account or any other field is rejected (`UNKNOWN_INPUT_FIELD`).

1. Checks: `1 ≤ G ≤ 100000000`, one unresolved payout
   (`PAYOUT_ALREADY_UNRESOLVED`), at most 20 payouts (`DOCUMENT_LIMIT_REACHED`),
   and the reservation of G cannot exceed the available commission
   (`INSUFFICIENT_UNRESERVED_OBLIGATION`). An identical retry of an existing key
   reuses its preparation.
2. The Agreement terms name the operator, its MyOS operator account and the
   accepted fee policy: `payoutOperator: test|stripe`
   (`PAYOUT_OPERATOR_UNSUPPORTED`), `payoutOperatorAccountId`
   (`PAYOUT_OPERATOR_ACCOUNT_REQUIRED`) and
   `payoutFeePolicy: myos-commission-fee-v1` (`PAYOUT_FEE_POLICY_UNSUPPORTED`).
   Both parties accept these terms with the Agreement.
3. `resolvePayoutTerms(G)` freezes the prepared PI's
   `/paymentDetails/payoutTerms`: `feePolicy, feeBps, grossMinor, feeMinor,
   netMinor, payoutKey, currency, operator, operatorAccountId,
   agreementOrigin` (this Agreement's document identity), and sets
   `paymentTerms.amountMinor = limitMinor = N`.
4. `domainPrepare` requires the template to be the Test/Stripe A2A type matching
   the operator, method `myos-account-to-account`, matching currency, payer,
   payee and guarantor channels declared as PI parties, and the payer in the
   instruction's Activation `required` list (`PAYOUT_INSTRUCTION_INVALID`).
5. `Commission Payout Opened.amountMinor = G` reserves G.
6. Payment accounts are not chosen by a request. The operator debits the payer
   party's and credits the payee party's own payment account for the operator
   (one per MyOS account and provider), verified before any effect.

## 6. Bootstrap, provide and execute

- The seller bootstraps the prepared PI (seller and partner mapped from the
  Agreement, guarantor supplied by hosting as the MyOS operator) and provides
  it with `providePayout`. Documents verifies the inactive PI in full (frozen
  preparation, roster, domain terms) and holds it as `awaiting_activation` with
  its `candidateOrigin`; no other instruction can replace it. Only then does the
  seller approve the PI (`approve_seller`): the payer approves its own debit, and
  payment, including the operator's acceptance request, starts only on an active
  PI. Providing the approved PI again links it under `/payouts/<key>`. An
  approval before provision is the seller's own choice; Business sends it only
  once the Agreement holds the PI. `domainValidateCandidate` rejects a candidate whose
  `paymentTerms` or `paymentDetails` differ from the frozen terms
  (`PAYOUT_TERMS_MISMATCH`) and a candidate whose guarantor is not the
  Agreement's `payoutOperatorAccountId` (`PAYOUT_OPERATOR_MISMATCH`): the
  seller supplies the guarantor at bootstrap, so without this check a
  seller-chosen "operator" could report a settlement or a decline itself.
- Operator gate (Core): the operator executes only a payout this Agreement has
  linked. Before any effect it verifies, with a narrow Core read of the
  Agreement named by `agreementOrigin`, that `/payouts/<payoutKey>` is exactly
  this PI and the Agreement parties are the PI payer and payee. Until then it
  waits; it rejects the PI (no effect) when the preparation was cancelled.
  Linking is irreversible and native cancellation refuses a linked
  preparation, so cancellation and execution exclude each other. An
  interruption after approval and before the second provision therefore
  moves no funds; sending again links the same PI. Provision embeds the PI at `/payouts/<key>` and emits
  `Documents/Document Attached`; `Commission Clause.payoutAttached` reconciles.
- PI: concrete Test/Stripe A2A type, `paymentDetails = {method:
  myos-account-to-account, payoutTerms}`, payer seller, payee partner,
  guarantor the MyOS operator, `paymentTerms.amountMinor = N`.
- Payer consent (review 2026-11-08): the operator acts only on a PI whose
  native Activation clause (`HRac84i2MqGQmcHdysnrmKjw3pQpLw7Fd82m4MJv8CZP`)
  requires the payer and is active with the payer's approval. Document content
  alone proves nothing, since any account can bootstrap a PI that names another
  account as payer; hosting binds each declared party's channel to that party's
  own timeline, and Activation records an approval only from the party's channel.
- Financial requests are guarantor-only connections with fixed request IDs and
  the full amount: `securePayout` (`payout-secure`, N) and `capturePayout`
  (`payout-capture`, N). The seller's only financial request is `voidPayout`
  (`payout-void`, the whole secured amount), which the PI protocol accepts only
  with funds secured and no secure or capture pending, and which blocks any
  later secure or capture. The template binds no refund, payee, details or
  final-amount request, so neither a party nor a direct Core call can request a
  partial amount, a reversal of a completed payout or a recipient change.

## 7. Settlement and closure

`confirmAccountSettlement` (guarantor) stores `/accountSettlement` once:
`payoutKey, grossMinor, feeMinor, netMinor, currency, transactionId,
debitReference, transferReference` (the split comes from the frozen terms, the
references from the operator). Identical repeat → no-op; different →
`ACCOUNT_SETTLEMENT_CONFLICT`. It emits `Account Settlement Confirmed`.

`Commission Clause.reconcile` reads the attached PI at `/payouts/<key>` and
settles a reserved payout only when its payout terms match G
(`INVALID_PAYOUT_TERMS` otherwise), no request is pending/unknown, the
settlement record matches G/F/N, `completed = N` and `reversed = 0`. Then
`reserved −= G`, `paid += G`, and the settlement records `paidMinor = G,
transferredMinor = N, feeMinor = F, status: closed`. The report and `Payment
Completed` may arrive in either order.

Closure without payout releases G exactly once with `paidMinor = feeMinor =
0` (settlement `status: closed`); a new payout can then start:

- Cancellation before linking: the seller's `cancelPayout` is the native
  Documents cancellation. It is refused once the preparation is linked
  (`PREPARATION_SELECTED_PROCESS_REQUIRES_DOMAIN_CANCELLATION`) and closes the
  requirement (`cancellation_requested`) so the key can never be provided
  again. `Commission Clause.payoutCancelled` releases G only for that state,
  with nothing under `/payouts/<key>`. A bootstrapped or held instruction of a
  cancelled preparation is never executed (operator gate above). Closing a UI
  window releases nothing.
- Operator rejection (`rejectPaymentInstruction`), or a declined or failed
  fixed securing request (`payout-secure`), with nothing secured or completed.
  The operator rejects at acceptance any approved PI whose split contradicts
  it, terms it cannot execute (currency, missing or shared accounts, the MyOS
  fee account as a party) and insufficient funds, and declines a secure only
  on a confirmed refusal with no hold. A timeout, a lost response or a worker
  failure is retried with the same execution identity, never reported as a
  decline.
- Confirmed void (`payout-void` succeeded via the operator's
  `cancelBeforeCompletion`), which returned the whole secured G to the seller
  before any partner transfer; nothing secured or completed remains.

Nothing else (timeouts, `reserved = 0`, `secured = 0`, a pending or unknown
request) releases G; there is no manual retire.

Native evidence:

- `examples/apps/30-commission-a2a-payout.case.yaml` (10 inputs, replay checked):
  approvals, preparation 1000/200/800, idempotent retry, fee injection, a
  second unresolved payout, cancellation before linking that releases G once
  (a repeat releases nothing), a new payout after it, and a partner refused
  cancellation.
- `tools/CommissionPayoutConformance.java` (`check_operation_inputs.py --case
  commission-payout`): real preparation (a template without the payer's approval
  is rejected) and initialization of the prepared PI with the supplied operator,
  which stays inactive with no payment until the seller approves it; then, from a
  modeled provided and approved state (the PI under `/payouts/p1`), real operator
  operations: split report plus completion settles G once (F = 200, N = 800),
  conflicting and identical reports, the over-available amount, operator
  rejection, a declined secure that releases G for a new payout, and a void: refused before securing, by the
  partner and with a capture pending; while pending it blocks capture and keeps G reserved; confirmed, it
  releases G with fee 0. The frozen terms name the operator account and this Agreement. Bootstrap provision compares Timeline actors,
  which the native runner cannot express; the hosted Core test covers it.

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
