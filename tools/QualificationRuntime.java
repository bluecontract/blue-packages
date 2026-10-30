package blue.packages;

import blue.contracts.RuntimeBindings;

/** The maintained package catalogue executes with Access Events and definition reads. */
public final class QualificationRuntime {
  private QualificationRuntime() {}
  public static RuntimeBindings bindings() {
    return RuntimeBindings.accessEvents().withDefinitionReadV1();
  }
}
