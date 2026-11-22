package blue.core;

import static blue.core.Values.*;
import static blue.coordination.ProviderProtocol.ref;

import blue.contracts.RuntimeBindings;
import blue.coordination.Coordination;
import blue.coordination.ProviderProtocol;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** The independently hosted catalog test submits delegated operations under native mandates. */
final class CatalogOrderIndependentMandates {
  private static final Duration WAIT = Duration.ofSeconds(90);
  private static final RuntimeBindings MANDATE_RUNTIME = RuntimeBindings.accessEvents()
      .withDefinitionReadV1().withMandateInitializationV2().withProcessingEventSourceV1();
  private static final String MANDATE_TYPE = "4hhnMbRj7ftRD2LKyNfu7tmmfF9V1k29impeX64jnNvM";
  private static final Set<String> ORDER_OPERATIONS = Set.of("prepareOrder", "provideOrder");
  private static final Set<String> PAYMENT_OPERATIONS = Set.of("preparePayment", "providePayment");

  private record Target(String origin, String channel) {}

  private final AcceptedBootstrapTestSupport fixture;
  private final TimelineProvider provider;
  private final Tenant owner;
  private final AgentContext actor;
  private final Map<Target, Coordination.Document> mandates = new LinkedHashMap<>();

  private CatalogOrderIndependentMandates(
      AcceptedBootstrapTestSupport fixture, TimelineProvider provider, Tenant owner, AgentContext actor) {
    this.fixture = fixture;
    this.provider = provider;
    this.owner = owner;
    this.actor = actor;
  }

  static CatalogOrderIndependentMandates connect(
      AcceptedBootstrapTestSupport fixture, TimelineProvider provider, Map<String, Tenant> tenants,
      Tenant owner) throws Exception {
    var security = fixture.host.security;
    var identity = new BusinessServiceAuthentication(
        HostBusinessServiceTest.KEY, 1, fixture.host.records.clock);
    var service = new HostBusinessService(security, identity);
    new HostBusinessAccounts(security, service, identity, fixture.secrets).ensure(owner.account);
    var login = new HostLogin(null, security, security.reader(fixture.host.records.database.database));
    AgentContext actor;
    try (var session = login.openBusiness(identity.token(), owner.account, identity)) {
      actor = HostLogin.principal(session).agent();
    }
    expect(actor.origin() instanceof AgentContext.BusinessAccount, "Expected the connected Business Agent");
    owner.writerSecurity.synchronize();
    if (owner.mandateImports == null) {
      owner.mandateImports = new MandateImports(owner, owner.account, provider, fixture.keys,
          (account, action, input) -> {
            var recipient = tenants.values().stream().filter(tenant -> account.equals(tenant.account))
                .findFirst().orElseThrow();
            return BootstrapWorkspace.apply(recipient, account, action, input);
          });
    }
    // The test owner opts into the same native mandate verification used for the hosted purchase.
    owner.mandateImports.policy(true, id(), fixture.human(owner.account));
    return new CatalogOrderIndependentMandates(fixture, provider, owner, actor);
  }

  AgentContext actor() {
    return actor;
  }

  Map<String, Object> bootstrapPayment(Coordination.Document order,
      NativePreparedPaymentRequirement.Requirement requirement, String key) throws Exception {
    var mandate = mandate(new Target(order.state().documentId(), "seller"));
    fixture.worker(owner);
    var selector = map("clauseId", requirement.clauseId(), "itemKey", requirement.itemKey(),
        "requestId", requirement.requestId(), "requirementRef", requirement.requirementRef());
    var authorized = owner.command(actor, "document.bootstrap",
        () -> PreparedPaymentAuthorization.require(owner, actor, order.handle(), selector, mandate.handle()));
    expect(mandate.state().documentId().equals(authorized.mandateDocumentId())
            && order.state().documentId().equals(authorized.orderDocumentId())
            && requirement.requirementRef().equals(authorized.requirementRef()),
        "Seller payment policy did not qualify the exact prepared requirement");
    var validatedInput = obj(authorized.bootstrapInput().get("input"));
    // The paid Business flow submits the exact prepared source with recipient bindings.
    var started = fixture.start(owner.account, map("document", ref(requirement.requirementRef()),
        "inputMode", "exact", "executionSelection", validatedInput.get("executionSelection"),
        "participantMappings", validatedInput.get("participantMappings")), key, actor);
    String admissionId = required(started, "bootstrapId");
    var admission = owner.records.get("admissions", admissionId);
    expect(admission.get("human") == null && actor.equals(HostSubjects.admission(admission))
            && authorized.businessConnectionGeneration().longValue() == number(admission.get(PaymentBusinessGrant.FIELD)),
        "Prepared Payment Instruction did not retain the seller Business Agent");
    var accepted = provider.bootstrapPlan(required(owner.records.get("bootstrap_jobs", admissionId), "acceptedPlan"));
    expect(actor.equals(AgentContext.read(accepted.get("acceptedAgent")))
            && requirement.requirementRef().equals(obj(accepted.get("prepared")).get("sourceBlueId"))
            && started.get("sessionId").equals(accepted.get("sessionId")),
        "Canonical payment registration did not retain the seller Agent and exact prepared source");
    return started;
  }

  String submit(Coordination.Document target, String partyChannel, String operation,
      Map<String, Object> request, boolean exact, String... allScopedOperations) throws Exception {
    var key = new Target(target.state().documentId(), partyChannel);
    var scope = operations(partyChannel);
    expect(scope.contains(operation), "Operation is outside the test party's mandate");
    expect(allScopedOperations.length == 0 || scope.equals(Set.of(allScopedOperations)),
        "Mandate scope differs from the catalog workflow");
    var mandate = mandate(key);
    var input = map("accountId", owner.account, "documentId", key.origin(),
        "mandateId", mandate.state().documentId(), "operation", operation, "request", request);
    if (exact) input.put("documentVersion", target.state().stable().orElseThrow().blueId());
    var accepted = BusinessAgentOperations.submit(owner, actor, input, id());
    var receipt = AcceptedBootstrapTestSupport.await(owner, required(accepted, "admissionId"), WAIT);
    expect("succeeded".equals(receipt.get("status")), "Delegated " + operation + " admission failed");
    var result = obj(receipt.get("result"));
    String entry = required(result, "entryBlueId");
    requireSignedAuthority(result, entry, key, mandate, exact);
    return entry;
  }

  private Coordination.Document mandate(Target target) throws Exception {
    var existing = mandates.get(target);
    if (existing != null) return existing;
    var source = mandateSource(target);
    String mandatePackage = "partner".equals(target.channel())
        ? PackageDefaults.CURRENT_MANDATE_PACKAGE : PackageDefaults.COMPOSED_MANDATE_PACKAGE;
    var started = fixture.start(owner.account, map("document", source,
        "packages", List.of(mandatePackage),
        "executionSelection", MANDATE_RUNTIME.identities(),
        "participantMappings", List.of(
            map("channelName", "authorityHolderChannel", "accountId", owner.account),
            map("channelName", "authorizedActorChannel", "accountId", owner.account,
                "agentId", actor.agentId()))), id());
    var mandate = owner.service.document(required(started, "sessionId"));
    mandate.awaitInitialized(WAIT);
    long deadline = System.nanoTime() + WAIT.toNanos();
    while (System.nanoTime() < deadline && accessCount(mandate) != 2) Thread.sleep(20);
    expect(accessCount(mandate) == 2, "Mandate signing routes did not become ready");
    for (int attempt = 0; attempt < 3; attempt++) {
      String approval = fixture.submit(owner, mandate.handle(), "approveMandate", map());
      AcceptedBootstrapTestSupport.awaitOperationOutcome(mandate, approval,
          document -> "Active".equals(document.get("status")), WAIT);
      if ("Active".equals(mandate.state().stable().orElseThrow().document().get("status"))) {
        mandates.put(target, mandate);
        return mandate;
      }
      var disposition = obj(mandate.describe().get("lastInputDisposition"));
      expect("STALE_DOCUMENT_PRECONDITION".equals(disposition.get("reason")),
          "Mandate approval did not apply");
    }
    throw new AssertionError("Mandate approval did not reach Active");
  }

  private Map<String, Object> mandateSource(Target target) {
    if ("seller".equals(target.channel())) {
      var source = ReaderAccountPaymentPolicy.source(owner.account);
      source.put("name", "Prepare my customer payments");
      return source;
    }
    return map("type", ref(MANDATE_TYPE), "name", "Process orders from my offer",
        "description", "Allow MyOS to request catalogue quotes when customers review their cart, "
            + "then prepare and link Orders only after their final confirmation. This does not change commercial terms, "
            + "approve Orders or authorize payments.",
        "clauses", map(), "scope", map(
            "step1", map("target", map("initialDocument", ref(target.origin()), "channel", "partner", "operation", "prepareOrder")),
            "step2", map("target", map("initialDocument", ref(target.origin()), "channel", "partner", "operation", "provideOrder"))));
  }

  private void requireSignedAuthority(Map<String, Object> result, String entry, Target target,
      Coordination.Document mandate, boolean exactVersion) {
    try (var view = fixture.canonical.store.read(); var exact = new ProviderProtocol()) {
      var signed = view.scan("core_provider_entries", required(result, "timelineId") + "/").stream()
          .map(row -> obj(row.getValue())).filter(row -> entry.equals(row.get("id")))
          .findFirst().orElseThrow();
      Object payload = signed.get("entry");
      Object message = exact.field(payload, "message");
      Object authority = exact.field(payload, "onBehalfOf");
      expect(HostActorProfiles.agent(owner.account, actor.agentId()).equals(exact.field(payload, "actor")),
          "Delegated entry was not signed on the account Agent timeline");
      expect(target.channel().equals(exact.field(message, "channel"))
              && Boolean.valueOf(exactVersion).equals(exact.field(message, "requireExactDocumentVersion")),
          "Signed operation changed its party channel or version precondition");
      expect(authority != null
              && mandate.state().documentId().equals(exact.identify(exact.field(authority, "mandate"))),
          "Signed operation did not carry the approved native mandate");
    }
  }

  private static Set<String> operations(String partyChannel) {
    return switch (partyChannel) {
      case "partner" -> ORDER_OPERATIONS;
      case "seller" -> PAYMENT_OPERATIONS;
      default -> throw new AssertionError("Unsupported delegated catalog party " + partyChannel);
    };
  }

  private static int accessCount(Coordination.Document mandate) {
    return obj(mandate.state().stable().orElseThrow().document().getOrDefault("timelineAccess", map())).size();
  }

  private static void expect(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
}
