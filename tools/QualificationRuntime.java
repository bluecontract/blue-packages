package blue.packages;

import blue.contracts.RuntimeBindings;

/** The runtime edition must match the explicitly selected package catalogue. */
public final class QualificationRuntime {
  private QualificationRuntime() {}
  public static RuntimeBindings bindings() {
    return switch (System.getProperty("blue.packages.edition", "access-events")) {
      case "access-events" -> RuntimeBindings.accessEvents().withDefinitionReadV1();
      case "demand-scoped" -> RuntimeBindings.demandScopedSourceExpansionEdition().withDefinitionReadV1();
      default -> throw new IllegalArgumentException("Unknown package edition");
    };
  }
}
