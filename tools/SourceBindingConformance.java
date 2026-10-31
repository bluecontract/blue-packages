import blue.packages.QualificationRuntime;
import blue.contracts.*;
import blue.bex.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Generated source-binding workflows preserve typed optional presence and exact references. */
public final class SourceBindingConformance {
  static Map<String,Object> m(Object... p){return OperationInputConformance.m(p);}
  static void require(boolean x,String text){OperationInputConformance.require(x,text);}
  static Map<String,Object> agreement(String name){
    var channel=m("type","Contracts/External Channel","event",m("source","owner"));
    return m("name",name,"type","Agreements/Agreement with Clauses","state","ready","contracts",m("owner",channel),
        "clauses",m("activation",m("type","Activation/Activation Clause","parameters",m("parties",m("owner",m("type","Parties/Party",
        "lead",m("channel",channel),"readerKeys",List.of("reader-owner"))),"required",List.of("owner")))));
  }
  static Object event(Contracts.Document d,String operation,Object input){
    return m("source","owner","operation",m("type","Contracts/Operation Request","channel","owner","operation",operation,
        "document",m("blueId",d.blueId()),"requireExactDocumentVersion",true,"request",input));
  }
  // Compare exact bodies, permitting only observed native checkpoints and managed-edge re-encoding.
  static Object comparison(NativeRuntime nativeRuntime, Exact node, Map<String,Object> replacements) {
    var fields=new TreeMap<String,Object>(nativeRuntime.open(node).fields());
    var nested=new TreeMap<String,Map<String,Object>>();
    for(var entry:replacements.entrySet()) {
      String path=entry.getKey();require(path.startsWith("/"),"Absolute fixture path");
      int slash=path.indexOf('/',1);String field=path.substring(1,slash<0?path.length():slash);
      require(fields.containsKey(field),"Compared exact path exists: "+path);
      if(slash<0) {
        if(entry.getValue()==null)fields.remove(field);else fields.put(field,entry.getValue());
      } else nested.computeIfAbsent(field,k->new LinkedHashMap<>()).put(path.substring(slash),entry.getValue());
    }
    for(var entry:nested.entrySet()) fields.put(entry.getKey(),comparison(nativeRuntime,(Exact)fields.get(entry.getKey()),entry.getValue()));
    return fields;
  }
  static void duplicateOnlyCheckpoints(Contracts p, Contracts.Document before, Contracts.Result duplicate, Object event) {
    var a=p.execution().snapshot(before);var b=p.execution().snapshot(duplicate.document());
    require(a.documents.keySet().equals(b.documents.keySet())&&a.edges.equals(b.edges),"Duplicate preserves exact member topology and generations");
    require(((List<?>)duplicate.observations().get("changes")).isEmpty()&&p.emitted(duplicate).isEmpty(),"No duplicate business changes or effects");
    var changed=new HashSet<String>();String eventId=NativeRuntime.identity(p.execution().values().source(event));
    for(Object raw:(List<?>)duplicate.observations().get("checkpoints")) {
      var row=(Map<?,?>)raw;String member=row.get("document").toString();
      require("owner".equals(row.get("channel")),"Only consumed owner channel checkpoint");
      require(WireData.write(row.get("after")).equals(WireData.write(m("timestamp",4,"event",m("blueId",eventId)))),"Exact duplicate event and timestamp");
      require(changed.add(member),"One owner checkpoint per member");
      for(var side:List.of(m("snapshot",a,"value",row.get("before")),m("snapshot",b,"value",row.get("after")))) {
        var snapshot=(ContractsExecution.Snapshot)side.get("snapshot");
        var entry=p.execution().values().select(snapshot.documents.get(member).body,"/contracts/checkpoint/entries/owner");
        var fields=p.execution().values().nativeRuntime().open(p.execution().values().exact(entry)).fields();
        require(fields.keySet().equals(Set.of("timestamp","event")),"Checkpoint entry contains only timestamp and protected event identity");
        // Match markerRecord: timestamp is logical scalar; event is protected exact identity.
        var actual=m("timestamp",p.execution().values().bexData(fields.get("timestamp")),
            "event",m("blueId",NativeRuntime.identity((Exact)fields.get("event"))));
        require(WireData.write(actual).equals(WireData.write(side.get("value"))),"Observed checkpoint row matches actual marker entry: "+WireData.write(actual));
      }
    }
    require(changed.contains(a.root),"Receiver consumed duplicate event");
    var nativeRuntime=p.execution().values().nativeRuntime();
    for(String key:a.documents.keySet()) {
      var left=a.documents.get(key);var right=b.documents.get(key);
      require(left.channelLives.equals(right.channelLives),"Duplicate preserves channel life");
      var masks=new LinkedHashMap<String,Object>();
      if(changed.contains(key))masks.put("/contracts/checkpoint/entries/owner",m("consumedOwnerEntry",true));
      for(var edge:a.edges.values())if(edge.source().equals(key)) {
        for(var snapshot:List.of(a,b)) {
          var selected=p.execution().values().select(snapshot.documents.get(key).body,edge.path());
          require(snapshot.documents.get(edge.target()).blueId.equals(NativeRuntime.identity(p.execution().values().exact(selected))),"Managed edge encodes exact target publication");
        }
        masks.put(edge.path(),m("managedMember",edge.target()));
      }
      require(comparison(nativeRuntime,left.body,masks).equals(comparison(nativeRuntime,right.body,masks)),"Only checkpoint and its managed reference encoding may change: "+key);
    }
  }
  static void requireApplied(Contracts p, Contracts.Result result, String context) {
    if (!result.status().equals("APPLIED"))
      throw new AssertionError(context+": "+OperationInputConformance.initializationDiagnostic(p,result));
  }
  @SuppressWarnings("unchecked")
  static Contracts.Result generatedReceiver(Contracts p, Contracts.Document source) throws Exception {
    var parent=agreement("Public Documents source-binding factory");
    parent.put("supplied",m("blueId",source.blueId()));
    var template=agreement("Generated receiver");
    template.put("sources",m("payer",m()));
    var clause=m("type","Documents/Document Clause","parameters",m("obtain","create","suppliedBy","owner","template",template),
        "bindings",m("parties",m("owner","owner"),"sources",m("payer","/supplied"),"document","/receiver",
            "prepare",m("prepareReceiver",m("on","workflow","party","owner","request",m("type","Documents/Preparation Input")))));
    ((Map<String,Object>)parent.get("clauses")).put("factory",clause);
    var initialized=p.initialize(parent);
    requireApplied(p,initialized,"Public factory initialization");
    var approved=p.process(initialized.document(),event(initialized.document(),"approve_owner",m("revision",p.read(initialized.document(),"/activation/revision"))),10);
    require(approved.status().equals("APPLIED"),"Public factory approval");
    var prepared=p.process(approved.document(),event(approved.document(),"prepareReceiver",m("type","Documents/Preparation Input")),11);
    requireApplied(p,prepared,"Actual Documents prepare/configureSources");
    var entries=(Map<?,?>)p.read(prepared.document(),"/process_factory/entries");
    require(entries.size()==1,"One public preparation entry");
    var entry=(Map<?,?>)entries.values().iterator().next();
    String path=entry.get("itemPath")+"/prepared";
    var values=p.execution().values();
    var exact=values.exact(values.select(new Exact.Ref(prepared.document().blueId()),path));
    var receiver=p.initialize(m("blueId",NativeRuntime.identity(exact)));
    requireApplied(p,receiver,"Generated receiver initialized");
    var declaration=p.execution().declarations(new Exact.Ref(receiver.document().blueId())).get("bindSource_owner");
    require(declaration!=null&&declaration.containsKey("request"),"Factory requestFrom generates public request matcher");
    require(!declaration.containsKey("$blue:requestFrom"),"Generator consumes authoring-only requestFrom");
    var expected=values.select(values.source(m("type","Documents/Source Functions"),"definition"),"/functions/bindSourcePublic/args/input");
    require(NativeRuntime.identity(values.exact(expected)).equals(NativeRuntime.identity(values.source(declaration.get("request"),"definition"))),
        "Public factory request is the exact published bindSourcePublic input");
    System.out.println("PASS actual Documents preparation configureSources and generated exact requestFrom matcher");
    return receiver;
  }
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    boolean accessEvents=QualificationRuntime.bindings().timelineAccessEvents();
    boolean publicWrapper=Arrays.asList(args).contains("public");
    boolean cyclic=Arrays.asList(args).contains("cyclic");
    var bindings=QualificationRuntime.bindings();
    try(var blue=packages.language();var runtime=new AuthoringRuntime(bindings)) {
      var p=runtime.processor(blue);var values=p.execution().values();
      var sourceDefinition=agreement("Existing independent source");
      if(cyclic) {
        @SuppressWarnings("unchecked") var contracts=(Map<String,Object>)sourceDefinition.get("contracts");
        contracts.put("embedded",m("type","Contracts/Process Embedded","paths",List.of("/cycle")));
        contracts.put("attachCycle",m("type","Contracts/Sequential Workflow Operation","channel","owner",
            "steps",List.of(m("type","Contracts/Update Document","changeset",List.of(
                m("op","add","path","/cycle","val",m("$binding","call/request/child")))))));
      }
      var original=p.initialize(sourceDefinition);require(original.status().equals("APPLIED"),"Source init: "+OperationInputConformance.initializationDiagnostic(p,original));
      var source=p.process(original.document(),event(original.document(),"approve_owner",m("revision",p.read(original.document(),"/activation/revision"))),1);
      require(Boolean.TRUE.equals(p.read(source.document(),"/activation/active")),"Source active");
      if(cyclic) {
        var wrapper=p.initialize(m("name","Authentic source-cycle wrapper",
            "child",m("blueId",source.document().blueId()),
            "contracts",m("embedded",m("type","Contracts/Process Embedded","paths",List.of("/child")))));
        requireApplied(p,wrapper,"Cycle wrapper initialized");
        p.execution().chooseHistory(wrapper.document().blueId(),p.execution().snapshot(wrapper.document()));
        source=p.process(source.document(),event(source.document(),"attachCycle",
            m("child",m("blueId",wrapper.document().blueId()))),2);
        requireApplied(p,source,"Cycle attachment applied");
        require(source.document().blueId().contains("#"),"Use a real initialized cyclic publication, not a fabricated component");
        require(Boolean.TRUE.equals(p.read(source.document(),"/activation/active")),"Cyclic source remains active");
      }
      p.execution().chooseHistory(source.document().blueId(),p.execution().snapshot(source.document()));
      System.out.println("SOURCE exact="+source.document().blueId()+" cyclic="+cyclic);
      String origin=NativeRuntime.identity(values.exact(values.select(new Exact.Ref(source.document().blueId()),"/contracts/initialized/document")));
      var matcher=values.select(values.source(m("type","Documents/Source Functions"),"definition"),"/functions/bindSourcePublic/args/input");
      Contracts.Document otherSource=null;
      if(Arrays.asList(args).contains("guards")){var other=p.initialize(agreement("Other initialized source"));require(other.status().equals("APPLIED"),"Other source init");otherSource=other.document();p.execution().chooseHistory(otherSource.blueId(),p.execution().snapshot(otherSource));}
      var expectedReasons=Map.of("typed-wrong-origin","SOURCE_IDENTITY_MISMATCH","typed-undeclared","SOURCE_UNDECLARED_NAME","typed-inactive","SOURCE_INACTIVE","typed-reader-mismatch","PARTY_PRIMARY_KEYS_MISMATCH","typed-channel-mismatch","SOURCE_MAIN_PARTY_MISSING","typed-rebinding","SOURCE_REBINDING_FORBIDDEN");
      var modes=publicWrapper?List.of("typed-reference"):Arrays.asList(args).contains("boundary")?List.of("typed-missing","typed-uninitialized"):Arrays.asList(args).contains("routing")?List.of("typed-stale","typed-unauthorized","typed-malformed-path"):(Arrays.asList(args).contains("replay")||Arrays.asList(args).contains("history"))?List.of("typed-reference"):Arrays.asList(args).contains("guards")?List.of("typed-inactive","typed-reader-mismatch","typed-channel-mismatch","typed-rebinding"):List.of("typed-reference","typed-path","typed-both","typed-inherited","typed-missing","typed-uninitialized","typed-wrong-origin","typed-undeclared","legacy-reference","legacy-path");
      for(String mode:modes) {
        String requiredOrigin=mode.equals("typed-wrong-origin")?NativeRuntime.identity(values.source(m("name","Different required origin"))):origin;
        var host=agreement("Source receiver "+mode);host.put("sources",m());host.put("supplied",m("blueId",source.document().blueId()));
        if(Arrays.asList(args).contains("history")||mode.equals("typed-stale"))host.remove("supplied");
        @SuppressWarnings("unchecked") var clauses=(Map<String,Object>)host.get("clauses");
        if(mode.equals("typed-rebinding"))host.put("sources",m("payer",m("blueId",otherSource.blueId())));
        @SuppressWarnings("unchecked") var activation=(Map<String,Object>)clauses.get("activation");
        @SuppressWarnings("unchecked") var parameters=(Map<String,Object>)activation.get("parameters");
        @SuppressWarnings("unchecked") var parties=(Map<String,Object>)parameters.get("parties");
        @SuppressWarnings("unchecked") var owner=(Map<String,Object>)parties.get("owner");
        if(mode.equals("typed-reader-mismatch"))owner.put("readerKeys",List.of("reader-other"));
        if(mode.equals("typed-channel-mismatch")) {
          var otherChannel=m("type","Contracts/External Channel","event",m("source","other"));
          owner.put("lead",m("channel",otherChannel));
          @SuppressWarnings("unchecked") var hostContracts=(Map<String,Object>)host.get("contracts");hostContracts.put("owner",otherChannel);
        }
        var connection=m("on","workflow","party","owner","request",mode.startsWith("legacy")?m():m("blueId",NativeRuntime.identity(values.exact(matcher))));
        clauses.put("documentSources",m("type","Documents/Source Binding Clause","parameters",m("requirements",m("payer",m("origin",requiredOrigin,"selectionPath",""))),
            "bindings",m("bind",m("bindSource_owner",connection))));
        var initialized=publicWrapper?generatedReceiver(p,source.document()):p.initialize(host);requireApplied(p,initialized,"Receiver init");
        var approvalEvent=event(initialized.document(),"approve_owner",m("revision",p.read(initialized.document(),"/activation/revision")));
        if(mode.equals("typed-channel-mismatch"))((Map<String,Object>)approvalEvent).put("source","other");
        var approved=p.process(initialized.document(),approvalEvent,2);
        require(Boolean.TRUE.equals(p.read(approved.document(),"/activation/active")),"Receiver active");
        var input=m("alias",mode.equals("typed-undeclared")?"undeclared":"payer");if(!mode.startsWith("legacy"))input.put("type","Documents/Source Binding Input");
        if(mode.endsWith("reference")||mode.endsWith("both")||mode.equals("typed-wrong-origin")||expectedReasons.containsKey(mode)||Arrays.asList(args).contains("routing"))input.put("document",m("blueId",source.document().blueId()));
        if(mode.endsWith("path")||mode.endsWith("both"))input.put("sourcePath","/supplied");
        if(mode.equals("typed-inherited")) {
          input.put("type",m("type","Documents/Source Binding Input","sourcePath","/supplied"));
          input.put("document",m("blueId",source.document().blueId()));
          var normalized=m("$pointerSet",m("object",m("$object",m("$binding","input")),"path","/type","op","remove"));
          var program=m("do",List.of(m("$return",m("$pointerGet",m("object",normalized,"path","/sourcePath","default","")))));
          var context=new BexContext(m(),m(),m(),Values.UNDEFINED,m(),m("input",values.view(values.source(input))),"/",null,
              (actual,pattern)->values.matches(actual,values.source(pattern,"definition")),null);
          var bex=new Bex(BexProfile.current());
          require("/supplied".equals(bex.execute(bex.compile(program),context,100000).value()),
              "Materialization must retain inherited concrete sourcePath");
        }
        if(mode.equals("typed-inactive"))input.put("document",m("blueId",original.document().blueId()));
        if(mode.equals("typed-uninitialized"))input.put("document",m("blueId",NativeRuntime.identity(values.source(m("state","not-initialized")))));
        if(mode.equals("typed-malformed-path"))input.put("sourcePath","not-an-absolute-pointer");
        String exact=WireData.write(input);
        var bindingEvent=event(approved.document(),"bindSource_owner",input);
        if(mode.equals("typed-channel-mismatch"))((Map<String,Object>)bindingEvent).put("source","other");
        if(mode.equals("typed-stale"))((Map<String,Object>)((Map<String,Object>)bindingEvent).get("operation")).put("document",m("blueId",initialized.document().blueId()));
        if(mode.equals("typed-unauthorized"))((Map<String,Object>)bindingEvent).put("source","unauthorized");
        var bound=p.process(approved.document(),bindingEvent,3);
        if(Arrays.asList(args).contains("routing")) {
          require(bound.document().blueId().equals(approved.document().blueId())&&p.emitted(bound).isEmpty(),"Routing rejection preserves state/effects: "+mode);
          require(exact.equals(WireData.write(input)),"Routing request unchanged");
          if(mode.equals("typed-unauthorized")) {
            require(bound.status().equals("APPLIED")&&((List<?>)bound.observations().get("work")).isEmpty(),"Unmatched external channel executes no work");
          } else {
            String expected=mode.equals("typed-stale")?"STALE_DOCUMENT_PRECONDITION":"BEX_BEX_RUNTIME_ERROR";
            require(bound.status().equals("FAILED")&&expected.equals(((Map<?,?>)ClauseGasProbe.diagnostic(bound)).get("code")),"Exact routing rejection: "+mode+" "+bound.observations());
          }
          System.out.println("PASS "+mode+" status="+bound.status()+" diagnostic="+ClauseGasProbe.diagnostic(bound)+" unchanged state/request/effects");
          continue;
        }
        if(expectedReasons.containsKey(mode)) {
          String reason=expectedReasons.get(mode);
          require(!bound.commits(),"Invalid source must remain rejected: "+mode);
          require(bound.status().equals("FAILED"),"Business guard is an execution rejection: "+mode);
          require("BEX_EXECUTION_REJECTED".equals(((Map<?,?>)ClauseGasProbe.diagnostic(bound)).get("code")),"Exact native rejection code: "+bound.observations());
          boolean diagnosed=false;
          try { ClauseGasProbe.diagnose(p,approved.document(),bindingEvent,3); }
          catch(BexError failure) { diagnosed=failure.toString().contains(reason);if(!diagnosed)throw failure; }
          require(diagnosed,"Expected authored source rejection "+reason);
          require(approved.document().blueId().equals(bound.document().blueId()),"Rejected source must not change receiver");
          require(exact.equals(WireData.write(input)),"Rejected request remains unchanged");
          require(p.emitted(bound).isEmpty(),"Rejected source emits no effects");
          System.out.println("PASS "+mode+" FAILED/BEX_EXECUTION_REJECTED authored="+reason+" unchanged receiver/request; no effects");
          continue;
        }
        if(mode.endsWith("missing")||mode.endsWith("uninitialized")) {
          require(!bound.commits(),"Missing or uninitialized source must remain rejected: "+mode);
          require(approved.document().blueId().equals(bound.document().blueId()),"Rejected source must not change receiver");
          require(exact.equals(WireData.write(input))&&p.emitted(bound).isEmpty(),"Invalid input preserves request and has no effects");
          require(bound.status().equals("FAILED")&&"BEX_EXECUTION_REJECTED".equals(((Map<?,?>)ClauseGasProbe.diagnostic(bound)).get("code")),"Initialized-source guard executes during binding");
          boolean initializedGuard=false;
          try { ClauseGasProbe.diagnose(p,approved.document(),bindingEvent,3); }
          catch(BexError failure) { initializedGuard=failure.toString().contains("SOURCE_INITIALIZED_PROCESS_REQUIRED");if(!initializedGuard)throw failure; }
          require(initializedGuard,"Explicit initialized source execution guard");
          System.out.println("PASS "+mode+" FAILED/BEX_EXECUTION_REJECTED authored=SOURCE_INITIALIZED_PROCESS_REQUIRED unchanged state/request; no effects");
          continue;
        }
        requireApplied(p,bound,"Generated bindSource "+mode);
        var linked=values.select(new Exact.Ref(bound.document().blueId()),"/sources/payer");
        require(linked!=null&&source.document().blueId().equals(NativeRuntime.identity(values.exact(linked))),"Exact provided publication must be stored: "+mode);
        require(exact.equals(WireData.write(input)),"Reviewed request remains unchanged");
        System.out.println("PASS "+mode+" APPLIED exact supplied publication="+source.document().blueId()+" request unchanged");
        if(Arrays.asList(args).contains("history")) {
          var beforeWire=p.exportSnapshot(approved.document());
          var sourceWire=p.exportSnapshot(source.document());
          try(var coldBlue=packages.language();var coldRuntime=new AuthoringRuntime(bindings)) {
            var cold=coldRuntime.processor(coldBlue);
            var beforeCopy=cold.importSnapshot(beforeWire,approved.document().identity());
            @SuppressWarnings("unchecked") var exactSourceContent=(Map<String,Object>)sourceWire.get("content");
            // Finite fixture records isolate native history from content availability.
            // This is not a minimal-closure or privacy measurement.
            cold.execution().values().nativeRuntime().addEvidence(new LinkedHashMap<>(p.execution().values().nativeRuntime().evidence()));
            var missing=cold.process(beforeCopy,bindingEvent,3);
            require(missing.status().equals("NEEDS_RESOURCES"),"Exact content alone cannot invent source history: "+missing.observations());
            var diagnostic=(Map<?,?>)ClauseGasProbe.diagnostic(missing);
            require(diagnostic.get("requiredHistory") instanceof List<?> history && history.contains(source.document().blueId()),"Missing history is the exact supplied publication: "+diagnostic);
            require(missing.document().identity().equals(beforeCopy.identity())&&cold.emitted(missing).isEmpty(),"Missing history leaves state/effects unchanged");
            var sourceCopy=cold.importSnapshot(sourceWire,source.document().identity());
            cold.execution().chooseHistory(sourceCopy.blueId(),cold.execution().snapshot(sourceCopy));
            var completed=cold.process(beforeCopy,bindingEvent,3);
            require(completed.status().equals("APPLIED")&&completed.receipt().equals(bound.receipt()),"Only authentic history permits exact replay");
            System.out.println("PASS cold missing exact history refuses; authentic history restores exact receipt");
          }
        }
        if(Arrays.asList(args).contains("replay")) {
          var beforeWire=p.exportSnapshot(approved.document());
          var sourceWire=p.exportSnapshot(source.document());
          var afterWire=p.exportSnapshot(bound.document());
          try(var coldBlue=packages.language();var coldRuntime=new AuthoringRuntime(bindings)) {
            var cold=coldRuntime.processor(coldBlue);
            var sourceCopy=cold.importSnapshot(sourceWire,source.document().identity());
            cold.execution().chooseHistory(sourceCopy.blueId(),cold.execution().snapshot(sourceCopy));
            var beforeCopy=cold.importSnapshot(beforeWire,approved.document().identity());
            cold.execution().values().nativeRuntime().addEvidence(new LinkedHashMap<>(p.execution().values().nativeRuntime().evidence()));
            var replay=cold.process(beforeCopy,bindingEvent,3);
            requireApplied(cold,replay,"Cold replay applied");
            require(replay.document().identity().equals(bound.document().identity())&&replay.receipt().equals(bound.receipt()),"Cold replay exact identity and receipt");
            var afterCopy=cold.importSnapshot(afterWire,bound.document().identity());
            require(afterCopy.blueId().equals(bound.document().blueId()),"Cold committed identity");
            var duplicateEvent=event(afterCopy,"bindSource_owner",input);
            var duplicate=cold.process(afterCopy,duplicateEvent,4);
            requireApplied(cold,duplicate,"Same-origin duplicate accepted");
            System.out.println("DUPLICATE_DIAGNOSTIC "+WireData.write(m("before",afterCopy.blueId(),"after",duplicate.document().blueId(),"changes",duplicate.observations().get("changes"),"checkpoints",duplicate.observations().get("checkpoints"),"events",cold.emitted(duplicate))));
            duplicateOnlyCheckpoints(cold,afterCopy,duplicate,duplicateEvent);
            System.out.println("PASS cold replay exact receipt/identity and same-origin duplicate no effects");
          }
        }
      }
      System.out.println("PASS generated source binding modes="+modes+"; accessEvents="+accessEvents+", cyclic="+cyclic+", replay="+Arrays.asList(args).contains("replay")+", history="+Arrays.asList(args).contains("history"));
    }
  }
}
