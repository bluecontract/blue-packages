package blue.language.next;
import java.nio.file.*;
import java.util.*;
import com.fasterxml.jackson.databind.ObjectMapper;
public class PackageCheck {
  public static void main(String[] args) throws Exception {
    Path root=Path.of(args[0]);
    var rows=new ArrayList<Map<String,Object>>();
    BluePackage contracts=null;
    for (var slug: List.of("blue-language","blue-bex","blue-contracts")) {
      var p=BluePackage.open(root.resolve(slug+"/dist/package.bluepkg"));
      rows.add(Map.of("package",p.name(),"blueId",p.blueId(),"language",p.languageBlueId(),"exports",p.exports().size()));
      if(slug.equals("blue-contracts")) contracts=p;
    }
    try (var blue=Blue.builder().packages(PackageBundle.builder().mount("contracts",contracts).build()).build()) {
      var doc=blue.createYaml(Files.readString(root.resolve("blue-contracts/examples/counter.blue")));
      System.out.println(new ObjectMapper().writeValueAsString(Map.of("packages",rows,"authoredBlueId",doc.blueId(),"count",blue.query(doc,"/count",Query.INTEGER).require(),"exact",new ObjectMapper().readTree(doc.exactText()))));
    }
  }
}
