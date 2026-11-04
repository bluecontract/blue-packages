import blue.core.CompositionPackages;

import blue.bex.*;
import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native isolated clause qualification. Authenticated Core bootstrap remains a separate hosted proof. */
public final class BootstrapOrdersConformance {
  static Map<String,Object> m(Object... pairs) {
    var out=new LinkedHashMap<String,Object>();
    for(int i=0;i<pairs.length;i+=2)out.put((String)pairs[i],pairs[i+1]);
    return out;
  }
  @SuppressWarnings("unchecked") static Map<String,Object> obj(Object value) {return (Map<String,Object>)value;}
  static void require(boolean condition,String message) {if(!condition)throw new AssertionError(message);}
  static void equal(Object a,Object b,String message) {require(Objects.equals(Values.copy(a),Values.copy(b)),message);}
  static Object copy(Object value) {return Values.copy(value);}
  static Object event(Contracts.Document document,String operation,Object request) {
    return m("source","partner","operation",m("type","Contracts/Operation Request","channel","partner",
        "operation",operation,"document",m("blueId",document.blueId()),"request",request,"requireExactDocumentVersion",true));
  }
  static Contracts.Result applied(Contracts.Result result) {
    require(result.commits(),result.status()+" "+result.observations());return result;
  }
  static Object channel(String source) {return m("type","Contracts/External Channel","event",m("source",source));}
  static Object party(String role) {
    return m("type","Parties/Party","myosAccountId",role+"-account","lead",m("channel",channel(role)),
        "readerKeys",List.of(role+"-reader"),"representatives",m("agent",m("representativeId",role+"-agent",
            "myosAccountId",role+"-agent-account","channel",channel(role+"-agent"),"readerKeys",List.of(role+"-agent-reader"))));
  }
  static Object template(List<String> required) {
    return m("type","Orders/Order with Clauses","name","Prepared catalogue Order","currency","USD",
        "clauses",m("activation",m("type","Activation/Activation Clause","parameters",m(
            "parties",m("seller",m("type","Parties/Party"),"partner",m("type","Parties/Party"),"customer",m("type","Parties/Party")),"required",required))));
  }
  static Map<String,Object> source(Map<String,Object> fixture,boolean fulfilment,List<String> required) {
    var clauses=m("activation",m("type","Activation/Activation Clause","parameters",m(
        "parties",m("seller",party("seller"),"partner",party("partner")),"required",List.of())),
        "catalog",m("type","Reseller/Catalog Clause","parameters",fixture.get("catalogParameters"),"bindings",m(
            "state","/products","quotes","/quotes","quote",m("createQuote",m("on","workflow","party","partner","params",m("$var","trigger"))))),
        "orders",m("type","Reseller/Customer Orders Bootstrap Clause","bindings",m("template","/orderTemplate","collection","/orders",
            "parties",m("seller","seller","partner","partner"),"startOrder",m("newOrder",m("on","workflow","party","partner","params",m("$var","trigger"))),
            "provide",m("provideOrder",m("on","workflow","party","partner")))));
    if(fulfilment)clauses.put("fulfilment",m("type","Reseller/Fulfilment Terms Clause","parameters",m(
        "terms",fixture.get("fulfilmentTerms"),"template",m("clauses",m("confirmation",m("type","Reseller/Confirmation Clause"))))));
    return m("type","Agreements/Agreement with Clauses","name","Private catalogue agreement","description",fixture.get("agreementDescription"),
        "products",fixture.get("products"),"quotes",m(),"orders",m(),"orderTemplate",template(required),
        "contracts",m("seller",channel("seller"),"partner",channel("partner"),"seller__agent",channel("seller-agent"),"partner__agent",channel("partner-agent")),"clauses",clauses);
  }
  static Map<String,Object> item(Contracts p,Contracts.Document d) {return obj(obj(p.read(d,"/process_orders/entries")).values().iterator().next());}
  static Object literal(Contracts p,Contracts.Document d,String path) {
    var values=p.execution().values();
    return values.literal(values.exact(values.select(new Exact.Ref(d.blueId()),path)));
  }
  static void rejected(Contracts p,Contracts.Document before,String operation,Object request,String reason,long now) {
    var result=p.process(before,event(before,operation,request),now);
    require(!result.commits(),"Expected rejection: "+reason);
    equal(before.identity(),result.document().identity(),"Rejected request must preserve document");
    equal(obj(ClauseGasProbe.diagnostic(result)).get("code"),"BEX_EXECUTION_REJECTED","Native execution rejection");
    require(p.emitted(result).isEmpty(),"Rejected request emits no effects");
    boolean diagnosed=false;
    try {ClauseGasProbe.diagnose(p,before,event(before,operation,request),now);}
    catch(BexError failure) {diagnosed=failure.toString().contains(reason);if(!diagnosed)throw failure;}
    require(diagnosed,"Expected authored rejection "+reason);
  }
  static void scenario(CompositionPackages packages,Path root,Path reports,String name,boolean fulfilment,List<String> required) throws Exception {
    var fixture=obj(WireData.json(Files.readString(root.resolve("clause-reseller/tests/fixtures/"+name+"/catalogue.json"))));
    try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var p=runtime.processor(packages.language());
      var current=applied(p.initialize(source(fixture,fulfilment,required)));
      require(Boolean.TRUE.equals(p.read(current.document(),"/activation/active")),"Parent active");
      var quoteRequest=obj(copy(obj(fixture.get("quote")).get("intent")));
      current=applied(p.process(current.document(),event(current.document(),"createQuote",quoteRequest),1));
      equal(p.read(current.document(),"/quotes/family-quote"),fixture.get("quote"),"Unchanged authoritative quote "+name);
      var input=m("key","order-one","requestId","prepare-one","customer","customer-account","quoteKey","family-quote","description","Reviewed booking");
      if(fulfilment)input.put("groups",fixture.get("groups"));
      current=applied(p.process(current.document(),event(current.document(),"newOrder",input),2));
      var pending=item(p,current.document());String path=pending.get("itemPath")+"/prepared";
      equal(pending.get("prepareFor"),"bootstrap","Native preparation mode");equal(pending.get("status"),"awaiting_provider","Await actual provider");
      equal(p.read(current.document(),"/orders"),m(),"No initialized embedded Order before bootstrap");
      var prepared=obj(p.read(current.document(),path));
      require(!obj(prepared.getOrDefault("contracts",m())).containsKey("initialized"),"Requirement remains uninitialized");
      equal(p.read(current.document(),path+"/clauses/activation/parameters/required"),required,"Template required approvers preserved");
      equal(prepared.get("quote"),fixture.get("quote"),"Frozen quote");equal(prepared.get("customerAccountId"),"customer-account","Frozen customer");
      for(String role:List.of("seller","partner")) {
        var mapped=obj(p.read(current.document(),path+"/clauses/activation/parameters/parties/"+role));
        require(!obj(mapped.getOrDefault("lead",m())).containsKey("channel"),"No parent lead channel");
        var rep=obj(obj(mapped.get("representatives")).get("agent"));require(!rep.containsKey("channel"),"No parent representative channel");
        equal(rep.get("representativeId"),role+"-agent","Preserved representative identity");equal(rep.get("readerKeys"),List.of(role+"-agent-reader"),"Preserved representative readers");
      }
      var wrongProvision=m("type","Documents/Provision Input","key","order-one","inResponseTo","different-request","requirementRef",pending.get("requirementRef"),"document",m("blueId",current.document().blueId()));
      rejected(p,current.document(),"provideOrder",wrongProvision,"PREPARATION_WRONG_REQUEST",3);
      wrongProvision.put("inResponseTo",pending.get("requestId"));wrongProvision.put("requirementRef","different-requirement");
      rejected(p,current.document(),"provideOrder",wrongProvision,"PREPARATION_WRONG_REQUIREMENT",4);
      var retainedLiteral=obj(literal(p,current.document(),pending.get("itemPath").toString()));
      var preparedLiteral=obj(literal(p,current.document(),path));
      domainGuards(p,preparedLiteral,obj(retainedLiteral.get("domainTerms")));
      Object exact=copy(pending);
      var repeated=applied(p.process(current.document(),event(current.document(),"newOrder",input),2_000_000_000_000_000L));
      equal(item(p,repeated.document()),exact,"Exact replay after original proposed date");
      equal(obj(p.read(repeated.document(),"/process_orders/entries")).size(),1,"One preparation");
      var changed=obj(copy(input));changed.put("customer","other-account");rejected(p,repeated.document(),"newOrder",changed,"PREPARATION_OBLIGATION_CONFLICT",2_000_000_000_000_001L);
      changed=obj(copy(input));changed.put("quoteKey","another-quote");rejected(p,repeated.document(),"newOrder",changed,"PREPARATION_OBLIGATION_CONFLICT",2_000_000_000_000_002L);
      changed=obj(copy(input));changed.put("amountMinor",1);rejected(p,repeated.document(),"newOrder",changed,"UNKNOWN_ORDER_INPUT",2_000_000_000_000_003L);
      if(!fulfilment){changed=obj(copy(input));changed.put("key","new-grouped");changed.put("groups",List.of());rejected(p,repeated.document(),"newOrder",changed,"BOOKING_CLAUSE_REQUIRED",2_000_000_000_000_004L);}
      String id=name+(fulfilment?"-fulfilment":"-plain")+(required.isEmpty()?"-no-extra-approval":"-supplier-approval");
      Files.writeString(reports.resolve(id+".json"),WireData.write(m("scope","Native component execution; authenticated hosted bootstrap not performed","item",retainedLiteral,"prepared",preparedLiteral,"quote",fixture.get("quote"),"sameKeyReplay",true,"noEmbeddedOrder",true)));
      System.out.println("PASS "+id);
    }
  }
  static void domainGuards(Contracts processor,Map<String,Object> prepared,Map<String,Object> frozen) throws Exception {
    var values=processor.execution().values();
    var definition=values.source(m("type","Reseller/Customer Orders Bootstrap Clause"),"definition");
    var all=obj(values.bexData(values.select(definition,"/actionDefinition/type/functions")));
    var library=m("functions",m("domainValidateCandidate",all.get("domainValidateCandidate")));
    var code=m("do",List.of(m("$return",m("$call",m("function","domainValidateCandidate","args",m(
        "frozenTerms",m("$binding","call/request/frozen"),"candidate",m("$binding","call/request/candidate")))))));
    var bex=new Bex(BexProfile.current());var program=bex.compile(code,library,null);
    for(String variant:List.of("exact","changed-current-customer","changed-origin-customer","missing-origin-customer","changed-quote","changed-price","changed-fulfilment")) {
      var candidate=obj(copy(prepared));var initial=obj(copy(prepared));
      var initialCustomer=obj(obj(obj(obj(initial.get("clauses")).get("activation")).get("parameters")).get("parties"));
      // The generic bootstrap requirement deliberately leaves the supplied customer slot open.
      // This isolated domain test models the Core-bound origin; the hosted proof supplies it for real.
      initialCustomer.put("customer",m("myosAccountId","customer-account"));
      candidate.put("contracts",m("initialized",m("document",initial)));
      candidate.put("activation",m("parties",m("customer",m("myosAccountId","customer-account"))));
      String reason="CUSTOMER_ORDER_COMMERCIAL_TERMS_CHANGED";
      switch(variant) {
        case "changed-current-customer" -> {obj(obj(candidate.get("activation")).get("parties")).put("customer",m("myosAccountId","foreign"));reason="CUSTOMER_ORDER_IDENTITY_CHANGED";}
        case "changed-origin-customer" -> {obj(initialCustomer.get("customer")).put("myosAccountId","foreign");reason="CUSTOMER_ORDER_BOOTSTRAP_IDENTITY_CHANGED";}
        case "missing-origin-customer" -> {obj(initialCustomer.get("customer")).remove("myosAccountId");reason="CUSTOMER_ORDER_BOOTSTRAP_IDENTITY_CHANGED";}
        case "changed-quote" -> candidate.put("quote",m("totalMinor",1));
        case "changed-price" -> candidate.put("amountMinor",1);
        case "changed-fulfilment" -> {candidate.put("orderSnapshot",m("changed",true));reason="CUSTOMER_ORDER_FULFILMENT_CHANGED";}
      }
      var context=new BexContext(m(),m(),m(),Values.UNDEFINED,m(),m("call",m("request",m("candidate",candidate,"frozen",frozen))),"/",null,
          (actual,pattern)->values.matches(actual,values.source(pattern,"definition")),
          (actual,gas)->NativeRuntime.identity(values.source(Values.blueValue(actual))));
      boolean rejected=false;
      try {bex.execute(program,context,1_000_000);} catch(BexError failure) {
        require(failure.getMessage().contains(reason),variant+": "+failure.getMessage());rejected=true;
      }
      require(rejected!=variant.equals("exact"),"Frozen native domain guard "+variant);
    }
  }
  public static void main(String[] args) throws Exception {
    Path root=Path.of(args[0]),reports=Path.of(args[1]);Files.createDirectories(reports);
    var selection=obj(WireData.json(Files.readString(root.resolve("PACKAGES.json"))));
    Path archive=root.resolve("clause-reseller/dist/package.bluepkg");var reseller=BluePackage.open(archive);
    String sha="sha256:"+HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(archive)));
    obj(selection.get("mounts")).put("Reseller",m("path","clause-reseller/dist/package.bluepkg","blueId",reseller.blueId(),"archiveSha256",sha));
    Path selectionFile=reports.resolve("selection.json");Files.writeString(selectionFile,WireData.write(selection));
    var packages=CompositionPackages.published(root,selectionFile);
    BootstrapPreparationConformance.bootstrapPartyGuards(packages);
    BootstrapPreparationConformance.bootstrapAccessGuards(packages);
    for(String example:List.of("01-cruise","02-massage","03-watersports"))scenario(packages,root,reports,example,true,List.of());
    scenario(packages,root,reports,"01-cruise",false,List.of());
    scenario(packages,root,reports,"01-cruise",true,List.of("seller"));
  }
}
