package blue.core;
import java.nio.file.*;
import java.util.*;
/** Real workflow initialization, self-payout validation and late correction. */
public final class StripeBankTransferExecutionConformance {
  static Map<String,Object> m(Object... p){var m=new LinkedHashMap<String,Object>();for(int i=0;i<p.length;i+=2)m.put((String)p[i],p[i+1]);return m;}
  static Map<String,Object> step(String op,String ch,Map<String,Object> input){return m("operation",op,"channel",ch,"request",input,"requireExactDocumentVersion",true);}
  public static void main(String[] a)throws Exception{
    Path root=Path.of(a[0]).toAbsolutePath().normalize(),reports=root.resolve("reports/stripe-withdrawals/execution");Files.createDirectories(reports);
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    for(boolean invalid:List.of(false,true)){
      var source=m("name","Withdraw own funds","type","MyOS/MyOS Stripe Bank Transfer Instruction","paymentTerms",m("amountMinor",100,"limitMinor",invalid?101:100,"currency","USD","payerChannel","payer","payeeChannel","payer","guarantorChannel","guarantor","allowedPayees",List.of("payer"),"recipientApprovalRequired",false),"paymentDetails",m("externalBankAccountId","ba_test"),"clauses",m("activation",m("type","Activation/Activation Clause","parameters",m("parties",m("payer",m("type","Parties/Party","representatives",m("agent",m("type","Parties/Representative"))),"guarantor",m("type","Parties/Party")),"required",List.of("payer","guarantor")))));
      var steps=new ArrayList<Object>();steps.add(step("approve_payer","payer",m("revision",1)));steps.add(step("approve_guarantor","guarantor",m("revision",1)));steps.add(step("acceptPaymentInstruction","guarantor",m()));
      var request=step("requestTransfer","payer",m("requestId","request-1"));
      if(invalid){request.put("status","FAILED");request.put("notEvents",List.of(m("kind","Transfer Requested")));request.put("expect",m("/bankTransfer/status","idle","/bankTransfer/requestId",""));steps.add(request);}
      else{request.put("events",List.of(m("kind","Transfer Requested")));request.put("expect",m("/bankTransfer/status","requested"));steps.add(request);steps.add(step("confirmTransfer","guarantor",m("requestId","request-1","reference","po_test","amountMinor",100,"currency","USD")));var failure=step("reportPayoutFailureAfterConfirmation","guarantor",m("type","MyOS/Stripe Payout Failure Input","requestId","request-1","reference","po_test","failureCode","account_closed"));failure.put("expect",m("/bankTransfer/status","failed_after_confirmation","/payment/completed",100,"/payment/reversed",0));failure.put("events",List.of(m("kind","Payout Failed After Confirmation")));steps.add(failure);var duplicate=new LinkedHashMap<>(failure);duplicate.remove("events");duplicate.put("notEvents",List.of(m("kind","Payout Failed After Confirmation")));steps.add(duplicate);var stale=step("confirmTransfer","guarantor",m("requestId","request-1","reference","po_test","amountMinor",100,"currency","USD"));stale.put("status","FAILED");steps.add(stale);}
      CurrentOperationScenarios.run(packages,reports,invalid?"invalid-terms.case.yaml":"late-failure.case.yaml",m("document","withdrawal.blue","initial",m("expect",m("/bankTransfer/status","idle")),"steps",steps),source);
    }
    System.out.println("PASS initialized Stripe transfer workflow, invalid request rollback, correction duplicate and stale paid");
  }
}
