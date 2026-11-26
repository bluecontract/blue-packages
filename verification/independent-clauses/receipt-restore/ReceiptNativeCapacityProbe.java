import blue.contracts.ClauseGasProbe;
import blue.contracts.Contracts;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.Exact;
import blue.language.next.NativeRuntime;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Measures native dispatch over initialized managed Orders with modeled payment effects. */
public final class ReceiptNativeCapacityProbe {
  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]).toAbsolutePath().normalize();
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    int orderCount = args.length > 1 ? Integer.parseInt(args[1]) : 80;
    try (var blue = packages.language(); var runtime = new AuthoringRuntime(QualificationRuntime.bindings())) {
      run(runtime.processor(blue), orderCount);
    }
  }

  static void run(Contracts engine, int count) {
    var orders = m();
    for (int n=0; n<count; n++) {
      orders.put("order-"+n,m("name","Receipt capacity order "+n,
          "contracts",m(),"activation",m("active",true),"payment",m("type","PaymentInstruction/Payment Instruction",
              "paymentTerms",m("currency","USD"),"payment",m("completed",7200,"reversed",5400))));
    }
    var channel=m("type","Contracts/External Channel","event",m("source","merchant"));
    var source=m("name","Receipt capacity Agreement","type","Agreements/Agreement with Clauses","orders",orders,
        "terms",m("currency","USD"),"fixtureEntries",m(),
        "contracts",m("merchant",channel),
        "clauses",m("activation",m("type","Activation/Activation Clause","parameters",m("parties",m("merchant",
            m("type","Parties/Party","myosAccountId","merchant","readerKeys",List.of("fixture-reader"),"lead",m("channel",channel))),
            "required",List.of())),
          "receipts",m("type","Payment/Receipts Clause","bindings",m("entries","/fixtureEntries",
              "reconcile",m("afterAccessRestored",m("on","event","event",m("type","Parties/Document Access Restored"))))),
          "commission",m("type","Ledger/Ledger Clause","bindings",m("state","/commission","receipts","/receipts",
              "orders","/orders","orderEntries","/fixtureEntries","frozenRate","/domainTerms/commissionTerms/commissionBps",
              "accruePercent",m("accrue",m("on","event","event",m("type","Events/Event","kind","Confirmed Receipts Changed"))))),
          "fixture",m("type",m("type","Connections/Connected Clause","actions",
              m("seed",m("do",List.of(patch("/fixtureEntries","entries"),patch("/receipts/targets","targets"),
                  patch("/receipts/grossConfirmedMinor","gross"),patch("/receipts/netReceivedMinor","gross"),
                  patch("/commission/targets","commissionTargets"),patch("/commission/accrued","accrued"))),
                "restore",m("do",List.of(m("$appendEvent",m("type","Parties/Document Access Restored","revision",1)))))),
              "bindings",m("seed",m("seedForTest",route()),"restore",m("restoreForTest",route())))));
    var initialized = applied(engine.initialize(source), "initialization");
    var receiptTargets = m();
    var commissionTargets = m();
    var entries = m();
    var values = engine.execution().values();
    var agreementRef = new Exact.Ref(initialized.document().blueId());
    for (int index = 0; index < count; index++) {
      String key = "order-" + index;
      String path = "/orders/" + key;
      var origin = values.exact(values.select(agreementRef, path + "/contracts/initialized/document"));
      String id = NativeRuntime.identity(values.source(key));
      entries.put(id,m("status","usable","key",key,"path",path,"documentOrigin",NativeRuntime.identity(origin),
          "domainTerms",m("commissionTerms",m("commissionBps",1200))));
      receiptTargets.put(key,m("grossConfirmedMinor",7200,"refundsMinor",0,"netReceivedMinor",7200));
      commissionTargets.put(key,864);
    }
    System.out.printf("NATIVE entries=%d initializationGas=%d%n",count,initialized.gas());
    var seed=applied(engine.process(initialized.document(),event(initialized.document(),"seedForTest",
        m("entries",entries,"targets",receiptTargets,"commissionTargets",commissionTargets,"gross",count*7200,"accrued",count*864)),1),
        "seed");
    System.out.printf("NATIVE entries=%d setupGas=%d%n",count,seed.gas());
    var restored=applied(engine.process(seed.document(),event(seed.document(),"restoreForTest",m()),2),"restore");
    check(engine,restored.document(),count);
    long changed=receiptEvents(engine,restored);
    if (changed!=count) throw new AssertionError("Changed keys "+changed);
    System.out.printf("NATIVE entries=%d changed=%d gas=%d%n",count,changed,restored.gas());
    var replay=applied(engine.process(restored.document(),event(restored.document(),"restoreForTest",m()),3),"replay");
    check(engine,replay.document(),count);
    if (receiptEvents(engine,replay)!=0) throw new AssertionError("Replay emitted a receipt event");
    System.out.printf("NATIVE entries=%d exactRestoredReplayGas=%d events=0%n",count,replay.gas());
  }

  private static void check(Contracts engine, Contracts.Document document, int count) {
    amount(engine, document, "/receipts/grossConfirmedMinor", count * 7200);
    amount(engine, document, "/receipts/refundsMinor", count * 5400);
    amount(engine, document, "/receipts/netReceivedMinor", count * 1800);
    amount(engine, document, "/commission/accrued", count * 216);
    for (int index = 0; index < count; index++) {
      String key = "order-" + index;
      String receiptTarget = "/receipts/targets/" + key;
      amount(engine, document, receiptTarget + "/grossConfirmedMinor", 7200);
      amount(engine, document, receiptTarget + "/refundsMinor", 5400);
      amount(engine, document, receiptTarget + "/netReceivedMinor", 1800);
      amount(engine, document, "/commission/targets/" + key, 216);
    }
  }

  private static void amount(Contracts engine, Contracts.Document document, String path, int expected) {
    Object actual = engine.read(document, path);
    if (!(actual instanceof Number number) || number.longValue() != expected)
      throw new AssertionError(path + " expected " + expected + " got " + actual);
  }

  private static long receiptEvents(Contracts engine, Contracts.Result result) {
    return ClauseGasProbe.eventData(engine, result).stream()
        .filter(event -> event instanceof Map<?, ?> row && "Confirmed Receipts Changed".equals(row.get("kind")))
        .count();
  }
  static Map<String,Object> patch(String path,String field) {
    return m("$appendChange",m("op","replace","path",path,"val",m("$var",m("name","params","path","/"+field))));
  }
  static Map<String,Object> route() {
    return m("on","workflow","party","merchant","params",m("$object",m("$var","trigger")));
  }
  static Object event(Contracts.Document doc,String op,Map<String,Object> request) {
    return m("source","merchant","operation",m("type","Contracts/Operation Request","channel","merchant","operation",op,
        "document",m("blueId",doc.blueId()),"requireExactDocumentVersion",true,"request",request));
  }
  static Map<String,Object> m(Object... x) {
    var result=new LinkedHashMap<String,Object>();
    for(int i=0;i<x.length;i+=2) result.put((String)x[i],x[i+1]);
    return result;
  }
  static Contracts.Result applied(Contracts.Result r,String message) {
    if(!r.commits()) throw new AssertionError(message+" status="+r.status()+" gas="+r.gas()+" "+ClauseGasProbe.diagnostic(r));
    return r;
  }
}
