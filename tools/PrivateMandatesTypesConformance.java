import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native Language conformance for the Coordination evidence types and the private-mandates schemas; Core qualifies execution. */
public final class PrivateMandatesTypesConformance {
  /**
   * Identities of the default (Access Events) edition. The evidence packages are additive: the
   * Coordination and Mandates publications they require must still carry exactly these, so a document
   * with an evidence channel consumes the same signed timelines as every other document.
   */
  static final Map<String, String> DEFAULT = Map.ofEntries(
      Map.entry("Coordination", "4gmSjwn3DCYBVeDieXxuXgsPvvz2dU6ovFXnnuyv2RjA"),
      Map.entry("Coordination/Timeline Channel", "GCd3gAEibsaZi1vdhFhTSfRch1HPruFcE1pgm9eAMKwy"),
      Map.entry("Coordination/Public Timeline Channel", "BvtgU3qxEP7vTPD7vTwC1qTdvWSBwwxsaA4j6xkyqbJt"),
      Map.entry("Coordination/Signed Timeline", "EzfsjTUabtmb2KAMy7LHDrM9ffQzbx7JvXsGVSr6wh73"),
      Map.entry("Coordination/Timeline Entry", "G4dok8HLuBFPutTwD4h71y3y6ph7esA6qJGtDvoYAxKV"),
      Map.entry("Coordination/Timeline Provider", "AT9pX83cgt2mw9EPutC3dHKeWU8Ruj4TXB2cbTkBRxS7"),
      Map.entry("Coordination/Provider Descriptor", "kqnzQTYbwKbwvRTR4GT8P1WTfCY7EW6GKizMGT6VwNs"),
      Map.entry("Coordination/Provider Attestation", "2Ap8D4xbzPNtCTe4jcFAJR4rLbef4ZzoPuPKiYqiqcwy"),
      Map.entry("Coordination/Timeline Completeness Guarantee", "2j2ZNTZnv3w6GC3XxoUG7pe35gVHJLaKqiHQjdHXAcHH"),
      Map.entry("Coordination/Timeline Attestation", "CSm4Ph8vD14hyE1Yhb2fNpNiBqGPEJ6tTcVvrVRFaGyk"),
      Map.entry("Coordination/Timeline Range Evidence", "Hh9pViBbBJw3zP7a19oJDwG9pZVCoGNqF6MYHmRfpjXo"),
      Map.entry("Coordination/Timeline Successor Evidence", "HKipW4hQAiDPfDX6oMH25LERWurv9vDnTbywQ2siDvcz"),
      Map.entry("Coordination/Ed25519 Public Key", "4QJmKi3QsZcU5MmoScSdruB5fayT8ykSNdZ3C3jKJx9e"),
      Map.entry("Coordination/Order Key", "FenCaravyQuwz4aT1LfX6i8nkbWPEhcFZ4fYbg2GijgJ"),
      Map.entry("Mandates", "4kaMxybWTTeTpkzUtoYVUPk8dUo3HxKM5MG5joxN6LFL"),
      Map.entry("Mandates/Authority", "AypmNprcDHuFc293hkDJFJ91GKtwbH7mDiCii8hmUBjP"),
      Map.entry("Mandates/Mandate Authority", "2YnsAG44Sg9Q9XrzUe9Yz5PNXkHuxDcpvv4Wv4QNysTe"));
  /** BlueIds of content no mounted package holds (the withdrawn rebuilt Coordination and Mandates candidates). */
  static final String UNHELD = "HHsCUAybKPWQJesQCSrpk6dpppjiii7tyz9vaWavMdP5", UNHELD_MANDATE = "CGJTGJvfh4TTFeawShQyeTXa3xzwNxz3UnQmSnwJEtTC";
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
        "Coordination", "blue-coordination", "CoordinationEvidence", "blue-coordination-evidence",
        "Mandates", "blue-mandates", "PrivateMandates", "blue-private-mandates").entrySet())
      open.put(mount.getKey(), BluePackage.open(root.resolve(mount.getValue() + "/dist/package.bluepkg")));
    var coordination = open.get("Coordination");
    var evidence = open.get("CoordinationEvidence");
    var mandates = open.get("Mandates");
    var privateMandates = open.get("PrivateMandates");
    // Private Mandates has one profile, the signed statement, and no other evidence form.
    require(privateMandates.exports().keySet().equals(Set.of("Mandate Commitment Authority", "Mandate State Attestation",
        "Signed Statement Profile")), "Private Mandates exports changed: " + privateMandates.exports().keySet());
    // The required publications are the default edition's, with their exact identities.
    for (var row : DEFAULT.entrySet()) {
      String[] name = row.getKey().split("/", 2);
      var publication = open.get(name[0]);
      String actual = name.length == 1 ? publication.blueId() : publication.exportId(name[1]);
      require(row.getValue().equals(actual), "Default-edition identity changed: " + row.getKey() + " is " + actual);
    }
    // The evidence package adds exactly its four types and redefines nothing of Coordination.
    require(evidence.exports().keySet().equals(Set.of("Timeline Channel with Evidence", "Evidence Profile", "Proof Entry",
        "Rejection Entry")), "Evidence package exports changed: " + evidence.exports().keySet());
    for (String name : evidence.exports().keySet())
      require(!coordination.exports().containsKey(name), "Evidence type must not be a Coordination export: " + name);
    for (String name : privateMandates.exports().keySet())
      require(!mandates.exports().containsKey(name) && !evidence.exports().containsKey(name),
          "Extension must not redefine a required export: " + name);

    var bundle = PackageBundle.builder();
    open.forEach(bundle::mount);
    try (Blue blue = Blue.builder().packages(bundle.build()).build()) {
      descends(blue, "Timeline Channel with Evidence", evidence.exportId("Timeline Channel with Evidence"),
          coordination.exportId("Timeline Channel"));
      descends(blue, "Mandate Commitment Authority", privateMandates.exportId("Mandate Commitment Authority"),
          mandates.exportId("Authority"));
      descends(blue, "Signed Statement Profile", privateMandates.exportId("Signed Statement Profile"),
          evidence.exportId("Evidence Profile"));
      require(!NativeRuntime.ancestry(privateMandates.exportId("Mandate Commitment Authority"), new NativeRuntime(blue))
          .contains(mandates.exportId("Mandate Authority")), "The commitment claim must not be a Mandate Authority");

      // A type-only node is unvalued; a required actor needs identifying content.
      Map<String, Object> actor = Map.of("type", "Coordination/Principal Actor", "displayName", "Holder");
      Map<String, Object> provider = Map.of("type", "Coordination/Timeline Provider",
          "endpoint", "https://provider.example", "publicKey", HEX);
      Map<String, Object> timeline = Map.of("type", "Coordination/Signed Timeline", "provider", provider,
          "publicRead", false, "url", "https://provider.example/timelines/operations");
      Map<String, Object> proofs = with(timeline, "url", "https://provider.example/timelines/proofs");
      Map<String, Object> profile = Map.of("type", "PrivateMandates/Signed Statement Profile", "statementSignerKey", "cd".repeat(32));
      Map<String, Object> channel = Map.of("type", "CoordinationEvidence/Timeline Channel with Evidence",
          "actor", actor, "timeline", timeline, "evidenceTimeline", proofs,
          "mandateProcessorKey", "ef".repeat(32), "evidenceProfile", profile);
      Map<String, Object> authority = Map.of("type", "PrivateMandates/Mandate Commitment Authority",
          "actor", actor, "mandateCommitment", HEX);
      // References by content BlueId. These two targets are content the mounted packages provide.
      Map<String, Object> document = Map.of("blueId", coordination.exportId("Timeline Channel"));
      Map<String, Object> operationEntry = Map.of("blueId", coordination.exportId("Timeline Entry"));
      Map<String, Object> proof = Map.of("type", "CoordinationEvidence/Proof Entry", "receipt", "AAECAw==",
          "document", document, "operationEntry", operationEntry);
      Map<String, Object> rejection = Map.of("type", "CoordinationEvidence/Rejection Entry",
          "document", document, "operationEntry", operationEntry);

      final String ADMITTED = "Admitted", SCHEMA = "Invalid/SchemaViolation", TYPE = "Invalid/TypeCompatibilityViolation",
          INCOMPLETE = "Incomplete/ProviderUnavailable";
      Map<String, Object> unavailable = Map.of("blueId", UNHELD);
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
          with(channel, "evidenceProfile", Map.of("type", "CoordinationEvidence/Evidence Profile")), SCHEMA);
      expect(blue, schema, "channel with a type-only specialisation as profile", with(channel, "evidenceProfile",
          Map.of("type", "PrivateMandates/Signed Statement Profile")), SCHEMA);
      // The profile: one required key of fixed length, at most one field with a value.
      expect(blue, schema, "profile without statementSignerKey", with(profile, "statementSignerKey", null), SCHEMA);
      expect(blue, schema, "profile with a short key", with(profile, "statementSignerKey", "ef"), SCHEMA);
      expect(blue, schema, "profile with an integer key", with(profile, "statementSignerKey", 7), TYPE);
      expect(blue, schema, "profile with a provider list (a second valued field)",
          with(profile, "allowedProviders", List.of("01".repeat(32))), SCHEMA);
      expect(blue, schema, "profile with a further valued field", with(profile, "note", "x"), SCHEMA);
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
          Map.of("type", "CoordinationEvidence/Evidence Profile", "anything", "x")), ADMITTED);
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
          with(authority, "mandate", Map.of("blueId", UNHELD_MANDATE)), INCOMPLETE);

      // 4. Proof Entry and Rejection Entry have open schemas: every malformed entry below is admitted as
      // Blue content. The processor skips it.
      var skipped = new TreeMap<String, Object>();
      expect(blue, skipped, "proof entry with an extra field", with(proof, "note", "x"), ADMITTED);
      expect(blue, skipped, "proof entry without receipt", with(proof, "receipt", null), ADMITTED);
      expect(blue, skipped, "proof entry with an integer receipt", with(proof, "receipt", 7), ADMITTED);
      expect(blue, skipped, "proof entry with an empty receipt", with(proof, "receipt", ""), ADMITTED);
      expect(blue, skipped, "proof entry with a list receipt", with(proof, "receipt", List.of("AAECAw==")), ADMITTED);
      expect(blue, skipped, "proof entry with a receipt that is not canonical base64",
          with(proof, "receipt", "not base64 !!"), ADMITTED);
      expect(blue, skipped, "proof entry with a text document", with(proof, "document", "someDocumentId"), ADMITTED);
      expect(blue, skipped, "proof entry with an integer operationEntry", with(proof, "operationEntry", 7), ADMITTED);
      expect(blue, skipped, "proof entry with only its type", Map.of("type", "CoordinationEvidence/Proof Entry"), ADMITTED);
      expect(blue, skipped, "proof entry with only an unknown field",
          Map.of("type", "CoordinationEvidence/Proof Entry", "note", "x"), ADMITTED);
      expect(blue, skipped, "rejection with an extra field", with(rejection, "reason", "x"), ADMITTED);
      expect(blue, skipped, "rejection without document", with(rejection, "document", null), ADMITTED);
      expect(blue, skipped, "rejection without operationEntry", with(rejection, "operationEntry", null), ADMITTED);
      expect(blue, skipped, "rejection with only its type", Map.of("type", "CoordinationEvidence/Rejection Entry"), ADMITTED);
      expect(blue, skipped, "rejection with the earlier text fields",
          Map.of("type", "CoordinationEvidence/Rejection Entry", "documentId", "x", "operationEntry", "y"), ADMITTED);
      expect(blue, skipped, "rejection with an object that names nothing as document",
          with(rejection, "document", Map.of("id", "x")), ADMITTED);

      // Well formed since only receipt is required: a Proof Entry without the optional advisory hint.
      var hintless = new TreeMap<String, Object>();
      expect(blue, hintless, "proof entry without document", with(proof, "document", null), ADMITTED);
      expect(blue, hintless, "proof entry without operationEntry", with(proof, "operationEntry", null), ADMITTED);
      expect(blue, hintless, "proof entry with receipt only",
          Map.of("type", "CoordinationEvidence/Proof Entry", "receipt", "AAECAw=="), ADMITTED);

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
      expect(blue, nativeRules, "signer key not lower-case hex", with(profile, "statementSignerKey", "CD".repeat(32)), ADMITTED);
      // Key well-formedness beyond the length is a native rule: a small-order key, a non-canonical encoding
      // and bytes that are no curve point are all admitted by the schema.
      final String IDENTITY = "01" + "00".repeat(31), ORDER8 = "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05",
          Y_IS_P = "ed" + "ff".repeat(30) + "7f", NO_POINT = "02" + "00".repeat(31);
      expect(blue, nativeRules, "channel key of small order (identity)", with(channel, "mandateProcessorKey", IDENTITY), ADMITTED);
      expect(blue, nativeRules, "channel key of small order (order 8)", with(channel, "mandateProcessorKey", ORDER8), ADMITTED);
      expect(blue, nativeRules, "channel key not canonically encoded (y = p)", with(channel, "mandateProcessorKey", Y_IS_P), ADMITTED);
      expect(blue, nativeRules, "channel key that is no curve point (y = 2)", with(channel, "mandateProcessorKey", NO_POINT), ADMITTED);
      expect(blue, nativeRules, "signer key of small order", with(profile, "statementSignerKey", IDENTITY), ADMITTED);
      expect(blue, nativeRules, "signer key that is no curve point (y = 2)", with(profile, "statementSignerKey", NO_POINT), ADMITTED);
      expect(blue, nativeRules, "profile with a further field carrying only a type",
          with(profile, "note", Map.of("type", "Text")), ADMITTED);

      // 8. Mandate State Attestation: the document the mandate processor signs (its BlueId is signed).
      var attestationCases = new TreeMap<String, Object>();
      // The referenced documents are written in full here: this tool holds no mandate, and a reference and
      // its content written in full are the same Blue content (case 5). ref1 and ref2 stand for a timeline
      // and an entry.
      Map<String, Object> ref1 = timeline;
      Map<String, Object> ref2 = with(operationTimelineEntry, "onBehalfOf", null);
      Map<String, Object> attestation = new TreeMap<>(Map.of("type", "PrivateMandates/Mandate State Attestation",
          "mandate", actor, "state", provider,
          "authorityPackage", mandates.blueId(), "mandateProgram", "sha256:" + HEX, "approvedProgram", "sha256:" + HEX,
          "position", List.of(Map.of("timeline", ref1), Map.of("timeline", ref2, "lastEntry", ref2)),
          "sequence", 0));
      ids.put("attestation", admitted(blue, "attestation", attestation));
      expect(blue, attestationCases, "well-formed attestation whose references resolve", attestation, ADMITTED);
      expect(blue, attestationCases, "with documents, a later sequence and previous", with(with(with(attestation,
          "documents", List.of(ref1)), "sequence", 3), "previous", ref2), ADMITTED);
      Map<String, Object> firing = Map.of("timestamp", 900, "source", "1".repeat(32), "entry", "z".repeat(43));
      // A reference to a type definition resolves but is not a value, so it does not satisfy a required field.
      expect(blue, attestationCases, "mandate that is a reference to a type definition",
          with(attestation, "mandate", Map.of("blueId", mandates.exportId("Mandate"))), SCHEMA);
      // The two timer bounds name a firing by its order key: timestamp, Timer Source id, Timer Entry id.
      expect(blue, attestationCases, "with a next timer bound", with(attestation, "nextTimerFiring", firing), ADMITTED);
      expect(blue, attestationCases, "with both timer bounds", with(with(attestation, "nextTimerFiring", firing),
          "lastTimerFiring", with(firing, "timestamp", 100)), ADMITTED);
      for (String part : List.of("timestamp", "source", "entry"))
        expect(blue, attestationCases, "timer bound without " + part, with(attestation, "nextTimerFiring", with(firing, part, null)), SCHEMA);
      expect(blue, attestationCases, "timer bound with a negative timestamp",
          with(attestation, "nextTimerFiring", with(firing, "timestamp", -1)), SCHEMA);
      expect(blue, attestationCases, "timer bound with a short source id",
          with(attestation, "nextTimerFiring", with(firing, "source", "abc")), SCHEMA);
      expect(blue, attestationCases, "timer bound with an entry id of 45 characters",
          with(attestation, "nextTimerFiring", with(firing, "entry", "z".repeat(45))), SCHEMA);
      expect(blue, attestationCases, "timer bound whose timestamp is a text",
          with(attestation, "nextTimerFiring", with(firing, "timestamp", "soon")), TYPE);
      expect(blue, attestationCases, "timer bound that is a text", with(attestation, "nextTimerFiring", "soon"), TYPE);
      for (String field : List.of("mandate", "state", "authorityPackage", "mandateProgram", "position", "sequence"))
        expect(blue, attestationCases, "without " + field, with(attestation, field, null), SCHEMA);
      expect(blue, attestationCases, "without approvedProgram (none approved)", with(attestation, "approvedProgram", null), ADMITTED);
      expect(blue, attestationCases, "negative sequence", with(attestation, "sequence", -1), SCHEMA);
      expect(blue, attestationCases, "sequence that is not a number", with(attestation, "sequence", "first"), TYPE);
      // A BlueId is the base58 text of 32 bytes: 32 to 44 characters.
      expect(blue, attestationCases, "authorityPackage of 42 characters",
          with(attestation, "authorityPackage", "1tVm6cThRU3drxZ9G9xTDz3kpTJep4CpNQxUj9CFwL"), ADMITTED);
      expect(blue, attestationCases, "authorityPackage of 32 characters", with(attestation, "authorityPackage", "1".repeat(32)), ADMITTED);
      expect(blue, attestationCases, "authorityPackage of 45 characters", with(attestation, "authorityPackage", "z".repeat(45)), SCHEMA);
      expect(blue, attestationCases, "authorityPackage of 31 characters", with(attestation, "authorityPackage", "1".repeat(31)), SCHEMA);
      expect(blue, attestationCases, "empty position", with(attestation, "position", List.of()), SCHEMA);
      expect(blue, attestationCases, "position that is not a list", with(attestation, "position", "x"), TYPE);
      // A reference may name a member of a cyclic set: a plain id, '#' and a canonical decimal index. The
      // Language accepts that form and refuses the others; the content of the made-up ids is not held here.
      var memberIds = new TreeMap<String, Object>();
      for (String index : List.of("0", "3", "10", "999999999"))
        expect(blue, memberIds, "state named by a member id #" + index,
            with(attestation, "state", Map.of("blueId", UNHELD + "#" + index)), INCOMPLETE);
      expect(blue, memberIds, "mandate named by a member id", with(attestation, "mandate", Map.of("blueId", UNHELD + "#1")), INCOMPLETE);
      expect(blue, memberIds, "documents naming a member id",
          with(attestation, "documents", List.of(Map.of("blueId", UNHELD + "#0"))), INCOMPLETE);
      expect(blue, memberIds, "last entry named by a member id", with(attestation, "position",
          List.of(Map.of("timeline", ref1, "lastEntry", Map.of("blueId", UNHELD + "#2")))), INCOMPLETE);
      for (String bad : List.of("#01", "#-1", "#+1", "#", "#1#2", "#1a", "# 1", "#１"))
        expect(blue, memberIds, "state named by an id ending in " + bad,
            with(attestation, "state", Map.of("blueId", UNHELD + bad)), "Invalid/InvalidBlueId");
      expect(blue, memberIds, "state named by a member id whose master is not a plain id",
          with(attestation, "state", Map.of("blueId", "not-a-blue-id#0")), "Invalid/InvalidBlueId");
      // Left to the signer: the bound of 9 digits on the index, and plain-only positions.
      expect(blue, memberIds, "state named by a member id with an index of 10 digits (signer rule)",
          with(attestation, "state", Map.of("blueId", UNHELD + "#1234567890")), INCOMPLETE);
      expect(blue, memberIds, "previous named by a member id (signer rule: plain only)",
          with(attestation, "previous", Map.of("blueId", UNHELD + "#0")), INCOMPLETE);

      // The schema does not close the field set or check the canonical construction: left to the verifier.
      var attestationVerifier = new TreeMap<String, Object>();
      expect(blue, attestationVerifier, "extra field with a value", with(attestation, "signature", HEX), ADMITTED);
      expect(blue, attestationVerifier, "extra field carrying only a type", with(attestation, "note", Map.of("type", "Text")), ADMITTED);
      expect(blue, attestationVerifier, "sequence written as the text \"0\"", with(attestation, "sequence", "0"), ADMITTED);
      expect(blue, attestationVerifier, "previous present with sequence 0", with(attestation, "previous", ref2), ADMITTED);
      expect(blue, attestationVerifier, "later sequence without previous", with(attestation, "sequence", 3), ADMITTED);
      expect(blue, attestationVerifier, "position rows not ascending",
          with(attestation, "position", List.of(Map.of("timeline", ref2), Map.of("timeline", ref1))), ADMITTED);
      expect(blue, attestationVerifier, "position row with another field",
          with(attestation, "position", List.of(Map.of("timeline", ref1, "note", "x"))), ADMITTED);
      expect(blue, attestationVerifier, "timer bound with a further part",
          with(attestation, "nextTimerFiring", with(firing, "note", "x")), ADMITTED);
      expect(blue, attestationVerifier, "timer source id with a character outside base58",
          with(attestation, "nextTimerFiring", with(firing, "source", "0".repeat(32))), ADMITTED);
      expect(blue, attestationVerifier, "mandate that is a text, not a reference", with(attestation, "mandate", "x"), ADMITTED);

      require(MISMATCHES.isEmpty(), "Language behaviour differs from the recorded expectation:\n" + String.join("\n", MISMATCHES));

      var result = new TreeMap<String, Object>();
      result.put("coordinationPackage", coordination.blueId());
      result.put("coordinationEvidencePackage", evidence.blueId());
      result.put("mandatesPackage", mandates.blueId());
      result.put("privateMandatesPackage", privateMandates.blueId());
      var typeIds = new TreeMap<String, Object>();
      for (String name : List.of("Timeline Channel", "Signed Timeline", "Timeline Entry"))
        typeIds.put("Coordination/" + name, coordination.exportId(name));
      for (String name : evidence.exports().keySet()) typeIds.put("CoordinationEvidence/" + name, evidence.exportId(name));
      for (String name : privateMandates.exports().keySet()) typeIds.put("PrivateMandates/" + name, privateMandates.exportId(name));
      result.put("typeBlueIds", typeIds);
      result.put("sampleBlueIds", ids);
      result.put("schemaDecisions", schema);
      result.put("profileAdmittedBySchemaExcludedByNativeRule", profileNative);
      result.put("authorityAdmittedBySchemaRejectedByProcessorRule", authorityNative);
      result.put("entriesAdmittedBySchemaSkippedByProcessor", skipped);
      result.put("proofEntriesWellFormedWithoutHint", hintless);
      result.put("referenceAndInlinedContentSameBlueId", byReference.equals(byContent));
      result.put("referenceAdmissionOutcomes", references);
      result.put("leftToNativeRules", nativeRules);
      result.put("attestationSchemaDecisions", attestationCases);
      result.put("memberIdReferenceOutcomes", memberIds);
      result.put("attestationAdmittedBySchemaLeftToVerifier", attestationVerifier);
      result.put("scope", "Language schema, inheritance and unchanged default-edition identities; not native execution qualification");
      System.out.println(WireData.write(result));
    }
  }
}
