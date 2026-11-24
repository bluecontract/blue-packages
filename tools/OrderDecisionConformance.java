import blue.bex.BexError;
import blue.contracts.ClauseGasProbe;
import blue.contracts.ContractException;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Native rejection, Connections mappings and selected-instruction capture policy. */
public final class OrderDecisionConformance {
  private static final String REQUEST_ID = "order-accepted-capture";

  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]);
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var language = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var processor = runtime.processor(language);
      rejection(processor);
      configuredClosure(processor);
      capture(processor);
    }
  }

  private static void rejection(Contracts processor) {
    var connection = map("on", "workflow", "party", "seller", "input", true,
        "params", map("provider", "configured"),
        "inputParams", map("/values/reference", "/reference", "/values/fallback", "/absent",
            "/values/amountMinor", "/amountMinor"),
        "documentParams", map("/values/amountMinor", "/amountMinor",
            "/values/orderOrigin", "/contracts/initialized/document"));
    var projection = map("type", "Features/Feature Clause",
        "parameters", map("actions", map("record", map(
            "defaults", map("values", map("fallback", "kept")),
            "do", List.of(map("$appendChange", map("path", "/recorded", "op", "add", "val", map("$var", "params"))))))),
        "bindings", map("record", map("recordContext", connection)));
    var source = map("name", "Native seller decision", "type", "Orders/Order with Seller Decision", "amountMinor", 7200,
        "clauses", map("activation", activation(List.of("seller", "buyer"), List.of("rejectOrder", "recordContext")),
            "projection", projection));
    var initial = initialized(processor, source);
    equal("PENDING", processor.read(initial, "/orderDecision/status"), "Initial seller decision");
    equal(false, processor.read(initial, "/activation/active"), "Order waits for seller approval");

    var recorded = process(processor, initial,
        event(initial, "seller", "recordContext",
            map("reference", "provider-1", "provider", "caller", "amountMinor", 1), true), 1).document();
    equal("7200", String.valueOf(processor.read(recorded, "/recorded/values/amountMinor")), "Document projection");
    equal("provider-1", processor.read(recorded, "/recorded/values/reference"), "Nested input projection");
    equal("kept", processor.read(recorded, "/recorded/values/fallback"), "Missing projection preserves fallback");
    equal("configured", processor.read(recorded, "/recorded/provider"), "Explicit params override forwarded input");
    equal("provider-1", processor.read(recorded, "/recorded/reference"), "Unmapped request field is forwarded");
    var values = processor.execution().values();
    var origin = values.select(new Exact.Ref(initial.blueId()), "/contracts/initialized/document");
    var mappedOrigin = values.select(new Exact.Ref(recorded.blueId()), "/recorded/values/orderOrigin");
    equal(NativeRuntime.identity(values.exact(origin)), NativeRuntime.identity(values.exact(mappedOrigin)),
        "A projected Order origin retains its exact BlueId");

    var revision = processor.read(recorded, "/activation/revision");
    var reject = map("revision", revision);
    noRejection(processor, recorded, event(initial, "seller", "rejectOrder", reject, true), 2);
    noRejection(processor, recorded, event(recorded, "customer", "rejectOrder", reject, true), 3);
    failure(processor, recorded, event(recorded, "seller", "rejectOrder", reject, false), 4, "EXACT_REVIEW_REQUIRED");
    failure(processor, recorded, event(recorded, "seller", "rejectOrder", map("revision", 999), true),
        5, "ORDER_REVISION_CHANGED");

    var rejected = process(processor, recorded, event(recorded, "seller", "rejectOrder", reject, true), 6);
    equal("REJECTED", processor.read(rejected.document(), "/orderDecision/status"), "Seller rejection");
    equal(revision, processor.read(rejected.document(), "/orderDecision/revision"), "Reviewed revision recorded");
    equal(1L, ClauseGasProbe.eventData(processor, rejected).stream().filter(OrderDecisionConformance::isRejection).count(),
        "One rejection event");
    var retry = process(processor, rejected.document(),
        event(rejected.document(), "seller", "rejectOrder", reject, true), 7);
    equal(List.of(), processor.emitted(retry), "An exact retry emits no event");
    var approve = process(processor, retry.document(),
        event(retry.document(), "seller", "approve_seller", reject, true), 8);
    var buyerApprove = process(processor, approve.document(),
        event(approve.document(), "buyer", "approve_buyer", reject, true), 9);
    equal(false, processor.read(buyerApprove.document(), "/activation/active"), "Rejection blocks later approval");
    for (String role : List.of("seller", "buyer")) {
      equal(false, Boolean.TRUE.equals(processor.read(buyerApprove.document(), "/activation/approved/" + role)),
          "Rejection blocks approval for " + role);
    }
    var accessUpdate = map("type", "Activation/Party Update Input",
        "replacement", map("lead", map("channel", channel("seller")), "displayName", "Seller contact"));
    var updated = process(processor, buyerApprove.document(),
        event(buyerApprove.document(), "seller", "updateParty_seller", accessUpdate, true), 10).document();
    equal("Seller contact", processor.read(updated, "/activation/parties/seller/displayName"),
        "Rejection still permits participant access updates");
    equal("REJECTED", processor.read(updated, "/orderDecision/status"), "Participant access changes preserve the decision");
    guardDenied(processor, updated, "seller", "approve_seller",
        map("revision", processor.read(updated, "/activation/revision")), 11, "ORDER_REJECTED");

    var sellerAccepted = process(processor, recorded,
        event(recorded, "seller", "approve_seller", reject, true), 6).document();
    var accepted = process(processor, sellerAccepted,
        event(sellerAccepted, "buyer", "approve_buyer", reject, true), 7).document();
    equal(true, processor.read(accepted, "/activation/active"), "The same approvals apply before rejection");
    failure(processor, accepted, event(accepted, "seller", "rejectOrder", reject, true), 8, "ORDER_ALREADY_ACCEPTED");
    System.out.println("PASS seller rejection, exact version checks, retry, dispatch denial and workflow projections");
  }

  private static void configuredClosure(Contracts processor) {
    var activation = activation(List.of("seller"), List.of("rejectOrder", "withdrawOrder",
        "proposeAndActivate", "audit/receipt~reconcile"));
    parameters(activation).put("negotiation", map("allowedPaths", List.of("/price")));
    var settlementEvent = map("type", "Commerce/Domain Event", "kind", "Settlement reconciled", "clause", "reconciliation");
    var reconciliation = map("type", "Features/Feature Clause",
        "parameters", map("actions", map("record", map("do",
            List.of(map("$appendChange", map("op", "add", "path", "/reconciled", "val", true)))))),
        "bindings", map("record", map("afterSettlement", map("on", "event", "event", settlementEvent))));
    parameters(activation).put("preActivationConnections", List.of(
        map("clause", "reconciliation", "action", "record", "connection", "afterSettlement")));
    var cancellation = map("type", "Commerce/Whole Order Cancellation Policy",
        "parameters", map("freeCancellationHoursAfterStart", 1, "lateCancellationChargePercent", 0,
            "closedOrderStatuses", List.of("REJECTED")),
        "bindings", map("amount", "/amountMinor", "decision", "/commercialDecision", "windowStart", "/clockStart",
            "orderStatus", "/orderDecision/status", "confirmation", "/activation/approved/seller",
            "accept", map("withdrawOrder", map("on", "workflow", "party", "customer", "input", true,
                "requireExactDocumentVersion", true))));
    var source = map("name", "Seller Order with composed closing decision", "type", "Orders/Order with Seller Decision",
        "amountMinor", 7200, "price", 100, "clockStart", 1,
        "clauses", map("activation", activation, "cancellation", cancellation, "reconciliation", reconciliation),
        "contracts", map(
            "seller", channel("seller"),
            "orderOpen", map("constants", map("closedStates", map("withdrawal",
                map("path", "/commercialDecision/status", "equals", "accepted", "reason", "COMMERCIALLY_CLOSED")))),
            "proposeAndActivate", map("type", "Contracts/Sequential Workflow Operation", "channel", "seller",
                "steps", List.of(map("type", "Contracts/Compute", "do",
                    List.of(map("$appendChange", map("op", "add", "path", "/customReview", "val", true)))))),
            "audit/receipt~reconcile", map("type", "Contracts/Sequential Workflow Operation", "channel", "seller",
                "steps", List.of(map("type", "Contracts/Compute", "constants", map("approvalRole", "seller"),
                    "do", List.of(map("$appendEvent", settlementEvent)))))));
    var open = initialized(processor, source);
    var termsRef = processor.read(open, "/activation/terms/ref");
    var selection = map("revision", processor.read(open, "/activation/revision"), "termsRef", termsRef);
    var termsOnly = map("type", "Activation/Terms Selection Input", "termsRef", termsRef);
    var proposal = map("type", "Activation/Terms Proposal Input", "proposalId", "revised-price",
        "baseTermsRef", termsRef,
        "changes", map("type", "List", "itemType", "Activation/Term Change", "items",
            List.of(map("type", "Activation/Term Change", "path", "/price", "replacement", 120))));
    var approved = process(processor, open, event(open, "seller", "approve_seller", selection, true), 1);
    equal(true, processor.read(approved.document(), "/activation/active"), "Seller approval can accept the open Order");
    var cancellationInput = map("key", "withdraw-1", "reason", "Plans changed");
    var cancelled = process(processor, open, event(open, "customer", "withdrawOrder", cancellationInput, true), 1);
    var closed = cancelled.document();
    equal("accepted", processor.read(closed, "/commercialDecision/status"), "Alternative cancellation destination records the decision");
    var restored = processor.importSnapshot(processor.exportSnapshot(closed), closed.identity());
    guardDenied(processor, restored, "seller", "rejectOrder", map("revision", 1), 2, "COMMERCIALLY_CLOSED");
    guardDenied(processor, restored, "seller", "approve_seller", selection, 2, "COMMERCIALLY_CLOSED");
    guardDenied(processor, restored, "seller", "proposeAndActivate_seller", proposal, 2, "COMMERCIALLY_CLOSED");
    var afterBuyerApproval = process(processor, restored, event(restored, "buyer", "approve_buyer", selection, true), 2).document();
    equal(true, processor.read(afterBuyerApproval, "/activation/approved/buyer"), "The configured closure selects seller approval only");
    equal(false, processor.read(afterBuyerApproval, "/activation/active"), "An unrelated approval does not accept the closed Order");

    guardDenied(processor, restored, "seller", "activate_seller", termsOnly, 2, "COMMERCIALLY_CLOSED");
    var withdrawal = process(processor, restored, event(restored, "seller", "withdrawAcceptance_seller", termsOnly, true), 2);
    equal(false, WireData.write(withdrawal.observations()).contains("\"reason\":\"COMMERCIALLY_CLOSED\""),
        "Withdrawal of acceptance still reaches Activation");
    var withdrawn = withdrawal.document();
    var settled = process(processor, withdrawn, event(withdrawn, "seller", "audit/receipt~reconcile", map(), true), 3).document();
    equal(true, processor.read(settled, "/reconciled"), "Unrelated operation and triggered reconciliation still run on the closed Order");
    var replay = process(processor, settled, event(settled, "customer", "withdrawOrder", cancellationInput, true), 4);
    equal(processor.read(closed, "/commercialDecision"), processor.read(replay.document(), "/commercialDecision"),
        "Exact retry preserves the closure");
    equal(List.of(), processor.emitted(replay), "Cancellation retry emits no duplicate financial trigger");

    var rejected = process(processor, open, event(open, "seller", "rejectOrder", map("revision", 1), true), 1).document();
    guardDenied(processor, rejected, "seller", "proposeAndActivate_seller", proposal, 2, "ORDER_REJECTED");
    var custom = process(processor, rejected, event(rejected, "seller", "proposeAndActivate", map(), true), 2).document();
    equal(true, processor.read(custom, "/customReview"), "An unrelated operation's legacy-looking name confers no approval role");
    var afterRejection = process(processor, custom, event(custom, "seller", "audit/receipt~reconcile", map(), true), 3).document();
    equal(true, processor.read(afterRejection, "/reconciled"), "Rejection preserves reconciliation too");
    failure(processor, afterRejection, event(afterRejection, "customer", "withdrawOrder", cancellationInput, true),
        4, "ORDER_CLOSED");
    System.out.println("PASS configured terminal selector, restored Order, exact accepting operations, withdrawal and reconciliation");
  }

  private static void guardDenied(Contracts processor, Contracts.Document before, String actor, String operation,
      Object request, long timestamp, String reason) {
    var result = process(processor, before, event(before, actor, operation, request, true), timestamp);
    var evidence = WireData.write(result.observations());
    equal(true, evidence.contains("\"reason\":\"" + reason + "\""), "Native dispatch denies " + operation + " with " + reason);
    equal(List.of(), processor.emitted(result), "Denied " + operation + " emits no effects");
    for (String path : List.of("/activation", "/orderDecision", "/commercialDecision")) {
      equal(processor.read(before, path), processor.read(result.document(), path), "Denied " + operation + " preserves " + path);
    }
  }

  private static void capture(Contracts processor) {
    var execution = processor.execution();
    var values = execution.values();
    var profile = map("type", "Payment/Selected Order Capture", "mode", "when", "requestId", REQUEST_ID);
    var processClause = map("type", "Payment/Payment Process Clause",
        "parameters", map("method", "myos-customer", "sources", map("order", map()), "capture", profile));
    var instruction = initialized(processor, map("name", "Conditional instruction",
        "type", "PaymentInstruction/Payment Instruction with Clauses",
        "contracts", map("guarantor", channel("guarantor")),
        "paymentTerms", map("amountMinor", 7200, "limitMinor", 7200, "currency", "USD", "payerChannel", "customer",
            "payeeChannel", "seller", "guarantorChannel", "guarantor", "allowedPayees", List.of("seller"),
            "recipientApprovalRequired", false),
        "clauses", map("activation", activation(List.of(), List.of()), "payment", processClause)));
    equal("/paymentProcess_payment/captureAllowed", processor.read(instruction, "/paymentTerms/captureGate"),
        "Named capture policy installs native instruction gate");
    equal(false, processor.read(instruction, "/paymentProcess_payment/captureAllowed"),
        "Gate is closed before source selection");
    equal(true, processor.read(instruction, "/contracts/paymentSourcesHandler") != blue.bex.Values.UNDEFINED,
        "Named policy is re-evaluated for source deliveries");

    // Read the predicate as published and exercise all sides of its financial admission boundary.
    var published = values.source(map("type", "Payment/Selected Order Capture"), "definition");
    var predicate = values.source(map("expr", values.bexData(values.select(published, "/when"))));
    captureProjections(processor, predicate);
    System.out.println("PASS named capture gate, selected PI identity, requirement, order review, amount, currency and access");
  }

  private static void captureProjections(Contracts processor, Exact predicate) {
    var values = processor.execution().values();
    var orderIdentity = map("fixture", "Original order");
    var instructionIdentity = map("fixture", "Original payment instruction");
    String instructionId = NativeRuntime.identity(values.source(instructionIdentity));
    var requirement = map("fixture", "Prepared payment requirement");
    var selected = map("candidateOrigin", instructionId, "documentOrigin", instructionId,
        "requirementRef", NativeRuntime.identity(values.source(requirement)), "prepared", requirement);
    var activation = map("active", true, "accessReady", true, "revision", 1, "terms", map("ref", "terms-1"));
    var orderDecision = map("status", "PENDING");
    var linkedInstruction = map("document", instructionIdentity);
    var paymentKey = NativeRuntime.identity(values.source("single"));
    var order = map("contracts", map("initialized", map("document", orderIdentity)), "activation", activation,
        "orderDecision", orderDecision, "amountMinor", 7200, "currency", "USD",
        "process_payment", map("entries", map(paymentKey, selected)),
        "payment", map("contracts", map("initialized", linkedInstruction)));
    var businessContext = map("orderOrigin", orderIdentity, "orderRevision", 1, "orderTermsRef", "terms-1");
    var subject = map("sources", map("order", order), "contracts", map("initialized", map("document", instructionIdentity)),
        "businessContext", businessContext, "paymentTerms", map("amountMinor", 7200, "currency", "USD"));
    var probe = new CaptureProbe(processor, predicate, subject);
    probe.expect(true);
    probe.when(selected, "candidateOrigin", "other-id", false);
    probe.when(selected, "documentOrigin", "other-id", false);
    probe.when(selected, "requirementRef", "other-id", false);
    probe.when(linkedInstruction, "document", map("fixture", "Foreign PI"), false);
    probe.when(activation, "active", false, false);
    probe.when(activation, "accessReady", false, false);
    probe.when(activation, "revision", 2, false);
    probe.when(activation, "terms", map("ref", "terms-2"), false);
    probe.when(businessContext, "orderOrigin", map("fixture", "Foreign order"), false);
    probe.when(order, "amountMinor", 7199, false);
    probe.when(order, "currency", "EUR", false);
    probe.when(orderDecision, "status", "REJECTED", false);
    // Commercial clauses can contribute their own predicate. The stock PI
    // selection does not interpret this fixture's reservation or decision.
    order.put("wholeOrderReservation", map("id", "unscoped", "status", "pending_supplier"));
    order.put("cancellationDecision", map("status", "accepted"));
    probe.expect(true);
  }

  private record CaptureProbe(Contracts processor, Exact predicate, Map<String, Object> subject) {
    void expect(boolean expected) {
      var execution = processor.execution();
      var values = execution.values();
      var result = execution.evaluatePredicate(values.source(subject), values.source(map()),
          "input", predicate, 10_000_000);
      equal(expected, result.value(), "Published capture policy");
    }

    void when(Map<String, Object> fields, String field, Object value, boolean expected) {
      Object prior = fields.put(field, value);
      try {
        expect(expected);
      } catch (AssertionError failure) {
        throw new AssertionError("Capture policy with " + field + " = " + value, failure);
      } finally {
        fields.put(field, prior);
      }
    }
  }

  private static Map<String, Object> activation(List<String> required, List<String> preOperations) {
    var parties = map();
    for (String role : List.of("seller", "customer", "guarantor", "buyer")) {
      parties.put(role, map("type", "Parties/Party", "lead", map("channel", channel(role)),
          "myosAccountId", role + "-account", "readerKeys", List.of("reader-" + role)));
    }
    return map("type", "Activation/Activation Clause", "parameters",
        map("parties", parties, "required", required, "preActivationOperations", preOperations));
  }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> parameters(Map<String, Object> clause) {
    return (Map<String, Object>) clause.get("parameters");
  }

  private static Object channel(String role) {
    return map("type", "Contracts/External Channel", "event", map("source", role));
  }

  private static boolean isRejection(Object value) {
    return value instanceof Map<?, ?> event && "Order rejected".equals(event.get("name"));
  }

  private static Contracts.Document initialized(Contracts processor, Object source) {
    var result = processor.initialize(source);
    if (!result.commits()) {
      try {
        ClauseGasProbe.diagnose(processor, source);
      } catch (ContractException failure) {
        throw new AssertionError(failure.code() + " " + failure.context(), failure);
      }
    }
    equal("APPLIED", result.status(), OperationInputConformance.initializationDiagnostic(processor, result));
    return result.document();
  }

  private static Contracts.Result process(
      Contracts processor, Contracts.Document document, Object event, long timestamp) {
    var result = processor.process(document, event, timestamp);
    if (!result.commits()) ClauseGasProbe.diagnose(processor, document, event, timestamp);
    equal("APPLIED", result.status(), "Processing " + event);
    return result;
  }

  private static void failure(
      Contracts processor, Contracts.Document document, Object event, long timestamp, String expected) {
    noRejection(processor, document, event, timestamp);
    try {
      ClauseGasProbe.diagnose(processor, document, event, timestamp);
      throw new AssertionError("Expected " + expected);
    } catch (BexError error) {
      equal(expected, error.getMessage(), "Rejection failure");
    }
  }

  private static void noRejection(
      Contracts processor, Contracts.Document document, Object event, long timestamp) {
    var result = processor.process(document, event, timestamp);
    equal(List.of(), processor.emitted(result), "Denied rejection emits no event");
    if (result.commits()) {
      equal("PENDING", processor.read(result.document(), "/orderDecision/status"), "Denied rejection preserves status");
    }
  }

  private static Object event(Contracts.Document version, String actor, String operation, Object request, boolean exact) {
    return map("source", actor, "operation", map("type", "Contracts/Operation Request",
        "channel", actor, "operation", operation, "request", request,
        "document", map("blueId", version.blueId()), "requireExactDocumentVersion", exact));
  }

  private static Map<String, Object> map(Object... pairs) {
    return OperationInputConformance.m(pairs);
  }

  private static void equal(Object expected, Object actual, String message) {
    if (!Objects.equals(expected, actual)) {
      throw new AssertionError(message + ": expected " + expected + ", got " + actual);
    }
  }
}
