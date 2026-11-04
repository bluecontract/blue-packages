import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import java.nio.file.*;
import java.util.*;

/** Native binding proof only; seller decision/source authority is qualified separately. */
public final class EarlyVoidConnectionConformance {
 static Map<String,Object> m(Object... v){return OperationInputConformance.m(v);}
 @SuppressWarnings("unchecked") static Map<String,Object> obj(Object v){return (Map<String,Object>)v;}
 static void require(boolean b,String s){OperationInputConformance.require(b,s);}
 static Object d(String p){return m("$document",p);}
 static Object eq(String p,Object v){return m("$eq",List.of(d(p),v));}
 static final String ID="order-reject:order-origin:1:review";
 static Object binding(String path){return m("on","change","path",path,"when",m("$and",List.of(
   eq("/customerOrderState/cancellationRequested",true),eq("/payment/accepted",true),m("$ne",List.of(d("/payment/transactionId"),"")),
   eq("/payment/closed",false),eq("/payment/cancellationPending",false),m("$ne",List.of(d("/payment/locks/void"),true)),
   eq("/payment/reserved/secure",0),eq("/payment/reserved/capture",0),eq("/payment/reserved/void",0))),
   "params",m("requestId",m("$concat",List.of("order-reject:",d("/paymentPreparation/orderDocumentId"),":",d("/customerOrderState/decision/revision"),":",d("/customerOrderState/decision/termsRef"))),"amountMinor",d("/payment/secured")));}
 static Contracts.Result invoke(Contracts p,Contracts.Result s,String role,String op,Object request,long time){
   var r=p.process(s.document(),m("source",role,"operation",m("type","Contracts/Operation Request","channel",role,"operation",op,"document",m("blueId",s.document().blueId()),"request",request,"requireExactDocumentVersion",true)),time);
   require(r.commits(),op+": "+r.status()+" "+r.observations());return r;
 }
 public static void main(String[] args)throws Exception{
  Path root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
  for(String scenario:List.of("zero","secured","pending"))try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())){
   var p=runtime.processor(packages.language());var source=obj(BuildFinalGas.read(root.resolve("examples/apps/27-payment-protocol.blue")));
   obj(source.get("paymentTerms")).put("amountMinor",100);obj(source.get("paymentTerms")).put("limitMinor",100);
   source.put("paymentPreparation",m("orderDocumentId","order-origin"));source.put("customerOrderState",m("cancellationRequested",false,"captureAllowed",false,"decision",m("revision",1,"termsRef","review")));
   var clauses=obj(source.get("clauses"));var activation=obj(obj(clauses.get("activation")).get("parameters"));activation.put("required",List.of());
   var contracts=m();source.put("contracts",contracts);
   for(String role:List.of("customer","seller","seller2","guarantor")){
    var channel=m("type","Contracts/External Channel","event",m("source",role));contracts.put(role,channel);
    obj(obj(activation.get("parties")).get(role)).putAll(m("lead",m("channel",channel),"readerKeys",List.of(role+"-reader")));
   }
   contracts.put("rejectProbe",m("type","Contracts/Sequential Workflow Operation","channel","seller","steps",List.of(m("type","Contracts/Update Document","changeset",List.of(m("op","add","path","/customerOrderState/cancellationRequested","val",true))))));
   var requests=obj(clauses.get("requests"));requests.put("type","Payment/Payment Process Clause");requests.put("parameters",m("method","reservation","capture",m("mode","when","requestId","capture-1","when",eq("/customerOrderState/captureAllowed",true))));
   var bindings=obj(requests.get("bindings"));bindings.remove("requestCapture");
   obj(bindings.get("requestVoid")).putAll(m("cancelOnDecision",binding("/customerOrderState"),"cancelAfterOutcome",binding("/payment")));
   var state=p.initialize(source);require(state.commits(),"Initialize: "+state.observations());
   state=invoke(p,state,"guarantor","acceptPaymentInstruction",m(),1);
   state=invoke(p,state,"guarantor","recordTransactionInitiated",m("type","PaymentInstruction/Transaction Initiation Input","transactionId","transaction","railType","test","attachmentPoint","instruction","providerReference","provider-one"),2);
   if(!scenario.equals("zero"))state=invoke(p,state,"customer","requestSecureFunds",m("type","PaymentInstruction/Payment Request Input","requestId","secure-1","amountMinor",100),3);
   if(scenario.equals("secured"))state=invoke(p,state,"guarantor","secureFunds",m("type","PaymentInstruction/Payment Outcome Input","requestId","secure-1","amountSecured",100),4);
   state=invoke(p,state,"seller","rejectProbe",m(),5);
   if(scenario.equals("pending")){
    require(!obj(p.read(state.document(),"/payment/requests")).containsKey(ID),"Pending secure must reconcile before VOID");
    state=invoke(p,state,"guarantor","secureFunds",m("type","PaymentInstruction/Payment Outcome Input","requestId","secure-1","amountSecured",100),6);
   }
   var request=obj(obj(p.read(state.document(),"/payment/requests")).get(ID));require(request!=null,"Authoritative cancellation must issue ordinary VOID: "+scenario);
   require("void".equals(obj(request.get("intent")).get("action")),"Canonical void request");
   require(!Boolean.TRUE.equals(p.read(state.document(),"/payment/closed")),"Intent/request does not close funds");
   require(!obj(p.read(state.document(),"/payment/requests")).containsKey("capture-1"),"Capture remains blocked");
   state=invoke(p,state,"guarantor","cancelBeforeCompletion",m("type","PaymentInstruction/Payment Outcome Input","requestId",ID,"amountCancelled",scenario.equals("zero")?0:100),7);
   require(Boolean.TRUE.equals(p.read(state.document(),"/payment/closed")),"Only native outcome closes PI");
   require("0".equals(p.read(state.document(),"/payment/secured").toString()),"Native VOID releases the remaining authorization");
   require("0".equals(p.read(state.document(),"/payment/completed").toString()),"Rejected Order never captures funds");
   int count=obj(p.read(state.document(),"/payment/requests")).size();state=invoke(p,state,"seller","rejectProbe",m(),8);
   require(count==obj(p.read(state.document(),"/payment/requests")).size(),"Retry creates no second request");
   System.out.println("PASS ordinary VOID binding "+scenario);
  }
 }
}
