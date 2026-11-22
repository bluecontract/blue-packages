import blue.bex.BexError;
import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.stream.IntStream;

/** Exercises full native catalog document invocations at the published gas limit. */
public final class CatalogCapacityConformance {
  private static final long GAS_LIMIT = 10_000_000;
  private static final String STANDALONE_CATALOG = "examples/reseller/catalog.blue";
  private static final List<Integer> HOURS = IntStream.rangeClosed(145, 168).boxed().toList();

  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]).toAbsolutePath().normalize();
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    var realistic = "examples/reseller/adventures-in-paradise-preview.blue";
    var checks = List.of(
        new Fixture(STANDALONE_CATALOG, "catalog-clause-250", 250, false, null),
        new Fixture(realistic, "reseller-109", 109, false, null),
        new Fixture(realistic, "reseller-250", 250, false, null),
        new Fixture(realistic, "reseller-250-full-item-options", 250, true, null),
        new Fixture(realistic, "reseller-250-invalid-last-duration", 250, true, "DUPLICATE_DURATION_CHOICE"),
        new Fixture(realistic, "reseller-251", 251, false, "INVALID_ITEMS"));

    int failures = 0;
    for (var check : checks) {
      try {
        verifyInitialization(packages, root, check);
        System.out.println("PASS " + check.name());
      } catch (AssertionError | RuntimeException failure) {
        System.out.println("FAIL " + check.name());
        failure.printStackTrace(System.out);
        failures++;
      }
    }
    try {
      verifyPublication(packages, root);
    } catch (AssertionError | RuntimeException failure) {
      System.out.println("FAIL catalog publication");
      failure.printStackTrace(System.out);
      failures++;
    }
    require(failures == 0, failures + " catalog capacity checks failed");
  }

  private record Fixture(String source, String name, int count, boolean fullOptions, String rejection) {}

  private static void verifyInitialization(CompositionPackages packages, Path root, Fixture check)
      throws Exception {
    var source = documentSource(root, check.source());
    String catalogKey = check.source().equals(STANDALONE_CATALOG) ? "catalog" : "products";
    if (catalogKey.equals("products")) {
      // Inject deterministic party channels while keeping the current native checkout composition.
      var scenarios = object(WireData.json(Files.readString(root.resolve(
          "examples/reseller/tests/bootstrap-preparation.case.json"))));
      var scenario = object(((List<?>) scenarios.get("scenarios")).getFirst());
      var patch = object(scenario.get("sourcePatch"));
      object(source.get("clauses")).put("activation", patch.get("/clauses/activation"));
    }
    var catalog = object(source.get(catalogKey));
    var entries = items(object(catalog.get("entries")), check.count(), check.fullOptions());
    catalog.put("entries", entries);
    if ("DUPLICATE_DURATION_CHOICE".equals(check.rejection())) {
      var hours = new ArrayList<>(HOURS);
      hours.set(hours.size() - 1, hours.getFirst());
      object(entries.get(itemId(check.count() - 1, check.fullOptions())))
          .put("allowedDurationHours", hours);
    }

    try (var blue = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var processor = runtime.processor(blue);
      equal(GAS_LIMIT, processor.gasPolicy().sharedLimit(), "Native gas budget");
      var result = processor.initialize(source);
      checkGas(check.name(), result);
      if (check.rejection() != null) {
        verifyRejection(processor, result, check.rejection(),
            () -> ClauseGasProbe.diagnose(processor, source));
        return;
      }

      equal("APPLIED", result.status(), "Valid catalog must initialize within the budget");
      equal(true, processor.read(result.document(), "/activation/active"), "Reseller agreement is active");
      verifyCatalog(processor, result, "/" + catalogKey, catalog);
      if (check.source().equals(STANDALONE_CATALOG)) {
        equal(Map.of(), processor.read(result.document(), "/quotes"), "Catalog initializes with no quotes");
      }
    }
  }

  private static void verifyPublication(CompositionPackages packages, Path root) throws Exception {
    var source = documentSource(root, STANDALONE_CATALOG);
    var catalog = object(source.get("catalog"));
    var samples = object(catalog.get("entries"));
    try (var blue = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var processor = runtime.processor(blue);
      equal(GAS_LIMIT, processor.gasPolicy().sharedLimit(), "Native gas budget");
      var initial = processor.initialize(source);
      equal("APPLIED", initial.status(), "Catalog publication fixture initializes");
      var document = initial.document();

      var oversized = publication(document, items(samples, 251, true));
      var rejected = processor.process(document, oversized, 1);
      checkGas("publish-251-full-item-options", rejected);
      verifyRejection(processor, rejected, "INVALID_ITEMS",
          () -> ClauseGasProbe.diagnose(processor, document, oversized, 1));
      verifyCatalog(processor, rejected, "/catalog", catalog);
      System.out.println("PASS publish-251-full-item-options");

      var entries = items(samples, 250, true);
      var published = processor.process(document, publication(document, entries), 2);
      checkGas("publish-250-full-item-options", published);
      equal("APPLIED", published.status(), "Valid catalog publication must fit the budget");
      var replacement = new LinkedHashMap<>(catalog);
      replacement.put("revision", 2);
      replacement.put("entries", entries);
      verifyCatalog(processor, published, "/catalog", replacement);
      require(processor.emitted(published).stream().map(CatalogCapacityConformance::object)
          .anyMatch(event -> "Catalog Published".equals(event.get("kind"))
              && "2".equals(WireData.write(event.get("revision")))), "Revision 2 publication event");
      System.out.println("PASS publish-250-full-item-options");
    }
  }

  private static Object publication(Contracts.Document document, Map<String, Object> entries) {
    return Map.of("source", "seller", "operation", Map.of(
        "type", "Contracts/Operation Request",
        "document", Map.of("blueId", document.blueId()),
        "channel", "seller",
        "operation", "publishCatalog",
        "request", Map.of("expectedRevision", 1, "entries", entries),
        "requireExactDocumentVersion", true));
  }

  private static void checkGas(String name, Contracts.Result result) {
    var observed = result.observations();
    System.out.printf("%s status=%s gas=%d diagnostic=%s rejectedCharge=%s%n",
        name, result.status(), result.gas(), observed.get("diagnostic"), observed.get("rejected"));
    require(result.gas() > 0 && result.gas() <= GAS_LIMIT, "Gas outside published bounds");
  }

  private static void verifyRejection(
      Contracts processor, Contracts.Result result, String reason, Runnable diagnose) {
    equal("FAILED", result.status(), "Invalid catalog must fail by its authored guard");
    equal(Map.of("code", "BEX_EXECUTION_REJECTED"), result.observations().get("diagnostic"), "Native failure");
    equal(result.inputIdentity(), result.document().identity(), "Invalid catalog execution is atomic");
    equal(List.of(), processor.emitted(result), "Invalid catalog emits no effects");
    // Native observations expose only the rejection code. Recover the authored reason
    // from the same input in the native diagnostic runner after measuring the invocation.
    try {
      diagnose.run();
      throw new AssertionError("Expected authored rejection " + reason);
    } catch (BexError failure) {
      equal(reason, failure.getMessage(), "Authored catalog validation");
      System.out.println("Authored rejection " + reason);
    }
  }

  private static void verifyCatalog(Contracts processor, Contracts.Result result, String path, Map<String, Object> catalog) {
    require(WireData.write(catalog).equals(WireData.write(processor.read(result.document(), path))),
        "Expected catalog revision, supplier, currency and all item fields");
  }

  private static Map<String, Object> documentSource(Path root, String path) throws Exception {
    return object(WireData.parse(Files.readString(root.resolve(path)), "yaml"));
  }

  private static Map<String, Object> items(Map<String, Object> samples, int count, boolean fullOptions) {
    var prototypes = new ArrayList<>(samples.values());
    var items = new LinkedHashMap<String, Object>();
    for (int i = 0; i < count; i++) {
      var item = new LinkedHashMap<>(object(prototypes.get(i % prototypes.size())));
      if (fullOptions) {
        item.put("label", maximumText("Premium rental " + i + " ", 120));
        item.put("description", maximumText("Rental package " + i + " includes fitted equipment. ", 2000));
        item.put("pricingUnit", "per_selected_hour");
        item.put("dateRequired", true);
        item.put("dateSelectionHint", maximumText("Choose a pickup date for package " + i + ". ", 500));
        item.put("allowedDurationHours", HOURS);
        item.put("maxQuantity", 1000);
        item.put("guestDiscountPercent", 15 + i % 5);
      } else {
        item.put("label", item.get("label") + " — package " + (i + 1));
      }
      item.put("unitAmountMinor", 1000 + i * 275);
      items.put(itemId(i, fullOptions), item);
    }
    return items;
  }

  private static String itemId(int index, boolean fullOptions) {
    String stem = String.format(Locale.ROOT, "package-%03d", index + 1);
    return fullOptions ? stem + "-rental".repeat(7) + "-set" : stem;
  }

  private static String maximumText(String prefix, int codePoints) {
    // A supplementary character exercises the storage and text work of wide code points.
    return prefix + "🚲".repeat(codePoints - prefix.codePointCount(0, prefix.length()));
  }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> object(Object value) {
    return (Map<String, Object>) value;
  }

  private static void equal(Object expected, Object actual, String label) {
    require(Objects.equals(expected, actual), label + ": expected " + expected + ", got " + actual);
  }

  private static void require(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
}
