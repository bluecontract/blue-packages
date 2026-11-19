import blue.contracts.*;
import blue.bex.Values;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import blue.language.next.*;
import java.nio.file.*;
import java.util.*;

/** Authored BEX rule regressions on explicit modeled state; not hosted child/financial qualification. */
public final class AccountPayoutCancellationAgreementConformance {
  static Map<String,Object> m(Object... pairs) {return CommissionRecoveryConformance.m(pairs);}
  static Map<String,Object> o(Object value) {return CommissionRecoveryConformance.o(value);}
  static Map<String,Object> load(Path root,String path)throws Exception {
    return CommissionRecoveryConformance.load(root,path);
  }
  static void check(boolean condition,String why) {if(!condition)throw new AssertionError(why);}
  static blue.bex.Engine.Result run(Contracts p,Map<String,Object> functions,Map<String,Object> document,
      String function,Map<String,Object> event) {
    return CommissionRecoveryConformance.run(p,functions,document,function,m(),"seller",event);
  }
  static void requestDoesNotRelease(Contracts p,Path root)throws Exception {
    var v=p.execution().values();String key="payout-one";
    String keyId=NativeRuntime.identity(v.source(key));
    var clause=load(root,"clause-reseller/types/commission-clause.blue");
    var action=o(o(clause.get("actions")).get("payoutCancelled"));
    var steps=new ArrayList<Object>();steps.add(m("$let",m("name","actionResult","expr",m())));
    steps.addAll((List<?>)action.get("do"));steps.add(m("$return",m("$var","actionResult")));
    var functions=m("requestForTest",m("args",m(),"do",steps));
    var prepared=m("paymentDetails",m("executionTerms",m("executionPolicy","BLUE_ACCOUNT_PAYOUT_STOP_V1")));
    var item=m("key",key,"status","cancellation_requested","prepared",prepared);
    var document=m("clauses",m("payouts",m("bindings",m("collection","/payouts"))),
        "process_payouts",m("entries",m(keyId,item)),"payouts",m(),
        "commission",m("accrued",1800,"paid",0,"reserved",1800,"settlements",
            m(key,m("amountMinor",1800,"paidMinor",0,"status","reserved"))));
    var event=m("type","Documents/Preparation Cancellation Requested","clauseId","payouts","itemKey",key);
    var result=run(p,o(v.bexData(v.source(functions))),document,"requestForTest",event);
    System.out.println("request-only modeled rule changes="+WireData.write(result.changeset()));
    check(result.changeset().isEmpty(),"Cancellation request without native STOPPED must keep reserved G1800 and settlement open");
  }
  static void refreshCannotReopenStopped(Contracts p,Path root)throws Exception {
    var v=p.execution().values();String key="payout-one";String keyId=NativeRuntime.identity(v.source(key));
    var definition=v.source(m("type",load(root,"clause-documents/types/preparation-functions.blue")));
    var functions=o(v.bexData(v.select(definition,"/functions")));
    var original=m("name","Modeled already-stopped child origin","fixtureOriginKey","stopped-child");
    String origin=NativeRuntime.identity(v.source(original));
    String itemPath="/process_commission/entries/"+keyId;
    var item=m("key",key,"status","cancelled","documentOrigin",origin,"path","/payouts/"+key,
        "itemPath",itemPath,"nextActions",List.of());
    var document=m("process_commission",m("entries",m(keyId,item)),
        "payouts",m(key,m("contracts",m("initialized",m("document",original)),"activation",m("active",false))));
    functions.put("fixturePresenceForTest",m("args",m(),"do",List.of(m("$return",m("$exists",
        m("$document","/payouts/"+key+"/contracts/initialized/document"))))));
    var library=o(v.bexData(v.source(functions)));
    check(Boolean.TRUE.equals(run(p,library,document,"fixturePresenceForTest",m()).value()),
        "Refresh fixture initialized origin must be concrete native data, not metadata-only");
    var result=run(p,library,document,"sharedRefresh",m());
    System.out.println("terminal-refresh modeled rule changes="+WireData.write(v.bexData(v.source(Values.blueValue(result.changeset())))));
    check(result.changeset().isEmpty(),"Refresh must retain cancelled terminal preparation, not reopen selected/usable");
  }
  static void stoppedApplicationIsAtomicAndIdempotent(Contracts p,Path root)throws Exception {
    var v=p.execution().values();
    var definition=v.source(m("type",load(root,"clause-reseller/types/commission-account-payouts-clause.blue")));
    var library=o(v.bexData(v.select(definition,"/actionDefinition/functions")));
    var functions=m("applyStoppedPayout",library.get("applyStoppedPayout"));
    String key="modeled-stop";String itemPath="/process_payouts/entries/"+NativeRuntime.identity(v.source(key));
    var candidate=m("name","Explicit modeled candidate, not authenticated native history");
    String origin=NativeRuntime.identity(v.source(candidate));
    var proof=m("status","STOPPED","requestId","modeled-request","instructionOrigin",origin);
    var closed=m("amountMinor",1800,"paidMinor",0,"transferredMinor",0,"feeMinor",0,"status","closed","stopProof",proof);
    var item=m("key",key,"status","awaiting_provider","path","/payouts/"+key,"nextActions",List.of("provide"));
    var state=m("accrued",1800,"reserved",1800,"paid",0);
    var checked=m("outcome","acceptedNew","key",key,"itemPath",itemPath,"item",item,
        "candidate",candidate,"origin",origin,"proof",proof,"state",state,"gross",1800,"stoppedSettlement",closed);
    var document=m("commission",state,"payouts",m());var exact=v.source(document);
    var context=new blue.bex.Engine.Context();context.document=v.view(exact);
    context.readDocument=(path,view,doc)->v.view(v.select(exact,path));
    context.matcher=(actual,pattern)->v.matches(v.source(Values.blueValue(actual)),v.source(Values.blueValue(pattern),"definition"));
    context.nodeBlueId=(value,gas)->NativeRuntime.identity(v.source(Values.blueValue(value)));
    var program=m("functions",functions,"constants",m("bindings",m("commission","/commission","collection","/payouts")),
        "do",List.of(m("$return",m("$call",m("function","applyStoppedPayout","args",m("checked",checked))))));
    var result=p.execution().evaluator().execute(program,context,10000000);
    check(result.changeset().size()==4&&result.events().size()==1,"Stopped application must stage exactly one atomic four-change release and one event");
    var changes=new LinkedHashMap<String,Object>();var rawChanges=new LinkedHashMap<String,Object>();
    for(Object raw:result.changeset()){var change=o(raw);changes.put((String)change.get("path"),v.bexData(v.source(Values.blueValue(change.get("val")))));rawChanges.put((String)change.get("path"),change.get("val"));}
    check(changes.keySet().equals(Set.of(itemPath,"/payouts/"+key,"/commission/reserved","/commission/settlements/"+key)),"Stopped application changed unrelated state");
    var cancelled=o(changes.get(itemPath));check(cancelled.get("status").equals("cancelled")&&cancelled.get("documentOrigin").equals(origin)&&cancelled.get("nextActions").equals(List.of()),"Terminal attachment must not select or activate");
    check(Values.blueValue(rawChanges.get("/payouts/"+key)).equals(m("blueId",origin)),"Attachment must retain the exact candidate reference object");
    check(changes.get("/commission/reserved").toString().equals("0"),"Release must subtract G exactly once");
    check(NativeRuntime.identity(v.source(changes.get("/commission/settlements/"+key))).equals(NativeRuntime.identity(v.source(closed))),"Release must preserve the exact stopped settlement proof");
    checked.put("outcome","duplicate");
    var duplicate=p.execution().evaluator().execute(new LinkedHashMap<>(program),context,10000000);
    check(duplicate.changeset().isEmpty()&&duplicate.events().isEmpty(),"Validated duplicate must not release, attach or emit twice");
    System.out.println("PASS modeled checked-result application: exact terminal attachment/proof/G release and duplicate no-op; authentication/history not exercised");
  }
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
      var p=runtime.processor(blue);var failures=new ArrayList<String>();
      try {stoppedApplicationIsAtomicAndIdempotent(p,root);}catch(AssertionError failure){failures.add(failure.getMessage());}
      try {requestDoesNotRelease(p,root);}catch(AssertionError failure){failures.add(failure.getMessage());}
      try {refreshCannotReopenStopped(p,root);}catch(AssertionError failure){failures.add(failure.getMessage());}
      if(!failures.isEmpty())throw new AssertionError(String.join("; ",failures));
      System.out.println("PASS modeled authored rules: cancellation request retains G; terminal cancelled refresh remains terminal. Native proof adoption tested separately.");
    }
  }
}
