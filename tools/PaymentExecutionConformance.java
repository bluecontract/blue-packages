package blue.core;

import blue.contracts.RuntimeBindings;
import blue.language.next.WireData;
import java.nio.file.*;
import java.util.*;

/** Native execution evidence for every current payment response and configured request action. */
public final class PaymentExecutionConformance {
  static final Set<String> ACTIONS=Set.of("approveRecipient","requestSecureFunds","requestCompletePayment",
      "requestReverseAfterCompletion","requestCancelBeforeCompletion","requestPayeeAssignment",
      "requestTransactionDetailsUpdate","requestFinalAmountResolution","requestPaymentCompletionLock",
      "requestPaymentCompletionUnlock","requestPaymentReversalLock","requestPaymentReversalUnlock",
      "requestTransactionDetailsUpdateLock","requestTransactionDetailsUpdateUnlock");
  @SuppressWarnings("unchecked") static Map<String,Object> object(Object value){return (Map<String,Object>)value;}
  @SuppressWarnings("unchecked") static List<Object> list(Object value){return (List<Object>)value;}

  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]).toAbsolutePath();
    String catalogue=Files.readString(root.resolve("PACKAGES.json"));
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    if(!catalogue.equals(Files.readString(root.resolve("PACKAGES.json"))))
      throw new AssertionError("Package candidate changed while opening the execution catalogue");
    Path reports=root.resolve("reports/operation-input/payment-execution");Files.createDirectories(reports);
    var declared=object(CurrentOperationScenarios.read(root.resolve("payment-instruction/types/payment-instruction.blue")).get("contracts"));
    var responses=new TreeSet<String>();
    declared.forEach((name,raw)->{if("Contracts/Sequential Workflow Operation".equals(object(raw).get("type")))responses.add(name);});
    if(responses.size()!=36)throw new AssertionError("Expected all36 current payment response declarations");
    var checkedResponses=new TreeSet<String>();var checkedActions=new TreeSet<String>();var outcomes=new ArrayList<Object>();
    for(String prefix:List.of("27","28","29","recipient")) {
      Path file=CurrentOperationScenarios.caseFile(root,prefix.equals("recipient")?"27":prefix);
      var scenario=CurrentOperationScenarios.read(file);
      var source=CurrentOperationScenarios.read(file.resolveSibling(scenario.get("document").toString()));
      String name=file.getFileName().toString();
      if(prefix.equals("recipient")) {
        name="recipient-approval.case.yaml";
        object(source.get("paymentTerms")).put("recipientApprovalRequired",true);
        var steps=new ArrayList<Object>(list(scenario.get("steps")).subList(0,4));
        steps.add(Map.of("operation","approveRecipient","channel","seller","request",Map.of(),
            "requireExactDocumentVersion",true,"expect",Map.of("/payment/recipientApproved",true),
            "events",List.of(Map.of("kind","Recipient Approved"))));
        scenario.put("steps",steps);
      }
      try {
        CurrentOperationScenarios.run(packages,reports,name,scenario,source);
        var rows=list(WireData.parse(Files.readString(reports.resolve(name+".json")),"json"));
        for(Object raw:rows) {
          var row=object(raw);var input=object(row.get("input"));String operation=String.valueOf(input.get("operation"));
          if(!"APPLIED".equals(row.get("status")))continue;
          // A committed admission alone is insufficient: require actual emitted event or asserted state.
          boolean effect=!list(row.get("events")).isEmpty()||!object(row.get("reads")).isEmpty();
          if(effect&&responses.contains(operation))checkedResponses.add(operation);
          if(effect&&ACTIONS.contains(operation))checkedActions.add(operation);
        }
        outcomes.add(Map.of("case",name,"result","PASS","evidence",name+".json"));
      } catch(AssertionError|RuntimeException failure) {
        outcomes.add(Map.of("case",name,"result","FAIL","reason",failure.toString()));
        System.err.println("FAIL "+name+": "+failure);
      }
    }
    var missingResponses=new TreeSet<>(responses);missingResponses.removeAll(checkedResponses);
    var missingActions=new TreeSet<>(ACTIONS);missingActions.removeAll(checkedActions);
    boolean unchanged=catalogue.equals(Files.readString(root.resolve("PACKAGES.json")));
    if(!unchanged)outcomes.add(Map.of("case","candidate-identity","result","FAIL","reason","Package candidate changed during execution"));
    boolean passed=unchanged&&missingResponses.isEmpty()&&missingActions.isEmpty()&&outcomes.stream().allMatch(row->"PASS".equals(object(row).get("result")));
    var summary=new LinkedHashMap<String,Object>();summary.put("result",passed?"PASS":"FAIL");
    summary.put("runtime",RuntimeBindings.accessEvents().withDefinitionReadV1().identities());summary.put("packages",WireData.parse(catalogue,"json"));
    summary.put("cases",outcomes);summary.put("responsesWithNativeEffect",checkedResponses);summary.put("actionsWithNativeEffect",checkedActions);
    summary.put("missingResponses",missingResponses);summary.put("missingActions",missingActions);
    Files.writeString(reports.resolve("summary.json"),WireData.write(summary));
    if(!passed)throw new AssertionError("Native payment execution incomplete; see "+reports.resolve("summary.json"));
    System.out.println("PASS all36 payment responses and14 request actions with native effects and deterministic replay");
  }
}
