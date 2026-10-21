# Operation input coverage

Central execution plan: `myos-business/docs/generic-operations-execution-plan.md`.
This is the source coverage register, not a second implementation plan.

Baseline: source `e1114704825b29e4ca584f6000b6a9a8ae345b51`, Core `150f45b4cfef3e0e08d2d6fbcfc11bbbc04d24bb`. The acceptance baseline has **34 current packages**. One additional `blue-definition-read` support protocol is explicitly included; it is not a replacement for any baseline row. Historical source publications are unchanged.

## All current source families

`CHANGED` records implementation, not a passing final qualification. `INHERITED` and `EXCEPTION` identify actual source arrangements; all relevant final runtime paths still require the gates below. Baseline versions are provenance; candidate versions identify unpublished work.

| Package | Baseline → candidate | Scope and source evidence | Disposition |
|---|---|---|---|
| `blue-language` | 1.0.0 → 1.0.0 | A10 protocol/type definitions: `blue-package.yaml`, exported definitions; no installed business operation missing an input | EXCEPTION |
| `blue-bex` | 1.0.0-final-gas.1 → 1.0.0-final-gas.1 | A10 protocol/type definitions: `blue-package.yaml`, exported definitions; no installed business operation missing an input | EXCEPTION |
| `blue-contracts` | 1.0.0-final-gas.1 → 1.0.0-final-gas.1 | A10 protocol/type definitions: `blue-package.yaml`, exported definitions; no installed business operation missing an input | EXCEPTION |
| `blue-coordination` | 0.2.0-access-events.1 → 0.2.0-access-events.1 | A10 protocol/type definitions: `blue-package.yaml`, exported definitions; no installed business operation missing an input | EXCEPTION |
| `blue-time` | 0.2.0-gas10m.1.finalgas.1 → 0.2.0-gas10m.1.finalgas.1 | A10 protocol/type definitions: `blue-package.yaml`, exported definitions; no installed business operation missing an input | EXCEPTION |
| `blue-dispatch` | 0.1.0-preview.1 → 0.1.0-preview.1 | A10 protocol/type definitions: `blue-package.yaml`, exported definitions; no installed business operation missing an input | EXCEPTION |
| `blue-events` | 0.7.0-preview.1.finalgas.1 → 0.7.0-preview.1.finalgas.1 | A10 protocol/type definitions: `blue-package.yaml`, exported definitions; no installed business operation missing an input | EXCEPTION |
| `blue-parties` | 0.8.0-preview.1 → 0.8.0-preview.1 | A10 shared/inherited types: `types/`; concrete public operations belong to implementing clauses | INHERITED |
| `blue-mandates` | 0.2.0-preview.1.finalgas.1 → 0.2.0-preview.1.finalgas.1 | A10 explicit empty and native typed matchers: `types/mandate.blue`, `qualification-mandate.blue`: approveMandate/requestEvidence explicit {}; terminateMandate reason; provideEvidence Evidence Responded | EXCEPTION |
| `blue-clauses` | 0.8.0-preview.1 → 0.8.0-preview.1 | A10 shared/inherited types: `types/`; concrete public operations belong to implementing clauses | INHERITED |
| `blue-agreements` | 0.8.0-preview.1 → 0.8.0-preview.1 | A10 shared/inherited types: `types/`; concrete public operations belong to implementing clauses | INHERITED |
| `blue-orders` | 0.8.0-preview.1 → 0.8.0-preview.1 | A10 shared/inherited types: `types/`; concrete public operations belong to implementing clauses | INHERITED |
| `blue-documents` | 0.8.0-preview.1 → 0.8.0-preview.1 | A10 shared/inherited types: `types/`; concrete public operations belong to implementing clauses | INHERITED |
| `clause-connections` | 0.8.0-preview.1 → 0.8.0-preview.3 | Explicit configured workflow input: `types/planning-functions.blue`: exact definition read with explicit action binding precedence over defaultBindings; no action-name/default inference | CHANGED |
| `clause-commerce` | 0.8.0-preview.1 → 0.8.0-preview.3 | A9 quote: `types/functions.blue`, `product-clause.blue`: bounded unitPriceMinor/quantity, currency from configuration | CHANGED |
| `clause-amendments` | 0.8.0-preview.1 → 0.8.0-preview.3 | A9 propose / approve: `types/functions.blue`, `amendment-input.blue`, `clause.blue`: public typed optional preservePending; raw internal entry preserved | CHANGED |
| `clause-activation` | 0.8.0-preview.2 → 0.8.0-preview.3 | A1 eight generated operations: `types/functions.blue`, `negotiation.blue`, `plan.blue`: requestFrom entries and explicit native public adapters; no preparation metadata | CHANGED |
| `payment-instruction` | 0.8.0-preview.1 → 0.8.0-preview.3 | A7 all36 responses and14 reusable requests: `types/payment-instruction.blue`, `payment-protocol-functions.blue`, `payment-action-definitions.blue`; configured examples27/28/29 explicit public requests | CHANGED |
| `clause-documents` | 0.8.0-preview.2 → 0.8.0-preview.3 | A2 admission/access/source/preparation: `types/admission-functions.blue`, `source-functions.blue`, `preparation-functions.blue`, `preparation-plan.blue`; original raw internal callers preserved | CHANGED |
| `clause-payment` | 0.8.0-preview.2 → 0.8.0-preview.3 | A2/A7 inherited Documents and request actions: `types/process-clause.blue`, `conditional-base.blue`: configured amount defaults do not become mandatory public input | INHERITED / REBUILT |
| `clause-state-machine` | 0.8.0-preview.1 → 0.8.0-preview.3 | A9 transition: `types/functions.blue`, `transition-input.blue`, `clause.blue`: to required; reason optional; allowed targets from configuration | CHANGED |
| `clause-features` | 0.8.0-preview.1 → 0.8.0-preview.3 | A10 configured actions: `types/clause.blue`: operation input belongs to supplied action/workflow configuration, not a universal family schema | INHERITED / REBUILT |
| `blue-money` | 0.7.0-preview.1.finalgas.1 → 0.7.0-preview.1.finalgas.1 | A10 shared/inherited types: `types/`; concrete public operations belong to implementing clauses | INHERITED |
| `clause-balance` | 0.8.0-preview.1 → 0.8.0-preview.3 | A9 setTarget / reserve / settle: `types/functions.blue`: key; nonnegative target, positive reservation; no amount required for settle | CHANGED |
| `clause-termination` | 0.8.0-preview.1 → 0.8.0-preview.3 | A10 lifecycle actions: `types/clause.blue`, `functions.blue`: configured request/finish use lifecycle state; no missing fields inferred solely from empty matcher | EXCEPTION / REBUILT |
| `clause-inspection` | 0.8.0-preview.2 → 0.8.0-preview.3 | A2 inherited preparation: `types/clause.blue`, `preparation-functions.blue`: shared Documents inputs, configuration-specific fields | INHERITED / REBUILT |
| `clause-schedule` | 0.8.0-preview.1 → 0.8.0-preview.3 | A10 configured lifecycle actions: `types/clause.blue`, `functions.blue`: start configuration/state controls generated child input | INHERITED / REBUILT |
| `myos` | 0.8.0-preview.2 → 0.8.0-preview.3 | A6 three session/funding operations: `types/customer-instruction.blue`, `customer-session-functions.blue`: sessionId; optional expiresAt only for provideSession; no invented amount/currency | CHANGED |
| `acme-bank` | 0.8.0-preview.2 → 0.8.0-preview.3 | A4 four transfer operations: `types/transfer-contract.blue`, `transfer-functions.blue`: requestId/reference; conditional amountMinor/currency; no required reason | CHANGED |
| `manual-payments` | 0.8.0-preview.2 → 0.8.0-preview.3 | A5 one instruction + four receipt operations: `types/instruction.blue`, `receipt-instruction.blue`: preserve distinct extra-field and length rules | CHANGED |
| `shipping-instruction` | 0.8.0-preview.2 → 0.8.0-preview.3 | A8 nine responses + three reusable requests: `types/functions.blue`, `instruction.blue`, `request-actions.blue`: requestId; address only for change-address; optional trackingId/reason | CHANGED |
| `clause-representation` | 0.8.0-preview.1 → 0.8.0-preview.3 | A10 configured delegation: `types/clause.blue`: public shape depends on explicit configured delegation workflow; no independent static operation declaration | INHERITED / REBUILT |
| `clause-attachments` | 0.8.0-preview.2 → 0.8.0-preview.3 | A3 attach/authority/access/preparation: `types/*functions.blue`, `*plan.blue`: initialized document references, native typed public Access lists, explicit configured matcher preservation and roster parameters | CHANGED |
| `blue-tasks` | 0.1.0-preview.3.access-events.1 → 0.1.0-preview.4.access-events.1 | A10 late assignment: `types/work-clause.blue`: reportSuccess request assigned from reportRequest after construction; no Task executor exposed to chat | EXCEPTION / REBUILT |

## Explicit additional capability

`blue-definition-read` / namespace `DefinitionRead` / `1.0.0-preview.1` is published by the existing native protocol builder. Connections and Attachments declare its exact execution requirement. It enables `$document {path, view: definition}` to return the exact canonical definition reference, including schema-only matchers and empty definitions. Default value reads remain unchanged. Source null follows native Language admission; the reader invents no distinct native null field. Historical execution selections do not silently acquire this capability.

## Current static publication mappings

Each row below is extracted from the actual authored declaration. An explicit request remains authoritative; every requestFrom link is resolved and validated by the same helper in both builders.

| Family / operation | Authored source | Explicit input entry |
|---|---|---|
| payment-instruction / `acceptPaymentInstruction` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / acceptPublic / input` |
| payment-instruction / `rejectPaymentInstruction` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / rejectPublic / input` |
| payment-instruction / `recordTransactionInitiated` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / initiatePublic / input` |
| payment-instruction / `recordTransactionInitiationFailed` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordInitiationFailurePublic / input` |
| payment-instruction / `secureFunds` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeSuccessPublic / input` |
| payment-instruction / `declineSecureFunds` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `failSecureFunds` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `recordFundsSecuringUnknown` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `completePayment` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeSuccessPublic / input` |
| payment-instruction / `declineCompletePayment` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `failCompletePayment` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `recordPaymentCompletionUnknown` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `cancelBeforeCompletion` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeSuccessPublic / input` |
| payment-instruction / `declineCancelBeforeCompletion` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `failCancelBeforeCompletion` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `recordPaymentCancellationUnknown` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `reverseAfterCompletion` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeSuccessPublic / input` |
| payment-instruction / `declineReverseAfterCompletion` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `failReverseAfterCompletion` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `recordPaymentReversalUnknown` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / recordOutcomeFailurePublic / input` |
| payment-instruction / `confirmPayeeAssignment` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlSuccessPublic / input` |
| payment-instruction / `rejectPayeeAssignment` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlFailurePublic / input` |
| payment-instruction / `confirmTransactionDetailsUpdated` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlSuccessPublic / input` |
| payment-instruction / `rejectTransactionDetailsUpdate` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlFailurePublic / input` |
| payment-instruction / `failTransactionDetailsUpdate` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlFailurePublic / input` |
| payment-instruction / `resolveFinalAmount` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlSuccessPublic / input` |
| payment-instruction / `rejectFinalAmountResolution` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlFailurePublic / input` |
| payment-instruction / `lockPaymentCompletion` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlSuccessPublic / input` |
| payment-instruction / `failPaymentCompletionLockChange` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / failPaymentCompletionLockChangeResponsePublic / input` |
| payment-instruction / `unlockPaymentCompletion` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlSuccessPublic / input` |
| payment-instruction / `lockPaymentReversal` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlSuccessPublic / input` |
| payment-instruction / `failPaymentReversalLockChange` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / failPaymentReversalLockChangeResponsePublic / input` |
| payment-instruction / `unlockPaymentReversal` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlSuccessPublic / input` |
| payment-instruction / `lockTransactionDetailsUpdate` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlSuccessPublic / input` |
| payment-instruction / `failTransactionDetailsUpdateLockChange` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / failTransactionDetailsUpdateLockChangeResponsePublic / input` |
| payment-instruction / `unlockTransactionDetailsUpdate` | `payment-instruction/types/payment-instruction.blue` | `{'type': 'PaymentInstruction/Payment Protocol Functions'} / decideControlSuccessPublic / input` |
| shipping-instruction / `confirmShipment` | `shipping-instruction/types/instruction.blue` | `{'type': 'Shipping/Shipping Functions'} / respondPublic / input` |
| shipping-instruction / `rejectShipment` | `shipping-instruction/types/instruction.blue` | `{'type': 'Shipping/Shipping Functions'} / respondPublic / input` |
| shipping-instruction / `recordDispatched` | `shipping-instruction/types/instruction.blue` | `{'type': 'Shipping/Shipping Functions'} / respondPublic / input` |
| shipping-instruction / `confirmDelivery` | `shipping-instruction/types/instruction.blue` | `{'type': 'Shipping/Shipping Functions'} / respondPublic / input` |
| shipping-instruction / `failShipment` | `shipping-instruction/types/instruction.blue` | `{'type': 'Shipping/Shipping Functions'} / respondPublic / input` |
| shipping-instruction / `confirmCancellation` | `shipping-instruction/types/instruction.blue` | `{'type': 'Shipping/Shipping Functions'} / respondPublic / input` |
| shipping-instruction / `rejectCancellation` | `shipping-instruction/types/instruction.blue` | `{'type': 'Shipping/Shipping Functions'} / respondPublic / input` |
| shipping-instruction / `confirmAddressChange` | `shipping-instruction/types/instruction.blue` | `{'type': 'Shipping/Shipping Functions'} / respondPublic / input` |
| shipping-instruction / `rejectAddressChange` | `shipping-instruction/types/instruction.blue` | `{'type': 'Shipping/Shipping Functions'} / respondPublic / input` |
| acme-bank / `requestTransfer` | `acme-bank/types/transfer-contract.blue` | `{'type': 'ACME/Bank Transfer Functions'} / request / input` |
| acme-bank / `confirmTransfer` | `acme-bank/types/transfer-contract.blue` | `{'type': 'ACME/Bank Transfer Functions'} / confirmPublic / input` |
| acme-bank / `reportTransferUnknown` | `acme-bank/types/transfer-contract.blue` | `{'type': 'ACME/Bank Transfer Functions'} / unknownPublic / input` |
| acme-bank / `declineTransfer` | `acme-bank/types/transfer-contract.blue` | `{'type': 'ACME/Bank Transfer Functions'} / declinePublic / input` |
| manual-payments / `reportTransfer` | `manual-payments/types/instruction.blue` | `{'type': 'ManualPayments/Manual Transfer Functions'} / reportTransfer / input` |
| manual-payments / `reportTransfer` | `manual-payments/types/receipt-instruction.blue` | `{'type': 'ManualPayments/Manual Receipt Functions'} / report / input` |
| manual-payments / `acknowledgeTransfer` | `manual-payments/types/receipt-instruction.blue` | `{'type': 'ManualPayments/Manual Receipt Functions'} / acknowledge / input` |
| manual-payments / `reportRefund` | `manual-payments/types/receipt-instruction.blue` | `{'type': 'ManualPayments/Manual Receipt Functions'} / reportRefund / input` |
| manual-payments / `acknowledgeRefund` | `manual-payments/types/receipt-instruction.blue` | `{'type': 'ManualPayments/Manual Receipt Functions'} / acknowledgeRefund / input` |
| myos / `provideSession` | `myos/types/customer-instruction.blue` | `{'type': 'MyOS/Customer Session Functions'} / provideSessionPublic / input` |
| myos / `confirmFunding` | `myos/types/customer-instruction.blue` | `{'type': 'MyOS/Customer Session Functions'} / confirmFunding / input` |
| myos / `requestCustomerFunding` | `myos/types/customer-instruction.blue` | `{'type': 'MyOS/Customer Session Functions'} / requestFunding / input` |

## Dynamic and mapped public inputs

- A1: approve requires revision and conditional termsRef; updateParty requires replacement.lead.channel with optional party and no revision; proposal entries require proposalId/baseTermsRef/nonempty changes, optional supersedes; term-selection entries require termsRef with conditional proposalId; withdraw/reject require proposalId. Public List adapters consume native List values from `/changes`, never a guessed `/changes/items` value-view path.
- A2/A3: Documents/Attachments entry schemas and generators are qualified by `DocumentInputConformance`; public Access lists use explicit native List envelopes while raw internal callers retain their prior ABI. Existing references must satisfy the initialized document structure checked by the executor. Configured prepare/provide/cancel/resume retain their explicit mapping-specific public shape. The12 typed begin bindings in11 preparation examples explicitly materialize the reviewed trigger as an object and remove its type before calling the existing raw internal begin ABI; the public request remains typed and unchanged.
- A7: all14 configured request actions are represented in examples27/28/29. Thirteen input-bearing operations use explicit Payment Request Input with requestId and relevant control fields; optional financial aliases remain optional. Their mapping removes the reviewed type envelope explicitly. approveRecipient uses state and requires no fields. Other supplied financial workflows with constant requestId/amount declare no required user inputs; identity mappings declare their external input.
- A8: examples25 declares separate book/cancel/change-address inputs. Three public request entry functions preserve the shared executor without requiring address for book/cancel. Nine typed response adapters retain optional trackingId/reason.
- A9: examples15/16/18/07/20 declare actual external request shapes; example07 explicitly uses existing Legacy Payment Clause for its legacy amount/instruction/start bindings (current Payment Clause extends Documents/Document Base and does not expose that ABI); mapping-supplied fields are not copied blindly from internal signatures. Native function/caller tests cover bounded quote, ledger operations, amendment optionality and configured transition targets.

## Native semantics and authoring evidence

The shared helper has prior PASS evidence for both builders, imported/inherited functions, distinct same-name libraries, explicit request including {}, invalid links, scalar/list/reference inputs, labels, native optionality, self-library generator publication and native BEX argument calls. Raw objects do not automatically satisfy named input types. Descriptions are metadata, not required payload values. See `tools/test_operation_inputs.py` and `OperationInputConformance.java`.

## Qualification status

The final catalogue is `4fa19e26453533eb48c92db66956521fae21cd23fe5aa9ef3712420dd363577d` after the Documents dependency closure rebuild. Earlier evidence for unchanged package identities remains applicable and records its earlier complete catalogue. `PENDING` and `FAIL` are not passes.

| Gate | Current evidence | Status |
|---|---|---|
| Both authoring builders/native semantics | `helper-native-verification.json`: all3 cases | PASS |
| Activation eight minimal input shapes + approval effect | `owned-native-verification.json`: activation-inputs | PASS |
| Activation negotiation/replacement effects | Same report: activation-effects; native List adapter `/changes` | PASS |
| Payment36 matchers | Same report: payment-inputs | PASS |
| Payment36responses +14actions native effects | payment-execution/summary.json:36responses +14actions, actual effects and deterministic replay across27/28/29/recipient variant | PASS |
| Shipping nine responses/three mapped requests | final8-shipping/report.json: matcher without root description and inherited/default override precedence | PASS |
| Provider12 | provider-final-cap-verification.json: final catalogue12 PASS | PASS |
| Additional action libraries | actions-final-cap-verification.json: final capability canonical and7 native action effects | PASS |
| Documents/Attachments | Final inputs and Access guards PASS; source08 Attachment begin/resume and current Payment Clause prepare/resume strengthened native effect assertions PASS (`final-inputs.log`, `final-accessGuards.log`, `final-preparation.log`, `final-paymentPreparation.log`) | PASS |
| Byte reproducibility for20changed +support | final-reproducibility-verification.json: unaffected13 PASS reused; final8 comparisons PASS | PASS |
| Configured published examples |07/15/16/18/20/25 native execution and deterministic replay:8/4/7/6/5/12 inputs;07/25 rerun PASS after final8 closure;07 legacy ABI corrected without removing assertions | PASS |
| Repository static checks | final8-static-verification.json: release35; payment50messages/36responses; tutorial13families/30documents; unit9; catalogue consistency; diffcheck | PASS |

Evidence files are under ignored `reports/operation-input/`; source and catalogue identities are recorded in each maintained native qualification report.

The first DefinitionRead draft incorrectly claimed a native null/absent distinction. Its intermediate build was deliberately stopped with exit143. It was not qualified. The corrected rules require canonical Language admission, and the complete dependency closure is rebuilt with corrected IDs. Transport-level request omission, literal null and {} handling remains a separate API concern.

See [operation-input-qualification.md](operation-input-qualification.md) for maintained suite instructions and native List representation. The source build, native A1–A10 qualification, reproducibility and repository checks listed above are complete and PASS. Cross-repository HTTP/Confirm integration, the current 49 real-model scenarios and UI qualification remain separate required gates and have not yet run against this final imported candidate. No local build is an external publication or deployment.
