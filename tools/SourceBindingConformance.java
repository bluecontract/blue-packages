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
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var p=runtime.processor(blue);var values=p.execution().values();
      var original=p.initialize(agreement("Existing independent source"));require(original.status().equals("APPLIED"),"Source init");
      var source=p.process(original.document(),event(original.document(),"approve_owner",m("revision",p.read(original.document(),"/activation/revision"))),1);
      require(Boolean.TRUE.equals(p.read(source.document(),"/activation/active")),"Source active");
      p.execution().chooseHistory(source.document().blueId(),p.execution().snapshot(source.document()));
      String origin=NativeRuntime.identity(values.exact(values.select(new Exact.Ref(source.document().blueId()),"/contracts/initialized/document")));
      var matcher=values.select(values.source(m("type","Documents/Source Functions"),"definition"),"/functions/bindSourcePublic/args/input");
      for(String mode:List.of("typed-reference","typed-path","typed-both","typed-inherited","typed-missing","typed-uninitialized","legacy-reference","legacy-path")) {
        var host=agreement("Source receiver "+mode);host.put("sources",m());host.put("supplied",m("blueId",source.document().blueId()));
        @SuppressWarnings("unchecked") var clauses=(Map<String,Object>)host.get("clauses");
        var connection=m("on","workflow","party","owner","request",mode.startsWith("legacy")?m():m("blueId",NativeRuntime.identity(values.exact(matcher))));
        clauses.put("documentSources",m("type","Documents/Source Binding Clause","parameters",m("requirements",m("payer",m("origin",origin,"selectionPath",""))),
            "bindings",m("bind",m("bindSource_owner",connection))));
        var initialized=p.initialize(host);require(initialized.status().equals("APPLIED"),"Receiver init "+initialized.observations());
        var approved=p.process(initialized.document(),event(initialized.document(),"approve_owner",m("revision",p.read(initialized.document(),"/activation/revision"))),2);
        require(Boolean.TRUE.equals(p.read(approved.document(),"/activation/active")),"Receiver active");
        var input=m("alias","payer");if(!mode.startsWith("legacy"))input.put("type","Documents/Source Binding Input");
        if(mode.endsWith("reference")||mode.endsWith("both"))input.put("document",m("blueId",source.document().blueId()));
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
        if(mode.equals("typed-uninitialized"))input.put("document",m("blueId",NativeRuntime.identity(values.source(m("state","not-initialized")))));
        String exact=WireData.write(input);
        var bound=p.process(approved.document(),event(approved.document(),"bindSource_owner",input),3);
        if(mode.endsWith("missing")||mode.endsWith("uninitialized")) {
          require(!bound.commits(),"Missing or uninitialized source must remain rejected: "+mode);
          require(approved.document().blueId().equals(bound.document().blueId()),"Rejected source must not change receiver");
          continue;
        }
        require(bound.status().equals("APPLIED"),"Generated bindSource "+mode+": "+bound.status()+" "+bound.observations());
        var linked=values.select(new Exact.Ref(bound.document().blueId()),"/sources/payer");
        require(linked!=null&&source.document().blueId().equals(NativeRuntime.identity(values.exact(linked))),"Exact provided publication must be stored: "+mode);
        require(exact.equals(WireData.write(input)),"Reviewed request remains unchanged");
      }
      System.out.println("PASS generated source binding: typed reference/path, missing rejection, legacy raw and exact publication");
    }
  }
}
