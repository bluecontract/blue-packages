import blue.bex.Values;
import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Actor-scoped fixture operations through the native engine. Monetary outcomes are fixture reports. */
public final class FinancialComposition {
  private static final String SOURCE = "/sources/order";
  private static final String CREDIT_KEY = "credit-1";
  private static final String CREDIT_PATH = "/payment/requests/" + CREDIT_KEY;
  private static final long CAPTURE = 10000;
  private static final long REFUND = 8000;
  private static final long RETAINED = 2000;
  private static final String DIRECT_REFUND = """
      afterCancellation:
        'on': embedded
        path: /sources/order
        event: {type: Commerce/Domain Event, kind: Order Cancellation Accepted, clause: cancellation}
        params:
          requestId: order-cancellation-refund
          amountMinor: {$document: /sources/order/cancellationDecision/releasedMinor}
        when: {$gt: [{$var: {name: params, path: /amountMinor}}, 0]}
      """;

  private final Contracts engine;
  private final Path fixtures;

  private FinancialComposition(Contracts engine, Path fixtures) {
    this.engine = engine;
    this.fixtures = fixtures;
  }

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]);
    var fixtures = root.resolve("verification/independent-clauses/financial");
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var language = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var test = new FinancialComposition(runtime.processor(language), fixtures);
      if (args.length > 1 && args[1].equals("request-readiness")) {
        test.requestReadiness();
        return;
      }
      if (args.length > 1 && args[1].equals("selection-probe")) {
        test.selectionGuard(test.adjustmentPayment(false));
        return;
      }
      if (args.length > 1 && args[1].equals("shared-selection")) {
        test.sharedSelection();
        return;
      }
      if (args.length > 1 && args[1].equals("preparation-mode")) {
        test.preparationMode();
        return;
      }
      if (args.length > 1 && args[1].equals("direct-refund")) {
        System.out.println(WireData.write(map("catalogueSha256", sha(root.resolve("PACKAGES.json")),
            "paymentActionLibrary", test.identityOfAlias("PaymentInstruction/Payment Request Actions"),
            "paymentProtocolLibrary", test.identityOfAlias("PaymentInstruction/Payment Protocol Functions"),
            "binding", yaml(DIRECT_REFUND), "lateCancellation", test.directRefund(1800),
            "zeroRelease", test.directRefund(7200))));
        return;
      }
      var cancellation = test.paidCase("cancellation");
      var adjustment = test.paidCase("price adjustment");
      equal(cancellation.get("refundIntent"), adjustment.get("refundIntent"), "Both decisions reach an identical payment request");
      var free = test.complimentaryCancellation();
      equal(cancellation.get("cancellationClause"), free.get("cancellationClause"),
          "Complimentary cancellation uses the identical authored action");
      System.out.println(WireData.write(map("paymentActionLibrary",
          test.identityOfAlias("PaymentInstruction/Payment Request Actions"),
          "paymentProtocolLibrary", test.identityOfAlias("PaymentInstruction/Payment Protocol Functions"),
          "catalogueSha256", sha(root.resolve("PACKAGES.json")),
          "fixtureSha256", map("order.blue", sha(fixtures.resolve("order.blue")),
              "payment.blue", sha(fixtures.resolve("payment.blue"))),
          "cancellation", cancellation, "priceAdjustment", adjustment, "complimentaryCancellation", free)));
    }
  }

  private void requestReadiness() throws Exception {
    var held = adjustmentPayment(false);
    held = turn(held, "", "guarantor", "recordFundsSecuringUnknown",
        map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "initial-hold",
            "reason", "Provider outcome unknown"), 4);
    held = setTarget(held, 0, 5);
    absent(held, "/payment/locks/void", "Stock ledger omits a void lock");
    absent(held, "/payment/requests/adjustment-void", "Unknown authorization must resolve first");
    held = turn(held, "", "guarantor", "secureFunds", outcome("initial-hold", "amountSecured", 7200), 6);
    money(held, "/payment/requests/adjustment-void/intent/amountMinor", 7200);
    absent(held, "/payment/requests/adjustment-refund", "There are no confirmed proceeds to refund");
    held = turn(held, "", "guarantor", "cancelBeforeCompletion",
        map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "adjustment-void"), 7);
    equal("succeeded", read(held, "/payment/requests/adjustment-void/status"), "Confirmed full void");
    money(held, "/payment/secured", 0);
    rejectedCapture(held, 8);
    System.out.println("PASS unknown hold resolves into whole void on stock PI");

    var pending = adjustmentPayment(true);
    pending = turn(pending, "", "guarantor", "secureFunds", outcome("initial-hold", "amountSecured", 7200), 4);
    money(pending, "/payment/requests/fixture-capture/intent/amountMinor", 7200);
    pending = turn(pending, "", "guarantor", "recordPaymentCompletionUnknown",
        map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "fixture-capture",
            "reason", "Provider outcome unknown"), 5);
    pending = setTarget(pending, 0, 6);
    equal(false, read(pending, "/paymentProcess_requests/captureAllowed"),
        "Supplemental restriction revokes capture while the base condition is still true");
    absent(pending, "/payment/requests/adjustment-void", "Do not void during unknown capture");
    absent(pending, "/payment/requests/adjustment-refund", "Do not refund during unknown capture");
    pending = turn(pending, "", "guarantor", "completePayment", outcome("fixture-capture", "amountCompleted", 7200), 7);
    money(pending, "/payment/completed", 7200);
    money(pending, "/targetMinor", 0);
    if (read(pending, "/payment/requests/adjustment-refund") == Values.UNDEFINED) {
      throw new AssertionError("Capture was confirmed without catch-up refund: " + read(pending, "/payment"));
    }
    money(pending, "/payment/requests/adjustment-refund/intent/amountMinor", 7200);
    pending = turn(pending, "", "guarantor", "reverseAfterCompletion",
        outcome("adjustment-refund", "amountReversed", 7200), 8);
    money(pending, "/payment/reversed", 7200);
    absent(pending, "/payment/requests/adjustment-void", "Capture resolved, full refund confirmed");
    System.out.println("PASS unknown capture resolves into one full refund");

    var paid = adjustmentPayment(true);
    paid = turn(paid, "", "guarantor", "secureFunds", outcome("initial-hold", "amountSecured", 7200), 4);
    paid = turn(paid, "", "guarantor", "completePayment", outcome("fixture-capture", "amountCompleted", 7200), 5);
    paid = turn(paid, "", "guarantor", "refundManually", paymentRequest("prior-refund", 1200), 6);
    paid = setTarget(paid, 1800, 7);
    absent(paid, "/payment/requests/adjustment-refund", "Wait for preceding refund to resolve");
    paid = turn(paid, "", "guarantor", "reverseAfterCompletion",
        outcome("prior-refund", "amountReversed", 1200), 8);
    money(paid, "/payment/requests/adjustment-refund/intent/amountMinor", 4200);
    paid = turn(paid, "", "guarantor", "reverseAfterCompletion",
        outcome("adjustment-refund", "amountReversed", 4200), 9);
    paid = setTarget(paid, 1800, 10);
    money(paid, "/payment/reversed", 5400);
    equal("succeeded", read(paid, "/payment/requests/adjustment-refund/status"), "Repeat preserves confirmed request");
    equal(4, CompositionPackages.obj(read(paid, "/payment/requests")).size(), "One new refund after earlier refund");
    System.out.println("PASS prior refund resolves before one additional refund to net 1800");
    selectionGuard(paid);
  }

  private Contracts.Document adjustmentPayment(boolean capture) throws Exception {
    var instruction = source("payment.blue");
    instruction.remove("sources");
    instruction.put("ordinaryCapture", capture);
    CompositionPackages.obj(instruction.get("paymentTerms")).put("amountMinor", 7200);
    CompositionPackages.obj(instruction.get("paymentTerms")).put("limitMinor", 7200);
    var contracts = CompositionPackages.obj(instruction.get("contracts"));
    contracts.put("setTarget", yaml("""
        type: Contracts/Sequential Workflow Operation
        channel: guarantor
        steps:
        - type: Contracts/Update Document
          changeset:
          - {op: add, path: /targetMinor, val: {$binding: call/request/targetMinor}}
        """));
    contracts.put("probeSelection", source("selection-probe.blue"));
    CompositionPackages.obj(instruction.get("clauses")).put("requests", source("request-readiness.blue"));
    var pi = initialized(instruction);
    pi = turn(pi, "", "guarantor", "acceptPaymentInstruction", map(), 1);
    pi = turn(pi, "", "guarantor", "recordTransactionInitiated", map(
        "type", "PaymentInstruction/Transaction Initiation Input", "transactionId", "eligibility-" + capture,
        "railType", "test", "attachmentPoint", "instruction", "providerReference", "fixture"), 2);
    return turn(pi, "", "guarantor", "authorize", paymentRequest("initial-hold", 7200), 3);
  }

  private Contracts.Document setTarget(Contracts.Document pi, long amount, long time) {
    return turn(pi, "", "guarantor", "setTarget", map("targetMinor", amount), time);
  }

  private void rejectedCapture(Contracts.Document pi, long time) {
    var result = engine.process(pi,
        event(pi, "", "guarantor", "pay", paymentRequest("manual-capture", 7200)), time);
    absent(result.commits() ? result.document() : pi, "/payment/requests/manual-capture",
        "Supplemental native policy blocks manual capture");
    equal(false, read(pi, "/paymentProcess_requests/captureAllowed"), "Native instruction gate remains false");
  }

  private void selectionGuard(Contracts.Document pi) {
    var origin = map("blueId", identityAt(pi, "/contracts/initialized/document"));
    var originalOrder = initialized(map("name", "Original order source", "state", "fixture"));
    var sourceOrigin = map("blueId", identityAt(originalOrder, "/contracts/initialized/document"));
    var prepared = map("name", "Original payment requirement", "amountMinor", 7200);
    var values = engine.execution().values();
    var obligation = map("key", "single", "requestId", "different-business-request-id", "path", "/payment",
        "status", "selected", "candidateOrigin", origin.get("blueId"), "documentOrigin", origin.get("blueId"),
        "prepared", prepared, "requirementRef", NativeRuntime.identity(values.source(prepared)));
    var source = map("contracts", map("initialized", map("document", sourceOrigin)),
        "payment", map("contracts", map("initialized", map("document", origin))));
    var input = map("obligations", map(NativeRuntime.identity(values.source("single")), obligation),
        "source", source, "expectedSourceOrigin", sourceOrigin, "path", "/payment", "key", "single");
    var valid = turn(pi, "", "guarantor", "probeSelection", input, 11);
    equal(true, read(valid, "/probeSelected"), "Native obligation key can differ from request ID");
    obligation.put("requirementRef", NativeRuntime.identity(values.source(map("name", "Wrong requirement"))));
    var wrongRequirement = turn(valid, "", "guarantor", "probeSelection", input, 12);
    equal(false, read(wrongRequirement, "/probeSelected"), "Foreign requirement is rejected");
    input.remove("source");
    var waiting = turn(wrongRequirement, "", "guarantor", "probeSelection", input, 13);
    equal(false, read(waiting, "/probeSelected"), "Not yet linked is false rather than an evaluation error");
    System.out.println("PASS distinct native obligation key, foreign requirement and missing linked source");
  }

  private void sharedSelection() throws Exception {
    var instruction = source("payment.blue");
    instruction.put("type", "MyOS/MyOS Test Customer Payment Instruction");
    instruction.put("paymentDetails", map("method", "myos-customer"));
    var terms = CompositionPackages.obj(instruction.get("paymentTerms"));
    terms.put("amountMinor", 7200);
    terms.put("limitMinor", 7200);
    terms.put("payerChannel", "payer");
    var clauses = CompositionPackages.obj(instruction.get("clauses"));
    var activation = CompositionPackages.obj(CompositionPackages.obj(clauses.get("activation")).get("parameters"));
    var parties = CompositionPackages.obj(activation.get("parties"));
    var payer = CompositionPackages.obj(parties.remove("customer"));
    var payerChannel = map("type", "Contracts/External Channel", "event", map("source", "payer"));
    payer.put("lead", map("channel", payerChannel));
    parties.put("payer", payer);
    clauses.put("method", map("type", "MyOS/Payment Method Events"));
    var selector = map("source", SOURCE, "expectedSourceOrigin", "/businessContext/orderOrigin",
        "entries", SOURCE + "/process_payment/entries", "path", "/payment", "key", "single");
    var cancellation = map("decision", map("path", "/decision", "when", map("field", "status", "equals", "cancelled"),
        "retainMinorFrom", "retainedMinor"), "requestIds", map("refund", "refund-cancellation", "void", "void-cancellation"));
    var rejection = map("decision", map("path", "/decision", "when", map("field", "status", "equals", "rejected"),
        "retainMinor", 0), "requestIds", map("void", "void-rejection"));
    var parameters = map("selectedPayment", selector, "sources", map("order", map()),
        "capture", map("type", "Payment/Selected Order Capture", "requestId", "capture-order", "blockedBy", "cancellation"),
        "adjustments", map("cancellation", cancellation, "rejection", rejection));
    clauses.put("requests", map("type", "Payment/Payment Process Clause", "parameters", parameters,
        "bindings", map("requestAuthorize", map("authorize", map("on", "workflow", "party", "guarantor", "input", true)))));
    var contracts = CompositionPackages.obj(instruction.get("contracts"));
    contracts.put("payer", payerChannel);
    contracts.put("probeSharedSelection", yaml("""
        type: Contracts/Sequential Workflow Operation
        channel: guarantor
        steps:
        - type: Contracts/Compute
          definition: {type: Payment/Payment Process Functions}
          constants: {sourceMode: workflow}
          do:
          - $appendChange:
              op: add
              path: /effectiveAdjustments
              val:
                $call:
                  function: withSharedSelection
                  args:
                    adjustments: {$binding: call/request/adjustments}
                    sharedSelection: {$binding: call/request/selector}
        """));

    var authorized = authorizedMyos(instruction);
    var held = turn(authorized, "", "guarantor", "secureFunds", outcome("hold", "amountSecured", 7200), 6);
    money(held, "/payment/secured", 7200);
    var override = new LinkedHashMap<>(selector);
    override.put("expectedSourceOrigin", "/otherOrigin");
    rejection.put("selectedPayment", override);
    var normalized = turn(held, "", "guarantor", "probeSharedSelection",
        map("adjustments", map("cancellation", cancellation, "rejection", rejection), "selector", selector), 7);
    equal(selector, read(normalized, "/effectiveAdjustments/cancellation/selectedPayment"), "Omitted selector uses the full default");
    equal(override, read(normalized, "/effectiveAdjustments/rejection/selectedPayment"), "Explicit selector overrides the default");
    equal("refund-cancellation", read(normalized, "/effectiveAdjustments/cancellation/requestIds/refund"), "Refund ID is preserved");
    equal("void-rejection", read(normalized, "/effectiveAdjustments/rejection/requestIds/void"), "Void ID is preserved");
    rejection.put("selectedPayment", map("path", "/payment"));
    try {
      ClauseGasProbe.diagnose(engine, instruction);
      throw new AssertionError("A partial override must not borrow shared selector fields");
    } catch (blue.bex.BexError error) {
      equal("PAYMENT_ADJUSTMENT_SELECTION_PATH_REQUIRED", error.getMessage(), "Partial override is refused");
    }
    System.out.println("PASS shared selector and whole override, distinct request IDs, inherited capture mode and real MyOS request events");
  }

  private Contracts.Document authorizedMyos(Map<String, Object> instruction) {
    var result = engine.initialize(instruction);
    if (!result.commits()) ClauseGasProbe.diagnose(engine, instruction);
    equal("APPLIED", result.status(), "Shared selector plus implicit mode initializes");
    assertMyosEvent(result, "Customer Payment Session Requested");
    var pi = result.document();
    equal("/paymentProcess_requests/captureAllowed", read(pi, "/paymentTerms/captureGate"), "Named type supplies conditional mode");
    equal(false, read(pi, "/paymentProcess_requests/captureAllowed"), "Missing selection holds the gate closed");
    pi = turn(pi, "", "guarantor", "acceptPaymentInstruction", map(), 1);
    pi = turn(pi, "", "guarantor", "provideSession", map("type", "MyOS/Customer Session Input", "sessionId", "test"), 2);
    pi = turn(pi, "", "guarantor", "confirmFunding", map("sessionId", "test"), 3);
    pi = turn(pi, "", "guarantor", "recordTransactionInitiated",
        map("type", "PaymentInstruction/Transaction Initiation Input", "transactionId", "test-shared-selection",
            "railType", "test", "attachmentPoint", "instruction", "providerReference", "test"), 4);
    var authorize = engine.process(pi, event(pi, "", "guarantor", "authorize", paymentRequest("hold", 7200)), 5);
    equal("APPLIED", authorize.status(), "Native authorization request");
    assertMyosEvent(authorize, "MyOS Execution Requested");
    return authorize.document();
  }

  private void assertMyosEvent(Contracts.Result result, String kind) {
    var matching = ClauseGasProbe.eventData(engine, result).stream().map(CompositionPackages::obj)
        .filter(value -> kind.equals(value.get("kind"))).toList();
    equal(1, matching.size(), kind);
    var details = CompositionPackages.obj(matching.getFirst().get("details"));
    equal("myos-customer", details.get("method"), "Adapter method comes from paymentDetails");
    if ("MyOS Execution Requested".equals(kind))
      equal("myos-customer", matching.getFirst().get("method"), "Execution carries the same method");
  }

  private void preparationMode() throws Exception {
    var condition = map("$eq", List.of(map("$document", "/activation/active"), false));
    var typed = map("type", map("name", "Conditional capture policy", "mode", "when"),
        "requestId", "capture-probe", "when", condition);
    prepareAndProvide("inline typed capture", "capture", typed, false, true);
    prepareAndProvide("bound typed capture", "capture", typed, true, true);
    prepareAndProvide("explicit conditional capture", "capture",
        map("mode", "when", "requestId", "explicit-capture", "when", condition), false, true);
    prepareAndProvide("explicit workflow", "capture", map("mode", "workflow"), false, false);
    prepareAndProvide("implicit workflow", "capture", map(), false, false);
    var transfer = map("type", map("name", "Conditional transfer policy", "mode", "when"),
        "requestId", "transfer-probe", "when", condition);
    prepareAndProvide("inline typed transfer", "transfer", transfer, false, true);
  }

  private void prepareAndProvide(String label, String action, Map<String, Object> policy, boolean pointer, boolean conditional)
      throws Exception {
    var template = source("payment.blue");
    template.remove("sources");
    CompositionPackages.obj(template.get("contracts")).put("changeCurrencyForProbe", yaml("""
        type: Contracts/Sequential Workflow Operation
        channel: guarantor
        steps:
        - type: Contracts/Update Document
          changeset:
          - {op: replace, path: /paymentTerms/currency, val: EUR}
        """));
    var instructionClauses = CompositionPackages.obj(template.get("clauses"));
    var roles = map("customer", "customer", "seller", "seller", "guarantor", "guarantor");
    if ("transfer".equals(action)) {
      template.put("type", "ACME/Bank Transfer Instruction");
      var activation = CompositionPackages.obj(CompositionPackages.obj(instructionClauses.get("activation")).get("parameters"));
      var parties = CompositionPackages.obj(activation.get("parties"));
      var payer = CompositionPackages.obj(parties.remove("customer"));
      var channel = map("type", "Contracts/External Channel", "event", map("source", "payer"));
      payer.put("lead", map("channel", channel));
      parties.put("payer", payer);
      CompositionPackages.obj(template.get("contracts")).put("payer", channel);
      CompositionPackages.obj(template.get("paymentTerms")).put("payerChannel", "payer");
      roles.remove("customer");
      roles.put("payer", "payer");
      instructionClauses.put("requests", map("type", "ACME/Bank Transfer Process Clause", "parameters", map("transfer", policy)));
    } else {
      instructionClauses.put("requests", map("type", "Payment/Payment Process Clause", "parameters",
          map("capture", policy)));
    }
    var bindings = map("instruction", "/payment", "parties", roles,
        "prepare", map("preparePayment", map("on", "workflow", "party", "seller")),
        "provide", map("providePayment", map("on", "workflow", "party", "seller")));
    var parameters = map("obtain", "provide", "suppliedBy", "seller");
    var orderSource = map("name", label, "type", "Orders/Order with Clauses",
        "clauses", map("activation", instructionClauses.get("activation"),
        "payment", map("type", "Payment/Payment Clause", "parameters", parameters, "bindings", bindings)));
    if (pointer) {
      orderSource.put("paymentTemplate", template);
      bindings.put("template", "/paymentTemplate");
    } else {
      parameters.put("template", template);
    }
    var prepared = turn(initialized(orderSource), "", "seller", "preparePayment",
        map("type", "Documents/Preparation Input", "key", "single", "requestId", "payment-probe", "values", map()), 1);
    var entries = CompositionPackages.obj(read(prepared, "/process_payment/entries"));
    var item = CompositionPackages.obj(entries.values().iterator().next());
    String path = item.get("itemPath").toString();
    var values = engine.execution().values();
    var source = values.literal(values.exact(values.select(new Exact.Ref(prepared.blueId()), path + "/prepared")));
    var pi = initialized(source);
    var gate = read(pi, "/paymentTerms/" + action + "Gate");
    equal(conditional, ("/paymentProcess_requests/" + action + "Allowed").equals(gate), label + " effective mode");
    equal(gate, read(prepared, path + "/domainTerms/" + action + "Gate"), label + " frozen gate matches initialized PI");
    if (conditional && !pointer && "capture".equals(action) && policy.containsKey("type")) {
      var tampered = turn(pi, "", "guarantor", "changeCurrencyForProbe", map(), 1);
      equal("EUR", read(tampered, "/paymentTerms/currency"), "Probe actually changes the initialized candidate");
      var input = event(prepared, "", "seller", "providePayment", paymentProvision(item, tampered));
      var rejected = engine.process(prepared, input, 2);
      equal(false, rejected.commits(), "Providing a changed currency is rejected");
      equal(List.of(), engine.emitted(rejected), "Rejected terms emit no effects");
      try {
        ClauseGasProbe.diagnose(engine, prepared, input, 2);
        throw new AssertionError("Expected the strict financial terms check");
      } catch (blue.bex.BexError failure) {
        equal("PAYMENT_TERMS_MISMATCH", failure.getMessage(), "Frozen terms comparison stays exact");
      }
    }
    var admitted = turn(prepared, "", "seller", "providePayment", paymentProvision(item, pi), 2);
    equal(identityAt(pi, "/contracts/initialized/document"),
        identityAt(admitted, "/payment/contracts/initialized/document"), label + " admits the exact PI");
    System.out.println("PASS " + label + " freezes and admits equal native payment terms");
  }

  private static Map<String, Object> paymentProvision(Map<String, Object> entry, Contracts.Document payment) {
    return map("type", "Documents/Provision Input", "key", entry.get("key"), "inResponseTo", entry.get("requestId"),
        "requirementRef", entry.get("requirementRef"), "document", map("blueId", payment.blueId()));
  }

  private Map<String, Object> paidCase(String scenario) throws Exception {
    var order = order(scenario, CAPTURE, RETAINED, true);
    var pi = capturedPayment(order, source("payment.blue"), scenario, CAPTURE);
    var origin = identityAt(pi, SOURCE + "/contracts/initialized/document");

    var spoof = engine.process(pi, map("type", "Commerce/Domain Event", "kind", "Credit Approved",
        "clause", "credit", "entityId", CREDIT_KEY, "amountMinor", REFUND), 7);
    absent(spoof.commits() ? spoof.document() : pi, CREDIT_PATH, "An external event cannot simulate an embedded credit");
    var unrelated = order("unlinked source", CAPTURE, RETAINED, true);
    var foreign = engine.process(pi, event(unrelated, "", "customer", "cancelOrder", map("key", CREDIT_KEY)), 7);
    absent(foreign.commits() ? foreign.document() : pi, CREDIT_PATH, "A valid caller on a different Order cannot credit this instruction");
    Object repeat;
    String actor;
    String operation;
    if (scenario.equals("cancellation")) {
      repeat = map("key", CREDIT_KEY);
      actor = "customer";
      operation = "cancelOrder";
      var denied = engine.process(pi, event(pi, SOURCE, "seller", operation, repeat), 8);
      var prior = denied.commits() ? denied.document() : pi;
      absent(prior, SOURCE + "/cancellationDecision", "Seller has no customer cancellation authority");
      absent(prior, CREDIT_PATH, "Unauthorized cancellation requests no refund");
      pi = turn(pi, SOURCE, actor, operation, repeat, 9);
      money(pi, SOURCE + "/cancellationDecision/retainedMinor", RETAINED);
      money(pi, SOURCE + "/cancellationDecision/releasedMinor", REFUND);
    } else {
      pi = turn(pi, SOURCE, "seller", "proposePrice", map("type", "Amendments/Amendment Input",
          "proposalId", CREDIT_KEY, "path", "/agreedPriceMinor", "expectedRevision", 1, "replacement", RETAINED), 8);
      repeat = map("proposalId", CREDIT_KEY);
      pi = turn(pi, SOURCE, "seller", "approvePriceSeller", repeat, 9);
      absent(pi, CREDIT_PATH, "A single approval cannot refund");
      money(pi, SOURCE + "/agreedPriceMinor", CAPTURE);
      actor = "customer";
      operation = "approvePriceCustomer";
      pi = turn(pi, SOURCE, actor, operation, repeat, 10);
      money(pi, SOURCE + "/agreedPriceMinor", RETAINED);
      absent(pi, SOURCE + "/cancellationDecision", "Price adjustment stays independent of cancellation");
    }
    equal(origin, identityAt(pi, SOURCE + "/contracts/initialized/document"), "Propagation preserves the independent source identity");
    var refund = read(pi, CREDIT_PATH + "/intent");
    equal("refund", read(pi, CREDIT_PATH + "/intent/action"),
        "Stock requestRefund recorded a refund in " + scenario + " " + read(pi, "/payment/requests"));
    money(pi, CREDIT_PATH + "/intent/amountMinor", REFUND);
    equal("pending", read(pi, CREDIT_PATH + "/status"), "Effect awaits a guarantor report");
    money(pi, "/payment/reversed", 0);
    money(pi, "/payment/reserved/refund", REFUND);

    var replay = engine.process(pi, event(pi, SOURCE, actor, operation, repeat), 11);
    pi = replay.commits() ? replay.document() : pi;
    equal(refund, read(pi, CREDIT_PATH + "/intent"), "Source replay preserves a single exact refund request");
    money(pi, "/payment/reserved/refund", REFUND);
    pi = turn(pi, "", "guarantor", "reverseAfterCompletion", outcome(CREDIT_KEY, "amountReversed", REFUND), 12);
    equal("succeeded", read(pi, CREDIT_PATH + "/status"), "The separate guarantor report confirms the refund");
    money(pi, "/payment/completed", CAPTURE);
    money(pi, "/payment/reversed", REFUND);
    money(pi, "/payment/reserved/refund", 0);
    var evidence = map("orderOrigin", origin, "instructionOrigin", identityAt(pi, "/contracts/initialized/document"),
        "cancellationClause", identityAt(pi, SOURCE + "/clauses/cancellation"), "refundIntent", refund, "capturedMinor", CAPTURE, "reversedMinor", REFUND, "netMinor", RETAINED,
        "pendingBeforeGuarantor", true, "replayedSourceRequest", true);
    if (scenario.equals("price adjustment")) {
      var secondApproval = map("proposalId", "second-reduction");
      pi = turn(pi, SOURCE, "seller", "proposePrice", map("type", "Amendments/Amendment Input",
          "proposalId", "second-reduction", "path", "/agreedPriceMinor", "expectedRevision", 2, "replacement", 1000), 13);
      pi = turn(pi, SOURCE, "seller", "approvePriceSeller", secondApproval, 14);
      pi = turn(pi, SOURCE, "customer", "approvePriceCustomer", secondApproval, 15);
      money(pi, "/payment/requests/second-reduction/intent/amountMinor", 1000);
      money(pi, "/payment/reserved/refund", 1000);
      money(pi, "/payment/reversed", REFUND);
      pi = turn(pi, "", "guarantor", "reverseAfterCompletion", outcome("second-reduction", "amountReversed", 1000), 16);
      money(pi, "/payment/reversed", 9000);
      evidence.put("secondReduction", map("previousPriceMinor", RETAINED, "newPriceMinor", 1000,
          "additionalRefundMinor", 1000, "cumulativeRefundMinor", 9000));
    }
    return evidence;
  }

  private Map<String, Object> directRefund(long retained) throws Exception {
    long amount = 7200;
    long released = amount - retained;
    String requestId = "order-cancellation-refund";
    String path = "/payment/requests/" + requestId;
    String scenario = "direct refund with retained " + retained;
    var order = order(scenario, amount, retained, false);
    var instruction = source("payment.blue");
    var requests = CompositionPackages.obj(CompositionPackages.obj(instruction.get("clauses")).get("requests"));
    CompositionPackages.obj(requests.get("bindings")).put("requestRefund", yaml(DIRECT_REFUND));
    var pi = capturedPayment(order, instruction, scenario, amount);
    absent(pi, SOURCE + "/clauses/credit", "The direct template has no intermediate credit clause");

    var spoof = engine.process(pi, map("type", "Commerce/Domain Event", "kind", "Order Cancellation Accepted",
        "clause", "cancellation", "entityId", "external"), 7);
    absent(spoof.commits() ? spoof.document() : pi, path, "An external event cannot trigger an embedded refund");
    var foreign = order("unlinked " + scenario, amount, retained, false);
    var foreignAttempt = engine.process(pi, event(foreign, "", "customer", "cancelOrder", map("key", "foreign")), 7);
    absent(foreignAttempt.commits() ? foreignAttempt.document() : pi, path, "An unrelated Order cannot refund this instruction");

    // The customer key is valid for the Order. The PI uses its own reserved key.
    var input = map("key", "customer/request");
    pi = turn(pi, SOURCE, "customer", "cancelOrder", input, 8);
    equal("accepted", read(pi, SOURCE + "/cancellationDecision/status"), "Commercial decision committed");
    money(pi, SOURCE + "/cancellationDecision/retainedMinor", retained);
    money(pi, SOURCE + "/cancellationDecision/releasedMinor", released);
    String decision = identityAt(pi, SOURCE + "/cancellationDecision");
    money(pi, "/payment/reversed", 0);
    money(pi, "/payment/reserved/refund", released);
    if (released == 0) {
      absent(pi, path, "Zero release creates no refund request");
    } else {
      equal("pending", read(pi, path + "/status"), "The stock refund awaits a guarantor report");
      money(pi, path + "/intent/amountMinor", released);
    }

    var replay = engine.process(pi, event(pi, SOURCE, "customer", "cancelOrder", input), 9);
    pi = replay.commits() ? replay.document() : pi;
    equal(decision, identityAt(pi, SOURCE + "/cancellationDecision"), "Replay preserves the first decision");
    money(pi, "/payment/reserved/refund", released);
    if (released == 0) {
      absent(pi, path, "Replay at zero creates no request");
    } else {
      pi = turn(pi, "", "guarantor", "reverseAfterCompletion", outcome(requestId, "amountReversed", released), 10);
      equal("succeeded", read(pi, path + "/status"), "The separate guarantor report confirms the refund");
      var afterConfirmation = engine.process(pi, event(pi, SOURCE, "customer", "cancelOrder", input), 11);
      pi = afterConfirmation.commits() ? afterConfirmation.document() : pi;
      equal("succeeded", read(pi, path + "/status"), "Replay leaves the original confirmed request");
    }
    money(pi, "/payment/completed", amount);
    money(pi, "/payment/reversed", released);
    money(pi, "/payment/reserved/refund", 0);
    equal(released == 0 ? 2 : 3, CompositionPackages.obj(read(pi, "/payment/requests")).size(), "Exactly the expected native requests");
    return map("capturedMinor", amount, "retainedMinor", retained, "reversedMinor", released,
        "refundRequestId", released > 0 ? requestId : null, "decisionBlueId", decision, "replayChecked", true);
  }

  private Contracts.Document capturedPayment(Contracts.Document order, Map<String, Object> instruction, String label, long amount) {
    instruction.put("sources", map("order", map("blueId", order.blueId())));
    var terms = CompositionPackages.obj(instruction.get("paymentTerms"));
    terms.put("amountMinor", amount);
    terms.put("limitMinor", amount);
    var pi = initialized(instruction);
    money(pi, "/paymentTerms/amountMinor", amount);
    equal(identityAt(order, "/contracts/initialized/document"),
        identityAt(pi, SOURCE + "/contracts/initialized/document"), "Exact original Order source");
    pi = turn(pi, "", "guarantor", "acceptPaymentInstruction", map(), 1);
    pi = turn(pi, "", "guarantor", "recordTransactionInitiated",
        map("type", "PaymentInstruction/Transaction Initiation Input", "transactionId", "test-" + label,
            "railType", "test", "attachmentPoint", "instruction", "providerReference", "fixture"), 2);
    pi = turn(pi, "", "guarantor", "authorize", paymentRequest("initial-hold", amount), 3);
    pi = turn(pi, "", "guarantor", "secureFunds", outcome("initial-hold", "amountSecured", amount), 4);
    pi = turn(pi, "", "guarantor", "pay", paymentRequest("initial-capture", amount), 5);
    pi = turn(pi, "", "guarantor", "completePayment", outcome("initial-capture", "amountCompleted", amount), 6);
    money(pi, "/payment/completed", amount);
    money(pi, "/payment/reversed", 0);
    return pi;
  }

  private Map<String, Object> complimentaryCancellation() throws Exception {
    var order = order("complimentary", 0, 0, false);
    order = turn(order, "", "customer", "cancelOrder", map("key", "complimentary-cancel"), 1);
    equal("accepted", read(order, "/cancellationDecision/status"), "The same cancellation action works independently");
    money(order, "/cancellationDecision/retainedMinor", 0);
    money(order, "/cancellationDecision/releasedMinor", 0);
    absent(order, "/clauses/credit", "Complimentary cancellation needs no credit adapter");
    absent(order, "/clauses/priceAdjustment", "Complimentary cancellation needs no price amendment");
    absent(order, "/payment", "Complimentary cancellation needs no Payment Instruction");
    return map("decision", read(order, "/cancellationDecision"),
        "cancellationClause", identityAt(order, "/clauses/cancellation"), "hasPaymentInstruction", false);
  }

  private Contracts.Document order(String scenario, long amount, long retains, boolean useCreditAdapter) throws Exception {
    var source = source("order.blue");
    source.put("name", "Independent source Order for " + scenario);
    source.put("purchaseAmountMinor", amount);
    source.put("agreedPriceMinor", amount);
    source.put("retainedOnCancellationMinor", retains);
    if (!useCreditAdapter) {
      var clauses = CompositionPackages.obj(source.get("clauses"));
      clauses.remove("credit");
      clauses.remove("priceAdjustment");
      source.put("clauses", clauses);
    }
    return initialized(source);
  }

  private Contracts.Document initialized(Object source) {
    var result = engine.initialize(source);
    if (!result.commits()) ClauseGasProbe.diagnose(engine, source);
    equal("APPLIED", result.status(), "Native initialization");
    return result.document();
  }

  private Contracts.Document turn(Contracts.Document doc, String path, String actor, String operation, Object input, long time) {
    var event = event(doc, path, actor, operation, input);
    var result = engine.process(doc, event, time);
    if (!result.commits()) ClauseGasProbe.diagnose(engine, doc, event, time);
    equal("APPLIED", result.status(), "Native " + operation);
    return result.document();
  }

  private Object event(Contracts.Document doc, String path, String actor, String operation, Object input) {
    var target = path.isEmpty() ? doc.blueId() : identityAt(doc, path);
    return map("source", actor, "operation", map("type", "Contracts/Operation Request", "channel", actor,
        "operation", operation, "request", input, "document", map("blueId", target), "requireExactDocumentVersion", true));
  }

  private String identityAt(Contracts.Document doc, String path) {
    var values = engine.execution().values();
    return NativeRuntime.identity(values.exact(values.select(new Exact.Ref(doc.blueId()), path)));
  }

  private String identityOfAlias(String alias) {
    return engine.displayAliases().entrySet().stream().filter(entry -> alias.equals(entry.getValue()))
        .map(Map.Entry::getKey).findFirst().orElseThrow();
  }

  private Map<String, Object> source(String filename) throws Exception {
    return yaml(Files.readString(fixtures.resolve(filename)));
  }

  private static Map<String, Object> yaml(String source) {
    return CompositionPackages.obj(WireData.json(WireData.write(WireData.parse(source, "yaml"))));
  }

  private Object read(Contracts.Document doc, String path) {
    return engine.read(doc, path);
  }

  private void money(Contracts.Document doc, String path, long amount) {
    equal(Long.toString(amount), String.valueOf(read(doc, path)), path);
  }

  private void absent(Contracts.Document doc, String path, String reason) {
    equal(Values.UNDEFINED, read(doc, path), reason);
  }

  private static String sha(Path path) throws Exception {
    return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256")
        .digest(Files.readAllBytes(path)));
  }

  private static Map<String, Object> paymentRequest(String key, long amount) {
    return map("type", "PaymentInstruction/Payment Request Input", "requestId", key, "amountMinor", amount);
  }

  private static Map<String, Object> outcome(String key, String field, long amount) {
    return map("type", "PaymentInstruction/Payment Outcome Input", "requestId", key, field, amount);
  }

  private static Map<String, Object> map(Object... pairs) {
    var result = new LinkedHashMap<String, Object>();
    for (int i = 0; i < pairs.length; i += 2) result.put((String) pairs[i], pairs[i + 1]);
    return result;
  }

  private static void equal(Object expected, Object actual, String label) {
    if (!Objects.equals(expected, actual)) throw new AssertionError(label + " expected " + expected + ", got " + actual);
  }
}
