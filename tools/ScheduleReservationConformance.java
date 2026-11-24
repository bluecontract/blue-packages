import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.language.next.WireData;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Native Contracts coverage for independent booking and seller decision rules. */
public final class ScheduleReservationConformance {
  private static final long START_MICROS = 36_000_000_000L;

  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]);
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var language = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      var processor = runtime.processor(language);
      standaloneBooking(processor);
      reviewedBooking(processor);
      reviewedAlternative(processor);
      invalidReviewRollsBack(processor);
      invalidReviewEvidence(processor);
      widerReviewedAlternatives(processor);
      independentBookings(processor);
      duplicateReviewedSelector(processor);
      reviewedRoleNamesDoNotCollide(processor);
      independentSellerDecision(processor);
      wholeOrderAcceptance(processor);
    }
  }

  private static void standaloneBooking(Contracts processor) {
    var source = booking(processor, true, true);
    fields(source.get("clauses")).remove("activation");
    source.put("contracts", map("seller", external("seller"), "customer", external("customer")));
    var pending = initialize(processor, source);
    var confirmed = invoke(processor, pending, "seller", "confirmReservation", confirmation(processor, pending));
    equal("confirmed", processor.read(confirmed, "/booking/status"), "Schedule confirms without an Activation clause");
    equal(blue.bex.Values.UNDEFINED, processor.read(confirmed, "/activation"), "Schedule creates no acceptance state");
    System.out.println("PASS standalone Schedule confirms a booking without Activation");
  }

  private static void reviewedBooking(Contracts processor) {
    var waiting = initialize(processor, booking(processor, false, true));
    var confirmation = confirmation(processor, waiting);
    check(!Boolean.TRUE.equals(processor.read(waiting, "/activation/active")), "Seller has not accepted yet");
    equal("pending_supplier", processor.read(waiting, "/booking/status"), "Published booking is pending");
    assertBlocked(processor, waiting, "seller", "approve_seller", approval(processor, waiting), true);
    assertBlocked(processor, waiting, "seller", "confirmReservation", confirmation, true);

    var ready = initialize(processor, booking(processor, true, true));
    assertBlocked(processor, ready, "seller", "approve_seller", approval(processor, ready), true);
    var cancelled = invoke(processor, ready, "customer", "emitCancellation", map());
    equal("cancelled", processor.read(cancelled, "/booking/status"), "Connected closure releases a pending booking");
    equal(false, processor.read(cancelled, "/activation/active"), "Closure grants no seller acceptance");
    equal(map(), processor.read(cancelled, "/reservationRequests"), "Connected closure consumes no workflow request key");
    assertBlocked(processor, cancelled, "seller", "confirmReservation", confirmation(processor, cancelled), true);
    var currentConfirmation = confirmation(processor, ready);
    assertBlocked(processor, ready, "seller", "confirmReservation", currentConfirmation, false);
    assertBlocked(processor, ready, "customer", "confirmReservation", currentConfirmation, true);
    var stale = map("key", "confirm", "groupId", "booking-1", "expectedProposalBlueId", "stale");
    assertBlocked(processor, ready, "seller", "confirmReservation", stale, true);
    var confirmationResult = apply(processor, ready, "seller", "confirmReservation", currentConfirmation);
    var confirmed = confirmationResult.document();
    equal(List.of("seller"), acceptedParties(processor, confirmationResult),
        "One booking turn emits the seller's acceptance");
    equal(true, processor.read(confirmed, "/activation/active"), "Reviewed seller booking activates the Order");
    equal(true, processor.read(confirmed, "/activation/approved/seller"), "Seller's actual review records acceptance");
    equal("confirmed", processor.read(confirmed, "/booking/status"), "Confirmation publishes operational status");
    equal(Long.toString(START_MICROS), String.valueOf(processor.read(confirmed, "/booking/confirmedStartMicros")),
        "Confirmed service start comes from the exact booking proposal");
    var duplicate = apply(processor, confirmed, "seller", "confirmReservation", currentConfirmation);
    equal(List.of(), processor.emitted(duplicate), "A duplicate emits no second approval or booking event");
    var repeatedConfirmation = duplicate.document();
    for (String path : List.of("/activation", "/reservations", "/reservationRequests")) {
      equal(processor.read(confirmed, path), processor.read(repeatedConfirmation, path),
          "Same request key and reviewed proposal preserve " + path);
    }
    equal(blue.bex.Values.UNDEFINED, processor.read(confirmed, "/booking/amountMinor"), "Summary has no monetary state");
    equal(blue.bex.Values.UNDEFINED, processor.read(confirmed, "/reservations/booking-1/freeCancellationUntilMicros"),
        "Schedule does not select or publish a commercial cutoff");
    var cancel = map("key", "operational-close", "groupId", "booking-1", "reason", "Customer ended the reservation",
        "expectedProposalBlueId", processor.read(confirmed, "/reservations/booking-1/proposalBlueId"));
    var closed = invoke(processor, confirmed, "customer", "cancelReservation", cancel);
    equal("cancelled", processor.read(closed, "/booking/status"), "Operational reservation closes");
    equal(blue.bex.Values.UNDEFINED, processor.read(closed, "/reservations/booking-1/decision"),
        "Operational close creates no duplicate paid decision");
    var replayed = invoke(processor, closed, "customer", "cancelReservation", cancel);
    equal(processor.read(closed, "/reservations"), processor.read(replayed, "/reservations"), "Repeated operational close is idempotent");

    var closedByEvent = invoke(processor, confirmed, "customer", "emitCancellation", map());
    equal("cancelled", processor.read(closedByEvent, "/booking/status"), "Connected closure releases a confirmed booking");
    var repeated = invoke(processor, closedByEvent, "customer", "emitCancellation", map());
    equal(processor.read(closedByEvent, "/reservations"), processor.read(repeated, "/reservations"), "Repeated accepted event leaves reservation unchanged");
    equal(processor.read(confirmed, "/reservationRequests"), processor.read(repeated, "/reservationRequests"),
        "Connected closure and its repeat leave existing request evidence unchanged");
    var withoutSummary = initialize(processor, booking(processor, true, false));
    equal(blue.bex.Values.UNDEFINED, processor.read(withoutSummary, "/booking"), "Booking summary is optional");
    System.out.println("PASS separate reviewed booking, arbitrary optional summary path, exact guard and operational close");
  }

  private static void reviewedAlternative(Contracts processor) {
    var pending = initialize(processor, booking(processor, true, true));
    var alternative = alternative(processor, pending, "booking-1", "seller", START_MICROS * 2);
    var offeredResult = apply(processor, pending, "seller", "proposeAlternative", alternative);
    var offered = offeredResult.document();
    equal("pending_customer", processor.read(offered, "/booking/status"), "Seller's alternative waits for buyer approval");
    equal(false, processor.read(offered, "/activation/active"), "An offered alternative does not activate the Order");
    equal(List.of(), acceptedParties(processor, offeredResult), "An alternative emits no final acceptance");
    equal(7200L, integer(processor.read(offered, "/reservations/booking-1/proposal/amountMinor")),
        "The alternative keeps the approved monetary scope");
    equal(2L, integer(processor.read(offered, "/reservations/booking-1/proposal/number")),
        "The offered alternative has its own proposal revision");
    equal(processor.read(offered, "/reservations/booking-1/proposalBlueId"),
        processor.read(offered, "/activation/reviewedGrants/seller/proposal"), "Activation owns the selected proposal grant");
    equal(7200L, integer(processor.read(offered, "/activation/reviewedGrants/seller/basis")), "The held grant retains its amount");
    assertBlocked(processor, offered, "customer", "acceptProposal", confirmation(processor, pending), true);
    var revised = invoke(processor, offered, "customer", "updateParty_customer", map("type", "Activation/Party Update Input",
        "replacement", party("customer", "Customer profile revised")));
    equal(integer(processor.read(offered, "/activation/revision")) + 1,
        integer(processor.read(revised, "/activation/revision")), "A real party update advances the commercial revision");
    equal(processor.read(offered, "/reservations/booking-1/proposalBlueId"),
        processor.read(revised, "/reservations/booking-1/proposalBlueId"), "The offered Schedule proposal is still current");
    equal(processor.read(offered, "/activation/reviewedGrants/seller"),
        processor.read(revised, "/activation/reviewedGrants/seller"), "The original seller's approval grant is stale");
    assertFailure(processor, revised, "customer", "acceptProposal", confirmation(processor, revised),
        "REVIEWED_APPROVAL_GRANT_REQUIRED");
    var agreedResult = apply(processor, offered, "customer", "acceptProposal", confirmation(processor, offered));
    var agreed = agreedResult.document();
    equal(List.of("seller"), acceptedParties(processor, agreedResult), "The buyer closes exactly one seller authorization");
    equal(true, processor.read(agreed, "/activation/active"), "Exact acceptance of the seller's alternative activates the Order");
    equal(true, processor.read(agreed, "/activation/approved/seller"), "Buyer acceptance closes the seller's reviewed proposal");
    equal(processor.read(offered, "/reservations/booking-1/proposalBlueId"),
        processor.read(agreed, "/reservations/booking-1/proposalBlueId"), "Acceptance retains the exact chosen proposal");
    equal(processor.read(pending, "/activation/revision"), processor.read(agreed, "/activation/revision"),
        "Date substitution does not change the commercial revision");
    equal(Long.toString(START_MICROS * 2), String.valueOf(processor.read(agreed, "/booking/confirmedStartMicros")),
        "The new proposal's date is the confirmed service date");
    System.out.println("PASS alternative booking needs the exact customer's acceptance");
  }

  private static void invalidReviewRollsBack(Contracts processor) {
    var source = booking(processor, true, true);
    source.put("amountMinor", 7300);
    var pending = initialize(processor, source);
    assertFailure(processor, pending, "seller", "confirmReservation", confirmation(processor, pending),
        "REVIEWED_APPROVAL_SCOPE_CHANGED");
    equal("pending_supplier", processor.read(pending, "/booking/status"), "A mismatched approval amount cannot release the booking");
    equal(false, processor.read(pending, "/activation/active"), "A rejected booking cannot activate the Order");
    System.out.println("PASS mismatch rolls back booking, approval, request record and emitted effects");
  }

  private static void invalidReviewEvidence(Contracts processor) {
    var source = booking(processor, true, true);
    var clauses = fields(source.get("clauses"));
    var activationParameters = fields(fields(clauses.get("activation")).get("parameters"));
    var allowed = new java.util.ArrayList<Object>((List<?>) activationParameters.get("preActivationOperations"));
    allowed.add("fixtureMismatchedReview");
    activationParameters.put("preActivationOperations", allowed);
    String group = "/reservations/booking-1";
    var payload = map("clause", "reservation", "subject", "booking-1",
        "decision", "approve", "actor", "seller", "proposal", map("$document", group + "/proposalBlueId"),
        "basis", map("$document", group + "/proposal/amountMinor"),
        "recordBlueId", corruptWhen("record", map("$nodeBlueId", map("$document", group))),
        "requestBlueId", corruptWhen("request", map("$nodeBlueId", map("$binding", "call/request"))));
    clauses.put("corruptWitness", map("type", "Features/Feature Clause",
        "parameters", map("actions", map("publish", map("do", List.of(map("$appendEvent",
            map("$merge", List.of(map("type", "Schedule/Reservation Reviewed"), payload))))))),
        "bindings", map("publish", map("fixtureMismatchedReview", route("seller")))));
    var pending = initialize(processor, source);
    assertFailure(processor, pending, "seller", "fixtureMismatchedReview", map("mutate", "record"),
        "REVIEWED_APPROVAL_SCOPE_CHANGED");
    assertFailure(processor, pending, "seller", "fixtureMismatchedReview", map("mutate", "request"),
        "REVIEWED_APPROVAL_SCOPE_CHANGED");
    System.out.println("PASS T08 same actor, group and price with mismatched reviewed record or request rolls back");
  }

  private static Object corruptWhen(String evidence, Object original) {
    return map("$choose", map("cond", map("$eq", List.of(map("$binding", "call/request/mutate"), evidence)),
        "then", "different-exact-identity", "else", original));
  }

  private static void widerReviewedAlternatives(Contracts processor) {
    var waiting = initialize(processor, booking(processor, true, true));
    String group = "/reservations/booking-1";
    equal("original-service", processor.read(waiting, group + "/proposal/quote/lines/0/itemId"), "Original service");
    var samePrice = alternative(processor, waiting, "booking-1", "seller", START_MICROS * 2);
    var offered = invoke(processor, waiting, "seller", "proposeAlternative", samePrice);
    equal("booking", processor.read(offered, group + "/proposal/quote/lines/0/itemId"), "Native Schedule permits a changed item");
    equal(7200L, integer(processor.read(offered, group + "/proposal/amountMinor")), "Funding basis preserved");
    assertBlocked(processor, offered, "seller", "acceptProposal", confirmation(processor, offered), true);
    assertFailure(processor, offered, "customer", "acceptProposal", confirmation(processor, waiting), "STALE_PROPOSAL");
    var accepted = invoke(processor, offered, "customer", "acceptProposal", confirmation(processor, offered));
    equal(true, processor.read(accepted, "/activation/approved/seller"), "Exact customer accepts the existing wider policy");

    var two = alternative(processor, waiting, "booking-1", "seller", START_MICROS * 2);
    two.put("lines", List.of(map("itemId", "booking", "quantity", 2)));
    alternativeProduct(two).put("unitAmountMinor", 3600);
    var twoOffered = invoke(processor, waiting, "seller", "proposeAlternative", two);
    equal(2L, integer(processor.read(twoOffered, group + "/proposal/quote/lines/0/quantity")), "Same total permits a changed quantity");
    equal(7200L, integer(processor.read(twoOffered, group + "/proposal/amountMinor")), "The same financial scope is required");

    var wrongPrice = alternative(processor, waiting, "booking-1", "seller", START_MICROS * 2);
    alternativeProduct(wrongPrice).put("unitAmountMinor", 7201);
    assertFailure(processor, waiting, "seller", "proposeAlternative", wrongPrice, "REVIEWED_APPROVAL_SCOPE_CHANGED");
    var otherSeller = alternative(processor, waiting, "booking-1", "other-seller", START_MICROS * 2);
    assertFailure(processor, waiting, "seller", "proposeAlternative", otherSeller, "ALTERNATIVE_SELLER_OR_CURRENCY_MISMATCH");
    var wrongCurrency = alternative(processor, waiting, "booking-1", "seller", START_MICROS * 2);
    fields(wrongCurrency.get("catalog")).put("currency", "EUR");
    assertFailure(processor, waiting, "seller", "proposeAlternative", wrongCurrency, "ALTERNATIVE_SELLER_OR_CURRENCY_MISMATCH");
    System.out.println("PASS T10 same-price item and quantity changes remain reviewable; changed amount, seller, currency and wrong/stale buyer are refused");
  }

  private static Map<String, Object> alternativeProduct(Map<String, Object> input) {
    return fields(fields(fields(input.get("catalog")).get("entries")).get("booking"));
  }

  private static void independentBookings(Contracts processor) {
    var waiting = initialize(processor, independentSource(processor, "hotel", "restaurant"));
    var hotel = confirmation(processor, waiting, "hotel");
    assertFailure(processor, waiting, "hotel", "confirmHotel", confirmation(processor, waiting, "restaurant"),
        "REVIEWED_APPROVAL_PARTY_REQUIRED");
    assertBlocked(processor, waiting, "hotel", "confirmRestaurant", confirmation(processor, waiting, "restaurant"), true);
    assertBlocked(processor, waiting, "restaurant", "approve_restaurant", approval(processor, waiting), true);
    assertFailure(processor, waiting, "hotel", "offerHotel",
        alternative(processor, waiting, "hotel", "multi-service", START_MICROS * 3),
        "REVIEWED_APPROVAL_DELEGATION_REQUIRED");
    var hotelResult = apply(processor, waiting, "hotel", "confirmHotel", hotel);
    var hotelConfirmed = hotelResult.document();
    equal(List.of("hotel"), acceptedParties(processor, hotelResult), "Only the hotel approval was emitted");
    equal("confirmed", processor.read(hotelConfirmed, "/reservations/hotel/status"), "Hotel confirms only its reservation");
    equal("pending_supplier", processor.read(hotelConfirmed, "/reservations/restaurant/status"), "Restaurant stays pending");
    equal(true, processor.read(hotelConfirmed, "/activation/approved/hotel"), "Hotel gives its own approval");
    check(!Boolean.TRUE.equals(processor.read(hotelConfirmed, "/activation/approved/restaurant")),
        "Hotel cannot grant restaurant approval");
    equal(false, processor.read(hotelConfirmed, "/activation/active"), "Both identified services are required");
    var restaurantResult = apply(processor, hotelConfirmed, "restaurant", "confirmRestaurant",
        confirmation(processor, hotelConfirmed, "restaurant"));
    var bothConfirmed = restaurantResult.document();
    equal(List.of("restaurant"), acceptedParties(processor, restaurantResult), "The second service emits only its own approval");
    equal(true, processor.read(bothConfirmed, "/activation/approved/restaurant"), "Restaurant independently approves");
    equal(true, processor.read(bothConfirmed, "/activation/active"), "Both correctly scoped approvals activate the Order");
    equal(7200L, integer(processor.read(bothConfirmed, "/reservations/hotel/proposal/amountMinor")), "Hotel amount stays isolated");
    equal(7200L, integer(processor.read(bothConfirmed, "/reservations/restaurant/proposal/amountMinor")), "Restaurant amount stays isolated");
    equal(START_MICROS, integer(processor.read(bothConfirmed, "/reservations/hotel/confirmedStartMicros")), "Hotel retains its own time");
    equal(START_MICROS * 2, integer(processor.read(bothConfirmed, "/reservations/restaurant/confirmedStartMicros")), "Restaurant retains its own time");
    var mismatched = independentSource(processor, "hotel", "restaurant");
    mismatched.put("restaurantAmountMinor", 7300);
    var waitingWithMismatch = initialize(processor, mismatched);
    var admittedHotel = invoke(processor, waitingWithMismatch, "hotel", "confirmHotel", confirmation(processor, waitingWithMismatch, "hotel"));
    assertFailure(processor, admittedHotel, "restaurant", "confirmRestaurant", confirmation(processor, admittedHotel, "restaurant"),
        "REVIEWED_APPROVAL_SCOPE_CHANGED");
    equal(true, processor.read(admittedHotel, "/activation/approved/hotel"), "Restaurant denial preserves prior approved hotel");
    System.out.println("PASS independent hotel and restaurant reviews preserve scope, price and approval");
  }

  private static void duplicateReviewedSelector(Contracts processor) {
    var source = independentSource(processor, "hotel", "restaurant");
    var activation = fields(fields(source.get("clauses")).get("activation"));
    var reviews = fields(fields(activation.get("parameters")).get("reviewedApprovals"));
    fields(reviews.get("restaurant")).put("event", fields(reviews.get("hotel")).get("event"));
    var result = processor.initialize(source);
    equal(false, result.commits(), "Two identical selectors cannot configure independent approval");
    try {
      ClauseGasProbe.diagnose(processor, source);
      throw new AssertionError("Expected duplicated reviewed approval source rejection");
    } catch (blue.bex.BexError failure) {
      equal("DUPLICATE_REVIEWED_APPROVAL_SOURCE", failure.getMessage(), "Exact duplicate selector rejection");
    }
    System.out.println("PASS R04 identical event selectors fail native approval planning");
  }

  private static void reviewedRoleNamesDoNotCollide(Contracts processor) {
    var waiting = initialize(processor, independentSource(processor, "case", "caseHandler"));
    var first = apply(processor, waiting, "case", "confirmHotel", confirmation(processor, waiting, "hotel"));
    equal(List.of("case"), acceptedParties(processor, first), "The first valid role owns its generated workflow");
    equal(false, processor.read(first.document(), "/activation/active"), "Only one role has approved");
    var second = apply(processor, first.document(), "caseHandler", "confirmRestaurant",
        confirmation(processor, first.document(), "restaurant"));
    equal(List.of("caseHandler"), acceptedParties(processor, second), "The related name resolves to its own workflow");
    equal(true, processor.read(second.document(), "/activation/active"), "Both generated workflows are reachable");
    System.out.println("PASS reviewed channel and handler names remain distinct for case and caseHandler");
  }

  private static Map<String,Object> independentSource(Contracts processor, String hotelRole, String restaurantRole) {
    var source = booking(processor, true, false);
    var snapshot = fields(source.get("orderSnapshot"));
    var quote = map("supplierId", "multi-service", "currency", "USD", "totalMinor", 14400,
        "lines", List.of(map("lineTotalMinor", 7200), map("lineTotalMinor", 7200)));
    snapshot.put("quote", quote);
    snapshot.put("quoteBlueId", identity(processor, quote));
    snapshot.put("groups", List.of(map("id", "hotel", "lineIndices", List.of(0), "proposedStartMicros", START_MICROS),
        map("id", "restaurant", "lineIndices", List.of(1), "proposedStartMicros", START_MICROS * 2)));
    source.put("amountMinor", 14400);
    source.put("hotelAmountMinor", 7200);
    source.put("restaurantAmountMinor", 7200);
    var clauses = fields(source.get("clauses"));
    clauses.remove("fixtureEvent");
    var bindings = fields(fields(clauses.get("reservation")).get("bindings"));
    bindings.clear();
    bindings.put("confirm", map("confirmHotel", route(hotelRole), "confirmRestaurant", route(restaurantRole)));
    bindings.put("alternative", map("offerHotel", route(hotelRole)));
    var hotelReview = reviewedApproval("hotel", "/hotelAmountMinor");
    hotelReview.remove("acceptanceBy");
    clauses.put("activation", activation(List.of(hotelRole, restaurantRole, "customer"), List.of(hotelRole, restaurantRole),
        List.of("confirmHotel", "confirmRestaurant", "offerHotel"), List.of("cx.reservation.initialize._automatic_source"),
        map(hotelRole, hotelReview, restaurantRole, reviewedApproval("restaurant", "/restaurantAmountMinor"))));
    return source;
  }

  private static void independentSellerDecision(Contracts processor) {
    var before = initialize(processor, map("name", "Order without Schedule",
        "type", "Orders/Order with Seller Decision", "amountMinor", 7200,
        "clauses", map("activation", activation(List.of("rejectOrder", "recordAlternative"), List.of()),
            "orderDecision", map("parameters", map("activationOperations", List.of("recordAlternative"))),
            "probe", map("type", "Features/Feature Clause",
                "parameters", map("actions", map("record", map("do", List.of(map("$appendChange",
                    map("op", "add", "path", "/acceptedAlternative", "val", true)))))),
                "bindings", map("record", map("recordAlternative", route("seller")))))));
    var approved = invoke(processor, before, "seller", "approve_seller", approval(processor, before));
    equal(true, processor.read(approved, "/activation/active"), "Ordinary seller approval needs no Booking clause");
    var alternative = invoke(processor, before, "seller", "recordAlternative", map());
    equal(true, processor.read(alternative, "/acceptedAlternative"), "Author-declared operation is usable before rejection");
    var rejected = invoke(processor, before, "seller", "rejectOrder", approval(processor, before));
    equal("REJECTED", processor.read(rejected, "/orderDecision/status"), "Seller review rejected the Order");
    assertBlocked(processor, rejected, "seller", "approve_seller", approval(processor, rejected), true);
    assertBlocked(processor, rejected, "seller", "recordAlternative", map(), true);
    System.out.println("PASS Order rejection with standalone approval and authored alternative operation veto");
  }

  private static void wholeOrderAcceptance(Contracts processor) {
    var source = booking(processor, true, true);
    source.put("type", "Orders/Order with Lifecycle Guards");
    source.put("contracts", map(
        "seller", external("seller"),
        "orderOpen", map("constants", map(
            "actions", map("reservation", List.of("confirm", "alternative", "accept")),
            "closedStates", map("commercialDecision", map("path", "/cancellationDecision/status",
                "equals", "accepted", "reason", "ORDER_CANCELLED", "approvals", List.of("seller"))))),
        "emitReviewed", map("type", "Contracts/Sequential Workflow Operation", "channel", "seller",
            "steps", List.of(map("type", "Contracts/Compute",
                "do", List.of(map("$appendEvent", map("$binding", "call/request"))))))));
    Map<String,Object> clauses = fields(source.get("clauses"));
    clauses.remove("fixtureEvent");
    var scheduleBindings = fields(fields(clauses.get("reservation")).get("bindings"));
    scheduleBindings.put("confirm", map("confirmTime", route("seller")));
    scheduleBindings.put("alternative", map("offerAnotherTime", route("seller")));
    scheduleBindings.put("accept", map("acceptNewTime", route("customer")));
    var close = fields(fields(scheduleBindings.get("close")).get("afterCancellation"));
    fields(close.get("params")).put("reason", map("$document", "/cancellationDecision/reason"));
    var parameters = fields(fields(clauses.get("activation")).get("parameters"));
    parameters.put("preActivationOperations", List.of("confirmTime", "offerAnotherTime", "acceptNewTime", "cancelOrder", "emitReviewed"));
    parameters.remove("preActivationChannels");
    parameters.put("preActivationConnections", List.of(
        map("clause", "reservation", "action", "initialize", "automatic", true),
        map("clause", "reservation", "action", "close", "connection", "afterCancellation"),
        map("clause", "cancellation", "action", "refreshAvailability", "automatic", true)));
    clauses.put("cancellation", map("type", "Commerce/Whole Order Cancellation Policy",
        "parameters", map("freeCancellationHoursBeforeStart", 1, "lateCancellationChargePercent", 25),
        "bindings", map("amount", "/amountMinor", "decision", "/cancellationDecision", "serviceStart", "/booking/confirmedStartMicros",
            "confirmation", "/activation/approved/seller", "accept", map("cancelOrder", route("customer")))));
    var before = initialize(processor, source);
    var confirmed = invoke(processor, before, "seller", "confirmTime", confirmation(processor, before));
    equal("confirmed", processor.read(confirmed, "/booking/status"), "Renamed workflow confirms the open reservation");
    equal(true, processor.read(confirmed, "/activation/approved/seller"), "Reviewed reservation approves the open Order");
    var request = map("key", "operational-close", "reason", "Customer decided to cancel the Order");
    var cancelled = invoke(processor, before, "customer", "cancelOrder", request);
    equal("accepted", processor.read(cancelled, "/cancellationDecision/status"), "Stock Commerce accepts the real cancellation");
    equal("cancelled", processor.read(cancelled, "/booking/status"), "Stock Commerce event closes the pending native reservation");
    equal(map(), processor.read(cancelled, "/reservationRequests"), "Stock decision closes Schedule without adding a request key");
    var routedRequests = map("confirmTime", confirmation(processor, before), "acceptNewTime", confirmation(processor, before),
        "offerAnotherTime", alternative(processor, before, "booking-1", "seller", START_MICROS * 2),
        "approve_seller", approval(processor, cancelled));
    for (var route : routedRequests.entrySet()) {
      var operation = route.getKey();
      var role = operation.equals("acceptNewTime") ? "customer" : "seller";
      var denied = apply(processor, cancelled, role, operation, route.getValue());
      assertCancellationVeto(denied);
      assertSameState(processor, cancelled, denied, operation);
      equal(List.of(), processor.emitted(denied), "Terminal veto emits no effects for " + operation);
    }
    var reviewed = apply(processor, cancelled, "seller", "emitReviewed",
        reviewedApproval("booking-1", "/amountMinor").get("event"));
    assertCancellationVeto(reviewed);
    assertSameState(processor, cancelled, reviewed, "reviewed approval delivery");
    var retry = apply(processor, cancelled, "customer", "cancelOrder", request);
    var replayed = retry.document();
    equal(processor.read(cancelled, "/cancellationDecision"), processor.read(replayed, "/cancellationDecision"), "Commerce decision replay is stable");
    equal(processor.read(cancelled, "/reservations"), processor.read(replayed, "/reservations"), "Schedule closure replay is stable");
    equal(List.of(), processor.emitted(retry), "Cancellation replay publishes no duplicate effect");
    System.out.println("PASS Order lifecycle closes renamed Schedule routes and reviewed approval while Commerce cancellation remains idempotent");
  }

  private static void assertCancellationVeto(Contracts.Result denial) {
    check(WireData.write(denial.observations()).contains("\"reason\":\"ORDER_CANCELLED\""),
        "The Order records the terminal native dispatch decision");
  }

  @SuppressWarnings("unchecked")
  private static Map<String,Object> fields(Object value) {
    return (Map<String,Object>) value;
  }

  private static Map<String,Object> booking(Contracts processor, boolean verified, boolean output) {
    var quote = map("supplierId", "seller", "currency", "USD", "totalMinor", 7200,
        "lines", List.of(map("itemId", "original-service", "quantity", 1, "lineTotalMinor", 7200)));
    var terms = map("agreementDescription", "Local native fixture", "fulfilmentText", "Book a two-hour class",
        "confirmationMode", "supplier", "dateRequired", true);
    var snapshot = map("quote", quote, "quoteBlueId", identity(processor, quote), "terms", terms,
        "termsBlueId", identity(processor, terms), "groups", List.of(map("id", "booking-1", "lineIndices", List.of(0),
            "proposedStartMicros", START_MICROS)));
    var bindings = map("confirm", map("confirmReservation", route("seller")), "cancel", map("cancelReservation", route("customer")),
        "alternative", map("proposeAlternative", route("seller")), "accept", map("acceptProposal", route("customer")), "close", map("afterCancellation", map("on", "event", "event", cancellationEvent(),
            "params", map("groupId", "booking-1", "reason", "Customer ended the booking"))));
    if (output) bindings.put("wholeReservation", "/booking");
    var schedule = map("type", "Schedule/Reservation Clause",
        "parameters", map("conditions",
            map("confirm", map("$eq", List.of(map("$document", "/reviewVerified"), true)))), "bindings", bindings);
    return map("type", "Orders/Order with Clauses", "name", "Stand-alone scheduled Order", "amountMinor", 7200,
        "orderSnapshot", snapshot, "reviewVerified", verified,
        "clauses", map("activation", activation(List.of("seller", "customer"), List.of("seller"),
            List.of("confirmReservation", "proposeAlternative", "acceptProposal", "cancelReservation", "emitCancellation"),
            List.of("cx.reservation.initialize._automatic_source", "cx.reservation.close.afterCancellation_source"),
            map("seller", reviewedApproval("booking-1", "/amountMinor"))),
            "reservation", schedule, "fixtureEvent", map("type", "Features/Feature Clause",
                "parameters", map("actions", map("emit", map("do", List.of(map("$appendEvent", cancellationEvent()))))),
                "bindings", map("emit", map("emitCancellation", route("customer"))))));
  }

  private static Map<String,Object> cancellationEvent() {
    return map("type", "Commerce/Domain Event", "kind", "Order Cancellation Accepted", "clause", "cancellation");
  }

  private static String identity(Contracts processor, Object node) {
    return NativeRuntime.identity(processor.execution().values().source(node));
  }

  private static Map<String,Object> activation(List<String> operations, List<String> channels) {
    return activation(List.of("seller", "customer"), List.of("seller"), operations, channels, map());
  }

  private static Map<String,Object> activation(List<String> roles, List<String> required, List<String> operations,
      List<String> channels, Map<String,Object> reviewed) {
    var parties = map();
    for (String role : roles) {
      parties.put(role, party(role, role));
    }
    var parameters = map("parties", parties, "required", required,
        "preActivationOperations", operations, "preActivationChannels", channels);
    if (!reviewed.isEmpty()) parameters.put("reviewedApprovals", reviewed);
    return map("type", "Activation/Activation Clause", "parameters", parameters);
  }

  private static Map<String,Object> reviewedApproval(String groupId, String amount) {
    return map("event", map("type", "Schedule/Reservation Reviewed", "clause", "reservation", "subject", groupId),
        "source", "/reservations/" + groupId, "basis", amount, "acceptanceBy", "customer");
  }

  private static Map<String,Object> external(String role) {
    return map("type", "Contracts/External Channel", "event", map("source", role));
  }

  private static Map<String,Object> party(String role, String displayName) {
    return map("type", "Parties/Party", "myosAccountId", role + "-account", "displayName", displayName,
        "readerKeys", List.of("key-" + role), "lead", map("channel", external(role)));
  }

  private static Map<String,Object> route(String party) {
    return map("on", "workflow", "party", party, "input", true, "requireExactDocumentVersion", true);
  }

  private static Map<String,Object> confirmation(Contracts processor, Contracts.Document order) {
    return confirmation(processor, order, "booking-1");
  }

  private static Map<String,Object> confirmation(Contracts processor, Contracts.Document order, String group) {
    return map("key", "confirm-" + group, "groupId", group,
        "expectedProposalBlueId", processor.read(order, "/reservations/" + group + "/proposalBlueId"));
  }

  private static Map<String,Object> alternative(Contracts processor, Contracts.Document order, String group,
      String supplier, long proposedStart) {
    var catalogue = map("supplierId", supplier, "revision", 1, "currency", "USD", "entries",
        map("booking", map("label", "Booking", "description", "Reviewed service", "pricingUnit", "per_unit",
            "unitAmountMinor", 7200, "dateRequired", false)));
    return map("key", "offer-" + group, "groupId", group, "proposedStartMicros", proposedStart, "catalog", catalogue,
        "expectedProposalBlueId", processor.read(order, "/reservations/" + group + "/proposalBlueId"),
        "lines", List.of(map("itemId", "booking", "quantity", 1)));
  }

  private static Map<String,Object> approval(Contracts processor, Contracts.Document order) {
    return map("revision", processor.read(order, "/activation/revision"));
  }

  private static Object event(Contracts.Document document, String actor, String operation, Object request, boolean exact) {
    return map("source", actor, "operation", map("type", "Contracts/Operation Request", "channel", actor,
        "operation", operation, "request", request, "document", map("blueId", document.blueId()),
        "requireExactDocumentVersion", exact));
  }

  private static Contracts.Document initialize(Contracts processor, Map<String,Object> source) {
    var result = processor.initialize(source);
    if (!result.commits()) ClauseGasProbe.diagnose(processor, source);
    check(result.commits(), "Initialize " + source.get("name"));
    return result.document();
  }

  private static Contracts.Document invoke(Contracts processor, Contracts.Document order, String actor,
      String operation, Object request) {
    return apply(processor, order, actor, operation, request).document();
  }

  private static Contracts.Result apply(Contracts processor, Contracts.Document order, String actor,
      String operation, Object request) {
    Object input = event(order, actor, operation, request, true);
    var result = processor.process(order, input, START_MICROS / 2);
    if (!result.commits()) ClauseGasProbe.diagnose(processor, order, input, START_MICROS / 2);
    check(result.commits(), "Apply " + operation);
    return result;
  }

  private static void assertBlocked(Contracts processor, Contracts.Document order, String actor,
      String operation, Object request, boolean exact) {
    var result = processor.process(order, event(order, actor, operation, request, exact), START_MICROS / 2);
    equal(List.of(), processor.emitted(result), "Denied operation has no emitted effects: " + operation);
    if (!result.commits()) return;
    assertSameState(processor, order, result, operation);
  }

  private static void assertFailure(Contracts processor, Contracts.Document order, String actor,
      String operation, Object request, String errorCode) {
    var input = event(order, actor, operation, request, true);
    var result = processor.process(order, input, START_MICROS / 2);
    equal(false, result.commits(), "Refused " + operation + " cannot commit a provisional change");
    equal(List.of(), processor.emitted(result), "Refused " + operation + " emits no public effects");
    assertSameState(processor, order, result, operation);
    try {
      ClauseGasProbe.diagnose(processor, order, input, START_MICROS / 2);
      throw new AssertionError("Expected " + errorCode);
    } catch (blue.bex.BexError failure) {
      equal(errorCode, failure.getMessage(), "Expected reviewed approval rejection from Activation");
    }
  }

  private static void assertSameState(Contracts processor, Contracts.Document before, Contracts.Result result,
      String operation) {
    for (String path : List.of("/activation/approved", "/activation/active", "/orderDecision", "/reservations",
        "/activation/reviewedGrants", "/reservationRequests", "/booking", "/acceptedAlternative")) {
      equal(processor.read(before, path), processor.read(result.document(), path), "Denied " + operation + " preserves " + path);
    }
  }

  private static long integer(Object value) {
    return Long.parseLong(String.valueOf(value));
  }

  private static List<Object> acceptedParties(Contracts processor, Contracts.Result result) {
    var values = processor.execution().values();
    var accepted = values.source(map("type", "Activation/Terms Accepted"));
    var type = NativeRuntime.identity(values.exact(values.select(accepted, "/type")));
    var revision = processor.read(result.document(), "/activation/revision");
    return result.publicEvents().stream()
        .map(event -> new Exact.Ref(event.get("event").toString()))
        .filter(event -> type.equals(NativeRuntime.identity(values.exact(values.select(event, "/type")))))
        .map(event -> fields(values.bexData(event)))
        .map(event -> {
          equal(integer(revision), integer(event.get("revision")), "Acceptance event names the current revision");
          return event.get("party");
        })
        .toList();
  }

  private static void equal(Object expected, Object result, String description) {
    check(Objects.equals(expected, result), description + ": expected " + expected + ", got " + result);
  }

  private static void check(boolean condition, String description) {
    if (!condition) throw new AssertionError(description);
  }

  private static Map<String,Object> map(Object... pairs) {
    var result = new LinkedHashMap<String,Object>();
    for (int i = 0; i < pairs.length; i += 2) result.put((String) pairs[i], pairs[i + 1]);
    return result;
  }
}
