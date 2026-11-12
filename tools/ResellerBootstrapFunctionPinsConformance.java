import blue.contracts.*;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Validates copied Reseller preparation pins against the current native Documents definition. */
public final class ResellerBootstrapFunctionPinsConformance {
    @SuppressWarnings("unchecked")
    private static Map<String, Object> object(Object value) { return (Map<String, Object>) value; }

    public static void main(String[] args) throws Exception {
        Path root = Path.of(args[0]);
        var documents = BluePackage.open(root.resolve("clause-documents/dist/package.bluepkg"));
        var composition = object(WireData.json(Files.readString(root.resolve("clause-reseller/bootstrap-composition.json"))));
        var authored = object(WireData.parse(Files.readString(root.resolve("clause-reseller/types/customer-orders-bootstrap-clause.blue")), "yaml"));
        var copied = object(object(object(authored.get("actionDefinition")).get("type")).get("functions"));
        var errors = new ArrayList<String>();
        // checkProvision and its exact Admission Plan function execute these sibling functions.
        for (String name : List.of("providedInitialTerms", "providedAdmissionPlan", "providedAdmissionProof",
                "validateProviderSlotsWithAdmission", "validateBootstrapAccessWithAdmission",
                "assembleAdmissionPlan", "assembleAdmissionDefinition")) {
            if (!object(composition.get("functions")).containsKey(name)) errors.add("missing/composition/" + name);
            if (!copied.containsKey(name)) errors.add("missing/actionDefinition/" + name);
        }
        try (var blue = Blue.builder().packages(PackageBundle.builder().mount("Documents", documents).build()).build()) {
            var values = new Contracts(blue, RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
            var definition = new Exact.Ref(documents.exportId("Document Preparation Functions"));
            var metadata = object(WireData.json(Files.readString(root.resolve("clause-documents/dist/package.json"))));
            if (!definition.id().equals(composition.get("sourceDefinition"))) errors.add("sourceDefinition");
            if (!metadata.get("packageBlueId").equals(composition.get("sourcePackageId"))) errors.add("sourcePackageId");
            // The separate quote-based bootstrap profile owns this unchanged helper
            // after main's Customer Orders adopts catalogRevision/lines semantics.
            String bookingId = NativeRuntime.identity(values.source(copied.get("prepareBooking")));
            String expectedBooking = object(object(composition.get("domainFunctionReferences")).get("prepareBooking")).get("blueId").toString();
            if (!bookingId.equals(expectedBooking)) errors.add("domainFunction/prepareBooking");
            for (var entry : object(composition.get("functions")).entrySet()) {
                String name = entry.getKey();
                String expected = NativeRuntime.identity(values.exact(values.select(definition, "/functions/" + name)));
                if (!Map.of("blueId", expected).equals(entry.getValue())) errors.add("composition/" + name);
                if (!Map.of("blueId", expected).equals(copied.get(name))) errors.add("actionDefinition/" + name);
            }
        }
        if (!errors.isEmpty()) throw new AssertionError("Stale native function pins: " + errors);
        System.out.println("PASS all " + object(composition.get("functions")).size() + " native function pins and definition/package provenance");
    }
}
