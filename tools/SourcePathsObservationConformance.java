import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native child planning must observe exact prebound declared source documents. */
public final class SourcePathsObservationConformance {
  static Map<String,Object> m(Object... x){return BootstrapPreparationConformance.m(x);}
  static Map<String,Object> obj(Object x){return BootstrapPreparationConformance.obj(x);}
  static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);var bundle=PackageBundle.builder();
    for(String[] mount:List.of(new String[]{"Contracts","blue-contracts"},new String[]{"Clauses","blue-clauses"},new String[]{"Connections","clause-connections"},new String[]{"Activation","clause-activation"},new String[]{"Parties","blue-parties"},new String[]{"Documents","clause-documents"},new String[]{"Orders","blue-orders"},new String[]{"Agreements","blue-agreements"}))
      bundle.mount(mount[0],BluePackage.open(root.resolve(mount[1]+"/dist/package.bluepkg")));
    try(var blue=Blue.builder().packages(bundle.build()).build();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var p=runtime.processor(blue);var source=BootstrapPreparationConformance.source(null);
      var clauses=obj(source.get("clauses"));
      String mode=args.length>1?args[1]:"freshness";
      String alias=mode.equals("escaped-alias")?"order/tilde~":"order";
      String sourcePointer="/sources/"+alias.replace("~","~0").replace("/","~1");
      boolean admission=Set.of("admission","foreign-source","nonroot","escaped-alias").contains(mode);
      obj(obj(clauses.get("activation")).get("parameters")).put("admission",m("approvers",List.of("merchant")));
      obj(obj(clauses.get("activation")).get("parameters")).put("preActivationOperations",List.of("prepareOrder","provideOrder"));
      var parameters=obj(obj(clauses.get("orders")).get("parameters"));
      parameters.put("sourcePaths",m(alias,""));parameters.put("suppliedParties",List.of());
      var template=obj(parameters.get("template"));template.put("sources",m(alias,m()));
      var activation=obj(obj(obj(template.get("clauses")).get("activation")).get("parameters"));
      obj(activation.get("parties")).remove("customer");activation.put("required",List.of());
      if(admission){
        parameters.put("suppliedParties",List.of("guarantor"));
        obj(activation.get("parties")).put("guarantor",m("type","Parties/Party","myosAccountId","guarantor","readerKeys",List.of("reader-guarantor"),"lead",m("channel",m("type","Contracts/External Channel","event",m("source","guarantor")))));
      }
      if(mode.equals("collision"))obj(template.get("clauses")).put("documentSourceObservation_"+NativeRuntime.identity(p.execution().values().source(alias)),m("type","Activation/Activation Clause"));
      if(mode.equals("undeclared"))template.remove("sources");
      Contracts.Result other=null;
      if(mode.equals("foreign-source")||mode.equals("nonroot")){
        var otherSource=BootstrapPreparationConformance.source(null);otherSource.put("name","Other immutable source");
        other=BootstrapPreparationConformance.applied(p.initialize(otherSource));
        if(mode.equals("nonroot")){source.put("orders",m());source.put("peer",m("blueId",other.document().blueId()));parameters.put("sourcePaths",m("order","/peer"));}
      }
      var host=BootstrapPreparationConformance.applied(p.initialize(source));
      check(!Boolean.TRUE.equals(p.read(host.document(),"/activation/active")),"Host must remain inactive");
      var preparation=p.process(host.document(),BootstrapPreparationConformance.event(host.document(),"prepareOrder",m("type","Documents/Preparation Input","key","one","values",m("size",42))),1);
      if(mode.equals("collision")){check(!preparation.commits(),"Reserved observation clause must reject");check(host.document().identity().equals(preparation.document().identity()),"Collision must not mutate host");System.out.println("PASS collision rejected");return;}
      var prepared=BootstrapPreparationConformance.applied(preparation);
      var item=obj(obj(p.read(prepared.document(),"/process_orders/entries")).values().iterator().next());
      var values=p.execution().values();
      var exact=values.select(new Exact.Ref(prepared.document().blueId()),item.get("itemPath")+"/prepared");
      var childSource=values.literal(values.exact(exact));
      if(mode.equals("foreign-source"))obj(obj(childSource).get("sources")).put("order",m("blueId",other.document().blueId()));
      var childResult=p.initialize(childSource);
      var child=BootstrapPreparationConformance.applied(childResult);
      Object collections=p.read(child.document(),"/contracts/embedded/collectionPaths");
      Object paths=p.read(child.document(),"/contracts/embedded/paths");
      System.out.println("Native host inactive; ordinary preparation and child initialization PASS; embedded paths="+paths+" collections="+collections);
      boolean observed=collections instanceof List<?> list&&list.contains("/sources") || paths instanceof List<?> directPaths&&directPaths.contains(sourcePointer);
      if(mode.equals("undeclared")){check(!observed,"Undeclared legacy path mode remains unchanged");System.out.println("PASS undeclared sourcePaths behavior preserved");return;}
      check(observed,"Declared prebound source has no native live observation edge");
      if(!admission){
        var advanced=BootstrapPreparationConformance.applied(p.process(child.document(),BootstrapPreparationConformance.event(host.document(),"approve_merchant",m("revision",1)),2));
        check(Boolean.TRUE.equals(p.read(advanced.document(),sourcePointer+"/activation/active")),"Same source approval must propagate through the native edge");
        check(Boolean.TRUE.equals(p.read(advanced.document(),sourcePointer+"/activation/approved/merchant")),"Actual source party approved");
        var origin=values.select(new Exact.Ref(advanced.document().blueId()),sourcePointer+"/contracts/initialized/document");
        var originalOrigin=values.select(new Exact.Ref(host.document().blueId()),"/contracts/initialized/document");
        check(NativeRuntime.identity(values.exact(origin)).equals(NativeRuntime.identity(values.exact(originalOrigin))),"Observation must preserve exact source process identity");
        System.out.println("PASS actual same-source seller approval propagated through native embedding");
      }
      if(admission){
        var input=m("type","Documents/Provision Input","key",item.get("key"),"inResponseTo",item.get("requestId"),"requirementRef",item.get("requirementRef"),"document",m("blueId",child.document().blueId()));
        var provision=p.process(prepared.document(),BootstrapPreparationConformance.event(prepared.document(),"provideOrder",input),2);
        if(mode.equals("foreign-source")){check(!provision.commits(),"Foreign source must reject provision");check(prepared.document().identity().equals(provision.document().identity()),"Rejected source must not mutate host");System.out.println("PASS foreign source rejected");return;}
        var provided=BootstrapPreparationConformance.applied(provision);
        var staged=obj(p.read(provided.document(),item.get("itemPath").toString()));
        if(mode.equals("nonroot")){check(!staged.containsKey("admissionRef"),"Nonroot dependency cannot admit parties to host");check(!obj(p.read(provided.document(),"/activation/parties")).containsKey("guarantor"),"No implicit foreign-source admission");System.out.println("PASS nonroot source does not authorize host admission");return;}
        check("admission_pending".equals(staged.get("status")),"Missing guarantor must require admission: "+staged.get("status"));
        check(staged.containsKey("admissionRef"),"Admission token required");
        check(!Boolean.TRUE.equals(p.read(provided.document(),"/activation/active")),"Admission cannot approve host");
        check(obj(p.read(provided.document(),"/activation/approved")).isEmpty(),"No commercial approval");
        System.out.println("PASS declared-source host admission pending; no automatic commercial approval");
      }
    }
  }
}
