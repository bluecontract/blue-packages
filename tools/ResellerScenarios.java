package blue.packages;

import blue.bex.Values;
import blue.contracts.Contracts;
import blue.contracts.ContractsExecution;
import blue.contracts.RuntimeBindings;
import blue.language.next.Blue;
import blue.language.next.BluePackage;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.language.next.PackageBundle;
import blue.language.next.WireData;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Runs authored source through an explicitly selected native Blue Contracts runtime.
 * Does not evaluate pricing, compile BEX, replace channels, or supply business results.
 * The runtime configuration contains independently verified exact provider records
 * and aliases. It is not a substitute for package release qualification.
 */
public final class ResellerScenarios {
  private final Path sourcePath;
  private final Path scenarioPath;
  private final Path reportPath;
  private final Path runtimePath;
  private final Map<String, Object> runtime;
  private final RuntimeBindings bindings;
  private final PackageBundle bundle;
  private final List<Object> packageEvidence = new ArrayList<>();

  private ResellerScenarios(String[] args, RuntimeBindings bindings) throws Exception {
    this.bindings = bindings;
    if (args.length != 4) {
      throw new IllegalArgumentException(
          "Usage: ResellerScenarios SOURCE SCENARIOS REPORT RUNTIME_CONFIG");
    }
    sourcePath = Path.of(args[0]).toAbsolutePath();
    scenarioPath = Path.of(args[1]).toAbsolutePath();
    reportPath = Path.of(args[2]).toAbsolutePath();
    runtimePath = Path.of(args[3]).toAbsolutePath();
    runtime = object(parse(runtimePath));
    var packages = PackageBundle.builder();
    for (Object raw : array(runtime.getOrDefault("packages", List.of()))) {
      Map<String, Object> pin = object(raw);
      Path archive = runtimePath.getParent().resolve(text(pin.get("path"))).normalize();
      String archiveHash = hash(archive);
      equal(pin.get("archiveSha256"), archiveHash, "Package archive differs: " + archive);
      BluePackage publication = BluePackage.open(archive, text(pin.get("packageBlueId")));
      bindings.require(publication);
      packages.mount(text(pin.get("namespace")), publication);
      packageEvidence.add(map("namespace", pin.get("namespace"),
          "packageBlueId", publication.blueId(), "archiveSha256", archiveHash));
    }
    bundle = packages.build();
  }

  public static void main(String[] args) throws Exception {
    int failures = run(args, QualificationRuntime.bindings());
    if (failures != 0) System.exit(1);
  }

  public static int run(String[] args, RuntimeBindings bindings) throws Exception {
    return new ResellerScenarios(args, bindings).run();
  }

  private int run() throws Exception {
    String sourceHash = hash(sourcePath);
    String scenarioHash = hash(scenarioPath);
    String runtimeHash = hash(runtimePath);
    Map<String, Object> specification = object(parse(scenarioPath));
    List<Object> scenarios = specification.containsKey("scenarios")
        ? array(specification.get("scenarios")) : List.of(specification);
    check(!scenarios.isEmpty(), "No native scenarios supplied");
    List<Object> results = new ArrayList<>();
    int failed = 0;
    int selected = 0;
    for (Object raw : scenarios) {
      Map<String, Object> scenario = object(raw);
      String name = text(scenario.getOrDefault("name", "unnamed"));
      String filter = System.getProperty("reseller.scenario");
      if (filter != null && !name.contains(filter)) continue;
      selected++;
      System.out.println("CASE " + selected + " " + name);
      Map<String, Object> evidence = map("name", name, "passed", false);
      long started = System.nanoTime();
      try (Runner runner = new Runner()) {
        evidence.put("captures", runner.captures);
        evidence.put("transitions", runner.transitions);
        Map<String, Object> source = object(parse(sourcePath));
        for (var entry : object(scenario.getOrDefault("sourcePatch", map())).entrySet()) {
          updateExisting(source, entry.getKey(), entry.getValue(), false);
        }
        for (Object pointer : array(scenario.getOrDefault("sourceRemove", List.of()))) {
          updateExisting(source, text(pointer), null, true);
        }
        String initialStatus = text(scenario.getOrDefault("initialStatus", "APPLIED"));
        runner.initialize(source, initialStatus);
        if (initialStatus.equals("APPLIED")) {
          runner.expect(object(scenario.getOrDefault("initial", map())), name + " initial");
          int step = 0;
          for (Object rawStep : array(scenario.getOrDefault("steps", List.of()))) {
            Map<String, Object> row = object(rawStep);
            if (Boolean.TRUE.equals(row.get("restore"))) runner.restore();
            ++step;
            if (row.containsKey("bootstrapPrepared")) runner.bootstrapPrepared(row);
            else runner.operation(row, step);
            runner.expect(row, name + " step " + step + " " + row.get("operation"));
          }
          evidence.put("operations", step);
        } else {
          evidence.put("operations", 0);
        }
        evidence.put("expectedFailures", runner.expectedFailures);
        evidence.put("maxGas", runner.maxGas);
        evidence.put("restores", runner.restores);
        evidence.put("quotes", runner.quoteEvidence);
        evidence.put("captures", runner.captures);
        evidence.put("passed", true);
        System.out.println("CASE PASSED");
      } catch (Throwable failure) {
        failed++;
        evidence.put("errorClass", failure.getClass().getName());
        evidence.put("error", String.valueOf(failure.getMessage()));
        if (failure instanceof blue.language.next.Failure languageFailure) {
          System.out.println(WireData.write(languageFailure.outcome()));
        }
        if (failure instanceof blue.contracts.ContractException contractFailure) {
          System.out.println(contractFailure.diagnosticPath() + " " + WireData.write(contractFailure.context()));
        }
        failure.printStackTrace(System.out);
        System.out.println("CASE FAILED");
      }
      evidence.put("elapsedMillis", (System.nanoTime() - started) / 1_000_000);
      results.add(evidence);
    }
    check(selected > 0, "No native scenarios selected");
    equal(sourceHash, hash(sourcePath), "Source changed during the run");
    equal(scenarioHash, hash(scenarioPath), "Scenario file changed during the run");
    equal(runtimeHash, hash(runtimePath), "Runtime provider changed during the run");
    Map<String, Object> report = map(
        "format", "blue-native-reseller-scenarios/1",
        "runtimeBindings", bindings.identities(),
        "source", sourcePath.toString(),
        "sourceSha256", sourceHash,
        "scenarioSha256", scenarioHash,
        "runtimeConfigSha256", runtimeHash,
        "runtimePackages", packageEvidence,
        "runtimeEvidence", runtime.getOrDefault("evidence", map()),
        "passed", selected - failed,
        "failed", failed,
        "skipped", scenarios.size() - selected,
        "cases", results,
        "scope", "Explicit native Contracts selection with fixture channels; not hosted authorization or package publication qualification");
    Files.createDirectories(reportPath.getParent());
    Files.writeString(reportPath, WireData.write(report) + "\n");
    System.out.println("NATIVE CASES passed=" + (selected - failed) + " failed=" + failed);
    return failed;
  }

  private final class Runner implements AutoCloseable {
    private Blue blue;
    private Contracts processor;
    private Contracts.Document document;
    private long maxGas;
    private int expectedFailures;
    private int restores;
    private final List<Object> quoteEvidence = new ArrayList<>();
    private final List<Object> captures = new ArrayList<>();
    private final List<Object> transitions = new ArrayList<>();
    private final Map<String,Object> remembered = new LinkedHashMap<>();

    Runner() {
      open();
    }

    private void open() {
      Blue.Builder builder = Blue.builder().packages(bundle);
      builder.provider(object(runtime.getOrDefault("records", map())));
      object(runtime.getOrDefault("aliases", map())).forEach((name, id) -> builder.alias(name, text(id)));
      blue = builder.build();
      processor = new Contracts(blue, bindings);
    }

    void initialize(Object source, String expectedStatus) {
      Contracts.Result result = processor.initialize(source);
      transitions.add(map("operation", "initialize", "status", result.status(), "gas", result.gas(),
          "documentBlueId", result.document().blueId(), "events", jsonEvidence(processor.emitted(result))));
      equal(expectedStatus, result.status(), "Native initialization: " + diagnostic(result));
      document = result.document();
      maxGas = Math.max(maxGas, result.gas());
      if (!result.status().equals("APPLIED")) expectedFailures++;
      System.out.println("INITIAL status=" + result.status() + " gas=" + result.gas());
    }

    void restore() {
      Map<String, Object> saved = object(copy(processor.exportSnapshot(document)));
      String identity = document.identity();
      String blueId = document.blueId();
      blue.close();
      open();
      document = processor.importSnapshot(saved, identity);
      equal(identity, document.identity(), "Restore changed the document identity");
      equal(blueId, document.blueId(), "Restore changed the document version");
      restores++;
      System.out.println("NATIVE COLD RESTORE completed");
    }

    void bootstrapPrepared(Map<String, Object> step) {
      String path = text(step.get("bootstrapPrepared"));
      var entries = object(processor.read(document, path + "/entries"));
      equal(1, entries.size(), "Expected one prepared instruction");
      var entry = object(entries.values().iterator().next());
      equal("awaiting_provider", entry.get("status"), "Instruction must await its supplier");
      retainMemberHistories(document);
      var result = processor.initialize(map("blueId", entry.get("requirementRef")));
      equal("APPLIED", result.status(), "Prepared instruction bootstrap: " + diagnostic(result));
      for (var binding : object(step.getOrDefault("bindPreparedSources", map())).entrySet()) {
        var values = processor.execution().values();
        String sourceVersion = NativeRuntime.identity(values.exact(
            values.select(new Exact.Ref(document.blueId()), text(binding.getValue()))));
        Object request = map("type", "Documents/Source Binding Input", "alias", binding.getKey(),
            "document", map("blueId", sourceVersion));
        Object input = map("source", step.get("sourceBindingSource"), "operation", map(
            "type", "Contracts/Operation Request", "document", map("blueId", result.document().blueId()),
            "operation", step.get("sourceBindingOperation"), "channel", step.get("sourceBindingChannel"),
            "request", request));
        result = processor.process(result.document(), input,
            Long.parseLong(WireData.write(step.get("timestampMicros"))));
        equal("APPLIED", result.status(), "Prepared source binding: " + diagnostic(result));
      }
      retainMemberHistories(result.document());
      for (var expectation : object(step.getOrDefault("expectBootstrapped", map())).entrySet()) {
        sameValue(expectation.getValue(), processor.read(result.document(), expectation.getKey()),
            "Bootstrapped instruction " + expectation.getKey());
      }
      String name = text(step.get("rememberAs"));
      remembered.put(name, map("blueId", result.document().blueId()));
      remembered.put(name + ".inResponseTo", entry.get("requestId"));
      remembered.put(name + ".requirementRef", entry.get("requirementRef"));
      maxGas = Math.max(maxGas, result.gas());
      captures.add(map("label", "bootstrapped-" + name, "requirementRef", entry.get("requirementRef"),
          "documentBlueId", result.document().blueId(), "events", jsonEvidence(processor.emitted(result))));
      System.out.println("BOOTSTRAP " + name + " status=" + result.status() + " gas=" + result.gas());
    }

    void retainMemberHistories(Contracts.Document source) {
      var execution = processor.execution();
      var snapshot = execution.snapshot(source);
      var outgoing = ContractsExecution.outgoing(snapshot);
      for (var member : snapshot.documents.values())
        execution.chooseHistory(member.blueId,
            ContractsExecution.rooted(snapshot, member.key, outgoing));
    }

    void operation(Map<String, Object> step, int timestamp) {
      // A prepared source may pin the version immediately before this operation.
      retainMemberHistories(document);
      Map<String, Object> before = new LinkedHashMap<>();
      for (Object rawPath : array(step.getOrDefault("unchangedPaths", List.of()))) {
        String path = text(rawPath);
        before.put(path, pathIdentity(path));
      }
      String target = text(step.getOrDefault("target", ""));
      var values = processor.execution().values();
      Exact selected = target.isEmpty()
          ? new Exact.Ref(document.blueId())
          : values.exact(values.select(new Exact.Ref(document.blueId()), target));
      String targetVersion = NativeRuntime.identity(selected);
      Map<String, Object> requestValue = new LinkedHashMap<>(object(step.getOrDefault("request", map())));
      for (var entry : object(step.getOrDefault("requestFromState", map())).entrySet()) {
        requestValue.put(entry.getKey(), copy(processor.read(document, text(entry.getValue()))));
      }
      for (var entry : object(step.getOrDefault("requestFromRemembered", map())).entrySet()) {
        check(remembered.containsKey(text(entry.getValue())), "Unknown remembered value");
        requestValue.put(entry.getKey(), copy(remembered.get(text(entry.getValue()))));
      }
      Map<String, Object> call = map(
          "type", "Contracts/Operation Request",
          "document", map("blueId", targetVersion),
          "operation", step.get("operation"),
          "channel", step.get("channel"),
          "request", requestValue,
          "requireExactDocumentVersion", step.getOrDefault("requireExactDocumentVersion", false));
      Object input = step.containsKey("rawInput") ? step.get("rawInput") : map(
          "source", step.getOrDefault("source", step.get("channel")), "operation", call);
      long hostTimestamp = Long.parseLong(WireData.write(step.getOrDefault("timestampMicros", timestamp)));
      Contracts.Result result = processor.process(document, input, hostTimestamp);
      transitions.add(map("operation", step.get("operation"), "status", result.status(), "gas", result.gas(),
          "documentBlueId", result.document().blueId(), "events", jsonEvidence(processor.emitted(result))));
      String expectedStatus = text(step.getOrDefault("status", "APPLIED"));
      String label = "step " + timestamp + " " + step.get("operation");
      equal(expectedStatus, result.status(), label + ": " + diagnostic(result));
      if (!result.commits()) equal(document.blueId(), result.document().blueId(), label + " rejected document version");
      if (step.containsKey("diagnosticContains")) {
        check(WireData.write(result.observations()).contains(text(step.get("diagnosticContains"))),
            label + " missing diagnostic: " + step.get("diagnosticContains") + " actual=" + diagnostic(result));
      }
      if (Boolean.TRUE.equals(step.get("expectNoEffects"))) {
        Map<String, Object> observations = object(result.observations());
        for (String key : List.of("changes", "events", "publicEvents")) {
          equal(List.of(), observations.get(key), label + " unexpected " + key);
        }
        equal(List.of(), processor.emitted(result), label + " emitted effects");
      }
      document = result.document();
      if (step.containsKey("expectProvisionRequested")) {
        var entries = object(processor.read(document, text(step.get("expectProvisionRequested")) + "/entries"));
        equal(1, entries.size(), label + " prepared instruction count");
        var entry = object(entries.values().iterator().next());
        Object pattern = map("type", "Documents/Document Provision Requested", "clauseId", step.getOrDefault("provisionClause", "payment"),
            "itemKey", entry.get("key"), "inResponseTo", entry.get("requestId"),
            "requirementRef", entry.get("requirementRef"), "party", step.getOrDefault("provisionParty", "seller"));
        var matching = array(object(result.observations()).get("events")).stream()
            .map(ResellerScenarios::object)
            .filter(event -> values.matches(new Exact.Ref(text(event.get("event"))), values.source(pattern)))
            .toList();
        equal(1, matching.size(), label + " correlated native provision request");
        captures.add(map("label", "native-provision-request", "origin", matching.getFirst().get("document"),
            "event", values.projectPreservingCycles(new Exact.Ref(text(matching.getFirst().get("event"))))));
      }
      for (Object alias : array(step.getOrDefault("absentEventTypes", List.of()))) {
        Object pattern = values.source(map("type", alias));
        for (Object event : array(object(result.observations()).get("events"))) {
          check(!values.matches(new Exact.Ref(text(object(event).get("event"))), pattern),
              label + " unexpected event: " + alias);
        }
      }
      for (var entry : object(step.getOrDefault("remember", map())).entrySet()) {
        remembered.put(entry.getKey(), copy(processor.read(document, text(entry.getValue()))));
      }
      for (var entry : before.entrySet()) {
        equal(entry.getValue(), pathIdentity(entry.getKey()), label + " changed " + entry.getKey());
      }
      if (step.containsKey("capture")) {
        Map<String,Object> states = new LinkedHashMap<>();
        for(Object path : array(step.getOrDefault("capturePaths", List.of("/reservations", "/orderSnapshot"))))
          states.put(text(path), jsonEvidence(processor.read(document,text(path))));
        captures.add(map("label", step.get("capture"), "documentBlueId", document.blueId(), "timestampMicros",hostTimestamp,"state",states,"events",jsonEvidence(processor.emitted(result))));
      }
      if (step.containsKey("captureExact")) {
        Map<String, Object> documents = new LinkedHashMap<>();
        for (Object pointer : array(step.get("captureExact"))) {
          Exact exact = values.exact(values.select(new Exact.Ref(document.blueId()), text(pointer)));
          documents.put(text(pointer), map("blueId", NativeRuntime.identity(exact),
              "value", values.literal(exact)));
        }
        captures.add(map("label", "exact-documents", "documents", documents));
      }
      maxGas = Math.max(maxGas, result.gas());
      if (!result.status().equals("APPLIED")) expectedFailures++;
      if (result.status().equals("APPLIED") && "createQuote".equals(step.get("operation"))) {
        Map<String, Object> request = object(step.getOrDefault("request", map()));
        String key = text(request.get("key"));
        String path = "/quotes/" + key.replace("~", "~0").replace("/", "~1");
        Exact quote = values.exact(values.select(new Exact.Ref(document.blueId()), path));
        quoteEvidence.add(map("step", timestamp, "key", key,
            "blueId", NativeRuntime.identity(quote),
            "snapshot", copy(processor.read(document, path))));
      }
      System.out.println("STEP " + timestamp + " " + step.get("operation")
          + " status=" + result.status() + " gas=" + result.gas());
    }

    void expect(Map<String, Object> row, String label) {
      for (var entry : object(row.getOrDefault("expect", map())).entrySet()) {
        sameValue(entry.getValue(), processor.read(document, entry.getKey()), label + " " + entry.getKey());
      }
      for (var entry : object(row.getOrDefault("expectEntryCounts", map())).entrySet()) {
        sameValue(entry.getValue(), object(processor.read(document, entry.getKey())).size(),
            label + " entry count " + entry.getKey());
      }
      for (Object path : array(row.getOrDefault("absent", List.of()))) {
        equal(Values.UNDEFINED, processor.read(document, text(path)), label + " unexpected field " + path);
      }
    }

    String pathIdentity(String path) {
      var values = processor.execution().values();
      return NativeRuntime.identity(values.exact(values.select(new Exact.Ref(document.blueId()), path)));
    }

    @Override public void close() {
      if (blue != null) blue.close();
    }
  }

  private static Object parse(Path path) throws Exception {
    String text = Files.readString(path);
    // Native Source accepts lexical numeric tokens, including fractional input.
    // The generic JSON utility returns BigDecimal, which is not a host Source scalar.
    return WireData.parse(text, text.stripLeading().startsWith("{") ? "json" : "yaml");
  }

  private static String diagnostic(Contracts.Result result) {
    return WireData.write(result.observations());
  }

  private static Object copy(Object value) {
    return WireData.json(WireData.write(value));
  }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> object(Object value) {
    if (!(value instanceof Map<?, ?>)) throw new IllegalArgumentException("Expected object: " + value);
    return (Map<String, Object>) value;
  }

  @SuppressWarnings("unchecked")
  private static List<Object> array(Object value) {
    if (!(value instanceof List<?>)) throw new IllegalArgumentException("Expected array: " + value);
    return (List<Object>) value;
  }

  private static String text(Object value) {
    if (!(value instanceof String)) throw new IllegalArgumentException("Expected string: " + value);
    return (String) value;
  }

  private static Map<String, Object> map(Object... values) {
    if (values.length % 2 != 0) throw new IllegalArgumentException("Map needs key/value pairs");
    Map<String, Object> result = new LinkedHashMap<>();
    for (int i = 0; i < values.length; i += 2) result.put(text(values[i]), values[i + 1]);
    return result;
  }

  private static void updateExisting(Map<String, Object> root, String pointer, Object value, boolean remove) {
    check(pointer.startsWith("/") && pointer.length() > 1, "sourcePatch requires a non-root pointer");
    String[] parts = pointer.substring(1).split("/", -1);
    Map<String, Object> parent = root;
    for (int i = 0; i < parts.length - 1; i++) parent = object(parent.get(unescape(parts[i])));
    String key = unescape(parts[parts.length - 1]);
    check(parent.containsKey(key), "sourcePatch field does not exist: " + pointer);
    if (remove) parent.remove(key);
    else parent.put(key, copy(value));
  }

  private static String unescape(String value) {
    return value.replace("~1", "/").replace("~0", "~");
  }

  private static void sameValue(Object expected, Object actual, String label) {
    check(actual != Values.UNDEFINED, label + ": expected field is absent");
    equal(WireData.write(expected), WireData.write(actual), label);
  }

  // Native absent object fields have no JSON representation; omit them only in report evidence.
  private static Object jsonEvidence(Object value) {
    if (value == blue.bex.Values.UNDEFINED) return null;
    if (value instanceof Map<?, ?> values) {
      Map<String, Object> out = new LinkedHashMap<>();
      values.forEach((key, item) -> { if (item != blue.bex.Values.UNDEFINED) out.put(text(key), jsonEvidence(item)); });
      return out;
    }
    if (value instanceof List<?> values) return values.stream().map(ResellerScenarios::jsonEvidence).toList();
    return value;
  }

  private static void equal(Object expected, Object actual, String label) {
    check(Objects.equals(expected, actual), label + ": expected=" + expected + ", actual=" + actual);
  }

  private static void check(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }

  private static String hash(Path path) throws Exception {
    return "sha256:" + HexFormat.of().formatHex(
        MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
  }
}
