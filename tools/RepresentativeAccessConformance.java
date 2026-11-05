import blue.bex.*;
import blue.contracts.*;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Executes published native access functions; does not replace owner/provider authorization. */
public final class RepresentativeAccessConformance {
  static Map<String,Object> m(Object... a){var r=new LinkedHashMap<String,Object>();for(int i=0;i<a.length;i+=2)r.put((String)a[i],a[i+1]);return r;}
  @SuppressWarnings("unchecked") static Map<String,Object> o(Object x){return (Map<String,Object>)x;}
  static void check(boolean v,String s){if(!v)throw new AssertionError(s);}
  static Object provider(){return m("type","Coordination/Timeline Provider","endpoint","https://provider.example","publicKey","00".repeat(32));}
  static Object timeline(String id){return m("type","Coordination/Signed Timeline","url","https://provider.example/"+id,"publicRead",false,"provider",provider());}
  static Object channel(String id){return m("type","Coordination/Timeline Channel","actor",m("type","Coordination/Actor","id",id),"timeline",timeline(id));}
  static Object access(String id,List<String> keys){return m("type","Coordination/Timeline Access","allowedKeys",keys,"allowedTimelines",List.of(timeline(id)),"contracts",m("provider",m("type","Coordination/Public Timeline Channel","provider",provider(),"url","https://provider.example/access/"+id),"checkpoint",m("entries",m("provider",m("event",m("id","checkpoint-"+id))))));}
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);var bundle=PackageBundle.builder();
    bundle.mount("Activation",BluePackage.open(root.resolve("clause-activation/dist/package.bluepkg")));
    bundle.mount("Coordination",BluePackage.open(root.resolve("blue-coordination/dist/package.bluepkg")));
    bundle.mount("Contracts",BluePackage.open(root.resolve("blue-contracts/dist/package.bluepkg")));
    try(var blue=Blue.builder().packages(bundle.build()).build()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var definition=values.source(m("type","Activation/Activation Functions"),"definition");
      var library=m("functions",values.bexData(values.select(definition,"/functions")));
      var parties=m();var acls=m();var paths=new ArrayList<String>();
      for(String role:List.of("seller","customer")) {
        parties.put(role,m("readerKeys",List.of("11".repeat(32)),"lead",m("channel",channel(role)),"representatives",m("myosAgent",m("channel",channel(role+"__myosAgent"),"readerKeys",List.of("11".repeat(32))))));
        for(String transport:List.of(role,role+"__myosAgent")){acls.put(transport,access(transport,List.of("11".repeat(32))));paths.add("/timelineAccess/"+transport);}
      }
      var doc=m("activation",m("revision",1,"active",false,"approved",m(),"parties",parties,"accessPaths",paths),"timelineAccess",acls);
      var event=m("admissionRef","admission-1","expectedRevision",1,"itemPath","/process_payment/entries/single","clauseKey","payment","parties",m("guarantor",m("readerKeys",List.of("22".repeat(32)),"lead",m("channel",m("type","Contracts/External Channel","event",m("source","guarantor"))))));
      var stale=m();stale.putAll(event);stale.put("expectedRevision",2);
      check(run(values,library,doc,stale,"requestPartyAddition").changeset().isEmpty(),"Stale revision must not request access");
      // Caller metadata cannot select another transport; enumeration comes solely from the roster.
      event.put("transport","foreign");event.put("channel",channel("foreign"));event.put("accessPath","/timelineAccess/foreign");
      var representatives=m();
      for(String role:parties.keySet())representatives.put(role,o(parties.get(role)).remove("representatives"));
      var leadOnly=run(values,library,doc,event,"requestPartyAddition");
      check(o(o(o(leadOnly.changeset().getLast()).get("val")).get("requests")).keySet().equals(Set.of("seller","customer")),"Existing lead-only roster keeps exact keys");
      for(String role:parties.keySet())o(parties.get(role)).put("representatives",representatives.get(role));
      var result=run(values,library,doc,event,"requestPartyAddition");
      var record=o(o(result.changeset().getLast()).get("val"));var requests=o(record.get("requests"));
      check(requests.keySet().equals(Set.of("seller","seller__myosAgent","customer","customer__myosAgent")),"Missing exact representative requests: "+requests.keySet());
      for(String transport:requests.keySet()){
        var request=o(requests.get(transport));String role=transport.split("__")[0];
        check(role.equals(request.get("party")),"Parent role must remain stable");
        check(("/timelineAccess/"+transport).equals(request.get("accessPath")),"Exact transport ACL");
        Object expected=values.bexData(values.source(channel(transport)));
        check(expected.equals(request.get("channel")),"Exact declared channel");
        String checkpoint=NativeRuntime.identity(values.source(m("id","checkpoint-"+transport)));
        check(checkpoint.equals(request.get("expectedAccessEntry")),"Own checkpoint, not lead checkpoint");
        var expectedLead=m("admissionRef","admission-1","expectedRevision",1,"itemPath","/process_payment/entries/single","clauseKey","payment","party",role,"channel",expected,"readerGroups",m("seller",List.of("11".repeat(32)),"seller__myosAgent",List.of("11".repeat(32)),"customer",List.of("11".repeat(32)),"customer__myosAgent",List.of("11".repeat(32)),"guarantor",List.of("22".repeat(32))),"ready",false,"accessPath","/timelineAccess/"+transport,"expectedAccessEntry",checkpoint);
        check(WireData.write(expectedLead).equals(WireData.write(request)),"Existing lead fields or shared approved scope changed: "+transport);
      }
      o(doc.get("activation")).put("accessRequests",m("admission-1",record));
      for(String role:List.of("seller","customer"))acls.put(role,access(role,List.of("11".repeat(32),"22".repeat(32))));
      check(run(values,library,doc,m(),"refreshAccessRequests").changeset().isEmpty(),"Lead-only access cannot complete parent readiness");
      for(String role:List.of("seller","customer"))acls.put(role+"__myosAgent",access(role+"__myosAgent",List.of("11".repeat(32),"22".repeat(32))));
      acls.put("seller__myosAgent",access("foreign",List.of("11".repeat(32),"22".repeat(32))));
      var foreign=run(values,library,doc,m(),"refreshAccessRequests");
      check(foreign.changeset().size()==2,"Foreign representative timeline must not satisfy seller coverage");
      for(Object change:foreign.changeset())check(o(change).get("path").toString().contains("/requests/customer"),"Only correctly covered customer can become ready");
      acls.put("seller__myosAgent",access("seller__myosAgent",List.of("11".repeat(32),"22".repeat(32))));
      var refreshed=run(values,library,doc,m(),"refreshAccessRequests");
      check(refreshed.changeset().size()==4,"Every exact request must become ready only after full parent coverage");
      for(Object change:refreshed.changeset())check(Boolean.TRUE.equals(o(change).get("val")),"Ready value");
      check(run(values,library,doc,event,"requestPartyAddition").changeset().isEmpty(),"Same admission replay must not duplicate requests");
      check(Boolean.FALSE.equals(o(doc.get("activation")).get("active"))&&o(o(doc.get("activation")).get("approved")).isEmpty(),"No commercial activation/approval");
      System.out.println("PASS exact four transports, unchanged lead shape, per-ACL checkpoint, full-role readiness and replay");
    }
  }
  static Engine.Result run(ContractsExecution.Values values,Map<String,Object> library,Map<String,Object> doc,Map<String,Object> event,String function){
    var bex=new Bex(BexProfile.current());var program=bex.compile(m("do",List.of(m("$return",m("$call",m("function",function,"args",m()))))),library,null);
    var context=new BexContext(values.bexData(values.source(doc)),values.bexData(values.source(event)),m(),Values.UNDEFINED,m(),m(),"/",null,
      (actual,pattern)->values.matches(actual,values.source(pattern,"definition")),
      (actual,gas)->NativeRuntime.identity(values.source(Values.blueValue(actual))));
    return bex.execute(program,context,10000000);
  }
}
