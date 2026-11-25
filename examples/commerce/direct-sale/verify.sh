#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  printf 'Usage: %s RESULTS_JSON\n' "$0" >&2
  exit 2
fi
: "${BLUE_JAVA_CLASSPATH:?Set BLUE_JAVA_CLASSPATH to the matching native Core test runtime classpath}"
: "${JAVA_HOME:?Set JAVA_HOME to the Java 21 JDK}"

example_dir=$(cd -- "$(dirname -- "$0")" && pwd)
packages_root=$(cd -- "$example_dir/../../.." && pwd)

scratch=$(mktemp -d "${TMPDIR:-/tmp}/marigold-direct-sale.XXXXXX")
trap 'rm -rf -- "$scratch"' EXIT

"$JAVA_HOME/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" -d "$scratch" \
  "$packages_root/tools/QualificationRuntime.java" "$example_dir/VerifyDirectSale.java"
"$JAVA_HOME/bin/java" -Xmx3g -XX:ActiveProcessorCount=4 -cp "$scratch:$BLUE_JAVA_CLASSPATH" \
  blue.core.VerifyDirectSale "$packages_root" "$example_dir" "$1"
