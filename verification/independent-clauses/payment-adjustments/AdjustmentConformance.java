package blue.core;

import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

/** Drives stock payment effects with a fixture-owned, independent price decision. */
public final class AdjustmentConformance {
  private static final String ORDER = "/sources/order";
  private static final String GATE = "/paymentProcess_payment/captureAllowed";
  private static final String REQUESTS = "/payment/requests/";
  private static final long AMOUNT = 7200;

  private final Contracts engine;
  private final Path fixtures;
  private long time;

  private AdjustmentConformance(Contracts engine, Path fixtures) {
    this.engine = engine;
    this.fixtures = fixtures;
  }

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]);
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var language = packages.language();
         var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var checks = new AdjustmentConformance(runtime.processor(language), Path.of(args[1]));
      if (args.length > 2 && args[2].equals("manual-refund-recovery")) {
        checks.manualRefundRecovery();
        return;
      }
      checks.partialPriorRefund();
      checks.pendingCapture();
      checks.heldAndMissingInputs();
      checks.optionalVoidLeg();
      checks.reusedRequestId();
    }
  }

  private void partialPriorRefund() throws Exception {
    var payment = payment("correction", "both");
    expect(false, read(payment, GATE), "Missing selection denies capture");
    payment = select(payment, true);
    payment = gates(payment, "confirmed", "pending");
    expect(false, read(payment, GATE), "Legacy whenAlso still applies");
    payment = gates(payment, "waiting", "approved");
    expect(false, read(payment, GATE), "Published service requirement adds its own restriction");
    payment = gates(payment, "confirmed", "approved");
    if (!Boolean.TRUE.equals(read(payment, GATE))) {
      for (String path : new String[] {"/activation", "/businessContext", "/paymentTerms",
          ORDER + "/activation", ORDER + "/process_payment", ORDER + "/payment",
          ORDER + "/serviceStatus", ORDER + "/ordinaryReview", "/sourceLinks"}) {
        System.err.println(path + " = " + read(payment, path));
      }
    }
    expect(true, read(payment, GATE), "Original selected payment and both restrictions pass");
    payment = fund(payment);
    payment = secure(payment);
    amount(AMOUNT, read(payment, REQUESTS + "ordinary-capture/intent/amountMinor"), "Stock full capture request");
    payment = invoke(payment, "", "guarantor", "completePayment", outcome("ordinary-capture"));
    payment = invoke(payment, "", "seller", "requestRefund", request("earlier-refund", 1200));
    payment = decide(payment, true, 1800L);
    expect(false, read(payment, GATE), "Accepted adjustment blocks new capture");
    absent(payment, REQUESTS + "correction-refund", "An earlier pending refund occupies the available amount");
    payment = invoke(payment, "", "guarantor", "reverseAfterCompletion", outcome("earlier-refund"));
    amount(4200, read(payment, REQUESTS + "correction-refund/intent/amountMinor"), "Refund only the remainder");
    payment = invoke(payment, "", "guarantor", "reverseAfterCompletion", outcome("correction-refund"));
    payment = decide(payment, true, 1800L);
    amount(5400, read(payment, "/payment/reversed"), "Native confirmed cumulative refund");
    amount(4, object(read(payment, "/payment/requests")).size(), "Decision replay adds no request");
    absent(payment, REQUESTS + "correction-void", "A retained balance never requests void");
    System.out.println("PASS typed capture guards, prior refund and price correction replay");
  }

  private void manualRefundRecovery() throws Exception {
    String automatic = "correction-refund";
    String retry = "manual-refund-recovery";
    String reserved = "/payment/reserved/refund";
    long refund = 5400;
    var payment = gates(select(payment("refund-recovery", "both"), true), "confirmed", "approved");
    payment = secure(fund(payment));
    amount(0, read(payment, "/payment/completed"), "Hold and pending capture are not receipts");
    payment = invoke(payment, "", "guarantor", "completePayment", outcome("ordinary-capture"));
    payment = decide(payment, true, 1800L);
    var decision = identityAt(payment, ORDER + "/priceCorrection");

    expect("pending", read(payment, REQUESTS + automatic + "/status"), "Automatic refund awaits confirmation");
    amount(refund, read(payment, reserved), "Pending refund reserves its amount");
    payment = invoke(payment, "", "seller", "requestRefund", request(automatic, refund));
    amount(3, object(read(payment, "/payment/requests")).size(), "Identical request is idempotent");
    deny(payment, "seller", "requestRefund", request(automatic, refund - 1));
    deny(payment, "seller", "requestRefund", request(retry, refund));
    amount(0, read(payment, "/payment/reversed"), "Pending attempt proves no refund");

    payment = invoke(payment, "", "guarantor", "recordPaymentReversalUnknown",
        m("type", "PaymentInstruction/Payment Outcome Input", "requestId", automatic, "reason", "Provider timed out"));
    expect("unknown", read(payment, REQUESTS + automatic + "/status"), "Unknown attempt remains unresolved");
    amount(refund, read(payment, reserved), "Unknown attempt keeps its reservation");
    deny(payment, "seller", "requestRefund", request(retry, refund));
    // The reservation accounts for amounts. Independent use of remaining capacity stays available.
    payment = invoke(payment, "", "seller", "requestRefund", request("independent-refund", 100));
    amount(refund + 100, read(payment, reserved), "Independent request reserves only unused capacity");
    payment = invoke(payment, "", "guarantor", "failReverseAfterCompletion", failure("independent-refund"));
    amount(refund, read(payment, reserved), "Independent terminal failure releases only its reservation");

    payment = invoke(payment, "", "guarantor", "failReverseAfterCompletion", failure(automatic));
    var failedAttempt = read(payment, REQUESTS + automatic);
    expect("failed", read(payment, REQUESTS + automatic + "/status"), "Guarantor establishes terminal failure");
    amount(0, read(payment, reserved), "Terminal failure releases the first reservation");
    amount(0, read(payment, "/payment/reversed"), "Unknown and failed attempts leave confirmed net unchanged");
    payment = decide(payment, true, 1800L);
    absent(payment, REQUESTS + retry, "Replayed obligation never starts another attempt");
    expect(failedAttempt, read(payment, REQUESTS + automatic), "Replayed obligation retains the failed attempt");

    deny(payment, "customer", "requestRefund", request(retry, refund));
    payment = invoke(payment, "", "seller", "requestRefund", request(retry, refund));
    expect("pending", read(payment, REQUESTS + retry + "/status"), "Payee can start a new attempt after failure");
    expect(failedAttempt, read(payment, REQUESTS + automatic), "New attempt preserves original request and outcome");
    amount(refund, read(payment, reserved), "New attempt reserves once");
    payment = invoke(payment, "", "guarantor", "reverseAfterCompletion", outcome(retry));
    payment = invoke(payment, "", "guarantor", "reverseAfterCompletion", outcome(retry));
    payment = decide(payment, true, 1800L);
    expect(decision, identityAt(payment, ORDER + "/priceCorrection"), "Retry retains the accepted commercial decision");
    expect(failedAttempt, read(payment, REQUESTS + automatic), "Terminal first attempt remains auditable");
    expect("succeeded", read(payment, REQUESTS + retry + "/status"), "Separate attempt confirms success");
    amount(AMOUNT, read(payment, "/payment/completed"), "Original capture remains confirmed");
    amount(refund, read(payment, "/payment/reversed"), "Duplicate confirmation reverses only once");
    amount(0, read(payment, reserved), "Confirmed attempt releases its reservation");
    amount(5, object(read(payment, "/payment/requests")).size(), "Only declared and explicit attempts exist");
    System.out.println("PASS manual payee refund recovery after terminal failure: captured=7200 reversed=5400 net=1800");
  }

  private void pendingCapture() throws Exception {
    var payment = gates(select(payment("pending-capture", "both"), true), "confirmed", "approved");
    payment = secure(fund(payment));
    payment = invoke(payment, "", "guarantor", "recordPaymentCompletionUnknown",
        m("type", "PaymentInstruction/Payment Outcome Input", "requestId", "ordinary-capture",
            "reason", "Provider result unavailable"));
    payment = decide(payment, true, 0L);
    absent(payment, REQUESTS + "correction-refund", "Unknown capture must resolve before refund");
    absent(payment, REQUESTS + "correction-void", "Unknown capture must resolve before void");
    payment = invoke(payment, "", "guarantor", "completePayment", outcome("ordinary-capture"));
    amount(AMOUNT, read(payment, REQUESTS + "correction-refund/intent/amountMinor"), "Confirmed capture triggers whole refund");
    absent(payment, REQUESTS + "correction-void", "Terminal financial event observes the full capture transition");
    System.out.println("PASS unknown capture settles with full refund and no void");
  }

  private void heldAndMissingInputs() throws Exception {
    var payment = secure(fund(payment("held-payment", "both")));
    payment = decide(payment, true, 0L);
    absent(payment, REQUESTS + "correction-void", "A correction cannot act without a selection");
    payment = select(payment, false);
    absent(payment, REQUESTS + "correction-void", "Wrong prepared requirement stays ineligible");
    payment = decide(payment, true, 1000L);
    payment = select(payment, true);
    absent(payment, REQUESTS + "ordinary-capture", "Positive adjustment cannot charge an uncaptured hold");
    absent(payment, REQUESTS + "correction-void", "A positive target does not release a parked hold");
    payment = decide(payment, true, null);
    absent(payment, REQUESTS + "correction-void", "Missing target is distinct from zero");
    payment = decide(payment, true, 0L);
    amount(AMOUNT, read(payment, REQUESTS + "correction-void/intent/amountMinor"), "Zero target releases the entire hold");
    payment = invoke(payment, "", "guarantor", "cancelBeforeCompletion", outcome("correction-void"));
    payment = decide(payment, true, 0L);
    amount(0, read(payment, "/payment/secured"), "Provider confirmed release");
    amount(2, object(read(payment, "/payment/requests")).size(), "Void is stable under replay");
    System.out.println("PASS original selection, parked authorization, absent target and native whole void");
  }

  private void optionalVoidLeg() throws Exception {
    var refundOnly = secure(fund(select(payment("refund-only", "refund"), true)));
    refundOnly = decide(refundOnly, true, 0L);
    amount(1, object(read(refundOnly, "/payment/requests")).size(), "No configured void leg means no void");
    var voidOnly = secure(fund(payment("void-only", "void")));
    voidOnly = decide(voidOnly, true, null);
    absent(voidOnly, REQUESTS + "correction-void", "A declared void waits for attachment");
    voidOnly = select(voidOnly, true);
    amount(AMOUNT, read(voidOnly, REQUESTS + "correction-void/intent/amountMinor"), "Explicit literal zero supports void-only policy");
    absent(voidOnly, REQUESTS + "correction-refund", "Void-only never requests refund");
    System.out.println("PASS optional legs and explicit zero target");
  }

  private void reusedRequestId() throws Exception {
    var result = engine.initialize(paymentSource("duplicate-request-id", "conflict"));
    expect("FAILED", result.status(), "Two adjustment legs cannot share a native PI request ID");
    System.out.println("PASS reused native request ID fails configuration");
  }

  private Contracts.Document payment(String label, String legs) throws Exception {
    var source = paymentSource(label, legs);
    var result = engine.initialize(source);
    if (!result.commits()) ClauseGasProbe.diagnose(engine, source);
    return applied(result, "Payment Instruction");
  }

  private Map<String, Object> paymentSource(String label, String legs) throws Exception {
    var orderSource = load("order.blue");
    orderSource.put("name", "Original Order " + label);
    var order = applied(engine.initialize(orderSource), "original Order");
    engine.execution().chooseHistory(order.blueId(), engine.execution().snapshot(order));
    var source = CurrentOperationScenarios.read(fixtures.resolve("../financial/payment.blue"));
    source.put("name", "Payment " + label);
    source.put("sources", m("order", ref(order.blueId())));
    source.put("businessContext", m(
        "orderOrigin", ref(identityAt(order, "/contracts/initialized/document")),
        "orderRevision", read(order, "/activation/revision"),
        "orderTermsRef", read(order, "/activation/terms/ref")));
    var terms = object(source.get("paymentTerms"));
    terms.put("amountMinor", AMOUNT);
    terms.put("limitMinor", AMOUNT);
    var clauses = object(source.get("clauses"));
    clauses.remove("requests");
    var process = load("process.blue");
    var correction = object(object(object(process.get("parameters")).get("adjustments")).get("correction"));
    if (legs.equals("refund")) object(correction.get("requestIds")).remove("void");
    if (legs.equals("void")) {
      var decision = object(correction.get("decision"));
      decision.remove("retainMinorFrom");
      decision.put("retainMinor", 0);
      object(correction.get("requestIds")).remove("refund");
    }
    if (legs.equals("conflict")) object(correction.get("requestIds")).put("void", "correction-refund");
    clauses.put("payment", process);
    return source;
  }

  private Contracts.Document select(Contracts.Document payment, boolean exact) {
    String origin = identityAt(payment, "/contracts/initialized/document");
    var prepared = m("name", "Immutable payment requirement", "amountMinor", AMOUNT);
    var values = engine.execution().values();
    String keyId = NativeRuntime.identity(values.source("single"));
    var entry = m("key", "single", "requestId", "independent-attempt", "path", "/payment", "status", "selected",
        "candidateOrigin", origin, "documentOrigin", origin, "prepared", prepared,
        "requirementRef", NativeRuntime.identity(values.source(exact ? prepared : m("name", "Foreign requirement"))));
    return invoke(payment, ORDER, "owner", "select", m(
        "payment", m("contracts", m("initialized", m("document", ref(origin)))),
        "process", m("entries", m(keyId, entry))));
  }

  private Contracts.Document gates(Contracts.Document payment, String service, String review) {
    return invoke(payment, ORDER, "owner", "exerciseGates", m("serviceStatus", service, "ordinaryReview", review));
  }

  private Contracts.Document decide(Contracts.Document payment, boolean accept, Long target) {
    var decision = m("status", accept ? "accepted" : "pending");
    if (target != null) decision.put("retainedMinor", target);
    return invoke(payment, ORDER, "owner", "decide", decision);
  }

  private Contracts.Document fund(Contracts.Document payment) {
    payment = invoke(payment, "", "guarantor", "acceptPaymentInstruction", m());
    payment = invoke(payment, "", "guarantor", "recordTransactionInitiated", m(
        "type", "PaymentInstruction/Transaction Initiation Input", "transactionId", "fixture-transaction",
        "railType", "test", "attachmentPoint", "instruction", "providerReference", "fixture"));
    return invoke(payment, "", "guarantor", "authorize", request("hold", AMOUNT));
  }

  private Contracts.Document secure(Contracts.Document payment) {
    return invoke(payment, "", "guarantor", "secureFunds", outcome("hold"));
  }

  private Contracts.Document invoke(Contracts.Document payment, String target, String role, String operation, Object input) {
    String id = target.isEmpty() ? payment.blueId() : identityAt(payment, target);
    var event = m("source", role, "operation", m("type", "Contracts/Operation Request", "channel", role,
        "operation", operation, "document", ref(id), "request", input, "requireExactDocumentVersion", true));
    return applied(engine.process(payment, event, ++time), operation);
  }

  private void deny(Contracts.Document payment, String role, String operation, Object input) {
    var event = m("source", role, "operation", m("type", "Contracts/Operation Request", "channel", role,
        "operation", operation, "document", ref(payment.blueId()), "request", input, "requireExactDocumentVersion", true));
    var result = engine.process(payment, event, ++time);
    if (result.commits()) throw new AssertionError("Unexpectedly accepted " + operation + " from " + role + ": " + input);
  }

  private Contracts.Document applied(Contracts.Result result, String label) {
    if (!result.status().equals("APPLIED")) {
      throw new AssertionError(label + " " + result.status() + " " + WireData.write(ClauseGasProbe.diagnostic(result)));
    }
    return result.document();
  }

  private Map<String, Object> load(String file) throws Exception {
    return CurrentOperationScenarios.read(fixtures.resolve(file));
  }

  private Object read(Contracts.Document document, String path) {
    return engine.read(document, path);
  }

  private String identityAt(Contracts.Document document, String path) {
    var values = engine.execution().values();
    return NativeRuntime.identity(values.exact(values.select(new Exact.Ref(document.blueId()), path)));
  }

  private void absent(Contracts.Document document, String path, String reason) {
    expect(blue.bex.Values.UNDEFINED, read(document, path), reason);
  }

  private static void amount(long expected, Object actual, String label) {
    if (!(actual instanceof Number number) || number.longValue() != expected) {
      throw new AssertionError(label + " expected " + expected + ", got " + actual);
    }
  }

  private static void expect(Object expected, Object actual, String label) {
    if (!Objects.equals(expected, actual)) throw new AssertionError(label + " expected " + expected + ", got " + actual);
  }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> object(Object value) {
    return (Map<String, Object>) value;
  }

  private static Map<String, Object> outcome(String requestId) {
    return m("type", "PaymentInstruction/Payment Outcome Input", "requestId", requestId);
  }

  private static Map<String, Object> failure(String requestId) {
    return m("type", "PaymentInstruction/Payment Outcome Input", "requestId", requestId, "reason", "Provider rejected refund");
  }

  private static Map<String, Object> request(String requestId, long amount) {
    return m("type", "PaymentInstruction/Payment Request Input", "requestId", requestId, "amountMinor", amount);
  }

  private static Map<String, Object> ref(String blueId) {
    return m("blueId", blueId);
  }

  private static Map<String, Object> m(Object... fields) {
    var value = new LinkedHashMap<String, Object>();
    for (int i = 0; i < fields.length; i += 2) value.put((String) fields[i], fields[i + 1]);
    return value;
  }
}
