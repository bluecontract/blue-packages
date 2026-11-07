import blue.contracts.*;import blue.language.next.*;import blue.bex.Values;import java.nio.file.*;import java.util.*;
/** Exact retained native policy regression; no hosted state or authority is fabricated. */
public final class AdmissionConsentDispatchConformance {
 static Map<String,Object> m(Object... x){var r=new LinkedHashMap<String,Object>();for(int i=0;i<x.length;i+=2)r.put((String)x[i],x[i+1]);return r;}
 @SuppressWarnings("unchecked") static Map<String,Object> o(Object x){return (Map<String,Object>)x;}
 static void calls(Object x,Set<String> names){if(x instanceof Map<?,?> map){if(map.get("$call") instanceof Map<?,?> c&&c.get("function") instanceof String n)names.add(n);map.forEach((k,v)->{if(!k.equals("$literal"))calls(v,names);});}else if(x instanceof List<?> l)l.forEach(v->calls(v,names));}
 static Object materialize(ContractsExecution.Values v,Object x,boolean literal){if(x instanceof Map<?,?> map){var out=m();map.forEach((k,y)->out.put(k.toString(),materialize(v,y,literal)));return out;}if(x instanceof List<?> list)return list.stream().map(y->materialize(v,y,literal)).toList();if(x==null||x instanceof String||x instanceof Number||x instanceof Boolean)return x;if(x instanceof Values.HostValue h){if(literal)return h.blueOutput();if(h.kind().equals("object")){var out=m();for(String key:h.keys())out.put(key,materialize(v,h.get(key),false));return out;}if(h.kind().equals("list")){var out=new ArrayList<Object>();for(int i=0;i<h.size();i++)out.add(materialize(v,h.get(i),false));return out;}return h.blueOutput();}throw new IllegalArgumentException(x.getClass().toString());}
 static Map<String,Object> policySource(Object x){if(x instanceof Map<?,?> map){if(map.get("constants") instanceof Map<?,?> c&&c.containsKey("preOperations")&&map.containsKey("do"))return o(x);for(Object child:map.values()){var r=policySource(child);if(r!=null)return r;}}else if(x instanceof List<?> l)for(Object child:l){var r=policySource(child);if(r!=null)return r;}return null;}
  @SuppressWarnings("unchecked")
  static void patch(ContractsExecution.Values values,Exact original,Map<String,Object> target,String path,Object value){
    String[] parts=path.substring(1).split("/");Object current=target;String prefix="";
    for(int i=0;i<parts.length-1;i++){
      String key=parts[i];prefix+="/"+key;
      Object child=current instanceof List<?> list?list.get(Integer.parseInt(key)):o(current).get(key);
      if(child==null || child instanceof Map<?,?> map&&map.keySet().equals(Set.of("blueId"))){
        child=Values.copy(values.literal(values.exact(values.select(original,prefix))));
        if(current instanceof List<?> list)((List<Object>)list).set(Integer.parseInt(key),child);else o(current).put(key,child);
      }
      current=child;
    }
    String key=parts[parts.length-1];if(current instanceof List<?> list)((List<Object>)list).set(Integer.parseInt(key),value);else o(current).put(key,value);
  }
 public static void main(String[] a)throws Exception{
  var root=Path.of(a[0]);var capture=o(WireData.json(Files.readString(Path.of(a[1]))));var responses=o(capture.get("responses"));
  try(var blue=Blue.builder().packages(PackageBundle.builder().mount("Clauses",BluePackage.open(root.resolve("blue-clauses/dist/package.bluepkg"))).build()).nodeProvider(id->responses.containsKey(id)?NodeProviderResult.found(ContentRecord.fromResponse(o(responses.get(id)))):NodeProviderResult.notFound()).build()){
   var ex=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution();var v=ex.values();var host=new Exact.Ref((String)capture.get("publication"));
   var operations=(List<?>)o(capture.get("description")).get("operations");var operation=operations.stream().map(AdmissionConsentDispatchConformance::o).filter(x->x.get("name").toString().startsWith("consentAdmission_payment_")).findFirst().orElseThrow();String op=(String)operation.get("name"),channel=(String)operation.get("channel");
   String policy="/contracts/activationDispatch";var functions=m();var body=o(v.bexData(v.select(host,policy)));var source=policySource(WireData.parse(Files.readString(root.resolve("clause-activation/types/plan.blue")),"yaml"));body.put("do",o(source.get("do")).get("$literal"));
   var pending=new LinkedHashSet<String>();calls(body.get("do"),pending);while(!pending.isEmpty()){String fn=pending.iterator().next();pending.remove(fn);if(functions.containsKey(fn))continue;Object f=v.bexData(v.select(host,policy+"/definition/functions/"+fn));functions.put(fn,f);calls(f,pending);}body.remove("definition");body.remove("type");body.put("functions",functions);
   String step="/contracts/admissionUpdate_payment_processHandler/steps/2";
   var installFunctions=m();var pendingInstall=new LinkedHashSet<String>();pendingInstall.add("installAdmissionConsentOperations");
   while(!pendingInstall.isEmpty()){String fn=pendingInstall.iterator().next();pendingInstall.remove(fn);if(installFunctions.containsKey(fn))continue;Object selected=v.select(host,step+"/definition/functions/"+fn);if(selected==null)throw new AssertionError("Missing function "+fn+" at "+step);Object f=v.bexData(selected);installFunctions.put(fn,f);calls(f,pendingInstall);}
   var authored=o(o(WireData.parse(Files.readString(root.resolve("clause-documents/types/admission-functions.blue")),"yaml")).get("functions"));
   var originalDo=new ArrayList<Object>((List<?>)o(installFunctions.get("installAdmissionConsentOperations")).get("do"));
   var revisedDo=(List<?>)o(authored.get("installAdmissionConsentOperations")).get("do");
   var loop=o(o(originalDo.get(2)).get("$forEach"));var loopDo=new ArrayList<Object>((List<?>)loop.get("do"));
   var revisedLoop=(List<?>)o(o(revisedDo.get(4)).get("$forEach")).get("do");loopDo.addAll(revisedLoop.subList(revisedLoop.size()-3,revisedLoop.size()));loop.put("do",loopDo);
   originalDo.add(2,revisedDo.get(2));originalDo.add(3,revisedDo.get(3));o(installFunctions.get("installAdmissionConsentOperations")).put("do",originalDo);
   String itemPath=(String)v.bexData(v.select(host,"/contracts/"+op+"/steps/0/constants/itemPath"));
   var installer=m("functions",installFunctions,"constants",v.bexData(v.select(host,step+"/constants")),"do",List.of(m("$return",m("$call",m("function","installAdmissionConsentOperations","args",m("item",m("$binding","item")))))));
   var installed=ex.evaluatePredicate(host,v.exact(v.select(host,itemPath)),"item",v.source(installer),10000000);
   System.out.println("Installer result="+installed.value()+" gas="+installed.gasUsed()+" changes="+installed.changeset());
   if(installed.changeset().size()!=2)throw new AssertionError("Expected registry root and exact operation registration");
   var target=o(Values.copy(v.literal(host)));for(Object raw:installed.changeset()){var change=o(raw);patch(v,host,target,(String)change.get("path"),Values.copy(change.get("val")));}var registered=v.source(target);
   var dispatch=v.source(m("kind","EXTERNAL","operation",op,"channel",channel));var result=ex.evaluatePredicate(registered,dispatch,"dispatch",v.source(body),10000000);System.out.println("Exact owned consent policy result="+result.value()+" gas="+result.gasUsed());
   if(!Boolean.TRUE.equals(o(result.value()).get("allowed")))throw new AssertionError("Current exact admission consent must be allowed before commercial activation");
   var planHost=o(Values.copy(target));patch(v,registered,planHost,"/clauseRuntime/work",m("initializing",false,"candidate",m("activation",v.literal(v.exact(v.select(host,"/clauses/activation"))))));var planning=v.source(planHost);
   String planDefinition="/clauses/activation/type/hookDefinition/type";var planFunctions=m();var planNames=new LinkedHashSet<String>();planNames.add("plan");
   while(!planNames.isEmpty()){String fn=planNames.iterator().next();planNames.remove(fn);if(planFunctions.containsKey(fn))continue;Object selected=v.select(host,planDefinition+"/functions/"+fn);if(selected==null)throw new AssertionError("Missing planner function "+fn);Object f=v.bexData(selected);planFunctions.put(fn,f);calls(f,planNames);}
   var planPolicy=policySource(planFunctions.get("plan"));planPolicy.put("do",source.get("do"));
   var planExpr=m("functions",planFunctions,"constants",m("clauseKey","activation"),"do",List.of(m("$return",m("$call",m("function","plan","args",m())))));
   var planned=ex.evaluatePredicate(planning,v.source(m()),"input",v.source(planExpr),10000000);System.out.println("PASS native plan gas="+planned.gasUsed());
   var commit=o(WireData.parse(Files.readString(root.resolve("blue-clauses/types/commit-amendment-step.blue")),"yaml"));Object adoption=null;
   for(Object statement:(List<?>)commit.get("do")){if(o(statement).get("$forEach") instanceof Map<?,?> each&&"ck".equals(each.get("item"))&&WireData.write(each).contains("STATE_OWNER_COLLISION")){adoption=Values.copy(statement);var stateLoop=o(o(adoption).get("$forEach"));stateLoop.put("do",new ArrayList<>(((List<?>)stateLoop.get("do")).subList(0,2)));break;}}
   if(adoption==null)throw new AssertionError("Maintained state adoption loop missing");
   planFunctions.put("reject",v.bexData(v.select(v.source(m("type","Clauses/Commit Amendment Step")),"/functions/reject")));
   var adoptionExpr=m("functions",planFunctions,"constants",m("clauseKey","activation"),"do",List.of(m("$let",m("name","plans","expr",m("activation",m("$call",m("function","plan","args",m()))))),m("$let",m("name","stateWrites","expr",m())),m("$let",m("name","stateClaims","expr",m())),m("$let",m("name","candidate","expr",m("$document","/clauseRuntime/work/candidate"))),adoption,m("$return",m("$var","stateWrites"))));
   var adopted=ex.evaluatePredicate(planning,v.source(m()),"plans",v.source(adoptionExpr),10000000);
   if(!o(adopted.value()).isEmpty()||!adopted.changeset().isEmpty())throw new AssertionError("Replan overwrote adopted native state: "+adopted.changeset());System.out.println("PASS maintained Clauses state adoption gas="+adopted.gasUsed());
   var stateExpr=m("functions",planFunctions,"constants",m("clauseKey","activation"),"do",List.of(m("$return",m("$call",m("function","computeState","args",m("state",m("$document","/activation")))))));
   var recomputed=ex.evaluatePredicate(planning,v.source(m()),"input",v.source(stateExpr),10000000);var state=o(materialize(v,recomputed.value(),false));
   if(!Boolean.FALSE.equals(state.get("active"))||Boolean.TRUE.equals(o(state.get("approved")).get("seller"))||!Objects.equals(state.get("admissionConsentOperations"),v.bexData(v.select(registered,"/activation/admissionConsentOperations"))))throw new AssertionError("Replan changed approval/registration");
   var replanned=o(Values.copy(planHost));patch(v,planning,replanned,"/activation",materialize(v,recomputed.value(),true));
   var emitted=o(materialize(v,o(o(o(planned.value()).get("contracts")).get("activationDispatch")).get("contract"),false));emitted.remove("type");emitted.remove("definition");emitted.put("functions",functions);
   var rechecked=ex.evaluatePredicate(v.source(replanned),dispatch,"dispatch",v.source(emitted),10000000);if(!Boolean.TRUE.equals(o(rechecked.value()).get("allowed")))throw new AssertionError("Emitted replanned policy denied consent");System.out.println("PASS replan/adoption/computeState/emitted-policy consent gas="+rechecked.gasUsed());
   String registry="/activation/admissionConsentOperations/"+op;
   var mutations=m("stale revision",List.of("/activation/revision",999),"closed",List.of("/activation/closed",true),"access unavailable",List.of("/activation/accessReady",false),"stale item",List.of(itemPath+"/status","ready"),"stale ref",List.of(itemPath+"/admissionRef","foreign"),"foreign party",List.of(registry+"/party","seller"),"foreign op identity",List.of(registry+"/operationId","foreign"),"foreign channel identity",List.of(registry+"/channelId","foreign"),"foreign channel",List.of(registry+"/channel","seller"),"replaced operation",List.of("/contracts/"+op,m()),"replaced channel",List.of("/contracts/"+channel,m()),"missing registration",List.of("/activation/admissionConsentOperations",m()));
   for(var mutation:mutations.entrySet()){var variant=o(Values.copy(target));var edit=(List<?>)mutation.getValue();patch(v,registered,variant,(String)edit.get(0),edit.get(1));var denied=ex.evaluatePredicate(v.source(variant),dispatch,"dispatch",v.source(body),10000000);if(Boolean.TRUE.equals(o(denied.value()).get("allowed")))throw new AssertionError("Accepted "+mutation.getKey());System.out.println("DENIED "+mutation.getKey()+" gas="+denied.gasUsed());}
   var replay=ex.evaluatePredicate(registered,v.exact(v.select(registered,itemPath)),"item",v.source(installer),10000000);if(!Boolean.TRUE.equals(replay.value())||!replay.changeset().isEmpty())throw new AssertionError("Registration replay not idempotent");System.out.println("PASS idempotent installer gas="+replay.gasUsed());
   String ref=(String)v.bexData(v.select(host,itemPath+"/admissionRef"));
   for(String path:List.of("/process_payment/admission/ledger/history/"+ref,"/process_payment/admission/grants/"+ref)){var variant=o(Values.copy(v.literal(host)));patch(v,host,variant,path,false);var denied=ex.evaluatePredicate(v.source(variant),v.exact(v.select(host,itemPath)),"item",v.source(installer),10000000);if(!Boolean.FALSE.equals(denied.value())||!denied.changeset().isEmpty())throw new AssertionError("Unapproved registration "+path);System.out.println("DENIED unapproved installer "+path);}

  }
 }
}
