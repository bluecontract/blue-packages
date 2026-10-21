import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Actual current package generators and BEX execution; no handwritten operation declarations. */
public final class OperationCatalogConformance {
  static Map<String,Object> m(Object... pairs) {return OperationInputConformance.m(pairs);}
  static void require(boolean value,String message) {OperationInputConformance.require(value,message);}
  static void activation(Path root)throws Exception {
    activation(root,false);
  }
  static void activation(Path root,boolean full)throws Exception {
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    var channel=m("type","Contracts/External Channel","event",m("source","owner"));
    var source=m("name","Generated approval input","type","Agreements/Agreement with Clauses",
        "contracts",m("owner",channel),"clauses",m("activation",m("type","Activation/Activation Clause",
            "parameters",m("parties",m("owner",m("type","Parties/Party","lead",m("channel",channel),
                "readerKeys",List.of("reader-owner"))),"required",List.of("owner")))));
    if(full) {
      source.put("price",100);
      @SuppressWarnings("unchecked") var clauses=(Map<String,Object>)source.get("clauses");
      @SuppressWarnings("unchecked") var clause=(Map<String,Object>)clauses.get("activation");
      @SuppressWarnings("unchecked") var parameters=(Map<String,Object>)clause.get("parameters");
      parameters.put("negotiation",m("allowedPaths",List.of("/price")));
    }
    try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var processor=runtime.processor(packages.language());var initialized=processor.initialize(source);
      require(initialized.status().equals("APPLIED"),"Native initialization: "+initialized.status());
      require(processor.read(initialized.document(),"/operationPreparation")==blue.bex.Values.UNDEFINED,
          "New documents must not contain operationPreparation: "+processor.read(initialized.document(),"/operationPreparation"));
      var execution=processor.execution();var declaration=execution.declarations(new Exact.Ref(initialized.document().blueId())).get("approve_owner");
      if(full)for(String operation:List.of("updateParty_owner","proposeChanges_owner","proposeAndActivate_owner","activate_owner","withdrawAcceptance_owner","withdrawProposal_owner","rejectProposal_owner")) {
        var contract=execution.declarations(new Exact.Ref(initialized.document().blueId())).get(operation);
        require(contract!=null&&contract.containsKey("request"),"Activation public matcher missing: "+operation);
      }
      if(full) {
        var cases=m(
          "updateParty_owner",m("type","Activation/Party Update Input","replacement",m("lead",m("channel",channel))),
          "proposeChanges_owner",m("type","Activation/Terms Proposal Input","proposalId","proposal-1","baseTermsRef",processor.read(initialized.document(),"/activation/terms/ref"),"changes",m("type","List","itemType","Activation/Term Change","items",List.of(m("type","Activation/Term Change","path","/price","replacement",120)))),
          "activate_owner",m("type","Activation/Terms Selection Input","termsRef",processor.read(initialized.document(),"/activation/terms/ref")),
          "withdrawAcceptance_owner",m("type","Activation/Terms Selection Input","termsRef",processor.read(initialized.document(),"/activation/terms/ref")),
          "withdrawProposal_owner",m("proposalId","proposal-1"),"rejectProposal_owner",m("proposalId","proposal-1"));
        cases.put("proposeAndActivate_owner",cases.get("proposeChanges_owner"));
        for(var entry:cases.entrySet()) {
          var contract=execution.declarations(new Exact.Ref(initialized.document().blueId())).get(entry.getKey());
          var inputMatcher=execution.values().source(contract.get("request"),"definition");
          require(execution.values().matches(execution.values().source(entry.getValue()),inputMatcher),"Activation minimal optional omissions: "+entry.getKey());
          require(!execution.values().matches(execution.values().source(m()),inputMatcher),"Activation required input: "+entry.getKey());
        }
      }
      require(declaration.containsKey("request"),"Generated approval must retain its public input matcher");
      Object revision=processor.read(initialized.document(),"/activation/revision");
      var request=m("revision",revision);
      if(full)request.put("termsRef",processor.read(initialized.document(),"/activation/terms/ref"));
      var matcher=execution.values().source(declaration.get("request"),"definition");
      require(execution.values().matches(execution.values().source(request),matcher),"Current revision must match");
      require(!execution.values().matches(execution.values().source(m()),matcher),"Missing revision must fail");
      require(Boolean.FALSE.equals(processor.read(initialized.document(),"/activation/active")),"Matching must not approve");
      var event=m("source","owner","operation",m("type","Contracts/Operation Request","channel","owner",
          "operation","approve_owner","document",m("blueId",initialized.document().blueId()),
          "requireExactDocumentVersion",true,"request",request));
      var approved=processor.process(initialized.document(),event,1);
      require(approved.status().equals("APPLIED"),"Native approval: "+approved.status());
      require(Boolean.TRUE.equals(processor.read(approved.document(),"/activation/active")),"Approval must activate");
      System.out.println("PASS generated Activation request, no metadata, zero matching effect, native approval effect");
    }
  }
  static void shipping(Path root)throws Exception {
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language()) {
      var runtime=new NativeRuntime(blue);
      var definition=blue.admitDefinition(WireData.write(m("type","Shipping/Shipping Instruction")));
      var selected=NativeRuntime.recipe(NativeRuntime.exactOf(definition));
      selected=NativeRuntime.head(selected,runtime).contracts;
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var input=m("type","Shipping/Shipping Response Input","requestId","shipment-1");
      for(String operation:List.of("confirmShipment","rejectShipment","recordDispatched","confirmDelivery","failShipment",
          "confirmCancellation","rejectCancellation","confirmAddressChange","rejectAddressChange")) {
        var contract=NativeRuntime.child(NativeRuntime.head(selected,runtime),operation);
        require(contract!=null,"Shipping declaration missing: "+operation+" available="+NativeRuntime.head(selected,runtime).fields.keySet());
        require(NativeRuntime.head(contract,runtime).fields.containsKey("request"),"Shipping public matcher missing: "+operation);
        var matcher=NativeRuntime.exact(NativeRuntime.child(NativeRuntime.head(contract,runtime),"request"),runtime);
        require(values.matches(values.source(input),matcher),"Optional Shipping fields may be omitted: "+operation);
        require(!values.matches(values.source(m("type","Shipping/Shipping Response Input")),matcher),"Shipping requestId required");
        require(!values.matches(values.source(m("type","Shipping/Shipping Response Input","requestId",7)),matcher),"Shipping requestId type");
        require(values.matches(values.source(m("type","Shipping/Shipping Response Input","requestId","shipment-1","reason","Carrier explanation","trackingId","parcel-1")),matcher),"Optional fields retain their declared native types");
      }
      @SuppressWarnings("unchecked") var example=(Map<String,Object>)WireData.parse(Files.readString(root.resolve("examples/apps/25-shipping.blue")),"yaml");
      @SuppressWarnings("unchecked") var source=(Map<String,Object>)WireData.copy(example.get("shippingTemplate"));
      @SuppressWarnings("unchecked") var clauses=(Map<String,Object>)source.get("clauses");
      @SuppressWarnings("unchecked") var activation=(Map<String,Object>)clauses.get("activation");
      @SuppressWarnings("unchecked") var parameters=(Map<String,Object>)activation.get("parameters");
      var parties=m();var channels=m();
      for(String role:List.of("seller","carrier")) {
        var channel=m("type","Contracts/External Channel","event",m("source",role));
        channels.put(role,channel);parties.put(role,m("type","Parties/Party","lead",m("channel",channel),"readerKeys",List.of("reader-"+role)));
      }
      // A matcher must survive even when it has no root label or concrete values.
      @SuppressWarnings("unchecked") var configured=(Map<String,Object>)((Map<String,Object>)clauses.get("requests")).get("bindings");
      for(Object action:configured.values())for(Object connection:((Map<?,?>)action).values()) {
        var inputDefinition=((Map<?,?>)connection).get("request");
        if(inputDefinition instanceof Map<?,?> inputMap)inputMap.remove("description");
      }
      parameters.put("parties",parties);source.put("contracts",channels);
      // Effective inherited defaults and explicit action overrides use their exact authored paths.
      for(boolean override : List.of(false,true)) {
        @SuppressWarnings("unchecked") var defaultsSource=(Map<String,Object>)WireData.copy(source);
        @SuppressWarnings("unchecked") var defaultClauses=(Map<String,Object>)defaultsSource.get("clauses");
        @SuppressWarnings("unchecked") var requestClause=(Map<String,Object>)defaultClauses.get("requests");
        Object bindings=requestClause.remove("bindings");
        requestClause.put("type",m("type",requestClause.get("type"),"defaultBindings",bindings));
        if(override) {
          var explicit=m("on","workflow","party","seller","params",m("$object",m("$var","trigger")));
          requestClause.put("bindings",m("requestShipment",m("bookShipment",explicit)));
        }
        try(var authoring=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
          var processor=authoring.processor(blue);var initialized=processor.initialize(defaultsSource);
          require(initialized.status().equals("APPLIED"),"Default-binding initialization "+initialized.status());
          var declarations=processor.execution().declarations(new Exact.Ref(initialized.document().blueId()));
          require(declarations.get("bookShipment").containsKey("request") != override,
              "Explicit action binding must replace defaults without inventing a request");
          require(declarations.get("cancelShipment").containsKey("request"),"Inherited default request must survive");
        }
      }
      try(var authoring=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
        var processor=authoring.processor(blue);var initialized=processor.initialize(source);
        require(initialized.status().equals("APPLIED"),"Shipping initialization "+initialized.status());
        var requests=processor.execution().declarations(new Exact.Ref(initialized.document().blueId()));
        for(String operation:List.of("bookShipment","cancelShipment","changeAddress"))
          require(requests.get(operation).containsKey("request"),"Configured Shipping request matcher missing: "+operation);
        var requested=processor.process(initialized.document(),event(initialized.document(),"seller","bookShipment",m("requestId","shipment-1")),1);
        require(requested.status().equals("APPLIED"),"Shipping request "+requested.status());
        require("requested".equals(processor.read(requested.document(),"/shipment/status")),"Request must not confirm shipment");
        var confirmed=processor.process(requested.document(),event(requested.document(),"carrier","confirmShipment",input),2);
        require(confirmed.status().equals("APPLIED"),"Typed Shipping response "+confirmed.status());
        require("accepted".equals(processor.read(confirmed.document(),"/shipment/status")),"Native shared respond effect");
        System.out.println("PASS nine Shipping matchers, optional fields, public adapter and native response effect");
      }
    }
  }
  static Object event(Contracts.Document document,String channel,String operation,Object request) {
    return m("source",channel,"operation",m("type","Contracts/Operation Request","channel",channel,
        "operation",operation,"document",m("blueId",document.blueId()),"requireExactDocumentVersion",true,"request",request));
  }
  public static void main(String[] args)throws Exception {
    if(args.length>1&&args[1].equals("shipping"))shipping(Path.of(args[0]));
    else activation(Path.of(args[0]),args.length>1&&args[1].equals("activation-complete"));
  }
}
