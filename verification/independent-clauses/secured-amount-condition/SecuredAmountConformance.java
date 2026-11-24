package blue.core;

import blue.bex.BexError;
import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public final class SecuredAmountConformance {
  private static final long AMOUNT = 7200;
  private static final long START = 36_000_000_000L;
  private static final String INSTRUCTION = "/escrow/instruction";
  private static final String DEPOSIT = "/deposits/primary";
  private final Contracts runtime;
  private final Path fixtures;
  private long time = 1000;

  private SecuredAmountConformance(Contracts runtime, Path fixtures) {
    this.runtime = runtime;
    this.fixtures = fixtures;
  }

  public static void main(String[] args) throws Exception {
    var packages = CompositionPackages.published(Path.of(args[0]), Path.of(args[0], "PACKAGES.json"));
    try (var language = packages.language(); var authoring = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var proof = new SecuredAmountConformance(authoring.processor(language), Path.of(args[1]));
      proof.schedule();
      proof.membership();
    }
  }

  private void schedule() throws Exception {
    var pending = initialize(scheduledSource());
    denied(pending, "seller", "confirmReservation", review(pending));
    denied(pending, "seller", "proposeAlternative", alternative(pending));
    var payment = instruction(read(pending, "/activation/revision"), read(pending, "/activation/terms/ref"));
    var linked = attach(pending, "seller", payment);
    denied(linked, "seller", "confirmReservation", review(linked));
    var funded = secure(linked, INSTRUCTION, AMOUNT);
    var confirmed = call(funded, "", "seller", "confirmReservation", review(funded));
    equal("confirmed", read(confirmed, "/booking/status"), "Seller confirmation reaches stock Schedule");
    equal(true, read(confirmed, "/activation/active"), "Normal review activates");

    var offered = call(funded, "", "seller", "proposeAlternative", alternative(funded));
    equal("pending_customer", read(offered, "/booking/status"), "Seller alternative reaches stock Schedule");
    var reserved = call(offered, INSTRUCTION, "guarantor", "capture", instructionRequest("capture-pending", 1));
    equal("1", String.valueOf(read(reserved, INSTRUCTION + "/payment/reserved/capture")), "Native capture in flight");
    denied(reserved, "customer", "acceptProposal", review(reserved));
    var retry = call(reserved, INSTRUCTION, "guarantor", "failCompletePayment", m(
        "type", "PaymentInstruction/Payment Outcome Input", "requestId", "capture-pending", "reason", "Failed"));
    equal("0", String.valueOf(read(retry, INSTRUCTION + "/payment/reserved/capture")), "Native failure freed reservation");
    var accepted = call(retry, "", "customer", "acceptProposal", review(retry));
    equal("confirmed", read(accepted, "/booking/status"), "Buyer acceptance reads restored available hold");
    System.out.println("PASS stock confirm, alternative, and accept against a live managed instruction");
  }

  private void membership() throws Exception {
    var review = membershipSource(m("instruction", DEPOSIT, "amountMinor", "/renewal/deposit",
        "revision", "/renewal/edition", "termsRef", "/renewal/contract"));
    var pending = initialize(review);
    var empty = attach(pending, "seller", instruction(3, "membership-terms"));
    var approved = call(empty, "", "seller", "confirmMembership", m());
    equal(true, read(approved, "/confirmed"), "Zero deposit has no artificial minimum");
    var increased = revise(empty, 1, 3, "membership-terms");
    denied(increased, "seller", "confirmMembership", m());
    var newEdition = revise(empty, 0, 4, "membership-terms");
    denied(newEdition, "seller", "confirmMembership", m());
    var newTerms = revise(empty, 0, 3, "replacement-terms");
    denied(newTerms, "seller", "confirmMembership", m());
    var restored = revise(newTerms, 0, 3, "membership-terms");
    var reviewedAgain = call(restored, "", "seller", "confirmMembership", m());
    equal(true, read(reviewedAgain, "/confirmed"), "Same attached PI passes with restored current scope");

    var stale = attach(pending, "seller", instruction(2, "membership-terms"));
    denied(stale, "seller", "confirmMembership", m());
    var wrongTerms = attach(pending, "seller", instruction(3, "old-membership-terms"));
    denied(wrongTerms, "seller", "confirmMembership", m());
    var missingGroupInput = initialize(membershipSource(m("instruction", DEPOSIT,
        "amountMinor", "/renewal/deposit", "revision", "/renewal/edition")));
    missingGroupInput = attach(missingGroupInput, "seller", instruction(3, "membership-terms"));
    denied(missingGroupInput, "seller", "confirmMembership", m());

    var funded = secure(empty, DEPOSIT, AMOUNT);
    var voiding = call(funded, DEPOSIT, "guarantor", "void", instructionRequest("release", AMOUNT));
    equal(true, read(voiding, DEPOSIT + "/payment/cancellationPending"), "Native cancellation in progress");
    denied(voiding, "seller", "confirmMembership", m());
    var closed = call(voiding, DEPOSIT, "guarantor", "cancelBeforeCompletion", outcome("release"));
    equal(true, read(closed, DEPOSIT + "/payment/closed"), "Native closure");
    denied(closed, "seller", "confirmMembership", m());
    System.out.println("PASS membership layout, live amount and scope, zero, missing input, void and closed state");
  }

  private Map<String,Object> scheduledSource() {
    var quote = m("supplierId", "seller", "currency", "USD", "totalMinor", AMOUNT,
        "lines", List.of(m("lineTotalMinor", AMOUNT)));
    var terms = m("agreementDescription", "Native review fixture", "fulfilmentText", "Two-hour class",
        "confirmationMode", "supplier", "dateRequired", true);
    var snapshot = m("quote", quote, "quoteBlueId", sourceId(quote), "terms", terms, "termsBlueId", sourceId(terms),
        "groups", List.of(m("id", "booking-1", "lineIndices", List.of(0), "proposedStartMicros", START)));
    var funded = group(List.of("confirm", "alternative", "accept"), m(
        "instruction", INSTRUCTION, "amountMinor", "/amountMinor",
        "revision", "/activation/revision", "termsRef", "/activation/terms/ref"));
    var reservation = m("type", "Schedule/Reservation Clause",
        "parameters", m("conditionGroups", m("reviewedEscrow", funded)),
        "bindings", m("wholeReservation", "/booking",
            "confirm", m("confirmReservation", route("seller")),
            "alternative", m("proposeAlternative", route("seller")),
            "accept", m("acceptProposal", route("customer"))));
    var reviewed = m("seller", m(
        "event", m("type", "Schedule/Reservation Reviewed", "clause", "reservation", "subject", "booking-1"),
        "source", "/reservations/booking-1", "basis", "/amountMinor", "acceptanceBy", "customer"));
    var review = activation(List.of("seller"), List.of("attach", "confirmReservation", "proposeAlternative", "acceptProposal"),
        List.of("cx.reservation.initialize._automatic_source"), reviewed);
    return m("name", "Date review with escrow", "type", "Orders/Order with Clauses",
        "amountMinor", AMOUNT, "orderSnapshot", snapshot, "escrow", m(),
        "contracts", embedding(INSTRUCTION, false),
        "clauses", m("activation", review, "reservation", reservation));
  }

  private Map<String,Object> membershipSource(Map<String,Object> inputs) {
    var action = m("preflight", List.of(write("/preflight"), m("$set", m("name", "actionResult",
        "expr", m("outcome", "acceptedNew")))), "do", List.of(write("/confirmed")));
    var declaration = m("type", m("name", "Membership review", "type", "Connections/Connected Clause",
        "actions", m("confirm", action)), "parameters", m("conditionGroups", m("deposit", group(List.of("confirm"), inputs))),
        "bindings", m("confirm", m("confirmMembership", m("on", "workflow", "party", "seller",
            "before", List.of(write("/before"))))));
    var contracts = embedding(DEPOSIT, true);
    contracts.put("revise", m("type", "Contracts/Sequential Workflow Operation", "channel", "seller",
        "steps", List.of(m("type", "Contracts/Update Document", "changeset", List.of(
          m("op", "replace", "path", "/renewal/deposit", "val", m("$binding", "call/request/deposit")),
          m("op", "replace", "path", "/renewal/edition", "val", m("$binding", "call/request/edition")),
          m("op", "replace", "path", "/renewal/contract", "val", m("$binding", "call/request/terms")))))));
    return m("name", "Membership renewal", "type", "Agreements/Agreement with Clauses",
        "renewal", m("edition", 3, "contract", "membership-terms", "deposit", 0), "deposits", m(),
        "contracts", contracts,
        "clauses", m("activation", activation(List.of(), List.of(), List.of()), "membership", declaration));
  }

  private Map<String,Object> group(List<String> actions, Map<String,Object> inputs) {
    return m("type", "Payment/Secured Amount Condition", "actions", actions, "inputs", inputs);
  }

  private Map<String,Object> embedding(String path, boolean collection) {
    var embedded = m("type", "Contracts/Process Embedded", collection ? "collectionPaths" : "paths",
        List.of(collection ? "/deposits" : path));
    return m("embedded", embedded, "seller", m("type", "Contracts/External Channel", "event", m("source", "seller")),
        "attach", m("type", "Contracts/Sequential Workflow Operation", "channel", "seller",
      "steps", List.of(m("type", "Contracts/Update Document", "changeset", List.of(m(
          "op", "add", "path", path, "val", m("$binding", "call/request/instruction")))))));
  }

  private Contracts.Document instruction(Object revision, Object terms) throws Exception {
    var source = CurrentOperationScenarios.read(fixtures.resolve("../financial/payment.blue"));
    source.remove("sources");
    source.put("businessContext", m("orderRevision", revision, "orderTermsRef", terms));
    var requests = CompositionPackages.obj(CompositionPackages.obj(source.get("clauses")).get("requests"));
    requests.put("bindings", m("requestAuthorize", m("authorize", route("guarantor")),
        "requestCapture", m("capture", route("guarantor")), "requestVoid", m("void", route("guarantor"))));
    return initialize(source);
  }

  private Contracts.Document attach(Contracts.Document host, String actor, Contracts.Document instruction) {
    runtime.execution().chooseHistory(instruction.blueId(), runtime.execution().snapshot(instruction));
    return call(host, "", actor, "attach", m("instruction", ref(instruction.blueId())));
  }

  private Contracts.Document revise(Contracts.Document host, int deposit, int edition, String terms) {
    return call(host, "", "seller", "revise", m("deposit", deposit, "edition", edition, "terms", terms));
  }

  private Contracts.Document secure(Contracts.Document host, String path, long amount) {
    host = call(host, path, "guarantor", "acceptPaymentInstruction", m());
    host = call(host, path, "guarantor", "recordTransactionInitiated", m(
        "type", "PaymentInstruction/Transaction Initiation Input", "transactionId", "fixture-hold",
        "railType", "test", "attachmentPoint", "instruction", "providerReference", "fixture"));
    host = call(host, path, "guarantor", "authorize", instructionRequest("hold", amount));
    return call(host, path, "guarantor", "secureFunds", outcome("hold"));
  }

  private Map<String,Object> review(Contracts.Document order) {
    return m("key", "confirm", "groupId", "booking-1",
        "expectedProposalBlueId", read(order, "/reservations/booking-1/proposalBlueId"));
  }

  private Map<String,Object> alternative(Contracts.Document order) {
    var request = review(order);
    request.put("key", "alternative");
    request.put("proposedStartMicros", START * 2);
    request.put("catalog", m("supplierId", "seller", "revision", 1, "currency", "USD", "entries", m(
        "bike", m("label", "Bike", "description", "Hourly rental", "pricingUnit", "per_unit",
            "unitAmountMinor", AMOUNT, "dateRequired", false))));
    request.put("lines", List.of(m("itemId", "bike", "quantity", 1)));
    return request;
  }

  private Map<String,Object> activation(List<String> required, List<String> operations, List<String> channels) {
    return activation(required, operations, channels, m());
  }

  private Map<String,Object> activation(List<String> required, List<String> operations, List<String> channels,
      Map<String,Object> reviewed) {
    var parties = m();
    for (var role : List.of("seller", "customer")) {
      parties.put(role, m("type", "Parties/Party", "myosAccountId", role + "-account",
        "readerKeys", List.of("key-" + role), "lead", m("channel", m("type", "Contracts/External Channel",
            "event", m("source", role)))));
    }
    var parameters = m("parties", parties, "required", required,
        "preActivationOperations", operations, "preActivationChannels", channels);
    if (!reviewed.isEmpty()) parameters.put("reviewedApprovals", reviewed);
    return m("type", "Activation/Activation Clause", "parameters", parameters);
  }

  private Contracts.Document initialize(Map<String,Object> source) {
    var result = runtime.initialize(source);
    if (!result.commits()) ClauseGasProbe.diagnose(runtime, source);
    require(result.commits(), "Initialize " + source.get("name"));
    return result.document();
  }

  private Contracts.Document call(Contracts.Document host, String path, String actor, String operation, Object input) {
    var event = event(host, path, actor, operation, input);
    var result = runtime.process(host, event, ++time);
    if (!result.commits()) ClauseGasProbe.diagnose(runtime, host, event, time);
    require(result.commits(), "Apply " + operation);
    return result.document();
  }

  private void denied(Contracts.Document host, String actor, String operation, Object input) {
    var event = event(host, "", actor, operation, input);
    var result = runtime.process(host, event, ++time);
    equal(false, result.commits(), "Deny " + operation);
    equal(List.of(), runtime.emitted(result), "Denial emits no events");
    for (var path : List.of("/activation/approved", "/reservationRequests", "/booking", "/preflight", "/before", "/confirmed")) {
      equal(read(host, path), read(result.document(), path), "Denial leaves " + path);
    }
    try {
      ClauseGasProbe.diagnose(runtime, host, event, time);
      throw new AssertionError("Expected ACTION_CONDITION_FAILED");
    } catch (BexError failure) {
      require(failure.getMessage().contains("ACTION_CONDITION_FAILED"), failure.getMessage());
    }
  }

  private Object event(Contracts.Document host, String path, String actor, String operation, Object input) {
    var values = runtime.execution().values();
    String target = path.isEmpty() ? host.blueId()
        : NativeRuntime.identity(values.exact(values.select(new Exact.Ref(host.blueId()), path)));
    return m("source", actor, "operation", m("type", "Contracts/Operation Request", "channel", actor,
        "operation", operation, "request", input, "document", ref(target), "requireExactDocumentVersion", true));
  }

  private Object read(Contracts.Document host, String path) { return runtime.read(host, path); }
  private String sourceId(Object data) { return NativeRuntime.identity(runtime.execution().values().source(data)); }
  private static Object write(String p) { return m("$appendChange", m("op", "add", "path", p, "val", true)); }
  private static Map<String,Object> ref(String id) { return m("blueId", id); }
  private static Map<String,Object> route(String actor) {
    return m("on", "workflow", "party", actor, "input", true, "requireExactDocumentVersion", true);
  }
  private static Map<String,Object> instructionRequest(String key, long amount) {
    return m("type", "PaymentInstruction/Payment Request Input", "requestId", key, "amountMinor", amount);
  }
  private static Map<String,Object> outcome(String key) {
    return m("type", "PaymentInstruction/Payment Outcome Input", "requestId", key);
  }
  private static Map<String,Object> m(Object... args) {
    var map = new LinkedHashMap<String,Object>();
    for (int i=0; i<args.length; i+=2) map.put((String)args[i], args[i+1]);
    return map;
  }
  private static void equal(Object expected, Object actual, String label) {
    require(Objects.equals(expected, actual), label + " expected " + expected + ", got " + actual);
  }
  private static void require(boolean condition, String explanation) {
    if (!condition) throw new AssertionError(explanation);
  }
}
