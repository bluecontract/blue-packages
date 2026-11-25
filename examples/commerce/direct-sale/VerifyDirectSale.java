package blue.core;

import static blue.core.Values.*;

import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.coordination.Coordination;
import blue.coordination.ProviderAccessExecution;
import blue.coordination.ProviderProtocol;
import blue.coordination.store.InMemoryRecordStore;
import blue.coordination.store.RecordStore;
import blue.language.next.Blue;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/** Real native documents and signed coordination. The guarantor submits fixture payment outcomes. */
public final class VerifyDirectSale {
  private static final String OWNER = "direct-sale-fixture";
  private static final String ENDPOINT = "https://direct-sale.example.test/provider";
  private static final Duration WAIT = Duration.ofSeconds(55);
  private static final long TOTAL = 4375;

  private final Tenant tenant;
  private final TimelineProvider provider;
  private final Blue language;
  private final Contracts processor;
  private final Map<String, String> readers = new LinkedHashMap<>();
  private final Map<String, Object> results = map();
  private final Path output;
  private int submission;

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]);
    var example = Path.of(args[1]);
    var selection = obj(CompositionPackages.yaml(root.resolve("PACKAGES.json")));
    var mounts = obj(selection.get("mounts"));
    var fixtureMounts = Set.of("Activation", "Agreements", "BEX", "Clauses", "Commerce", "Connections",
        "Contracts", "Coordination", "DefinitionRead", "Dispatch", "Documents", "DocumentsDomain",
        "Events", "Execution", "Language", "Money", "MyOS", "Orders", "Parties", "Payment",
        "PaymentInstruction", "ProcessingEventSource", "Time");
    var packages = new CompositionPackages(root, root);
    for (String alias : new java.util.TreeSet<>(fixtureMounts)) {
      packages.packages.put(alias, CompositionPackages.openPinned(root, obj(mounts.get(alias))));
    }
    var bindings = QualificationRuntime.bindings();
    var secrets = new Secrets(new byte[32]);
    try (var store = new InMemoryRecordStore();
         var provider = new TimelineProvider(new Records(store), secrets, ENDPOINT);
         var tenant = new Tenant(OWNER, new InMemoryRecordStore(), secrets, bindings, Telemetry.NOOP);
         var blue = packages.language(tenant.service.nodeProvider());
         var runtime = new AuthoringRuntime(bindings)) {
      var transport = new ProviderTransport() {
        @Override public Response request(String method, String url, String body) {
          require(url.startsWith(ENDPOINT + "/"), "Expected local provider");
          String route = url.substring(ENDPOINT.length() + 1);
          try {
            Object response = switch (route) {
              case "provider" -> provider.descriptor();
              case "types" -> provider.types();
              default -> provider.fetch(route, WireData.json(body), null);
            };
            return new Response(200, WireData.write(response));
          } catch (Problem error) {
            return new Response(error.status, WireData.write(map("code", error.code, "message", error.getMessage())));
          }
        }
      };
      var keys = new ReaderKeys(new Records(store), secrets);
      tenant.imports = new TimelineImports(tenant, OWNER, keys, provider, transport, false);
      var run = new VerifyDirectSale(tenant, provider, blue, runtime.processor(blue), keys, Path.of(args[2]));
      run.results.putAll(map("status", "PARTIAL",
          "packageCatalogueSha256", WireData.sha256(Files.readAllBytes(root.resolve("PACKAGES.json"))),
          "authoringSourceSha256", WireData.sha256(Files.readAllBytes(example.resolve("print-shop.blue"))),
          "transport", "Signed native Coordination histories with one local in-memory tenant and an in-process Timeline Provider",
          "provider", "Fixture session, transaction, secure and capture outcomes are submitted by the guarantor on its signed channel"));
      run.run(obj(CompositionPackages.yaml(example.resolve("print-shop.blue"))),
          obj(CompositionPackages.yaml(example.resolve("basket.yaml"))));
      run.checkpoint("PASS");
    }
  }

  private VerifyDirectSale(Tenant tenant, TimelineProvider provider, Blue language, Contracts processor, ReaderKeys keys, Path output) {
    this.tenant = tenant;
    this.provider = provider;
    this.language = language;
    this.processor = processor;
    this.output = output;
    for (String party : List.of("seller", "customer", "guarantor")) {
      readers.put(party, required(keys.create(OWNER, party, party), "publicKey"));
    }
  }

  private void run(Map<String, Object> source, Map<String, Object> basket) throws Exception {
    var template = obj(source.get("orderTemplate"));
    var paymentTemplate = obj(parameters(template, "payment").get("template"));
    obj(obj(parameters(template, "activation").get("readers")).get("guarantor"))
        .put("readerKeys", List.of(readers.get("guarantor")));
    var guarantor = obj(obj(parameters(paymentTemplate, "activation").get("parties")).get("guarantor"));
    obj(guarantor.get("readerKeys")).put("items", List.of(readers.get("guarantor")));

    var catalogue = bootstrap("catalogue", source, Map.of("seller", "seller"));
    equal(false, read(catalogue, "/activation/active"), "Catalogue starts inactive");
    call(catalogue, "approve_seller", map("revision", 1));
    equal(true, read(catalogue, "/activation/active"), "Seller activates the catalogue");

    var selection = obj(basket.get("values"));
    var quote = map("key", "counter-quote-01", "catalogRevision", selection.get("catalogRevision"),
        "lines", selection.get("lines"));
    call(catalogue, "quoteBasket", quote);
    equal(TOTAL, number(read(catalogue, "/quotes/counter-quote-01/totalMinor")), "Catalogue quote");
    var savedQuote = read(catalogue, "/quotes/counter-quote-01");
    call(catalogue, "quoteBasket", quote);
    equal(savedQuote, read(catalogue, "/quotes/counter-quote-01"), "Quote retry");

    var overCap = map("type", basket.get("type"), "key", "over-cap", "requestId", "over-cap",
        "values", map("catalogRevision", 1, "customerEmail", "buyer@example.test",
            "lines", List.of(map("itemId", "botanical-poster", "quantity", 7))));
    var stale = map("type", basket.get("type"), "key", "stale", "requestId", "stale",
        "values", map("catalogRevision", 2, "customerEmail", "buyer@example.test", "lines", selection.get("lines")));
    String overCapRejection = call(catalogue, "prepareOrder", overCap, true);
    String staleRejection = call(catalogue, "prepareOrder", stale, true);
    equal(0, obj(read(catalogue, "/process_orders/entries")).size(), "Rejected basket creates no order");
    call(catalogue, "prepareOrder", basket);
    var orderEntry = only(catalogue, "/process_orders");
    String preparedOrderPath = required(orderEntry, "itemPath") + "/prepared";
    equal(TOTAL, number(read(catalogue, preparedOrderPath + "/amountMinor")), "Frozen order amount");
    equal("USD", read(catalogue, preparedOrderPath + "/currency"), "Frozen order currency");
    equal(3700L, number(read(catalogue, preparedOrderPath + "/quote/lines/0/lineTotalMinor")), "Poster line");
    equal(675L, number(read(catalogue, preparedOrderPath + "/quote/lines/1/lineTotalMinor")), "Postcard line");
    call(catalogue, "prepareOrder", basket);
    equal(orderEntry.get("requirementRef"), only(catalogue, "/process_orders").get("requirementRef"), "Same requirement on retry");

    results.putAll(map("catalogueRevision", 1, "currency", "USD", "lineTotalsMinor", List.of(3700, 675),
        "quoteTotalMinor", TOTAL, "orderAmountMinor", TOTAL, "orderRequirementRef", orderEntry.get("requirementRef"),
        "rejectedOverCap", overCapRejection, "rejectedStaleRevision", staleRejection,
        "retry", map("stableQuote", true, "stablePreparedOrder", true)));
    checkpoint("ORDER_PREPARATION_VERIFIED");

    var order = bootstrap("order", prepared(catalogue, orderEntry), Map.of("customer", "customer", "seller", "seller"));
    String orderOrigin = identity(order, "/contracts/initialized/document");
    call(catalogue, "provideOrder", provision(orderEntry, order));
    equal(orderOrigin, identity(catalogue, "/orders/counter-order-01/contracts/initialized/document"), "Selected exact order");
    equal(false, read(order, "/activation/active"), "Order awaits seller");
    results.put("orderOriginBlueId", orderOrigin);
    checkpoint("ORDER_PROVISION_VERIFIED");
    call(order, "preparePayment", map());
    var paymentEntry = only(order, "/process_payment");
    results.put("paymentRequirementRef", paymentEntry.get("requirementRef"));
    checkpoint("PAYMENT_PREPARATION_VERIFIED");
    var payment = bootstrap("payment", prepared(order, paymentEntry), Map.of("payer", "customer", "payee", "seller", "guarantor", "guarantor"));
    String paymentOrigin = identity(payment, "/contracts/initialized/document");
    equal(orderOrigin, identity(payment, "/sources/order/contracts/initialized/document"), "PI source order identity");
    equal(TOTAL, number(read(payment, "/paymentTerms/amountMinor")), "PI amount equals order amount");
    equal("USD", read(payment, "/paymentTerms/currency"), "PI currency equals order currency");
    call(order, "providePayment", provision(paymentEntry, payment));
    equal(paymentOrigin, identity(order, "/payment/contracts/initialized/document"), "Only the matching PI is selected");

    call(payment, "acceptPaymentInstruction", map());
    call(payment, "provideSession", map("type", "MyOS/Customer Session Input", "sessionId", "marigold-test-session"));
    call(payment, "confirmFunding", map("sessionId", "marigold-test-session"));
    call(payment, "recordTransactionInitiated", map("type", "PaymentInstruction/Transaction Initiation Input",
        "transactionId", "marigold-test-transaction", "railType", "test", "attachmentPoint", "instruction",
        "providerReference", "marigold-test-reference"));
    call(payment, "authorize", map("type", "PaymentInstruction/Payment Request Input", "requestId", "print-order-hold", "amountMinor", TOTAL));
    call(payment, "secureFunds", map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "print-order-hold", "amountSecured", TOTAL));
    equal(TOTAL, number(read(payment, "/payment/secured")), "Test hold is secured");
    equal(null, read(payment, "/payment/requests/print-order-capture"), "No capture before seller approval");
    call(order, "approve_seller", map("revision", read(order, "/activation/revision")));
    equal("pending", read(payment, "/payment/requests/print-order-capture/status"), "Native capture request");
    equal(TOTAL, number(read(payment, "/payment/requests/print-order-capture/intent/amountMinor")), "Capture equals frozen order total");
    var completion = map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "print-order-capture", "amountCompleted", TOTAL);
    call(payment, "completePayment", completion);
    equal(TOTAL, number(read(payment, "/payment/completed")), "Completed capture");
    equal(TOTAL, number(read(order, "/payment/payment/completed")), "Order observes confirmed capture");
    call(payment, "completePayment", completion);
    equal(TOTAL, number(read(payment, "/payment/completed")), "Repeated callback cannot increase completed amount");
    equal(Set.of("print-order-hold", "print-order-capture"), obj(read(payment, "/payment/requests")).keySet(), "Exactly one hold and one capture");
    results.putAll(map("securedBeforeCaptureMinor", TOTAL, "captureRequestedMinor", TOTAL,
        "completedMinor", TOTAL, "orderObservedCompletedMinor", TOTAL,
        "orderOriginBlueId", orderOrigin, "paymentInstructionOriginBlueId", paymentOrigin,
        "retry", map("stableQuote", true, "stablePreparedOrder", true, "captureRequests", 1, "completedMinor", TOTAL)));
  }

  private void checkpoint(String status) throws Exception {
    results.put("status", status);
    Files.writeString(output, WireData.write(results) + "\n");
  }

  private Coordination.Document bootstrap(String handle, Map<String, Object> source, Map<String, String> roles) throws Exception {
    var activation = parameters(source, "activation");
    var parties = obj(activation.get("parties"));
    if (activation.get("readers") instanceof Map<?, ?> descriptors) {
      obj(descriptors).replaceAll((role, reader) -> reader instanceof Map<?, ?> descriptor ? descriptor.get("readerKeys") : reader);
    }
    var contracts = obj(source.computeIfAbsent("contracts", unused -> map()));
    var access = map();
    var accessPaths = new ArrayList<>();
    for (var assignment : new TreeMap<>(roles).entrySet()) {
      String role = assignment.getKey(), account = assignment.getValue();
      String title = handle + "-" + role;
      var timeline = provider.create(OWNER, title, title);
      String timelineId = required(timeline, "id");
      var channel = ProviderProtocol.typed(tenant.service.bindings(), "Timeline Channel",
          "timeline", timeline.get("timeline"), "actor", ProviderProtocol.typed("Principal Actor", "displayName", OWNER));
      var grant = provider.changeAccess(OWNER, null, List.of(timelineId), List.copyOf(readers.values()),
          "access-" + title, tenant.service.bindings());
      tenant.imports.adoptOwned(timeline);
      IndependentHostedAccessTest.poll(tenant);
      var imported = tenant.imports.importAccess(ENDPOINT, required(grant, "id"));
      var proof = tenant.service.document(required(imported, "sessionId"));
      proof.awaitInitialized(WAIT);
      contracts.put(role, channel);
      obj(parties.get(role)).putAll(map("myosAccountId", account, "lead", map("channel", channel),
          "readerKeys", List.of(readers.get(account))));
      access.put(role, ref(stable(proof)));
      accessPaths.add("/timelineAccess/" + role);
    }
    activation.put("accessPaths", accessPaths);
    source.put("timelineAccess", access);
    var sourceJson = WireData.write(source);
    System.out.println("BOOTSTRAPPING " + handle + " (" + sourceJson.length() + " characters)");
    System.gc();
    var admitted = language.createJson(sourceJson);
    tenant.service.publishContent(admitted);
    tenant.service.engine().add(handle, ref(admitted.blueId()));
    var document = tenant.service.document(handle);
    tenant.service.awaitIdle(WAIT);
    if (document.progress().stable().isEmpty()) {
      try {
        blue.contracts.ClauseGasProbe.diagnose(processor, source);
      } catch (blue.contracts.ContractException diagnostic) {
        throw new AssertionError("Bootstrap " + handle + " " + diagnostic.code()
            + " at " + diagnostic.diagnosticPath() + " " + diagnostic.context(), diagnostic);
      }
      throw new AssertionError("Bootstrap " + handle + " " + document.progress());
    }
    System.out.println("INITIALIZED " + handle);
    return document;
  }

  private String call(Coordination.Document document, String operation, Map<String, Object> request) throws Exception {
    return call(document, operation, request, false);
  }

  private String call(Coordination.Document document, String operation, Map<String, Object> request, boolean reject) throws Exception {
    var routes = document.routes(operation);
    equal(1, routes.size(), document.handle() + "/" + operation + " route");
    var route = routes.getFirst();
    var bindings = tenant.service.bindings();
    var values = processor.execution().values();
    var nativeRequest = values.literal(values.source(request));
    var call = map("type", ref(ProviderAccessExecution.operationRequestType(bindings)), "document", ref(stable(document)),
        "channel", route.channel(), "operation", operation, "request", nativeRequest, "requireExactDocumentVersion", true);
    try (var view = tenant.store.read()) {
      var writes = new TreeMap<RecordStore.Key, Object>();
      values.nativeRuntime().evidence().forEach((id, body) -> {
        if (view.get("content", id) == null) writes.put(new RecordStore.Key("content", id), body);
      });
      equal("COMMITTED", tenant.store.publish(view.packet("direct-sale-evidence", writes, null)).status(), "Retain exact definitions");
    }
    var appended = provider.append(OWNER, route.timeline(), call, "direct-sale-" + (++submission), true);
    String entry;
    try (var protocol = new ProviderProtocol()) {
      entry = protocol.identify(appended.get("object"));
    }
    long deadline = System.nanoTime() + WAIT.toNanos();
    do {
      IndependentHostedAccessTest.poll(tenant);
      tenant.service.awaitIdle(WAIT);
      var input = tenant.documents.input(document.handle(), entry);
      if (IndependentHostedAccessTest.rejected(tenant, document, entry)) {
        var disposition = obj(input.get("disposition"));
        var result = obj(disposition.get("result"));
        String diagnostic = WireData.write(result.get("diagnostic"));
        require(reject, operation + " rejected: " + diagnostic);
        System.out.println("REJECTED " + operation + " " + diagnostic);
        return diagnostic;
      }
      var progress = document.progress();
      require(!Set.of(Coordination.Status.ERROR, Coordination.Status.HOST_INCOMPLETE).contains(progress.status()),
          operation + " failed: " + progress);
      if (arr(input.get("localHistory")).stream().map(Values::obj).anyMatch(row -> Boolean.TRUE.equals(row.get("stable")))) {
        require(!reject, operation + " unexpectedly applied");
        System.out.println("APPLIED " + document.handle() + "/" + operation);
        return entry;
      }
      Thread.sleep(20);
    } while (System.nanoTime() < deadline);
    throw new AssertionError(operation + " timed out: " + document.progress());
  }

  private Map<String, Object> only(Coordination.Document document, String process) {
    var entries = obj(read(document, process + "/entries"));
    equal(1, entries.size(), "Single obligation at " + process);
    return obj(entries.values().iterator().next());
  }

  private Map<String, Object> prepared(Coordination.Document document, Map<String, Object> entry) {
    var values = processor.execution().values();
    return obj(values.literal(values.exact(values.select(new Exact.Ref(stable(document)), required(entry, "itemPath") + "/prepared"))));
  }

  private Object read(Coordination.Document document, String path) {
    var values = processor.execution().values();
    var selected = values.select(new Exact.Ref(stable(document)), path);
    return selected == null ? null : values.bexData(selected);
  }

  private String identity(Coordination.Document document, String path) {
    var values = processor.execution().values();
    return NativeRuntime.identity(values.exact(values.select(new Exact.Ref(stable(document)), path)));
  }

  private static String stable(Coordination.Document document) {
    return document.state().stable().orElseThrow().blueId();
  }

  private static Map<String, Object> ref(String blueId) {
    return map("blueId", blueId);
  }

  private static Map<String, Object> provision(Map<String, Object> entry, Coordination.Document candidate) {
    return map("type", "Documents/Provision Input", "key", entry.get("key"), "inResponseTo", entry.get("requestId"),
        "requirementRef", entry.get("requirementRef"), "document", ref(stable(candidate)));
  }

  private static Map<String, Object> parameters(Map<String, Object> source, String clause) {
    return obj(obj(obj(source.get("clauses")).get(clause)).get("parameters"));
  }

  private static void equal(Object expected, Object actual, String label) {
    require(java.util.Objects.equals(expected, actual), label + " expected=" + expected + " actual=" + actual);
  }

  private static void require(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
}
