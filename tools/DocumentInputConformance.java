import blue.contracts.*;
import blue.bex.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native document/attachment generator and executor qualification. */
public final class DocumentInputConformance {
  static Map<String,Object> m(Object... pairs) {return OperationInputConformance.m(pairs);}
  static void require(boolean value,String message) {OperationInputConformance.require(value,message);}
  @SuppressWarnings("unchecked")
  static Map<String,Object> workOrder(Path root) throws Exception { return workOrder(root,"08-local-work-order.blue",true); }
  @SuppressWarnings("unchecked")
  static Map<String,Object> workOrder(Path root,String file,boolean override) throws Exception {
    var source=(Map<String,Object>)WireData.parse(Files.readString(root.resolve("examples/preparation/"+file)),"yaml");
    var clauses=(Map<String,Object>)source.get("clauses");
    var wire=blue.core.ClauseAppsExamples.class.getDeclaredMethod("wire",Object.class);
    wire.setAccessible(true);wire.invoke(null,source);
    if(!override)return source;
    var instruction=(Map<String,Object>)clauses.get("instruction");
    var bindings=(Map<String,Object>)instruction.get("bindings");
    var begin=(Map<String,Object>)bindings.get("begin");
    ((Map<String,Object>)begin.get("prepareDocument")).put("request",m("auditLabel",m("type","Text")));
    var resume=(Map<String,Object>)bindings.get("resume");
    ((Map<String,Object>)resume.get("resumeDocument")).put("request",m());
    return source;
  }
  static void connectionRequests(Path root)throws Exception {
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var authoring=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var processor=authoring.processor(packages.language());
      var initialized=processor.initialize(workOrder(root));
      require(initialized.status().equals("APPLIED"),"Document preparation initialization: "+initialized.receipt()+" observations="+initialized.observations());
      var execution=processor.execution();
      var declarations=execution.declarations(new Exact.Ref(initialized.document().blueId()));
      var operation=declarations.get("prepareDocument");
      require(operation!=null,"Generated prepareDocument must exist");
      require(operation.containsKey("request"),"Explicit connection.request must be retained by Attachment Preparation Plan");
      var matcher=execution.values().source(operation.get("request"),"definition");
      require(execution.values().matches(execution.values().source(m("auditLabel","reviewed")),matcher),"Explicit connection matcher accepts valid value");
      require(!execution.values().matches(execution.values().source(m()),matcher),"Explicit connection matcher requires its declared field");
      require(declarations.get("resumeDocument").containsKey("request"),"Explicit connection.request:{} must remain present");
      System.out.println("PASS native Attachment generated connection.request and explicit empty matcher");
    }
  }
  @SuppressWarnings("unchecked")
  static void accessLibrary(Path root)throws Exception {
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var definition=values.source(m("type","Attachments/Attachment Access Functions"),"definition");
      var library=m("functions",values.bexData(values.select(definition,"/functions")));
      var bex=new Bex(BexProfile.current());
      bex.compile(m("constants",m("authority","provider","key","attachment"),"do",List.of(m("$return",m("$call",m("function","addAuthority","args",m("input",m())))))),library,null);
      System.out.println("PASS native Attachment Access Functions public entry compilation");
    }
  }
  static void accessGuards(Path root)throws Exception {
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      for(String owner:List.of("Attachments/Attachment Access Functions","Documents/Document Access Functions")) {
      String fn=owner.startsWith("Attachments")?"registerAccessPublic":"registerDocumentAccessPublic";
      var definition=values.source(m("type",owner),"definition");
      var library=m("functions",values.bexData(values.select(definition,"/functions")));
      var source=m("constants",m("authority","provider","key","attachment"),"do",List.of(m("$return",m("$call",m("function",fn,"args",m("input",m("$binding","call/request")))))));
      var bex=new Bex(BexProfile.current());var program=bex.compile(source,library,null);
      var publicKey=typed(values,"Coordination/Ed25519 Public Key","value","00".repeat(32));
      var timelineProvider=typed(values,"Coordination/Timeline Provider","publicKey",publicKey,"endpoint","https://provider.example");
      var provider=typed(values,"Coordination/Public Timeline Channel","provider",timelineProvider,"url","https://provider.example/public");
      var access=typed(values,"Coordination/Timeline Access","allowedKeys",List.of(),"allowedTimelines",List.of(),"contracts",m("provider",provider));
      for(Object candidate:List.of(access)) {
        var matcher=inputMatcher(values,owner,fn);
        require(!matches(values,m("documents",List.of(7)),matcher),"Malformed scalar is rejected at the public matcher");
        var itemType=values.literal(values.exact(values.child(values.child(matcher,"documents"),"itemType")));
        Object request=m("documents",List.of(values.view(values.source(candidate))),"basePath","/access");
        if(candidate.equals(access)) {
          var wire=m("documents",m("type","List","itemType",itemType,"items",List.of(access)),"basePath","/access");
          require(matches(values,wire,matcher),"Uninitialized exact Timeline Access reaches existing executor guard");
          request=values.view(values.source(wire));
        }
        var context=new BexContext(m("activation",m("parties",m("buyer",m()),"allowNewParties",true)),m(),m(),Values.UNDEFINED,m(),m("call",m("channel","buyer","requireExactDocumentVersion",true,"request",request)),"/",null,
          (actual,pattern)->values.matches(actual,values.source(pattern,"definition")),
          (actual,gas)->NativeRuntime.identity(values.source(Values.blueValue(actual))));
        String expected=candidate.equals(access)?"TIMELINE_ACCESS_INITIALIZATION_REQUIRED":"TIMELINE_ACCESS_DOCUMENT_REQUIRED";
        boolean rejected=false;
        try{bex.execute(program,context,1000000);}catch(BexError invalid){rejected=invalid.toString().contains(expected);if(!rejected)throw invalid;}
        require(rejected,"Existing executor rejects at precise stage "+expected);
      }
      }
      System.out.println("PASS both public Access matchers reject scalar; existing executors reject noninitialized documents");
    }
  }
  @SuppressWarnings("unchecked")
  static void sourceInputs(Path root)throws Exception {
    var source=(Map<String,Object>)WireData.parse(Files.readString(root.resolve("clause-documents/types/admission-consent-functions.blue")),"yaml");
    var functions=(Map<String,Object>)source.get("functions");
    var function=(Map<String,Object>)functions.get("recordConsent");
    var args=(Map<String,Object>)function.get("args");
    try(var blue=Blue.builder().build()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      require(!values.matches(values.source(m()),values.source(args.get("input"),"definition")),"recordConsent must reject missing admissionRef and decision");
    }
  }
  static Map<String,Object> typed(ContractsExecution.Values values,String type,Object... fields) {
    var result=m("type",m("blueId",values.head(values.source(m("type",type),"definition")).type));
    result.putAll(m(fields));return result;
  }
  static boolean matches(ContractsExecution.Values values,Object input,Object matcher) {
    try {return values.matches(values.source(input),matcher);}catch(Failure invalid){return false;}
    catch(ContractException invalid){if(invalid.code().startsWith("LANGUAGE_"))return false;throw invalid;}
  }
  static Object inputMatcher(ContractsExecution.Values values,String library,String function) {
    return values.select(values.source(m("type",library),"definition"),"/functions/"+function+"/args/input");
  }
  static void inputs(Path root)throws Exception {
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      for(var entry:List.of(List.of("Documents/Admission Consent Functions","recordConsent","admissionRef"),
          List.of("Attachments/Attachment Endpoint Functions","linkParent","document"),
          List.of("Attachments/Attachment Functions","attach","document"),
          List.of("Attachments/Attachment Access Functions","registerAccessPublic","documents"),
          List.of("Documents/Document Access Functions","registerDocumentAccessPublic","documents"))) {
        var matcher=inputMatcher(values,entry.get(0),entry.get(1));
        require(!matches(values,m(),matcher),entry.get(0)+"."+entry.get(1)+" must require "+entry.get(2));
      }
      var consent=inputMatcher(values,"Documents/Admission Consent Functions","recordConsent");
      for(String choice:List.of("approve","decline"))require(matches(values,m("admissionRef","pending","decision",choice),consent),"Consent accepts explicit "+choice);
      require(!matches(values,m("admissionRef","pending","decision","maybe"),consent),"Consent rejects unknown decision");
      require(!matches(values,m("admissionRef",7,"decision","approve"),consent),"Consent rejects incorrect reference type");
      for(String library:List.of("Documents/Document Access Functions","Attachments/Attachment Access Functions")) {
        String fn=library.startsWith("Documents")?"registerDocumentAccessPublic":"registerAccessPublic";
        var matcher=inputMatcher(values,library,fn);
        require(!matches(values,m("documents",List.of()),matcher),"Access documents cannot be empty");
        require(!matches(values,m("documents",List.of(m("unrelated",true))),matcher),"Access requires Timeline Access documents");
        var access=typed(values,"Coordination/Timeline Access","allowedKeys",List.of(),"allowedTimelines",List.of(),"contracts",m("initialized",m("document",m("state","Original access"))));
        var itemType=values.literal(values.exact(values.child(values.child(matcher,"documents"),"itemType")));
        require(!matches(values,m("documents",m("type","List","itemType",itemType,"items",List.of())),matcher),"Native Access list cannot be empty");
        var list=m("type","List","itemType",itemType,"items",List.of(access));
        require(matches(values,m("documents",list),matcher),"Existing native access type is accepted without republishing");
        var existingRef=m("blueId",NativeRuntime.identity(values.source(access)));
        require(matches(values,m("documents",m("type","List","itemType",itemType,"items",List.of(existingRef))),matcher),"Existing native Access publication reference matches unchanged");
        require(!matches(values,m("documents",m("type","List","itemType",itemType,"items",Collections.nCopies(17,access))),matcher),"Access list cannot exceed sixteen documents");
      }
      var rebase=inputMatcher(values,"Documents/Admission Functions","rebaseAdmissionPublic");
      var typed=typed(values,"Documents/Admission Rebase Input","admissionRef","pending");
      require(matches(values,typed,rebase),"Rebase key is optional");
      typed.put("key","entry");require(matches(values,typed,rebase),"Rebase accepts explicit key");
      typed.put("key",7);require(!matches(values,typed,rebase),"Rebase validates optional key type");
      var prepare=inputMatcher(values,"Attachments/Attachment Functions","preparePublic");
      require(matches(values,typed(values,"Attachments/Attachment Preparation Input"),prepare),"Existing authority allows omitted optional input");
      require(!matches(values,typed(values,"Attachments/Attachment Preparation Input","authorityParty",m("lead",m("channel",7))),prepare),"Authority channel type checked");
      var begin=inputMatcher(values,"Attachments/Preparation Functions","beginPublic");
      require(matches(values,typed(values,"Attachments/Attachment Preparation Input","requestId","request-1"),begin),"Begin accepts omitted optional data");
      require(!matches(values,typed(values,"Attachments/Attachment Preparation Input"),begin),"Begin requires requestId");
      for(var entry:List.of(List.of("Attachments/Attachment Functions","create"),List.of("Attachments/Preparation Functions","resume")))
        require(matches(values,m(),inputMatcher(values,entry.get(0),entry.get(1))),entry+" requires no fabricated fields");
      var candidate=values.source(m("name","Existing document","state",true,"contracts",m("initialized",m("document",m("state","origin")))));
      var ref=m("blueId",NativeRuntime.identity(candidate));
      require(matches(values,m("document",ref),inputMatcher(values,"Attachments/Attachment Functions","attach")),"Attach accepts exact existing publication reference");
      System.out.println("PASS native document/attachment required, optional, enum, access, reference and no-input declarations");
    }
  }
  @SuppressWarnings("unchecked")
  static void preparationEffect(Path root)throws Exception {
    var source=workOrder(root);
    var original=(Map<String,Object>)WireData.parse(Files.readString(root.resolve("examples/preparation/08-local-work-order.blue")),"yaml");
    var clauses=(Map<String,Object>)source.get("clauses");var instruction=(Map<String,Object>)clauses.get("instruction");
    var bindings=(Map<String,Object>)instruction.get("bindings");
    var originalClauses=(Map<String,Object>)original.get("clauses");var originalInstruction=(Map<String,Object>)originalClauses.get("instruction");
    instruction.put("bindings",originalInstruction.get("bindings"));
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var authoring=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var processor=authoring.processor(packages.language());var initial=processor.initialize(source);
      require(initial.status().equals("APPLIED"),"Preparation source initialization: "+initial.observations());
      var request=m("type","Attachments/Attachment Preparation Input","requestId","reviewed-preparation-1");
      var prepared=processor.process(initial.document(),OperationCatalogConformance.event(initial.document(),"customer","prepareDocument",request),1);
      if(!prepared.status().equals("APPLIED")) ClauseGasProbe.diagnose(processor,initial.document(),OperationCatalogConformance.event(initial.document(),"customer","prepareDocument",request),1L);
      require(prepared.status().equals("APPLIED"),"Configured preparation execution: "+prepared.observations());
      require("reviewed-preparation-1".equals(processor.read(prepared.document(),"/preparation_instruction/requestId")),"Preparation persists exact user request ID");
      require(processor.read(prepared.document(),"/instructionRequest")!=null,"Preparation creates the configured request");
      require("ready".equals(processor.read(prepared.document(),"/preparation_instruction/status")),"Preparation reaches actual ready state");
      require(processor.read(prepared.document(),"/instruction")!=null,"Preparation installs its actual document");
      var resumed=processor.process(prepared.document(),OperationCatalogConformance.event(prepared.document(),"seller","resumeDocument",m()),2);
      require(resumed.status().equals("APPLIED"),"Configured resume without fabricated input: "+resumed.observations());
      require("reviewed-preparation-1".equals(processor.read(resumed.document(),"/preparation_instruction/requestId")),"Resume preserves preparation identity");
      System.out.println("PASS actual configured native preparation and no-input resume effects");
    }
  }
  static void paymentPreparation(Path root)throws Exception {
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var authoring=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var processor=authoring.processor(packages.language());
      var initial=processor.initialize(workOrder(root,"13-current-payment-document.blue",false));
      require(initial.status().equals("APPLIED"),"Current Payment Clause initialization: "+initial.observations());
      var prepared=processor.process(initial.document(),OperationCatalogConformance.event(initial.document(),"customer","preparePayment",m()),1);
      if(!prepared.status().equals("APPLIED")) ClauseGasProbe.diagnose(processor,initial.document(),OperationCatalogConformance.event(initial.document(),"customer","preparePayment",m()),1L);
      require(prepared.status().equals("APPLIED"),"Current Payment Clause preparation: "+prepared.observations());
      var state=processor.read(prepared.document(),"/process_instruction");
      require(state instanceof Map<?,?> map && map.get("entries") instanceof Map<?,?> entries && !entries.isEmpty(),"Current Payment Clause persists a prepared entry");
      var resumed=processor.process(prepared.document(),OperationCatalogConformance.event(prepared.document(),"customer","resumePayment",m()),2);
      require(resumed.status().equals("APPLIED"),"Current Payment Clause resume: "+resumed.observations());
      System.out.println("PASS current Payment Clause native Documents preparation and resume");
    }
  }
  static void nativeLists() {
    try(var blue=Blue.builder().build()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var fresh=values.source(m("name","New document review item","count",m("type","Integer","schema",m("required",true))),"definition");
      var itemType=m("blueId",NativeRuntime.identity(fresh));
      var item=m("type",itemType,"count",7);
      var declaration=values.source(m("type","List","itemType",itemType),"definition");
      var raw=List.of(item);var rawNode=values.source(raw);
      require(!values.matches(rawNode,declaration),"Raw array must not silently acquire declared native List type");
      require(values.matches(rawNode,values.source(List.of(m("type",itemType)),"definition")),"Raw array remains valid for positional native matcher");
      var itemRef=m("blueId",NativeRuntime.identity(values.source(item)));
      for(Object member:List.of(item,itemRef)) {
        var request=m("type","List","itemType",itemType,"items",List.of(member));
        var before=WireData.write(request);
        require(values.matches(values.source(request),declaration),"Explicit native List accepts custom value and reference");
        require(before.equals(WireData.write(request)),"Validation must preserve exact reference/envelope input");
      }
      require(!matches(values,m("type","List","itemType",itemType,"items",List.of(m("type",itemType,"count","wrong"))),declaration),"Custom list validates item fields");
      System.out.println("PASS source admission versus canonical raw/typed/reference custom List matrix");
    }
  }
  static void referenceExecutor(Path root)throws Exception {
    try(var blue=Blue.builder().build()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var sourceLibrary=(Map<?,?>)WireData.parse(Files.readString(root.resolve("clause-attachments/types/rules.blue")),"yaml");
      var sourceFunctions=(Map<?,?>)sourceLibrary.get("functions");
      var library=m("functions",m("origin",sourceFunctions.get("origin")));
      var source=m("do",List.of(m("$return",m("$call",m("function","origin","args",m("document",m("$binding","call/request")))))));
      var bex=new Bex(BexProfile.current());var program=bex.compile(source,library,null);
      var origin=values.source(m("state","Original publication"));
      var initialized=values.source(m("state","Current publication","contracts",m("initialized",m("document",m("blueId",NativeRuntime.identity(origin))))));
      var ref=m("blueId",NativeRuntime.identity(initialized));
      for(Object input:List.of(ref,7,m("name","Uninitialized"))) {
        var context=new BexContext(m(),m(),m(),Values.UNDEFINED,m(),m("call",m("request",values.view(values.source(input)))),"/",null,
          (actual,pattern)->values.matches(actual,values.source(pattern,"definition")),
          (actual,gas)->NativeRuntime.identity(values.source(Values.blueValue(actual))));
        boolean accepted=true;
        try{bex.execute(program,context,1000000);}catch(BexError invalid){accepted=false;}
        require(accepted==input.equals(ref),"Executor initialization requirement must agree for "+input);
      }
      System.out.println("PASS actual Attachment origin executor accepts native reference and rejects scalar/uninitialized document");
    }
  }
  static void consentEffect(Path root)throws Exception {
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var definition=values.source(m("type","Documents/Admission Consent Functions"),"definition");
      var library=m("functions",values.bexData(values.select(definition,"/functions")));
      var source=m("constants",m("itemPath","/pending","admissionRef","admission-1","party","buyer"),"do",List.of(m("$return",m("$call",m("function","recordConsent","args",m("input",m("$binding","call/request")))))));
      var bex=new Bex(BexProfile.current());var program=bex.compile(source,library,null);
      var input=m("admissionRef","admission-1","decision","approve");
      var context=new BexContext(m("pending",m("admissionRef","admission-1","status","admission_pending","consents",m())),m(),m(),Values.UNDEFINED,m(),m("call",m("request",input)),"/",null,
        (actual,pattern)->values.matches(actual,values.source(pattern,"definition")),
        (actual,gas)->NativeRuntime.identity(values.source(Values.blueValue(actual))));
      var result=bex.execute(program,context,1000000);
      require(result.changeset().stream().anyMatch(item->item instanceof Map<?,?> map&&"/pending/consents/buyer".equals(map.get("path"))&&"approve".equals(map.get("val"))),"Consent must record exact user decision");
      System.out.println("PASS native admission consent effect");
    }
  }
  public static void main(String[] args)throws Exception {
    if(args.length>1&&args[1].equals("paymentPreparation"))paymentPreparation(Path.of(args[0]));else if(args.length>1&&args[1].equals("accessGuards"))accessGuards(Path.of(args[0]));else if(args.length>1&&args[1].equals("preparation"))preparationEffect(Path.of(args[0]));else if(args.length>1&&args[1].equals("representation"))nativeLists();else if(args.length>1&&args[1].equals("reference"))referenceExecutor(Path.of(args[0]));else if(args.length>1&&args[1].equals("consent"))consentEffect(Path.of(args[0]));else if(args.length>1&&args[1].equals("source"))sourceInputs(Path.of(args[0]));else if(args.length>1&&args[1].equals("inputs"))inputs(Path.of(args[0]));else if(args.length>1&&args[1].equals("access"))accessLibrary(Path.of(args[0]));else connectionRequests(Path.of(args[0]));
  }
}
