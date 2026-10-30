#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
edition=access-events
args=()
while [[ $# -gt 0 ]]; do
  if [[ "$1" == --edition ]]; then
    [[ $# -ge 2 ]] || { echo '--edition requires a value' >&2; exit 2; }
    edition=$2; shift 2
  else
    args+=("$1"); shift
  fi
done
selected=$(PYTHONPATH="$root/tools" python3 -c 'from pathlib import Path; import sys; from editions import edition_root; print(edition_root(Path(sys.argv[1]), sys.argv[2]))' "$root" "$edition")
: "${BLUE_JAVA_CLASSPATH:?Set BLUE_JAVA_CLASSPATH to the qualified Java runtime jars; no runtime binaries are vendored here}"
java_cmd=java
javac_cmd=javac
if [[ -n "${JAVA_HOME:-}" ]]; then java_cmd="$JAVA_HOME/bin/java"; javac_cmd="$JAVA_HOME/bin/javac"; fi
mkdir -p "$root/build/payment-family-classes"
"$javac_cmd" -cp "$BLUE_JAVA_CLASSPATH" -d "$root/build/payment-family-classes" "$root/tools/OperationInputs.java" "$root/tools/BuildPaymentFamily.java"
exec "$java_cmd" -Xmx1500m -cp "$root/build/payment-family-classes:$BLUE_JAVA_CLASSPATH" BuildPaymentFamily "$selected" "${args[@]}"
