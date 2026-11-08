import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native refresh cost and exact-definition fallback for custom document clauses. */
public final class DocumentsRefreshConformance {
  static Map<String,Object> m(Object... pairs){return BootstrapPreparationConformance.m(pairs);}
  static Map<String,Object> obj(Object value){return BootstrapPreparationConformance.obj(value);}
  static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
  static final Set<String> CLOSURE=Set.of("sharedRefresh","processStatePath","checkedDomainNextActions","domainNextActions","namedSourcesReady","processOrigin","rosterCovers");
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]);var bundle=PackageBundle.builder();
    var documents=BluePackage.open(root.resolve("clause-documents/dist/package.bluepkg"));
    for(String[] mount:List.of(new String[]{"Contracts","blue-contracts"},new String[]{"Clauses","blue-clauses"},new String[]{"Connections","clause-connections"},new String[]{"Activation","clause-activation"},new String[]{"Parties","blue-parties"},new String[]{"Documents","clause-documents"},new String[]{"Orders","blue-orders"},new String[]{"Agreements","blue-agreements"}))
      bundle.mount(mount[0],BluePackage.open(root.resolve(mount[1]+"/dist/package.bluepkg")));
    for(String variant:List.of("canonical","override-entry","override-helper","override-anchor","missing-anchor")) {
      try(var blue=Blue.builder().packages(bundle.build()).build();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
        var p=runtime.processor(blue);var values=p.execution().values();var source=BootstrapPreparationConformance.source(null);
        var clauses=obj(source.get("clauses"));var orders=obj(clauses.get("orders"));
        if(variant.startsWith("override")) {
          String function=variant.equals("override-entry")?"sharedRefresh":"processStatePath";
          var body=obj(values.literal(values.exact(values.select(new Exact.Ref(documents.exportId("Document Preparation Functions")),"/functions/"+function))));
          var statements=new ArrayList<Object>((List<?>)body.get("do"));
          statements.add(m("$let",m("name","customProbe","expr",m("$call",m("function","customHelper","args",m())))));body.put("do",statements);
          var custom=m("type","Documents/Document Preparation Functions","functions",m(function,body,"customHelper",m("args",m(),"do",List.of(m("$return",0)))));
          var clause=m("type","Documents/Documents Clause","actionDefinition",m("type",custom));
          if(variant.equals("override-anchor"))clause.put("hookDefinition",m("type",m("type","Documents/Preparation Plan","constants",m("refreshCanonicalDefinition",m("type",custom)))));
          orders.put("type",clause);
        }
        if(variant.equals("missing-anchor")) {
          var base=obj(WireData.parse(Files.readString(root.resolve("clause-documents/types/base.blue")),"yaml"));
          var own=obj(values.bexData(new Exact.Ref(documents.exportId("Documents Clause"))));
          for(var entry:own.entrySet()) {
            if(base.get(entry.getKey()) instanceof Map && entry.getValue() instanceof Map)obj(base.get(entry.getKey())).putAll(obj(entry.getValue()));
            else base.put(entry.getKey(),entry.getValue());
          }
          base.put("type","Clauses/Clause");
          base.put("hookDefinition",m("type",m("type","Connections/Connection Planning Functions","constants",m(),"functions",values.bexData(values.select(new Exact.Ref(documents.exportId("Preparation Plan")),"/functions")))));
          orders.put("type",base);
        }
        clauses.put("payouts",m("type","Documents/Documents Clause","parameters",orders.get("parameters"),"bindings",m("parties",m("seller","merchant"),"collection","/payouts")));
        int count=variant.equals("canonical")?4:1;
        var body=new ArrayList<Object>();body.add(m("$appendChange",m("op","add","path","/emitted","val",count)));
        for(int i=0;i<count;i++)body.add(m("$appendEvent",m("kind","Child changed","index",i)));
        source.put("orders",m("one",m("name","Child event source","emitted",0,"contracts",m(
            "input",m("type","Contracts/External Channel","event",m("source","child")),
            "emit",m("type","Contracts/Sequential Workflow","channel","input","steps",List.of(m("type","Contracts/Compute","do",body)))))));
        var initialized=BootstrapPreparationConformance.applied(p.initialize(source));
        var document=new Exact.Ref(initialized.document().blueId());
        var original=values.select(document,"/clauses/orders/type/actionDefinition/type");
        for(String handler:List.of("refreshProcesses_orders","refreshEmbeddedProcesses_orders")) {
          String path="/contracts/"+handler+"/steps/0/definition";var selected=values.select(document,path);
          if(variant.equals("canonical")) {
            check(obj(values.bexData(values.select(document,path+"/functions"))).keySet().equals(CLOSURE),"Incomplete refresh closure");
            for(String function:CLOSURE)check(NativeRuntime.identity(values.exact(values.select(document,path+"/functions/"+function))).equals(NativeRuntime.identity(values.exact(values.select(document,"/clauses/orders/type/actionDefinition/type/functions/"+function)))),"Function body changed: "+function);
          } else check(NativeRuntime.identity(values.exact(selected)).equals(NativeRuntime.identity(values.exact(original))),"Custom definition was truncated: "+variant);
        }
        var active=BootstrapPreparationConformance.applied(p.process(initialized.document(),BootstrapPreparationConformance.event(initialized.document(),"approve_merchant",m("revision",1)),1));
        var result=p.process(active.document(),m("source","child"),2);
        System.out.println("refresh "+variant+" events="+count+" status="+result.status()+" gas="+result.observations().get("gas")+" initGas="+initialized.observations().get("gas"));
        if(!result.commits()) {
          System.out.println("diagnostic="+p.execution().outcome(result).diagnostic);
          var library=obj(values.bexData(values.select(document,"/contracts/refreshEmbeddedProcesses_orders/steps/0/definition")));
          p.execution().evaluator().compile(m("do",List.of(m("$call",m("function","sharedRefresh","args",m())))),library,null);
        }
        check(result.commits(),"Refresh failed: "+result.status());
        check(String.valueOf(count).equals(String.valueOf(p.read(result.document(),"/orders/one/emitted"))),"Child change must commit");
        check(obj(p.read(result.document(),"/process_orders/entries")).isEmpty(),"Refresh must not invent an order preparation");
        check(obj(p.read(result.document(),"/process_payouts/entries")).isEmpty(),"Refresh must not invent a payout");
      }
    }
  }
}
