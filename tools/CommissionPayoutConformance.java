package blue.core;

import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native commission payout by a provided MyOS Test account-to-account Payment Instruction.
 * Real: preparation (frozen G/F/N, reservation, guards) and initialization of the prepared instruction with the
 * supplied MyOS operator. Modeled: the provided state (the prepared instruction under /payouts/<key>), then real
 * operator operations and Commission settlement. Bootstrap provision compares Timeline actors, which this native
 * runner cannot express; the hosted Core test covers bootstrap and providePayout. No account money is moved. */
public final class CommissionPayoutConformance {
  static Map<String,Object> m(Object... x){var out=new LinkedHashMap<String,Object>();for(int i=0;i<x.length;i+=2)out.put((String)x[i],x[i+1]);return out;}
  @SuppressWarnings("unchecked") static Map<String,Object> o(Object x){return (Map<String,Object>)x;}
  static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);}
  static Map<String,Object> channel(String role){return ClauseAppsExamples.transport(role);}
  static void channels(Map<String,Object> document,List<String> roles) {
    var contracts=o(document.computeIfAbsent("contracts",k->m()));
    var parties=o(o(o(o(document.get("clauses")).get("activation")).get("parameters")).get("parties"));
    for(String role:roles){var c=channel(role);o(o(parties.get(role)).computeIfAbsent("lead",k->m())).put("channel",c);contracts.put(role,c);}
  }

  final Contracts p;Contracts.Document host;int sequence;
  CommissionPayoutConformance(Contracts p){this.p=p;}

  Object event(String channel,String operation,Object document,Object request) {
    return m("source",channel,"operation",m("type","Contracts/Operation Request","channel",channel,"operation",operation,
        "document",m("blueId",document),"request",request,"requireExactDocumentVersion",true));
  }
  Contracts.Result run(String channel,String operation,Object document,Object request) {
    return p.process(host,event(channel,operation,document,request),++sequence);
  }
  void apply(String channel,String operation,Object document,Object request) {
    var result=run(channel,operation,document,request);
    if(!result.commits()) {
      String cause;
      try{ClauseGasProbe.diagnose(p,host,event(channel,operation,document,request),sequence);cause="no exception";}
      catch(Throwable failure){cause=failure.toString();}
      throw new AssertionError(operation+" must apply: "+cause);
    }
    host=result.document();
  }
  void deny(String channel,String operation,Object document,Object request) {
    var result=run(channel,operation,document,request);
    check(!result.commits(),operation+" must be rejected: "+request);
  }
  void root(String channel,String operation,Object request){apply(channel,operation,host.blueId(),request);}
  Contracts.Document init(Map<String,Object> source) {
    var result=p.initialize(source);
    if(!result.commits()) {
      String cause;try{ClauseGasProbe.diagnose(p,source);cause="no exception";}catch(Throwable failure){cause=failure.toString();}
      throw new AssertionError("Document must initialize: "+cause);
    }
    return result.document();
  }
  Object read(String path){return p.read(host,path);}
  long number(String path){return ((Number)read(path)).longValue();}
  String embedded(String path) {
    var v=p.execution().values();return NativeRuntime.identity(v.exact(v.select(new Exact.Ref(host.blueId()),path)));
  }
  Map<String,Object> literal(String path) {
    var v=p.execution().values();return o(WireData.json(WireData.write(v.literal(v.exact(v.select(new Exact.Ref(host.blueId()),path))))));
  }
  /** The prepared requirement entry for one payout key. */
  Map<String,Object> entry(String key) {
    for(Object raw:o(read("/process_payouts/entries")).values())if(key.equals(o(raw).get("key")))return o(raw);
    throw new AssertionError("No prepared entry for "+key);
  }
  /** The prepared instruction as the hosted bootstrap supplies it: the MyOS operator joins as guarantor. */
  Map<String,Object> supplied(Map<String,Object> entry) {
    var prepared=literal(entry.get("itemPath")+"/prepared");
    var parties=o(o(o(o(prepared.get("clauses")).get("activation")).get("parameters")).get("parties"));
    parties.put("guarantor",m("type","MyOS/MyOS Party","displayName","MyOS payment operator","myosAccountId","test-guarantor"));
    parties.forEach((role,party)->o(party).putIfAbsent("readerKeys",List.of("test-key-"+role)));
    // The prepared literal names its clause types by identity: wire each party's channel as the case runner does.
    channels(prepared,List.of("seller","partner","guarantor"));
    return prepared;
  }
  void initiate(String key) {
    apply("guarantor","acceptPaymentInstruction",embedded("/payouts/"+key),m());
    apply("guarantor","recordTransactionInitiated",embedded("/payouts/"+key),m("type","PaymentInstruction/Transaction Initiation Input","transactionId","payout-"+key,
        "railType","myos-account-to-account","attachmentPoint","instruction","providerReference","test"));
    apply("guarantor","securePayout",embedded("/payouts/"+key),m());
  }
  void settle(String key,long net,String debit) {
    initiate(key);
    apply("guarantor","secureFunds",embedded("/payouts/"+key),m("type","PaymentInstruction/Payment Outcome Input","requestId","payout-secure","amountSecured",net));
    apply("guarantor","capturePayout",embedded("/payouts/"+key),m());
    apply("guarantor","confirmAccountSettlement",embedded("/payouts/"+key),m("debitReference",debit,"transferReference","test-transfer-"+key));
  }

  public static void main(String[] args) throws Exception {
    var root=Path.of(args[0]).toAbsolutePath();var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var t=new CommissionPayoutConformance(runtime.processor(blue));
      var source=o(WireData.parse(Files.readString(root.resolve("examples/apps/30-commission-a2a-payout.blue")),"yaml"));
      // Wire the Agreement's own parties only; the payout template stays as authored (bootstrap supplies channels).
      var template=WireData.json(WireData.write(source.get("payoutTemplate")));
      ClauseAppsExamples.wire(source);source.put("payoutTemplate",template);channels(source,List.of("seller","partner"));
      t.host=t.init(source);
      check(!o(t.read("/clauses/activation/parameters/parties")).containsKey("guarantor"),"The MyOS operator is not an Agreement party");
      t.root("seller","approve_seller",m("revision",1));t.root("partner","approve_partner",m("revision",1));

      t.root("seller","startPayout",m("key","p1","amountMinor",1000));
      check(t.number("/commission/reserved")==1000,"G is reserved once");
      var p1=t.entry("p1");var frozen=t.literal(p1.get("itemPath")+"/prepared");
      check(Long.valueOf(800).equals(((Number)o(frozen.get("paymentTerms")).get("amountMinor")).longValue()),"The instruction amount is N");
      var split=o(o(frozen.get("paymentDetails")).get("payoutTerms"));
      check(Map.of("grossMinor",1000L,"feeMinor",200L,"netMinor",800L,"feeBps",2000L).entrySet().stream()
          .allMatch(e->e.getValue().equals(((Number)split.get(e.getKey())).longValue())),"Frozen G/F/N: "+split);
      check(!o(frozen.get("clauses")).containsKey("orders"),"Only the payout instruction is prepared");
      t.root("seller","startPayout",m("key","p1","amountMinor",1000));
      check(t.number("/commission/reserved")==1000,"A repeated preparation is idempotent");
      t.deny("seller","startPayout",t.host.blueId(),m("key","p2","amountMinor",500));
      t.deny("seller","startPayout",t.host.blueId(),m("key","p2","amountMinor",500,"feeMinor",0));
      System.out.println("PASS prepare freezes G=1000 F=200 N=800, reserves G once and guards a second unresolved payout");

      // A template whose instruction the payer would not approve cannot be prepared.
      var unconsented=o(WireData.json(WireData.write(source)));
      o(o(o(o(unconsented.get("payoutTemplate")).get("clauses")).get("activation")).get("parameters")).put("required",List.of());
      var u=new CommissionPayoutConformance(t.p);u.host=u.init(unconsented);
      u.root("seller","approve_seller",m("revision",1));u.root("partner","approve_partner",m("revision",1));
      u.deny("seller","startPayout",u.host.blueId(),m("key","p1","amountMinor",1000));
      check(u.number("/commission/reserved")==0,"Nothing is reserved for an unconsented payout");
      System.out.println("PASS a payout instruction the seller would not approve is rejected at preparation");

      var instruction=t.supplied(p1);
      var standalone=t.p.initialize(instruction);
      check(standalone.commits(),"The prepared instruction initializes with the supplied operator: "+ClauseGasProbe.diagnostic(standalone));
      check(Long.valueOf(800).equals(((Number)t.p.read(standalone.document(),"/paymentTerms/amountMinor")).longValue()),"Initialized N");
      check(Boolean.FALSE.equals(t.p.read(standalone.document(),"/activation/active"))
          &&List.of("seller").equals(t.p.read(standalone.document(),"/activation/required")),"The payout stays inactive until the seller approves it");
      check(o(t.p.read(standalone.document(),"/payment")).isEmpty()&&"AWAITING_ACCEPTANCE".equals(t.p.read(standalone.document(),"/activation/status")),
          "Payment does not start before the seller approves it");
      System.out.println("PASS the prepared instruction initializes with the MyOS operator as its supplied guarantor");

      // Modeled provided state: the same instruction under /payouts/p1 with the commission as reserved above.
      var commission=t.literal("/commission");
      // The modeled embedding cannot run the instruction's own activation: it stands for the instruction after the
      // seller approved it (payer approval is qualified above and in hosted Core).
      var approved=o(WireData.json(WireData.write(instruction)));
      o(o(o(approved.get("clauses")).get("activation")).get("parameters")).put("required",List.of());
      var provided=o(WireData.json(WireData.write(source)));provided.put("commission",commission);provided.put("payouts",m("p1",approved));
      var b=new CommissionPayoutConformance(t.p);b.host=b.init(provided);
      b.root("seller","approve_seller",m("revision",1));b.root("partner","approve_partner",m("revision",1));
      check(b.number("/commission/reserved")==1000&&b.number("/commission/paid")==0,"Provision alone settles nothing");
      b.settle("p1",800,"test-debit-p1");
      check(b.number("/commission/paid")==0,"The split report alone does not settle G");
      b.deny("guarantor","confirmAccountSettlement",b.embedded("/payouts/p1"),m("debitReference","other-debit","transferReference","test-transfer-p1"));
      b.apply("guarantor","completePayment",b.embedded("/payouts/p1"),m("type","PaymentInstruction/Payment Outcome Input","requestId","payout-capture","amountCompleted",800));
      check(b.number("/commission/paid")==1000&&b.number("/commission/reserved")==0,"Report plus completion settles G exactly once");
      var settlement=o(b.read("/commission/settlements/p1"));
      check(Long.valueOf(200).equals(((Number)settlement.get("feeMinor")).longValue())
          &&Long.valueOf(800).equals(((Number)settlement.get("transferredMinor")).longValue())
          &&"closed".equals(settlement.get("status")),"MyOS keeps F=200; partner received N=800: "+settlement);
      b.apply("guarantor","confirmAccountSettlement",b.embedded("/payouts/p1"),m("debitReference","test-debit-p1","transferReference","test-transfer-p1"));
      check(b.number("/commission/paid")==1000,"An identical report is idempotent");
      b.deny("seller","startPayout",b.host.blueId(),m("key","p3","amountMinor",1001));
      System.out.println("PASS operator split report plus completion settles G=1000 once; MyOS F=200, partner N=800; 1001 exceeds the rest");

      var c=new CommissionPayoutConformance(t.p);c.host=c.init(provided);
      c.root("seller","approve_seller",m("revision",1));c.root("partner","approve_partner",m("revision",1));
      c.apply("guarantor","rejectPaymentInstruction",c.embedded("/payouts/p1"),m("reason","payment_insufficient_funds"));
      check(c.number("/commission/reserved")==0&&c.number("/commission/paid")==0,"Operator rejection releases G");
      check(Long.valueOf(0).equals(((Number)o(c.read("/commission/settlements/p1")).get("paidMinor")).longValue()),"A rejected payout pays nothing");
      System.out.println("PASS operator rejection releases G without settlement");

      var d=new CommissionPayoutConformance(t.p);d.host=d.init(provided);
      d.root("seller","approve_seller",m("revision",1));d.root("partner","approve_partner",m("revision",1));
      d.initiate("p1");
      check(d.number("/commission/reserved")==1000,"A pending secure keeps G reserved");
      d.apply("guarantor","declineSecureFunds",d.embedded("/payouts/p1"),m("type","PaymentInstruction/Payment Outcome Input","requestId","payout-secure","reason","payment_insufficient_funds"));
      var declined=o(d.read("/commission/settlements/p1"));
      check(d.number("/commission/reserved")==0&&d.number("/commission/paid")==0&&"closed".equals(declined.get("status"))
          &&Long.valueOf(0).equals(((Number)declined.get("paidMinor")).longValue()),"A declined secure releases G and pays nothing: "+declined);
      d.root("seller","startPayout",m("key","p2","amountMinor",500));
      check(d.number("/commission/reserved")==500,"The released commission can be paid out again");
      System.out.println("PASS a declined secure releases G and a new payout can start");
    }
  }
}
