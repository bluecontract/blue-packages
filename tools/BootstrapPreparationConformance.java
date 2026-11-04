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
    bootstrapPartyGuards(packages);
    bootstrapAccessGuards(packages);
    for(String mode:List.of("bootstrap","inherited","unknown"))try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var p=runtime.processor(packages.language());
      var host=applied(p.initialize(source(mode.equals("inherited")?null:mode)));
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
