import static blue.core.CompositionPackages.list;
import static blue.core.CompositionPackages.obj;

import blue.bex.BexError;
import blue.bex.Values;
import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.contracts.RuntimeBindings;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
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
import java.util.Set;

public final class VerifyCafeSupply {
    private static final Set<String> MOUNTS = Set.of(
            "Activation", "Agreements", "Amendments", "BEX", "Clauses", "Commerce",
            "Connections", "Contracts", "Coordination", "DefinitionRead", "Dispatch",
            "Events", "Language", "Money", "Parties", "Time");

    private final Contracts processor;
    private final Map<String, String> versions = new LinkedHashMap<>();
    private Contracts.Document document;
    private long clock = 1;
    private Object firstQuote;

    private VerifyCafeSupply(Contracts processor, Object source) {
        this.processor = processor;
        var result = processor.initialize(source);
        equal("APPLIED", result.status(), "initialization " + result.observations());
        document = result.document();
        equal(false, read("/activation/active"), "agreement starts inactive");
        equal("1", String.valueOf(read("/catalog/revision")), "initial catalogue revision");
        equal(Map.of(), read("/quotes"), "no initial quotes");
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            throw new IllegalArgumentException("Provide the Blue Packages root and this example directory.");
        }
        var root = Path.of(args[0]).toAbsolutePath().normalize();
        var example = Path.of(args[1]);
        var catalogue = root.resolve("PACKAGES.json");
        var mounts = obj(obj(CompositionPackages.yaml(catalogue)).get("mounts"));
        mounts.keySet().retainAll(MOUNTS);
        equal(MOUNTS, mounts.keySet(), "package catalogue mounts");

        var source = example.resolve("cafe-supply-agreement.blue");
        var operations = example.resolve("operations.yaml");
        var selection = Files.createTempFile("cafe-supply-packages-", ".json");
        try {
            Files.writeString(selection, WireData.write(map("mounts", mounts)));
            var packages = CompositionPackages.published(root, selection);
            var bindings = RuntimeBindings.accessEvents().withDefinitionReadV1();
            try (var language = packages.language(); var runtime = new AuthoringRuntime(bindings)) {
                var evidence = new VerifyCafeSupply(runtime.processor(language), CompositionPackages.yaml(source));
                var steps = list(obj(CompositionPackages.yaml(operations)).get("steps"));
                var results = new ArrayList<Object>();
                for (var step : steps) results.add(evidence.run(obj(step)));
                var finalQuotes = obj(evidence.read("/quotes"));
                equal(Set.of("restock-01", "restock-02"), finalQuotes.keySet(), "saved quote keys");
                equal(evidence.firstQuote, finalQuotes.get("restock-01"), "original quote snapshot at finish");
                var earlierCatalogue = obj(evidence.firstQuote).get("catalogBlueId");
                var currentCatalogue = obj(finalQuotes.get("restock-02")).get("catalogBlueId");
                if (Objects.equals(earlierCatalogue, currentCatalogue)) {
                    throw new AssertionError("The quotes must identify distinct catalogue snapshots.");
                }
                System.out.println(WireData.write(map(
                        "outcome", "PASS",
                        "packageCatalogueSha256", sha256(catalogue),
                        "sourceSha256", sha256(source),
                        "operationsSha256", sha256(operations),
                        "verifierSha256", sha256(example.resolve("VerifyCafeSupply.java")),
                        "mountedPackages", mounts,
                        "steps", results,
                        "finalQuotes", finalQuotes)));
            }
        } finally {
            Files.deleteIfExists(selection);
        }
    }

    private Map<String, Object> run(Map<String, Object> step) {
        var id = (String) step.get("id");
        var party = (String) step.get("party");
        var operation = (String) step.get("operation");
        var expect = obj(step.get("expect"));
        var request = obj(step.get("request"));
        var before = document.blueId();
        var requestedVersion = before;
        if (step.containsKey("documentVersionAfter")) {
            requestedVersion = versions.get(step.get("documentVersionAfter"));
            if (requestedVersion == null || requestedVersion.equals(before)) {
                throw new AssertionError("The stale-document input must refer to an older version.");
            }
        }
        var input = map("source", party, "operation", map(
                "type", "Contracts/Operation Request", "document", map("blueId", requestedVersion),
                "channel", party, "operation", operation, "request", request,
                "requireExactDocumentVersion", true));
        var quotesBefore = read("/quotes");
        var timestamp = clock++;
        var result = processor.process(document, input, timestamp);
        var next = result.document();
        var events = processor.emitted(result);
        var eventKinds = eventKinds(events);
        var record = map("id", id, "input", input, "timestampMicros", timestamp,
                "nativeStatus", result.status(), "beforeBlueId", before, "afterBlueId", next.blueId(),
                "eventKinds", eventKinds);

        if (expect.containsKey("rejection")) {
            equal(before, next.blueId(), id + " leaves the agreement version unchanged");
            equal(List.of(), events, id + " emits no events");
            var diagnostic = result.observations().get("diagnostic");
            if (diagnostic != null) record.put("nativeDiagnostic", diagnostic);
            if (expect.containsKey("diagnostic")) {
                equal(expect.get("diagnostic"), obj(diagnostic).get("code"), id + " native diagnostic");
            }
            var reason = (String) expect.get("rejection");
            switch (reason) {
                case "wrong-role", "stale-document" -> record.put("blockedInput", reason);
                default -> {
                    try {
                        ClauseGasProbe.diagnose(processor, document, input, timestamp);
                        throw new AssertionError("Expected domain error " + reason + " for " + id);
                    } catch (BexError error) {
                        equal(reason, error.getMessage(), id + " domain error");
                        record.put("domainError", error.getMessage());
                    }
                }
            }
        } else {
            equal("APPLIED", result.status(), id + " " + result.observations());
        }
        document = next;
        versions.put(id, document.blueId());

        check(expect, "activation", "/activation/active", record);
        check(expect, "catalogueRevision", "/catalog/revision", record);
        check(expect, "cupPriceMinor", "/catalog/entries/cups-12oz/unitAmountMinor", record);
        check(expect, "amendmentRevision", "/catalogueChanges/revision", record);
        if (expect.containsKey("pendingApprovals")) {
            var approvals = read("/catalogueChanges/proposal/approvals");
            equal(expect.get("pendingApprovals"), approvals, id + " recorded approvals");
            record.put("pendingApprovals", approvals);
        }
        if (expect.containsKey("appliedAmendment")) {
            equal(Map.of(), read("/catalogueChanges/proposal"), id + " clears the pending proposal");
            var proposal = expect.get("appliedAmendment");
            equal(true, read("/catalogueChanges/history/" + proposal), id + " records the applied proposal");
            record.put("appliedAmendment", proposal);
        }
        if (expect.containsKey("events")) equal(expect.get("events"), eventKinds, id + " events");
        if (expect.containsKey("absentQuote")) {
            equal(Values.UNDEFINED, read("/quotes/" + expect.get("absentQuote")), id + " stores no quote");
            record.put("absentQuote", expect.get("absentQuote"));
        }
        if (expect.containsKey("quote")) {
            var quoteKey = (String) expect.get("quote");
            var path = "/quotes/" + quoteKey;
            var quote = obj(read(path));
            equal(WireData.write(request), WireData.write(quote.get("intent")), path + " intent");
            equal("EUR", quote.get("currency"), path + " currency");
            equal(String.valueOf(request.get("catalogRevision")), String.valueOf(quote.get("catalogRevision")),
                    path + " catalogue revision");
            check(expect, "totalMinor", path + "/totalMinor", record);
            equal(expect.get("totalMinor").toString(), quote.get("subtotalMinor").toString(), path + " subtotal");
            equal("0", quote.get("discountMinor").toString(), path + " discount");
            var lines = list(quote.get("lines"));
            var itemPrices = lines.stream().map(line -> obj(line).get("unitAmountMinor").toString()).toList();
            var lineTotals = lines.stream().map(line -> obj(line).get("lineTotalMinor").toString()).toList();
            equal(strings(expect.get("unitAmountsMinor")), itemPrices, path + " unit prices");
            equal(strings(expect.get("lineTotalsMinor")), lineTotals, path + " line totals");
            record.put("quote", quoteKey);
            if (firstQuote == null) firstQuote = quote;
        }
        if (firstQuote != null) {
            equal(firstQuote, read("/quotes/restock-01"), id + " preserves the full original quote");
        }
        if (Boolean.TRUE.equals(expect.get("preservesQuotes"))) {
            equal(quotesBefore, read("/quotes"), id + " preserves the entire quote collection");
            record.put("preservesQuotes", true);
        }
        return record;
    }

    private static List<String> eventKinds(List<?> events) {
        return events.stream().map(value -> obj(value).get("kind"))
                .filter(Objects::nonNull).map(Object::toString).toList();
    }

    private void check(Map<String, Object> expect, String key, String path, Map<String, Object> record) {
        if (expect.containsKey(key)) {
            var actual = read(path);
            equal(String.valueOf(expect.get(key)), String.valueOf(actual), path);
            record.put(key, actual);
        }
    }

    private Object read(String path) {
        return processor.read(document, path);
    }

    private static List<String> strings(Object value) {
        return list(value).stream().map(String::valueOf).toList();
    }

    private static String sha256(Path file) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));
    }

    private static void equal(Object expected, Object actual, String context) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(context + " expected " + expected + ", got " + actual);
        }
    }

    private static Map<String, Object> map(Object... pairs) {
        var result = new LinkedHashMap<String, Object>();
        for (int i = 0; i < pairs.length; i += 2) result.put((String) pairs[i], pairs[i + 1]);
        return result;
    }
}
