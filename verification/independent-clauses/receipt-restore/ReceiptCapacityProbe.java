import blue.bex.BexError;
import blue.bex.Engine;
import blue.bex.Gas;
import blue.bex.Values;
import blue.contracts.Contracts;
import blue.core.CompositionPackages;
import blue.language.next.NativeRuntime;
import blue.packages.QualificationRuntime;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Measures exact Receipts and Ledger BEX on controlled Order facts, separately from Contracts dispatch. */
public final class ReceiptCapacityProbe {
  private static final long BUDGET = 10_000_000;
  private static final int REQUIRED_ORDERS = 80;

  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]).toAbsolutePath().normalize();
    var catalogue = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    try (var blue = catalogue.language()) {
      var execution = new Contracts(blue, QualificationRuntime.bindings()).execution();
      var v = execution.values();
      var def = v.source(m("type", "Payment/Receipts Clause"), "definition");
      var functions = v.bexData(v.select(def, "/actionDefinition/type/functions"));
      if (!(functions instanceof Map)) throw new AssertionError("Exact functions not loaded: " + functions);
      var program = m("functions", functions, "constants", m("clauseKey", "receipts", "bindings",
          m("orders", "/orders", "entries", "/process_orders/entries", "instruction", "/payment",
              "state", "/receipts", "currency", "/terms/currency")),
          "do", v.bexData(v.select(def, "/actions/reconcile/do")));
      var evaluator = execution.evaluator();
      var receiptAction = evaluator.compile(program);
      var ledgerDefinition = v.source(m("type", "Ledger/Balance Functions"), "definition");
      var ledgerAction = evaluator.compile(m("functions", v.bexData(v.select(ledgerDefinition, "/functions")),
          "constants", m("clauseKey", "commission", "bindings", m("state", "/commission", "receipts", "/receipts", "orders", "/orders",
              "orderEntries", "/process_orders/entries", "frozenRate", "/domainTerms/commissionTerms/commissionBps")),
          "do", List.of(m("$return",m("$call",m("function","accruePercent","args",m()))))));
      for (int count : List.of(4, 24, 48, 64, REQUIRED_ORDERS, 128, 256, 512, 1024, 2048, 4096)) {
        for (boolean dirty : List.of(true,false)) {
          var orders = m(); var entries = m(); var targets = m(); var commissions = m();
          for (int n = 0; n < count; n++) {
            String key = "order-" + n;
            var origin = m("name", "Fixture order " + n);
            entries.put(NativeRuntime.identity(v.source(key)), m("status", "usable", "key", key,
                "path", "/orders/" + key, "documentOrigin", NativeRuntime.identity(v.source(origin)),
                "domainTerms", m("commissionTerms", m("commissionBps",1200))));
            orders.put(key, m("contracts", m("initialized", m("document", origin)),
                "activation", m("active", true), "payment", m("type", "PaymentInstruction/Payment Instruction",
                    "paymentTerms", m("currency", "USD"), "payment", m("completed", 7200, "reversed", dirty ? 5400 : 0))));
            targets.put(key,m("grossConfirmedMinor",7200,"refundsMinor",0,"netReceivedMinor",7200));
            commissions.put(key,864);
          }
          var modeled = m("activation",m("active",true), "orders", orders, "process_orders", m("entries", entries),
              "terms", m("currency","USD"), "receipts", m("grossConfirmedMinor",count*7200,"refundsMinor",0,
                  "netReceivedMinor",count*7200,"currency","USD","targets",targets),
              "commission",m("accrued",count*864,"paid",0,"reserved",0,"targets",commissions,"settlements",m()));
          var context = new Engine.Context();
          context.document = modeled;
          context.readDocument = (path,view,doc) -> Values.pointerGet(doc,path);
          context.matcher = (a,b) -> v.matches(v.source(Values.blueValue(a)),v.source(Values.blueValue(b),"definition"));
          context.nodeBlueId = (a,g) -> NativeRuntime.identity(v.source(Values.blueValue(a)));
          try {
            context.event = m("type", "Parties/Document Access Restored", "revision", 1);
            var restoreEvent = context.event;
            var gas = new Gas(BUDGET);
            var result = evaluator.execute(receiptAction, context, gas, Engine.TraceMode.METER_ONLY);
            if (result.events().size() != (dirty?count:0)) {
              var selected = m("functions",functions,"do",List.of(m("$return",m("$call",
                  m("function","usableCollectionEntry","args",m("collection","/orders","entries","/process_orders/entries","key","order-0"))))));
              throw new AssertionError("Outcome count " + result.events().size() + " gas " + result.gasUsed()
                  + " target selection " + evaluator.execute(selected, context, BUDGET).value());
            }
            long receiptGas = gas.used();
            apply(modeled,result.changeset());
            for (Object event : result.events()) {
              context.event = event;
              apply(modeled,evaluator.execute(ledgerAction, context, gas, Engine.TraceMode.METER_ONLY).changeset());
            }
            long expected = dirty ? count * 216L : count * 864L;
            Number actual = (Number) Values.pointerGet(modeled,"/commission/accrued");
            if (actual.longValue()!=expected) throw new AssertionError("Ledger accrued " + actual + " != " + expected);
            long expectedRefunds = dirty ? count * 5400L : 0L;
            long expectedNet = count * 7200L - expectedRefunds;
            amount(modeled, "/receipts/grossConfirmedMinor", count * 7200L);
            amount(modeled, "/receipts/refundsMinor", expectedRefunds);
            amount(modeled, "/receipts/netReceivedMinor", expectedNet);
            for (int n=0; n<count; n++) {
              String target="/receipts/targets/order-" + n;
              amount(modeled,target+"/grossConfirmedMinor",7200);
              amount(modeled,target+"/refundsMinor",dirty?5400:0);
              amount(modeled,target+"/netReceivedMinor",dirty?1800:7200);
              amount(modeled,"/commission/targets/order-" + n,dirty?216:864);
            }
            System.out.printf("orders=%d changed=%d receiptGas=%d stockLedgerGas=%d totalBex=%d patches=%d%n",
                count,result.events().size(),receiptGas,gas.used()-receiptGas,gas.used(),result.changeset().size());
            if (dirty) {
              context.event = restoreEvent;
              var replay = evaluator.execute(receiptAction, context, new Gas(BUDGET), Engine.TraceMode.METER_ONLY);
              if (!replay.events().isEmpty() || !replay.changeset().isEmpty())
                throw new AssertionError("Replay on identical restored facts had an effect");
              amount(modeled, "/receipts/netReceivedMinor", expectedNet);
              amount(modeled, "/commission/accrued", expected);
              System.out.printf("orders=%d exactRestoredReplayGas=%d events=0 patches=0%n",count,replay.gasUsed());
            }
          } catch (BexError ex) {
            System.out.printf("orders=%d dirty=%s %s%n",count,dirty,ex);
            if (!"GAS_LIMIT_EXCEEDED".equals(ex.code()) || count <= REQUIRED_ORDERS) throw ex;
          }
        }
      }
    }
  }

  private static void amount(Map<String, Object> model, String path, long expected) {
    Object actual = Values.pointerGet(model,path);
    if (!(actual instanceof Number number) || number.longValue() != expected)
      throw new AssertionError(path + " amount " + actual + " != " + expected);
  }

  private static Map<String, Object> m(Object... pairs) {
    var map = new LinkedHashMap<String, Object>();
    for (int i = 0; i < pairs.length; i += 2) map.put((String) pairs[i], pairs[i + 1]);
    return map;
  }

  @SuppressWarnings("unchecked")
  private static void apply(Map<String, Object> document, List<Object> changes) {
    for (Object raw : changes) {
      var change = (Map<String, Object>) raw;
      var segments = ((String) change.get("path")).substring(1).split("/");
      var parent = document;
      for (int i=0;i<segments.length-1;i++) parent=(Map<String,Object>) parent.get(segments[i]);
      parent.put(segments[segments.length-1],change.get("val"));
    }
  }
}
