package blue.core;

import static blue.core.Values.*;
import static org.junit.jupiter.api.Assertions.*;

import blue.coordination.Coordination;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/** Business's original-authorized-payment orchestration with Core services and a local Stripe boundary. */
final class CatalogOrderIndependentPrecheckout {
  private static final long AMOUNT = 3895;
  private final HostSource records;
  private final AgentContext seller;
  private final PaymentPrecheckouts checkouts;
  private final StripeFixture stripe;
  private final Map<String, Object> financialRequest;
  private final String checkoutId;
  private final String intent;

  private CatalogOrderIndependentPrecheckout(HostSource records, AgentContext seller, PaymentPrecheckouts checkouts,
      StripeFixture stripe, Map<String, Object> financialRequest, String checkoutId, String intent) {
    this.records = records;
    this.seller = seller;
    this.checkouts = checkouts;
    this.stripe = stripe;
    this.financialRequest = financialRequest;
    this.checkoutId = checkoutId;
    this.intent = intent;
  }

  static CatalogOrderIndependentPrecheckout authorize(AcceptedBootstrapTestSupport fixture, Tenant partner,
      AgentContext partnerActor, AgentContext seller, Coordination.Document agreement,
      Map<String, Object> prepareOrder, StripeFixture stripe) {
    var values = obj(prepareOrder.get("values"));
    String requestId = required(prepareOrder, "requestId");
    var selection = map("requestId", requestId, "agreementSessionId", agreement.handle(),
        "agreementVersion", agreement.state().stable().orElseThrow().blueId(), "clauseId", "orders",
        "itemKey", required(prepareOrder, "key"), "preparationRequestId", requestId,
        "applicantEmail", required(values, "customerEmail"), "catalogRevision", values.get("catalogRevision"),
        "lines", values.get("lines"), "groups", values.get("groups"));
    var quote = NativeCataloguePaymentQuote.read(partner, partnerActor, selection);
    assertEquals(AMOUNT, number(quote.get("amountMinor")));
    assertEquals("USD", quote.get("currency"));
    assertEquals(seller.accountId(), quote.get("sellerAccountId"));
    assertEquals(selection.get("agreementVersion"), quote.get("sourceVersion"));
    var price = obj(quote.get("quote"));
    assertEquals(4100L, number(price.get("subtotalMinor")));
    assertEquals(205L, number(price.get("discountMinor")));
    var financialRequest = map("requestId", requestId, "amountMinor", quote.get("amountMinor"),
        "currency", quote.get("currency"), "recipientPaymentAccountId", required(quote, "recipientPaymentAccountId"),
        "applicantEmail", selection.get("applicantEmail"));

    var configuration = StripeConfiguration.from(Map.of(
        "CORE_STRIPE_SECRET_KEY", "sk_test_catalog_fixture",
        "CORE_STRIPE_PUBLISHABLE_KEY", "pk_test_catalog_fixture",
        "CORE_STRIPE_PLATFORM_ACCOUNT_ID", stripe.platform().platformAccountId(),
        "CORE_STRIPE_PAYMENTS_WEBHOOK_SECRET", "whsec_catalog_payments_fixture",
        "CORE_STRIPE_ACCOUNTS_WEBHOOK_SECRET", "whsec_catalog_accounts_fixture"));
    var checkouts = new PaymentPrecheckouts(fixture.host.security, stripe.gateway(), configuration);
    var checkout = checkouts.createFinancial(seller.accountId(), seller, financialRequest);
    String checkoutId = required(checkout, "checkoutId");
    assertEquals("PENDING", checkout.get("authorizationStatus"));
    String intent = required(checkouts.stripeSession(checkoutId), "paymentIntentId");
    assertEquals(AMOUNT, stripe.amount());
    stripe.confirmCard();
    var authorized = checkouts.refresh(checkoutId);
    assertEquals("AUTHORIZED", authorized.get("authorizationStatus"));
    assertEquals(intent, authorized.get("paymentIntentId"));
    assertNull(authorized.get("customerBinding"));
    assertNull(authorized.get("nativeDocumentId"));
    stripe.assertCalls(0);
    System.out.println("PASS Core priced and authorized the two-item checkout before accepting or preparing an Order");
    return new CatalogOrderIndependentPrecheckout(fixture.host.records, seller, checkouts, stripe,
        financialRequest, checkoutId, intent);
  }

  void bind(HumanContext customer, String account) {
    var bound = checkouts.bind(checkoutId, account, customer, map("requestId", financialRequest.get("requestId")));
    assertEquals(account, obj(bound.get("customerBinding")).get("accountId"));
    assertEquals(financialRequest.get("applicantEmail"), obj(bound.get("customerBinding")).get("verifiedEmail"));
    assertEquals("AUTHORIZED", bound.get("authorizationStatus"));
    assertEquals(intent, bound.get("paymentIntentId"));
  }

  String providerReference() {
    return intent;
  }

  boolean adoptedBy(Coordination.Document payment) {
    var purchase = checkouts.view(checkoutId);
    return intent.equals(purchase.get("paymentIntentId"))
        && payment.state().documentId().equals(purchase.get("nativeDocumentId"));
  }

  boolean boundTo(Coordination.Document payment) {
    try (var tx = records.open()) {
      var checkout = records.row(tx, "payment_precheckouts", checkoutId);
      var attempt = records.row(tx, "stripe_payment_attempts", required(checkout, "attemptId"));
      var binding = StripePaymentAttempts.nativeBinding(records, tx, attempt);
      return binding != null && intent.equals(attempt.get("stripeIntentId"))
          && payment.state().documentId().equals(binding.get("documentId"));
    }
  }

  void assertSecured(Coordination.Document payment) {
    var root = payment.state().stable().orElseThrow().document();
    assertEquals(intent, scalar(obj(root.get("paymentDetails")).get("providerReference")));
    var ledger = obj(root.get("payment"));
    assertEquals(AMOUNT, number(scalar(ledger.get("secured"))));
    assertEquals(0L, number(scalar(ledger.get("completed"))));
    assertEffects(payment, Set.of("SECURE"));
    stripe.assertCalls(0);
  }

  void assertCaptured(Coordination.Document payment) {
    var root = payment.state().stable().orElseThrow().document();
    assertEquals(AMOUNT, number(scalar(obj(root.get("payment")).get("completed"))));
    assertEffects(payment, Set.of("SECURE", "CAPTURE"));
    stripe.assertCalls(1);
  }

  void replay(Coordination.Document payment) {
    var replay = checkouts.createFinancial(seller.accountId(), seller, financialRequest);
    assertEquals(checkoutId, replay.get("checkoutId"));
    assertEquals(intent, replay.get("paymentIntentId"));
    assertCaptured(payment);
  }

  private void assertEffects(Coordination.Document payment, Set<String> actions) {
    assertTrue(adoptedBy(payment), "Original authorization must be owned by this Payment Instruction");
    try (var tx = records.open()) {
      var checkout = records.row(tx, "payment_precheckouts", checkoutId);
      String attemptId = required(checkout, "attemptId");
      var attempt = records.row(tx, "stripe_payment_attempts", attemptId);
      assertEquals(intent, attempt.get("stripeIntentId"));
      assertEquals("NATIVE", attempt.get("financialOwner"));
      var effects = records.select(tx, "stripe_payment_executions", "attempt_id=?", attemptId);
      assertEquals(actions.size(), effects.size());
      assertEquals(actions, new HashSet<>(effects.stream().map(row -> required(row, "action")).toList()));
      for (var effect : effects) {
        assertEquals(payment.state().documentId(), effect.get("documentId"));
        assertEquals(AMOUNT, number(effect.get("amountMinor")));
        assertEquals("SUCCEEDED", effect.get("outcome"));
        assertEquals("CONFIRMED", effect.get("reportStatus"));
      }
    }
  }

  private static Object scalar(Object node) {
    return node instanceof Map<?, ?> value && value.containsKey("value") ? value.get("value") : node;
  }

  /** Count the shared provider's effects independently from Core's durable receipts. */
  static final class StripeFixture {
    private final CurrentHostedPaymentFlow.MockStripe delegate;
    private final StripeGateway gateway;
    private int creates;
    private int authorizations;
    private int captures;
    private int cancellations;

    StripeFixture(HostSource records, String seller) {
      delegate = CurrentHostedPaymentFlow.create(records, seller);
      gateway = (StripeGateway) Proxy.newProxyInstance(StripeGateway.class.getClassLoader(),
          new Class<?>[]{StripeGateway.class}, (proxy, method, args) -> {
            synchronized (this) {
              switch (method.getName()) {
                case "createManualCardIntent" -> creates++;
                case "captureIntent" -> captures++;
                case "cancelIntent" -> cancellations++;
                default -> { }
              }
              try {
                return method.invoke(delegate.gateway(), args);
              } catch (InvocationTargetException failure) {
                throw failure.getCause();
              }
            }
          });
    }

    StripeGateway gateway() {
      return gateway;
    }

    StripeGateway.PlatformIdentity platform() {
      return delegate.platform();
    }

    synchronized long amount() {
      return delegate.amount();
    }

    synchronized void confirmCard() {
      delegate.confirmCard();
      authorizations++;
    }

    private synchronized void assertCalls(int expectedCaptures) {
      assertEquals(1, creates, "One provider PaymentIntent creation");
      assertEquals(1, authorizations, "One provider card authorization");
      assertEquals(expectedCaptures, captures, "Capture the original authorization once after seller approval");
      assertEquals(0, cancellations, "Do not cancel the retained authorization");
    }
  }
}
