package blue.core;

import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class ClockCompositionProof {
  private static final long SECURED = 36_000_000_000L;
  private static final long ATTACHED = 36_120_000_000L;
  private static final long APPROVED = 36_180_000_000L;
  private static final String CLOCK = "/clockStartMicros";
  private static final String FACT = "/securedTimestamp/timestampMicros";

  private final Contracts processor;
  private final Path packageRoot;
  private final Path fixtures;
  private final boolean exported;
  private final Map<String, Object> bindings;

  private ClockCompositionProof(Contracts processor, Path packageRoot, Path fixtures, boolean exported)
      throws Exception {
    this.processor = processor;
    this.packageRoot = packageRoot;
    this.fixtures = fixtures;
    this.exported = exported;
    this.bindings = CurrentOperationScenarios.read(fixtures.resolve("agreement-bindings.blue"));
  }

  public static void main(String[] args) throws Exception {
    var packageRoot = Path.of(args[0]);
    var packages = CompositionPackages.published(packageRoot, packageRoot.resolve("PACKAGES.json"));
    try (var blue = packages.language();
         var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var proof = new ClockCompositionProof(
          runtime.processor(blue), packageRoot, Path.of(args[1]),
          args.length > 2 && args[2].equals("--exported"));
      proof.live();
      proof.late();
      proof.merchant();
      if (proof.exported) {
        proof.activationWithAlreadySecuredSource();
        proof.invalidPrimary();
        proof.invalidFallback();
        proof.restoredReadiness();
        proof.invalidProfiles();
      }
    }
  }

  private void live() throws Exception {
    var payment = payment("live");
    var agreement = agreement("automatic", "live", "authorizationAttachment");
    missing(agreement, CLOCK);
    if (exported && !Boolean.TRUE.equals(processor.read(agreement, "/clockStartUnavailable"))) {
      throw new AssertionError("Initial activation without a native timestamp must admit fallback");
    }
    agreement = attach(agreement, payment, 20_000_000L);
    missing(agreement, CLOCK);
    agreement = secure(agreement, payment);
    number(agreement, "/monetarySource" + FACT, SECURED);
    number(agreement, CLOCK, SECURED);
    System.out.println("PASS live native embedded SECURE at " + SECURED);
  }

  private void late() throws Exception {
    var payment = secure(payment("late"));
    number(payment, FACT, SECURED);
    payment = call(payment, "guarantor", "secureFunds", outcome(), SECURED + 1);
    number(payment, FACT, SECURED);
    var agreement = agreement("automatic", "late", "authorizationEvent");
    missing(agreement, CLOCK);
    agreement = attach(agreement, payment, ATTACHED);
    number(agreement, "/monetarySource" + FACT, SECURED);
    number(agreement, CLOCK, SECURED);
    System.out.println("PASS real retained native publication attached at " + ATTACHED
        + " yields original SECURE " + SECURED);
  }

  private void merchant() throws Exception {
    var payment = secure(payment("merchant"));
    var agreement = agreement("merchant", "merchant", null);
    agreement = attach(agreement, payment, ATTACHED);
    number(agreement, "/monetarySource" + FACT, SECURED);
    missing(agreement, CLOCK);
    agreement = call(agreement, "merchant", "approve_merchant", m("revision", 1), APPROVED);
    number(agreement, CLOCK, APPROVED);
    System.out.println("PASS no clock while awaiting merchant, then native approval at " + APPROVED);
  }

  private void activationWithAlreadySecuredSource() throws Exception {
    var payment = secure(payment("priority"));
    var early = agreement("automatic", "already-attached", null, List.of("merchant"), null, null);
    early = attach(early, payment, ATTACHED);
    number(early, "/monetarySource" + FACT, SECURED);
    missing(early, CLOCK);
    missing(early, "/clockStartUnavailable");
    early = call(early, "merchant", "approve_merchant", m("revision", 1), APPROVED);
    number(early, CLOCK, APPROVED);

    var agreement = agreement(
        "automatic", "same-turn", null, List.of("merchant"), payment, null);
    missing(agreement, CLOCK);
    agreement = call(agreement, "merchant", "approve_merchant", m("revision", 1), APPROVED);
    missing(agreement, "/clockStartUnavailable");
    number(agreement, "/monetarySource" + FACT, SECURED);
    number(agreement, CLOCK, APPROVED);

    var later = agreement("automatic", "approval-first", null, List.of("merchant"), null, null);
    later = call(later, "merchant", "approve_merchant", m("revision", 1), APPROVED);
    number(later, CLOCK, APPROVED);
    later = attach(later, payment, APPROVED + 1);
    number(later, CLOCK, APPROVED);

    var initial = agreement("automatic", "already-secured-on-init", null, List.of(), payment, null);
    if (!Boolean.TRUE.equals(processor.read(initial, "/clockStartUnavailable"))) {
      throw new AssertionError("Actual initialization must attest the missing primary timestamp");
    }
    number(initial, "/monetarySource" + FACT, SECURED);
    number(initial, CLOCK, SECURED);
    System.out.println("PASS 10:00 fallback observed before, during, or after activation yields 10:03 primary;"
        + " initialization without entry time catches up to 10:00");
  }

  private void invalidPrimary() throws Exception {
    var payment = secure(payment("invalid-primary"));
    var agreement = agreement("automatic", "invalid-primary", null, List.of("merchant"), null, null);
    agreement = call(agreement, "merchant", "approve_merchant", m("revision", 1), 0);
    missing(agreement, CLOCK);
    missing(agreement, "/clockStartUnavailable");
    agreement = attach(agreement, payment, ATTACHED);
    number(agreement, "/monetarySource" + FACT, SECURED);
    missing(agreement, CLOCK);
    missing(agreement, "/clockStartUnavailable");
    System.out.println("PASS invalid zero primary does not attest absence or admit fallback");
  }

  private void invalidFallback() throws Exception {
    for (Object invalid : List.of(0, -1, "36000000000")) {
      var source = applied(processor.initialize(m("name", "Invalid fallback " + invalid,
          "securedTimestamp", m("timestampMicros", invalid))), "untrusted timestamp fixture");
      var agreement = agreement("automatic", "invalid-fallback-" + invalid, null);
      agreement = attach(agreement, source, ATTACHED);
      if (!Boolean.TRUE.equals(processor.read(agreement, "/clockStartUnavailable"))) {
        throw new AssertionError("Missing primary must be established before validating fallback");
      }
      missing(agreement, CLOCK);
    }
    System.out.println("PASS absent primary does not permit zero, negative, or text fallback");
  }

  private void restoredReadiness() throws Exception {
    var payment = secure(payment("readiness"));
    var source = agreementSource("automatic", "restored-readiness", null, List.of(), null, null);
    var clock = object(object(source.get("clauses")).get("clock"));
    object(clock.get("bindings")).put("sourceReady", "/fixtureSourceReady");
    source.put("fixtureSourceReady", false);
    object(source.get("contracts")).put("fixtureAccessRestored", m(
        "type", "Contracts/Sequential Workflow Operation", "channel", "merchant",
        "steps", List.of(m("type", "Contracts/Compute", "do", List.of(
            m("$appendChange", m("op", "replace", "path", "/fixtureSourceReady", "val",
                m("$binding", "call/request/ready"))),
            m("$appendEvent", m("type", "Parties/Document Access Restored", "revision", 1)))))));
    var agreement = applied(processor.initialize(source), "readiness fixture");
    agreement = attach(agreement, payment, ATTACHED);
    number(agreement, "/monetarySource" + FACT, SECURED);
    missing(agreement, CLOCK);
    agreement = call(agreement, "merchant", "fixtureAccessRestored", m("ready", false), APPROVED);
    missing(agreement, CLOCK);
    agreement = call(agreement, "merchant", "fixtureAccessRestored", m("ready", true), APPROVED + 1);
    number(agreement, CLOCK, SECURED);
    agreement = call(agreement, "merchant", "fixtureAccessRestored", m("ready", true), APPROVED + 2);
    number(agreement, CLOCK, SECURED);
    System.out.println("PASS restoration requires declared source readiness and catches up once to original 10:00");
  }

  private void invalidProfiles() throws Exception {
    expectProfileRejection("CONNECTION_PROFILE_UNKNOWN", m("profile", "missing"));
    expectProfileRejection("CONNECTION_PROFILE_LOCAL_CONFLICT", m("profile", "first", "when", true));
    System.out.println("PASS unknown named profiles and conflicting local guards are rejected");
  }

  private void expectProfileRejection(String expected, Map<String, Object> profile) throws Exception {
    var source = agreementSource("merchant", expected, null, List.of("merchant"), null, profile);
    var result = processor.initialize(source);
    var diagnostic = WireData.write(ClauseGasProbe.diagnostic(result)) + processor.emitted(result);
    if (!"FAILED".equals(result.status()) || !diagnostic.contains("BEX_EXECUTION_REJECTED")) {
      throw new AssertionError("Expected " + expected + ", got " + result.status() + " " + diagnostic);
    }
  }

  private Contracts.Document payment(String key) throws Exception {
    var source = CurrentOperationScenarios.read(packageRoot.resolve("examples/apps/27-payment-protocol.blue"));
    source.put("instanceKey", "clock-proof-" + key);
    object(source.get("clauses")).put("timestamp", m(
        "type", exported ? "Payment/Secure Timestamp Projection"
            : CurrentOperationScenarios.read(fixtures.resolve("secure-timestamp.blue")),
        "bindings", bindings.get("producer")));
    ClauseAppsExamples.wire(source);
    var payment = applied(processor.initialize(source), "stock Payment Instruction initialization");
    List<String> channels = List.of("customer", "seller", "seller2", "guarantor");
    for (int i = 0; i < channels.size(); i++) {
      String channel = channels.get(i);
      payment = call(payment, channel, "approve_" + channel, m("revision", 1), 1_000_000L + i);
    }
    payment = call(payment, "guarantor", "acceptPaymentInstruction", m(), 2_000_000L);
    payment = call(payment, "guarantor", "recordTransactionInitiated", m(
        "type", "PaymentInstruction/Transaction Initiation Input", "transactionId", "transaction-" + key,
        "railType", "test", "attachmentPoint", "instruction", "providerReference", "provider-1"), 3_000_000L);
    payment = call(payment, "customer", "requestSecureFunds", m(
        "type", "PaymentInstruction/Payment Request Input", "requestId", "full", "amount", 10_000), 4_000_000L);
    missing(payment, FACT);
    return payment;
  }

  private Contracts.Document agreement(String mode, String key, String omitConnection) throws Exception {
    return agreement(mode, key, omitConnection, mode.equals("automatic") ? List.of() : List.of("merchant"), null, null);
  }

  private Contracts.Document agreement(
      String mode, String key, String omitConnection, List<String> required,
      Contracts.Document attachOnActivation, Map<String, Object> invalidProfile) throws Exception {
    return applied(processor.initialize(
        agreementSource(mode, key, omitConnection, required, attachOnActivation, invalidProfile)),
        "clock agreement initialization");
  }

  private Map<String, Object> agreementSource(
      String mode, String key, String omitConnection, List<String> required,
      Contracts.Document attachOnActivation, Map<String, Object> invalidProfile) throws Exception {
    var channel = m("type", "Contracts/External Channel", "event", m("source", "merchant"));
    var activation = m("type", "Activation/Activation Clause", "parameters", m(
        "parties", m("merchant", m("type", "Parties/Party", "lead", m("channel", channel))),
        "required", required,
        "preActivationOperations", List.of("attachFixtureSource")));
    // The fixture operation connects the actual immutable producer publication.
    // It models selection by the agreement rather than a checkout admission policy.
    var attach = m("type", "Contracts/Sequential Workflow Operation", "channel", "merchant",
        "steps", List.of(m("type", "Contracts/Update Document", "changeset",
            List.of(m("op", "add", "path", "/monetarySource",
                "val", m("$binding", "call/request/source"))))));
    var configured = exported && mode.equals("automatic")
        ? CurrentOperationScenarios.read(fixtures.resolve("exported-automatic-bindings.blue"))
        : m("bindings", bindings.get(mode));
    var modeBindings = new LinkedHashMap<>(object(configured.get("bindings")));
    if (omitConnection != null) {
      String action = modeBindings.containsKey("startFromFallback") ? "startFromFallback" : "startAt";
      var connected = new LinkedHashMap<>(object(modeBindings.get(action)));
      connected.remove(omitConnection);
      modeBindings.put(action, connected);
    }
    if (modeBindings.containsKey("startFromFallback")) {
      var fallback = object(modeBindings.get("startFromFallback"));
      var preActivationChannels = List.of("authorizationAttachment", "authorizationEvent").stream()
          .filter(fallback::containsKey)
          .map(name -> "cx.clock.startFromFallback." + name + "_source").toList();
      object(activation.get("parameters")).put("preActivationChannels", preActivationChannels);
    }
    if (invalidProfile != null) {
      var startAt = new LinkedHashMap<>(object(modeBindings.get("startAt")));
      var approval = new LinkedHashMap<>(object(startAt.get("approval")));
      approval.putAll(invalidProfile);
      startAt.put("approval", approval);
      modeBindings.put("startAt", startAt);
    }
    var clock = m(
        "type", exported ? "Connections/Remember First Timestamp"
            : CurrentOperationScenarios.read(fixtures.resolve("start-clock.blue")),
        "bindings", modeBindings);
    if (configured.containsKey("parameters")) clock.put("parameters", configured.get("parameters"));
    if (invalidProfile != null) clock.put("parameters", m("connectionProfiles", m(
        "first", m("params", m("timestampMicros", 1234)))));
    var source = m("name", "Fixture clock " + key, "type", "Agreements/Agreement with Clauses",
        "contracts", m("merchant", channel, "attachFixtureSource", attach),
        "clauses", m("activation", activation, "clock", clock));
    if (attachOnActivation != null) {
      processor.execution().chooseHistory(attachOnActivation.blueId(), processor.execution().snapshot(attachOnActivation));
      source.put("fixtureSource", m("blueId", attachOnActivation.blueId()));
      object(source.get("clauses")).put("attach", m(
          "type", m("name", "Fixture Attachment", "type", "Connections/Connected Clause",
              "actions", m("attach", m("do", List.of(m("$appendChange", m(
                  "op", "add", "path", "/monetarySource", "val", m("$document", "/fixtureSource"))))))),
          "bindings", m("attach", m("onActivation", m("on", "activated")))));
    }
    return source;
  }

  private Contracts.Document attach(Contracts.Document agreement, Contracts.Document payment, long time) {
    processor.execution().chooseHistory(payment.blueId(), processor.execution().snapshot(payment));
    return call(agreement, "merchant", "attachFixtureSource", m("source", m("blueId", payment.blueId())), time);
  }

  private Contracts.Document secure(Contracts.Document payment) {
    return secure(payment, payment);
  }

  private Contracts.Document secure(Contracts.Document receiver, Contracts.Document payment) {
    var after = applied(
        processor.process(receiver, entry(payment, "guarantor", "secureFunds", outcome()), SECURED),
        "native secureFunds");
    String paymentPath = receiver == payment ? "" : "/monetarySource";
    if (!"succeeded".equals(processor.read(after, paymentPath + "/payment/requests/full/status"))) {
      throw new AssertionError("Expected committed full SECURE response from the stock instruction");
    }
    number(after, paymentPath + FACT, SECURED);
    return after;
  }

  private static Map<String, Object> outcome() {
    return m("type", "PaymentInstruction/Payment Outcome Input", "requestId", "full");
  }

  private Contracts.Document call(
      Contracts.Document document, String channel, String operation, Object request, long time) {
    return applied(processor.process(document, entry(document, channel, operation, request), time), operation);
  }

  private static Map<String, Object> entry(
      Contracts.Document target, String channel, String operation, Object request) {
    return m("source", channel, "operation", m(
        "type", "Contracts/Operation Request", "channel", channel, "operation", operation,
        "document", m("blueId", target.blueId()), "requireExactDocumentVersion", true, "request", request));
  }

  private Contracts.Document applied(Contracts.Result result, String context) {
    if (!result.status().equals("APPLIED")) {
      throw new AssertionError(context + " " + result.status() + " "
          + WireData.write(ClauseGasProbe.diagnostic(result)) + " " + processor.emitted(result));
    }
    return result.document();
  }

  private void number(Contracts.Document document, String path, long expected) {
    Object value = processor.read(document, path);
    if (!(value instanceof Number number) || number.longValue() != expected) {
      throw new AssertionError(path + " expected " + expected + ", got " + value);
    }
  }

  private void missing(Contracts.Document document, String path) {
    Object value = processor.read(document, path);
    if (value != null && value != blue.bex.Values.UNDEFINED) {
      throw new AssertionError(path + " must be absent, got " + value);
    }
  }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> object(Object value) {
    return (Map<String, Object>) value;
  }

  private static Map<String, Object> m(Object... entries) {
    var map = new LinkedHashMap<String, Object>();
    for (int i = 0; i < entries.length; i += 2) map.put((String) entries[i], entries[i + 1]);
    return map;
  }
}
