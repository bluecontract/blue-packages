import blue.contracts.*;import blue.coordination.AuthoringRuntime;import blue.core.CompositionPackages;import blue.language.next.*;import java.nio.file.*;import java.util.*;
/** Native attachment dispatch plus explicit small-state guard/replay models; no hosted finance proof. */
public final class CommissionAttachmentConformance {
 static Map<String,Object> m(Object...x){return BootstrapPreparationConformance.m(x);}static Map<String,Object> o(Object x){return BootstrapPreparationConformance.obj(x);}
 static Contracts.Result ok(Contracts.Result x){if(!x.commits())throw new AssertionError(x.status()+" "+x.observations());return x;}
 public static void main(String[]args)throws Exception{
 var root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
 try(var blue=packages.language();var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())){
 var authored=o(WireData.parse(Files.readString(root.resolve("clause-reseller/types/commission-clause.blue")),"yaml"));
 var p=runtime.processor(blue);if(args.length>2&&args[2].equals("models")){checkModels(p,authored,m("type","Documents/Document Attached","clauseId","orders","itemKey","order-1","inResponseTo","order-1"));return;}for(int initialAmount:List.of(10000,0)){var source=BootstrapPreparationConformance.source(null);var cs=o(source.get("clauses"));var params=o(o(cs.get("orders")).get("parameters"));params.put("suppliedParties",List.of());var template=o(params.get("template"));var activation=o(o(o(template.get("clauses")).get("activation")).get("parameters"));o(activation.get("parties")).remove("customer");activation.put("required",List.of("seller"));template.put("payment",m("payment",m("completed",initialAmount,"reversed",0)));
 o(template.get("clauses")).put("testPaymentEvents",paymentEmitter());
 source.put("orders",m());source.put("payouts",m());source.put("terms",m("commissionBps",1200));source.put("attachmentSeen",m());
 cs.put("commission",m("type",authored,"bindings",m("state","/commission","orders","/orders","payouts","/payouts","rate","/terms/commissionBps")));
 cs.put("attachmentObserver",m("type",m("type","Connections/Connected Clause","actions",m("observe",m("automatic",m("on","event","event",m("type","Documents/Document Attached")),"do",List.of(m("$appendChange",m("op","replace","path","/attachmentSeen","val",m("$event","")))))))));
 var host=ok(p.initialize(source));host=ok(p.process(host.document(),BootstrapPreparationConformance.event(host.document(),"approve_merchant",m("revision",1)),1));
 host=ok(p.process(host.document(),BootstrapPreparationConformance.event(host.document(),"prepareOrder",m("type","Documents/Preparation Input","key","order-1","values",m("size",42))),2));
 var item=o(o(p.read(host.document(),"/process_orders/entries")).values().iterator().next());var v=p.execution().values();var prepared=v.literal(v.exact(v.select(new Exact.Ref(host.document().blueId()),item.get("itemPath")+"/prepared")));var child=ok(p.initialize(prepared));
 var approve=m("source","merchant","operation",m("type","Contracts/Operation Request","channel","seller","operation","approve_seller","document",m("blueId",child.document().blueId()),"requireExactDocumentVersion",true,"request",m("revision",1)));
 child=ok(p.process(child.document(),approve,3));if(!Boolean.TRUE.equals(p.read(child.document(),"/activation/active")))throw new AssertionError("Child not active");
 var request=m("type","Documents/Provision Input","key",item.get("key"),"inResponseTo",item.get("requestId"),"requirementRef",item.get("requirementRef"),"document",m("blueId",child.document().blueId()));
 host=ok(p.process(host.document(),BootstrapPreparationConformance.event(host.document(),"provideOrder",request),4));
 var result=m("boundary","Real native prepare/initialize/approve/provide/sharedRefresh/event dispatch in small modeled completed-state fixture; not hosted financial history","status",p.read(host.document(),item.get("itemPath")+"/status"),"attachmentSeen",p.read(host.document(),"/attachmentSeen"),"commission",p.read(host.document(),"/commission"),"completed",p.read(host.document(),"/orders/order-1/payment/payment/completed"));
 if(args.length>1)Files.writeString(Path.of(args[1]),WireData.write(result));System.out.println(WireData.write(result));
 if(o(result.get("attachmentSeen")).isEmpty())throw new AssertionError("Real local Document Attached not dispatched");
 check(Integer.toString(initialAmount==0?0:1200).equals(p.read(host.document(),"/commission/accrued").toString()),"Attachment must reconcile current net");
 System.out.println("PASS real native Documents attachment dispatch initialCompleted="+initialAmount);
 for(int reversed:List.of(0,0,2500,2500,10000,10000)){
  String childId=NativeRuntime.identity(v.exact(v.select(new Exact.Ref(host.document().blueId()),"/orders/order-1")));
  var paymentEvent=m("source","merchant","operation",m("type","Contracts/Operation Request","channel","seller","operation","testSettle","document",m("blueId",childId),"requireExactDocumentVersion",true,"request",m("completed",10000,"reversed",reversed)));
  host=ok(p.process(host.document(),paymentEvent,5+reversed));
  check(Integer.toString((10000-reversed)*12/100).equals(p.read(host.document(),"/commission/accrued").toString()),"Native collection event/replay target for reversal"+reversed);
 }
 System.out.println("PASS generated collection dispatch completion/replay/partial/full reversal after initialCompleted="+initialAmount);
 if(initialAmount==10000)checkModels(p,authored,o(result.get("attachmentSeen")));
 }
 }
 }
 static Map<String,Object> paymentEmitter(){
  var completed=m("$var",m("name","params","path","/completed"));
  var reversed=m("$var",m("name","params","path","/reversed"));
  var event=m("$choose",m("cond",m("$gt",List.of(reversed,0)),"then",m("type","PaymentInstruction/Payment Reversed After Completion","requestId","refund-model","amountReversed",2500),"else",m("type","PaymentInstruction/Payment Completed","requestId","capture-model","amountCompleted",10000)));
  var steps=List.of(m("$appendChange",m("op","replace","path","/payment/payment/completed","val",completed)),m("$appendChange",m("op","replace","path","/payment/payment/reversed","val",reversed)),m("$appendEvent",m("type","Payment/Payment Event Received","kind","payment-model","clause","payment","instructionPath","/payment","event",event)));
  var type=m("type","Connections/Connected Clause","actions",m("settle",m("do",steps)));
  var connection=m("on","workflow","party","seller","params",m("$object",m("$var","trigger")));
  return m("type",type,"bindings",m("settle",m("testSettle",connection)));
 }
 static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
 static void checkModels(Contracts p,Map<String,Object> authored,Map<String,Object> attached)throws Exception {
  var v=p.execution().values();var definition=v.source(m("type",authored));var sourceFunctions=v.source(m("type","Documents/Source Functions"));
  for(String name:List.of("namedSourcesReady","processOrigin","rosterCovers"))check(NativeRuntime.identity(v.exact(v.select(definition,"/actionDefinition/functions/"+name))).equals(NativeRuntime.identity(v.exact(v.select(sourceFunctions,"/functions/"+name)))),"Stale shared readiness pin "+name);
  var original=m("name","Model initialized Order identity","marker","original-order");String origin=NativeRuntime.identity(v.source(original));String key="order-1";String itemPath="/process_orders/entries/"+NativeRuntime.identity(v.source(key));
  var event=new LinkedHashMap<String,Object>(attached);event.put("documentOrigin",origin);
  var item=m("key",key,"path","/orders/order-1","itemPath",itemPath,"status","usable","requestId",event.get("inResponseTo"),"documentOrigin",origin);
  var order=m("contracts",m("initialized",m("document",original)),"activation",m("active",true,"parties",m()),"payment",m("payment",m("completed",10000,"reversed",0)));
  var model=m("clauses",m("orders",m("bindings",m("collection","/orders"))),"orders",m(key,order),"process_orders",m("entries",m(NativeRuntime.identity(v.source(key)),item)),"terms",m("commissionBps",1200),"commission",m("targets",m(),"accrued",0,"paid",0,"reserved",0,"settlements",m()));
  var baseline=run(p,definition,model,event,"attached");check(amount(baseline)==1200,"Passing modeled attachment control: "+baseline);
  apply(model,baseline);check(run(p,definition,model,event,"attached").changeset().isEmpty(),"Attachment replay must not duplicate");
  var completed=m("sourcePath","/orders/order-1","event",m("type","Payment/Payment Event Received","kind","payment-model","clause","payment","instructionPath","/payment","event",m("type","PaymentInstruction/Payment Completed","requestId","capture-model","amountCompleted",10000)));
  check(run(p,definition,model,completed,"confirmed").changeset().isEmpty(),"Completed after catch-up must not duplicate");
  set(model,"/orders/order-1/payment/payment/reversed",2500);var reversed=m("sourcePath","/orders/order-1","event",m("type","Payment/Payment Event Received","kind","payment-model","clause","payment","instructionPath","/payment","event",m("type","PaymentInstruction/Payment Reversed After Completion","requestId","refund-model","amountReversed",2500)));var partial=run(p,definition,model,reversed,"reversed");check(amount(partial)==900,"Partial reversal target900");apply(model,partial);check(run(p,definition,model,event,"attached").changeset().isEmpty(),"Replay after partial reversal");
  set(model,"/orders/order-1/payment/payment/reversed",10000);var full=run(p,definition,model,reversed,"reversed");check(amount(full)==0,"Full reversal target0");apply(model,full);check(run(p,definition,model,reversed,"reversed").changeset().isEmpty(),"Reversal replay");
  set(model,"/orders/order-1/payment/payment/completed",0);set(model,"/orders/order-1/payment/payment/reversed",0);check(run(p,definition,model,event,"attached").changeset().isEmpty(),"Attach before payment target0");set(model,"/orders/order-1/payment/payment/completed",10000);var later=run(p,definition,model,completed,"confirmed");check(amount(later)==1200,"Completion after attachment target1200");
  var mutations=m("wrong collection",List.of("/clauses/orders/bindings/collection","/foreign"),"wrong entry key",List.of(itemPath+"/key","foreign"),"wrong entry path",List.of(itemPath+"/path","/foreign/order-1"),"wrong itemPath",List.of(itemPath+"/itemPath","/foreign"),"not usable",List.of(itemPath+"/status","selected"),"stale request",List.of(itemPath+"/requestId","foreign"),"wrong origin",List.of(itemPath+"/documentOrigin","foreign"),"replaced Order",List.of("/orders/order-1/contracts/initialized/document",m("name","Another Order","marker","different-order")),"inactive",List.of("/orders/order-1/activation/active",false),"source unavailable",List.of("/orders/order-1/clauses",m("documentSources",m("parameters",m("requirements",m("agreement",m("origin","missing","selectionPath","")))))));
  for(var x:mutations.entrySet()){check(amount(run(p,definition,model,event,"attached"))==1200,"Control before "+x.getKey());var copy=copy(model);var edit=(List<?>)x.getValue();set(copy,(String)edit.get(0),edit.get(1));var denied=run(p,definition,copy,event,"attached");check(denied.changeset().isEmpty()&&denied.events().isEmpty(),"Rejected "+x.getKey());System.out.println("DENIED "+x.getKey());}
  for(String field:List.of("clauseId","itemKey","inResponseTo","documentOrigin")){var foreign=new LinkedHashMap<String,Object>(event);foreign.put(field,"foreign");check(amount(run(p,definition,model,event,"attached"))==1200,"Event control");var denied=run(p,definition,model,foreign,"attached");check(denied.changeset().isEmpty(),"Wrong event "+field);}
  for(Object rate:List.of(-1,10001,"1200")){var copy=copy(model);set(copy,"/terms/commissionBps",rate);boolean failed=false;try{run(p,definition,copy,event,"attached");}catch(RuntimeException expected){failed=true;}check(failed,"Invalid rate "+rate);}
  for(Object net:List.of(-1,1000000000001L,"10000")){var copy=copy(model);set(copy,"/orders/order-1/payment/payment/completed",net);boolean failed=false;try{run(p,definition,copy,event,"attached");}catch(RuntimeException expected){failed=true;}check(failed,"Invalid completed "+net);}
  for(Object reversedValue:List.of(-1,"2500",10001)){
   check(amount(run(p,definition,model,event,"attached"))==1200,"Money positive control");
   var changed=copy(model);set(changed,"/orders/order-1/payment/payment/reversed",reversedValue);boolean denied=false;
   try{run(p,definition,changed,event,"attached");}catch(RuntimeException expected){denied=true;}
   check(denied,"Invalid reversed "+reversedValue);
  }
  for(String malformed:List.of("../order-1","order~1","")){
   var bad=new LinkedHashMap<String,Object>(event);bad.put("itemKey",malformed);
   check(run(p,definition,model,bad,"attached").changeset().isEmpty(),"Malformed key");
  }
  var named=copy(model);var party=m("lead",m("channel",m("marker","seller-channel")),"readerKeys",List.of("seller-reader"));
  var sourceOriginal=m("marker","source-origin");String sourceOrigin=NativeRuntime.identity(v.source(sourceOriginal));
  set(named,"/orders/order-1/activation/parties",m("seller",party));
  set(named,"/orders/order-1/sources",m("agreement",m("contracts",m("initialized",m("document",sourceOriginal)),"activation",m("active",true,"parties",m("seller",party)))));
  set(named,"/orders/order-1/clauses",m("documentSources",m("parameters",m("requirements",m("agreement",m("origin",sourceOrigin,"selectionPath",""))))));
  for(var change:m("source inactive",List.of("/orders/order-1/sources/agreement/activation/active",false),"source reader mismatch",List.of("/orders/order-1/sources/agreement/activation/parties/seller/readerKeys",List.of("foreign")),"source identity changed",List.of("/orders/order-1/sources/agreement/contracts/initialized/document",m("marker","foreign-origin"))).entrySet()){
   check(amount(run(p,definition,named,event,"attached"))==1200,"Named source positive control");
   var bad=copy(named);var edit=(List<?>)change.getValue();set(bad,(String)edit.get(0),edit.get(1));var denied=run(p,definition,bad,event,"attached");check(denied.changeset().isEmpty()&&denied.events().isEmpty(),change.getKey());System.out.println("DENIED "+change.getKey());
  }
  var net=copy(model);set(net,"/orders/order-1/payment/payment/reversed",2500);check(amount(run(p,definition,net,event,"attached"))==900,"Reversal before attachment uses net");
  System.out.println("PASS modeled before/after completion, replay, partial/full reversal, routing/readiness and money controls; 10M gas per execution");
 }
 static blue.bex.Engine.Result run(Contracts p,Exact definition,Map<String,Object> document,Map<String,Object> event,String action){
  var v=p.execution().values();var exact=v.source(document);var context=new blue.bex.Engine.Context();context.document=v.view(exact);context.event=v.view(v.source(event));context.readDocument=(path,view,doc)->v.view(v.select(exact,path));context.matcher=(a,b)->v.matches(v.source(blue.bex.Values.blueValue(a)),v.source(blue.bex.Values.blueValue(b),"definition"));context.nodeBlueId=(a,g)->NativeRuntime.identity(v.source(blue.bex.Values.blueValue(a)));
  var steps=new ArrayList<Object>();steps.add(m("$let",m("name","actionResult","expr",m())));steps.addAll((List<?>)v.bexData(v.select(definition,"/actions/"+action+"/do")));
  var expr=m("functions",v.bexData(v.select(definition,"/actionDefinition/functions")),"constants",m("clauseKey","commission","bindings",m("orders","/orders","payouts","/payouts","state","/commission","rate","/terms/commissionBps")),"do",steps);
  return p.execution().evaluator().execute(expr,context,10000000);
 }
 static long amount(blue.bex.Engine.Result result){for(Object x:result.changeset()){var c=o(x);if("/commission/accrued".equals(c.get("path")))return ((Number)c.get("val")).longValue();}return -1;}
 static Map<String,Object> copy(Map<String,Object> x){return o(WireData.json(WireData.write(x)));}
 static void set(Map<String,Object> root,String path,Object value){String[] p=path.substring(1).split("/");var n=root;for(int i=0;i<p.length-1;i++)n=o(n.computeIfAbsent(p[i],k->m()));n.put(p[p.length-1],value);}
 static void apply(Map<String,Object> document,blue.bex.Engine.Result result){for(Object x:result.changeset()){var c=o(x);set(document,(String)c.get("path"),c.get("val"));}}
}
