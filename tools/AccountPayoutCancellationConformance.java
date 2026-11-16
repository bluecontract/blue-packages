import blue.contracts.*;
import blue.bex.Values;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native preactivation operation authority and report materialization; no external financial stop claim. */
public final class AccountPayoutCancellationConformance {
  static Map<String,Object> m(Object... pairs) {
    var result=new LinkedHashMap<String,Object>();
    for(int i=0;i<pairs.length;i+=2)result.put((String)pairs[i],pairs[i+1]);
    return result;
  }
  @SuppressWarnings("unchecked") static Map<String,Object> o(Object value) { return (Map<String,Object>)value; }
  static void check(boolean condition,String message) { if(!condition)throw new AssertionError(message); }
  static Map<String,Object> party(String actor) {
    return m("type","Parties/Party","myosAccountId",actor,"readerKeys",List.of("reader-"+actor),
        "lead",m("channel",m("type","Contracts/External Channel","event",m("source",actor))));
  }
  static Map<String,Object> binding(String operation,String actor) {
    return m(operation,m("on","workflow","party",actor,"params",
        m("requestId",m("$var",m("name","trigger","path","/requestId")))));
  }
  static Map<String,Object> source(Path root)throws Exception {
    var settlement=o(WireData.parse(Files.readString(root.resolve(
        "clause-reseller/types/commission-payout-settlement-clause.blue")),"yaml"));
    return m("name","Preactivation account cancellation native fixture",
        "type","MyOS/MyOS Test Account to Account Payment Instruction",
        "instanceKey","native-preparation-slot",
        "contracts",m("seller",m("type","Contracts/External Channel","event",m("source","seller")),
            "partner",m("type","Contracts/External Channel","event",m("source","partner")),
            "guarantor",m("type","Contracts/External Channel","event",m("source","guarantor"))),
        "paymentTerms",m("amountMinor",1440,"limitMinor",1440,"currency","USD",
            "payerChannel","seller","payeeChannel","partner","guarantorChannel","guarantor",
            "allowedPayees",List.of("partner"),"captureGate","","recipientApprovalRequired",false),
        "paymentDetails",m("method","myos-account-to-account",
            "executionTerms",m("executionPolicy","BLUE_ACCOUNT_PAYOUT_STOP_V1"),
            "payoutTerms",m("agreementOrigin","agreement-fixture","payoutKey","payout-one",
                "preparationClauseId","payouts","currency","USD","operator","test","grossMinor",1800,"netMinor",1440,"feeMinor",360)),
        "clauses",m("activation",m("type","Activation/Activation Clause","parameters",
            m("parties",m("seller",party("seller"),"partner",party("partner"),"guarantor",party("guarantor")),
                "required",List.of("seller"),"preActivationOperations",
                List.of("requestAccountPaymentCancellation","confirmAccountPaymentStopped"))),
            "accountSettlement",m("type",settlement,"bindings",
                m("requestCancellation",binding("requestAccountPaymentCancellation","seller"),
                    "confirmStopped",binding("confirmAccountPaymentStopped","guarantor")))));
  }
  static Object operation(Contracts.Document document,String actor,String name,String requestId) {
    return m("source",actor,"operation",m("type","Contracts/Operation Request","channel",actor,
        "operation",name,"document",m("blueId",document.blueId()),
        "requireExactDocumentVersion",true,"request",m("requestId",requestId)));
  }
  static Object input(Contracts.Document document,String actor,String name,Map<String,Object> request) {
    return m("source",actor,"operation",m("type","Contracts/Operation Request","channel",actor,
        "operation",name,"document",m("blueId",document.blueId()),
        "requireExactDocumentVersion",true,"request",request));
  }
  static Contracts.Document apply(Contracts p,Contracts.Document document,String actor,String name,
      Map<String,Object> request,long time) {
    return applied(p.process(document,input(document,actor,name,request),time),name).document();
  }
  static Contracts.Result applied(Contracts.Result result,String step) {
    check(result.commits(),step+": "+result.status()+" "+result.observations()+" "+result.receipt());
    return result;
  }
  static void denied(Contracts p,Contracts.Document document,String actor,String name,String requestId,long time) {
    var result=p.process(document,operation(document,actor,name,requestId),time);
    check(!result.commits(),"Unauthorized/conflicting operation committed: "+actor+" "+name+" "+result.status());
    check(result.document().blueId().equals(document.blueId()),"Denied operation changed document");
    check(p.emitted(result).isEmpty(),"Denied operation emitted a business event");
  }
  static void inactive(Contracts p,Contracts.Document document) {
    check(!Boolean.TRUE.equals(p.read(document,"/activation/active")),"Cancellation activated payment");
    check(p.read(document,"/payment/secured")==Values.UNDEFINED||
        ((Number)p.read(document,"/payment/secured")).longValue()==0,"Cancellation secured funds");
    check(p.read(document,"/payment/completed")==Values.UNDEFINED||
        ((Number)p.read(document,"/payment/completed")).longValue()==0,"Cancellation completed payment");
  }
  static void unsupportedPolicies(Contracts p,Path root)throws Exception {
    var absent=source(root);
    o(o(absent.get("paymentDetails")).get("executionTerms")).remove("executionPolicy");
    var initial=applied(p.initialize(absent),"Missing-policy negative fixture");
    denied(p,initial.document(),"seller","requestAccountPaymentCancellation","cancel-one",10);
    var legacy=source(root);
    o(o(legacy.get("paymentDetails")).get("executionTerms")).put("fundingModel","LEGACY_ACCOUNT_DEBIT");
    var document=applied(p.initialize(legacy),"Legacy-policy negative fixture").document();
    document=apply(p,document,"seller","requestAccountPaymentCancellation",m("requestId","cancel-one"),11);
    var before=p.read(document,"/accountCancellation");
    denied(p,document,"guarantor","confirmAccountPaymentStopped","cancel-one",12);
    check(before.equals(p.read(document,"/accountCancellation")),"Unsupported stop changed request");
    inactive(p,document);
  }
  static void paidCannotStop(Contracts p,Path root)throws Exception {
    var source=source(root);var clauses=o(source.get("clauses"));
    var fixed=m("requestId","payout-secure","amountMinor",m("$document","/paymentTerms/amountMinor"));
    var capture=m("requestId","payout-capture","amountMinor",m("$document","/paymentTerms/amountMinor"));
    clauses.put("payment",m("type","PaymentInstruction/Payment Request Actions","bindings",
        m("requestAuthorize",m("securePayout",m("on","workflow","party","guarantor","params",fixed)),
            "requestCapture",m("capturePayout",m("on","workflow","party","guarantor","params",capture)))));
    o(o(clauses.get("accountSettlement")).get("bindings")).put("confirm",
        m("confirmAccountSettlement",m("on","workflow","party","guarantor","params",
            m("debitReference",m("$var",m("name","trigger","path","/debitReference")),
                "transferReference",m("$var",m("name","trigger","path","/transferReference"))))));
    var document=applied(p.initialize(source),"Native paid negative fixture").document();
    document=apply(p,document,"seller","requestAccountPaymentCancellation",m("requestId","cancel-one"),20);
    document=apply(p,document,"seller","approve_seller",m("revision",1),21);
    document=apply(p,document,"guarantor","acceptPaymentInstruction",m(),22);
    document=apply(p,document,"guarantor","recordTransactionInitiated",m(
        "type","PaymentInstruction/Transaction Initiation Input","transactionId","native-paid-negative",
        "railType","test","attachmentPoint","instruction","providerReference","local-no-psp"),23);
    document=apply(p,document,"guarantor","securePayout",m(),24);
    document=apply(p,document,"guarantor","secureFunds",
        m("type","PaymentInstruction/Payment Outcome Input","requestId","payout-secure"),25);
    document=apply(p,document,"guarantor","capturePayout",m(),26);
    document=apply(p,document,"guarantor","completePayment",
        m("type","PaymentInstruction/Payment Outcome Input","requestId","payout-capture"),27);
    check(((Number)p.read(document,"/payment/completed")).longValue()==1440,
        "Paid negative must use actual native completion, not seeded state");
    var before=p.read(document,"/accountCancellation");
    denied(p,document,"guarantor","confirmAccountPaymentStopped","cancel-one",28);
    document=apply(p,document,"guarantor","confirmAccountSettlement",
        m("debitReference","native-debit","transferReference","native-transfer"),29);
    check(p.read(document,"/accountSettlement") instanceof Map,"Actual native settlement report missing");
    denied(p,document,"guarantor","confirmAccountPaymentStopped","cancel-one",30);
    check(before.equals(p.read(document,"/accountCancellation")),"Known-paid refusal changed cancellation state");
    check(((Number)p.read(document,"/payment/completed")).longValue()==1440,"Stop changed completed amount");
  }
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var p=runtime.processor(blue);
      var nativeSource=source(root);
      var initialization=p.initialize(nativeSource);
      if(!initialization.commits())ClauseGasProbe.diagnose(p,nativeSource);
      var initial=applied(initialization,"Initialize authored cancellation clause");
      var document=initial.document();inactive(p,document);
      denied(p,document,"partner","requestAccountPaymentCancellation","cancel-one",1);
      denied(p,document,"guarantor","confirmAccountPaymentStopped","cancel-one",1);
      var requested=applied(p.process(document,operation(document,"seller",
          "requestAccountPaymentCancellation","cancel-one"),2),"Actual payer request before activation");
      document=requested.document();inactive(p,document);
      check("REQUESTED".equals(p.read(document,"/accountCancellation/status")),"Request was not durably processed");
      check(p.read(document,"/accountCancellation/instructionOrigin")==Values.UNDEFINED,"Request fabricated stopped proof");
      denied(p,document,"seller","requestAccountPaymentCancellation","other-request",2);
      var duplicate=applied(p.process(document,operation(document,"seller",
          "requestAccountPaymentCancellation","cancel-one"),3),"Request retry");
      check(p.emitted(duplicate).isEmpty(),"Repeated request emitted twice");document=duplicate.document();
      denied(p,document,"seller","confirmAccountPaymentStopped","cancel-one",4);
      denied(p,document,"guarantor","confirmAccountPaymentStopped","other-request",5);
      var stopped=applied(p.process(document,operation(document,"guarantor",
          "confirmAccountPaymentStopped","cancel-one"),6),"Guarantor report");
      document=stopped.document();inactive(p,document);
      check("STOPPED".equals(p.read(document,"/accountCancellation/status")),"Report was not durably processed");
      check("native-preparation-slot".equals(p.read(document,"/accountCancellation/instanceKey")),"Report changed own slot");
      check("BLUE_ACCOUNT_PAYOUT_STOP_V1".equals(p.read(document,"/accountCancellation/executionPolicy")),"Report lost accepted policy");
      var v=p.execution().values();
      String origin=NativeRuntime.identity(v.exact(v.select(new Exact.Ref(document.blueId()),"/contracts/initialized/document")));
      check(origin.equals(p.read(document,"/accountCancellation/instructionOrigin")),"Report did not copy own origin");
      check(p.read(document,"/paymentDetails/payoutTerms").equals(p.read(document,"/accountCancellation/payoutTerms")),
          "Report did not copy exact own payout terms");
      var proof=p.read(document,"/accountCancellation");
      var replay=applied(p.process(document,operation(document,"guarantor",
          "confirmAccountPaymentStopped","cancel-one"),7),"Stopped report retry");
      check(p.emitted(replay).isEmpty(),"Stopped replay emitted a second business event");
      check(proof.equals(p.read(replay.document(),"/accountCancellation")),"Stopped replay changed proof");
      inactive(p,replay.document());
      unsupportedPolicies(p,root);
      paidCannotStop(p,root);
      System.out.println("PASS missing-policy/legacy and actual native completed/settled stop refusal; native payer preactivation request; wrong-party denial; request != stopped; guarantor own-facts report; idempotent replay. No financial stop/fence claim.");
    }
  }
}
