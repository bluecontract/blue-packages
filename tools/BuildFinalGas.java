import blue.language.next.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Build a deliberately selected native edition from its authored definitions. */
public final class BuildFinalGas {
  @SuppressWarnings("unchecked") static Map<String,Object> map(Object v) { return (Map<String,Object>)v; }
  @SuppressWarnings("unchecked") static List<Object> list(Object v) { return (List<Object>)v; }
  static Object read(Path p) throws Exception { return WireData.json(WireData.write(WireData.parse(Files.readString(p), "yaml"))); }
  static String sha(Path p) throws Exception { return "sha256:"+HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p))); }
  public static void main(String[] args) throws Exception {
    Path root=Path.of(args[0]), p=root.resolve(args[1]);
    var c=map(read(p.resolve("blue-package.yaml")));
    if (!Boolean.TRUE.equals(c.get("previewOnly")))
      throw new IllegalArgumentException("This builder only replaces explicitly unpublished candidates");
    var builder=BluePackage.builder(c.get("name").toString(),c.get("version").toString()).namespace(c.get("namespace").toString());
    var locks=new TreeMap<String,Object>();
    var importedPackages=new LinkedHashMap<String,BluePackage>();
    for (var e:map(c.get("imports")).entrySet()) {
      String rel=map(e.getValue()).get("path").toString();Path path=p.resolve(rel).normalize();
      if(!path.startsWith(root)) throw new IllegalArgumentException("Dependency escapes source root");
      var dep=BluePackage.open(path);builder.importPackage(e.getKey(),dep);
      importedPackages.put(e.getKey(),dep);
      if(e.getKey().equals(c.get("language"))) builder.language(e.getKey(),dep);
      locks.put(e.getKey(),Map.of("path",rel,"packageBlueId",dep.blueId(),"archiveSha256",sha(path),"name",dep.name(),"version",dep.version()));
    }
    for(Object need:list(c.getOrDefault("executionRequires",List.of())))builder.executionRequires(need.toString());
    if(c.containsKey("protocol")) {
      var protocol=map(c.get("protocol"));String rules=protocol.get("rules").toString();
      if(!sha(p.resolve(rules)).equals(map(read(p.resolve("spec/frozen.json"))).get(rules)))throw new IllegalArgumentException("Unfrozen rules");
      var requires=new TreeMap<String,String>();map(protocol.getOrDefault("requires",Map.of())).forEach((k,v)->requires.put(k,v.toString()));
      builder.protocol(new ProtocolDefinition(protocol.get("name").toString(),protocol.get("status").toString(),new ProtocolDefinition.Asset(rules,Files.readString(p.resolve(rules)),sha(p.resolve(rules))),null,null,requires));
    }
    Map<String,Object> definitions=new LinkedHashMap<>();
    for(Object v:list(c.get("exports"))) {var e=map(v);definitions.put(e.get("name").toString(),read(p.resolve(e.get("path").toString())));}
    definitions=OperationInputs.publish(c.get("namespace").toString(),definitions,importedPackages);
    var ordered=new LinkedHashSet<String>();for(String name:definitions.keySet())BuildPaymentFamily.order(name,c.get("namespace")+"/",definitions,ordered,new HashSet<>());
    for(String name:ordered)builder.exportJson(name,WireData.write(definitions.get(name)));
    builder.documentation("README.md",Files.readString(p.resolve("README.md")));
    for(Object f:list(c.getOrDefault("files",List.of())))builder.documentation(f.toString(),Files.readString(p.resolve(f.toString())));
    Files.createDirectories(root.resolve("build"));Path temp=Files.createTempDirectory(root.resolve("build"),"final-gas-");
    Path output=temp.resolve("dist");var pkg=builder.write(output);BluePackage.archive(output,output.resolve("package.bluepkg"),PackageSelection.pinned(pkg.blueId()));
    Path dist=p.resolve("dist"), backup=temp.resolve("previous");if(Files.exists(dist))Files.move(dist,backup);
    try {Files.move(output,dist);}catch(Exception e){if(Files.exists(backup))Files.move(backup,dist);throw e;}
    BuildPaymentFamily.removeGenerated(temp);
    Files.writeString(p.resolve("blue-package.lock.json"),WireData.write(Map.of("format",2,"imports",locks))+"\n");
    System.out.println(WireData.write(Map.of("package",pkg.blueId(),"exports",pkg.exports())));
  }
}
