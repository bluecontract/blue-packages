package blue.core;

import static blue.core.Values.*;

import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.coordination.Coordination;
import blue.coordination.ProviderProtocol;
import blue.coordination.ProviderAccessExecution;
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
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/** Runs the selected Reseller package on native, signed Coordination histories. */
public final class CatalogOrderAttachmentConformance {
  private static final String ORDER = "/orders/checkout-1";
  private static final String PAYMENT = ORDER + "/payment";
  private static final long AMOUNT = 3895;
  private static final long COMMISSION = 390;
  private static final Duration WAIT = Duration.ofSeconds(90);
  private static final String OWNER = "merchant";
  private static final String ENDPOINT = "https://catalog-order.example.test/provider";

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]);
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    var secrets = new Secrets(new byte[32]);
    var bindings = QualificationRuntime.bindings();
    try (var store = new InMemoryRecordStore();
         var provider = new TimelineProvider(new Records(store), secrets, ENDPOINT);
         var tenant = new Tenant(OWNER, new InMemoryRecordStore(), secrets, bindings, Telemetry.NOOP);
         var blue = packages.language(tenant.service.nodeProvider());
         var runtime = new AuthoringRuntime(bindings)) {
      var processor = runtime.processor(blue);
      var transport = new ProviderTransport() {
        @Override
        public Response request(String method, String url, String body) {
          require(url.startsWith(ENDPOINT + "/"), "Unexpected provider endpoint");
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
      new Scenario(tenant, provider, blue, processor, keys).run(root);
    }
  }

  private static final class Scenario {
    private final Tenant tenant;
    private final TimelineProvider provider;
    private final Blue language;
    private final Contracts processor;
    private final Map<String, String> readers = new LinkedHashMap<>();
    private final long proposedStart = Instant.now().plus(Duration.ofDays(7)).getEpochSecond() * 1_000_000;

    Scenario(Tenant tenant, TimelineProvider provider, Blue language, Contracts processor, ReaderKeys keys)
        throws Exception {
      this.tenant = tenant;
      this.provider = provider;
      this.language = language;
      this.processor = processor;
      for (String party : List.of("seller", "partner", "customer", "guarantor")) {
        readers.put(party, required(keys.create(OWNER, party, party), "publicKey"));
      }
    }

    private Participant timeline(String document, String role, String account) throws Exception {
      String name = document + "-" + role;
      var timeline = provider.create(OWNER, name, "catalog-order-" + name);
      var channel = ProviderProtocol.typed(tenant.service.bindings(), "Timeline Channel",
          "timeline", timeline.get("timeline"), "actor", ProviderProtocol.typed("Principal Actor", "displayName", OWNER));
      var accessGrant = provider.changeAccess(OWNER, null, List.of(required(timeline, "id")),
          List.copyOf(readers.values()), "catalog-order-access-" + name, tenant.service.bindings());
      tenant.imports.adoptOwned(timeline);
      IndependentHostedAccessTest.poll(tenant);
      var imported = tenant.imports.importAccess(ENDPOINT, required(accessGrant, "id"));
      var access = tenant.service.document(required(imported, "sessionId"));
      access.awaitInitialized(WAIT);
      return new Participant(channel, readers.get(account), stableId(access));
    }

    void run(Path root) throws Exception {
      var source = obj(WireData.parse(Files.readString(
          root.resolve("examples/reseller/adventures-in-paradise-preview.blue")), "yaml"));
      var orderTemplate = obj(source.get("orderTemplate"));
      var orderClauses = obj(orderTemplate.get("clauses"));
      var orderActivation = activationParameters(orderTemplate);
      orderActivation.put("required", List.of("seller"));
      var payment = obj(orderClauses.get("payment"));
      var paymentParams = obj(payment.get("parameters"));
      paymentParams.put("sourcePaths", map("order", ""));
      orderActivation.put("readers", map("guarantor", map(
          "myosAccountId", "guarantor", "readerKeys", List.of(readers.get("guarantor")))));
      orderActivation.remove("preActivationChannels");
      orderActivation.put("preActivationOperations", List.of("preparePayment", "providePayment"));
      obj(payment.get("bindings")).put("prepare", map("preparePayment", map(
          "on", "workflow", "party", "seller", "params",
          obj(obj(obj(payment.get("bindings")).get("prepare")).get("onOrderCreated")).get("params"))));
      var piTemplate = obj(paymentParams.get("template"));
      obj(obj(obj(piTemplate.get("clauses")).get("payment")).get("parameters"))
          .put("sources", map("order", map()));
      obj(obj(obj(source.get("products")).get("entries")).get("dolphin-cruise-child"))
          .put("unitAmountMinor", 4100);

      var agreement = bootstrap("agreement", source, Map.of("seller", "seller", "partner", "partner"));
      System.out.println("Catalog Orders Clause " + identityAt(agreement, "/clauses/orders/type"));
      call(agreement, "approve_seller", map("revision", 1));
      call(agreement, "approve_partner", map("revision", 1));
      call(agreement, "prepareOrder",
          map("type", "Documents/Preparation Input", "key", "checkout-1", "requestId", "basket-1",
              "values", map("customerEmail", "guest@example.test", "catalogRevision", 1,
                  "lines", List.of(map("itemId", "dolphin-cruise-child", "quantity", 1),
                      map("itemId", "dolphin-cruise-under-4", "quantity", 1)),
                  "groups", List.of(map("id", "visit", "lineIndices", List.of(0, 1),
                      "proposedStartMicros", proposedStart)))));
      require(obj(read(agreement, "/orders")).isEmpty(), "Preparation leaves /orders empty");
      var orderEntry = onlyPreparation(agreement, "/process_orders");
      var order = bootstrap("order", prepared(agreement, orderEntry),
          Map.of("seller", "seller", "partner", "partner", "customer", "customer"));
      equal(false, read(order, "/activation/active"), "Order awaits supplier approval");
      equal(AMOUNT, number(read(order, "/amountMinor")), "Two-line order amount");
      equal("USD", read(order, "/currency"), "Order currency");
      equal(null, read(order, "/payment"), "Bootstrapped Order has no PI");
      String orderOrigin = identityAt(order, "/contracts/initialized/document");
      var provision = provision(orderEntry, stableId(order));
      call(agreement, "provideOrder", provision);
      String entryPath = required(orderEntry, "itemPath");
      var state = read(agreement, entryPath + "/status");
      var orders = obj(read(agreement, "/orders"));
      require(orders.size() == 1 && orders.containsKey("checkout-1"),
          "First provideOrder must select the initialized Order while inactive. status=" + state
              + " order keys=" + orders.keySet());
      equal(orderOrigin, identityAt(agreement, ORDER + "/contracts/initialized/document"), "Selected Order origin");
      equal("selected", state, "Commercially inactive Order stays selected");
      equal(false, read(agreement, ORDER + "/activation/active"), "Provision cannot approve the Order");
      equal(null, read(agreement, PAYMENT), "Early link has no PI");
      accrued(agreement, 0);
      System.out.println("PASS first provideOrder selected one inactive Order with no PI");

      call(order, "preparePayment", map());
      var paymentEntry = onlyPreparation(order, "/process_payment");
      var instruction = bootstrap("payment", prepared(order, paymentEntry),
          Map.of("payer", "customer", "payee", "seller", "observer", "partner", "guarantor", "guarantor"));
      String instructionOrigin = identityAt(instruction, "/contracts/initialized/document");
      equal(orderOrigin, identityAt(instruction, "/sources/order/contracts/initialized/document"),
          "PI was bootstrapped with the same Order as its declared source");
      call(order, "providePayment", provision(paymentEntry, stableId(instruction)));
      equal(instructionOrigin, identityAt(agreement, PAYMENT + "/contracts/initialized/document"),
          "Independent attachment of PI reaches the same selected Order");
      accrued(agreement, 0);

      call(instruction, "acceptPaymentInstruction", map());
      call(instruction, "recordTransactionInitiated",
          map("type", "PaymentInstruction/Transaction Initiation Input", "transactionId", "checkout-transaction",
              "railType", "test", "attachmentPoint", "instruction", "providerReference", "test"));
      call(instruction, "authorize",
          map("type", "PaymentInstruction/Payment Request Input", "requestId", "authorize-1", "amountMinor", AMOUNT));
      call(instruction, "secureFunds",
          map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "authorize-1", "amountSecured", AMOUNT));
      accrued(agreement, 0);
      equal(false, read(agreement, ORDER + "/activation/active"), "Securing payment cannot approve the Order");
      equal(AMOUNT, number(read(agreement, PAYMENT + "/payment/secured")), "Independent authorization reaches Agreement");
      call(order, "approve_seller", map("revision", 1));
      equal(true, read(agreement, ORDER + "/activation/active"), "Independent approval reaches Agreement");
      equal(true, read(instruction, "/sources/order/activation/active"), "Independent approval reaches the PI source");
      equal("usable", read(agreement, entryPath + "/status"), "Approved Order becomes usable");
      equal("pending_supplier", read(order, "/reservations/visit/status"), "Reservation awaits separate confirmation");
      call(order, "confirmReservation",
          map("key", "confirmation-1", "groupId", "visit",
              "expectedProposalBlueId", read(order, "/reservations/visit/proposalBlueId")));
      equal(proposedStart, number(read(agreement, ORDER + "/reservations/visit/confirmedStartMicros")),
          "Independent supplier confirms the proposed date");

      call(instruction, "pay",
          map("type", "PaymentInstruction/Payment Request Input", "requestId", "capture-1", "amountMinor", AMOUNT));
      var receipt = map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "capture-1", "amountCompleted", AMOUNT);
      call(instruction, "completePayment", receipt);
      assertPaidOrder(agreement, entryPath, orderOrigin, instructionOrigin);
      System.out.println("PASS independent PI completion accrued 390 without a second provideOrder");

      String paidPublication = identityAt(agreement, ORDER);
      call(instruction, "completePayment", receipt);
      assertPaidOrder(agreement, entryPath, orderOrigin, instructionOrigin);
      String afterReceiptReplay = identityAt(agreement, ORDER);
      System.out.println("Order publication after receipt retry " + paidPublication + " -> " + afterReceiptReplay);
      call(agreement, "provideOrder", provision);
      assertPaidOrder(agreement, entryPath, orderOrigin, instructionOrigin);
      System.out.println("Order publication after provision retry " + afterReceiptReplay + " -> " + identityAt(agreement, ORDER));
      System.out.println("PASS retries preserve the selected Order, PI and single commission");
    }

    private void assertPaidOrder(Coordination.Document agreement, String entryPath,
        String orderOrigin, String instructionOrigin) {
      equal(Set.of("checkout-1"), obj(read(agreement, "/orders")).keySet(), "One Order");
      equal("usable", read(agreement, entryPath + "/status"), "Order remains usable");
      equal(orderOrigin, identityAt(agreement, ORDER + "/contracts/initialized/document"), "Same Order origin");
      equal(true, read(agreement, ORDER + "/activation/approved/seller"), "Supplier approval retained");
      equal(proposedStart, number(read(agreement, ORDER + "/reservations/visit/confirmedStartMicros")),
          "Supplier confirmation retained");
      equal(instructionOrigin, identityAt(agreement, PAYMENT + "/contracts/initialized/document"), "Same PI origin");
      equal(AMOUNT, number(read(agreement, PAYMENT + "/payment/completed")), "Completed receipt retained");
      accrued(agreement, COMMISSION);
      equal(Set.of("checkout-1"), obj(read(agreement, "/commission/targets")).keySet(), "One commission target");
      equal(COMMISSION, number(read(agreement, "/commission/targets/checkout-1")), "Commission rounds to 390");
    }

    private Coordination.Document bootstrap(String handle, Map<String, Object> source,
        Map<String, String> roles) throws Exception {
      var activation = activationParameters(source);
      var parties = obj(activation.get("parties"));
      if (activation.get("readers") instanceof Map<?, ?> rawReaders) {
        obj(rawReaders).replaceAll((key, reader) ->
            reader instanceof Map<?, ?> descriptor ? descriptor.get("readerKeys") : reader);
      }
      var contracts = obj(source.computeIfAbsent("contracts", ignored -> map()));
      var accesses = new LinkedHashMap<String, Object>();
      var paths = new ArrayList<String>();
      for (var assignment : new TreeMap<>(roles).entrySet()) {
        String role = assignment.getKey();
        String actor = assignment.getValue();
        var participant = timeline(handle, role, actor);
        var party = obj(parties.get(role));
        contracts.put(role, participant.channel());
        party.put("myosAccountId", actor);
        party.put("lead", map("channel", participant.channel()));
        party.put("readerKeys", List.of(participant.reader()));
        accesses.put(role, ref(participant.access()));
        paths.add("/timelineAccess/" + role);
      }
      activation.put("accessPaths", paths);
      source.put("timelineAccess", accesses);
      var admitted = language.createJson(WireData.write(source));
      tenant.service.publishContent(admitted);
      tenant.service.engine().add(handle, ref(admitted.blueId()));
      var document = tenant.service.document(handle);
      tenant.service.awaitIdle(WAIT);
      require(document.progress().stable().isPresent(), "Initialize " + handle + " " + admitted.blueId()
          + ": " + document.progress());
      System.out.println("INITIALIZED " + handle);
      return document;
    }

    private void call(Coordination.Document document, String operation, Map<String, Object> request) throws Exception {
      var routes = document.routes(operation);
      equal(1, routes.size(), "One route for " + operation);
      var route = routes.getFirst();
      var bindings = tenant.service.bindings();
      var nativeRequest = processor.execution().values().literal(processor.execution().values().source(request));
      var call = map("type", ref(ProviderAccessExecution.operationRequestType(bindings)),
          "document", ref(stableId(document)), "channel", route.channel(), "operation", operation,
          "request", nativeRequest, "requireExactDocumentVersion", true);
      // The request may carry types from the published business packages, which the
      // local provider's native-only type catalogue does not mount.
      equal("request", processor.execution().role(processor.execution().values().source(call)), "Operation type");
      publishEvidence();
      var appended = provider.append(OWNER, route.timeline(), call,
          "catalog-order-" + document.handle() + "-" + operation + "-" + java.util.UUID.randomUUID(), true);
      String entry;
      try (var protocol = new ProviderProtocol()) {
        entry = protocol.identify(appended.get("object"));
      }
      long deadline = System.nanoTime() + WAIT.toNanos();
      do {
        IndependentHostedAccessTest.poll(tenant);
        tenant.service.awaitIdle(WAIT);
        var input = tenant.documents.input(document.handle(), entry);
        var progress = document.progress();
        if (IndependentHostedAccessTest.rejected(tenant, document, entry)) {
          if (operation.equals("provideOrder") || operation.equals("providePayment")) {
            diagnoseProvision(document, operation, route.channel(), request);
          }
          var result = obj(obj(input.get("disposition")).get("result"));
          throw new AssertionError(operation + " rejected: " + WireData.write(result.get("diagnostic")));
        }
        require(!Set.of(Coordination.Status.ERROR, Coordination.Status.HOST_INCOMPLETE).contains(progress.status()),
            operation + " failed: " + progress);
        if (arr(input.get("localHistory")).stream().map(Values::obj)
            .anyMatch(row -> Boolean.TRUE.equals(row.get("stable")))) {
          System.out.println("APPLIED " + document.handle() + "/" + operation);
          return;
        }
        Thread.sleep(20);
      } while (System.nanoTime() < deadline);
      throw new AssertionError(operation + " did not finish: " + document.progress());
    }

    private void diagnoseProvision(Coordination.Document document, String operation, String channel,
        Map<String, Object> request) {
      var values = processor.execution().values();
      var root = new Exact.Ref(stableId(document));
      String step = "/contracts/" + operation + "/steps/0";
      var functions = new LinkedHashMap<>(obj(values.bexData(values.select(root, step + "/definition/functions"))));
      var local = values.select(root, step + "/functions");
      if (local != null) functions.putAll(obj(values.bexData(local)));
      functions.replaceAll((name, body) -> body instanceof Map<?, ?> ref && ref.get("blueId") instanceof String id
          ? values.bexData(new Exact.Ref(id)) : body);
      var program = map("functions", functions, "constants", values.bexData(values.select(root, step + "/constants")),
          "expr", map("$call", map("function", "checkProvision",
              "args", map("input", map("$binding", "call/request")))));
      var input = values.source(map("channel", channel, "request", request));
      processor.execution().evaluatePredicate(root, input, "call", values.source(program), 10_000_000);
    }

    private void publishEvidence() {
      try (var view = tenant.store.read()) {
        var writes = new TreeMap<RecordStore.Key, Object>();
        processor.execution().values().nativeRuntime().evidence().forEach((id, body) -> {
          if (view.get("content", id) == null) writes.put(new RecordStore.Key("content", id), body);
        });
        equal("COMMITTED", tenant.store.publish(view.packet("catalog-order-definitions", writes, null)).status(),
            "Retain immutable inputs");
      }
    }

    private Map<String, Object> onlyPreparation(Coordination.Document document, String process) {
      var entries = obj(read(document, process + "/entries"));
      equal(1, entries.size(), "One preparation at " + process);
      return obj(entries.values().iterator().next());
    }

    private Map<String, Object> prepared(Coordination.Document document, Map<String, Object> entry) {
      var values = processor.execution().values();
      return obj(values.literal(values.exact(values.select(new Exact.Ref(stableId(document)),
          required(entry, "itemPath") + "/prepared"))));
    }

    private Object read(Coordination.Document document, String path) {
      var values = processor.execution().values();
      var selected = values.select(new Exact.Ref(stableId(document)), path);
      return selected == null ? null : values.bexData(selected);
    }

    private String identityAt(Coordination.Document document, String path) {
      var values = processor.execution().values();
      return NativeRuntime.identity(values.exact(values.select(new Exact.Ref(stableId(document)), path)));
    }

    private void accrued(Coordination.Document agreement, long expected) {
      equal(expected, number(read(agreement, "/commission/accrued")), "Commission accrued");
    }
  }

  private record Participant(Map<String, Object> channel, String reader, String access) {}

  private static String stableId(Coordination.Document document) {
    return document.state().stable().orElseThrow().blueId();
  }

  private static Map<String, Object> ref(String blueId) {
    return map("blueId", blueId);
  }

  private static Map<String, Object> provision(Map<String, Object> item, String documentId) {
    return map("type", "Documents/Provision Input", "key", item.get("key"),
        "inResponseTo", item.get("requestId"), "requirementRef", item.get("requirementRef"),
        "document", ref(documentId));
  }

  private static Map<String, Object> activationParameters(Map<String, Object> source) {
    return obj(obj(obj(source.get("clauses")).get("activation")).get("parameters"));
  }

  private static void equal(Object expected, Object actual, String label) {
    require(java.util.Objects.equals(expected, actual), label + " expected=" + expected + " actual=" + actual);
  }

  private static void require(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
}
