import blue.language.next.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Generic source-package publisher. Business logic is authored in the package .blue files. */
public final class BuildPaymentFamily {
  static final Map<Path,BluePackage> CACHE=new HashMap<>();
  static BluePackage open(Path path) throws Exception {
    path=path.toAbsolutePath().normalize();
    var found=CACHE.get(path);
    if(found==null) { found=BluePackage.open(path);CACHE.put(path,found); }
    return found;
  }
  @SuppressWarnings("unchecked") static Map<String,Object> map(Object o) { return (Map<String,Object>)o; }
  @SuppressWarnings("unchecked") static List<Object> list(Object o) { return (List<Object>)o; }
  static Object read(Path p) throws Exception { return WireData.json(WireData.write(WireData.parse(Files.readString(p), "yaml"))); }
  static String sha(Path p) throws Exception { return "sha256:"+HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p))); }
  static void references(Object v, String prefix, Set<String> names, Set<String> found) {
    if (v instanceof String s && s.startsWith(prefix) && names.contains(s.substring(prefix.length()))) found.add(s.substring(prefix.length()));
    else if(v instanceof Map<?,?> m) m.values().forEach(x->references(x,prefix,names,found));
    else if(v instanceof List<?> l) l.forEach(x->references(x,prefix,names,found));
  }
  static void removeGenerated(Path root) throws Exception {
    if(Files.exists(root)) try(var paths=Files.walk(root)) {
      for(Path p:paths.sorted(Comparator.reverseOrder()).toList()) Files.delete(p);
    }
  }
  static void order(String name,String prefix,Map<String,Object> definitions,Set<String> done,Set<String> visiting) {
    if(done.contains(name)) return;
    if(!visiting.add(name)) throw new IllegalArgumentException("Cyclic type definitions: "+name);
    var refs=new TreeSet<String>(); references(definitions.get(name),prefix,definitions.keySet(),refs);
    for(String ref:refs) order(ref,prefix,definitions,done,visiting);
    visiting.remove(name);done.add(name);
  }
  public static void main(String[] args) throws Exception {
    Path root=Path.of(args[0]).toAbsolutePath().normalize();
    var selection=map(read(root.resolve("PACKAGE-SOURCES.json")));
    if (!"unpublished-candidate".equals(selection.get("status")))
      throw new IllegalArgumentException("This publisher only rebuilds unpublished candidates");
    Set<String> only = args.length > 1 ? Set.of(args[1].split(",")) : Set.of();
    var rows=new ArrayList<Object>();var mounted=new TreeMap<String,Object>();
    for(Object item:list(selection.get("foundations"))) {
      Path archive=root.resolve(item.toString()).resolve("dist/package.bluepkg");var pkg=open(archive);
      String ns=map(read(archive.getParent().getParent().resolve("blue-package.yaml"))).get("namespace").toString();
      rows.add(Map.of("directory",item.toString(),"namespace",ns,"name",pkg.name(),"version",pkg.version(),"packageBlueId",pkg.blueId(),"path",root.relativize(archive).toString(),"archiveSha256",sha(archive)));
      mounted.put(ns,Map.of("path",root.relativize(archive).toString(),"blueId",pkg.blueId(),"archiveSha256",sha(archive)));
    }
    for(Object item:list(selection.get("packages"))) {
      Path source=root.resolve(item.toString());var cfg=map(read(source.resolve("blue-package.yaml")));
      if (!Boolean.TRUE.equals(cfg.get("previewOnly")))
        throw new IllegalArgumentException("Refusing to overwrite a non-preview package: "+source);
      String ns=cfg.get("namespace").toString();
      if (!only.isEmpty() && !only.contains(ns)) {
        Path archive=source.resolve("dist/package.bluepkg");var pkg=open(archive);
        rows.add(Map.of("directory",item.toString(),"namespace",ns,"name",pkg.name(),"version",pkg.version(),"packageBlueId",pkg.blueId(),"path",root.relativize(archive).toString(),"archiveSha256",sha(archive)));
        mounted.put(ns,Map.of("path",root.relativize(archive).toString(),"blueId",pkg.blueId(),"archiveSha256",sha(archive)));
        // Foundation mounts are taken from the declared, exact repository paths too.
        for(var e:map(cfg.get("imports")).entrySet()) if(!mounted.containsKey(e.getKey())) {
          Path dep=source.resolve(map(e.getValue()).get("path").toString()).normalize();var imported=open(dep);
          mounted.put(e.getKey(),Map.of("path",root.relativize(dep).toString(),"blueId",imported.blueId(),"archiveSha256",sha(dep)));
        }
        continue;
      }
      var builder=BluePackage.builder(cfg.get("name").toString(),cfg.get("version").toString()).namespace(ns);
      var importedPackages=new LinkedHashMap<String,BluePackage>();
      var locks=new TreeMap<String,Object>();
      for(var entry:map(cfg.get("imports")).entrySet()) {
        String relative=map(entry.getValue()).get("path").toString();Path path=source.resolve(relative).normalize();
        if(!path.startsWith(root)) throw new IllegalArgumentException("Dependency outside blue-packages: "+path);
        var pkg=open(path);builder.importPackage(entry.getKey(),pkg);
        importedPackages.put(entry.getKey(),pkg);
        if(entry.getKey().equals(cfg.get("language"))) builder.language(entry.getKey(),pkg);
        var pin=Map.of("path",relative,"packageBlueId",pkg.blueId(),"archiveSha256",sha(path),"name",pkg.name(),"version",pkg.version());
        locks.put(entry.getKey(),pin);
        mounted.put(entry.getKey(),Map.of("path",root.relativize(path).toString(),"blueId",pkg.blueId(),"archiveSha256",sha(path)));
      }
      for(Object need:list(cfg.get("executionRequires"))) builder.executionRequires(need.toString());
      if(cfg.containsKey("protocol")) {
        var protocol=map(cfg.get("protocol"));String path=protocol.get("rules").toString();String rules=Files.readString(source.resolve(path));
        if(!sha(source.resolve(path)).equals(map(read(source.resolve("spec/frozen.json"))).get(path))) throw new IllegalArgumentException("Frozen rules differ: "+source);
        var requirements=new TreeMap<String,String>();map(protocol.get("requires")).forEach((k,v)->requirements.put(k,v.toString()));
        builder.protocol(new ProtocolDefinition(protocol.get("name").toString(),protocol.get("status").toString(),new ProtocolDefinition.Asset(path,rules,sha(source.resolve(path))),null,null,requirements));
      }
      Map<String,Object> definitions=new LinkedHashMap<>();
      for(Object e:list(cfg.get("exports"))) {var export=map(e);definitions.put(export.get("name").toString(),read(source.resolve(export.get("path").toString())));}
      definitions=OperationInputs.publish(ns,definitions,importedPackages);
      var ordered=new LinkedHashSet<String>();for(String name:definitions.keySet()) order(name,ns+"/",definitions,ordered,new HashSet<>());
      for(String name:ordered) {
        if(cfg.containsKey("protocol") && !map(definitions.get(name)).containsKey("specification")) throw new IllegalArgumentException("Native source needs explicit rules reference: "+name);
        builder.exportJson(name,WireData.write(definitions.get(name)));
      }
      builder.documentation("README.md",Files.readString(source.resolve("README.md")));
      Path staging=Files.createTempDirectory(root.resolve("build"),"payment-candidate-");
      Path prepared=staging.resolve("dist");var pkg=builder.write(prepared);
      BluePackage.archive(prepared,prepared.resolve("package.bluepkg"),PackageSelection.pinned(pkg.blueId()));
      // These explicitly unpublished distributions may be rebuilt; published archives are untouched.
      Path dist=source.resolve("dist"),backup=staging.resolve("previous");
      if(Files.exists(dist)) Files.move(dist,backup);
      try { Files.move(prepared,dist); }
      catch(Exception failure) { if(Files.exists(backup)) Files.move(backup,dist);throw failure; }
      removeGenerated(staging);
      Path archive=dist.resolve("package.bluepkg");
      CACHE.put(archive.toAbsolutePath().normalize(),pkg);
      Files.writeString(source.resolve("blue-package.lock.json"),WireData.write(Map.of("format",2,"imports",locks))+"\n");
      var row=Map.of("directory",item.toString(),"namespace",ns,"name",pkg.name(),"version",pkg.version(),"packageBlueId",pkg.blueId(),"path",root.relativize(archive).toString(),"archiveSha256",sha(archive));
      rows.add(row); mounted.put(ns,Map.of("path",root.relativize(archive).toString(),"blueId",pkg.blueId(),"archiveSha256",sha(archive)));
      System.out.println(ns+" "+pkg.blueId());
    }
    Files.writeString(root.resolve("PACKAGES.json"),WireData.write(Map.of("format","blue-package-catalog/2","status","unpublished-candidate","packages",rows,"mounts",mounted))+"\n");
  }
}
