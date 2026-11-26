import blue.bex.BexError;
import blue.bex.Values;
import blue.contracts.ClauseGasProbe;
import blue.contracts.ContractException;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Native negotiation, agreement-local catalogue amendments and private quote snapshots. */
public final class BaseCommerceConformance {
    private final Contracts processor;
    private Contracts.Document document;
    private long time = 1;

    private BaseCommerceConformance(Contracts processor, Integer minimum) {
        this.processor = processor;
        var source = agreement(minimum);
        Contracts.Result initialized;
        try {
            initialized = processor.initialize(source);
            if (!"APPLIED".equals(initialized.status())) ClauseGasProbe.diagnose(processor, source);
        } catch (ContractException e) {
            throw new AssertionError(e.code() + " " + e.diagnosticPath() + " " + e.context(), e);
        }
        equal("APPLIED", initialized.status(), "Initialize agreement: " + initialized.observations());
        document = initialized.document();
    }

    public static void main(String[] args) throws Exception {
        var root = Path.of(args[0]);
        var selection = root.resolve("PACKAGES.json");
        var mounts = record(record(CompositionPackages.yaml(selection)).get("mounts"));
        mounts.keySet().removeAll(List.of("Reseller", "CancellationTiming"));
        equal(false, mounts.containsKey("Sales"), "No Sales package");
        var fixtureSelection = Files.createTempFile("declarative-commerce-", ".json");
        try {
            Files.writeString(fixtureSelection, WireData.write(map("mounts", mounts)));
            qualify(CompositionPackages.published(root, fixtureSelection));
        } finally {
            Files.deleteIfExists(fixtureSelection);
        }
        System.out.println("PASS stock activation, separate bilateral amendments and private quote history");
    }

    private static void qualify(CompositionPackages packages) throws Exception {
        try (var language = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
            var processor = runtime.processor(language);
            var agreement = new BaseCommerceConformance(processor, 275);
            agreement.negotiate(275, 625);
            agreement.amendAndQuote();
            var noFloor = new BaseCommerceConformance(processor, null);
            noFloor.activateDefault();
            noFloor.reject("seller", "proposeCommissionSeller",
                    amendment("increased", 1, "/terms/commissionBps", 426), "INVALID_AMENDMENT_REPLACEMENT");
            noFloor.apply("seller", "proposeCommissionSeller",
                    amendment("zeroChain", 1, "/terms/commissionBps", 0));
            noFloor.apply("seller", "approveCommissionSeller", approval("zeroChain"));
            noFloor.reject("partner", "approveCommissionPartner", approval("zeroChain"), "INVALID_AMENDMENT_REPLACEMENT");
            noFloor.number(425, "/terms/commissionBps");
            noFloor.number(1, "/commissionAmendments/revision");
            var zeroProposal = noFloor.apply("seller", "proposeCommissionSeller",
                    amendment("zero", 1, "/terms/commissionBps", 0));
            noFloor.number(425, "/terms/commissionBps");
            equal(false, noFloor.emittedKind(zeroProposal, "Validator Effect"),
                    "A validator cannot publish its staged event");
            noFloor.apply("seller", "approveCommissionSeller", approval("zero"));
            noFloor.apply("partner", "approveCommissionPartner", approval("zero"));
            equal("queued", noFloor.read("/commissionAmendments/proposal/id"), "Approval can queue a valid next proposal");
            noFloor.number(424, "/commissionAmendments/proposal/replacement");
            noFloor.apply("seller", "quoteSeller", quote("zero", 1));
            noFloor.snapshot("zero", 2, 0);
        }
    }

    private void negotiate(Integer minimum, int rate) {
        equal(false, read("/activation/active"), "Negotiation starts inactive");
        equal(Values.UNDEFINED, read("/terms/commissionBps"), "The operational rate starts unset");
        reject("seller", "proposeCatalogSeller", amendment("tooEarly", 1, "/products", catalog(2, "EUR", 900)), "TERMS_FROZEN");
        reject("seller", "proposeCommissionSeller",
                amendment("tooEarly", 1, "/terms/commissionBps", 700), "TERMS_FROZEN");
        reject("seller", "proposeChanges_seller", negotiation("badRate", "/terms/initialCommissionBps", 10001), null);
        reject("seller", "proposeChanges_seller", negotiation("wrongScope", "/terms/currency", "USD"), null);
        if (minimum != null) {
            reject("seller", "proposeChanges_seller", negotiation("belowFloor", "/terms/initialCommissionBps", minimum - 1), null);
        }
        var proposal = negotiation("initial", "/terms/initialCommissionBps", rate);
        record(proposal.get("changes")).put("items", List.of(
                change("/terms/initialCommissionBps", rate), change("/terms/exclusive", true)));
        apply("seller", "proposeChanges_seller", proposal);
        var selection = map("type", "Activation/Terms Selection Input", "proposalId", "initial",
                "termsRef", read("/activation/negotiation/proposal/termsRef"));
        apply("seller", "activate_seller", selection);
        equal(false, read("/activation/active"), "One acceptance keeps the agreement inactive");
        equal(Values.UNDEFINED, read("/terms/commissionBps"), "The first acceptance does not seed the rate");
        apply("partner", "activate_partner", selection);
        equal(true, read("/activation/active"), "Both parties activate the agreement");
        number(rate, "/terms/initialCommissionBps");
        number(rate, "/terms/commissionBps");
        equal(true, read("/terms/exclusive"), "The parties can agree exclusivity");
        reject("seller", "proposeChanges_seller", negotiation("afterActivation", "/terms/exclusive", false), null);
    }

    private void activateDefault() {
        equal(Values.UNDEFINED, read("/terms/commissionBps"), "Current rate starts unset");
        var selection = map("type", "Activation/Terms Selection Input", "termsRef", read("/activation/terms/ref"));
        apply("seller", "activate_seller", selection);
        apply("partner", "activate_partner", selection);
        equal(true, read("/activation/active"), "Both parties can accept the unmodified terms");
        number(425, "/terms/commissionBps");
        apply("partner", "quotePartner", quote("defaultRate", 1));
        snapshot("defaultRate", 1, 425);
    }

    private void amendAndQuote() {
        apply("partner", "quotePartner", quote("before", 1));
        Object original = read("/quotes/before");
        Object acceptedTerms = read("/activation/terms");
        number(777, "/quotes/before/totalMinor");
        snapshot("before", 1, 625);

        var aborted = apply("seller", "proposeCatalogSeller",
                amendment("abortEarly", 1, "/products", catalog(2, "USD", 900)));
        number(625, "/terms/commissionBps");
        equal(List.of(), processor.emitted(aborted), "Callback's explicit empty effects are preserved");

        var wrongSupplier = catalog(2, "EUR", 900);
        wrongSupplier.put("supplierId", "other");
        reject("seller", "proposeCatalogSeller", amendment("wrongSupplier", 1, "/products", wrongSupplier),
                "CATALOG_SUPPLIER_AND_CURRENCY_FIXED");
        reject("seller", "proposeCatalogSeller", amendment("wrongCurrency", 1, "/products", catalog(2, "USD", 900)),
                "CATALOG_SUPPLIER_AND_CURRENCY_FIXED");
        reject("seller", "proposeCatalogSeller", amendment("wrongRevision", 1, "/products", catalog(3, "EUR", 900)),
                "STALE_CATALOG_REVISION");
        reject("seller", "proposeCatalogSeller", amendment("invalidProduct", 1, "/products", catalog(2, "EUR", -10)), null);
        reject("seller", "proposeCatalogSeller", amendment("wrongPath", 1, "/terms", catalog(2, "EUR", 900)),
                "FIELD_NOT_AMENDABLE");

        var competing = amendment("competing", 1, "/products", catalog(2, "EUR", 980));
        apply("seller", "proposeCompetingSeller", competing);
        var proposed = amendment("update", 1, "/products", catalog(2, "EUR", 1350));
        apply("seller", "proposeCatalogSeller", proposed);
        var reviewedVersion = document.blueId();
        apply("seller", "proposeCatalogSeller", amendment("different", 1, "/products", catalog(2, "EUR", 950)));
        apply("seller", "proposeCatalogSeller", proposed);
        rejected(invoke("partner", "approveCatalogPartner", approval("update"), reviewedVersion, true), "Delayed review");
        reject("partner", "approveCatalogPartner", approval("update"), false, "EXACT_REVIEW_REQUIRED");
        apply("seller", "approveCatalogSeller", approval("update"));
        number(1, "/products/revision");
        apply("partner", "approveCatalogPartner", approval("update"));
        number(2, "/products/revision");
        number(2, "/catalogAmendments/revision");
        equal(List.of(), processor.emitted(apply("seller", "proposeCompetingSeller", competing)),
                "Duplicating a stale proposal does not run the validator");
        var partial = apply("seller", "approveCompetingSeller", approval("competing"));
        equal(true, emittedKind(partial, "Amendment Applied"),
                "An authored callback may emit the same notification without finalizing the proposal");
        number(1, "/competingAmendments/revision");
        equal(List.of(), processor.emitted(apply("seller", "approveCompetingSeller", approval("competing"))),
                "Repeating a nonfinal approval does not run the validator");
        reject("partner", "approveCompetingPartner", approval("competing"), "STALE_CATALOG_REVISION");
        number(1, "/competingAmendments/revision");
        reject("seller", "proposeCatalogSeller", amendment("staleRequest", 1, "/products", catalog(3, "EUR", 900)),
                "STALE_REVISION");
        number(1, "/commissionAmendments/revision");

        reject("seller", "proposeCommissionSeller", amendment("badRate", 1, "/terms/commissionBps", 10001),
                null);
        reject("partner", "proposeCommissionPartner", amendment("belowFloor", 1, "/terms/commissionBps", 274),
                null);
        reject("partner", "proposeCommissionPartner",
                amendment("objectRate", 1, "/terms/commissionBps", map("commissionBps", 800, "privateData", "unreviewed")),
                "INVALID_AMENDMENT_REPLACEMENT");
        reject("partner", "proposeCommissionPartner",
                amendment("textRate", 1, "/terms/commissionBps", map("type", "Text", "value", "800")),
                "INVALID_AMENDMENT_REPLACEMENT");
        reject("partner", "proposeCommissionPartner", amendment("fractionalRate", 1, "/terms/commissionBps", 800.5),
                "INVALID_AMENDMENT_REPLACEMENT");
        reject("partner", "proposeCommissionPartner", amendment("badRevision", 2, "/terms/commissionBps", 800),
                "STALE_REVISION");
        apply("seller", "quoteSeller", quote("newPrice", 2));
        number(1350, "/quotes/newPrice/totalMinor");
        snapshot("newPrice", 1, 625);
        var rateChange = amendment("newRate", 1, "/terms/commissionBps", 850);
        apply("seller", "proposeCommissionSeller", amendment("sellerProposal", 1, "/terms/commissionBps", 775));
        apply("partner", "proposeCommissionPartner", rateChange);
        equal(List.of(), processor.emitted(apply("partner", "proposeCommissionPartner", rateChange)), "Proposal replay");
        number(1, "/commissionAmendments/revision");
        number(625, "/terms/commissionBps");
        apply("partner", "approveCommissionPartner", approval("newRate"));
        number(1, "/commissionAmendments/revision");
        number(625, "/terms/commissionBps");
        apply("seller", "approveCommissionSeller", approval("newRate"));
        equal(List.of(), processor.emitted(apply("seller", "approveCommissionSeller", approval("newRate"))), "Approval replay");
        number(2, "/commissionAmendments/revision");
        number(850, "/terms/commissionBps");
        equal(acceptedTerms, read("/activation/terms"), "An amendment preserves the historical acceptance");
        number(625, "/terms/initialCommissionBps");
        equal(true, read("/terms/exclusive"), "The rate amendment preserves exclusivity");
        equal(Values.UNDEFINED, read("/commissionTerms"), "No duplicate current rate state is needed");

        equal(List.of(), processor.emitted(apply("seller", "quoteSeller", quote("before", 1))), "Cross-route quote replay");
        equal(original, read("/quotes/before"), "Replaying a quote preserves its price");
        snapshot("before", 1, 625);
        reject("seller", "quoteSeller", quote("before", 2), "QUOTE_KEY_CONFLICT");
        reject("partner", "quotePartner", quote("newOnWrongRevision", 1), "STALE_CATALOG_REVISION");
        apply("seller", "quoteSeller", quote("sellerRate", 2));
        snapshot("sellerRate", 2, 850);
        apply("partner", "quotePartner", quote("partnerRate", 2));
        snapshot("partnerRate", 2, 850);
        apply("seller", "announceQuote", map());
        equal(Values.UNDEFINED, read("/quoteCommissionTerms/announced"), "An application event cannot simulate a native insert");
        reject("seller", "quoteSeller", quote("rollback", 2), "QUOTE_SNAPSHOT_ALREADY_EXISTS");
        equal(Values.UNDEFINED, read("/quotes/rollback"), "A failed snapshot write rolls back the quote");
        number(641, "/quoteCommissionTerms/rollback/commissionBps");
        apply("seller", "otherQuoteSeller", quote("differentCollection", 2));
        equal(Values.UNDEFINED, read("/quoteCommissionTerms/differentCollection"), "The other catalogue uses its own quote collection");
        apply("seller", "proposeCommissionSeller", amendment("anotherRate", 2, "/terms/commissionBps", 950));
        apply("seller", "approveCommissionSeller", approval("anotherRate"));
        apply("partner", "approveCommissionPartner", approval("anotherRate"));
        equal(List.of(), processor.emitted(apply("seller", "approveCommissionSeller", approval("newRate"))),
                "Historic approval replay emits no effects after another revision");
        number(3, "/commissionAmendments/revision");
        number(950, "/terms/commissionBps");
        snapshot("sellerRate", 2, 850);
        restoreAccess();
    }

    private void restoreAccess() {
        var restored = apply("seller", "modelAccessRecovery", map());
        equal(true, read("/activation/active"), "Stock activation refresh restored the agreement");
        equal(true, emittedType(restored, "Parties/Document Access Restored"), "Stock refresh emitted access restored");
        equal(false, emittedType(restored, "Parties/Document Activated"), "Restoration is distinct from first activation");
        number(950, "/terms/commissionBps");
        apply("partner", "quotePartner", quote("restored", 2));
        snapshot("restored", 3, 950);
    }

    private boolean emittedType(Contracts.Result result, String type) {
        var values = processor.execution().values();
        var pattern = values.source(map("type", type), "definition");
        return ClauseGasProbe.eventData(processor, result).stream().anyMatch(event -> values.matches(event, pattern));
    }

    private boolean emittedKind(Contracts.Result result, String kind) {
        var values = processor.execution().values();
        var pattern = values.source(map("type", "Commerce/Domain Event", "kind", kind), "definition");
        return ClauseGasProbe.eventData(processor, result).stream().anyMatch(event -> values.matches(event, pattern));
    }

    private void snapshot(String key, int revision, int rate) {
        number(revision, "/quoteCommissionTerms/" + key + "/revision");
        number(rate, "/quoteCommissionTerms/" + key + "/commissionBps");
        equal(Values.UNDEFINED, read("/quotes/" + key + "/commissionBps"), "No commission rate in the public quote");
        equal(Values.UNDEFINED, read("/quotes/" + key + "/commissionTerms"), "No private terms in the public quote");
    }

    private Contracts.Result apply(String party, String operation, Object request) {
        var result = invoke(party, operation, request, document.blueId(), true);
        equal("APPLIED", result.status(), operation + ": " + result.observations());
        document = result.document();
        return result;
    }

    private void reject(String party, String operation, Object request, String message) {
        reject(party, operation, request, true, message);
    }

    private void reject(String party, String operation, Object request, boolean exact, String message) {
        var input = operationInput(party, operation, request, document.blueId(), exact);
        var result = processor.process(document, input, time);
        rejected(result, operation);
        if (message != null) {
            try {
                ClauseGasProbe.diagnose(processor, document, input, time);
                throw new AssertionError("Expected authored rejection " + message + ": " + result.observations());
            } catch (BexError rejection) {
                equal(message, rejection.getMessage(), operation);
            }
        }
        time++;
    }

    private void rejected(Contracts.Result result, String operation) {
        if ("APPLIED".equals(result.status())) {
            // A native request matcher can skip an invalid command while processing its envelope.
            for (var path : List.of("/terms", "/activation", "/products", "/quotes", "/quoteCommissionTerms",
                    "/commissionAmendments", "/catalogAmendments", "/competingAmendments")) {
                equal(read(path), processor.read(result.document(), path), operation + " must preserve " + path);
            }
        } else {
            equal(document.blueId(), result.document().blueId(), operation + " preserves exact state");
        }
        equal(List.of(), processor.emitted(result), operation + " emits no business effects");
    }

    private Contracts.Result invoke(String party, String operation, Object request, String version, boolean exact) {
        return processor.process(document, operationInput(party, operation, request, version, exact), time++);
    }

    private static Map<String, Object> operationInput(String party, String operation, Object request,
                                                        String version, boolean exact) {
        return map("source", party, "operation", map("type", "Contracts/Operation Request",
                "document", map("blueId", version), "channel", party, "operation", operation,
                "request", request, "requireExactDocumentVersion", exact));
    }

    private static Map<String, Object> agreement(Integer minimum) {
        var parties = map();
        var channels = map();
        for (var role : List.of("seller", "partner")) {
            var channel = map("type", "Contracts/External Channel", "event", map("source", role));
            channels.put(role, channel);
            parties.put(role, map("type", "Parties/Party", "lead", map("channel", channel),
                    "readerKeys", List.of("reader-" + role), "myosAccountId", role + "-account"));
        }
        var activation = map("type", "Activation/Activation Clause", "parameters",
                map("parties", parties, "required", List.of("seller", "partner"),
                        "preActivationChannels", List.of("cx.catalog.validate._automatic_source",
                                "cx.otherCatalog.validate._automatic_source"),
                        "preActivationOperations", List.of("proposeCatalogSeller", "proposeCommissionSeller"),
                        "negotiation", map("allowedPaths", List.of("/terms/initialCommissionBps", "/terms/exclusive"))));
        var terms = map("type", map("initialCommissionBps", rateSchema(minimum), "exclusive", map("type", "Boolean"),
                "currency", map("type", "Text")), "initialCommissionBps", 425, "exclusive", false, "currency", "EUR");
        var catalogValidator = replacementValidator("Commerce/Catalog Functions", "validateCatalogReplacement");
        var rateValidator = minimum == null ? rateValidator() : null;
        String rateSchemaPath = "/terms/type/initialCommissionBps";
        return map("name", "Rental agreement", "type", "Agreements/Agreement with Clauses", "contracts", channels,
                "terms", terms, "products", catalog(1, "EUR", 777), "quotes", map(), "otherQuotes", map(),
                "quoteCommissionTerms", map("rollback", map("revision", 1, "commissionBps", 641)),
                "clauses", map("activation", activation,
                        "catalog", catalogue("/quotes", map("quoteSeller", workflow("seller"), "quotePartner", workflow("partner")), true),
                        "otherCatalog", catalogue("/otherQuotes", map("otherQuoteSeller", workflow("seller")), false),
                        "catalogAmendments", amendments("Catalog", "/catalogAmendments", "/products", catalogValidator, null),
                        "competingAmendments", amendments("Competing", "/competingAmendments", "/products", catalogValidator, null),
                        "commissionAmendments", amendments("Commission", "/commissionAmendments", "/terms/commissionBps",
                                rateValidator, rateSchemaPath),
                        "activateRate", activationRateFeature(), "accessProbe", restorationProbe()));
    }

    private static Map<String, Object> rateSchema(Integer minimum) {
        var schema = map("maximum", 10000);
        schema.put("minimum", minimum == null ? 0 : minimum);
        return map("type", "Integer", "schema", schema);
    }

    private static Map<String, Object> catalogue(String quotes, Object operations, boolean privateSnapshot) {
        var bindings = map("state", "/products", "quotes", quotes, "quote", operations);
        var clause = map("type", "Commerce/Catalog Clause", "bindings", bindings);
        if (privateSnapshot) {
            bindings.put("quoteSnapshots", "/quoteCommissionTerms");
            clause.put("parameters", map("quoteSnapshot", map("revision", "/commissionAmendments/revision",
                    "commissionBps", "/terms/commissionBps")));
        }
        return clause;
    }

    private static Map<String, Object> replacementValidator(Object definition, String function) {
        return map("definition", map("type", definition), "function", function);
    }

    private static Map<String, Object> rateValidator() {
        var input = map("current", map("type", "Integer"), "replacement", map("type", "Integer"));
        var comparison = map("args", input,
                "expr", map("$lte", List.of(map("$var", "replacement"), map("$var", "current"))));
        var validator = map("args", input, "do", List.of(
                map("$appendChange", map("op", "replace", "path", "/terms/commissionBps", "val", 9999)),
                map("$appendEvent", map("type", "Commerce/Domain Event", "kind", "Validator Effect")),
                map("$return", map("$and", List.of(map("$const", "once"),
                        map("$const", map("name", "bindings", "path", "/enabled")),
                        map("$call", map("function", "initialize",
                                "args", map("current", map("$var", "current"), "replacement", map("$var", "replacement")))))))));
        return replacementValidator(map("type", "Contracts/Compute Definition",
                "constants", map("once", true, "bindings", map("enabled", true)),
                "functions", map("doesNotIncrease", validator, "initialize", comparison)), "doesNotIncrease");
    }

    private static Map<String, Object> amendments(String label, String state, String path, Object validator,
                                                     String schemaPath) {
        var parameters = map("paths", List.of(path), "approvers", List.of("seller", "partner"));
        if (schemaPath != null) parameters.put("replacementSchema", map("path", schemaPath, "kind", "integer"));
        if (validator != null) parameters.put("replacementValidator", validator);
        Object type = "Amendments/Amendments Clause";
        var sellerProposal = workflow("seller");
        if ("Catalog".equals(label)) {
            var helpers = map("evaluateAmendmentAction", map("args", map(), "expr", true));
            type = map("type", type, "actionDefinition",
                    map("type", map("type", "Amendments/Amendments Functions", "functions", helpers)));
            sellerProposal.put("before", List.of(
                    map("$call", map("function", "evaluateAmendmentAction", "args", map())),
                    map("$if", map(
                            "cond", map("$eq", List.of(var("params", "/proposalId"), "abortEarly")),
                            "then", List.of(
                                    map("$appendChange", map("op", "replace", "path", "/terms/commissionBps", "val", 9999)),
                                    map("$appendEvent", map("type", "Commerce/Domain Event", "kind", "Aborted Callback")),
                                    map("$return", map("changeset", List.of(), "events", List.of())))))));
        }
        var sellerApproval = exactWorkflow("seller");
        var partnerApproval = exactWorkflow("partner");
        if ("Competing".equals(label)) {
            sellerApproval.put("after", List.of(map("$appendEvent", map("type", "Commerce/Domain Event",
                    "kind", "Amendment Applied", "clause", "competingAmendments",
                    "proposalId", var("params", "/proposalId")))));
            partnerApproval.put("after", List.of(queueNextProposal("competing", state, path, catalog(3, "EUR", 910))));
        }
        if ("Commission".equals(label) && validator != null) {
            partnerApproval.put("after", List.of(
                    queueNextProposal("zeroChain", state, path, 426),
                    queueNextProposal("zero", state, path, 424)));
        }
        return map("type", type, "parameters", parameters,
                "bindings", map("state", state, "editable", "/activation/everActivated",
                        "propose", map("propose" + label + "Seller", sellerProposal,
                                "propose" + label + "Partner", workflow("partner")),
                        "approve", map("approve" + label + "Seller", sellerApproval,
                                "approve" + label + "Partner", partnerApproval)));
    }

    private static Object queueNextProposal(String previousId, String state, String path, Object replacement) {
        var input = map("proposalId", "queued", "path", path, "replacement", replacement,
                "expectedRevision", map("$resultValue", state + "/revision"));
        var arguments = map("input", input, "state", map("$resultValue", state), "parameters", map("$const", "parameters"),
                "bindings", map("$const", "bindings"), "clauseKey", map("$const", "clauseKey"));
        return map("$if", map("cond", map("$eq", List.of(var("params", "/proposalId"), previousId)),
                "then", List.of(map("$call", map("function", "recordAmendmentProposal", "args", arguments)))));
    }

    private static Map<String, Object> activationRateFeature() {
        var type = map("type", "Contracts/Document Update");
        var insert = map("op", "add", "beforePresent", false, "afterPresent", true);
        var fabricatedUpdate = map("$merge", List.of(type, insert, map(
                "path", "/quotes/announced", "after", map("intent", map("key", "announced")))));
        var announce = map("do", List.of(map("$appendEvent", fabricatedUpdate)));
        var initializeRate = map("do", List.of(map("$appendChange", map("op", "add",
                "path", "/terms/commissionBps", "val", map("$document", "/terms/initialCommissionBps")))));
        return map("type", "Features/Feature Clause",
                "parameters", map("actions", map("announce", announce, "initializeRate", initializeRate)),
                "bindings", map("announce", map("announceQuote", workflow("seller")),
                        "initializeRate", map("firstActivation", map("on", "activated", "once", true))));
    }

    /** Supply the post-revocation state, then run the stock refresh in the same native transaction. */
    private static Map<String, Object> restorationProbe() {
        var recover = map("do", List.of(
                map("$appendChange", map("op", "replace", "path", "/activation/active", "val", false)),
                map("$appendChange", map("op", "replace", "path", "/activation/accessReady", "val", false)),
                map("$appendChange", map("op", "replace", "path", "/activation/status", "val", "SUSPENDED_ACCESS")),
                map("$appendEvent", map("$merge", List.of(map("type", "Clauses/Clauses Initialized"))))));
        return map("type", "Features/Feature Clause",
                "parameters", map("actions", map("recover", recover)),
                "bindings", map("recover", map("modelAccessRecovery", workflow("seller"))));
    }

    private static Map<String, Object> workflow(String party) {
        return map("on", "workflow", "party", party, "params", map("$object", var("trigger", "")));
    }

    private static Map<String, Object> exactWorkflow(String party) {
        var binding = workflow(party);
        binding.put("requireExactDocumentVersion", true);
        return binding;
    }

    private static Map<String, Object> quote(String key, int revision) {
        return map("key", key, "catalogRevision", revision, "lines", List.of(map("itemId", "rental", "quantity", 1)));
    }

    private static Map<String, Object> catalog(int revision, String currency, int price) {
        return map("revision", revision, "supplierId", "seller", "currency", currency, "entries",
                map("rental", map("label", "Bike rental", "pricingUnit", "per_unit", "dateRequired", false,
                        "unitAmountMinor", price)));
    }

    private Map<String, Object> negotiation(String proposalId, String path, Object value) {
        return map("type", "Activation/Terms Proposal Input", "proposalId", proposalId,
                "baseTermsRef", read("/activation/terms/ref"),
                "changes", map("type", "List", "itemType", "Activation/Term Change", "items", List.of(change(path, value))));
    }

    private static Map<String, Object> change(String path, Object replacement) {
        return map("type", "Activation/Term Change", "path", path, "replacement", replacement);
    }

    private static Map<String, Object> amendment(String proposalId, int expectedRevision, String path, Object value) {
        return map("type", "Amendments/Amendment Input", "proposalId", proposalId, "expectedRevision", expectedRevision,
                "path", path, "replacement", value);
    }

    private static Map<String, Object> approval(String proposalId) {
        return map("proposalId", proposalId);
    }

    private Object read(String path) {
        return processor.read(document, path);
    }

    private void number(int expected, String path) {
        equal(Integer.toString(expected), String.valueOf(read(path)), path);
    }

    private static Map<String, Object> var(String name, String path) {
        return map("$var", path.isEmpty() ? name : map("name", name, "path", path));
    }

    private static Map<String, Object> map(Object... entries) {
        var result = new LinkedHashMap<String, Object>();
        for (int index = 0; index < entries.length; index += 2) {
            result.put((String) entries[index], entries[index + 1]);
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> record(Object value) {
        return (Map<String, Object>) value;
    }

    private static void equal(Object expected, Object actual, String context) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(context + ": expected " + expected + ", got " + actual);
        }
    }
}
