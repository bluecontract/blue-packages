package blue.core;

import java.nio.file.Files;
import java.nio.file.Path;

/** Run a Blue document and its case file with the native package conformance runner. */
public final class RunCatalogueCase {
    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            throw new IllegalArgumentException("Expected package checkout, case YAML, and output directory");
        }
        Path packages = Path.of(args[0]).toRealPath();
        Path caseFile = Path.of(args[1]).toRealPath();
        Path output = Files.createDirectories(Path.of(args[2]).toAbsolutePath());
        var scenario = CurrentOperationScenarios.read(caseFile);
        String fileName = (String) scenario.get("document");
        var document = CurrentOperationScenarios.read(caseFile.resolveSibling(fileName));
        var catalogue = ClauseAppsExamples.packages(packages, document);
        CurrentOperationScenarios.run(catalogue, output, caseFile.getFileName().toString(), scenario, document);
    }
}
