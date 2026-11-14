import blue.contracts.*;
import blue.bex.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native preparation contract; signed bootstrap/provision is qualified in Core. */
public final class BootstrapPreparationConformance {
  static Map<String,Object> m(Object... pairs) {
    var result=new LinkedHashMap<String,Object>();
    for(int i=0;i<pairs.length;i+=2)result.put((String)pairs[i],pairs[i+1]);
    return result;
  }
  @SuppressWarnings("unchecked") static Map<String,Object> obj(Object value) {return (Map<String,Object>)value;}
  static void require(boolean condition,String message) {if(!condition)throw new AssertionError(message);}
  static Object event(Contracts.Document document,String operation,Object request) {
    return m("source","merchant","operation",m("type","Contracts/Operation Request",
        "channel","merchant","operation",operation,"document",m("blueId",document.blueId()),
        "request",request,"requireExactDocumentVersion",true));
  }
  static Contracts.Result applied(Contracts.Result result) {
    require(result.commits(),result.status()+" "+result.observations());return result;
  }
  static Map<String,Object> source(String mode) {
    var channel=m("type","Contracts/External Channel","event",m("source","merchant"));
    var party=m("type","Parties/Party","myosAccountId","merchant","lead",m("channel",channel),"readerKeys",List.of("reader-merchant"));
    var child=m("name","Customer order","type","Orders/Order with Clauses",
        "size",m("type","Integer","schema",m("enum",List.of(40,41,42))),
        "clauses",m("activation",m("type","Activation/Activation Clause","parameters",m(
            "parties",m("seller",m("type","Parties/Party"),"customer",m("type","Parties/Party")),
            "required",List.of("seller","customer")))));
    var parameters=m("obtain","provide","suppliedBy","merchant","suppliedParties",List.of("customer"),
        "fieldPaths",m("size","/size"),"template",child);
    if(mode!=null)parameters.put("prepareFor",mode);
    return m("name","Private agreement","type","Agreements/Agreement with Clauses",
        "contracts",m("merchant",channel),"clauses",m(
            "activation",m("type","Activation/Activation Clause","parameters",m("parties",m("merchant",party),"required",List.of("merchant"))),
            "orders",m("type","Documents/Documents Clause","parameters",parameters,"bindings",m(
                "parties",m("seller","merchant"),"collection","/orders",
                "prepare",m("prepareOrder",m("on","workflow","party","merchant","request",m("type","Documents/Preparation Input"),"params",m("$pointerSet",m("object",m("$var","trigger"),"path","/type","op","remove")))),
                "provide",m("provideOrder",m("on","workflow","party","merchant"))))));
  }
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    pinnedReaderNormalization(packages);
    rootReaderAccessGuards(packages);
    bootstrapPartyGuards(packages);
    bootstrapAccessGuards(packages);
    for(String mode:List.of("bootstrap","inherited","unknown"))try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var p=runtime.processor(packages.language());
      var host=applied(p.initialize(source(mode.equals("inherited")?null:mode)));
      if(mode.equals("bootstrap")) {
        require("/activation".equals(p.read(host.document(),"/contracts/processActivation_orders/path")),"Local activation transition must trigger a fresh readiness evaluation");
        require("processActivation_orders".equals(p.read(host.document(),"/contracts/refreshActivationProcesses_orders/channel")),"Activation readiness workflow must use its local update channel");
        require(p.read(host.document(),"/contracts/refreshActivationProcesses_orders/steps/0/functions/configuredSources") instanceof Map<?,?> activationContext && activationContext.containsKey("expr"),"Activation refresh must compile exact source validators");
        require(Objects.equals(p.read(host.document(),"/contracts/refreshProcesses_orders/steps"),p.read(host.document(),"/contracts/refreshActivationProcesses_orders/steps")),"Activation refresh must preserve the existing guarded refresh computation");
        require(p.read(host.document(),"/contracts/refreshProcesses_orders/steps/0/functions/connectionConfiguration") instanceof Map<?,?> context0 && context0.containsKey("expr"),"Generated refresh must retain its exact clause configuration");
        require(p.read(host.document(),"/contracts/refreshEmbeddedProcesses_orders/steps/0/functions/configuredSources") instanceof Map<?,?> context1 && context1.containsKey("expr"),"Generated embedded refresh must compile source validators");
        var observedSource=source("bootstrap");
        obj(obj(obj(observedSource.get("clauses")).get("activation")).get("parameters")).put("accessPaths",List.of("/observerAccess"));
        observedSource.put("observerAccess",m());
        var observerClause=obj(obj(observedSource.get("clauses")).get("orders"));
        observedSource.put("readerTemplate",obj(observerClause.get("parameters")).remove("template"));
        obj(observerClause.get("bindings")).put("template","/readerTemplate");
        var observed=applied(p.initialize(observedSource));
        require(p.read(observed.document(),"/contracts/rootSourceAccess_orders_0/steps/0/functions/connectionConfiguration") instanceof Map<?,?> context2 && context2.containsKey("expr"),"Generated access observer must retain its exact clause configuration");
        require(p.read(observed.document(),"/contracts/rootSourceAccess_orders_0/steps/0/functions/configuredSources") instanceof Map<?,?> context3 && context3.containsKey("expr"),"Generated access observer must compile source validators");
        require("bootstrap".equals(p.read(observed.document(),"/contracts/rootSourceAccess_orders_0/steps/0/functions/connectionConfiguration/expr/$literal/parameters/prepareFor")),"Observer must use this clause's exact configuration");
        require("Customer order".equals(p.read(observed.document(),"/contracts/rootSourceAccess_orders_0/steps/0/functions/connectionSnapshots/expr/$literal/template/name")),"Observer must freeze the declared template binding");
      }
      host=applied(p.process(host.document(),event(host.document(),"approve_merchant",m("revision",1)),1));
      var request=m("type","Documents/Preparation Input","key","one","values",m("size",42));
      var result=p.process(host.document(),event(host.document(),"prepareOrder",request),2);
      if(!result.commits()&&!mode.equals("unknown"))ClauseGasProbe.diagnose(p,host.document(),event(host.document(),"prepareOrder",request),2);
      if(mode.equals("unknown")) {
        require(!result.commits(),"Unknown mode must not create an obligation");
        require(host.document().identity().equals(result.document().identity()),"Rejected mode mutated agreement");
      } else {
        host=applied(result);
        var items=obj(p.read(host.document(),"/process_orders/entries"));require(items.size()==1,"One preparation");
        var item=obj(items.values().iterator().next());
        require(mode.equals(item.get("prepareFor")),"Frozen preparation mode");
        String path=item.get("itemPath")+"/prepared";
        var prepared=obj(p.read(host.document(),path));
        require(!prepared.containsKey("contracts")||!obj(prepared.get("contracts")).containsKey("initialized"),"Preparation must not initialize order");
        require(p.read(host.document(),path+"/size").toString().equals("42"),"Selected size: "+p.read(host.document(),path+"/size")+" prepared "+prepared+" item "+item);
        require(List.of("reader-merchant").equals(p.read(host.document(),path+"/clauses/activation/parameters/parties/seller/readerKeys")),"Preserved reader keys");
        var lead=obj(p.read(host.document(),path+"/clauses/activation/parameters/parties/seller/lead"));
        require(lead.containsKey("channel")==mode.equals("inherited"),"Only inherited mode retains parent channel");
        if(mode.equals("bootstrap")) {
          require(!prepared.containsKey("timelineAccess"),"No parent access in bootstrap preparation");
          require(!obj(obj(obj(prepared.get("clauses")).get("activation")).get("parameters")).containsKey("accessPaths"),"No inherited access paths");
        }
        var repeated=applied(p.process(host.document(),event(host.document(),"prepareOrder",request),3));
        require(obj(p.read(repeated.document(),"/process_orders/entries")).size()==1,"Retry must reuse obligation");
        var invalid=p.process(repeated.document(),event(repeated.document(),"prepareOrder",m("type","Documents/Preparation Input","key","bad","values",m("size",99))),4);
        require(!invalid.commits(),"Disallowed size must fail natively");
      }
      System.out.println("PASS native preparation "+mode);
    }
  }
  static void pinnedReaderNormalization(CompositionPackages packages)throws Exception {
    try(var blue=packages.language()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var definition=values.source(m("type","Documents/Factory Functions"),"definition");
      var functions=new LinkedHashMap<>(obj(values.bexData(values.select(definition,"/functions"))));
      var preparation=obj(WireData.parse(Files.readString(Path.of("clause-documents/types/preparation-functions.blue")),"yaml"));
      functions.putAll(obj(preparation.get("functions")));
      functions.putAll(obj(obj(WireData.parse(Files.readString(Path.of("clause-documents/types/bootstrap-functions.blue")),"yaml")).get("functions")));
      functions.keySet().retainAll(Set.of("normalizeBootstrapSource","normalizeSlots","configuredConstraint","configuredTemplate","configurationParameters","connectionConfiguration","connectionSnapshots","preparedReaderGroups","validateBootstrapReaders"));
      functions=new LinkedHashMap<>(obj(values.bexData(values.select(values.source(m("functions",functions),"definition"),"/functions"))));
      var expected=m("clauses",m("activation",m("parameters",m("readers",m("guarantor",
          m("myosAccountId","guarantor-account","readerKeys",List.of("pinned-key")))))));
      var actual=m("clauses",m("activation",m("parameters",m("readers",m("guarantor",List.of("pinned-key"))))));
      // Mixed maps and nested templates are not erased by root normalization.
      obj(obj(obj(obj(expected.get("clauses")).get("activation")).get("parameters")).get("readers")).put("auditor",List.of("audit-key"));
      obj(obj(obj(obj(actual.get("clauses")).get("activation")).get("parameters")).get("readers")).put("auditor",List.of("audit-key"));
      var nested=m("clauses",m("activation",m("parameters",m("readers",m("nested",m("myosAccountId","nested-account","readerKeys",List.of("nested-key")))))));
      expected.put("template",nested);actual.put("template",Values.copy(nested));
      var programSource=m("do",List.of(m("$return",m("$eq",List.of(
          m("$call",m("function","normalizeBootstrapSource","args",m("source",m("$binding","call/request/actual"),"slots",List.of(),"expected",expected))),
          m("$call",m("function","normalizeBootstrapSource","args",m("source",expected,"slots",List.of(),"expected",expected))))))));
      var bex=new Bex(BexProfile.current());var program=bex.compile(programSource,m("functions",functions),null);
      var context=new BexContext(m(),m(),m(),Values.UNDEFINED,m(),m("call",m("request",m("actual",actual))),"/",null,
          (a,p)->values.matches(a,values.source(p,"definition")),(a,g)->NativeRuntime.identity(values.source(Values.blueValue(a))));
      require(Boolean.TRUE.equals(bex.execute(program,context,1000000).value()),"Pinned reader descriptor must normalize to its exact bootstrap list");
      var changedNested=obj(Values.copy(actual));changedNested.put("template",m("changed",true));
      var nestedCheck=new BexContext(m(),m(),m(),Values.UNDEFINED,m(),m("call",m("request",m("actual",changedNested))),"/",null,
          (x,p)->values.matches(x,values.source(p,"definition")),(x,g)->NativeRuntime.identity(values.source(Values.blueValue(x))));
      require(Boolean.FALSE.equals(bex.execute(program,nestedCheck,1000000).value()),"Nested template must remain exact");
      var valid=m("contracts",m("initialized",m("document",actual)),"clauses",actual.get("clauses"),
          "activation",m("readers",m("guarantor",List.of("pinned-key"),"auditor",List.of("audit-key"))));
      var validation=bex.compile(m("do",List.of(m("$return",m("$call",m("function","validateBootstrapReaders","args",
          m("expected",m("$binding","call/request/expected"),"candidate",m("$binding","call/request/actual"))))))),m("functions",functions),null);
      for(String variant:List.of("valid","changed-key","extra-key","renamed","missing","missing-legacy-reader","runtime-descriptor","initial-changed","current-changed","unknown-field","empty-key","empty-account","nontext-account")) {
        var candidate=obj(Values.copy(valid));var frozen=obj(Values.copy(expected));
        var readers=obj(obj(candidate.get("activation")).get("readers"));
        switch(variant) {
          case "changed-key" -> readers.put("guarantor",List.of("other-key"));
          case "extra-key" -> readers.put("guarantor",List.of("pinned-key","other-key"));
          case "renamed" -> {readers.remove("guarantor");readers.put("other",List.of("pinned-key"));}
          case "missing" -> readers.clear();
          case "missing-legacy-reader" -> readers.remove("auditor");
          case "runtime-descriptor" -> readers.put("guarantor",m("myosAccountId","guarantor-account","readerKeys",List.of("pinned-key")));
          case "initial-changed" -> obj(obj(obj(obj(obj(obj(candidate.get("contracts")).get("initialized")).get("document")).get("clauses")).get("activation")).get("parameters")).put("readers",m());
          case "current-changed" -> obj(obj(obj(candidate.get("clauses")).get("activation")).get("parameters")).put("readers",m());
          case "unknown-field" -> obj(obj(obj(obj(obj(frozen.get("clauses")).get("activation")).get("parameters")).get("readers")).get("guarantor")).put("email","unsupported@example.test");
          case "empty-key" -> obj(obj(obj(obj(obj(frozen.get("clauses")).get("activation")).get("parameters")).get("readers")).get("guarantor")).put("readerKeys",List.of(""));
          case "empty-account" -> obj(obj(obj(obj(obj(frozen.get("clauses")).get("activation")).get("parameters")).get("readers")).get("guarantor")).put("myosAccountId","");
          case "nontext-account" -> obj(obj(obj(obj(obj(frozen.get("clauses")).get("activation")).get("parameters")).get("readers")).get("guarantor")).put("myosAccountId",42);
        }
        var check=new BexContext(m(),m(),m(),Values.UNDEFINED,m(),m("call",m("request",m("expected",frozen,"actual",candidate))),"/",null,
            (x,p)->values.matches(x,values.source(p,"definition")),(x,g)->NativeRuntime.identity(values.source(Values.blueValue(x))));
        boolean rejected=false;try {bex.execute(validation,check,1000000);}catch(BexError failure){
          require(failure.getMessage().contains(Set.of("unknown-field","empty-key","empty-account","nontext-account").contains(variant)?"PREPARATION_PINNED_READER_INVALID":"PREPARATION_PINNED_READER_MISMATCH"),"Unexpected pinned reader rejection: "+failure.getMessage());rejected=true;}
        require(rejected!=variant.equals("valid"),"Pinned reader guard "+variant);
      }
      System.out.println("PASS exact pinned reader normalization and initial/current/runtime guards");
    }
  }
  static void rootReaderAccessGuards(CompositionPackages packages)throws Exception {
    try(var blue=packages.language()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var definition=values.source(m("type","Documents/Factory Functions"),"definition");
      var functions=new LinkedHashMap<>(obj(values.bexData(values.select(definition,"/functions"))));
      var authored=obj(obj(WireData.parse(Files.readString(Path.of("clause-documents/types/admission-functions.blue")),"yaml")).get("functions"));
      functions.putAll(authored);
      functions.put("configurationParameters",m("args",m(),"do",List.of(m("$return",m("$binding","call/request/parameters")))));
      functions.keySet().retainAll(Set.of("rootSourceReaderPartyCovered","rootSourceReaderScope","rootSourceReaderGroupsMatch","configurationParameters","readerGroups","transports","accessRecordsValid"));
      functions=new LinkedHashMap<>(obj(values.bexData(values.select(values.source(m("functions",functions),"definition"),"/functions"))));
      var bex=new Bex(BexProfile.current());
      var source=m("do",List.of(m("$return",m("$call",m("function","rootSourceReaderPartyCovered","args",m("party",m("$binding","call/request/party")))))));
      var document=accessCandidate(values);var activation=obj(document.get("activation"));
      var key=obj(obj(obj(activation.get("parties")).get("seller"))).get("readerKeys");
      var seller=obj(obj(activation.get("parties")).get("seller"));
      var representative=obj(Values.copy(obj(seller.get("lead")).get("channel")));
      obj(representative.get("timeline")).put("url","https://provider.example/order-agent");
      seller.put("representatives",m("agent",m("readerKeys",key,"channel",representative)));
      var representativeAccess=obj(Values.copy(obj(document.get("timelineAccess")).get("seller")));
      representativeAccess.put("allowedTimelines",List.of(representative.get("timeline")));
      obj(document.get("timelineAccess")).put("seller__agent",representativeAccess);
      activation.put("accessPaths",List.of("/timelineAccess/seller","/timelineAccess/seller__agent"));
      activation.put("readers",m("guarantor",key));
      document.put("clauses",m("activation",m("parameters",m("readers",m("guarantor",key)))));
      var needed=m("readerKeys",key,"representatives",m("agent",m("readerKeys",key)));
      for(String variant:List.of("valid","revoked","restored","missing-access","missing-representative-grant","uninitialized","wrong-provider","different-representative","nonroot","bindings-self")) {
        var actual=obj(Values.copy(document));var party=obj(Values.copy(needed));
        var access=obj(obj(actual.get("timelineAccess")).get("seller"));
        if(variant.equals("revoked"))access.put("allowedKeys",List.of());
        if(variant.equals("missing-access"))obj(actual.get("timelineAccess")).clear();
        if(variant.equals("missing-representative-grant"))obj(obj(actual.get("timelineAccess")).get("seller__agent")).put("allowedKeys",List.of());
        if(variant.equals("uninitialized"))obj(access.get("contracts")).remove("initialized");
        if(variant.equals("wrong-provider"))obj(obj(access.get("contracts")).get("provider")).put("provider",typed(values,"Coordination/Timeline Provider","publicKey",typed(values,"Coordination/Ed25519 Public Key","value","11".repeat(32)),"endpoint","https://foreign.example"));
        if(variant.equals("different-representative"))obj(obj(party.get("representatives")).get("agent")).put("readerKeys",List.of("other-key"));
        var parameters=m("sourcePaths",m("order",variant.equals("nonroot")?"/peer":""));
        var bindings=variant.equals("bindings-self")?m("sources",m("order","self")):m();
        var program=bex.compile(source,m("functions",functions,"constants",m("bindings",bindings)),null);
        var context=new BexContext(actual,m(),m(),Values.UNDEFINED,m(),
            m("call",m("request",m("parameters",parameters,"party",party))),"/",null,
            (x,p)->values.matches(x,values.source(p,"definition")),(x,g)->NativeRuntime.identity(values.source(Values.blueValue(x))));
        Object observed=bex.execute(program,context,1000000).value();
        boolean result=Boolean.TRUE.equals(observed);
        require(result==Set.of("valid","restored").contains(variant),"Root reader access guard "+variant+" result="+observed);
      }
      System.out.println("PASS root reader exact groups, grant and scope guards (predicate-level)");
      rootReaderObserverGuards(values,document,needed);
    }
  }
  static void rootReaderObserverGuards(ContractsExecution.Values values,Map<String,Object> base,Map<String,Object> needed)throws Exception {
    var definition=values.source(m("type","Documents/Factory Functions"),"definition");
    var functions=new LinkedHashMap<>(obj(values.bexData(values.select(definition,"/functions"))));
    for(String file:List.of("admission-functions","preparation-functions"))functions.putAll(obj(obj(WireData.parse(Files.readString(Path.of("clause-documents/types/"+file+".blue")),"yaml")).get("functions")));
    functions.put("configurationParameters",m("args",m(),"do",List.of(m("$return",m("sourcePaths",m("order",""))))));
    functions.put("processStatePath",m("args",m(),"do",List.of(m("$return","/process_payment"))));
    functions.keySet().retainAll(Set.of("rootSourceAccessLost","rootSourceReaderScope","rootSourceReaderGroupsMatch","rootSourceReaderPartyCovered","configurationParameters","processStatePath","readerGroups","transports","accessRecordsValid"));
    functions=new LinkedHashMap<>(obj(values.bexData(values.select(values.source(m("functions",functions),"definition"),"/functions"))));
    var bex=new Bex(BexProfile.current());
    var program=bex.compile(m("do",List.of(m("$call",m("function","rootSourceAccessLost","args",m())))),m("functions",functions,"constants",m("bindings",m())),null);
    for(String variant:List.of("valid","revoked","missing-reader","changed-reader","already-selected","unrelated")) {
      var document=obj(Values.copy(base));
      document.put("contracts",m("initialized",m("document",Values.copy(base))));
      var party=obj(Values.copy(needed));party.remove("representatives");party.put("myosAccountId","guarantor");
      var keys=party.get("readerKeys");
      party.put("readerKeys",m("type","List","itemType","Text","schema",m("minItems",1,"maxItems",1,"uniqueItems",true),"items",keys));
      if(variant.equals("unrelated"))party.put("readerKeys",List.of("foreign-reader"));
      var item=m("status",variant.equals("already-selected")?"selected":"usable","itemPath","/process_payment/entries/one","nextActions",List.of(m("operation","secure")),"prepared",m("clauses",m("activation",m("parameters",m("parties",m("guarantor",party))))));
      document.put("process_payment",m("entries",m("one",item)));
      if(!variant.equals("valid"))obj(obj(document.get("timelineAccess")).get("seller")).put("allowedKeys",List.of());
      if(variant.equals("missing-reader"))obj(document.get("activation")).put("readers",m());
      if(variant.equals("changed-reader"))obj(document.get("activation")).put("readers",m("guarantor",List.of("different-key")));
      var nativeDocument=values.view(values.source(document,"definition"));
      var context=new BexContext(nativeDocument,m(),m(),Values.UNDEFINED,m(),m(),"/",null,
          (x,p)->values.matches(x,values.source(p,"definition")),(x,g)->NativeRuntime.identity(values.source(Values.blueValue(x))));
      var result=bex.execute(program,context,1000000);
      boolean lost=Set.of("revoked","missing-reader","changed-reader").contains(variant);
      require(result.events().isEmpty(),"Access observer must emit no domain events");
      require(result.changeset().size()==(lost?2:0),"Reader observer "+variant+" changes="+result.changeset());
      if(lost) {
        require(obj(result.changeset().get(0)).get("val").equals("selected"),"Only downgrade selected status");
        require(obj(result.changeset().get(1)).get("val").equals(List.of()),"Clear stale actions");
      }
    }
    System.out.println("PASS frozen reader dependency observer, revoke/remove/change and no domain effects (native value/helper-level)");
  }
  static Map<String,Object> party(String timeline) {
    return m("lead",m("channel",m("actor","merchant","timeline",timeline)),
        "readerKeys",List.of("merchant-reader"),"representatives",m("myosAgent",
            m("representativeId","agent","channel",m("actor","agent","timeline",timeline+"-agent"),
              "readerKeys",List.of("agent-reader"))));
  }
  static void bootstrapPartyGuards(CompositionPackages packages)throws Exception {
    try(var blue=packages.language()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var definition=values.source(m("type","Documents/Factory Functions"),"definition");
      var functions=new LinkedHashMap<>(obj(values.bexData(values.select(definition,"/functions"))));
      functions.keySet().retainAll(Set.of("requireSameBootstrapParty","requireSameBootstrapPrimary","requireSameMainParty"));
      var library=m("functions",functions);
      var source=m("do",List.of(m("$return",m("$call",m("function","requireSameBootstrapParty","args",
          m("expected",m("$binding","call/request/expected"),"actual",m("$binding","call/request/actual")))))));
      var bex=new Bex(BexProfile.current());var program=bex.compile(source,library,null);
      for(String variant:List.of("fresh-transports","changed-actor","changed-reader","removed-agent","changed-agent","changed-agent-reader")) {
        var actual=party("child");
        switch(variant) {
          case "changed-actor" -> obj(obj(actual.get("lead")).get("channel")).put("actor","stranger");
          case "changed-reader" -> actual.put("readerKeys",List.of("stranger-reader"));
          case "removed-agent" -> actual.put("representatives",m());
          case "changed-agent" -> obj(obj(obj(actual.get("representatives")).get("myosAgent")).get("channel")).put("actor","stranger");
          case "changed-agent-reader" -> obj(obj(actual.get("representatives")).get("myosAgent")).put("readerKeys",List.of("stranger-reader"));
        }
        var context=new BexContext(m(),m(),m(),Values.UNDEFINED,m(),m("call",m("request",m("expected",party("parent"),"actual",actual))),"/",null,
            (a,p)->values.matches(a,values.source(p,"definition")),(a,g)->NativeRuntime.identity(values.source(Values.blueValue(a))));
        boolean rejected=false;
        try {bex.execute(program,context,1000000);}catch(BexError failure) {rejected=true;}
        require(rejected!=variant.equals("fresh-transports"),"Bootstrap mapped-party guard: "+variant);
      }
      System.out.println("PASS bootstrap mapped-party and representative guards");
    }
  }
  static Map<String,Object> typed(ContractsExecution.Values values,String type,Object... fields) {
    var result=m("type",m("blueId",values.head(values.source(m("type",type),"definition")).type));
    result.putAll(m(fields));return result;
  }
  static Map<String,Object> accessCandidate(ContractsExecution.Values values) {
    var key=typed(values,"Coordination/Ed25519 Public Key","value","00".repeat(32));
    var provider=typed(values,"Coordination/Timeline Provider","publicKey",key,"endpoint","https://provider.example");
    var timeline=typed(values,"Coordination/Signed Timeline","provider",provider,"publicRead",false,"url","https://provider.example/order");
    var channel=typed(values,"Coordination/Timeline Channel","actor",typed(values,"Coordination/Actor","id","merchant"),"timeline",timeline);
    var access=typed(values,"Coordination/Timeline Access","allowedKeys",List.of(key),"allowedTimelines",List.of(timeline),
        "contracts",m("initialized",m("document",m("state","origin")),"provider",
            typed(values,"Coordination/Public Timeline Channel","provider",provider,"url","https://provider.example/public")));
    return m("activation",m("parties",m("seller",m("lead",m("channel",channel),"readerKeys",List.of(key))),
        "accessPaths",List.of("/timelineAccess/seller")),"timelineAccess",m("seller",access));
  }
  static void bootstrapAccessGuards(CompositionPackages packages)throws Exception {
    try(var blue=packages.language()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var definition=values.source(m("type","Documents/Factory Functions"),"definition");
      var functions=new LinkedHashMap<>(obj(values.bexData(values.select(definition,"/functions"))));
      functions.keySet().retainAll(Set.of("validateBootstrapAccess","accessRecordsValid","readerGroups","transports"));
      var source=m("do",List.of(m("$return",m("$call",m("function","validateBootstrapAccess","args",m("candidate",m("$binding","call/request")))))));
      var bex=new Bex(BexProfile.current());var program=bex.compile(source,m("functions",functions),null);
      for(String variant:List.of("complete","missing-proof","uninitialized","wrong-provider","missing-key","wrong-timeline","extra-proof","wrong-path")) {
        var candidate=accessCandidate(values);var access=obj(obj(candidate.get("timelineAccess")).get("seller"));
        String reason="PREPARATION_BOOTSTRAP_ACCESS_MISSING";
        switch(variant) {
          case "missing-proof" -> {candidate.put("timelineAccess",m());reason="PREPARATION_BOOTSTRAP_ACCESS_SHAPE";}
          case "extra-proof" -> {obj(candidate.get("timelineAccess")).put("extra",access);reason="PREPARATION_BOOTSTRAP_ACCESS_SHAPE";}
          case "wrong-path" -> {obj(candidate.get("activation")).put("accessPaths",List.of("/timelineAccess/other"));reason="PREPARATION_BOOTSTRAP_ACCESS_SHAPE";}
          case "uninitialized" -> {obj(access.get("contracts")).remove("initialized");reason="PREPARATION_BOOTSTRAP_ACCESS_NOT_INITIALIZED";}
          case "wrong-provider" -> obj(obj(access.get("contracts")).get("provider")).put("provider",typed(values,"Coordination/Timeline Provider","publicKey",typed(values,"Coordination/Ed25519 Public Key","value","11".repeat(32)),"endpoint","https://other.example"));
          case "missing-key" -> access.put("allowedKeys",List.of());
          case "wrong-timeline" -> access.put("allowedTimelines",List.of());
        }
        var context=new BexContext(m(),m(),m(),Values.UNDEFINED,m(),m("call",m("request",candidate)),"/",null,
            (a,p)->values.matches(a,values.source(p,"definition")),(a,g)->NativeRuntime.identity(values.source(Values.blueValue(a))));
        boolean rejected=false;
        try {bex.execute(program,context,1000000);}catch(BexError failure) {
          require(failure.getMessage().contains(reason),variant+" failed for unexpected reason: "+failure.getMessage());
          rejected=true;
        }
        require(rejected!=variant.equals("complete"),"Bootstrap access guard: "+variant);
      }
      System.out.println("PASS bootstrap access coverage and provider guards");
    }
  }

}
