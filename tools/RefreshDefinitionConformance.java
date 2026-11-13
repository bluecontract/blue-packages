import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Complete custom refresh libraries survive the canonical-only gas optimization. */
public final class RefreshDefinitionConformance {
  static Map<String,Object> m(Object... pairs) { return BootstrapPreparationConformance.m(pairs); }
  static Map<String,Object> o(Object value) { return BootstrapPreparationConformance.obj(value); }
  static void check(boolean value,String message) { if(!value)throw new AssertionError(message); }
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);
    var bundle=PackageBundle.builder();
    for(String[] mount:List.of(new String[]{"Contracts","blue-contracts"},new String[]{"Clauses","blue-clauses"},new String[]{"Connections","clause-connections"},new String[]{"Activation","clause-activation"},new String[]{"Parties","blue-parties"},new String[]{"Documents","clause-documents"},new String[]{"Orders","blue-orders"},new String[]{"Agreements","blue-agreements"},new String[]{"Reseller","clause-reseller"}))
      bundle.mount(mount[0],BluePackage.open(root.resolve(mount[1]+"/dist/package.bluepkg")));
    var documents=BluePackage.open(root.resolve("clause-documents/dist/package.bluepkg"));
    for(String variant:List.of("canonical","custom-helper","custom-constants","reseller")) {
      try(var blue=Blue.builder().packages(bundle.build()).build();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
        var processor=runtime.processor(blue);var v=processor.execution().values();
        var source=BootstrapPreparationConformance.source("bootstrap");
        var definition=new Exact.Ref(documents.exportId("Document Preparation Functions"));
        if(variant.equals("reseller")) {
          source=o(WireData.json(WireData.write(source).replace("merchant","partner")));
          o(o(source.get("clauses")).get("orders")).put("type","Reseller/Customer Orders Bootstrap Clause");
        }
        else if(!variant.equals("canonical")) {
          var custom=m("type","Documents/Document Preparation Functions","constants",m("customConstant",42));
          if(variant.equals("custom-helper")) {
            var body=o(v.bexData(v.select(definition,"/functions/sharedRefresh")));
            var steps=new ArrayList<Object>((List<?>)body.get("do"));
            steps.add(m("$let",m("name","customProbe","expr",m("$call",m("function","customHelper","args",m())))));
            body.put("do",steps);
            custom.put("functions",m("sharedRefresh",body,"customHelper",m("args",m(),"do",List.of(m("$return",42)))));
          }
          o(o(source.get("clauses")).get("orders")).put("type",m("type","Documents/Documents Clause","actionDefinition",m("type",custom)));
        }
        var initialized=processor.initialize(source);
        check(initialized.commits(),variant+" initialization failed: "+initialized.observations());
        var document=new Exact.Ref(initialized.document().blueId());
        var original=v.select(document,"/clauses/orders/type/actionDefinition/type");
        Set<String> expected=o(v.bexData(v.select(new Exact.Ref(documents.exportId("Preparation Plan")),"/constants/refreshCanonicalFunctions"))).keySet();
        for(String handler:List.of("refreshProcesses_orders","refreshEmbeddedProcesses_orders","refreshActivationProcesses_orders")) {
          String step="/contracts/"+handler+"/steps/0";
          var selected=v.select(document,step+"/definition");
          if(variant.equals("custom-helper"))check(NativeRuntime.identity(v.exact(original)).equals(NativeRuntime.identity(v.exact(selected))),"Custom definition truncated: "+handler);
          else check(o(v.bexData(v.select(document,step+"/definition/functions"))).keySet().equals(expected),"Canonical closure differs: "+handler);
          if(variant.startsWith("custom-"))check(o(v.bexData(v.select(document,step+"/definition/constants"))).get("customConstant").toString().equals("42"),"Custom constant lost");
          check(o(v.bexData(v.select(document,step+"/functions"))).keySet().containsAll(Set.of("connectionConfiguration","connectionSnapshots")),"Step overrides lost");
        }
        if(variant.equals("reseller")) {
          System.out.println("PASS actual Reseller bootstrap initialization with shared guarded refresh planner");
          continue;
        }
        var approved=BootstrapPreparationConformance.applied(processor.process(initialized.document(),BootstrapPreparationConformance.event(initialized.document(),"approve_merchant",m("revision",1)),1));
        var prepared=processor.process(approved.document(),BootstrapPreparationConformance.event(approved.document(),"prepareOrder",m("type","Documents/Preparation Input","key","one","values",m("size",42))),2);
        check(prepared.commits(),variant+" prepare failed: "+prepared.observations());
        System.out.println("PASS "+variant+" refresh closure/constants/overrides and prepare gas="+prepared.observations().get("gas"));
      }
    }
  }
}
