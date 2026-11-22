package blue.core;

import static blue.core.Values.*;

import blue.readmodel.EmissionJobs;
import blue.readmodel.EmissionScheduler;
import com.sun.net.httpserver.HttpServer;
import java.lang.reflect.Method;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Local Core HTTP fixture with durable native projections and the real emission dispatcher. */
final class CatalogOrderIndependentGuarantor implements AutoCloseable {
  private final CoreHttpTestSupport projection;
  private final CoreServer server;
  private final HostServices host;
  private final AcceptedBootstrapTestSupport fixture;
  private final TimelineProvider provider;
  private final Map<String,Tenant> bootstrapTenants;
  private final Method tenantLookup;
  private final String guarantor;
  private final String endpoint;
  private PaymentCoreClient client;
  private EmissionScheduler scheduler;
  private String lastWorkerDiagnostic;

  static CatalogOrderIndependentGuarantor open(List<String> accounts, String guarantor) throws Exception {
    Path directory = Path.of(ReadModelConfiguration.required(System.getenv(), "CORE_DATA"));
    var projection = new CoreHttpTestSupport(directory, java.util.function.UnaryOperator.identity());
    CoreServer server = null;
    try {
      server = projection.server(Telemetry.NOOP);
      var runtime = new CatalogOrderIndependentGuarantor(projection, server, guarantor);
      for (String account : accounts) runtime.tenant(account);
      return runtime;
    } catch (Exception | Error failure) {
      if (server != null) {
        try { CoreMcpHttpTest.HttpHarness.close(server); }
        catch (Exception cleanup) { failure.addSuppressed(cleanup); }
      }
      try { projection.close(); }
      catch (RuntimeException cleanup) { failure.addSuppressed(cleanup); }
      throw failure;
    }
  }

  @SuppressWarnings("unchecked")
  private CatalogOrderIndependentGuarantor(CoreHttpTestSupport projection, CoreServer server, String guarantor)
      throws Exception {
    this.projection = projection;
    this.server = server;
    this.guarantor = guarantor;
    host = CoreHttpTestSupport.host(server);
    check(guarantor.equals(host.paymentGuarantor), 500, "fixture_guarantor",
        "Set CORE_PAYMENT_GUARANTOR_ACCOUNT_ID to the fixture account");
    provider = (TimelineProvider) CoreMcpHttpTest.HttpHarness.field(server, "timelineProvider");
    check(provider != null, 500, "fixture_provider", "Set CORE_TIMELINE_PROVIDER_ENDPOINT for the local fixture");
    tenantLookup = CoreServer.class.getDeclaredMethod("tenant", String.class);
    tenantLookup.setAccessible(true);
    CoreMcpHttpTest.HttpHarness.set(server, "recovering", false);
    ((HttpServer) CoreMcpHttpTest.HttpHarness.field(server, "server")).start();
    IndependentProcessHttpTest.Harness.providerWakes(server);
    endpoint = CoreMcpHttpTest.HttpHarness.base(server);

    var records = (Records) CoreMcpHttpTest.HttpHarness.field(server, "registry");
    var secrets = (Secrets) CoreMcpHttpTest.HttpHarness.field(server, "secrets");
    var authentication = new HostHttpFixture(server, AccountRuntimes.defaultBindings());
    fixture = new AcceptedBootstrapTestSupport(records, secrets, authentication, true);
    // Adopt refs in the test helper only. CoreServer remains the journal and worker owner.
    bootstrapTenants = (Map<String,Tenant>) CoreMcpHttpTest.HttpHarness.field(fixture, "tenants");
    CoreMcpHttpTest.HttpHarness.set(fixture, "provider", provider);
  }

  AcceptedBootstrapTestSupport fixture() { return fixture; }
  TimelineProvider provider() { return provider; }

  Tenant tenant(String account) throws Exception {
    var existing = bootstrapTenants.get(account);
    if (existing != null) return existing;
    fixture.human(account);
    HostHttpFixture.activate(server, account);
    var owned = (Tenant) tenantLookup.invoke(server, account);
    bootstrapTenants.put(account, owned);
    return owned;
  }

  Map<String,Object> start(String account, Map<String,Object> input, String request) throws Exception {
    tenant(account);
    return fixture.start(account, input, request);
  }

  void startWorker(StripeGateway stripe, StripeGateway.PlatformIdentity platform) {
    if (scheduler != null) throw new IllegalStateException("Guarantor worker already started");
    var source = host.source;
    var database = source.database.database;
    var principal = new Identity.Principal(guarantor, guarantor + "@example.test", true);
    var key = fixture.host.keyForColdAccount(principal, "Catalog qualification", "catalog-guarantor-worker");
    client = new PaymentCoreClient(endpoint, required(key, "secret"), guarantor, source);
    var operator = new PaymentExecutions(source, new StripePaymentExecutions(source, stripe, platform));
    var handler = new PaymentGuarantorHandler(source, client, guarantor, operator,
        new StripeRefundExecutions(source, stripe, platform), new StripeAccountTransfers(source, stripe, platform));
    var delivery = new PaymentCheckoutDelivery(source, client, guarantor, operator, this::logWorkerDiagnostic);
    var subscription = PaymentGuarantorHandler.subscription(guarantor, source.controlIdentity);
    scheduler = new EmissionScheduler(database, new EmissionJobs(database),
        List.of(new EmissionScheduler.Registration(subscription, job -> {
          try {
            return handler.advance(job);
          } catch (Problem failure) {
            logWorkerDiagnostic(failure.code);
            throw failure;
          }
        })),
        new EmissionScheduler.Configuration(1, Duration.ofMillis(100), Duration.ofMillis(200),
            Duration.ofSeconds(1), Duration.ofSeconds(30), 50),
        List.of(delivery.task(Duration.ofMillis(200), 50)));
    scheduler.start();
  }

  private void logWorkerDiagnostic(String code) {
    try {
      var tenant = bootstrapTenants.get(guarantor);
      var receipts = host.source.database.read(connection -> {
        var result = new ArrayList<Map<String,Object>>();
        try (var query = SourceDatabase.statement(connection, """
            SELECT s.operation_name,s.admission_id,a.status,
                   s.requester_user_id=a.requester_user_id AND s.membership_generation=a.requester_generation,
                   a.body->'problem'->>'title'
            FROM core_source.payment_operation_submissions s
            LEFT JOIN read_model.admissions a ON a.account_id=s.account_id AND a.admission_id=s.admission_id
            WHERE s.namespace=? AND s.account_id=? ORDER BY s.created_at,s.operation_name LIMIT 25
            """, host.source.namespace, guarantor); var rows = query.executeQuery()) {
          while (rows.next()) {
            String admission = rows.getString(2);
            var nativeReceipt = admission == null ? null : tenant.records.get("admissions", admission);
            result.add(map("operation", rows.getString(1), "nativeStatus", nativeReceipt == null ? null : nativeReceipt.get("status"),
                "projectedStatus", rows.getString(3), "projectedRequesterMatches", rows.getObject(4),
                "projectedProblem", rows.getString(5)));
          }
        }
        return result;
      });
      String diagnostic = blue.language.next.WireData.write(map("code", code, "admissions", receipts));
      if (!Objects.equals(lastWorkerDiagnostic, diagnostic)) {
        System.out.println("Guarantor worker diagnostics " + diagnostic);
        lastWorkerDiagnostic = diagnostic;
      }
    } catch (RuntimeException failure) {
      System.out.println("Guarantor worker diagnostics unavailable: " + failure.getClass().getSimpleName());
    }
  }

  Map<String,String> jobStatuses(String document) {
    return host.source.database.read(connection -> {
      var result = new LinkedHashMap<String,String>();
      try (var query = SourceDatabase.statement(connection, """
          SELECT event_type_blue_id,status FROM core_source.emission_jobs
          WHERE account_id=? AND document_id=? AND handler_type='payment-guarantor-v1'
          ORDER BY created_at,job_id
          """, guarantor, document); var rows = query.executeQuery()) {
        while (rows.next()) result.put(rows.getString(1), rows.getString(2));
      }
      return result;
    });
  }

  @Override public void close() throws Exception {
    // Finish real operator callbacks before stopping their HTTP destination and SQL projection.
    if (scheduler != null) scheduler.close();
    try {
      if (client != null) client.close();
      CoreMcpHttpTest.HttpHarness.close(server);
    } finally {
      projection.close();
    }
  }
}
