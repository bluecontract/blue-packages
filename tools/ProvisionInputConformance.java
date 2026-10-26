import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Actual generated provision actions must distinguish absent optional fields from inherited values. */
public final class ProvisionInputConformance {
  static Map<String,Object> m(Object... p){var out=new LinkedHashMap<String,Object>();for(int i=0;i<p.length;i+=2)out.put((String)p[i],p[i+1]);return out;}
  static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
  @SuppressWarnings("unchecked") static Map<String,Object> obj(Object value){return (Map<String,Object>)value;}
  static Object event(Contracts.Document document,String operation,Object request){return m("source","owner","operation",m("type","Contracts/Operation Request","channel","owner","operation",operation,"document",m("blueId",document.blueId()),"request",request,"requireExactDocumentVersion",true));}
  static Contracts.Result applied(Contracts.Result result){require(result.status().equals("APPLIED"),result.status()+" "+result.observations());return result;}
  static Map<String,Object> source(){
    var channel=m("type","Contracts/External Channel","event",m("source","owner"));
    var party=m("type","Parties/Party","lead",m("channel",channel),"readerKeys",List.of("reader-owner"));
    var activation=m("type","Activation/Activation Clause","parameters",m("parties",m("owner",party),"required",List.of("owner")));
    var template=m("name","Independent candidate","type","DocumentsDomain/Document with Clauses","clauses",m("activation",activation),"result","unchanged");
    var work=m("type","Documents/Document Clause","parameters",m("obtain","provide","suppliedBy","owner","template",template),"bindings",m("parties",m("owner","owner"),"document","/work","prepare",m("prepareWork",m("on","workflow","party","owner")),"provide",m("provideWork",m("on","workflow","party","owner"))));
    return m("name","Provision receiver","type","Agreements/Agreement with Clauses","contracts",m("owner",channel),"clauses",m("activation",activation,"work",work));
  }
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    for(String mode:List.of("omitted","explicit","inherited","reference","inherited-wrong-key","wrong-request","wrong-requirement","changed-terms"))try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var p=runtime.processor(packages.language());var values=p.execution().values();
      var host=applied(p.initialize(source()));host=applied(p.process(host.document(),event(host.document(),"approve_owner",m("revision",1)),1));
      host=applied(p.process(host.document(),event(host.document(),"prepareWork",m()),2));
      var pending=obj(obj(p.read(host.document(),"/process_work/entries")).values().iterator().next());
      var childSource=obj(AttachmentDocuments.source(p,host.document(),pending.get("itemPath")+"/prepared"));
      if(mode.equals("changed-terms"))childSource.put("result","substituted");
      var child=applied(p.initialize(childSource));
      child=applied(p.process(child.document(),event(child.document(),"approve_owner",m("revision",1)),3));
      var request=m("type","Documents/Provision Input","inResponseTo",pending.get("requestId"),"requirementRef",pending.get("requirementRef"),"document",m("blueId",child.document().blueId()));
      if(mode.equals("explicit"))request.put("key","single");
      if(mode.equals("wrong-request"))request.put("inResponseTo","other-request");
      if(mode.equals("wrong-requirement"))request.put("requirementRef",m("blueId",child.document().blueId()));
      if(mode.startsWith("inherited"))request.put("type",m("type","Documents/Provision Input","key",mode.endsWith("wrong-key")?"different":"single"));
      Object input=mode.equals("reference")?m("blueId",NativeRuntime.identity(values.source(request))):request;
      String before=WireData.write(input);var result=p.process(host.document(),event(host.document(),"provideWork",input),4);
      if(Set.of("inherited-wrong-key","wrong-request","wrong-requirement","changed-terms").contains(mode)) {
        require(!result.commits(),"Invalid provision must not commit: "+mode);
        require(host.document().identity().equals(result.document().identity())&&p.emitted(result).isEmpty(),"Rejected key leaves document/effects untouched");
      } else {
        applied(result);var selected=values.select(new Exact.Ref(result.document().blueId()),"/work");
        require(selected!=null&&child.document().blueId().equals(NativeRuntime.identity(values.exact(selected))),"Exact candidate publication selected: "+mode);
        require("usable".equals(obj(obj(p.read(result.document(),"/process_work/entries")).values().iterator().next()).get("status")),"Provision usable: "+mode);
      }
      require(before.equals(WireData.write(input)),"Request unchanged: "+mode);System.out.println("PASS generated provision "+mode);
    }
  }
}
