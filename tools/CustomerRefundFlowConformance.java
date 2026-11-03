package blue.core;

import blue.coordination.AuthoringRuntime;
import blue.contracts.*;
import blue.language.next.WireData;
import java.nio.file.*;
import java.util.*;

/** Native contract evidence from the Business-composed PI. No provider effect or hosted auth claim. */
public final class CustomerRefundFlowConformance {
  @SuppressWarnings("unchecked") static Map<String,Object> obj(Object v){return (Map<String,Object>)v;}
  static Map<String,Object> m(Object... pairs){var r=new LinkedHashMap<String,Object>();for(int i=0;i<pairs.length;i+=2)r.put((String)pairs[i],pairs[i+1]);return r;}
  static void require(boolean ok,String why){if(!ok)throw new AssertionError(why);}
  static Object copy(Object value){return WireData.parse(WireData.write(value),"json");}
  static Map<String,Object> request(String id,long amount){return m("type","PaymentInstruction/Payment Request Input","requestId",id,"amountMinor",amount);}
  static Map<String,Object> outcome(String id){return m("type","PaymentInstruction/Payment Outcome Input","requestId",id);}
  static Map<String,Object> source(Path fixture,boolean guarded)throws Exception {
    var source=obj(copy(obj(CompositionPackages.yaml(fixture)).get("paymentTemplate")));
    source.put("paymentPreparation",m("orderDocumentId","native-refund-fixture-order","clauseId","payment","itemKey","single","requestId","single"));
    var terms=obj(source.get("paymentTerms"));terms.put("amountMinor",10000);terms.put("limitMinor",10000);
    var clauses=obj(source.get("clauses"));var activation=obj(clauses.get("activation"));
    var parties=obj(obj(activation.get("parameters")).get("parties"));
    parties.put("partner",m("type","Parties/Party"));
    var transports=m();source.put("contracts",transports);
    for(var e:parties.entrySet()) {
      var channel=m("type","Contracts/External Channel","event",m("source",e.getKey()));
      var party=obj(e.getValue());party.put("myosAccountId","fixture-"+e.getKey());party.put("lead",m("channel",channel));party.put("readerKeys",List.of("reader-"+e.getKey()));transports.put(e.getKey(),channel);
    }
    if(guarded)obj(obj(obj(obj(clauses.get("customerCapture")).get("bindings")).get("requestRefund")).get("refund")).put("before",List.of(m("$failIf",m("cond",true,"message","REFUND_REQUIRES_REVIEW"))));
    return source;
  }
  static final class Session implements AutoCloseable {
    final AuthoringRuntime runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1());
    final Contracts processor;Contracts.Document document;long time=100;
    Session(CompositionPackages packages,Map<String,Object> source){processor=runtime.processor(packages.language());var init=processor.initialize(source);require(init.commits(),"Initialization "+init.status()+" "+init.observations());document=init.document();}
    void call(String channel,String operation,Map<String,Object> input,boolean success){
      var event=m("source",channel,"operation",m("type","Contracts/Operation Request","channel",channel,"operation",operation,"document",m("blueId",document.blueId()),"request",input,"requireExactDocumentVersion",true));
      var before=document;var result=processor.process(before,event,time++);
      require(result.commits()==success,operation+" expected "+success+" got "+result.status()+" "+result.observations());
      if(!success){require(before.identity().equals(result.document().identity()),"Failed request changed state");require(processor.emitted(result).isEmpty(),"Failed request emitted financial event");}
      document=result.document();
    }
    long number(String path){return ((Number)processor.read(document,path)).longValue();}
    void paid(){
      call("guarantor","acceptPaymentInstruction",m(),true);
      call("guarantor","recordTransactionInitiated",m("type","PaymentInstruction/Transaction Initiation Input","transactionId","fixture-transaction","railType","test","attachmentPoint","instruction","providerReference","fixture-reference"),true);
      call("guarantor","provideSession",m("type","MyOS/Customer Session Input","requestId","customer-session-1","sessionId","fixture-session","expiresAt",number("/customerSession/paymentDueAt")),true);
      call("guarantor","requestCustomerPayment",m("sessionId","fixture-session","requestId","secure-1"),true);
      call("guarantor","secureFunds",outcome("secure-1"),true);
      call("guarantor","completePayment",outcome("customer-capture-1"),true);
      require(number("/payment/completed")==10000,"Actual native capture");
    }
    public void close(){runtime.close();}
  }
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);var fixture=Path.of(args[1]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var session=new Session(packages,source(fixture,false))) {
      session.paid();
      for(String denied:List.of("payer","partner","guarantor"))session.call(denied,"refund",request("forbidden-"+denied,1),false);
      session.call("payee","refund",request("refund-1",2500),true);
      session.call("payee","refund",request("refund-1",2500),true);
      require(session.number("/payment/reserved/refund")==2500,"Replay does not reserve twice");
      session.call("payee","refund",request("refund-1",2501),false);
      session.call("payee","reverseAfterCompletion",outcome("refund-1"),false);
      session.call("guarantor","reverseAfterCompletion",outcome("refund-1"),true);
      session.call("payee","refund",request("refund-2",3000),true);
      session.call("guarantor","recordPaymentReversalUnknown",m("type","PaymentInstruction/Payment Outcome Input","requestId","refund-2","reason","provider_response_unknown"),true);
      require(session.number("/payment/reserved/refund")==3000,"Unknown retains reservation");
      session.call("payee","refund",request("over-reserved",5000),false);
      session.call("guarantor","reverseAfterCompletion",outcome("refund-2"),true);
      session.call("payee","refund",request("refund-3",4500),true);
      session.call("guarantor","reverseAfterCompletion",outcome("refund-3"),true);
      session.call("guarantor","reverseAfterCompletion",outcome("refund-3"),true);
      require(session.number("/payment/completed")==10000&&session.number("/payment/reversed")==10000&&session.number("/payment/reserved/refund")==0,"Three partial refunds retain capture and exhaust refundable amount exactly once");
      session.call("payee","refund",request("too-much",1),false);
    }
    try(var guarded=new Session(packages,source(fixture,true))) {
      guarded.paid();guarded.call("payee","refund",request("blocked-before",1),false);
      require(guarded.number("/payment/reserved/refund")==0,"Native before blocks direct operation without reservation");
    }
    System.out.println("PASS native Business PI refund authority, multiple partial refunds, reservation, unknown/retry, over-limit and before guard; no provider/closed-flow claim");
  }
}
