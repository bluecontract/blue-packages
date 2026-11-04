import blue.bex.*;
import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Actual generated dispatch policy; authentic timer ticket delivery is qualified by Core. */
public final class EarlyActivationTimerConformance {
  static Map<String,Object> m(Object... v){return OperationInputConformance.m(v);}
  @SuppressWarnings("unchecked") static Map<String,Object> obj(Object v){return (Map<String,Object>)v;}
  static void require(boolean b,String s){OperationInputConformance.require(b,s);}
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    for(boolean selected:List.of(false,true))try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var p=runtime.processor(packages.language());var channel=m("type","Contracts/External Channel","event",m("source","merchant"));
      var source=m("name","Timer policy","type","Agreements/Agreement with Clauses","contracts",m("merchant",channel),"clauses",m("activation",m("type","Activation/Activation Clause","parameters",m("parties",m("merchant",m("type","Parties/Party","lead",m("channel",channel),"readerKeys",List.of("merchant-reader"))),"required",List.of("merchant")))));
      String clock="cx.wakeup.ping.once_source";
      obj(source.get("clauses")).put("wakeup",m("type",m("type","Connections/Connected Clause","actions",m("ping",m("do",List.of(m("$return",m()))))),"bindings",m("ping",m("once",m("on","timer","timestamp",0,"once",true)))));
      var parameters=obj(obj(obj(source.get("clauses")).get("activation")).get("parameters"));
      if(selected)parameters.put("preActivationTimerChannels",List.of(clock));
      var initialized=p.initialize(source);require(initialized.commits(),"Initialize: "+initialized.observations());
      var policy=obj(AttachmentDocuments.source(p,initialized.document(),"/contracts/activationDispatch"));
      var values=p.execution().values();var nativeRuntime=new NativeRuntime(packages.language());
      var definition=values.head(values.source(policy.get("definition"),"definition"));
      var library=m();for(String key:List.of("constants","functions")) {var v=NativeRuntime.child(definition,key);if(v!=null)library.put(key,values.bexData(v));}
      var policyNode=values.head(values.source(policy,"definition"));
      var policySource=m();for(String key:List.of("constants","do")){var v=NativeRuntime.child(policyNode,key);if(v!=null)policySource.put(key,values.bexData(v));}
      var bex=new Bex(BexProfile.current());var program=bex.compile(policySource,library,null);
      for(String scenario:List.of("timer","unlisted","wrong-type","unavailable","closed","non-external")) {
        var document=m("activation",new LinkedHashMap<>(obj(AttachmentDocuments.source(p,initialized.document(),"/activation"))),"contracts",m(clock,AttachmentDocuments.source(p,initialized.document(),"/contracts/"+clock)));
        require(document.get("activation")!=Values.UNDEFINED,"Native activation exists");
        require(obj(document.get("contracts")).get(clock)!=Values.UNDEFINED,"Native declared Timer channel exists");
        String dispatchChannel=scenario.equals("unlisted")?"other":clock;
        if(scenario.equals("wrong-type"))obj(document.get("contracts")).put(clock,m("type","Contracts/External Channel"));
        if(scenario.equals("unavailable"))obj(document.get("activation")).put("accessReady",false);
        if(scenario.equals("closed"))obj(document.get("activation")).put("closed",true);
        var bindings=m("dispatch",m("kind",scenario.equals("non-external")?"TRIGGERED":"EXTERNAL","channel",dispatchChannel,"operation",""));
        var context=new BexContext(document,m(),m(),Values.UNDEFINED,m(),bindings,"/",null,(a,b)->values.matches(values.source(a),values.source(b,"definition")),(a,g)->NativeRuntime.identity(values.source(a)));
        var result=bex.execute(program,context,1000000);
        require(Boolean.TRUE.equals(obj(result.value()).get("allowed"))==(selected&&scenario.equals("timer")),"Timer policy "+selected+"/"+scenario+": "+result.value());
      }
    }
    System.out.println("PASS 12 generated timer policy cases; default/unlisted/wrong-type/access/closed/non-external denied. Core owns authentic delivery proof.");
  }
}
