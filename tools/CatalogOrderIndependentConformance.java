package blue.core;

import static blue.core.Values.*;

import blue.contracts.Contracts;
import blue.contracts.ContractsExecution;
import blue.contracts.RuntimeBindings;
import blue.coordination.Coordination;
import blue.language.next.Blue;
import blue.language.next.Exact;
import blue.language.next.WireData;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.BooleanSupplier;

/** Runs the authored paid checkout through independently processing Core accounts. */
public final class CatalogOrderIndependentConformance {
  private static final RuntimeBindings RUNTIME = BusinessAgentPreparationFixture.RUNTIME;
  private static final String SELLER = "seller";
  private static final String PARTNER = "partner";
  private static final String GUARANTOR = "guarantor";
  private static final String CUSTOMER = "customer";
  private static final String PROVISION_INPUT = "BteTJBAcHb5ppEg1ezCtPY6tJSDSHzxP1Xr1r5CAkmdM";
  private static final List<String> REGISTERED = List.of(SELLER, PARTNER, GUARANTOR, CUSTOMER);
  private static final Duration WAIT = Duration.ofMinutes(3);

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]);
    var authored = readFile(root.resolve("tools/fixtures/paid-catalogue-reseller.json"));
    try (var host = CatalogOrderIndependentGuarantor.open(REGISTERED, GUARANTOR);
         var scenario = new Scenario(root, authored, host, args.length > 1 && args[1].equals("converged-source"))) {
      scenario.run();
    }
  }

  private static final class Scenario implements AutoCloseable {
    private final Map<String, Object> authored;
    private final AcceptedBootstrapTestSupport fixture;
    private final TimelineProvider provider;
    private final CatalogOrderIndependentGuarantor host;
    private final boolean requireConvergedSource;
    private final Map<String, Tenant> tenants = new LinkedHashMap<>();
    private final ResellerPackage resellerPackage;
    private final List<String> packages;
    private final Map<Tenant, Blue> languages = new LinkedHashMap<>();
    private final Map<Tenant, ContractsExecution.Values> views = new LinkedHashMap<>();

    Scenario(Path root, Map<String, Object> authored, CatalogOrderIndependentGuarantor host,
        boolean requireConvergedSource) throws Exception {
      this.authored = authored;
      this.host = host;
      this.requireConvergedSource = requireConvergedSource;
      fixture = host.fixture();
      provider = host.provider();
      resellerPackage = ResellerPackage.current(root);
      var requested = new ArrayList<>(arr(authored.get("packages")).stream().map(Values::text).toList());
      requested.removeIf(resellerPackage.previous()::equals);
      if (!requested.contains(resellerPackage.current())) requested.add(resellerPackage.current());
      packages = List.copyOf(requested);
      for (String account : REGISTERED) {
        var tenant = host.tenant(account);
        tenants.put(account, tenant);
        tenant.packages.installClosure(packages.stream().filter(id -> !id.equals(resellerPackage.current())).toList());
        tenant.packages.installVerified(resellerPackage.metadata(), resellerPackage.resource());
        tenant.partyAccess.settings(true, "catalog-reseller-activation-sharing", fixture.human(account));
      }
    }

    void run() throws Exception {
      var seller = tenants.get(SELLER);
      var partner = tenants.get(PARTNER);
      var guarantor = tenants.get(GUARANTOR);
      String readerKey = required(fixture.keys.paymentAdmissionKey(GUARANTOR, fixture.human(GUARANTOR)), "publicKey");
      var stripe = new CatalogOrderIndependentPrecheckout.StripeFixture(fixture.host.records, SELLER);
      HostAccountTestSupport.paymentCountry(fixture.host.records, SELLER, fixture.human(SELLER), "US");
      String recipient = required(new StripePaymentAccounts(fixture.host.records, stripe.gateway(), stripe.platform())
          .create(SELLER, fixture.human(SELLER), "US", id()), "paymentAccountId");
      var agreementSource = admitAgreement(seller, bindFixture(readerKey, recipient));

      var partnerMandates = CatalogOrderIndependentMandates.connect(fixture, provider, tenants, partner);
      var sellerMandates = CatalogOrderIndependentMandates.connect(fixture, provider, tenants, seller);
      System.out.println("BOOTSTRAP Agreement source=" + agreementSource + " package=" + resellerPackage.current()
          + " ordersType=" + resellerPackage.ordersType());
      var agreementBootstrap = bootstrap(ref(agreementSource), arr(authored.get("participants")));
      Map<String, Object> agreementStart;
      try {
        agreementStart = host.start(SELLER, agreementBootstrap, "paid-reseller-agreement");
      } catch (Problem failure) {
        try {
          BootstrapInputs.prepare(seller, fixture.accounts, SELLER, BootstrapInputs.request(agreementBootstrap));
        } catch (RuntimeException diagnostic) {
          failure.addSuppressed(diagnostic);
        }
        System.err.println("Agreement bootstrap " + failure.code + " status=" + failure.status);
        throw failure;
      }
      String agreementSession = required(agreementStart, "sessionId");
      var sellingAgreement = initialized(seller, agreementSession);
      var partnerAgreement = initialized(partner, agreementSession);
      requireSameOrigin(List.of(sellingAgreement, partnerAgreement));
      human(seller, sellingAgreement, "approve_seller", map("revision", 1));
      human(partner, partnerAgreement, "approve_partner", map("revision", 1));
      for (var agreement : List.of(sellingAgreement, partnerAgreement)) {
        await("Agreement active in " + agreement.handle(), () -> Boolean.TRUE.equals(field(agreement, "activation", "active")));
      }
      System.out.println("PASS seller and partner independently processed Agreement approvals");

      var preparation = obj(authored.get("prepareOrder"));
      String key = required(preparation, "key");
      var expected = obj(authored.get("expected"));
      long amount = number(expected.get("amountMinor"));
      long commission = number(expected.get("commissionMinor"));
      for (Object raw : arr(obj(preparation.get("values")).get("groups"))) {
        obj(raw).put("proposedStartMicros", Instant.now().plus(Duration.ofDays(7)).getEpochSecond() * 1_000_000);
      }
      var purchase = CatalogOrderIndependentPrecheckout.authorize(fixture, partner, partnerMandates.actor(),
          sellerMandates.actor(), partnerAgreement, preparation, stripe);
      purchase.bind(fixture.human(CUSTOMER), CUSTOMER);
      String preparationEntry = partnerMandates.submit(partnerAgreement, PARTNER, "prepareOrder", preparation, true,
          "prepareOrder", "provideOrder");
      processed(partner, partnerAgreement, preparationEntry, "partner prepares catalog Order");
      processed(seller, sellingAgreement, preparationEntry, "seller receives catalog preparation");
      var orderRequirement = entry(partnerAgreement, "orders", key);
      equal(required(orderRequirement, "requirementRef"), required(entry(sellingAgreement, "orders", key), "requirementRef"),
          "Both Agreement accounts prepared the same exact Order source");
      var orderStart = fixture.start(PARTNER, bootstrap(ref(required(orderRequirement, "requirementRef")),
          arr(authored.get("childParticipants"))), "paid-reseller-order", partnerMandates.actor());
      var orderAdmission = partner.records.get("admissions", required(orderStart, "bootstrapId"));
      equal(partnerMandates.actor(), HostSubjects.admission(orderAdmission), "Order bootstrap uses the partner Business account");
      var orderPlan = provider.bootstrapPlan(required(
          partner.records.get("bootstrap_jobs", required(orderStart, "bootstrapId")), "acceptedPlan"));
      equal(partnerMandates.actor(), AgentContext.read(orderPlan.get("acceptedAgent")), "Accepted Order plan retained signed partner authority");
      equal(required(orderRequirement, "requirementRef"), obj(orderPlan.get("prepared")).get("sourceBlueId"),
          "Accepted Order plan retained exact prepared origin");
      String orderSession = required(orderStart, "sessionId");
      System.out.println("BOOTSTRAPPED Order " + orderSession);
      String customerAccount = required(obj(obj(orderStart.get("participants")).get("customer")), "accountId");
      var customer = tenants.get(customerAccount);
      require(customer != null, "Customer must be registered by the ordinary bootstrap recipient dispatch");
      requireIndependentAccounts(List.of(seller, partner, guarantor, customer));
      equal(4L, List.of(seller, partner, guarantor, customer).stream()
          .map(tenant -> required(fixture.keys.defaultKey(tenant.account), "publicKey")).distinct().count(),
          "Distinct participant reader keys");
      var sellerOrder = initialized(seller, orderSession);
      var partnerOrder = initialized(partner, orderSession);
      var guarantorOrder = initialized(guarantor, orderSession);
      var customerOrder = initialized(customer, orderSession);
      String orderOrigin = requireSameOrigin(List.of(sellerOrder, partnerOrder, guarantorOrder, customerOrder));
      equal(false, field(sellerOrder, "activation", "active"), "Order awaiting supplier");
      equal(amount, number(state(sellerOrder).get("amountMinor")), "Actual two-product amount");
      equal("USD", state(sellerOrder).get("currency"), "Actual currency");
      equal(null, state(sellerOrder).get("payment"), "No Payment Instruction exists yet");
      require(!obj(field(guarantorOrder, "activation", "parties")).containsKey(GUARANTOR),
          "Guarantor can read the Order as an explicit reader");
      assertAgreementPrivate(agreementStart, agreementSession, readerKey, guarantor, customer);

      String initialOrder = stableId(partnerOrder);
      var provision = provision(orderRequirement, initialOrder);
      String orderProvided = partnerMandates.submit(partnerAgreement, PARTNER, "provideOrder", provision, true,
          "prepareOrder", "provideOrder");
      processed(partner, partnerAgreement, orderProvided, "partner provides Order");
      processed(seller, sellingAgreement, orderProvided, "seller receives first provideOrder");
      assertEarly(seller, sellingAgreement, key, orderOrigin);
      assertEarly(partner, partnerAgreement, key, orderOrigin);
      System.out.println("PASS both Agreement accounts independently selected one inactive Order with no PI");

      String preparedPayment = sellerMandates.submit(sellerOrder, SELLER, "preparePayment",
          map("providerReference", purchase.providerReference()), true,
          "preparePayment", "providePayment");
      processed(seller, sellerOrder, preparedPayment, "seller's scoped agent prepares payment");
      processed(guarantor, guarantorOrder, preparedPayment, "guarantor observes payment preparation as Order reader");
      var paymentEntry = entries(sellerOrder, "payment").values().stream().map(Values::obj).findFirst().orElseThrow();
      var paymentRequirement = NativePreparedPaymentRequirement.read(seller, fixture.human(SELLER), orderSession,
          map("requestId", paymentEntry.get("requestId")));
      equal("stripe", paymentRequirement.provider(), "Actual authored Stripe program");
      equal(GUARANTOR, paymentRequirement.guarantorAccountId(), "Frozen guarantor");
      equal(recipient, paymentRequirement.recipientPaymentAccountId(), "Local supplier payment account");
      equal(amount, paymentRequirement.amountMinor(), "Frozen checkout amount");
      equal(purchase.providerReference(),
          read(seller, sellerOrder, required(paymentEntry, "itemPath") + "/prepared/paymentDetails/providerReference"),
          "Prepared PI references the original authorized precheckout");
      host.startWorker(stripe.gateway(), stripe.platform());
      var paymentStart = sellerMandates.bootstrapPayment(sellerOrder, paymentRequirement, "paid-reseller-payment");
      String paymentSession = required(paymentStart, "sessionId");
      System.out.println("BOOTSTRAPPED Payment Instruction " + paymentSession);
      var guarantorPayment = initialized(guarantor, paymentSession);
      var sellerPayment = initialized(seller, paymentSession);
      var partnerPayment = initialized(partner, paymentSession);
      var customerPayment = initialized(customer, paymentSession);
      String paymentOrigin = requireSameOrigin(List.of(sellerPayment, partnerPayment, guarantorPayment, customerPayment));
      equal(orderOrigin, origin(guarantor, guarantorPayment, "/sources/order"), "Guarantor PI references the exact Order");
      var reviewed = paymentCandidate(seller, sellerOrder, sellerPayment);
      equal(orderOrigin, identity(seller, reviewed.payment(), "/businessContext/orderOrigin"),
          "Ready PI keeps the exact authored Order binding");
      equal(purchase.providerReference(), read(seller, reviewed.payment(), "/paymentDetails/providerReference"),
          "Ready PI keeps the bound precheckout intent");
      System.out.println("PROVIDE Payment Instruction candidate=" + reviewed.payment() + " sourceOrder="
          + reviewed.sourceOrder() + " currentOrder=" + reviewed.currentOrder()
          + " requireConvergedSource=" + requireConvergedSource);
      var providePayment = provision(paymentEntry, reviewed.payment());
      providePayment.put("type", ref(PROVISION_INPUT));
      String paymentProvided = sellerMandates.submit(sellerOrder, SELLER, "providePayment", providePayment, false,
          "preparePayment", "providePayment");
      System.out.println("SUBMITTED providePayment entry=" + paymentProvided);
      processed(seller, sellerOrder, paymentProvided, "seller's scoped agent provides Payment Instruction");
      processed(guarantor, guarantorOrder, paymentProvided, "guarantor learns PI provision through Order history");
      for (var account : List.of(seller, guarantor)) {
        var order = account == seller ? sellerOrder : guarantorOrder;
        linkedPayment(account, order, paymentEntry, paymentOrigin);
      }

      await("Guarantor bound the original precheckout authorization", () -> purchase.boundTo(guarantorPayment));
      await("Guarantor published the funded checkout session",
          () -> Boolean.TRUE.equals(read(guarantor, guarantorPayment, "/customerSession/funded")));
      System.out.println("PASS real worker published the funded session for the bound precheckout");
      await("Guarantor published the original payment transaction",
          () -> !text(read(guarantor, guarantorPayment, "/payment/transactionId")).isEmpty());
      await("Guarantor secured the original precheckout authorization",
          () -> number(read(guarantor, guarantorPayment, "/payment/secured")) == amount);
      await("Guarantor completed the original intent ownership handover",
          () -> purchase.adoptedBy(guarantorPayment));
      purchase.assertSecured(guarantorPayment);
      for (var agreement : List.of(partnerAgreement, sellingAgreement)) {
        var account = agreement == partnerAgreement ? partner : seller;
        await("Grant-scoped Agreement observes secured PI " + account.account,
            () -> number(read(account, agreement, orderPath(key) + "/payment/payment/secured")) == amount);
        equal(false, read(account, agreement, orderPath(key) + "/activation/active"), "Authorization preserves pending supplier approval");
        equal(0L, number(read(account, agreement, "/commission/accrued")), "Authorization accrues no commission");
      }
      System.out.println("PASS guarantor worker secured 3895 via Stripe's mock boundary before supplier approval");

      supplierAccept(seller, sellerOrder, preparation, paymentOrigin);
      await("Guarantor completed the payment after supplier confirmation",
          () -> number(read(guarantor, guarantorPayment, "/payment/completed")) == amount);
      var financialJobs = Set.of(PaymentGuarantorHandler.ACCEPT, PaymentGuarantorHandler.ACCEPTED,
          PaymentGuarantorHandler.SECURE, PaymentGuarantorHandler.CAPTURE);
      await("Real guarantor jobs for acceptance, session, secure and capture finished", () -> {
        var jobs = host.jobStatuses(paymentOrigin);
        return financialJobs.stream().allMatch(type -> "FINISHED".equals(jobs.get(type)));
      });
      purchase.assertCaptured(guarantorPayment);
      System.out.println("PASS four native guarantor job types finished in Core's retained emission queue");
      verifyPaid(seller, sellingAgreement, key, orderOrigin, paymentOrigin, amount, commission, preparation);
      verifyPaid(partner, partnerAgreement, key, orderOrigin, paymentOrigin, amount, commission, preparation);
      for (var account : List.of(customer, guarantor)) {
        var order = account.service.document(orderSession);
        await("Independent paid Order for " + account.account, () -> number(read(account, order, "/payment/payment/completed")) == amount);
        equal(orderOrigin, order.state().documentId(), "Recipient Order origin");
      }
      System.out.println("PASS seller and partner independently received capture and accrued 390 before reprovision");

      purchase.replay(guarantorPayment);
      String retried = partnerMandates.submit(partnerAgreement, PARTNER, "provideOrder", provision, true,
          "prepareOrder", "provideOrder");
      require(!orderProvided.equals(retried), "Provision replay is an independent signed input");
      processed(partner, partnerAgreement, retried, "duplicate provision by partner");
      processed(seller, sellingAgreement, retried, "seller receives duplicate provision");
      verifyPaid(seller, sellingAgreement, key, orderOrigin, paymentOrigin, amount, commission, preparation);
      verifyPaid(partner, partnerAgreement, key, orderOrigin, paymentOrigin, amount, commission, preparation);
      purchase.assertCaptured(guarantorPayment);
      assertAgreementPrivate(agreementStart, agreementSession, readerKey, guarantor, customer);
      System.out.println("PASS one original provision and one signed retry preserved one Order and one commission target");
      System.out.println("PASS customer and guarantor hold Order and PI replicas, without Agreement grants");
    }

    private Map<String, Object> bindFixture(String readerKey, String recipient) {
      var source = obj(authored.get("source"));
      var order = obj(source.get("orderTemplate"));
      var activation = clausesParameters(order, "activation");
      var holder = obj(obj(activation.get("readers")).get(GUARANTOR));
      holder.put("myosAccountId", GUARANTOR);
      holder.put("readerKeys", List.of(readerKey));
      var instruction = obj(clausesParameters(order, "payment").get("template"));
      var guarantor = obj(obj(clausesParameters(instruction, "activation").get("parties")).get(GUARANTOR));
      guarantor.put("myosAccountId", GUARANTOR);
      obj(guarantor.get("readerKeys")).put("items", List.of(readerKey));
      obj(obj(instruction.get("paymentDetails")).get("customerPaymentTerms")).put("recipientPaymentAccountId", recipient);
      obj(obj(clausesParameters(source, "activation").get("parties")).get(SELLER)).put("myosAccountId", SELLER);
      var ordersType = obj(obj(obj(source.get("clauses")).get("orders")).get("type"));
      var provenance = obj(obj(authored.get("provenance")).get("candidate"));
      equal(provenance.get("sourceType"), ordersType.get("blueId"), "Exact authored Customer Orders export");
      equal(provenance.get("candidateType"), resellerPackage.ordersType(), "Exact preview.10 Customer Orders export");
      ordersType.put("blueId", resellerPackage.ordersType());
      return source;
    }

    private String admitAgreement(Tenant seller, Map<String, Object> source) throws Exception {
      var request = AdaptedInputs.request("content.create", map("content", source, "goal", "definition"));
      String admission = required(seller.submit("adapted.content.create", request, id(), fixture.human(SELLER)), "id");
      var receipt = AcceptedBootstrapTestSupport.await(seller, admission, WAIT);
      require("succeeded".equals(receipt.get("status")), "Immutable Agreement source admission: " + receipt.get("problem"));
      String sourceId = required(obj(receipt.get("result")), "blueId");
      System.out.println("ADMITTED authored Agreement source " + sourceId);
      return sourceId;
    }

    private Map<String, Object> bootstrap(Object source, List<Object> participants) {
      return map("document", source, "inputMode", "exact", "packages", packages, "executionSelection", RUNTIME.identities(),
          "participantMappings", participants);
    }

    private void human(Tenant actor, Coordination.Document target, String operation, Map<String, Object> request)
        throws Exception {
      for (int attempt = 0; ; attempt++) {
        try {
          processed(actor, target, fixture.submit(actor, target.handle(), operation, request), operation);
          return;
        } catch (OperationRejection rejection) {
          if (attempt == 2 || !"STALE_DOCUMENT_PRECONDITION".equals(rejection.reason)) throw rejection;
          System.out.println(operation + " reviewing the new publication after a stale precondition");
        }
      }
    }

    private ProvisionCandidate paymentCandidate(Tenant seller, Coordination.Document order,
        Coordination.Document payment) throws Exception {
      long deadline = System.nanoTime() + WAIT.toNanos();
      ProvisionCandidate last = null;
      do {
        var orderState = order.state();
        var paymentState = payment.state();
        if (orderState.status() == Coordination.Status.READY && paymentState.status() == Coordination.Status.READY) {
          var orderStable = orderState.stable().orElseThrow();
          var paymentStable = paymentState.stable().orElseThrow();
          var orderActivation = obj(orderStable.document().get("activation"));
          var paymentActivation = obj(paymentStable.document().get("activation"));
          if (Boolean.TRUE.equals(orderActivation.get("functional"))
              && Boolean.TRUE.equals(orderActivation.get("accessReady"))
              && Boolean.TRUE.equals(paymentActivation.get("active"))
              && Boolean.TRUE.equals(paymentActivation.get("functional"))
              && Boolean.TRUE.equals(paymentActivation.get("accessReady"))) {
            last = new ProvisionCandidate(paymentStable.blueId(),
                identity(seller, paymentStable.blueId(), "/sources/order"), orderStable.blueId());
            if (!requireConvergedSource || last.sourceOrder().equals(last.currentOrder())) return last;
          }
        }
        Thread.sleep(50);
      } while (System.nanoTime() < deadline);
      throw new AssertionError("No provision candidate; requireConvergedSource=" + requireConvergedSource
          + " last=" + last + " order=" + order.progress() + " payment=" + payment.progress());
    }

    private void supplierAccept(Tenant seller, Coordination.Document order, Map<String, Object> preparation,
        String paymentOrigin) throws Exception {
      var groups = arr(obj(preparation.get("values")).get("groups"));
      equal(1, groups.size(), "One dated reservation in the authored checkout");
      String group = required(obj(groups.getFirst()), "id");
      Object proposal = read(seller, order, "/reservations/" + group + "/proposalBlueId");
      require(!Boolean.TRUE.equals(read(seller, order, "/activation/approved/seller")),
          "Dated Order has no separate commercial approval before confirmation");
      human(seller, order, "confirmReservation", map("key", "confirm-" + group, "groupId", group,
          "expectedProposalBlueId", proposal));
      var grant = obj(read(seller, order, "/datedSellerGrant"));
      equal(paymentOrigin, grant.get("payment"), "Dated seller grant binds the authorized PI origin");
      equal(proposal, grant.get("proposal"), "Dated seller grant binds the confirmed proposal");
      equal("confirm-" + group, grant.get("requestKey"), "Dated seller grant binds the confirmed receipt");
      equal(true, read(seller, order, "/activation/approved/seller"), "Native dated confirmation grants seller approval");
      equal(true, read(seller, order, "/activation/active"), "Dated confirmation activates the Order");
      equal("PENDING", read(seller, order, "/orderDecision/status"), "Dated confirmation preserves separate decision");
      System.out.println("PASS one signed confirmReservation granted dated approval for original PI " + paymentOrigin);
    }

    private void linkedPayment(Tenant tenant, Coordination.Document order, Map<String, Object> prepared,
        String paymentOrigin) throws Exception {
      String key = required(prepared, "key");
      try {
        await("Original PI is linked to the Order in " + tenant.account, () -> {
          var selected = entry(order, "payment", key);
          return paymentOrigin.equals(selected.get("documentOrigin"))
              && read(tenant, order, "/payment") != null
              && paymentOrigin.equals(origin(tenant, order, "/payment"));
        });
      } catch (AssertionError timeout) {
        var selected = entry(order, "payment", key);
        throw new AssertionError("PI link in " + tenant.account + " status=" + selected.get("status")
            + " reason=" + selected.get("reason") + " origin=" + selected.get("documentOrigin")
            + " paymentPresent=" + (read(tenant, order, "/payment") != null), timeout);
      }
      var selected = entry(order, "payment", key);
      equal(prepared.get("requirementRef"), selected.get("requirementRef"), "Original PI requirement on " + tenant.account);
      System.out.println("PASS " + tenant.account + " linked PI " + paymentOrigin + " status=" + selected.get("status"));
    }

    private void assertAgreementPrivate(Map<String, Object> start, String session, String guarantorReader,
        Tenant guarantor, Tenant customer) {
      var privateReaders = new LinkedHashSet<String>();
      privateReaders.add(guarantorReader);
      for (var tenant : List.of(guarantor, customer)) {
        for (var key : fixture.keys.list(tenant.account)) privateReaders.add(required(key, "publicKey"));
      }
      for (Object raw : obj(start.get("timelines")).values()) {
        var timeline = obj(raw);
        String owner = required(obj(timeline.get("writer")), "accountId");
        String timelineId = required(timeline, "id");
        require(provider.access(owner, timelineId).stream().noneMatch(
            grant -> arr(grant.get("allowedKeys")).stream().anyMatch(privateReaders::contains)),
            "Neither customer nor guarantor receives an Agreement reader grant");
        equal(null, guarantor.imports.get(timelineId), "Guarantor did not import an Agreement timeline");
        equal(null, customer.imports.get(timelineId), "Customer did not import an Agreement timeline");
      }
      for (var tenant : List.of(guarantor, customer)) {
        require(tenant.service.documents().stream().noneMatch(document -> document.handle().equals(session)),
            "No Agreement replica for " + tenant.account);
      }
    }

    private void assertEarly(Tenant tenant, Coordination.Document agreement, String key, String orderOrigin) {
      equal(Set.of(key), obj(state(agreement).get("orders")).keySet(), "One early Order for " + tenant.account);
      equal("selected", entry(agreement, "orders", key).get("status"), "Early selection for " + tenant.account);
      equal(orderOrigin, origin(tenant, agreement, orderPath(key)), "Selected exact Order");
      equal(false, read(tenant, agreement, orderPath(key) + "/activation/active"), "Still awaiting supplier approval");
      equal(null, read(tenant, agreement, orderPath(key) + "/payment"), "Early Order has no PI");
      equal(0L, number(read(tenant, agreement, "/commission/accrued")), "Early Agreement accrues zero commission");
    }

    private void verifyPaid(Tenant tenant, Coordination.Document agreement, String key, String orderOrigin,
        String paymentOrigin, long amount, long commission, Map<String, Object> preparation) throws Exception {
      await("Commission in " + tenant.account, () -> number(read(tenant, agreement, "/commission/accrued")) == commission);
      equal(Set.of(key), obj(state(agreement).get("orders")).keySet(), "One paid Order for " + tenant.account);
      equal(orderOrigin, origin(tenant, agreement, orderPath(key)), "Same Order origin");
      equal(paymentOrigin, origin(tenant, agreement, orderPath(key) + "/payment"), "Same PI origin");
      equal(amount, number(read(tenant, agreement, orderPath(key) + "/payment/payment/completed")), "Native completion");
      equal("usable", entry(agreement, "orders", key).get("status"), "Usable selected Order");
      equal(true, read(tenant, agreement, orderPath(key) + "/activation/approved/seller"), "Seller approval retained");
      equal(true, read(tenant, agreement, orderPath(key) + "/activation/active"), "Dated Order activation retained");
      equal("PENDING", read(tenant, agreement, orderPath(key) + "/orderDecision/status"), "Separate decision stays pending");
      equal(paymentOrigin, read(tenant, agreement, orderPath(key) + "/datedSellerGrant/payment"),
          "Dated approval retains the authorized PI");
      for (Object raw : arr(obj(preparation.get("values")).get("groups"))) {
        var group = obj(raw);
        equal(number(group.get("proposedStartMicros")), number(read(tenant, agreement,
            orderPath(key) + "/reservations/" + required(group, "id") + "/confirmedStartMicros")), "Confirmed service date retained");
      }
      equal(Set.of(key), obj(read(tenant, agreement, "/commission/targets")).keySet(), "One commission target");
      equal(commission, number(read(tenant, agreement, "/commission/targets/" + key)), "Commission for selected Order");
      System.out.println("Agreement " + tenant.account + " stable=" + stableId(agreement) + " completed=" + amount
          + " commission=" + commission + " orderOrigin=" + orderOrigin + " paymentOrigin=" + paymentOrigin);
    }

    private ContractsExecution.Values values(Tenant tenant) {
      return views.computeIfAbsent(tenant, account -> {
        var language = Blue.builder().nodeProvider(account.service.nodeProvider()).build();
        languages.put(account, language);
        return new Contracts(language, RUNTIME).execution().values();
      });
    }

    private Object read(Tenant tenant, Coordination.Document document, String path) {
      return read(tenant, stableId(document), path);
    }

    private Object read(Tenant tenant, String publication, String path) {
      var values = values(tenant);
      var selected = values.select(new Exact.Ref(publication), path);
      return selected == null ? null : values.bexData(selected);
    }

    private String origin(Tenant tenant, Coordination.Document document, String path) {
      return identity(tenant, stableId(document), path + "/contracts/initialized/document");
    }

    private String identity(Tenant tenant, String publication, String path) {
      var values = values(tenant);
      return blue.language.next.NativeRuntime.identity(values.exact(values.select(new Exact.Ref(publication), path)));
    }

    @Override
    public void close() {
      languages.values().forEach(Blue::close);
    }
  }

  private record ProvisionCandidate(String payment, String sourceOrder, String currentOrder) {}

  private record ResellerPackage(String current, String previous, String ordersType, String resource,
      Map<String, Object> metadata) {
    static ResellerPackage current(Path root) throws Exception {
      var release = arr(readFile(root.resolve("PACKAGES.json")).get("packages")).stream().map(Values::obj)
          .filter(row -> "clause-reseller".equals(row.get("name"))).findFirst().orElseThrow();
      var packageData = readFile(root.resolve("clause-reseller/dist/package.json"));
      var imports = map();
      obj(packageData.get("imports")).forEach((prefix, row) -> imports.put(prefix, obj(row).get("packageBlueId")));
      var exports = map();
      arr(packageData.get("exports")).stream().map(Values::obj)
          .forEach(row -> exports.put(required(row, "name"), row.get("blueId")));
      String current = required(release, "packageBlueId");
      String previous = arr(readFile(root.resolve("PACKAGE-SOURCES.json")).get("retainedArchives")).stream()
          .map(Values::obj).filter(row -> required(row, "path").startsWith("retained/reseller-preview.9/"))
          .map(row -> required(row, "packageBlueId")).findFirst().orElseThrow();
      var metadata = map("id", "catalog-order-independent-reseller", "name", "Reseller",
          "version", release.get("version"), "blueId", current, "archiveSha256", release.get("archiveSha256"),
          "imports", imports, "exports", exports);
      return new ResellerPackage(current, previous, required(exports, "Customer Orders Clause"),
          required(release, "path"), metadata);
    }
  }

  private static Coordination.Document initialized(Tenant tenant, String session) throws Exception {
    var document = tenant.service.document(session);
    document.awaitInitialized(WAIT);
    return document;
  }

  private static void processed(Tenant tenant, Coordination.Document document, String entry, String label)
      throws Exception {
    await(label, () -> {
      var progress = document.progress();
      if (progress.status() == Coordination.Status.ERROR || progress.status() == Coordination.Status.HOST_INCOMPLETE) {
        throw new AssertionError(label + " could not publish " + entry + ": " + progress.issue());
      }
      var input = tenant.documents.input(document.handle(), entry);
      if (input.get("assessment") instanceof Map<?, ?> assessment
          && Set.of("REJECTED", "EXECUTION_REJECTED", "NO_MATCH").contains(assessment.get("outcome"))) {
        throw new OperationRejection(label, text(assessment.get("reason")), assessment.get("result"));
      }
      return arr(input.get("localHistory")).stream().map(Values::obj).anyMatch(row -> Boolean.TRUE.equals(row.get("stable")));
    });
    System.out.println("APPLIED " + tenant.account + " " + label + " entry=" + entry);
  }

  private static final class OperationRejection extends AssertionError {
    private final String reason;

    OperationRejection(String label, String reason, Object result) {
      super(label + " rejected: " + reason + " " + result);
      this.reason = reason;
    }
  }

  private static void await(String label, BooleanSupplier condition) throws Exception {
    long deadline = System.nanoTime() + WAIT.toNanos();
    while (System.nanoTime() < deadline) {
      if (condition.getAsBoolean()) return;
      Thread.sleep(50);
    }
    throw new AssertionError("Timed out: " + label);
  }

  private static void requireIndependentAccounts(List<Tenant> tenants) {
    equal(4L, tenants.stream().map(tenant -> tenant.account).distinct().count(), "Distinct account identities");
    equal(4L, tenants.stream().map(tenant -> tenant.store).distinct().count(), "Independent record stores");
    equal(4L, tenants.stream().map(tenant -> tenant.service).distinct().count(), "Independent Coordination runtimes");
  }

  private static String requireSameOrigin(List<Coordination.Document> copies) {
    String initial = copies.getFirst().state().documentId();
    require(initial != null, "Native initialized origin");
    for (var copy : copies) equal(initial, copy.state().documentId(), "Same origin of independent replicas");
    return initial;
  }

  private static Map<String, Object> state(Coordination.Document document) {
    return document.state().stable().orElseThrow().document();
  }

  private static Object field(Coordination.Document document, String container, String key) {
    return obj(state(document).get(container)).get(key);
  }

  private static Map<String, Object> entries(Coordination.Document document, String clause) {
    return obj(obj(state(document).get("process_" + clause)).get("entries"));
  }

  private static Map<String, Object> entry(Coordination.Document document, String clause, String key) {
    return entries(document, clause).values().stream().map(Values::obj)
        .filter(row -> key.equals(row.get("key"))).findFirst().orElseThrow();
  }

  private static Map<String, Object> provision(Map<String, Object> entry, String publication) {
    return map("key", entry.get("key"), "inResponseTo", entry.get("requestId"),
        "requirementRef", entry.get("requirementRef"), "document", ref(publication));
  }

  private static Map<String, Object> readFile(Path file) throws Exception {
    return obj(WireData.json(Files.readString(file)));
  }

  private static Map<String, Object> clausesParameters(Map<String, Object> document, String clause) {
    return obj(obj(obj(document.get("clauses")).get(clause)).get("parameters"));
  }

  private static String stableId(Coordination.Document document) {
    return document.state().stable().orElseThrow().blueId();
  }

  private static String orderPath(String key) {
    return "/orders/" + key;
  }

  private static Map<String, Object> ref(String id) {
    return map("blueId", id);
  }

  private static void equal(Object expected, Object actual, String label) {
    require(Objects.equals(expected, actual), label + " expected=" + expected + " actual=" + actual);
  }

  private static void require(boolean condition, String label) {
    if (!condition) throw new AssertionError(label);
  }
}
