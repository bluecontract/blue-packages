import blue.packages.QualificationRuntime;
import blue.contracts.*;
import blue.core.CompositionPackages;
import blue.language.next.*;
import blue.bex.*;
import java.nio.file.*;
import java.util.*;

/** Canonical published provider input validation and native BEX effects; no deployed service. */
public final class ProviderInputConformance {
  static Map<String,Object> m(Object... pairs) { return OperationInputConformance.m(pairs); }
  static void require(boolean value,String message) { OperationInputConformance.require(value,message); }
  static ContractsExecution.Values values;
  static Blue blue;
  static NativeRuntime runtime;
  static Map<String,Object> matchers=new HashMap<>();
  static Object matcher(String type,String operation) {
    String key=type+"/"+operation;
    if(matchers.containsKey(key))return matchers.get(key);
    var definition=blue.admitDefinition(WireData.write(m("type",type)));
    var head=NativeRuntime.head(NativeRuntime.recipe(NativeRuntime.exactOf(definition)),runtime);
    var contract=NativeRuntime.child(NativeRuntime.head(head.contracts,runtime),operation);
    require(contract!=null,"Missing public operation "+type+"/"+operation);
    var request=NativeRuntime.child(NativeRuntime.head(contract,runtime),"request");
    require(request!=null,"Missing public request "+type+"/"+operation);
    matchers.put(key,request);return request;
  }
  static boolean matches(Object input,Object matcher) {
    try { return values.matches(values.source(input),matcher); }
    catch(blue.language.next.Failure invalid) { return false; }
    catch(ContractException invalid) {
      if(Set.of("LANGUAGE_SchemaViolation", "LANGUAGE_TypeCompatibilityViolation").contains(invalid.code()))return false;
      throw invalid;
    }
  }
  static void valid(String type,String operation,Map<String,Object> input,String required) {
    Object matcher=matcher(type,operation);
    require(matches(input,matcher),operation+" valid input");
    var missing=new LinkedHashMap<>(input);missing.remove(required);
    require(!matches(missing,matcher),operation+" must require "+required);
    var wrong=new LinkedHashMap<>(input);wrong.put(required,7);
    require(!matches(wrong,matcher),operation+" rejects wrong "+required+" type");
    var empty=new LinkedHashMap<>(input);empty.put(required,"");
    require(!matches(empty,matcher),operation+" rejects empty "+required);
  }
  static Map<String,Object> typed(String type,Map<String,Object> fields) {
    var result=new LinkedHashMap<String,Object>();
    result.put("type",m("blueId",NativeRuntime.head(NativeRuntime.recipe(values.source(m("type",type),"definition")),runtime).type));
    result.putAll(fields);return result;
  }
  @SuppressWarnings("unchecked")
  static Engine.Result execute(String instruction,String operation,Map<String,Object> input,Object document,String channel) {
    var instructionHead=values.head(values.source(m("type",instruction),"definition"));
    var contract=NativeRuntime.child(NativeRuntime.head(instructionHead.contracts,runtime),operation);
    var steps=NativeRuntime.head(NativeRuntime.child(NativeRuntime.head(contract,runtime),"steps"),runtime);
    var compute=NativeRuntime.head(NativeRuntime.child(steps,steps.items.size()-1),runtime);
    var definition=NativeRuntime.head(NativeRuntime.child(compute,"definition"),runtime);
    var library=new LinkedHashMap<String,Object>();
    for(String field:List.of("constants","functions")) {
      var selected=NativeRuntime.child(definition,field);
      if(selected!=null)library.put(field,values.bexData(selected));
    }
    var source=new LinkedHashMap<String,Object>();
    for(String field:List.of("do","constants","functions")) {
      var selected=NativeRuntime.child(compute,field);
      if(selected!=null)source.put(field,values.bexData(selected));
    }
    var bex=new Bex(BexProfile.current());
    var program=bex.compile(source,library,null);
    var context=new BexContext(document,m(),m(),Values.UNDEFINED,m(),m("call",m("channel",channel,"request",input),"timestamp",100),"/",null,
      (actual,pattern)->values.matches(values.source(actual),values.source(pattern,"definition")),
      (actual,gas)->NativeRuntime.identity(values.source(actual)));
    return bex.execute(program,context,1000000);
  }
  static void change(Engine.Result result,String path,Object value) {
    require(result.changeset().stream().anyMatch(item->item instanceof Map<?,?> map&&path.equals(map.get("path"))&&Objects.equals(value,map.get("val"))),
      "Expected native change "+path+"="+value+"; actual="+result.changeset());
  }
  static Map<String,Object> payment() {
    return m("paymentTerms",m("payerChannel","payer","guarantorChannel","bank","payeeChannel","bank","amountMinor",100,"currency","USD"),
      "payment",m("accepted",true,"closed",false,"completed",0,"reversed",0),
      "bankTransfer",m("requestId","transfer-1","status","requested","reference",""));
  }
  static void acme() {
    String type="ACME/Bank Transfer Contract";
    valid(type,"requestTransfer",m("requestId","transfer-1"),"requestId");
    Object request=matcher(type,"requestTransfer");
    require(!matches(m("requestId","x".repeat(129)),request),"ACME requestId max128");
    require(!matches(m("requestId","x","extra",true),request),"ACME request has exact keys");
    var confirm=m("requestId","transfer-1","reference","bank-ref","amountMinor",100,"currency","USD");
    valid(type,"confirmTransfer",confirm,"reference");
    valid(type,"confirmTransfer",confirm,"requestId");
    require(!matches(m("requestId","transfer-1","reference","bank-ref"),matcher(type,"confirmTransfer")),"Confirmation amount/currency required");
    change(execute(type,"confirmTransfer",confirm,payment(),"bank"),"/bankTransfer/status","completed");
    for(String operation:List.of("reportTransferUnknown","declineTransfer")) {
      var input=typed("ACME/Bank Transfer Outcome Input",m("requestId","transfer-1","reference","bank-ref"));
      valid(type,operation,input,"reference");
      valid(type,operation,input,"requestId");
      var withOptional=new LinkedHashMap<>(input);withOptional.put("amountMinor",100);withOptional.put("currency","USD");
      require(matches(withOptional,matcher(type,operation)),operation+" optional amount/currency accepted");
      var extra=new LinkedHashMap<>(input);extra.put("reason","not permitted");
      require(!matches(extra,matcher(type,operation)),operation+" keeps exact allowed keys");
      var tooLong=new LinkedHashMap<>(input);tooLong.put("reference","x".repeat(257));
      require(!matches(tooLong,matcher(type,operation)),operation+" reference max256");
      change(execute(type,operation,input,payment(),"bank"),"/bankTransfer/status",operation.equals("declineTransfer")?"declined":"unknown");
    }
    var doc=payment();doc.put("bankTransfer",m("requestId","","status","idle","reference",""));
    change(execute(type,"requestTransfer",m("requestId","transfer-1"),doc,"payer"),"/bankTransfer/status","requested");
    System.out.println("PASS ACME4 public schemas, bounds, optional fields, allowed keys and native effects");
  }
  static void manual() {
    String instruction="ManualPayments/Manual Payment Instruction";
    var input=m("requestId","request-1","reference","customer-ref");
    valid(instruction,"reportTransfer",input,"requestId");
    valid(instruction,"reportTransfer",input,"reference");
    var extra=new LinkedHashMap<>(input);extra.put("note","user evidence");
    require(matches(extra,matcher(instruction,"reportTransfer")),"Manual instruction permits additional fields");
    var longReference=new LinkedHashMap<>(input);longReference.put("reference","r".repeat(257));
    require(matches(longReference,matcher(instruction,"reportTransfer")),"Manual instruction has no receipt-only reference limit");
    change(execute(instruction,"reportTransfer",extra,payment(),"payer"),"/reportedTransfer",extra);
    String receipt="ManualPayments/Manual Receipt Instruction";
    for(String operation:List.of("reportTransfer","acknowledgeTransfer","reportRefund","acknowledgeRefund")) {
      valid(receipt,operation,input,"reference");
      valid(receipt,operation,input,"requestId");
      Object pattern=matcher(receipt,operation);
      require(!matches(extra,pattern),operation+" receipt permits exactly two fields");
      require(!matches(longReference,pattern),operation+" receipt reference max256");
      require(!matches(m("requestId","r".repeat(257),"reference","ref"),pattern),operation+" receipt requestId max256");
    }
    var doc=payment();doc.put("activation",m("parties",m("bank",m("readerKeys",List.of("bank-key"),"lead",m("channel",m("type","Contracts/External Channel","event",m("source","bank")))))));
    change(execute(receipt,"reportTransfer",input,doc,"payer"),"/reportedTransfer",input);
    doc.put("reportedTransfer",input);
    require(execute(receipt,"acknowledgeTransfer",input,doc,"bank").changeset().stream().anyMatch(item->item instanceof Map<?,?> map&&"/payment/completed".equals(map.get("path"))),"Receipt acknowledgment records completion");
    doc.put("payment",m("accepted",true,"closed",false,"completed",100,"reversed",0));
    change(execute(receipt,"reportRefund",input,doc,"bank"),"/reportedRefund",input);
    doc.put("reportedRefund",input);
    require(execute(receipt,"acknowledgeRefund",input,doc,"payer").changeset().stream().anyMatch(item->item instanceof Map<?,?> map&&"/payment/reversed".equals(map.get("path"))),"Refund acknowledgment records reversed amount");
    System.out.println("PASS Manual5 public inputs, distinct extra-field/length policies and native effects");
  }
  static void myos() {
    String type="MyOS/MyOS Customer Payment Instruction";
    Object pattern=matcher(type,"provideSession");
    var input=typed("MyOS/Customer Session Input",m("sessionId","session-1"));
    valid(type,"provideSession",input,"sessionId");
    var expiring=new LinkedHashMap<>(input);expiring.put("expiresAt",1000);
    require(matches(expiring,pattern),"Customer expiresAt accepted when supplied");
    var invalid=new LinkedHashMap<>(input);invalid.put("expiresAt","tomorrow");
    require(!matches(invalid,pattern),"Customer expiresAt must be an integer");
    var doc=payment();doc.put("customerSession",m("id","","expiresAt",0,"requested",false,"funded",false));
    var provided=execute(type,"provideSession",input,doc,"bank");
    change(provided,"/customerSession/id","session-1");
    change(provided,"/customerSession/expiresAt",new java.math.BigInteger("900000100"));
    change(execute(type,"provideSession",expiring,doc,"bank"),"/customerSession/expiresAt",new java.math.BigInteger("1000"));
    var expired=new LinkedHashMap<>(input);expired.put("expiresAt",100);
    boolean rejected=false;try {execute(type,"provideSession",expired,doc,"bank");}catch(BexError error){rejected=true;}
    require(rejected,"Customer expiry time remains validated during execution");
    doc.put("customerSession",m("id","session-1","expiresAt",1000,"requested",false,"funded",false));
    doc.put("paymentAction",m("kind","customer-funding"));
    for(String operation:List.of("confirmFunding","requestCustomerFunding")) valid(type,operation,m("sessionId","session-1"),"sessionId");
    change(execute(type,"confirmFunding",m("sessionId","session-1"),doc,"bank"),"/customerSession/funded",true);
    change(execute(type,"requestCustomerFunding",m("sessionId","session-1"),doc,"payer"),"/customerSession/requested",true);
    System.out.println("PASS MyOS3 public inputs, optional expiry, preserved default/time validation and native effects");
  }
  public static void main(String[] args)throws Exception {
    Path root=Path.of(args[0]).toAbsolutePath();
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var language=packages.language()) {
      blue=language;values=new Contracts(blue,QualificationRuntime.bindings()).execution().values();runtime=new NativeRuntime(blue);
      String mode=args.length<2?"all":args[1];
      require(Set.of("all","acme","manual","myos").contains(mode),"Unknown provider mode "+mode);
      if(mode.equals("all")||mode.equals("acme"))acme();
      if(mode.equals("all")||mode.equals("manual"))manual();
      if(mode.equals("all")||mode.equals("myos"))myos();
    }
  }
}
