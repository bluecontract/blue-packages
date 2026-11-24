package blue.core;

import static blue.core.Values.*;

import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.coordination.Coordination;
import blue.coordination.ProviderProtocol;
import blue.coordination.ProviderAccessExecution;
import blue.coordination.store.InMemoryRecordStore;
import blue.coordination.store.RecordStore;
import blue.language.next.Blue;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/** Runs the selected Reseller package on native, signed Coordination histories. */
public final class CatalogOrderAttachmentConformance {
  private static final String ORDER = "/orders/checkout-1";
  private static final String PAYMENT = ORDER + "/payment";
  private static final long AMOUNT = 3895;
  private static final long COMMISSION = 390;
  private static final Duration WAIT =
      Duration.ofSeconds(Long.getLong("blue.packages.signedConformanceWaitSeconds", 90L));
  private static final String OWNER = "merchant";
  private static final String ENDPOINT = "https://catalog-order.example.test/provider";

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]).toAbsolutePath().normalize();
    boolean currentGo = args.length > 1;
    var packages = CompositionPackages.published(root,
        root.resolve(currentGo ? "PACKAGES.json" : "retained/pre-declarative-reseller/PACKAGES.json"));
    var secrets = new Secrets(new byte[32]);
    var bindings = QualificationRuntime.bindings();
    try (var store = new InMemoryRecordStore();
         var provider = new TimelineProvider(new Records(store), secrets, ENDPOINT);
         var tenant = new Tenant(OWNER, new InMemoryRecordStore(), secrets, bindings, Telemetry.NOOP);
         var blue = packages.language(tenant.service.nodeProvider());
         var runtime = new AuthoringRuntime(bindings)) {
      var processor = runtime.processor(blue);
      var transport = new ProviderTransport() {
        @Override
        public Response request(String method, String url, String body) {
          require(url.startsWith(ENDPOINT + "/"), "Unexpected provider endpoint");
          String route = url.substring(ENDPOINT.length() + 1);
          try {
            Object response = switch (route) {
              case "provider" -> provider.descriptor();
              case "types" -> provider.types();
              default -> provider.fetch(route, WireData.json(body), null);
            };
            return new Response(200, WireData.write(response));
          } catch (Problem error) {
            return new Response(error.status, WireData.write(map("code", error.code, "message", error.getMessage())));
          }
        }
      };
      var keys = new ReaderKeys(new Records(store), secrets);
      tenant.imports = new TimelineImports(tenant, OWNER, keys, provider, transport, false);
      var scenario = new Scenario(tenant, provider, blue, processor, keys);
      if (currentGo) {
        require(args.length >= 3 && (args.length - 1) % 2 == 0,
            "Provide pairs of exact Go source path and rejection scenario");
        System.out.println("CATALOGUE " + WireData.sha256(Files.readAllBytes(root.resolve("PACKAGES.json"))));
        for (int i = 1; i < args.length; i += 2) scenario.goRejection(Path.of(args[i]), args[i + 1]);
      } else {
        scenario.run(root);
      }
    }
  }

  private static final class Scenario {
    private final Tenant tenant;
    private final TimelineProvider provider;
    private final Blue language;
    private final Contracts processor;
    private final Map<String, String> readers = new LinkedHashMap<>();
    private final Map<String, Participant> fixtureParticipants = new LinkedHashMap<>();
    private int readinessChange;
    private final long proposedStart = Instant.now().plus(Duration.ofDays(7)).getEpochSecond() * 1_000_000;

    Scenario(Tenant tenant, TimelineProvider provider, Blue language, Contracts processor, ReaderKeys keys)
        throws Exception {
      this.tenant = tenant;
      this.provider = provider;
      this.language = language;
      this.processor = processor;
      for (String party : List.of("seller", "partner", "customer", "guarantor")) {
        readers.put(party, required(keys.create(OWNER, party, party), "publicKey"));
      }
    }

    private Participant timeline(String document, String role, String account) throws Exception {
      String name = document + "-" + role;
      var timeline = provider.create(OWNER, name, "catalog-order-" + name);
      var channel = ProviderProtocol.typed(tenant.service.bindings(), "Timeline Channel",
          "timeline", timeline.get("timeline"), "actor", ProviderProtocol.typed("Principal Actor", "displayName", OWNER));
      var accessGrant = provider.changeAccess(OWNER, null, List.of(required(timeline, "id")),
          List.copyOf(readers.values()), "catalog-order-access-" + name, tenant.service.bindings());
      tenant.imports.adoptOwned(timeline);
      IndependentHostedAccessTest.poll(tenant);
      var imported = tenant.imports.importAccess(ENDPOINT, required(accessGrant, "id"));
      var access = tenant.service.document(required(imported, "sessionId"));
      access.awaitInitialized(WAIT);
      var participant = new Participant(channel, readers.get(account), stableId(access),
          required(timeline, "id"), required(accessGrant, "id"));
      fixtureParticipants.put(name, participant);
      return participant;
    }

    void goRejection(Path sourcePath, String mode) throws Exception {
      require(Set.of("plain-after-secure", "plain-before-secure", "timed-reject-first", "timed-cancel-first",
          "timed-typed-pi-init", "timed-late-refund", "timed-confirm-funding", "timed-accept-alternative",
          "timed-cancellation-service-refresh", "timed-payment-admission", "timed-late-refund-before-payout", "timed-late-refund-after-payout",
          "timed-late-refund-during-payout", "timed-late-refund-order-readiness",
          "timed-late-refund-agreement-readiness", "timed-late-refund-after-payout-agreement-readiness",
          "timed-late-refund-agreement-reapprove", "timed-late-refund-payout-recover-access",
          "timed-late-refund-payout-recover-terms", "timed-late-refund-payout-completion-only",
          "timed-finance-amendment-freeze").contains(mode),
          "Unknown Go rejection scenario " + mode);
      byte[] sourceBytes = Files.readAllBytes(sourcePath);
      var source = obj(WireData.json(new String(sourceBytes, java.nio.charset.StandardCharsets.UTF_8)));
      var profile = obj(source.get("template"));
      equal("catalogue-agreement-authoring", profile.get("id"), "Exact Go source profile");
      require(Set.of("15", "16", "17").contains(profile.get("version")), "Supported baseline or revised Go fixture profile");
      var template = obj(source.get("orderTemplate"));
      boolean timed = mode.startsWith("timed-");
      boolean initOnly = mode.equals("timed-typed-pi-init");
      boolean lateRefund = mode.startsWith("timed-late-refund");
      boolean reviewAlternative = mode.equals("timed-accept-alternative");
      boolean serviceRefresh = mode.equals("timed-cancellation-service-refresh");
      boolean paymentAdmission = mode.equals("timed-payment-admission");
      boolean reviewFunding = mode.equals("timed-confirm-funding") || reviewAlternative || serviceRefresh;
      equal(timed, obj(template.get("clauses")).containsKey("cancellation"), "Requested commercial policy");
      if (timed) {
        var capture = obj(obj(paymentInstruction(template).get("clauses")).get("payment"));
        var parameters = obj(capture.get("parameters"));
        var policy = obj(parameters.get("capture"));
        required(obj(policy.get("type")), "blueId");
        equal("cancellation", policy.get("blockedBy"), "Typed capture policy refers to the authored adjustment");
        var adjustment = obj(obj(parameters.get("adjustments")).get("cancellation"));
        equal(map("path", "/sources/order/cancellationDecision", "when", map("field", "status", "equals", "accepted"),
            "retainMinorFrom", "retainedMinor"), adjustment.get("decision"), "Typed cancellation decision input");
      }
      if (lateRefund) {
        var clauses = obj(template.get("clauses"));
        var policy = obj(obj(clauses.get("cancellation")).get("parameters"));
        equal(0L, number(policy.get("freeCancellationHoursAfterStart")), "Immediate expiry in the qualification case");
        equal(25L, number(policy.get("lateCancellationChargePercent")), "Declared 25 percent late fee");
        var clock = obj(obj(clauses.get("windowStart")).get("bindings"));
        equal(map("activation", map("on", "activated")), clock.get("startFromEntry"), "Native primary is declarative");
        require(!WireData.write(clock).contains("\"$"), "Authored clock bindings contain no BEX");
      }
      equal(List.of("seller"), activationParameters(template).get("required"), "Supplier approves the original sale");
      System.out.println("SOURCE " + mode + " " + WireData.sha256(sourceBytes));
      bindGoFixtureAccounts(source, template);
      if (lateRefund) obj(source.get("terms")).put("payoutOperatorAccountId", "guarantor");

      var agreement = bootstrap(mode + "-agreement", source, Map.of("partner", "partner", "seller", "seller"));
      acceptTerms(agreement, "seller");
      acceptTerms(agreement, "partner");
      var items = obj(obj(source.get("products")).get("entries"));
      String sku = items.keySet().iterator().next();
      var selection = map("customerEmail", "buyer@example.test", "catalogRevision", 1,
          "lines", List.of(map("itemId", sku, "quantity", 1)));
      boolean dated = false;
      if (template.containsKey("reservationPolicy")) {
        var terms = obj(template.get("reservationPolicy"));
        var group = map("id", "booking-1", "lineIndices", List.of(0));
        dated = Boolean.TRUE.equals(terms.get("dateRequired"));
        if (dated) group.put("proposedStartMicros", proposedStart);
        selection.put("groups", List.of(group));
      }
      if (reviewFunding) {
        require(dated, "Funding qualification requires a dated Order");
        var reservation = obj(obj(template.get("clauses")).get("reservation"));
        var groups = obj(obj(reservation.get("parameters")).get("conditionGroups"));
        required(obj(obj(groups.get("fundedReview")).get("type")), "blueId");
        if (reviewAlternative) {
          var reviewed = obj(obj(activationParameters(template).get("reviewedApprovals")).get("seller"));
          equal("booking-1", obj(reviewed.get("event")).get("subject"),
              "Ordinary Go artifact declares Activation as the owner of reviewed booking approval");
          require(!obj(reservation.get("parameters")).containsKey("reviewedSellerActivation"),
              "Schedule no longer owns commercial approval");
        }
      }
      call(agreement, "prepareOrder", map("type", "Documents/Preparation Input", "key", "checkout-1",
          "requestId", "basket-1", "values", selection));
      var entry = onlyPreparation(agreement, "/process_orders");
      if (mode.equals("timed-finance-amendment-freeze")) {
        verifyFrozenCommission(agreement, entry, selection, sku);
        return;
      }
      if (lateRefund) {
        equal(1250L, number(read(agreement, required(entry, "itemPath") + "/domainTerms/commissionTerms/commissionBps")),
            "Private commission rate is frozen on the Agreement admission entry");
        equal(null, read(agreement, required(entry, "itemPath") + "/prepared/commissionTerms"),
            "Private commission rate is not a prepared Order field");
      }
      var order = bootstrap(mode + "-order", prepared(agreement, entry),
          Map.of("customer", "customer", "partner", "partner", "seller", "seller"));
      long amount = number(read(order, "/amountMinor"));
      require(amount >= 50, "The original Order must qualify for a full card authorization");
      equal("USD", read(order, "/currency"), "Fixture currency");
      equal(false, read(order, "/activation/active"), "Seller approval remains pending");
      if (!timed) {
        equal(null, read(order, "/customerAccountId"), "Email bootstrap needs no duplicate buyer identity");
        customerIdentityRules(agreement);
      }
      call(agreement, "provideOrder", provision(entry, stableId(order)));
      String providerReference = "pi_fixture_" + mode;
      call(order, "preparePayment", map("providerReference", providerReference));
      var piEntry = onlyPreparation(order, "/process_payment");
      var payment = bootstrap(mode + "-payment", prepared(order, piEntry),
          Map.of("payer", "customer", "payee", "seller", "observer", "partner", "guarantor", "guarantor"));
      String orderOrigin = identityAt(order, "/contracts/initialized/document");
      String paymentOrigin = identityAt(payment, "/contracts/initialized/document");
      equal(orderOrigin, identityAt(payment, "/sources/order/contracts/initialized/document"), "Original PI source");
      if (lateRefund) {
        equal(null, read(order, "/commissionTerms"), "Original Order has no private commission terms");
        equal(null, read(payment, "/commissionTerms"), "Original PI has no private commission terms");
      }
      if (initOnly) {
        var gate = read(payment, "/paymentTerms/captureGate");
        require(gate instanceof String path && path.startsWith("/"), "Native capture gate installed");
        equal(false, read(payment, (String) gate), "Capture gate remains closed before Payment Instruction selection");
        System.out.println("PASS " + mode + " order=" + orderOrigin + " payment=" + paymentOrigin + " gate=" + gate);
        return;
      }
      if (paymentAdmission) {
        verifyPaymentAdmission(order, piEntry, payment, amount);
        return;
      }
      call(order, "providePayment", provision(piEntry, stableId(payment)));
      equal(paymentOrigin, identityAt(order, "/payment/contracts/initialized/document"), "Selected original PI");
      call(payment, "acceptPaymentInstruction", map());
      String session = "customer-session-" + mode;
      call(payment, "provideSession", map("type", "MyOS/Customer Session Input", "sessionId", session));
      call(payment, "confirmFunding", map("sessionId", session));
      call(payment, "recordTransactionInitiated", map("type", "PaymentInstruction/Transaction Initiation Input",
          "transactionId", "held-" + mode, "railType", "stripe", "attachmentPoint", "instruction",
          "providerReference", providerReference));
      var fundingReview = reviewFunding ? fundingConfirmation(order) : Map.<String, Object>of();
      var alternative = reviewAlternative ? widerAlternative(order, obj(source.get("products")), sku) : Map.<String, Object>of();
      if (reviewFunding) {
        equal(0L, number(read(payment, "/payment/secured")), "Selected PI has no confirmed hold");
        var refusedEntry = call(order, "confirmReservation", fundingReview, true);
        require(refusedEntry != null, "Real seller route refused the signed unfunded confirmation");
        equal("pending_supplier", read(order, "/wholeOrderReservation/status"), "Unfunded booking stays pending");
        equal(false, read(order, "/activation/active"), "Unfunded review cannot activate the Order");
        equal(null, read(payment, "/payment/requests/order-accepted-capture/status"),
            "Unfunded review cannot request capture");
        System.out.println("PASS signed confirmation refused before the original hold, entry=" + refusedEntry);
        if (reviewAlternative) {
          var refusedAlternative = call(order, "proposeAlternative", alternative, true);
          require(refusedAlternative != null, "Signed same-price alternative still requires current selected funding");
          equal(fundingReview, fundingConfirmation(order), "Unfunded alternative keeps the exact original proposal");
          equal(null, read(order, "/activation/reviewedGrants/seller"), "Unfunded alternative creates no grant");
          System.out.println("PASS T10 signed broader alternative refused before the original hold, entry=" + refusedAlternative);
        }
      }
      call(payment, "authorize", map("type", "PaymentInstruction/Payment Request Input", "requestId", "original-hold",
          "amountMinor", amount));
      boolean rejectBeforeSecure = mode.equals("plain-before-secure");
      var sellerDecision = map("revision", read(order, "/activation/revision"));
      if (rejectBeforeSecure) {
        call(order, "rejectOrder", sellerDecision);
        equal(Set.of("original-hold"), obj(read(payment, "/payment/requests")).keySet(), "Pending hold has no void yet");
      }
      call(payment, "secureFunds", map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "original-hold",
          "amountSecured", amount));
      if (reviewFunding) {
        equal(amount, number(read(order, "/payment/payment/secured")), "Order sees the selected confirmed hold");
        equal(fundingReview, fundingConfirmation(order), "Reviewed confirmation inputs are unchanged after SECURE");
        require(call(order, "approve_seller", sellerDecision, true) != null,
            "The direct seller approval route cannot bypass a funded exact booking review");
        long acceptedStart = proposedStart;
        if (reviewAlternative) {
          acceptedStart = verifyReviewedAlternative(order, payment, alternative, sku, amount);
        } else {
          call(order, "confirmReservation", fundingReview);
        }
        equal("confirmed", read(order, "/wholeOrderReservation/status"), "Funded seller confirms the booking");
        equal(acceptedStart, number(read(order, "/wholeOrderReservation/confirmedStartMicros")),
            "The reviewed booking keeps the exact accepted time");
        equal(true, read(order, "/activation/active"), "Funded booking activates the Order");
        equal(true, read(order, "/activation/approved/seller"), "Activation records the seller approval");
        var capture = "/payment/requests/order-accepted-capture";
        equal("pending", read(payment, capture + "/status"), "Selected PI requests capture after confirmation");
        equal(amount, number(read(payment, capture + "/intent/amountMinor")), "Capture matches the reviewed original amount");
        equal(Set.of("original-hold", "order-accepted-capture"), obj(read(payment, "/payment/requests")).keySet(),
            "One hold and one capture on the selected instruction");
        if (serviceRefresh) verifyServiceRefresh(template, order, payment, acceptedStart, amount);
        System.out.println("PASS " + mode + " order=" + orderOrigin + " payment=" + paymentOrigin
            + " amountMinor=" + amount + " serviceStartMicros=" + acceptedStart + " requestedCapture=1");
        return;
      }
      if (lateRefund) {
        verifyLateRefund(agreement, order, payment, sellerDecision, sku, mode);
        return;
      }
      var cancellation = map("key", "terminal-cancellation", "reason", "The customer cancels this Order");
      boolean cancellationFirst = mode.equals("timed-cancel-first");
      String voidRequest = cancellationFirst ? "order-cancellation-void" : "order-rejected-void";
      if (timed) {
        equal("available", read(order, "/cancellationAvailability/status"), "Pending original Order offers cancellation");
        equal(true, read(order, "/cancellationAvailability/beforeConfirmation"), "Cancellation is free pending seller approval");
      }
      if (!rejectBeforeSecure) {
        equal(amount, number(read(payment, "/payment/secured")), "Full native hold exists before the terminal decision");
        if (cancellationFirst) {
          String cancellationEntry = call(order, "cancelOrder", cancellation);
          if (dated) verifyTimedReservationClosure(order, orderOrigin, cancellationEntry, cancellation.get("reason"));
        } else call(order, "rejectOrder", sellerDecision);
      }
      assertOnlyVoid(payment, voidRequest, amount);
      if (cancellationFirst) {
        call(order, "rejectOrder", sellerDecision, true);
        equal("accepted", read(order, "/cancellationDecision/status"), "Native cancellation remains terminal");
        call(order, "cancelOrder", cancellation);
      } else {
        if (timed) {
          equal("unavailable", read(order, "/cancellationAvailability/status"), "Native rejected Order hides cancellation");
          equal("order_closed", read(order, "/cancellationAvailability/reason"), "Native cancellation unavailability reason");
          require(call(order, "cancelOrder", cancellation, true) != null,
              "The actual signed customer operation is rejected after seller rejection");
          require(call(order, "cancelBySupplier", cancellation, true) != null,
              "The actual signed supplier operation is rejected after seller rejection");
        }
        equal("REJECTED", read(order, "/orderDecision/status"), "Native seller decision remains terminal");
        equal(null, read(order, "/cancellationDecision/status"), "No second terminal cancellation decision");
        call(order, "rejectOrder", sellerDecision);
      }
      call(order, "approve_seller", sellerDecision, true);
      equal(false, read(order, "/activation/active"), "Terminal Order cannot be approved");
      assertOnlyVoid(payment, voidRequest, amount);
      call(payment, "cancelBeforeCompletion", map("type", "PaymentInstruction/Payment Outcome Input", "requestId", voidRequest));
      equal("succeeded", read(payment, "/payment/requests/" + voidRequest + "/status"), "One reported native void outcome");
      equal(0L, number(read(payment, "/payment/secured")), "Full hold released");
      assertOnlyVoid(payment, voidRequest, amount);
      if (timed && !cancellationFirst) {
        equal("unavailable", read(order, "/cancellationAvailability/status"), "Cancellation stays unavailable after void");
        equal(null, read(order, "/cancellationDecision/status"), "No cancellation decision after confirmed hold release");
      }
      equal(0L, number(read(agreement, "/commission/accrued")), "No captured proceeds or commission");
      System.out.println("PASS " + mode + " order=" + orderOrigin + " payment=" + paymentOrigin + " sku=" + sku
          + " amountMinor=" + amount + " request=" + voidRequest + " captureMinor=0 refundMinor=0");
    }

    private Map<String, Object> fundingConfirmation(Coordination.Document order) {
      return map("key", "dated-funding-review", "groupId", "booking-1",
          "expectedProposalBlueId", read(order, "/reservations/booking-1/proposalBlueId"));
    }

    private void verifyServiceRefresh(Map<String, Object> template, Coordination.Document order,
        Coordination.Document payment, long start, long amount) throws Exception {
      var clauses = obj(template.get("clauses"));
      require(!clauses.containsKey("windowStart"), "T01 exercises service-only without an elapsed clock trigger");
      var policy = obj(obj(clauses.get("cancellation")).get("parameters"));
      long advance = Duration.ofHours(number(policy.get("freeCancellationHoursBeforeStart"))).toSeconds() * 1_000_000;
      String availability = "/cancellationAvailability";
      System.out.println("T01 observed booking=confirmed start=" + start + " activation=active beforeConfirmation="
          + read(order, availability + "/beforeConfirmation") + " freeUntil="
          + read(order, availability + "/freeCancellationUntilMicros"));
      equal(false, read(order, availability + "/beforeConfirmation"), "T01 seller confirmation replaces the initial exemption");
      equal(start - advance, number(read(order, availability + "/freeCancellationUntilMicros")),
          "T01 Schedule confirmation sets the exact service-only cutoff in the same native result");
      equal(start - 1, number(read(order, availability + "/lastCancellationMicros")), "T01 ordinary cancellation ends before service");
      equal(true, read(order, availability + "/lateCancellationAwaitingCapture"), "T02 awaiting original capture");
      call(payment, "completePayment", map("type", "PaymentInstruction/Payment Outcome Input",
          "requestId", "order-accepted-capture", "amountCompleted", amount));
      equal(amount, number(read(payment, "/payment/completed")), "T02 confirmed original PI outcome");
      equal(false, read(order, availability + "/lateCancellationAwaitingCapture"),
          "T02 selected PI completion wakes Order availability without a parent operation");
      equal(true, read(order, availability + "/retentionReady"), "T02 availability reflects the selected captured basis");
      equal(start - advance, number(read(order, availability + "/freeCancellationUntilMicros")), "T02 cutoff unchanged");
      equal(null, read(order, "/cancellationDecision/status"), "Projection does not create a cancellation decision");
      System.out.println("PASS T01/T02 service-only confirmation and selected capture refresh without a parent patch");
    }

    private void verifyPaymentAdmission(Coordination.Document order, Map<String, Object> requirement,
        Coordination.Document original, long amount) throws Exception {
      var wrongSource = prepared(order, requirement);
      wrongSource.put("name", "Other same-price PI");
      obj(wrongSource.get("paymentDetails")).put("providerReference", "pi_other_fixture");
      var foreign = bootstrap("timed-payment-admission-other", wrongSource,
          Map.of("payer", "customer", "payee", "seller", "observer", "partner", "guarantor", "guarantor"));
      equal(amount, number(read(foreign, "/paymentTerms/amountMinor")), "Foreign PI is genuinely the same price");
      equal(read(original, "/paymentTerms/currency"), read(foreign, "/paymentTerms/currency"), "Foreign PI has the same currency");
      require(!identityAt(original, "/contracts/initialized/document").equals(identityAt(foreign, "/contracts/initialized/document")),
          "T11 exercises two independent native PI origins");
      var snapshot = read(order, "/process_payment/entries");
      var wrongRequest = provision(requirement, stableId(original));
      wrongRequest.put("inResponseTo", "different-order-request");
      var wrongRequirement = provision(requirement, stableId(original));
      wrongRequirement.put("requirementRef", ref(stableId(foreign)));
      var wrongCandidate = provision(requirement, stableId(foreign));
      requireRefusedPaymentAdmission(order, snapshot, wrongRequest, "wrong request");
      requireRefusedPaymentAdmission(order, snapshot, wrongRequirement, "wrong requirement");
      requireRefusedPaymentAdmission(order, snapshot, wrongCandidate, "same-price foreign original");
      call(order, "providePayment", provision(requirement, stableId(original)));
      var originalOrigin = identityAt(original, "/contracts/initialized/document");
      equal(originalOrigin, identityAt(order, "/payment/contracts/initialized/document"), "Original exact PI was selected");
      var selected = read(order, "/process_payment/entries");
      require(call(order, "providePayment", wrongCandidate, true) != null, "Selected PI cannot be exchanged for foreign same-priced candidate");
      equal(selected, read(order, "/process_payment/entries"), "Invalid reselection leaves exact committed obligation intact");
      equal(originalOrigin, identityAt(order, "/payment/contracts/initialized/document"), "The selected original managed PI remains");
      System.out.println("PASS T11 signed providePayment rejects wrong request, wrong requirement and same-price foreign candidate; original="
          + originalOrigin + " selected unchanged after retrying foreign admission");
    }

    private void requireRefusedPaymentAdmission(Coordination.Document order, Object snapshot,
        Map<String, Object> request, String mismatch) throws Exception {
      require(call(order, "providePayment", request, true) != null, "Signed providePayment rejects " + mismatch);
      equal(snapshot, read(order, "/process_payment/entries"), "Refused admission preserves the pending exact obligation");
      equal(null, read(order, "/payment"), "Refused candidate does not attach");
      System.out.println("T11 native refusal for " + mismatch + " preserved the original pending obligation");
    }

    private Map<String, Object> widerAlternative(Coordination.Document order, Map<String, Object> catalogue, String sku) {
      var product = new LinkedHashMap<>(obj(obj(catalogue.get("entries")).get(sku)));
      long unitPrice = number(product.get("unitAmountMinor"));
      require(unitPrice % 2 == 0, "The rental fixture allows an exact same-price two-unit alternate");
      product.put("unitAmountMinor", unitPrice / 2);
      var updatedCatalogue = new LinkedHashMap<>(catalogue);
      String changedSku = sku + "-alternate";
      updatedCatalogue.put("entries", map(changedSku, product));
      return map("key", "seller-alternative", "groupId", "booking-1",
          "expectedProposalBlueId", read(order, "/reservations/booking-1/proposalBlueId"), "catalog", updatedCatalogue,
          "lines", List.of(map("itemId", changedSku, "quantity", 2)),
          "proposedStartMicros", proposedStart + Duration.ofDays(1).getSeconds() * 1_000_000);
    }

    private long verifyReviewedAlternative(Coordination.Document order, Coordination.Document payment,
        Map<String, Object> alternative, String sku, long amount) throws Exception {
      var group = "/reservations/booking-1";
      var revision = read(order, "/activation/revision");
      var terms = read(order, "/activation/terms/ref");
      var original = read(order, group + "/proposalBlueId");
      var purchaseSnapshot = read(order, "/orderSnapshot");
      equal(sku, read(order, "/orderSnapshot/quote/lines/0/itemId"), "Frozen purchase has the original catalogue item");
      equal(1L, number(read(order, "/orderSnapshot/quote/lines/0/quantity")), "Frozen purchase has the original quantity");
      long newStart = number(alternative.get("proposedStartMicros"));
      call(order, "proposeAlternative", alternative);
      equal("pending_customer", read(order, group + "/status"), "A signed alternative awaits the buyer");
      equal(false, read(order, "/activation/active"), "A proposed alternative gives no final consent");
      equal(null, read(payment, "/payment/requests/order-accepted-capture/status"), "No capture before the buyer review");
      var updated = read(order, group + "/proposalBlueId");
      require(updated != null && !updated.equals(original), "Alternative has a new exact proposal identity");
      equal(2L, number(read(order, group + "/proposal/number")), "Alternative advances the proposal only once");
      equal(amount, number(read(order, group + "/proposal/amountMinor")), "Alternative preserves the original price");
      equal(sku + "-alternate", read(order, group + "/proposal/quote/lines/0/itemId"), "Alternative contains a different item at the same price");
      equal(2L, number(read(order, group + "/proposal/quote/lines/0/quantity")), "Alternative contains a different quantity");
      equal(newStart, number(read(order, group + "/proposal/proposedStartMicros")), "Alternative retains the proposed time");
      require(call(order, "acceptProposal", map("key", "accept-alternative", "groupId", "booking-1",
          "expectedProposalBlueId", original), true) != null, "A stale signed acceptance is refused");
      equal("pending_customer", read(order, group + "/status"), "Rejecting stale review preserves booking state");
      equal(false, read(order, "/activation/active"), "Stale review does not activate the Order");
      var accepted = call(order, "acceptProposal", map("key", "accept-alternative", "groupId", "booking-1",
          "expectedProposalBlueId", updated));
      equal(updated, read(order, group + "/proposalBlueId"), "The buyer accepts the exact retained alternative");
      equal(revision, read(order, "/activation/revision"), "The same commercial revision remains in force");
      equal(terms, read(order, "/activation/terms/ref"), "The same commercial terms remain in force");
      equal(amount, number(read(order, "/amountMinor")), "The original Order authority keeps its price");
      equal(purchaseSnapshot, read(order, "/orderSnapshot"), "The original prepared purchase snapshot remains immutable");
      System.out.println("PASS signed buyer accepted exact alternative entry=" + accepted + " proposal=" + updated);
      System.out.println("PASS T10 same-price SKU and quantity change accepted while the original purchase snapshot remained intact");
      return newStart;
    }

    private void verifyTimedReservationClosure(Coordination.Document order, String origin, String entry, Object reason) {
      equal("cancelled", read(order, "/wholeOrderReservation/status"), "Stock booking closes from the signed cancellation");
      equal(reason, read(order, "/cancellationDecision/reason"), "Immutable decision retains the signed reason");
      var observed = tenant.documents.input(order.handle(), entry);
      var history = arr(observed.get("localHistory")).stream().map(Values::obj).toList();
      var events = tenant.documents.epochEvents(order.handle(), origin, history, new LinkedHashMap<>());
      var values = processor.execution().values();
      var closed = arr(events.get("emitted")).stream()
          .map(Values::obj).map(ref -> new Exact.Ref(required(ref, "blueId")))
          .map(ref -> obj(values.bexData(ref)))
          .filter(event -> "Reservation Changed".equals(event.get("kind")) && "cancelled".equals(event.get("status")))
          .toList();
      equal(1, closed.size(), "One recorded booking closure");
      equal("booking-1", closed.getFirst().get("groupId"), "Whole order booking group closed");
      equal(reason, closed.getFirst().get("reason"), "Booking closure retains the signed customer's reason");
      System.out.println("PASS dated reservation closed with the exact signed customer reason");
    }

    private void verifyFrozenCommission(Coordination.Document agreement, Map<String, Object> original,
        Map<String, Object> selection, String sku) throws Exception {
      String oldPath = required(original, "itemPath");
      equal(7200L, financeAmount(agreement, oldPath + "/prepared/amountMinor"), "Original discounted price");
      equal(1250L, financeAmount(agreement, oldPath + "/domainTerms/commissionTerms/commissionBps"), "Original frozen rate");
      var originalPrepared = identityAt(agreement, oldPath + "/prepared");
      call(agreement, "proposeCommission_seller", map("type", "Amendments/Amendment Input", "proposalId", "new-commission",
          "path", "/terms/commissionBps", "expectedRevision", 1, "replacement", 1375));
      call(agreement, "approveCommission_seller", map("proposalId", "new-commission"));
      equal(1250L, financeAmount(agreement, "/terms/commissionBps"), "One party cannot change the commission");
      call(agreement, "approveCommission_partner", map("proposalId", "new-commission"));
      equal(1375L, financeAmount(agreement, "/terms/commissionBps"), "Both parties change the commission");

      var catalog = obj(WireData.json(WireData.write(read(agreement, "/products"))));
      catalog.put("revision", 2);
      obj(obj(catalog.get("entries")).get(sku)).put("label", "Amended catalogue label");
      call(agreement, "proposeCatalog", map("type", "Amendments/Amendment Input", "proposalId", "new-catalogue",
          "path", "/products", "expectedRevision", 1, "replacement", catalog));
      call(agreement, "approveCatalog_seller", map("proposalId", "new-catalogue"));
      equal(1L, financeAmount(agreement, "/products/revision"), "One party cannot change the catalogue");
      call(agreement, "approveCatalog_partner", map("proposalId", "new-catalogue"));
      equal(2L, financeAmount(agreement, "/products/revision"), "Both parties change the catalogue");

      call(agreement, "prepareOrder", map("type", "Documents/Preparation Input", "key", "checkout-1",
          "requestId", "basket-1", "values", selection));
      equal(originalPrepared, identityAt(agreement, oldPath + "/prepared"), "Retry preserves the exact old prepared document");
      equal(original, read(agreement, oldPath), "Retry preserves the full original admission entry and private terms");
      var laterSelection = new LinkedHashMap<>(selection);
      laterSelection.put("catalogRevision", 2);
      call(agreement, "prepareOrder", map("type", "Documents/Preparation Input", "key", "checkout-2",
          "requestId", "basket-2", "values", laterSelection));
      var entries = obj(read(agreement, "/process_orders/entries"));
      equal(2, entries.size(), "Only two unique preparations exist");
      var later = entries.values().stream().map(Values::obj).filter(entry -> "checkout-2".equals(entry.get("key"))).findFirst().orElseThrow();
      String newPath = required(later, "itemPath");
      equal(7200L, financeAmount(agreement, newPath + "/prepared/amountMinor"), "Same checkout value on revised catalogue");
      equal(1375L, financeAmount(agreement, newPath + "/domainTerms/commissionTerms/commissionBps"), "Only the new entry uses new rate");
      equal(null, read(agreement, newPath + "/prepared/commissionTerms"), "Commission remains private");
      System.out.println("PASS signed bilateral amendments and retry retain exact old 1250 bps while new Order at 7200 freezes 1375");
    }

    private void verifyLateRefund(Coordination.Document agreement, Coordination.Document order,
        Coordination.Document payment, Map<String, Object> sellerDecision, String sku, String mode) throws Exception {
      String capture = "order-accepted-capture";
      String refund = "order-cancellation-refund";
      String refundPath = "/payment/requests/" + refund;
      long amount = 7200, released = 5400, retained = 1800;
      equal(amount, number(read(payment, "/payment/secured")), "Full original hold");
      equal(0L, number(read(payment, "/payment/completed")), "Sale still awaits seller");
      receipts(agreement, 0, 0, 0);
      accrued(agreement, 0);
      call(order, "approve_seller", sellerDecision);
      require(number(read(order, "/clockStartMicros")) > 0, "Actual seller approval supplies native clock");
      equal("pending", read(payment, "/payment/requests/" + capture + "/status"), "Selected PI requests automatic capture");
      equal(amount, number(read(payment, "/payment/requests/" + capture + "/intent/amountMinor")), "Full selected capture");
      receipts(agreement, 0, 0, 0);
      accrued(agreement, 0);
      var completed = map("type", "PaymentInstruction/Payment Outcome Input", "requestId", capture, "amountCompleted", amount);
      call(payment, "completePayment", completed);
      equal(amount, number(read(order, "/payment/payment/completed")), "Original capture reached owning Order");
      awaitFinanceState(agreement, "/commission/accrued", 900L);
      receipts(agreement, 7200, 0, 7200);
      ledger(agreement, 900, 0, 0);
      call(payment, "completePayment", completed);
      receipts(agreement, 7200, 0, 7200);
      ledger(agreement, 900, 0, 0);
      equal(Set.of("checkout-1"), obj(read(agreement, "/receipts/targets")).keySet(), "One captured receipt target");
      equal(Set.of("checkout-1"), obj(read(agreement, "/commission/targets")).keySet(), "One accrued commission target");
      System.out.println("PASS signed hold and pending capture produce no receipts; confirmed 7200 and commission 900 once");

      if (mode.contains("-payout-recover-") || mode.endsWith("-completion-only")) {
        verifyPayoutRecovery(agreement, order, payment, mode);
        return;
      }
      boolean reapprove = mode.endsWith("agreement-reapprove");
      boolean paidFirst = mode.endsWith("after-payout") || mode.endsWith("after-payout-agreement-readiness");
      boolean reservedFirst = mode.endsWith("during-payout");
      Coordination.Document payout = null;
      if (paidFirst || reservedFirst) {
        payout = prepareCommissionPayout(agreement, mode, paidFirst);
        if (paidFirst) confirmCommissionPayout(agreement, payout, 900, true);
      }

      var cancellation = map("key", "late-cancellation", "reason", "Customer requests a late cancellation");
      call(order, "cancelOrder", cancellation);
      equal("accepted", read(order, "/cancellationDecision/status"), "Accepted late cancellation");
      require(number(read(order, "/cancellationDecision/timestampMicros")) > number(read(order, "/clockStartMicros")),
          "Cancellation happened after the zero-hour deadline");
      equal(retained, number(read(order, "/cancellationDecision/retainedMinor")), "25 percent retained");
      equal(released, number(read(order, "/cancellationDecision/releasedMinor")), "75 percent released");
      equal("pending", read(payment, refundPath + "/status"), "Only the provider outcome confirms the refund");
      equal("refund", read(payment, refundPath + "/intent/action"), "Typed adjustment requests a refund");
      equal(released, number(read(payment, refundPath + "/intent/amountMinor")), "Exact refund amount");
      equal(0L, number(read(payment, "/payment/reversed")), "Pending request has no financial effect");
      receipts(agreement, 7200, 0, 7200);
      ledger(agreement, 900, paidFirst ? 900 : 0, reservedFirst ? 900 : 0);
      var requests = new java.util.LinkedHashSet<>(Set.of("original-hold", capture, refund));
      equal(requests, obj(read(payment, "/payment/requests")).keySet(), "One refund without a second capture or VOID");
      var decision = read(order, "/cancellationDecision");
      call(order, "cancelOrder", cancellation);
      equal(decision, read(order, "/cancellationDecision"), "Signed retry preserves the accepted decision");
      equal(requests, obj(read(payment, "/payment/requests")).keySet(), "Signed retry preserves the one refund request");

      boolean manuallyRecovered = mode.endsWith("before-payout");
      String confirmedRefund = manuallyRecovered ? "manual-refund-attempt" : refund;
      Object failedAttempt = null;
      if (manuallyRecovered) {
        var manualRequest = map("type", "PaymentInstruction/Payment Request Input", "requestId", confirmedRefund,
            "amountMinor", released);
        call(payment, "recordPaymentReversalUnknown", map("type", "PaymentInstruction/Payment Outcome Input",
            "requestId", refund, "reason", "Awaiting the provider result"));
        equal("unknown", read(payment, refundPath + "/status"), "Original refund remains unresolved");
        require(call(payment, "refund", manualRequest, true) != null,
            "The payee cannot spend the funds still reserved by the unresolved refund");
        call(payment, "failReverseAfterCompletion", map("type", "PaymentInstruction/Payment Outcome Input",
            "requestId", refund, "reason", "Provider confirmed failure"));
        equal("failed", read(payment, refundPath + "/status"), "First attempt is terminal");
        failedAttempt = read(payment, refundPath);
        call(order, "cancelOrder", cancellation);
        equal(requests, obj(read(payment, "/payment/requests")).keySet(), "Decision replay does not create a retry");
        receipts(agreement, 7200, 0, 7200);
        accrued(agreement, 900);
        call(payment, "refund", manualRequest);
        requests.add(confirmedRefund);
        equal("pending", read(payment, "/payment/requests/" + confirmedRefund + "/status"), "Payee starts a new attempt");
        receipts(agreement, 7200, 0, 7200);
      }

      var suspended = mode.endsWith("order-readiness") ? order
          : mode.endsWith("agreement-readiness") ? agreement : null;
      if (suspended != null) setReadiness(suspended, false);
      var orderEntry = required(onlyPreparation(agreement, "/process_orders"), "itemPath");
      var missedReceipts = reapprove ? recoverySignals(agreement) : null;
      if (reapprove) {
        require(missedReceipts.get("activated") > 0 && missedReceipts.get("attached") > 0,
            "Native receipt history sees first activation and original attachment");
        requireFreshApproval(agreement);
      }
      var refunded = map("type", "PaymentInstruction/Payment Outcome Input", "requestId", confirmedRefund,
          "amountReversed", released);
      call(payment, "reverseAfterCompletion", refunded);
      equal("succeeded", read(payment, "/payment/requests/" + confirmedRefund + "/status"), "Native guarantor confirmed refund");
      if (manuallyRecovered) {
        equal(failedAttempt, read(payment, refundPath), "Manual retry does not rewrite the failed request");
        equal(decision, read(order, "/cancellationDecision"), "Manual retry retains the accepted decision");
        System.out.println("PASS signed payee retry confirms 5400 with original failed attempt and decision preserved");
      }
      equal(amount, number(read(payment, "/payment/completed")), "Original capture remains in history");
      equal(released, number(read(payment, "/payment/reversed")), "Confirmed refund on the selected PI");
      equal(requests, obj(read(payment, "/payment/requests")).keySet(), "No additional financial request");
      if (suspended != null) {
        equal(false, read(suspended, "/activation/active"), "Provider confirmation does not bypass access");
        receipts(agreement, 7200, 0, 7200);
        ledger(agreement, 900, paidFirst ? 900 : 0, reservedFirst ? 900 : 0);
        setReadiness(suspended, true);
      }
      if (reapprove) {
        equal(true, read(order, "/activation/active"), "The independent sale Order stays active");
        equal(true, read(agreement, "/activation/accessReady"), "Agreement access stayed ready during the refund");
        equal(5400L, financeAmount(order, "/payment/payment/reversed"), "The sale Order received the original refund");
        receipts(agreement, 7200, 0, 7200);
        ledger(agreement, 900, 0, 0);
        resumeApprovedTerms(agreement, 900, 0, 0);
        equal(missedReceipts, recoverySignals(agreement), "Neither access restoration nor attachment caused recovery");
        equal("usable", read(agreement, orderEntry + "/status"), "The original Order remains usable");
        awaitFinanceState(agreement, PAYMENT + "/payment/reversed", 5400L);
        System.out.println("OBSERVED F01 after reapprovals, no access/attach signal: net="
            + financeAmount(agreement, "/receipts/netReceivedMinor") + " accrued=" + financeAmount(agreement, "/commission/accrued"));
      }
      if (reapprove) awaitRecoveredFinanceState(agreement, "/receipts/netReceivedMinor", retained);
      else awaitFinanceState(agreement, "/receipts/netReceivedMinor", retained);
      receipts(agreement, 7200, 5400, 1800);
      ledger(agreement, 225, paidFirst ? 900 : 0, reservedFirst ? 900 : 0);
      if (suspended != null) System.out.println("PASS native access restored after cumulative refund: " + suspended.handle());
      call(payment, "reverseAfterCompletion", refunded);
      receipts(agreement, 7200, 5400, 1800);
      ledger(agreement, 225, paidFirst ? 900 : 0, reservedFirst ? 900 : 0);
      if (reapprove) {
        requireFreshApproval(agreement);
        resumeApprovedTerms(agreement, 225, 0, 0);
        equal(missedReceipts, recoverySignals(agreement), "Repeated consent recovery emits no attachment or access restoration");
        receipts(agreement, 7200, 5400, 1800);
        ledger(agreement, 225, 0, 0);
        verifyNextRefund(agreement, payment, 0);
      }
      if (reservedFirst) {
        System.out.println("PASS refund while payout unresolved: accrued=225 paid=0 reserved=900 available=-675");
        confirmCommissionPayout(agreement, payout, 225, false);
      }
      if (mode.endsWith("payout") || paidFirst) {
        long paid = paidFirst || reservedFirst ? 900 : 0;
        long attempted = paid > 0 ? 1 : 900;
        require(call(agreement, "startPayout", payoutRequest("uncovered-payout", attempted), true) != null,
            "Actual seller payout route rejects an uncovered reservation");
        ledger(agreement, 225, paid, 0);
        System.out.println("PASS payout/refund ordering " + mode + " accrued=225 paid=" + paid
            + " reserved=0 available=" + (225 - paid));
      }
      System.out.println("PASS " + mode + " sku=" + sku + " capturedMinor=" + amount
          + " refundMinor=" + released + " retainedMinor=" + retained + " commissionMinor=225");
    }

    private void receipts(Coordination.Document agreement, long gross, long refunds, long net) {
      equal(gross, financeAmount(agreement, "/receipts/grossConfirmedMinor"), "Confirmed gross receipts");
      equal(refunds, financeAmount(agreement, "/receipts/refundsMinor"), "Confirmed refunds");
      equal(net, financeAmount(agreement, "/receipts/netReceivedMinor"), "Net confirmed receipts");
    }

    private long financeAmount(Coordination.Document document, String path) {
      var value = scalar(read(document, path));
      require(value instanceof Number, "Missing or wrong native financial amount at " + path + ": " + value);
      return number(value);
    }

    private Object scalar(Object value) {
      return value instanceof Map<?, ?> record && record.containsKey("value") ? record.get("value") : value;
    }

    private void ledger(Coordination.Document agreement, long accrued, long paid, long reserved) {
      equal(accrued, financeAmount(agreement, "/commission/accrued"), "Accrued commission");
      equal(paid, financeAmount(agreement, "/commission/paid"), "Paid gross commission");
      equal(reserved, financeAmount(agreement, "/commission/reserved"), "Reserved gross commission");
    }

    private Map<String, Object> payoutRequest(String key, long gross) {
      return map("key", key, "amountMinor", gross, "accountContext", map("payerBinding", "seller-test-binding",
          "payeeBinding", "partner-test-binding", "platformAccountId", "guarantor-test-platform", "environment", "TEST"));
    }

    private Coordination.Document prepareCommissionPayout(Coordination.Document agreement, String mode, boolean reportFirst)
        throws Exception {
      call(agreement, "startPayout", payoutRequest("commission-payout", 900));
      ledger(agreement, 900, 0, 900);
      var entry = onlyPreparation(agreement, "/process_payouts");
      var payout = bootstrap(mode + "-payout", prepared(agreement, entry),
          Map.of("seller", "seller", "partner", "partner", "guarantor", "guarantor"));
      var terms = "/paymentDetails/payoutTerms";
      equal(900L, number(read(payout, terms + "/grossMinor")), "Frozen gross");
      equal(180L, number(read(payout, terms + "/feeMinor")), "Frozen fee");
      equal(720L, number(read(payout, terms + "/netMinor")), "Frozen transfer");
      call(payout, "approve_seller", map("revision", read(payout, "/activation/revision")));
      equal(true, read(payout, "/activation/active"), "Seller approves the prepared payout terms");
      call(agreement, "providePayout", provision(entry, stableId(payout)));
      awaitFinanceState(agreement, required(entry, "itemPath") + "/status", "usable");
      equal(identityAt(payout, "/contracts/initialized/document"),
          identityAt(agreement, required(entry, "path") + "/contracts/initialized/document"), "Exact prepared payout selected");
      call(payout, "acceptPaymentInstruction", map());
      call(payout, "recordTransactionInitiated", map("type", "PaymentInstruction/Transaction Initiation Input",
          "transactionId", "commission-transaction", "railType", "myos-account-to-account", "attachmentPoint", "instruction",
          "providerReference", "test-transfer"));
      call(payout, "securePayout", map());
      call(payout, "secureFunds", map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "payout-secure",
          "amountSecured", 720));
      call(payout, "capturePayout", map());
      ledger(agreement, 900, 0, 900);
      if (reportFirst) {
        call(payout, "confirmAccountSettlement", payoutReport());
        ledger(agreement, 900, 0, 900);
        System.out.println("PASS signed split report alone keeps G=900 reserved, F=180, N=720");
      }
      return payout;
    }

    private void confirmCommissionPayout(Coordination.Document agreement, Coordination.Document payout, long accrued,
        boolean reportFirst) throws Exception {
      require(call(payout, "completePayment", map("type", "PaymentInstruction/Payment Outcome Input",
          "requestId", "payout-capture", "amountCompleted", 719), true) != null,
          "The actual guarantor route rejects nonmatching completion for the frozen full transfer");
      ledger(agreement, accrued, 0, 900);
      call(payout, "completePayment", map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "payout-capture",
          "amountCompleted", 720));
      if (!reportFirst) {
        ledger(agreement, accrued, 0, 900);
        System.out.println("PASS signed completion alone leaves accrued=225 paid=0 reserved=900");
        call(payout, "confirmAccountSettlement", payoutReport());
      }
      awaitFinanceState(agreement, "/commission/paid", 900L);
      ledger(agreement, accrued, 900, 0);
      call(payout, "confirmAccountSettlement", payoutReport());
      ledger(agreement, accrued, 900, 0);
      equal("commission-transaction", read(payout, "/accountSettlement/transactionId"), "Report names the native transaction");
      equal(identityAt(payout, "/contracts/initialized/document"), read(payout, "/accountSettlement/instructionOrigin"),
          "Report belongs to the selected payout instruction");
      equal(read(payout, "/paymentDetails/payoutTerms"), read(payout, "/accountSettlement/payoutTerms"),
          "Report attests the entire frozen transfer terms");
      String settlement = "/commission/settlements/commission-payout";
      equal(900L, number(read(agreement, settlement + "/paidMinor")), "Confirmed settlement pays the frozen gross once");
      equal(180L, number(read(agreement, settlement + "/feeMinor")), "MyOS fee is frozen");
      equal(720L, number(read(agreement, settlement + "/transferredMinor")), "Confirmed transfer is net");
    }

    private Map<String, Object> payoutReport() {
      return map("debitReference", "test-debit", "transferReference", "test-transfer");
    }

    private void verifyPayoutRecovery(Coordination.Document agreement, Coordination.Document order,
        Coordination.Document payment, String mode) throws Exception {
      boolean terms = mode.endsWith("recover-terms");
      boolean partial = mode.endsWith("completion-only");
      var payout = prepareCommissionPayout(agreement, mode, false);
      var entry = onlyPreparation(agreement, "/process_payouts");
      String entryPath = required(entry, "itemPath");
      String path = required(entry, "path");
      String origin = identityAt(payout, "/contracts/initialized/document");
      var signals = recoverySignals(agreement);
      require(signals.get("activated") > 0 && signals.get("attached") > 0, "Native receipt history sees initial activation and attachment");
      if (terms) requireFreshApproval(agreement);
      else setReadiness(agreement, false);
      equal(false, read(agreement, "/activation/active"), "Agreement is inactive before payout outcomes");
      equal(terms, read(agreement, "/activation/accessReady"), "The fixture exercises only the selected readiness transition");
      equal(true, read(payout, "/activation/active"), "Independent payout remains active");
      equal("usable", read(agreement, entryPath + "/status"), "The admitted payout stays usable during the gap");

      var completed = map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "payout-capture", "amountCompleted", 720);
      var report = payoutReport();
      if (!partial && !terms) call(payout, "confirmAccountSettlement", report);
      call(payout, "completePayment", completed);
      if (!partial && terms) call(payout, "confirmAccountSettlement", report);
      equal(false, read(agreement, "/activation/active"), "Payout outcomes do not activate the Agreement");
      equal(720L, financeAmount(payout, "/payment/completed"), "Actual payout net completion");
      equal(partial, read(payout, "/accountSettlement") == null, "The expected report is present only in the complete-proof cases");
      if (!partial) {
        equal(900L, financeAmount(payout, "/accountSettlement/grossMinor"), "Guarantor reports gross");
        equal(180L, financeAmount(payout, "/accountSettlement/feeMinor"), "Guarantor reports fee");
        equal(720L, financeAmount(payout, "/accountSettlement/netMinor"), "Guarantor reports transfer");
        equal(origin, read(payout, "/accountSettlement/instructionOrigin"), "Report belongs to the exact original payout");
      }
      ledger(agreement, 900, 0, 900);
      if (terms) resumeApprovedTerms(agreement, 900, 0, 900);
      else setReadiness(agreement, true);
      awaitFinanceState(agreement, path + "/payment/completed", 720L);
      if (partial) equal(null, read(agreement, path + "/accountSettlement"), "The selected payout snapshot has no account report");
      else awaitFinanceState(agreement, path + "/accountSettlement", read(payout, "/accountSettlement"));
      equal("usable", read(agreement, entryPath + "/status"), "Resume does not reattach the selected payout");
      equal(origin, identityAt(agreement, path + "/contracts/initialized/document"), "Resume observes the same selected payout");
      var later = recoverySignals(agreement);
      equal(signals.get("activated"), later.get("activated"), "Resume is not first activation");
      equal(signals.get("attached"), later.get("attached"), "Resume emits no new Document Attached");
      equal(signals.get("accessRestored") + (terms ? 0 : 1), later.get("accessRestored"), "Only the intended resume signal is emitted");
      logPayoutRecoveryWitness(agreement, entryPath, path, origin);
      System.out.println("OBSERVED F02 after " + mode + " without child replay or attachment: paid="
          + financeAmount(agreement, "/commission/paid") + " reserved=" + financeAmount(agreement, "/commission/reserved"));
      if (partial) {
        ledger(agreement, 900, 0, 900);
        System.out.println("PASS completion-only recovery retains the full reservation without an account report");
        call(payout, "confirmAccountSettlement", report);
      }
      awaitRecoveredFinanceState(agreement, "/commission/paid", 900L);
      ledger(agreement, 900, 900, 0);
      String settlement = "/commission/settlements/commission-payout";
      equal(900L, financeAmount(agreement, settlement + "/paidMinor"), "Recovered payout settles gross");
      equal(180L, financeAmount(agreement, settlement + "/feeMinor"), "Recovered payout settles fee");
      equal(720L, financeAmount(agreement, settlement + "/transferredMinor"), "Recovered payout settles transfer");
      if (terms) {
        requireFreshApproval(agreement);
        resumeApprovedTerms(agreement, 900, 900, 0);
      } else {
        setReadiness(agreement, false);
        setReadiness(agreement, true);
      }
      ledger(agreement, 900, 900, 0);
      call(payout, "completePayment", completed);
      call(payout, "confirmAccountSettlement", report);
      ledger(agreement, 900, 900, 0);
      call(order, "cancelOrder", map("key", "next-cancellation", "reason", "Later ordinary refund after payout recovery"));
      call(payment, "reverseAfterCompletion", map("type", "PaymentInstruction/Payment Outcome Input",
          "requestId", "order-cancellation-refund", "amountReversed", 5400));
      awaitFinanceState(agreement, "/receipts/netReceivedMinor", 1800L);
      receipts(agreement, 7200, 5400, 1800);
      ledger(agreement, 225, 900, 0);
      System.out.println("PASS " + mode + " after real resume and replay, later refund leaves accrued=225 paid=900 reserved=0");
    }

    private void logPayoutRecoveryWitness(Coordination.Document agreement, String entry, String path, String origin) {
      var original = read(agreement, path + "/contracts/initialized/document");
      var terms = obj(read(agreement, path + "/paymentDetails/payoutTerms"));
      var report = read(agreement, path + "/accountSettlement");
      System.out.println("F02 native selection " + WireData.write(map(
          "key", read(agreement, entry + "/key"), "path", path, "status", read(agreement, entry + "/status"),
          "documentOrigin", read(agreement, entry + "/documentOrigin"), "initializedOrigin", origin,
          "initializedFields", original instanceof Map<?, ?> map ? map.keySet() : List.of(),
          "instructionType", identityAt(agreement, path + "/type"), "completed", financeAmount(agreement, path + "/payment/completed"),
          "termsFields", terms.keySet(), "gross", terms.get("grossMinor"), "fee", terms.get("feeMinor"), "net", terms.get("netMinor"),
          "reportFields", report instanceof Map<?, ?> map ? map.keySet() : List.of())));
    }

    private void setReadiness(Coordination.Document document, boolean ready) throws Exception {
      var seller = fixtureParticipants.get(document.handle() + "-seller");
      var keys = new ArrayList<>(readers.values());
      if (!ready) keys.remove(readers.get("seller"));
      provider.changeAccess(OWNER, seller.grant(), List.of(seller.timeline()), keys,
          "finance-access-" + document.handle() + "-" + ++readinessChange, tenant.service.bindings());
      awaitFinanceState(document, "/activation/active", ready);
      equal(true, read(document, "/activation/everActivated"), "Access change preserves earlier approval history");
    }

    private void requireFreshApproval(Coordination.Document agreement) throws Exception {
      String seller = "/activation/parties/seller";
      var party = read(agreement, seller);
      long revision = financeAmount(agreement, "/activation/revision");
      equal(true, read(agreement, "/activation/active"), "Agreement begins active");
      equal(true, read(agreement, "/activation/accessReady"), "Agreement begins with ready access");
      call(agreement, "updateParty_seller", map("type", "Activation/Party Update Input", "replacement", party));
      equal(party, read(agreement, seller), "Reapproval uses an unchanged party and transport");
      equal(revision + 1, financeAmount(agreement, "/activation/revision"), "The signed update creates a new revision");
      equal(Map.of(), read(agreement, "/activation/approved"), "All previous approvals are invalidated");
      equal(false, read(agreement, "/activation/active"), "Agreement needs new terms approvals");
      equal(true, read(agreement, "/activation/accessReady"), "Agreement access stays ready");
      equal(true, read(agreement, "/activation/everActivated"), "Earlier activation is preserved");
    }

    private void resumeApprovedTerms(Coordination.Document agreement, long accrued, long paid, long reserved)
        throws Exception {
      long accepted = countEmissions(agreement, "Activation/Terms Accepted");
      require(accepted > 0, "Native receipt history sees earlier Terms Accepted");
      var receiptsBefore = read(agreement, "/receipts");
      acceptTerms(agreement, "seller");
      equal(false, read(agreement, "/activation/active"), "One renewed approval cannot recover finance");
      equal(true, read(agreement, "/activation/accessReady"), "Access remains ready after the first approval");
      equal(receiptsBefore, read(agreement, "/receipts"), "One renewed approval does not affect receipts");
      ledger(agreement, accrued, paid, reserved);
      acceptTerms(agreement, "partner");
      equal(true, read(agreement, "/activation/active"), "Both current approvals restore activity");
      equal(true, read(agreement, "/activation/accessReady"), "No access restore is needed");
      equal(accepted + 2, countEmissions(agreement, "Activation/Terms Accepted"), "Both native terms approvals were emitted");
    }

    private Map<String, Long> recoverySignals(Coordination.Document agreement) {
      return Map.of("activated", countEmissions(agreement, "Parties/Document Activated"),
          "accessRestored", countEmissions(agreement, "Parties/Document Access Restored"),
          "attached", countEmissions(agreement, "Documents/Document Attached"));
    }

    private long countEmissions(Coordination.Document document, String type) {
      var values = processor.execution().values();
      var expected = NativeRuntime.identity(values.exact(values.select(values.source(map("type", type)), "/type")));
      long count = 0;
      for (String receipt : document.history().stream().map(row -> text(row.get("receipt"))).filter(id -> !id.isBlank()).distinct().toList()) {
        var root = new Exact.Ref(receipt);
        for (int ordinal = 0; ; ordinal++) {
          var occurrence = "/emitted/" + ordinal;
          if (values.select(root, occurrence) == null) break;
          var actual = values.select(root, occurrence + "/event/type");
          if (actual != null && expected.equals(NativeRuntime.identity(values.exact(actual)))) count++;
        }
      }
      return count;
    }

    private void verifyNextRefund(Coordination.Document agreement, Coordination.Document payment, long paid) throws Exception {
      call(payment, "refund", map("type", "PaymentInstruction/Payment Request Input", "requestId", "next-manual-refund",
          "amountMinor", 100));
      receipts(agreement, 7200, 5400, 1800);
      call(payment, "reverseAfterCompletion", map("type", "PaymentInstruction/Payment Outcome Input",
          "requestId", "next-manual-refund", "amountReversed", 100));
      awaitFinanceState(agreement, "/receipts/netReceivedMinor", 1700L);
      receipts(agreement, 7200, 5500, 1700);
      ledger(agreement, 213, paid, 0);
      System.out.println("PASS later ordinary signed refund updates net=1700 and accrued=213");
    }

    private void awaitFinanceState(Coordination.Document document, String path, Object expected) throws Exception {
      awaitFinanceState(document, path, expected, WAIT);
    }

    private void awaitRecoveredFinanceState(Coordination.Document document, String path, long expected) throws Exception {
      var observation = Duration.ofSeconds(Long.getLong("blue.packages.recoveryObservationSeconds", WAIT.toSeconds()));
      awaitFinanceState(document, path, expected, observation);
    }

    private void awaitFinanceState(Coordination.Document document, String path, Object expected, Duration observation)
        throws Exception {
      long deadline = System.nanoTime() + observation.toNanos();
      Object observed;
      do {
        IndependentHostedAccessTest.poll(tenant);
        tenant.service.awaitIdle(WAIT);
        observed = scalar(read(document, path));
        if (observed instanceof Number actual && expected instanceof Number target
            ? actual.longValue() == target.longValue() : java.util.Objects.equals(expected, observed)) return;
      } while (System.nanoTime() < deadline);
      throw new AssertionError(document.handle() + " " + path + " expected " + expected + ", observed " + observed
          + ": " + document.progress());
    }

    private void bindGoFixtureAccounts(Map<String, Object> source, Map<String, Object> order) {
      obj(source.get("terms")).put("payoutOperatorAccountId", "test-payout-account");
      var reader = obj(obj(activationParameters(order).get("readers")).get("guarantor"));
      reader.put("myosAccountId", "guarantor");
      reader.put("readerKeys", List.of(readers.get("guarantor")));
      var payment = paymentInstruction(order);
      var guarantor = obj(obj(activationParameters(payment).get("parties")).get("guarantor"));
      guarantor.put("myosAccountId", "guarantor");
      obj(guarantor.get("readerKeys")).put("items", List.of(readers.get("guarantor")));
      obj(obj(payment.get("paymentDetails")).get("customerPaymentTerms"))
          .put("recipientPaymentAccountId", "test-recipient-account");
    }

    private Map<String, Object> paymentInstruction(Map<String, Object> order) {
      var clause = obj(obj(order.get("clauses")).get("payment"));
      return obj(obj(clause.get("parameters")).get("template"));
    }

    private void acceptTerms(Coordination.Document agreement, String role) throws Exception {
      call(agreement, "activate_" + role, map("type", "Activation/Terms Selection Input",
          "termsRef", read(agreement, "/activation/terms/ref")));
    }

    private void assertOnlyVoid(Coordination.Document payment, String voidRequest, long amount) {
      equal(Set.of("original-hold", voidRequest), obj(read(payment, "/payment/requests")).keySet(),
          "Exactly the original authorization and one native VOID request");
      var intent = "/payment/requests/" + voidRequest + "/intent";
      equal("void", read(payment, intent + "/action"), "Autonomous request is VOID");
      equal(amount, number(read(payment, intent + "/amountMinor")), "VOID covers the original full hold");
      equal(0L, number(read(payment, "/payment/completed")), "No capture");
      equal(0L, number(read(payment, "/payment/reversed")), "No refund");
    }

    private void customerIdentityRules(Coordination.Document agreement) {
      var frozen = map("customerEmail", "buyer@example.test", "amountMinor", 7200, "currency", "USD",
          "quote", map("fixture", "Frozen quote"), "quoteBlueId", "frozen-quote", "orderSnapshot", map());
      var currentBuyer = map("myosAccountId", "customer");
      var initialBuyer = map("myosAccountId", "customer");
      var candidate = new LinkedHashMap<String, Object>(frozen);
      candidate.put("activation", map("parties", map("customer", currentBuyer,
          "seller", map("myosAccountId", "seller"), "partner", map("myosAccountId", "partner"))));
      candidate.put("contracts", map("initialized", map("document", map("clauses", map("activation",
          map("parameters", map("parties", map("customer", initialBuyer))))))));
      assertCustomerIdentity(agreement, frozen, candidate, null);
      candidate.put("customerAccountId", "customer");
      assertCustomerIdentity(agreement, frozen, candidate, null);
      candidate.put("customerAccountId", "foreign-customer");
      assertCustomerIdentity(agreement, frozen, candidate, "CUSTOMER_ORDER_IDENTITY_CHANGED");
      candidate.remove("customerAccountId");
      currentBuyer.put("myosAccountId", "foreign-customer");
      assertCustomerIdentity(agreement, frozen, candidate, "CUSTOMER_ORDER_IDENTITY_CHANGED");
      currentBuyer.put("myosAccountId", "customer");
      frozen.put("customerAccountId", "foreign-customer");
      assertCustomerIdentity(agreement, frozen, candidate, "CUSTOMER_ORDER_COMMERCIAL_TERMS_CHANGED");
      System.out.println("PASS canonical initial/current buyer, optional copy validation and frozen explicit authority");
    }

    private void assertCustomerIdentity(Coordination.Document agreement, Map<String, Object> frozen,
        Map<String, Object> candidate, String expectedFailure) {
      var program = provisionProgram(agreement, "provideOrder");
      program.put("expr", map("$call", map("function", "domainValidateCandidate", "args",
          map("frozenTerms", map("$binding", "call/frozen"), "candidate", map("$binding", "call/candidate")))));
      var values = processor.execution().values();
      var input = values.source(map("frozen", frozen, "candidate", candidate));
      try {
        var result = processor.execution().evaluatePredicate(new Exact.Ref(stableId(agreement)), input, "call",
            values.source(program), 10_000_000);
        equal(null, expectedFailure, "Forged identity must fail native validation");
        equal(true, result.value(), "Authoritative buyer identity applies");
      } catch (blue.bex.BexError error) {
        equal(expectedFailure, error.getMessage(), "Exact customer identity guard");
      }
    }

    void run(Path root) throws Exception {
      var source = obj(WireData.parse(Files.readString(
          root.resolve("examples/reseller/adventures-in-paradise-preview.blue")), "yaml"));
      var orderTemplate = obj(source.get("orderTemplate"));
      var orderClauses = obj(orderTemplate.get("clauses"));
      var orderActivation = activationParameters(orderTemplate);
      orderActivation.put("required", List.of("seller"));
      var payment = obj(orderClauses.get("payment"));
      var paymentParams = obj(payment.get("parameters"));
      paymentParams.put("sourcePaths", map("order", ""));
      orderActivation.put("readers", map("guarantor", map(
          "myosAccountId", "guarantor", "readerKeys", List.of(readers.get("guarantor")))));
      orderActivation.remove("preActivationChannels");
      orderActivation.put("preActivationOperations", List.of("preparePayment", "providePayment"));
      obj(payment.get("bindings")).put("prepare", map("preparePayment", map(
          "on", "workflow", "party", "seller", "params",
          obj(obj(obj(payment.get("bindings")).get("prepare")).get("onOrderCreated")).get("params"))));
      var piTemplate = obj(paymentParams.get("template"));
      obj(obj(obj(piTemplate.get("clauses")).get("payment")).get("parameters"))
          .put("sources", map("order", map()));
      obj(obj(obj(source.get("products")).get("entries")).get("dolphin-cruise-child"))
          .put("unitAmountMinor", 4100);

      var agreement = bootstrap("agreement", source, Map.of("seller", "seller", "partner", "partner"));
      System.out.println("Catalog Orders Clause " + identityAt(agreement, "/clauses/orders/type"));
      call(agreement, "approve_seller", map("revision", 1));
      call(agreement, "approve_partner", map("revision", 1));
      call(agreement, "prepareOrder",
          map("type", "Documents/Preparation Input", "key", "checkout-1", "requestId", "basket-1",
              "values", map("customerEmail", "guest@example.test", "catalogRevision", 1,
                  "lines", List.of(map("itemId", "dolphin-cruise-child", "quantity", 1),
                      map("itemId", "dolphin-cruise-under-4", "quantity", 1)),
                  "groups", List.of(map("id", "visit", "lineIndices", List.of(0, 1),
                      "proposedStartMicros", proposedStart)))));
      require(obj(read(agreement, "/orders")).isEmpty(), "Preparation leaves /orders empty");
      var orderEntry = onlyPreparation(agreement, "/process_orders");
      var order = bootstrap("order", prepared(agreement, orderEntry),
          Map.of("seller", "seller", "partner", "partner", "customer", "customer"));
      equal(false, read(order, "/activation/active"), "Order awaits supplier approval");
      equal(AMOUNT, number(read(order, "/amountMinor")), "Two-line order amount");
      equal("USD", read(order, "/currency"), "Order currency");
      equal(null, read(order, "/payment"), "Bootstrapped Order has no PI");
      String orderOrigin = identityAt(order, "/contracts/initialized/document");
      var provision = provision(orderEntry, stableId(order));
      call(agreement, "provideOrder", provision);
      String entryPath = required(orderEntry, "itemPath");
      var state = read(agreement, entryPath + "/status");
      var orders = obj(read(agreement, "/orders"));
      require(orders.size() == 1 && orders.containsKey("checkout-1"),
          "First provideOrder must select the initialized Order while inactive. status=" + state
              + " order keys=" + orders.keySet());
      equal(orderOrigin, identityAt(agreement, ORDER + "/contracts/initialized/document"), "Selected Order origin");
      equal("selected", state, "Commercially inactive Order stays selected");
      equal(false, read(agreement, ORDER + "/activation/active"), "Provision cannot approve the Order");
      equal(null, read(agreement, PAYMENT), "Early link has no PI");
      accrued(agreement, 0);
      System.out.println("PASS first provideOrder selected one inactive Order with no PI");

      call(order, "preparePayment", map());
      var paymentEntry = onlyPreparation(order, "/process_payment");
      var instruction = bootstrap("payment", prepared(order, paymentEntry),
          Map.of("payer", "customer", "payee", "seller", "observer", "partner", "guarantor", "guarantor"));
      String instructionOrigin = identityAt(instruction, "/contracts/initialized/document");
      equal(orderOrigin, identityAt(instruction, "/sources/order/contracts/initialized/document"),
          "PI was bootstrapped with the same Order as its declared source");
      call(order, "providePayment", provision(paymentEntry, stableId(instruction)));
      equal(instructionOrigin, identityAt(agreement, PAYMENT + "/contracts/initialized/document"),
          "Independent attachment of PI reaches the same selected Order");
      accrued(agreement, 0);

      call(instruction, "acceptPaymentInstruction", map());
      call(instruction, "recordTransactionInitiated",
          map("type", "PaymentInstruction/Transaction Initiation Input", "transactionId", "checkout-transaction",
              "railType", "test", "attachmentPoint", "instruction", "providerReference", "test"));
      call(instruction, "authorize",
          map("type", "PaymentInstruction/Payment Request Input", "requestId", "authorize-1", "amountMinor", AMOUNT));
      call(instruction, "secureFunds",
          map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "authorize-1", "amountSecured", AMOUNT));
      accrued(agreement, 0);
      equal(false, read(agreement, ORDER + "/activation/active"), "Securing payment cannot approve the Order");
      equal(AMOUNT, number(read(agreement, PAYMENT + "/payment/secured")), "Independent authorization reaches Agreement");
      call(order, "approve_seller", map("revision", 1));
      equal(true, read(agreement, ORDER + "/activation/active"), "Independent approval reaches Agreement");
      equal(true, read(instruction, "/sources/order/activation/active"), "Independent approval reaches the PI source");
      equal("usable", read(agreement, entryPath + "/status"), "Approved Order becomes usable");
      equal("pending_supplier", read(order, "/reservations/visit/status"), "Reservation awaits separate confirmation");
      call(order, "confirmReservation",
          map("key", "confirmation-1", "groupId", "visit",
              "expectedProposalBlueId", read(order, "/reservations/visit/proposalBlueId")));
      equal(proposedStart, number(read(agreement, ORDER + "/reservations/visit/confirmedStartMicros")),
          "Independent supplier confirms the proposed date");

      call(instruction, "pay",
          map("type", "PaymentInstruction/Payment Request Input", "requestId", "capture-1", "amountMinor", AMOUNT));
      var receipt = map("type", "PaymentInstruction/Payment Outcome Input", "requestId", "capture-1", "amountCompleted", AMOUNT);
      call(instruction, "completePayment", receipt);
      assertPaidOrder(agreement, entryPath, orderOrigin, instructionOrigin);
      System.out.println("PASS independent PI completion accrued 390 without a second provideOrder");

      String paidPublication = identityAt(agreement, ORDER);
      call(instruction, "completePayment", receipt);
      assertPaidOrder(agreement, entryPath, orderOrigin, instructionOrigin);
      String afterReceiptReplay = identityAt(agreement, ORDER);
      System.out.println("Order publication after receipt retry " + paidPublication + " -> " + afterReceiptReplay);
      call(agreement, "provideOrder", provision);
      assertPaidOrder(agreement, entryPath, orderOrigin, instructionOrigin);
      System.out.println("Order publication after provision retry " + afterReceiptReplay + " -> " + identityAt(agreement, ORDER));
      System.out.println("PASS retries preserve the selected Order, PI and single commission");
    }

    private void assertPaidOrder(Coordination.Document agreement, String entryPath,
        String orderOrigin, String instructionOrigin) {
      equal(Set.of("checkout-1"), obj(read(agreement, "/orders")).keySet(), "One Order");
      equal("usable", read(agreement, entryPath + "/status"), "Order remains usable");
      equal(orderOrigin, identityAt(agreement, ORDER + "/contracts/initialized/document"), "Same Order origin");
      equal(true, read(agreement, ORDER + "/activation/approved/seller"), "Supplier approval retained");
      equal(proposedStart, number(read(agreement, ORDER + "/reservations/visit/confirmedStartMicros")),
          "Supplier confirmation retained");
      equal(instructionOrigin, identityAt(agreement, PAYMENT + "/contracts/initialized/document"), "Same PI origin");
      equal(AMOUNT, number(read(agreement, PAYMENT + "/payment/completed")), "Completed receipt retained");
      accrued(agreement, COMMISSION);
      equal(Set.of("checkout-1"), obj(read(agreement, "/commission/targets")).keySet(), "One commission target");
      equal(COMMISSION, number(read(agreement, "/commission/targets/checkout-1")), "Commission rounds to 390");
    }

    private Coordination.Document bootstrap(String handle, Map<String, Object> source,
        Map<String, String> roles) throws Exception {
      var activation = activationParameters(source);
      var parties = obj(activation.get("parties"));
      if (activation.get("readers") instanceof Map<?, ?> rawReaders) {
        obj(rawReaders).replaceAll((key, reader) ->
            reader instanceof Map<?, ?> descriptor ? descriptor.get("readerKeys") : reader);
      }
      var contracts = obj(source.computeIfAbsent("contracts", ignored -> map()));
      var accesses = new LinkedHashMap<String, Object>();
      var paths = new ArrayList<String>();
      for (var assignment : new TreeMap<>(roles).entrySet()) {
        String role = assignment.getKey();
        String actor = assignment.getValue();
        var participant = timeline(handle, role, actor);
        var party = obj(parties.get(role));
        contracts.put(role, participant.channel());
        party.put("myosAccountId", actor);
        party.put("lead", map("channel", participant.channel()));
        party.put("readerKeys", List.of(participant.reader()));
        accesses.put(role, ref(participant.access()));
        paths.add("/timelineAccess/" + role);
      }
      activation.put("accessPaths", paths);
      source.put("timelineAccess", accesses);
      var admitted = language.createJson(WireData.write(source));
      tenant.service.publishContent(admitted);
      tenant.service.engine().add(handle, ref(admitted.blueId()));
      var document = tenant.service.document(handle);
      tenant.service.awaitIdle(WAIT);
      require(document.progress().stable().isPresent(), "Initialize " + handle + " " + admitted.blueId()
          + ": " + document.progress());
      System.out.println("INITIALIZED " + handle);
      return document;
    }

    private String call(Coordination.Document document, String operation, Map<String, Object> request) throws Exception {
      return call(document, operation, request, false);
    }

    private String call(Coordination.Document document, String operation, Map<String, Object> request, boolean blocked)
        throws Exception {
      var routes = document.routes(operation);
      if (blocked && routes.isEmpty()) {
        System.out.println("UNAVAILABLE " + document.handle() + "/" + operation);
        return null;
      }
      equal(1, routes.size(), "One route for " + operation);
      var route = routes.getFirst();
      var bindings = tenant.service.bindings();
      var nativeRequest = processor.execution().values().literal(processor.execution().values().source(request));
      var call = map("type", ref(ProviderAccessExecution.operationRequestType(bindings)),
          "document", ref(stableId(document)), "channel", route.channel(), "operation", operation,
          "request", nativeRequest, "requireExactDocumentVersion", true);
      // The request may carry types from the published business packages, which the
      // local provider's native-only type catalogue does not mount.
      equal("request", processor.execution().role(processor.execution().values().source(call)), "Operation type");
      publishEvidence();
      var appended = provider.append(OWNER, route.timeline(), call,
          "catalog-order-" + document.handle() + "-" + operation + "-" + java.util.UUID.randomUUID(), true);
      String entry;
      try (var protocol = new ProviderProtocol()) {
        entry = protocol.identify(appended.get("object"));
      }
      long deadline = System.nanoTime() + WAIT.toNanos();
      do {
        IndependentHostedAccessTest.poll(tenant);
        tenant.service.awaitIdle(WAIT);
        var input = tenant.documents.input(document.handle(), entry);
        var progress = document.progress();
        if (IndependentHostedAccessTest.rejected(tenant, document, entry)) {
          if (blocked) {
            System.out.println("BLOCKED " + document.handle() + "/" + operation);
            return entry;
          }
          if (operation.equals("provideOrder") || operation.equals("providePayment")) {
            diagnoseProvision(document, operation, route.channel(), request);
          }
          var result = obj(obj(input.get("disposition")).get("result"));
          throw new AssertionError(operation + " rejected: " + WireData.write(result.get("diagnostic")));
        }
        require(!Set.of(Coordination.Status.ERROR, Coordination.Status.HOST_INCOMPLETE).contains(progress.status()),
            operation + " failed: " + progress);
        if (arr(input.get("localHistory")).stream().map(Values::obj)
            .anyMatch(row -> Boolean.TRUE.equals(row.get("stable")))) {
          require(!blocked, operation + " unexpectedly applied after the terminal decision");
          System.out.println("APPLIED " + document.handle() + "/" + operation);
          return entry;
        }
        Thread.sleep(20);
      } while (System.nanoTime() < deadline);
      throw new AssertionError(operation + " did not finish: " + document.progress());
    }

    private void diagnoseProvision(Coordination.Document document, String operation, String channel,
        Map<String, Object> request) {
      var program = provisionProgram(document, operation);
      program.put("expr", map("$call", map("function", "checkProvision",
          "args", map("input", map("$binding", "call/request")))));
      var values = processor.execution().values();
      var input = values.source(map("channel", channel, "request", request));
      processor.execution().evaluatePredicate(new Exact.Ref(stableId(document)), input, "call", values.source(program), 10_000_000);
    }

    private Map<String, Object> provisionProgram(Coordination.Document document, String operation) {
      var values = processor.execution().values();
      var root = new Exact.Ref(stableId(document));
      String step = "/contracts/" + operation + "/steps/0";
      var functions = new LinkedHashMap<>(obj(values.bexData(values.select(root, step + "/definition/functions"))));
      var local = values.select(root, step + "/functions");
      if (local != null) functions.putAll(obj(values.bexData(local)));
      functions.replaceAll((name, body) -> body instanceof Map<?, ?> ref && ref.get("blueId") instanceof String id
          ? values.bexData(new Exact.Ref(id)) : body);
      return map("functions", functions, "constants", values.bexData(values.select(root, step + "/constants")));
    }

    private void publishEvidence() {
      try (var view = tenant.store.read()) {
        var writes = new TreeMap<RecordStore.Key, Object>();
        processor.execution().values().nativeRuntime().evidence().forEach((id, body) -> {
          if (view.get("content", id) == null) writes.put(new RecordStore.Key("content", id), body);
        });
        equal("COMMITTED", tenant.store.publish(view.packet("catalog-order-definitions", writes, null)).status(),
            "Retain immutable inputs");
      }
    }

    private Map<String, Object> onlyPreparation(Coordination.Document document, String process) {
      var entries = obj(read(document, process + "/entries"));
      equal(1, entries.size(), "One preparation at " + process);
      return obj(entries.values().iterator().next());
    }

    private Map<String, Object> prepared(Coordination.Document document, Map<String, Object> entry) {
      var values = processor.execution().values();
      return obj(values.literal(values.exact(values.select(new Exact.Ref(stableId(document)),
          required(entry, "itemPath") + "/prepared"))));
    }

    private Object read(Coordination.Document document, String path) {
      var values = processor.execution().values();
      var selected = values.select(new Exact.Ref(stableId(document)), path);
      return selected == null ? null : values.bexData(selected);
    }

    private String identityAt(Coordination.Document document, String path) {
      var values = processor.execution().values();
      return NativeRuntime.identity(values.exact(values.select(new Exact.Ref(stableId(document)), path)));
    }

    private void accrued(Coordination.Document agreement, long expected) {
      equal(expected, number(read(agreement, "/commission/accrued")), "Commission accrued");
    }
  }

  private record Participant(Map<String, Object> channel, String reader, String access, String timeline, String grant) {}

  private static String stableId(Coordination.Document document) {
    return document.state().stable().orElseThrow().blueId();
  }

  private static Map<String, Object> ref(String blueId) {
    return map("blueId", blueId);
  }

  private static Map<String, Object> provision(Map<String, Object> item, String documentId) {
    return map("type", "Documents/Provision Input", "key", item.get("key"),
        "inResponseTo", item.get("requestId"), "requirementRef", item.get("requirementRef"),
        "document", ref(documentId));
  }

  private static Map<String, Object> activationParameters(Map<String, Object> source) {
    return obj(obj(obj(source.get("clauses")).get("activation")).get("parameters"));
  }

  private static void equal(Object expected, Object actual, String label) {
    require(java.util.Objects.equals(expected, actual), label + " expected=" + expected + " actual=" + actual);
  }

  private static void require(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
}
