import blue.packages.QualificationRuntime;
import blue.contracts.*;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Current published payment inputs, with no inference from operation names at runtime. */
public final class PaymentInputConformance {
  static Map<String,Object> m(Object... pairs){return OperationInputConformance.m(pairs);}
  static void require(boolean value,String message){OperationInputConformance.require(value,message);}
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language()) {
      var runtime=new NativeRuntime(blue);var values=new Contracts(blue,QualificationRuntime.bindings()).execution().values();
      var definition=blue.admitDefinition(WireData.write(m("type","PaymentInstruction/Payment Instruction")));
      var contracts=NativeRuntime.head(NativeRuntime.recipe(NativeRuntime.exactOf(definition)),runtime).contracts;
      @SuppressWarnings("unchecked") var source=(Map<String,Object>)WireData.parse(Files.readString(root.resolve("payment-instruction/types/payment-instruction.blue")),"yaml");
      @SuppressWarnings("unchecked") var declared=(Map<String,Object>)source.get("contracts");int count=0;
      for(var entry:declared.entrySet()) {
        if(!(entry.getValue() instanceof Map<?,?> c)||!"Contracts/Sequential Workflow Operation".equals(c.get("type")))continue;
        count++;
        var actual=NativeRuntime.child(NativeRuntime.head(contracts,runtime),entry.getKey());
        require(NativeRuntime.head(actual,runtime).fields.containsKey("request"),"Payment input matcher missing: "+entry.getKey());
        var matcher=NativeRuntime.exact(NativeRuntime.child(NativeRuntime.head(actual,runtime),"request"),runtime);
        String operation=entry.getKey();Map<String,Object> input;
        if(operation.equals("acceptPaymentInstruction")) {
          require(values.matches(values.source(m()),matcher),"Acceptance must retain raw {} semantics");
          require(values.matches(values.source(m("reason","Accepted by user")),matcher),"Acceptance optional reason");
          continue;
        }
        if(operation.equals("rejectPaymentInstruction"))input=m("reason","Rejected by user");
        else if(operation.equals("recordTransactionInitiationFailed"))input=m("requestId","pending-1","reason","Failed initiation");
        else if(operation.equals("recordTransactionInitiated"))input=m("type","PaymentInstruction/Transaction Initiation Input","transactionId","transaction-1");
        else {
          boolean financial=List.of("secureFunds","declineSecureFunds","failSecureFunds","recordFundsSecuringUnknown",
              "completePayment","declineCompletePayment","failCompletePayment","recordPaymentCompletionUnknown",
              "cancelBeforeCompletion","declineCancelBeforeCompletion","failCancelBeforeCompletion","recordPaymentCancellationUnknown",
              "reverseAfterCompletion","declineReverseAfterCompletion","failReverseAfterCompletion","recordPaymentReversalUnknown").contains(operation);
          input=m("type",financial?"PaymentInstruction/Payment Outcome Input":"PaymentInstruction/Payment Control Input","requestId","pending-1");
          if(List.of("declineSecureFunds","failSecureFunds","recordFundsSecuringUnknown","declineCompletePayment","failCompletePayment","recordPaymentCompletionUnknown",
              "declineCancelBeforeCompletion","failCancelBeforeCompletion","recordPaymentCancellationUnknown","declineReverseAfterCompletion","failReverseAfterCompletion","recordPaymentReversalUnknown",
              "rejectPayeeAssignment","rejectTransactionDetailsUpdate","failTransactionDetailsUpdate","rejectFinalAmountResolution",
              "failPaymentCompletionLockChange","failPaymentReversalLockChange","failTransactionDetailsUpdateLockChange").contains(operation))input.put("reason","User explanation");
        }
        require(values.matches(values.source(input),matcher),"Minimal input must match: "+operation);
        for(String required:input.keySet())if(!required.equals("type")) {
          var missing=new LinkedHashMap<>(input);missing.remove(required);
          require(!values.matches(values.source(missing),matcher),"Required field "+operation+"/"+required);
          var wrong=new LinkedHashMap<>(input);wrong.put(required,7);
          boolean rejected;
          try { rejected=!values.matches(values.source(wrong),matcher); }
          catch(RuntimeException error) {
            if(!error.getMessage().equals("LANGUAGE_TypeCompatibilityViolation"))throw error;
            rejected=true;
          }
          require(rejected,"Wrong field type "+operation+"/"+required);
        }
      }
      require(count==36,"All36 current payment declarations must be covered");
      System.out.println("PASS all36 published payment input declarations");
    }
  }
}
