import static blue.core.CompositionPackages.obj;

import blue.bex.Bex;
import blue.bex.BexContext;
import blue.bex.BexError;
import blue.bex.BexProfile;
import blue.bex.Engine;
import blue.bex.Values;
import blue.contracts.Contracts;
import blue.core.CompositionPackages;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/** Exact published BEX functions with modeled native Order and provider observations. */
public final class UnifiedCancellationConformance {
  private static final long HOUR = 3_600_000_000L;
  private static final String SLOT = "BEBjgocEv82EQ16WxjrHRs9oVwDMzxS89tzEuJdLwqDY";
  private static final String GROUP = "whole-order";
  private static final String RESERVATION = "Schedule/Reservation Functions";
  private static final String SETTLEMENT = "Payment/Reservation Settlement Functions";

  private final blue.contracts.ContractsExecution.Values values;

  private UnifiedCancellationConformance(Contracts runtime) {
    values = runtime.execution().values();
  }

  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]).toAbsolutePath().normalize();
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var blue = packages.language()) {
      var probe = new UnifiedCancellationConformance(new Contracts(blue, QualificationRuntime.bindings()));
      probe.deadlines();
      probe.sellerClock();
      probe.automaticClock();
      probe.reviewedSellerGrant();
      probe.cancellationAdmission();
      probe.settlement();
    }
  }

  private void deadlines() {
    var order = map("payment", map("authorizationTiming", map("authorizedAtMicros", HOUR)));
    var timing = map("clock", "order_activation", "activatedAtMicros", 2 * HOUR,
        "policy", map("freeCancellationHoursAfterActivation", 3, "freeCancellationHoursBeforeStart", 2));
    var group = map("status", "confirmed", "confirmedStartMicros", 6 * HOUR);
    var policy = map("freeCancellationHoursBeforeStart", 2, "lateCancellationChargePercent", 20);
    var input = map("timing", timing, "policy", policy, "group", group, "dateRequired", true, "startedAt", 2 * HOUR, "authorizationPending", false);
    equal(false, run(RESERVATION, "outsideExplicitWindow", input, order, 4 * HOUR).value(), "Service cutoff inclusive");
    equal(true, run(RESERVATION, "outsideExplicitWindow", input, order, 4 * HOUR + 1).value(), "Earlier service cutoff applies");
    group.put("confirmedStartMicros", 9 * HOUR);
    equal(false, run(RESERVATION, "outsideExplicitWindow", input, order, 5 * HOUR).value(), "Elapsed cutoff inclusive");
    equal(true, run(RESERVATION, "outsideExplicitWindow", input, order, 5 * HOUR + 1).value(), "Earlier elapsed cutoff applies");
    rejected(RESERVATION, "outsideExplicitWindow", input, order, 9 * HOUR + 1, "ORDINARY_CANCELLATION_AFTER_START");
    var noSpecialBehavior = map("parameters", map());
    var elapsed = map("timing", timing, "policy", policy, "group", group, "dateRequired", true,
        "confirmed", true, "now", 5 * HOUR);
    var evidence = obj(run(RESERVATION, "evaluateCustomerCancellation", elapsed, order, 5 * HOUR, noSpecialBehavior).value());
    amount(2 * HOUR, obj(evidence.get("evidence")).get("orderActivatedAtMicros"),
        "An older instruction authorization cannot move the real Order start");
    timing.remove("activatedAtMicros");
    try {
      run(RESERVATION, "evaluateCustomerCancellation", elapsed, order, 5 * HOUR, noSpecialBehavior);
      throw new AssertionError("Without a real Order activation the elapsed deadline is unproven");
    } catch (BexError failure) {
      equal("CANCELLATION_WINDOW_START_REQUIRED", failure.getMessage(), "The payment clock cannot fill an absent Order clock");
    }
    var serviceOnly = map("policy", map("freeCancellationHoursBeforeStart", 2));
    var serviceInput = map("timing", serviceOnly, "policy", policy, "group", group, "dateRequired", true,
        "confirmed", true, "now", 7 * HOUR);
    var atCutoff = obj(run(RESERVATION, "evaluateCustomerCancellation", serviceInput, order, 7 * HOUR,
        noSpecialBehavior).value());
    equal(false, atCutoff.get("chargeApplies"), "A service-only rule requires no elapsed anchor");
    require(!obj(atCutoff.get("evidence")).containsKey("orderActivatedAtMicros"),
        "Service-only decision does not manufacture an activation time");
    var oneAfter = obj(run(RESERVATION, "evaluateCustomerCancellation", serviceInput, order, 7 * HOUR + 1,
        noSpecialBehavior).value());
    equal(true, oneAfter.get("chargeApplies"), "Service-only deadline applies one instant after the cutoff");
    System.out.println("PASS genuine Order clock, absence despite older PI authorization, inclusive deadlines and service-only cutoff");
  }

  private void sellerClock() {
    var timing = map("clock", "order_activation",
        "policy", map("freeCancellationHoursAfterActivation", 2, "freeCancellationHoursBeforeStart", 1));
    var activation = map("active", false, "approved", map("seller", false));
    var order = map("activation", activation, "cancellationTiming", timing,
        "payment", map("authorizationTiming", map("authorizedAtMicros", HOUR)));
    var constants = map("parameters", map("sellerConfirmationRequired", true),
        "bindings", map("timing", "/cancellationTiming"));
    var group = map("status", "pending_supplier");
    var policy = map("freeCancellationHoursBeforeStart", 1, "lateCancellationChargePercent", 20);
    var input = map("timing", timing, "policy", policy, "group", group, "dateRequired", true,
        "confirmed", false, "now", 4 * HOUR);
    var before = obj(run(RESERVATION, "evaluateCustomerCancellation", input, order, 4 * HOUR, constants).value());
    equal(false, before.get("chargeApplies"), "Seller wait beyond the authorization deadline cannot incur a fee");
    equal(true, obj(before.get("evidence")).get("beforeSellerConfirmation"), "Explicit pre-confirmation decision evidence");
    require(!obj(before.get("evidence")).containsKey("orderActivatedAtMicros"), "No synthetic activation clock");
    equal(List.of(), run(RESERVATION, "rememberCancellationActivation", map(), order, 4 * HOUR, constants).changeset(),
        "Unapproved Order cannot start the clock");

    activation.put("active", true);
    obj(activation.get("approved")).put("seller", true);
    var first = run(RESERVATION, "rememberCancellationActivation", map(), order, 6 * HOUR, constants);
    amount(6 * HOUR, change(first, "/cancellationTiming/activatedAtMicros"), "Native seller activation starts the grace period");
    timing.put("activatedAtMicros", 6 * HOUR);
    group.put("status", "confirmed");
    group.put("confirmedStartMicros", 10 * HOUR);
    input.put("confirmed", true);
    input.put("now", 8 * HOUR);
    var at = obj(run(RESERVATION, "evaluateCustomerCancellation", input, order, 8 * HOUR, constants).value());
    equal(false, at.get("chargeApplies"), "Seller confirmation followed by grace includes exact boundary");
    amount(6 * HOUR, obj(at.get("evidence")).get("orderActivatedAtMicros"), "Decision records the chosen immutable clock");
    input.put("now", 8 * HOUR + 1);
    var after = obj(run(RESERVATION, "evaluateCustomerCancellation", input, order, 8 * HOUR + 1, constants).value());
    equal(true, after.get("chargeApplies"), "One instant after the chosen boundary is late");
    equal(List.of(), run(RESERVATION, "rememberCancellationActivation", map(), order, 9 * HOUR, constants).changeset(),
        "Later observations cannot reset the first confirmation clock");
    System.out.println("PASS free cancellation before seller confirmation, first native activation anchor and inclusive grace");
  }

  private void automaticClock() {
    var timing = map("initializedWithoutTimestamp", true, "policy", map("freeCancellationHoursAfterActivation", 2));
    var group = map("status", "confirmed");
    var policy = map("freeCancellationHoursBeforeStart", 0, "lateCancellationChargePercent", 20);
    var parameters = map("parameters", map(), "bindings", map("authorizationTimingFallback", "/payment/authorizationTiming"));
    var args = map("timing", timing, "policy", policy, "group", group, "dateRequired", false, "confirmed", true, "now", 3 * HOUR);
    var orderOrigin = map("name", "Auto Order initialized without time");
    var instructionOrigin = map("name", "Retained exact original payment");
    var entry = selected(instructionOrigin);
    var requests = map();
    var payment = map("contracts", map("initialized", map("document", instructionOrigin)),
        "businessContext", map("orderOrigin", orderOrigin), "paymentTerms", map("amountMinor", 1000, "currency", "USD"),
        "payment", map("completed", 0, "secured", 0, "requests", requests));
    var activation = map("active", true, "everActivated", true, "accessReady", true, "required", List.of());
    var order = map("activation", activation, "amountMinor", 1000, "currency", "USD",
        "contracts", map("initialized", map("document", orderOrigin)),
        "orderSnapshot", map("terms", map("confirmationMode", "automatic")));
    var beforeSelection = clockDecision(args, order, 3 * HOUR, parameters);
    equal(false, beforeSelection.get("chargeApplies"), "Automatic checkout is free to cancel without an attached PI");
    equal(true, obj(beforeSelection.get("evidence")).get("paymentAuthorizationPending"), "No elapsed charge starts before PI");
    obj(timing.get("policy")).put("freeCancellationHoursBeforeStart", 1);
    policy.put("freeCancellationHoursBeforeStart", 1);
    group.put("confirmedStartMicros", 4 * HOUR);
    args.put("dateRequired", true);
    equal(false, clockDecision(args, order, 3 * HOUR, parameters).get("chargeApplies"),
        "The independent service cutoff stays inclusive while authorization is pending");
    equal(true, clockDecision(args, order, 3 * HOUR + 1, parameters).get("chargeApplies"),
        "Pending authorization cannot disable the independent service cutoff");
    obj(timing.get("policy")).remove("freeCancellationHoursBeforeStart");
    policy.put("freeCancellationHoursBeforeStart", 0);
    group.remove("confirmedStartMicros");
    args.put("dateRequired", false);

    order.put("process_payment", map("entries", map(SLOT, entry)));
    order.put("payment", payment);
    var beforeSecure = clockDecision(args, order, 3 * HOUR, parameters);
    equal(false, beforeSecure.get("chargeApplies"), "Selected PI with no full SECURE remains free");
    requests.put("partial", map("status", "succeeded", "response", map("outcome", "succeeded"),
        "intent", map("action", "secure", "amountMinor", 500)));
    equal(true, obj(clockDecision(args, order, 3 * HOUR, parameters).get("evidence")).get("paymentAuthorizationPending"),
        "Partial authorization does not start grace");
    requests.put("full", map("status", "succeeded", "response", map("outcome", "succeeded"),
        "intent", map("action", "secure", "amountMinor", 1000)));
    clockRejected(args, order, 3 * HOUR, parameters, "CANCELLATION_WINDOW_START_REQUIRED");
    payment.put("authorizationTiming", map("authorizedAtMicros", HOUR, "requestId", "full"));
    var attachedBeforeSecure = clockDecision(args, order, 3 * HOUR, parameters);
    equal(false, attachedBeforeSecure.get("chargeApplies"), "Automatic elapsed deadline includes the exact boundary");
    var evidence = obj(attachedBeforeSecure.get("evidence"));
    amount(HOUR, evidence.get("paymentAuthorizedAtMicros"), "Use actual native SECURE signed time");
    require(!evidence.containsKey("orderActivatedAtMicros"), "Authorization does not impersonate Order activation");

    // Reattach the same settled instruction with its already-persisted authorization stamp.
    order.remove("payment");
    order.remove("process_payment");
    order.put("process_payment", map("entries", map(SLOT, entry)));
    order.put("payment", payment);
    obj(payment.get("payment")).put("completed", 1000);
    equal(true, clockDecision(args, order, 3 * HOUR + 1, parameters).get("chargeApplies"),
        "Exact original authorized before attachment retains clock after capture and zero held balance");
    payment.put("authorizationTiming", map("authorizedAtMicros", HOUR, "requestId", "partial"));
    clockRejected(args, order, 3 * HOUR, parameters, "CANCELLATION_WINDOW_START_REQUIRED");
    payment.put("authorizationTiming", map("authorizedAtMicros", HOUR, "requestId", 5));
    clockRejected(args, order, 3 * HOUR, parameters, "CANCELLATION_WINDOW_START_REQUIRED");
    payment.put("authorizationTiming", map("authorizedAtMicros", HOUR, "requestId", "full"));
    clockRejected(args, order, 3 * HOUR, map("parameters", map()), "CANCELLATION_WINDOW_START_REQUIRED");
    entry.put("documentOrigin", id(map("name", "Foreign selected instruction")));
    clockRejected(args, order, 3 * HOUR, parameters, "SELECTED_PAYMENT_AUTHORIZATION_REQUIRED");
    entry.put("documentOrigin", id(instructionOrigin));
    activation.put("active", false);
    clockRejected(args, order, 3 * HOUR, parameters, "CANCELLATION_WINDOW_START_REQUIRED");
    activation.put("active", true);
    timing.put("activatedAtMicros", 2 * HOUR);
    var signed = clockDecision(args, order, 3 * HOUR + 1, parameters);
    equal(false, signed.get("chargeApplies"), "Genuine activation prevails over preserved secure timestamp");
    amount(2 * HOUR, obj(signed.get("evidence")).get("orderActivatedAtMicros"), "Genuine activation remains primary");
    System.out.println("PASS auto grace before SECURE, both attachment orders, capture, source integrity and inclusive boundary");
  }

  private Map<String, Object> clockDecision(Map<String, Object> args, Map<String, Object> order,
      long time, Map<String, Object> parameters) {
    return obj(run(RESERVATION, "evaluateCustomerCancellation", args, order, time, parameters).value());
  }

  private void clockRejected(Map<String, Object> args, Map<String, Object> order,
      long time, Map<String, Object> parameters, String code) {
    try {
      clockDecision(args, order, time, parameters);
      throw new AssertionError("Expected cancellation clock rejection " + code);
    } catch (BexError error) {
      equal(code, error.getMessage(), "Expected domain error for unverified cancellation clock");
    }
  }

  private void reviewedSellerGrant() {
    var orderOrigin = map("name", "Reviewed scheduled Order");
    var instructionOrigin = map("name", "Selected secured instruction");
    var proposal = map("amountMinor", 1000, "proposedStartMicros", 12 * HOUR);
    var group = map("proposalBlueId", id(proposal), "proposal", proposal);
    var context = map("orderOrigin", orderOrigin, "orderRevision", 2, "orderTermsRef", "terms-2");
    var order = map("contracts", map("initialized", map("document", orderOrigin)), "amountMinor", 1000, "currency", "USD",
        "activation", map("accessReady", true, "revision", 2, "terms", map("ref", "terms-2"),
            "parties", map("seller", map("myosAccountId", "seller-account"))),
        "orderSnapshot", map("groups", List.of(map("id", GROUP))),
        "process_payment", map("entries", map(SLOT, selected(instructionOrigin))),
        "payment", map("contracts", map("initialized", map("document", instructionOrigin)), "businessContext", context,
            "paymentTerms", map("amountMinor", 1000, "currency", "USD"),
            "payment", map("accepted", true, "closed", false, "cancellationPending", false, "secured", 1000,
                "reserved", map("secure", 0, "capture", 0, "void", 0))));
    var exactSeller = map("channel", "seller", "requireExactDocumentVersion", true);
    var exactCustomer = map("channel", "customer", "requireExactDocumentVersion", true);
    var constants = map("parameters", map("reviewedSellerActivation", true));
    var arguments = map("input", map("groupId", GROUP), "action", "confirm", "group", group);
    equal(true, run(RESERVATION, "requireReviewedSellerDecision", arguments, order, 6 * HOUR, constants, exactSeller).value(),
        "Exact seller may confirm the original fully secured booking");
    deniedReview(arguments, order, constants, exactCustomer);
    deniedReview(arguments, order, constants, map("channel", "seller", "requireExactDocumentVersion", false));
    context.put("orderRevision", 1);
    deniedReview(arguments, order, constants, exactSeller);
    context.put("orderRevision", 2);
    context.put("orderTermsRef", "different-terms");
    deniedReview(arguments, order, constants, exactSeller);
    context.put("orderTermsRef", "terms-2");
    order.put("datedSellerGrant", run(RESERVATION, "reviewedSellerScope", map("group", group), order, 6 * HOUR).value());
    arguments.put("action", "accept");
    equal(true, run(RESERVATION, "requireReviewedSellerDecision", arguments, order, 7 * HOUR, constants, exactCustomer).value(),
        "Exact customer can accept the identical seller alternative");
    proposal.put("proposedStartMicros", 13 * HOUR);
    group.put("proposalBlueId", id(proposal));
    deniedReview(arguments, order, constants, exactCustomer);
    System.out.println("PASS exact dated seller and customer grant scope, actor, version, terms and proposed start");
  }

  private void deniedReview(Map<String, Object> args, Map<String, Object> order,
      Map<String, Object> constants, Map<String, Object> caller) {
    try {
      run(RESERVATION, "requireReviewedSellerDecision", args, order, 7 * HOUR, constants, caller);
      throw new AssertionError("A stale or unrelated booking review must not activate the Order");
    } catch (BexError error) {
      equal("ORDER_RESERVATION_REVIEW_CHANGED", error.getMessage(), "Reviewed scope rejected");
    }
  }

  private void cancellationAdmission() {
    var orderOrigin = map("name", "Cancellation admission Order");
    var instructionOrigin = map("name", "Cancellation admission payment");
    var proposal = map("amountMinor", 1000, "currency", "USD");
    var group = map("status", "pending_supplier", "proposalBlueId", id(proposal), "proposal", proposal);
    var timing = map("clock", "order_activation", "policy", map("freeCancellationHoursAfterActivation", 2));
    var terms = map("dateRequired", false, "cancellationPolicy",
        map("freeCancellationHoursBeforeStart", 0, "lateCancellationChargePercent", 20));
    var payment = map("completed", 0, "secured", 1000, "requests", map());
    var order = map("amountMinor", 1000, "contracts", map("initialized", map("document", orderOrigin)),
        "process_payment", map("entries", map(SLOT, selected(instructionOrigin))),
        "payment", map("contracts", map("initialized", map("document", instructionOrigin)),
            "businessContext", map("orderOrigin", orderOrigin), "authorizationTiming", map("authorizedAtMicros", HOUR),
            "payment", payment),
        "cancellationTiming", timing, "reservations", map(GROUP, group), "reservationRequests", map(),
        "orderSnapshot", map("terms", terms, "quote", map("currency", "USD"),
            "groups", List.of(map("id", GROUP, "lineIndices", List.of(0)))));
    var request = map("key", "cancel", "groupId", GROUP, "expectedProposalBlueId", id(proposal), "reason", "Customer canceled");
    var arguments = map("input", request, "action", "cancel");
    var constants = map("clauseKey", "reservation", "parameters",
        map("sellerConfirmationRequired", true, "cancellationRequiresCapture", true),
        "bindings", map("timing", "/cancellationTiming", "snapshot", "/orderSnapshot",
            "state", "/reservations", "requests", "/reservationRequests"));

    var free = run(RESERVATION, "endReservation", arguments, order, 4 * HOUR, constants);
    var pendingDecision = obj(obj(change(free, "/reservations/" + GROUP)).get("decision"));
    amount(0, pendingDecision.get("chargeMinor"), "The actual pre-confirmation decision charges zero on the held card");
    equal(true, pendingDecision.get("beforeSellerConfirmation"), "The decision records why elapsed time did not apply");

    timing.put("activatedAtMicros", 6 * HOUR);
    obj(timing.get("policy")).put("freeCancellationHoursAfterActivation", 0);
    group.put("status", "confirmed");
    group.put("confirmedStartMicros", 12 * HOUR);
    try {
      run(RESERVATION, "endReservation", arguments, order, 6 * HOUR + 1, constants);
      throw new AssertionError("A positive fee must wait for the already authorized ordinary capture");
    } catch (BexError error) {
      equal("CANCELLATION_AWAITING_CAPTURE", error.getMessage(), "No irreversible decision on the held-only Order");
    }
    payment.put("requests", map("order-accepted-capture", map("status", "pending",
        "intent", map("action", "capture", "amountMinor", 1000))));
    try {
      run(RESERVATION, "endReservation", arguments, order, 6 * HOUR + 2, constants);
      throw new AssertionError("A request does not establish captured money");
    } catch (BexError error) {
      equal("CANCELLATION_AWAITING_CAPTURE", error.getMessage(), "Pending capture leaves ordinary capture eligible");
    }
    require(!group.containsKey("decisionBlueId"), "Deferral preserves the live group and its original proposal");
    payment.put("completed", 1000);
    var accepted = run(RESERVATION, "endReservation", arguments, order, 6 * HOUR + 3, constants);
    var cancelled = obj(change(accepted, "/reservations/" + GROUP));
    var decision = obj(cancelled.get("decision"));
    amount(200, decision.get("chargeMinor"), "Retry after full capture freezes the exact fee");
    amount(6 * HOUR, decision.get("orderActivatedAtMicros"), "The accepted decision records the original seller clock");
    obj(order.get("reservations")).put(GROUP, cancelled);
    obj(order.get("reservationRequests")).put("cancel", change(accepted, "/reservationRequests/cancel"));
    equal(List.of(), run(RESERVATION, "endReservation", arguments, order, 6 * HOUR + 4, constants).changeset(),
        "Cancellation replay preserves the already accepted decision");
    System.out.println("PASS stale hold does not charge before seller review, late decision defers to confirmed capture and then replays");
  }

  private void settlement() {
    var orderOrigin = map("name", "Reviewed order");
    var instructionOrigin = map("name", "Exact payment");
    var proposal = map("amountMinor", 1000);
    var quote = map("currency", "USD", "totalMinor", 1000);
    var decision = map("groupId", GROUP, "proposalBlueId", id(proposal), "currency", "USD",
        "basisMinor", 1000, "chargeMinor", 0, "releasedMinor", 1000);
    var group = map("status", "cancelled", "originalLineIndices", List.of(0), "proposalBlueId", id(proposal),
        "proposal", proposal, "decision", decision, "decisionBlueId", id(decision));
    var entry = selected(instructionOrigin);
    entry.put("status", "selected");
    var order = map("contracts", map("initialized", map("document", orderOrigin)),
        "process_payment", map("entries", map(SLOT, entry)), "activation", map("active", false),
        "payment", map("contracts", map("initialized", map("document", instructionOrigin))),
        "reservations", map(GROUP, group), "orderSnapshot", map("quote", quote, "quoteBlueId", id(quote),
            "terms", map("cancellationPolicy", map("lateCancellationChargePercent", 20)),
            "groups", List.of(map("id", GROUP, "lineIndices", List.of(0)))));
    var terms = map("amountMinor", 1000, "limitMinor", 1000, "currency", "USD",
        "captureGate", "/fixtureCaptureAllowed", "guarantorChannel", "guarantor", "payerChannel", "buyer",
        "payeeChannel", "seller", "recipientApprovalRequired", false);
    var payment = map("accepted", true, "transactionId", "tx", "closed", false,
        "reserved", map("capture", 0, "refund", 0, "void", 0, "secure", 0),
        "completed", 0, "reversed", 0, "secured", 1000, "targetMinor", 1000,
        "locks", map(), "requests", map(), "controlRequests", map(), "payeeChannel", "seller");
    var instruction = map("contracts", map("initialized", map("document", instructionOrigin)),
        "businessContext", map("orderOrigin", orderOrigin), "sourceLinks", map("ready", false),
        "sources", map("order", order), "activation", map("active", true), "paymentTerms", terms,
        "payment", payment, "paymentDetails", map("method", "myos-customer"), "fixtureCaptureAllowed", false);
    var binding = map("clauseKey", "payment");
    entry.put("candidateOrigin", id(map("name", "Another PI")));
    equal(List.of(), run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 4 * HOUR, binding).changeset(),
        "An unready foreign instruction cannot release a hold");
    entry.put("candidateOrigin", id(instructionOrigin));
    var free = run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 4 * HOUR, binding);
    var freeState = obj(change(free, "/cancellationSettlement"));
    equal("requested", freeState.get("status"), "A selected Order waiting for seller confirmation can release the hold");
    equal("void", freeState.get("action"), "Free request action");
    amount(1000, freeState.get("requestedMinor"), "Whole authorized hold");
    amount(0, freeState.get("netPaidMinor"), "No capture was recorded");
    instruction.put("cancellationSettlement", freeState);
    var requestId = freeState.get("lastRequestId").toString();
    var nativeVoid = obj(change(free, "/payment/requests/" + requestId));
    equal("pending", nativeVoid.get("status"), "The void request is pending until the provider reports it");
    var outstanding = map("status", "pending", "intent", nativeVoid.get("intent"));
    payment.put("requests", map(requestId, outstanding));
    var repeated = run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 4 * HOUR + 1, binding);
    require(repeated.changeset().stream().noneMatch(event -> obj(event).get("path").toString().startsWith("/payment/requests/")),
        "Replay while the first void is pending cannot submit another financial operation");
    outstanding.put("status", "unknown");
    var unknown = obj(change(run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 4 * HOUR + 2, binding),
        "/cancellationSettlement"));
    equal("unknown", unknown.get("status"), "Unknown provider state remains explicit");
    equal(requestId, unknown.get("lastRequestId"), "Unknown outcome keeps the original native request identity");
    outstanding.put("status", "succeeded");
    payment.put("secured", 0);
    var freed = obj(change(run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 5 * HOUR, binding),
        "/cancellationSettlement"));
    equal("settled", freed.get("status"), "Confirmed release resolves free cancellation");
    amount(0, freed.get("netPaidMinor"), "A release does not create receipts");
    equal(requestId, freed.get("lastRequestId"), "A confirmed release remains bound to the native void request");

    var ordinaryCapture = map("status", "pending", "intent", map("action", "capture", "amountMinor", 1000));
    var captureRequests = map("order-accepted-capture", ordinaryCapture);
    payment.put("requests", captureRequests);
    payment.put("secured", 1000);
    instruction.remove("cancellationSettlement");
    obj(instruction.get("sourceLinks")).put("ready", true);
    obj(order.get("activation")).put("active", true);
    entry.put("status", "usable");
    var waitForCapture = run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 5 * HOUR + 1, binding);
    equal("waiting_payment", obj(change(waitForCapture, "/cancellationSettlement")).get("status"),
        "Free cancellation waits for a previously submitted ordinary capture");
    require(waitForCapture.changeset().stream().noneMatch(event -> obj(event).get("path").toString().startsWith("/payment/requests/")),
        "Do not request a conflicting void while ordinary capture is pending");
    ordinaryCapture.put("status", "succeeded");
    payment.put("completed", 1000);
    payment.put("secured", 0);
    var fullRefundRequested = run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 5 * HOUR + 2, binding);
    var fullRefund = obj(change(fullRefundRequested, "/cancellationSettlement"));
    equal("refund", fullRefund.get("action"), "Free cancellation refunds all of a confirmed overlapping capture");
    amount(1000, fullRefund.get("requestedMinor"), "Exact full amount");
    var refundRequestId = fullRefund.get("lastRequestId").toString();
    var recordedRequest = obj(change(fullRefundRequested, "/payment/requests/" + refundRequestId));
    equal("pending", recordedRequest.get("status"), "Settlement refers to the exact native provider request");
    captureRequests.put(refundRequestId, map("status", "succeeded", "intent", recordedRequest.get("intent")));
    payment.put("reversed", 1000);
    instruction.put("cancellationSettlement", fullRefund);
    var refunded = obj(change(run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 5 * HOUR + 3, binding),
        "/cancellationSettlement"));
    equal("settled", refunded.get("status"), "Confirmation settles the free cancellation");
    amount(0, refunded.get("netPaidMinor"), "Confirmed full refund leaves no proceeds");

    payment.putAll(map("completed", 0, "reversed", 0, "requests", map()));
    entry.put("status", "selected");
    obj(order.get("activation")).put("active", false);
    obj(instruction.get("sourceLinks")).put("ready", false);
    decision.put("chargeMinor", 200);
    decision.put("releasedMinor", 800);
    group.put("decisionBlueId", id(decision));
    payment.put("secured", 1000);
    instruction.remove("cancellationSettlement");
    var late = run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 6 * HOUR, binding);
    var blocked = obj(change(late, "/cancellationSettlement"));
    equal("blocked", blocked.get("status"), "Late pending hold cannot bypass the mandatory capture gate");
    amount(200, blocked.get("targetMinor"), "Cancellation decision preserves the authorized late fee");
    amount(0, blocked.get("netPaidMinor"), "Blocked fee records zero received");
    require(late.changeset().stream().noneMatch(event -> obj(event).get("path").toString().startsWith("/payment/requests/")),
        "No new payment request appears while gate is closed");

    instruction.put("fixtureCaptureAllowed", true);
    obj(instruction.get("sourceLinks")).put("ready", true);
    obj(order.get("activation")).put("active", true);
    entry.put("status", "usable");
    var staleGate = run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 6 * HOUR + 1, binding);
    var blockedCapture = obj(change(staleGate, "/cancellationSettlement"));
    equal("blocked", blockedCapture.get("status"), "The card rail cannot issue a partial fee capture through a stale gate");
    require(staleGate.changeset().stream().noneMatch(event -> obj(event).get("path").toString().startsWith("/payment/requests/")),
        "No fee capture on an authorization-only card");
    ordinaryCapture.put("status", "pending");
    payment.put("requests", map("order-accepted-capture", ordinaryCapture));
    var pending = obj(change(run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction,
        6 * HOUR + 2, binding), "/cancellationSettlement"));
    equal("waiting_payment", pending.get("status"), "Cancellation waits for the genuinely in-flight full capture");
    ordinaryCapture.put("status", "succeeded");
    payment.put("secured", 0);
    payment.put("completed", 1000);
    var refund = obj(change(run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 7 * HOUR, binding),
        "/cancellationSettlement"));
    equal("requested", refund.get("status"), "Captured payable Order requests an excess refund");
    equal("refund", refund.get("action"), "Late cancellation refund action");
    amount(800, refund.get("requestedMinor"), "Refund only the excess above the agreed charge");
    amount(1000, refund.get("netPaidMinor"), "A requested refund is not confirmed money");
    instruction.put("cancellationSettlement", refund);
    payment.put("reversed", 800);
    var settled = obj(change(run(SETTLEMENT, "reconcileCancellationPayment", map(), instruction, 8 * HOUR, binding),
        "/cancellationSettlement"));
    equal("settled", settled.get("status"), "The confirmed refund equals the approved target");
    amount(200, settled.get("netPaidMinor"), "Exactly the agreed fee remains received");
    equal(Map.of(GROUP, id(decision)), settled.get("decisionBlueIds"), "Whole-order decision identity");
    System.out.println("PASS pre-capture void, full refund after overlapping capture, blocked inactive fee and confirmed excess refund");
  }

  private Map<String, Object> selected(Object instruction) {
    var prepared = map("name", "Exact obligation");
    return map("status", "usable", "path", "/payment", "requestId", "single", "prepared", prepared,
        "candidateOrigin", id(instruction), "documentOrigin", id(instruction), "requirementRef", id(prepared));
  }

  private Engine.Result run(String type, String name, Object arguments, Object document, long time) {
    return run(type, name, arguments, document, time, map());
  }

  private Engine.Result run(String type, String name, Object arguments, Object document,
      long time, Map<String, Object> constants) {
    return run(type, name, arguments, document, time, constants, map("channel", "customer"));
  }

  private Engine.Result run(String type, String name, Object arguments, Object document,
      long time, Map<String, Object> constants, Map<String, Object> caller) {
    var definition = values.source(map("type", type), "definition");
    var functions = obj(values.bexData(values.select(definition, "/functions")));
    functions.replaceAll((key, body) -> body instanceof Map<?, ?> reference && reference.get("blueId") instanceof String id
        ? values.bexData(new Exact.Ref(id)) : body);
    var selection = map();
    selectFunctions(name, functions, selection);
    var authoredConstants = map("bindings", map());
    authoredConstants.putAll(constants);
    var program = map("do", List.of(map("$return", map("$call", map("function", name, "args", arguments)))),
        "constants", authoredConstants);
    var bex = new Bex(BexProfile.current());
    var context = new BexContext(document, map(), map(), Values.UNDEFINED, map(),
        map("timestamp", time, "call", caller), "/", null,
        (candidate, pattern) -> values.matches(values.source(candidate), values.source(pattern, "definition")),
        (node, gas) -> id(node));
    return bex.execute(bex.compile(program, map("functions", selection), null), context, 10_000_000);
  }

  private static void selectFunctions(String name, Map<String, Object> all, Map<String, Object> selected) {
    if (selected.containsKey(name)) return;
    var function = all.get(name);
    require(function != null, "Missing function " + name);
    selected.put(name, function);
    selectCalls(function, all, selected);
  }

  private static void selectCalls(Object node, Map<String, Object> all, Map<String, Object> selected) {
    if (node instanceof Map<?, ?> object) {
      if (object.get("$call") instanceof Map<?, ?> call && call.get("function") instanceof String target) {
        selectFunctions(target, all, selected);
      }
      object.values().forEach(child -> selectCalls(child, all, selected));
    } else if (node instanceof List<?> list) {
      list.forEach(child -> selectCalls(child, all, selected));
    }
  }

  private void rejected(String type, String function, Object arguments, Object document, long time, String code) {
    try {
      run(type, function, arguments, document, time);
    } catch (BexError failure) {
      equal(code, failure.getMessage(), "Required rejection");
      return;
    }
    throw new AssertionError("Missing rejection " + code);
  }

  private String id(Object value) {
    return NativeRuntime.identity(values.source(value));
  }

  private static Object change(Engine.Result result, String path) {
    return result.changeset().stream().map(CompositionPackages::obj).filter(row -> path.equals(row.get("path")))
        .map(row -> row.get("val")).findFirst().orElseThrow(() -> new AssertionError("No change at " + path + " " + result));
  }

  private static Map<String, Object> map(Object... pairs) {
    return OperationInputConformance.m(pairs);
  }

  private static void amount(long expected, Object actual, String message) {
    equal(Long.toString(expected), String.valueOf(actual), message);
  }

  private static void equal(Object expected, Object actual, String message) {
    require(expected.equals(actual), message + ". Expected " + expected + " but got " + actual);
  }

  private static void require(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
}
