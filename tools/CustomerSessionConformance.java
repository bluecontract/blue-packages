import blue.packages.QualificationRuntime;
import blue.contracts.*;
import blue.core.CompositionPackages;
import blue.language.next.*;
import blue.bex.Values;
import blue.bex.Bex;
import blue.bex.BexContext;
import blue.bex.BexProfile;
import blue.bex.BexError;
import blue.bex.Engine;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.*;

/** Published session correlation and native BEX effects. Hosted writer authorization is tested in Core. */
public final class CustomerSessionConformance {
  static final String TYPE="MyOS/MyOS Customer Payment Instruction";
  static Map<String,Object> m(Object... pairs){return ProviderInputConformance.m(pairs);}
  static void require(boolean ok,String message){ProviderInputConformance.require(ok,message);}
  static Map<String,Object> pending(){
    var doc=ProviderInputConformance.payment();
    doc.put("paymentDetails",m("customerPaymentTerms",m("provider","test","recipientPaymentAccountId","account-1","paymentWindowDays",30)));
    doc.put("customerSession",m("requestId","prepare-1","id","","status","requested","paymentDueAt",1000,"expiresAt",0,"paymentAttemptId","","failureReason",""));
    return doc;
  }
  static Map<String,Object> response(){return ProviderInputConformance.typed("MyOS/Customer Session Input",m("requestId","prepare-1","sessionId","session-1","expiresAt",1000));}
  static void rejected(String operation,Map<String,Object> request,Object doc,String channel,String expected,String why){
    boolean failed=false;
    try {ProviderInputConformance.execute(TYPE,operation,request,doc,channel);}
    catch(BexError error){require(error.getMessage().contains(expected),"Expected "+expected+" for "+why+", actual "+error.code()+": "+error.getMessage());failed=true;}
    require(failed,why);
  }
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]).toAbsolutePath();
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language()){
      ProviderInputConformance.blue=blue;
      ProviderInputConformance.values=new Contracts(blue,QualificationRuntime.bindings()).execution().values();
      ProviderInputConformance.runtime=new NativeRuntime(blue);
      if(args.length>1&&args[1].equals("capture-policy"))capturePolicy();else check();
    }
  }
  @SuppressWarnings("unchecked") static Map<String,Object> object(Object value){return (Map<String,Object>)value;}
  static Map<String,Object> ready(){
    var doc=pending();
    doc.put("customerSession",m("requestId","prepare-1","id","session-1","status","ready","paymentDueAt",1000,"expiresAt",1000,"paymentAttemptId","","failureReason",""));
    doc.put("instanceKey","customer-payment-1");
    doc.put("paymentAction",m("kind","customer-payment","id","session-1"));
    doc.put("payment",m("accepted",true,"rejected",false,"closed",false,"transactionId","transaction-1","completed",0,"secured",0,"reversed",0,"targetMinor",100,"cancellationPending",false,"requests",m(),"controlRequests",m(),"reserved",m("secure",0,"capture",0,"refund",0,"void",0),"locks",m("secure",false,"capture",false,"refund",false,"void",false)));
    return doc;
  }
  static boolean same(Object a,Object b){return a instanceof Number && b instanceof Number ? new java.math.BigDecimal(a.toString()).compareTo(new java.math.BigDecimal(b.toString()))==0 : Objects.equals(a,b);}
  static void event(Engine.Result result,String kind,Map<String,Object> fields){
    require(result.events().stream().anyMatch(raw->{var row=object(raw);return kind.equals(row.get("kind"))&&fields.entrySet().stream().allMatch(e->same(e.getValue(),row.get(e.getKey())));}),"Expected event "+kind+" "+fields+" actual="+result.events());
  }
  static void startEffects(){
    var request=m("sessionId","session-1","requestId","attempt-1");
    var result=ProviderInputConformance.execute(TYPE,"requestCustomerPayment",request,ready(),"bank");
    ProviderInputConformance.change(result,"/payment/reserved/secure",BigInteger.valueOf(100));
    ProviderInputConformance.change(result,"/customerSession/paymentAttemptId","attempt-1");
    require(result.changeset().stream().anyMatch(x->"remove".equals(object(x).get("op"))&&"/paymentAction".equals(object(x).get("path"))),"Accepted attempt removes the checkout action");
    event(result,"Payment Requested",m("requestId","attempt-1","amountMinor",100,"type",ProviderInputConformance.typed("PaymentInstruction/Secure Funds Requested",m()).get("type")));
    for(String actor:List.of("payer","seller"))rejected("requestCustomerPayment",request,ready(),actor,"Guarantor workflow required","Payer cannot invoke public payment in guarantor role");
    var expired=ready();object(expired.get("customerSession")).put("paymentDueAt",100);
    rejected("requestCustomerPayment",request,expired,"bank","CUSTOMER_SESSION_EXPIRED","A new attempt cannot begin at the deadline");
    var unknown=ready();object(unknown.get("customerSession")).put("paymentAttemptId","attempt-1");
    object(unknown.get("payment")).put("requests",m("attempt-1",m("intent",m("action","secure","amountMinor",100,"reason",""),"status","unknown")));
    object(unknown.get("payment")).put("reserved",m("secure",100,"capture",0,"refund",0,"void",0));
    var repeated=ProviderInputConformance.execute(TYPE,"requestCustomerPayment",request,unknown,"bank",2000);
    require(repeated.changeset().isEmpty()&&repeated.events().isEmpty(),"Same unknown attempt reconciles after deadline without a second charge request");
    rejected("requestCustomerPayment",m("sessionId","session-1","requestId","attempt-2"),unknown,"bank","CUSTOMER_PAYMENT_ATTEMPT_ALREADY_EXISTS","Unknown attempt cannot be replaced");
  }
  /** Characterizes the unchanged published request guard; this is not hosted authorization. */
  static void capturePolicy(){
    var values=ProviderInputConformance.values;var runtime=ProviderInputConformance.runtime;
    var definition=NativeRuntime.head(NativeRuntime.recipe(values.source(m("type","PaymentInstruction/Payment Functions"),"definition")),runtime);
    var library=new LinkedHashMap<String,Object>();
    for(String field:List.of("constants","functions")) {
      var selected=NativeRuntime.child(definition,field);
      if(selected!=null)library.put(field,values.bexData(selected));
    }
    var bex=new Bex(BexProfile.current());
    var program=bex.compile(m("constants",m("sourceMode","workflow"),"do",List.of(m("$call",m("function","request","args",m("action","capture","input",m("requestId","capture-policy-1","amountMinor",100)))))),library,null);
    for(String state:List.of("missing","false","true")) {
      var doc=ready();object(doc.get("paymentTerms")).put("captureGate","/capturePolicy/allowed");
      if(!state.equals("missing"))doc.put("capturePolicy",m("allowed",state.equals("true")));
      object(doc.get("payment")).put("secured",100);object(doc.get("payment")).put("payeeChannel","bank");
      String before=WireData.write(doc);
      var context=new BexContext(doc,m(),m(),Values.UNDEFINED,m(),m("call",m("channel","bank"),"timestamp",100),"/",null,
          (actual,pattern)->values.matches(values.source(actual),values.source(pattern,"definition")),
          (actual,gas)->NativeRuntime.identity(values.source(actual)));
      try {
        var result=bex.execute(program,context,1000000);
        require(state.equals("true"),"Unsatisfied capture policy must reject before reserving or emitting");
        ProviderInputConformance.change(result,"/payment/reserved/capture",BigInteger.valueOf(100));
        event(result,"Payment Requested",m("requestId","capture-policy-1","amountMinor",100,"type",ProviderInputConformance.typed("PaymentInstruction/Complete Payment Requested",m()).get("type")));
      } catch(BexError failure) {
        require(!state.equals("true")&&failure.getMessage().contains("CAPTURE_CONDITIONS_NOT_MET"),"Expected exact policy refusal, actual="+failure.getMessage());
      }
      require(before.equals(WireData.write(doc)),"Evaluation cannot mutate the source document");
    }
    System.out.println("PASS frozen capture guard: missing/false refused, true reserves and emits completion request");
  }
  static void preparationEffects(){
    var doc=pending();object(doc.get("customerSession")).put("status","idle");
    var first=ProviderInputConformance.execute(TYPE,"__customerPrepareSession",m(),doc,"__customerAccepted");
    long deadline=100L+30L*86400000000L;
    ProviderInputConformance.change(first,"/customerSession/paymentDueAt",BigInteger.valueOf(deadline));
    event(first,"Customer Payment Session Requested",m("requestId","customer-session-1","amountMinor",100,"currency","USD","provider","test","recipientPaymentAccountId","account-1","paymentDueAt",BigInteger.valueOf(deadline)));
    var repeated=ProviderInputConformance.execute(TYPE,"__customerPrepareSession",m(),pending(),"__customerAccepted");
    require(repeated.changeset().isEmpty()&&repeated.events().isEmpty(),"Repeated acceptance does not prepare a second session or extend deadline");
  }
  static void check() {
      var input=response();
      ProviderInputConformance.valid(TYPE,"provideSession",input,"requestId");
      ProviderInputConformance.valid(TYPE,"provideSession",input,"sessionId");
      var result=ProviderInputConformance.execute(TYPE,"provideSession",input,pending(),"bank");
      ProviderInputConformance.change(result,"/customerSession/id","session-1");
      ProviderInputConformance.change(result,"/customerSession/status","ready");
      var wrong=new LinkedHashMap<>(input);wrong.put("requestId","other-request");
      rejected("provideSession",wrong,pending(),"bank","CUSTOMER_SESSION_REQUEST_MISMATCH","An unrelated preparation response must fail");
      wrong=new LinkedHashMap<>(input);wrong.put("expiresAt",2000);
      rejected("provideSession",wrong,pending(),"bank","CUSTOMER_SESSION_EXPIRY_MISMATCH","The provider cannot extend the PI payment deadline");
      for(String actor:List.of("payer","seller"))rejected("provideSession",input,pending(),actor,"Guarantor workflow required","Payer cannot provide a session");
      var ready=pending();ready.put("customerSession",m("requestId","prepare-1","id","session-1","status","ready","paymentDueAt",1000,"expiresAt",1000,"paymentAttemptId","","failureReason",""));
      var duplicate=ProviderInputConformance.execute(TYPE,"provideSession",input,ready,"bank");
      require(duplicate.changeset().isEmpty()&&duplicate.events().isEmpty(),"Identical response has no second state effect or Ready event");
      wrong=new LinkedHashMap<>(input);wrong.put("sessionId","other-session");
      rejected("provideSession",wrong,ready,"bank","SESSION_ID_CONFLICT","A conflicting duplicate must fail");
      var failure=m("requestId","prepare-1","reason","recipient_unavailable");
      ProviderInputConformance.change(ProviderInputConformance.execute(TYPE,"failSessionPreparation",failure,pending(),"bank"),"/customerSession/status","failed");
      rejected("failSessionPreparation",failure,ready,"bank","CUSTOMER_SESSION_NOT_PENDING","Known failure cannot replace a ready session");
      var failed=pending();object(failed.get("customerSession")).put("status","failed");object(failed.get("customerSession")).put("failureReason","recipient_unavailable");
      var repeatedFailure=ProviderInputConformance.execute(TYPE,"failSessionPreparation",failure,failed,"bank");
      require(repeatedFailure.changeset().isEmpty()&&repeatedFailure.events().isEmpty(),"Known failure duplicate is inert");
      rejected("failSessionPreparation",m("requestId","prepare-1","reason","different"),failed,"bank","CUSTOMER_SESSION_FAILURE_CONFLICT","A contradictory known failure cannot replace the first result");
      ProviderInputConformance.valid(TYPE,"requestCustomerPayment",m("sessionId","session-1","requestId","attempt-1"),"requestId");
      ProviderInputConformance.valid(TYPE,"requestCustomerPayment",m("sessionId","session-1","requestId","attempt-1"),"sessionId");
      preparationEffects();
      startEffects();
      System.out.println("PASS Customer preparation, correlation, secure request, deadline, authorization and reconciliation effects");
  }
}
