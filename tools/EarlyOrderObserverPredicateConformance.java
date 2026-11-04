import blue.bex.*;
import blue.contracts.*;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Predicate-only adversarial checks; these do not replace hosted source/access propagation. */
public final class EarlyOrderObserverPredicateConformance {
 static Map<String,Object> m(Object... v){return OperationInputConformance.m(v);}
 @SuppressWarnings("unchecked") static Map<String,Object> obj(Object v){return (Map<String,Object>)v;}
 static void require(boolean b,String s){OperationInputConformance.require(b,s);}
 public static void main(String[] args)throws Exception {
  Path root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
  try(var blue=packages.language()) {
   var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
   String order=NativeRuntime.identity(values.source(m("name","Order origin")));
   String pi=NativeRuntime.identity(values.source(m("name","PI origin")));
   var terms=m("amountMinor",100,"currency","USD");var customer=m("provider","test","recipientPaymentAccountId","account");
   var source=m("contracts",m("initialized",m("document",m("blueId",order))),"activation",m("active",true,"approved",m("seller",true),"revision",1,"terms",m("ref","review")),"orderDecision",m("status","PENDING"),"payment",m("contracts",m("initialized",m("document",m("blueId",pi)))),"paymentTemplate",m("paymentTerms",terms,"paymentDetails",m("customerPaymentTerms",customer)));
   var base=m("contracts",m("initialized",m("document",m("blueId",pi))),"sources",m("order",source),"paymentPreparation",m("orderDocumentId",order),"customerOrderTerms",m("revision",1,"termsRef","review"),"paymentTerms",terms,"paymentDetails",m("customerPaymentTerms",customer),"customerCaptureAllowed",false,"customerOrderState",m());
   var authored=obj(BuildFinalGas.read(root.resolve("myos-payment-mandates/types/early-order-payment-observer.blue")));
   var action=obj(obj(authored.get("actions")).get("refresh"));var bex=new Bex(BexProfile.current());var program=bex.compile(action,m(),null);
   for(String scenario:List.of("accepted","pending-spoof-reject-event","source-missing","wrong-origin","wrong-backlink","revision","terms","amount","provider","account","access","rejected")) {
    var doc=obj(WireData.json(WireData.write(base)));var actual=obj(obj(doc.get("sources")).get("order"));var activation=obj(actual.get("activation"));
    switch(scenario) {
     case "pending-spoof-reject-event" -> {activation.put("active",false);activation.put("approved",m());}
     case "source-missing" -> doc.put("sources",m());
     case "wrong-origin" -> obj(doc.get("paymentPreparation")).put("orderDocumentId",pi);
     case "wrong-backlink" -> actual.put("payment",m());
     case "revision" -> activation.put("revision",2);
     case "terms" -> activation.put("terms",m("ref","changed"));
     case "amount" -> obj(obj(actual.get("paymentTemplate")).get("paymentTerms")).put("amountMinor",101);
     case "provider" -> obj(obj(obj(actual.get("paymentTemplate")).get("paymentDetails")).get("customerPaymentTerms")).put("provider","stripe");
     case "account" -> obj(obj(obj(actual.get("paymentTemplate")).get("paymentDetails")).get("customerPaymentTerms")).put("recipientPaymentAccountId","different");
     case "access" -> activation.put("active",false);
     case "rejected" -> actual.put("orderDecision",m("status","REJECTED","revision",1,"termsRef","review"));
    }
    var context=new BexContext(doc,m("revision",999,"termsRef","forged","status","REJECTED"),m(),Values.UNDEFINED,m(),m(),"/",null,(a,p)->values.matches(values.source(a),values.source(p,"definition")),(a,g)->NativeRuntime.identity(values.source(a)));
    var result=bex.execute(program,context,1000000);
    var changes=result.changeset();
    var state=changes.stream().filter(v->v instanceof Map<?,?> c&&"/customerOrderState".equals(c.get("path"))).map(v->obj(obj(v).get("val"))).findFirst().orElseThrow();
    require(Boolean.TRUE.equals(state.get("captureAllowed"))==scenario.equals("accepted"),"Capture predicate: "+scenario);
    require(Boolean.TRUE.equals(state.get("cancellationRequested"))==scenario.equals("rejected"),"Cancellation follows authoritative source only: "+scenario);
    require(result.events().isEmpty(),"Observer emits no financial or recursive events");
   }
   System.out.println("PASS 12 observer predicate cases; spoof payload ignored, source/origin/backlink/terms/access gates, no financial events");
  }
 }
}
