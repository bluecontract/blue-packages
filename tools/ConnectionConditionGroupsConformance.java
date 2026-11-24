import blue.bex.BexError;
import blue.bex.Values;
import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/** Conditions on grouped and ordinary native workflows. */
public final class ConnectionConditionGroupsConformance {
  private static final List<String> GUARDED = List.of("confirm", "propose", "accept");
  private static final List<String> ACTIONS = List.of("confirm", "propose", "accept", "review");

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]);
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var language = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var processor = runtime.processor(language);
      var groups = map("funding", map("actions", GUARDED, "condition", document("/funded")),
          "empty", map("actions", List.of(), "condition", false));
      var unfunded = initialize(processor, source(false, true, groups));
      for (var name : GUARDED) denied(processor, unfunded, name);
      succeeds(processor, unfunded, "review");
      var skipped = processor.process(unfunded, event(unfunded, "silenced"), 1);
      require(skipped.commits(), "A false connection when still silently skips");
      noEffects(processor, skipped.document(), "confirm");

      var unreviewed = initialize(processor, source(true, false, groups));
      succeeds(processor, unreviewed, "confirm");
      succeeds(processor, unreviewed, "propose");
      denied(processor, unreviewed, "accept");
      denied(processor, unreviewed, "review");
      var ready = initialize(processor, source(true, true, groups));
      succeeds(processor, ready, "accept");

      var missing = initialize(processor, source(true, true, map("missing", map("actions", List.of("propose")))));
      denied(processor, missing, "propose");
      succeeds(processor, missing, "confirm");

      var invalid = source(true, true, map("typo", map("actions", List.of("confirm", "prosoe"), "condition", true)));
      require(!processor.initialize(invalid).commits(), "Unknown group action must fail to initialize");
      fails("CONNECTION_UNKNOWN_CONDITION_ACTION", () -> ClauseGasProbe.diagnose(processor, invalid));
      typedConditions(processor);
      System.out.println("PASS grouped guard, legacy conjunction, skip, empty group, missing predicate, and unknown action");
    }
  }

  private static void typedConditions(Contracts processor) {
    var pointer = map("$var", map("name", "conditionInputs", "path", "/source"));
    var condition = map("$and", List.of(map("$isKind", map("val", pointer, "kind", "text")),
        map("$eq", List.of(map("$document", pointer), true))));
    var type = map("name", "Document flag condition", "inputs", map(), "condition", condition);
    var first = map("type", type, "actions", List.of("confirm", "accept"), "inputs", map("source", "/funded"));
    var second = map("type", type, "actions", List.of("propose", "accept"), "inputs", map("source", "/otherFunding"));
    var groups = map("aRenamedCondition", first, "zOtherCondition", second);

    var firstOnly = source(true, true, groups);
    firstOnly.put("otherFunding", false);
    var firstReady = initialize(processor, firstOnly);
    succeeds(processor, firstReady, "confirm");
    denied(processor, firstReady, "propose");
    denied(processor, firstReady, "accept");

    var secondOnly = source(false, true, groups);
    secondOnly.put("otherFunding", true);
    var secondReady = initialize(processor, secondOnly);
    denied(processor, secondReady, "confirm");
    succeeds(processor, secondReady, "propose");
    denied(processor, secondReady, "accept");

    var both = source(true, true, groups);
    both.put("otherFunding", true);
    succeeds(processor, initialize(processor, both), "accept");

    var expressionInput = map("type", type, "actions", List.of("propose"),
        "inputs", map("source", map("$literal", "/funded")));
    denied(processor, initialize(processor, source(true, true, map("literalInput", expressionInput))), "propose");
    var unbound = map("type", type, "actions", List.of("propose"));
    denied(processor, initialize(processor, source(true, true, map("unboundInput", unbound))), "propose");
    System.out.println("PASS independently bound inherited conditions and literal inputs");
  }

  private static Map<String, Object> source(boolean funded, boolean reviewed, Object groups) {
    var actions = map();
    var bindings = map();
    for (var name : ACTIONS) {
      actions.put(name, map("preflight", List.of(effect("/preflight/" + name),
              map("$set", map("name", "actionResult", "expr", map("outcome", "acceptedNew")))),
          "do", List.of(effect("/effects/" + name))));
      bindings.put(name, map(name, map("on", "workflow", "party", "seller",
          "before", List.of(effect("/before/" + name)))));
    }
    bindings.put("confirm", map("confirm", map("on", "workflow", "party", "seller",
            "before", List.of(effect("/before/confirm"))),
        "silenced", map("on", "workflow", "party", "seller", "when", false)));
    var feature = map("type", "Features/Feature Clause", "parameters", map("actions", actions,
        "conditionGroups", groups, "conditions", map("accept", document("/reviewed"), "review", document("/reviewed"))),
        "bindings", bindings);
    var seller = map("type", "Parties/Party", "lead", map("channel",
        map("type", "Contracts/External Channel", "event", map("source", "seller"))),
        "myosAccountId", "seller-account", "readerKeys", List.of("reader-seller"));
    return map("type", "Orders/Order with Clauses", "name", "Grouped workflow conditions",
        "funded", funded, "reviewed", reviewed, "preflight", map(), "before", map(), "effects", map(),
        "clauses", map("activation", map("type", "Activation/Activation Clause",
            "parameters", map("parties", map("seller", seller), "required", List.of())), "feature", feature));
  }

  private static Object document(String path) {
    return map("$document", path);
  }

  private static Object effect(String path) {
    return map("$appendChange", map("op", "add", "path", path, "val", true));
  }

  private static Contracts.Document initialize(Contracts processor, Object source) {
    var result = processor.initialize(source);
    if (!result.commits()) ClauseGasProbe.diagnose(processor, source);
    require(result.commits(), OperationInputConformance.initializationDiagnostic(processor, result));
    return result.document();
  }

  private static Object event(Contracts.Document document, String operation) {
    return map("source", "seller", "operation", map("type", "Contracts/Operation Request", "channel", "seller",
        "operation", operation, "request", map(), "document", map("blueId", document.blueId()),
        "requireExactDocumentVersion", true));
  }

  private static void succeeds(Contracts processor, Contracts.Document document, String operation) {
    var event = event(document, operation);
    var result = processor.process(document, event, 1);
    if (!result.commits()) ClauseGasProbe.diagnose(processor, document, event, 1);
    require(result.commits(), operation + " must complete");
    for (var stage : List.of("preflight", "before", "effects")) {
      require(Boolean.TRUE.equals(processor.read(result.document(), "/" + stage + "/" + operation)),
          operation + " must reach " + stage);
    }
  }

  private static void denied(Contracts processor, Contracts.Document document, String operation) {
    var event = event(document, operation);
    var result = processor.process(document, event, 1);
    require(processor.emitted(result).isEmpty(), operation + " unexpectedly emitted an event");
    noEffects(processor, result.commits() ? result.document() : document, operation);
    fails("ACTION_CONDITION_FAILED", () -> ClauseGasProbe.diagnose(processor, document, event, 1));
  }

  private static void noEffects(Contracts processor, Contracts.Document document, String operation) {
    for (var stage : List.of("preflight", "before", "effects")) {
      require(processor.read(document, "/" + stage + "/" + operation) == Values.UNDEFINED,
          operation + " unexpectedly reached " + stage);
    }
  }

  private static void fails(String expected, Runnable diagnose) {
    try {
      diagnose.run();
      throw new AssertionError("Expected " + expected);
    } catch (BexError error) {
      require(expected.equals(error.getMessage()), "Expected " + expected + ", got " + error.getMessage());
    }
  }

  private static Map<String, Object> map(Object... pairs) {
    return OperationInputConformance.m(pairs);
  }

  private static void require(boolean condition, String message) {
    OperationInputConformance.require(condition, message);
  }
}
