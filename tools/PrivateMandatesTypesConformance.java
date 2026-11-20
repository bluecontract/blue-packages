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
  static final List<String> MISMATCHES = new ArrayList<>();
  /** Admission result of one value: "Admitted", or outcome and category of the Language failure. */
  static String outcome(Blue blue, Object value) {
    try {
      blue.createJson(WireData.write(value));
      return "Admitted";
    } catch (Failure failure) {
      return failure.outcome().get("outcome") + "/" + failure.category();
    }
  }
  /** Asserts the exact Language behaviour, not merely success or any failure, and records it. */
  static void expect(Blue blue, Map<String, Object> log, String what, Object value, String expected) {
    String actual = outcome(blue, value);
    if (!expected.equals(actual)) MISMATCHES.add(what + ": expected " + expected + ", got " + actual);
    require(log.put(what, actual) == null, "Duplicate case: " + what);
  }
  static String admitted(Blue blue, String what, Object value) {
    try {
      return blue.createJson(WireData.write(value)).blueId();
    } catch (Failure failure) {
      throw new AssertionError("Valid " + what + " was rejected: " + failure.category() + " " + failure.getMessage());
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

      final String ADMITTED = "Admitted", SCHEMA = "Invalid/SchemaViolation", TYPE = "Invalid/TypeCompatibilityViolation",
          INCOMPLETE = "Incomplete/ProviderUnavailable";
      Map<String, Object> unavailable = Map.of("blueId", PRIOR.get("Coordination"));
      Map<String, Object> typeOnlyMandate = Map.of("type", "Mandates/Operation Mandate");

      var ids = new TreeMap<String, Object>();
      ids.put("profile", admitted(blue, "profile", profile));
      ids.put("channel", admitted(blue, "channel", channel));
      ids.put("authority", admitted(blue, "authority", authority));
      ids.put("proofEntry", admitted(blue, "proof entry", proof));
      ids.put("rejectionEntry", admitted(blue, "rejection entry", rejection));
      admitted(blue, "plain timeline channel",
          Map.of("type", "Coordination/Timeline Channel", "actor", actor, "timeline", timeline));

      // 1. What the schemas reject, with the exact failure kind.
      var schema = new TreeMap<String, Object>();
      for (String field : List.of("evidenceTimeline", "mandateProcessorKey", "evidenceProfile", "timeline", "actor"))
        expect(blue, schema, "channel without " + field, with(channel, field, null), SCHEMA);
      expect(blue, schema, "channel with a short key", with(channel, "mandateProcessorKey", "ef"), SCHEMA);
      expect(blue, schema, "channel with a text profile", with(channel, "evidenceProfile", "latest"), TYPE);
      expect(blue, schema, "channel with an integer profile", with(channel, "evidenceProfile", 7), TYPE);
      expect(blue, schema, "channel with a list profile", with(channel, "evidenceProfile", List.of(profile)), SCHEMA);
      expect(blue, schema, "channel with a bare base profile",
          with(channel, "evidenceProfile", Map.of("type", "Coordination/Evidence Profile")), SCHEMA);
      expect(blue, schema, "channel with a type-only specialisation as profile", with(channel, "evidenceProfile",
          Map.of("type", "PrivateMandates/RISC Zero Succinct Receipt Profile")), SCHEMA);
      expect(blue, schema, "profile with an empty provider list", with(profile, "allowedProviders", List.of()), ADMITTED);
      expect(blue, schema, "profile with only a digest",
          with(with(profile, "allowedProviders", null), "providerSetDigest", HEX), SCHEMA);
      expect(blue, schema, "profile with an extra valued field", with(profile, "providerSetDigest", HEX), SCHEMA);
      expect(blue, schema, "profile with a short provider key", with(profile, "allowedProviders", List.of("01")), SCHEMA);
      expect(blue, schema, "profile with a repeated provider key",
          with(profile, "allowedProviders", List.of("01".repeat(32), "01".repeat(32))), SCHEMA);
      for (String field : List.of("programImageId", "allowedProviders", "factsRule"))
        expect(blue, schema, "profile without " + field, with(profile, field, null), SCHEMA);
      // The profile names exactly one of two facts rules; any third value is rejected by the schema.
      expect(blue, schema, "profile with the facts rule FULL(D)", with(profile, "factsRule", "FULL(D)"), ADMITTED);
      expect(blue, schema, "profile with the facts rule MERKLE(FULL(D))",
          with(profile, "factsRule", "MERKLE(FULL(D))"), ADMITTED);
      expect(blue, schema, "channel whose profile has the facts rule MERKLE(FULL(D))", with(channel, "evidenceProfile",
          with(profile, "factsRule", "MERKLE(FULL(D))")), ADMITTED);
      expect(blue, schema, "profile with another facts rule", with(profile, "factsRule", "CANONICAL"), SCHEMA);
      expect(blue, schema, "profile with the facts rule MERKLE", with(profile, "factsRule", "MERKLE"), SCHEMA);
      expect(blue, schema, "profile with the facts rule in lower case", with(profile, "factsRule", "merkle(full(d))"), SCHEMA);
      expect(blue, schema, "profile with both facts rules as a list",
          with(profile, "factsRule", List.of("FULL(D)", "MERKLE(FULL(D))")), TYPE);
      expect(blue, schema, "profile with a short image id", with(profile, "programImageId", "ab"), SCHEMA);
      expect(blue, schema, "authority without commitment", with(authority, "mandateCommitment", null), SCHEMA);
      expect(blue, schema, "authority without holder", with(authority, "actor", null), SCHEMA);
      expect(blue, schema, "authority with a short commitment", with(authority, "mandateCommitment", "ab"), SCHEMA);
      expect(blue, schema, "authority with an integer commitment", with(authority, "mandateCommitment", 7), TYPE);
      expect(blue, schema, "authority with a clear mandate text", with(authority, "mandate", "someMandateBlueId"), SCHEMA);
      expect(blue, schema, "authority with a valued mandate object", with(authority, "mandate", Map.of("a", 1)), SCHEMA);
      expect(blue, schema, "authority with another valued field", with(authority, "note", "x"), SCHEMA);
      Map<String, Object> operationTimelineEntry = Map.of("type", "Coordination/Timeline Entry", "actor", actor,
          "timeline", timeline, "timestamp", 200, "message", Map.of("type", "Contracts/Operation Request",
              "channel", "ownerChannel", "operation", "approve"), "onBehalfOf", authority);
      expect(blue, schema, "timeline entry with a commitment authority", operationTimelineEntry, ADMITTED);
      // A claim the schema rejects makes the whole entry inadmissible: existing Coordination behaviour.
      expect(blue, schema, "timeline entry whose commitment authority has a valued mandate",
          with(operationTimelineEntry, "onBehalfOf", with(authority, "mandate", "someMandateBlueId")), SCHEMA);

      // 2. The profile field is not typed by the schema: typing is structural. These values are admitted,
      // and only the native rule (exact type is a supported specialisation of Evidence Profile) excludes them.
      var profileNative = new TreeMap<String, Object>();
      expect(blue, profileNative, "untyped object with the profile fields", with(channel, "evidenceProfile",
          with(profile, "type", null)), ADMITTED);
      expect(blue, profileNative, "untyped object with arbitrary content",
          with(channel, "evidenceProfile", Map.of("anything", "x")), ADMITTED);
      expect(blue, profileNative, "base Evidence Profile with a field", with(channel, "evidenceProfile",
          Map.of("type", "Coordination/Evidence Profile", "anything", "x")), ADMITTED);
      expect(blue, profileNative, "a Signed Timeline", with(channel, "evidenceProfile", timeline), ADMITTED);
      expect(blue, profileNative, "a Timeline Provider", with(channel, "evidenceProfile", provider), ADMITTED);
      expect(blue, profileNative, "a plain Timeline Channel", with(channel, "evidenceProfile",
          Map.of("type", "Coordination/Timeline Channel", "actor", actor, "timeline", timeline)), ADMITTED);
      expect(blue, profileNative, "a commitment authority", with(channel, "evidenceProfile", authority), ADMITTED);
      // Not evidence of typing: some unrelated typed values happen to be refused. Recorded as observed.
      expect(blue, profileNative, "a Principal Actor (refused, unlike the values above)",
          with(channel, "evidenceProfile", actor), TYPE);

      // 3. The commitment authority schema limits valued fields but does not close the field set.
      // These claims are admitted; the processor rule (fields exactly actor and mandateCommitment) rejects them.
      var authorityNative = new TreeMap<String, Object>();
      expect(blue, authorityNative, "mandate carrying only a type", with(authority, "mandate", typeOnlyMandate), ADMITTED);
      expect(blue, authorityNative, "mandate as a reference that resolves",
          with(authority, "mandate", Map.of("blueId", mandates.exportId("Mandate"))), ADMITTED);
      expect(blue, authorityNative, "another field carrying only a type",
          with(authority, "note", Map.of("type", "Text")), ADMITTED);
      expect(blue, authorityNative, "timeline entry whose claim has a type-only mandate",
          with(operationTimelineEntry, "onBehalfOf", with(authority, "mandate", typeOnlyMandate)), ADMITTED);
      // Not a schema rejection: an unavailable reference target leaves admission incomplete.
      expect(blue, authorityNative, "mandate as a reference whose content is unavailable",
          with(authority, "mandate", Map.of("blueId", PRIOR.get("Mandates"))), INCOMPLETE);

      // 4. Proof Entry and Rejection Entry have open schemas: every malformed entry below is admitted as
      // Blue content. The processor skips it.
      var skipped = new TreeMap<String, Object>();
      expect(blue, skipped, "proof entry with an extra field", with(proof, "note", "x"), ADMITTED);
      expect(blue, skipped, "proof entry without receipt", with(proof, "receipt", null), ADMITTED);
      expect(blue, skipped, "proof entry without document", with(proof, "document", null), ADMITTED);
      expect(blue, skipped, "proof entry without operationEntry", with(proof, "operationEntry", null), ADMITTED);
      expect(blue, skipped, "proof entry with an integer receipt", with(proof, "receipt", 7), ADMITTED);
      expect(blue, skipped, "proof entry with an empty receipt", with(proof, "receipt", ""), ADMITTED);
      expect(blue, skipped, "proof entry with a list receipt", with(proof, "receipt", List.of("AAECAw==")), ADMITTED);
      expect(blue, skipped, "proof entry with a receipt that is not canonical base64",
          with(proof, "receipt", "not base64 !!"), ADMITTED);
      expect(blue, skipped, "proof entry with a text document", with(proof, "document", "someDocumentId"), ADMITTED);
      expect(blue, skipped, "proof entry with an integer operationEntry", with(proof, "operationEntry", 7), ADMITTED);
      expect(blue, skipped, "proof entry with only its type", Map.of("type", "Coordination/Proof Entry"), ADMITTED);
      expect(blue, skipped, "proof entry with only an unknown field",
          Map.of("type", "Coordination/Proof Entry", "note", "x"), ADMITTED);
      expect(blue, skipped, "rejection with an extra field", with(rejection, "reason", "x"), ADMITTED);
      expect(blue, skipped, "rejection without document", with(rejection, "document", null), ADMITTED);
      expect(blue, skipped, "rejection without operationEntry", with(rejection, "operationEntry", null), ADMITTED);
      expect(blue, skipped, "rejection with only its type", Map.of("type", "Coordination/Rejection Entry"), ADMITTED);
      expect(blue, skipped, "rejection with the earlier text fields",
          Map.of("type", "Coordination/Rejection Entry", "documentId", "x", "operationEntry", "y"), ADMITTED);
      expect(blue, skipped, "rejection with an object that names nothing as document",
          with(rejection, "document", Map.of("id", "x")), ADMITTED);

      // 5. Naming is by BlueId, never by wire form: a reference and the same content written in full
      // give the same entry BlueId, so no rule can ask whether a field "is a reference".
      var records = map(WireData.json(Files.readString(root.resolve("blue-coordination/dist/package-records.json"))));
      String target = coordination.exportId("Order Key");
      Object inline = WireData.json(map(records.get(target)).get("text").toString());
      String byReference = admitted(blue, "rejection naming by reference", with(rejection, "document", Map.of("blueId", target)));
      String byContent = admitted(blue, "rejection naming by content", with(rejection, "document", inline));
      require(byReference.equals(byContent), "A reference and its inlined content must give the same BlueId");
      require(!byReference.equals(ids.get("rejectionEntry")), "Another named document must give another entry BlueId");

      // 6. The known limit. A {blueId} value is opened by Language admission wherever it stands in an entry,
      // as for the free document field of an Operation Request. The entry schemas cannot change that.
      var references = new TreeMap<String, Object>();
      expect(blue, references, "operation request, document content unavailable", Map.of("type", "Contracts/Operation Request",
          "channel", "c", "operation", "o", "document", unavailable), INCOMPLETE);
      expect(blue, references, "proof entry, document content unavailable", with(proof, "document", unavailable), INCOMPLETE);
      expect(blue, references, "proof entry, operationEntry content unavailable",
          with(proof, "operationEntry", unavailable), INCOMPLETE);
      expect(blue, references, "proof entry, receipt is an unavailable reference", with(proof, "receipt", unavailable), INCOMPLETE);
      expect(blue, references, "proof entry, unknown extra field holds an unavailable reference",
          with(proof, "note", unavailable), INCOMPLETE);
      expect(blue, references, "proof entry, unavailable reference nested in an extra field",
          with(proof, "note", Map.of("inner", List.of(unavailable))), INCOMPLETE);
      expect(blue, references, "rejection, document content unavailable", with(rejection, "document", unavailable), INCOMPLETE);
      expect(blue, references, "rejection, operationEntry content unavailable",
          with(rejection, "operationEntry", unavailable), INCOMPLETE);
      expect(blue, references, "evidence timeline entry whose proof names unavailable content",
          Map.of("type", "Coordination/Timeline Entry", "actor", actor, "timeline", proofs, "timestamp", 201,
              "message", with(proof, "document", unavailable)), INCOMPLETE);
      expect(blue, references, "proof entry, document blueId is not a BlueId",
          with(proof, "document", Map.of("blueId", "not-a-blue-id")), "Invalid/InvalidBlueId");
      expect(blue, references, "proof entry, document reference with other content",
          with(proof, "document", Map.of("blueId", target, "extra", 1)), "Invalid/InvalidReferenceShape");

      // 7. Admitted as data; decided by the native rules stated in the two specifications.
      var nativeRules = new TreeMap<String, Object>();
      expect(blue, nativeRules, "channel key not lower-case hex", with(channel, "mandateProcessorKey", "EF".repeat(32)), ADMITTED);
      expect(blue, nativeRules, "commitment not lower-case hex", with(authority, "mandateCommitment", "zz".repeat(32)), ADMITTED);
      expect(blue, nativeRules, "image id not lower-case hex", with(profile, "programImageId", "AB".repeat(32)), ADMITTED);
      expect(blue, nativeRules, "provider list not ascending",
          with(profile, "allowedProviders", List.of("02".repeat(32), "01".repeat(32))), ADMITTED);
      expect(blue, nativeRules, "profile with a further field carrying only a type",
          with(profile, "note", Map.of("type", "Text")), ADMITTED);

      require(MISMATCHES.isEmpty(), "Language behaviour differs from the recorded expectation:\n" + String.join("\n", MISMATCHES));

      var result = new TreeMap<String, Object>();
      result.put("coordinationPackage", coordination.blueId());
      result.put("mandatesPackage", mandates.blueId());
      result.put("privateMandatesPackage", privateMandates.blueId());
      var typeIds = new TreeMap<String, Object>();
      for (String name : List.of("Timeline Channel", "Timeline Channel with Evidence", "Evidence Profile", "Proof Entry", "Rejection Entry"))
        typeIds.put("Coordination/" + name, coordination.exportId(name));
      for (String name : privateMandates.exports().keySet()) typeIds.put("PrivateMandates/" + name, privateMandates.exportId(name));
      result.put("typeBlueIds", typeIds);
      result.put("sampleBlueIds", ids);
      result.put("schemaDecisions", schema);
      result.put("profileAdmittedBySchemaExcludedByNativeRule", profileNative);
      result.put("authorityAdmittedBySchemaRejectedByProcessorRule", authorityNative);
      result.put("entriesAdmittedBySchemaSkippedByProcessor", skipped);
      result.put("referenceAndInlinedContentSameBlueId", byReference.equals(byContent));
      result.put("referenceAdmissionOutcomes", references);
      result.put("leftToNativeRules", nativeRules);
      result.put("scope", "Language schema, inheritance and retained prior identities; not native execution qualification");
      System.out.println(WireData.write(result));
    }
  }
}
