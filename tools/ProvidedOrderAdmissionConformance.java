import blue.contracts.*;
import blue.bex.Values;
import blue.language.next.*;
import blue.core.CompositionPackages;
import blue.coordination.AuthoringRuntime;
import java.nio.file.*;
import java.util.*;

/** Small native characterization; modeled inputs are not hosted history or approval evidence. */
public final class ProvidedOrderAdmissionConformance {
  static Map<String,Object> m(Object... entries) {
    var out=new LinkedHashMap<String,Object>();
    for(int i=0;i<entries.length;i+=2)out.put((String)entries[i],entries[i+1]);
    return out;
  }
  @SuppressWarnings("unchecked") static Map<String,Object> o(Object value) { return (Map<String,Object>)value; }
  static void check(boolean ok,String message) { if(!ok)throw new AssertionError(message); }
  static Object binding(String path) { return m("$binding","targetDocument"+path); }
  static Object identity(Object value) { return m("$nodeBlueId",value); }
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
  static void patch(ContractsExecution.Values values,Exact original,Map<String,Object> target,String path,Object value) {
    String[] parts=path.substring(1).split("/");Map<String,Object> current=target;String prefix="";
    for(int i=0;i<parts.length-1;i++) {
      String key=parts[i];prefix+="/"+key;Object child=current.get(key);
      if(child==null||child instanceof Map<?,?> map&&map.keySet().equals(Set.of("blueId"))) {
        child=Values.copy(values.literal(values.exact(values.select(original,prefix))));current.put(key,child);
      }
      current=o(child);
    }
    current.put(parts[parts.length-1],value);
  }
  // Retained records are explicit external test inputs, never embedded production fixtures.
  static NodeProviderResult recorded(Map<String,Object> records,String id) {
    if(records.containsKey(id))return NodeProviderResult.found(ContentRecord.fromResponse(o(records.get(id))));
    if(id.contains("#")) {
      String prefix=id.substring(0,id.indexOf('#')+1);
      for(var entry:records.entrySet())if(entry.getKey().startsWith(prefix)&&o(entry.getValue()).containsKey("proof"))
        return NodeProviderResult.found(ContentRecord.fromResponse(m("proof",o(entry.getValue()).get("proof"))));
    }
    System.err.println("Missing retained record "+id);
    return NodeProviderResult.notFound();
  }
  static void calls(Object value,Set<String> result) {
    if(value instanceof Map<?,?> map) {
      if(map.containsKey("$literal"))return;
      if(map.get("$call") instanceof Map<?,?> call)result.add((String)call.get("function"));
      for(Object child:map.values())calls(child,result);
    } else if(value instanceof List<?> list)for(Object child:list)calls(child,result);
  }
  static void retainedProof(Path root,String[] args)throws Exception {
    var capture=o(WireData.json(Files.readString(Path.of(args[1]))));var records=new LinkedHashMap<String,Object>(o(capture.get("responses")));String parentPublication=null;
    boolean aclOnly=Arrays.asList(args).contains("--acl-only");
    for(int i=2;i<args.length;i++) {
      if(args[i].equals("--acl-only")||args[i].equals("--anchor-only"))continue;
      var supplement=o(WireData.json(Files.readString(Path.of(args[i]))));
      if(supplement.get("responses") instanceof Map<?,?>){o(supplement.get("responses")).forEach(records::putIfAbsent);if(supplement.get("publication") instanceof String id)parentPublication=id;continue;}
      check(Boolean.TRUE.equals(supplement.get("verified")),"Supplement requires recorded native identity verification");
      String id=(String)supplement.get("blueId");Object prior=records.putIfAbsent(id,supplement.get("response"));
      check(prior==null||prior.equals(supplement.get("response")),"Conflicting retained evidence");
    }
    var imports=new LinkedHashMap<String,BluePackage>();var bundle=PackageBundle.builder();
    for(var entry:o(o(WireData.json(Files.readString(root.resolve("PACKAGES.json")))).get("mounts")).entrySet()) {
      var pkg=BluePackage.open(root.resolve((String)o(entry.getValue()).get("path")));imports.put(entry.getKey(),pkg);bundle.mount(entry.getKey(),pkg);
    }
    var source=o(WireData.parse(Files.readString(root.resolve("clause-documents/types/preparation-functions.blue")),"yaml"));
    var shared=o(WireData.parse(Files.readString(root.resolve("clause-documents/types/admission-plan-function.blue")),"yaml"));
    var prepared=OperationInputs.publish("Documents",m("Admission Plan Function",shared,"Provided Proof",source),imports);
    prepared.put("Bootstrap Functions",o(WireData.parse(Files.readString(root.resolve("clause-documents/types/bootstrap-functions.blue")),"yaml")).get("functions"));
    try(var blue=Blue.builder().packages(bundle.build()).nodeProvider(id->recorded(records,id)).build()) {
      var ex=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution();var v=ex.values();v.source(prepared.get("Admission Plan Function"));
      var published=new Exact.Ref(imports.get("Documents").exportId("Document Preparation Functions"));
      var functions=o(v.bexData(v.select(published,"/functions")));functions.putAll(o(o(prepared.get("Provided Proof")).get("functions")));
      var selected=m();var pending=new LinkedHashSet<String>();pending.add("providedAdmissionProof");
      while(!pending.isEmpty()) {
        String key=pending.iterator().next();pending.remove(key);if(selected.containsKey(key))continue;
        Object fn=functions.get(key);check(fn!=null,"Missing function "+key);
        if(o(fn).get("blueId") instanceof String id)fn=v.bexData(new Exact.Ref(id));selected.put(key,fn);calls(fn,pending);
      }
      var publication=new Exact.Ref((String)capture.get("publication"));
      if(Arrays.asList(args).contains("--anchor-only")) {
        canonicalAnchor(ex,v,publication,functions);
        return;
      }
      var expression=m("functions",selected,"constants",m("clauseKey","orders"),"expr",m("$call",m("function","providedAdmissionProof","args",m("original",m("$document","/contracts/initialized/document"),"candidate",m("$document","/")))));
      var result=ex.evaluatePredicate(publication,publication,"input",v.source(expression),10000000);
      check(result.events().isEmpty()&&result.changeset().isEmpty(),"Admission proof must have no effects");
      check(o(o(result.value()).get("parties")).keySet().equals(Set.of("guarantor")),"Exact added cohort");
      check(((List<?>)o(result.value()).get("paths")).size()==2,"Exact added access records");
      System.out.println("Retained native admission proof PASS gas="+result.gasUsed());
      var noExtra=o(Values.copy(expression));
      o(o(o(noExtra.get("expr")).get("$call")).get("args")).put("candidate",m("activation",m("parties",m("$document","/contracts/initialized/document/clauses/activation/parameters/parties"))));
      var unchanged=ex.evaluatePredicate(publication,publication,"input",v.source(noExtra),10000000);
      check(o(o(unchanged.value()).get("parties")).isEmpty()&&((List<?>)o(unchanged.value()).get("paths")).isEmpty(),"No-extension path must require no admission witness");
      check(unchanged.events().isEmpty()&&unchanged.changeset().isEmpty(),"No-extension effects");
      System.out.println("Modeled no-extension path PASS gas="+unchanged.gasUsed());
      if(parentPublication!=null)fullProvision(ex,v,new Exact.Ref(parentPublication),publication,prepared);
      String entryKey=o(v.literal(v.exact(v.select(publication,"/process_payment/entries")))).keySet().iterator().next();
      String entry="/process_payment/entries/"+entryKey;
      String ref=(String)v.bexData(v.select(publication,entry+"/admissionRef"));
      var mutations=new LinkedHashMap<String,Object>();
      mutations.put("/activation/revision",3);mutations.put("/clauseRuntime/revision",2);
      mutations.put("/activation/terms/ref","foreign");mutations.put("/activation/terms/fields",m("changed",true));
      mutations.put("/activation/required",List.of());
      mutations.put("/activation/parties/rogue",v.literal(v.exact(v.select(publication,"/activation/parties/guarantor"))));
      mutations.put("/activation/parties/guarantor/myosAccountId","foreign");
      mutations.put(entry+"/consents/guarantor",false);mutations.put(entry+"/admittedRevision",3);
      mutations.put(entry+"/admittedTerms/previousRef","foreign");mutations.put(entry+"/admissionRef","foreign");
      mutations.put("/process_payment/admission/ledger/history/"+ref,false);
      mutations.put("/process_payment/admission/grants/"+ref,m());
      mutations.put("/clauseRuntime/initialDocument",m("foreign",true));
      mutations.put("/activation/parties/seller/myosAccountId","foreign");
      mutations.put("/contracts/admissionUpdate_payment_processHandler",m("forged",true));
      String consentOperation=o(v.literal(v.exact(v.select(publication,"/activation/admissionConsentOperations")))).keySet().iterator().next();
      mutations.put("/contracts/"+consentOperation,m("forged",true));
      mutations.put("/activation/admissionConsentOperations/"+consentOperation+"/operationId","foreign");
      var accessOrigins=new ArrayList<String>(o(v.literal(v.exact(v.select(publication,"/partyAccess")))).keySet());check(accessOrigins.size()==2,"Exact retained access pair");
      String accessOrigin=accessOrigins.get(0);
      mutations.put("/partyAccess/"+accessOrigin,v.literal(v.exact(v.select(publication,"/partyAccess/"+accessOrigins.get(1)))));
      var derivativeExpression=o(Values.copy(expression));
      o(o(o(derivativeExpression.get("expr")).get("$call")).get("args")).put("candidate",m("$binding","input"));
      Object proofCall=derivativeExpression.remove("expr");derivativeExpression.put("do",List.of(proofCall,m("$return",true)));
      var compiled=v.source(derivativeExpression);
      for(var mutation:mutations.entrySet()) {
        if(aclOnly&&!mutation.getKey().startsWith("/partyAccess/"))continue;
        var baseline=o(Values.copy(v.literal(publication)));
        var control=ex.evaluatePredicate(publication,v.source(baseline),"input",compiled,10000000);
        check(Boolean.TRUE.equals(control.value()),"Unmodified derivative control");
        check(control.events().isEmpty()&&control.changeset().isEmpty(),"Control effects");
        patch(v,publication,baseline,mutation.getKey(),mutation.getValue());
        boolean denied=false;
        try {ex.evaluatePredicate(publication,v.source(baseline),"input",compiled,10000000);}
        catch(blue.bex.BexError failure) {if(!failure.getMessage().contains("PREPARATION_ADMISSION_PROOF_REQUIRED"))throw failure;denied=true;}
        check(denied,"Accepted modified admission proof "+mutation.getKey());
        System.out.println("Retained derivative rejected "+mutation.getKey());
      }

    }
  }
  // Coherent override of both the purported canonical library and action implementation.
  // The unchanged original hook type alone must not authorize this modeled custom library.
  static void canonicalAnchor(ContractsExecution ex,ContractsExecution.Values v,Exact candidate,Map<String,Object> functions) {
    String path="/contracts/initialized/document/clauses/payment";
    Exact original=v.exact(v.select(candidate,path));
    var baseline=o(Values.copy(v.literal(original)));
    System.out.println("Anchor canonical="+NativeRuntime.identity(v.exact(v.select(original,"/hookDefinition/constants/admissionCanonicalDefinition")))+" type="+NativeRuntime.identity(v.exact(v.select(original,"/hookDefinition/constants/admissionCanonicalDefinition/type")))+" trusted="+NativeRuntime.identity(v.source(m("type","Documents/Admission Functions"))));
    String name="nextAdmissionRequest";
    var expression=m("functions",m("assembleAdmissionDefinition",functions.get("assembleAdmissionDefinition")),"do",List.of(
      m("$call",m("function","assembleAdmissionDefinition","args",m("clauses",m("payment",m("$binding","input")),"clauseKey","payment","definition",m(),"names",List.of(name),"definitionPath","unused","canonicalPath","unused"))),m("$return",true)));
    var compiled=v.source(expression);
    var control=ex.evaluatePredicate(candidate,v.source(baseline),"input",compiled,10000000);
    check(Boolean.TRUE.equals(control.value())&&control.events().isEmpty()&&control.changeset().isEmpty(),"Canonical anchor baseline");
    Object forged=m("args",m(),"expr",true);
    patch(v,original,baseline,"/hookDefinition/constants/admissionCanonicalDefinition/functions/"+name,forged);
    patch(v,original,baseline,"/actionDefinition/functions/"+name,forged);
    check(NativeRuntime.identity(v.exact(v.select(v.source(baseline),"/hookDefinition/type"))).equals(NativeRuntime.identity(v.exact(v.select(original,"/hookDefinition/type")))),"Original canonical hook type preserved");
    boolean denied=false;
    try {ex.evaluatePredicate(candidate,v.source(baseline),"input",compiled,10000000);}
    catch(blue.bex.BexError failure) {if(!failure.getMessage().contains("PREPARATION_ADMISSION_PROOF_REQUIRED"))throw failure;denied=true;}
    check(denied,"Coherent canonical/action override must be rejected");
    System.out.println("Canonical library anchor PASS original control and coherent override denial; gas limit=10000000");
  }
  static void fullProvision(ContractsExecution ex,ContractsExecution.Values v,Exact host,Exact candidate,Map<String,Object> prepared) {
    String step="/contracts/provideOrder/steps/0";
    var functions=o(v.bexData(v.select(host,step+"/definition/functions")));Object overrides=v.select(host,step+"/functions");
    if(overrides!=null)functions.putAll(o(v.bexData(overrides)));
    for(var entry:o(o(prepared.get("Provided Proof")).get("functions")).entrySet())
      if(entry.getKey().startsWith("provided")||entry.getKey().startsWith("assembleAdmission")||entry.getKey().equals("validateProviderSlotsWithAdmission")||entry.getKey().equals("checkProvision"))functions.put(entry.getKey(),entry.getValue());
    functions.put("validateBootstrapAccessWithAdmission",o(prepared.get("Bootstrap Functions")).get("validateBootstrapAccessWithAdmission"));
    var selected=m();var pending=new LinkedHashSet<String>();pending.add("checkProvision");
    while(!pending.isEmpty()) {
      String key=pending.iterator().next();pending.remove(key);if(selected.containsKey(key))continue;
      Object fn=functions.get(key);check(fn!=null,"Missing full provision function "+key);
      if(o(fn).get("blueId") instanceof String id)fn=v.bexData(new Exact.Ref(id));selected.put(key,fn);calls(fn,pending);
    }
    var entries=o(v.literal(v.exact(v.select(host,"/process_orders/entries"))));check(entries.size()==1,"Expected one retained parent entry");
    String item="/process_orders/entries/"+entries.keySet().iterator().next();
    var request=m("key",v.bexData(v.select(host,item+"/key")),"inResponseTo",v.bexData(v.select(host,item+"/requestId")),"requirementRef",v.bexData(v.select(host,item+"/requirementRef")),"document",m("blueId",NativeRuntime.identity(candidate)));
    var input=v.source(m("channel",v.bexData(v.select(host,item+"/supplier")),"request",request));
    var call=m("$call",m("function","checkProvision","args",m("input",m("$binding","call/request"))));
    var expression=m("functions",selected,"constants",v.bexData(v.select(host,step+"/constants")),"do",List.of(m("$let",m("name","checked","expr",call)),m("$return",m("outcome",m("$var",m("name","checked","path","/outcome")),"status",m("$var",m("name","checked","path","/staged/status"))))));
    var result=ex.evaluatePredicate(host,input,"call",v.source(expression),10000000);
    check(result.events().isEmpty()&&result.changeset().isEmpty(),"Full checkProvision effects");
    check("acceptedNew".equals(o(result.value()).get("outcome")),"Expected accepted new provision");
    check("ready".equals(o(result.value()).get("status")),"Expected ready candidate after legitimate admission");
    System.out.println("Full native checkProvision PASS ready; modeled matching request gas="+result.gasUsed());
  }
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]).toAbsolutePath().normalize();
    if(args.length>1){retainedProof(root,args);return;}
    plannerParity(root);
    var authored=o(WireData.parse(Files.readString(root.resolve("clause-activation/types/functions.blue")),"yaml"));
    var initialize=o(o(authored.get("functions")).get("initializeTerms"));
    try(var blue=Blue.builder().build()) {
      var ex=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution();
      var v=ex.values();
      var original=m("name","Prepared child","amountMinor",10000,"timelineAccess",m("seller",m("readers",List.of("key"))),
          "clauses",m("activation",m("parameters",m("parties",m("seller",m("myosAccountId","seller","readerKeys",List.of("key"))),
              "required",List.of("seller"),"accessPaths",List.of("/timelineAccess/seller"),"readers",m()))));
      var originalExact=v.source(original);
      var context=m("clauseRuntime",m("initialDocument",v.literal(originalExact)),"clauses",original.get("clauses"),
          "activation",m("accessPaths",List.of("/timelineAccess/seller")));
      var doc=v.source(context);
      var initial=ex.evaluatePredicate(doc,doc,"targetDocument",v.source(initialize),10000000);
      check(initial.events().isEmpty()&&initial.changeset().isEmpty(),"initial terms must be read-only");
      var terms=o(o(initial.value()).get("terms"));
      var expectedDefinition=m("name","Prepared child","amountMinor",10000,"timelineAccess",m(),
          "clauses",m("activation",m("parameters",m("parties",m("seller",m("myosAccountId","seller")),"required",List.of("seller")))));
      var definition=ex.evaluatePredicate(doc,v.source(expectedDefinition),"targetDocument",v.source(m("expr",identity(binding("")))),10000000);
      check(Objects.equals(definition.value(),terms.get("definition")),"reuse exact initial terms normalization");
      var cohort=m("previous",terms.get("definition"),"parties",m("seller",m("myosAccountId","seller"),"newParticipant",m("myosAccountId","new")),"required",List.of("seller"));
      var transform=m("expr",identity(m("definition",identity(binding("")),"fields",m("$literal",m()))));
      var admitted=ex.evaluatePredicate(doc,v.source(cohort),"targetDocument",v.source(transform),10000000);
      for(String field:List.of("previous","parties","required")) {
        var changed=new LinkedHashMap<>(cohort);
        changed.put(field,field.equals("previous")?"foreign":field.equals("parties")?m("rogue",m("myosAccountId","rogue")):List.of());
        var result=ex.evaluatePredicate(doc,v.source(changed),"targetDocument",v.source(transform),10000000);
        check(!Objects.equals(result.value(),admitted.value()),"terms must bind "+field);
        check(result.events().isEmpty()&&result.changeset().isEmpty(),"no effects");
      }
      System.out.println("Initial normalization and single admission terms identity PASS; modeled read-only cases only");
    }
  }
}
