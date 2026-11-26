import static blue.bex.Values.UNDEFINED;
import static blue.bex.Values.escape;

import blue.bex.BexError;
import blue.contracts.ClauseGasProbe;
import blue.contracts.ContractException;
import blue.contracts.Contracts;
import blue.contracts.RuntimeBindings;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/** Native attachment, observation and ledger dispatch with modeled cumulative Payment Instruction state. */
public final class DeclarativeReceiptsConformance {
  private final Contracts processor;
  private final String ordersPath;
  private final String entriesPath;
  private final String receiptPath;
  private final String instructionPath;
  private final boolean withCommission;
  private Contracts.Document agreement;
  private int sequence;

  private DeclarativeReceiptsConformance(Contracts processor, boolean alternatePaths, boolean withCommission,
      boolean withInstruction) {
    this(processor, alternatePaths, withCommission, withInstruction, false);
  }

  private DeclarativeReceiptsConformance(Contracts processor, boolean alternatePaths, boolean withCommission,
      boolean withInstruction, boolean frozenRates) {
    this(processor, alternatePaths, withCommission, withInstruction, frozenRates, false);
  }

  private DeclarativeReceiptsConformance(Contracts processor, boolean alternatePaths, boolean withCommission,
      boolean withInstruction, boolean frozenRates, boolean differentCurrency) {
    this(processor, alternatePaths, withCommission, withInstruction, frozenRates, differentCurrency, false);
  }

  private DeclarativeReceiptsConformance(Contracts processor, boolean alternatePaths, boolean withCommission,
      boolean withInstruction, boolean frozenRates, boolean differentCurrency, boolean reconcile) {
    this.processor = processor;
    this.withCommission = withCommission;
    ordersPath = alternatePaths ? "/purchases" : "/orders";
    receiptPath = alternatePaths ? "/saleReceipts" : "/receipts";
    instructionPath = alternatePaths ? "/checkout" : "/payment";
    String producer = alternatePaths ? "purchases" : "orders";
    entriesPath = "/process_" + producer + "/entries";
    var source = BootstrapPreparationConformance.source(null);
    var clauses = object(source.get("clauses"));
    var orders = object(clauses.get("orders"));
    if (!producer.equals("orders")) {
      clauses.remove("orders");
      clauses.put(producer, orders);
    }
    object(orders.get("bindings")).put("collection", ordersPath);
    var parameters = object(orders.get("parameters"));
    parameters.put("suppliedParties", List.of());
    var template = object(parameters.get("template"));
    var templateClauses = object(template.get("clauses"));
    var activation = object(object(templateClauses.get("activation")).get("parameters"));
    object(activation.get("parties")).remove("customer");
    activation.put("required", List.of("seller"));
    if (withInstruction) {
      template.put(instructionPath.substring(1), map("type", "PaymentInstruction/Payment Instruction",
          "paymentTerms", map("currency", differentCurrency ? "EUR" : "USD"),
          "payment", map("completed", frozenRates ? 0 : 10000, "reversed", frozenRates ? 0 : 2500)));
      templateClauses.put("modeledPaymentEvent", paymentEmitter(instructionPath));
    }
    if (differentCurrency) {
      source.put("terms", map("currency", "USD"));
    }
    if (frozenRates) {
      var domainPrepare = map("args", map("prepared", map()), "do", List.of(
          map("$return", map("commissionTerms", map("$document", "/testCommissionTerms")))));
      orders.put("type", map("type", "Documents/Documents Clause", "actionDefinition", map("type",
          map("type", "Documents/Document Preparation Functions", "functions", map("domainPrepare", domainPrepare)))));
      var change = map("$appendChange", map("op", "replace", "path", "/testCommissionTerms",
          "val", map("$var", "params")));
      var termsDefinition = map("type", "Connections/Connected Clause", "actions",
          map("change", map("do", List.of(change))));
      var termsBinding = map("on", "workflow", "party", "merchant",
          "params", map("$object", map("$var", "trigger")));
      clauses.put("modeledCommissionChange", map("type", termsDefinition,
          "bindings", map("change", map("changeCommissionForTest", termsBinding))));
      source.put("testCommissionTerms", map("revision", 1, "commissionBps", 1000));
    }
    if (reconcile) {
      template.remove(instructionPath.substring(1));
      templateClauses.put("modeledPaymentEvent", restoreOutcomeEmitter(instructionPath));
      // Model the missed receipt deliveries locally. The signed ACL fixture
      // separately verifies the genuine access suspension/restoration.
      var restore = map("type", map("type", "Connections/Connected Clause", "actions",
          map("restored", map("do", List.of(map("$appendEvent",
              map("type", "Parties/Document Access Restored", "revision", 1)))))),
          "bindings", map("restored", map("restoreForTest", map("on", "workflow", "party", "merchant"))));
      clauses.put("modeledAccessSignal", restore);
    }
    source.put(ordersPath.substring(1), map());
    var projection = map("type", "Payment/Receipts Clause");
    if (alternatePaths) {
      projection.put("bindings", map("orders", ordersPath, "instruction", instructionPath,
          "state", receiptPath, "entries", entriesPath));
    }
    if (reconcile) {
      object(projection.computeIfAbsent("bindings", ignored -> map())).put("reconcile", map("afterAccessRestored",
          map("on", "event", "event", map("type", "Parties/Document Access Restored"))));
    }
    clauses.put("receiptProjection", projection);
    if (withCommission) {
      if (!frozenRates) {
        var fields = map("commissionBps", "/terms/commissionBps");
        parameters.put("privateTerms", map("commissionTerms", map("fields", fields)));
      }
      source.put("payouts", map());
      source.put("terms", map("currency", "USD", "commissionBps", 1200));
      var workflow = map("on", "workflow", "party", "merchant", "params", map("$object", map("$var", "trigger")));
      var commission = map("type", "Ledger/Ledger Clause", "bindings", map(
          "state", "/commission", "receipts", receiptPath, "orders", ordersPath, "orderEntries", entriesPath,
          "frozenRate", "/domainTerms/commissionTerms/commissionBps",
          "accruePercent", map("accrue", map("on", "event", "event",
              map("type", "Events/Event", "kind", "Confirmed Receipts Changed"))),
          "reserve", map("reserveForTest", workflow), "settle", map("settleForTest", workflow)));
      clauses.put("commission", commission);
    }
    try {
      agreement = applied(processor.initialize(source));
    } catch (ContractException failed) {
      throw new AssertionError(failed.diagnosticPath() + " " + failed.context(), failed);
    }
    operation("approve_merchant", map("revision", 1));
  }

  private static Map<String, Object> paymentEmitter(String instructionPath) {
    var completed = map("$var", map("name", "params", "path", "/completed"));
    var reversed = map("$var", map("name", "params", "path", "/reversed"));
    var capture = map("$var", map("name", "params", "path", "/capture"));
    var event = map("$choose", map("cond", capture,
        "then", map("type", "PaymentInstruction/Payment Completed", "requestId", "capture", "amountCompleted", 2000),
        "else", map("type", "PaymentInstruction/Payment Reversed After Completion",
            "requestId", "refund", "amountReversed", 2000)));
    var steps = List.of(
        map("$appendChange", map("op", "replace", "path", instructionPath + "/payment/completed", "val", completed)),
        map("$appendChange", map("op", "replace", "path", instructionPath + "/payment/reversed", "val", reversed)),
        map("$appendEvent", map("type", "Payment/Payment Event Received", "kind", "test outcome",
            "clause", "payment", "instructionPath", instructionPath, "event", event)));
    var definition = map("type", "Connections/Connected Clause", "actions", map("settle", map("do", steps)));
    var connection = map("on", "workflow", "party", "seller", "params", map("$object", map("$var", "trigger")));
    return map("type", definition, "bindings", map("settle", map("testSettle", connection)));
  }

  private static Map<String, Object> restoreOutcomeEmitter(String instructionPath) {
    var completed = map("$var", map("name", "params", "path", "/completed"));
    var reversed = map("$var", map("name", "params", "path", "/reversed"));
    var path = map("$choose", map("cond", map("$var", map("name", "params", "path", "/foreign")),
        "then", "/foreignPayment", "else", instructionPath));
    var instruction = map("$merge", List.of(map("type", "PaymentInstruction/Payment Instruction"),
        map("paymentTerms", map("currency", "USD"), "payment", map("completed", completed, "reversed", reversed))));
    var steps = List.of(
        map("$appendChange", map("op", "add", "path", path, "val", instruction)),
        map("$if", map("cond", map("$var", map("name", "params", "path", "/pause")),
            "then", List.of(map("$appendChange", map("op", "replace", "path", "/activation/active", "val", false))))),
        map("$if", map("cond", map("$var", map("name", "params", "path", "/relay")),
            "then", List.of(map("$appendEvent", map("type", "Payment/Payment Event Received", "kind", "test outcome",
                "clause", "payment", "instructionPath", instructionPath, "event",
                map("type", "PaymentInstruction/Payment Completed", "requestId", "capture", "amountCompleted", 7200)))))));
    var definition = map("type", "Connections/Connected Clause", "actions", map("settle", map("do", steps)));
    var connection = map("on", "workflow", "party", "seller", "params", map("$object", map("$var", "trigger")));
    return map("type", definition, "bindings", map("settle", map("testSettle", connection)));
  }

  private void exerciseRestore(int additionalOrders) {
    attach("prior");
    attach("first/capture");
    attach("foreign");
    attach("paused");
    modeledOutcome("prior", 7200, 0, true, false, false);
    receipt("", 7200, 0, 7200);
    checkAmount("/commission/targets/prior", 864);
    modeledOutcome("prior", 7200, 5400, false, false, false);
    modeledOutcome("first/capture", 7200, 0, false, false, false);
    modeledOutcome("foreign", 7200, 0, false, true, false);
    modeledOutcome("paused", 7200, 0, false, false, true);
    for (int i = 0; i < additionalOrders; i++) {
      String key = "unreported-" + i;
      attach(key);
      modeledOutcome(key, 7200, 0, false, false, false);
    }
    receipt("", 7200, 0, 7200);
    var restored = operation("restoreForTest", map());
    long gross = (2L + additionalOrders) * 7200;
    receipt("", gross, 5400, gross - 5400);
    receipt("/targets/prior", 7200, 5400, 1800);
    receipt("/targets/first~1capture", 7200, 0, 7200);
    assertRestoredCommission(additionalOrders);
    require(processor.read(agreement, receiptPath + "/targets/paused") == UNDEFINED,
        "A stale usable entry must not count the inactive Order");
    require(processor.read(agreement, receiptPath + "/targets/foreign") == UNDEFINED,
        "Only the configured PI path can supply receipts");
    long changed = receiptChanges(restored);
    require(changed == 2 + additionalOrders, "One event per changed order target, got " + changed);
    var repeated = operation("restoreForTest", map());
    require(receiptChanges(repeated) == 0, "Recovery of unchanged cumulative outcomes must emit no new receipt change");
    receipt("", gross, 5400, gross - 5400);
    assertRestoredCommission(additionalOrders);
    System.out.printf("PASS modeled missed receipt deliveries, scoped native reconciliation and replay. "
            + "Entries=%d changed=%d gas=%d unchangedGas=%d%n",
        4 + additionalOrders, changed, restored.gas(), repeated.gas());
  }

  private void assertRestoredCommission(int additionalOrders) {
    checkAmount("/commission/targets/prior", 216);
    checkAmount("/commission/targets/first%2Fcapture", 864);
    for (int i = 0; i < additionalOrders; i++) {
      checkAmount("/commission/targets/unreported-" + i, 864);
    }
    checkAmount("/commission/accrued", 216L + (1L + additionalOrders) * 864L);
  }

  private void modeledOutcome(String key, int completed, int reversed, boolean relay, boolean foreign, boolean pause) {
    var values = processor.execution().values();
    var order = values.exact(values.select(new Exact.Ref(agreement.blueId()), ordersPath + "/" + escape(key)));
    var input = childOperation(NativeRuntime.identity(order), "testSettle",
        map("completed", completed, "reversed", reversed, "relay", relay, "foreign", foreign, "pause", pause));
    agreement = applied(processor.process(agreement, input, ++sequence));
  }

  private long receiptChanges(Contracts.Result result) {
    return ClauseGasProbe.eventData(processor, result).stream().filter(data -> data instanceof Map<?, ?> event
        && "Confirmed Receipts Changed".equals(event.get("kind"))).count();
  }

  private void attach(String key) {
    var request = prepareProvision(key);
    operation("provideOrder", request);
    operation("provideOrder", request);
  }

  private Map<String, Object> prepareProvision(String key) {
    operation("prepareOrder", map("type", "Documents/Preparation Input", "key", key, "values", map("size", 42)));
    var item = object(object(processor.read(agreement, entriesPath)).values().stream()
        .filter(raw -> key.equals(object(raw).get("key"))).findFirst().orElseThrow());
    var values = processor.execution().values();
    var prepared = values.literal(values.exact(values.select(new Exact.Ref(agreement.blueId()), item.get("itemPath") + "/prepared")));
    var order = applied(processor.initialize(prepared));
    order = applied(processor.process(order, childOperation(order.blueId(), "approve_seller", map("revision", 1)), ++sequence));
    return map("type", "Documents/Provision Input", "key", key, "inResponseTo", item.get("requestId"),
        "requirementRef", item.get("requirementRef"), "document", map("blueId", order.blueId()));
  }

  private void rejectDifferentCurrency() {
    var request = prepareProvision("other-currency");
    var input = BootstrapPreparationConformance.event(agreement, "provideOrder", request);
    var result = processor.process(agreement, input, ++sequence);
    require(!result.commits(), "A different payment currency must not update a shared receipt total");
    try {
      ClauseGasProbe.diagnose(processor, agreement, input, sequence);
      throw new AssertionError("Expected a receipt currency failure");
    } catch (BexError failure) {
      require("RECEIPT_CURRENCY_MISMATCH".equals(failure.getMessage()),
          "A mixed-currency receipt gave " + failure.getMessage());
    }
    require(processor.read(result.document(), receiptPath + "/targets/other-currency") == UNDEFINED,
        "Different currency has no recorded target");
  }

  private void reportPayment(String key, int completed, int reversed, boolean capture) {
    var values = processor.execution().values();
    var order = values.exact(values.select(new Exact.Ref(agreement.blueId()), ordersPath + "/" + escape(key)));
    var operation = childOperation(NativeRuntime.identity(order), "testSettle",
        map("completed", completed, "reversed", reversed, "capture", capture));
    agreement = applied(processor.process(agreement, operation, ++sequence));
  }

  private Contracts.Result operation(String name, Map<String, Object> request) {
    var input = BootstrapPreparationConformance.event(agreement, name, request);
    var result = processor.process(agreement, input, ++sequence);
    if (!result.commits()) {
      ClauseGasProbe.diagnose(processor, agreement, input, sequence);
    }
    agreement = applied(result);
    return result;
  }

  private static Object childOperation(String document, String name, Map<String, Object> request) {
    return map("source", "merchant", "operation", map("type", "Contracts/Operation Request", "channel", "seller",
        "operation", name, "document", map("blueId", document), "requireExactDocumentVersion", true, "request", request));
  }

  private void receipt(String suffix, long gross, long refunded, long net) {
    checkAmount(receiptPath + suffix + "/grossConfirmedMinor", gross);
    checkAmount(receiptPath + suffix + "/refundsMinor", refunded);
    checkAmount(receiptPath + suffix + "/netReceivedMinor", net);
    if (withCommission && suffix.isEmpty()) {
      var targets = object(processor.read(agreement, receiptPath + "/targets"));
      long expectedCommission = targets.values().stream()
          .mapToLong(raw -> roundBps(((Number) object(raw).get("netReceivedMinor")).longValue(), 1200))
          .sum();
      checkAmount("/commission/accrued", expectedCommission);
    }
  }

  private static long roundBps(long amountMinor, int basisPoints) {
    return Math.floorDiv(amountMinor * basisPoints + 5000L, 10000L);
  }

  private void checkAmount(String path, long expected) {
    var actual = processor.read(agreement, path);
    require(actual instanceof Number number && number.longValue() == expected,
        path + " expected " + expected + ", received " + actual);
  }

  private List<Object> receiptAmountMetadata() {
    var values = processor.execution().values();
    var type = values.select(new Exact.Ref(agreement.blueId()), receiptPath + "/type");
    return List.of(NativeRuntime.identity(values.exact(type)),
        receiptFieldMetadata("grossConfirmedMinor", "Confirmed Customer Captures"),
        receiptFieldMetadata("refundsMinor", "Confirmed Customer Refunds"),
        receiptFieldMetadata("netReceivedMinor", "Net Customer Receipts"));
  }

  private List<Object> receiptFieldMetadata(String field, String expectedName) {
    var path = receiptPath + "/" + field;
    var name = processor.read(agreement, path + "/name");
    var description = processor.read(agreement, path + "/description");
    require(expectedName.equals(name) && description instanceof String text && !text.isBlank(),
        path + " must expose its native name and description");
    return List.of(name, description);
  }

  private static Contracts.Document applied(Contracts.Result result) {
    return BootstrapPreparationConformance.applied(result).document();
  }

  private static Map<String, Object> map(Object... pairs) {
    return BootstrapPreparationConformance.m(pairs);
  }

  private static Map<String, Object> object(Object value) {
    return BootstrapPreparationConformance.obj(value);
  }

  private static void require(boolean condition, String message) {
    BootstrapPreparationConformance.require(condition, message);
  }

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]);
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var blue = packages.language();
         var runtime = new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var processor = runtime.processor(blue);
      if (args.length >= 2 && args[1].equals("--restore")) {
        var restore = new DeclarativeReceiptsConformance(processor, false, true, true, false, false, true);
        restore.exerciseRestore(args.length == 3 ? Integer.parseInt(args[2]) : 0);
        return;
      }
      var agreement = new DeclarativeReceiptsConformance(processor, false, true, true);
      agreement.receipt("", 0, 0, 0);
      var amountMetadata = agreement.receiptAmountMetadata();
      require(processor.read(agreement.agreement, "/receipts/currency") == UNDEFINED,
          "Receipt currency must remain absent before the first qualifying Instruction");
      agreement.attach("first");
      agreement.receipt("", 10000, 2500, 7500);
      agreement.receipt("/targets/first", 10000, 2500, 7500);
      var currencyMetadata = agreement.receiptFieldMetadata("currency", "Receipts Currency");
      agreement.attach("order/2026");
      agreement.receipt("", 20000, 5000, 15000);
      agreement.reportPayment("first", 12000, 2500, true);
      agreement.reportPayment("first", 12000, 2500, true);
      agreement.receipt("", 22000, 5000, 17000);
      agreement.receipt("/targets/first", 12000, 2500, 9500);
      // Model an earlier settlement by exercising the ledger's real reservation and settlement functions.
      agreement.operation("reserveForTest", map("key", "paid-earlier", "amountMinor", 1600));
      agreement.operation("settleForTest", map("key", "paid-earlier"));
      agreement.checkAmount("/commission/paid", 1600);
      agreement.reportPayment("first", 12000, 12000, false);
      agreement.reportPayment("first", 12000, 12000, false);
      agreement.receipt("", 22000, 14500, 7500);
      agreement.receipt("/targets/first", 12000, 12000, 0);
      agreement.receipt("/targets/order~12026", 10000, 2500, 7500);
      agreement.checkAmount("/commission/targets/order%2F2026", 900);
      agreement.checkAmount("/commission/paid", 1600);
      agreement.checkAmount("/commission/reserved", 0);
      require(amountMetadata.equals(agreement.receiptAmountMetadata())
              && currencyMetadata.equals(agreement.receiptFieldMetadata("currency", "Receipts Currency"))
              && "USD".equals(processor.read(agreement.agreement, "/receipts/currency")),
          "Receipts must retain the native field declarations and currency through capture, refund and replay");
      System.out.println("PASS resolved receipt field metadata, numeric totals, and currency after capture and refund across two Orders");
      System.out.println("PASS native cumulative receipts and commission, late attachment, retries and full refund");
      agreement.attach("a~b");
      agreement.attach("a%7Eb");
      agreement.reportPayment("order/2026", 10000, 4700, false);
      agreement.reportPayment("order/2026", 10000, 4700, false);
      agreement.reportPayment("a~b", 10000, 6200, false);
      agreement.reportPayment("a~b", 10000, 6200, false);
      agreement.receipt("", 42000, 25400, 16600);
      agreement.receipt("/targets/order~12026", 10000, 4700, 5300);
      agreement.receipt("/targets/a~0b", 10000, 6200, 3800);
      agreement.receipt("/targets/a%7Eb", 10000, 2500, 7500);
      agreement.checkAmount("/commission/targets/order%2F2026", 636);
      agreement.checkAmount("/commission/targets/a%7Eb", 456);
      agreement.checkAmount("/commission/targets/a%257Eb", 900);
      agreement.checkAmount("/commission/paid", 1600);
      System.out.println("PASS native slash, tilde and percent order keys, live refund replays and distinct ledger targets");

      var revised = new DeclarativeReceiptsConformance(processor, false, true, true, true);
      revised.operation("changeCommissionForTest", map("revision", 1, "commissionBps", 1250));
      revised.attach("revision-one");
      revised.reportPayment("revision-one", 7200, 0, true);
      revised.checkAmount("/commission/targets/revision-one", 900);
      revised.operation("changeCommissionForTest", map("revision", 2, "commissionBps", 1375));
      revised.attach("revision-two");
      revised.reportPayment("revision-two", 7200, 0, true);
      revised.checkAmount("/commission/targets/revision-two", 990);
      revised.reportPayment("revision-one", 7200, 5400, false);
      revised.reportPayment("revision-one", 7200, 5400, false);
      revised.checkAmount("/commission/targets/revision-one", 225);
      revised.checkAmount("/commission/accrued", 1215);
      require(processor.read(revised.agreement, "/orders/revision-one/commissionTerms") == UNDEFINED
              && processor.read(revised.agreement, "/orders/revision-two/commissionTerms") == UNDEFINED,
          "Customer Orders do not contain private commission terms");
      System.out.println("PASS native private rates 1250/1375 bps: captures 7200 accrue 900/990, old refund 5400 leaves 225");

      var rounding = new DeclarativeReceiptsConformance(processor, false, true, true, true);
      rounding.operation("changeCommissionForTest", map("revision", 1, "commissionBps", 1700));
      rounding.attach("rounded");
      rounding.reportPayment("rounded", 552, 0, true);
      rounding.checkAmount("/commission/targets/rounded", 94);
      rounding.reportPayment("rounded", 552, 442, false);
      rounding.reportPayment("rounded", 552, 442, false);
      rounding.checkAmount("/commission/targets/rounded", 19);
      rounding.checkAmount("/receipts/netReceivedMinor", 110);
      rounding.attach("tie");
      rounding.reportPayment("tie", 50, 0, true);
      rounding.checkAmount("/commission/targets/tie", 9);
      rounding.checkAmount("/commission/accrued", 28);
      System.out.println("PASS native commission rounds 552 at 17% to 94, the net 110 to 19, and a half-minor-unit tie up");

      {
        var missing = new DeclarativeReceiptsConformance(processor, false, true, true, true);
        missing.operation("changeCommissionForTest", map("revision", 2));
        missing.attach("missing");
        missing.reportPayment("missing", 10000, 0, true);
        missing.checkAmount("/receipts/netReceivedMinor", 10000);
        missing.checkAmount("/commission/accrued", 0);
        require(processor.read(missing.agreement, "/commission/targets/missing") == UNDEFINED,
            "Current agreement rate does not establish a share without a frozen rate");
        missing.operation("changeCommissionForTest", map("revision", 3, "commissionBps", 0));
        missing.attach("zero");
        missing.reportPayment("zero", 10000, 0, true);
        missing.checkAmount("/receipts/netReceivedMinor", 20000);
        missing.checkAmount("/commission/accrued", 0);
        System.out.println("PASS missing or zero frozen rate never uses the current live rate");
      }

      var direct = new DeclarativeReceiptsConformance(processor, true, false, true);
      direct.attach("direct");
      direct.reportPayment("direct", 12000, 4500, false);
      direct.receipt("", 12000, 4500, 7500);
      require(amountMetadata.equals(direct.receiptAmountMetadata()), "Receipt metadata follows the configured state binding");
      require("USD".equals(processor.read(direct.agreement, direct.receiptPath + "/currency")),
          "Direct sales pin the verified projection currency");
      require(processor.read(direct.agreement, "/commission") == UNDEFINED, "Direct sale has no commission clause");
      System.out.println("PASS direct sale receipts with independent collection, instruction and state bindings");

      var mixed = new DeclarativeReceiptsConformance(processor, false, false, true, false, true);
      mixed.rejectDifferentCurrency();
      mixed.receipt("", 0, 0, 0);
      System.out.println("PASS a Payment Instruction's currency must match the agreement's receipt currency");

      var noPayment = new DeclarativeReceiptsConformance(processor, false, true, false);
      noPayment.attach("free");
      noPayment.receipt("", 0, 0, 0);
      require(object(processor.read(noPayment.agreement, "/receipts/targets")).isEmpty(),
          "Order without a Payment Instruction has no receipt target");
      System.out.println("PASS order without payment leaves receipts and commission unchanged");
    }
  }
}
