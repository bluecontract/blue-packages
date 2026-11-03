import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Real Agreement preparation with frozen approved payment templates; no hosted/charge claim. */
public final class PaymentMethodChoiceConformance {
  static Map<String,Object> m(Object... values){var result=new LinkedHashMap<String,Object>();for(int i=0;i<values.length;i+=2)result.put((String)values[i],values[i+1]);return result;}
  @SuppressWarnings("unchecked") static Map<String,Object> obj(Object value){return (Map<String,Object>)value;}
  static void require(boolean value,String why){if(!value)throw new AssertionError(why);}
  static Object event(Contracts.Document document,String role,String operation,Object request){return m("source",role,"operation",m("type","Contracts/Operation Request","channel",role,"operation",operation,"document",m("blueId",document.blueId()),"request",request,"requireExactDocumentVersion",true));}
  static Contracts.Result applied(Contracts.Result result){require(result.commits(),result.status()+" "+result.observations());return result;}
  static Map<String,Object> request(String key,String method,Object template){return m("type","Documents/Preparation Input","key",key,"requestId",key,"paymentMethodId",method,"values",template==null?m():m("paymentTemplate",template));}
  static void capture(Path root,String name,Blue language,Contracts processor,Contracts.Document document)throws Exception {
    var snapshot=processor.execution().snapshot(document);var body=snapshot.documents.get(snapshot.root).body;
    var values=processor.execution().values();var resolved=values.literal(body);
    Files.writeString(root.resolve("reports/payment-flow/"+name+".json"),WireData.write(m(
        "format","standalone-native-definition/1","documentId",document.blueId(),"root",resolved,
        "contents",values.nativeRuntime().records(body))));
  }
  public static void main(String[] args)throws Exception{
    Path root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    var fixture=obj(CompositionPackages.yaml(Path.of(args[1])));var source=obj(fixture.get("document"));
    @SuppressWarnings("unchecked") var options=(List<Map<String,Object>>)fixture.get("options");
    var parties=obj(obj(obj(obj(source.get("clauses")).get("activation")).get("parameters")).get("parties"));
    var contracts=m();source.put("contracts",contracts);
    for(var entry:parties.entrySet()) {var role=entry.getKey();var channel=m("type","Contracts/External Channel","event",m("source",role));var party=obj(entry.getValue());party.put("myosAccountId",role);party.put("lead",m("channel",channel));party.put("readerKeys",List.of("reader-"+role));contracts.put(role,channel);}
    try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())){
      var language=packages.language();var p=runtime.processor(language);var host=applied(p.initialize(source));long time=1;
      capture(root,"methods-initialized-agreement",language,p,host.document());
      for(String role:List.of("seller","partner"))host=applied(p.process(host.document(),event(host.document(),role,"approve_"+role,m("revision",1)),time++));
      require(Boolean.TRUE.equals(p.read(host.document(),"/activation/active")),"Agreement active");
      var unknown=p.process(host.document(),event(host.document(),"partner","prepareOrder",request("bad","payment-"+"0".repeat(64),null)),time++);
      require(!unknown.commits(),"Unknown choice must fail");require(host.document().identity().equals(unknown.document().identity()),"Unknown choice changed Agreement");
      for(int i=0;i<options.size();i++){
        var option=options.get(i);String key="choice-"+i;String id=(String)option.get("id");
        var attack=m("paymentDetails",m("customerPaymentTerms",m("provider","stripe","recipientPaymentAccountId","attacker")));
        var req=request(key,id,attack);
        host=applied(p.process(host.document(),event(host.document(),"partner","prepareOrder",req),time++));
        var entries=obj(p.read(host.document(),"/process_orders/entries"));Map<String,Object> selected=null;
        for(Object value:entries.values()){var item=obj(value);if(key.equals(item.get("key")))selected=item;}
        require(selected!=null,"Selected native requirement missing");String prepared=selected.get("itemPath")+"/prepared";
        String path=prepared+"/paymentTemplate/paymentDetails/customerPaymentTerms";
        require(option.get("provider").equals(p.read(host.document(),path+"/provider")),"Selected provider must come from approved map");
        require(option.get("recipientPaymentAccountId").equals(p.read(host.document(),path+"/recipientPaymentAccountId")),"Selected recipient must come from approved map, not caller template");
        capture(root,"methods-prepared-agreement-"+i,language,p,host.document());
        var nativeValues=p.execution().values();var current=new Exact.Ref(host.document().blueId());
        String entryKey=entries.entrySet().stream().filter(e->key.equals(obj(e.getValue()).get("key"))).findFirst().orElseThrow().getKey();
        String storedPath="/process_orders/entries/"+entryKey+"/intent/values/paymentTemplate";
        String authoredPath="/approvedPaymentTemplates/"+id;
        Files.writeString(root.resolve("reports/payment-flow/method-template-identities.json"),WireData.write(m(
            "storedIdentity",NativeRuntime.identity(nativeValues.exact(nativeValues.select(current,storedPath))),
            "authoredIdentity",NativeRuntime.identity(nativeValues.exact(nativeValues.select(current,authoredPath))),
            "storedKeys",new ArrayList<>(obj(p.read(host.document(),storedPath)).keySet()),
            "authoredKeys",new ArrayList<>(obj(p.read(host.document(),authoredPath)).keySet()))));
        var retryEvent=event(host.document(),"partner","prepareOrder",req);long retryTime=time++;
        var retried=p.process(host.document(),retryEvent,retryTime);
        if(!retried.commits()) {
          Files.writeString(root.resolve("reports/payment-flow/method-retry-evidence.json"),WireData.write(m("request",req,"event",retryEvent,"entries",p.execution().values().literal(p.execution().values().exact(p.execution().values().select(new Exact.Ref(host.document().blueId()),"/process_orders/entries"))))));
          ClauseGasProbe.diagnose(p,host.document(),retryEvent,retryTime);
        }
        var retry=applied(retried);
        require(entries.equals(p.read(retry.document(),"/process_orders/entries")),"Same choice retry changed frozen source");host=retry;
        var changed=p.process(host.document(),event(host.document(),"partner","prepareOrder",request(key,(String)options.get((i+1)%options.size()).get("id"),null)),time++);
        require(!changed.commits(),"Same requirement cannot change its selected method");require(host.document().identity().equals(changed.document().identity()),"Changed selection mutated requirement");
      }
      System.out.println("PASS native Agreement payment method allowlist, whole-template substitution isolation, stable retry and changed-choice rejection; no provider payment claim");
    }
  }
}
