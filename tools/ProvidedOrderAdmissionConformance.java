import blue.contracts.*;
import blue.language.next.*;
import blue.core.CompositionPackages;
import blue.coordination.AuthoringRuntime;
import java.nio.file.*;
import java.util.*;

/** Exact-reference and native general-admission planner parity, including custom definitions. */
public final class ProvidedOrderAdmissionConformance {
  static Map<String,Object> m(Object... entries) {
    var out=new LinkedHashMap<String,Object>();
    for(int i=0;i<entries.length;i+=2)out.put((String)entries[i],entries[i+1]);
    return out;
  }
  @SuppressWarnings("unchecked") static Map<String,Object> o(Object value) { return (Map<String,Object>)value; }
  static void check(boolean ok,String message) { if(!ok)throw new AssertionError(message); }
  static void plannerParity(Path root) throws Exception {
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    var authored=o(o(WireData.parse(Files.readString(root.resolve("clause-documents/types/preparation-plan.blue")),"yaml")).get("functions"));
    var shared=o(WireData.parse(Files.readString(root.resolve("clause-documents/types/admission-plan-function.blue")),"yaml"));
    var imports=new LinkedHashMap<String,BluePackage>();
    var config=o(WireData.parse(Files.readString(root.resolve("clause-documents/blue-package.yaml")),"yaml"));
    for(var entry:o(config.get("imports")).entrySet())imports.put(entry.getKey(),BluePackage.open(root.resolve("clause-documents").resolve((String)o(entry.getValue()).get("path")).normalize()));
    var documentPackage=BluePackage.open(root.resolve("clause-documents/dist/package.bluepkg"));
    imports.put("PublishedDocuments",documentPackage);
    shared=o(WireData.json(WireData.write(shared).replace("Documents/Admission Functions","PublishedDocuments/Admission Functions")));
    var consumer=m("functions",m("assembleAdmissionPlan",authored.get("assembleAdmissionPlan")));
    var prepared=OperationInputs.publish("Documents",m("Admission Plan Function",shared,"Reference Consumer",consumer),imports);
    shared=o(prepared.get("Admission Plan Function"));
    var preparedReference=o(o(o(prepared.get("Reference Consumer")).get("functions")).get("assembleAdmissionPlan"));
    try(var language=packages.language()) {
      String expected=language.admitDefinition(WireData.write(shared)).blueId();
      check(preparedReference.equals(m("blueId",expected)),"Prepared reference must match exact current shared source");
    }
    var changedShared=o(WireData.json(WireData.write(shared)));
    var changedSteps=new ArrayList<Object>((List<?>)changedShared.get("do"));changedSteps.add(m("$let",m("name","revisionMarker","expr",true)));changedShared.put("do",changedSteps);
    var changedPrepared=OperationInputs.publish("Documents",m("Admission Plan Function",changedShared,"Reference Consumer",consumer),imports);
    var changedReference=o(o(o(changedPrepared.get("Reference Consumer")).get("functions")).get("assembleAdmissionPlan"));
    try(var language=packages.language()) {
      String currentId=language.admitDefinition(WireData.write(changedPrepared.get("Admission Plan Function"))).blueId();
      check(changedReference.equals(m("blueId",currentId)),"Changed source must receive its new exact function reference");
      check(!preparedReference.equals(changedReference),"Earlier reference must not survive a source change");
    }
    for(Object malformed:List.of(m("$blue:functionFrom",m("type","Documents/Admission Plan Function"),"extra",true),m("$blue:functionFrom",m("type","Parties/Party")))) {
      boolean denied=false;
      try {OperationInputs.publish("Documents",m("Admission Plan Function",shared,"Bad Consumer",m("functions",m("bad",malformed))),imports);}catch(IllegalArgumentException expected){denied=true;}
      check(denied,"Malformed or non-function reference must be rejected");
    }
    System.out.println("Authoring exact-reference preparation and malformed-reference controls PASS");
    for(boolean custom:List.of(false,true)) {
      Map<String,String> baseline=null;
      for(boolean extracted:List.of(false,true))try(var blue=packages.language();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
        var processor=runtime.processor(blue);var v=processor.execution().values();
        var source=BootstrapPreparationConformance.source("bootstrap");var clauses=o(source.get("clauses"));
        o(o(clauses.get("activation")).get("parameters")).put("admission",m("approvers",List.of("merchant")));
        var clauseType=m("type","Documents/Documents Clause");
        if(custom) {
          var definition=v.source(m("type","Documents/Document Preparation Functions"));
          var body=o(v.literal(v.exact(v.select(definition,"/functions/nextAdmissionRequest"))));
          var steps=new ArrayList<Object>((List<?>)body.get("do"));steps.add(m("$let",m("name","customMarker","expr",true)));body.put("do",steps);
          clauseType.put("actionDefinition",m("type",m("type","Documents/Document Preparation Functions","functions",m("nextAdmissionRequest",body))));
        }
        if(extracted) {
          check(preparedReference.equals(m("blueId",NativeRuntime.identity(v.source(shared)))),"Current shared definition must be available under the prepared exact reference");
          var base=o(WireData.parse(Files.readString(root.resolve("clause-documents/types/base.blue")),"yaml"));
          var documents=BluePackage.open(root.resolve("clause-documents/dist/package.bluepkg"));
          var own=o(v.bexData(new Exact.Ref(documents.exportId("Documents Clause"))));
          for(var entry:own.entrySet()) {
            if(base.get(entry.getKey()) instanceof Map && entry.getValue() instanceof Map)o(base.get(entry.getKey())).putAll(o(entry.getValue()));
            else base.put(entry.getKey(),entry.getValue());
          }
          if(custom)base.put("actionDefinition",clauseType.get("actionDefinition"));
          base.put("type","Clauses/Clause");
          var freshFunctions=new LinkedHashMap<String,Object>(o(v.bexData(v.select(new Exact.Ref(documents.exportId("Preparation Plan")),"/functions"))));freshFunctions.put("planAdmission",authored.get("planAdmission"));freshFunctions.put("assembleAdmissionDefinition",authored.get("assembleAdmissionDefinition"));freshFunctions.put("assembleAdmissionPlan",preparedReference);
          var currentConstants=o(v.bexData(v.select(new Exact.Ref(documents.exportId("Preparation Plan")),"/constants")));
          base.put("hookDefinition",m("type",m("type","Connections/Connection Planning Functions","constants",currentConstants,"functions",freshFunctions)));
          clauseType=base;
        }
        o(clauses.get("orders")).put("type",clauseType);
        System.out.println("Planner initializing custom="+custom+" extracted="+extracted);
        var initialized=processor.initialize(source);
        if(!initialized.commits()) {
          var nativeSource=v.source(source);
          var hook=o(v.bexData(v.select(nativeSource,"/clauses/orders/type/hookDefinition/type")));
          o(hook.computeIfAbsent("constants",k->m())).put("clauseKey","orders");
          processor.execution().evaluator().compile(m("do",List.of(m("$return",m("$call",m("function","plan","args",m()))))),hook,"plan");
        }
        check(initialized.commits(),"Planner initialization failed "+initialized.observations());
        var document=new Exact.Ref(initialized.document().blueId());var hashes=new TreeMap<String,String>();
        for(String key:o(v.bexData(v.select(document,"/contracts"))).keySet())if(key.startsWith("admission")||key.startsWith("approveAdmission"))hashes.put(key,NativeRuntime.identity(v.exact(v.select(document,"/contracts/"+key))));
        check(!hashes.isEmpty(),"Admission declarations missing");
        if(!extracted)baseline=hashes;else check(baseline.equals(hashes),"Generated admission declaration identity mismatch custom="+custom);
      }
      System.out.println("Planner native output identity parity PASS custom="+custom);
    }
  }
  public static void main(String[] args) throws Exception {
    plannerParity(Path.of(args[0]).toAbsolutePath().normalize());
  }
}
