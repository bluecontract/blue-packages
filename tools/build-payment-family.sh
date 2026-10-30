#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
for arg in "$@"; do
  if [[ "$arg" == --* ]]; then
    echo "Unsupported option: $arg (this builder uses Access Events)" >&2
    exit 2
  fi
done
: "${BLUE_JAVA_CLASSPATH:?Set BLUE_JAVA_CLASSPATH to the qualified Java runtime jars; no runtime binaries are vendored here}"
java_cmd=java
javac_cmd=javac
if [[ -n "${JAVA_HOME:-}" ]]; then java_cmd="$JAVA_HOME/bin/java"; javac_cmd="$JAVA_HOME/bin/javac"; fi
mkdir -p "$root/build/payment-family-classes"
"$javac_cmd" -cp "$BLUE_JAVA_CLASSPATH" -d "$root/build/payment-family-classes" "$root/tools/OperationInputs.java" "$root/tools/BuildPaymentFamily.java"
exec "$java_cmd" -Xmx1500m -cp "$root/build/payment-family-classes:$BLUE_JAVA_CLASSPATH" BuildPaymentFamily "$root" "$@"
