import blue.contracts.*;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Native counterexamples for gas charged to unused definitions and visible pruning. */
public final class ComputeGasBoundaryConformance {
  static Map<String,Object> m(Object... pairs) { return ComputeDependenciesConformance.m(pairs); }
  static void check(boolean condition,String message) { ComputeDependenciesConformance.require(condition,message); }
  static Object call(String name) { return m("$call",m("function",name,"args",m())); }

  static Map<String,Object> library(int unused) {
    var functions=m("used",m("args",m(),"expr",7));
    for(int i=0;i<unused;i++)functions.put("unused"+i,m("args",m(),"expr",i));
    return m("type","Contracts/Compute Definition","functions",functions,"constants",m());
  }

  static Map<String,Object> compute(Object definition) {
    return m("type","Contracts/Compute","definition",definition,"do",List.of(
        m("$appendChange",m("op","replace","path","/total","val",call("used")))));
  }

  static Map<String,Object> run(Contracts p,Object compute,int count,String observedRoot) {
    var contracts=m("in",m("type","Contracts/External Channel"),
        "calculate",m("type","Contracts/Sequential Workflow","channel","in",
            "steps",new ArrayList<>(Collections.nCopies(count,compute))));
    if(observedRoot!=null) {
      String path=(observedRoot.isEmpty()?"/contracts":"")+"/calculate/steps/0/definition/functions";
      var read=m("$size",m("$keys",m("$pointerGet",m("object",m("$document",observedRoot),"path",path))));
      contracts.put("observer",m("type","Contracts/Sequential Workflow","channel","in","steps",List.of(
          m("type","Contracts/Compute","do",List.of(m("$appendChange",m("op","replace","path","/seen","val",read)))))));
    }
    var initialized=p.initialize(m("total",0,"seen",0,"contracts",contracts));
    check(initialized.commits(),"Initialize: "+initialized.status()+" "+p.execution().outcome(initialized).diagnostic);
    var result=p.process(initialized.document(),m("trigger",true),100);
    check(result.commits(),"Process: "+result.status()+" "+p.execution().outcome(result).diagnostic);
    check(p.read(result.document(),"/total").toString().equals("7"),"Same executed function result");
    return m("steps",count,"initializationGas",initialized.gas(),"operationGas",result.gas(),
        "total",p.read(result.document(),"/total"),"seen",p.read(result.document(),"/seen"));
  }

  public static void main(String[] args)throws Exception {
    var planning=ComputeDependenciesConformance.read(Path.of(args[0]).resolve("clause-connections/types/compute-dependency-planning-functions.blue"));
    try(var blue=Blue.builder().build()) {
      var p=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1());
      long firstSmall=0,firstLarge=0;
      for(int unused:List.of(0,1,24))for(int count:List.of(1,2,8)) {
        var result=run(p,compute(library(unused)),count,null);result.put("unused",unused);
        System.out.println(WireData.write(result));
        if(count==1&&unused==0)firstSmall=((Number)result.get("operationGas")).longValue();
        if(count==1&&unused==24)firstLarge=((Number)result.get("operationGas")).longValue();
      }
      var full=compute(library(1));
      var selected=ComputeDependenciesConformance.linked(p,blue,planning,library(1),full);
      for(String root:List.of("/contracts","")) {
        var original=run(p,full,1,root);var reduced=run(p,selected,1,root);
        check(original.get("seen").toString().equals("2"),"Observer sees the complete function map");
        check(reduced.get("seen").toString().equals("1"),"Observer detects a pruned function");
        System.out.println(WireData.write(m("observerRoot",root,"original",original,"pruned",reduced)));
      }
      if(args.length>1&&args[1].equals("--require-demand-pricing"))
        check(firstLarge<=firstSmall,"Unused functions increase first-use gas: "+firstSmall+" -> "+firstLarge);
      System.out.println("PASS native gas measurements and independent observer counterexamples");
    }
  }
}
