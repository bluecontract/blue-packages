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
    if (operation.equals("startPayout")) {
      var withContext = new LinkedHashMap<>(o(request));
      withContext.putIfAbsent("accountContext",m("payerBinding","test-seller-binding","payeeBinding","test-partner-binding",
          "platformAccountId","test-guarantor","environment","TEST"));
      request = withContext;
    }
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
      // Expose inherited request actions in this test fixture so the profile, not convenience mappings,
      // must reject alternative amounts, request IDs, recipients and details.
      var templateBindings=o(o(o(o(source.get("payoutTemplate")).get("clauses")).get("payment")).get("bindings"));
      for(var probe:List.of(List.of("requestAuthorize","probeSecure","guarantor"),List.of("requestRefund","probeRefund","seller"),
          List.of("requestFinalAmountResolution","probeFinal","seller"),List.of("requestTransactionDetailsUpdate","probeDetails","seller"),
          List.of("requestPayeeAssignment","probePayee","seller"))) {
        var params=m("requestId",m("$var",m("name","trigger","path","/requestId")));
        String field=switch(probe.get(1)){case "probeFinal" -> "finalAmount";case "probeDetails" -> "transactionDetails";case "probePayee" -> "payeeRef";default -> "amountMinor";};
        params.put(field,m("$var",m("name","trigger","path","/"+field)));
        o(templateBindings.computeIfAbsent(probe.get(0),k->m())).put(probe.get(1),m("on","workflow","party",probe.get(2),"params",params));
      }
      if(args.length>1 && args[1].equals("--guard-only")) {
        var pi=o(source.get("payoutTemplate"));
        o(pi.get("paymentTerms")).put("amountMinor",800);o(pi.get("paymentTerms")).put("limitMinor",800);
        o(pi.get("paymentDetails")).put("payoutTerms",m("netMinor",800,"payeeChannel","partner"));
        var activation=o(o(o(pi.get("clauses")).get("activation")).get("parameters"));
        activation.put("required",List.of());
        o(activation.get("parties")).forEach((role,party)->o(party).put("myosAccountId","test-"+role));
        channels(pi,List.of("seller","partner","guarantor"));t.host=t.init(pi);
        t.root("guarantor","acceptPaymentInstruction",m());
        t.root("guarantor","recordTransactionInitiated",m("type","PaymentInstruction/Transaction Initiation Input","transactionId","guard-only","railType","myos-account-to-account","attachmentPoint","instruction","providerReference","test"));
        t.deny("seller","probeFinal",t.host.blueId(),m("requestId","change-amount","finalAmount",400));
        t.deny("guarantor","probeSecure",t.host.blueId(),m("requestId","payout-secure","amountMinor",400));
        t.root("guarantor","probeSecure",m("requestId","payout-secure","amountMinor",800));
        t.root("seller","probeFinal",m("requestId","same-amount","finalAmount",800));
        check(t.number("/payment/targetMinor")==800&&o(t.read("/payment/requests")).size()==1,"Only full-N request survived");
        System.out.println("PASS standalone inherited request profile guards and positive controls");return;
      }
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
      check("test-guarantor".equals(split.get("operatorAccountId"))&&t.embedded("/contracts/initialized/document").equals(split.get("agreementOrigin")),"The payout names the operator and this Agreement: "+split);
      t.root("seller","startPayout",m("key","p1","amountMinor",1000));
      check(t.number("/commission/reserved")==1000,"A repeated preparation is idempotent");
      t.deny("seller","startPayout",t.host.blueId(),m("key","p2","amountMinor",500));
      t.deny("seller","startPayout",t.host.blueId(),m("key","p2","amountMinor",500,"feeMinor",0));
      System.out.println("PASS prepare freezes G=1000 F=200 N=800, reserves G once and guards a second unresolved payout");
      t.deny("seller","startPayout",t.host.blueId(),m("key","p1","amountMinor",1000,"accountContext",m("payerBinding","other","payeeBinding","test-partner-binding","platformAccountId","test-guarantor","environment","TEST")));
      var rounding=new CommissionPayoutConformance(t.p);rounding.host=rounding.init(source);
      rounding.root("seller","approve_seller",m("revision",1));rounding.root("partner","approve_partner",m("revision",1));
      rounding.root("seller","startPayout",m("key","rounding","amountMinor",3));
      var rounded=rounding.literal(rounding.entry("rounding").get("itemPath")+"/prepared/paymentDetails/payoutTerms");
      check(((Number)rounded.get("feeMinor")).longValue()==1&&((Number)rounded.get("netMinor")).longValue()==2,"Money rounding is applied to G=3");
      rounding.root("seller","cancelPayout",m("key","rounding"));rounding.root("seller","cancelPayout",m("key","rounding"));
      check(rounding.number("/commission/reserved")==0,"Duplicate cancel releases gross once");

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
      // Activate and initiate, then exercise generic inherited requests against the same profile.
      var guard=new CommissionPayoutConformance(t.p);guard.host=guard.init(provided);
      guard.root("seller","approve_seller",m("revision",1));guard.root("partner","approve_partner",m("revision",1));
      guard.apply("guarantor","acceptPaymentInstruction",guard.embedded("/payouts/p1"),m());
      guard.apply("guarantor","recordTransactionInitiated",guard.embedded("/payouts/p1"),m("type","PaymentInstruction/Transaction Initiation Input","transactionId","guard-p1","railType","myos-account-to-account","attachmentPoint","instruction","providerReference","test"));
      guard.deny("guarantor","probeSecure",guard.embedded("/payouts/p1"),m("requestId","payout-secure","amountMinor",400));
      guard.deny("guarantor","probeSecure",guard.embedded("/payouts/p1"),m("requestId","other-secure","amountMinor",800));
      guard.deny("seller","probeFinal",guard.embedded("/payouts/p1"),m("requestId","change-amount","finalAmount",400));
      guard.deny("seller","probeDetails",guard.embedded("/payouts/p1"),m("requestId","change-details","transactionDetails",m("recipient","other")));
      guard.deny("seller","probePayee",guard.embedded("/payouts/p1"),m("requestId","change-payee","payeeRef","seller"));
      check(guard.number("/payouts/p1/payment/targetMinor")==800&&o(guard.read("/payouts/p1/payment/requests")).isEmpty(),"Rejected inherited requests leave the exact approved payment unchanged");
      guard.apply("guarantor","probeSecure",guard.embedded("/payouts/p1"),m("requestId","payout-secure","amountMinor",800));
      guard.apply("seller","probeFinal",guard.embedded("/payouts/p1"),m("requestId","same-amount","finalAmount",800));
      guard.apply("seller","probeDetails",guard.embedded("/payouts/p1"),m("requestId","same-details","transactionDetails",m()));
      guard.apply("seller","probePayee",guard.embedded("/payouts/p1"),m("requestId","same-payee","payeeRef","partner"));
      check(o(guard.read("/payouts/p1/payment/requests")).size()==1,"The same inherited request alias permits exactly the canonical full-N secure");
      b.settle("p1",800,"test-debit-p1");
      check(b.number("/commission/paid")==0,"The split report alone does not settle G");
      b.deny("guarantor","confirmAccountSettlement",b.embedded("/payouts/p1"),m("debitReference","other-debit","transferReference","test-transfer-p1"));
      b.apply("guarantor","completePayment",b.embedded("/payouts/p1"),m("type","PaymentInstruction/Payment Outcome Input","requestId","payout-capture","amountCompleted",800));
      check(b.number("/commission/paid")==1000&&b.number("/commission/reserved")==0,"Report plus completion settles G exactly once");
      b.deny("seller","probeRefund",b.embedded("/payouts/p1"),m("requestId","payout-refund","amountMinor",800));
      var settlement=o(b.read("/commission/settlements/p1"));
      check(Long.valueOf(200).equals(((Number)settlement.get("feeMinor")).longValue())
          &&Long.valueOf(800).equals(((Number)settlement.get("transferredMinor")).longValue())
          &&"closed".equals(settlement.get("status")),"MyOS keeps F=200; partner received N=800: "+settlement);
      b.apply("guarantor","confirmAccountSettlement",b.embedded("/payouts/p1"),m("debitReference","test-debit-p1","transferReference","test-transfer-p1"));
      check(b.number("/commission/paid")==1000,"An identical report is idempotent");
      b.deny("seller","startPayout",b.host.blueId(),m("key","p3","amountMinor",1001));
      System.out.println("PASS operator split report plus completion settles G=1000 once; MyOS F=200, partner N=800; 1001 exceeds the rest");
      var completionFirst=new CommissionPayoutConformance(t.p);completionFirst.host=completionFirst.init(provided);
      completionFirst.root("seller","approve_seller",m("revision",1));completionFirst.root("partner","approve_partner",m("revision",1));
      completionFirst.initiate("p1");
      completionFirst.apply("guarantor","secureFunds",completionFirst.embedded("/payouts/p1"),m("type","PaymentInstruction/Payment Outcome Input","requestId","payout-secure","amountSecured",800));
      completionFirst.apply("guarantor","capturePayout",completionFirst.embedded("/payouts/p1"),m());
      completionFirst.apply("guarantor","completePayment",completionFirst.embedded("/payouts/p1"),m("type","PaymentInstruction/Payment Outcome Input","requestId","payout-capture","amountCompleted",800));
      check(completionFirst.number("/commission/paid")==0&&completionFirst.number("/commission/reserved")==1000,"Completion without split receipt retains G");
      completionFirst.apply("guarantor","confirmAccountSettlement",completionFirst.embedded("/payouts/p1"),m("debitReference","completion-first-debit","transferReference","completion-first-transfer"));
      completionFirst.apply("guarantor","confirmAccountSettlement",completionFirst.embedded("/payouts/p1"),m("debitReference","completion-first-debit","transferReference","completion-first-transfer"));
      check(completionFirst.number("/commission/paid")==1000&&completionFirst.number("/commission/reserved")==0,"Completion then duplicate receipt settles G once");
      System.out.println("PASS completion first retains G until a matching split receipt arrives");

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

      // Void before the partner transfer: only the whole secured debit, only with no capture pending.
      var e=new CommissionPayoutConformance(t.p);e.host=e.init(provided);
      e.root("seller","approve_seller",m("revision",1));e.root("partner","approve_partner",m("revision",1));
      e.initiate("p1");
      e.deny("seller","voidPayout",e.embedded("/payouts/p1"),m());
      e.apply("guarantor","secureFunds",e.embedded("/payouts/p1"),m("type","PaymentInstruction/Payment Outcome Input","requestId","payout-secure","amountSecured",800));
      e.deny("partner","voidPayout",e.embedded("/payouts/p1"),m());
      e.apply("seller","voidPayout",e.embedded("/payouts/p1"),m());
      e.deny("guarantor","capturePayout",e.embedded("/payouts/p1"),m());
      check(e.number("/commission/reserved")==1000,"A pending void keeps G reserved until the operator confirms it");
      e.apply("guarantor","cancelBeforeCompletion",e.embedded("/payouts/p1"),m("type","PaymentInstruction/Payment Outcome Input","requestId","payout-void","amountCancelled",800));
      var voided=o(e.read("/commission/settlements/p1"));
      check(e.number("/commission/reserved")==0&&e.number("/commission/paid")==0&&"closed".equals(voided.get("status"))
          &&Long.valueOf(0).equals(((Number)voided.get("feeMinor")).longValue()),"A confirmed void releases G without a fee: "+voided);
      var f=new CommissionPayoutConformance(t.p);f.host=f.init(provided);
      f.root("seller","approve_seller",m("revision",1));f.root("partner","approve_partner",m("revision",1));
      f.initiate("p1");
      f.apply("guarantor","secureFunds",f.embedded("/payouts/p1"),m("type","PaymentInstruction/Payment Outcome Input","requestId","payout-secure","amountSecured",800));
      f.apply("guarantor","capturePayout",f.embedded("/payouts/p1"),m());
      f.deny("seller","voidPayout",f.embedded("/payouts/p1"),m());
      System.out.println("PASS the seller voids only the whole secured debit before capture; a confirmed void releases G, fee 0");
    }
  }
}
