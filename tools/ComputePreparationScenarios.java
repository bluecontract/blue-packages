import blue.contracts.RuntimeBindings;
import blue.packages.ResellerScenarios;

/** Explicit experimental binding for the unchanged native scenario assertions. */
public final class ComputePreparationScenarios {
  public static void main(String[] args)throws Exception {
    int failed=ResellerScenarios.run(args,
        RuntimeBindings.accessEvents().withDefinitionReadV1().withComputePreparationV1());
    if(failed!=0)throw new AssertionError("Compute preparation scenarios failed: "+failed);
  }
}
