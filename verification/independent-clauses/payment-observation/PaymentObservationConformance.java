import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Native proof for a selected instruction and an independent same-price instruction.
 * Arguments are the exact catalogue directory and examples/preparation/13-current-payment-document.blue.
 */
public final class PaymentObservationConformance {
  private static final String SELECTED = "/instruction";
  private static final String FOREIGN = "/otherInstruction";
  private final Contracts processor;
  private final Path sample;
  private long timestamp;

  private PaymentObservationConformance(Contracts processor, Path sample) {
    this.processor = processor;
    this.sample = sample;
  }

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]).toAbsolutePath().normalize();
    var sample = Path.of(args[1]);
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var blue = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      new PaymentObservationConformance(runtime.processor(blue), sample).exercise();
    }
  }

  private void exercise() throws Exception {
    var noObserver = initialize(source(false));
    var observer = initialize(source(true));
    equal(processor.read(noObserver, "/contracts/embedded/paths"),
        processor.read(observer, "/contracts/embedded/paths"), "Opt-in embed:false contributes no managed path");
    equal(operations(noObserver), operations(observer), "Opt-in contributes no public operation");
    equal(processor.read(noObserver, "/activation/parties"), processor.read(observer, "/activation/parties"),
        "Opt-in grants no party authority");

    noObserver = apply(noObserver, "", "customer", "preparePayment", map()).document();
    var noObserverOutcome = secure(noObserver, SELECTED);
    equal(0, relays(noObserverOutcome).size(), "An unbound Payment Clause remains silent");

    observer = apply(observer, "", "customer", "preparePayment", map()).document();
    observer = apply(observer, "", "customer", "prepareOtherPayment", map()).document();
    String origin = identityAt(observer, SELECTED + "/contracts/initialized/document");
    String foreignOrigin = identityAt(observer, FOREIGN + "/contracts/initialized/document");
    require(!origin.equals(foreignOrigin), "Managed instructions must have distinct initialized identities");

    var foreignOutcome = secure(observer, FOREIGN);
    equal("200", String.valueOf(processor.read(foreignOutcome.document(), FOREIGN + "/payment/secured")),
        "The foreign instruction records its full native hold");
    equal(0, relays(foreignOutcome).size(), "A separate same-price instruction cannot impersonate the bound slot");
    var selectedOutcome = secure(foreignOutcome.document(), SELECTED);
    equal(origin, identityAt(selectedOutcome.document(), SELECTED + "/contracts/initialized/document"),
        "Native events retain the selected process identity");
    assertOneExactRelay(selectedOutcome, "instruction", SELECTED, "PaymentInstruction/Funds Secured");
    var resumed = apply(selectedOutcome.document(), "", "customer", "resumePayment", map());
    equal(0, relays(resumed).size(), "Resuming an already secured selection does not invent a historical relay");
    equal("200", String.valueOf(processor.read(resumed.document(), SELECTED + "/payment/secured")),
        "A consumer can read the current authoritative state directly");
    System.out.println("PASS opt-in selected PI, exact event identity, no added authority, same-price foreign PI ignored");

    var standalone = initialize(standaloneSource());
    var standaloneHold = secure(standalone, SELECTED);
    assertOneExactRelay(standaloneHold, "observer", SELECTED, "PaymentInstruction/Funds Secured");
    standalone = standaloneHold.document();
    standalone = apply(standalone, SELECTED, "customer", "requestCompletePayment",
        map("type", "PaymentInstruction/Payment Request Input", "requestId", "capture", "amountMinor", 200))
        .document();
    var original = operation(standalone, SELECTED, "guarantor", "completePayment",
        map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "capture", "amountCompleted", 200));
    long time = ++timestamp;
    var completion = processor.process(standalone, original, time);
    committed(completion, "capture outcome");
    assertOneExactRelay(completion, "observer", SELECTED, "PaymentInstruction/Payment Completed");
    var replay = processor.process(standalone, original, time);
    equal(completion.publicEvents(), replay.publicEvents(), "Replay recreates the same native event identities");
    equal(completion.document().identity(), replay.document().identity(), "Replay recreates the same state");
    var duplicate = processor.process(completion.document(), original, time);
    equal(0, relays(duplicate).size(), "The same exact request cannot add a relay to the advanced state");
    equal(processor.read(completion.document(), SELECTED + "/payment"),
        processor.read(duplicate.document(), SELECTED + "/payment"),
        "Replay on the advanced state leaves confirmed money and requests unchanged");
    System.out.println("PASS standalone automatic observer, authoritative catch-up and replay");
  }

  private Map<String, Object> source(boolean observe) throws Exception {
    var host = object(CompositionPackages.yaml(sample));
    var clauses = object(host.get("clauses"));
    clauses.remove("status");
    var roles = object(object(object(clauses.get("activation")).get("parameters")).get("parties"));
    var channels = new LinkedHashMap<String, Object>();
    roles.forEach((role, value) -> {
      var channel = map("type", "Contracts/External Channel", "event", map("source", role));
      channels.put(role, channel);
      object(value).put("lead", map("channel", channel));
      object(value).put("readerKeys", List.of("reader-" + role));
      object(value).put("myosAccountId", role);
    });
    host.put("contracts", channels);
    var first = object(clauses.get("instruction"));
    var template = object(object(first.get("parameters")).get("template"));
    var request = map("on", "workflow", "party", "customer",
        "request", map("type", "PaymentInstruction/Payment Request Input"),
        "params", map("$pointerSet", map("object", map("$object", map("$var", "trigger")),
            "path", "/type", "op", "remove")));
    object(template.get("clauses")).put("requests", map("type", "PaymentInstruction/Payment Request Actions",
        "bindings", map("requestAuthorize", map("requestSecureFunds", request),
            "requestCapture", map("requestCompletePayment", request))));
    var second = object(WireData.copy(first));
    object(object(second.get("parameters")).get("template")).put("name", "Separate instruction, same price");
    var secondBindings = object(second.get("bindings"));
    secondBindings.put("instruction", FOREIGN);
    var prepare = object(secondBindings.get("prepare"));
    prepare.put("prepareOtherPayment", prepare.remove("preparePayment"));
    secondBindings.remove("resume");
    clauses.put("other", second);
    if (observe) {
      object(first.get("bindings")).put("observe", map(
          "selected", map("on", "embedded", "path", SELECTED, "embed", false),
          "wrongPath", map("on", "embedded", "path", FOREIGN, "embed", false)));
    }
    return host;
  }

  private Map<String, Object> standaloneSource() throws Exception {
    var fixture = source(false);
    var clauses = object(fixture.get("clauses"));
    var payment = object(object(object(clauses.get("instruction")).get("parameters")).get("template"));
    payment.put("contracts", fixture.get("contracts"));
    object(payment.get("clauses")).put("activation", clauses.get("activation"));
    return map("type", "Agreements/Agreement with Clauses", "name", "Standalone instruction observer",
        "instruction", payment, "clauses", map("observer", map("type", "Payment/Payment Observation Clause",
            "bindings", map("instruction", SELECTED))));
  }

  private Contracts.Result secure(Contracts.Document host, String path) {
    host = apply(host, path, "guarantor", "acceptPaymentInstruction", map()).document();
    host = apply(host, path, "guarantor", "recordTransactionInitiated",
        map("type", "PaymentInstruction/Transaction Initiation Input", "transactionId", "rail-transaction",
            "railType", "test", "attachmentPoint", "instruction", "providerReference", "rail-test"))
        .document();
    host = apply(host, path, "customer", "requestSecureFunds",
        map("type", "PaymentInstruction/Payment Request Input", "requestId", "hold", "amountMinor", 200))
        .document();
    return apply(host, path, "guarantor", "secureFunds",
        map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "hold", "amountSecured", 200));
  }

  private void assertOneExactRelay(Contracts.Result result, String clause, String path, String eventType) {
    var values = processor.execution().values();
    var matcher = values.source(map("type", eventType), "definition");
    var observed = relays(result).stream().map(row -> new Exact.Ref(row.get("event").toString()))
        .filter(wrapper -> values.matches(values.select(wrapper, "/event"), matcher)).toList();
    equal(1, observed.size(), "One relay for the originating " + eventType);
    var wrapper = observed.getFirst();
    equal(clause, values.bexData(values.select(wrapper, "/clause")), "Wrapper identifies its own observing clause");
    equal(path, values.bexData(values.select(wrapper, "/instructionPath")), "Wrapper identifies the bound path");
    String original = NativeRuntime.identity(values.exact(values.select(wrapper, "/event")));
    var originalReceipts = (List<?>) result.observations().get("events");
    equal(1L, originalReceipts.stream().map(PaymentObservationConformance::object)
        .filter(row -> original.equals(row.get("event"))).count(),
        "The wrapper carries the exact originating event reference");
  }

  private List<Map<String, Object>> relays(Contracts.Result result) {
    var values = processor.execution().values();
    var matcher = values.source(map("type", "Payment/Payment Event Received"), "definition");
    return result.publicEvents().stream()
        .filter(row -> values.matches(new Exact.Ref(row.get("event").toString()), matcher)).toList();
  }

  private List<String> operations(Contracts.Document document) {
    var root = new Exact.Ref(document.blueId());
    var values = processor.execution().values();
    var matcher = values.source(map("type", "Contracts/Sequential Workflow Operation"), "definition");
    var names = processor.execution().declarations(root).keySet().stream()
        .filter(name -> values.matches(values.select(root, "/contracts/" + name), matcher)).sorted().toList();
    require(names.contains("preparePayment"), "The original public operation remains discoverable");
    return names;
  }

  private Contracts.Document initialize(Object source) {
    return committed(processor.initialize(source), "host initialization");
  }

  private Contracts.Result apply(Contracts.Document host, String path, String role, String op, Object input) {
    var event = operation(host, path, role, op, input);
    var result = processor.process(host, event, ++timestamp);
    if (!result.commits()) ClauseGasProbe.diagnose(processor, host, event, timestamp);
    committed(result, op);
    return result;
  }

  private Object operation(Contracts.Document host, String path, String role, String op, Object input) {
    String version = path.isEmpty() ? host.blueId() : identityAt(host, path);
    return map("source", role, "operation", map("type", "Contracts/Operation Request",
        "channel", role, "operation", op, "document", ref(version),
        "request", input, "requireExactDocumentVersion", true));
  }

  private Contracts.Document committed(Contracts.Result result, String label) {
    equal("APPLIED", result.status(), label + " " + ClauseGasProbe.diagnostic(result));
    return result.document();
  }

  private String identityAt(Contracts.Document document, String path) {
    var values = processor.execution().values();
    return NativeRuntime.identity(values.exact(values.select(new Exact.Ref(document.blueId()), path)));
  }

  private static Map<String, Object> ref(String id) {
    return map("blueId", id);
  }

  private static Map<String, Object> map(Object... pairs) {
    var result = new LinkedHashMap<String, Object>();
    for (int i = 0; i < pairs.length; i += 2) result.put((String) pairs[i], pairs[i + 1]);
    return result;
  }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> object(Object value) {
    return (Map<String, Object>) value;
  }

  private static void equal(Object expected, Object actual, String label) {
    require(java.util.Objects.equals(expected, actual), label + ": expected " + expected + ", got " + actual);
  }

  private static void require(boolean condition, String label) {
    if (!condition) throw new AssertionError(label);
  }
}
