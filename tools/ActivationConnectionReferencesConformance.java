import static java.util.List.of;

import blue.bex.BexError;
import blue.bex.Values;
import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.NativeRuntime;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Executes the public Activation and Connections composition in the native runtime. */
public final class ActivationConnectionReferencesConformance {
  private static final String POLICY = "/contracts/activationDispatch/constants";
  private static final String PROBE = "probe";
  private static final String PING = "Connections/Ping";

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]);
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var language = packages.language();
        var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var processor = runtime.processor(language);
      equivalentGrantAndRename(processor);
      observationGrant(processor);
      approvalMetadata(processor);
      stockPlanningHooks(processor);
      customPlannerMapping(processor);
      compositionChanges(processor, false);
      compositionChanges(processor, true);
      installActivation(processor);
      malformedReferences(processor);
    }
  }

  private static void equivalentGrantAndRename(Contracts processor) {
    var formerChannels = of("cx.probe.prime._automatic_source", "cx.probe.watch.ping_source");
    var legacy = initialize(processor, source(PROBE, "watch", "ping", false,
        map("preActivationChannels", formerChannels)));
    var logical = initialize(processor, source(PROBE, "watch", "ping", false,
        map("preActivationConnections", references(PROBE, "watch", "ping"))));
    equal(formerChannels, processor.read(logical, POLICY + "/preChannels"), "Resolved grants");
    for (var document : of(legacy, logical)) {
      effectsBeforeActivation(processor, document);
    }

    var renamed = initialize(processor, source("renamedClause", "renamedAction", "renamedBinding",
        false, map("preActivationConnections", references("renamedClause", "renamedAction", "renamedBinding"))));
    effectsBeforeActivation(processor, renamed);

    var accepting = initialize(processor, source(PROBE, "watch", "ping", false, map(
        "preActivationConnections", references(PROBE, "watch", "ping"),
        "preActivationOperations", of("emitPing", "perform"))));
    var performed = apply(processor, accepting, "perform", map(), 1);
    equal(true, processor.read(performed.document(), "/effects/workflow"),
        "Explicit operation allowance enables the workflow before activation");
    System.out.println("PASS matching legacy and logical grants, renamed author clause/action/binding keys, and separate external operation allowance");
  }

  private static void effectsBeforeActivation(Contracts processor, Contracts.Document document) {
    equal(false, processor.read(document, "/activation/active"), "Activation stays pending");
    equal(true, processor.read(document, "/effects/automatic"), "Automatic initialized action ran");
    var delivered = apply(processor, document, "emitPing", map(), 1).document();
    equal(true, processor.read(delivered, "/effects/named"), "Named event action ran");
    equal(Values.UNDEFINED, processor.read(delivered, "/effects/unlisted"),
        "Unlisted action consuming the same event was blocked");
    var blocked = apply(processor, delivered, "perform", map(), 2);
    equal(Values.UNDEFINED, processor.read(blocked.document(), "/effects/workflow"),
        "A logical workflow reference grants no external operation");
  }

  private static void observationGrant(Contracts processor) {
    var source = source(PROBE, "watch", "ping", false,
        map("preActivationConnections", of(observations(PROBE, "watch"))));
    var probe = fields(fields(source.get("clauses")).get(PROBE));
    var actions = fields(fields(probe.get("parameters")).get("actions"));
    var watch = fields(actions.get("watch"));
    watch.put("automatic", map("on", "initialized"));
    watch.put("do", of(map("$appendChange", map("op", "add", "val", true,
        "path", map("$concat", of("/effects/", map("$const", "connectionKey")))))));
    var defaults = fields(fields(fields(probe.get("type")).get("defaultBindings")).get("watch"));
    defaults.put("afterCapture", map("on", "change", "path", "/effects/capture"));
    defaults.put("performObservation", workflow());
    defaults.put("shared", map("on", "channel", "channel", "seller"));
    defaults.put("timed", map("on", "timer", "timestamp", 10));
    fields(actions.get("emit")).put("do", of(effect("capture"),
        map("$appendEvent", map("type", PING, "text", "ping"))));

    var pending = initialize(processor, source);
    equal(of("cx.probe.watch._automatic_source", "cx.probe.watch.afterCapture_source",
        "cx.probe.watch.ping_source"), processor.read(pending, POLICY + "/preChannels"),
        "Automatic and dedicated internal bindings are the only granted sources");
    installedRoute(processor, pending, "cx.probe.watch.shared", "seller");
    installedRoute(processor, pending, "cx.probe.watch.timed", "cx.probe.watch.timed_source");
    equal(Values.UNDEFINED, processor.read(
        processor.process(pending, map("source", "seller", "case", "shared-before-approval"), 1).document(),
        "/effects/shared"), "Shared external channel stays gated");
    equal(true, processor.read(pending, "/effects/_automatic"), "Automatic observation ran");
    var observed = apply(processor, pending, "emitPing", map(), 2).document();
    equal(false, processor.read(observed, "/activation/active"), "Observation did not approve");
    equal(true, processor.read(observed, "/effects/ping"), "Default event binding ran");
    equal(true, processor.read(observed, "/effects/afterCapture"), "Internal change binding ran");
    equal(Values.UNDEFINED, processor.read(observed, "/effects/unlisted"), "Other action stayed gated");
    var blocked = apply(processor, observed, "performObservation", map(), 3).document();
    equal(Values.UNDEFINED, processor.read(blocked, "/effects/performObservation"),
        "Workflow on the marked action stayed gated");
    var active = apply(processor, blocked, "approve_seller",
        map("revision", processor.read(blocked, "/activation/revision")), 4).document();
    equal(true, processor.read(active, "/activation/active"), "Normal approval activated the document");
    var performed = apply(processor, active, "performObservation", map(), 5).document();
    equal(true, processor.read(performed, "/effects/performObservation"), "Workflow remains usable after consent");
    System.out.println("PASS compact observation grant covers automatic, named internal event and capture-change sources only");
  }

  private static void stockPlanningHooks(Contracts processor) {
    var source = source(PROBE, "watch", "ping", false, map("preActivationConnections",
        of(automatic("reservation", "initialize"), observations("cancellation", "refreshAvailability"))));
    var terms = map("agreementDescription", "Reviewed booking", "fulfilmentText", "Local booking",
        "confirmationMode", "supplier", "dateRequired", true);
    var quote = map("supplierId", "seller", "currency", "USD", "totalMinor", 7200,
        "lines", of(map("itemId", "service", "quantity", 1, "lineTotalMinor", 7200)));
    var group = map("id", "booking-1", "lineIndices", of(0), "proposedStartMicros", 18_000_000_000L);
    source.put("amountMinor", 7200);
    source.put("orderSnapshot", map("quote", quote, "quoteBlueId", identity(processor, quote),
        "terms", terms, "termsBlueId", identity(processor, terms), "groups", of(group)));
    fields(source.get("clauses")).put("reservation", map("type", "Schedule/Reservation Clause",
        "parameters", map(), "bindings", map()));
    fields(source.get("clauses")).put("cancellation", map("type", "Commerce/Whole Order Cancellation Policy",
        "parameters", map("freeCancellationHoursBeforeStart", 1, "lateCancellationChargePercent", 25),
        "bindings", map("amount", "/amountMinor", "decision", "/cancellationDecision",
            "serviceStart", "/orderSnapshot/groups/0/proposedStartMicros", "confirmation", "/activation/approved/seller", "availability", "/cancellationAvailability")));

    var initialized = initialize(processor, source);
    equal(false, processor.read(initialized, "/activation/active"), "Stock composition stays pending");
    var reservation = "cx.reservation.initialize._automatic";
    var cancellation = "cx.cancellation.refreshAvailability._automatic";
    equal(of(reservation + "_source", cancellation + "_source"),
        processor.read(initialized, POLICY + "/preChannels"), "Stock source channels are granted");
    installedRoute(processor, initialized, reservation, reservation + "_source");
    installedRoute(processor, initialized, cancellation, cancellation + "_source");
    require(processor.read(initialized, "/reservations/booking-1") != Values.UNDEFINED,
        "Stock Schedule initialized the booking");
    equal(true, processor.read(initialized, "/cancellationAvailability/beforeConfirmation"),
        "Stock Commerce published pre-confirmation availability");
    System.out.println("PASS stock Schedule and Commerce planning hooks admit their explicitly referenced sources");
  }

  private static void approvalMetadata(Contracts processor) {
    var reviewedEvent = map("type", PING, "clause", "probe", "subject", "order");
    var source = source(PROBE, "watch", "ping", false, map(
        "negotiation", map("allowedPaths", of("/price")),
        "reviewedApprovals", map("seller", map("event", reviewedEvent, "source", "/review", "basis", "/price"))));
    source.put("price", 100);
    var document = initialize(processor, source);
    for (String operation : of("approve_seller", "activate_seller", "proposeAndActivate_seller")) {
      equal("seller", processor.read(document, "/contracts/" + operation + "/steps/0/constants/activationApprovalRole"),
          operation + " carries the installed approval role");
    }
    for (String operation : of("updateParty_seller", "proposeChanges_seller", "withdrawProposal_seller",
        "rejectProposal_seller", "withdrawAcceptance_seller")) {
      equal(Values.UNDEFINED, processor.read(document, "/contracts/" + operation + "/steps/0/constants/activationApprovalRole"),
          operation + " remains independent of the approval guard");
    }
    String reviewChannel = "activation.reviewed.source.seller";
    equal("seller", processor.read(document, POLICY + "/reviewedApprovalRoles/" + reviewChannel),
        "Installed local reviewed approval maps its source to the role");
    installedRoute(processor, document, "activation.reviewed.workflow.seller", reviewChannel);
    equal(Values.UNDEFINED, processor.read(document, POLICY + "/reviewedApprovalRoles/seller"),
        "External party channel is separate from reviewed approval sources");
    System.out.println("PASS exact direct and reviewed approval metadata leaves draft and access routes separate");
  }

  private static void customPlannerMapping(Contracts processor) {
    String handler = "cx.probe.watch.ping";
    String expectedChannel = handler + "_source";
    String renamedChannel = "renamed." + handler;
    var compatible = initialize(processor, withSourceChannelHelper(processor, of(map("$var", "id"), "_", "source")));
    equal(of(expectedChannel), processor.read(compatible, POLICY + "/preChannels"),
        "An equivalent custom helper retains the stock grant");
    installedRoute(processor, compatible, handler, expectedChannel);
    var delivered = apply(processor, compatible, "emitPing", map(), 1).document();
    equal(false, processor.read(delivered, "/activation/active"), "Custom mapping is tested before approval");
    equal(true, processor.read(delivered, "/effects/named"), "Equivalent custom mapping delivers the listed connection");
    equal(Values.UNDEFINED, processor.read(delivered, "/effects/unlisted"), "Equivalent helper leaves the unlisted route pending");

    var differentlyMapped = initialize(processor, withSourceChannelHelper(processor, of("renamed.", map("$var", "id"))));
    equal(of(expectedChannel), processor.read(differentlyMapped, POLICY + "/preChannels"),
        "Exact shared planConnections passes admission but resolves the canonical source name");
    equal(Values.UNDEFINED, processor.read(differentlyMapped, "/contracts/" + expectedChannel),
        "The renamed plan did not install the granted channel");
    installedRoute(processor, differentlyMapped, handler, renamedChannel);
    var blocked = apply(processor, differentlyMapped, "emitPing", map(), 1).document();
    equal(false, processor.read(blocked, "/activation/active"), "Renamed route is tested before approval");
    equal(Values.UNDEFINED, processor.read(blocked, "/effects/named"), "Renamed source is not covered by the grant");
    equal(Values.UNDEFINED, processor.read(blocked, "/effects/unlisted"), "Renaming granted no rights to the unlisted route");
    var approved = apply(processor, blocked, "approve_seller",
        map("revision", processor.read(blocked, "/activation/revision")), 2).document();
    equal(true, processor.read(approved, "/activation/active"), "Seller can approve through the unchanged authority");
    var after = apply(processor, approved, "emitPing", map(), 3).document();
    equal(true, processor.read(after, "/effects/named"), "Renamed route is operational after approval");
    System.out.println("PASS F04 equivalent custom helper uses the declared early route; renamed helper installs a different route and remains gated");
  }

  private static Map<String, Object> withSourceChannelHelper(Contracts processor, List<Object> pieces) {
    var source = source(PROBE, "watch", "ping", true,
        map("preActivationConnections", of(named(PROBE, "watch", "ping"))));
    var probe = fields(fields(source.get("clauses")).get(PROBE));
    var type = fields(probe.get("type"));
    var functions = fields(fields(type.get("hookDefinition")).get("functions"));
    var values = processor.execution().values();
    var library = values.source(map("type", "Connections/Connection Planning Functions"));
    var shared = values.select(library, "/functions");
    // Compose the published members by exact reference before admission, as $blue:membersFrom does.
    for (String name : fields(values.bexData(shared)).keySet()) {
      functions.putIfAbsent(name,
          map("blueId", NativeRuntime.identity(values.exact(values.select(library, "/functions/" + name)))));
    }
    functions.put("connectionSourceChannel",
        map("args", map("id", map("type", "Text")), "expr", map("$concat", pieces)));
    customPlanner(type, "Contracts/Compute Definition", functions);
    return source;
  }

  private static void installedRoute(Contracts processor, Contracts.Document document, String handler, String channel) {
    equal(channel, processor.read(document, "/contracts/" + handler + "/channel"), "Installed handler uses its planned source");
    require(processor.read(document, "/contracts/" + channel) != Values.UNDEFINED, "Planned source channel is installed");
  }

  private static String identity(Contracts processor, Object source) {
    return NativeRuntime.identity(processor.execution().values().source(source));
  }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> fields(Object value) {
    return (Map<String, Object>) value;
  }

  private static void malformedReferences(Contracts processor) {
    for (var malformed : of(
        map("clause", PROBE, "action", "watch", "connection", "ping", "automatic", true),
        map("clause", PROBE, "action", "prime", "automatic", false),
        map("clause", PROBE, "action", "watch", "observations", false),
        map("clause", PROBE, "action", "watch", "connection", "ping", "observations", true),
        map("clause", PROBE, "action", "watch", "automatic", true, "observations", true),
        map("clause", PROBE, "action", "watch", "connection", "*"),
        "cx.probe.watch.ping_source",
        map("clause", PROBE, "connection", "ping"))) {
      rejected(processor, of(malformed), "INVALID_PRE_ACTIVATION_CONNECTION_REFERENCE");
    }
    rejected(processor, map("clause", PROBE, "action", "watch", "connection", "ping"),
        "INVALID_PRE_ACTIVATION_CONNECTION_REFERENCE");
    rejected(processor, of(named("missing", "watch", "ping")), "PRE_ACTIVATION_CONNECTION_UNKNOWN_CLAUSE");
    rejected(processor, of(named("activation", "watch", "ping")), "PRE_ACTIVATION_CONNECTION_CLAUSE_NOT_CONNECTED");
    rejected(processor, of(named(PROBE, "missing", "ping")), "PRE_ACTIVATION_CONNECTION_UNKNOWN_ACTION");
    rejected(processor, of(observations(PROBE, "missing")), "PRE_ACTIVATION_CONNECTION_UNKNOWN_ACTION");
    rejected(processor, of(observations(PROBE, "execute")), "PRE_ACTIVATION_CONNECTION_ACTION_NOT_OBSERVATIONAL");
    rejected(processor, of(named(PROBE, "watch", "missing")), "PRE_ACTIVATION_CONNECTION_UNKNOWN_CONNECTION");
    rejected(processor, of(automatic(PROBE, "watch")), "PRE_ACTIVATION_CONNECTION_UNKNOWN_CONNECTION");
    rejected(processor, of(named(PROBE, "watch", "shared")), "PRE_ACTIVATION_CONNECTION_SHARED_CHANNEL");
    rejected(processor, of(named(PROBE, "watch", "timed")), "PRE_ACTIVATION_CONNECTION_TIMER_UNSUPPORTED");
    var forgedSource = source(PROBE, "watch", "ping", false,
        map("preActivationConnections", of(named(PROBE, "watch", "ping"))));
    var probe = fields(fields(forgedSource.get("clauses")).get(PROBE));
    var pass = map("args", map(), "expr", map("allowed", true, "code", ""));
    var emptyPlan = map("args", map(), "expr", map("contracts", map(), "states", map(), "reads", of()));
    customPlanner(fields(probe.get("type")), "Contracts/Compute Definition",
        map("validateTransition", pass, "validateConfiguration", pass, "plan", emptyPlan, "planConnections", emptyPlan));
    require(!processor.initialize(forgedSource).commits(), "Unrelated planner compiled a logical grant");
    expectFailure("PRE_ACTIVATION_CONNECTION_CLAUSE_NOT_CONNECTED",
        () -> ClauseGasProbe.diagnose(processor, forgedSource));
    System.out.println("PASS invalid shapes, wildcards, missing declarations, forged planner, and unsupported channel/timer");
  }

  private static void compositionChanges(Contracts processor, boolean grouped) {
    var connections = grouped ? of(automatic(PROBE, "prime"), observations(PROBE, "watch"))
        : references(PROBE, "watch", "ping");
    var policy = map("preActivationConnections", connections);
    var stock = activate(processor, initialize(processor, source(PROBE, "watch", "ping", false, policy)));
    var changed = amend(processor, stock, 2,
        map("action", "update", "key", PROBE, "clause", probe("watch", "renamed", false)));
    var events = ClauseGasProbe.eventData(processor, changed);
    require(events.stream().anyMatch(e -> e instanceof Map<?, ?> event
        && "CONNECTIONS_REQUIRE_NEW_CLAUSE_KEY".equals(event.get("code"))), "Expected same-key edit rejection: " + events);
    equal(processor.read(stock, POLICY + "/preChannels"),
        processor.read(changed.document(), POLICY + "/preChannels"), "Rejected amendment preserves grants");

    var removable = activate(processor,
        initialize(processor, source(PROBE, "watch", "ping", true, policy)));
    if (grouped) {
      var extended = probe("watch", "ping", true);
      fields(extended.get("bindings")).put("watch", map(
          "ping", map("on", "event", "event", map("type", PING)),
          "newObservation", map("on", "event", "event", map("type", PING))));
      var replaced = amend(processor, removable, 2, map("action", "update", "key", PROBE, "clause", extended)).document();
      require(processor.read(replaced, "/contracts/cx.probe.watch.newObservation_source") != Values.UNDEFINED,
          "Replacement installed the new observation");
      equal(of(), processor.read(replaced, POLICY + "/preChannels"),
          "Changed declaration does not inherit the compact grant");
    }
    var unchangedReference = amend(processor, removable, 2,
        map("action", "add", "key", "otherProbe", "clause", removableProbe("alternate")));
    equal(processor.read(removable, POLICY + "/preChannels"),
        processor.read(unchangedReference.document(), POLICY + "/preChannels"),
        "Unrelated addition preserves live references");
    equal(true, processor.read(unchangedReference.document(), "/clauses/otherProbe") != Values.UNDEFINED,
        "Addition committed");

    var replacement = amend(processor, unchangedReference.document(), 3,
        map("action", "remove", "key", PROBE),
        map("action", "add", "key", "replacement", "clause", removableProbe("replacement")));
    equal(Values.UNDEFINED, processor.read(replacement.document(), "/clauses/" + PROBE), "Removal committed");
    equal(Values.UNDEFINED, processor.read(replacement.document(), "/contracts/cx.probe.watch.ping_source"),
        "Retired channel removed");
    equal(of(), processor.read(replacement.document(), POLICY + "/preChannels"), "No orphaned grants");
    var addedAgain = amend(processor, replacement.document(), 4,
        map("action", "add", "key", PROBE, "clause", probe("watch", "ping", true)));
    equal(of(), processor.read(addedAgain.document(), POLICY + "/preChannels"),
        "A reused clause key did not regrant withdrawn rights");
    equal(true, processor.read(addedAgain.document(), "/contracts/cx.probe.watch.ping_source") != Values.UNDEFINED,
        "Re-added clause has a route without a pre-activation grant");
    System.out.println("PASS " + (grouped ? "compact" : "individual")
        + " grant lifecycle with rejected update, unchanged declaration, replacement, removal and key reuse");
  }

  private static void installActivation(Contracts processor) {
    var source = source(PROBE, "watch", "ping", false, map("preActivationConnections",
        references(PROBE, "watch", "ping")));
    var clauses = fields(source.get("clauses"));
    var activation = fields(clauses.remove("activation"));
    activation.put("bindings", map());
    var probe = fields(clauses.get(PROBE));
    var managerWorkflow = map("on", "workflow", "party", "manager");
    probe.put("bindings", map("emit", map("emitPing", managerWorkflow), "execute", map("perform", managerWorkflow)));
    var before = initialize(processor, source);

    var invalidParams = map();
    invalidParams.putAll(fields(activation.get("parameters")));
    invalidParams.put("preActivationConnections", of(named("missing", "watch", "ping")));
    var invalid = map("type", activation.get("type"), "bindings", map(), "parameters", invalidParams);
    var event = operation(before, "manager", "amendComposition",
        amendment(processor, before, 1, map("action", "add", "key", "activation", "clause", invalid)));
    require(!processor.process(before, event, 1).commits(), "Installing Activation must validate refs");
    expectFailure("PRE_ACTIVATION_CONNECTION_UNKNOWN_CLAUSE",
        () -> ClauseGasProbe.diagnose(processor, before, event, 1));

    var accepted = amend(processor, before, 2,
        map("action", "add", "key", "activation", "clause", activation)).document();
    equal(false, processor.read(accepted, "/activation/active"), "New Activation waits for approval");
    equal(of("cx.probe.prime._automatic_source", "cx.probe.watch.ping_source"),
        processor.read(accepted, POLICY + "/preChannels"), "New Activation receives its explicit grants");
    System.out.println("PASS legal Activation installation validates and applies its logical policy");
  }

  private static Map<String, Object> removableProbe(String operationSuffix) {
    var clause = probe("watch", "ping", true);
    // The public workflow keys are global. Distinct test instances must use distinct names.
    return map("type", clause.get("type"), "parameters", clause.get("parameters"),
        "bindings", map("emit", map("emit" + operationSuffix, workflow()), "execute",
            map("perform" + operationSuffix, workflow())));
  }

  private static Map<String, Object> source(String key, String action, String connection,
      boolean removable, Map<String, Object> config) {
    var seller = map("type", "Parties/Party", "lead", map("channel",
        map("type", "Contracts/External Channel", "event", map("source", "seller"))),
        "myosAccountId", "seller-account", "readerKeys", of("reader-seller"));
    var params = map("parties", map("seller", seller), "required", of("seller"),
        "preActivationOperations", of("emitPing"));
    params.putAll(config);
    var amend = map("$appendEvent", map("$merge", of(
        map("type", "Clauses/Amendment Requested"),
        map("actorChannel", "manager", "request", map("$var", "trigger")))));
    var governor = map("type", map("name", "Fixture amendment governor",
        "type", "Features/Feature Clause", "governsAmendments", true),
        "parameters", map("actions", map("amend", map("do", of(amend)))),
        "bindings", map("amend", map("amendComposition", map("on", "workflow", "party", "manager"))));
    return map("name", "Activation connection reference", "type", "Orders/Order with Clauses",
        "effects", map(), "contracts", map("manager", map("type", "Contracts/External Channel",
            "event", map("source", "manager"))), "clauses", map(
            "activation", map("type", "Activation/Activation Clause", "parameters", params),
            "governor", governor, key, probe(action, connection, removable)));
  }

  private static Map<String, Object> probe(String action, String connection, boolean removable) {
    var type = map("name", "Fixture Connections actions", "type", "Features/Feature Clause",
        "defaultBindings", map(action, map(connection, map("on", "event", "event", map("type", PING)))));
    if (removable) {
      customPlanner(type, "Connections/Connection Planning Functions", map(
          "validateConfiguration", planFunction("validateConnectionsConfiguration"),
          "validateTransition", map("args", map(), "expr", map("allowed", true, "code", "")),
          "plan", planFunction("planConnections")));
    }
    return map("type", type, "parameters", map("actions", map(
        "prime", map("automatic", map("on", "initialized"), "do", of(effect("automatic"))),
        action, map("observation", true, "do", of(effect("named"))),
        "other", map("do", of(effect("unlisted"))),
        "emit", map("do", of(map("$appendEvent", map("type", PING, "text", "ping")))),
        "execute", map("do", of(effect("workflow"))))),
        "bindings", map("emit", map("emitPing", workflow()), "execute", map("perform", workflow()),
            "other", map("alsoPing", map("on", "event", "event", map("type", PING)))));
  }

  private static void customPlanner(Map<String, Object> clauseType, String library, Map<String, Object> functions) {
    clauseType.put("type", "Clauses/Clause");
    clauseType.put("configurableActions", true);
    clauseType.put("hookAbi", "document-context-1");
    clauseType.put("hookDefinition", map("type", library, "functions", functions));
  }

  private static Map<String, Object> planFunction(String function) {
    return map("args", map(), "expr", map("$call", map("function", function, "args", map())));
  }

  private static Map<String, Object> workflow() {
    return map("on", "workflow", "party", "seller");
  }

  private static List<Object> references(String clause, String action, String connection) {
    return of(automatic(clause, "prime"), named(clause, action, connection), named(clause, "execute", "perform"));
  }

  private static Map<String, Object> automatic(String clause, String action) {
    return map("clause", clause, "action", action, "automatic", true);
  }

  private static Map<String, Object> named(String clause, String action, String connection) {
    return map("clause", clause, "action", action, "connection", connection);
  }

  private static Map<String, Object> observations(String clause, String action) {
    return map("clause", clause, "action", action, "observations", true);
  }

  private static Map<String, Object> effect(String effect) {
    return map("$appendChange", map("op", "add", "path", "/effects/" + effect, "val", true));
  }

  private static Contracts.Document initialize(Contracts processor, Object source) {
    var result = processor.initialize(source);
    if (!result.commits()) {
      ClauseGasProbe.diagnose(processor, source);
    }
    require(result.commits(), OperationInputConformance.initializationDiagnostic(processor, result));
    return result.document();
  }

  private static void rejected(Contracts processor, Object references, String reason) {
    var source = source(PROBE, "watch", "ping", false, map(
        "preActivationConnections", references, "preActivationChannels", of("cx.probe.prime._automatic_source")));
    var probe = fields(fields(source.get("clauses")).get(PROBE));
    var bindings = fields(probe.get("bindings"));
    if (reason.equals("PRE_ACTIVATION_CONNECTION_TIMER_UNSUPPORTED")) {
      bindings.put("watch", map("timed", map("on", "timer", "timestamp", 10)));
    }
    if (reason.equals("PRE_ACTIVATION_CONNECTION_SHARED_CHANNEL")) {
      bindings.put("watch", map("shared", map("on", "channel", "channel", "seller")));
    }
    require(!processor.initialize(source).commits(), "Invalid reference unexpectedly initialized: " + references);
    expectFailure(reason, () -> ClauseGasProbe.diagnose(processor, source));
  }

  private static void expectFailure(String reason, Runnable diagnose) {
    try {
      diagnose.run();
      throw new AssertionError("Missing planning error " + reason);
    } catch (BexError error) {
      equal(reason, error.getMessage(), "Planning diagnostic");
    }
  }

  private static Contracts.Document activate(Contracts processor, Contracts.Document document) {
    var activated = apply(processor, document, "approve_seller",
        map("revision", processor.read(document, "/activation/revision")), 1).document();
    equal(true, processor.read(activated, "/activation/active"), "Approval activated the fixture");
    return activated;
  }

  @SafeVarargs
  private static Contracts.Result amend(Contracts processor, Contracts.Document document, long time,
      Map<String, Object>... changes) {
    return apply(processor, document, "manager", "amendComposition", amendment(processor, document, time, changes), time);
  }

  @SafeVarargs
  private static Map<String, Object> amendment(Contracts processor, Contracts.Document document, long time,
      Map<String, Object>... changes) {
    return map("requestId", "amend-" + time,
        "expectedRevision", processor.read(document, "/clauseRuntime/revision"),
        "expectedConfigurationId", processor.read(document, "/clauseRuntime/configurationId"), "changes", of(changes));
  }

  private static Object operation(Contracts.Document document, String actor, String operation, Object request) {
    return map("source", actor, "operation", map("type", "Contracts/Operation Request",
        "channel", actor, "operation", operation, "request", request,
        "document", map("blueId", document.blueId()), "requireExactDocumentVersion", true));
  }

  private static Contracts.Result apply(Contracts processor, Contracts.Document document,
      String operation, Object request, long time) {
    return apply(processor, document, "seller", operation, request, time);
  }

  private static Contracts.Result apply(Contracts processor, Contracts.Document document,
      String actor, String operation, Object request, long time) {
    var event = operation(document, actor, operation, request);
    var result = processor.process(document, event, time);
    if (!result.commits()) {
      ClauseGasProbe.diagnose(processor, document, event, time);
    }
    require(result.commits(), operation + " did not complete: " + ClauseGasProbe.diagnostic(result));
    return result;
  }

  private static Map<String, Object> map(Object... pairs) {
    return OperationInputConformance.m(pairs);
  }

  private static void equal(Object expected, Object actual, String context) {
    require(Objects.equals(expected, actual), context + ": expected " + expected + ", got " + actual);
  }

  private static void require(boolean condition, String message) {
    OperationInputConformance.require(condition, message);
  }
}
