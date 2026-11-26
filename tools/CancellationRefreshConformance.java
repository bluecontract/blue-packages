import blue.bex.Values;
import blue.contracts.AttachmentDocuments;
import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Crosses real native managed-document boundaries without a browser or provider. */
public final class CancellationRefreshConformance {
  private static final long AMOUNT = 7200;
  private static final long HOUR = 3_600_000_000L;
  private static final String AVAILABILITY = "/cancellationAvailability";
  private static final List<String> ROLES = List.of("seller", "customer", "guarantor");
  private final Contracts engine;
  private long time = 2 * HOUR;

  private CancellationRefreshConformance(Contracts engine) {
    this.engine = engine;
  }

  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]);
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var language = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var test = new CancellationRefreshConformance(runtime.processor(language));
      test.localParentReplacement();
      boolean baseline = args.length == 2 && args[1].equals("baseline");
      test.managedCapture(baseline);
      if (!baseline) test.attachCompleted();
    }
  }

  private void localParentReplacement() {
    var order = initialized(order("C17 parent replacement", true));
    order = apply(order, "", "seller", "overwriteFacts", m("flag", true)).document();
    equal(true, read(order, "/facts/flag"), "Ancestor replacement was committed");
    equal(Values.UNDEFINED, read(order, "/localWatchObserved"), "T03 descendant local watcher ignored ancestor replacement");
    equal(true, read(order, "/parentWatchObserved"), "A watcher on the replaced parent observes the write");
    order = apply(order, "", "seller", "writeFlag", m("flag", false)).document();
    equal(true, read(order, "/localWatchObserved"), "T03 exact descendant write still reaches same local watcher");
    System.out.println("PASS T03 local child watcher ignores ancestor replacement but observes an exact local write");
  }

  private void managedCapture(boolean baseline) {
    var order = initialized(order("Selected and foreign Payment Instructions", baseline));
    var selected = prepare(order, "selectedPayment", "Selected root");
    order = selected.order();
    var foreign = prepare(order, "foreignPayment", "Other root at identical amount");
    order = foreign.order();
    var selectedPI = prepareCapture(selected.payment());
    var foreignPI = prepareCapture(foreign.payment());
    String selectedOrigin = refAt(selectedPI, "/contracts/initialized/document");
    String foreignOrigin = refAt(foreignPI, "/contracts/initialized/document");
    if (Objects.equals(selectedOrigin, foreignOrigin)) throw new AssertionError("Fixture PI origins must differ");
    order = provision(order, selected, selectedPI, "selectedPayment").document();
    order = provision(order, foreign, foreignPI, "foreignPayment").document();
    equal(selectedOrigin, refAt(order, "/payment/contracts/initialized/document"), "Attached selected origin");
    equal(foreignOrigin, refAt(order, "/foreignPI/contracts/initialized/document"), "Attached different origin");
    assertAwaitingCapture(order, true);

    var foreignOutcome = complete(order, "/foreignPI");
    equal(AMOUNT, number(foreignOutcome.document(), "/foreignPI/payment/completed"), "Foreign native completion at the same amount");
    equal(0L, number(foreignOutcome.document(), "/payment/payment/completed"), "Selected PI still awaiting completion");
    equal(List.of("foreignObserver"), relayedCaptureClauses(foreignOutcome), "Genuine same-type foreign relay");
    equal(Values.UNDEFINED, read(foreignOutcome.document(), "/qualifiedWake"), "Foreign completion cannot reach selected trigger");
    assertAwaitingCapture(foreignOutcome.document(), true);

    var selectedOutcome = complete(foreignOutcome.document(), "/payment");
    equal(AMOUNT, number(selectedOutcome.document(), "/payment/payment/completed"), "Selected native completion committed");
    equal(List.of("payment"), relayedCaptureClauses(selectedOutcome), "A selected completion has one ordinary typed relay");
    if (baseline) {
      assertAwaitingCapture(selectedOutcome.document(), true);
      System.out.println("PASS T03 local leaf watcher remains stale after a genuinely managed selected PI completion");
      return;
    }
    equal(true, read(selectedOutcome.document(), "/qualifiedWake"), "The selected relay reaches the qualified listener");
    assertAwaitingCapture(selectedOutcome.document(), false);
    var replay = complete(selectedOutcome.document(), "/payment");
    equal(List.of(), relayedCaptureClauses(replay), "No new relay on exact provider outcome replay");
    assertAwaitingCapture(replay.document(), false);
    equal(Values.UNDEFINED, read(replay.document(), "/cancellationDecision/status"), "Capture and replay create no cancellation decision");
    System.out.println("PASS T02 selected origin " + selectedOrigin + " refreshed by capture; foreign origin "
        + foreignOrigin + " at same amount left selected availability untouched");
  }

  private void attachCompleted() {
    var prepared = prepare(initialized(order("Catch-up from a completed PI", false)), "selectedPayment", "Selected root");
    var paid = complete(prepareCapture(prepared.payment()), "").document();
    equal(AMOUNT, number(paid, "/payment/completed"), "PI completed before the stock provide operation");
    assertAwaitingCapture(prepared.order(), true);
    var attached = provision(prepared.order(), prepared, paid, "selectedPayment");
    var values = engine.execution().values();
    equal(1L, eventsOf(attached, "Documents/Document Attached").stream()
        .filter(event -> "selectedPayment".equals(values.bexData(values.select(event, "/clauseId")))
            && "single".equals(values.bexData(values.select(event, "/itemKey")))).count(),
        "One native selected attachment response");
    equal(List.of(), relayedCaptureClauses(attached), "Attaching retained outcome does not replay operator event");
    assertAwaitingCapture(attached.document(), false);
    var retry = provision(attached.document(), prepared, paid, "selectedPayment");
    equal(read(attached.document(), AVAILABILITY), read(retry.document(), AVAILABILITY), "T04 replay leaves availability intact");
    equal(Values.UNDEFINED, read(retry.document(), "/cancellationDecision/status"), "Catch-up leaves decision absent");
    System.out.println("PASS T04 actual selected attachment catches up already completed PI " + refAt(paid, "/contracts/initialized/document"));
  }

  private record Prepared(Contracts.Document order, Contracts.Document payment, Map<String, Object> obligation) {}

  private Prepared prepare(Contracts.Document order, String key, String name) {
    order = apply(order, "", "seller", "prepare_" + key, m()).document();
    var entries = fields(read(order, "/process_" + key + "/entries"));
    equal(1, entries.size(), "One prepared obligation for " + key);
    var obligation = fields(entries.values().iterator().next());
    equal("single", obligation.get("key"), "The payment slot has the default obligation key");
    var prepared = fields(AttachmentDocuments.source(engine, order, obligation.get("itemPath") + "/prepared"));
    equal(name, prepared.get("name"), "The stock obligation selects its own prepared template");
    return new Prepared(order, initialized(prepared), obligation);
  }

  private Contracts.Result provision(Contracts.Document order, Prepared prepared, Contracts.Document pi, String key) {
    engine.execution().chooseHistory(pi.blueId(), engine.execution().snapshot(pi));
    return apply(order, "", "seller", "provide_" + key, m("type", "Documents/Provision Input",
        "inResponseTo", prepared.obligation().get("requestId"), "requirementRef", prepared.obligation().get("requirementRef"),
        "document", m("blueId", pi.blueId())));
  }

  private Contracts.Document prepareCapture(Contracts.Document pi) {
    pi = apply(pi, "", "guarantor", "acceptPaymentInstruction", m()).document();
    pi = apply(pi, "", "guarantor", "recordTransactionInitiated", m("type", "PaymentInstruction/Transaction Initiation Input",
        "transactionId", "transaction-" + pi.blueId(), "railType", "test", "attachmentPoint", "instruction", "providerReference", "local")).document();
    pi = apply(pi, "", "customer", "requestHold", request("hold")).document();
    pi = apply(pi, "", "guarantor", "secureFunds", outcome("hold")).document();
    return apply(pi, "", "customer", "requestCapture", request("capture")).document();
  }

  private Contracts.Result complete(Contracts.Document root, String path) {
    return apply(root, path, "guarantor", "completePayment", outcome("capture"));
  }

  private static Object request(String key) {
    return m("type", "PaymentInstruction/Payment Request Input", "requestId", key, "amountMinor", AMOUNT);
  }

  private static Object outcome(String key) {
    return m("type", "PaymentInstruction/Payment Outcome Input", "requestId", key);
  }

  private Map<String, Object> order(String name, boolean legacy) {
    var changed = legacy ? m("on", "change", "path", "/payment/payment/completed")
        : m("on", "event", "event", qualifiedCapture());
    var refresh = m("capture", changed);
    if (!legacy) refresh.put("attachment", m("on", "event", "event",
        m("type", "Documents/Document Attached", "clauseId", "selectedPayment", "itemKey", "single")));
    var cancellation = m("type", "Commerce/Whole Order Cancellation Policy", "parameters",
        m("lateCancellationChargePercent", 25, "freeCancellationHoursAfterStart", 0), "bindings", m(
            "amount", "/amountMinor", "retentionBasis", "/payment/payment/completed", "decision", "/cancellationDecision",
            "availability", AVAILABILITY, "windowStart", "/windowStart", "refreshAvailability", refresh,
            "accept", m("cancelOrder", route("customer"))));
    return m("type", "Orders/Order with Clauses", "name", name, "amountMinor", AMOUNT,
        "windowStart", HOUR, "facts", m("flag", false),
        "contracts", m("seller", channel("seller"), "overwriteFacts", write("/facts", ""),
            "writeFlag", write("/facts/flag", "/flag")),
        "clauses", m("activation", activation(), "selectedPayment", documentClause("selectedPayment", "/payment", "Selected root"),
            "foreignPayment", documentClause("foreignPayment", "/foreignPI", "Other root at identical amount"),
            "cancellation", cancellation, "payment", observation("/payment"), "foreignObserver", observation("/foreignPI"),
            "probe", m("type", m("name", "Native cancellation observations", "type", "Connections/Connected Clause",
                "actions", m("local", mark("/localWatchObserved"), "parent", mark("/parentWatchObserved"),
                    "qualified", mark("/qualifiedWake"))), "bindings", m(
                    "local", m("leaf", m("on", "change", "path", "/facts/flag")),
                    "parent", m("root", m("on", "change", "path", "/facts")),
                    "qualified", m("capture", m("on", "event", "event", qualifiedCapture()))))));
  }

  private static Object documentClause(String key, String path, String name) {
    var parties = m("seller", "seller", "customer", "customer", "guarantor", "guarantor");
    var payment = m("type", "PaymentInstruction/Payment Instruction with Clauses", "name", name,
        "paymentTerms", m("amountMinor", AMOUNT, "limitMinor", AMOUNT, "currency", "USD", "payerChannel", "customer",
            "payeeChannel", "seller", "guarantorChannel", "guarantor", "allowedPayees", List.of("seller"), "recipientApprovalRequired", false),
        "clauses", m("activation", activation(), "requests", m("type", "PaymentInstruction/Payment Request Actions", "bindings", m(
            "requestAuthorize", m("requestHold", route("customer")), "requestCapture", m("requestCapture", route("customer"))))));
    return m("type", "Documents/Document Clause", "parameters", m("obtain", "provide", "suppliedBy", "seller", "template", payment),
        "bindings", m("parties", parties, "document", path,
            "prepare", m("prepare_" + key, route("seller")), "provide", m("provide_" + key, route("seller"))));
  }

  private static Object activation() {
    var parties = m();
    for (var role : ROLES) parties.put(role, m("type", "Parties/Party", "myosAccountId", role + "-account",
        "readerKeys", List.of("reader-" + role), "lead", m("channel", channel(role))));
    return m("type", "Activation/Activation Clause", "parameters", m("parties", parties, "required", List.of()));
  }

  private static Object channel(String actor) {
    return m("type", "Contracts/External Channel", "event", m("source", actor));
  }

  private static Object observation(String path) {
    return m("type", "Payment/Payment Observation Clause", "bindings", m("instruction", path));
  }

  private static Object qualifiedCapture() {
    return m("type", "Payment/Payment Event Received", "clause", "payment", "instructionPath", "/payment",
        "event", m("type", "PaymentInstruction/Payment Completed"));
  }

  private static Object write(String path, String field) {
    return m("type", "Contracts/Sequential Workflow Operation", "channel", "seller", "steps", List.of(
        m("type", "Contracts/Update Document", "changeset", List.of(m("op", "replace", "path", path,
            "val", m("$binding", "call/request" + field))))));
  }

  private static Object mark(String path) {
    return m("do", List.of(m("$appendChange", m("op", "add", "path", path, "val", true))));
  }

  private static Map<String, Object> route(String actor) {
    return m("on", "workflow", "party", actor, "input", true, "requireExactDocumentVersion", true);
  }

  private List<Object> relayedCaptureClauses(Contracts.Result result) {
    var values = engine.execution().values();
    var completed = values.source(m("type", "PaymentInstruction/Payment Completed"), "definition");
    return eventsOf(result, "Payment/Payment Event Received").stream()
        .filter(event -> values.matches(values.select(event, "/event"), completed))
        .map(event -> values.bexData(values.select(event, "/clause")))
        .toList();
  }

  private List<Exact.Ref> eventsOf(Contracts.Result result, String alias) {
    var values = engine.execution().values();
    var type = values.source(m("type", alias), "definition");
    return result.publicEvents().stream()
        .map(event -> new Exact.Ref(event.get("event").toString()))
        .filter(event -> values.matches(event, type))
        .toList();
  }

  private Contracts.Document initialized(Object source) {
    var result = engine.initialize(source);
    if (!result.commits()) ClauseGasProbe.diagnose(engine, source);
    equal("APPLIED", result.status(), "Initialize native fixture");
    return result.document();
  }

  private Contracts.Result apply(Contracts.Document root, String path, String actor, String operation, Object request) {
    var event = m("source", actor, "operation", m("type", "Contracts/Operation Request", "channel", actor,
        "operation", operation, "request", request, "document", m("blueId", refAt(root, path)), "requireExactDocumentVersion", true));
    var result = engine.process(root, event, ++time);
    if (!result.commits()) ClauseGasProbe.diagnose(engine, root, event, time);
    equal("APPLIED", result.status(), operation);
    return result;
  }

  private String refAt(Contracts.Document root, String path) {
    var values = engine.execution().values();
    return NativeRuntime.identity(values.exact(values.select(new Exact.Ref(root.blueId()), path)));
  }

  private void assertAwaitingCapture(Contracts.Document order, boolean expected) {
    equal(!expected, read(order, AVAILABILITY + "/retentionReady"), "Native captured retention basis");
    equal(expected, read(order, AVAILABILITY + "/lateCancellationAwaitingCapture"), "Native retained availability");
  }

  private Object read(Contracts.Document root, String path) { return engine.read(root, path); }

  private long number(Contracts.Document root, String path) { return Long.parseLong(String.valueOf(read(root, path))); }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> fields(Object fields) { return (Map<String, Object>) fields; }

  private static Map<String, Object> m(Object... values) {
    var result = new LinkedHashMap<String, Object>();
    for (int i = 0; i < values.length; i += 2) result.put((String) values[i], values[i + 1]);
    return result;
  }

  private static void equal(Object expected, Object actual, String label) {
    if (!Objects.equals(expected, actual)) throw new AssertionError(label + ": expected " + expected + ", got " + actual);
  }
}
