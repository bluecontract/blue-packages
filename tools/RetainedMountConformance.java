import blue.language.next.WireData;
import java.nio.file.*;
import java.util.*;

/** Index generation must retain data dependencies without mounting their historical aliases. */
public final class RetainedMountConformance {
  @SuppressWarnings("unchecked") static Map<String,Object> map(Object o){return (Map<String,Object>)o;}
  public static void main(String[] args)throws Exception{
    Path source=Path.of(args[0]).toAbsolutePath(),root=Files.createTempDirectory("retained-mount-");
    try{
      var selection=map(WireData.parse(Files.readString(source.resolve("PACKAGE-SOURCES.json")),"json"));
      Files.writeString(root.resolve("PACKAGE-SOURCES.json"),WireData.write(Map.of("status","unpublished-candidate","foundations",List.of(),"packages",List.of("myos","myos-customer-expiry-direct"),"retainedArchives",selection.get("retainedArchives"))));
      try(var paths=Files.list(source)){for(Path path:paths.filter(Files::isDirectory).toList())Files.createSymbolicLink(root.resolve(path.getFileName()),path);}
      BuildPaymentFamily.main(new String[]{root.toString(),"__index_only__"});
      var catalogue=map(WireData.parse(Files.readString(root.resolve("PACKAGES.json")),"json"));
      var mounts=map(catalogue.get("mounts"));
      if(mounts.values().stream().map(RetainedMountConformance::map).anyMatch(row->Set.of("JBKJgWsAk7NhA9EX2LNCDtkP5HPPG6vC7DjuGqoEeSwc","9hVPM9LaGLNE5LxN8uZLAFFnjmi3MJW84eQ7G9csZpma").contains(row.get("blueId"))))throw new AssertionError("Retained legacy imports must not be active namespace mounts");
      if(!mounts.containsKey("MyOS")||!mounts.containsKey("BEX"))throw new AssertionError("Current/execution mounts must remain");
      byte[] first=Files.readAllBytes(root.resolve("PACKAGES.json"));
      BuildPaymentFamily.main(new String[]{root.toString(),"__index_only__"});
      if(!Arrays.equals(first,Files.readAllBytes(root.resolve("PACKAGES.json"))))throw new AssertionError("Repeated split-root index changed bytes");
      System.out.println("PASS retained import excluded from namespace mounts; repeated split-root index byte-identical");
    }finally{try(var paths=Files.walk(root)){for(Path path:paths.sorted(Comparator.reverseOrder()).toList())Files.delete(path);}}
  }
}
