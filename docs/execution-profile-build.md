# Build and verify the execution profile publication

The package is an ordinary Language-only publication. Its builder is unchanged
Core source `c9890020fa2c93d0e2e0885d5f406bbcecc4c62f`, tree
`9d01779ffb27b32542f3dfdf5afe132cdab693f8`. Build
`:blue-package-tools:installDist` in that revision's `runtime` directory using
Java 21. The qualified local build used Temurin `21.0.12.1+1-LTS`.

Set `JAVA_HOME` and `BLUE_JAVA_CLASSPATH` to the resulting Java installation and
runtime distribution JARs. The immutable classpath manifest in the integration
handoff records every JAR checksum. No local uncommitted runtime classes may
replace these inputs. The maintained Python wrapper compiles
`OperationInputs.java`, `BuildPaymentFamily.java` and `BuildFinalGas.java`.

From a clean task checkout with `tools/requirements.txt` installed:

```sh
python3 tools/build_final_gas.py all
python3 tools/build_final_gas.py blue-execution-profile --check
python3 tools/sync_catalogues.py --check
python3 tools/release.py check
python3 -m unittest discover -s tools -p 'test_release.py'
python3 -m unittest discover -s tools -p 'test_build_final_gas.py'
python3 -m unittest discover -s tools -p 'test_execution_profile.py'
python3 tools/check_payment_family.py
python3 tools/check_clause_tutorial.py
```

`--check` builds in isolation and compares every distribution byte and the
dependency lock. The ordinary publication has no `protocol`, native
`specBindings` or `declaredRequirements`; its only import is Language.
Compare all preceding entries of `PACKAGES.json` by package ID and archive
checksum. Adding this publication must not modify those immutable inputs.

The native schema check uses the same pinned Language classpath:

```sh
mkdir -p reports/execution-profile/classes
"$JAVA_HOME/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" \
  -d reports/execution-profile/classes tools/ExecutionProfileConformance.java
"$JAVA_HOME/bin/java" -Xmx512m \
  -cp "reports/execution-profile/classes:$BLUE_JAVA_CLASSPATH" \
  ExecutionProfileConformance .
```

It admits actual Source and Exact descriptors, preserves a sibling declaration,
and checks native required-field and list-uniqueness constraints. It also checks
that omitted optionals remain absent in Source, Exact and canonical values,
including a node type that declares a profile field without supplying a value.
This does not
install or qualify a Core runtime. Core's reader separately checks the closed
descriptor, exact types/references and implemented native semantics; graph,
restore and replay conformance remains part of the linked Core PR.

The existing release CI job runs the publication/fixture checks and prepares
verified archives. Its full source tree is required for all current and retained
archives, locks and source checksum inventories. The added check needs no new
job, trigger or Git history. Release preparation does not tag, publish or deploy.
