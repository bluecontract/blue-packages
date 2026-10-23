package blue.core;

import blue.coordination.AuthoringRuntime;
import blue.contracts.RuntimeBindings;
import blue.contracts.ClauseGasProbe;
import blue.language.next.WireData;
import java.nio.file.*;
import java.util.*;

/** Runs maintained current-source scenarios against their exact selected package catalogue. */
public final class CurrentOperationScenarios {
  @SuppressWarnings("unchecked") static Map<String,Object> read(Path path)throws Exception {
    return (Map<String,Object>)CompositionPackages.yaml(path);
  }

  static Path caseFile(Path root,String prefix)throws Exception {
    try(var paths=Files.list(root.resolve("examples/apps"))) {
      return paths.filter(p->p.getFileName().toString().startsWith(prefix+"-")&&p.toString().endsWith(".case.yaml")).findFirst().orElseThrow();
    }
  }

  static void run(CompositionPackages packages,Path reports,String name,Map<String,Object> scenario,
      Map<String,Object> source)throws Exception {
    ClauseAppsExamples.wire(source);
    Path prepared=Files.createTempDirectory(reports,"case-");
    Files.writeString(prepared.resolve(scenario.get("document").toString()),WireData.write(source));
    Files.writeString(prepared.resolve(name),WireData.write(scenario));
    try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
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
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    Path reports=root.resolve("reports/operation-input/scenarios");Files.createDirectories(reports);
    for(int i=1;i<args.length;i++) {
      Path file=caseFile(root,args[i]);var scenario=read(file);
      run(packages,reports,file.getFileName().toString(),scenario,read(file.getParent().resolve(scenario.get("document").toString())));
      System.out.println("PASS current native scenario "+file.getFileName());
    }
  }
}
