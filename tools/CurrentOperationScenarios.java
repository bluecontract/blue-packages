package blue.core;

import blue.packages.QualificationRuntime;
import blue.coordination.AuthoringRuntime;
import blue.contracts.RuntimeBindings;
import blue.contracts.ClauseGasProbe;
import blue.language.next.WireData;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Runs maintained current-source scenarios against their exact selected package catalogue. */
public final class CurrentOperationScenarios {
  @SuppressWarnings("unchecked") static Map<String,Object> read(Path path)throws Exception {
    return (Map<String,Object>)CompositionPackages.yaml(path);
  }

  static Path caseFile(Path root,String prefix)throws Exception {
    try(var paths=Files.list(root.resolve("examples/apps"))) {
      return paths.filter(path -> {
        String name = path.getFileName().toString();
        return name.endsWith(".case.yaml") && (name.equals(prefix + ".case.yaml") || name.startsWith(prefix + "-"));
      }).findFirst().orElseThrow(() -> new IllegalArgumentException("Unknown scenario: " + prefix));
    }
  }

  static void run(CompositionPackages packages,Path reports,String name,Map<String,Object> scenario,
      Map<String,Object> source)throws Exception {
    ClauseAppsExamples.wire(source);
    Path prepared=Files.createTempDirectory(reports,"case-");
    Files.writeString(prepared.resolve(scenario.get("document").toString()),WireData.write(source));
    Files.writeString(prepared.resolve(name),WireData.write(scenario));
    try(var runtime=new AuthoringRuntime(QualificationRuntime.bindings())) {
      try {
        CompositionExamples.run(packages,prepared.resolve(name),reports,()->runtime.processor(packages.language()));
      } catch(AssertionError|RuntimeException failure) {
        // Preserve actual initialization evidence when the maintained case fails before its first report row.
        var processor=runtime.processor(packages.language());var initial=processor.initialize(source);
        Files.writeString(reports.resolve(name+".initial-failure.json"),WireData.write(Values.map(
            "status",initial.status(),"events",processor.emitted(initial),"snapshot",initial.document().identity(),
            "failure",failure.toString(),"diagnostic",ClauseGasProbe.diagnostic(initial))));
        throw failure;
      }
    }
  }

  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]).toAbsolutePath();
    boolean historical = args.length > 1 && args[1].equals("--historical-payment");
    int firstCase = historical ? 2 : 1;
    if (args.length == firstCase) throw new IllegalArgumentException("Name at least one scenario");
    Path selection = root.resolve("PACKAGES.json");
    var retained = read(root.resolve("examples/apps/historical-payment-edition.json"));
    var retainedCases = CompositionPackages.obj(retained.get("examples"));
    if (historical) {
      selection = root.resolve(retained.get("catalogue").toString());
      var digest = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(selection)));
      if (!digest.equals(retained.get("catalogueSha256"))) throw new IllegalArgumentException("Historical catalogue checksum differs");
    }
    var packages=CompositionPackages.published(root, selection);
    Path reports=root.resolve(historical ? "reports/operation-input/scenarios-historical-payment" : "reports/operation-input/scenarios");
    Files.createDirectories(reports);
    for(int i=firstCase;i<args.length;i++) {
      Path file=caseFile(root,args[i]);
      String stem = file.getFileName().toString().replaceFirst("\\.case\\.yaml$", "");
      if (retainedCases.containsKey(stem) != historical)
        throw new IllegalArgumentException("Select the matching scenario edition for " + stem);
      var scenario=read(file);
      Path document = file.getParent().resolve(scenario.get("document").toString());
      if (historical) {
        var checksums = CompositionPackages.obj(retainedCases.get(stem));
        for (Path source : List.of(file, document)) {
          var digest = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source)));
          if (!digest.equals(checksums.get(source.getFileName().toString())))
            throw new IllegalArgumentException("Historical source checksum differs: " + source.getFileName());
        }
      }
      run(packages,reports,file.getFileName().toString(),scenario,read(document));
      System.out.println("PASS " + (historical ? "retained payment" : "current native") + " scenario " + file.getFileName());
    }
  }
}
