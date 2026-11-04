import blue.bex.BexError;
import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Declared dependencies use initialized exact paths without granting source approval. */
public final class SourcePathsDeclarationConformance {
  static Map<String,Object> m(Object... pairs){return BootstrapPreparationConformance.m(pairs);}
  static Map<String,Object> obj(Object value){return BootstrapPreparationConformance.obj(value);}
  static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    int failures=0;
    for(String variant:List.of("declared","missing-alias","wrong-type","wrong-field","missing-required-field","uninitialized","mixed","undeclared","undeclared-extra-path","extra-path")) {
      try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
        var p=runtime.processor(packages.language());var source=BootstrapPreparationConformance.source("bootstrap");
        var clauses=obj(source.get("clauses"));var activation=obj(obj(clauses.get("activation")).get("parameters"));
        activation.put("preActivationOperations",List.of("prepareOrder"));
        var clause=obj(clauses.get("orders"));var parameters=obj(clause.get("parameters"));
        var paths=m("order","");parameters.put("sourcePaths",paths);
        var declaration=m("type","Agreements/Agreement with Clauses","name","Private agreement");
        var declarations=m("order",declaration);obj(parameters.get("template")).put("sources",declarations);
        String expected=null;
        switch(variant){
          case "missing-alias"->{declarations.put("absent",m());expected="SOURCE_MAPPING_INCOMPLETE";}
          case "wrong-type"->{declaration.put("type","Orders/Order with Clauses");expected="SOURCE_DECLARATION_MISMATCH";}
          case "wrong-field"->{declaration.put("name","Other agreement");expected="SOURCE_DECLARATION_MISMATCH";}
          case "missing-required-field"->{declaration.put("requiredBusinessField","required-by-declaration");expected="SOURCE_DECLARATION_MISMATCH";}
          case "uninitialized"->{source.put("draft",m("name","Uninitialized"));paths.put("order","/draft");expected="SOURCE_NOT_INITIALIZED";}
          case "mixed"->{obj(clause.get("bindings")).put("sources",m("order","self"));expected="SOURCE_LEGACY_MAPPING_CONFLICT";}
          case "undeclared"->obj(parameters.get("template")).remove("sources");
          case "undeclared-extra-path"->{obj(parameters.get("template")).remove("sources");paths.put("alsoOrder","");}
          case "extra-path"->paths.put("alsoOrder","");
        }
        var host=BootstrapPreparationConformance.applied(p.initialize(source));
        check(!Boolean.TRUE.equals(p.read(host.document(),"/activation/active")),"Source must await commercial approval");
        var request=m("type","Documents/Preparation Input","key","one","values",m("size",42));
        var event=BootstrapPreparationConformance.event(host.document(),"prepareOrder",request);
        var result=p.process(host.document(),event,2);
        if(expected==null){
          check(result.commits(),variant+" rejected: "+ClauseGasProbe.diagnostic(result));
          var entries=obj(p.read(result.document(),"/process_orders/entries"));check(entries.size()==1,"One requirement");
          var item=obj(entries.values().iterator().next());String path=item.get("itemPath")+"/prepared/sources/order";
          var values=p.execution().values();
          String selected=NativeRuntime.identity(values.exact(values.select(new Exact.Ref(result.document().blueId()),path)));
          check(selected.equals(host.document().blueId()),"Exact initialized source reference preserved");
          check(!Boolean.TRUE.equals(p.read(result.document(),"/activation/active")),"Preparation cannot approve source");
        } else {
          check(!result.commits(),variant+" must reject");check(host.document().identity().equals(result.document().identity()),"Failure mutated source");
          String observed="";try{ClauseGasProbe.diagnose(p,host.document(),event,2);}catch(BexError error){observed=error.getMessage();}
          check(observed.contains(expected),variant+": expected "+expected+", got "+observed);
        }
        System.out.println("PASS "+variant);
      } catch(AssertionError failure){failures++;System.out.println("FAIL "+variant+": "+failure.getMessage());}
    }
    if(failures>0)throw new AssertionError(failures+" source-path declaration cases failed");
  }
}
