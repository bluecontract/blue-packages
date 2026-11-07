import blue.core.CompositionPackages;
import blue.coordination.AuthoringRuntime;
import blue.contracts.*;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;
/** Native component probe; real email bootstrap and provide are qualified separately in Core. */
public class DeferredCustomerConformance {
 static Map<String,Object> m(Object... p){return BootstrapOrdersConformance.m(p);}
 static Map<String,Object> obj(Object p){return BootstrapOrdersConformance.obj(p);}
 public static void main(String[] a)throws Exception {
  Path root=Path.of(a[0]),report=Path.of(a[1]);Files.createDirectories(report);
  var selection=obj(WireData.json(Files.readString(root.resolve("PACKAGES.json"))));
  Path archive=root.resolve("clause-reseller/dist/package.bluepkg");var reseller=BluePackage.open(archive);
  String sha="sha256:"+HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(archive)));
  obj(selection.get("mounts")).put("Reseller",m("path","clause-reseller/dist/package.bluepkg","blueId",reseller.blueId(),"archiveSha256",sha));
  Path selected=report.resolve("selection.json");Files.writeString(selected,WireData.write(selection));
  var packages=CompositionPackages.published(root,selected);
  var fixture=obj(WireData.json(Files.readString(root.resolve("clause-reseller/tests/fixtures/01-cruise/catalogue.json"))));
  try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
   var p=runtime.processor(packages.language());
   var source=BootstrapOrdersConformance.source(fixture,true,a.length>2 && (a[2].equals("inactive") || a[2].equals("same-seller"))?List.of("seller"):List.of());
   if(a.length>2 && a[2].equals("collision"))obj(obj(source.get("orderTemplate")).get("clauses")).put("customerBinding",m("type","Connections/Connected Clause"));
   var d=BootstrapOrdersConformance.applied(p.initialize(source));
   d=BootstrapOrdersConformance.applied(p.process(d.document(),BootstrapOrdersConformance.event(d.document(),"createQuote",obj(fixture.get("quote")).get("intent")),1));
   var request=m("key","deferred","requestId","deferred","quoteKey","family-quote","groups",fixture.get("groups"));
   var input=BootstrapOrdersConformance.event(d.document(),"newOrder",request);
   var result=p.process(d.document(),input,2);if(a.length>2 && a[2].equals("collision")){BootstrapOrdersConformance.require(!result.commits(),"Existing customerBinding clause must not be overwritten");System.out.println("PASS customerBinding collision rejected");return;}if(!result.commits())ClauseGasProbe.diagnose(p,d.document(),input,2);
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
   parties.forEach((role,raw)->{var party=obj(raw);party.put("myosAccountId",role.equals("customer")?(a.length>2 && a[2].equals("same-seller")?"seller-account":"resolved-customer"):role+"-account");party.put("readerKeys",List.of(role+"-reader"));party.put("lead",m("channel",BootstrapOrdersConformance.channel(role)));obj(party.getOrDefault("representatives",m())).forEach((key,value)->{if(!key.equals("type"))obj(value).put("channel",BootstrapOrdersConformance.channel(role+"-"+key));});});
   var child=p.initialize(prepared);if(a.length>2 && a[2].equals("same-seller")){BootstrapOrdersConformance.require(!child.commits(),"Resolved customer must remain distinct from seller"); System.out.println("PASS deferred seller substitution rejected"); return;}if(!child.commits())ClauseGasProbe.diagnose(p,prepared);BootstrapOrdersConformance.applied(child);
   BootstrapOrdersConformance.equal(p.read(child.document(),"/customerAccountId"),"resolved-customer","Derived customer bound once at ordinary child initialization");
   BootstrapOrdersConformance.equal(p.read(child.document(),"/orderSnapshot/customer/myosAccountId"),"resolved-customer","Fulfilment customer agrees with actual party");
   Files.writeString(report.resolve("initialized-child-component.json"),WireData.write(p.exportSnapshot(child.document())));
   System.out.println("PASS deferred native preparation + exact replay + component child account/fulfilment binding; actual hosted email bootstrap/provide remains separate");
  }
 }
}
