package blue.core;

import blue.contracts.Contracts;
import blue.language.next.*;
import blue.packages.QualificationRuntime;
import java.nio.file.*;
import java.util.*;

/** Concrete adapter identities retain the upstream instruction protocols. No operator calls. */
public final class MyosInstructionTypesConformance {
  static final List<String> TYPES = List.of(
      "MyOS Stripe Customer Payment Instruction", "MyOS Test Customer Payment Instruction",
      "MyOS Stripe Account to Account Payment Instruction", "MyOS Test Account to Account Payment Instruction");

  @SuppressWarnings("unchecked")
  static Map<String, Object> payerFixture(Map<String, Object> value) {
    return (Map<String, Object>) WireData.parse(WireData.write(value).replace("customer", "payer"), "json");
  }

  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]).toAbsolutePath();
    var myos = BluePackage.open(root.resolve("myos/dist/package.bluepkg"));
    var payment = BluePackage.open(root.resolve("payment-instruction/dist/package.bluepkg"));
    var ids = new HashSet<String>();
    try (var blue = Blue.builder().packages(PackageBundle.builder().mount("MyOS", myos).build()).build()) {
      var values = new Contracts(blue, QualificationRuntime.bindings()).execution().values();
      for (String name : TYPES) {
        String id = myos.exportId(name);
        if (id == null || !ids.add(id)) throw new AssertionError("Missing or duplicate concrete type: " + name);
        var concrete = new Exact.Ref(id);
        boolean customer = name.contains("Customer");
        var base = new Exact.Ref(customer ? myos.exportId("MyOS Customer Payment Instruction")
            : payment.exportId("Payment Instruction with Clauses"));
        for (String path : List.of("/contracts", "/clauses", "/paymentTerms")) {
          var actual = values.select(concrete, path);
          var expected = values.select(base, path);
          if (!Objects.equals(actual == null ? null : values.bexData(actual),
              expected == null ? null : values.bexData(expected)))
            throw new AssertionError(name + " changes inherited " + path);
        }
        if (values.select(concrete, "/provider") != null)
          throw new AssertionError("Provider is identified by concrete type, not a second field");
      }
    }
    var packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    Path reports = root.resolve("reports/operation-input/myos-instruction-types");
    Files.createDirectories(reports);
    for (String name : TYPES) {
      Path file = CurrentOperationScenarios.caseFile(root, "27");
      var source = CurrentOperationScenarios.read(file.resolveSibling("27-payment-protocol.blue"));
      source.put("type", "MyOS/" + name);
      var scenario = CurrentOperationScenarios.read(file);
      if (name.contains("Customer")) {
        source = payerFixture(source);
        scenario = payerFixture(scenario);
      }
      @SuppressWarnings("unchecked") var original = (List<Object>) scenario.get("steps");
      var steps = new ArrayList<>(original.subList(0, 5));
      if (name.contains("Customer")) {
        steps.add(Map.of("operation", "provideSession", "channel", "guarantor",
            "request", Map.of("type", "MyOS/Customer Session Input", "sessionId", "concrete-session"), "requireExactDocumentVersion", true,
            "expect", Map.of("/customerSession/funded", false)));
        steps.add(Map.of("operation", "confirmFunding", "channel", "guarantor",
            "request", Map.of("sessionId", "concrete-session"), "requireExactDocumentVersion", true,
            "expect", Map.of("/customerSession/funded", true)));
      }
      steps.add(original.get(5));
      scenario.put("steps", steps);
      CurrentOperationScenarios.run(packages, reports, name.replace(' ', '-') + ".case.yaml", scenario, source);
      System.out.println("PASS " + name + ": native acceptance and initiation; upstream funding preserved");
    }
  }
}
