import blue.bex.*;
import blue.contracts.*;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native blueprint decoder identity checks; Core qualifies actual policy bootstrap. */
public final class EarlyBlueprintReferenceConformance {
  static Map<String,Object> m(Object... values){return OperationInputConformance.m(values);}
  @SuppressWarnings("unchecked") static Map<String,Object> obj(Object value){return (Map<String,Object>)value;}
  static Object find(Object value,String key){
    if(value instanceof Map<?,?> map){if(map.containsKey(key))return map.get(key);for(Object child:map.values()){Object found=find(child,key);if(found!=null)return found;}}
    if(value instanceof List<?> list)for(Object child:list){Object found=find(child,key);if(found!=null)return found;}
    return null;
  }
  public static void main(String[] args)throws Exception{
    Path root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language()){
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var exports=(List<?>)obj(BuildFinalGas.read(root.resolve("blue-time/dist/package.json"))).get("exports");
      String timer=(String)exports.stream().map(EarlyBlueprintReferenceConformance::obj).filter(row->"Time/Timer Request".equals(row.get("alias"))).findFirst().orElseThrow().get("blueId");
      var mandate=BuildFinalGas.read(root.resolve("myos-payment-mandates/types/early-order-seller-payment-policy-mandate.blue"));
      var decoder=find(mandate,"decodeDefinition");
      OperationInputConformance.require(decoder!=null,"Published source decoder exists");
      var programSource=m("do",List.of(m("$return",m("$call",m("function","decodeDefinition","args",m("sectionName","contracts"))))));
      var bex=new Bex(BexProfile.current());var program=bex.compile(programSource,m("functions",m("decodeDefinition",decoder)),null);
      String other=NativeRuntime.identity(values.source(m("name","Different immutable node"),"definition"));
      for(String id:List.of(timer,other)){
        var rows=List.of(m("path","","kind","object"),m("path","/type","kind","reference","scalar",id));
        var document=m("expectedProgram",m("contracts",m("definition",rows)));
        // Storage contains text only, never an embedded reference to a required-input type.
        values.source(document);
        var context=new BexContext(document,m(),m(),Values.UNDEFINED,m(),m(),"/",null,(a,b)->values.matches(values.source(a),values.source(b,"definition")),(a,g)->NativeRuntime.identity(values.source(a,"definition")));
        var decoded=bex.execute(program,context,1000000).value();
        String actual=NativeRuntime.identity(values.source(decoded,"definition"));
        String expected=NativeRuntime.identity(values.source(m("type",m("blueId",id)),"definition"));
        OperationInputConformance.require(actual.equals(expected),"Scalar reference must reconstruct exact identity: "+id);
        if(!id.equals(timer))OperationInputConformance.require(!actual.equals(NativeRuntime.identity(values.source(m("type",m("blueId",timer)),"definition"))),"Changed reference must change canonical identity");
      }
      var replacement=find(mandate,"validReplacement");
      var checkSource=m("do",List.of(m("$return",m("$call",m("function","validReplacement","args",m("sectionName","contracts","patch",m("$document","/patch")))))));
      var check=bex.compile(checkSource,m("functions",m("validReplacement",replacement)),null);
      String prefix="/cx.payment.prepare.accessReady/steps/0/functions/connectionSnapshots/expr/$literal/";
      for(String scenario:List.of("canonical","foreign-path","foreign-section","wrong-kind")){
        var patch=m("kind",scenario.equals("wrong-kind")?"text":"section","section",scenario.equals("foreign-section")?"clauses":"paymentTemplate","path",prefix+(scenario.equals("foreign-path")?"other":"template"),"sourcePath","/unapproved");
        var context=new BexContext(m("patch",patch),m(),m(),Values.UNDEFINED,m(),m(),"/",null,(a,b)->values.matches(values.source(a),values.source(b,"definition")),(a,g)->NativeRuntime.identity(values.source(a,"definition")));
        Object allowed=bex.execute(check,context,1000000).value();
        OperationInputConformance.require(Boolean.TRUE.equals(allowed)==scenario.equals("canonical"),"Access-ready snapshot replacement: "+scenario+"="+allowed);
      }
      var checkpoint=find(mandate,"expectedCheckpointAt");
      var checkpointSource=m("do",List.of(m("$return",m("$call",m("function","expectedCheckpointAt","args",m("checkpointPath","/contracts/checkpoint","channelKind","root"))))));
      var checkpointProgram=bex.compile(checkpointSource,m("functions",m("decodeDefinition",decoder,"expectedCheckpointAt",checkpoint)),null);
      String timerChannel="cx.payment.prepare.preparePayment_source";
      for(String scenario:List.of("canonical","foreign-channel","invalid-timestamp")){
        var actual=m("type",m("blueId","DDu7utWeDaAusXsBXLFXYHKeg9CsnUX9E9q7LgyBznLu"),"entries",m(scenario.equals("foreign-channel")?"cx.foreign.timer":timerChannel,m("event",m("blueId",other),"timestamp",scenario.equals("invalid-timestamp")?"0":0)));
        var document=m("expectedProgram",m("timelineAccess",m("definition",List.of(m("path","","kind","object"),m("path","/seller","kind","object")))));
        var context=new BexContext(document,m(),m(),Values.UNDEFINED,m(),m("targetDocument",m("contracts",m("checkpoint",actual))),"/",null,(a,b)->values.matches(values.source(a),values.source(b,"definition")),(a,g)->NativeRuntime.identity(values.source(a,"definition")));
        Object expected=bex.execute(checkpointProgram,context,1000000).value();
        boolean same=NativeRuntime.identity(values.source(expected,"definition")).equals(NativeRuntime.identity(values.source(actual,"definition")));
        OperationInputConformance.require(same==scenario.equals("canonical"),"Prepare timer checkpoint: "+scenario+"="+same);
      }
      System.out.println("PASS canonical prepare timer checkpoint and foreign channel/invalid timestamp denial");
      System.out.println("PASS exact access-ready snapshot replacement and foreign path/section/kind denial");
      System.out.println("PASS inert scalar reference storage and exact native decoder identity; changed ID cannot preserve original identity");
    }
  }
}
