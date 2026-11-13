import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Actual planner initialization preserves native function bodies and subtype behavior. */
public final class AdmissionDefinitionConformance {
  static Map<String,Object> m(Object... pairs){return BootstrapPreparationConformance.m(pairs);}
  static Map<String,Object> obj(Object value){return BootstrapPreparationConformance.obj(value);}
  static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
  static final List<List<String>> CLOSURES=List.of(
      List.of("nextAdmissionRequest","retireInvalidAdmission","retireAdmission"),
      List.of("admissionInstallRequest","installAdmissionConsentOperations","admissionConsentNames","admissionConsentHandler","admissionConsentRegistration","accessValid","accessRecordsValid","readerGroups","transports"),
      List.of("finishAdmission","requireRosterCoverage","requireSameMainParty"));
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]);var documents=BluePackage.open(root.resolve("clause-documents/dist/package.bluepkg"));
    var bundle=PackageBundle.builder();
    for(String[] mount:List.of(new String[]{"Contracts","blue-contracts"},new String[]{"Clauses","blue-clauses"},new String[]{"Connections","clause-connections"},new String[]{"Activation","clause-activation"},new String[]{"Parties","blue-parties"},new String[]{"Documents","clause-documents"},new String[]{"Orders","blue-orders"},new String[]{"Agreements","blue-agreements"}))
      bundle.mount(mount[0],BluePackage.open(root.resolve(mount[1]+"/dist/package.bluepkg")));
    for(String variant:List.of("canonical","override-entry","override-helper","override-anchor","missing-anchor","override-constants")) {
      if(args.length>1&&!args[1].equals(variant))continue;
      try(var blue=Blue.builder().packages(bundle.build()).build();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
        var processor=runtime.processor(blue);var values=processor.execution().values();
        var source=BootstrapPreparationConformance.source("bootstrap");var clauses=obj(source.get("clauses"));
        obj(obj(clauses.get("activation")).get("parameters")).put("admission",m("approvers",List.of("merchant")));
        if(!variant.equals("canonical") && !variant.equals("missing-anchor") && !variant.equals("override-constants")) {
          var overrides=new LinkedHashMap<String,Object>();
          for(var names:CLOSURES) {
            String name=variant.equals("override-entry")?names.getFirst():names.getLast();
            var body=obj(values.literal(values.exact(values.select(new Exact.Ref(documents.exportId("Document Preparation Functions")),"/functions/"+name))));
            var steps=new ArrayList<Object>((List<?>)body.get("do"));
            steps.add(m("$let",m("name","customProbe","expr",m("$call",m("function","customHelper","args",m())))));body.put("do",steps);overrides.put(name,body);
          }
          overrides.put("customHelper",m("args",m(),"do",List.of(m("$return",0))));
          var custom=m("type","Documents/Document Preparation Functions","functions",overrides);
          var clauseType=m("type","Documents/Documents Clause","actionDefinition",m("type",custom));
          if(variant.equals("override-anchor"))clauseType.put("hookDefinition",m("type",m("type","Documents/Preparation Plan","constants",m("admissionCanonicalDefinition",m("type",custom)))));
          obj(clauses.get("orders")).put("type",clauseType);
        }
        if(variant.equals("override-constants")) {
          var custom=m("type","Documents/Document Preparation Functions","constants",m("conformance",42));
          obj(clauses.get("orders")).put("type",m("type","Documents/Documents Clause","actionDefinition",m("type",custom)));
        }
        if(variant.equals("missing-anchor")) {
          var clauseType=obj(WireData.json(WireData.write(WireData.parse(Files.readString(root.resolve("clause-documents/types/base.blue")),"yaml"))));
          var own=obj(values.bexData(new Exact.Ref(documents.exportId("Documents Clause"))));
          for(var entry:own.entrySet()) {
            if(clauseType.get(entry.getKey()) instanceof Map && entry.getValue() instanceof Map) obj(clauseType.get(entry.getKey())).putAll(obj(entry.getValue()));
            else clauseType.put(entry.getKey(),entry.getValue());
          }
          clauseType.put("type","Clauses/Clause");
          var planner=new Exact.Ref(documents.exportId("Preparation Plan"));
          var hook=m("type","Connections/Connection Planning Functions","constants",m("refreshCanonicalFunctions",values.bexData(values.select(planner,"/constants/refreshCanonicalFunctions"))),"functions",values.bexData(values.select(planner,"/functions")));
          clauseType.put("hookDefinition",m("type",hook));
          obj(clauses.get("orders")).put("type",clauseType);
        }
        Contracts.Result initialized;try{initialized=processor.initialize(source);}catch(Failure failure){System.out.println(variant+" "+failure.outcome());throw failure;}
        check(initialized.commits(),variant+" initialization failed");
        var document=new Exact.Ref(initialized.document().blueId());
        String originalPath="/clauses/orders/type/actionDefinition/type";
        var original=values.select(document,originalPath);
        for(int i=0;i<CLOSURES.size();i++) {
          String path="/contracts/admissionUpdate_orders_processHandler/steps/"+List.of(0,2,4).get(i)+"/definition";
          var selected=values.select(document,path);check(selected!=null,"Missing generated definition "+path);
          if(variant.equals("canonical") || variant.equals("override-constants")) {
            if(variant.equals("override-constants"))check(obj(values.bexData(values.select(document,path+"/constants"))).get("conformance").toString().equals("42"),"Custom constants not preserved");
            var functions=obj(values.bexData(values.select(document,path+"/functions")));
            check(functions.keySet().equals(new HashSet<>(CLOSURES.get(i))),"Unexpected closure "+functions.keySet());
            for(String name:CLOSURES.get(i))check(NativeRuntime.identity(values.exact(values.select(document,path+"/functions/"+name))).equals(NativeRuntime.identity(values.exact(values.select(document,originalPath+"/functions/"+name)))),"Function changed "+name);
          } else check(NativeRuntime.identity(values.exact(selected)).equals(NativeRuntime.identity(values.exact(original))),"Custom definition not preserved "+variant);
        }
        if(variant.equals("canonical")) {
          var approved=BootstrapPreparationConformance.applied(processor.process(initialized.document(),BootstrapPreparationConformance.event(initialized.document(),"approve_merchant",m("revision",1)),1));
          var request=m("type","Documents/Preparation Input","key","one","values",m("size",42));
          var prepared=BootstrapPreparationConformance.applied(processor.process(approved.document(),BootstrapPreparationConformance.event(approved.document(),"prepareOrder",request),2));
          var repeated=BootstrapPreparationConformance.applied(processor.process(prepared.document(),BootstrapPreparationConformance.event(prepared.document(),"prepareOrder",request),3));
          check(obj(processor.read(repeated.document(),"/process_orders/entries")).size()==1,"Preparation retry duplicated obligation");
          System.out.println("PASS canonical prepare/retry; gas="+prepared.observations().get("gas"));
        }
        System.out.println("PASS "+variant+" native initialization and three definitions; gas="+initialized.observations().get("gas"));
      }
    }
  }
}
