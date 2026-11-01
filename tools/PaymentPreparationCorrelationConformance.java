import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native preparation, caller isolation and requirement identity; no hosted bootstrap claim. */
public final class PaymentPreparationCorrelationConformance {
  static Map<String,Object> m(Object... fields) { return BootstrapPreparationConformance.m(fields); }
  static Map<String,Object> obj(Object value) { return BootstrapPreparationConformance.obj(value); }
  static void require(boolean condition,String reason) { BootstrapPreparationConformance.require(condition,reason); }
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]);boolean baseline=args.length>1&&args[1].equals("baseline");
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    var origins=new ArrayList<String>();var requirements=new ArrayList<Object>();
    for(String name:List.of("first","second","default-key"))try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var processor=runtime.processor(packages.language());
      var source=BootstrapPreparationConformance.source("bootstrap");source.put("name",name);
      var clause=obj(obj(source.get("clauses")).get("orders"));
      if(!baseline) {
        var parameters=obj(clause.get("parameters"));
        obj(parameters.get("fieldPaths")).put("paymentPreparation","/paymentPreparation");
        obj(parameters.get("template")).put("paymentPreparation",m("type","MyOSPaymentMandates/Payment Preparation Correlation"));
        var prepare=obj(obj(obj(clause.get("bindings")).get("prepare")).get("prepareOrder"));
        prepare.put("params",WireData.parse(Files.readString(root.resolve("myos-payment-mandates/examples/correlated-prepare-params.blue")),"yaml"));
      }
      String initialId=NativeRuntime.identity(processor.execution().values().source(source));
      var initialized=BootstrapPreparationConformance.applied(processor.initialize(source));
      var host=BootstrapPreparationConformance.applied(processor.process(initialized.document(),BootstrapPreparationConformance.event(initialized.document(),"approve_merchant",m("revision",1)),1));
      var values=m("size",42);
      if(!baseline)values.put("paymentPreparation",m("orderDocumentId","forged","clauseId","wrong","itemKey","wrong","requestId","wrong"));
      var request=m("type","Documents/Preparation Input","key","one","requestId","request-one","values",values);
      if(name.equals("default-key"))request.remove("key");
      host=BootstrapPreparationConformance.applied(processor.process(host.document(),BootstrapPreparationConformance.event(host.document(),"prepareOrder",request),2));
      var entries=obj(processor.read(host.document(),"/process_orders/entries"));
      var item=obj(entries.values().iterator().next());
      var correlation=processor.read(host.document(),item.get("itemPath")+"/prepared/paymentPreparation");
      require(correlation instanceof Map,"Prepared source must carry native requirement correlation");
      var actual=obj(correlation);
      require(actual.keySet().equals(Set.of("orderDocumentId","clauseId","itemKey","requestId")),"Exact complete correlation object");
      require("orders".equals(actual.get("clauseId")),"Native clause key");
      require((name.equals("default-key")?"single":"one").equals(actual.get("itemKey")),"Native item key including typed absent-key default");
      require("request-one".equals(actual.get("requestId")),"Native request ID");
      require(initialId.equals(actual.get("orderDocumentId")),"Exact initial Order identity, not current state or caller input");
      origins.add(actual.get("orderDocumentId").toString());requirements.add(item.get("requirementRef"));
      var repeated=BootstrapPreparationConformance.applied(processor.process(host.document(),BootstrapPreparationConformance.event(host.document(),"prepareOrder",request),3));
      require(obj(processor.read(repeated.document(),"/process_orders/entries")).equals(entries),"Retry reuses exact obligation/source");
    }
    require(!origins.get(0).equals(origins.get(1)),"Distinct Order origins");
    require(!requirements.get(0).equals(requirements.get(1)),"Correlation participates in requirementRef identity");
    System.out.println("PASS native correlation, forged-input isolation, distinct source identity and retry");
  }
}
