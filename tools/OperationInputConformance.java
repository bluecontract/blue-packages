import blue.language.next.*;
import blue.contracts.*;
import blue.bex.*;
import java.nio.file.*;
import java.util.*;

/** Small native qualification for authoring inputs; no deployed services or fixture mutations. */
public final class OperationInputConformance {
  static Map<String,Object> m(Object... pairs) {
    var result=new LinkedHashMap<String,Object>();
    for(int i=0;i<pairs.length;i+=2)result.put((String)pairs[i],pairs[i+1]);
    return result;
  }
  static void require(boolean value,String message) {if(!value)throw new AssertionError(message);}
  static String initializationDiagnostic(Contracts processor, Contracts.Result result) {
    if(result.status().equals("APPLIED"))return result.status();
    var summary=new LinkedHashMap<String,Object>();summary.put("status",result.status());
    Object raw=processor.execution().outcome(result).diagnostic;
    if(raw instanceof Map<?,?> diagnostic)for(String key:List.of("code","required","requiredHistory","path","location","document","member")) {
      Object value=diagnostic.get(key);
      if(value instanceof String text)summary.put(key,text.substring(0,Math.min(text.length(),256)));
      else if(value instanceof List<?> list)summary.put(key,list.stream().filter(String.class::isInstance).limit(16).toList());
    }
    return summary.toString();
  }
  static void nativeInputs(RuntimeBindings bindings, String edition) {
    try(var blue=Blue.builder().build()) {
      var values=new Contracts(blue,bindings).execution().values();
      var parent=values.source(m("name","Optional input","description","An input description",
          "optional",m("type","Text","description","May be omitted")),"definition");
      String id=NativeRuntime.identity(parent);
      var matcher=m("type",m("blueId",id),"required",m("type","Integer","description","Required count"));
      var exactMatcher=values.source(matcher,"definition");
      var typed=m("type",m("blueId",id),"required",7);
      require(values.matches(values.source(typed),exactMatcher),"Inherited abstract field must be optional");
      require(!values.matches(values.source(m("required",7)),exactMatcher),"Named matcher requires an explicit native type");
      require(!values.matches(values.source(m("type",m("blueId",id))),exactMatcher),"Authored required field must be present");
      require(!values.matches(values.source(m()),values.source(m("optional",m("type","Text","schema",m("required",false))),"definition")),
          "schema.required:false must not erase authored presence");
      require(values.matches(values.source("hello"),values.source(m("type","Text","description","A description is not a value"),"definition")),
          "Description must not become payload");
      require(values.matches(values.source(List.of("hello")),values.source(List.of(m("type","Text")),"definition")),"Native raw list matcher");
      var referenced=values.source(m("name","Existing document","required",7));
      require(values.matches(values.source(m("blueId",NativeRuntime.identity(referenced))),values.source(m("required",m("type","Integer")),"definition")),
          "Existing document reference must resolve canonically");
      var bex=new Bex(BexProfile.current());
      var source=m("functions",m("entry",m("args",m("input",matcher),"do",List.of(m("$return",m("$var","input"))))),
          "do",List.of(m("$return",m("$call",m("function","entry","args",m("input",m("$literal",typed)))))));
      var context=new BexContext(m(),m(),m(),Values.UNDEFINED,m(),m(),"/",null,
          (actual,pattern)->values.matches(values.source(actual),values.source(pattern,"definition")),null);
      bex.execute(bex.compile(source),context,100000);
      source.put("do",List.of(m("$return",m("$call",m("function","entry","args",m("input",m("$literal",m("type",m("blueId",id)))))))));
      boolean rejected=false;
      try {bex.execute(bex.compile(source),context,100000);}catch(BexError invalid){rejected=true;}
      require(rejected,"Native BEX must reject a missing required argument field");
      System.out.println("PASS "+edition+" native presence, labels, scalar/list/reference and BEX argument validation");
    }
  }
  static void publication(Path source,boolean payment)throws Exception {
    Path root=Files.createTempDirectory("operation-input-publication-");
    try {
      for(String name:List.of("blue-language","blue-contracts")) {
        Path dir=root.resolve(name+"/dist");Files.createDirectories(dir);
        Files.copy(source.resolve(name+"/dist/package.bluepkg"),dir.resolve("package.bluepkg"));
        Files.copy(source.resolve(name+"/blue-package.yaml"),dir.getParent().resolve("blue-package.yaml"));
      }
      Path fixture=root.resolve("fixture");Files.createDirectories(fixture);
      var library=m("name","Library","type","Contracts/Compute Definition","functions",m("approve",
          m("args",m("input",m("revision",m("type","Integer","description","Current document revision"))),
              "do",List.of(m("$return",true))),"respond",m("args",m("input",m("requestId",m("type","Text")),"kind",m("type","Text")),"do",List.of(m("$return",true)))));
      @SuppressWarnings("unchecked") var functions=(Map<String,Object>)library.get("functions");
      functions.put("businessField",m("args",m("input",m("requestFrom",m("type","Text"))),
          "do",List.of(m("$return",m("$var","input")))));
      var ordinaryLinkData=m("requestFrom",m("definition",m(),
          "function","approve","argument","input"));
      functions.put("businessData",m("args",m(),"do",List.of(m("$return",m("$literal",ordinaryLinkData)))));
      functions.put("optional",m("args",m("input",m("type","Fixture/Optional Input","requestId",m("type","Text"))),"do",List.of(m("$return",true))));
      functions.put("generate",m("args",m(),"do",List.of(m("$return",m("$literal",m(
          "type","Contracts/Sequential Workflow Operation","channel","owner","steps",List.of(),
          "$blue:requestFrom",m("definition",m("type","Fixture/Library"),"function","approve","argument","input")))))));
      var operation=m("name","Fixture","contracts",m("differentPublicName",m("type","Contracts/Sequential Workflow Operation",
          "channel","owner","$blue:requestFrom",m("definition",m("type","Fixture/Library"),"function","approve","argument","input"),
          "steps",List.of())));
      var externalLibrary=m("name","External library","type","Contracts/Compute Definition","functions",m("approve",
          m("args",m("input",m("proposalId",m("type","Text"))),"do",List.of(m("$return",true)))));
      Path externalDist=root.resolve("external/dist");
      var external=BluePackage.builder("external","0.0.0-test").namespace("External")
          .language(BluePackage.open(root.resolve("blue-language/dist/package.bluepkg")))
          .importPackage("Contracts",BluePackage.open(root.resolve("blue-contracts/dist/package.bluepkg")))
          .exportJson("Library",WireData.write(externalLibrary)).write(externalDist);
      BluePackage.archive(externalDist,externalDist.resolve("package.bluepkg"),PackageSelection.pinned(external.blueId()));
      Files.writeString(root.resolve("external/blue-package.yaml"),WireData.write(m("namespace","External")));
      var inherited=m("name","Inherited library","type","External/Library");
      Files.writeString(fixture.resolve("inherited.blue"),WireData.write(inherited));
      Files.writeString(fixture.resolve("optional.blue"),WireData.write(m("name","Optional Input","reason",m("type","Text","description","Optional explanation"))));
      @SuppressWarnings("unchecked") var contracts=(Map<String,Object>)operation.get("contracts");
      contracts.put("otherApprove",m("type","Contracts/Sequential Workflow Operation","channel","owner",
          "$blue:requestFrom",m("definition",m("type","Fixture/Inherited"),"function","approve","argument","input"),"steps",List.of()));
      contracts.put("explicitAdapter",m("type","Contracts/Sequential Workflow Operation","channel","owner","request",m(),
          "$blue:requestFrom",m("definition",m("type","Fixture/Library"),"function","approve","argument","input"),"steps",List.of()));
      for(String name:List.of("confirm","decline"))contracts.put(name,m("type","Contracts/Sequential Workflow Operation","channel","owner",
          "$blue:requestFrom",m("definition",m("type","Fixture/Library"),"function","respond","argument","input"),"steps",List.of()));
      contracts.put("optionalAction",m("type","Contracts/Sequential Workflow Operation","channel","owner",
          "$blue:requestFrom",m("definition",m("type","Fixture/Library"),"function","optional","argument","input"),"steps",List.of()));
      Files.writeString(fixture.resolve("library.blue"),WireData.write(library));
      Files.writeString(fixture.resolve("operation.blue"),WireData.write(operation));
      Files.writeString(fixture.resolve("README.md"),"# Native input fixture\n");
      var cfg=m("name","fixture","namespace","Fixture","version","0.0.0-test","previewOnly",true,"language","Language",
          "imports",m("Language",m("path","../blue-language/dist/package.bluepkg"),"Contracts",m("path","../blue-contracts/dist/package.bluepkg"),"External",m("path","../external/dist/package.bluepkg")),
          "executionRequires",List.of("Contracts"),"exports",List.of(m("name","Optional Input","path","optional.blue"),m("name","Library","path","library.blue"),m("name","Inherited","path","inherited.blue"),m("name","Fixture","path","operation.blue")));
      Files.writeString(fixture.resolve("blue-package.yaml"),WireData.write(cfg));Files.createDirectories(root.resolve("build"));
      Files.writeString(root.resolve("PACKAGE-SOURCES.json"),WireData.write(m("status","unpublished-candidate",
          "foundations",List.of("blue-language","blue-contracts","external"),"packages",List.of("fixture"))));
      if(payment)BuildPaymentFamily.main(new String[]{root.toString()});else BuildFinalGas.main(new String[]{root.toString(),"fixture"});
      var pkg=BluePackage.open(fixture.resolve("dist/package.bluepkg"));
      try(var blue=Blue.builder().packages(PackageBundle.builder().mount("Fixture",pkg).build()).build()) {
        var values=new Contracts(blue,RuntimeBindings.demandScopedEdition()).execution().values();
        var document=new Exact.Ref(pkg.exportId("Fixture"));
        var request=values.select(document,"/contracts/differentPublicName/request");
        require(request!=null,"Builder must publish requestFrom function input as contract.request");
        require(values.select(document,"/contracts/differentPublicName/$blue:requestFrom")==null,"Authoring marker must not be published");
        require(values.matches(m("revision",3),request),"Published matcher accepts valid public input");
        require(!values.matches(m(),request),"Published matcher requires revision");
        var other=values.select(document,"/contracts/otherApprove/request");
        require(values.matches(m("proposalId","proposal"),other),"Imported inherited function input must resolve");
        require(!values.matches(m("revision",3),other),"Same function name in different libraries must not collide");
        require(values.matches(m(),values.select(document,"/contracts/explicitAdapter/request")),"Explicit empty matcher must survive");
        require(values.select(document,"/contracts/approve")==null,"Functions must not become operations automatically");
        for(String name:List.of("confirm","decline")) {
          var responseMatcher=values.select(document,"/contracts/"+name+"/request");
          require(values.matches(m("requestId","request"),responseMatcher),"Shared respond must publish only its selected input argument");
          require(!values.matches(m(),responseMatcher),"Shared response requires requestId");
        }
        var optional=values.select(document,"/contracts/optionalAction/request");
        require(pkg.exportId("Optional Input").equals(values.head(optional).type),"Copied input must use final published named-type identity");
        require(values.matches(m("type",m("blueId",pkg.exportId("Optional Input")),"requestId","request"),optional),"Published inherited optional field may be omitted");
        @SuppressWarnings("unchecked") var libraryData=(Map<String,Object>)values.bexData(new Exact.Ref(pkg.exportId("Library")));
        var bex=new Bex(BexProfile.current());
        var program=bex.compile(m("do",List.of(m("$return",m("$call",m("function","generate","args",m()))))),libraryData,null);
        var context=new BexContext(m(),m(),m(),Values.UNDEFINED,m(),m(),"/",null,
            (actual,pattern)->values.matches(values.source(actual),values.source(pattern,"definition")),null);
        var businessMatcher=values.select(new Exact.Ref(pkg.exportId("Library")),"/functions/businessField/args/input");
        require(values.matches(m("requestFrom","customer text"),businessMatcher),"Ordinary requestFrom business field must survive publication");
        require(!values.matches(m(),businessMatcher),"Ordinary requestFrom business field remains required");
        var dataProgram=bex.compile(m("do",List.of(m("$return",m("$call",m("function","businessData","args",m()))))),libraryData,null);
        require(ordinaryLinkData.equals(bex.execute(dataProgram,context,100000).value()),
            "BEX literal data named requestFrom must survive, even with former instruction shape");
        @SuppressWarnings("unchecked") var generated=(Map<String,Object>)bex.execute(program,context,100000).value();
        require(!generated.containsKey("$blue:requestFrom")&&generated.containsKey("request"),"Native generator must return only the standard request matcher");
        require(values.matches(m("revision",4),generated.get("request")),"Generated request accepts its declared input");
      }
      contracts.put("invalidAdapter",m("request",m(),"$blue:requestFrom",m("definition",m("type","Fixture/Library"),
          "function","missingFunction","argument","input")));
      Files.writeString(fixture.resolve("operation.blue"),WireData.write(operation));
      boolean rejected=false;
      try {if(payment)BuildPaymentFamily.main(new String[]{root.toString()});else BuildFinalGas.main(new String[]{root.toString(),"fixture"});}
      catch(IllegalArgumentException error) {rejected=error.getMessage().contains("Invalid operation input link")&&error.getMessage().contains("missingFunction");}
      require(rejected,"Invalid explicit link must fail even beside an explicit request");
      System.out.println("PASS "+(payment?"BuildPaymentFamily":"BuildFinalGas")+" explicit input publication");
    } finally {BuildPaymentFamily.removeGenerated(root);}
  }
  public static void main(String[] args)throws Exception {
    if(args[0].equals("native")) {
      nativeInputs(RuntimeBindings.finalGas(), "final-gas");
      nativeInputs(RuntimeBindings.demandScopedEdition(), "demand-scoped");
    }
    else publication(Path.of(args[1]),args[0].equals("payment"));
  }
}
