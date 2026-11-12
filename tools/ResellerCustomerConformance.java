package blue.packages;

import blue.bex.*;
import blue.contracts.*;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Tests only the exported Reseller customer checks after Documents checkProvision succeeds.
 * Signed bootstrap, generic provision validation and completed replay require Core integration.
 */
public final class ResellerCustomerConformance {
  private static Map<String, Object> map(Object... fields) {
    var result = new LinkedHashMap<String, Object>();
    for (int i = 0; i < fields.length; i += 2) result.put((String) fields[i], fields[i + 1]);
    return result;
  }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> object(Object value) {
    return (Map<String, Object>) value;
  }

  @SuppressWarnings("unchecked")
  private static List<Object> list(Object value) {
    return (List<Object>) value;
  }

  private static Map<String, Object> checked(String current, String initial, boolean email) {
    var prepared = email ? map("customerEmail", "contact@example.test") : map("customerAccountId", "guest");
    return map("outcome", "acceptedNew", "item", map("prepared", prepared),
        "candidate", map("activation", map("parties", map(
            "seller", map("myosAccountId", "seller"), "partner", map("myosAccountId", "partner"),
            "customer", map("myosAccountId", current))),
            "contracts", map("initialized", map("document", map("clauses", map("activation",
                map("parameters", map("parties", map("customer", map("myosAccountId", initial))))))))));
  }

  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]);
    var catalogue = object(WireData.json(Files.readString(root.resolve("PACKAGES.json"))));
    var bundle = PackageBundle.builder();
    for (var entry : object(catalogue.get("mounts")).entrySet()) {
      var pin = object(entry.getValue());
      bundle.mount(entry.getKey(), BluePackage.open(root.resolve((String) pin.get("path")),
          (String) pin.get("blueId")));
    }
    try (var blue = Blue.builder().packages(bundle.build()).build()) {
      var values = new Contracts(blue, QualificationRuntime.bindings()).execution().values();
      var definition = values.source(map("type", "Reseller/Customer Orders Clause"), "definition");
      var preflight = list(values.bexData(values.select(definition, "/actions/provideOrder/preflight")));
      var body = new ArrayList<Object>();
      body.add(map("$let", map("name", "actionResult", "expr", map("$binding", "call/request"))));
      // The first statement invokes Documents checkProvision. This focused unit starts
      // at its successful result and executes the actual remaining exported statements.
      body.addAll(preflight.subList(1, preflight.size()));
      body.add(map("$return", true));
      var bex = new Bex(BexProfile.current());
      var program = bex.compile(map("do", body), map(), null);
      var cases = new LinkedHashMap<String, Map<String, Object>>();
      cases.put("email existing actual account", checked("guest", "guest", true));
      cases.put("email new actual account", checked("new-guest", "new-guest", true));
      cases.put("email contact does not pin actual account", checked("other-authorized-guest", "other-authorized-guest", true));
      cases.put("email current account changed", checked("changed", "guest", true));
      cases.put("email initial account missing", checked("guest", "", true));
      cases.put("email actual account absent", checked("", "", true));
      cases.put("email actual seller forbidden", checked("seller", "seller", true));
      cases.put("email actual partner forbidden", checked("partner", "partner", true));
      cases.put("account exact pin", checked("guest", "guest", false));
      cases.put("account changed pin forbidden", checked("another", "another", false));
      cases.put("duplicate already checked by Documents", map("outcome", "duplicate"));
      var rejected = Map.of(
          "email current account changed", "ORDER_CUSTOMER_MISMATCH",
          "email initial account missing", "ORDER_CUSTOMER_MISMATCH",
          "email actual account absent", "CUSTOMER_REQUIRED",
          "email actual seller forbidden", "CUSTOMER_MUST_BE_DISTINCT",
          "email actual partner forbidden", "CUSTOMER_MUST_BE_DISTINCT",
          "account changed pin forbidden", "ORDER_CUSTOMER_MISMATCH");
      for (var test : cases.entrySet()) {
        var context = new BexContext(map(), map(), map(), Values.UNDEFINED, map(),
            map("call", map("request", test.getValue())), "/", null,
            (actual, pattern) -> values.matches(actual, values.source(pattern, "definition")),
            (actual, gas) -> NativeRuntime.identity(values.source(Values.blueValue(actual))));
        String error = null;
        try {
          bex.execute(program, context, 1_000_000);
        } catch (BexError failure) {
          error = failure.getMessage();
        }
        String expected = rejected.get(test.getKey());
        if (expected == null ? error != null : error == null || !error.contains(expected)) {
          throw new AssertionError(test.getKey() + " expected=" + expected + " actual=" + error);
        }
        System.out.println("PASS specialized customer boundary " + test.getKey());
      }
      System.out.println("PASS " + cases.size() + " cases; generic checkProvision and signed replay excluded");
    }
  }
}
