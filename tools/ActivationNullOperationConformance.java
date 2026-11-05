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
        boolean consent = args.length > 2 && args[2].equals("consent");
        var input = consent ? capture : object(capture.get("input"));
        var content = object(input.get(consent ? "responses" : "content"));
        String publication;
        Map<String, Object> consentOperation = Map.of();
        if (consent) {
            publication = (String) capture.get("publication");
            consentOperation = ((List<?>) object(capture.get("description")).get("operations")).stream()
                    .map(ActivationNullOperationConformance::object)
                    .filter(operation -> operation.get("name").toString().startsWith("consentAdmission_payment_"))
                    .findFirst().orElseThrow();
        } else {
            var documents = (List<?>) object(input.get("snapshot")).get("documents");
            publication = documents.stream().map(ActivationNullOperationConformance::object)
                    .filter(document -> Objects.equals(document.get("key"), capture.get("targetMember")))
                    .map(document -> (String) document.get("blueId")).findFirst().orElseThrow();
        }
        try (var blue = Blue.builder().nodeProvider(id -> content.containsKey(id)
                ? NodeProviderResult.found(ContentRecord.fromResponse(object(content.get(id))))
                : NodeProviderResult.notFound()).build()) {
            var processor = new Contracts(blue, RuntimeBindings.accessEvents().withDefinitionReadV1());
            var execution = processor.execution();
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
            for (String scenario : consent ? List.of("consent", "wrongConsentChannel", "unknownNamed")
                    : List.of("seller", "seller__myosAgent", "missingOperation", "unknownNamed")) {
                var dispatch = new LinkedHashMap<String, Object>();
                dispatch.put("kind", "EXTERNAL");
                dispatch.put("channel", scenario.equals("consent") ? consentOperation.get("channel")
                        : scenario.equals("unknownNamed") || scenario.equals("wrongConsentChannel") ? "seller" : scenario);
                dispatch.put("operation", scenario.equals("consent") || scenario.equals("wrongConsentChannel")
                        ? consentOperation.get("name") : scenario.equals("seller") ? "preparePayment"
                        : scenario.equals("unknownNamed") ? "unregisteredOperation" : null);
                if (scenario.equals("missingOperation")) dispatch.remove("operation");
                // DocumentDispatchV1 installs this raw map. Native source conversion erases
                // explicit null and would miss the non-target Agent delivery regression.
                var result = RawDispatchEvaluation.evaluate(processor, host, dispatch, body, 10_000_000);
                System.out.println(scenario + " result=" + WireData.write(result.value()));
                if (!result.changeset().isEmpty() || !result.events().isEmpty()) {
                    throw new AssertionError("Dispatch policy produced effects: " + scenario);
                }
                boolean allowed = scenario.equals("seller") || scenario.equals("consent");
                if (!allowed
                        && !"DOCUMENT_NOT_ACTIVE".equals(object(result.value()).get("reason"))) {
                    throw new AssertionError("Unexpected denial reason: " + scenario);
                }
                if (!Objects.equals(allowed, object(result.value()).get("allowed"))) {
                    throw new AssertionError("Unexpected activation authorization: " + scenario);
                }
            }
        }
    }
}
