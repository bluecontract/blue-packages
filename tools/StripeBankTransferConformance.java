import blue.packages.QualificationRuntime;
import blue.contracts.*;
import blue.core.CompositionPackages;
import blue.language.next.*;
import blue.bex.*;
import java.nio.file.*;
import java.util.*;

/** Published schema and native BEX correction effects; no Stripe or deployed services. */
public final class StripeBankTransferConformance {
  static final String TYPE="MyOS/MyOS Stripe Bank Transfer Instruction";
  static Map<String,Object> m(Object... p){return ProviderInputConformance.m(p);}
  static void require(boolean b,String s){ProviderInputConformance.require(b,s);}
  static Map<String,Object> document(String status){
    return m("paymentTerms",m("payerChannel","payer","payeeChannel","payer","guarantorChannel","guarantor","amountMinor",100,"limitMinor",100,"currency","USD"),
      "paymentDetails",m("method","myos-stripe-bank-transfer","externalBankAccountId","ba_test"),
      "payment",m("accepted",true,"closed",false,"completed",Set.of("completed","failed_after_confirmation").contains(status)?100:0,"reversed",0,"transactionId","po_test"),
      "bankTransfer",m("requestId","request-1","status",status,"reference","po_test"));
  }
  static Engine.Result execute(Map<String,Object> input,Map<String,Object> doc,String channel){return ProviderInputConformance.execute(TYPE,"reportPayoutFailureAfterConfirmation",input,doc,channel);}
  static void rejected(Map<String,Object> input,Map<String,Object> doc,String channel){
    boolean rejected=false;try{execute(input,doc,channel);}catch(BexError failure){rejected=true;}
    require(rejected,"Invalid correction must fail: "+input+"/"+channel);
  }
  @SuppressWarnings("unchecked")
  public static void main(String[] args)throws Exception{
    Path root=Path.of(args[0]).toAbsolutePath();var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language()){
      ProviderInputConformance.blue=blue;
      ProviderInputConformance.values=new Contracts(blue,QualificationRuntime.bindings()).execution().values();
      ProviderInputConformance.runtime=new NativeRuntime(blue);
      for(String operation:List.of("reportTransferUnknown","declineTransfer")){
        var outcome=ProviderInputConformance.typed("ACME/Bank Transfer Outcome Input",m("requestId","request-1","reference","po_test"));
        ProviderInputConformance.change(ProviderInputConformance.execute(TYPE,operation,outcome,document("requested"),"guarantor"),"/bankTransfer/status",operation.equals("declineTransfer")?"declined":"unknown");
      }
      var input=ProviderInputConformance.typed("MyOS/Stripe Payout Failure Input",m("requestId","request-1","reference","po_test","failureCode","account_closed"));
      for(String field:List.of("requestId","reference","failureCode"))ProviderInputConformance.valid(TYPE,"reportPayoutFailureAfterConfirmation",input,field);
      Object matcher=ProviderInputConformance.matcher(TYPE,"reportPayoutFailureAfterConfirmation");
      var enriched=new LinkedHashMap<>(input);enriched.put("failureBalanceTransaction","txn_return");
      require(ProviderInputConformance.matches(enriched,matcher),"Optional return evidence accepted");
      var extra=new LinkedHashMap<>(input);extra.put("extra",true);
      require(!ProviderInputConformance.matches(extra,matcher),"Unexpected fields rejected");
      var result=execute(enriched,document("completed"),"guarantor");
      ProviderInputConformance.change(result,"/bankTransfer/status","failed_after_confirmation");
      require(result.changeset().stream().noneMatch(raw->raw instanceof Map<?,?> c&&Set.of("/payment/completed","/payment/reversed","/payment/transactionId","/bankTransfer/reference").contains(c.get("path"))),"Historical completion and refund totals preserved");
      require(result.events().size()==1,"One correction event");
      var duplicate=document("failed_after_confirmation");((Map<String,Object>)duplicate.get("bankTransfer")).put("payoutFailure",m("requestId","request-1","reference","po_test","failureCode","account_closed","failureBalanceTransaction","txn_return"));
      var retry=execute(enriched,duplicate,"guarantor");require(retry.changeset().isEmpty()&&retry.events().isEmpty(),"Duplicate correction no second effect");
      var conflict=new LinkedHashMap<>(enriched);conflict.put("failureCode","different");rejected(conflict,duplicate,"guarantor");
      for(String status:List.of("idle","requested","unknown","declined"))rejected(input,document(status),"guarantor");
      rejected(input,document("completed"),"payer");
      for(String field:List.of("requestId","reference")){var bad=new LinkedHashMap<>(input);bad.put(field,"different");rejected(bad,document("completed"),"guarantor");}
      boolean staleRejected=false;try{ProviderInputConformance.execute(TYPE,"confirmTransfer",m("requestId","request-1","reference","po_test","amountMinor",100,"currency","USD"),duplicate,"guarantor");}catch(BexError failure){staleRejected=true;}
      require(staleRejected,"Stale paid cannot overwrite late failure");
      System.out.println("PASS Stripe correction schema, authorization, prior-confirmation binding, historical evidence, duplicate and stale-paid effects");
    }
  }
}
