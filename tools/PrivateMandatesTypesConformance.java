import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native Language conformance for the evidence-channel and private-mandates schemas; Core qualifies execution. */
public final class PrivateMandatesTypesConformance {
  /** Identities published before this edition; adding it must not move them. */
  static final Map<String, String> PRIOR = Map.of(
      "Coordination", "4gmSjwn3DCYBVeDieXxuXgsPvvz2dU6ovFXnnuyv2RjA",
      "Coordination/Timeline Channel", "GCd3gAEibsaZi1vdhFhTSfRch1HPruFcE1pgm9eAMKwy",
      "Mandates", "4kaMxybWTTeTpkzUtoYVUPk8dUo3HxKM5MG5joxN6LFL",
      "Mandates/Authority", "AypmNprcDHuFc293hkDJFJ91GKtwbH7mDiCii8hmUBjP",
      "Mandates/Mandate Authority", "2YnsAG44Sg9Q9XrzUe9Yz5PNXkHuxDcpvv4Wv4QNysTe");
  static final String HEX = "ab".repeat(32);

  @SuppressWarnings("unchecked")
  static Map<String, Object> map(Object value) { return (Map<String, Object>) value; }
  static void require(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
  static Map<String, Object> with(Map<String, Object> base, String field, Object value) {
    var copy = new TreeMap<>(base);
    if (value == null) copy.remove(field); else copy.put(field, value);
    return copy;
  }
  static String admitted(Blue blue, String what, Map<String, Object> value) {
    try {
      return blue.createJson(WireData.write(value)).blueId();
    } catch (Failure failure) {
      throw new AssertionError("Valid " + what + " was rejected: " + failure.getMessage());
    }
  }
  static void rejected(Blue blue, String what, Map<String, Object> value) {
    try {
      blue.createJson(WireData.write(value));
    } catch (Failure failure) {
      return;
    }
    throw new AssertionError("Invalid value was admitted: " + what);
  }
  static void descends(Blue blue, String what, String type, String ancestor) {
    require(NativeRuntime.ancestry(type, new NativeRuntime(blue)).contains(ancestor), what + " must extend its base type");
  }

  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]);
    var open = new TreeMap<String, BluePackage>();
    for (var mount : Map.of("Language", "blue-language", "BEX", "blue-bex", "Contracts", "blue-contracts",
        "Coordination", "blue-coordination", "Mandates", "blue-mandates",
        "CoordinationEvidence", "blue-coordination-evidence", "PrivateMandates", "blue-private-mandates").entrySet())
      open.put(mount.getKey(), BluePackage.open(root.resolve(mount.getValue() + "/dist/package.bluepkg")));
    var coordination = open.get("Coordination");
    var mandates = open.get("Mandates");
    var evidence = open.get("CoordinationEvidence");
    var privateMandates = open.get("PrivateMandates");
    require(PRIOR.get("Coordination").equals(coordination.blueId()), "Coordination publication changed");
    require(PRIOR.get("Coordination/Timeline Channel").equals(coordination.exportId("Timeline Channel")),
        "Timeline Channel identity changed");
    require(PRIOR.get("Mandates").equals(mandates.blueId()), "Mandates publication changed");
    require(PRIOR.get("Mandates/Authority").equals(mandates.exportId("Authority"))
        && PRIOR.get("Mandates/Mandate Authority").equals(mandates.exportId("Mandate Authority")),
        "Mandates authority identities changed");
    for (String name : evidence.exports().keySet())
      require(!coordination.exports().containsKey(name), "Evidence edition must not redefine a Coordination export: " + name);
    for (String name : privateMandates.exports().keySet())
      require(!mandates.exports().containsKey(name), "Extension must not redefine a Mandates export: " + name);

    var bundle = PackageBundle.builder();
    open.forEach(bundle::mount);
    try (Blue blue = Blue.builder().packages(bundle.build()).build()) {
      descends(blue, "Timeline Channel with Evidence", evidence.exportId("Timeline Channel with Evidence"),
          coordination.exportId("Timeline Channel"));
      descends(blue, "Mandate Commitment Authority", privateMandates.exportId("Mandate Commitment Authority"),
          mandates.exportId("Authority"));
      descends(blue, "RISC Zero Succinct Receipt Profile",
          privateMandates.exportId("RISC Zero Succinct Receipt Profile"), evidence.exportId("Evidence Profile"));
      require(!NativeRuntime.ancestry(privateMandates.exportId("Mandate Commitment Authority"), new NativeRuntime(blue))
          .contains(mandates.exportId("Mandate Authority")), "The commitment claim must not be a Mandate Authority");

      // A type-only node is unvalued; a required actor needs identifying content.
      Map<String, Object> actor = Map.of("type", "Coordination/Principal Actor", "displayName", "Holder");
      Map<String, Object> provider = Map.of("type", "Coordination/Timeline Provider",
          "endpoint", "https://provider.example", "publicKey", HEX);
      Map<String, Object> timeline = Map.of("type", "Coordination/Signed Timeline", "provider", provider,
          "publicRead", false, "url", "https://provider.example/timelines/operations");
      Map<String, Object> proofs = with(timeline, "url", "https://provider.example/timelines/proofs");
      Map<String, Object> profile = Map.of("type", "PrivateMandates/RISC Zero Succinct Receipt Profile",
          "programImageId", HEX, "allowedProviders", List.of("01".repeat(32), "02".repeat(32)), "factsRule", "FULL(D)");
      Map<String, Object> channel = Map.of("type", "CoordinationEvidence/Timeline Channel with Evidence",
          "actor", actor, "timeline", timeline, "proofTimeline", proofs,
          "mandateProcessorKey", "ef".repeat(32), "evidenceProfile", profile);
      Map<String, Object> authority = Map.of("type", "PrivateMandates/Mandate Commitment Authority",
          "actor", actor, "mandateCommitment", HEX);
      Map<String, Object> proof = Map.of("type", "CoordinationEvidence/Proof Entry", "receipt", "AAECAw==");
      Map<String, Object> rejection = Map.of("type", "CoordinationEvidence/Rejection Entry",
          "documentId", PRIOR.get("Coordination"), "operationEntry", PRIOR.get("Mandates"));

      var ids = new TreeMap<String, Object>();
      ids.put("profile", admitted(blue, "profile", profile));
      ids.put("channel", admitted(blue, "channel", channel));
      ids.put("authority", admitted(blue, "authority", authority));
      ids.put("proofEntry", admitted(blue, "proof entry", proof));
      ids.put("rejectionEntry", admitted(blue, "rejection entry", rejection));
      admitted(blue, "plain timeline channel",
          Map.of("type", "Coordination/Timeline Channel", "actor", actor, "timeline", timeline));

      for (String field : List.of("proofTimeline", "mandateProcessorKey", "evidenceProfile", "timeline", "actor"))
        rejected(blue, "channel without " + field, with(channel, field, null));
      rejected(blue, "channel with a short key", with(channel, "mandateProcessorKey", "ef"));
      // A profile is a typed value of a specialisation, never a name or an unrelated value (decision 31).
      rejected(blue, "channel with a text profile", with(channel, "evidenceProfile", "latest"));
      rejected(blue, "channel with an integer profile", with(channel, "evidenceProfile", 7));
      rejected(blue, "channel with an actor as profile", with(channel, "evidenceProfile", actor));
      rejected(blue, "channel with a bare base profile",
          with(channel, "evidenceProfile", Map.of("type", "CoordinationEvidence/Evidence Profile")));
      admitted(blue, "profile with an empty provider list", with(profile, "allowedProviders", List.of()));
      rejected(blue, "profile with only a digest", with(with(profile, "allowedProviders", null), "providerSetDigest", HEX));
      rejected(blue, "profile with an extra field", with(profile, "providerSetDigest", HEX));
      rejected(blue, "profile with a short provider key", with(profile, "allowedProviders", List.of("01")));
      rejected(blue, "profile with a repeated provider key",
          with(profile, "allowedProviders", List.of("01".repeat(32), "01".repeat(32))));
      rejected(blue, "authority with a clear mandate text", with(authority, "mandate", "someMandateBlueId"));
      rejected(blue, "authority with a clear mandate reference",
          with(authority, "mandate", Map.of("blueId", PRIOR.get("Mandates"))));
      rejected(blue, "proof entry with an extra field", with(proof, "note", "x"));
      rejected(blue, "rejection with an extra field", with(rejection, "reason", "x"));
      // The Language schema has no character-set or ordering predicate. These values are admitted as
      // data and are decided by the native rules stated in the two specifications.
      var nativeRules = new ArrayList<String>();
      for (var left : List.of(
          Map.entry("channel key not lower-case hex", with(channel, "mandateProcessorKey", "EF".repeat(32))),
          Map.entry("channel profile of the base type with a field", with(channel, "evidenceProfile",
              Map.of("type", "CoordinationEvidence/Evidence Profile", "anything", "x"))),
          Map.entry("commitment not lower-case hex", with(authority, "mandateCommitment", "zz".repeat(32))),
          Map.entry("image id not lower-case hex", with(profile, "programImageId", "AB".repeat(32))),
          Map.entry("provider list not ascending",
              with(profile, "allowedProviders", List.of("02".repeat(32), "01".repeat(32)))),
          Map.entry("receipt not canonical base64", with(proof, "receipt", "not base64 !!")))) {
        admitted(blue, left.getKey(), left.getValue());
        nativeRules.add(left.getKey());
      }
      for (String field : List.of("programImageId", "allowedProviders", "factsRule"))
        rejected(blue, "profile without " + field, with(profile, field, null));
      rejected(blue, "profile with another facts rule", with(profile, "factsRule", "CANONICAL"));
      rejected(blue, "profile with a short image id", with(profile, "programImageId", "ab"));
      rejected(blue, "authority without commitment", with(authority, "mandateCommitment", null));
      rejected(blue, "authority without holder", with(authority, "actor", null));
      rejected(blue, "authority with a short commitment", with(authority, "mandateCommitment", "ab"));
      rejected(blue, "proof entry without receipt", with(proof, "receipt", null));
      rejected(blue, "rejection without documentId", with(rejection, "documentId", null));
      rejected(blue, "rejection without operationEntry", with(rejection, "operationEntry", null));

      var result = new TreeMap<String, Object>();
      result.put("coordinationEvidencePackage", evidence.blueId());
      result.put("privateMandatesPackage", privateMandates.blueId());
      result.put("sampleBlueIds", ids);
      result.put("leftToNativeRules", nativeRules);
      result.put("scope", "Language schema, inheritance and unchanged prior identities; not native execution qualification");
      System.out.println(WireData.write(result));
    }
  }
}
