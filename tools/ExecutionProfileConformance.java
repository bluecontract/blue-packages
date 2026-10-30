import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native Language conformance for the neutral schema; Core qualifies execution. */
public final class ExecutionProfileConformance {
  @SuppressWarnings("unchecked")
  static Map<String,Object> map(Object value) { return (Map<String,Object>)value; }
  static Map<String,Object> ref(String id) { return Map.of("blueId", id); }
  static void require(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
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
    var profile = BluePackage.open(root.resolve("blue-execution-profile/dist/package.bluepkg"));
    var bexManifest = manifest(root, "blue-bex");
    var contractsManifest = manifest(root, "blue-contracts");
    var profileManifest = manifest(root, "blue-execution-profile");
    var semantic = map(map(profileManifest.get("semanticPackages")).get(profile.blueId()));
    var asset = map(map(semantic.get("documentation")).get("spec/execution-profile-v1.md"));
    String execution = map(asset.get("content")).get("blueId").toString();
    var bundle = PackageBundle.builder().mount("Language", language).mount("BEX", bex)
        .mount("Contracts", contracts).mount("Execution", profile).build();
    try (Blue blue = Blue.builder().packages(bundle).build()) {
      var value = new TreeMap<String,Object>();
      value.put("type", "Execution/Profile");
      value.put("executionSpecification", ref(execution));
      value.put("language", ref(language.blueId()));
      value.put("bex", ref(bexManifest.get("protocol").toString()));
      value.put("bexSpecification", ref(rules(bexManifest)));
      value.put("contract", ref(contractsManifest.get("protocol").toString()));
      value.put("contractsSpecification", ref(rules(contractsManifest)));
      value.put("capabilities", List.of());
      value.put("supportedPackages", List.of(bex.blueId(), contracts.blueId(), language.blueId())
          .stream().sorted().map(ExecutionProfileConformance::ref).toList());
      var admitted = blue.createJson(WireData.write(value));
      var exact = blue.create(admitted.exactText(), Blue.Mode.EXACT, "json", Blue.Goal.VALUE);
      require(admitted.blueId().equals(exact.blueId()), "Source/Exact preserve the profile identity");
      var embedded = blue.createJson(WireData.write(Map.of("executionProfile", value,
          "contracts", Map.of())));
      require(embedded.exactText().contains("executionProfile"), "Declaration stays in native node");
      var missing = new TreeMap<>(value);
      missing.remove("executionSpecification");
      rejected(blue, missing);
      var duplicates = new TreeMap<>(value);
      duplicates.put("supportedPackages", List.of(ref(bex.blueId()), ref(bex.blueId())));
      rejected(blue, duplicates);
      System.out.println(WireData.write(Map.of("schemaBlueId", profile.exportId("Profile"),
          "executionSpecification", execution, "profileBlueId", admitted.blueId(),
          "checks", 4, "scope", "Language schema, not native execution qualification")));
    }
  }
}
