import blue.contracts.*;
import blue.core.CompositionPackages;
import blue.language.next.*;
import blue.bex.*;
import java.nio.file.*;
import java.util.*;

/** Native arguments and configured-call adaptation for the four reusable action libraries. */
public final class ActionInputConformance {
  static Map<String,Object> m(Object... pairs){return OperationInputConformance.m(pairs);}
  static void require(boolean v,String message){OperationInputConformance.require(v,message);}
  static ContractsExecution.Values values; static NativeRuntime runtime;
  static Object field(Object node,String name){return NativeRuntime.child(values.head(node),name);}
  static Object matcher(String type,String function){
    return field(field(field(field(values.source(m("type",type),"definition"),"functions"),function),"args"),"input");
  }
  static boolean matches(Object input,Object matcher){
    try{return values.matches(values.source(input),matcher);}
    catch(ContractException e){if(Set.of("LANGUAGE_TypeCompatibilityViolation","LANGUAGE_SchemaViolation").contains(e.code()))return false;throw e;}
  }
  static Map<String,Object> typed(String type,Map<String,Object> input){
    var result=new LinkedHashMap<String,Object>();
    result.put("type",m("blueId",NativeRuntime.head(NativeRuntime.recipe(values.source(m("type",type),"definition")),runtime).type));result.putAll(input);return result;
  }
  static void check(String type,String function,Map<String,Object> input,List<String> required){
    Object schema=matcher(type,function);require(matches(input,schema),function+" valid input");
    for(String key:required){
      var omitted=new LinkedHashMap<>(input);omitted.remove(key);require(!matches(omitted,schema),function+" requires "+key);
      if(!key.equals("replacement")){
        var wrong=new LinkedHashMap<>(input);wrong.put(key,input.get(key) instanceof Number?"wrong-type":7);
        require(!matches(wrong,schema),function+" rejects wrong type for "+key);
      }
    }
  }
  @SuppressWarnings("unchecked") static Engine.Result action(String type,String name,Map<String,Object> input,Object document,Object parameters,Object bindings) {
    Object clause=values.source(m("type",type),"definition");
    Object libraryNode=field(clause,"actionDefinition");
    var library=m("functions",values.bexData(field(libraryNode,"functions")),"constants",m("parameters",parameters,"bindings",bindings,"clauseKey","test"));
    var body=new ArrayList<Object>();body.add(m("$let",m("name","actionResult","expr",m("$literal",m()))));body.add(m("$let",m("name","params","expr",m("$literal",input))));
    body.addAll((List<Object>)values.bexData(field(field(field(clause,"actions"),name),"do")));
    var bex=new Bex(BexProfile.current());
    var context=new BexContext(document,m(),m(),Values.UNDEFINED,m(),m("call",m("channel","owner")),"/",null,
      (actual,pattern)->values.matches(values.source(actual),values.source(pattern,"definition")),null);
    return bex.execute(bex.compile(m("do",body),library,null),context,1000000);
  }
  static void change(Engine.Result result,String path,Object value) {
    require(result.changeset().stream().anyMatch(item->item instanceof Map<?,?> row&&path.equals(row.get("path"))&&Objects.equals(value,row.get("val"))),
      "Missing native effect "+path+"="+value+": "+result.changeset());
  }
  static void effects(){
    var zero=new java.math.BigInteger("0");var twelve=new java.math.BigInteger("12");
    var ledger=m("targets",m(),"accrued",100,"paid",0,"reserved",0,"settlements",m());
    change(action("Ledger/Ledger Clause","setTarget",m("key","x","amountMinor",12),m("balance",ledger),m(),m("state","/balance")),"/balance/targets/x",twelve);
    change(action("Ledger/Ledger Clause","reserve",m("key","x","amountMinor",12),m("balance",ledger),m(),m("state","/balance")),"/balance/reserved",twelve);
    ledger.put("settlements",m("x",m("status","reserved","amountMinor",12)));ledger.put("reserved",12);
    change(action("Ledger/Ledger Clause","settle",m("key","x"),m("balance",ledger),m(),m("state","/balance")),"/balance/reserved",zero);
    var quote=action("Commerce/Product Clause","quote",m("unitPriceMinor",4,"quantity",3),m(),m("currency","USD"),m("product","/product"));
    require(quote.changeset().stream().anyMatch(item->item instanceof Map<?,?> row&&row.get("val") instanceof Map<?,?> value&&twelve.equals(value.get("totalMinor"))&&"USD".equals(value.get("currency"))),"Quote native configured currency and total");
    var transitions=m("subject","Order","transitions",m("open",List.of("closed")));
    change(action("State/Status Clause","transition",m("to","closed"),m("status","open"),transitions,m("state","/status")),"/status","closed");
    boolean denied=false;try{action("State/Status Clause","transition",m("to","other"),m("status","open"),transitions,m("state","/status"));}catch(BexError e){denied=true;}require(denied,"State targets remain configuration controlled");
    var state=m("revision",1,"proposal",m(),"history",m());
    var params=m("approvers",List.of("owner"),"paths",List.of("/terms/price"));var bindings=m("state","/amendments","editable","/termsEditable");
    var proposed=action("Amendments/Amendments Clause","propose",m("expectedRevision",1,"path","/terms/price","proposalId","p1","replacement",12),m("amendments",state,"termsEditable",true),params,bindings);
    require(proposed.changeset().stream().anyMatch(item->item instanceof Map<?,?> row&&"/amendments/proposal".equals(row.get("path"))),"Amendment configured caller wraps optional input explicitly");
    state.put("proposal",m("id","p1","revision",1,"path","/terms/price","replacement",12,"approvals",m()));
    change(action("Amendments/Amendments Clause","approve",m("proposalId","p1"),m("amendments",state,"termsEditable",true),params,bindings),"/terms/price",twelve);
    System.out.println("PASS A9 actual configured action callers and native effects");
  }
  @SuppressWarnings("unchecked") public static void main(String[] args)throws Exception{
    Path root=Path.of(args[0]).toAbsolutePath();
    var source=(Map<String,Object>)WireData.parse(Files.readString(root.resolve("clause-balance/types/functions.blue")),"yaml");
    var fs=(Map<String,Object>)source.get("functions");
    var input=(Map<?,?>)((Map<?,?>)((Map<?,?>)fs.get("setTarget")).get("args")).get("input");
    require(input.containsKey("amountMinor"),"Balance setTarget must declare native input constraints");
    var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    try(var blue=packages.language()){
      runtime=new NativeRuntime(blue);values=new Contracts(blue,RuntimeBindings.accessEvents().withDefinitionReadV1()).execution().values();
      check("Ledger/Balance Functions","setTarget",m("key","invoice-1","amountMinor",0),List.of("key","amountMinor"));
      check("Ledger/Balance Functions","reserve",m("key","invoice-1","amountMinor",1),List.of("key","amountMinor"));
      check("Ledger/Balance Functions","settle",m("key","invoice-1"),List.of("key"));
      require(!matches(m("key","x","amountMinor",-1),matcher("Ledger/Balance Functions","setTarget")),"Negative target rejected");
      require(!matches(m("key","x","amountMinor",0),matcher("Ledger/Balance Functions","reserve")),"Zero reservation rejected");
      var proposal=typed("Amendments/Amendment Input",m("expectedRevision",1,"path","/terms/price","proposalId","p1","replacement",12));
      check("Amendments/Amendments Functions","proposePublic",proposal,List.of("expectedRevision","path","proposalId","replacement"));
      var preserve=new LinkedHashMap<>(proposal);preserve.put("preservePending",true);require(matches(preserve,matcher("Amendments/Amendments Functions","proposePublic")),"Optional preservePending");
      preserve.put("preservePending","yes");require(!matches(preserve,matcher("Amendments/Amendments Functions","proposePublic")),"preservePending Boolean");
      check("Amendments/Amendments Functions","approve",m("proposalId","p1"),List.of("proposalId"));
      check("Commerce/Product Functions","quote",m("unitPriceMinor",0,"quantity",1),List.of("unitPriceMinor","quantity"));
      require(!matches(m("unitPriceMinor",1000000001,"quantity",1),matcher("Commerce/Product Functions","quote")),"Quote price bound");
      require(!matches(m("unitPriceMinor",1,"quantity",1001),matcher("Commerce/Product Functions","quote")),"Quote quantity bound");
      var transition=typed("State/Transition Input",m("to","closed"));
      check("State/State Machine Functions","transition",transition,List.of("to"));
      transition.put("reason","User selected closing");require(matches(transition,matcher("State/State Machine Functions","transition")),"Optional transition reason");
      transition.put("reason",7);require(!matches(transition,matcher("State/State Machine Functions","transition")),"Transition reason Text");
      System.out.println("PASS A9 native required/optional fields and numeric bounds");
      effects();
    }
  }
}
