import blue.core.CompositionPackages;
import blue.coordination.AuthoringRuntime;
import blue.contracts.*;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;
/** Retained preview.9 deferred customer resolution with component channels. */
public class DeferredCustomerConformance {
 static Map<String,Object> m(Object... p){return BootstrapOrdersConformance.m(p);}
 static Map<String,Object> obj(Object p){return BootstrapOrdersConformance.obj(p);}
 static void run(CompositionPackages packages, Path root, Path report, String variant) throws Exception {
  Files.createDirectories(report);
  var fixture=obj(WireData.json(Files.readString(root.resolve("clause-reseller/tests/fixtures/01-cruise/catalogue.json"))));
  try(var blue=packages.language();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
   var p=runtime.processor(blue);
   var source=BootstrapOrdersConformance.source(fixture,true,(variant.equals("inactive") || variant.equals("same-seller"))?List.of("seller"):List.of());
   if(variant.equals("collision"))obj(obj(source.get("orderTemplate")).get("clauses")).put("customerBinding",m("type","Connections/Connected Clause"));
   var d=BootstrapOrdersConformance.applied(p.initialize(source));
   d=BootstrapOrdersConformance.applied(p.process(d.document(),BootstrapOrdersConformance.event(d.document(),"createQuote",obj(fixture.get("quote")).get("intent")),1));
   var request=m("key","deferred","requestId","deferred","quoteKey","family-quote","groups",fixture.get("groups"));
   var input=BootstrapOrdersConformance.event(d.document(),"newOrder",request);
   var result=p.process(d.document(),input,2);if(variant.equals("collision")){BootstrapOrdersConformance.require(!result.commits(),"Existing customerBinding clause must not be overwritten");System.out.println("PASS customerBinding collision rejected");return;}if(!result.commits())ClauseGasProbe.diagnose(p,d.document(),input,2);
   d=BootstrapOrdersConformance.applied(result);
   var item=BootstrapOrdersConformance.item(p,d.document());
   Files.writeString(report.resolve("prepared-parent.json"),WireData.write(p.exportSnapshot(d.document())));
   var prepared=obj(BootstrapOrdersConformance.literal(p,d.document(),item.get("itemPath")+"/prepared"));
   Files.writeString(report.resolve("prepared-order.json"),WireData.write(prepared));Files.writeString(report.resolve("item.json"),WireData.write(BootstrapOrdersConformance.literal(p,d.document(),item.get("itemPath").toString())));
   BootstrapOrdersConformance.require(!prepared.containsKey("customerAccountId"),"Requirement has no customer account identity");
   BootstrapOrdersConformance.require(!obj(obj(prepared.get("orderSnapshot")).get("customer")).containsKey("myosAccountId"),"Fulfilment snapshot has no guessed customer account");
   BootstrapOrdersConformance.equal(obj(prepared.get("orderSnapshot")).get("customer"),m(),"Deferred snapshot is plain empty identity, not a live Party");
   BootstrapOrdersConformance.equal(obj(prepared.get("orderSnapshot")).get("seller"),m("myosAccountId","seller-account"),"Seller snapshot contains only frozen identity");
   var replay=BootstrapOrdersConformance.applied(p.process(d.document(),BootstrapOrdersConformance.event(d.document(),"newOrder",request),3));
   BootstrapOrdersConformance.equal(BootstrapOrdersConformance.item(p,replay.document()),item,"Same request keeps one obligation");
   var parties=obj(obj(obj(obj(prepared.get("clauses")).get("activation")).get("parameters")).get("parties"));
   parties.forEach((role,raw)->{var party=obj(raw);party.put("myosAccountId",role.equals("customer")?(variant.equals("same-seller")?"seller-account":"resolved-customer"):role+"-account");party.put("readerKeys",List.of(role+"-reader"));party.put("lead",m("channel",BootstrapOrdersConformance.channel(role)));obj(party.getOrDefault("representatives",m())).forEach((key,value)->{if(!key.equals("type"))obj(value).put("channel",BootstrapOrdersConformance.channel(role+"-"+key));});});
   var child=p.initialize(prepared);if(variant.equals("same-seller")){BootstrapOrdersConformance.require(!child.commits(),"Resolved customer must remain distinct from seller"); System.out.println("PASS deferred seller substitution rejected"); return;}if(!child.commits())ClauseGasProbe.diagnose(p,prepared);BootstrapOrdersConformance.applied(child);
   BootstrapOrdersConformance.equal(p.read(child.document(),"/customerAccountId"),"resolved-customer","Derived customer bound once at ordinary child initialization");
   BootstrapOrdersConformance.equal(p.read(child.document(),"/orderSnapshot/customer/myosAccountId"),"resolved-customer","Fulfilment customer agrees with actual party");
   Files.writeString(report.resolve("initialized-child-component.json"),WireData.write(p.exportSnapshot(child.document())));
   System.out.println("PASS deferred native preparation + exact replay + component child account/fulfilment binding; actual hosted email bootstrap/provide remains separate");
  }
 }
}
