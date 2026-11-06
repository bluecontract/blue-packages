import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native Language conformance for the neutral schema; Core qualifies execution. */
public final class ExecutionProfileConformance {
  static final String TEXT = "GX7CFUmSDrE2MzptunLCCdZwnuwwrenRQqEnHL4x3uoC";
  @SuppressWarnings("unchecked")
  static Map<String,Object> map(Object value) { return (Map<String,Object>)value; }
  static Map<String,Object> ref(String id) { return Map.of("blueId", id); }
  static Map<String,Object> textId(String id) {
    return Map.of("type", ref(TEXT), "value", id);
  }
  static void require(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
  static void absentOptionals(Blue blue, Exact descriptor) {
    var runtime = new NativeRuntime(blue);
    var head = NativeRuntime.head(NativeRuntime.recipe(descriptor), runtime);
    for (String field : List.of("coordination", "coordinationSpecification", "provider"))
      require(!NativeRuntime.present(NativeRuntime.child(head, field), runtime),
          "Omitted profile field must be absent under native Language semantics: " + field);
  }
  static Map<String,Object> manifest(Path root, String folder) throws Exception {
    return map(WireData.json(Files.readString(root.resolve(folder + "/dist/package.json"))));
  }
  static String rules(Map<String,Object> manifest) {
    var specification = map(map(manifest.get("semanticSpecifications"))
        .get(manifest.get("protocol")));
    return map(specification.get("rules")).get("blueId").toString();
  }
  static void rejected(Blue blue, Map<String,Object> value) {
    try {
      blue.createJson(WireData.write(value));
    } catch (Failure failure) {
      require(failure.getMessage().contains("required")
          || failure.getMessage().contains("uniqueItems"),
          "Expected a profile presence/uniqueness failure: " + failure.diagnostic());
      return;
    }
    throw new AssertionError("Invalid profile schema value was admitted");
  }
  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]);
    var language = BluePackage.open(root.resolve("blue-language/dist/package.bluepkg"));
    var bex = BluePackage.open(root.resolve("blue-bex/dist/package.bluepkg"));
    var contracts = BluePackage.open(root.resolve("blue-contracts/dist/package.bluepkg"));
    var time = BluePackage.open(root.resolve("blue-time/dist/package.bluepkg"));
    var profile = BluePackage.open(root.resolve("blue-execution-profile/dist/package.bluepkg"));
    var bexManifest = manifest(root, "blue-bex");
    var contractsManifest = manifest(root, "blue-contracts");
    var profileManifest = manifest(root, "blue-execution-profile");
    var timeManifest = manifest(root, "blue-time");
    var semantic = map(map(profileManifest.get("semanticPackages")).get(profile.blueId()));
    var asset = map(map(semantic.get("documentation")).get("spec/execution-profile-v1.md"));
    String execution = map(asset.get("content")).get("blueId").toString();
    var bundle = PackageBundle.builder().mount("Language", language).mount("BEX", bex)
        .mount("Contracts", contracts).mount("Time", time).mount("Execution", profile).build();
    Map<String,Object> retainedNode;
    try (Blue blue = Blue.builder().packages(bundle).build()) {
      // An actual required definition must remain a definition inside an approval record.
      var approval = blue.admitDefinition(WireData.write(Map.of("kind", "interpreted-type",
          "definition", ref(time.exportId("Timer Fired")), "specification", ref(rules(timeManifest)))));
      var value = new TreeMap<String,Object>();
      value.put("type", "Execution/Profile");
      value.put("executionSpecification", execution);
      value.put("language", language.blueId());
      value.put("bex", bexManifest.get("protocol").toString());
      value.put("bexSpecification", rules(bexManifest));
      value.put("contract", contractsManifest.get("protocol").toString());
      value.put("contractsSpecification", rules(contractsManifest));
      value.put("capabilities", List.of(approval.blueId()));
      value.put("supportedPackages", List.of(bex.blueId(), contracts.blueId(), language.blueId(), time.blueId())
          .stream().sorted().toList());
      var admitted = blue.createJson(WireData.write(value));
      var exact = blue.create(admitted.exactText(), Blue.Mode.EXACT, "json", Blue.Goal.VALUE);
      require(admitted.blueId().equals(exact.blueId()), "Source/Exact preserve the profile identity");
      var canonicalSource = new TreeMap<>(value);
      value.forEach((field, identifier) -> {
        if (identifier instanceof String id) canonicalSource.put(field, textId(id));
        else if (identifier instanceof List<?> ids) canonicalSource.put(field,
            Map.of("items", ids.stream().map(id -> textId(id.toString())).toList()));
      });
      canonicalSource.put("type", ref(profile.exportId("Profile")));
      var runtime = new NativeRuntime(blue);
      var canonical = NativeRuntime.normalize(canonicalSource, runtime, "exact", false);
      require(admitted.blueId().equals(NativeRuntime.identity(canonical)),
          "Canonical base-schema record preserves the native profile identity");
      for (Exact form : List.of(NativeRuntime.exactOf(admitted), NativeRuntime.exactOf(exact), canonical))
        absentOptionals(blue, form);
      var definition = blue.admitDefinition(WireData.write(Map.of("name", "Optional profile input",
          "executionProfile", Map.of("type", ref(profile.exportId("Profile"))))));
      var node = runtime.prepare(Map.of("type", ref(definition.blueId())));
      var declaration = NativeRuntime.child(NativeRuntime.head(NativeRuntime.recipe(node), runtime),
          "executionProfile");
      require(!NativeRuntime.present(declaration, runtime),
          "An inherited profile schema alone must not supply a profile value");
      var embedded = blue.createJson(WireData.write(Map.of("executionProfile", value,
          "contracts", Map.of())));
      require(embedded.exactText().contains("executionProfile"), "Declaration stays in native node");
      var embeddedExact = blue.create(embedded.exactText(), Blue.Mode.EXACT, "json", Blue.Goal.VALUE);
      var embeddedReference = blue.createJson(WireData.write(Map.of("executionProfile", ref(admitted.blueId()),
          "contracts", Map.of())));
      require(embedded.blueId().equals(embeddedExact.blueId())
          && embedded.blueId().equals(embeddedReference.blueId()),
          "Source, Exact and referenced descriptor preserve required-definition identifiers");
      var languageText = blue.createJson(WireData.write(language.blueId()));
      var textReferenceSource = new TreeMap<>(value);
      textReferenceSource.put("language", ref(languageText.blueId()));
      var textReference = blue.createJson(WireData.write(textReferenceSource));
      var textHead = NativeRuntime.head(NativeRuntime.child(NativeRuntime.head(
          NativeRuntime.recipe(NativeRuntime.exactOf(textReference)), runtime), "language"), runtime);
      require(language.blueId().equals(textHead.value) && TEXT.equals(textHead.type),
          "A pure reference to a plain Text-ID value resolves to the carried identifier");
      runtime.admit(new Exact.Ref(time.blueId()), "definition");
      runtime.admit(new Exact.Ref(approval.blueId()), "definition");
      var closure = runtime.records(List.of(new Exact.Ref(time.blueId()), new Exact.Ref(approval.blueId())), false);
      require(closure.containsKey(time.blueId()) && closure.containsKey(time.exportId("Timer Fired"))
          && closure.containsKey(approval.blueId()), "Explicit dependency closure includes required definitions");
      retainedNode = map(WireData.json(embedded.exactText()));
      var missing = new TreeMap<>(value);
      missing.remove("executionSpecification");
      rejected(blue, missing);
      var duplicates = new TreeMap<>(value);
      duplicates.put("supportedPackages", List.of(bex.blueId(), bex.blueId()));
      rejected(blue, duplicates);
      System.out.println(WireData.write(Map.of("schemaBlueId", profile.exportId("Profile"),
          "executionSpecification", execution, "profileBlueId", admitted.blueId(),
          "timePackageBlueId", time.blueId(), "requiredDefinitionBlueId", time.exportId("Timer Fired"),
          "interpretedApprovalBlueId", approval.blueId(), "explicitDependencyRecords", closure.size(),
          "scope", "Language schema and dependency roles, not native execution qualification")));
    }
    try (Blue cold = Blue.builder().provider(profile.records()).build()) {
      cold.create(WireData.write(retainedNode), Blue.Mode.EXACT, "json", Blue.Goal.VALUE);
      try {
        new NativeRuntime(cold).admit(new Exact.Ref(time.blueId()), "definition");
        throw new AssertionError("Text identifiers do not prove dependency availability");
      } catch (Failure failure) {
        require(failure.category().equals("ProviderUnavailable"), failure.diagnostic().toString());
      }
    }
  }
}
