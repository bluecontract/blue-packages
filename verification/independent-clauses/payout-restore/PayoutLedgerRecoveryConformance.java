import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Native Ledger dispatch with modeled snapshots of admitted payout instructions. */
public final class PayoutLedgerRecoveryConformance {
  private static final int GROSS = 900;
  private static final int FEE = 180;
  private static final int NET = GROSS - FEE;
  private static final List<String> PAYOUTS =
      List.of("first", "second", "missing-report", "unresolved", "foreign", "wrong-transaction", "void");

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]).toAbsolutePath().normalize();
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    int closedHistory = args.length > 1 ? Integer.parseInt(args[1]) : 0;
    try (var blue = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      verify(runtime.processor(blue), closedHistory);
    }
  }

  private static void verify(Contracts engine, int closedHistory) {
    var payouts = map();
    for (String key : PAYOUTS) {
      var terms = map("payoutKey", key, "grossMinor", GROSS, "feeMinor", FEE, "netMinor", NET, "currency", "USD");
      String transaction = "transaction-" + key;
      boolean isVoid = key.equals("void");
      var requests = isVoid ? map("payout-void", map("status", "succeeded"))
          : map("payout-capture", map("status", key.equals("unresolved") ? "unknown" : "succeeded"));
      var payout = map("name", "Payout " + key, "type", "MyOS/MyOS Test Account to Account Payment Instruction",
          "contracts", map("guarantor", channel("guarantor"), "payer", channel("payer"), "payee", channel("payee")),
          "clauses", map("receiptFixture", map(
              "type", map("type", "Connections/Connected Clause", "actions", map("confirm", map("do", List.of(
                  map("$appendChange", map("op", "add", "path", "/accountSettlement", "val", map("$var", "params"))))))),
              "bindings", map("confirm", map("confirmFixtureReport", map("on", "workflow", "party", "guarantor",
                  "params", map("$object", map("$var", "trigger"))))))),
          "paymentDetails", map("payoutTerms", terms),
          "payment", map("accepted", true, "completed", isVoid ? 0 : NET, "secured", 0, "reversed", 0, "transactionId", transaction,
              "requests", requests));
      payouts.put(key, payout);
    }

    var source = map("name", "Payout Recovery Fixture", "type", "Agreements/Agreement with Clauses",
        "contracts", map("merchant", channel("merchant")), "activation", map("active", false), "payouts", payouts, "entries", map(),
        "clauses", map(
            "commission", ledger("/commission", "Parties/Document Access Restored", false, true),
            "otherCommission", ledger("/otherCommission", "Activation/Terms Accepted", true, true),
            "offCommission", ledger("/offCommission", "Activation/Terms Accepted", true, false),
            "fixture", fixtureClauses()));
    var current = applied(engine.initialize(source), "initialize");
    var entries = map();
    var history = map();
    for (int index = 0; index < closedHistory; index++)
      history.put("closed-" + index, map("status", "closed", "amountMinor", GROSS, "paidMinor", 0));
    var reservations = new LinkedHashMap<>(history);
    var reports = map();
    for (String key : PAYOUTS) {
      String path = "/payouts/" + key;
      String origin = storedOrigin(engine, current.document(), path);
      String entryOrigin = key.equals("foreign") ? "another-initialized-instruction" : origin;
      entries.put(NativeRuntime.identity(engine.execution().values().source(key)),
          map("key", key, "path", path, "status", "usable", "documentOrigin", entryOrigin));
      reservations.put(key, map("status", "reserved", "amountMinor", GROSS));
      if (hasReport(key)) {
        reports.put(key, map("payoutKey", key, "grossMinor", GROSS, "feeMinor", FEE, "netMinor", NET, "currency", "USD",
            "payoutTerms", engine.read(current.document(), path + "/paymentDetails/payoutTerms"),
            "transactionId", key.equals("wrong-transaction") ? "another-transaction" : "transaction-" + key,
            "instructionOrigin", origin));
      }
    }
    int initialReserved = PAYOUTS.size() * GROSS;
    var state = map("accrued", initialReserved, "paid", 0, "reserved", initialReserved, "settlements", reservations);
    current = apply(engine, current.document(), "seedFixture",
        map("entries", entries, "ledger", state, "accrued", initialReserved, "history", history), 1);
    for (String key : PAYOUTS)
      current = apply(engine, current.document(), "reserveFixture", map("key", key, "amountMinor", GROSS), 2);
    for (String key : PAYOUTS) {
      if (!hasReport(key)) continue;
      @SuppressWarnings("unchecked") var proof = (Map<String, Object>) reports.get(key);
      current = apply(engine, current.document(), "/payouts/" + key, "guarantor", "confirmFixtureReport", proof, 3);
    }
    current = apply(engine, current.document(), "accessFixture", map(), 4);
    checkTotals(engine, current.document(), "/commission", 0, initialReserved);
    checkNoQualifiedPayout(engine, current, "Inactive agreement");
    current = apply(engine, current.document(), "activateFixture", map(), 5);
    equal(true, engine.read(current.document(), "/activation/active"), "Fixture sets the readiness condition");
    var report = (Map<?, ?>) reports.get("first");
    equal(report.get("instructionOrigin"), storedOrigin(engine, current.document(), "/payouts/first"),
        "Selected payout origin survives the fixture write");

    current = apply(engine, current.document(), "scopedFixture",
        map("clause", "commission", "key", "first", "instructionOrigin", "another-origin"), 6);
    checkTotals(engine, current.document(), "/commission", 0, initialReserved);
    current = apply(engine, current.document(), "scopedFixture",
        map("clause", "offCommission", "key", "first", "instructionOrigin", report.get("instructionOrigin")), 7);
    checkTotals(engine, current.document(), "/offCommission", 0, initialReserved);

    current = apply(engine, current.document(), "accessFixture", map(), 8);
    long closes = events(engine, current, "Settlement Closed");
    long candidates = events(engine, current, "MyOS Payout Settlement Ready");
    if (closes != 3 || candidates != 3) {
      var definition = engine.read(current.document(), "/contracts");
      if (definition instanceof Map<?, ?> deployed)
        System.err.println("Commission connections: " + deployed.keySet().stream()
            .filter(key -> key.toString().contains("commission")).toList());
      System.err.println("Readiness " + engine.read(current.document(), "/activation/active")
          + ", reserved " + engine.read(current.document(), "/commission/reserved")
          + ", ledger gas " + current.gas());
      throw new AssertionError("Expected three scoped settlement wakes and closes, got "
          + candidates + " wakes and " + closes + " closes. Events: " + ClauseGasProbe.eventData(engine, current));
    }
    checkQualifiedPayouts(engine, current.document(), "/commission");
    checkTotals(engine, current.document(), "/otherCommission", 0, initialReserved);
    checkTotals(engine, current.document(), "/offCommission", 0, initialReserved);
    equal(1L, events(engine, current, "Fixture Recovery Accepted"), "Eligible evidence runs the authored after hook once");
    System.out.println("PASS two equal-sized transfers close cumulatively and terminal void releases once;"
        + " historicalClosed=" + closedHistory + " gas=" + current.gas());

    current = apply(engine, current.document(), "termsFixture", map(), 9);
    checkQualifiedPayouts(engine, current.document(), "/otherCommission");
    checkQualifiedPayouts(engine, current.document(), "/commission");
    checkTotals(engine, current.document(), "/offCommission", 0, initialReserved);
    equal(3L, events(engine, current, "Settlement Closed"), "Only the ledger listening to terms recovers");
    System.out.println("PASS inherited Connections default route works, disabled and differently addressed ledgers stay unchanged");

    current = apply(engine, current.document(), "accessFixture", map(), 10);
    checkQualifiedPayouts(engine, current.document(), "/commission");
    checkNoQualifiedPayout(engine, current, "Restore replay");
    for (int index = 0; index < closedHistory; index++) {
      String path = "/commission/settlements/closed-" + index;
      equal("closed", engine.read(current.document(), path + "/status"), path);
      amount(engine, current.document(), path + "/paidMinor", 0);
    }
    System.out.println("PASS missing report, unknown request, foreign origin and exact replay preserve ledger; gas=" + current.gas());
  }

  private static Map<String, Object> ledger(String state, String event, boolean inherited, boolean enabled) {
    var connection = map("resume", map("on", "event", "event", map("type", event),
        "after", List.of(map("$appendEvent", map("type", "Events/Event", "kind", "Fixture Recovery Accepted")))));
    var definition = inherited
        ? map("type", "MyOS/Payout Ledger Clause", "defaultBindings", map("reconcilePayouts", connection))
        : "MyOS/Payout Ledger Clause";
    var bindings = map("state", state, "payouts", "/payouts", "payoutEntries", "/entries");
    if (state.equals("/commission"))
      bindings.put("reserve", map("reserveFixture", map("on", "workflow", "party", "merchant")));
    bindings.put("observePayout", map("managePayoutCollection", map("on", "collection", "path", "/payouts",
        "event", map("type", "Events/Event", "kind", "Unused Fixture Event"))));
    if (!enabled) bindings.put("reconcilePayouts", map());
    else if (!inherited) bindings.put("reconcilePayouts", connection);
    return map("type", definition, "bindings", bindings);
  }

  private static Map<String, Object> fixtureClauses() {
    var actions = map(
        "seed", map("do", List.of(change("/entries", "entries"), change("/commission/accrued", "accrued"),
            change("/commission/settlements", "history"),
            change("/otherCommission", "ledger"), change("/offCommission", "ledger"))),
        "activate", map("do", List.of(map("$appendChange", map("op", "replace", "path", "/activation/active", "val", true)))),
        "access", map("do", List.of(map("$appendEvent", map("type", "Parties/Document Access Restored", "revision", 1)))),
        "terms", map("do", List.of(map("$appendEvent", map("type", "Activation/Terms Accepted", "revision", 2, "party", "merchant")))),
        "scoped", map("do", List.of(map("$appendEvent", map("$merge", List.of(
            map("type", "Events/Event", "kind", "MyOS Payout Settlement Ready"), map("$var", "params")))))));
    var bindings = map();
    for (String action : actions.keySet()) {
      bindings.put(action, map(action + "Fixture", map("on", "workflow", "party", "merchant",
          "params", map("$object", map("$var", "trigger")))));
    }
    return map("type", map("type", "Connections/Connected Clause", "actions", actions), "bindings", bindings);
  }

  private static Map<String, Object> change(String path, String field) {
    return map("$appendChange", map("op", "replace", "path", path, "val", map("$var", map("name", "params", "path", "/" + field))));
  }

  private static Object channel(String actor) {
    return map("type", "Contracts/External Channel", "event", map("source", actor));
  }

  private static boolean hasReport(String key) {
    return !key.equals("missing-report") && !key.equals("void");
  }

  private static Contracts.Result apply(Contracts engine, Contracts.Document current, String operation,
      Map<String, Object> request, int time) {
    return apply(engine, current, "", "merchant", operation, request, time);
  }

  private static Contracts.Result apply(Contracts engine, Contracts.Document current, String path, String actor,
      String operation, Map<String, Object> request, int time) {
    String document = path.isEmpty() ? current.blueId() : identityAt(engine, current, path);
    Object event = map("source", actor, "operation", map("type", "Contracts/Operation Request", "channel", actor,
        "operation", operation, "document", map("blueId", document), "requireExactDocumentVersion", true, "request", request));
    return applied(engine.process(current, event, time), operation);
  }

  private static Contracts.Result applied(Contracts.Result result, String operation) {
    if (!result.commits()) throw new AssertionError(operation + " status=" + result.status() + " "
        + ClauseGasProbe.diagnostic(result));
    return result;
  }

  private static long events(Contracts engine, Contracts.Result result, String kind) {
    return ClauseGasProbe.eventData(engine, result).stream()
        .filter(event -> event instanceof Map<?, ?> row && kind.equals(row.get("kind")))
        .count();
  }

  private static String storedOrigin(Contracts engine, Contracts.Document document, String path) {
    return identityAt(engine, document, path + "/contracts/initialized/document");
  }

  private static String identityAt(Contracts engine, Contracts.Document document, String path) {
    var values = engine.execution().values();
    return NativeRuntime.identity(values.exact(values.select(new Exact.Ref(document.blueId()), path)));
  }

  private static void checkNoQualifiedPayout(Contracts engine, Contracts.Result result, String context) {
    equal(0L, events(engine, result, "Settlement Closed"), context + " closure");
    equal(0L, events(engine, result, "MyOS Payout Settlement Ready"), context + " candidate");
    equal(0L, events(engine, result, "Fixture Recovery Accepted"), context + " author hook");
  }

  private static void checkTotals(Contracts engine, Contracts.Document document, String path, int paid, int reserved) {
    amount(engine, document, path + "/accrued", PAYOUTS.size() * GROSS);
    amount(engine, document, path + "/paid", paid);
    amount(engine, document, path + "/reserved", reserved);
  }

  private static void checkQualifiedPayouts(Contracts engine, Contracts.Document document, String path) {
    checkTotals(engine, document, path, 2 * GROSS, (PAYOUTS.size() - 3) * GROSS);
    for (String key : List.of("first", "second", "void")) {
      String reservation = path + "/settlements/" + key;
      equal("closed", engine.read(document, reservation + "/status"), key);
      boolean isVoid = key.equals("void");
      amount(engine, document, reservation + "/paidMinor", isVoid ? 0 : GROSS);
      amount(engine, document, reservation + "/feeMinor", isVoid ? 0 : FEE);
      amount(engine, document, reservation + "/transferredMinor", isVoid ? 0 : NET);
    }
    for (String key : List.of("missing-report", "unresolved", "foreign", "wrong-transaction")) {
      String reservation = path + "/settlements/" + key;
      equal("reserved", engine.read(document, reservation + "/status"), key);
      equal(blue.bex.Values.UNDEFINED, engine.read(document, reservation + "/paidMinor"), key + " unaltered");
    }
  }

  private static void amount(Contracts engine, Contracts.Document document, String path, int expected) {
    Object actual = engine.read(document, path);
    if (!(actual instanceof Number value) || value.longValue() != expected)
      throw new AssertionError(path + " expected " + expected + " got " + actual);
  }

  private static void equal(Object expected, Object actual, String context) {
    if (!java.util.Objects.equals(expected, actual))
      throw new AssertionError(context + " expected " + expected + " got " + actual);
  }

  private static Map<String, Object> map(Object... pairs) {
    var result = new LinkedHashMap<String, Object>();
    for (int index = 0; index < pairs.length; index += 2) result.put((String) pairs[index], pairs[index + 1]);
    return result;
  }
}
