import blue.language.next.*;
import com.fasterxml.jackson.databind.*;
import com.fasterxml.jackson.databind.node.*;
import java.nio.file.*;
import java.util.*;

/** Build the root-clause dependency chain using only the generic Java package publisher. */
public class BuildAgreements {
  static final ObjectMapper JSON =
      new ObjectMapper().enable(SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS);
  static final List<String> NAMES =
      List.of(
          "blue-agreements",
          "clause-mutual-activation",
          "clause-immediate-termination",
          "agreement-reseller");

  static String sha(Path path) throws Exception {
    return "sha256:"
        + HexFormat.of()
            .formatHex(
                java.security.MessageDigest.getInstance("SHA-256")
                    .digest(Files.readAllBytes(path)));
  }

  static JsonNode manifest(Path archive) throws Exception {
    try (var zip = new java.util.zip.ZipFile(archive.toFile());
        var input = zip.getInputStream(zip.getEntry("package.json"))) {
      return JSON.readTree(input);
    }
  }

  static void write(Path path, Object value) throws Exception {
    Files.writeString(path, JSON.writerWithDefaultPrettyPrinter().writeValueAsString(value) + "\n");
  }

  static void removeTree(Path root) throws Exception {
    if (Files.exists(root))
      try (var paths = Files.walk(root)) {
        for (Path path : paths.sorted(Comparator.reverseOrder()).toList()) Files.delete(path);
      }
  }

  static void copyProject(Path source, Path target) throws Exception {
    try (var paths = Files.walk(source)) {
      for (Path path : paths.toList()) {
        Path relative = source.relativize(path);
        if (relative.getNameCount() > 0
            && (relative.getName(0).toString().equals("dist")
                || relative.getName(0).toString().startsWith(".build-"))) continue;
        Path out = target.resolve(relative);
        if (Files.isDirectory(path)) Files.createDirectories(out);
        else Files.copy(path, out);
      }
    }
  }

  public static void main(String[] args) throws Exception {
    if (args.length < 1 || args.length > 2 || (args.length == 2 && !args[1].equals("--check")))
      throw new IllegalArgumentException(
          "Usage: BuildAgreements.java <blue-packages-directory> [--check]");
    Path root = Path.of(args[0]).toAbsolutePath().normalize();
    if (args.length == 2) {
      Path candidate = Files.createTempDirectory("blue-agreements-build-");
      try {
        for (String name : NAMES) copyProject(root.resolve(name), candidate.resolve(name));
        for (String name :
            List.of("blue-language", "blue-bex", "blue-contracts", "blue-coordination")) {
          Path out = candidate.resolve(name + "/dist/package.bluepkg");
          Files.createDirectories(out.getParent());
          Files.copy(root.resolve(name + "/dist/package.bluepkg"), out);
        }
        build(candidate);
        for (String name : NAMES) {
          for (String file : List.of("dist/package.bluepkg", "blue-package.lock.json")) {
            if (Files.mismatch(
                    root.resolve(name).resolve(file), candidate.resolve(name).resolve(file))
                != -1) throw new IllegalStateException("Rebuild differs: " + name + "/" + file);
          }
        }
        System.out.println("All four publications and locks reproduce exactly.");
      } finally {
        removeTree(candidate);
      }
    } else build(root);
  }

  static void build(Path root) throws Exception {
    for (String name : NAMES) {
      Path project = root.resolve(name);
      var config = (ObjectNode) JSON.readTree(project.resolve("blue-package.yaml").toFile());
      if (name.equals("blue-agreements")) {
        var definition = JSON.readTree(project.resolve("types/clause-installer.blue").toFile());
        var step = JSON.readTree(project.resolve("types/clause-runtime-step.blue").toFile());
        if (!definition.path("functions").equals(step.path("functions")))
          throw new IllegalStateException(
              "Clause Installer and Clause Runtime Step functions differ");
      }
      var builder =
          BluePackage.builder(name, config.path("version").asText())
              .namespace(config.path("namespace").asText());
      var imports = new LinkedHashMap<String, BluePackage>();
      var locks = new TreeMap<String, Object>();
      var fields = config.path("imports").properties().iterator();
      while (fields.hasNext()) {
        var entry = fields.next();
        String prefix = entry.getKey(), relative = entry.getValue().path("path").asText();
        Path archive = project.resolve(relative);
        var pkg = BluePackage.open(archive);
        imports.put(prefix, pkg);
        builder.importPackage(prefix, pkg);
        if (prefix.equals(config.path("language").asText())) builder.language(prefix, pkg);
        locks.put(
            prefix,
            Map.of(
                "path",
                relative,
                "packageBlueId",
                pkg.blueId(),
                "archiveSha256",
                sha(archive),
                "name",
                pkg.name(),
                "version",
                pkg.version(),
                "repositoryIdentity",
                manifest(archive).path("repository").path("identity").asText()));
      }
      for (var need : config.path("executionRequires")) builder.executionRequires(need.asText());
      if (name.equals("agreement-reseller")) {
        Path source = project.resolve("types/reseller-agreement.blue");
        var value = (ObjectNode) JSON.readTree(source.toFile());
        value
            .putArray("clauseTypes")
            .add(imports.get("MutualActivation").exportId("Mutual Activation Clause"))
            .add(imports.get("ImmediateTermination").exportId("Immediate Termination Clause"));
        write(source, value);
      }
      builder.documentation(
          "README.md", Files.readString(project.resolve(config.path("readme").asText())));
      for (var file : config.path("files"))
        builder.documentation(file.asText(), Files.readString(project.resolve(file.asText())));
      for (var export : config.path("exports"))
        builder.exportFile(
            export.path("name").asText(),
            project.resolve(export.path("path").asText()),
            BlueFormat.JSON);
      Path temporary = Files.createTempDirectory(project, ".build-");
      Path built = temporary.resolve("dist");
      BluePackage pkg;
      try {
        pkg = builder.write(built);
      } catch (Failure failure) {
        System.err.println(failure.outcome());
        throw failure;
      }
      BluePackage.archive(
          built, temporary.resolve("package.bluepkg"), PackageSelection.pinned(pkg.blueId()));
      Files.copy(temporary.resolve("package.bluepkg"), built.resolve("package.bluepkg"));
      Path dist = project.resolve("dist");
      if (Files.exists(dist))
        try (var paths = Files.walk(dist)) {
          for (var path : paths.sorted(Comparator.reverseOrder()).toList()) Files.delete(path);
        }
      Files.move(built, dist);
      Files.delete(temporary.resolve("package.bluepkg"));
      Files.delete(temporary);
      write(project.resolve("blue-package.lock.json"), Map.of("format", 2, "imports", locks));
      System.out.println(name + " " + pkg.blueId());
    }
  }
}
