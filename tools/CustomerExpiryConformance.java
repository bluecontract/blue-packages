import blue.packages.QualificationRuntime;
import blue.contracts.*;
import blue.core.CompositionPackages;
import blue.language.next.*;
import blue.bex.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.*;

/** Real published BEX guards; external Stripe evidence remains the guarantor's responsibility. */
public final class CustomerExpiryConformance {
  static String TYPE;
  static final String OP="requestExpiredAuthorizationVoid";
  static Map<String,Object> m(Object... pairs){return ProviderInputConformance.m(pairs);}
  static void require(boolean ok,String why){ProviderInputConformance.require(ok,why);}
  @SuppressWarnings("unchecked") static Map<String,Object> object(Object value){return (Map<String,Object>)value;}
  static Map<String,Object> secured(){
    var doc=CustomerSessionConformance.ready();
    object(object(doc.get("paymentDetails")).get("customerPaymentTerms")).put("provider","stripe");
    object(doc.get("customerSession")).put("paymentAttemptId","secure-1");
    var payment=object(doc.get("payment"));payment.put("secured",100);
    object(payment.get("requests")).put("secure-1",m("intent",m("action","secure","amountMinor",100,"reason",""),"status","succeeded"));
    return doc;
  }
  static Map<String,Object> input(){return m("sessionId","session-1","secureRequestId","secure-1","requestId","expiry-1");}
  static Engine.Result run(Map<String,Object> input,Map<String,Object> doc,String actor){return ProviderInputConformance.execute(TYPE,OP,input,doc,actor);}
  static void denied(Map<String,Object> input,Map<String,Object> doc,String actor,String message){
    try{run(input,doc,actor);}catch(BexError error){require(error.getMessage().contains(message),"Wrong rejection: "+error.getMessage());return;}
    throw new AssertionError("Expected rejection: "+message);
  }
  static void activePartyStep(Map<String,Object> document) {
    var runtime=ProviderInputConformance.runtime;var values=ProviderInputConformance.values;
    var definition=values.head(values.source(m("type",TYPE),"definition"));
    var contract=NativeRuntime.child(NativeRuntime.head(definition.contracts,runtime),OP);
    var steps=NativeRuntime.head(NativeRuntime.child(NativeRuntime.head(contract,runtime),"steps"),runtime);
    var compute=NativeRuntime.head(NativeRuntime.child(steps,0),runtime);
    var libraryDefinition=NativeRuntime.head(NativeRuntime.child(compute,"definition"),runtime);
    var library=new LinkedHashMap<String,Object>();var source=new LinkedHashMap<String,Object>();
    for(String field:List.of("constants","functions")){var value=NativeRuntime.child(libraryDefinition,field);if(value!=null)library.put(field,values.bexData(value));}
    for(String field:List.of("do","constants","functions")){var value=NativeRuntime.child(compute,field);if(value!=null)source.put(field,values.bexData(value));}
    var bex=new Bex(BexProfile.current());
    var context=new BexContext(document,m(),m(),Values.UNDEFINED,m(),m("call",m("channel","bank","request",input()),"timestamp",100),"/",null,
      (actual,pattern)->values.matches(values.source(actual),values.source(pattern,"definition")),(actual,gas)->NativeRuntime.identity(values.source(actual)));
    var result=bex.execute(bex.compile(source,library,null),context,1000000);
    require(result.events().isEmpty()&&result.changeset().isEmpty(),"Party guard must not alter financial state");
  }
  public static void main(String[] args)throws Exception{
    var root=Path.of(args[0]).toAbsolutePath();
    try(var blue=CompositionPackages.published(root,root.resolve("PACKAGES.json")).language()){
      ProviderInputConformance.blue=blue;
      ProviderInputConformance.values=new Contracts(blue,QualificationRuntime.bindings()).execution().values();
      ProviderInputConformance.runtime=new NativeRuntime(blue);
      // An additive subtype must not grant the operation to already-published Customer PIs.
      var old=ProviderInputConformance.values.head(ProviderInputConformance.values.source(m("type",CustomerSessionConformance.TYPE),"definition"));
      require(NativeRuntime.child(NativeRuntime.head(old.contracts,ProviderInputConformance.runtime),OP)==null,"Legacy PI gained expiry authority");
      for(String candidate:List.of("MyOS/MyOS Expiry-Aware Customer Payment Instruction","MyOSExpiryDirect/MyOS Expiry-Aware Direct Customer Payment Instruction")){
      TYPE=candidate;
      var rootParties=secured();rootParties.put("parties",m("payer",m(),"payee",m()));activePartyStep(rootParties);
      var inactive=secured();inactive.put("activation",m("active",false));
      try{activePartyStep(inactive);throw new AssertionError("Inactive bootstrap document accepted");}catch(BexError error){require(error.getMessage().contains("DOCUMENT_NOT_ACTIVE"),"Inactive guard mismatch");}

      for(String field:List.of("sessionId","secureRequestId","requestId"))ProviderInputConformance.valid(TYPE,OP,input(),field);
      var result=run(input(),secured(),"bank");
      ProviderInputConformance.change(result,"/payment/reserved/void",BigInteger.valueOf(100));
      ProviderInputConformance.change(result,"/payment/cancellationPending",true);
      CustomerSessionConformance.event(result,"Payment Requested",m("action","void","requestId","expiry-1","amountMinor",100));
      require(result.changeset().stream().noneMatch(raw->{var row=object(raw);return Set.of("/payment/completed","/payment/secured").contains(row.get("path"));}),"Request must not report a financial outcome");
      for(String actor:List.of("payer","seller"))denied(input(),secured(),actor,"Guarantor workflow required");
      var extra=input();extra.put("amountMinor",1);denied(extra,secured(),"bank","EXPIRY_INPUT_FIELD_UNSUPPORTED");
      extra=input();extra.put("unknown",true);denied(extra,secured(),"bank","EXPIRY_INPUT_FIELD_UNSUPPORTED");
      var notReady=secured();object(notReady.get("customerSession")).put("status","closed");denied(input(),notReady,"bank","SESSION_NOT_READY");
      var wrong=input();wrong.put("sessionId","other");denied(wrong,secured(),"bank","SESSION_ID_MISMATCH");
      wrong=input();wrong.put("secureRequestId","other");denied(wrong,secured(),"bank","SECURE_REQUEST_MISMATCH");
      var doc=secured();object(object(doc.get("paymentDetails")).get("customerPaymentTerms")).put("provider","test");denied(input(),doc,"bank","STRIPE_PAYMENT_REQUIRED");
      doc=secured();object(doc.get("payment")).put("completed",1);denied(input(),doc,"bank","PAYMENT_ALREADY_COMPLETED");
      for(String action:List.of("secure","capture","void")){
        doc=secured();object(object(doc.get("payment")).get("reserved")).put(action,100);denied(input(),doc,"bank","Resolve pending authorization and capture before void");
      }
      doc=secured();object(doc.get("payment")).put("secured",0);denied(input(),doc,"bank","Void releases the entire remaining authorization");
      doc=secured();object(object(object(doc.get("payment")).get("requests")).get("secure-1")).put("status","unknown");denied(input(),doc,"bank","SECURE_REQUEST_MISMATCH");
      for(String status:List.of("pending","succeeded")){
        doc=secured();var payment=object(doc.get("payment"));
        object(payment.get("requests")).put("expiry-1",m("intent",m("action","void","amountMinor",100,"reason","stripe_authorization_expired"),"status",status));
        if(status.equals("succeeded")){payment.put("secured",0);payment.put("closed",true);object(doc.get("customerSession")).put("status","closed");}
        var duplicate=run(input(),doc,"bank");require(duplicate.events().isEmpty()&&duplicate.changeset().isEmpty(),"Replay must be inert even after cancellation");
      }
      doc=secured();object(object(doc.get("payment")).get("requests")).put("expiry-1",m("intent",m("action","void","amountMinor",99,"reason","stripe_authorization_expired"),"status","pending"));
      denied(input(),doc,"bank","Conflicting payment request identifier");
      var testStart=ProviderInputConformance.execute(TYPE,"requestCustomerPayment",m("sessionId","session-1","requestId","test-attempt"),CustomerSessionConformance.ready(),"bank");
      ProviderInputConformance.change(testStart,"/payment/reserved/secure",BigInteger.valueOf(100));
      doc=secured();var payment=object(doc.get("payment"));payment.put("cancellationPending",true);object(payment.get("reserved")).put("void",100);
      object(payment.get("requests")).put("expiry-1",m("intent",m("action","void","amountMinor",100,"reason","stripe_authorization_expired"),"status","pending"));
      var cancelled=ProviderInputConformance.execute(TYPE,"cancelBeforeCompletion",ProviderInputConformance.typed("PaymentInstruction/Payment Outcome Input",m("requestId","expiry-1")),doc,"bank");
      ProviderInputConformance.change(cancelled,"/payment/secured",BigInteger.ZERO);
      ProviderInputConformance.change(cancelled,"/payment/closed",true);
      require(cancelled.changeset().stream().noneMatch(raw->"/payment/completed".equals(object(raw).get("path"))),"Void outcome must never complete payment");
      System.out.println("PASS "+TYPE+" guards and replay; no external expiry proof claimed");
      }
    }
  }
}
