import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import blue.bex.*;
import java.nio.file.*;
import java.util.*;

/** Native decision qualification; no handwritten activation state or financial ledger. */
public final class EarlyOrderDecisionConformance {
  static Map<String,Object> m(Object... values){return OperationInputConformance.m(values);}
  static void require(boolean value,String message){OperationInputConformance.require(value,message);}
  static Object doc(String path){return m("$document",path);}
  static Object eq(Object left,Object right){return m("$eq",List.of(left,right));}
  static Object event(Contracts.Document d,String operation,Object request){return eventId(d.blueId(),operation,request);}
  static Object eventId(String id,String operation,Object request){return m("source","seller","operation",m("type","Contracts/Operation Request","channel","seller","operation",operation,"document",m("blueId",id),"request",request,"requireExactDocumentVersion",true));}
  static Object paymentTerms(){return m("amountMinor",100,"currency","USD");}
  static Object customerTerms(){return m("provider","test","recipientPaymentAccountId","test-account");}
  // attachPayment is a local event-delivery fixture matching native Document Selected notification; hosted ordinary provision is qualified in Core.
  static Map<String,Object> source(Path root)throws Exception{
    var channel=m("type","Contracts/External Channel","event",m("source","seller"));
    return m("name","Pending seller Order","type","Orders/Order with Clauses","orderDecision",m("status","PENDING"),"paymentTemplate",m("paymentTerms",paymentTerms(),"paymentDetails",m("customerPaymentTerms",customerTerms())),"contracts",m("seller",channel,"attachPayment",m("type","Contracts/Sequential Workflow Operation","channel","seller","steps",List.of(m("type","Contracts/Update Document","changeset",List.of(m("op","add","path","/payment","val",m("$binding","call/request/payment")))),m("type","Contracts/Compute","do",List.of(m("$appendEvent",m("type","Documents/Document Selected","clauseId","payment","itemKey","single")))))),"earlyOrderDecision",BuildFinalGas.read(root.resolve("myos-payment-mandates/types/early-order-decision-guard.blue"))),"clauses",m(
      "activation",m("type","Activation/Activation Clause","parameters",m("parties",m("seller",m("type","Parties/Party","lead",m("channel",channel),"readerKeys",List.of("seller-reader"))),"required",List.of("seller"),"preActivationOperations",List.of("rejectOrder","attachPayment"))),
      "orderDecision",m("type",BuildFinalGas.read(root.resolve("myos-payment-mandates/types/early-order-decision.blue")),"bindings",m("reject",m("rejectOrder",m("on","workflow","party","seller","request",m("revision",m("type","Integer")),"params",m("$object",m("$var","trigger"))))))));
  }
  static void observe(Path root, Contracts p, Contracts.Document order) throws Exception {
    p.execution().chooseHistory(order.blueId(),p.execution().snapshot(order));
    var observer=BuildFinalGas.read(root.resolve("myos-payment-mandates/types/early-order-payment-observer.blue"));
    var receiver=p.initialize(m("name","Independent observer","type",m("type","Orders/Order with Clauses","clauses",((Map<?,?>)BuildFinalGas.read(root.resolve("myos-payment-mandates/types/early-order-customer-instruction.blue"))).get("clauses")),
      "paymentTerms",paymentTerms(),"paymentDetails",m("customerPaymentTerms",customerTerms()),"customerOrderTerms",m("revision",p.read(order,"/activation/revision"),"termsRef",p.read(order,"/activation/terms/ref")),"paymentPreparation",m("orderDocumentId",NativeRuntime.identity(p.execution().values().exact(p.execution().values().select(new Exact.Ref(order.blueId()),"/contracts/initialized/document")))) ,"sources",m("order",m("blueId",order.blueId())),
      "clauses",m("orderObserver",m("type",observer,"bindings",m("refresh",m(
        "changed",m("on","change","path","/sources/order"),"source",m("on","embedded","path","/sources/order"),"initial",m("on","initialized")))))));
    require(receiver.commits(),"Observer initialized: "+receiver.observations());
    require(Boolean.FALSE.equals(p.read(receiver.document(),"/customerOrderState/captureAllowed")),"Native initializer keeps pending source gate false");
    require("WAITING".equals(p.read(receiver.document(),"/customerOrderState/status")),"Native initializer/observer exposes WAITING");
    p.execution().chooseHistory(receiver.document().blueId(),p.execution().snapshot(receiver.document()));
    var linked=p.process(receiver.document(),event(order,"attachPayment",m("payment",m("blueId",receiver.document().blueId()))),1);
    require(linked.commits(),"Backlink attach: "+linked.observations());
    require(p.read(linked.document(),"/sources/order/activation/revision").equals(p.read(order,"/activation/revision")),"Backlink preserves native review revision");
    require(p.read(linked.document(),"/sources/order/activation/terms/ref").equals(p.read(order,"/activation/terms/ref")),"Backlink preserves native review terms");
    require(!Boolean.TRUE.equals(p.read(linked.document(),"/customerOrderState/captureAllowed")),"Backlink alone does not approve");
    var currentOrder=NativeRuntime.identity(p.execution().values().exact(p.execution().values().select(new Exact.Ref(linked.document().blueId()),"/sources/order")));
    var approved=p.process(linked.document(),eventId(currentOrder,"approve_seller",m("revision",1)),2);
    require(approved.commits(),"Embedded approval processes: "+approved.observations());
    require(Boolean.TRUE.equals(p.read(approved.document(),"/sources/order/activation/approved/seller")),"Real embedded source observes seller approval: "+approved.observations());
    require(Boolean.TRUE.equals(p.read(approved.document(),"/customerOrderState/captureAllowed")),"Source observer opens gate after real approval: "+approved.observations());
    var refused=p.process(linked.document(),eventId(currentOrder,"rejectOrder",m("revision",1)),2);
    require(refused.commits(),"Embedded seller rejection processes");
    require(!Boolean.TRUE.equals(p.read(refused.document(),"/customerOrderState/captureAllowed")),"Rejection never opens gate");
    require(Boolean.TRUE.equals(p.read(refused.document(),"/customerOrderState/cancellationRequested")),"Native rejection exposes only cancellation intent: source="+p.read(refused.document(),"/sources/order/orderDecision")+" sourceApproved="+p.read(refused.document(),"/sources/order/activation/approved")+" observed="+p.read(refused.document(),"/customerOrderState")+" diagnostics="+refused.observations());
    require("REJECTED".equals(p.read(refused.document(),"/customerOrderState/status")),"Source rejection status observed");
    require(p.read(refused.document(),"/customerOrderState/decision/revision").equals(p.read(order,"/activation/revision")),"Cancellation bound to native review");
    var beforeLink=p.process(receiver.document(),event(order,"approve_seller",m("revision",1)),1);
    require(!Boolean.TRUE.equals(p.read(beforeLink.document(),"/customerOrderState/captureAllowed")),"Approved wrong/missing backlink remains closed");
    var approvedOrder=NativeRuntime.identity(p.execution().values().exact(p.execution().values().select(new Exact.Ref(beforeLink.document().blueId()),"/sources/order")));
    var lateLink=p.process(beforeLink.document(),eventId(approvedOrder,"attachPayment",m("payment",m("blueId",receiver.document().blueId()))),2);
    require(Boolean.TRUE.equals(p.read(lateLink.document(),"/customerOrderState/captureAllowed")),"Late reciprocal link reevaluates existing approval");
    System.out.println("PASS native embedded source approval, rejection intent, reciprocal link and late attachment (not hosted B0)");
  }
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())){
      var p=runtime.processor(packages.language());var result=p.initialize(source(root));
      require(result.commits(),"Initialized pending Order: "+result.observations());
      var initial=result.document();require(!Boolean.TRUE.equals(p.read(initial,"/activation/active")),"Seller approval outstanding");
      result=p.process(initial,event(initial,"rejectOrder",m("revision",1)),1);
      require("REJECTED".equals(p.read(result.document(),"/orderDecision/status")),"Seller rejection recorded: "+result.observations());
      require(p.emitted(result).size()==1,"One native rejection event");
      var rejected=result.document();result=p.process(rejected,event(rejected,"approve_seller",m("revision",1)),2);
      require(!Boolean.TRUE.equals(p.read(result.document(),"/activation/active")),"Rejected Order must not subsequently activate");
      var repeated=p.process(result.document(),event(result.document(),"rejectOrder",m("revision",1)),3);
      require(repeated.commits(),"Same rejection remains resumable");
      require(p.emitted(repeated).isEmpty(),"Rejection replay emits no duplicate event");
      require("REJECTED".equals(p.read(repeated.document(),"/orderDecision/status")),"Terminal decision preserved");
      require(!Boolean.TRUE.equals(p.read(repeated.document(),"/activation/active")),"Replay never approves");
      var accepted=p.process(initial,event(initial,"approve_seller",m("revision",1)),1);
      require(Boolean.TRUE.equals(p.read(accepted.document(),"/activation/active")),"Normal seller approval preserved");
      var late=p.process(accepted.document(),event(accepted.document(),"rejectOrder",m("revision",1)),2);
      require(!"REJECTED".equals(p.read(late.document(),"/orderDecision/status")),"Cannot reject accepted Order");
      var wrong=p.process(initial,event(initial,"rejectOrder",m("revision",2)),1);
      require(!"REJECTED".equals(p.read(wrong.document(),"/orderDecision/status")),"Wrong revision denied");
      observe(root, p, initial);
      System.out.println("PASS native seller rejection, replay, late approval denial, accepted and wrong revision guards");
    }
  }
}
