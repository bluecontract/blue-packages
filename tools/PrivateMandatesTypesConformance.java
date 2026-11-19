import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native Language conformance for the Coordination evidence types and the private-mandates schemas; Core qualifies execution. */
public final class PrivateMandatesTypesConformance {
  /** Identities of the edition before this one; its retained archives must still carry them. */
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
  /** Open entry schemas: a malformed entry is Blue content; the processor, not the schema, skips it. */
  static void skippedByProcessor(Blue blue, List<String> log, String what, Map<String, Object> value) {
    try {
      blue.createJson(WireData.write(value));
    } catch (Failure failure) {
      throw new AssertionError("Malformed entry must be admitted by the open schema: " + what + ": "
          + failure.category() + " " + failure.getMessage());
    }
    log.add(what);
  }
  /** A {blueId} value is a Language reference wherever it stands; returns the admission outcome and category. */
  static String referenceOutcome(Blue blue, Map<String, Object> value) {
    try {
      blue.createJson(WireData.write(value));
      return "Admitted";
    } catch (Failure failure) {
      return failure.outcome().get("outcome") + "/" + failure.category();
    }
  }
  static void descends(Blue blue, String what, String type, String ancestor) {
    require(NativeRuntime.ancestry(type, new NativeRuntime(blue)).contains(ancestor), what + " must extend its base type");
  }

  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]);
    var open = new TreeMap<String, BluePackage>();
    for (var mount : Map.of("Language", "blue-language", "BEX", "blue-bex", "Contracts", "blue-contracts",
        "Coordination", "blue-coordination", "Mandates", "blue-mandates",
        "PrivateMandates", "blue-private-mandates").entrySet())
      open.put(mount.getKey(), BluePackage.open(root.resolve(mount.getValue() + "/dist/package.bluepkg")));
    var coordination = open.get("Coordination");
    var mandates = open.get("Mandates");
    var privateMandates = open.get("PrivateMandates");
    // The previous edition stays available as retained archives with its exact identities.
    var priorCoordination = BluePackage.open(root.resolve("retained/pre-evidence-20261119/blue-coordination/package.bluepkg"));
    var priorMandates = BluePackage.open(root.resolve("retained/pre-evidence-20261119/blue-mandates/package.bluepkg"));
    require(PRIOR.get("Coordination").equals(priorCoordination.blueId()), "Retained Coordination publication changed");
    require(PRIOR.get("Coordination/Timeline Channel").equals(priorCoordination.exportId("Timeline Channel")),
        "Retained Timeline Channel identity changed");
    require(PRIOR.get("Mandates").equals(priorMandates.blueId()), "Retained Mandates publication changed");
    require(PRIOR.get("Mandates/Authority").equals(priorMandates.exportId("Authority"))
        && PRIOR.get("Mandates/Mandate Authority").equals(priorMandates.exportId("Mandate Authority")),
        "Retained Mandates authority identities changed");
    // A new edition has new identities; it never reuses those of the previous one.
    require(!PRIOR.get("Coordination").equals(coordination.blueId())
        && !PRIOR.get("Coordination/Timeline Channel").equals(coordination.exportId("Timeline Channel"))
        && !PRIOR.get("Mandates").equals(mandates.blueId()), "The new edition must not reuse earlier identities");
    for (String name : priorCoordination.exports().keySet())
      require(coordination.exports().containsKey(name), "The new edition must keep every earlier Coordination export: " + name);
    for (String name : List.of("Timeline Channel with Evidence", "Evidence Profile", "Proof Entry", "Rejection Entry"))
      require(coordination.exports().containsKey(name) && !priorCoordination.exports().containsKey(name),
          "Evidence type must be new in this Coordination edition: " + name);
    for (String name : privateMandates.exports().keySet())
      require(!mandates.exports().containsKey(name), "Extension must not redefine a Mandates export: " + name);

    var bundle = PackageBundle.builder();
    open.forEach(bundle::mount);
    try (Blue blue = Blue.builder().packages(bundle.build()).build()) {
      descends(blue, "Timeline Channel with Evidence", coordination.exportId("Timeline Channel with Evidence"),
          coordination.exportId("Timeline Channel"));
      descends(blue, "Mandate Commitment Authority", privateMandates.exportId("Mandate Commitment Authority"),
          mandates.exportId("Authority"));
      descends(blue, "RISC Zero Succinct Receipt Profile",
          privateMandates.exportId("RISC Zero Succinct Receipt Profile"), coordination.exportId("Evidence Profile"));
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
      Map<String, Object> channel = Map.of("type", "Coordination/Timeline Channel with Evidence",
          "actor", actor, "timeline", timeline, "evidenceTimeline", proofs,
          "mandateProcessorKey", "ef".repeat(32), "evidenceProfile", profile);
      Map<String, Object> authority = Map.of("type", "PrivateMandates/Mandate Commitment Authority",
          "actor", actor, "mandateCommitment", HEX);
      // References by content BlueId. These two targets are content the mounted packages provide.
      Map<String, Object> document = Map.of("blueId", coordination.exportId("Timeline Channel"));
      Map<String, Object> operationEntry = Map.of("blueId", coordination.exportId("Timeline Entry"));
      Map<String, Object> proof = Map.of("type", "Coordination/Proof Entry", "receipt", "AAECAw==",
          "document", document, "operationEntry", operationEntry);
      Map<String, Object> rejection = Map.of("type", "Coordination/Rejection Entry",
          "document", document, "operationEntry", operationEntry);

      var ids = new TreeMap<String, Object>();
      ids.put("profile", admitted(blue, "profile", profile));
      ids.put("channel", admitted(blue, "channel", channel));
      ids.put("authority", admitted(blue, "authority", authority));
      ids.put("proofEntry", admitted(blue, "proof entry", proof));
      ids.put("rejectionEntry", admitted(blue, "rejection entry", rejection));
      admitted(blue, "plain timeline channel",
          Map.of("type", "Coordination/Timeline Channel", "actor", actor, "timeline", timeline));

      for (String field : List.of("evidenceTimeline", "mandateProcessorKey", "evidenceProfile", "timeline", "actor"))
        rejected(blue, "channel without " + field, with(channel, field, null));
      rejected(blue, "channel with a short key", with(channel, "mandateProcessorKey", "ef"));
      // A profile is a typed value of a specialisation, never a name or an unrelated value (decision 31).
      rejected(blue, "channel with a text profile", with(channel, "evidenceProfile", "latest"));
      rejected(blue, "channel with an integer profile", with(channel, "evidenceProfile", 7));
      rejected(blue, "channel with an actor as profile", with(channel, "evidenceProfile", actor));
      rejected(blue, "channel with a bare base profile",
          with(channel, "evidenceProfile", Map.of("type", "Coordination/Evidence Profile")));
      admitted(blue, "profile with an empty provider list", with(profile, "allowedProviders", List.of()));
      rejected(blue, "profile with only a digest", with(with(profile, "allowedProviders", null), "providerSetDigest", HEX));
      rejected(blue, "profile with an extra field", with(profile, "providerSetDigest", HEX));
      rejected(blue, "profile with a short provider key", with(profile, "allowedProviders", List.of("01")));
      rejected(blue, "profile with a repeated provider key",
          with(profile, "allowedProviders", List.of("01".repeat(32), "01".repeat(32))));
      rejected(blue, "authority with a clear mandate text", with(authority, "mandate", "someMandateBlueId"));
      rejected(blue, "authority with a clear mandate reference",
          with(authority, "mandate", Map.of("blueId", PRIOR.get("Mandates"))));
      // Proof Entry and Rejection Entry have open schemas: every malformed entry below is admitted as
      // Blue content, so it cannot fail the import of a evidence timeline. The processor skips it.
      var skipped = new ArrayList<String>();
      skippedByProcessor(blue, skipped, "proof entry with an extra field", with(proof, "note", "x"));
      skippedByProcessor(blue, skipped, "proof entry without receipt", with(proof, "receipt", null));
      skippedByProcessor(blue, skipped, "proof entry without document", with(proof, "document", null));
      skippedByProcessor(blue, skipped, "proof entry without operationEntry", with(proof, "operationEntry", null));
      skippedByProcessor(blue, skipped, "proof entry with an integer receipt", with(proof, "receipt", 7));
      skippedByProcessor(blue, skipped, "proof entry with an empty receipt", with(proof, "receipt", ""));
      skippedByProcessor(blue, skipped, "proof entry with a list receipt", with(proof, "receipt", List.of("AAECAw==")));
      skippedByProcessor(blue, skipped, "proof entry with a text document", with(proof, "document", "someDocumentId"));
      skippedByProcessor(blue, skipped, "proof entry with an integer operationEntry", with(proof, "operationEntry", 7));
      skippedByProcessor(blue, skipped, "proof entry with only an unknown field",
          Map.of("type", "Coordination/Proof Entry", "note", "x"));
      skippedByProcessor(blue, skipped, "rejection with an extra field", with(rejection, "reason", "x"));
      skippedByProcessor(blue, skipped, "rejection without document", with(rejection, "document", null));
      skippedByProcessor(blue, skipped, "rejection without operationEntry", with(rejection, "operationEntry", null));
      skippedByProcessor(blue, skipped, "rejection with the earlier text fields",
          Map.of("type", "Coordination/Rejection Entry", "documentId", "x", "operationEntry", "y"));
      skippedByProcessor(blue, skipped, "rejection with an object that is not a reference as document",
          with(rejection, "document", Map.of("id", "x")));
      // The reference convention itself. A {blueId} value is opened by Language admission wherever it
      // stands, as for the free document field of an Operation Request. The entry schemas cannot change
      // that; the outcomes are recorded here so that a change of the runtime is noticed.
      Map<String, Object> unavailable = Map.of("blueId", PRIOR.get("Coordination"));
      var references = new TreeMap<String, Object>();
      references.put("proof entry, document content unavailable", referenceOutcome(blue, with(proof, "document", unavailable)));
      references.put("proof entry, operationEntry content unavailable",
          referenceOutcome(blue, with(proof, "operationEntry", unavailable)));
      references.put("rejection, document content unavailable", referenceOutcome(blue, with(rejection, "document", unavailable)));
      references.put("operation request, document content unavailable", referenceOutcome(blue,
          Map.of("type", "Contracts/Operation Request", "channel", "c", "operation", "o", "document", unavailable)));
      references.put("proof entry, document blueId not a BlueId",
          referenceOutcome(blue, with(proof, "document", Map.of("blueId", "not-a-blue-id"))));
      for (String what : List.of("proof entry, document content unavailable", "proof entry, operationEntry content unavailable",
          "rejection, document content unavailable"))
        require(references.get(what).equals(references.get("operation request, document content unavailable")),
            "An entry reference must behave as the document reference of an Operation Request: " + what);
      require("Incomplete/ProviderUnavailable".equals(references.get("operation request, document content unavailable")),
          "Recorded limit changed: an unavailable reference target is expected to leave admission incomplete");
      require(references.get("proof entry, document blueId not a BlueId").toString().startsWith("Invalid/"),
          "Recorded limit changed: a value that is not a reference is expected to be invalid");
      // The Language schema has no character-set or ordering predicate. These values are admitted as
      // data and are decided by the native rules stated in the two specifications.
      var nativeRules = new ArrayList<String>();
      for (var left : List.of(
          Map.entry("channel key not lower-case hex", with(channel, "mandateProcessorKey", "EF".repeat(32))),
          Map.entry("channel profile of the base type with a field", with(channel, "evidenceProfile",
              Map.of("type", "Coordination/Evidence Profile", "anything", "x"))),
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

      var result = new TreeMap<String, Object>();
      result.put("coordinationPackage", coordination.blueId());
      result.put("mandatesPackage", mandates.blueId());
      var typeIds = new TreeMap<String, Object>();
      for (String name : List.of("Timeline Channel", "Timeline Channel with Evidence", "Evidence Profile", "Proof Entry", "Rejection Entry"))
        typeIds.put("Coordination/" + name, coordination.exportId(name));
      for (String name : privateMandates.exports().keySet()) typeIds.put("PrivateMandates/" + name, privateMandates.exportId(name));
      result.put("typeBlueIds", typeIds);
      result.put("admittedBySchemaSkippedByProcessor", skipped);
      result.put("referenceAdmissionOutcomes", references);
      result.put("privateMandatesPackage", privateMandates.blueId());
      result.put("sampleBlueIds", ids);
      result.put("leftToNativeRules", nativeRules);
      result.put("scope", "Language schema, inheritance and retained prior identities; not native execution qualification");
      System.out.println(WireData.write(result));
    }
  }
}
