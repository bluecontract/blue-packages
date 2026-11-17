import blue.contracts.*;
import blue.bex.Values;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Narrow native BEX boundary checks; no Stripe or hosted execution. */
public final class CommissionRecoveryConformance {
  static Map<String,Object> m(Object... xs){var out=new LinkedHashMap<String,Object>();for(int i=0;i<xs.length;i+=2)out.put((String)xs[i],xs[i+1]);return out;}
  @SuppressWarnings("unchecked") static Map<String,Object> o(Object x){return (Map<String,Object>)x;}
  static Map<String,Object> load(Path root,String path)throws Exception{return o(WireData.parse(Files.readString(root.resolve(path)),"yaml"));}
  static Map<String,Object> copy(Map<String,Object> value){return o(WireData.json(WireData.write(value)));}
  static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
  static void denied(Runnable action,String why){boolean rejected=false;try{action.run();}catch(RuntimeException expected){rejected=true;}check(rejected,why);}
  static Map<String,Object> adjustment(long gross,long retained,long net,long fee){return m("grossMinor",gross,"retainedGrossMinor",retained,"sellerRecoveryMinor",8750,"payouts",net+fee==0?List.of():List.of(m("payoutInstructionId","a2a-1","grossMinor",net+fee,"netMinor",net,"feeMinor",fee)));}
  static blue.bex.Engine.Result run(Contracts p,Map<String,Object> functions,Map<String,Object> document,String function,Map<String,Object> args,String channel){
    return run(p,functions,document,function,args,channel,m());
  }
  static blue.bex.Engine.Result run(Contracts p,Map<String,Object> functions,Map<String,Object> document,String function,Map<String,Object> args,String channel,Map<String,Object> event){
    var v=p.execution().values();var exact=v.source(document);var c=new blue.bex.Engine.Context();c.document=v.view(exact);c.bindings=m("call",m("channel",channel));c.event=v.view(v.source(event));
    c.readDocument=(path,view,doc)->v.view(v.select(exact,path));c.matcher=(a,b)->{var actual=v.source(Values.blueValue(a));var pattern=v.source(Values.blueValue(b),"definition");return v.matches(actual,pattern);};c.nodeBlueId=(a,g)->NativeRuntime.identity(v.source(Values.blueValue(a)));
    return p.execution().evaluator().execute(m("functions",functions,"constants",m("sourceMode","workflow","clauseKey","commission","bindings",m("state","/commission","orders","/orders","payouts","/payouts","rate","/terms/commissionBps","catalog","/catalog","quotes","/quotes","fulfilment","/absent")),"do",List.of(m("$return",m("$call",m("function",function,"args",args))))),c,10000000);
  }
  public static void main(String[] args)throws Exception{
    var root=Path.of(args[0]);System.setProperty("blue.package.root",root.toString());var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())){
      var p=runtime.processor(blue);var v=p.execution().values();
      if(args.length>1&&args[1].equals("--factory")){factoryCommissionFields(p,root);return;}
      if(args.length>1&&args[1].equals("--funding")){fundingModes(p,root);return;}
      if(args.length>1&&args[1].equals("--agreement")){agreementRecovery(p,root);frozenAccrual(p,root);bookingSnapshots(p,root);fundingModes(p,root);return;}
      var generic=args.length>1?o(WireData.parse(Files.readString(Path.of(args[1])),"yaml")):load(root,"payment-instruction/types/payment-functions.blue");var functions=o(v.bexData(v.source(generic.get("functions"))));

      var helper=root.resolve("clause-reseller/types/customer-commission-recovery-functions.blue");check(Files.exists(helper),"Missing optional guarantor recovery clause helper");
      functions.putAll(o(v.bexData(v.source(load(root,"clause-reseller/types/customer-commission-recovery-functions.blue").get("functions")))));
      refundIntent(p,functions);
      invalidAmounts(p,functions);
      var adjustment=adjustment(1000,0,800,200);
      run(p,functions,m(),"validateCommissionAdjustment",m("candidate",adjustment),"guarantor");
      var bad=copy(adjustment);bad.put("grossMinor",999);
      denied(()->run(p,functions,m(),"validateCommissionAdjustment",m("candidate",bad),"guarantor"),"Wrong G total accepted");
      var pi=m("contracts",m("initialized",m("document",m("name","original customer PI"))),"paymentTerms",m("guarantorChannel","guarantor","amountMinor",10000),
          "paymentDetails",m("customerPaymentTerms",m("commissionTerms",m("grossMinor",1000,"commissionBps",1000,"adjustmentPolicy","BLUE_ROUND_BPS_V1","recoveryPolicy","BLUE_SCT_SOURCE_RECOVERY_V1"))),
          "payment",m("accepted",true,"reversed",10000,"requests",m("refund-1",m("status","succeeded","intent",m("action","refund","amountMinor",10000)))));
      var noPolicy=copy(pi);o(o(o(noPolicy.get("paymentDetails")).get("customerPaymentTerms")).get("commissionTerms")).remove("recoveryPolicy");
      var report=copy(adjustment);report.put("requestId","refund-1");report.put("recoveryId","recovery-1");
      denied(()->run(p,functions,pi,"confirmRecovery",m("input",report),"payer"),"Payer cannot report external recovery");
      denied(()->run(p,functions,noPolicy,"confirmRecovery",m("input",report),"guarantor"),"Missing accepted policy allowed report");
      var pending=copy(pi);o(o(o(pending.get("payment")).get("requests")).get("refund-1")).put("status","pending");
      denied(()->run(p,functions,pending,"confirmRecovery",m("input",report),"guarantor"),"Unconfirmed customer refund allowed report");
      var result=run(p,functions,pi,"confirmRecovery",m("input",report),"guarantor");
      check(result.changeset().size()==1&&result.events().size()==1,"Actual report must persist once and emit once");
      pi.put("commissionRecoveries",v.bexData(v.source(Values.blueValue(o(result.changeset().getFirst()).get("val")))));
      var duplicate=run(p,functions,pi,"confirmRecovery",m("input",report),"guarantor");
      check(duplicate.changeset().isEmpty()&&duplicate.events().isEmpty(),"Duplicate must not persist or emit twice");
      var conflict=copy(report);conflict.put("sellerRecoveryMinor",8749);
      denied(()->run(p,functions,pi,"confirmRecovery",m("input",conflict),"guarantor"),"Changed duplicate accepted");
      var extra=copy(report);extra.put("recoveryId","recovery-2");
      denied(()->run(p,functions,pi,"confirmRecovery",m("input",extra),"guarantor"),"Second report exceeded accepted policy cumulative original G");
      nativeFirstReport(p,functions);
      policyBounds(p,functions);
      bookingSnapshots(p,root);
      factoryCommissionFields(p,root);
      agreementRecovery(p,root);
      frozenAccrual(p,root);
      fundingModes(p,root);
      for(String file:List.of("customer-orders-clause","customer-orders-bootstrap-clause")){
        var source=load(root,"clause-reseller/types/"+file+".blue");var definition=v.source(m("type",o(source.get("actionDefinition")).get("type")));
        var prep=o(v.bexData(v.select(definition,"/functions")));check(prep.containsKey("prepareCommissionTerms"),"Missing trusted parent scalar prep");
        var agreement=m("contracts",m("initialized",m("document",m("name","agreement"))),"terms",m("commissionBps",333),"activation",m("parties",m("partner",m("myosAccountId","trusted-partner"))));
        var scalar=run(p,prep,agreement,"prepareCommissionTerms",m("amountMinor",10050),"seller");
        check(o(scalar.value()).get("grossMinor").toString().equals("335"),"Native half-up commission rounding changed");
        check(o(scalar.value()).get("beneficiaryAccountId").equals("trusted-partner"),"Wrong trusted recipient");
        o(agreement.get("terms")).remove("commissionBps");
        check(o(run(p,prep,agreement,"prepareCommissionTerms",m("amountMinor",10050),"seller").value()).isEmpty(),"Legacy absence must stay empty");
      }
      System.out.println("PASS native adjustment arithmetic; guarantor auth; report/replay/conflict/cumulative limits; accepted amount-only recovery policy; both parent scalar preparations and half-up rounding");
    }
  }
  static void nativeFirstReport(Contracts p,Map<String,Object> functions){
    var report=m("recoveryId","native-first","requestId","refund-1","grossMinor",50,"retainedGrossMinor",50,"sellerRecoveryMinor",450,"payouts",List.of());
    var terms=m("grossMinor",100,"commissionBps",1000,"adjustmentPolicy","BLUE_ROUND_BPS_V1","recoveryPolicy","BLUE_SCT_SOURCE_RECOVERY_V1");
    // Reuse the already-qualified native payment fixture; never seed its financial state.
    Map<String,Object> source;
    try{source=o(WireData.json(WireData.write(AccountPayoutCancellationConformance.source(
        Path.of(System.getProperty("blue.package.root")))).replace("seller","payer")));}
    catch(Exception failure){throw new RuntimeException(failure);}
    source.put("type","MyOS/MyOS Test Customer Payment Instruction");
    o(source.get("paymentTerms")).put("amountMinor",1000);o(source.get("paymentTerms")).put("limitMinor",1000);
    source.put("paymentDetails",m("customerPaymentTerms",m("commissionTerms",terms)));
    var clauses=o(source.get("clauses"));clauses.remove("accountSettlement");
    o(o(clauses.get("activation")).get("parameters")).remove("preActivationOperations");
    clauses.put("commissionRecovery",m("type","Reseller/Customer Commission Recovery Clause","bindings",
        m("confirm",m("report",m("on","workflow","party","guarantor","params",m("input",m("$var","trigger")))))));
    var bindings=m();
    for(var pair:List.of(List.of("requestAuthorize","secureRecovery","secure-1"),
        List.of("requestCapture","captureRecovery","capture-1"),List.of("requestRefund","refundRecovery","refund-1")))
      bindings.put(pair.get(0),m(pair.get(1),m("on","workflow","party","guarantor","params",
          m("requestId",pair.get(2),"amountMinor",1000))));
    clauses.put("payment",m("type","PaymentInstruction/Payment Request Actions","bindings",bindings));
    var ordinary=copy(source);o(ordinary.get("clauses")).remove("commissionRecovery");
    var plain=p.initialize(ordinary);check(plain.commits(),"Plain customer component initialization failed");
    check(!nativeContracts(p,plain.document()).containsKey("report"),"Uncommissioned instruction exposed recovery operation");
    check(!o(loadUnchecked("myos/types/customer-instruction.blue").get("contracts")).containsKey("confirmCommissionRecovery"),"Shared Customer PI still owns recovery");
    var initialized=p.initialize(source);check(initialized.status().equals("APPLIED"),"Native report fixture initialization failed: "+initialized.receipt());
    check(nativeContracts(p,initialized.document()).containsKey("report"),"Optional recovery operation was not mounted on typed Customer PI");
    var nativeProgram=o(p.execution().values().bexData(p.execution().values().source(nativeContracts(p,initialized.document()).get("report"))));
    var actionSteps=(List<?>)o(((List<?>)nativeProgram.get("steps")).getFirst()).get("do");
    int guardIndex=-1,recoveryIndex=-1;
    for(int index=0;index<actionSteps.size();index++){
      var call=o(actionSteps.get(index)).get("$call");
      if(call instanceof Map<?,?>){if("requireActive".equals(o(call).get("function")))guardIndex=index;
        if("confirmRecovery".equals(o(call).get("function")))recoveryIndex=index;}
    }
    check(guardIndex>=0&&recoveryIndex>guardIndex,"Mounted recovery must enforce the maintained active-party guard before financial report validation");
    for(String scenario:List.of("inactive","revoked","access")){
      var refusedSource=copy(source);o(refusedSource.get("clauses")).remove("activation");
      var state=m("active",!scenario.equals("inactive"),"parties",m());
      if(scenario.equals("access"))state.put("parties",m("guarantor",m("readerKeys",List.of("reader"),"lead",m("channel",RepresentativeAccessConformance.channel("guarantor")))));
      refusedSource.put("activation",state);
      // Contracts exposes the BEX rejection category, not the domain message. Check the exact
      // maintained guard separately on the same state, and its position in the native program above.
      String expectedGuard=switch(scenario){case "inactive"->"DOCUMENT_NOT_ACTIVE";case "revoked"->"REPRESENTATIVE_NO_LONGER_AUTHORIZED";default->"PARTICIPANT_ACCESS_MISSING";};
      try{run(p,functions,refusedSource,"requireActive",m("channel","guarantor","workflow",true),"guarantor");throw new AssertionError("Guard accepted "+scenario);}
      catch(blue.bex.BexError expected){check(expected.getMessage().contains(expectedGuard),"Wrong guard refusal for "+scenario+": "+expected.getMessage());}
      var refusedDoc=p.initialize(refusedSource);check(refusedDoc.commits(),"Guard fixture initialization failed: "+scenario);
      check(nativeContracts(p,refusedDoc.document()).containsKey("report"),"Guard fixture lost mounted operation: "+scenario);
      var deniedInput=AccountPayoutCancellationConformance.input(refusedDoc.document(),"guarantor","report",report);
      var refused=p.process(refusedDoc.document(),deniedInput,1);
      check(!refused.commits()&&refused.document().blueId().equals(refusedDoc.document().blueId())&&p.emitted(refused).isEmpty(),"Inactive/revoked/access-invalid instruction reported recovery: "+scenario);
    }
    var document=initialized.document();long time=10;
    document=AccountPayoutCancellationConformance.apply(p,document,"payer","approve_payer",m("revision",1),time++);
    document=AccountPayoutCancellationConformance.apply(p,document,"guarantor","acceptPaymentInstruction",m(),time++);
    document=AccountPayoutCancellationConformance.apply(p,document,"guarantor","provideSession",
        m("type","MyOS/Customer Session Input","sessionId","recovery-session"),time++);
    document=AccountPayoutCancellationConformance.apply(p,document,"guarantor","confirmFunding",m("sessionId","recovery-session"),time++);
    document=AccountPayoutCancellationConformance.apply(p,document,"guarantor","recordTransactionInitiated",
        m("type","PaymentInstruction/Transaction Initiation Input","transactionId","native-recovery-transaction",
            "railType","test","attachmentPoint","instruction","providerReference","local-no-psp"),time++);
    for(var pair:List.of(List.of("secureRecovery","secureFunds","secure-1"),
        List.of("captureRecovery","completePayment","capture-1"),List.of("refundRecovery","reverseAfterCompletion","refund-1"))){
      document=AccountPayoutCancellationConformance.apply(p,document,"guarantor",pair.get(0),m(),time++);
      document=AccountPayoutCancellationConformance.apply(p,document,"guarantor",pair.get(1),
          m("type","PaymentInstruction/Payment Outcome Input","requestId",pair.get(2)),time++);
    }
    check(((Number)p.read(document,"/payment/completed")).longValue()==1000&&
        ((Number)p.read(document,"/payment/reversed")).longValue()==1000&&
        "succeeded".equals(p.read(document,"/payment/requests/refund-1/status")),"Recovery fixture must use actual native completed payment and successful refund");
    var wrongActor=p.process(document,AccountPayoutCancellationConformance.input(document,"payer","report",report),time++);
    check(!wrongActor.commits()&&wrongActor.document().blueId().equals(document.blueId())&&p.emitted(wrongActor).isEmpty(),"Payer executed guarantor-only native recovery operation");
    var operation=AccountPayoutCancellationConformance.input(document,"guarantor","report",report);
    var first=p.process(document,operation,time++);
    check(first.status().equals("APPLIED"),"First native report patch failed: "+first.status()+" "+first.receipt()+" "+first.observations());
    check(p.read(first.document(),"/commissionRecoveries/native-first/recoveryId").equals("native-first"),"First native report was not durably applied");
    var retry=AccountPayoutCancellationConformance.input(first.document(),"guarantor","report",report);
    var duplicate=p.process(first.document(),retry,time++);
    check(duplicate.status().equals("APPLIED")&&p.emitted(duplicate).isEmpty(),"Native duplicate report failed or re-emitted business event: "+duplicate.status()+" "+duplicate.observations()+" "+p.emitted(duplicate));
    var secondReport=copy(report);secondReport.put("recoveryId","native-second");
    var secondOperation=AccountPayoutCancellationConformance.input(duplicate.document(),"guarantor","report",secondReport);
    var second=p.process(duplicate.document(),secondOperation,time++);
    check(second.status().equals("APPLIED"),"Second native report failed: "+second.observations());
    check(p.read(second.document(),"/commissionRecoveries/native-first/recoveryId").equals("native-first")&&p.read(second.document(),"/commissionRecoveries/native-second/recoveryId").equals("native-second"),"New root-map report overwrote existing receipt");
    System.out.println("PASS native first recovery patch without preseeded map; duplicate preserves receipt and emits nothing");
  }
  static Map<String,Object> nativeContracts(Contracts p,Contracts.Document document){
    return o(o(WireData.json(p.toJson(document))).get("contracts"));
  }
  static Map<String,Object> loadUnchecked(String path){try{return load(Path.of(System.getProperty("blue.package.root")),path);}catch(Exception e){throw new RuntimeException(e);}}
  static void invalidAmounts(Contracts p,Map<String,Object> functions){
    for(String field:List.of("grossMinor","retainedGrossMinor","sellerRecoveryMinor","payoutGrossMinor","netMinor","feeMinor")){
      for(Object bad:Arrays.asList(null,"1",1.5,-1,1000000000001L)){
        var value=adjustment(1000,0,800,200);
        var target=field.equals("payoutGrossMinor")||field.equals("netMinor")||field.equals("feeMinor")?o(((List<?>)value.get("payouts")).getFirst()):value;
        target.put(field.equals("payoutGrossMinor")?"grossMinor":field,bad);String error=bad==null?"function argument pattern rejected: candidate":target==value?"COMMISSION_ADJUSTMENT_AMOUNT_INVALID":"COMMISSION_ADJUSTMENT_PAYOUT_AMOUNT_INVALID";
        try{run(p,functions,m(),"validateCommissionAdjustment",m("candidate",value),"guarantor");throw new AssertionError("Invalid amount accepted "+field+" "+bad);}
        catch(blue.bex.BexError expected){check(expected.getMessage().contains(error),"Changed amount validation error for "+field+"="+bad+": "+expected.getMessage());}
      }
    }
  }
  static void policyBounds(Contracts p,Map<String,Object> functions){
    var v=p.execution().values();
    var terms=m("grossMinor",335,"commissionBps",333,"adjustmentPolicy","BLUE_ROUND_BPS_V1","recoveryPolicy","BLUE_SCT_SOURCE_RECOVERY_V1");
    var requests=m("refund-1",m("status","succeeded","intent",m("action","refund","amountMinor",2500)));
    var pi=m("contracts",m("initialized",m("document",m("name","rounding origin"))),"paymentTerms",m("guarantorChannel","guarantor","amountMinor",10050),"paymentDetails",m("customerPaymentTerms",m("commissionTerms",terms)),"payment",m("accepted",true,"reversed",2500,"requests",requests));
    var first=m("recoveryId","r1","requestId","refund-1","grossMinor",84,"retainedGrossMinor",84,"sellerRecoveryMinor",2416,"payouts",List.of());
    var tooMuch=copy(first);tooMuch.put("grossMinor",85);tooMuch.put("retainedGrossMinor",85);tooMuch.put("sellerRecoveryMinor",2415);
    denied(()->run(p,functions,pi,"confirmRecovery",m("input",tooMuch),"guarantor"),"Independent refund rounding exceeded frozen cumulative G target");
    var one=run(p,functions,pi,"confirmRecovery",m("input",first),"guarantor");
    pi.put("commissionRecoveries",v.bexData(v.source(Values.blueValue(o(one.changeset().getFirst()).get("val")))));
    o(pi.get("payment")).put("reversed",10050);requests.put("refund-2",m("status","succeeded","intent",m("action","refund","amountMinor",7550)));
    var last=m("recoveryId","r2","requestId","refund-2","grossMinor",251,"retainedGrossMinor",251,"sellerRecoveryMinor",7299,"payouts",List.of());
    check(run(p,functions,pi,"confirmRecovery",m("input",last),"guarantor").changeset().size()==1,"Full refund did not admit exact remaining original G");
    terms.put("grossMinor",336);
    denied(()->run(p,functions,pi,"confirmRecovery",m("input",last),"guarantor"),"Original G inconsistent with accepted rounding was trusted");
    System.out.println("PASS native cumulative partial/full refund rounding; original G conflict; no external correction input");
  }
  static void factoryCommissionFields(Contracts p,Path root)throws Exception{
    var v=p.execution().values();
    var nativeFactory=load(root,"clause-documents/types/functions.blue");
    for(String name:List.of("customer-orders-clause","customer-orders-bootstrap-clause")){
      var clause=load(root,"clause-reseller/types/"+name+".blue");
      var constructor=name.equals("customer-orders-clause")?o(o(nativeFactory.get("functions")).get("constructDocument")):
          o(o(o(clause.get("actionDefinition")).get("type")).get("functions"));
      if(!name.equals("customer-orders-clause"))constructor=o(constructor.get("constructDocument"));
      Object fieldStep=null;
      for(Object step:(List<?>)constructor.get("do")){
        var each=o(step).get("$forEach");
        if(each instanceof Map<?,?> && "nextValue".equals(o(each).get("item"))&&"field".equals(o(each).get("key"))){fieldStep=step;break;}
      }
      check(fieldStep!=null,"Factory lost approved-field copy loop");
      var config=m("args",m(),"do",List.of(m("$return",clause.get("parameters"))));
      var steps=List.of(m("$let",m("name","child","expr",m())),fieldStep,m("$return",m("$var","child")));
      var functions=o(v.bexData(v.source(m("configurationParameters",config,"factoryFieldsForTest",m("args",m("input",m()),"do",steps)))));
      var accepted=m("grossMinor",335,"commissionBps",333,"beneficiaryAccountId","trusted-partner");
      var result=run(p,functions,m(),"factoryFieldsForTest",m("input",m("fields",m("customerCommissionTerms",accepted))),"seller");
      var expectedAccepted=v.bexData(v.source(accepted));
      check(o(result.value()).get("customerCommissionTerms").equals(expectedAccepted),"Factory did not copy trusted commissionTerms exactly: "+name+" actual="+WireData.write(result.value())+" expected="+WireData.write(expectedAccepted));
      check(!o(run(p,functions,m(),"factoryFieldsForTest",m("input",m("fields",m())),"seller").value()).containsKey("customerCommissionTerms"),"Absent commission field invented by factory");
    }
    System.out.println("PASS native approved field-copy loops retain trusted commission terms in both constructors; no duplicate assignment needed");
  }
  static void fundingModes(Contracts p,Path root)throws Exception{
    var v=p.execution().values();
      var payoutSource=load(root,"clause-reseller/types/commission-account-payouts-clause.blue");
      var payoutDefinition=v.source(m("type",o(payoutSource.get("actionDefinition")).get("type")));
      var payoutFuncs=o(v.bexData(v.select(payoutDefinition,"/functions")));
      check(o(run(p,payoutFuncs,m(),"executionTermsFromContext",m("context",m()),"seller").value()).equals(m("executionPolicy","BLUE_ACCOUNT_PAYOUT_STOP_V1")),"Test context requires stop policy without fundingModel");
      for(String mode:List.of("SCT","LEGACY_ACCOUNT_DEBIT"))check(o(run(p,payoutFuncs,m(),"executionTermsFromContext",m("context",m("fundingModel",mode)),"seller").value()).equals(m("executionPolicy","BLUE_ACCOUNT_PAYOUT_STOP_V1","fundingModel",mode)),"Explicit funding selection/policy lost");
      denied(()->run(p,payoutFuncs,m(),"executionTermsFromContext",m("context",m("fundingModel","AUTO")),"seller"),"Unknown funding selection accepted");
    System.out.println("PASS native exact stop policy for Test without fundingModel and explicit SCT/legacy funding; unknown mode rejected");
  }
  static void agreementRecovery(Contracts p,Path root)throws Exception{
    var v=p.execution().values();var source=load(root,"clause-reseller/types/commission-clause.blue");
    var funcs=o(v.bexData(v.source(o(o(source.get("actionDefinition")).get("type")).get("functions"))));
    var original=m("name","Agreement origin");String pool=NativeRuntime.identity(v.source(original));
    var customerOriginal=m("name","Customer PI origin");String customer=NativeRuntime.identity(v.source(customerOriginal));
    var payoutOriginal=m("name","A2A PI origin");String payout=NativeRuntime.identity(v.source(payoutOriginal));
    var terms=m("settlementPoolId",pool,"beneficiaryAccountId","partner");
    var records=m();
    for(String id:List.of("r1","r2"))records.put(id,m("recoveryId",id,"requestId","refund-1","customerInstructionId",customer,"grossMinor",500,"retainedGrossMinor",0,"sellerRecoveryMinor",4375,"payouts",List.of(m("payoutInstructionId",payout,"grossMinor",500,"netMinor",400,"feeMinor",100))));
    var settlements=m("payout-1",m("status","closed","paidMinor",1000,"transferredMinor",800,"feeMinor",200));
    var agreement=m("contracts",m("initialized",m("document",original)),"activation",m("parties",m("partner",m("myosAccountId","partner"))),
      "commission",m("paid",1000,"accrued",0,"reserved",0,"settlements",settlements),
      "payouts",m("payout-1",m("fixturePaidPayout",true,"payment",m("completed",800),"contracts",m("initialized",m("document",payoutOriginal)))),
      "orders",m("order-1",m("payment",m("type","MyOS/MyOS Stripe Customer Payment Instruction","contracts",m("initialized",m("document",customerOriginal)),"paymentDetails",m("customerPaymentTerms",m("commissionTerms",terms)),"commissionRecoveries",records))));
    var history=copy(settlements);
    var trustedEvent=m("sourcePath","/orders/order-1","event",m("event",m("recovery",records.get("r1"))));
    terms.put("settlementPoolId","foreign-pool");
    denied(()->run(p,funcs,agreement,"reconcileCommissionRecovery",m(),"seller",trustedEvent),"Foreign settlement pool changed Agreement paid");
    terms.put("settlementPoolId",pool);terms.put("beneficiaryAccountId","foreign-beneficiary");
    denied(()->run(p,funcs,agreement,"reconcileCommissionRecovery",m(),"seller",trustedEvent),"Foreign beneficiary changed Agreement paid");
    terms.put("beneficiaryAccountId","partner");
    var forged=copy(o(records.get("r1")));forged.put("sellerRecoveryMinor",4374);
    denied(()->run(p,funcs,agreement,"reconcileCommissionRecovery",m(),"seller",m("sourcePath","/orders/order-1","event",m("event",m("recovery",forged)))),"Event not equal to stored PI receipt was trusted");
    for(String id:List.of("r2","r1","r2","r1")){
      var event=m("sourcePath","/orders/order-1","event",m("event",m("recovery",records.get(id))));
      var result=run(p,funcs,agreement,"reconcileCommissionRecovery",m(),"seller",event);
      for(Object change:result.changeset()){var c=o(change);check(c.get("path").equals("/commission"),"Recovery mutated A2A history");agreement.put("commission",v.bexData(v.source(Values.blueValue(c.get("val")))));}
      if(id.equals("r2")&&o(o(agreement.get("commission")).get("recoveries")).size()==1){
        var excessive=copy(o(records.get("r1")));excessive.put("payouts",List.of(m("payoutInstructionId",payout,"grossMinor",500,"netMinor",399,"feeMinor",101)));
        var prior=records.put("r1",excessive);
        denied(()->run(p,funcs,agreement,"reconcileCommissionRecovery",m(),"seller",m("sourcePath","/orders/order-1","event",m("event",m("recovery",excessive)))),"Remaining original payout fee cap was exceeded");
        records.put("r1",prior);
      }
    }
    var state=o(agreement.get("commission"));
    check(state.get("paid").toString().equals("0"),"Reordered partial recoveries must reduce paid G exactly once");
    check(state.get("recoveredNetMinor").toString().equals("800")&&state.get("recoveredFeeMinor").toString().equals("200"),"N/F tracked separately");
    check(history.equals(copy(o(state.get("settlements")))),"Original A2A settlement was changed");
    var retained=m("recoveryId","retained","requestId","refund-2","customerInstructionId",customer,"grossMinor",100,"retainedGrossMinor",100,"sellerRecoveryMinor",0,"payouts",List.of());records.put("retained",retained);
    var onlyRetained=run(p,funcs,agreement,"reconcileCommissionRecovery",m(),"seller",m("sourcePath","/orders/order-1","event",m("event",m("recovery",retained))));
    check(o(o(onlyRetained.changeset().getFirst()).get("val")).get("paid").toString().equals("0"),"Retained G must never reduce paid");
    System.out.println("PASS native Agreement reordered partial/replayed recovery, retained G, separate N/F and immutable A2A settlements");
  }

  static void refundIntent(Contracts p,Map<String,Object> funcs){
    var state=m("accepted",true,"transactionId","pi_captured","closed",false,"locks",m("refund",false),"completed",10000,"reversed",0,"reserved",m("refund",0),"requests",m(),"controlRequests",m());
    var document=m("payment",state,"paymentTerms",m("method","myos-customer"));
    var input=m("requestId","refund-1","amountMinor",10000,"reason","Customer requested refund");
    var legacy=run(p,funcs,document,"request",m("action","refund","input",input),"seller");
    var legacyIntent=o(o(legacy.changeset().getFirst()).get("val")).get("intent");
    check(o(legacyIntent).keySet().equals(Set.of("action","amountMinor","reason")),"Legacy request fingerprint changed");
    document.put("paymentDetails",m("customerPaymentTerms",m("commissionTerms",m("grossMinor",1000))));
    check(!run(p,funcs,document,"request",m("action","refund","input",input),"seller").changeset().isEmpty(),"SCT amount-only refund must remain accepted");
    var ordinary=run(p,funcs,document,"request",m("action","refund","input",input),"seller");
    check(o(o(o(ordinary.changeset().getFirst()).get("val")).get("intent")).keySet().equals(Set.of("action","amountMinor","reason")),"SCT refund changed the simple accepted request fingerprint");
    System.out.println("PASS native legacy and SCT amount-only refund fingerprints unchanged");
  }

  static void frozenAccrual(Contracts p,Path root)throws Exception{
    var v=p.execution().values();var source=load(root,"clause-reseller/types/commission-clause.blue");
    var definition=v.source(m("type",o(source.get("actionDefinition")).get("type")));
    var funcs=o(v.bexData(v.select(definition,"/functions")));
    for(String action:List.of("confirmed","reversed")){
      var steps=new ArrayList<Object>();steps.add(m("$let",m("name","actionResult","expr",m())));steps.addAll((List<?>)o(o(source.get("actions")).get(action)).get("do"));
      funcs.put(action+"ForTest",v.bexData(v.source(m("args",m(),"do",steps))));
    }
    var order=m("customerCommissionTerms",m("commissionBps",333,"grossMinor",335),"payment",m("payment",m("completed",10050,"reversed",0)));
    var agreement=m("terms",m("commissionBps",9999),"orders",m("order-1",order),"commission",m("targets",m(),"accrued",0,"paid",0,"reserved",0,"settlements",m()));
    var event=m("sourcePath","/orders/order-1","event",m("type","Payment/Payment Event Received","event",m("type","PaymentInstruction/Payment Completed","requestId","capture-1","amountCompleted",10050)));
    var result=run(p,funcs,agreement,"confirmedForTest",m(),"seller",event);
    check(accrued(result)==335,"Agreement amendment changed frozen Order G at PaymentCompleted: "+result.changeset());
    o(o(order.get("payment")).get("payment")).put("reversed",2500);
    event.put("event",m("type","Payment/Payment Event Received","event",m("type","PaymentInstruction/Payment Reversed After Completion","requestId","refund-1","amountReversed",2500)));
    check(accrued(run(p,funcs,agreement,"reversedForTest",m(),"seller",event))==251,"Refund used amended current rate instead of frozen accepted rule");
    order.remove("customerCommissionTerms");o(o(order.get("payment")).get("payment")).put("reversed",0);
    event.put("event",m("type","Payment/Payment Event Received","event",m("type","PaymentInstruction/Payment Completed","requestId","capture-1","amountCompleted",10050)));
    check(accrued(run(p,funcs,agreement,"confirmedForTest",m(),"seller",event))==10049,"Legacy current-rate behavior changed");
    System.out.println("PASS native amendment-between-preparation/capture frozen G and refund rounding; legacy current-rate fallback");
  }
  static long accrued(blue.bex.Engine.Result result){
    for(Object change:result.changeset()){var c=o(change);if(c.get("path").equals("/commission/accrued"))return ((Number)c.get("val")).longValue();}
    return -1;
  }

  static void bookingSnapshots(Contracts p,Path root)throws Exception{
    var v=p.execution().values();var catalog=v.bexData(v.source(load(root,"examples/reseller/catalog.blue").get("catalog")));
    var parent=m("contracts",m("initialized",m("document",m("name","Prepared Agreement origin"))),"terms",m("commissionBps",333),"activation",m("parties",m("partner",m("myosAccountId","trusted-partner"))),"catalog",catalog,"quotes",m("quote-1",m("totalMinor",3800)));
    for(String file:List.of("customer-orders-clause","customer-orders-bootstrap-clause")){
      var source=load(root,"clause-reseller/types/"+file+".blue");var def=v.source(m("type",o(source.get("actionDefinition")).get("type")));var funcs=o(v.bexData(v.select(def,"/functions")));
      var input=m("fields",m("amountMinor",1,"customerCommissionTerms",m("grossMinor",999999,"beneficiaryAccountId","attacker")),"catalogRevision",1,"lines",List.of(m("itemId","museum-admission--regular-weekday","quantity",1,"serviceDate","2026-11-03")),"quoteKey","quote-1");
      if(file.equals("customer-orders-clause")){
      var priced=run(p,funcs,parent,"priceSelections",m("input",m("catalogRevision",1,"lines",input.get("lines")),"catalogState",catalog),"seller");
      check(priced.value() instanceof Map<?,?>&&o(priced.value()).get("totalMinor")!=null,"Real priceSelections missing totalMinor in "+file+": "+priced.value());
      check(o(priced.value()).get("totalMinor").toString().equals("3800"),"Unexpected real catalogue price in "+file+": "+priced.value());
      }
      var result=run(p,funcs,parent,"prepareBooking",m("input",input),"seller");
      var fields=o(o(result.value()).get("fields"));var terms=o(fields.get("customerCommissionTerms"));
      check(fields.get("amountMinor").toString().equals("3800"),"Caller amount overrode native pricing");
      check(terms.get("grossMinor").toString().equals("127")&&terms.get("beneficiaryAccountId").equals("trusted-partner"),"Caller scalar overrode trusted booking quote/partner");
      check(result.changeset().isEmpty(),"Booking preparation accrued commission before PaymentCompleted");
    }
    System.out.println("PASS native catalogue/quote booking snapshots override spoofed amount/G/beneficiary without early accrual");
  }

}
