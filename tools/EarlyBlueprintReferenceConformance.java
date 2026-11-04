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
      System.out.println("PASS inert scalar reference storage and exact native decoder identity; changed ID cannot preserve original identity");
    }
  }
}
