import blue.bex.Compiler;
import blue.bex.BexError;
import blue.contracts.Contracts;
import blue.contracts.ContractException;
import blue.contracts.ContractsExecution;
import blue.contracts.RuntimeBindings;
import blue.language.next.*;
import java.util.*;

/** Publication-time qualification for the standard Connections planner, never runtime authority. */
public final class ComputeDependencies {
  private ComputeDependencies() {}
  // These are the actual constant slots constructed by Connection Planning Functions.
  static final Set<String> SLOTS = Set.of("clauseKey", "connectionKey", "parameters", "bindings",
      "statePath", "sourceMode", "sourcePath", "once", "timerChannel", "resultContract", "hasPreflight");
  private static final Set<String> STATIC = Set.of("type", "itemType", "keyType", "valueType", "schema", "blue");

  @SuppressWarnings("unchecked") static Map<String,Object> map(Object value) {
    return (Map<String,Object>) value;
  }

  static Object qualify(Blue blue, Object authored) {
    try { return qualifyResolved(blue, authored); }
    catch (ContractException failure) {
      if (!failure.code().equals("NEEDS_RESOURCES")) throw failure;
      // No dependency proof is possible without all exact records. Preserve ordinary loading.
      System.err.println("Compute dependency selection skipped: " + failure.code() + " " + failure.context());
      return authored;
    }
  }

  private static Object qualifyResolved(Blue blue, Object authored) {
    var values = new Contracts(blue, RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
    var clause = values.source(authored, "definition");
    var selectedDefinition = values.select(clause, "/actionDefinition/type");
    var selectedHook = values.select(clause, "/hookDefinition");
    if (selectedDefinition == null || selectedHook == null) return authored;
    var hook = values.exact(selectedHook);
    var functions = values.select(hook, "/functions");
    if (functions == null || !values.head(functions).fields.containsKey("selectConnectionCompute")) return authored;
    var planner = standardPlanner(values, hook);
    if (planner == null) return authored;
    var qualified = new LinkedHashMap<>(index(values, values.exact(selectedDefinition)));
    if (qualified.isEmpty()) return authored;
    qualified.putAll(planner);
    var inherited = values.select(hook, "/constants/computeDependencyIndexes");
    if (inherited == null || qualified.isEmpty()) return authored;
    String definitionId = qualified.get("definitionId").toString();
    if (values.head(inherited).fields.containsKey(definitionId)) return authored;
    // Add a qualified exact definition without changing frozen entries inherited from a base clause.
    var localHook = map(map(authored).getOrDefault("hookDefinition", Map.of()));
    var localConstants = map(localHook.getOrDefault("constants", Map.of()));
    if (localHook.containsKey("blueId") || localConstants.containsKey("blueId")) return authored;
    var emittedHook = new LinkedHashMap<>(localHook);
    var constants = new LinkedHashMap<>(localConstants);
    var indexes = new LinkedHashMap<>(map(constants.getOrDefault("computeDependencyIndexes", Map.of())));
    if (indexes.containsKey("blueId")) return authored;
    indexes.put(definitionId, qualified);
    constants.put("computeDependencyIndexes", indexes);
    emittedHook.put("constants", constants);
    var result = new LinkedHashMap<>(map(authored));
    // This constant belongs to the published executable hook, not mutable clause parameters.
    result.put("hookDefinition", emittedHook);
    return result;
  }

  static Map<String,Object> index(ContractsExecution.Values values, Exact definition) {
    var library = new LinkedHashMap<String,Object>();
    for (String field : List.of("functions", "constants")) {
      var selected = values.select(definition, "/" + field);
      library.put(field, selected == null ? Map.of() : values.bexData(values.exact(selected)));
    }
    // Host-provided intrinsics require an execution capability context unavailable here.
    if (containsIntrinsic(library.get("functions"))) return Map.of();
    var slots = new TreeMap<String,Object>();
    SLOTS.forEach(name -> slots.put(name, false));
    var generatedFunctions = new TreeMap<String,Object>();
    for (String name : List.of("connectionSnapshots", "connectionConfiguration"))
      generatedFunctions.put(name, Map.of("args", Map.of(), "expr", Map.of()));
    var missingConstants = new TreeMap<>(slots);
    missingConstants.keySet().removeAll(map(library.get("constants")).keySet());
    var missingFunctions = new TreeMap<>(generatedFunctions);
    missingFunctions.keySet().removeAll(map(library.get("functions")).keySet());
    // Validate the whole library. Only genuinely external generated slots are supplied.
    try {
      new Compiler().compile(Map.of("constants", missingConstants, "functions", missingFunctions, "do", List.of()), library, null);
    } catch (BexError failure) {
      // A generated override may repair a library declaration. Preserve that valid
      // existing composition without claiming a full-library publication proof.
      new Compiler().compile(Map.of("constants", slots, "functions", generatedFunctions, "do", List.of()), library, null);
      return Map.of();
    }
    var functions = new TreeMap<String,Object>();
    var required = new TreeSet<String>();
    var requiredFunctions = new TreeSet<String>();
    for (var function : map(library.get("functions")).entrySet()) {
      var references = references(function.getValue());
      required.addAll(references.constants);
      requiredFunctions.addAll(references.functions);
      var original = values.select(definition, "/functions/" + escape(function.getKey()));
      functions.put(function.getKey(), Map.of(
          "id", NativeRuntime.identity(values.exact(original)),
          "functions", List.copyOf(references.functions), "constants", List.copyOf(references.constants),
          "argsId", NativeRuntime.identity(values.source(map(function.getValue()).getOrDefault("args", Map.of()), "definition")),
          "safe", references.safe));
    }
    var constants = new TreeMap<String,Object>();
    for (String name : map(library.get("constants")).keySet())
      constants.put(name, NativeRuntime.identity(values.exact(values.select(definition, "/constants/" + escape(name)))));
    var specification = values.head(definition).specification;
    return Map.of("format", "connections-compute-dependencies/1",
        "definitionId", NativeRuntime.identity(values.exact(definition)),
        "functions", functions, "constants", constants, "requiredConstants", List.copyOf(required),
        "requiredFunctions", List.copyOf(requiredFunctions),
        "specificationId", specification == null ? "" : NativeRuntime.identity(specification));
  }

  private static Map<String,Object> standardPlanner(ContractsExecution.Values values, Exact hook) {
    Exact canonical;
    try { canonical = values.source(Map.of("type", "Connections/Connection Plan"), "definition"); }
    catch (ContractException unavailable) { return null; }
    var pending = new ArrayList<String>(List.of("plan"));
    var seen = new HashSet<String>();
    var constants = new HashSet<String>();
    while (!pending.isEmpty()) {
      String name = pending.removeLast();
      if (!seen.add(name)) continue;
      String path = "/functions/" + escape(name);
      var expected = values.select(canonical, path);
      var actual = values.select(hook, path);
      if (expected == null || actual == null || !NativeRuntime.identity(values.exact(expected)).equals(
          NativeRuntime.identity(values.exact(actual)))) return null;
      var dependencies = references(values.bexData(values.exact(expected)));
      pending.addAll(dependencies.functions);
      constants.addAll(dependencies.constants);
    }
    // This single declared slot is the publisher's output; every other used
    // constant, including declarations of framework-supplied values, must match.
    constants.remove("computeDependencyIndexes");
    var constantIds = new TreeMap<String,Object>();
    for (String name : constants) {
      var expected = values.select(canonical, "/constants/" + escape(name));
      var actual = values.select(hook, "/constants/" + escape(name));
      if (expected == null && actual == null) { constantIds.put(name, ""); continue; }
      if (expected == null || actual == null || !NativeRuntime.identity(values.exact(expected)).equals(
          NativeRuntime.identity(values.exact(actual)))) return null;
      constantIds.put(name, NativeRuntime.identity(values.exact(actual)));
    }
    return Map.of("plannerFunctionsId", NativeRuntime.identity(values.exact(values.select(hook, "/functions"))),
        "plannerConstants", constantIds);
  }

  static final class References {
    final Set<String> functions = new TreeSet<>(), constants = new TreeSet<>();
    boolean safe = true;
  }

  static References references(Object code) {
    var result = new References();
    var pending = new ArrayList<Object>();
    pending.add(code);
    while (!pending.isEmpty()) {
      Object value = pending.removeLast();
      if (value instanceof List<?> list) { pending.addAll(list); continue; }
      if (!(value instanceof Map<?,?> raw)) continue;
      var node = map(raw);
      boolean operator = node.size() == 1;
      if (operator && node.containsKey("$literal")) continue;
      if (operator) {
        if (node.containsKey("$currentContract")) result.safe = false;
        for (String read : List.of("$document", "$resultValue"))
          if (node.containsKey(read) && !outsideContracts(node.get(read))) result.safe = false;
        if (node.containsKey("$call")) result.functions.add((String) map(node.get("$call")).get("function"));
        if (node.containsKey("$const")) {
          Object read = node.get("$const");
          result.constants.add(read instanceof String name ? name : (String) map(read).get("name"));
        }
      }
      node.forEach((name, child) -> { if (!STATIC.contains(name)) pending.add(child); });
    }
    return result;
  }

  private static boolean outsideContracts(Object read) {
    Object path = read;
    if (path instanceof Map<?,?> map && map.containsKey("path")) path = map.get("path");
    boolean exact = true;
    if (path instanceof Map<?,?> map && map.get("$concat") instanceof List<?> parts && !parts.isEmpty()) {
      path = parts.getFirst(); exact = false;
    }
    if (!(path instanceof String prefix) || !prefix.startsWith("/") || prefix.equals("/")) return false;
    // A known complete first path segment cannot select a generated contract.
    int slash = prefix.indexOf('/', 1);
    String segment = slash < 0 ? prefix.substring(1) : prefix.substring(1, slash);
    return !segment.equals("contracts") && (slash >= 0 || exact || !"contracts".startsWith(segment));
  }

  private static boolean containsIntrinsic(Object value) {
    if (value instanceof Map<?,?> map) {
      if (map.size() == 1 && map.containsKey("$literal")) return false;
      if (map.size() == 1 && map.containsKey("$intrinsic")) return true;
      return map.values().stream().anyMatch(ComputeDependencies::containsIntrinsic);
    }
    return value instanceof List<?> list && list.stream().anyMatch(ComputeDependencies::containsIntrinsic);
  }

  private static String escape(String name) { return name.replace("~", "~0").replace("/", "~1"); }
}
