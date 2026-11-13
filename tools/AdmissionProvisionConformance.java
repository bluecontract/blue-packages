import blue.contracts.*;
import blue.bex.Values;
import blue.coordination.AuthoringRuntime;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Real native admission and provision; AuthoringRuntime is not signed hosted transport qualification. */
public final class AdmissionProvisionConformance {
  static Map<String,Object> m(Object... p){return BootstrapPreparationConformance.m(p);}
  static Map<String,Object> o(Object v){return BootstrapPreparationConformance.obj(v);}
  static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
  static Contracts.Result ok(Contracts.Result r){check(r.commits(),r.status()+" "+r.observations());return r;}
  static Contracts.Result apply(Contracts p,Contracts.Document d,Object event,long time){
    var result=p.process(d,event,time);if(!result.commits())ClauseGasProbe.diagnose(p,d,event,time);
    ok(result);
    System.out.println("Committed operation "+o(o(event).get("operation")).get("operation")+" gas="+result.observations().get("gas"));
    return result;
  }
  static Object event(Contracts.Document d,String channel,String source,String operation,Object request){
    return m("source",source,"operation",m("type","Contracts/Operation Request","channel",channel,"operation",operation,
        "document",m("blueId",d.blueId()),"request",request,"requireExactDocumentVersion",true));
  }
  static Map<String,Object> item(Contracts p,Contracts.Document d,String clause){return o(o(p.read(d,"/process_"+clause+"/entries")).values().iterator().next());}
  static Object exact(Contracts p,Contracts.Document d,String path){var v=p.execution().values();return v.literal(v.exact(v.select(new Exact.Ref(d.blueId()),path)));}
  static Map<String,Object> provision(Map<String,Object> item,Contracts.Document child){return m("type","Documents/Provision Input","key",item.get("key"),"inResponseTo",item.get("requestId"),"requirementRef",item.get("requirementRef"),"document",m("blueId",child.blueId()));}
  static Map<String,Object> party(String actor){return m("type","Parties/Party","myosAccountId",actor,"readerKeys",List.of("reader-"+actor),"lead",m("channel",m("type","Contracts/External Channel","event",m("source",actor))));}
  static Map<String,Object> source(){
    var parent=BootstrapPreparationConformance.source(null);
    parent.put("orders",m());
    var outer=o(o(parent.get("clauses")).get("orders"));
    o(outer.get("parameters")).put("specialization",m("dataPaths",List.of("/size")));
    var order=o(o(outer.get("parameters")).get("template"));
    order.put("payments",m());
    var activation=o(o(o(order.get("clauses")).get("activation")).get("parameters"));
    o(activation.get("parties")).put("customer",party("customer"));
    activation.put("admission",m("approvers",List.of("seller")));
    activation.put("preActivationOperations",List.of("preparePayment","providePayment","approveAdmission_payment_seller"));
    activation.put("preActivationChannels",List.of("admissionUpdate_payment_process","admissionUpdate_payment_activation"));
    var inner=o(o(BootstrapPreparationConformance.source(null).get("clauses")).get("orders"));
    var params=o(inner.get("parameters"));params.put("suppliedBy","seller");params.put("suppliedParties",List.of("guarantor"));params.put("sourcePaths",m("order",""));
    var payment=o(params.get("template"));payment.put("sources",m("order",m()));
    var pa=o(o(o(payment.get("clauses")).get("activation")).get("parameters"));
    pa.put("parties",m("seller",m("type","Parties/Party"),"customer",m("type","Parties/Party"),"guarantor",party("guarantor")));pa.put("required",List.of());
    var bindings=o(inner.get("bindings"));bindings.put("parties",m("seller","seller","customer","customer"));bindings.put("collection","/payments");
    var prepare=o(o(bindings.get("prepare")).remove("prepareOrder"));prepare.put("party","seller");bindings.put("prepare",m("preparePayment",prepare));
    bindings.put("provide",m("providePayment",m("on","workflow","party","seller")));
    o(order.get("clauses")).put("payment",inner);
    return parent;
  }
  static void rejected(Contracts p,Contracts.Document parent,Object input,long time,String expected){
    var denied=p.process(parent,input,time);
    check(!denied.commits(),"Accepted invalid provision: "+expected);
    boolean precise=false;
    try {ClauseGasProbe.diagnose(p,parent,input,time);}
    catch(blue.bex.BexError failure) {
      precise=failure.getMessage().contains(expected);
      if(!precise)throw failure;
    }
    check(precise,"Expected rejection "+expected);
    check(parent.identity().equals(denied.document().identity()),"Rejected provision changed parent");
    check(p.emitted(denied).isEmpty(),"Rejected provision emitted effects");
    System.out.println("Rejected invalid provision: "+expected);
  }
  public static void main(String[] args)throws Exception{
    var root=Path.of(args[0]);var bundle=PackageBundle.builder();
    for(String[] a:List.of(new String[]{"Contracts","blue-contracts"},new String[]{"Clauses","blue-clauses"},new String[]{"Connections","clause-connections"},new String[]{"Activation","clause-activation"},new String[]{"Parties","blue-parties"},new String[]{"Documents","clause-documents"},new String[]{"Orders","blue-orders"},new String[]{"Agreements","blue-agreements"}))bundle.mount(a[0],BluePackage.open(root.resolve(a[1]+"/dist/package.bluepkg")));
    try(var blue=Blue.builder().packages(bundle.build()).build();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())){
      var p=runtime.processor(blue);long clock=0;
      var parent=ok(p.initialize(source()));
      parent=apply(p,parent.document(),event(parent.document(),"merchant","merchant","approve_merchant",m("revision",1)),++clock);
      parent=apply(p,parent.document(),event(parent.document(),"merchant","merchant","prepareOrder",m("type","Documents/Preparation Input","key","one","values",m("size",42))),++clock);
      var outer=item(p,parent.document(),"orders");
      check(((List<?>)outer.get("slots")).stream().anyMatch(slot->"/size".equals(o(slot).get("path"))),"Fixture must declare size as a provider data slot");
      var orderSource=exact(p,parent.document(),outer.get("itemPath")+"/prepared");
      var initialized=p.initialize(orderSource);if(!initialized.commits())ClauseGasProbe.diagnose(p,orderSource);
      var order=ok(initialized);
      var initialTermsRef=p.read(order.document(),"/activation/terms/ref");
      check(!Boolean.TRUE.equals(p.read(order.document(),"/activation/active")),"Order must start inactive");
      check(((Number)p.read(order.document(),"/clauseRuntime/revision")).intValue()==1,"Initial clause revision");
      order=apply(p,order.document(),event(order.document(),"seller","merchant","preparePayment",m("type","Documents/Preparation Input","key","payment","values",m("size",42))),++clock);
      var pending=item(p,order.document(),"payment");
      var payment=ok(p.initialize(exact(p,order.document(),pending.get("itemPath")+"/prepared")));
      order=apply(p,order.document(),event(order.document(),"seller","merchant","providePayment",provision(pending,payment.document())),++clock);
      var staged=item(p,order.document(),"payment");check("admission_pending".equals(staged.get("status")),"Expected pending admission: "+staged.get("status"));
      order=apply(p,order.document(),event(order.document(),"seller","merchant","approveAdmission_payment_seller",m("proposalId",staged.get("admissionRef"))),++clock);
      check(Boolean.TRUE.equals(p.read(order.document(),"/process_payment/admission/ledger/history/"+staged.get("admissionRef"))),"Actual owner approval must authorize admission");
      var contracts=o(exact(p,order.document(),"/contracts"));String consent=contracts.keySet().stream().filter(x->x.startsWith("consentAdmission_payment_")).findFirst().orElseThrow();
      String channel=(String)o(contracts.get(consent)).get("channel");
      check(!Boolean.TRUE.equals(p.read(order.document(),"/activation/active")),"Consent must be available before commercial activation");
      check(!o(p.read(order.document(),"/activation/parties")).containsKey("guarantor"),"Approval without participant consent must not admit");
      var values=p.execution().values();
      // Predicate-level stale-token guard; the positive admission below still requires real consent.
      var pendingExact=new Exact.Ref(order.document().blueId());
      var admissionDefinition=values.source(m("type","Documents/Document Preparation Functions"),"definition");
      var library=values.bexData(values.select(admissionDefinition,"/functions"));
      for(boolean stale:List.of(false,true)) {
        var modeled=o(Values.copy(values.literal(pendingExact)));
        AdmissionConsentDispatchConformance.patch(values,pendingExact,modeled,staged.get("itemPath")+"/consents/guarantor","approve");
        if(stale)AdmissionConsentDispatchConformance.patch(values,pendingExact,modeled,"/activation/revision",999);
        var expression=m("functions",library,"constants",m("clauseKey","payment","bindings",m()),"expr",m("$call",m("function","admissionInstallRequest","args",m())));
        var result=p.execution().evaluatePredicate(values.source(modeled),values.source(m()),"input",values.source(expression),10000000);
        check(Boolean.TRUE.equals(o(result.value()).get("ready"))!=stale,"Admission token freshness guard stale="+stale);
        System.out.println("Predicate admission token stale="+stale+" gas="+result.gasUsed());
      }

      order=apply(p,order.document(),event(order.document(),channel,"guarantor",consent,m("admissionRef",staged.get("admissionRef"),"decision","approve")),++clock);
      check(o(p.read(order.document(),"/activation/parties")).containsKey("guarantor"),"Guarantor admitted");
      check(((Number)p.read(order.document(),"/activation/revision")).intValue()==2,"Admission advances activation revision");
      check(((Number)p.read(order.document(),"/clauseRuntime/revision")).intValue()==1,"Admission preserves clause revision");
      check(!Boolean.TRUE.equals(p.read(order.document(),"/activation/active")),"Admission must not commercially activate Order");
      check(o(p.read(order.document(),"/clauseRuntime/initialDocument/clauses/activation/parameters/parties")).keySet().equals(Set.of("seller","customer")),"Frozen original roster must have two parties");
      check(o(p.read(order.document(),"/activation/parties")).keySet().equals(Set.of("seller","customer","guarantor")),"Admission adds a third party to the two-party prepared roster");
      String innerPath=staged.get("itemPath").toString(), outerPath=outer.get("itemPath").toString();
      check("approve".equals(p.read(order.document(),innerPath+"/consents/guarantor")),"Actual consent effect required");
      check(((Number)p.read(order.document(),innerPath+"/admittedRevision")).intValue()==2,"Completed admission revision");
      check(!o(exact(p,order.document(),innerPath)).containsKey("admittedTerms"),"Admission must not produce a provision witness");
      var baselineOrder=new Exact.Ref(order.document().blueId());
      for(String variant:List.of("absent","plausible","tampered")) {
        var request=provision(outer,order.document());
        if(!variant.equals("absent")) {
          var changed=o(Values.copy(values.literal(baselineOrder)));
          var witness=m("previousRef",initialTermsRef,"previousRevision",1,
              "ref",p.read(order.document(),"/activation/terms/ref"),"revision",2,
              "candidateOrigin",staged.get("candidateOrigin"),"requirementRef",staged.get("requirementRef"),"admissionRef",staged.get("admissionRef"));
          if(variant.equals("tampered"))witness.put("candidateOrigin","foreign");
          AdmissionConsentDispatchConformance.patch(values,baselineOrder,changed,innerPath+"/admittedTerms",witness);
          request.put("document",m("blueId",NativeRuntime.identity(values.source(changed))));
        }
        rejected(p,parent.document(),event(parent.document(),"merchant","merchant","provideOrder",request),++clock,"PREPARATION_UNDECLARED_PARTY");
        System.out.println("Added-party witness variant rejected: "+variant);
      }
      // A separate candidate retains the originally prepared roster and ordinary commercial gate.
      order=ok(p.initialize(orderSource));
      check(o(p.read(order.document(),"/activation/parties")).keySet().equals(Set.of("seller","customer")),"Ordinary roster");
      var ordinaryExact=new Exact.Ref(order.document().blueId());
      for(var mutation:Map.of("party","/activation/parties/seller/lead/channel/event/source",
          "source","/contracts/initialized/document/name","policy","/clauses/activation/parameters/required",
          "slot","/size").entrySet()) {
        var changed=o(Values.copy(values.literal(ordinaryExact)));
        Object replacement=mutation.getKey().equals("policy")?List.of():mutation.getKey().equals("slot")?41:"foreign";
        AdmissionConsentDispatchConformance.patch(values,ordinaryExact,changed,mutation.getValue(),replacement);
        var request=provision(outer,order.document());request.put("document",m("blueId",NativeRuntime.identity(values.source(changed))));
        String expected=switch(mutation.getKey()) {
          case "party" -> "PARTY_PRIMARY_CHANNEL_MISMATCH";
          case "source" -> "PREPARATION_UNREVIEWED_SOURCE";
          case "policy" -> "PREPARATION_EFFECTIVE_POLICY_CHANGED";
          default -> "PREPARATION_PROVIDER_DATA_CHANGED";
        };
        rejected(p,parent.document(),event(parent.document(),"merchant","merchant","provideOrder",request),++clock,expected);
      }
      var wrongRequirement=provision(outer,order.document());wrongRequirement.put("requirementRef","foreign");
      rejected(p,parent.document(),event(parent.document(),"merchant","merchant","provideOrder",wrongRequirement),++clock,"PREPARATION_WRONG_REQUIREMENT");
      var inactiveRequest=provision(outer,order.document());
      parent=apply(p,parent.document(),event(parent.document(),"merchant","merchant","provideOrder",inactiveRequest),++clock);
      check("awaiting_activation".equals(p.read(parent.document(),outerPath+"/status")),"Generic profile preserves commercial activation gate");
      String stagedIdentity=NativeRuntime.identity(values.exact(values.select(new Exact.Ref(parent.document().blueId()),outerPath)));
      parent=apply(p,parent.document(),event(parent.document(),"merchant","merchant","provideOrder",inactiveRequest),++clock);
      check(p.emitted(parent).isEmpty(),"Inactive retry must not emit duplicate effects");
      check(stagedIdentity.equals(NativeRuntime.identity(values.exact(values.select(new Exact.Ref(parent.document().blueId()),outerPath)))),"Identical inactive provision duplicated or altered obligation");
      order=apply(p,order.document(),event(order.document(),"seller","merchant","approve_seller",m("revision",1)),++clock);
      order=apply(p,order.document(),event(order.document(),"customer","customer","approve_customer",m("revision",1)),++clock);
      check(Boolean.TRUE.equals(p.read(order.document(),"/activation/active")),"Actual commercial approvals required");
      var activeRequest=provision(outer,order.document());
      parent=apply(p,parent.document(),event(parent.document(),"merchant","merchant","provideOrder",activeRequest),++clock);
      check("usable".equals(p.read(parent.document(),outerPath+"/status")),"Approved ordinary Order must be usable");
      String acceptedIdentity=NativeRuntime.identity(values.exact(values.select(new Exact.Ref(parent.document().blueId()),outerPath)));
      parent=apply(p,parent.document(),event(parent.document(),"merchant","merchant","provideOrder",activeRequest),++clock);
      check(p.emitted(parent).isEmpty(),"Accepted retry must not emit duplicate effects");
      check(acceptedIdentity.equals(NativeRuntime.identity(values.exact(values.select(new Exact.Ref(parent.document().blueId()),outerPath)))),"Identical accepted provision duplicated or altered obligation");
      check(((Number)p.read(order.document(),"/activation/revision")).intValue()==1,"Ordinary provision never admits a party");
      System.out.println("PASS native admission without witness, undeclared-party rejection, ordinary provision, commercial gate and retry");
    }
  }
}
