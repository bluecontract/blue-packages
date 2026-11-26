import blue.language.next.*;
import java.util.*;

/** Resolves package-authoring links through native Language. */
public final class OperationInputs {
  private OperationInputs() {}
  // Reserved package-authoring namespace; ordinary requestFrom is always user data.
  private static final String LINK = "$blue:requestFrom";
  private static final String FUNCTION_LINK = "$blue:functionFrom";
  private static final String MEMBERS_LINK = "$blue:membersFrom";

  static Map<String,Object> publish(String namespace,Map<String,Object> definitions,Map<String,BluePackage> imports) {
    if(!containsLink(definitions))return definitions;
    var orderingDefinitions=new LinkedHashMap<String,Object>();
    definitions.forEach((name,value)->orderingDefinitions.put(name,withoutSelfLinks(value,namespace+"/"+name)));
    var ordered=new LinkedHashSet<String>();
    for(String name:definitions.keySet())BuildPaymentFamily.order(name,namespace+"/",orderingDefinitions,ordered,new HashSet<>());
    var bundle=PackageBundle.builder();imports.forEach(bundle::mount);
    var packages=bundle.build();var provider=new MemoryNodeProvider();var aliases=new LinkedHashMap<String,String>();
    var result=new LinkedHashMap<String,Object>();
    for(String name:ordered) {
      var builder=Blue.builder().packages(packages).nodeProvider(provider);aliases.forEach(builder::alias);
      String ownAlias=namespace+"/"+name;
      String provisionalId=null;
      // A generator may publish an argument of its own library. The authoring link is
      // not a recursive native type: resolve against a marker-free semantic view first.
      if(!Objects.equals(orderingDefinitions.get(name),definitions.get(name))) {
        try(var preliminary=builder.build()) {
          var admitted=preliminary.admitDefinition(WireData.write(withoutLinks(definitions.get(name))));
          provider.store(admitted);provisionalId=admitted.blueId();
        }
        builder=Blue.builder().packages(packages).nodeProvider(provider);aliases.forEach(builder::alias);
        builder.alias(ownAlias,provisionalId);
      }
      try(var blue=builder.build()) {
        Object transformed=transform(definitions.get(name),blue,ownAlias);
        if(provisionalId!=null&&referencesId(transformed,provisionalId))
          throw new IllegalArgumentException("Input link requires a provisional self type in "+ownAlias);
        var admitted=blue.admitDefinition(WireData.write(transformed));provider.store(admitted);
        aliases.put(namespace+"/"+name,admitted.blueId());result.put(name,transformed);
      } catch(Failure failure) {
        throw new IllegalArgumentException("Invalid exported definition "+ownAlias+": "+failure.outcome(),failure);
      }
    }
    return result;
  }

  private static boolean referencesId(Object value,String id) {
    if(value instanceof Map<?,?> map)return id.equals(map.get("blueId"))||map.values().stream().anyMatch(v->referencesId(v,id));
    return value instanceof List<?> list&&list.stream().anyMatch(v->referencesId(v,id));
  }

  private static Object withoutSelfLinks(Object value,String alias) {
    if(value instanceof List<?> list)return list.stream().map(v->withoutSelfLinks(v,alias)).toList();
    if(!(value instanceof Map<?,?> map))return value;
    var result=new LinkedHashMap<String,Object>();
    map.forEach((key,child)-> {
      if(key.equals(LINK)&&child instanceof Map<?,?> link&&link.get("definition") instanceof Map<?,?> definition
          &&alias.equals(definition.get("type")))return;
      result.put(key.toString(),withoutSelfLinks(child,alias));
    });return result;
  }

  private static Object withoutLinks(Object value) {
    if(value instanceof List<?> list)return list.stream().map(OperationInputs::withoutLinks).toList();
    if(!(value instanceof Map<?,?> map))return value;
    var result=new LinkedHashMap<String,Object>();
    map.forEach((key,child)->{if(!key.equals(LINK))result.put(key.toString(),withoutLinks(child));});return result;
  }

  private static boolean containsLink(Object value) {
    if(value instanceof Map<?,?> map)return map.containsKey(LINK)||map.containsKey(FUNCTION_LINK)
        ||map.containsKey(MEMBERS_LINK)||map.values().stream().anyMatch(OperationInputs::containsLink);
    return value instanceof List<?> list&&list.stream().anyMatch(OperationInputs::containsLink);
  }

  private static Object transform(Object value,Blue blue,String path) {
    if(value instanceof List<?> list) {
      var result=new ArrayList<Object>();for(int i=0;i<list.size();i++)result.add(transform(list.get(i),blue,path+"/"+i));return result;
    }
    if(!(value instanceof Map<?,?> map))return value;
    if(map.containsKey(FUNCTION_LINK)) {
      if(!map.keySet().equals(Set.of(FUNCTION_LINK)))
        throw new IllegalArgumentException("Function reference must be a singleton at "+path);
      return functionReference(map.get(FUNCTION_LINK),blue,path);
    }
    var result=new LinkedHashMap<String,Object>();
    if(map.containsKey(MEMBERS_LINK))result.putAll(memberReferences(map.get(MEMBERS_LINK),blue,path));
    map.forEach((k,v)->{
      if(!k.equals(LINK)&&!k.equals(MEMBERS_LINK))result.put(k.toString(),transform(v,blue,path+"/"+k));
    });
    if(map.get(MEMBERS_LINK) instanceof Map<?,?> link&&link.containsKey("aliases"))
      memberAliases(link.get("aliases"),result,path);
    if(map.containsKey(LINK)) {
      Object request=resolve(map.get(LINK),blue,path+"/"+LINK);
      // Resolve every explicit link, even when an authored public adapter retains its own matcher.
      if(!result.containsKey("request"))result.put("request",request);
    }
    return result;
  }

  /** Compose inherited members before admission so local overrides can replace fixed bodies. */
  private static Map<String,Object> memberReferences(Object raw,Blue blue,String path) {
    try {
      if(!(raw instanceof Map<?,?> link)
          ||!Set.of("definition","field","aliases").containsAll(link.keySet())
          ||!(link.get("definition") instanceof Map<?,?> definition)
          ||!(link.get("field") instanceof String field)
          ||!Set.of("functions","actions").contains(field)
          ||!path.endsWith("/"+field)) {
        throw new IllegalArgumentException("Expected a definition and the containing functions or actions field");
      }
      var runtime=new NativeRuntime(blue);
      var source=NativeRuntime.recipe(NativeRuntime.exactOf(blue.admitDefinition(WireData.write(definition))));
      var head=NativeRuntime.head(source,runtime);
      if(!head.fields.containsKey(field))
        throw new IllegalArgumentException("Definition declares no "+field);
      var members=NativeRuntime.child(head,field);
      var result=new LinkedHashMap<String,Object>();
      var memberMap=NativeRuntime.head(members,runtime);
      for(String name:memberMap.fields.keySet()) {
        var exact=NativeRuntime.exact(NativeRuntime.child(memberMap,name),runtime);
        result.put(name,field.equals("functions")
            ? Map.of("blueId",NativeRuntime.identity(exact))
            : WireData.json(NativeRuntime.exactText(exact)));
      }
      return result;
    } catch(RuntimeException failure) {
      throw new IllegalArgumentException("Invalid member composition at "+path+": "+failure.getMessage(),failure);
    }
  }

  private static void memberAliases(Object raw,Map<String,Object> members,String path) {
    if(!(raw instanceof Map<?,?> aliases))
      throw new IllegalArgumentException("Invalid member composition at "+path+": expected member aliases");
    var names=Set.copyOf(members.keySet());
    for(var alias:aliases.entrySet()) {
      if(!(alias.getKey() instanceof String name)||name.isBlank()
          ||!(alias.getValue() instanceof String from)||!names.contains(from)||members.containsKey(name))
        throw new IllegalArgumentException("Invalid member composition at "+path+": invalid or conflicting member alias "+alias.getKey());
      members.put(name,members.get(from));
    }
  }

  /** Authoring-time exact reference, not a runtime function loader or a typed instance. */
  private static Object functionReference(Object raw,Blue blue,String path) {
    try {
      if(!(raw instanceof Map<?,?> link))
        throw new IllegalArgumentException("Expected a function type or a definition and function name");
      var runtime=new NativeRuntime(blue);
      NativeRuntime.Recipe selected;
      if(link.keySet().equals(Set.of("type"))&&link.get("type") instanceof String alias&&!alias.isBlank()) {
        var wrapper=blue.admitDefinition(WireData.write(link));
        String typeId=NativeRuntime.head(NativeRuntime.recipe(NativeRuntime.exactOf(wrapper)),runtime).type;
        if(typeId==null)throw new IllegalArgumentException("Function type is missing");
        selected=NativeRuntime.recipe(new Exact.Ref(typeId));
      } else if(link.keySet().equals(Set.of("definition","function"))
          &&link.get("definition") instanceof Map<?,?> definition
          &&link.get("function") instanceof String name&&!name.isBlank()) {
        var wrapper=blue.admitDefinition(WireData.write(definition));
        selected=NativeRuntime.recipe(NativeRuntime.exactOf(wrapper));
        var functions=NativeRuntime.head(selected,runtime);
        if(!functions.fields.containsKey("functions"))
          throw new IllegalArgumentException("Definition declares no functions");
        functions=NativeRuntime.head(NativeRuntime.child(functions,"functions"),runtime);
        if(!functions.fields.containsKey(name))throw new IllegalArgumentException("Missing declared function "+name);
        selected=NativeRuntime.child(functions,name);
      } else {
        throw new IllegalArgumentException("Expected a function type or a definition and function name");
      }
      var head=NativeRuntime.head(selected,runtime);
      if(!head.fields.containsKey("args")||(!head.fields.containsKey("do")&&!head.fields.containsKey("expr")))
        throw new IllegalArgumentException("Referenced definition is not a function");
      return Map.of("blueId",NativeRuntime.identity(NativeRuntime.exact(selected,runtime)));
    } catch(RuntimeException failure) {
      throw new IllegalArgumentException("Invalid function reference at "+path+": "+failure.getMessage(),failure);
    }
  }

  private static Object resolve(Object raw,Blue blue,String path) {
    try {
      if(!(raw instanceof Map<?,?> link)||!link.keySet().equals(Set.of("definition","function","argument")))
        throw new IllegalArgumentException("Expected exactly definition, function and argument");
      for(String key:List.of("function","argument"))
        if(!(link.get(key) instanceof String s)||s.isBlank())throw new IllegalArgumentException("Invalid "+key);
      if(!(link.get("definition") instanceof Map<?,?>))throw new IllegalArgumentException("Definition must be a native type or Blue ID reference");
      var definition=blue.admitDefinition(WireData.write(link.get("definition")));
      var runtime=new NativeRuntime(blue);var selected=NativeRuntime.recipe(NativeRuntime.exactOf(definition));
      for(String field:List.of("functions",link.get("function").toString(),"args",link.get("argument").toString())) {
        var head=NativeRuntime.head(selected,runtime);
        if(!head.fields.containsKey(field))throw new IllegalArgumentException("Missing declared field "+field);
        selected=NativeRuntime.child(head,field);
      }
      var exact=NativeRuntime.exact(selected,runtime);
      return WireData.json(NativeRuntime.exactText(exact));
    } catch(RuntimeException failure) {
      throw new IllegalArgumentException("Invalid operation input link at "+path+": "+failure.getMessage(),failure);
    }
  }
}
