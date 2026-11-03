package blue.core;

import static blue.core.Values.*;
import blue.contracts.RuntimeBindings;
import blue.coordination.*;
import blue.language.next.*;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;

/** Signed holder approval and revocation of the additive policy package; no PI bootstrap claim. */
public final class SellerPaymentPolicyConformance {
  static void require(boolean value,String reason) { if(!value)throw new AssertionError(reason); }
  public static void main(String[] args)throws Exception {
    String negative=args.length>2&&!args[2].equals("baseline")?args[2]:null;
    var bindings=RuntimeBindings.accessEvents().withMandateInitializationV2().withDefinitionReadV1();
    var pkg=new PackageLoader().open(Path.of(args[0]).resolve("myos-payment-mandates/dist/package.bluepkg"),PackageSelection.pinned(args[1]));
    try(var input=new SignedActorInputs(bindings);var language=Blue.builder().nodeProvider(input.service.nodeProvider())
        .packages(PackageBundle.builder().mount("PaymentPolicy",pkg).build()).build()) {
      var owner=input.timeline("owner",HostActorProfiles.principal("seller"));
      var agent=input.timeline("agent",HostActorProfiles.agent("seller","agent"));input.refresh();
      var section=map("definition",List.of(),"replacements",List.of());
      var source=map("type","PaymentPolicy/Seller Payment Policy Mandate","name","Policy initialization conformance",
          "policy",map("sellerAccountId","seller","sellerAgentId","agent","orderProfile","correlated/3","provider","test",
              "recipientPaymentAccountId","recipient","guarantorAccountId","guarantor","currency","PLN",
              "minimumAmountMinor",1,"maximumAmountMinor",10000),
          "expectedProgram",map("orderType","DXVyaZMh1ohnUF7oY9NgDrwD7VB71WhVu7668Xwam1XS",
              "contracts",section,"clauses",section,"paymentTemplate",section,"timelineAccess",section,"rootKeys",List.of()),
          "contracts",map("authorityHolderChannel",owner.channel(),"authorizedActorChannel",agent.channel()));
      if(args.length>3) source.put("expectedProgram",WireData.parse(Files.readString(Path.of(args[3])),"json"));
      if(args.length>2&&args[2].equals("baseline"))
        source.put("type",map("blueId","GqUCrevmNkQt2p4mAM9G5oBynDXiZE7fiqDDgZhezZKb"));
      if(negative!=null) {
        var values=new blue.contracts.Contracts(language).execution().values();
        if(negative.equals("append-initializer") || negative.equals("append-do")) {
          var workflow=obj(values.literal(values.exact(values.select(values.source(source),"/contracts/initializeSellerPaymentScope"))));
          var rawSteps=workflow.get("steps");
          var steps=new ArrayList<>(arr(rawSteps instanceof Map ? obj(rawSteps).get("items") : rawSteps));
          var appended=obj(WireData.parse(WireData.write(steps.getFirst()),"json"));
          appended.put("do",List.of(map("$appendChange",map("op","replace","path","/scope","val",map("payment",map("target",map("channel","seller","operation","providePayment","documentValidation",map("function",map("expr",true)))))))));
          if(negative.equals("append-do")) { var first=obj(steps.getFirst()); var actions=new ArrayList<>(arr(first.get("do"))); actions.addAll(arr(appended.get("do"))); first.put("do",actions); }
          else steps.add(appended);
          obj(source.get("contracts")).put("initializeSellerPaymentScope",map("steps",steps));
        }
        else if(negative.equals("host-embedded")) obj(source.get("contracts")).put("embedded",map("type",map("blueId","4dHcKJRA9zrc9kuf2wCWFZrCCJz6rS3RgLhSHAWuGT2R"),"paths",List.of()));
        else if(negative.equals("initializer")) obj(source.get("contracts")).put("initializeSellerPaymentScope",map("steps",List.of()));
        else if(negative.equals("predicate")) obj(source.get("contracts")).put("initializeSellerPaymentScope",map("steps",List.of(map("functions",map("fixedPaymentGrant",map("expr",map("$literal",map("target",map("operation","approve_seller")))))))));
        else if(negative.equals("clauses")) source.put("clauses",map("mutator",map("enabled",true)));
        else if(negative.equals("embedded")) source.put("embedded",map("mutator",map("enabled",true)));
        else {
          var workflow=obj(values.literal(values.exact(values.select(values.source(source),"/contracts/initializeSellerPaymentScope"))));
          workflow.put("order",1);
          var step=obj(arr(workflow.get("steps")).getFirst());
          step.put("do",negative.equals("remove-gate")?List.of(
              map("$appendChange",map("op","remove","path","/contracts/initializeSellerPaymentScope")),
              map("$appendChange",map("op","remove","path","/contracts/extraMutator"))):
              negative.equals("self-delete")?List.of(map("$appendChange",map("op","remove","path","/contracts/extraMutator"))):List.of(map("$appendChange",map("op","replace","path","/policy/maximumAmountMinor","val",10000000))));
          obj(source.get("contracts")).put("extraMutator",workflow);
        }
      }
      var admitted=language.createJson(WireData.write(source));
      System.out.println("declaredRequirements="+WireData.write(language.declaredRequirements(admitted)));
      require(WireData.write(language.declaredRequirements(admitted)).contains(RuntimeBindings.INITIALIZABLE_MANDATES_RULES),
          "Derived mandate declares inherited Initializable Mandates authority specification");
      var mandate=input.service.register(admitted);
      var pending=mandate.awaitInitialized(Duration.ofSeconds(30));

      require(negative==null || negative.equals("host-embedded"),"Noncanonical extension initialized; application qualification required: "+negative);
      require("Pending".equals(pending.document().get("status")),"Holder approval required");
      require(obj(pending.document().get("scope")).keySet().equals(Set.of("payment")),"Exactly one installed grant");
      var grant=obj(obj(pending.document().get("scope")).get("payment"));
      require("providePayment".equals(obj(grant.get("target")).get("operation")),"Only provision operation");
      var constants=obj(obj(obj(grant.get("target")).get("documentValidation")).get("function"));
      constants=obj(constants.get("constants"));
      var values=new blue.contracts.Contracts(language).execution().values();
      var initial=values.source(source);
      require(constants.get("policyIdentity").equals(NativeRuntime.identity(values.exact(values.select(initial,"/policy")))),"Policy identity pinned natively");
      require(constants.get("expectedProgramIdentity").equals(NativeRuntime.identity(values.exact(values.select(initial,"/expectedProgram")))),"Recipe identity pinned natively");
      require(obj(pending.document().get("grantTemplates")).get("payment").equals(grant),"Protected template and initial scope match");
      var human=HostActorProfiles.browserSource(bindings,"seller","admin",1,1,"session","credential");
      input.call(mandate,owner,owner.actor,human,"authorityHolderChannel","approveMandate",null);
      var active=mandate.state().stable().orElseThrow().document();
      require("Active".equals(active.get("status")),"Signed holder approval activates");
      input.call(mandate,owner,owner.actor,human,"authorityHolderChannel","terminateMandate",null);
      var revoked=mandate.state().stable().orElseThrow().document();
      require("Terminated".equals(revoked.get("status")),"Signed holder revocation terminates");
      require(obj(revoked.get("scope")).isEmpty(),"Revocation clears inherited scope despite immutable grant template");
      var capture=map("source",source,"pending",pending.document(),"active",active,"terminated",revoked);
      try(var captureLanguage=Blue.builder().nodeProvider(input.service.nodeProvider()).build()) {
        capture.put("dependencyRecords",captureLanguage.admitDefinition(WireData.write(active)).dependencyResponses());
      }
      Files.writeString(Path.of("/tmp/myos-stage3-packages/policy-lifecycle-capture.json"),WireData.write(capture));
      System.out.println("PASS native policy initialization, signed approval and scope-clearing revocation");
    } catch(blue.contracts.ContractException e){
      if(negative!=null && !negative.equals("host-embedded")) {require(Set.of("BEX_EXECUTION_REJECTED").contains(e.code()),"Unexpected negative error: "+e.code()+" "+e.context());System.out.println("PASS denied "+negative+" "+e.code());return;}
      System.out.println(e.code()+" "+e.context());throw e;
    } catch(Failure e){if(negative!=null&&(negative.equals("initializer")||negative.equals("predicate"))){require(e.category().equals("FixedValueConflict"),"Unexpected admission failure: "+e.outcome());System.out.println("PASS fixed initializer rejects mutation "+e);return;}throw e;}
  }
}
