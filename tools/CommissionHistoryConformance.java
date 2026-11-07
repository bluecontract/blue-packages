import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native inactive selection boundary. Financial/history qualification is a separate scenario. */
public final class CommissionHistoryConformance {
  static Object originalProviderSlots;
  static Map<String,Object> m(Object... x) { return BootstrapPreparationConformance.m(x); }
  static Map<String,Object> o(Object x) { return BootstrapPreparationConformance.obj(x); }
  static Contracts.Result ok(Contracts.Result x) { return BootstrapPreparationConformance.applied(x); }
  static void check(boolean b, String message) { BootstrapPreparationConformance.require(b, message); }
  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]);
    if (args.length > 2) originalProviderSlots = WireData.json(Files.readString(Path.of(args[2])));
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    if (args.length > 1 && args[1].equals("access")) {
      BootstrapPreparationConformance.bootstrapAccessGuards(packages);
      return;
    }
    for (boolean selectInactive : args.length > 1 && args[1].equals("guards") ? List.of(true) : List.of(false, true)) {
      try (var blue = packages.language(); var runtime = new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
        var p = runtime.processor(blue);
        var source = BootstrapPreparationConformance.source(null);
        source.put("orders", m());
        var orders = o(o(source.get("clauses")).get("orders"));
        var parameters = o(orders.get("parameters"));
        parameters.put("suppliedParties", List.of());
        var activation = o(o(o(o(parameters.get("template")).get("clauses")).get("activation")).get("parameters"));
        o(activation.get("parties")).remove("customer");
        activation.put("required", List.of("seller"));
        var authored = o(WireData.parse(Files.readString(root.resolve("clause-documents/types/admission-functions.blue")), "yaml"));
        var definitionValues = p.execution().values();
        var authoredDefinition = definitionValues.source(m("type", authored), "definition");
        var publishedDefinition = definitionValues.source(m("type", "Documents/Document Preparation Functions"), "definition");
        var functions = m();
        for (String name : o(definitionValues.bexData(definitionValues.select(publishedDefinition, "/functions"))).keySet()) {
          functions.put(name, m("blueId", NativeRuntime.identity(definitionValues.exact(definitionValues.select(publishedDefinition, "/functions/" + name)))));
        }
        String candidateStageId = NativeRuntime.identity(definitionValues.exact(definitionValues.select(authoredDefinition, "/functions/candidateStage")));
        functions.put("candidateStage", m("blueId", candidateStageId));
        functions.put("maySelectInactiveCandidate", m("args", m(), "do", List.of(m("$return", selectInactive))));
        // Match Reseller's closed Compute Definition: refining the inherited function
        // would merge its do-list positionally rather than replace executable code.
        var originalClause = definitionValues.source(m("type", "Documents/Documents Clause"), "definition");
        var clauseType = m("type", "Clauses/Clause");
        for (String name : definitionValues.head(originalClause).fields.keySet()) {
          if (!name.equals("actionDefinition")) clauseType.put(name,
              definitionValues.literal(definitionValues.exact(definitionValues.select(originalClause, "/" + name))));
        }
        clauseType.put("actionDefinition", m("type", m("type", "Contracts/Compute Definition", "functions", functions)));
        orders.put("type", clauseType);
        var declared = definitionValues.source(source);
        check(candidateStageId.equals(NativeRuntime.identity(definitionValues.exact(definitionValues.select(declared,
            "/clauses/orders/actionDefinition/functions/candidateStage")))), "Exact authored staging function must survive native projection");
        if (args.length > 1 && args[1].equals("projection")) {
          System.out.println("PASS exact native candidateStage projection authoredOptIn=" + selectInactive);
          continue;
        }
        var host = ok(p.initialize(source));
        var approveEvent = BootstrapPreparationConformance.event(host.document(), "approve_merchant", m("revision", 1));
        var approved = p.process(host.document(), approveEvent, 1);
        if (!approved.commits()) ClauseGasProbe.diagnose(p, host.document(), approveEvent, 1);
        host = ok(approved);
        host = ok(p.process(host.document(), BootstrapPreparationConformance.event(host.document(), "prepareOrder", m(
            "type", "Documents/Preparation Input", "key", "one", "values", m("size", 42))), 2));
        var item = o(o(p.read(host.document(), "/process_orders/entries")).values().iterator().next());
        var values = p.execution().values();
        var prepared = values.literal(values.exact(values.select(new Exact.Ref(host.document().blueId()), item.get("itemPath") + "/prepared")));
        var child = ok(p.initialize(prepared));
        check(!Boolean.TRUE.equals(p.read(child.document(), "/activation/active")), "Order must remain commercially inactive");
        if (selectInactive) stagingGuards(root, p, host.document(), child.document(), item);
        var request = m("type", "Documents/Provision Input", "key", item.get("key"), "inResponseTo", item.get("requestId"),
            "requirementRef", item.get("requirementRef"), "document", m("blueId", child.document().blueId()));
        host = ok(p.process(host.document(), BootstrapPreparationConformance.event(host.document(), "provideOrder", request), 3));
        var status = p.read(host.document(), item.get("itemPath") + "/status");
        var embedded = o(p.read(host.document(), "/orders")).containsKey("one");
        System.out.println("Native inactive candidate: authoredOptIn=" + selectInactive + " status=" + status + " embedded=" + embedded);
        check((selectInactive ? "selected" : "awaiting_activation").equals(status), "Authored inactive-selection policy must determine stage");
        check(embedded == selectInactive, "Only explicit authored policy may embed inactive Order");
      }
    }
  }
  static void stagingGuards(Path sourceRoot, Contracts p, Contracts.Document host, Contracts.Document child, Map<String,Object> item) throws Exception {
    var values = p.execution().values();
    var root = new Exact.Ref(host.blueId());
    String step = "/contracts/provideOrder/steps/0";
    var functions = new LinkedHashMap<>(o(values.bexData(values.select(root, step + "/definition/functions"))));
    // Qualify the shipped Reseller action library, not a test-only copy of its hook.
    var shipped = values.source(m("type", "Reseller/Customer Orders Bootstrap Clause"), "definition");
    functions.putAll(o(values.bexData(values.select(shipped, "/actionDefinition/functions"))));
    // ContractRun: definition functions first, generated step-local functions last.
    functions.putAll(o(values.bexData(values.select(root, step + "/functions"))));

    for (var entry : functions.entrySet()) {
      if (entry.getValue() instanceof Map<?,?> ref && ref.get("blueId") instanceof String id)
        entry.setValue(values.bexData(new Exact.Ref(id)));
    }
    var expression = m("functions", functions, "constants", values.bexData(values.select(root, step + "/constants")),
        "expr", m("$call", m("function", "candidateStage", "args", m("checked", m(
            "item", m("$binding", "input/item"), "candidate", m("$binding", "input/candidate"),
            "origin", m("$binding", "input/origin"))))));
    var original = values.exact(values.select(new Exact.Ref(child.blueId()), "/contracts/initialized/document"));
    if (originalProviderSlots != null) providerSlotsParity(sourceRoot, p, root, child, item, functions, o(expression.get("constants")));
    for (String variant : List.of("valid", "changed-configuration", "missing-configuration")) {
      Object checkedItem = m("$binding", "input/item");
      if (!variant.equals("valid")) checkedItem = m("$pointerSet", m("object", checkedItem,
          "path", "/intent/configuration", "op", variant.equals("missing-configuration") ? "remove" : "set",
          "val", "foreign-configuration"));
      o(o(o(expression.get("expr")).get("$call")).get("args")).put("checked", m(
          "item", checkedItem, "candidate", m("$binding", "input/candidate"), "origin", m("$binding", "input/origin")));
      var input = values.source(m("item", m("blueId", NativeRuntime.identity(values.exact(values.select(root, String.valueOf(item.get("itemPath")))))),
          "candidate", m("blueId", child.blueId()), "origin", NativeRuntime.identity(original)));
      try {
        var result = p.execution().evaluatePredicate(root, input, "input", values.source(expression), 10000000);
        check(variant.equals("valid"), "Changed preparation configuration must reject: " + variant);
        check("ready".equals(o(result.value()).get("status")), "Valid scoped stage");
        check(result.events().isEmpty() && result.changeset().isEmpty(), "Pure stage must not grant authority");
      } catch (blue.bex.BexError error) {
        check(!variant.equals("valid") && error.getMessage().contains("PREPARATION_SELECTION_POLICY_CHANGED"),
            "Unexpected stage denial: " + error);
      }
      System.out.println("PASS native frozen-policy stage " + variant);
    }
    provisionGuards(p, root, child, item);
  }

  static void provisionGuards(Contracts p, Exact host, Contracts.Document child, Map<String,Object> item) {
    var v = p.execution().values();
    String step = "/contracts/provideOrder/steps/0";
    var functions = new LinkedHashMap<>(o(v.bexData(v.select(host, step + "/definition/functions"))));
    functions.putAll(o(v.bexData(v.select(host, step + "/functions"))));
    for (var entry : functions.entrySet()) {
      if (entry.getValue() instanceof Map<?,?> ref && ref.get("blueId") instanceof String id)
        entry.setValue(v.bexData(new Exact.Ref(id)));
    }
    for (String variant : List.of("valid", "wrong-request", "wrong-requirement", "wrong-supplier", "wrong-origin")) {
      var request = m("key", item.get("key"), "inResponseTo", item.get("requestId"),
          "requirementRef", item.get("requirementRef"), "document", m("blueId", child.blueId()));
      String channel = String.valueOf(item.get("supplier"));
      String reason = switch (variant) {
        case "wrong-request" -> "PREPARATION_WRONG_REQUEST";
        case "wrong-requirement" -> "PREPARATION_WRONG_REQUIREMENT";
        case "wrong-supplier" -> "PREPARATION_WRONG_SUPPLIER";
        case "wrong-origin" -> "PREPARATION_UNREVIEWED_SOURCE";
        default -> "";
      };
      if (variant.equals("wrong-request")) request.put("inResponseTo", "foreign-request");
      if (variant.equals("wrong-requirement")) request.put("requirementRef", "foreign-requirement");
      if (variant.equals("wrong-supplier")) channel = "foreign-supplier";
      Object input = m("$binding", "call/request");
      if (variant.equals("wrong-origin")) input = m("$pointerSet", m("object", input,
          "path", "/document/contracts/initialized/document", "op", "set", "val", m("$document", "/contracts/initialized/document")));
      var expression = m("functions", functions, "constants", v.bexData(v.select(host, step + "/constants")),
          "expr", m("$call", m("function", "checkProvision", "args", m("input", input))));
      var inputExact = v.source(m("channel", channel, "request", request));
      var expressionExact = v.source(expression);
      try {
        var result = p.execution().evaluatePredicate(host, inputExact, "call", expressionExact, 10000000);
        check(variant.equals("valid"), "Foreign provision must reject " + variant);
        check("acceptedNew".equals(o(result.value()).get("outcome")), "Full provision positive control");
        check("ready".equals(o(o(result.value()).get("staged")).get("status")), "Opted-in inactive stage");
        check(result.events().isEmpty() && result.changeset().isEmpty(), "Pure full provision check");
      } catch (blue.bex.BexError failure) {
        check(!variant.equals("valid") && failure.getMessage().contains(reason), "Unexpected provision denial " + failure);
      }
      System.out.println("PASS native full provision " + variant);
    }
  }

  static void providerSlotsParity(Path sourceRoot, Contracts p, Exact host, Contracts.Document child, Map<String,Object> item,
      Map<String,Object> functions, Map<String,Object> constants) throws Exception {
    var values = p.execution().values();
    var current = new Exact.Ref(child.blueId());
    var original = values.exact(values.select(current, "/contracts/initialized/document"));
    var authored = o(WireData.parse(Files.readString(sourceRoot.resolve("clause-documents/types/preparation-functions.blue")), "yaml"));
    var wrapper = o(authored.get("functions")).get("validateProviderSlots");
    for (boolean changed : List.of(false, true)) {
      Object candidate = m("$binding", "input/candidate");
      if (changed) candidate = m("$pointerSet", m("object", candidate,
          "path", "/activation/parties/undeclared", "op", "set", "val", m("$binding", "input/candidate/activation/parties/seller")));
      for (boolean commonWrapper : List.of(false, true)) {
        var library = new LinkedHashMap<>(functions);
        library.put("validateProviderSlots", commonWrapper ? wrapper : originalProviderSlots);
        var expression = m("functions", library, "constants", constants, "expr", m("$call", m(
            "function", "validateProviderSlots", "args", m("original", m("$binding", "input/original"),
                "candidate", candidate, "item", m("$binding", "input/item")))));
        boolean denied = false;
        try {
          var result = p.execution().evaluatePredicate(host, values.source(m("original", m("blueId", NativeRuntime.identity(original)),
              "candidate", m("blueId", child.blueId()), "item", m("blueId", NativeRuntime.identity(values.exact(values.select(host, String.valueOf(item.get("itemPath")))))))), "input", values.source(expression), 10000000);
          check(result.events().isEmpty() && result.changeset().isEmpty(), "Provider guard must be pure");
        } catch (blue.bex.BexError failure) {
          check(failure.getMessage().contains("PREPARATION_UNDECLARED_PARTY"), "Unexpected provider guard error " + failure);
          denied = true;
        }
        check(denied == changed, "Original/shared provider guard parity");
      }
      System.out.println("PASS native provider-slot common implementation changedRoster=" + changed);
    }
  }

}
