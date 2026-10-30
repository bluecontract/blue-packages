package blue.core;

import blue.contracts.MinimalDispatchPolicyProbe;
import blue.contracts.RuntimeBindings;
import blue.coordination.AuthoringRuntime;
import java.nio.file.Path;

/** Native behavior checks against the supplied Blue Packages catalogue and exact Core test classpath. */
public final class AccessEventsConformance {
  public static void main(String[] args) throws Exception {
    var root = Path.of(args[0]).toAbsolutePath();
    IndependentPartyMappingTest.packages = CompositionPackages.published(root, root.resolve("PACKAGES.json"));
    var tests = new ActivationFundamentalsTest();
    tests.approvalModeDefersStartupAndEmitsItOnlyOnce();
    System.out.println("PASS consent gate, denial before consent, activation and one-time startup");
    tests.ordinaryPartyReplacementStillRequiresFreshConsentWithoutRepeatingStartup();
    System.out.println("PASS party replacement requires fresh consent and retains startup history");
    tests.configurableObservationCannotBypassGate();
    System.out.println("PASS observation cannot bypass authorization gate");
    tests.recompositionInstallsTheUpdatedDocumentDispatchPolicy();
    System.out.println("PASS Clauses recomposition installs policy and protects Activation removal");
    try (var runtime = new AuthoringRuntime(RuntimeBindings.accessEvents())) {
      var p = runtime.processor(IndependentPartyMappingTest.packages.language());
      var source = ActivationFundamentalsTest.counter(true, false);
      var initialized = IndependentPartyMappingTest.success(p.process(source, Values.map("kind", "Initialize"), 10));
      var earlier = MinimalDispatchPolicyProbe.evaluate(p, initialized.document(), 9, "customer", "increment");
      var current = MinimalDispatchPolicyProbe.evaluate(p, initialized.document(), 11, "customer", "increment");
      if (!Boolean.TRUE.equals(earlier.get("allowed")) || !Boolean.TRUE.equals(current.get("allowed")))
        throw new AssertionError("Timestamp cutoff remains: " + earlier + " / " + current);
      if (Values.obj(p.read(initialized.document(), "/activation")).containsKey("channelsAdmittedAfter"))
        throw new AssertionError("Timestamp-dependent activation state remains");
      var standalone = IndependentPartyMappingTest.success(p.initialize(source));
      if (!initialized.document().blueId().equals(standalone.document().blueId()))
        throw new AssertionError("Initialization timestamp changed document identity");
      System.out.println("PASS earlier request policy allowed; timestamp-independent state and identity");
    }
  }
}
