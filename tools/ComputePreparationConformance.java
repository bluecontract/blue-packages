import blue.contracts.*;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Same real Reseller packages and input, with an explicitly selected experimental runtime. */
public final class ComputePreparationConformance {
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]);
    var before=ComputeDependenciesResellerConformance.run(root,null,RuntimeBindings.accessEvents().withDefinitionReadV1());
    before.put("arm","baseline-runtime");
    var after=ComputeDependenciesResellerConformance.run(root,null,RuntimeBindings.accessEvents().withDefinitionReadV1().withComputePreparationV1());
    after.put("arm","compute-preparation-v1");
    for(var row:List.of(before,after)) {
      ComputeDependenciesConformance.equal("APPLIED",row.get("initializationStatus"),"Initialization commits");
      ComputeDependenciesConformance.equal("APPLIED",row.get("operationStatus"),"Operation commits");
      System.out.println(WireData.write(row));
    }
    for(String field:List.of("quote","amountMinor","status","documentBlueId","events"))
      ComputeDependenciesConformance.equal(before.get(field),after.get(field),"Business and observable document equivalence: "+field);
    ComputeDependenciesConformance.require(((Number)after.get("operationGas")).longValue()<((Number)before.get("operationGas")).longValue(),"Real prepareOrder gas must decrease");
    if(args.length>1)Files.writeString(Path.of(args[1]),WireData.write(List.of(before,after))+"\n");
  }
}
