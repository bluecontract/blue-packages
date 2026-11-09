import blue.contracts.*;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Frozen real reseller prepareOrder inputs; optional baseline archives never touch running services. */
public final class ComputeDependenciesResellerConformance {
  static Map<String,Object> m(Object... pairs){return ComputeDependenciesConformance.m(pairs);}
  static Map<String,Object> obj(Object value){return ComputeDependenciesConformance.obj(value);}
  static Object read(Path path)throws Exception{return ComputeDependenciesConformance.read(path);}
  static void check(boolean value,String message){ComputeDependenciesConformance.require(value,message);}
  static void patch(Map<String,Object> source,String pointer,Object value) {
    var parts=pointer.substring(1).split("/");var parent=source;
    for(int i=0;i<parts.length-1;i++)parent=obj(parent.get(parts[i]));
    parent.put(parts[parts.length-1],value);
  }
  static Map<String,Object> run(Path root,Path baseline)throws Exception {
    return run(root,baseline,RuntimeBindings.accessEvents().withDefinitionReadV1());
  }
  static Map<String,Object> run(Path root,Path baseline,RuntimeBindings bindings)throws Exception {
    var bundle=PackageBundle.builder();
    var replacements=Map.of("Connections","connections.bluepkg","Documents","clause-documents.bluepkg","Reseller","clause-reseller.bluepkg");
    for(var mount:obj(obj(read(root.resolve("PACKAGES.json"))).get("mounts")).entrySet()) {
      Path path=baseline!=null&&replacements.containsKey(mount.getKey())?baseline.resolve(replacements.get(mount.getKey())):
          root.resolve(obj(mount.getValue()).get("path").toString());
      bundle.mount(mount.getKey(),BluePackage.open(path));
    }
    var scenario=obj(((List<?>)obj(read(root.resolve("examples/reseller/tests/bootstrap-preparation.case.json"))).get("scenarios")).getFirst());
    var source=obj(read(root.resolve("examples/reseller/adventures-in-paradise-preview.blue")));
    obj(scenario.get("sourcePatch")).forEach((path,value)->patch(source,path,value));
    var step=obj(((List<?>)scenario.get("steps")).getFirst());
    try(var blue=Blue.builder().packages(bundle.build()).build()) {
      var p=new Contracts(blue,bindings);
      var initialized=p.initialize(source);
      var row=m("arm",baseline==null?"candidate":"baseline","initializationStatus",initialized.status(),"initializationGas",initialized.gas());
      System.out.println(WireData.write(row));
      if(!initialized.commits()) {row.put("diagnostic",p.execution().outcome(initialized).diagnostic);return row;}
      var event=m("source","partner","operation",m("type","Contracts/Operation Request","channel",step.get("channel"),
          "operation",step.get("operation"),"request",step.get("request"),"document",m("blueId",initialized.document().blueId()),"requireExactDocumentVersion",true));
      var result=p.process(initialized.document(),event,((Number)step.get("timestampMicros")).longValue());
      row.put("operationStatus",result.status());row.put("operationGas",result.gas());
      if(!result.commits()){row.put("diagnostic",p.execution().outcome(result).diagnostic);return row;}
      var entries=obj(p.read(result.document(),"/process_orders/entries"));check(entries.size()==1,"One frozen preparation");
      var entry=obj(entries.values().iterator().next());var prepared=obj(entry.get("prepared"));
      row.put("amountMinor",prepared.get("amountMinor"));row.put("quote",prepared.get("quote"));row.put("status",entry.get("status"));
      row.put("documentBlueId",result.document().blueId());
      row.put("events",p.emitted(result));
      check(prepared.get("amountMinor").toString().equals("9310"),"USD 93.10 unchanged");
      check(entry.get("status").equals("awaiting_provider"),"Prepare does not bootstrap the order");
      return row;
    }
  }
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]);var rows=new ArrayList<Object>();
    if(args.length>1){var baseline=run(root,Path.of(args[1]));rows.add(baseline);System.out.println(WireData.write(baseline));}
    var candidate=run(root,null);rows.add(candidate);System.out.println(WireData.write(candidate));
    if(rows.size()==2&&candidate.containsKey("quote")&&obj(rows.getFirst()).containsKey("quote"))
      ComputeDependenciesConformance.equal(obj(rows.getFirst()).get("quote"),candidate.get("quote"),"Frozen business prices and lines");
    if(args.length>2)Files.writeString(Path.of(args[2]),WireData.write(rows)+"\n");
    check(candidate.get("initializationStatus").equals("APPLIED"),"Candidate must initialize under the unchanged 10M limit");
    check(candidate.get("operationStatus").equals("APPLIED"),"Candidate prepareOrder must succeed");
  }
}
