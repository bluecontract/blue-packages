package blue.core;

import static blue.core.CommissionPayoutConformance.*;

import blue.bex.Values;
import blue.coordination.AuthoringRuntime;
import blue.language.next.Exact;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/** Exercises direct checkout on both configurations emitted by Go, with local test transports. */
public final class DeclarativeOrderPreparationConformance {
  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]).toAbsolutePath().normalize();
    var source = declarativeAgreement(root);
    var catalog = o(source.get("products"));
    var bike = o(o(catalog.get("entries")).get("harbor-bike"));
    check(!bike.containsKey("maxQuantity"), "Fixture should have an uncapped entry");
    check(!source.containsKey("quotes") && !source.containsKey("quoteCommissionTerms"),
        "Direct checkout source must omit stored quotes");
    var packages = declarativePackages(root);
    try (var blue = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var test = activeAgreement(runtime.processor(blue), source);
      var initial = prepare("before", 1, 1001);
      check(!test.p.execution().declarations(new Exact.Ref(test.host.blueId())).containsKey("createQuote"),
          "Direct checkout offers no stored-quote operation");
      test.deny("partner", "prepareOrder", test.host.blueId(),
          m("type", "Documents/Preparation Input", "key", "stored", "requestId", "order-stored",
              "values", m("quoteKey", "old-quote", "customerEmail", "buyer@example.test")));
      test.root("partner", "prepareOrder", initial);
      var original = verifyOrder(test, "before", 7_207_200, 1250, null);

      test.deny("seller", "proposeCommission_seller", test.host.blueId(),
          m("type", "Amendments/Amendment Input", "proposalId", "invalid-rate",
              "expectedRevision", 1, "path", "/terms/commissionBps", "replacement", 10_001));
      amend(test, "Commission", "/terms/commissionBps", 1700);
      check(test.number("/terms/commissionBps") == 1700, "Bilateral commission amendment applies");
      var replacement = o(WireData.json(WireData.write(catalog)));
      replacement.put("revision", 2);
      o(o(replacement.get("entries")).get("harbor-bike")).putAll(m("maxQuantity", 1001, "unitAmountMinor", 9000));
      amend(test, "Catalog", "/products", replacement);
      check(test.number("/products/revision") == 2, "Bilateral catalogue amendment applies");
      test.deny("partner", "prepareOrder", test.host.blueId(), prepare("stale", 1, 1));
      test.deny("partner", "prepareOrder", test.host.blueId(), prepare("too-many", 2, 1002));
      test.root("partner", "prepareOrder", prepare("after", 2, 1001));
      verifyOrder(test, "after", 8_108_100, 1700, null);

      test.root("partner", "prepareOrder", initial);
      var replayed = verifyOrder(test, "before", 7_207_200, 1250, null);
      check(original.equals(replayed), "Retry reuses the original prepared identity and frozen private terms");
      check(o(test.read("/process_orders/entries")).size() == 2, "Only the two direct preparations create obligations");
      System.out.println("PASS generated direct checkout, quantity 1001 with and without a cap, bilateral amendments, commission rate bounds, private snapshots and retry");
      scheduledAgreement(root, runtime.processor(blue));
      automaticElapsedAgreement(root, runtime.processor(blue));
    }
  }

  private static void scheduledAgreement(Path root, blue.contracts.Contracts processor) throws Exception {
    var source = bindLocalAccounts(o(WireData.parse(Files.readString(root.resolve(
        "examples/sales/declarative/timed-bicycle-rental-agreement.blue")), "yaml")));
    var test = activeAgreement(processor, source);
    long start = 172_800_000_000L;
    var selection = prepare("timed", 1, 1);
    var values = o(selection.get("values"));
    values.put("groups", List.of(m("id", "standalone", "lineIndices", List.of(0), "proposedStartMicros", start)));
    test.deny("partner", "prepareOrder", test.host.blueId(), selection);
    values.put("groups", List.of(m("id", "booking-1", "lineIndices", List.of(0), "proposedStartMicros", start)));
    test.root("partner", "prepareOrder", selection);
    verifyOrder(test, "timed", 7200, 1250, start);
    var item = o(o(test.read("/process_orders/entries")).values().iterator().next());
    String prepared = item.get("itemPath") + "/prepared";
    check(test.number(prepared + "/clauses/cancellation/parameters/freeCancellationHoursAfterStart") == 2,
        "The prepared Order freezes the elapsed cancellation period");
    check(test.number(prepared + "/clauses/cancellation/parameters/freeCancellationHoursBeforeStart") == 24,
        "The prepared Order freezes the service cutoff");
    check(test.number(prepared + "/clauses/cancellation/parameters/lateCancellationChargePercent") == 25,
        "The prepared Order freezes the agreed retention");
    check(test.read(prepared + "/clauses/windowStart/bindings/fallback") == Values.UNDEFINED,
        "A scheduled Order awaiting seller confirmation uses its signed activation");
    System.out.println("PASS the same generated template prepares one scoped scheduled Order with frozen cancellation terms");
  }

  private static void automaticElapsedAgreement(Path root, blue.contracts.Contracts processor) throws Exception {
    var source = bindLocalAccounts(o(WireData.parse(Files.readString(root.resolve(
        "examples/sales/declarative/automatic-bicycle-rental-agreement.blue")), "yaml")));
    var test = activeAgreement(processor, source);
    test.root("partner", "prepareOrder", prepare("automatic", 1, 1));
    verifyOrder(test, "automatic", 7200, 1250, null);
    var item = o(o(test.read("/process_orders/entries")).values().iterator().next());
    String prepared = item.get("itemPath") + "/prepared";
    check("automatic".equals(test.read(prepared + "/orderSnapshot/terms/confirmationMode")),
        "The undated Order uses the automatic activation policy");
    check(test.number(prepared + "/clauses/cancellation/parameters/freeCancellationHoursAfterStart") == 2,
        "The prepared Order freezes its elapsed grace period");
    check("/clockStartMicros".equals(test.read(prepared + "/clauses/cancellation/bindings/windowStart")),
        "The prepared policy reads the configured Order clock");
    var clockBindings = o(test.read(prepared + "/clauses/windowStart/bindings"));
    check("/payment/securedTimestamp/timestampMicros".equals(clockBindings.get("fallback")),
        "The native fallback explicitly binds the selected PI's SECURE projection");
    var primary = o(clockBindings.get("startFromEntry"));
    check(primary.size() == 1 && m("on", "activated").equals(primary.values().iterator().next()),
        "One declared activation connection supplies the native primary entry timestamp");
    check(test.read(prepared + "/clockStartMicros") == Values.UNDEFINED,
        "Preparation does not claim that the independent Order has activated");
    System.out.println("PASS the same generated template prepares an automatic Order with an explicit native clock dependency");
  }

  private static void amend(CommissionPayoutConformance test, String name, String path, Object replacement) {
    String id = "change-" + name;
    Object previous = test.read(path);
    test.root("seller", "propose" + name + (name.equals("Commission") ? "_seller" : ""),
        m("type", "Amendments/Amendment Input", "proposalId", id,
            "expectedRevision", 1, "path", path, "replacement", replacement));
    test.root("seller", "approve" + name + "_seller", m("proposalId", id));
    check(previous.equals(test.read(path)), "One approval must not apply a replacement");
    test.root("partner", "approve" + name + "_partner", m("proposalId", id));
  }

  private static Map<String,Object> prepare(String key, int revision, int quantity) {
    return m("type", "Documents/Preparation Input", "key", key, "requestId", "order-" + key,
        "values", m("catalogRevision", revision, "customerEmail", "buyer@example.test",
            "lines", List.of(m("itemId", "harbor-bike", "quantity", quantity)),
            "groups", List.of(m("id", "booking-1", "lineIndices", List.of(0)))));
  }

  private static String verifyOrder(CommissionPayoutConformance test, String key, long amount, long rate, Long proposedStart) {
    var entries = o(test.read("/process_orders/entries"));
    var item = entries.values().stream().map(CommissionPayoutConformance::o)
        .filter(candidate -> key.equals(candidate.get("key"))).findFirst().orElseThrow();
    String path = item.get("itemPath").toString();
    check(test.number(path + "/prepared/amountMinor") == amount && "USD".equals(test.read(path + "/prepared/currency")),
        "Prepared amount and currency come from the current catalogue at preparation");
    check(test.number(path + "/domainTerms/commissionTerms/commissionBps") == rate,
        "Agreement freezes the effective commission in private preparation terms");
    check(test.read(path + "/prepared/commissionTerms") == Values.UNDEFINED,
        "Prepared customer source does not include the commission snapshot");
    String start = path + "/prepared/orderSnapshot/groups/0/proposedStartMicros";
    if (proposedStart == null) {
      check(test.read(start) == Values.UNDEFINED, "Undated checkout does not manufacture a service time");
    } else {
      check(test.number(start) == proposedStart, "Scheduled checkout preserves the exact proposed start");
    }
    return item.get("requirementRef").toString();
  }
}
