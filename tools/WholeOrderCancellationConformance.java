import blue.bex.BexError;
import blue.bex.Values;
import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Native whole-order decision, using role-scoped operations and independent trusted inputs. */
public final class WholeOrderCancellationConformance {
  private static final long HOUR = 3_600_000_000L;
  private static final long START = 7 * HOUR;
  private static final long DEADLINE = 9 * HOUR;
  private static final long BASIS = 7200;
  private static final String STATE = "/cancellationAvailability";
  private static final String DECISION = "/cancellationDecision";
  private static final Map<String, Object> INPUT = m("key", "cancel-1", "reason", "Customer changed plans");
  private final Contracts engine;

  private WholeOrderCancellationConformance(Contracts engine) {
    this.engine = engine;
  }

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]);
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var language = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var test = new WholeOrderCancellationConformance(runtime.processor(language));
      test.confirmation();
      test.elapsed();
      test.serviceCutoff();
      test.roundingAndWaiver();
      test.independentRetention();
      test.closedStatus();
    }
  }

  private void confirmation() {
    var waiting = order("Waiting for confirmation", BASIS, 25, true, true, true,
        m("confirmed", false, "serviceStart", 6 * HOUR));
    equal(true, read(waiting, STATE + "/beforeConfirmation"), "Live pre-confirmation exemption");
    absent(waiting, STATE + "/freeCancellationUntilMicros", "Waiting for seller does not expose a late deadline");
    var accepted = cancel(waiting, 10 * HOUR);
    amounts(accepted, 0, BASIS);
    equal(true, read(accepted, DECISION + "/beforeConfirmation"), "Accepted decision preserves exemption");
    var laterApproval = engine.process(accepted, event(accepted, "seller", "approve_seller", m("revision", 1), true), 11 * HOUR);
    equal(false, Boolean.TRUE.equals(read(laterApproval.commits() ? laterApproval.document() : accepted,
        "/activation/approved/seller")),
        "Configured terminal veto blocks later seller approval");
    System.out.println("PASS native pre-confirmation free cancellation and terminal approval veto");
  }

  private void elapsed() {
    var pending = order("Automatic without clock", BASIS, 25, true, false, false, m());
    equal(true, read(pending, STATE + "/awaitingWindowStart"), "Live pending clock flag");
    amounts(cancel(pending, 8 * HOUR), 0, BASIS);
    var at = order("Inclusive cutoff", BASIS, 25, true, false, false, m("windowStart", START));
    number(at, STATE + "/freeCancellationUntilMicros", DEADLINE);
    equal(true, read(at, STATE + "/lateCancellationAwaitingCapture"), "Advertise exact nonzero fee needs capture");
    amounts(cancel(at, DEADLINE), 0, BASIS);

    var late = order("Confirmed payable retry", BASIS, 25, true, false, false, m("windowStart", START));
    denies(late, "customer", "cancelOrder", INPUT, DEADLINE + 1, "CANCELLATION_AWAITING_CAPTURE");
    stillOpen(late);
    late = turn(late, "seller", "publishFacts", m("windowStart", START, "received", BASIS / 2), DEADLINE + 1);
    denies(late, "customer", "cancelOrder", INPUT, DEADLINE + 2, "CANCELLATION_AWAITING_CAPTURE");
    stillOpen(late);
    late = turn(late, "seller", "publishFacts", m("windowStart", START, "received", BASIS), DEADLINE + 2);
    equal(false, read(late, STATE + "/lateCancellationAwaitingCapture"), "Declared update recomputes readiness");
    var wrongRole = engine.process(late, event(late, "seller", "cancelOrder", INPUT, true), DEADLINE + 3);
    stillOpen(wrongRole.commits() ? wrongRole.document() : late);
    var unreviewed = engine.process(late, event(late, "customer", "cancelOrder", INPUT, false), DEADLINE + 4);
    stillOpen(unreviewed.commits() ? unreviewed.document() : late);
    denies(late, "customer", "cancelOrder", m("key", "cancel", "reason", "Partial", "lineIndices", List.of(0)),
        DEADLINE + 5, "INVALID_WHOLE_ORDER_CANCELLATION_INPUT");
    var result = engine.process(late, event(late, "customer", "cancelOrder", INPUT, true), DEADLINE + 6);
    equal("APPLIED", result.status(), "Late cancellation accepted");
    var cancelled = result.document();
    amounts(cancelled, 1800, 5400);
    equal("cancelled", read(cancelled, STATE + "/status"), "Availability transitions after acceptance");
    long acceptedEvents = ClauseGasProbe.eventData(engine, result).stream()
        .filter(data -> data instanceof Map<?, ?> fields && "Order Cancellation Accepted".equals(fields.get("kind"))
            && "cancel-1".equals(fields.get("entityId"))).count();
    equal(1L, acceptedEvents, "One typed event identifies the immutable decision");
    var replay = engine.process(cancelled, event(cancelled, "customer", "cancelOrder", INPUT, true), DEADLINE + 7);
    var replayed = replay.commits() ? replay.document() : cancelled;
    equal(read(cancelled, DECISION), read(replayed, DECISION), "Replay preserves exact decision");
    equal(List.of(), engine.emitted(replay), "Replay emits no second accepted event");
    denies(cancelled, "customer", "cancelOrder", m("key", "different", "reason", "Different decision"),
        DEADLINE + 8, "ORDER_CANCELLED");
    System.out.println("PASS native elapsed cutoff, positive captured retry, exact scope and immutable decision replay");
  }

  private void serviceCutoff() {
    var mixed = order("Service comes earlier", BASIS, 25, true, true, false,
        m("windowStart", 8 * HOUR, "serviceStart", 10 * HOUR, "received", BASIS));
    number(mixed, STATE + "/freeCancellationUntilMicros", 9 * HOUR);
    amounts(cancel(mixed, 9 * HOUR), 0, BASIS);
    var serviceOnly = order("Service-only", BASIS, 25, false, true, false,
        m("serviceStart", 10 * HOUR, "received", BASIS));
    number(serviceOnly, STATE + "/freeCancellationUntilMicros", 9 * HOUR);
    number(serviceOnly, STATE + "/lastCancellationMicros", 10 * HOUR - 1);
    amounts(cancel(serviceOnly, 9 * HOUR + 1), 1800, 5400);
    var after = order("Past service start", BASIS, 25, true, true, false,
        m("windowStart", 8 * HOUR, "serviceStart", 10 * HOUR, "received", BASIS));
    denies(after, "customer", "cancelOrder", INPUT, 10 * HOUR + 1, "ORDINARY_CANCELLATION_AFTER_START");
    var elapsedOnly = order("Elapsed window capped by service", BASIS, 25, true, false, false,
        m("windowStart", START, "serviceStart", 10 * HOUR, "received", BASIS));
    number(elapsedOnly, STATE + "/freeCancellationUntilMicros", DEADLINE);
    number(elapsedOnly, STATE + "/lastCancellationMicros", 10 * HOUR - 1);
    denies(elapsedOnly, "customer", "cancelOrder", INPUT, 10 * HOUR, "ORDINARY_CANCELLATION_AFTER_START");
    amounts(cancel(elapsedOnly, 10 * HOUR - 1), 1800, 5400);
    System.out.println("PASS native earliest service cutoff, inclusivity and after-start rejection");
  }

  private void roundingAndWaiver() {
    var roundedZero = order("Rounded zero", 1, 1, true, false, false, m("windowStart", START));
    equal(false, read(roundedZero, STATE + "/lateCancellationAwaitingCapture"), "Rounded zero needs no captured funds");
    amounts(cancel(roundedZero, DEADLINE + 1), 0, 1);
    var halfUp = order("Half minor unit", 2, 25, true, false, false, m("windowStart", START, "received", 2));
    amounts(cancel(halfUp, DEADLINE + 1), 1, 1);
    var complimentary = order("Complimentary", 0, 25, true, false, false, m());
    amounts(cancel(complimentary, DEADLINE + 1), 0, 0);
    var supplier = order("Authorized waiver", BASIS, 25, true, true, false,
        m("windowStart", START, "serviceStart", 10 * HOUR));
    var waived = turn(supplier, "seller", "cancelBySupplier", INPUT, 11 * HOUR);
    amounts(waived, 0, BASIS);
    equal(true, read(waived, DECISION + "/feeWaived"), "Author grants a separate fee-waived operation");
    System.out.println("PASS native common Money rounding, zero amount, and authorized fee waiver");
  }

  private void independentRetention() {
    var otherSettlement = order("Independent retention", BASIS, 25, true, false, false, false, m("windowStart", START));
    equal(false, read(otherSettlement, STATE + "/lateCancellationAwaitingCapture"), "Absent guard does not imply a payment hold");
    var accepted = cancel(otherSettlement, DEADLINE + 1);
    amounts(accepted, 1800, 5400);
    absent(accepted, "/payment", "An independent commercial decision needs no payment clause");
    System.out.println("PASS optional retention guard permits independent commercial decision");
  }

  private void closedStatus() {
    var statusBinding = m("orderStatus", "/facts/lifecycle");
    var statuses = m("closedOrderStatuses", List.of("DROPPED", "WITHDRAWN"));
    var pending = order("Open until closed", BASIS, 25, true, false, true, true,
        m("confirmed", false), statusBinding, statuses);
    equal("available", read(pending, STATE + "/status"), "Missing current status preserves availability");
    pending = turn(pending, "seller", "publishFacts", m("confirmed", false, "lifecycle", "QUEUED"), DEADLINE);
    equal("available", read(pending, STATE + "/status"), "Unlisted pending state preserves availability");
    equal(true, read(pending, STATE + "/beforeConfirmation"), "Still free while pending");
    var closed = turn(pending, "seller", "publishFacts", m("confirmed", false, "lifecycle", "WITHDRAWN"), DEADLINE + 1);
    equal("unavailable", read(closed, STATE + "/status"), "Status refresh removes cancellation availability");
    equal("order_closed", read(closed, STATE + "/reason"), "Generic unavailability reason");
    denies(closed, "customer", "cancelOrder", INPUT, DEADLINE + 2, "ORDER_CLOSED");
    denies(closed, "seller", "cancelBySupplier", INPUT, DEADLINE + 3, "ORDER_CLOSED");
    stillOpen(closed);
    absent(closed, DECISION + "/releasedMinor", "Closed state charges and releases nothing");

    var initiallyClosed = order("Closed at initialization", BASIS, 25, true, false, true, true,
        m("confirmed", false, "lifecycle", "DROPPED"), statusBinding, statuses);
    equal("unavailable", read(initiallyClosed, STATE + "/status"), "Every named status can close the initialized policy");
    var nonmatching = order("Pending is cancellable", BASIS, 25, true, false, true, true,
        m("confirmed", false, "lifecycle", "QUEUED"), statusBinding, statuses);
    var accepted = cancel(nonmatching, DEADLINE + 4);
    amounts(accepted, 0, BASIS);
    accepted = turn(accepted, "seller", "publishFacts", m("confirmed", false, "lifecycle", "DROPPED"), DEADLINE + 5);
    equal("cancelled", read(accepted, STATE + "/status"), "Prior acceptance stays visible after the status changes");
    var repeat = engine.process(accepted, event(accepted, "customer", "cancelOrder", INPUT, true), DEADLINE + 6);
    equal("APPLIED", repeat.status(), "Same exact cancellation is still retryable");
    equal(read(accepted, DECISION), read(repeat.document(), DECISION), "Retry keeps the original decision");
    equal(List.of(), engine.emitted(repeat), "Retry publishes no second financial trigger");
    denies(accepted, "seller", "cancelBySupplier", INPUT, DEADLINE + 7, "ORDER_CANCELLED");

    var unbound = order("Optional lifecycle is unbound", BASIS, 25, true, false, true, true,
        m("confirmed", false, "lifecycle", "WITHDRAWN"), m(), statuses);
    equal("available", read(unbound, STATE + "/status"), "No default status binding");
    amounts(cancel(unbound, DEADLINE + 8), 0, BASIS);
    System.out.println("PASS optional custom closed statuses drive native availability and both role routes; pending/free and exact replay remain");
  }

  private Contracts.Document order(String name, long amount, long percent, boolean elapsed, boolean service,
      boolean requireConfirmation, Map<String, Object> facts) {
    return order(name, amount, percent, elapsed, service, requireConfirmation, true, facts);
  }

  private Contracts.Document order(String name, long amount, long percent, boolean elapsed, boolean service,
      boolean requireConfirmation, boolean requireRetentionBasis, Map<String, Object> facts) {
    return order(name, amount, percent, elapsed, service, requireConfirmation, requireRetentionBasis, facts, m(), m());
  }

  private Contracts.Document order(String name, long amount, long percent, boolean elapsed, boolean service,
      boolean requireConfirmation, boolean requireRetentionBasis, Map<String, Object> facts,
      Map<String, Object> additionalBindings, Map<String, Object> additionalParameters) {
    var customer = channel("customer");
    var seller = channel("seller");
    var bind = m("amount", "/amountMinor", "decision", DECISION, "availability", STATE,
        "accept", m("cancelOrder", route("customer")),
        "acceptWithoutCharge", m("cancelBySupplier", route("seller")),
        "refreshAvailability", m("factsChanged", m("on", "change", "path", "/facts")));
    if (requireRetentionBasis) bind.put("retentionBasis", "/facts/received");
    var params = m("lateCancellationChargePercent", percent, "beforeWindowStarts", "free",
        "blockedOperationsAfterAcceptance", List.of("approve_seller"));
    if (elapsed) {
      bind.put("windowStart", "/facts/windowStart");
      params.put("freeCancellationHoursAfterStart", 2);
    }
    if (service || facts.containsKey("serviceStart")) bind.put("serviceStart", "/facts/serviceStart");
    if (service) params.put("freeCancellationHoursBeforeStart", 1);
    if (requireConfirmation) bind.put("confirmation", "/facts/confirmed");
    bind.putAll(additionalBindings);
    params.putAll(additionalParameters);
    var activation = m("type", "Activation/Activation Clause", "parameters", m(
        "parties", m("seller", party(seller), "customer", party(customer)),
        "required", requireConfirmation ? List.of("seller") : List.of(),
        "preActivationOperations", List.of("cancelOrder", "cancelBySupplier", "publishFacts"),
        "preActivationChannels", List.of("cx.cancellation.refreshAvailability._automatic_source",
            "cx.cancellation.refreshAvailability.factsChanged_source")));
    var publish = m("type", "Contracts/Sequential Workflow Operation", "channel", "seller", "steps",
        List.of(m("type", "Contracts/Compute", "do", List.of(m("$appendChange",
            m("op", "replace", "path", "/facts", "val", m("$binding", "call/request")))))));
    var source = m("type", "Orders/Order with Clauses", "name", name, "amountMinor", amount, "facts", facts,
        "contracts", m("seller", seller, "customer", customer, "publishFacts", publish),
        "clauses", m("activation", activation, "cancellation", m("type", "Commerce/Whole Order Cancellation Policy",
            "parameters", params, "bindings", bind)));
    var result = engine.initialize(source);
    if (!result.commits()) ClauseGasProbe.diagnose(engine, source);
    equal("APPLIED", result.status(), "Native initialize: " + name);
    return result.document();
  }

  private Contracts.Document cancel(Contracts.Document order, long time) {
    return turn(order, "customer", "cancelOrder", INPUT, time);
  }

  private void stillOpen(Contracts.Document order) {
    absent(order, DECISION + "/status", "No new whole-order decision");
  }

  private void amounts(Contracts.Document doc, long retained, long released) {
    equal("accepted", read(doc, DECISION + "/status"), "Recorded decision");
    number(doc, DECISION + "/retainedMinor", retained);
    number(doc, DECISION + "/releasedMinor", released);
  }

  private Contracts.Document turn(Contracts.Document doc, String actor, String op, Object input, long time) {
    var event = event(doc, actor, op, input, true);
    var result = engine.process(doc, event, time);
    if (!result.commits()) ClauseGasProbe.diagnose(engine, doc, event, time);
    equal("APPLIED", result.status(), "Native " + op);
    return result.document();
  }

  private void denies(Contracts.Document doc, String actor, String op, Object input, long time, String code) {
    var event = event(doc, actor, op, input, true);
    var result = engine.process(doc, event, time);
    equal(false, result.commits(), code + " rejects atomically");
    equal(List.of(), engine.emitted(result), "Rejected request emits no events");
    try {
      ClauseGasProbe.diagnose(engine, doc, event, time);
    } catch (BexError error) {
      equal(code, error.getMessage(), "Native failure reason");
      return;
    }
    throw new AssertionError("Expected " + code);
  }

  private Object read(Contracts.Document doc, String path) {
    return engine.read(doc, path);
  }

  private void number(Contracts.Document doc, String path, long value) {
    equal(Long.toString(value), String.valueOf(read(doc, path)), path);
  }

  private void absent(Contracts.Document doc, String path, String reason) {
    equal(Values.UNDEFINED, read(doc, path), reason);
  }

  private static Map<String, Object> event(Contracts.Document doc, String actor, String op, Object input, boolean exact) {
    return m("source", actor, "operation", m("type", "Contracts/Operation Request", "channel", actor,
        "operation", op, "request", input, "document", m("blueId", doc.blueId()), "requireExactDocumentVersion", exact));
  }

  private static Map<String, Object> route(String party) {
    return m("on", "workflow", "party", party, "input", true, "requireExactDocumentVersion", true);
  }

  private static Object channel(String role) {
    return m("type", "Contracts/External Channel", "event", m("source", role));
  }

  private static Object party(Object channel) {
    return m("type", "Parties/Party", "readerKeys", List.of("fixture-reader"), "lead", m("channel", channel));
  }

  private static Map<String, Object> m(Object... values) {
    var result = new LinkedHashMap<String, Object>();
    for (int i = 0; i < values.length; i += 2) result.put((String) values[i], values[i + 1]);
    return result;
  }

  private static void equal(Object expected, Object actual, String message) {
    if (!Objects.equals(expected, actual)) throw new AssertionError(message + " expected " + expected + ", got " + actual);
  }
}
