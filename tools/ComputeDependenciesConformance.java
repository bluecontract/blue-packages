import blue.bex.*;
import blue.contracts.*;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Publication, actual Connections planning and native Compute qualification; no services. */
public final class ComputeDependenciesConformance {
  static Map<String,Object> m(Object... pairs) {
    var out=new LinkedHashMap<String,Object>();
    for(int i=0;i<pairs.length;i+=2)out.put((String)pairs[i],pairs[i+1]);
    return out;
  }
  @SuppressWarnings("unchecked") static Map<String,Object> obj(Object x){return (Map<String,Object>)x;}
  static void require(boolean condition,String message){if(!condition)throw new AssertionError(message);}
  static Object call(String name,Object... args){return m("$call",m("function",name,"args",m(args)));}
  static Object qualified(Blue blue,Map<String,Object> library){
    var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
    return m("connectionDependencies",ComputeDependencies.index(values,values.source(library,"definition")));
  }
  static Object copy(Object value){return WireData.json(WireData.write(value));}
  static void equal(Object a,Object b,String reason){require(WireData.write(a).equals(WireData.write(b)),reason);}
  static Set<String> selectedFunctions(Map<String,Object> compute){return obj(obj(compute.get("definition")).get("functions")).keySet();}
  static Object read(Path p)throws Exception{return WireData.json(WireData.write(WireData.parse(Files.readString(p),"yaml")));}
  static Map<String,Object> library() {
    var functions=m("price",m("args",m("quantity",m("type","Integer")),"expr",m("$multiply",List.of(m("$var","quantity"),m("$const","unitPrice")))));
    var constants=m("unitPrice",25);
    for(int i=0;i<24;i++) {
      constants.put("unused"+i,"unused-data-".repeat(128));
      functions.put("unused"+i,m("args",m(),"expr",m("$const","unused"+i)));
    }
    return m("type","Contracts/Compute Definition","functions",functions,"constants",constants);
  }
  static Map<String,Object> program(Object definition) {
    return m("type","Contracts/Compute","definition",definition,
        "do",List.of(m("$appendChange",m("op","replace","path","/total",
            "val",call("price","quantity",m("$event","/quantity"))))));
  }
  static Map<String,Object> select(Contracts processor,Object planning,Map<String,Object> compute,Object index) {
    var values=processor.execution().values();
    var bex=new Bex(BexProfile.current());
    var compiled=bex.compile(m("constants",m("clauseKey","fixture"),"do",List.of(m("$return",call("selectComputeDefinition",
        "compute",m("$literal",compute),"index",m("$literal",index))))),obj(planning),null);
    var context=new BexContext(m(),m(),m(),Values.UNDEFINED,m(),m(),"/",null,
        (actual,pattern)->values.matches(values.source(actual),values.source(pattern,"definition")),
        (value,gas)->NativeRuntime.identity(values.source(value,"definition")));
    return obj(bex.execute(compiled,context,10000000).value());
  }
  static Map<String,Object> linked(Contracts p,Blue blue,Object planning,Map<String,Object> library,Map<String,Object> program) {
    var index=obj(obj(qualified(blue,library)).get("connectionDependencies"));
    program.put("definition",m("blueId",index.get("definitionId")));
    return select(p,planning,program,index);
  }
  static void negative(Blue blue,Map<String,Object> library,String reason) {
    boolean rejected=false;
    try { qualified(blue,library); } catch(BexError failure) { rejected=true; }
    require(rejected,"Full publication validation: "+reason);
  }
  static void dependencies(Contracts p,Blue blue,Object planning) {
    var library=library();var fs=obj(library.get("functions"));
    fs.put("amount",m("args",m(),"expr",2));
    fs.put("other",m("args",m(),"expr",3));
    var branch=program(m());branch.put("do",List.of(m("$return",m("$choose",m("cond",m("$event","/choose"),
        "then",call("price","quantity",call("amount")),"else",call("other"))))));
    var both=linked(p,blue,planning,library,branch);
    equal(new TreeSet<>(selectedFunctions(both)),new TreeSet<>(Set.of("price","amount","other")),"Both branches and calls inside arguments");
    var override=program(m());override.put("functions",m("price",m("args",m("quantity",m("type","Integer")),"expr",call("other"))));
    var overridden=linked(p,blue,planning,library,override);
    require(selectedFunctions(overridden).equals(Set.of("other")),"Local override before closure");
    require(obj(obj(overridden.get("definition")).get("constants")).isEmpty(),"Overridden function does not retain old constant");
    equal(override.get("functions"),overridden.get("functions"),"All local functions retained");
    var changed=program(m());changed.put("functions",m("price",m("args",m("other",m()),"expr",1)));
    equal(changed,linked(p,blue,planning,library,changed),"Changed argument set keeps full validation");
    var pattern=program(m());pattern.put("functions",m("price",m("args",m("quantity",m("type","Integer","value",1)),"expr",1)));
    equal(pattern,linked(p,blue,planning,library,pattern),"Same argument names with a different pattern keep full validation");
    var defaults=obj(copy(library));obj(obj(obj(defaults.get("functions")).get("price")).get("args")).put("quantity",m("default",2));
    var droppedDefault=program(m());droppedDefault.put("functions",m("price",m("args",m("quantity",m()),"expr",1)));
    equal(droppedDefault,linked(p,blue,planning,defaults,droppedDefault),"Removing a default preserves full declaration validation");
    var badDefaultCaller=obj(copy(defaults));obj(badDefaultCaller.get("functions")).put("g",m("args",m(),"expr",call("price")));
    negative(blue,badDefaultCaller,"This BEX edition requires all argument names even when a pattern carries default metadata");
    var inherited=m("type",library,"functions",m("invoice",m("args",m(),"expr",call("price","quantity",4))));
    var inheritedProgram=program(m());inheritedProgram.put("do",List.of(m("$return",call("invoice"))));
    require(selectedFunctions(linked(p,blue,planning,inherited,inheritedProgram)).equals(Set.of("price","invoice")),"Native inheritance resolves before dependency selection");
    var knownPath=program(m());knownPath.put("constants",m("statePath","/process_orders/entry"));
    knownPath.put("do",List.of(m("$return",m("$document",m("$concat",List.of(m("$const","statePath"),"/fired"))))));
    require(obj(obj(linked(p,blue,planning,library,knownPath).get("definition")).get("functions")).isEmpty(),"Final local constant proves generated state path safe");
    var observedPath=obj(copy(knownPath));obj(observedPath.get("constants")).put("statePath","/contracts/calculate");
    equal(observedPath,linked(p,blue,planning,library,observedPath),"A local constant cannot redirect a read to its own definition");
    var literal=program(m());literal.put("do",List.of(m("$return",m("$literal",m("$call",m("function","absent"))))));
    require(selectedFunctions(linked(p,blue,planning,library,literal)).isEmpty(),"Literal data is not executable code");
    var mixedObject=m("$literal","ordinary object key","$call","ordinary call key","$const","ordinary constant key",
        "$currentContract","ordinary context key","$document","ordinary document key","computed",call("other"));
    var mixed=program(m());mixed.put("do",List.of(m("$return",mixedObject)));
    require(selectedFunctions(linked(p,blue,planning,library,mixed)).equals(Set.of("other")),"Only a singleton $literal is an operator");
    var mixedLibrary=obj(copy(library));obj(mixedLibrary.get("functions")).put("mixed",m("args",m(),"expr",mixedObject));
    var mixedCall=program(m());mixedCall.put("do",List.of(m("$return",call("mixed"))));
    require(selectedFunctions(linked(p,blue,planning,mixedLibrary,mixedCall)).equals(Set.of("mixed","other")),"Publication scanner matches the compiler's singleton operator rule");
    var deep=program(m());Object nested=1;for(int depth=0;depth<35;depth++)nested=m("nested",nested);
    deep.put("do",List.of(m("$return",nested)));equal(deep,linked(p,blue,planning,library,deep),"Traversal cap uses full fallback");
    var observed=obj(copy(library));obj(observed.get("functions")).put("price",m("args",m("quantity",m()),"expr",m("$currentContract","/definition")));
    var observe=program(m());equal(observe,linked(p,blue,planning,observed,observe),"Self-inspection retains full definition");
    var dynamic=program(m());dynamic.put("do",List.of(m("$return",m("$document",m("$event","/path")))));
    equal(dynamic,linked(p,blue,planning,library,dynamic),"Unproven dynamic document read retains full definition");
    var index=obj(obj(qualified(blue,library)).get("connectionDependencies"));
    var different=library();obj(different.get("functions")).put("extra",m("args",m(),"expr",1));
    var otherIndex=obj(obj(qualified(blue,different)).get("connectionDependencies"));
    var altered=program(m("blueId",otherIndex.get("definitionId")));equal(altered,select(p,planning,altered,index),"Changed library cannot reuse old qualification");
    for(String mode:List.of("function","constant","syntax","recursion")) {
      var invalid=obj(copy(library));var body=switch(mode) {
        case "function" -> call("missing");case "constant" -> m("$const","missing");
        case "syntax" -> m("$unknown",true);default -> call("bad");
      };
      obj(invalid.get("functions")).put("bad",m("args",m(),"expr",body));negative(blue,invalid,mode);
    }
    var localInvalid=program(m());localInvalid.put("functions",m("bad",m("args",m(),"expr",call("bad"))));
    localInvalid.put("do",List.of(m("$return",0)));
    var localSelected=linked(p,blue,planning,library,localInvalid);boolean rejected=false;
    try{new blue.bex.Compiler().compile(localSelected);}catch(BexError failure){rejected=failure.getMessage().contains("recursive function call graph");}
    require(rejected,"An unused local recursive function is never removed");
    var specification=m("functions",m("unit",m("args",m(),"expr",1)),"specification",m("name","Unsupported test specification"));
    var specIndex=obj(obj(qualified(blue,specification)).get("connectionDependencies"));
    var specProgram=m("definition",m("blueId",specIndex.get("definitionId")),"entry","unit");
    var specSelected=select(p,planning,specProgram,specIndex);
    equal(obj(specSelected.get("definition")).get("specification"),m("blueId",specIndex.get("specificationId")),"Projection never bypasses runtime specification checks: "+specSelected+" index "+specIndex);
    System.out.println("PASS inheritance, branches, argument calls, complete declarations, constants, literals, full validation and fallback");
  }
  static Contracts.Result execute(Contracts p,Object compute) {
    var initialized=p.initialize(m("total",0,"contracts",m(
        "in",m("type","Contracts/External Channel"),
        "calculate",m("type","Contracts/Sequential Workflow","channel","in","steps",List.of(compute)))));
    require(initialized.commits(),"Initialization: "+initialized.status());
    var result=p.process(initialized.document(),m("quantity",4),100);
    require(result.commits(),"Compute: "+result.status()+" "+p.execution().outcome(result).diagnostic);
    require(p.read(result.document(),"/total").toString().equals("100"),"Calculated total");
    return result;
  }
  static Map<String,Object> connections(Path root,Path baseline,String mode)throws Exception {
    boolean qualify=!mode.equals("fallback"), changed=mode.equals("modified"), custom=mode.equals("custom"), derived=mode.equals("derived");
    var bundle=PackageBundle.builder();var imports=new LinkedHashMap<String,BluePackage>();
    var catalog=obj(read(root.resolve("PACKAGES.json")));
    for(var mount:obj(catalog.get("mounts")).entrySet()) {
      Path path=baseline!=null&&mount.getKey().equals("Connections")?baseline
          :root.resolve(obj(mount.getValue()).get("path").toString());
      var pkg=BluePackage.open(path);bundle.mount(mount.getKey(),pkg);imports.put(mount.getKey(),pkg);
    }
    var clause=m("name","Quote Clause","type","Connections/Connected Clause","actionDefinition",m("type",library()),
        "actions",m("quote",m("do",List.of(m("$appendChange",m("op","replace","path","/total",
            "val",call("price","quantity",m("$var",m("name","params","path","/quantity")))))))));
    if(custom)try(var blue=Blue.builder().packages(bundle.build()).build()) {
      var values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      var canonical=values.source(m("type","Connections/Connection Plan"),"definition");
      var functions=new LinkedHashMap<String,Object>();
      for(String name:values.head(values.select(canonical,"/functions")).fields.keySet())
        functions.put(name,m("blueId",NativeRuntime.identity(values.exact(values.select(canonical,"/functions/"+name)))));
      functions.put("plan",m("args",m(),"do",List.of(
          m("$let",m("name","plan","expr",call("planConnections"))),
          m("$set",m("name","plan","expr",m("$pointerSet",m("object",m("$var","plan"),
              "path","/contracts/calculate/contract/steps/0/functions/suppliedLater",
              "val",m("$literal",m("args",m(),"expr",m("$const","customUnitPrice"))))))),
          m("$set",m("name","plan","expr",m("$pointerSet",m("object",m("$var","plan"),
              "path","/contracts/calculate/contract/steps/0/constants/customUnitPrice","val",25)))),
          m("$return",m("$var","plan")))));
      clause.put("type","Clauses/Clause");clause.put("hookAbi","document-context-1");
      clause.put("hookDefinition",m("type","Contracts/Compute Definition","constants",m("computeDependencyIndexes",m()),"functions",functions));
      obj(obj(obj(clause.get("actionDefinition")).get("type")).get("functions")).put("price",
          m("args",m("quantity",m("type","Integer")),"expr",m("$multiply",List.of(m("$var","quantity"),call("suppliedLater")))));
    }
    if(derived) {
      var parent=OperationInputs.publish("Fixture",m("Standard Parent",clause),imports).get("Standard Parent");
      var bodyPath="/contracts/calculate/contract/steps/0/do";
      var customPlan=m("args",m(),"do",List.of(
          m("$let",m("name","plan","expr",call("planConnections"))),
          m("$return",m("$pointerSet",m("object",m("$var","plan"),"path",bodyPath,"val",m("$listConcat",List.of(
              m("$pointerGet",m("object",m("$var","plan"),"path",bodyPath)),
              m("$literal",List.of(m("$appendChange",m("op","replace","path","/extra","val",call("unused0"))))))))))));
      // Adding expr is a native-compatible subtype extension; BEX prefers it to inherited do.
      clause=m("type",parent,"hookDefinition",m("functions",m("plan",m("expr",call("customPlan")),"customPlan",customPlan)));
    }
    var beforePublication=copy(clause);
    if(mode.equals("selected")) {
      var changedConstant=obj(copy(clause));
      changedConstant.put("hookDefinition",m("constants",m("clauseKey","custom-default")));
      var unchanged=OperationInputs.publish("Fixture",m("Constant Override Clause",changedConstant),imports).get("Constant Override Clause");
      equal(changedConstant,unchanged,"Changed used planner constants require full fallback even when functions match");
    }
    long publication=System.nanoTime();
    if(qualify)clause=obj(OperationInputs.publish("Fixture",m("Quote Clause",clause),imports).get("Quote Clause"));
    if(custom||derived)equal(beforePublication,clause,"Custom hook composition is not prematurely validated as a standard planner");
    publication=System.nanoTime()-publication;
    if(qualify) {
      // Ordinary document data cannot become a publication/compilation witness.
      clause.put("connectionDependencies",m("format","connections-compute-dependencies/1","definitionId","forged"));
    }
    if(changed) {
      var altered=library();obj(altered.get("functions")).put("unusedBad",m("args",m(),"expr",call("missing")));
      clause.put("actionDefinition",m("type",altered));
    }
    var source=m("name","Dependency selection fixture","type","Agreements/Agreement with Clauses","total",0,
        "contracts",m("owner",m("type","Contracts/External Channel","event",m("source","owner"))),
        "clauses",m("catalog",m("type",clause,"parameters",m(),"bindings",m("quote",m("calculate",m("on","workflow","party","owner",
            "params",m("quantity",m("$var",m("name","trigger","path","/quantity")))))))));
    if(derived)source.put("extra","");
    try(var blue=Blue.builder().packages(bundle.build()).build()) {
      var p=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1());
      var initialized=p.initialize(source);
      require(initialized.commits(),"Connections initialization: "+initialized.status()+" "+p.execution().outcome(initialized).diagnostic);
      var event=m("source","owner","operation",m("type","Contracts/Operation Request","channel","owner","operation","calculate",
          "document",m("blueId",initialized.document().blueId()),"request",m("quantity",4),"requireExactDocumentVersion",true));
      var result=p.process(initialized.document(),event,100);
      if(changed) {
        require(!result.commits(),"Modified exact actionDefinition must retain validation of unused invalid code");
        var diagnostic=p.execution().outcome(result).diagnostic;
        require(WireData.write(diagnostic).contains("BEX_COMPILE_ERROR"),"Fallback must preserve the compiler rejection: "+diagnostic);
        return m("arm","modified-definition-fallback","initializationGas",initialized.gas(),"operationGas",result.gas(),"status",result.status(),"diagnostic",diagnostic);
      }
      require(result.commits(),"Connections action: "+result.status()+" "+p.execution().outcome(result).diagnostic);
      equal(p.read(result.document(),"/total"),100,"Generated Connections handler must calculate the same total");
      if(derived)equal(p.read(result.document(),"/extra"),"unused-data-".repeat(128),
          "Derived custom hook must not reuse its parent's matching library index after adding a previously unused call");
      var nextEvent=obj(copy(event));obj(nextEvent.get("operation")).put("document",m("blueId",result.document().blueId()));
      obj(obj(nextEvent.get("operation")).get("request")).put("quantity",6);
      var second=p.process(result.document(),nextEvent,101);
      require(second.commits(),"Fresh call values must not invalidate immutable library preparation");
      equal(p.read(second.document(),"/total"),150,"Fresh second argument");
      return m("arm",baseline!=null?"original":derived?"derived-hook-fallback":custom?"custom-hook-fallback":qualify?"selected":"fallback","publicationNanos",publication,
          "initializationGas",initialized.gas(),"operationGas",result.gas(),"total",p.read(result.document(),"/total"));
    }
  }
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]);
    var planning=read(root.resolve("clause-connections/types/compute-dependency-planning-functions.blue"));
    try(var blue=Blue.builder().build()) {
      var p=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1());
      var values=p.execution().values();
      dependencies(p,blue,planning);
      var qualified=obj(qualified(blue,library()));
      var index=obj(qualified.get("connectionDependencies"));
      var compute=program(m("blueId",index.get("definitionId")));
      var selected=select(p,planning,compute,index);
      require(obj(obj(selected.get("definition")).get("functions")).keySet().equals(Set.of("price")),"Only needed function: "+selected);
      require(obj(obj(selected.get("definition")).get("constants")).keySet().equals(Set.of("unitPrice")),"Only needed constant");
      var full=execute(p,compute);var reduced=execute(p,selected);
      require(reduced.gas()<full.gas(),"First-use gas must decrease");
      require(execute(p,selected).gas()==reduced.gas(),"Warm native caches cannot discount logical gas");
      System.out.println(WireData.write(m("fullGas",full.gas(),"selectedGas",reduced.gas(),"total",p.read(reduced.document(),"/total"))));
    }
    if(args.length>1)System.out.println(WireData.write(connections(root,Path.of(args[1]),"fallback")));
    var full=connections(root,null,"fallback");var selected=connections(root,null,"selected");
    System.out.println(WireData.write(full));System.out.println(WireData.write(selected));
    require(((Number)selected.get("operationGas")).longValue()<((Number)full.get("operationGas")).longValue(),"Generated handler first-use gas must decrease");
    System.out.println(WireData.write(connections(root,null,"modified")));
    System.out.println(WireData.write(connections(root,null,"custom")));
    System.out.println(WireData.write(connections(root,null,"derived")));
  }
}
