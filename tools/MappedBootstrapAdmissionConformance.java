import blue.contracts.*;
import blue.bex.Values;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Evaluates candidate staging against explicitly supplied retained native evidence. */
public final class MappedBootstrapAdmissionConformance {
  static Map<String,Object> m(Object... x){var r=new LinkedHashMap<String,Object>();for(int i=0;i<x.length;i+=2)r.put((String)x[i],x[i+1]);return r;}
  @SuppressWarnings("unchecked") static Map<String,Object> obj(Object x){return (Map<String,Object>)x;}
  static void calls(Object x,Set<String> names){if(x instanceof Map<?,?> map){if(map.get("$call") instanceof Map<?,?> c && c.get("function") instanceof String n)names.add(n);map.values().forEach(v->calls(v,names));}else if(x instanceof List<?> list)list.forEach(v->calls(v,names));}
  @SuppressWarnings("unchecked")
  static void patch(ContractsExecution.Values values,Exact original,Map<String,Object> target,String path,Object value){
    String[] parts=path.substring(1).split("/");Object current=target;String prefix="";
    for(int i=0;i<parts.length-1;i++){
      String key=parts[i];prefix+="/"+key;
      Object child=current instanceof List<?> list?list.get(Integer.parseInt(key)):obj(current).get(key);
      if(child==null || child instanceof Map<?,?> map&&map.keySet().equals(Set.of("blueId"))){
        child=Values.copy(values.literal(values.exact(values.select(original,prefix))));
        if(current instanceof List<?> list)((List<Object>)list).set(Integer.parseInt(key),child);else obj(current).put(key,child);
      }
      current=child;
    }
    String key=parts[parts.length-1];if(current instanceof List<?> list)((List<Object>)list).set(Integer.parseInt(key),value);else obj(current).put(key,value);
  }
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]), captures=Path.of(args[1]);var responses=m();var caps=m();
    for(String name:List.of("consent-observation","payment-initialized","after-prepare")){
      var cap=obj(WireData.json(Files.readString(captures.resolve("upstream-standard-admission-"+name+".json"))));caps.put(name,cap);responses.putAll(obj(cap.get("responses")));
    }
    var documents=BluePackage.open(root.resolve("clause-documents/dist/package.bluepkg"));
    try(var blue=Blue.builder().packages(PackageBundle.builder().mount("Documents",documents).build()).nodeProvider(id->responses.containsKey(id)?NodeProviderResult.found(ContentRecord.fromResponse(obj(responses.get(id)))):NodeProviderResult.notFound()).build()){
      var execution=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution();var v=execution.values();
      var host=new Exact.Ref((String)obj(caps.get("consent-observation")).get("publication"));
      var prepared=new Exact.Ref((String)obj(caps.get("after-prepare")).get("publication"));
      String item="/process_payment/entries/BEBjgocEv82EQ16WxjrHRs9oVwDMzxS89tzEuJdLwqDY", step="/contracts/providePayment/steps/0";
      var candidate=v.exact(v.select(host,item+"/candidateRef"));
      var sourceFunctions=obj(obj(WireData.parse(Files.readString(root.resolve("clause-documents/types/admission-functions.blue")),"yaml")).get("functions"));
      if(args.length>2&&args[2].equals("published")){
        var definition=new Exact.Ref(documents.exportId("Document Preparation Functions"));
        for(String name:List.of("candidateStage","mappedBootstrapPartyCovered"))sourceFunctions.put(name,v.bexData(v.select(definition,"/functions/"+name)));
      }
      var overrides=obj(v.bexData(v.select(host,step+"/functions")));var functions=m();var pending=new LinkedHashSet<String>();pending.add("candidateStage");
      while(!pending.isEmpty()){
        String name=pending.iterator().next();pending.remove(name);if(functions.containsKey(name))continue;
        Object body=sourceFunctions.containsKey(name)?sourceFunctions.get(name):v.bexData(v.select(host,step+(overrides.containsKey(name)?"/functions/":"/definition/functions/")+name));
        if(!(body instanceof Map))throw new AssertionError("Missing function "+name);functions.put(name,body);calls(body,pending);
      }
      var binding=v.source(m("item",v.literal(v.exact(v.select(prepared,item))),"candidate",m("blueId",NativeRuntime.identity(candidate))));
      var expression=m("functions",functions,"constants",v.bexData(v.select(host,step+"/constants")),"expr",m("$call",m("function","candidateStage","args",m("checked",m("item",m("$binding","input/item"),"candidate",m("$binding","input/candidate"),"origin",m("$document",item+"/candidateOrigin"))))));
      var result=execution.evaluatePredicate(host,binding,"input",v.source(expression),10000000);
      var staged=obj(result.value());var parties=obj(obj(staged.get("admissionToken")).get("parties"));
      System.out.println("Actual native stage parties="+parties.keySet()+" gas="+result.gasUsed());
      if(!parties.keySet().equals(Set.of("guarantor")))throw new AssertionError("Only supplied guarantor requires new host admission");
      if(!result.events().isEmpty()||!result.changeset().isEmpty())throw new AssertionError("Pure staging produced effects");
      var helperExpression=m("constants",expression.get("constants"),"functions",functions,"expr",m("$call",m("function","mappedBootstrapPartyCovered","args",m("item",m("$binding","input/item"),"candidate",m("$binding","input/candidate"),"role","observer","party",m("$binding","input/candidate/activation/parties/observer")))));
      var helper=v.source(helperExpression);
      for(String variant:List.of("valid","changed-parent","ambiguous-parent","supplied","missing-supplied","ambiguous-slot","missing-primary","wrong-kind","wrong-role","wrong-mode","current-actor","current-readers","current-representative","original-actor","original-readers","original-representative")){
        var hostBody=obj(Values.copy(v.literal(host)));var input=obj(Values.copy(v.literal(binding)));
        if(variant.equals("changed-parent"))patch(v,host,hostBody,"/activation/parties/seller/readerKeys",List.of("foreign"));
        if(variant.equals("ambiguous-parent"))patch(v,host,hostBody,"/activation/parties/duplicate",v.literal(v.exact(v.select(host,"/activation/parties/seller"))));
        if(variant.equals("supplied"))patch(v,binding,input,"/item/slots/1/supplied",true);
        if(variant.equals("missing-supplied")){patch(v,binding,input,"/item/slots/1/supplied",true);obj(((List<?>)obj(input.get("item")).get("slots")).get(1)).remove("supplied");}
        if(variant.equals("ambiguous-slot")){
          var slots=new ArrayList<Object>((List<?>)v.literal(v.exact(v.select(binding,"/item/slots"))));slots.add(slots.get(1));patch(v,binding,input,"/item/slots",slots);
        }
        if(variant.equals("missing-primary")){
          var slot=obj(v.literal(v.exact(v.select(binding,"/item/slots/1"))));slot.remove("bootstrapPrimary");patch(v,binding,input,"/item/slots/1",slot);
        }
        if(variant.equals("wrong-kind"))patch(v,binding,input,"/item/slots/1/kind","value");
        if(variant.equals("wrong-role"))patch(v,binding,input,"/item/slots/1/role","payee");
        if(variant.equals("wrong-mode"))patch(v,binding,input,"/item/prepareFor","inherited");
        if(variant.startsWith("current-")||variant.startsWith("original-")){
          String prefix=variant.startsWith("current-")?"/candidate/activation/parties/observer":"/candidate/contracts/initialized/document/clauses/activation/parameters/parties/observer";
          String suffix=variant.endsWith("actor")?"/lead/channel/actor":variant.endsWith("readers")?"/readerKeys":"/representatives/myosAgent/representativeId";
          patch(v,binding,input,prefix+suffix,variant.endsWith("readers")?List.of("foreign"):"foreign");
        }
        try{
          var checked=execution.evaluatePredicate(v.source(hostBody),v.source(input),"input",helper,10000000);
          boolean expected=variant.equals("valid");if(!Boolean.valueOf(expected).equals(checked.value()))throw new AssertionError(variant+" unexpectedly "+checked.value());
          if(!checked.events().isEmpty()||!checked.changeset().isEmpty())throw new AssertionError("Effects "+variant);
          System.out.println("PASS "+variant+" covered="+checked.value()+" gas="+checked.gasUsed());
        }catch(blue.bex.BexError failure){
          if(!(variant.startsWith("current-")||variant.startsWith("original-")) || !(failure.getMessage().startsWith("PREPARATION_BOOTSTRAP_")||failure.getMessage().startsWith("PARTY_")))throw failure;
          System.out.println("PASS "+variant+" rejected="+failure.getMessage());
        }
      }
      System.out.println("PASS mapped bootstrap aliases reuse existing host participants without consent or authority effects");
    }
  }
}
