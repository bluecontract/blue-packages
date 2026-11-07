/** Native channel/inner matcher parity; no hosted receiving or financial-success claim. */
import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;
public class CommissionChannelFilterConformance {
 static Map<String,Object> m(Object... pairs){var x=new LinkedHashMap<String,Object>();for(int i=0;i<pairs.length;i+=2)x.put((String)pairs[i],pairs[i+1]);return x;}
 @SuppressWarnings("unchecked") static Map<String,Object> o(Object x){return (Map<String,Object>)x;}
 public static void main(String[] args)throws Exception{
  var root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
  try(var blue=packages.language();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())){
   var processor=runtime.processor(blue);var v=processor.execution().values();
   var publishedClause=v.source(m("type","Reseller/Commission Clause"),"definition");
   var authored=o(WireData.parse(Files.readString(root.resolve("clause-reseller/types/commission-clause.blue")),"yaml"));
   var cases=new LinkedHashMap<String,Object>();
   cases.put("completed",m("type","Payment/Payment Event Received","event",m("type","PaymentInstruction/Payment Completed","requestId","capture-test","amountCompleted",2500)));
   cases.put("reversed",m("type","Payment/Payment Event Received","event",m("type","PaymentInstruction/Payment Reversed After Completion","requestId","refund-test","amountReversed",2500)));
   cases.put("other-payment",m("type","Payment/Payment Event Received","event",m("type","Events/Event")));
   cases.put("bare-completed",m("type","PaymentInstruction/Payment Completed","requestId","capture-test","amountCompleted",2500));
   cases.put("generic",m("type","Events/Event"));
   cases.put("untyped-lookalike",m("event",m("type","PaymentInstruction/Payment Completed","requestId","capture-test","amountCompleted",2500)));
   for(var value:cases.values()){var event=o(value);if("Payment/Payment Event Received".equals(event.get("type"))){event.put("kind","payment");event.put("clause","payment");event.put("instructionPath","/payment");}}
   var host=BootstrapPreparationConformance.source(null);
   host.put("orders",m());host.put("payouts",m());host.put("terms",m("commissionBps",1200));
   o(host.get("clauses")).put("commission",m("type","Reseller/Commission Clause","bindings",m("state","/commission","orders","/orders","payouts","/payouts","rate","/terms/commissionBps")));
   var unfilteredAction=m("automatic",m("on","collection","path","/orders"),"do",List.of(m("$return",m())));
   var unfilteredType=m("type","Connections/Connected Clause","actions",m("observe",unfilteredAction));
   o(host.get("clauses")).put("unfiltered",m("type",unfilteredType));
   var initialized=processor.initialize(host);
   if(!initialized.commits())throw new AssertionError(initialized.status()+" "+initialized.observations());
   var initializedRoot=new Exact.Ref(initialized.document().blueId());
   if(v.select(initializedRoot,"/contracts/cx.unfiltered.observe._automatic_source/event")!=null)throw new AssertionError("Unfiltered collection must remain unfiltered");
   if(v.select(initializedRoot,"/contracts/prepareOrder/request")==null)throw new AssertionError("Existing workflow request definition retained");
   var rows=new ArrayList<Object>();
   for(String action:List.of("confirmed","reversed","observed")){
    var a=o(o(authored.get("actions")).get(action));var first=o(((List<?>)a.get("do")).getFirst());
    var pattern=o(o(o(o(first.get("$if")).get("cond")).get("$not")).get("$is")).get("pattern");
    if(!pattern.equals(o(a.get("automatic")).get("event")))throw new AssertionError(action+" channel must retain exact inner pattern");
    var nativePattern=v.source(pattern,"definition");
    for(var c:cases.entrySet()){
     var event=v.source(c.getValue());var delivery=v.source(m("type","Contracts/Embedded Event Delivery","sourcePath","/orders/example","event",m("blueId",NativeRuntime.identity(event))));
     boolean channel=v.matches(event,nativePattern);
     var installed=v.select(initializedRoot,"/contracts/cx.commission."+action+"._automatic_source/event");
     if(installed==null)throw new AssertionError(action+" compiled channel event missing");
     boolean dispatched=v.matches(event,v.exact(installed));
     boolean published=v.matches(event,v.exact(v.select(publishedClause,"/actions/"+action+"/automatic/event")));boolean inner=v.matches(v.exact(v.select(delivery,"/event")),nativePattern);
     boolean expected=action.equals("observed")?Set.of("completed","reversed","other-payment").contains(c.getKey()):action.equals("confirmed")?c.getKey().equals("completed"):c.getKey().equals("reversed");
     if(channel!=inner||channel!=expected||published!=channel||dispatched!=channel)throw new AssertionError(action+"/"+c.getKey()+" channel="+channel+" inner="+inner+" expected="+expected);
     rows.add(m("action",action,"case",c.getKey(),"channel",channel,"inner",inner,"published",published,"installed",dispatched));
    }
   }
   Files.writeString(Path.of(args[1]),WireData.write(m("boundary","Native matcher equivalence only; synthetic event cases, no financial dispatch or measured RECEIVE gas", "rows",rows)));
   System.out.println("PASS "+rows.size()+" native matcher comparisons");
  }
 }
}
