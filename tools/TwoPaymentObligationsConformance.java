package blue.core;

import static blue.core.Values.*;

import blue.bex.Values;
import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Provisions and executes two independent obligations from application example 32. */
public final class TwoPaymentObligationsConformance {
  private static final int AMOUNT = 150;
  private static final String EXAMPLE = "examples/apps/32-current-two-payment-obligations.blue";
  private final Contracts processor;
  private long sequence;

  private TwoPaymentObligationsConformance(Contracts processor) {
    this.processor = processor;
  }

  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]).toAbsolutePath();
    Path fixture = Path.of(args.length > 1 ? args[1] : root.resolve(EXAMPLE).toString());
    var source = CurrentOperationScenarios.read(fixture);
    useProvidedInstructions(source);
    var packages = ClauseAppsExamples.packages(root, source);
    ClauseAppsExamples.wire(source);
    System.out.println("CATALOGUE " + WireData.sha256(Files.readAllBytes(root.resolve("PACKAGES.json"))));
    System.out.println("SOURCE " + WireData.sha256(Files.readAllBytes(fixture)));
    var executable = WireData.write(source).getBytes(StandardCharsets.UTF_8);
    System.out.println("EXECUTED_INPUT " + WireData.sha256(executable));
    if (args.length > 2) Files.write(Path.of(args[2]), executable);
    try (var blue = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      new TwoPaymentObligationsConformance(runtime.processor(blue)).prove(source);
    }
  }

  private static void useProvidedInstructions(Map<String,Object> source) {
    for (String obligation : List.of("deposit", "balance")) {
      var payment = obj(obj(source.get("clauses")).get(obligation));
      var parameters = obj(payment.get("parameters"));
      parameters.put("obtain", "provide");
      var template = obj(parameters.get("template"));
      obj(template.get("paymentTerms")).putAll(map("amountMinor", AMOUNT, "limitMinor", AMOUNT));
      obj(template.get("clauses")).put("requests", map(
          "type", "PaymentInstruction/Payment Request Actions",
          "bindings", map("requestAuthorize", request("authorize", "hold"),
              "requestCapture", request("capture", "capture"))));
      var provision = "provide" + Character.toUpperCase(obligation.charAt(0)) + obligation.substring(1);
      obj(payment.get("bindings")).put("provide", map(provision, map("on", "workflow", "party", "customer")));
    }
  }

  private static Object request(String action, String id) {
    return map(action, map("on", "workflow", "party", "customer",
        "params", map("requestId", id, "amountMinor", AMOUNT)));
  }

  private void prove(Map<String,Object> source) {
    var agreement = applied(processor.initialize(source));
    agreement = root(agreement, "customer", "prepareDeposit", map());
    agreement = root(agreement, "customer", "prepareBalance", map());
    var deposit = prepared(agreement, "deposit");
    var balance = prepared(agreement, "balance");
    require(!deposit.requirement().equals(balance.requirement()), "Separate prepared requirements");
    require(!deposit.document().blueId().equals(balance.document().blueId()), "Independently initialized instructions");
    for (var obligation : List.of(deposit, balance)) {
      expect(AMOUNT, processor.read(obligation.document(), "/paymentTerms/amountMinor"), "Equal fixture amounts");
      expect("EUR", processor.read(obligation.document(), "/paymentTerms/currency"), "Equal fixture currencies");
    }

    var wrong = operation(agreement.blueId(), "customer", "provideDeposit", deposit.provision(balance.document()));
    var rejected = processor.process(agreement, wrong, ++sequence);
    require(!rejected.commits(), "Balance instruction must not satisfy Deposit requirement");
    expect(agreement.identity(), rejected.document().identity(), "Rejected provision preserves agreement");
    expect(Values.UNDEFINED, processor.read(agreement, "/deposit"), "Deposit remains unattached after rejection");
    agreement = root(agreement, "customer", "provideDeposit", deposit.provision(deposit.document()));
    expect(Values.UNDEFINED, processor.read(agreement, "/balance"), "Deposit provision leaves Balance unattached");
    agreement = root(agreement, "customer", "provideBalance", balance.provision(balance.document()));
    String depositOrigin = embedded(deposit.document(), "/contracts/initialized/document");
    String balanceOrigin = embedded(balance.document(), "/contracts/initialized/document");
    expect(depositOrigin, embedded(agreement, "/deposit/contracts/initialized/document"),
        "Deposit keeps the supplied initialized origin");
    expect(balanceOrigin, embedded(agreement, "/balance/contracts/initialized/document"),
        "Balance keeps the supplied initialized origin");
    var balanceState = processor.read(agreement, "/balance/payment");
    expect("usable", entry(agreement, "deposit").get("status"), "Deposit admitted as usable");
    expect("usable", entry(agreement, "balance").get("status"), "Balance admitted as usable");
    System.out.println("PASS equal EUR obligations, distinct prepared refs, rejected substitute and exact admission of both PIs");

    agreement = depositCall(agreement, "guarantor", "acceptPaymentInstruction", map());
    agreement = depositCall(agreement, "guarantor", "recordTransactionInitiated", map(
        "type", "PaymentInstruction/Transaction Initiation Input", "transactionId", "deposit-transaction",
        "railType", "test", "attachmentPoint", "instruction", "providerReference", "test-deposit"));
    agreement = depositCall(agreement, "customer", "authorize", map());
    agreement = depositCall(agreement, "guarantor", "secureFunds", outcome("hold", "amountSecured"));
    agreement = depositCall(agreement, "customer", "capture", map());
    expect(0, processor.read(agreement, "/deposit/payment/completed"), "Capture request is pending until the guarantor result");
    var completed = outcome("capture", "amountCompleted");
    var completion = operation(embedded(agreement, "/deposit"), "guarantor", "completePayment", completed);
    long completionTime = ++sequence;
    var initial = processor.process(agreement, completion, completionTime);
    var replay = processor.process(agreement, completion, completionTime);
    expect(applied(initial).identity(), applied(replay).identity(), "Identical replay recreates the same result");
    expect(initial.publicEvents(), replay.publicEvents(), "Identical replay recreates the same event identities");
    agreement = initial.document();
    expect(AMOUNT, processor.read(agreement, "/deposit/payment/completed"), "Guarantor completed Deposit");
    expect(0, processor.read(agreement, "/balance/payment/completed"), "Balance remains unpaid");
    expect(balanceState, processor.read(agreement, "/balance/payment"), "Deposit completion leaves Balance state unchanged");
    expect(balanceOrigin, embedded(agreement, "/balance/contracts/initialized/document"), "Balance keeps its initialized origin");

    var repeat = operation(embedded(agreement, "/deposit"), "guarantor", "completePayment", completed);
    var duplicate = processor.process(agreement, repeat, ++sequence);
    var depositState = processor.read(agreement, "/deposit/payment");
    agreement = applied(duplicate);
    expect(depositState, processor.read(agreement, "/deposit/payment"),
        "Repeated completion preserves the entire Payment state");
    require(processor.emitted(duplicate).isEmpty(), "Duplicate completion emits no new effects");
    expect(balanceOrigin, embedded(agreement, "/balance/contracts/initialized/document"), "Repeated Deposit completion keeps Balance origin");
    expect(balanceState, processor.read(agreement, "/balance/payment"), "Repeated Deposit completion preserves Balance state");
    agreement = root(agreement, "customer", "provideBalance", balance.provision(balance.document()));
    expect(balanceOrigin, embedded(agreement, "/balance/contracts/initialized/document"), "Identical provision keeps the original Balance");
    expect(balanceState, processor.read(agreement, "/balance/payment"), "Identical provision preserves Balance state");
    expect(AMOUNT, processor.read(agreement, "/deposit/payment/completed"), "Unrelated provision replay cannot change Deposit");
    System.out.println("PASS authentic Contracts capture/result for Deposit only; duplicate admission and completion preserve both obligations");
  }

  private Map<String,Object> entry(Contracts.Document agreement, String obligation) {
    var entries = obj(processor.read(agreement, "/process_" + obligation + "/entries"));
    require(entries.size() == 1, "Exactly one preparation for " + obligation);
    return obj(entries.values().iterator().next());
  }

  private Prepared prepared(Contracts.Document agreement, String obligation) {
    var entry = entry(agreement, obligation);
    var values = processor.execution().values();
    var literal = values.literal(values.exact(values.select(new Exact.Ref(agreement.blueId()), entry.get("itemPath") + "/prepared")));
    return new Prepared(entry, applied(processor.initialize(literal)));
  }

  private record Prepared(Map<String,Object> entry, Contracts.Document document) {
    Object requirement() { return entry.get("requirementRef"); }
    Object provision(Contracts.Document candidate) {
      return map("type", "Documents/Provision Input", "key", entry.get("key"), "inResponseTo", entry.get("requestId"),
          "requirementRef", requirement(), "document", map("blueId", candidate.blueId()));
    }
  }

  private String embedded(Contracts.Document agreement, String path) {
    var values = processor.execution().values();
    return NativeRuntime.identity(values.exact(values.select(new Exact.Ref(agreement.blueId()), path)));
  }

  private static Object outcome(String id, String amountField) {
    return map("type", "PaymentInstruction/Payment Outcome Input", "requestId", id, amountField, AMOUNT);
  }

  private Contracts.Document depositCall(Contracts.Document agreement, String role, String name, Object request) {
    return call(agreement, embedded(agreement, "/deposit"), role, name, request);
  }

  private Contracts.Document root(Contracts.Document agreement, String role, String name, Object request) {
    return call(agreement, agreement.blueId(), role, name, request);
  }

  private Contracts.Document call(Contracts.Document agreement, String target, String role, String name, Object request) {
    var input = operation(target, role, name, request);
    var result = processor.process(agreement, input, ++sequence);
    if (!result.commits()) ClauseGasProbe.diagnose(processor, agreement, input, sequence);
    return applied(result);
  }

  private static Object operation(String target, String role, String name, Object request) {
    return map("source", role, "operation", map("type", "Contracts/Operation Request", "channel", role,
        "operation", name, "document", map("blueId", target), "request", request, "requireExactDocumentVersion", true));
  }

  private static Contracts.Document applied(Contracts.Result result) {
    require(result.commits(), "Operation must apply: " + result.status() + " " + result.observations());
    return result.document();
  }

  private static void expect(Object expected, Object actual, String detail) {
    boolean equal = expected instanceof Number a && actual instanceof Number b
        ? a.longValue() == b.longValue() : Objects.equals(expected, actual);
    require(equal, detail + " expected " + expected + ", got " + actual);
  }

  private static void require(boolean ok, String detail) {
    if (!ok) throw new AssertionError(detail);
  }
}
