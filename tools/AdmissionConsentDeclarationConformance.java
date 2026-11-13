import blue.contracts.*;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native identity parity against the pre-refactor installer, not the new constructor. */
public final class AdmissionConsentDeclarationConformance {
  static Map<String,Object> m(Object... pairs) {
    var out=new LinkedHashMap<String,Object>();
    for(int i=0;i<pairs.length;i+=2)out.put((String)pairs[i],pairs[i+1]);
    return out;
  }
  @SuppressWarnings("unchecked") static Map<String,Object> o(Object value) { return (Map<String,Object>)value; }
  static Object variable(String name) { return m("$var",name); }
  static Object call(String name,Map<String,Object> args) { return m("$call",m("function",name,"args",args)); }
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);
    var documents=BluePackage.open(root.resolve("clause-documents/dist/package.bluepkg"));
    var old=o(o(WireData.json(Files.readString(root.resolve("tools/fixtures/admission-consent-declarations.json")))).get("expressions"));
    var imports=new LinkedHashMap<String,BluePackage>();
    var config=o(WireData.parse(Files.readString(root.resolve("clause-documents/blue-package.yaml")),"yaml"));
    for(var entry:o(config.get("imports")).entrySet())imports.put(entry.getKey(),BluePackage.open(root.resolve("clause-documents").resolve((String)o(entry.getValue()).get("path")).normalize()));
    imports.put("Documents",documents);
    old=o(o(OperationInputs.publish("Conformance",m("Legacy Consent",m("expressions",old)),imports).get("Legacy Consent")).get("expressions"));
    var bundle=PackageBundle.builder();imports.forEach(bundle::mount);
    try(var blue=Blue.builder().packages(bundle.build()).build()) {
      var execution=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution();
      var v=execution.values();
      var library=new Exact.Ref(documents.exportId("Admission Functions"));
      var helpers=m();
      for(String name:List.of("admissionConsentNames","admissionConsentHandler","admissionConsentRegistration")) {
        Object helper=v.select(library,"/functions/"+name);
        if(helper==null)throw new AssertionError("Missing shared constructor "+name);
        helpers.put(name,v.bexData(helper));
      }
      for(String clause:List.of("payment","orders"))for(String role:List.of("guarantor","partner")) {
        var item=m("itemPath","/process_"+clause+"/entries/one","admissionRef","exact-admission", "admissionToken",m("activationRevision",1));
        var party=m("lead",m("channel",m("type","Contracts/External Channel","timelineId","participant")));
        List<String> identities=new ArrayList<>();
        for(boolean shared:List.of(false,true)) {
          var steps=new ArrayList<Object>();
          for(var entry:m("item",item,"party",party,"role",role).entrySet())steps.add(m("$let",m("name",entry.getKey(),"expr",m("$literal",entry.getValue()))));
          if(shared)steps.add(m("$let",m("name","names","expr",call("admissionConsentNames",m("clauseKey",clause,"admissionRef","exact-admission","role",role)))));
          for(String name:List.of("suffix","channel","operation","channelDeclaration","handler","registration")) {
            Object expression=old.get(name);
            if(shared&&(name.equals("channel")||name.equals("operation")))expression=m("$var",m("name","names","path","/"+name));
            if(shared&&name.equals("handler"))expression=call("admissionConsentHandler",m("channel",variable("channel"),"itemPath",m("$var",m("name","item","path","/itemPath")),"admissionRef",m("$var",m("name","item","path","/admissionRef")),"role",variable("role")));
            if(shared&&name.equals("registration"))expression=call("admissionConsentRegistration",m("handler",variable("handler"),"channel",variable("channel"),"channelDeclaration",variable("channelDeclaration"),"itemPath",m("$var",m("name","item","path","/itemPath")),"admissionRef",m("$var",m("name","item","path","/admissionRef")),"role",variable("role"),"activationRevision",1));
            steps.add(m("$let",m("name",name,"expr",expression)));
          }
          steps.add(m("$return",m("channel",variable("channelDeclaration"),"handler",variable("handler"),"registration",variable("registration"))));
          System.out.println("parity variant="+shared+" clause="+clause+" role="+role);
          var expression=v.source(m("functions",helpers,"constants",m("clauseKey",clause),"do",steps));
          var result=execution.evaluatePredicate(v.source(m()),v.source(m()),"input",expression,10_000_000);
          if(!result.changeset().isEmpty()||!result.events().isEmpty())throw new AssertionError("Constructor has effects");
          identities.add(NativeRuntime.identity(v.source(result.value())));
        }
        if(!identities.getFirst().equals(identities.getLast()))throw new AssertionError("Changed native declaration identity "+clause+"/"+role+": "+identities);
        System.out.println("PASS consent declaration identity "+clause+"/"+role+" "+identities.getFirst());
      }
    }
  }
}
