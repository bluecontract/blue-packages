import blue.contracts.*;
import blue.coordination.AuthoringRuntime;
import blue.core.CompositionPackages;
import java.nio.file.*;
import java.util.*;

/** Generated negotiation entries are exercised as native operations, not matcher-only assertions. */
public final class ActivationExecutionConformance {
  static Map<String,Object> m(Object... pairs){return OperationInputConformance.m(pairs);}
  static void require(boolean condition,String message){OperationInputConformance.require(condition,message);}
  public static void main(String[] args)throws Exception {
    var root=Path.of(args[0]);var packages=CompositionPackages.published(root,root.resolve("PACKAGES.json"));
    for(String action:List.of("proposeAndActivate","activate","withdrawProposal","rejectProposal","withdrawAcceptance","updateParty")) {
      var channel=m("type","Contracts/External Channel","event",m("source","owner"));
      var source=m("name","Native negotiation "+action,"type","Agreements/Agreement with Clauses","price",100,
        "contracts",m("owner",channel),"clauses",m("activation",m("type","Activation/Activation Clause","parameters",m(
          "parties",m("owner",m("type","Parties/Party","lead",m("channel",channel),"readerKeys",List.of("reader-owner"))),
          "required",List.of("owner"),"negotiation",m("allowedPaths",List.of("/price"))))));
      try(var runtime=new AuthoringRuntime(RuntimeBindings.accessEvents().withDefinitionReadV1())) {
        var processor=runtime.processor(packages.language());var initialized=processor.initialize(source);
        require(initialized.status().equals("APPLIED"),"Initialize "+action+": "+initialized.status());
        var document=initialized.document();long time=1;
        if(action.equals("updateParty")) {
          var request=m("type","Activation/Party Update Input","replacement",m("lead",m("channel",channel),"displayName","Changed owner"));
          var result=processor.process(document,OperationCatalogConformance.event(document,"owner","updateParty_owner",request),time);
          require(result.status().equals("APPLIED"),"Party replacement: "+result.status()+" "+result.receipt());
          require("Changed owner".equals(processor.read(result.document(),"/activation/parties/owner/displayName")),"Party replacement effect");
        } else if(action.equals("withdrawAcceptance")) {
          var request=m("type","Activation/Terms Selection Input","termsRef",processor.read(document,"/activation/terms/ref"));
          var result=processor.process(document,OperationCatalogConformance.event(document,"owner","withdrawAcceptance_owner",request),time);
          require(result.status().equals("APPLIED"),"Withdraw acceptance: "+result.status()+" "+result.receipt());
          require(Boolean.FALSE.equals(processor.read(result.document(),"/activation/active")),"Withdraw acceptance leaves inactive");
        } else {
          var proposal=m("type","Activation/Terms Proposal Input","proposalId","proposal-1","baseTermsRef",processor.read(document,"/activation/terms/ref"),
            "changes",m("type","List","itemType","Activation/Term Change","items",List.of(m("type","Activation/Term Change","path","/price","replacement",120))));
          String first=action.equals("proposeAndActivate")?action:"proposeChanges";
          var proposed=processor.process(document,OperationCatalogConformance.event(document,"owner",first+"_owner",proposal),time++);
          require(proposed.status().equals("APPLIED"),first+": "+proposed.status()+" "+proposed.receipt()+" "+proposed.observations());document=proposed.document();
          if(!action.equals("proposeAndActivate")) {
            var request=action.equals("activate")?m("type","Activation/Terms Selection Input","proposalId","proposal-1","termsRef",processor.read(document,"/activation/negotiation/proposal/termsRef")):m("proposalId","proposal-1");
            var result=processor.process(document,OperationCatalogConformance.event(document,"owner",action+"_owner",request),time);
            require(result.status().equals("APPLIED"),action+": "+result.status()+" "+result.receipt());document=result.document();
          }
          if(action.equals("activate")||action.equals("proposeAndActivate")) {
            require(processor.read(document,"/price").toString().equals("120"),action+" changed terms");
            require(Boolean.TRUE.equals(processor.read(document,"/activation/active")),action+" activated terms");
          } else require(!"proposal-1".equals(processor.read(document,"/activation/negotiation/proposal/id")),action+" removed current proposal");
        }
        System.out.println("PASS generated native Activation "+action);
      }
    }
  }
}
