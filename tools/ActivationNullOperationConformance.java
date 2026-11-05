import blue.contracts.*;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Replays the retained Agent dispatch policy without bootstrap or admission bypass. */
public final class ActivationNullOperationConformance {
    @SuppressWarnings("unchecked")
    private static Map<String, Object> object(Object value) {
        return (Map<String, Object>) value;
    }

    private static void calls(Object value, Set<String> names) {
        if (value instanceof Map<?, ?> map) {
            if (map.get("$call") instanceof Map<?, ?> call
                    && call.get("function") instanceof String name) names.add(name);
            map.forEach((key, child) -> {
                if (!key.equals("$literal")) calls(child, names);
            });
        } else if (value instanceof List<?> list) {
            list.forEach(child -> calls(child, names));
        }
    }

    public static void main(String[] args) throws Exception {
        Path root = Path.of(args[0]);
        var capture = object(WireData.json(Files.readString(Path.of(args[1]))));
        var input = object(capture.get("input"));
        var content = object(input.get("content"));
        var documents = (List<?>) object(input.get("snapshot")).get("documents");
        String publication = documents.stream().map(ActivationNullOperationConformance::object)
                .filter(document -> Objects.equals(document.get("key"), capture.get("targetMember")))
                .map(document -> (String) document.get("blueId")).findFirst().orElseThrow();
        try (var blue = Blue.builder().nodeProvider(id -> content.containsKey(id)
                ? NodeProviderResult.found(ContentRecord.fromResponse(object(content.get(id))))
                : NodeProviderResult.notFound()).build()) {
            var execution = new Contracts(blue,
                    RuntimeBindings.accessEvents().withDefinitionReadV1()).execution();
            var values = execution.values();
            var host = new Exact.Ref(publication);
            String path = "/contracts/activationDispatch";
            var body = object(values.bexData(values.select(host, path)));
            var functions = new LinkedHashMap<String, Object>();
            var pending = new LinkedHashSet<String>();
            calls(body.get("do"), pending);
            while (!pending.isEmpty()) {
                String name = pending.iterator().next();
                pending.remove(name);
                if (functions.containsKey(name)) continue;
                Object function = values.bexData(values.select(host, path + "/definition/functions/" + name));
                functions.put(name, function);
                calls(function, pending);
            }
            // Optional retained mode diagnoses the actual emitted policy before source changes.
            if (args.length < 3 || !args[2].equals("retained")) {
                var authored = AdmissionConsentDispatchConformance.policySource(WireData.parse(
                        Files.readString(root.resolve("clause-activation/types/plan.blue")), "yaml"));
                body.put("do", object(authored.get("do")).get("$literal"));
            }
            body.remove("type");
            body.remove("definition");
            body.put("functions", functions);
            for (String scenario : List.of("seller", "seller__myosAgent", "unknownNamed")) {
                var dispatch = new LinkedHashMap<String, Object>();
                dispatch.put("kind", "EXTERNAL");
                dispatch.put("channel", scenario.equals("unknownNamed") ? "seller" : scenario);
                dispatch.put("operation", scenario.equals("seller") ? "preparePayment"
                        : scenario.equals("unknownNamed") ? "unregisteredOperation" : null);
                var result = execution.evaluatePredicate(host, values.source(dispatch), "dispatch",
                        values.source(body), 10_000_000);
                System.out.println(scenario + " result=" + WireData.write(result.value()));
                if (!result.changeset().isEmpty() || !result.events().isEmpty()) {
                    throw new AssertionError("Dispatch policy produced effects: " + scenario);
                }
                if (!scenario.equals("seller")
                        && !"DOCUMENT_NOT_ACTIVE".equals(object(result.value()).get("reason"))) {
                    throw new AssertionError("Unexpected denial reason: " + scenario);
                }
                if (!Objects.equals(scenario.equals("seller"), object(result.value()).get("allowed"))) {
                    throw new AssertionError("Unexpected activation authorization: " + scenario);
                }
            }
        }
    }
}
