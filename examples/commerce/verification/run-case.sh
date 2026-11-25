#!/usr/bin/env bash
# Apply a Blue case to its sibling agreement and replay the same inputs.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: run-case.sh path/to/scenario.case.yaml path/to/output-directory" >&2
  exit 2
fi
: "${BLUE_JAVA_CLASSPATH:?Set BLUE_JAVA_CLASSPATH to the matching native Core test runtime classpath}"
: "${JAVA_HOME:?Set JAVA_HOME to the Java 21 JDK}"

script_dir="$(cd "$(dirname "$0")" && pwd)"
packages_root="$(cd "$script_dir/../../.." && pwd)"
classes="$(mktemp -d)"
trap 'rm -rf "$classes"' EXIT

"$JAVA_HOME/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" -d "$classes" \
  "$packages_root/tools/QualificationRuntime.java" \
  "$packages_root/tools/CurrentOperationScenarios.java" \
  "$script_dir/RunCatalogueCase.java"
"$JAVA_HOME/bin/java" -Xmx900m -cp "$classes:$BLUE_JAVA_CLASSPATH" \
  blue.core.RunCatalogueCase "$packages_root" "$1" "$2"
